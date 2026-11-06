# -*- coding: utf-8 -*-
import os
import sys
import re
import traceback
import ctypes
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
)
from control_window import ControlWindow
from PyQt5.QtCore import QPoint, QRect, Qt, QTimer, pyqtSignal
import config
from PyQt5 import QtCore

from fileutil import get_resources_dir
from ui.map_catalog import list_available_maps
from ui.window_geometry import clamp_window_position, find_screen_for_window
from ui.timer_window_actions import (
    handle_lock_shortcut,
    handle_map_switch_hotkey,
    handle_screenshot_hotkey,
)
from ui.timer_window_lifecycle import TimerWindowLifecycleMixin

class TimerWindow(TimerWindowLifecycleMixin, QMainWindow):
    # 创建信号用于地图更新
    progress_signal = QtCore.pyqtSignal(list)
    map_switch_signal = pyqtSignal()
    lock_shortcut_signal = pyqtSignal()
    screenshot_shortcut_signal = pyqtSignal()
    toggle_artifact_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # 初始化artifact_window
        from artifacts import ArtifactWindow
        self.artifact_window = ArtifactWindow(self)

        # 设置窗口属性以支持DPI缩放
        self.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WA_NativeWindow)
        # 初始化日志记录器
        from logging_util import get_logger
        self.logger = get_logger(__name__)
        self.logger.info('SC2 Timer 启动')
        
        # 初始化状态
        self.current_time = ""
        self.drag_position = QPoint(0, 0)
        self._last_ui_second = None
        self._last_centered_row = None
        self._last_toast_event_key = None
        self._is_quitting = False
        self._click_through_unlocked = None
        self.hotkey_handles = []
        self.rect_screenshots = []
        
        # 添加一个标志来追踪地图选择的来源
        self.manual_map_selection = False
        
        # 初始化UI
        self.init_ui()
        
        # 初始化Toast提示
        self.init_toast()
        
        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game_time)
        self.timer.start(250)  # 自动开始更新，每100毫秒更新一次
        
        # 初始化突变因子提醒标签和定时器
        self.mutator_alert_labels = {}
        self.mutator_alert_timers = {}
        
        # 为每种突变因子类型创建独立的标签和定时器
        from ui.mutator_alerts import MUTATOR_TYPES
        for mutator_type in MUTATOR_TYPES:
            label = QLabel(self)
            label.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool
            )
            label.setAttribute(Qt.WA_TranslucentBackground)
            label.hide()
            self.mutator_alert_labels[mutator_type] = label
            
            timer = QTimer()
            timer.timeout.connect(lambda t=mutator_type: self.hide_mutator_alert(t))
            self.mutator_alert_timers[mutator_type] = timer
        
        # 连接表格区域的双击事件
        self.table_area.mouseDoubleClickEvent = self.on_text_double_click
        
        # 初始化系统托盘
        self.init_tray()
        
        # 创建控制窗体
        self.control_window = ControlWindow()
        self.update_control_window_position()
        self.control_window.show()

        # 连接控制窗口的状态改变信号
        self.control_window.state_changed.connect(self.on_control_state_changed)
        
        # 监听主窗口位置变化
        self.windowHandle().windowStateChanged.connect(self.update_control_window_position)
        
        # 连接信号到处理函数
        self.progress_signal.connect(self.handle_progress_update)
        self.map_switch_signal.connect(self.handle_map_switch_hotkey)
        self.lock_shortcut_signal.connect(self.handle_lock_shortcut)
        self.screenshot_shortcut_signal.connect(self.handle_screenshot_hotkey)
        self.toggle_artifact_signal.connect(self.handle_artifact_shortcut)
        
        # 初始化全局快捷键
        self.init_global_hotkeys()

        self.click_through_guard_timer = QTimer(self)
        self.click_through_guard_timer.timeout.connect(self.enforce_click_through_state)
        self.click_through_guard_timer.start(5000)

        self.hotkey_guard_timer = QTimer(self)
        self.hotkey_guard_timer.timeout.connect(self.reset_global_hotkeys)
        self.hotkey_guard_timer.start(30 * 60 * 1000)
        
        # 启动游戏检查线程
        from mainfunctions import check_for_new_game
        import threading
        self.game_check_thread = threading.Thread(target=check_for_new_game, args=(self.progress_signal,), daemon=True)
        self.game_check_thread.start()
        
        # 初始化时设置为锁定状态（不可点击）
        # 使用延迟调用，确保窗口已完全初始化
        QTimer.singleShot(100, lambda: self.on_control_state_changed(False))
        
    def get_current_screen(self):
        """获取当前窗口所在的显示器"""
        return find_screen_for_window(
            self.geometry(), QApplication.screens(), QApplication.primaryScreen()
        )
    
    def update_control_window_position(self):
        # 保持控制窗口与主窗口位置同步
        current_screen = self.get_current_screen()
        screen_geometry = current_screen.geometry()

        new_x, new_y = clamp_window_position(
            self.x(),
            self.y() - self.control_window.height(),
            screen_geometry,
            self.control_window.width(),
            self.control_window.height(),
        )
        self.control_window.move(new_x, new_y)

    def center_table_on_row(self, row):
        """仅按纵向滚动，将目标行稳定放到表格中心。"""
        if row is None or row < 0 or row >= self.table_area.rowCount():
            return

        row_top = 0
        for row_index in range(row):
            row_top += self.table_area.rowHeight(row_index)

        row_height = self.table_area.rowHeight(row)
        viewport_height = self.table_area.viewport().height()
        target_scroll = int(row_top + (row_height / 2) - (viewport_height / 2))

        scrollbar = self.table_area.verticalScrollBar()
        target_scroll = max(scrollbar.minimum(), min(target_scroll, scrollbar.maximum()))

        if self._last_centered_row != row or abs(scrollbar.value() - target_scroll) > 1:
            scrollbar.setValue(target_scroll)
            self._last_centered_row = row

    def moveEvent(self, event):
        """鼠标移动事件，用于更新控制窗口位置"""
        super().moveEvent(event)
        if hasattr(self, 'control_window'):
            self.update_control_window_position()

    def handle_screenshot_hotkey(self):
        """处理截图快捷键"""
        handle_screenshot_hotkey(self)

    def init_ui(self):
        from ui.timer_layout import init_ui

        init_ui(self)
    
    def update_game_time(self):
        from ui.map_schedule import update_game_time

        update_game_time(self)
    
    
    def init_tray(self):
        """初始化系统托盘"""
        from tray_manager import TrayManager
        if hasattr(self, 'tray_manager') and self.tray_manager is not None:
            self.tray_manager.dispose()
        self.tray_manager = TrayManager(self)

    def mousePressEvent(self, event):
        """鼠标按下事件，用于实现窗口拖动"""
        # 检查窗口是否处于可点击状态（非锁定状态）
        is_clickable = not self.testAttribute(Qt.WA_TransparentForMouseEvents)
        
        if is_clickable:  # 窗口可点击时
            if event.button() == Qt.LeftButton:
                pos = event.pos()
                map_area = QRect(10, 5, 30, 30)
                if map_area.contains(pos):
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    self.is_dragging = True
                    event.accept()
                else:
                    # 检查是否点击了突变按钮
                    for btn in self.mutator_buttons:
                        if btn.geometry().contains(event.pos() - self.icon_area.pos()) and btn.property("clickable"):
                            event.accept()
                            return
                    event.ignore()
        else:
            if self.ctrl_pressed and event.button() == Qt.LeftButton:
                pos = event.pos()
                map_area = QRect(10, 5, 30, 30)
                if map_area.contains(pos):
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    self.is_dragging = True
                    event.accept()
                else:
                    event.ignore()
            else:
                event.ignore()

    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于实现窗口拖动"""
        if event.buttons() & Qt.LeftButton and hasattr(self, 'is_dragging') and self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            event.accept()

    def on_control_state_changed(self, unlocked):
        """处理控制窗口状态改变事件"""
        self.logger.info(f'控制窗口状态改变: unlocked={unlocked}')
        self._click_through_unlocked = unlocked
        
        # 根据解锁状态显示或隐藏替换指挥官按钮
        if hasattr(self, 'replace_commander_btn'):
            if unlocked:
                self.replace_commander_btn.show()
            else:
                self.replace_commander_btn.hide()
                
        # 同步更新指挥官选择器窗口的显示状态
        if hasattr(self, 'commander_selector'):
            self.commander_selector.set_visibility(unlocked)
        
        self.apply_click_through_state(unlocked, force=True)
        
        # 更新突变按钮的状态
        for btn in self.mutator_buttons:
            # 使用 setAttribute 来控制事件穿透
            btn.setAttribute(Qt.WA_TransparentForMouseEvents, not unlocked)
            
            # 不改变图标状态，保持当前显示
            if btn.isChecked():
                btn.setIcon(btn.original_icon)
            else:
                btn.setIcon(btn.gray_icon)

    def apply_click_through_state(self, unlocked, force=False):
        """Synchronize Qt and Win32 click-through state for the overlay."""
        transparent = not unlocked
        if self.testAttribute(Qt.WA_TransparentForMouseEvents) != transparent:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, transparent)

        if sys.platform != 'win32':
            if force:
                self.hide()
                self.show()
            self.logger.info('已设置窗口为%s状态', '可点击' if unlocked else '不可点击')
            return

        try:
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020

            hwnd = int(self.winId())
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            target_style = ex_style | WS_EX_LAYERED
            if transparent:
                target_style |= WS_EX_TRANSPARENT
            else:
                target_style &= ~WS_EX_TRANSPARENT

            if force or target_style != ex_style:
                kernel32.SetLastError(0)
                previous_style = user32.SetWindowLongW(hwnd, GWL_EXSTYLE, target_style)
                error = kernel32.GetLastError()
                if previous_style == 0 and error != 0:
                    self.logger.error(f'SetWindowLongW失败，错误码: {error}')
                else:
                    self.logger.info(
                        f'设置窗口为{"可点击" if unlocked else "不可点击"}状态，样式从 {ex_style} 更改为 {target_style}'
                    )

                user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0,
                    SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED
                )
        except Exception as e:
            self.logger.error(f'设置Windows平台点击穿透失败: {str(e)}')
            self.logger.error(traceback.format_exc())

    def enforce_click_through_state(self):
        """Restore click-through state if the native window style drifts."""
        if self._click_through_unlocked is not None:
            self.apply_click_through_state(self._click_through_unlocked)
                
    def on_replace_commander(self):
        """处理替换指挥官按钮的点击事件"""
        if hasattr(self, 'commander_selector'):
            # 切换指挥官选择器窗口的打开/关闭状态
            self.commander_selector.toggle_window()
    
    def handle_progress_update(self, data):
        """处理进度更新信号"""
        if data[0] == 'update_map':
            # 在下拉框中查找并选择地图
            map_name = data[1]
            self.logger.info(f'收到地图更新信号: {map_name}')
            
            # 如果是新游戏开始，强制更新地图
            index = self.combo_box.findText(map_name)
            if index >= 0:
                self.logger.info(f'找到地图 {map_name}，更新下拉框选择')
                # 暂时禁用手动选择标志
                self.manual_map_selection = False
                self.combo_box.setCurrentIndex(index)
                # 手动调用地图选择事件处理函数，确保加载地图文件
                self.on_map_selected(map_name)
            else:
                self.logger.warning(f'未在下拉框中找到地图: {map_name}')

    def on_version_selected(self):
        """处理地图版本按钮选择事件"""
        sender = self.sender()
        if not sender or not isinstance(sender, QPushButton):
            return
            
        # 取消其他按钮的选中状态
        for btn in self.version_buttons:
            if btn != sender:
                btn.setChecked(False)
        
        # 获取当前地图名称的前缀
        current_map = self.combo_box.currentText()
        if not current_map:
            return
            
        # 根据按钮文本和地图前缀构造新的地图名称
        prefix = current_map.rsplit('-', 1)[0]
        new_map = f"{prefix}-{sender.text()}"
        
        # 在下拉框中查找并选择新地图
        index = self.combo_box.findText(new_map)
        if index >= 0:
            self.combo_box.setCurrentIndex(index)
    
    def on_map_selected(self, map_name):
        from ui.map_schedule import on_map_selected

        on_map_selected(self, map_name)

    def init_toast(self):
        """初始化Toast提示组件"""
        from toast_manager import ToastManager
        self.toast_manager = ToastManager(self)

    def show_toast(self, message, duration=None, force_show=False):
        """显示Toast提示"""
        self.toast_manager.show_map_toast(message, duration, force_show)

    def show_mutator_alert(self, message, mutator_type='deployment'):
        from ui.mutator_alerts import show_mutator_alert

        show_mutator_alert(self, message, mutator_type)

    def hide_mutator_alert(self, mutator_type):
        """隐藏突变因子提醒"""
        if mutator_type in self.mutator_alert_labels:
            self.mutator_alert_labels[mutator_type].hide()
            self.mutator_alert_timers[mutator_type].stop()

    def hide_toast(self):
        """隐藏Toast提示"""
        self.toast_manager.hide_toast()
    
    def on_text_double_click(self, event):
        """处理表格区域双击事件"""
        if event.button() == Qt.LeftButton:
            selected_items = self.table_area.selectedItems()
            if selected_items:
                # 获取选中行的完整内容
                row = selected_items[0].row()
                time_item = self.table_area.item(row, 0)
                event_item = self.table_area.item(row, 1)
                army_item = self.table_area.item(row, 2)
                if time_item and event_item:
                    time_text = time_item.text().strip()
                    event_text = event_item.text().strip()
                    army_text = army_item.text().strip() if army_item else ""
                    selected_text = f"{time_text}\t{event_text}\t{army_text}" if time_text and army_text.strip() else (f"{time_text}\t{event_text}" if time_text else event_text)
                    self.show_toast(selected_text, config.TOAST_DURATION, force_show=True)  # 设置5000毫秒（5秒）后自动消失
            event.accept()
            
    def init_global_hotkeys(self):
        from ui.hotkeys import init_global_hotkeys

        init_global_hotkeys(self)

    def cleanup_global_hotkeys(self):
        from ui.hotkeys import cleanup_global_hotkeys

        cleanup_global_hotkeys(self)

    def reset_global_hotkeys(self):
        from ui.hotkeys import reset_global_hotkeys

        reset_global_hotkeys(self)


            
    def get_text(self, key):
        """获取多语言文本"""
        try:
            config_path = get_resources_dir('resources', 'words.conf')
            with open(config_path, 'r', encoding='utf-8') as f:
                import json
                content = json.load(f)
                texts = content['qt_gui']
                if config.current_language in texts and key in texts[config.current_language]:
                    return texts[config.current_language][key]
                return key
        except Exception as e:
            self.logger.error(f"加载语言配置文件失败: {str(e)}")
            return key

    def on_language_changed(self, lang):
        if lang == config.current_language:
            return
        """处理语言切换事件"""
        # 更新config.py中的语言配置
        if getattr(sys, 'frozen', False):  # 是否为打包的 exe
            config_file = os.path.join(os.path.dirname(sys.executable), 'config.py')  # exe 所在目录
        else:
            from ui.paths import source_config_path

            config_file = str(source_config_path()) # 源码所在目录

        self.logger.info(f"load config: {config_file}")

        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式替换current_language的值
        new_content = re.sub(r"current_language\s*=\s*'[^']*'", f"current_language = '{lang}'", content)
        
        self.logger.info(f"update config: {config_file}")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 更新config模块中的值
        config.current_language = lang
        
        # 更新commander_selector的语言设置
        if hasattr(self, 'commander_selector'):
            self.commander_selector.set_language(lang)
        
        # 重新加载地图列表
        files = list_available_maps(lang)
        
        # 清空并重新添加地图列表
        self.combo_box.clear()
        self.combo_box.addItems(files)
        
        # 如果有文件，自动加载第一个
        if files:
            self.on_map_selected(files[0])
        
        # 更新UI文本
        self.map_label.setText(self.get_text('map_label'))
        self.replace_commander_btn.setText(self.get_text('replace_commander'))
        
        # 重新初始化系统托盘菜单以更新语言选择标记
        self.init_tray()
    
    def handle_artifact_shortcut(self):
        # 如果窗口可见，则销毁图片
        if self.artifact_window.isVisible():
            self.artifact_window.destroy_images()
            self.artifact_window.hide()
        else:
            # 获取当前选择的地图名称并显示对应的神器图片
            try:
                current_map = self.combo_box.currentText()
                if current_map:
                    self.artifact_window.show_artifact(current_map, config.ARTIFACTS_IMG_OPACITY, config.ARTIFACTS_IMG_GRAY)
            except Exception as e:
                self.logger.error(f'draw artifacts layer failed: {str(e)}')
                self.logger.error(traceback.format_exc())

    def handle_lock_shortcut(self):
        """处理锁定快捷键"""
        handle_lock_shortcut(self)
    
    def handle_map_switch_hotkey(self):
        """处理地图切换快捷键"""
        handle_map_switch_hotkey(self)
    
    def on_mutator_toggled(self, button, checked):
        from ui.mutator_alerts import on_mutator_toggled

        on_mutator_toggled(self, button, checked)

    def load_mutator_config(self, mutator_name):
        from ui.mutator_alerts import load_mutator_config

        return load_mutator_config(self, mutator_name)

    def check_mutator_alerts(self):
        from ui.mutator_alerts import check_mutator_alerts

        check_mutator_alerts(self)
