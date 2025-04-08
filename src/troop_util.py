from logging import Logger
import os
import fileutil
import logging_util

logger=logging_util.get_logger(__name__)

class TroopLoader:
    def __init__(self):
        self.troop_cache = {}
        self.name_mapping = {}
        self.army_cache = {}
        self.army_name_mapping = {}
        self.init_troop_loader()

    def init_troop_loader(self):
        troops_dir = fileutil.get_resources_dir('resources', 'troops')
        if not troops_dir:
            logger.error('无法找到troops目录')
            return
        
        # 遍历所有种族目录并建立army缓存
        for race_name in os.listdir(troops_dir):
            race_dir = os.path.join(troops_dir, race_name)
            if os.path.isdir(race_dir):
                # 获取army配置文件列表
                army_files = fileutil.list_files(race_dir)
                self.army_cache[race_name] = army_files
                
                # 解析army名称并建立映射关系
                for army_file in army_files:
                    name_parts = os.path.splitext(army_file)[0].split('-')
                    if len(name_parts) == 2:
                        # 假设第一部分是中文名，第二部分是英文名
                        self.army_name_mapping[name_parts[0]] = race_name  # 中文名映射
                        self.army_name_mapping[name_parts[1]] = race_name  # 英文名映射
                
                # 遍历种族目录下的所有文件
                for troop_file in army_files:
                    file_path = fileutil.get_file_path(race_dir, troop_file)
                    if file_path:
                        try:
                            logger.info(f'=====加载兵种配置文件：{file_path} ====')                            
                            # 读取文件内容并构建缓存
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                troop_dict = {}
                                for line in lines:
                                    line = line.strip()
                                    if line and not line.startswith('#'):                            
                                        logger.info(f'{line}')
                                        parts = line.split('\t')
                                        if len(parts) >= 2:
                                            troop_dict[parts[0]] = parts[1]
                                
                                # 使用文件名作为key存储到缓存中
                                self.troop_cache[troop_file] = troop_dict
                                
                                # 解析文件名并建立映射关系
                                name_parts = os.path.splitext(troop_file)[0].split('-')
                                if len(name_parts) == 2:
                                    # 假设第一部分是中文名，第二部分是英文名
                                    self.name_mapping[name_parts[0]] = troop_file  # 中文名映射
                                    self.name_mapping[name_parts[1]] = troop_file  # 英文名映射
                        except Exception as e:
                            logger.error(f'读取文件{file_path}失败: {str(e)}')

    def get_troop_config(self, troop, level):
        # 先通过映射获取实际的文件名
        logger.info(f'获取兵种配置：{troop} T{level}')
        actual_file_name = self.name_mapping.get(troop, troop)
        logger.info(f'获取兵种配置-数据文件：{actual_file_name} T{level}')
        if actual_file_name in self.troop_cache and str(level) in self.troop_cache[actual_file_name]:
            return self.troop_cache[actual_file_name][str(level)]
        return None

    def get_army(self, army_name):
        # 通过中文或英文名称获取军队类型
        logger.info(f'获取军队类型：{army_name}')
        return self.army_name_mapping.get(army_name)