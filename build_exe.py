import os
import sys
import shutil

def clean_build_folders():
    """清理构建文件夹"""
    folders_to_clean = ['build', 'dist']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"清理 {folder} 文件夹...")
            shutil.rmtree(folder)

def build_exe():
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
    
    print("开始构建可执行文件...")
    print(f"执行命令: {build_cmd}")
    
    # 执行构建命令
    result = os.system(build_cmd)
    
    if result == 0:
        print("\n构建成功!")
        print("可执行文件位于 dist 文件夹中")
    else:
        print("\n构建失败!")
        print("请检查错误信息并修复问题")

def main():
    # 检查是否已安装PyInstaller
    try:
        import PyInstaller
        print(f"已检测到PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("未检测到PyInstaller，正在安装...")
        os.system("pip install pyinstaller")
        print("PyInstaller安装完成")
    
    # 执行构建
    build_exe()

if __name__ == "__main__":
    main()