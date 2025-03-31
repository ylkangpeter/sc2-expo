import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
from pynput import mouse
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import windll
from ctypes import c_int
import config
import traceback

from logging_util import get_logger, setup_logger
logger = get_logger(__name__)
        
class ScreenshotTool:
    def __init__(self):
        # 设置DPI感知
        try:
            windll.user32.SetProcessDPIAware()
        except AttributeError:
            pass
        
        self.start_pos = None
        self.end_pos = None
        self.is_capturing = False
        self.root = None
        self.canvas = None
        if hasattr(config, 'GAME_SCREEN_DPI'):
            logger.warning(f"使用用户自定义dpi： {config.GAME_SCREEN_DPI}")
            self.dpi = config.GAME_SCREEN_DPI/96
        else:    
            # 获取系统DPI缩放比例
            screen_dc = win32gui.GetDC(0)
            dpi = win32ui.GetDeviceCaps(screen_dc, win32con.LOGPIXELSX) / 96.0
            logger.warning(f"使用自动获取（可能不准，在windows桌面设置查看一下）的系统dpi： {dpi}")
            win32gui.ReleaseDC(0, screen_dc)
            self.dpi = dpi

    def capture_screen(self, start_pos, end_pos):
        # 临时隐藏选择框
        original_alpha = self.canvas.winfo_toplevel().attributes('-alpha')
        self.canvas.winfo_toplevel().attributes('-alpha', 0)
        self.root.update()

        # 获取所有显示器信息
        monitors = win32api.EnumDisplayMonitors()
        if not hasattr(config, 'GAME_SCREEN'):
            config.GAME_SCREEN = 0
            
        if config.GAME_SCREEN >= len(monitors):
            logger.info(f'警告：配置的屏幕序号{config.GAME_SCREEN}超出可用显示器数量，将使用主屏幕')
            monitor_info = win32api.GetMonitorInfo(monitors[0][0])
        else:
            monitor_info = win32api.GetMonitorInfo(monitors[config.GAME_SCREEN][0])

        # 获取目标屏幕的分辨率和位置
        monitor_rect = monitor_info['Monitor']
        real_width = monitor_rect[2] - monitor_rect[0]
        real_height = monitor_rect[3] - monitor_rect[1]
        logger.info(f'目标屏幕分辨率: {real_width/self.dpi}x{real_height/self.dpi}')
        logger.info(f'屏幕位置: ({monitor_rect[0]/self.dpi}, {monitor_rect[1]/self.dpi}, {monitor_rect[2]/self.dpi}, {monitor_rect[3]/self.dpi})')

        # 获取窗口位置，并根据DPI缩放调整坐标
        logger.info(f'窗口位置(DPI调整前) - x: {self.root.winfo_x()}, y: {self.root.winfo_y()}')
        window_x = int(self.root.winfo_x() /self.dpi)
        window_y = int(self.root.winfo_y() / self.dpi)
        logger.info(f'窗口位置(DPI调整后) - x: {window_x}, y: {window_y}')
        
        # 将窗口相对坐标转换为屏幕绝对坐标
        screen_start_x = int(window_x + start_pos[0]/self.dpi)
        screen_start_y = int(window_y + start_pos[1]/self.dpi)
        screen_end_x = int(window_x + end_pos[0]/self.dpi)
        screen_end_y = int(window_y + end_pos[1]/self.dpi)
        logger.info(f'截图区域(DPI调整后) - 起点: ({screen_start_x}, {screen_start_y}), 终点: ({screen_end_x}, {screen_end_y})')
        
        # 获取屏幕DC
        hwin = win32gui.GetDesktopWindow()
        
        # 创建设备上下文和内存设备上下文
        hwindc = win32gui.GetWindowDC(hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        
        # 创建位图对象
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, real_width, real_height)
        memdc.SelectObject(bmp)
        
        # 计算截图区域，使用转换后的屏幕坐标
        x1, y1 = min(screen_start_x, screen_end_x), min(screen_start_y, screen_end_y)
        x2, y2 = max(screen_start_x, screen_end_x), max(screen_start_y, screen_end_y)
        width = x2 - x1
        height = y2 - y1

        # 复制屏幕到内存设备上下文，使用正确的源坐标
        memdc.BitBlt((0, 0), (real_width, real_height), srcdc, (int(monitor_rect[0]/self.dpi), int(monitor_rect[1]/self.dpi)), win32con.SRCCOPY)
        
        try:
            # 保存位图
            bmpinfo = bmp.GetInfo()
            bmpstr = bmp.GetBitmapBits(True)
            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
            logger.info(f'截图坐标: {x1},{x2},{y1},{y2}')
            if x1<0:
                x1=real_width+x1
            if x2>real_width:
                x2=real_width+x2
            if  y1<0:
                y1=real_height+y1
            if y2>real_height:
                y2=real_height+y2

            im = im.crop((x1, y1, x2, y2))
            
            # im = im.crop((-500, 0, 3000, 2000))
            # 创建screenshots文件夹（如果不存在）
            if not os.path.exists('screenshots'):
                os.makedirs('screenshots')
            
            # 生成文件名并保存
            filename = f'screenshots/screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{real_width}x{real_height}_{screen_start_x}_{screen_start_y}_{screen_end_x}_{screen_end_y}.png'
            im.save(filename)
            logger.warning(f'截图已保存: {filename}')
            
            # 清理资源
            memdc.DeleteDC()
            win32gui.DeleteObject(bmp.GetHandle())
            win32gui.ReleaseDC(hwin, hwindc)
        except Exception as capture_error:
            logger.error(f'区域截图失败: {str(capture_error)}')
            logger.error(traceback.format_exc())

        # 恢复选择框显示
        self.canvas.winfo_toplevel().attributes('-alpha', original_alpha)
        self.root.update()

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            if pressed:
                self.start_pos = (x, y)
                self.is_capturing = True
                logger.info(f'开始位置: {self.start_pos}')
            elif self.is_capturing:
                self.end_pos = (x, y)
                logger.info(f'结束位置: {self.end_pos}')
                self.capture_screen(self.start_pos, self.end_pos)
                self.is_capturing = False

    def create_overlay(self):
        # 获取所有显示器信息
        monitors = win32api.EnumDisplayMonitors()
        if not hasattr(config, 'GAME_SCREEN'):
            config.GAME_SCREEN = 0
            
        if config.GAME_SCREEN >= len(monitors):
            logger.warning(f'警告：配置的屏幕序号{config.GAME_SCREEN}超出可用显示器数量，将使用主屏幕')
            monitor_info = win32api.GetMonitorInfo(monitors[0][0])
        else:
            monitor_info = win32api.GetMonitorInfo(monitors[config.GAME_SCREEN][0])

        # 获取目标屏幕的位置
        monitor_rect = monitor_info['Monitor']
        screen_width = monitor_rect[2] - monitor_rect[0]
        screen_height = monitor_rect[3] - monitor_rect[1]

        self.root = tk.Tk()
        self.root.overrideredirect(True)  # 移除窗口装饰
        self.root.attributes('-alpha', 0.3, '-topmost', True)
        self.root.configure(bg='gray')
        
        # 设置窗口大小和位置
        self.root.geometry(f'{screen_width}x{screen_height}+{monitor_rect[0]}+{monitor_rect[1]}')
        
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.configure(bg='gray')
        
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        # 将ESC键绑定从canvas移到root窗口
        self.root.bind('<Escape>', self.on_escape)
        self.root.focus_force()

    def on_escape(self, event):
        # 清理资源并退出程序
        if self.root:
            self.root.destroy()
            self.root.quit()

    def on_mouse_down(self, event):
        self.start_pos = (event.x, event.y)
        self.is_capturing = True
        logger.info(f'鼠标按下 - 原始坐标: ({event.x}, {event.y})，去掉dpi后实际屏幕坐标：({event.x/self.dpi}, {event.y/self.dpi})')

    def on_mouse_move(self, event):
        if self.is_capturing:
            # 删除之前的临时矩形
            self.canvas.delete('temp_rect')
            # 创建新的临时矩形
            self.canvas.create_rectangle(
                self.start_pos[0], self.start_pos[1],
                event.x, event.y,
                outline='red', width=2, tags='temp_rect'
            )

    def on_mouse_up(self, event):
        if self.is_capturing:
            self.end_pos = (event.x, event.y)
            logger.info(f'鼠标释放 - 原始坐标: ({event.x}, {event.y})，去掉dpi后实际屏幕坐标：({event.x/self.dpi}, {event.y/self.dpi})')
            logger.info(f'窗口位置 - x: {self.root.winfo_x()}, y: {self.root.winfo_y()}')
            # 创建一个永久性的矩形，使用时间戳作为唯一标签
            rect_tag = f'rect_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            self.canvas.create_rectangle(
                self.start_pos[0], self.start_pos[1],
                event.x, event.y,
                outline='red', width=2, tags=rect_tag
            )
            self.capture_screen(self.start_pos, self.end_pos)
            self.is_capturing = False
            # 不再调用withdraw和quit，保持窗口显示
            # 保持矩形框显示，不删除
            self.is_capturing = False

    def start(self):
        logger.info('截图工具已启动，请按住鼠标左键选择区域...')
        self.create_overlay()
        self.root.mainloop()

def draw_square(x1, y1, w1, h1):
    return

if __name__ == '__main__':
    setup_logger()
    tool = ScreenshotTool()
    tool.start()