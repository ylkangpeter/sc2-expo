from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap
import os
import traceback
import config
from fileutil import get_resources_dir
from mainfunctions import get_game_screen, get_troop_from_game
from troop_util import TroopLoader

class ToastManager:
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.logger = parent_window.logger
        self.init_toast()

    def init_toast(self):
        self.troop_loader = TroopLoader()
        """初始化Toast提示组件"""
        # 创建Toast标签
        self.toast_label = QLabel(self.parent)
        self.toast_label.setFont(QFont('Arial', config.TOAST_FONT_SIZE))
        self.toast_label.setStyleSheet(
            'QLabel {'
            '   color: ' + config.TOAST_FONT_COLOR + ';'
            '   padding: 10px;'
            '   background-color: transparent;'
            '   border: none;'
            '}'
        )
        self.toast_label.setAttribute(Qt.WA_TranslucentBackground)
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.hide()
        
        self.toast_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.toast_label.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        # 创建Toast定时器
        self.toast_timer = QTimer(self.parent)
        self.toast_timer.timeout.connect(self.hide_toast)

        # 创建Mutator Alert标签
        self.mutator_alert_label = QLabel()
        # 设置字体大小为普通toast的2/3
        mutator_font_size = int(config.TOAST_FONT_SIZE * 2/3) # 强制设置成小一些
        self.mutator_alert_label.setFont(QFont('Arial', mutator_font_size))
        self.mutator_alert_label.setStyleSheet(
            'QLabel {'
            '   color: ' + config.MUTATOR_DEPLOYMENT_COLOR + ';'
            '   padding: 10px;'
            '   background-color: transparent;'
            '   border: none;'
            '}'
        )
        self.mutator_alert_label.setAttribute(Qt.WA_TranslucentBackground)
        self.mutator_alert_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        # 设置窗口标志
        self.mutator_alert_label.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.mutator_alert_label.hide()
        
        # 创建Mutator Alert定时器
        self.mutator_alert_timer = QTimer(self.parent)
        self.mutator_alert_timer.timeout.connect(self.hide_mutator_alert)

    def hide_toast(self):
        """隐藏Toast提示"""
        self.toast_label.hide()
        self.toast_timer.stop()

    def hide_mutator_alert(self):
        """隐藏Mutator提示"""
        self.mutator_alert_label.hide()
        self.mutator_alert_timer.stop()

    def show_map_toast(self, message, duration=None, force_show=False):
        """显示地图相关的Toast提示"""
        self.show_toast(message, duration, force_show)

    def show_toast(self, message, duration=None, force_show=False):
        """显示Toast提示"""
        # 检查游戏状态，非游戏中状态不显示提示
        if not force_show and (get_game_screen() != 'in_game' or not config.TOAST_ALLOWED):
            self.logger.info('非游戏中状态或禁用toast，不显示Toast提示')
            return
        else:
            self.logger.info('显示Toast提示')

        if duration is None:
            duration = config.TOAST_DURATION

        # 创建一个水平布局来容纳文本和图标
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # 解析消息内容
        parts = message.split('\t')
        self.logger.info(f'split 行数据: {len(parts)},{parts}')
        display_text = parts[0] + ' ' + parts[1]
        if len(parts) >= 3:
            # 查找T标识的位置
            troops_data = parts[2].split('|')
            if troops_data and troops_data[0].startswith('T'):
                # 截断文本到T标识处
                display_text = display_text + ' ' + troops_data[0]

        # 添加文本标签
        text_label = QLabel(display_text)
        text_label.setFont(QFont('Arial', config.TOAST_FONT_SIZE))
        text_label.setStyleSheet(f'color: {config.TOAST_FONT_COLOR}; background-color: transparent;')
        layout.addWidget(text_label)

        # 解析第三列数据，获取部队图标
        if len(parts) >= 3:
            troops_data = parts[2].split('|')
            self.logger.info(f'解析第三列数据: {parts[2]}')
            if troops_data and troops_data[0].startswith('T'):
                # 创建一个垂直布局来容纳两行图标
                icons_container = QWidget()
                icons_layout = QVBoxLayout(icons_container)
                icons_layout.setContentsMargins(0, 0, 0, 0)
                icons_layout.setSpacing(5)
                layout.addWidget(icons_container)
                
                # 创建第一行布局用于显示Tx对应的兵种图标
                tx_container = QWidget()
                tx_layout = QHBoxLayout(tx_container)
                tx_layout.setContentsMargins(0, 0, 0, 0)
                tx_layout.setSpacing(2)
                icons_layout.addWidget(tx_container)
                
                # 创建第二行布局用于显示hybrid兵种图标
                hybrid_container = QWidget()
                hybrid_layout = QHBoxLayout(hybrid_container)
                hybrid_layout.setContentsMargins(0, 0, 0, 0)
                hybrid_layout.setSpacing(2)
                icons_layout.addWidget(hybrid_container)
                try:
                    # 获取种族和军队配置
                    
                    army = get_troop_from_game()
                    if army is not None:
                        race = self.troop_loader.get_army(army)
                        
                        self.logger.info(f'当前种族: {race}, 军队配置: {army}')
                        if race and army:
                            # 读取军队配置文件
                            army_file = get_resources_dir('resources', 'troops', race, army)
                            self.logger.info(f'读取军队配置文件: {army_file}')
                            if os.path.exists(army_file):
                                with open(army_file, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        line = line.strip()
                                        if line:
                                            army_parts = line.split()
                                            if len(army_parts) >= 2 and army_parts[0] == troops_data[0][1:]:
                                                # 获取对应的图标
                                                icons = army_parts[1].split('|')
                                                self.logger.info(f'找到匹配的部队配置: {line}, 图标: {icons}')
                                                for icon in icons:
                                                    icon_path = get_resources_dir('ico', 'troops', race, f'{icon}.png')
                                                    self.logger.info(f'加载图标文件: {icon_path}')
                                                    if os.path.exists(icon_path):
                                                        icon_label = QLabel()
                                                        pixmap = QPixmap(icon_path)
                                                        icon_label.setPixmap(pixmap.scaled(config.TROOP_ICON_SIZE, config.TROOP_ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                                                        tx_layout.addWidget(icon_label)
                                                    else:
                                                        self.logger.warning(f'图标文件不存在: {icon_path}')
                            else:
                                self.logger.warning(f'军队配置文件不存在: {army_file}')
                        else:
                            self.logger.info('未获取到种族或军队配置')
                except Exception as e:
                    self.logger.error(f'解析部队图标失败: {str(e)}\n{traceback.format_exc()}')
                
                # 处理hybrid兵种图标
                for troop_info in troops_data[1:]:
                    if troop_info:
                        troop_parts = troop_info.split('*')
                        troop_name = troop_parts[0]
                        troop_count = troop_parts[1] if len(troop_parts) > 1 else '1'
                        
                        # 创建水平布局来容纳图标和数量
                        troop_container = QWidget()
                        troop_layout = QHBoxLayout(troop_container)
                        troop_layout.setContentsMargins(0, 0, 0, 0)
                        troop_layout.setSpacing(2)
                        
                        # 加载hybrid兵种图标
                        icon_path = get_resources_dir('ico', 'troops', 'hybrid', f'{troop_name}.jpg')
                        if os.path.exists(icon_path):
                            icon_label = QLabel()
                            pixmap = QPixmap(icon_path)
                            icon_label.setPixmap(pixmap.scaled(config.TROOP_ICON_SIZE, config.TROOP_ICON_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                            troop_layout.addWidget(icon_label)
                            
                            # 添加数量标签
                            count_label = QLabel(f'*{troop_count}')
                            count_label.setFont(QFont('Arial', config.TROOP_HYBRCONT_FONT_SIZE))
                            count_label.setStyleSheet(f'color: {config.TROOP_HYBRID_ICON_COLOR}; background-color: transparent;')
                            troop_layout.addWidget(count_label)
                            
                            hybrid_layout.addWidget(troop_container)
                        else:
                            self.logger.warning(f'Hybrid兵种图标不存在: {icon_path}')

        # 设置容器大小并显示
        container.adjustSize()
        container.setStyleSheet('background-color: transparent;')
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setAttribute(Qt.WA_TransparentForMouseEvents)
        container.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        # 移动到屏幕中央
        current_screen = self.parent.get_current_screen()
        screen_geometry = current_screen.geometry()
        x = screen_geometry.center().x() - container.width() // 2
        y = int(self.parent.height() * config.TOAST_POSITION)
        container.move(x, y)

        # 显示容器并启动定时器
        self.toast_label = container
        self.toast_label.show()
        self.toast_timer.start(duration)
