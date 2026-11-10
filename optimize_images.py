# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
from PIL import Image

def compress_image(input_path, output_path, quality=85):
    """压缩图像文件"""
    try:
        extension = os.path.splitext(input_path)[1].lower()
        if extension in ('.svg', '.ico', '.gif', '.bmp'):
            if os.path.abspath(input_path) != os.path.abspath(output_path):
                shutil.copy2(input_path, output_path)
            return True

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension or '.tmp') as temp_file:
            temp_path = temp_file.name

        try:
            img = Image.open(input_path)
            if extension == '.png':
                img.save(temp_path, 'PNG', optimize=True, compress_level=9)
            elif extension in ('.jpg', '.jpeg'):
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                img.save(temp_path, 'JPEG', quality=quality, optimize=True)
            elif extension == '.webp':
                img.save(temp_path, 'WEBP', quality=quality, method=6)
            else:
                img.save(temp_path, optimize=True)

            if os.path.abspath(input_path) == os.path.abspath(output_path):
                if os.path.getsize(temp_path) < os.path.getsize(input_path):
                    shutil.move(temp_path, output_path)
                else:
                    os.remove(temp_path)
            else:
                shutil.move(temp_path, output_path)
            return True
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
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
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.ico', '.svg', '.webp')):
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
    # 优化发行包中的图片目录
    optimize_images('ico')
    optimize_images('img')
    optimize_images(os.path.join('resources', 'artifacts'))
    print("\n图像优化完成!")
