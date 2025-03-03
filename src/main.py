import os
import sys

# 检查当前目录是否存在config.py文件，如果存在则添加当前目录到sys.path
current_dir = os.getcwd()
if os.path.exists(os.path.join(current_dir, 'config.py')):
    sys.path.insert(0, current_dir)
    print(f"使用外部配置文件: {os.path.join(current_dir, 'config.py')}")

from qt_gui import TimerWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication

def main():
    # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # 设置DPI缩放因子的舍入策略
    QGuiApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    timer = TimerWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()