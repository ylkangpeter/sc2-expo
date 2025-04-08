import time
import json
import traceback
import requests
from PyQt5 import QtCore
from map_processor import MapProcessor
from IdentifyMap import identify_map
import config
from debug_utils import get_mock_data, reset_mock, get_mock_screen_data
from logging_util import get_logger
import show_fence

logger = get_logger(__name__)        

# 全局变量
APP_CLOSING = False
most_recent_playerdata = None
player_winrate_data = []
PLAYER_NAMES = []
current_game_id = None  # 添加新的全局变量用于标识当前游戏

# 创建session用于HTTP请求
session = requests.Session()

troop = None

def get_troop_from_game():
    return troop

def check_for_new_game(progress_callback: QtCore.pyqtSignal) -> None:
    global most_recent_playerdata, current_game_id
    
    logger.info('check_for_new_game函数启动')
    
    # 如果是调试模式，重置模拟时间
    if config.debug_mode:
        reset_mock()
    
    # 等待游戏初始化完成
    time.sleep(4)
    logger.info('游戏初始化等待完成')
    
    # 用于识别新游戏的变量
    last_game_time = None
    
    while True:
        time.sleep(0.5)

        if APP_CLOSING:
            logger.info('检测到应用程序正在关闭，退出check_for_new_game循环')
            break

        try:
            # 根据调试模式选择数据来源
            if config.debug_mode:
                resp = get_mock_data()
            else:
                resp = session.get('http://localhost:6119/game', timeout=6).json()
            
            players = resp.get('players', list())
            
            # 获取当前游戏时间并更新，无论是否为新游戏
            if 'displayTime' in resp:
                current_time = resp['displayTime']
                # 更新全局变量中的时间
                if most_recent_playerdata is None:
                    most_recent_playerdata = {'time': current_time}
                else:
                    most_recent_playerdata['time'] = current_time
                logger.debug(f'更新游戏时间: {current_time}')
            
            # 生成当前游戏的唯一标识（使用玩家列表的哈希值）
            new_game_id = hash(json.dumps(players, sort_keys=True))
            
            # 如果游戏ID发生变化，说明是新游戏
            if new_game_id != current_game_id:
                current_game_id = new_game_id
                logger.info('检测到新游戏，准备更新地图信息')
                
                logger.debug(f'从游戏服务器获取数据: 显示时间={resp.get("displayTime")}, 玩家数量={len(players)}')

                # 如果所有玩家都是用户类型，说明是对战模式，跳过
                all_users = True
                for player in players:
                    if player['type'] != 'user':
                        all_users = False

                if all_users:
                    logger.debug('检测到对战模式，跳过处理')
                    continue

                # 检查玩家数量
                if len(players) <= 2:
                    logger.debug(f'玩家数量不足: 玩家数量={len(players)}')
                    continue

                # 检查游戏时间变化
                current_time = resp['displayTime']
                logger.info(f'从服务器获取的原始时间数据: {current_time}')
                
                # 更新全局变量
                most_recent_playerdata = {
                    'time': current_time,
                    'map': resp.get('map')
                }
                logger.info(f'更新全局变量: {most_recent_playerdata}')

                last_game_time = current_time
                formatted_time = time.strftime("%M:%S", time.gmtime(current_time))
                logger.info(f'游戏时间更新: {formatted_time} (格式化后), 原始数据: {current_time}')
                # Find ally player and get your current player position
                # Add the first player name that's not the main player. This could be expanded to any number of players.
                
                player_names = list()
                player_position = 1
                for player in players:
                    if player['id'] in {1, 2}  and player['type'] != 'computer':
                        player_names.append(player['name'])
                        player_position = 2 if player['id'] == 1 else 1
                        break

                # 识别地图
                try:
                    logger.info('开始识别地图...')
                    logger.info(f'玩家数据: {json.dumps(players, ensure_ascii=False, indent=2)}')
                    # 从游戏API获取地图数据
                    map_found = identify_map(players)
                    
                    if map_found:
                        logger.info(f'地图识别成功: {map_found}')
                        # 发送信号更新下拉列表
                        progress_callback.emit(['update_map', map_found])
                        # 更新全局变量中的地图信息
                        most_recent_playerdata['map'] = map_found
                        logger.info(f'更新全局变量地图信息: {map_found}')
                    else:
                        logger.error('地图识别失败:')
                        logger.error(f'- 原因: 无法从API响应中获取地图名称')
                
                except Exception:
                    logger.error(f'地图识别出错: {traceback.format_exc()}')
                
                troop = None
                def troop_detection_callback(result):
                    if result['success']:
                        logger.info(f"检测到部队: {result['match']}, 相似度: {result['similarity']}")
                        troop = result['match']
                    else:
                        logger.info(f"部队检测失败: {result['reason']}")
                        troop = None
                
                show_fence.detect_troop(troop_detection_callback)
            
        except requests.exceptions.ConnectionError:
            logger.debug('SC2请求失败。游戏未运行。')

        except json.decoder.JSONDecodeError:
            logger.info('SC2请求json解码失败（SC2正在启动或关闭）')

        except requests.exceptions.ReadTimeout:
            logger.info('SC2请求超时')

        except Exception:
            logger.info(traceback.format_exc())

def get_player_data(player_names):
    """获取玩家数据"""
    # TODO: 实现获取玩家数据的逻辑
    return {}

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
            resp = session.get('http://localhost:6119/ui', timeout=6).json()
        
        # 获取activeScreens数组
        active_screens = resp.get('activeScreens', [])
        
        # 判断界面状态：数组不为空表示在匹配界面，为空表示在游戏中
        if active_screens:
            return 'matchmaking'
        else:
            return 'in_game'
            
    except requests.exceptions.ConnectionError:
        logger.debug('SC2请求失败。游戏未运行。')
        return 'unknown'
    except json.decoder.JSONDecodeError:
        logger.info('SC2请求json解码失败（SC2正在启动或关闭）')
        return 'unknown'
    except requests.exceptions.ReadTimeout:
        logger.info('SC2请求超时')
        return 'unknown'
    except Exception:
        logger.error(f'获取游戏界面状态出错: {traceback.format_exc()}')
        return 'unknown'