import os
import logging
import config

def setup_logger(base_dir=None):
    """初始化日志配置
    
    Args:
        base_dir: 日志文件存储的基础目录，如果为None则使用当前目录
    """
    if base_dir:
        log_dir = os.path.join(base_dir, 'log')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'sc2_timer.log')
    else:
        log_file = 'sc2_timer.log'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='a'),
            logging.StreamHandler()
        ]
    )

def get_logger(name):
    """获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称，通常使用__name__
    
    Returns:
        Logger: 配置好的日志记录器实例
    """
    return logging.getLogger(name)