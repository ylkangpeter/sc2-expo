# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QWidget,
)

import config
from commander_selector import CommanderSelector
from fileutil import get_resources_dir, list_files
from ui.mutator_alerts import MUTATOR_TYPES

def init_ui(window):
    """初始化用户界面"""
    window.setWindowTitle('SC2 Timer')
    window.setGeometry(
        getattr(config, 'MAIN_WINDOW_X', 0),
        getattr(config, 'MAIN_WINDOW_Y', 300),
        config.MAIN_WINDOW_WIDTH,
        30
    )

    # 设置窗口样式 - 不设置点击穿透，这将由on_control_state_changed方法控制
    window.setWindowFlags(
        Qt.FramelessWindowHint |  # 无边框
        Qt.WindowStaysOnTopHint |  # 置顶
        Qt.Tool |  # 不在任务栏显示
        Qt.MSWindowsFixedSizeDialogHint  # 禁用窗口自动调整
    )
    window.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
    window.setAttribute(Qt.WA_NoSystemBackground)  # 禁用系统背景

    # 添加键盘事件监听变量
    window.ctrl_pressed = False

    # 创建主容器控件
    window.main_container = QWidget(window)
    window.main_container.setGeometry(0, 0, config.MAIN_WINDOW_WIDTH, 50)  # 调整主容器初始高度
    from config import MAIN_WINDOW_BG_COLOR
    window.main_container.setStyleSheet(f'background-color: {MAIN_WINDOW_BG_COLOR}')

    # 创建时间显示标签
    window.time_label = QLabel(window.current_time, window.main_container)
    window.time_label.setFont(QFont('Consolas', 11))
    window.time_label.setStyleSheet('color: rgb(0, 255, 128); background-color: transparent')
    window.time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    window.time_label.setGeometry(10, 40, config.TIME_LABEL_WIDTH, 20)  # 使用配置的宽度
    window.time_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 添加鼠标事件穿透

    # 创建地图版本选择按钮组
    window.map_version_group = QWidget(window.main_container)
    window.map_version_group.setGeometry(10 + config.TIME_LABEL_WIDTH + 10, 40, 100, 20)  # 根据时间标签宽度动态计算位置
    window.map_version_group.setStyleSheet('background-color: transparent')
    version_layout = QHBoxLayout(window.map_version_group)
    version_layout.setContentsMargins(0, 0, 0, 0)
    version_layout.setSpacing(4)  # 增加按钮间距

    window.version_buttons = []
    for version in ['A', 'B']:  # 默认使用A/B，后续会根据地图类型动态更改
        btn = QPushButton(version)
        btn.setFont(QFont('Arial', 11))  # 增加字体大小
        btn.setFixedSize(48, 20)  # 增加按钮宽度到48px
        btn.setCheckable(True)
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
        version_layout.addWidget(btn)
        window.version_buttons.append(btn)
        btn.clicked.connect(window.on_version_selected)

    # 默认隐藏按钮组
    window.map_version_group.hide()

    # 创建表格显示区
    window.table_area = QTableWidget(window.main_container)
    window.table_area.setGeometry(0, 65, config.MAIN_WINDOW_WIDTH, config.TABLE_HEIGHT)  # 保持表格区域位置不变
    window.table_area.setColumnCount(3)
    window.table_area.horizontalHeader().setVisible(False)  # 隐藏水平表头
    window.table_area.setColumnWidth(0, config.TIME_LABEL_WIDTH)  # 设置时间列的固定宽度
    window.table_area.setColumnWidth(2, 5)  # 设置时间列的固定宽度
    window.table_area.setColumnWidth(1, config.MAIN_WINDOW_WIDTH - config.TIME_LABEL_WIDTH - 5)  # 设置文字列的固定宽度
    window.table_area.verticalHeader().setVisible(False)  # 隐藏垂直表头
    window.table_area.setEditTriggers(QTableWidget.NoEditTriggers)  # 设置表格只读
    window.table_area.setSelectionBehavior(QTableWidget.SelectRows)  # 设置选择整行
    window.table_area.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    window.table_area.setShowGrid(False)  # 隐藏网格线
    window.table_area.setStyleSheet(f'''
        QTableWidget {{ 
            border: none; 
            background-color: transparent; 
            padding-left: 5px; 
            font-size: {config.TABLE_FONT_SIZE}px;
            font-family: Arial;
        }}
        QTableWidget::horizontalHeader {{ 
            border: none;
            background-color: transparent;
            padding: 0px;
            padding-left: 5px;
            text-align: left;
        }}
        QTableWidget::verticalHeader {{
            border: none;
            background-color: transparent;
            padding: 0px;
            padding-left: 5px;
            text-align: left;
        }}
        QTableWidget::item {{ 
            padding: 0px;
            padding-left: 5px;
            text-align: left;
            /* 移除对颜色的全局设置，允许单元格通过setForeground方法设置颜色 */
        }}
        QTableWidget::item:selected {{ 
            background-color: transparent; 
            color: rgb(255, 255, 255); 
            border: none; 
            text-align: left;
        }}
        QTableWidget::item:focus {{ 
            background-color: transparent; 
            color: rgb(255, 255, 255); 
            border: none; 
            text-align: left;
        }}''')

    # 设置表格的滚动条策略
    window.table_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    window.table_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # window.setFixedSize(config.MAIN_WINDOW_WIDTH, 250)  # 固定窗口大小为250


    # 调整主窗口大小以适应新添加的控件
    window.main_container.setGeometry(0, 0, config.MAIN_WINDOW_WIDTH, 335)  # 调整容器高度

    # 创建地图标签
    window.map_label = QLabel(window.get_text('map_label'), window.main_container)
    window.map_label.setFont(QFont('Arial', 9))  # 修改字体大小为9pt
    window.map_label.setStyleSheet('color: white; background-color: transparent')
    window.map_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    window.map_label.setGeometry(10, 5, 30, 30)
    window.map_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 添加鼠标事件穿透

    # 创建下拉框
    window.combo_box = QComboBox(window.main_container)
    window.combo_box.setGeometry(40, 5, 117, 30)
    window.combo_box.setFont(QFont('Arial', 9))  # 修改字体大小为9pt

    # 设置下拉列表视图
    view = window.combo_box.view()
    view.setStyleSheet("""
        background-color: rgba(43, 43, 43, 200);
        color: white;
    """)

    # 设置ComboBox样式
    window.combo_box.setStyleSheet('''
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
    /* 下拉滚动条样式 */
    QComboBox QScrollBar:vertical {
        width: 8px;
        background: rgba(200, 200, 200, 100);
    }
    QComboBox QScrollBar::handle:vertical {
        background: rgba(150, 150, 150, 150);
        border-radius: 4px;
    }''')

    # 加载resources文件夹下的文件
    resources_dir = get_resources_dir('resources', 'maps', config.current_language)
    if not resources_dir:
        files = []
    else:
        files = list_files(resources_dir)
    window.combo_box.addItems(files)

    # 连接下拉框选择变化事件
    window.combo_box.currentTextChanged.connect(window.on_map_selected)

    # 如果有文件，自动加载第一个
    if files:
        window.on_map_selected(files[0])

    # 调整时间标签的位置和高度
    window.time_label.setGeometry(10, 40, 100, 20)

    # 在表格区域之后添加图标区域
    window.icon_area = QWidget(window.main_container)
    icon_layout = QHBoxLayout()  # 不要在构造函数中传入父widget
    window.icon_area.setLayout(icon_layout)  # 单独设置布局

    # 设置图标区域的样式，便于调试
    window.icon_area.setStyleSheet("""
        QWidget {
            background-color: rgba(43, 43, 43, 96);
            border-radius: 5px;
        }
    """)

    # 图标文件路径
    icon_paths = [f"{mutator_type}.png" for mutator_type in MUTATOR_TYPES]
    window.mutator_buttons = []

    for icon_name in icon_paths:
        btn = QPushButton()
        icon_path = os.path.join('ico', 'mutator', icon_name)

        # 加载原始图标
        original_pixmap = QPixmap(icon_path)
        if original_pixmap.isNull():
            window.logger.warning(f"无法加载图标: {icon_path}")
            continue

        # 创建半透明版本
        from PyQt5.QtGui import QPainter
        transparent_pixmap = QPixmap(original_pixmap.size())
        transparent_pixmap.fill(Qt.transparent)  # 填充透明背景
        painter = QPainter(transparent_pixmap)
        painter.setOpacity(config.MUTATOR_ICON_TRANSPARENCY)  # 设置70%不透明度
        painter.drawPixmap(0, 0, original_pixmap)
        painter.end()

        # 创建灰色版本
        gray_image = original_pixmap.toImage()
        for y in range(gray_image.height()):
            for x in range(gray_image.width()):
                color = gray_image.pixelColor(x, y)
                gray = int((color.red() * 0.299) + (color.green() * 0.587) + (color.blue() * 0.114))
                color.setRgb(gray, gray, gray, color.alpha())
                gray_image.setPixelColor(x, y, color)
        gray_pixmap = QPixmap.fromImage(gray_image)

        # 创建灰色半透明版本
        gray_transparent_pixmap = QPixmap(gray_pixmap.size())
        gray_transparent_pixmap.fill(Qt.transparent)  # 填充透明背景
        painter = QPainter(gray_transparent_pixmap)
        painter.setOpacity(config.MUTATOR_ICON_TRANSPARENCY)  # 设置70%不透明度
        painter.drawPixmap(0, 0, gray_pixmap)
        painter.end()

        # 设置按钮属性
        btn.setIcon(QIcon(transparent_pixmap))  # 默认使用半透明图标
        btn.setIconSize(QSize(26, 26))
        btn.setFixedSize(32, 32)  # 稍微减小按钮尺寸
        btn.setCheckable(True)

        # 修改按钮样式表，减小边框宽度和内边距
        btn.setStyleSheet('''
            QPushButton {
                border: none;
                padding: 0px;
                border-radius: 3px;
                background-color: transparent;
                min-width: 30px;
                min-height: 30px;
            }
            QPushButton:checked {
                background-color: rgba(255, 255, 255, 0.1);
                margin-top: -1px;
            }
        ''')

        # 存储原始和灰色图标
        btn.original_icon = QIcon(transparent_pixmap)  # 使用半透明版本
        btn.gray_icon = QIcon(gray_transparent_pixmap)  # 使用灰色半透明版本

        # 连接点击事件
        btn.toggled.connect(lambda checked, b=btn: window.on_mutator_toggled(b, checked))

        icon_layout.addWidget(btn)
        window.mutator_buttons.append(btn)

    # 调整布局，优化间距和边距
    icon_layout.setSpacing(8)  # 增加图标间距
    icon_layout.setContentsMargins(4, 5, 8, 5)  # 减小左侧边距
    icon_layout.addStretch()
    icon_layout.addStretch()

    # 调整主容器和图标区域的位置
    table_bottom = window.table_area.geometry().bottom()
    window.icon_area.setGeometry(0, table_bottom + 5, window.main_container.width(), 50)

    # 添加替换指挥官按钮
    window.replace_commander_btn = QPushButton(window.get_text('replace_commander'), window.main_container)
    window.replace_commander_btn.clicked.connect(window.on_replace_commander)
    window.replace_commander_btn.setStyleSheet('''
        QPushButton {
            color: black;
            background-color: rgba(236, 236, 236, 200);
            border: none;
            border-radius: 3px;
            padding: 5px;
            font-size: 12pt;
        }
        QPushButton:hover {
            background-color: rgba(43, 43, 43, 200);
        }
    ''')
    window.replace_commander_btn.setFixedSize(150, 30)
    commander_btn_x = (window.main_container.width() - window.replace_commander_btn.width()) // 2
    window.replace_commander_btn.move(commander_btn_x, window.icon_area.geometry().bottom() + 5)
    window.replace_commander_btn.hide()  # 初始状态为隐藏

    # 更新主容器高度
    window.main_container.setFixedHeight(window.replace_commander_btn.geometry().bottom() + 5)
    window.setFixedHeight(window.main_container.height())  # 更新窗口高度

    # 创建指挥官选择器实例，传入当前窗口的几何信息
    window.commander_selector = CommanderSelector(window)

    # 显示窗口并强制置顶
    window.show()
    if sys.platform == 'win32':
        import win32gui
        import win32con
        hwnd = int(window.winId())
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

