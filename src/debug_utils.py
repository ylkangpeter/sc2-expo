import time
import threading
from typing import Dict, Optional

def format_time_to_mmss(seconds: float) -> str:
    """将秒数转换为MM:SS格式"""
    minutes = int(seconds) // 60
    remaining_seconds = int(seconds) % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"

class GameTimeMock:
    def __init__(self, time_factor: float = 1.0):
        self._game_start_time = time.time()  # 游戏开始时间
        self._time_factor = time_factor
        self._paused = False
        self._pause_time = 0
        self._total_pause_time = 0
        self._lock = threading.Lock()
        
    def reset(self):
        """重置游戏时间到0"""
        with self._lock:
            self._game_start_time = time.time()
            self._paused = False
            self._pause_time = 0
            self._total_pause_time = 0
    
    def pause(self):
        """暂停游戏时间"""
        with self._lock:
            if not self._paused:
                self._paused = True
                self._pause_time = time.time()
    
    def resume(self):
        """恢复游戏时间"""
        with self._lock:
            if self._paused:
                self._paused = False
                self._total_pause_time += time.time() - self._pause_time
    
    def set_time_factor(self, factor: float):
        """设置时间流速因子"""
        with self._lock:
            self._time_factor = factor
    
    def get_current_time(self) -> float:
        """获取当前游戏时间（秒）"""
        with self._lock:
            if self._paused:
                elapsed = self._pause_time - self._game_start_time - self._total_pause_time
            else:
                elapsed = time.time() - self._game_start_time - self._total_pause_time
            return elapsed * self._time_factor

    def get_game_data(self) -> Dict:
        """模拟游戏API返回的数据结构"""
        return {
            'displayTime': self.get_current_time(),
            'players': [
                {'id': 1, 'type': 'computer', 'name': 'AI Player'}
            ]  # 添加一个AI玩家以通过游戏检查
        }

# 全局实例
_game_time_mock: Optional[GameTimeMock] = None

def init_mock(time_factor: float = 1.0):
    """初始化模拟器"""
    global _game_time_mock
    _game_time_mock = GameTimeMock(time_factor)

def reset_mock():
    """重置游戏时间"""
    if _game_time_mock is not None:
        _game_time_mock.reset()

def get_mock_data() -> Dict:
    """获取模拟的游戏数据"""
    global _game_time_mock
    if _game_time_mock is None:
        from config import debug_time_factor  # 延迟导入以避免循环依赖
        init_mock(debug_time_factor)
    return _game_time_mock.get_game_data()

def set_time_factor(factor: float):
    """设置时间流速"""
    if _game_time_mock is None:
        init_mock(factor)
    else:
        _game_time_mock.set_time_factor(factor)

def pause_game():
    """暂停游戏时间"""
    if _game_time_mock is not None:
        _game_time_mock.pause()

def resume_game():
    """恢复游戏时间"""
    if _game_time_mock is not None:
        _game_time_mock.resume()