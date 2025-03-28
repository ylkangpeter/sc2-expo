import sys
import time
import os
from PyQt5.QtWidgets import QApplication

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from image_util import draw_square, clear_square, capture_screen_rect

def test_draw_and_clear_square():
    # 初始化应用程序
    app = QApplication(sys.argv)
    
    # 测试不同位置和大小的正方形
    test_cases = [
        (100, 100, 100, 50),  # 默认大小的正方形
        (300, 300, 150, 20),  # 较大的正方形
        (500, 100, 500, 100),   # 较小的正方形
    ]
    
    # 绘制所有正方形并截图
    for x, y, width, height in test_cases:
        rect = draw_square(x, y, width, height)
        print(f"绘制正方形: 位置({x}, {y}), 大小{width}, {height}")
        # 对矩形区域进行截图
        print(f"截图矩形: {rect}")
        save_path = capture_screen_rect(rect, True)
        if save_path:
            print(f"截图已保存到: {save_path}")
        else:
            print("截图保存失败")
        time.sleep(1)  # 等待1秒以确保截图完成

    print("测试完成")

    # 等待用户按 q 键退出
    input("按 'q' 键退出程序...")

    # 保持程序运行，不自动退出
    app.quit()

if __name__ == '__main__':
    test_draw_and_clear_square()
