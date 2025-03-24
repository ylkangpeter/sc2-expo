from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QLabel, QRadioButton, QButtonGroup, QHBoxLayout, QVBoxLayout, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPoint, QTimer, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QCursor, QColor, QPalette, QMovie
import os
import sys
import logging
from PyQt5.QtWidgets import QApplication
from config import avatar
from config import WIKI_URL
import ast
from PyQt5.QtCore import pyqtSignal

# 自定义提示窗口类，替代QToolTip
class CustomTooltip(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool  # 不在任务栏显示
        )
        # self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setAlignment(Qt.AlignCenter)
        
        # 设置样式
        self.setStyleSheet("""
            QLabel {
                color: black;
                background-color: #FFFFDC;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
        """)
        
        # 创建计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide)
        
    def showText(self, pos, text, duration=5000):
        # 停止当前计时器
        if self.timer.isActive():
            self.timer.stop()
            
        # 设置文本并调整大小
        self.setText(text)
        self.adjustSize()
        
        # 移动到指定位置
        self.move(pos.x() - self.width() // 2, pos.y() - self.height() - 10)
        
        # 显示并启动计时器
        self.show()
        self.timer.start(duration)

class CommanderSelector(QWidget):
    region_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)
        self.commander_urls = {}
        self.load_commander_urls()
        # 从配置文件中读取默认region
        self.selected_region = self.commander_urls.get('current_region', 'KR')
        
        # 创建自定义提示窗口
        self.tooltip = CustomTooltip()
        
        # 初始化窗口状态
        self.is_visible = True  # 控制窗口的显示/隐藏状态
        self.is_open = False    # 控制窗口的打开/关闭状态
        
        self.init_ui()
        
    def load_commander_urls(self):
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(base_path, 'resources', 'commander', 'replacement.conf')
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 解析配置文件内容
                config_dict = {}
                exec(content, {}, config_dict)
                # 移除内置变量
                config_dict.pop('__builtins__', None)
                self.commander_urls = config_dict
        except Exception as e:
            self.logger.error(f"加载指挥官配置文件失败: {str(e)}")
            self.commander_urls = {}

    def init_ui(self):
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool  # 不在任务栏显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景

        # 设置窗口大小
        self.setFixedSize(950, 450)  # 增加高度以容纳区域选择按钮和提示文本

        # 创建主容器
        self.main_container = QWidget(self)
        self.main_container.setGeometry(0, 0, 950, 450)
        self.main_container.setStyleSheet('background-color: rgba(43, 43, 43, 200); border-radius: 10px; border: none;')

        # 创建关闭按钮容器
        close_button_container = QLabel(self.main_container)
        close_button_container.setGeometry(0, 0, 950, 35)
        close_button_container.setStyleSheet('background-color: transparent;')

        # 创建关闭按钮
        self.close_button = QPushButton('×', close_button_container)
        self.close_button.setGeometry(920, 5, 25, 25)
        self.close_button.setStyleSheet('''
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                font-size: 30px;
            }
            QPushButton:hover {
                color: rgb(255, 100, 100);
            }
        ''')
        self.close_button.clicked.connect(self.toggle_window)

        # 创建区域选择容器
        region_container = QLabel(self.main_container)
        region_container.setGeometry(0, 30, 950, 35)
        region_container.setStyleSheet('background-color: transparent;')

        # 创建按钮组以实现单选功能
        self.region_group = QButtonGroup(self)

        # 计算单选按钮的位置
        regions = ["CN", "KR", "EU", "US"]
        button_width = 60
        button_height = 25
        total_width = len(regions) * button_width + (len(regions) - 1) * 20  # 20是按钮间距
        start_x = (950 - total_width) // 2

        # 创建四个区域单选按钮
        for i, region in enumerate(regions):
            btn = QPushButton(region, region_container)
            btn.setGeometry(start_x + i * (button_width + 20), 10, button_width, button_height)
            btn.setFont(QFont('Arial', 11))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, r=region: self.on_region_changed(r))
            btn.setStyleSheet('''
                QPushButton {
                    color: rgb(200, 200, 200);
                    background-color: rgba(43, 43, 43, 200);
                    border: none;
                    border-radius: 3px;
                    padding: 0px;
                }
                QPushButton:checked {
                    color: rgb(0, 191, 255);
                    background-color: rgba(0, 191, 255, 30);
                }
                QPushButton:hover {
                    background-color: rgba(0, 191, 255, 20);
                }
            ''')
            if region == self.selected_region:
                btn.setChecked(True)
            self.region_group.addButton(btn, i)

        # 创建分割线容器
        separator_container = QLabel(self.main_container)
        separator_container.setGeometry(50, 80, 850, 1)
        separator_container.setStyleSheet('background-color: rgba(218, 165, 32, 150);')

        # 创建头像网格容器
        avatar_container = QLabel(self.main_container)
        avatar_container.setGeometry(0, 85, 950, 220)
        avatar_container.setStyleSheet('background-color: transparent;')

        # 创建网格布局
        self.grid_layout = QGridLayout(avatar_container)
        self.grid_layout.setSpacing(1)
        self.grid_layout.setContentsMargins(1, 1, 1, 1)

        # 获取指挥官图标路径
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(__file__))

        commander_dir = os.path.join(base_path, 'ico', 'commander')


        # 根据avatar数组添加指挥官按钮到网格
        for row_index, row_commanders in enumerate(avatar):
            for col_index, commander in enumerate(row_commanders):
                # 创建金色光晕的阴影效果
                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(15)  # 模糊半径，控制光晕的大小
                shadow.setOffset(0, 0)  # 阴影的偏移量，(0, 0) 表示没有偏移
                shadow.setColor(QColor(255, 215, 0))  # 金色的颜色
        
                btn = QPushButton()
                btn.setFixedSize(75, 75)
                icon_path = os.path.join(commander_dir, f'{commander}.png')
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(btn.size())
                btn.commander_name = commander
                btn.setGraphicsEffect(shadow)
                btn.mouseDoubleClickEvent = lambda event, b=btn: self.on_commander_double_clicked(event, b)
                btn.setStyleSheet('''
                    QPushButton {
                        border-radius: 5px;
                        padding: 0px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 215, 0, 30);
                        border: 0.5px solid rgba(255, 215, 0, 80);
                    }
                ''')
                self.grid_layout.addWidget(btn, row_index, col_index)
        
        # 添加随机选择按钮
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 100, 255))
        
        random_btn = QPushButton()
        random_btn.setFixedSize(75, 75)
        random_icon_path = os.path.join(commander_dir, 'random.gif')

        # 创建 QLabel 来显示 GIF
        label = QLabel(random_btn)
        label.setGeometry(0, 0, 75, 75)  # 设置 QLabel 的大小和位置
        label.setAlignment(Qt.AlignCenter) 
        movie = QMovie(random_icon_path)  # 加载 GIF 动画
        movie.setScaledSize(QSize(80, 80)) 
        label.setMovie(movie)  # 将 GIF 动画设置到 QLabel 上
        movie.start()  # 启动动画播放

        random_btn.commander_name = 'random'
        random_btn.setGraphicsEffect(shadow)
        random_btn.mouseDoubleClickEvent = lambda event, b=random_btn: self.on_random_commander_clicked(event, b)
        random_btn.setStyleSheet('''
            QPushButton {
                border-radius: 5px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 215, 0, 30);
                border: 0.5px solid rgba(255, 215, 0, 80);
            }
        ''')
        self.grid_layout.addWidget(random_btn, len(avatar)-1, len(avatar[-1]))

        # 创建提示文本容器
        hint_container = QLabel(self.main_container)
        hint_container.setGeometry(0, 300, 950, 140)
        hint_container.setStyleSheet('background-color: transparent')

        # 创建提示文本标签
        hint_label = QLabel(hint_container)
        hint_label.setGeometry(20, 10, 910, 64)
        hint_label.setText('免责声明：本软件相关技术方案都来源于公开网络，仅供学习交流使用，不构成任何形式的盈利，如产生封禁等问题后果自负。 作者: pppppp\n\n双击 头像 复制指令。  粘贴到聊天频道中-> 点击发送 -> 双击发送的链接 -> 进入替换图。\n选择随机替换时可以在config配置文件中排除不想要的指挥官。')
        hint_label.setStyleSheet('color: white; font-size: 13px; line-height: 1.5;')
        hint_label.setWordWrap(True)
        hint_label.setAlignment(Qt.AlignCenter)

        # 创建链接标签
        link_label = QLabel(hint_container)
        link_label.setGeometry(20, 94, 910, 20)
        link_label.setText('<a href="'+WIKI_URL+'" style="color: rgb(0, 191, 255); text-decoration: none;">--访问突变列表网页--</a>')
        link_label.setStyleSheet('font-size: 13px; a { color: rgb(0, 191, 255); } a:visited { color: rgb(0, 191, 255); }')
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setOpenExternalLinks(True)

    def showEvent(self, event):
        if not self.is_visible:
            self.hide()
            return
        self.center()
        super().showEvent(event)
        
    def set_visibility(self, visible):
        """设置窗口的显示/隐藏状态"""
        self.is_visible = visible
        if not visible:
            self.hide()
        elif self.is_open:
            self.show()
            
    def toggle_window(self):
        """切换窗口的打开/关闭状态"""
        self.is_open = not self.is_open
        if self.is_open and self.is_visible:
            self.show()
        else:
            self.hide()

    def center(self):
        # 获取父窗口所在的屏幕
        parent = self.parent()
        screens = QApplication.screens()
        parent_center = parent.geometry().center()
        
        # 找到父窗口所在的屏幕
        current_screen = None
        for screen in screens:
            if screen.geometry().contains(parent_center):
                current_screen = screen
                break
        
        if not current_screen:
            current_screen = QApplication.primaryScreen()
        
        # 获取屏幕几何信息并计算居中位置
        screen_geometry = current_screen.geometry()
        x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
        y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
        
        self.logger.info(f"窗口将移动到屏幕中心: ({x}, {y})")
        self.move(x, y)
        
    def on_region_changed(self, region):
        self.selected_region = region
        self.region_changed.emit(region)
        
        # 更新配置文件中的current_region
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'commander', 'replacement.conf')
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新current_region的值
            if 'current_region = ' in content:
                content = content.replace(f"current_region = '{self.commander_urls.get('current_region', 'KR')}'\n", f"current_region = '{region}'\n")
                
                # 写入更新后的内容
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                # 更新commander_urls中的current_region
                self.commander_urls['current_region'] = region
        except Exception as e:
            self.logger.error(f"更新区域配置失败: {str(e)}")
        
    def on_commander_double_clicked(self, event, btn):
        commander = btn.commander_name
        pos = QCursor.pos()
        
        if commander in self.commander_urls:
            url = self.commander_urls[commander].get(self.selected_region, '')
            if url:
                # 复制URL到剪贴板
                clipboard = QApplication.clipboard()
                clipboard.setText(f"替换为{commander}指挥官: {url}")
                # 显示新提示
                self.tooltip.showText(pos, f"替换为 {commander} 指挥官", 5000)
            else:
                # 显示新提示
                self.tooltip.showText(pos, f"对应指挥官未配置，请修改配置文件", 5000)
        else:
            # 显示新提示
            self.tooltip.showText(pos, f"对应指挥官未配置，请修改配置文件", 5000)
            
    def on_random_commander_clicked(self, event, btn):
        import random
        from config import BLACK_LIST
        pos = QCursor.pos()
        
        # 获取所有可用的指挥官（排除黑名单中的指挥官）
        available_commanders = []
        for row in avatar:
            for commander in row:
                if commander not in BLACK_LIST and commander in self.commander_urls:
                    url = self.commander_urls[commander].get(self.selected_region, '')
                    if url:
                        available_commanders.append(commander)
        
        if available_commanders:
            # 随机选择一个指挥官
            selected_commander = random.choice(available_commanders)
            url = self.commander_urls[selected_commander].get(self.selected_region, '')
            
            # 复制URL到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(f"替换为{selected_commander}指挥官: {url}")
            # 显示新提示
            self.tooltip.showText(pos, f"随机替换为 {selected_commander} 指挥官", 5000)
        else:
            # 显示新提示
            self.tooltip.showText(pos, "没有可用的指挥官", 5000)