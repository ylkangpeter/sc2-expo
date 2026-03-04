import os
import sys
from PIL import Image
import numpy as np
from fileutil import get_resources_dir, list_files
from logging_util import get_logger, setup_logger
logger = get_logger(__name__)

class LightweightImageCache:
    def __init__(self):
        self.cache = {}
        self.last_scan_time = None
        
    def add_image(self, image_path):
        try:
            img = Image.open(image_path)
            if img is not None:
                self.cache[image_path] = img
                logger.warning(f'已加载图片到缓存: {image_path}')
            else:
                logger.error(f'无法加载图片: {image_path}')
        except Exception as e:
            logger.error(f'加载图片时发生错误: {str(e)}')
            
    def scan_directory(self):
        troops_dir = get_resources_dir('resources', 'screen_capcture', 'troops')
        if not troops_dir:
            logger.error('无法找到troops目录')
            return
            
        if not os.path.exists(troops_dir):
            os.makedirs(troops_dir)
            logger.warning(f'创建troops目录: {troops_dir}')
            return
        
        logger.info(f'开始扫描troops目录: {troops_dir}')
            
        current_files = set(f for f in list_files(troops_dir) if f.lower().endswith('.png'))
        cached_files = set(os.path.basename(p) for p in self.cache.keys())
        
        # 找出新增的文件
        new_files = current_files - cached_files
        if new_files:
            for file in new_files:
                full_path = os.path.join(troops_dir, file)
                self.add_image(full_path)
                
        self.last_scan_time = None
        
    def mse(self, img1, img2):
        """计算均方误差"""
        # 确保图片大小一致
        img1 = img1.resize(img2.size)
        
        # 转换为灰度图
        img1_gray = img1.convert('L')
        img2_gray = img2.convert('L')
        
        # 转换为numpy数组
        arr1 = np.array(img1_gray)
        arr2 = np.array(img2_gray)
        
        # 计算均方误差
        diff = arr1 - arr2
        mse_value = np.mean(diff ** 2)
        
        return mse_value
    
    def get_most_similar_image(self, target_img):
        if not self.cache:
            logger.warning('图片缓存为空')
            return None, 0.0
            
        min_mse = float('inf')
        best_match = None
        
        for path, cached_img in self.cache.items():
            try:
                # 计算MSE
                mse_value = self.mse(target_img, cached_img)
                # 转换为相似度分数（MSE越小，相似度越高）
                score = 1.0 / (1.0 + mse_value)
                logger.info(f'与图片 {os.path.basename(path)} 的相似度: {score}')
                
                if score > min_mse:
                    min_mse = score
                    best_match = path
            except Exception as e:
                logger.error(f'比较图片时发生错误: {str(e)}')
                continue
        best_match = os.path.splitext(os.path.basename(best_match))[0] 
        return best_match, min_mse
        
    def compare_images(self, image_stream):
        """比较图像与缓存中的所有图像的相似度
        Args:
            image_stream: 图像数据流
        Returns:
            tuple: (最相似图片的路径, 相似度值)
        """
        try:
            # 扫描并更新图片缓存
            self.scan_directory()
            
            # 读取数据流中的图像
            from io import BytesIO
            img = Image.open(BytesIO(image_stream))
            
            if img is None:
                logger.error('无法读取图像数据流')
                return None, 0.0
                
            # 在缓存中查找最相似的图片
            best_match, max_score = self.get_most_similar_image(img)
            
            if best_match:
                logger.info(f'找到最相似的图片: {os.path.basename(best_match)}，相似度: {max_score}')
            else:
                logger.warning('未找到相似的图片')
                
            return best_match, max_score
            
        except Exception as e:
            logger.error(f'比较图像时发生错误: {str(e)}')
            import traceback
            logger.error(traceback.format_exc())
            return None, 0.0
