from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
import os

class ControlWindow(QMainWindow):
    # 创建状态改变信号
    state_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_locked = True  # 添加状态变量，默认为锁定状态
        self.init_ui()

    def init_ui(self):
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool  # 不在任务栏显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景

        # 创建图标标签
        self.icon_label = QLabel(self)
        self.icon_label.setGeometry(5, 12, 20, 20)
        
        # 设置图标
        icon_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ico')
        self.lock_icon = QIcon(os.path.join(icon_dir, 'lock.svg'))
        self.unlock_icon = QIcon(os.path.join(icon_dir, 'unlock.svg'))
        
        # 设置初始图标
        self.update_icon()
        
        # 设置标签样式
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
            }
        """)
        
        # 设置窗口大小
        self.setFixedSize(30, 30)
        
    def mousePressEvent(self, event):
        # 处理鼠标点击事件
        if event.button() == Qt.LeftButton:
            self.is_locked = not self.is_locked  # 切换状态
            self.update_icon()
            # 发送状态改变信号：True表示解锁状态（可点击），False表示锁定状态（不可点击）
            self.state_changed.emit(not self.is_locked)
    
    def update_icon(self):
        # 根据状态更新图标
        icon = self.lock_icon if self.is_locked else self.unlock_icon
        pixmap = icon.pixmap(20, 20)  # 创建固定大小的图标
        self.icon_label.setPixmap(pixmap)