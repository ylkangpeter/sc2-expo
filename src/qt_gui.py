import os
import sys
import re
import time
import logging
import traceback
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QSystemTrayIcon, QMenu, QAction, QApplication, QComboBox, QTableWidgetItem, QPushButton, QTableWidget, QHeaderView
from PyQt5.QtGui import QFont, QIcon, QPixmap, QBrush, QColor
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
        
        # 初始化UI
        self.init_ui()
        
        # 初始化Toast提示
        self.init_toast()
        
        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game_time)
        self.timer.start(100)  # 自动开始更新，每500毫秒更新一次
        
        # 连接表格区域的双击事件
        self.table_area.mouseDoubleClickEvent = self.on_text_double_click
        
        # 初始化系统托盘
        self.init_tray()
        
        # 连接信号到处理函数
        self.progress_signal.connect(self.handle_progress_update)
        
        # 启动游戏检查线程
        from mainfunctions import check_for_new_game
        import threading
        self.game_check_thread = threading.Thread(target=check_for_new_game, args=(self.progress_signal,), daemon=True)
        self.game_check_thread.start()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('SC2 Timer')
        self.setGeometry(0, 300, 167, 30)  # 调整初始窗口位置，x坐标设为0
        
        # 设置窗口样式
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool |  # 不在任务栏显示
            Qt.MSWindowsFixedSizeDialogHint  # 禁用窗口自动调整
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setAttribute(Qt.WA_NoSystemBackground)  # 禁用系统背景
        self.setAttribute(Qt.WA_X11NetWmWindowTypeDesktop)  # 禁用桌面管理器的窗口管理
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 默认设置鼠标事件穿透
        
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
        
        # 显示窗口
        self.show()
    
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
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ico', 'fav.ico')
        self.tray_icon.setIcon(QIcon(icon_path))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction("显示", self)
        quit_action = QAction("退出", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def toggle_visibility(self):
        """切换窗口显示状态"""
        if self.time_label.isVisible():
            self.time_label.hide()
            self.show_button.setText('显示')
        else:
            self.time_label.show()
            self.show_button.setText('隐藏')
    
    def update_display_images(self):
        if self.image_scroll_area.isHidden():
            return

        # 获取原始图像和裁剪图像
        full_image, cropped_image = self.image_processor.capture_game_time()
        if not full_image or not cropped_image:
            return

        # 获取滚动区域的可见宽度
        scroll_width = self.image_scroll_area.width() - 20  # 减去滚动条宽度

        # 降低原始图像分辨率
        width, height = full_image.size
        new_width = width // 2
        new_height = height // 2
        resized_full_image = full_image.resize((new_width, new_height))

        # 在原始图像上标记裁剪区域
        marked_image = resized_full_image.copy()
        draw = ImageDraw.Draw(marked_image)
        left, top, crop_width, crop_height, bottom = self.image_processor.get_crop_area(width, height)
        # 调整裁剪区域坐标以匹配缩放后的图像
        left = left // 2
        top = top // 2
        crop_width = crop_width // 2
        bottom = bottom // 2
        draw.rectangle([left, top, left + crop_width, bottom], outline='red', width=2)

        # 创建用于显示的图像列表
        images = [resized_full_image, marked_image]
        
        # 添加裁剪后的图像（用于OCR识别的图片）
        if cropped_image:
            # 确保裁剪图像为RGB模式
            if cropped_image.mode != 'RGB':
                cropped_image = cropped_image.convert('RGB')
            # 调整裁剪图像的大小以匹配其他图像
            crop_width, crop_height = cropped_image.size
            crop_scale = new_width / crop_width
            resized_crop = cropped_image.resize((new_width, int(crop_height * crop_scale)))
            images.append(resized_crop)
            
            # 尝试OCR识别，如果失败则添加预处理后的图像
            result = self.image_processor.recognize_time(cropped_image)
            if result == "无法识别时间":
                processed_image = self.image_processor.process_image(cropped_image)
                if processed_image:
                    # 确保预处理图像为RGB模式
                    if processed_image.mode != 'RGB':
                        processed_image = processed_image.convert('RGB')
                    # 调整预处理图像的大小
                    proc_width, proc_height = processed_image.size
                    proc_scale = new_width / proc_width
                    resized_proc = processed_image.resize((new_width, int(proc_height * proc_scale)))
                    images.append(resized_proc)

        # 计算总高度和最大宽度
        max_width = max(img.size[0] for img in images)
        total_height = sum(img.size[1] for img in images)

        # 计算每张图片的缩放比例，使其宽度适应滚动区域
        scale = scroll_width / max_width

        # 创建组合图像
        scaled_width = scroll_width
        scaled_height = int(total_height * scale)
        combined_image = Image.new('RGB', (max_width, total_height))
        y_offset = 0

        # 将所有图像垂直排列粘贴到组合图像中
        for img in images:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # 调整每张图片的大小，保持宽高比
            img_width = img.size[0]
            img_height = img.size[1]
            img_scale = max_width / img_width
            resized_img = img.resize((max_width, int(img_height * img_scale)))
            combined_image.paste(resized_img, (0, y_offset))
            y_offset += resized_img.size[1]

        # 缩放组合图像以适应滚动区域宽度
        combined_image = combined_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        # 转换为Qt图像并显示
        img_array = np.array(combined_image)
        height, width, channel = img_array.shape
        bytes_per_line = channel * width
        qt_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qt_image)
        
        # 设置图像到标签并调整滚动区域
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())
        self.image_scroll_area.ensureVisible(0, 0)  # 确保滚动区域可见

    def mousePressEvent(self, event):
        """鼠标按下事件，用于实现窗口拖动"""
        if self.ctrl_pressed:
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

    def closeEvent(self, event):
        """关闭事件"""
        event.ignore()
        self.hide()
        
    def handle_progress_update(self, data):
        """处理进度更新信号"""
        if data[0] == 'update_map':
            # 在下拉框中查找并选择地图
            index = self.combo_box.findText(data[1])
            if index >= 0:
                self.logger.info(f'找到地图 {data[1]}，更新下拉框选择')
                self.combo_box.setCurrentIndex(index)
                # 手动调用地图选择事件处理函数，确保加载地图文件
                self.on_map_selected(data[1])

    def on_text_double_click(self, event):
        """双击事件处理"""
        if event.button() == Qt.LeftButton:
            # 不再调用toggle_update，直接接受事件
            event.accept()

    def on_map_selected(self, map_name):
        """处理地图选择变化事件"""
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

    def update_display_images(self):
        if self.image_scroll_area.isHidden():
            return

        # 获取原始图像和裁剪图像
        full_image, cropped_image = self.image_processor.capture_game_time()
        if not full_image or not cropped_image:
            return

        # 获取滚动区域的可见宽度
        scroll_width = self.image_scroll_area.width() - 20  # 减去滚动条宽度

        # 降低原始图像分辨率
        width, height = full_image.size
        new_width = width // 2
        new_height = height // 2
        resized_full_image = full_image.resize((new_width, new_height))

        # 在原始图像上标记裁剪区域
        marked_image = resized_full_image.copy()
        draw = ImageDraw.Draw(marked_image)
        left, top, crop_width, crop_height, bottom = self.image_processor.get_crop_area(width, height)
        # 调整裁剪区域坐标以匹配缩放后的图像
        left = left // 2
        top = top // 2
        crop_width = crop_width // 2
        bottom = bottom // 2
        draw.rectangle([left, top, left + crop_width, bottom], outline='red', width=2)

        # 创建用于显示的图像列表
        images = [resized_full_image, marked_image]
        
        # 添加裁剪后的图像（用于OCR识别的图片）
        if cropped_image:
            # 确保裁剪图像为RGB模式
            if cropped_image.mode != 'RGB':
                cropped_image = cropped_image.convert('RGB')
            # 调整裁剪图像的大小以匹配其他图像
            crop_width, crop_height = cropped_image.size
            crop_scale = new_width / crop_width
            resized_crop = cropped_image.resize((new_width, int(crop_height * crop_scale)))
            images.append(resized_crop)
            
            # 尝试OCR识别，如果失败则添加预处理后的图像
            result = self.image_processor.recognize_time(cropped_image)
            if result == "无法识别时间":
                processed_image = self.image_processor.process_image(cropped_image)
                if processed_image:
                    # 确保预处理图像为RGB模式
                    if processed_image.mode != 'RGB':
                        processed_image = processed_image.convert('RGB')
                    # 调整预处理图像的大小
                    proc_width, proc_height = processed_image.size
                    proc_scale = new_width / proc_width
                    resized_proc = processed_image.resize((new_width, int(proc_height * proc_scale)))
                    images.append(resized_proc)

        # 计算总高度和最大宽度
        max_width = max(img.size[0] for img in images)
        total_height = sum(img.size[1] for img in images)

        # 计算每张图片的缩放比例，使其宽度适应滚动区域
        scale = scroll_width / max_width

        # 创建组合图像
        scaled_width = scroll_width
        scaled_height = int(total_height * scale)
        combined_image = Image.new('RGB', (max_width, total_height))
        y_offset = 0

        # 将所有图像垂直排列粘贴到组合图像中
        for img in images:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # 调整每张图片的大小，保持宽高比
            img_width = img.size[0]
            img_height = img.size[1]
            img_scale = max_width / img_width
            resized_img = img.resize((max_width, int(img_height * img_scale)))
            combined_image.paste(resized_img, (0, y_offset))
            y_offset += resized_img.size[1]

        # 缩放组合图像以适应滚动区域宽度
        combined_image = combined_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        # 转换为Qt图像并显示
        img_array = np.array(combined_image)
        height, width, channel = img_array.shape
        bytes_per_line = channel * width
        qt_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qt_image)
        
        # 设置图像到标签并调整滚动区域
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())
        self.image_scroll_area.ensureVisible(0, 0)  # 确保滚动区域可见

    def mousePressEvent(self, event):
        """鼠标按下事件，用于实现窗口拖动"""
        if self.ctrl_pressed:
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

    def closeEvent(self, event):
        """关闭事件"""
        event.ignore()
        self.hide()
        
    def handle_progress_update(self, data):
        """处理进度更新信号"""
        if data[0] == 'update_map':
            # 在下拉框中查找并选择地图
            index = self.combo_box.findText(data[1])
            if index >= 0:
                self.logger.info(f'找到地图 {data[1]}，更新下拉框选择')
                self.combo_box.setCurrentIndex(index)
                # 手动调用地图选择事件处理函数，确保加载地图文件
                self.on_map_selected(data[1])

    def on_text_double_click(self, event):
        """双击事件处理"""
        if event.button() == Qt.LeftButton:
            # 不再调用toggle_update，直接接受事件
            event.accept()


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

def main():
    app = QApplication(sys.argv)
    window = TimerWindow()
    window.start_timer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()