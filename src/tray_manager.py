import os
import sys
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication
from fileutil import get_resources_dir
import config
from logging_util import get_logger

class TrayManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.logger = get_logger(__name__)
        self.tray_icon = None
        self.init_tray()

    def init_tray(self):
        """初始化系统托盘"""
        # 如果已存在托盘图标，先删除它
        if self.tray_icon is not None:
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
            self.logger.info('已删除旧的托盘图标')

        self.tray_icon = QSystemTrayIcon(self.parent)
        
        # 修改图标路径获取方式
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            base_path = os.path.dirname(sys.executable)
            self.logger.info(f'准备修改tray，检测到exe环境：{base_path}')
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.dirname(__file__))
            self.logger.info(f'准备修改tray，检测到开发环境：{base_path}')
            
        icon_path = os.path.join(base_path, 'ico', 'fav.ico')
        self.logger.info(f'加载托盘图标: {icon_path}')
        
        if not os.path.exists(icon_path):
            self.logger.error(f'托盘图标文件不存在: {icon_path}')
        else:
            self.logger.info('找到托盘图标文件')
            
        self.tray_icon.setIcon(QIcon(icon_path))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction(self.parent.get_text("show_action"), self.parent)
        quit_action = QAction(self.parent.get_text("quit_action"), self.parent)
        
        show_action.triggered.connect(self.parent.show)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        # 添加语言设置菜单
        language_menu = QMenu(self.parent.get_text("language_menu"), self.parent)
        maps_dir = get_resources_dir('resources', 'maps')
        for lang_dir in os.listdir(maps_dir):
            if os.path.isdir(os.path.join(maps_dir, lang_dir)) and lang_dir not in ['.', '..']:
                language_action = QAction(lang_dir, self.parent)
                # 为当前选中的语言添加标记
                if lang_dir == config.current_language:
                    language_action.setText(f"{lang_dir}✓")
                language_action.triggered.connect(lambda checked, lang=lang_dir: self.parent.on_language_changed(lang))
                language_menu.addAction(language_action)
        
        tray_menu.addAction(show_action)
        tray_menu.addMenu(language_menu)
        tray_menu.addAction(quit_action)
        
        # 设置托盘菜单的位置
        def show_context_menu(reason):
            if reason in [QSystemTrayIcon.Context, QSystemTrayIcon.Trigger]:  # 右键点击或左键点击
                # 获取鼠标当前位置
                cursor_pos = QCursor.pos()
                self.logger.info(f'鼠标当前位置: x={cursor_pos.x()}, y={cursor_pos.y()}')
                
                # 获取菜单尺寸
                menu_width = tray_menu.sizeHint().width()
                menu_height = tray_menu.sizeHint().height()
                self.logger.info(f'菜单尺寸: width={menu_width}, height={menu_height}')
                
                # 计算菜单位置，在鼠标右上方显示
                menu_x = cursor_pos.x()
                menu_y = cursor_pos.y() - menu_height
                self.logger.info(f'初始计算的菜单位置: x={menu_x}, y={menu_y}')
                
                # 获取屏幕尺寸
                screen_width, screen_height = self.parent.get_screen_resolution()
                self.logger.info(f'屏幕尺寸: width={screen_width}, height={screen_height}')
                
                # 确保菜单不会超出屏幕边界
                if menu_x + menu_width > screen_width:
                    menu_x = screen_width - menu_width
                    self.logger.info(f'菜单超出右边界，调整后的x坐标: {menu_x}')
                if menu_y < 0:
                    menu_y = 0
                    self.logger.info(f'菜单超出上边界，调整后的y坐标: {menu_y}')
                
                self.logger.info(f'最终菜单显示位置: x={menu_x}, y={menu_y}')
                # 显示菜单
                tray_menu.exec_(QPoint(menu_x, menu_y))
        
        # 连接托盘图标的点击事件
        self.tray_icon.activated.connect(show_context_menu)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.logger.info('已创建新的托盘图标')