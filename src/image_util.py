import os
import random
import datetime
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QScreen
import fileutil
import config
import cv2
import numpy as np
from PyQt5.QtGui import QImage

class SquareOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.square_rects = []
        self.init_ui()

    def init_ui(self):
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool |  # 不在任务栏显示
            Qt.X11BypassWindowManagerHint  # 绕过窗口管理器
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # 显示时不获取焦点

    def draw_square(self, x, y, width=100, height=100):
        """在指定坐标绘制一个红色边框的正方形

        Args:
            x: 正方形左上角的x坐标
            y: 正方形左上角的y坐标

        Returns:
            QRect: 绘制的矩形对象
        """
        # 获取目标屏幕的位置
        screens = QApplication.screens()
        if not screens or config.GAME_SCREEN >= len(screens):
            return None
        
        screen = screens[config.GAME_SCREEN]
        screen_geometry = screen.geometry()
        
        # 调整坐标到目标屏幕
        screen_x = x + screen_geometry.x()
        screen_y = y + screen_geometry.y()
        
        rect = QRect(screen_x, screen_y, width, height)
        self.square_rects.append(rect)
        # 计算所有正方形的边界区域
        left = min(rect.left() for rect in self.square_rects)
        top = min(rect.top() for rect in self.square_rects)
        right = max(rect.right() for rect in self.square_rects)
        bottom = max(rect.bottom() for rect in self.square_rects)
        # 设置窗口大小为所有正方形的边界区域
        self.setGeometry(left, top, right - left + 1, bottom - top + 1)
        self.show()
        self.update()
        return rect

    def clear_square(self, rect=None):
        """清除指定的正方形或所有正方形

        Args:
            rect: 要清除的矩形对象，如果为None则清除所有矩形
        """
        if rect is None:
            self.square_rects.clear()
            self.hide()
        else:
            self.square_rects.remove(rect)
            if not self.square_rects:
                self.hide()
            else:
                # 重新计算窗口大小
                left = min(r.left() for r in self.square_rects)
                top = min(r.top() for r in self.square_rects)
                right = max(r.right() for r in self.square_rects)
                bottom = max(r.bottom() for r in self.square_rects)
                self.setGeometry(left, top, right - left + 1, bottom - top + 1)
                self.update()

    def paintEvent(self, event):
        if self.square_rects:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 设置画笔为红色，宽度为3像素
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(3)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            
            # 获取窗口左上角坐标
            window_left = self.geometry().left()
            window_top = self.geometry().top()
            
            # 绘制所有正方形边框
            for rect in self.square_rects:
                # 计算相对于窗口的坐标
                x = rect.left() - window_left
                y = rect.top() - window_top
                painter.drawRect(x, y, rect.width()-1, rect.height()-1)

# 创建全局实例
_square_overlay = None

def get_square_overlay():
    """获取或创建SquareOverlay实例"""
    global _square_overlay
    if _square_overlay is None:
        _square_overlay = SquareOverlay()
    return _square_overlay

def draw_square(x, y,  width=100, height=100):
    """在指定坐标绘制一个红色边框的正方形

    Args:
        x: 正方形左上角的x坐标
        y: 正方形左上角的y坐标
    Returns:
        QRect: 绘制的矩形对象
    """
    overlay = get_square_overlay()
    return overlay.draw_square(x, y, width, height)

def clear_square(rect=None):
    """清除指定的正方形或所有正方形

    Args:
        rect: 要清除的矩形对象，如果为None则清除所有矩形
    """
    if _square_overlay:
        _square_overlay.clear_square(rect)

def _generate_filename():
    """生成唯一的文件名，格式为：年月日时分秒_4位随机数.jpg"""
    now = datetime.datetime.now()
    random_num = random.randint(1000, 9999)
    return f"{now.strftime('%Y%m%d%H%M%S')}_{random_num}.jpg"

def capture_screen_area(x, y, width, height, save2File=False):
    """根据指定的坐标和大小截取屏幕区域

    Args:
        x: 截图区域左上角的x坐标
        y: 截图区域左上角的y坐标
        width: 截图区域的宽度
        height: 截图区域的高度

    Returns:
        str: 保存的图片文件路径，如果保存失败则返回None
    """
    screen = QApplication.primaryScreen()
    screen_geometry = screen.geometry()
    
    # 调整坐标到目标屏幕
    screen_x = x 
    screen_y = y 
    
    # 创建截图区域
    capture_rect = QRect(screen_x, screen_y, width, height)
    # 获取截图
    screenshot = screen.grabWindow(0, screen_x, screen_y, width, height)
    
    # 获取保存路径
    if save2File:
        save_dir = fileutil.get_resources_dir('img', 'userdata')
        if not save_dir:
            return None
        
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成文件路径
        filename = _generate_filename()
        save_path = os.path.join(save_dir, filename)
        
        # 保存截图
        if screenshot.save(save_path, 'JPG'):
            return save_path
    return None

def capture_screen_rect(rect, save2File=False):
    """根据QRect对象截取屏幕区域

    Args:
        rect: QRect对象，表示要截取的区域

    Returns:
        str: 保存的图片文件路径，如果保存失败则返回None
    """
    return capture_screen_area(rect.x(), rect.y(), rect.width(), rect.height(), save2File)


def compare_images(screenshot, local_image_path):
    """计算两个图片的相似度

    Args:
        screenshot: QImage对象，通过screen.grabWindow获取的截图数据
        local_image_path: str，本地图片文件的路径

    Returns:
        float: 相似度值，范围在0到1之间，1表示完全相同，0表示完全不同
    """
    # 将QImage转换为OpenCV格式
    width = screenshot.width()
    height = screenshot.height()
    ptr = screenshot.bits()
    ptr.setsize(height * width * 4)
    arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
    img1 = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)

    # 读取本地图片
    img2 = cv2.imread(local_image_path)
    if img2 is None:
        return 0.0

    # 将两张图片调整为相同大小
    img2 = cv2.resize(img2, (width, height))

    # 计算直方图
    hist1 = cv2.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

    # 归一化直方图
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    # 计算相似度
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return max(0.0, min(1.0, (similarity + 1) / 2))