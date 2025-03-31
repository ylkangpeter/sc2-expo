import os
import sys
import shutil
import zipfile
import argparse
from datetime import datetime

def clean_build_folders():
    """清理构建文件夹和旧的压缩包"""
    # 清理文件夹
    folders_to_clean = ['build', 'dist']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"清理 {folder} 文件夹...")
            shutil.rmtree(folder)
    
    # 清理旧的zip文件
    zip_file = "SC2_Timer.zip"
    if os.path.exists(zip_file):
        print(f"删除旧的压缩包: {zip_file}")
        os.remove(zip_file)

def create_zip():
    """创建zip压缩包"""
    print("\n开始创建压缩包...")
    zip_file = os.path.join('dist', "SC2_Timer.zip")
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加exe文件
        exe_path = os.path.join('dist', 'SC2 Timer.exe')
        if os.path.exists(exe_path):
            print(f"添加文件: SC2 Timer.exe")
            zipf.write(exe_path, 'SC2 Timer.exe')
        
        # 添加resources文件夹
        resources_dir = os.path.join('dist', 'resources')
        if os.path.exists(resources_dir):
            print("添加resources文件夹...")
            for root, _, files in os.walk(resources_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'dist')
                    print(f"添加文件: {arcname}")
                    zipf.write(file_path, arcname)
        
        # 添加ico文件夹
        ico_dir = os.path.join('dist', 'ico')
        if os.path.exists(ico_dir):
            print("添加ico文件夹...")
            for root, _, files in os.walk(ico_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'dist')
                    print(f"添加文件: {arcname}")
                    zipf.write(file_path, arcname)
        
        # 添加config.py
        config_path = os.path.join('dist', 'config.py')
        if os.path.exists(config_path):
            print(f"添加文件: config.py")
            zipf.write(config_path, 'config.py')
        
        # 添加说明.txt
        readme_path = os.path.join('dist', '说明.txt')
        if os.path.exists(readme_path):
            print(f"添加文件: 说明.txt")
            zipf.write(readme_path, '说明.txt')
    
    print(f"\n压缩包创建完成: {zip_file}")


def build_exe(use_upx=False):
    """使用PyInstaller打包应用"""
    # 确保当前目录是项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 清理之前的构建文件
    clean_build_folders()
    
    # 构建命令
    build_cmd = (
        "pyinstaller "
        "--name=\"SC2 Timer\" "
        "--icon=ico/fav.ico "
        "--windowed "
        "--onefile "
        "--clean "
        "--add-data=\"img;img\" "
        f"{'--upx-dir=upx-4.2.1-win64 ' if use_upx else ''}"
        "--exclude-module=matplotlib "
        "--exclude-module=notebook "
        "--exclude-module=scipy "
        "--exclude-module=pandas "
        "--exclude-module=PyQt5.QtNetwork "
        "--exclude-module=PyQt5.QtWebEngine "
        "--exclude-module=PyQt5.QtWebEngineCore "
        "--exclude-module=PyQt5.QtWebEngineWidgets "
        "--exclude-module=PyQt5.QtSql "
        "--exclude-module=PyQt5.QtXml "
        "src/main.py"
    )
    
    # 创建dist/resources目录，但不打包到exe中
    resources_dist_dir = os.path.join('dist', 'resources')
    if not os.path.exists(resources_dist_dir):
        os.makedirs(resources_dist_dir)
    
    # 复制resources目录内容到dist/resources
    print("复制resources目录到dist文件夹...")
    if os.path.exists('resources'):
        for item in os.listdir('resources'):
            src_path = os.path.join('resources', item)
            dst_path = os.path.join(resources_dist_dir, item)
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
    
    # 复制ico目录到dist
    print("复制ico目录到dist文件夹...")
    ico_dist_dir = os.path.join('dist', 'ico')
    if os.path.exists('ico'):
        if os.path.exists(ico_dist_dir):
            shutil.rmtree(ico_dist_dir)
        shutil.copytree('ico', ico_dist_dir)
    
    # 复制config.py到dist目录
    print("复制config.py到dist文件夹...")
    shutil.copy2(os.path.join('src', 'config.py'), os.path.join('dist', 'config.py'))
    
    # 复制说明.txt到dist目录
    print("复制说明.txt到dist文件夹...")
    shutil.copy2('说明.txt', os.path.join('dist', '说明.txt'))
    
    print("开始构建可执行文件...")
    print(f"执行命令: {build_cmd}")
    
    # 执行构建命令
    result = os.system(build_cmd)
    
    if result == 0:
        print("\n构建成功!")
        print("可执行文件位于 dist 文件夹中")
        # 创建zip压缩包
        create_zip()
    else:
        print("\n构建失败!")
        print("请检查错误信息并修复问题")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='构建SC2 Timer可执行文件')
    parser.add_argument('--upx', type=int, choices=[0, 1], default=0,
                        help='是否使用UPX压缩（0：不压缩，1：压缩）')
    args = parser.parse_args()

    # 检查是否已安装PyInstaller
    try:
        import PyInstaller
        print(f"已检测到PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("未检测到PyInstaller，正在安装...")
        os.system("pip install pyinstaller")
        print("PyInstaller安装完成")
    
    # 执行构建
    build_exe(use_upx=bool(args.upx))

if __name__ == "__main__":
    main()