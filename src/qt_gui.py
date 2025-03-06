import os
import sys
import re
import time
import logging
import traceback
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QSystemTrayIcon, QMenu, QAction, QApplication, QComboBox, QTableWidgetItem, QPushButton, QTableWidget, QHeaderView
from control_window import ControlWindow
from PyQt5.QtGui import QFont, QIcon, QPixmap, QBrush, QColor, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QRect
import config
from PyQt5 import QtCore

class TimerWindow(QMainWindow):
    # 创建信号用于地图更新
    progress_signal = QtCore.pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        
        # 初始化日志记录器
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'sc2_timer.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8', mode='a'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info('SC2 Timer 启动')
        
        # 初始化状态
        self.current_time = ""
        self.drag_position = QPoint(0, 0)
        
        # 添加一个标志来追踪地图选择的来源
        self.manual_map_selection = False
        
        # 初始化UI
        self.init_ui()
        
        # 初始化Toast提示
        self.init_toast()
        
        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game_time)
        self.timer.start(100)  # 自动开始更新，每100毫秒更新一次
        
        # 连接表格区域的双击事件
        self.table_area.mouseDoubleClickEvent = self.on_text_double_click
        
        # 初始化系统托盘
        self.init_tray()
        
        # 创建控制窗体
        self.control_window = ControlWindow()
        self.control_window.move(self.x(), self.y() - self.control_window.height())
        self.control_window.show()

        # 连接控制窗口的状态改变信号
        self.control_window.state_changed.connect(self.on_control_state_changed)
        
        # 监听主窗口位置变化
        self.windowHandle().windowStateChanged.connect(self.update_control_window_position)
        
        # 连接信号到处理函数
        self.progress_signal.connect(self.handle_progress_update)
        
        # 启动游戏检查线程
        from mainfunctions import check_for_new_game
        import threading
        self.game_check_thread = threading.Thread(target=check_for_new_game, args=(self.progress_signal,), daemon=True)
        self.game_check_thread.start()
        
        # 初始化时设置为锁定状态（不可点击）
        # 使用延迟调用，确保窗口已完全初始化
        QTimer.singleShot(100, lambda: self.on_control_state_changed(False))

    def update_control_window_position(self):
        # 保持控制窗口与主窗口位置同步
        self.control_window.move(self.x(), self.y() - self.control_window.height())

    def moveEvent(self, event):
        """鼠标移动事件，用于更新控制窗口位置"""
        super().moveEvent(event)
        if hasattr(self, 'control_window'):
            self.update_control_window_position()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('SC2 Timer')
        self.setGeometry(0, 300, 167, 30)  # 调整初始窗口位置，x坐标设为0
        
        # 设置窗口样式 - 不设置点击穿透，这将由on_control_state_changed方法控制
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool |  # 不在任务栏显示
            Qt.MSWindowsFixedSizeDialogHint  # 禁用窗口自动调整
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setAttribute(Qt.WA_NoSystemBackground)  # 禁用系统背景
        
        # 添加键盘事件监听变量
        self.ctrl_pressed = False
        
        # 创建主容器控件
        self.main_container = QWidget(self)
        self.main_container.setGeometry(0, 0, 167, 50)  # 调整主容器初始高度
        self.main_container.setStyleSheet('background-color: rgba(43, 43, 43, 96)')
        
        # 创建时间显示标签
        self.time_label = QLabel(self.current_time, self.main_container)
        self.time_label.setFont(QFont('Consolas', 11))
        self.time_label.setStyleSheet('color: rgb(0, 255, 128); background-color: transparent')
        self.time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.time_label.setGeometry(10, 40, 120, 20)  # 将宽度从100px增加到120px
        self.time_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 添加鼠标事件穿透

        # 创建表格显示区
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        self.table_area = QTableWidget(self.main_container)
        self.table_area.setGeometry(0, 65, 167, 185)  # 保持表格区域位置不变
        self.table_area.setColumnCount(2)
        self.table_area.horizontalHeader().setVisible(False)  # 隐藏水平表头
        self.table_area.setColumnWidth(0, 50)  # 设置时间列的固定宽度
        self.table_area.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.table_area.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置表格只读
        self.table_area.setSelectionBehavior(QTableWidget.SelectRows)  # 设置选择整行
        self.table_area.setShowGrid(False)  # 隐藏网格线
        self.table_area.setStyleSheet('''
            QTableWidget { 
                border: none; 
                background-color: transparent; 
                padding-left: 5px; 
            } 
            QTableWidget::item { 
                padding: 0px;
                text-align: left;
                height: 14px;
            } 
            QTableWidget::item:selected { 
                background-color: transparent; 
                color: rgb(255, 255, 255); 
                border: none; 
                text-align: left;
            } 
            QTableWidget::item:focus { 
                background-color: transparent; 
                color: rgb(255, 255, 255); 
                border: none; 
                text-align: left;
            }''')

        # 设置表格的滚动条策略
        self.table_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
 
        self.setFixedSize(167, 250)  # 固定窗口大小为250
 
        
        # 调整主窗口大小以适应新添加的控件
        self.main_container.setGeometry(0, 0, 167, 335)  # 调整容器高度
        
        # 创建地图标签
        self.map_label = QLabel('地图', self.main_container)
        self.map_label.setFont(QFont('Arial', 9))  # 修改字体大小为9pt
        self.map_label.setStyleSheet('color: white; background-color: transparent')
        self.map_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.map_label.setGeometry(10, 5, 30, 30)
        self.map_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 添加鼠标事件穿透
    
        # 创建下拉框
        self.combo_box = QComboBox(self.main_container)
        self.combo_box.setGeometry(40, 5, 117, 30)
        self.combo_box.setFont(QFont('Arial', 9))  # 修改字体大小为9pt
        self.combo_box.setStyleSheet(    '''
        QComboBox {
            color: rgb(0, 191, 255);
            background-color: rgba(43, 43, 43, 200);
            border: none;
            border-radius: 5px;
            padding: 5px;
            font-size: 9pt;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 6px solid white;
            width: 0;
            height: 0;
            margin-right: 5px;
        }
        /* 下拉列表整体样式 */
        QComboBox QListView {
            background-color: white;      /* 整个下拉背景设为白色 */
            border: 1px solid #cccccc;
            border-radius: 3px;
            outline: none;
            color: black;                /* 默认文字颜色设为黑色 */
        }
        /* 单个item默认样式 */
        QComboBox QListView::item {
            height: 25px;               /* 行高设置 */
            padding: 5px;
            background-color: white;    /* item背景白色 */
            color: black;               /* 文字颜色黑色 */
        }
        /* 鼠标悬停样式 */
        QComboBox QListView::item:hover {
            background-color: #f0f0f0;  /* 浅灰色悬停背景 */
            color: black;
        }
        /* 选中项样式 */
        QComboBox QListView::item:selected {
            background-color: #0096ff;  /* 选中背景蓝色 */
            color: white;               /* 选中文字白色 */
        }
        /* 下拉滚动条样式 */
        QComboBox QScrollBar:vertical {
            width: 8px;
            background: rgba(200, 200, 200, 100);
        }
        QComboBox QScrollBar::handle:vertical {
            background: rgba(150, 150, 150, 150);
            border-radius: 4px;
        }''')
        # 强制设置下拉列表的窗口标志
        self.combo_box.view().window().setAttribute(Qt.WA_TranslucentBackground, False)
        # 加载resources文件夹下的文件
        # 首先尝试在当前目录查找resources目录
        current_dir = os.getcwd()
        resources_dir = os.path.join(current_dir, 'resources')
        
        # 如果当前目录没有resources目录，则尝试在程序目录查找
        if not os.path.exists(resources_dir):
            self.logger.info(f'当前目录下未找到资源目录，尝试在程序目录查找')
            resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
            
        if not os.path.exists(resources_dir):
            self.logger.error(f'资源目录不存在: {resources_dir}')
            files = []
        else:
            self.logger.info(f'使用资源目录: {resources_dir}')
            files = [f for f in os.listdir(resources_dir) if os.path.isfile(os.path.join(resources_dir, f))]
        self.combo_box.addItems(files)
        
        # 连接下拉框选择变化事件
        self.combo_box.currentTextChanged.connect(self.on_map_selected)
        
        # 如果有文件，自动加载第一个
        if files:
            self.on_map_selected(files[0])
        
        # 调整时间标签的位置和高度
        self.time_label.setGeometry(10, 40, 100, 20)
        
        # 显示窗口并强制置顶
        self.show()
        if sys.platform == 'win32':
            import win32gui
            import win32con
            hwnd = int(self.winId())
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
    
    def update_game_time(self):
        """更新游戏时间显示"""
        self.logger.debug('开始更新游戏时间')
        start_time = time.time()
        
        try:
            # 从全局变量获取游戏时间
            from mainfunctions import most_recent_playerdata
            if most_recent_playerdata and isinstance(most_recent_playerdata, dict):
                game_time = most_recent_playerdata.get('time', 0)
                self.logger.debug(f'从全局变量获取的原始时间数据: {game_time}')
                
                # 格式化时间显示
                hours = int(float(game_time) // 3600)
                minutes = int((float(game_time) % 3600) // 60)
                seconds = int(float(game_time) % 60)
                
                # 修改格式化逻辑：有小时时显示HH:MM:SS，没有小时时只显示MM:SS
                if hours > 0:
                    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    formatted_time = f"{minutes:02d}:{seconds:02d}"
                    
                self.current_time = formatted_time
                self.time_label.setText(formatted_time)
                
                # 更新地图信息（如果有）
                map_name = most_recent_playerdata.get('map')
                if map_name:
                    self.logger.debug(f'地图信息更新: {map_name}')
                
                self.logger.debug(f'游戏时间更新: {formatted_time} (格式化后), 原始数据: {game_time}')
                
                # 根据当前时间调整表格滚动位置和行颜色
                try:
                    # 将当前时间转换为分钟数，以便于比较
                    current_minutes = hours * 60 + minutes
                    current_seconds = current_minutes * 60 + seconds
                    
                    # 遍历表格找到最接近的时间点并更新颜色
                    closest_row = 0
                    min_diff = float('inf')
                    
                    for row in range(self.table_area.rowCount()):
                        time_item = self.table_area.item(row, 0)
                        event_item = self.table_area.item(row, 1)
                        if time_item and time_item.text():
                            try:
                                # 解析表格中的时间（格式可能是MM:SS或HH:MM:SS）
                                time_parts = time_item.text().split(':')
                                row_seconds = 0
                                if len(time_parts) == 2:  # MM:SS格式
                                    row_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
                                elif len(time_parts) == 3:  # HH:MM:SS格式
                                    row_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
                                
                                # 计算时间差（秒）
                                diff = abs(current_seconds - row_seconds)
                                if diff < min_diff:
                                    min_diff = diff
                                    closest_row = row
                                
                                # 根据时间差设置颜色
                                if row_seconds < current_seconds:  # 已过去的时间
                                    time_item.setForeground(QBrush(QColor(128, 128, 128, 255)))
                                    if event_item:
                                        event_item.setForeground(QBrush(QColor(128, 128, 128, 255)))
                                elif abs(row_seconds - current_seconds) <= 30:  # 即将到来的时间（30秒内）
                                    time_item.setForeground(QBrush(QColor(0, 191, 255)))
                                    if event_item:
                                        event_item.setForeground(QBrush(QColor(0, 191, 255)))
                                        # 显示完整的时间和事件信息作为Toast提醒
                                        # 只有当Toast不可见时才显示，避免重复触发
                                        if not self.toast_label.isVisible():
                                            toast_message = f"{time_item.text()} {event_item.text()}"
                                            self.show_toast(toast_message, config.TOAST_DURATION)
                                else:  # 未来的时间
                                    time_item.setForeground(QBrush(QColor(255, 255, 255)))
                                    if event_item:
                                        event_item.setForeground(QBrush(QColor(255, 255, 255)))
                            except ValueError:
                                continue
                    
                    # 计算滚动位置，使最接近的时间点位于可见区域中间
                    visible_rows = self.table_area.height() // self.table_area.rowHeight(0)
                    scroll_position = max(0, closest_row - (visible_rows // 2))
                    
                    # 设置滚动位置
                    self.table_area.verticalScrollBar().setValue(scroll_position)
                except Exception as e:
                    self.logger.error(f'调整表格滚动位置和颜色失败: {str(e)}')

            else:
                self.logger.debug('未获取到有效的游戏时间数据')
                self.time_label.setText("00:00")
                
        except Exception as e:
            self.logger.error(f'获取游戏时间失败: {str(e)}\n{traceback.format_exc()}')
            # 如果获取失败，显示默认时间
            self.time_label.setText("00:00")
        
        self.logger.debug(f'本次更新总耗时：{time.time() - start_time:.2f}秒\n')
    
    
    def init_tray(self):
        """初始化系统托盘"""
        # 如果已存在托盘图标，先删除它
        if hasattr(self, 'tray_icon') and self.tray_icon is not None:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.logger.info('已删除旧的托盘图标')

        self.tray_icon = QSystemTrayIcon(self)
        
        # 修改图标路径获取方式
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.dirname(__file__))
            
        icon_path = os.path.join(base_path, 'ico', 'fav.ico')
        self.logger.info(f'加载托盘图标: {icon_path}')
        
        if not os.path.exists(icon_path):
            self.logger.error(f'托盘图标文件不存在: {icon_path}')
        else:
            self.logger.info('找到托盘图标文件')
            
        self.tray_icon.setIcon(QIcon(icon_path))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction("显示", self)
        quit_action = QAction("退出", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        # 设置托盘菜单的位置
        def show_context_menu(reason):
            if reason == QSystemTrayIcon.Context:  # 右键点击
                if sys.platform == 'win32':
                    import win32gui
                    try:
                        # 获取鼠标位置
                        cursor_pos = win32gui.GetCursorPos()
                        
                        # 调整菜单位置
                        menu_x = cursor_pos[0]
                        menu_y = cursor_pos[1] - tray_menu.sizeHint().height()
                        
                        # 确保菜单不会超出屏幕
                        screen = QApplication.primaryScreen().geometry()
                        if menu_y < 0:
                            menu_y = cursor_pos[1]
                        if menu_x + tray_menu.sizeHint().width() > screen.width():
                            menu_x = screen.width() - tray_menu.sizeHint().width()
                            
                        tray_menu.exec_(QPoint(menu_x, menu_y))
                    except Exception as e:
                        self.logger.error(f'显示托盘菜单时出错: {str(e)}')
                        # 如果出错，回退到默认位置
                        tray_menu.exec_(QCursor.pos())
                else:
                    # 非Windows系统使用默认位置
                    tray_menu.exec_(QCursor.pos())
        
        # 连接托盘图标的点击事件
        self.tray_icon.activated.connect(show_context_menu)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.logger.info('已创建新的托盘图标')

    def mousePressEvent(self, event):
        """鼠标按下事件，用于实现窗口拖动"""
        # 检查窗口是否处于可点击状态（非锁定状态）
        is_clickable = not self.testAttribute(Qt.WA_TransparentForMouseEvents)
        
        if is_clickable:  # 窗口可点击时
            if event.button() == Qt.LeftButton:
                # 获取点击位置相对于窗口的坐标
                pos = event.pos()
                # 检查点击位置是否在地图标签区域内
                map_area = QRect(10, 5, 30, 30)  # 只允许通过地图标签区域拖动
                if map_area.contains(pos):
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    self.is_dragging = True  # 添加拖动状态标记
                    event.accept()
                else:
                    event.ignore()
        else:  # 窗口不可点击时，保持原有的Ctrl按住才能拖动的逻辑
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
        """处理控制窗口状态改变事件
        
        Args:
            unlocked: 是否解锁，True表示解锁状态（可点击），False表示锁定状态（不可点击）
        """
        self.logger.info(f'控制窗口状态改变: unlocked={unlocked}')
        
        # 在Windows平台上，直接使用Windows API设置窗口样式
        if sys.platform == 'win32':
            try:
                import ctypes
                from ctypes import wintypes
                
                # 定义Windows API常量
                GWL_EXSTYLE = -20
                WS_EX_TRANSPARENT = 0x00000020
                WS_EX_LAYERED = 0x00080000
                
                # 获取窗口句柄
                hwnd = int(self.winId())
                
                # 获取当前窗口样式
                ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                self.logger.info(f'当前窗口样式: {ex_style}')
                
                if not unlocked:  # 锁定状态（不可点击）
                    # 添加透明样式
                    new_ex_style = ex_style | WS_EX_TRANSPARENT | WS_EX_LAYERED
                    self.logger.info(f'设置窗口为不可点击状态，样式从 {ex_style} 更改为 {new_ex_style}')
                else:  # 解锁状态（可点击）
                    # 移除透明样式，但保留WS_EX_LAYERED
                    new_ex_style = (ex_style & ~WS_EX_TRANSPARENT) | WS_EX_LAYERED
                    self.logger.info(f'设置窗口为可点击状态，样式从 {ex_style} 更改为 {new_ex_style}')
                
                # 设置新样式
                result = ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_ex_style)
                if result == 0:
                    error = ctypes.windll.kernel32.GetLastError()
                    self.logger.error(f'SetWindowLongW失败，错误码: {error}')
                    
                # 强制窗口重绘
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0, 
                    0x0001 | 0x0002 | 0x0004 | 0x0020  # SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED
                )
                
            except Exception as e:
                self.logger.error(f'设置Windows平台点击穿透失败: {str(e)}')
                self.logger.error(traceback.format_exc())
        else:
            # 非Windows平台使用Qt的方法
            self.hide()  # 先隐藏窗口
            
            if not unlocked:  # 锁定状态（不可点击）
                self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                self.logger.info('已设置窗口为不可点击状态')
            else:  # 解锁状态（可点击）
                self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                self.logger.info('已设置窗口为可点击状态')
                
            self.show()  # 重新显示窗口
    
    def closeEvent(self, event):
        """关闭事件"""
        event.ignore()
        self.hide()
        
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

    def on_map_selected(self, map_name):
        """处理地图选择变化事件"""
        # 检查是否是由用户手动选择触发的
        if not self.manual_map_selection and self.sender() == self.combo_box:
            self.manual_map_selection = True
            self.logger.info('用户手动选择了地图')
        
        try:
            # 获取地图文件的完整路径
            # 首先尝试在当前目录查找resources目录
            current_dir = os.getcwd()
            resources_dir = os.path.join(current_dir, 'resources')
            
            # 如果当前目录没有resources目录，则尝试在程序目录查找
            if not os.path.exists(resources_dir):
                self.logger.info(f'当前目录下未找到资源目录，尝试在程序目录查找')
                resources_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
            
            map_file_path = os.path.join(resources_dir, map_name)
            self.logger.info(f'尝试加载地图文件: {map_file_path}')
            
            # 读取地图文件内容
            if os.path.exists(map_file_path):
                with open(map_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.logger.info(f'成功读取地图文件内容: {map_name}\n文件内容:\n{content}')
                
                # 清空表格现有内容
                self.table_area.setRowCount(0)
                self.logger.info('已清空表格现有内容')
                
                # 按行分割内容，过滤掉空行和只包含空白字符的行
                lines = [line.strip() for line in content.split('\n') if line and not line.isspace()]
                self.logger.info('解析到的有效行数: {}'.format(len(lines)))
                self.logger.info('解析后的行内容:\n{}'.format('\n'.join(lines)))
                
                # 设置表格行数
                self.table_area.setRowCount(len(lines))
                self.logger.info(f'设置表格行数为: {len(lines)}')
                
                # 填充表格内容
                for row, line in enumerate(lines):
                    # 按tab分隔符拆分时间和事件
                    parts = line.split('\t')
                    self.logger.info(f'处理第{row+1}行: {line}, 拆分结果: {parts}')
                    
                    if len(parts) >= 2:
                        # 创建时间单元格
                        time_item = QTableWidgetItem(parts[0])
                        time_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        time_item.setForeground(QBrush(QColor(255, 255, 255)))  # 修改时间列文字颜色为白色
                        self.table_area.setItem(row, 0, time_item)
                        
                        # 创建事件单元格
                        event_item = QTableWidgetItem(parts[1])
                        event_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        event_item.setForeground(QBrush(QColor(255, 255, 255)))  # 设置事件列文字颜色为白色
                        self.table_area.setItem(row, 1, event_item)
                        
                        self.logger.info(f'已添加表格内容 - 行{row+1}: 时间={parts[0]}, 事件={parts[1]}')
                    else:
                        # 对于不符合格式的行，将整行内容显示在事件列
                        event_item = QTableWidgetItem(line)
                        event_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        event_item.setForeground(QBrush(QColor(255, 255, 255)))  # 设置事件列文字颜色为白色
                        
                        self.table_area.setItem(row, 0, event_item)
                        self.table_area.setSpan(row, 0, 1, 2)  # 将当前行的两列合并为一列

                        self.logger.info(f'已添加不规范行内容到合并单元格 - 行{row+1}: {line}')
                
                # 调整列宽
                self.table_area.setColumnWidth(0, 50)  # 时间列固定宽度
                self.table_area.setColumnWidth(1, 107)  # 事件列宽度为剩余空间
                self.logger.info('已完成表格列宽调整')
                
                # 验证表格内容
                row_count = self.table_area.rowCount()
                self.logger.info(f'最终表格行数: {row_count}')
                for row in range(row_count):
                    time_item = self.table_area.item(row, 0)
                    event_item = self.table_area.item(row, 1)
                    time_text = time_item.text() if time_item else 'None'
                    event_text = event_item.text() if event_item else 'None'
                    self.logger.info(f'验证第{row+1}行内容: 时间={time_text}, 事件={event_text}')
                
            else:
                self.logger.error(f'地图文件不存在: {map_name}')
                return
            
        except Exception as e:
            self.logger.error(f'加载地图文件时出错: {str(e)}')

    def init_toast(self):
        """初始化Toast提示组件"""
        # 创建Toast标签
        self.toast_label = QLabel(self)
        self.toast_label.setFont(QFont('Arial', config.TOAST_FONT_SIZE))  # 设置字体大小为24
        self.toast_label.setStyleSheet(
            'QLabel {'
            '   color: ' + config.TOAST_FONT_COLOR + ';'  # 使用配置文件中的颜色
            '   padding: 10px;'
            '   background-color: transparent;'
            '   border: none;'
            '}'
        )
        self.toast_label.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.hide()
        
        # 设置Toast标签属性
        self.toast_label.setAttribute(Qt.WA_TransparentForMouseEvents)  # 使标签不接收鼠标事件
        self.toast_label.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        # 创建Toast定时器
        self.toast_timer = QTimer(self)
        self.toast_timer.timeout.connect(self.hide_toast)
           
    def show_toast(self, message, duration=None):
        """显示Toast提示"""
        # 如果没有指定duration，使用配置文件中的默认值
        if duration is None:
            duration = config.TOAST_DURATION
        # 设置Toast文本
        self.toast_label.setText(message)
        
        # 调整Toast大小以适应文本
        self.toast_label.adjustSize()
        
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        
        # 计算Toast位置（屏幕水平中心，根据配置的垂直位置）
        x = screen.center().x() - self.toast_label.width() // 2
        y = int(self.height() * config.TOAST_POSITION)
        self.toast_label.move(x, y)
        
        # 显示Toast
        self.toast_label.show()
        
        # 设置定时器
        self.toast_timer.start(duration)
    
    def hide_toast(self):
        """隐藏Toast提示"""
        self.toast_label.hide()
        self.toast_timer.stop()
    
    def on_text_double_click(self, event):
        """处理表格区域双击事件"""
        if event.button() == Qt.LeftButton:
            selected_items = self.table_area.selectedItems()
            if selected_items:
                # 获取选中行的完整内容
                row = selected_items[0].row()
                time_item = self.table_area.item(row, 0)
                event_item = self.table_area.item(row, 1)
                if time_item and event_item:
                    time_text = time_item.text().strip()
                    event_text = event_item.text().strip()
                    selected_text = f"{time_text} {event_text}" if time_text else event_text
                    self.show_toast(selected_text, config.TOAST_DURATION)  # 设置5000毫秒（5秒）后自动消失
            event.accept()
            
    def keyPressEvent(self, event):
        """键盘按下事件处理"""
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = True
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # 禁用鼠标事件穿透
            event.accept()

    def keyReleaseEvent(self, event):
        """键盘释放事件处理"""
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 启用鼠标事件穿透
            event.accept()

    def showEvent(self, event):
        """窗口显示事件，确保窗口始终保持在最上层"""
        super().showEvent(event)
        if sys.platform == 'win32':
            import win32gui
            import win32con
            hwnd = int(self.winId())
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

def main():
    app = QApplication(sys.argv)
    window = TimerWindow()
    window.start_timer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()