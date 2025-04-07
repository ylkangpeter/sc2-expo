import image_util
import config
import importlib
import threading
import time

def show_square():
    thread = None
    def draw_loop():
        while True:
            importlib.reload(config)
            x, y, w, h = config.GAME_ICON_POS_AMON_TROOPS
            nonlocal thread
            if thread:
                thread.destroy()
            thread = image_util.ScreenshotTool.draw_square(x, y, w, h, "amon_troops")
            time.sleep(config.GAME_ICON_POS_SHOW_RELOAD_INTERVAL)
    
    threading.Thread(target=draw_loop, daemon=True).start()