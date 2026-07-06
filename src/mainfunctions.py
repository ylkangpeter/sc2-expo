# -*- coding: utf-8 -*-

import http.client
import json
import socket
import time
import traceback
from PyQt5 import QtCore
from IdentifyMap import identify_map
import config
from debug_utils import get_mock_data, reset_mock, get_mock_screen_data
from logging_util import get_logger
import show_fence

logger = get_logger(__name__)        

# 全局变量
APP_CLOSING = False
most_recent_playerdata = None
current_game_id = None  # 添加新的全局变量用于标识当前游戏

SC2_API_HOST = "localhost"
SC2_API_PORT = 6119
SC2_REQUEST_TIMEOUT_SECONDS = 6
SC2_REQUEST_ERRORS = (http.client.HTTPException, OSError, TimeoutError, socket.timeout)

troop = None

def get_troop_from_game():
    return troop


def get_sc2_json(path):
    """从 SC2 本地 API 获取 JSON。"""
    connection = http.client.HTTPConnection(
        SC2_API_HOST,
        SC2_API_PORT,
        timeout=SC2_REQUEST_TIMEOUT_SECONDS,
    )
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        data = response.read()
    finally:
        connection.close()

    return json.loads(data.decode("utf-8"))


def check_for_new_game(progress_callback: QtCore.pyqtSignal) -> None:
    global most_recent_playerdata, current_game_id, troop
    
    # 如果是调试模式，重置模拟时间
    if config.debug_mode:
        reset_mock()
    
    # 等待游戏初始化完成
    time.sleep(4)
    
    while True:
        time.sleep(0.5)

        if APP_CLOSING:
            break

        try:
            # 根据调试模式选择数据来源
            if config.debug_mode:
                resp = get_mock_data()
            else:
                resp = get_sc2_json("/game")
            
            players = resp.get('players', list())
            
            # 获取当前游戏时间并更新，无论是否为新游戏
            if 'displayTime' in resp:
                current_time = resp['displayTime']
                # 更新全局变量中的时间
                if most_recent_playerdata is None:
                    most_recent_playerdata = {'time': current_time}
                else:
                    most_recent_playerdata['time'] = current_time
            
            # 生成当前游戏的唯一标识（使用玩家列表的哈希值）
            new_game_id = hash(json.dumps(players, sort_keys=True))
            
            # 如果游戏ID发生变化，说明是新游戏
            if new_game_id != current_game_id:
                current_game_id = new_game_id
                
                # 如果所有玩家都是用户类型，说明是对战模式，跳过
                all_users = True
                for player in players:
                    if player['type'] != 'user':
                        all_users = False

                if all_users:
                    continue

                # 检查玩家数量
                if len(players) <= 2:
                    continue

                # 检查游戏时间变化
                current_time = resp['displayTime']
                
                # 更新全局变量
                most_recent_playerdata = {
                    'time': current_time,
                    'map': resp.get('map')
                }

                # 识别地图
                try:
                    # 从游戏API获取地图数据
                    map_found = identify_map(players)
                    
                    if map_found:
                        # 发送信号更新下拉列表
                        progress_callback.emit(['update_map', map_found])
                        # 更新全局变量中的地图信息
                        most_recent_playerdata['map'] = map_found
                
                except Exception:
                    logger.error(f'地图识别出错: {traceback.format_exc()}')
                
                troop = None
                def troop_detection_callback(result):
                    global troop
                    if result['success']:
                        troop = result['match']
                    else:
                        troop = None
                
                show_fence.detect_troop(troop_detection_callback)
            
        except SC2_REQUEST_ERRORS:
            pass

        except json.decoder.JSONDecodeError:
            pass

        except Exception:
            logger.error(traceback.format_exc())

def get_game_screen() -> str:
    """获取当前游戏界面状态
    
    Returns:
        str: 返回当前界面状态
            - 'matchmaking': 匹配界面
            - 'in_game': 游戏中
            - 'unknown': 未知状态或请求失败
    """
    try:
        # 根据调试模式选择数据来源
        if config.debug_mode:
            resp = get_mock_screen_data()
        else:
            # 请求游戏UI状态API
            resp = get_sc2_json("/ui")
        
        # 获取activeScreens数组
        active_screens = resp.get('activeScreens', [])
        
        # 判断界面状态：数组不为空表示在匹配界面，为空表示在游戏中
        if active_screens:
            return 'matchmaking'
        else:
            return 'in_game'
            
    except SC2_REQUEST_ERRORS:
        logger.debug('SC2请求失败。游戏未运行。')
        return 'unknown'
    except json.decoder.JSONDecodeError:
        logger.info('SC2请求json解码失败（SC2正在启动或关闭）')
        return 'unknown'
    except Exception:
        logger.error(f'获取游戏界面状态出错: {traceback.format_exc()}')
        return 'unknown'
