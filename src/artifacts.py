from PyQt5.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect, QFrame
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from fileutil import get_file_path, get_resources_dir
import os, sys
import config
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from logging_util import get_logger, setup_logger

from ctypes import windll

logger = get_logger(__name__)

class ArtifactWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool |  # 不在任务栏显示
            Qt.WindowTransparentForInput  # 窗口完全透明，不接收任何输入
        )
        
        # 设置窗口背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置窗口和所有子控件不接收鼠标事件
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        # 创建标签用于显示图片
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 设置图片标签鼠标穿透
        
        # 设置边框样式
        self.image_label.setFrameShape(QFrame.Box)
        self.image_label.setStyleSheet("QLabel { border: 4px solid rgb(0, 255, 128); background-color: transparent; }")
        
        # 创建透明度效果
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.image_label.setGraphicsEffect(self.opacity_effect)

    def show_artifact(self, filename, opacity=1.0, grayscale=False):
        # 获取图片完整路径
        image_path = get_resources_dir('resources', 'artifacts', filename+'.png')
        logger.info(f"Loading artifact image: {image_path}")
        
        if not image_path or not os.path.exists(image_path):
            logger.info(f"Artifact image not found: {image_path}")
            return False
        
        # 加载图片
        image = QImage(image_path)
        if image.isNull():
            logger.info(f"Failed to load artifact image: {image_path}")
            return False
        else:
            logger.info(f"Successfully loaded artifact image: {image_path}")
            
        # 应用灰度效果
        if grayscale:
            image = image.convertToFormat(QImage.Format_Grayscale8)
            logger.info("Applied grayscale effect to image")
        
        # 转换为QPixmap并设置
        pixmap = QPixmap.fromImage(image)
        # 缩放图片到原始尺寸的一半
        scaled_width = int(pixmap.width()*config.ARTIFACTS_IMG_SCALE_RATIO)
        scaled_height = int(pixmap.height()*config.ARTIFACTS_IMG_SCALE_RATIO)
        pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(pixmap)
        
        # 设置透明度
        self.opacity_effect.setOpacity(opacity)
        
        # 调整窗口大小为图片大小
        self.resize(pixmap.width(), pixmap.height())
        self.image_label.resize(pixmap.width(), pixmap.height())
        
        # 移动窗口到屏幕中央
        screen = self.screen().geometry()
        self.move(
            (screen.width() - pixmap.width()) // 2,
            (screen.height() - pixmap.height()) // 2
        )
        
        # 添加ikun图标
        icon_path = get_resources_dir('ico', 'ikun.png')
        logger.info(f"Loading ikun icon: {icon_path}")
        # 获取配置中的图标位置信息
        config_name = f'ARTIFACTS_POS_{filename}'
        logger.info(f"config name: {config_name}")
        if hasattr(config, config_name):
            pos_config = getattr(config, config_name)
            logger.info(f"Found icon position config for {filename}: {pos_config}")
            # 创建图标标签
            icon_label = QLabel(self)
            icon_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 设置图标标签鼠标穿透
            icon_pixmap = QPixmap(icon_path)
            # 设置图标大小
            icon_pixmap = icon_pixmap.scaled(pos_config[2], pos_config[3], Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            # 计算图标位置
            x = int(pixmap.width() * pos_config[0])
            y = int(pixmap.height() * pos_config[1])
            logger.info(f"Placing ikun icon at position: ({x}, {y}) with size: {pos_config[2]}x{pos_config[3]}")
            icon_label.move(x, y)
            icon_label.show()
        else:
            logger.info(f"No icon position config found for {filename}")
        # 显示窗口
        self.show()
        return True

    def destroy_images(self):
        # 移除主图片
        if self.image_label.pixmap():
            self.image_label.clear()
        
        # 删除图标标签
        for child in self.children():
            if isinstance(child, QLabel) and child != self.image_label:
                # 清除pixmap资源
                if child.pixmap():
                    child.clear()
                child.deleteLater()
                child.hide()  # 立即隐藏图标
        
        # 强制进行垃圾回收和界面更新
        QApplication.processEvents()
        self.update()  # 强制重绘窗口

if __name__ == '__main__':
    # 设置DPI感知
    try:
        windll.user32.SetProcessDPIAware()
    except AttributeError:
        pass
        
    setup_logger()
    # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # 启用高DPI图标
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    # 禁用原生对话框和原生小部件，确保统一的DPI缩放
    QApplication.setAttribute(Qt.AA_DontUseNativeDialogs)
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
    
    app = QApplication(sys.argv)
    # 设置DPI缩放策略为PassThrough，确保精确的DPI缩放
    app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    win = ArtifactWindow()
    # 测试不同的图片效果
    
    win.show_artifact('死亡摇篮', opacity=1, grayscale=False)
    input('input to esc... ')
    win.destroy_images()
    
    win.show_artifact('湮灭快车', opacity=1, grayscale=False)
    input('input to esc... ')
    win.destroy_images()
    
    win.show_artifact('净网行动', opacity=1, grayscale=False)    
    input('input to esc... ')
    win.destroy_images()
