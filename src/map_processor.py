import os
from logging_util import get_logger
import json

logger = get_logger(__name__)

class MapProcessor:
    def __init__(self):
        self.map_templates = {}
        self.load_map_templates()

    def load_map_templates(self):
        """加载地图模板数据"""
        try:
            from fileutil import get_resources_dir
            resources_dir = get_resources_dir('resources', 'maps', 'zh')
            if not resources_dir:
                return

            # 遍历resources目录下的所有地图模板文件
            for map_name in os.listdir(resources_dir):
                map_path = os.path.join(resources_dir, map_name)
                if os.path.isdir(map_path):
                    try:
                        # 加载地图配置
                        config_path = os.path.join(map_path, 'config.json')
                        if os.path.exists(config_path):
                            with open(config_path, 'r', encoding='utf-8') as f:
                                self.map_templates[map_name] = json.load(f)
                        else:
                            logger.error(f'无法加载地图模板: {map_name}')
                    except Exception as e:
                        logger.error(f'加载地图模板 {map_name} 时出错: {str(e)}')

            logger.info(f'成功加载 {len(self.map_templates)} 个地图模板')

        except Exception as e:
            logger.error(f'加载地图模板时出错: {str(e)}')

    def get_map_info(self, map_name):
        """获取地图信息
        
        Args:
            map_name (str): 地图名称
            
        Returns:
            dict: 地图配置信息
        """
        return self.map_templates.get(map_name)

    def get_all_maps(self):
        """获取所有已加载的地图列表
        
        Returns:
            list: 地图名称列表
        """
        return list(self.map_templates.keys())