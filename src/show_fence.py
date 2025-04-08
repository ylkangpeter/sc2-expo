import image_util
import config
import importlib
import threading
import time
import io
from logging_util import get_logger
logger = get_logger(__name__)

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
        return  {'success': False, 'reason': 'not enabled'}
    # 创建ScreenshotTool实例
    screenshot_tool = image_util.ScreenshotTool()
    # 创建ImageCache实例
    image_cache = image_util.ImageCache()
    
    found = False
    def detect_loop():
        start_time = time.time()
        result = None
        while not found:
            # 检查是否超过4分钟
            if time.time() - start_time > config.GAME_ICO_RECONGIZE_TIMEOUT:
                found = True
                logger.info("超过4分钟未找到最佳匹配，退出循环")
                result = {'success': False, 'reason': 'timeout'}
                break
            
            importlib.reload(config)
            x1, y1, x2, y2 = config.GAME_ICON_POS_AMON_TROOPS
            pil_image = screenshot_tool.capture_screen_core([x1,y1],[x2,y2], False)
            logger.info(f"开始探索截图区域 {x1},{y1},{x2},{y2}")
            if pil_image:
                logger.info(f"截图成功")
                # 将PIL图像转换为字节流
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                # 调用compare_images方法进行图像比对
                best_match, similarity = image_cache.compare_images(img_byte_arr)
                if similarity >= config.GAME_ICO_RECONGIZE_CONFIDENCE:
                    logger.info(f"最佳匹配: {best_match}, 相似度: {similarity}")
                    found = True
                    result = {'success': True, 'match': best_match, 'similarity': similarity}
            time.sleep(config.GAME_ICO_RECONGIZE_INTERVAL)
        
        if callback:
            callback(result)
            
    threading.Thread(target=detect_loop, daemon=True).start()
    

        
