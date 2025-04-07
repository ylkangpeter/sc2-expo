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
import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim
from fileutil import get_resources_dir, list_files
from logging_util import get_logger, setup_logger
logger = get_logger(__name__)

class ImageCache:
    def __init__(self):
        self.cache = {}
        self.last_scan_time = None
        
    def add_image(self, image_path):
        try:
            img = cv2.imread(image_path)
            if img is not None:
                self.cache[image_path] = img
                logger.warning(f'已加载图片到缓存: {image_path}')
            else:
                logger.error(f'无法加载图片: {image_path}')
        except Exception as e:
            logger.error(f'加载图片时发生错误: {str(e)}')
            
    def scan_directory(self):
        troops_dir = get_resources_dir('resources', 'screen_capcture', 'troops')
        if not troops_dir:
            logger.error('无法找到troops目录')
            return
            
        if not os.path.exists(troops_dir):
            os.makedirs(troops_dir)
            logger.warning(f'创建troops目录: {troops_dir}')
            return
        
        logger.info(f'开始扫描troops目录: {troops_dir}')
            
        current_files = set(f for f in list_files(troops_dir) if f.lower().endswith('.png'))
        cached_files = set(os.path.basename(p) for p in self.cache.keys())
        
        # 找出新增的文件
        new_files = current_files - cached_files
        if new_files:
            for file in new_files:
                full_path = os.path.join(troops_dir, file)
                self.add_image(full_path)
                
        self.last_scan_time = datetime.now()
        
    def get_most_similar_image(self, target_img):
        if not self.cache:
            logger.warning('图片缓存为空')
            return None, 0.0
            
        max_score = 0.0
        best_match = None
        
        for path, cached_img in self.cache.items():
            try:
                # 确保两张图片大小一致
                resized_cached = cv2.resize(cached_img, (target_img.shape[1], target_img.shape[0]))
                
                # 转换为灰度图
                gray1 = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(resized_cached, cv2.COLOR_BGR2GRAY)
                
                # 计算SSIM
                score = ssim(gray1, gray2)
                logger.info(f'与图片 {os.path.basename(path)} 的相似度: {score}')
                
                if score > max_score:
                    max_score = score
                    best_match = path
            except Exception as e:
                logger.error(f'比较图片时发生错误: {str(e)}')
                continue
        best_match = os.path.splitext(os.path.basename(best_match))[0] 
        return best_match, max_score
        
    def compare_images(self, image_stream):
        """比较图像与缓存中的所有图像的相似度
        Args:
            image_stream: 图像数据流
        Returns:
            tuple: (最相似图片的路径, 相似度值)
        """
        try:
            # 扫描并更新图片缓存
            self.scan_directory()
            
            # 读取数据流中的图像
            image_stream_array = np.frombuffer(image_stream, np.uint8)
            img = cv2.imdecode(image_stream_array, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error('无法读取图像数据流')
                return None, 0.0
                
            # 在缓存中查找最相似的图片
            best_match, max_score = self.get_most_similar_image(img)
            
            if best_match:
                logger.info(f'找到最相似的图片: {os.path.basename(best_match)}，相似度: {max_score}')
            else:
                logger.warning('未找到相似的图片')
                
            return best_match, max_score
            
        except Exception as e:
            logger.error(f'比较图像时发生错误: {str(e)}')
            logger.error(traceback.format_exc())
            return None, 0.0
        
class ScreenshotTool:
    def __init__(self):
        self.image_cache = ImageCache()
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
        self.confirm_button = None
        self.cancel_button = None
        self.current_rect_tag = None
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

    def capture_screen_core(self, start_pos, end_pos, save_file=True):
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

        # 计算屏幕绝对坐标
        screen_start_x = int(start_pos[0]/self.dpi)
        screen_start_y = int(start_pos[1]/self.dpi)
        screen_end_x = int(end_pos[0]/self.dpi)
        screen_end_y = int(end_pos[1]/self.dpi)
        
        # 如果存在UI窗口，需要加上窗口偏移
        if hasattr(self, 'root') and self.root:
            window_x = int(self.root.winfo_x() /self.dpi)
            window_y = int(self.root.winfo_y() / self.dpi)
            screen_start_x += window_x
            screen_start_y += window_y
            screen_end_x += window_x
            screen_end_y += window_y
            logger.info(f'窗口位置(DPI调整后) - x: {window_x}, y: {window_y}')
        
        logger.info(f'截图区域(DPI调整后) - 起点: ({screen_start_x}, {screen_start_y}), 终点: ({screen_end_x}, {screen_end_y})')
        
        # 获取屏幕DC
        hwin = win32gui.GetDesktopWindow()
        hwindc = win32gui.GetWindowDC(hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        
        # 创建位图对象
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, real_width, real_height)
        memdc.SelectObject(bmp)
        
        # 计算截图区域
        x1, y1 = min(screen_start_x, screen_end_x), min(screen_start_y, screen_end_y)
        x2, y2 = max(screen_start_x, screen_end_x), max(screen_start_y, screen_end_y)

        # 复制屏幕到内存设备上下文
        memdc.BitBlt((0, 0), (real_width, real_height), srcdc, (int(monitor_rect[0]/self.dpi), int(monitor_rect[1]/self.dpi)), win32con.SRCCOPY)
        
        try:
            # 保存位图
            bmpinfo = bmp.GetInfo()
            bmpstr = bmp.GetBitmapBits(True)
            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
            logger.info(f'截图坐标(调整前): {x1},{x2},{y1},{y2}')
            
            # 确保坐标不超出屏幕边界
            if x1 < 0: x1 = 0
            if x2 > real_width: x2 = real_width
            if y1 < 0: y1 = 0
            if y2 > real_height: y2 = real_height
            
            # 确保截图区域有效
            if x2 <= x1 or y2 <= y1:
                logger.error(f'无效的截图区域: ({x1},{y1},{x2},{y2})')
                raise ValueError("无效的截图区域：宽度或高度为0")
                
            logger.info(f'截图坐标(调整后): {x1},{x2},{y1},{y2}')

            im = im.crop((x1, y1, x2, y2))
            
            # 清理资源
            memdc.DeleteDC()
            win32gui.DeleteObject(bmp.GetHandle())
            win32gui.ReleaseDC(hwin, hwindc)
            
            if save_file:
                if not os.path.exists('screenshots'):
                    os.makedirs('screenshots')
                filename = f'screenshots/screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{real_width}x{real_height}_{screen_start_x}_{screen_start_y}_{screen_end_x}_{screen_end_y}.png'
                im.save(filename)
                logger.info(f'截图已保存: {filename}')
            else:
                return im
        except Exception as capture_error:
            logger.error(f'区域截图失败: {str(capture_error)}')
            logger.error(traceback.format_exc())
            raise

    def capture_screen(self, start_pos, end_pos, save_file=True):
        # 如果存在UI窗口，需要临时隐藏
        has_ui = hasattr(self, 'root') and self.root
        if has_ui:
            self.root.withdraw()
            self.overlay_window.withdraw()
            self.ui_window.withdraw()
            self.root.update()

        try:
            return self.capture_screen_core(start_pos, end_pos, save_file)
        finally:
            # 恢复UI窗口显示
            if has_ui:
                self.root.deiconify()
                self.overlay_window.deiconify()
                self.ui_window.deiconify()
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

        # 创建主窗口（用于接收鼠标事件）
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # 移除窗口装饰
        self.root.attributes('-alpha', 0.01, '-topmost', True)  # 设置几乎完全透明
        self.root.configure(bg='gray')
        self.root.geometry(f'{screen_width}x{screen_height}+{monitor_rect[0]}+{monitor_rect[1]}')
        
        # 创建蒙层窗口（半透明背景）
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.overrideredirect(True)
        self.overlay_window.attributes('-alpha', 0.3, '-topmost', True)
        self.overlay_window.configure(bg='gray')
        self.overlay_window.geometry(f'{screen_width}x{screen_height}+{monitor_rect[0]}+{monitor_rect[1]}')
        
        # 创建UI窗口（完全不透明，用于显示矩形和按钮）
        self.ui_window = tk.Toplevel(self.root)
        self.ui_window.overrideredirect(True)
        self.ui_window.attributes('-alpha', 1.0, '-topmost', True)
        self.ui_window.configure(bg='gray')
        self.ui_window.geometry(f'{screen_width}x{screen_height}+{monitor_rect[0]}+{monitor_rect[1]}')
        self.ui_window.attributes('-transparentcolor', 'gray')  # 使背景透明
        
        # 创建画布（在UI窗口上，完全不透明）
        self.canvas = tk.Canvas(self.ui_window, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.configure(bg='gray')
        
        # 绑定事件到主窗口
        self.root.bind('<Button-1>', self.on_mouse_down)
        self.root.bind('<B1-Motion>', self.on_mouse_move)
        self.root.bind('<ButtonRelease-1>', self.on_mouse_up)
        # 将ESC键绑定到root窗口
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
                outline='red', width=2, tags='temp_rect',
                fill='white', stipple='gray12'
            )

    def on_confirm(self):
        if hasattr(self, 'temp_start_pos') and hasattr(self, 'temp_end_pos') and \
           len(self.temp_start_pos) == 2 and len(self.temp_end_pos) == 2:
            # 使用临时保存的坐标值
            current_start_pos = tuple(self.temp_start_pos)
            current_end_pos = tuple(self.temp_end_pos)
            logger.debug(f'原始坐标 - 开始位置: {current_start_pos}, 结束位置: {current_end_pos}')
            logger.info(f'确认截图 - 开始位置: {current_start_pos}, 结束位置: {current_end_pos}')
            
            # 验证坐标是否构成有效的矩形区域
            if current_start_pos[0] >= current_end_pos[0] or current_start_pos[1] >= current_end_pos[1]:
                logger.warning(f'无效的截图区域: 开始位置{current_start_pos}必须在结束位置{current_end_pos}的左上方')
                self.cleanup_ui()
                return
                
            try:
                # 先清理UI，避免闪烁
                self.cleanup_ui()
                # 使用保存的坐标进行截图
                self.capture_screen(current_start_pos, current_end_pos)
                # 截图完成后立即销毁所有窗口
                if hasattr(self, 'overlay_window') and self.overlay_window.winfo_exists():
                    self.overlay_window.destroy()
                if hasattr(self, 'ui_window') and self.ui_window.winfo_exists():
                    self.ui_window.destroy()
                if self.root and self.root.winfo_exists():
                    # 立即退出事件循环并销毁root窗口
                    self.root.quit()
                    self.root.destroy()
            except Exception as e:
                logger.error(f'截图保存失败: {str(e)}')
                logger.error(traceback.format_exc())
                # 发生错误时清理UI
                self.cleanup_ui()
        else:
            logger.warning(f'确认截图时未检测到有效的开始和结束位置')
            self.cleanup_ui()

    def on_cancel(self):
        # 完全清理UI元素和状态
        self.cleanup_ui()
        # 重置所有状态变量
        self.start_pos = None
        self.end_pos = None
        self.temp_start_pos = None
        self.temp_end_pos = None
        self.is_capturing = False
        self.current_rect_tag = None
        # 确保窗口重新显示并获取焦点
        if self.root and self.root.winfo_exists():
            self.root.deiconify()
            self.root.focus_force()
        if hasattr(self, 'overlay_window') and self.overlay_window.winfo_exists():
            self.overlay_window.deiconify()
            self.overlay_window.focus_force()
        if hasattr(self, 'ui_window') and self.ui_window.winfo_exists():
            self.ui_window.deiconify()
            self.ui_window.focus_force()
            
        # 重新绑定鼠标事件
        if self.root and self.root.winfo_exists():
            self.root.bind('<Button-1>', self.on_mouse_down)
            self.root.bind('<B1-Motion>', self.on_mouse_move)
            self.root.bind('<ButtonRelease-1>', self.on_mouse_up)
            self.root.bind('<Escape>', self.on_escape)
            self.root.focus_force()

    def cleanup_ui(self):
        # 清理所有画布元素
        if self.canvas:
            self.canvas.delete('all')
        
        # 销毁按钮
        if self.confirm_button:
            self.confirm_button.destroy()
            self.confirm_button = None
        if self.cancel_button:
            self.cancel_button.destroy()
            self.cancel_button = None
            
        # 重置状态变量
        self.current_rect_tag = None
        self.start_pos = None
        self.end_pos = None
        self.is_capturing = False
        
        # 确保所有窗口都可见并更新
        if self.root and self.root.winfo_exists():
            self.root.deiconify()
            self.root.update()
        if hasattr(self, 'overlay_window') and self.overlay_window.winfo_exists():
            self.overlay_window.deiconify()
            self.overlay_window.update()
        if hasattr(self, 'ui_window') and self.ui_window.winfo_exists():
            self.ui_window.deiconify()
            self.ui_window.update()

    def create_buttons(self, x1, y1, x2, y2):
        # 计算按钮位置
        button_width = 60
        button_height = 30
        spacing = 10
        screen_height = self.ui_window.winfo_height()
        
        # 确定是否需要将按钮放在矩形内部
        bottom_space = screen_height - max(y1, y2) - button_height - spacing
        buttons_inside = bottom_space < spacing
        
        if buttons_inside:
            # 在矩形内部底部放置按钮
            button_y = max(y1, y2) - button_height - spacing
        else:
            # 在矩形下方放置按钮
            button_y = max(y1, y2) + spacing
        
        # 计算按钮的x坐标，使其居中对齐
        rect_center_x = (x1 + x2) / 2
        confirm_x = rect_center_x - button_width - spacing/2
        cancel_x = rect_center_x + spacing/2
        
        # 创建按钮
        self.confirm_button = tk.Button(
            self.ui_window,
            text='确认',
            command=self.on_confirm,
            bg='#4CAF50',  # 绿色背景
            fg='white',    # 白色文字
            activebackground='#45a049',  # 激活状态背景色
            activeforeground='white',    # 激活状态文字色
            relief='raised',             # 3D凸起效果
            bd=2,                        # 边框宽度
            borderwidth=2,               # 边框宽度
            highlightthickness=0,        # 无高亮边框
            padx=5,                      # 水平内边距
            pady=2                       # 垂直内边距
        )
        self.confirm_button.lift()  # 确保按钮在最上层
        self.cancel_button = tk.Button(
            self.ui_window,
            text='取消',
            command=self.on_cancel,
            bg='#f44336',  # 红色背景
            fg='white',    # 白色文字
            activebackground='#d32f2f',  # 激活状态背景色
            activeforeground='white',    # 激活状态文字色
            relief='raised',             # 3D凸起效果
            bd=2,                        # 边框宽度
            borderwidth=2,               # 边框宽度
            highlightthickness=0,        # 无高亮边框
            padx=5,                      # 水平内边距
            pady=2                       # 垂直内边距
        )
        self.cancel_button.lift()  # 确保按钮在最上层
        
        # 放置按钮
        self.confirm_button.place(x=confirm_x, y=button_y)
        self.cancel_button.place(x=cancel_x, y=button_y)

    def on_mouse_up(self, event):
        if not self.is_capturing or self.start_pos is None:
            # 如果没有有效的起始位置，重置状态
            self.cleanup_ui()
            return
            
        self.end_pos = (event.x, event.y)
        logger.info(f'鼠标释放 - 原始坐标: ({event.x}, {event.y})，去掉dpi后实际屏幕坐标：({event.x/self.dpi}, {event.y/self.dpi})')
        logger.info(f'窗口位置 - x: {self.root.winfo_x()}, y: {self.root.winfo_y()}')
        
        # 保存当前的start_pos和end_pos到临时变量
        self.temp_start_pos = tuple(self.start_pos)
        self.temp_end_pos = (event.x, event.y)
        
        # 清除之前的UI元素
        self.cleanup_ui()
        
        # 创建新的矩形
        self.current_rect_tag = f'rect_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        self.canvas.create_rectangle(
            self.temp_start_pos[0], self.temp_start_pos[1],
            event.x, event.y,
            outline='red', width=2, tags=self.current_rect_tag,
            fill='white', stipple='gray12'
        )
        
        # 创建确认和取消按钮
        self.create_buttons(
            self.temp_start_pos[0], self.temp_start_pos[1],
            event.x, event.y
        )

    def start_screenshot(self):
        """启动截图功能"""
        self.start()
        
    def start(self):
        logger.info('截图工具已启动，请按住鼠标左键选择区域...')
        self.create_overlay()
        self.root.mainloop()


    def draw_square(x1, y1, x2, y2, name):
        import threading
        
        # 创建一个Event用于控制线程退出
        stop_event = threading.Event()
        root = None
        
        def run_ui():
            nonlocal root
            # 根据传递的坐标计算画布的宽度和高度
            canvas_width = max(x1, x2) + 10  # +10 是为了保证画布稍大于矩形
            canvas_height = max(y1, y2) + 10  # 同上，保证画布稍大

            # 创建 Tkinter 主窗口
            root = tk.Tk()
            root.title("Draw Square")

            # 去掉窗口的标题栏和关闭按钮
            root.overrideredirect(1)  # 去掉窗口的边框和关闭按钮

            # 设置窗口完全透明
            root.attributes("-transparentcolor", "gray")  # 设置透明颜色为灰色
            root.attributes('-topmost', True)  # 保持窗口在最顶层

            # 创建一个 Canvas 小部件，使用计算出来的宽度和高度
            canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='gray')  # 设置为灰色背景
            canvas.pack()

            # 创建一个绿色边框，透明填充的矩形
            canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='green',  # 边框颜色为绿色
                width=2,  # 边框宽度为2
                fill='',  # 填充颜色为空，表示透明
                tags=name  # 为矩形添加标签
            )
            
            # 定义更新函数
            def update():
                if stop_event.is_set():
                    root.quit()
                    return
                try:
                    root.update()
                    if not stop_event.is_set():
                        root.after(100, update)  # 每100毫秒更新一次
                except tk.TclError:
                    return
                
            # 启动更新循环
            root.after(0, update)
            
            # 进入主循环
            root.mainloop()
            
        # 创建并启动UI线程
        ui_thread = threading.Thread(target=run_ui, daemon=True)
        ui_thread.start()
        
        def destroy():
            stop_event.set()
            if root:
                try:
                    root.quit()
                    root.destroy()
                except:
                    pass
            ui_thread.join(timeout=1.0)
        
        # 为线程对象添加销毁方法
        ui_thread.destroy = destroy
        
        return ui_thread  # 返回窗口对象以便外部控制