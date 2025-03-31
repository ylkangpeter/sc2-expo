import config
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect
import image_util
from logging_util import get_logger

class EnemyRecognizer:
    def __init__(self):
        self.rect_screenshots = []
        self._race = ''
        self._army = ''
        self.logger = get_logger(__name__)
        if config.DEBUG_SHOW_ENEMY_INFO_SQUARE:
            self.init_enemy_info_squares()
    
    def init_enemy_info_squares(self):
        """初始化敌方单位信息框"""
        # 获取屏幕大小
        screen = QApplication.screens()[config.GAME_SCREEN]
        screen_geometry = screen.geometry()
        
        # 获取实际屏幕分辨率
        from ctypes import windll
        user32 = windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        self.logger.info(f"屏幕分辨率: 宽 {screen_geometry.width()}, 高 {screen_geometry.height()}")
        self.logger.info(f"实际屏幕分辨率: 宽 {screen_width}, 高 {screen_height}")
        
        # 绘制 AMON_RACE 矩形
        x1, y1, w1, h1 = (
            screen_width - config.GAME_ICON_POS_AMON_RACE[0],
            screen_height - config.GAME_ICON_POS_AMON_RACE[1],
            config.GAME_ICON_POS_AMON_RACE[2],
            config.GAME_ICON_POS_AMON_RACE[3],
        )
        self.logger.info(f"AMON_RACE: 传入 draw_square 坐标: ({x1}, {y1}), 大小: {w1}x{h1}")
        
        amon_race_rect = image_util.draw_square(x1, y1, w1, h1)
        if amon_race_rect:
            self.logger.info(f"AMON_RACE: draw_square 返回: ({amon_race_rect.x()}, {amon_race_rect.y()}), 大小: {amon_race_rect.width()}x{amon_race_rect.height()}")
            self.rect_screenshots.append({
                "name": "AMON_RACE",
                "input_coords": {"x": x1, "y": y1, "width": w1, "height": h1},
                "returned_rect": amon_race_rect
            })
        
        # 绘制 AMON_TROOPS 矩形
        x2, y2, w2, h2 = (
            screen_width - config.GAME_ICON_POS_AMON_TROOPS[0],
            screen_height - config.GAME_ICON_POS_AMON_TROOPS[1],
            config.GAME_ICON_POS_AMON_TROOPS[2],
            config.GAME_ICON_POS_AMON_TROOPS[3],
        )
        self.logger.info(f"AMON_TROOPS: 传入 draw_square 坐标: ({x2}, {y2}), 大小: {w2}x{h2}")
        
        amon_troops_rect = image_util.draw_square(x2, y2, w2, h2)
        if amon_troops_rect:
            logger.info(f"AMON_TROOPS: draw_square 返回: ({amon_troops_rect.x()}, {amon_troops_rect.y()}), 大小: {amon_troops_rect.width()}x{amon_troops_rect.height()}")
            self.rect_screenshots.append({
                "name": "AMON_TROOPS",
                "input_coords": {"x": x2, "y": y2, "width": w2, "height": h2},
                "returned_rect": amon_troops_rect
            })
    
    def get_race(self):
        """获取当前种族"""
        if config.DEBUG_SHOW_ENEMY_INFO_SQUARE:
            return 'protoss'
        return self._race if self._race else ''
    
    def get_army(self):
        """获取当前军队"""
        if config.DEBUG_SHOW_ENEMY_INFO_SQUARE:
            return 'vanguard_of_aiur'
        return self._army if self._army else ''
    
    def set_race(self, race):
        """设置当前种族"""
        if not config.DEBUG_SHOW_ENEMY_INFO_SQUARE:
            self._race = race
    
    def set_army(self, army):
        """设置当前军队"""
        if not config.DEBUG_SHOW_ENEMY_INFO_SQUARE:
            self._army = army