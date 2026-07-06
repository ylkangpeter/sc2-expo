# -*- coding: utf-8 -*-

import os
import sys


def use_external_config_if_present():
    # 检查当前目录是否存在config.py文件，如果存在则添加当前目录到sys.path
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, "config.py")
    if os.path.exists(config_path):
        sys.path.insert(0, current_dir)
        print(f"使用外部配置文件: {config_path}")


use_external_config_if_present()

def main():
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    import logging_util
    import show_fence
    from qt_gui import TimerWindow

    logging_util.setup_logger()
    # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # 启用高DPI图标
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    # 禁用原生对话框和原生小部件，确保统一的DPI缩放
    QApplication.setAttribute(Qt.AA_DontUseNativeDialogs)
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    app = QApplication(sys.argv)
    # 设置DPI缩放策略为PassThrough，确保精确的DPI缩放
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app.timer_window = TimerWindow()
    show_fence.show_square()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
