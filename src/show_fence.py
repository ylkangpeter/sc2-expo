# -*- coding: utf-8 -*-

import image_util
import config
import importlib
import threading
import time
import io
from logging_util import get_logger
logger = get_logger(__name__)


class TroopDetectionJob:
    """Handle for a cancellable background troop detection run."""

    def __init__(self, thread, stop_event):
        self.thread = thread
        self.stop_event = stop_event

    def cancel(self):
        self.stop_event.set()

    def is_alive(self):
        return self.thread.is_alive()

    def join(self, timeout=None):
        self.thread.join(timeout=timeout)

def show_square():
    if not config.DEBUG_SHOW_ENEMY_INFO_SQUARE:
        return
    thread = None
    def draw_loop():
        while True:
            importlib.reload(config)
            x1, y1, x2, y2 = config.GAME_ICON_POS_AMON_TROOPS
            nonlocal thread
            if thread:
                thread.destroy()
            x1 = max(0, x1 - 3)
            y1 = max(0, y1 - 3)
            x2 = x2 + 3
            y2 = y2 + 3
            thread = image_util.ScreenshotTool.draw_square(x1, y1, x2, y2, "amon_troops")
            time.sleep(config.GAME_ICON_POS_SHOW_RELOAD_INTERVAL)
            logger.info(f"sleep {config.GAME_ICON_POS_SHOW_RELOAD_INTERVAL} second and redraw {config.GAME_ICON_POS_AMON_TROOPS}")
    
    threading.Thread(target=draw_loop, daemon=True).start()

def detect_troop(callback=None):
    if not config.DEBUG_SHOW_ENEMY_INFO_SQUARE:
        result = {'success': False, 'reason': 'not enabled'}
        if callback:
            callback(result)
        return result

    try:
        # 创建ScreenshotTool实例
        screenshot_tool = image_util.ScreenshotTool()
        # 创建ImageCache实例
        image_cache = image_util.ImageCache()
    except Exception as exc:
        logger.error(f'初始化部队识别失败: {exc}')
        result = {'success': False, 'reason': 'initialization_error'}
        if callback:
            callback(result)
        return result
    
    found = False
    stop_event = threading.Event()
    def detect_loop():
        nonlocal found
        start_time = time.time()
        result = None
        try:
            while not found:
                if stop_event.is_set():
                    found = True
                    result = {'success': False, 'reason': 'cancelled'}
                    break
                # 检查是否超过配置的识别超时
                if time.time() - start_time > config.GAME_ICO_RECONGIZE_TIMEOUT:
                    found = True
                    logger.info("超过识别超时，退出循环")
                    result = {'success': False, 'reason': 'timeout'}
                    break

                importlib.reload(config)
                x1, y1, x2, y2 = config.GAME_ICON_POS_AMON_TROOPS
                pil_image = screenshot_tool.capture_screen_core([x1, y1], [x2, y2], False)
                logger.info(f"开始探索截图区域 {x1},{y1},{x2},{y2}")
                if pil_image:
                    logger.info("截图成功")
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='PNG')
                    best_match, similarity = image_cache.compare_images(img_byte_arr.getvalue())
                    if similarity >= config.GAME_ICO_RECONGIZE_CONFIDENCE:
                        logger.info(f"最佳匹配: {best_match}, 相似度: {similarity}")
                        found = True
                        result = {'success': True, 'match': best_match, 'similarity': similarity}
                if found:
                    break
                if not stop_event.wait(config.GAME_ICO_RECONGIZE_INTERVAL):
                    continue
                found = True
                result = {'success': False, 'reason': 'cancelled'}
        except Exception as exc:
            logger.error(f'部队识别失败: {exc}')
            found = True
            result = {'success': False, 'reason': 'recognition_error'}
        finally:
            if callback:
                callback(result or {'success': False, 'reason': 'unknown'})
            
    thread = threading.Thread(target=detect_loop, daemon=True)
    job = TroopDetectionJob(thread, stop_event)
    thread.start()
    return job
    

        
