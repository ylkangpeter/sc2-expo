import os
import cv2
from PIL import Image
import numpy as np

def compress_image(input_path, output_path, quality=85):
    """压缩图像文件"""
    try:
        # 处理不同类型的图像
        if input_path.lower().endswith('.svg'):
            # SVG文件保持不变
            import shutil
            shutil.copy2(input_path, output_path)
            return True
        elif input_path.lower().endswith('.ico'):
            # ICO文件保持不变
            import shutil
            shutil.copy2(input_path, output_path)
            return True
        else:
            # 处理其他图像格式
            img = Image.open(input_path)
            # 保存为JPEG格式，降低质量
            if img.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3是alpha通道
                background.save(output_path, 'JPEG', quality=quality)
            else:
                img.save(output_path, 'JPEG', quality=quality)
            return True
    except Exception as e:
        print(f"压缩图像 {input_path} 时出错: {e}")
        return False

def optimize_images(directory):
    """优化目录中的所有图像文件"""
    print(f"开始优化 {directory} 目录中的图像...")
    total_size_before = 0
    total_size_after = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.ico', '.svg')):
                input_path = os.path.join(root, file)
                output_path = input_path
                
                # 计算原始大小
                size_before = os.path.getsize(input_path)
                total_size_before += size_before
                
                # 压缩图像
                success = compress_image(input_path, output_path)
                
                if success:
                    # 计算压缩后大小
                    size_after = os.path.getsize(output_path)
                    total_size_after += size_after
                    
                    # 计算压缩率
                    if size_before > 0:
                        compression_ratio = (1 - size_after / size_before) * 100
                        print(f"压缩 {file}: {size_before/1024:.2f}KB -> {size_after/1024:.2f}KB ({compression_ratio:.1f}% 压缩)")
    
    # 计算总体压缩效果
    if total_size_before > 0:
        total_compression = (1 - total_size_after / total_size_before) * 100
        print(f"\n总体压缩效果: {total_size_before/1024:.2f}KB -> {total_size_after/1024:.2f}KB ({total_compression:.1f}% 压缩)")
    else:
        print("没有找到可压缩的图像文件")

if __name__ == "__main__":
    # 优化ico和img目录
    optimize_images('ico')
    optimize_images('img')
    print("\n图像优化完成!")
