import os
import sys
import logging

logger = logging.getLogger(__name__)

def get_resources_dir(*subdirs):
    """
    获取资源目录的路径，支持多级子目录
    :param subdirs: 子目录路径，可以传入多个参数
    :return: 完整的目录路径
    """
    # 获取当前工作目录
    current_dir = os.getcwd()
    # 将当前工作目录与子目录路径拼接
    resource_dir = os.path.join(current_dir, *subdirs)
    
    # 如果当前工作目录没有找到资源目录，则尝试在程序目录查找
    if not os.path.exists(resource_dir):
        logger.info(f'当前工作目录下未找到目录，尝试在程序目录查找')
        program_dir = os.path.dirname(os.path.dirname(__file__))
        resource_dir = os.path.join(program_dir, *subdirs)
    
    # 如果在程序目录也没有找到资源目录，尝试在 exe 目录下查找
    if not os.path.exists(resource_dir):
        logger.info(f'程序目录下也未找到目录，尝试在打包后的 exe 所在目录查找')
        if getattr(sys, 'frozen', False):  # 判断是否是打包后的 exe 文件
            program_dir = os.path.dirname(sys.executable)
            resource_dir = os.path.join(program_dir, *subdirs)
    
    if not os.path.exists(resource_dir):
        logger.error(f'资源目录不存在: {resource_dir}')
        return None
    
    logger.info(f'使用资源目录: {resource_dir}')
    return resource_dir

def list_files(directory):
    """
    列出指定目录下的所有文件
    :param directory: 目录路径
    :return: 文件列表
    """
    if not directory or not os.path.exists(directory):
        return []
    
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def get_file_path(directory, filename):
    """
    获取文件的完整路径
    :param directory: 目录路径
    :param filename: 文件名
    :return: 文件的完整路径
    """
    if not directory or not filename:
        return None
    
    return os.path.join(directory, filename)