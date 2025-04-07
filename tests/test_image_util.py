import sys
import time
import os
import io
from PyQt5.QtWidgets import QApplication

from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QApplication, QWidget

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import win32api
import win32print
import win32con
import win32gui
import win32ui
import win32con
from image_util import ScreenshotTool
import image_util
import show_fence
import logging_util

def run_test_cases():
    # 创建ScreenshotTool实例
    screenshot_tool = ScreenshotTool()
    # 获取截图并转换为OpenCV格式
    pil_image = screenshot_tool.capture_screen_core([17,438],[134,763], False)
    if pil_image:
        print("截图成功")
        # 创建ImageCache实例
        image_cache = image_util.ImageCache()
        # 将PIL图像转换为字节流
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        # 调用compare_images方法进行图像比对
        best_match, similarity = image_cache.compare_images(img_byte_arr)
        print(f"最佳匹配: {best_match}, 相似度: {similarity}")
    else:
        print("截图失败")
    thread = ScreenshotTool.draw_square(1800,500,1920,1080,"test");
    # 等待用户输入后继续
    input('按回车键继续...')
    thread.destroy()
    input('按回车键继续...')
        
def print_all_monitors_info():
    # 获取所有显示器信息
    monitors = win32api.EnumDisplayMonitors()
    
    # 遍历所有显示器并打印信息
    for i, monitor in enumerate(monitors):
        monitor_handle = monitor[0]  # 获取显示器句柄
        monitor_info = win32api.GetMonitorInfo(monitor_handle)  # 获取显示器的详细信息
        
        monitor_rect = monitor_info['Monitor']  # 获取显示器的矩形区域
        
        print(f"显示器 {i + 1}:")
        print(f"  显示器句柄: {monitor_handle}")
        print(f"  显示器区域: {monitor_rect}")
        print(f"  左上角: ({monitor_rect[0]}, {monitor_rect[1]})")
        print(f"  右下角: ({monitor_rect[2]}, {monitor_rect[3]})")
        print(f"  宽度: {monitor_rect[2] - monitor_rect[0]}")
        print(f"  高度: {monitor_rect[3] - monitor_rect[1]}")
        print("-" * 40)

def run_image_capture():
    # show_fence.show_square();
    # input('按回车键继续...')
    show_fence.detect_troop()
    input('按回车键继续...')
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    logging_util.setup_logger()
    # run_test_cases()
    run_image_capture()
        
