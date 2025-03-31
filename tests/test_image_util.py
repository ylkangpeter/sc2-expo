import sys
import time
import os
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

def run_test_cases():
    # """测试绘制多个矩形并截图"""
    # test_cases = [(100, 100, 200, 150), (300, 200, 250, 200), (500, 400, 180, 120)]

    # def process_next(index):
    #     if index >= len(test_cases):
    #         print("测试完成")
    #         return

    #     x, y, width, height = test_cases[index]
    #     rect = draw_square(x, y, width, height)
    #     print(f"绘制正方形: 位置({x}, {y}), 大小({width}, {height})")

    #     QTimer.singleShot(1500, lambda: save_and_continue(rect, index))

    def save_and_continue(rect, index):
        """截图当前矩形，并处理下一个"""
        print(f"截图矩形: {rect}")
        save_path = capture_screen_rect(rect)
        if save_path:
            print(f"截图已保存到: {save_path}")
        else:
            print("截图保存失败")

        # 继续下一个测试用例
        process_next(index + 1)

    # 开始处理第一个用例
    process_next(0)

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
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    print_all_monitors_info()
        
