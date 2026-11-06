# -*- coding: utf-8 -*-

"""Mutator alert parsing helpers for the timer UI."""

import os
import sys
import traceback

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget

import config
from fileutil import get_resources_dir
from ui.map_schedule import parse_time_to_seconds

MUTATOR_TYPES = ("deployment", "propagator", "voidrifts", "killbots", "bombbots")


def parse_mutator_config_lines(lines: list[str]) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for raw_line in lines:
        line = str(raw_line or "").strip()
        if not line:
            continue
        parts = line.split("\t")
        seconds = parse_time_to_seconds(parts[0].strip())
        if seconds is None:
            continue
        text = parts[1].strip() if len(parts) > 1 else ""
        rows.append((seconds, text))
    return rows


def mutator_config_path(mutator_name: str) -> str | None:
    return get_resources_dir('resources', 'mutator', f'{mutator_name}.txt')


def cache_mutator_messages(window, mutator_name: str, rows: list[tuple[int, str]]) -> None:
    if not hasattr(window, 'mutator_alert_messages'):
        window.mutator_alert_messages = {}
    window.mutator_alert_messages[mutator_name] = {seconds: text for seconds, text in rows}


def get_mutator_message(window, mutator_name: str, time_point: int) -> str:
    messages = getattr(window, 'mutator_alert_messages', {})
    if mutator_name in messages:
        return messages[mutator_name].get(time_point, '')

    config_path = mutator_config_path(mutator_name)
    if not config_path or not os.path.exists(config_path):
        return ''

    with open(config_path, 'r', encoding='utf-8') as f:
        rows = parse_mutator_config_lines(f.readlines())
    cache_mutator_messages(window, mutator_name, rows)
    return window.mutator_alert_messages[mutator_name].get(time_point, '')


def show_mutator_alert(window, message, mutator_type='deployment'):
    """显示突变因子提醒"""
    # 检查游戏状态，非游戏中状态不显示提示
    from mainfunctions import get_game_screen
    if get_game_screen() != 'in_game':
        window.logger.info('非游戏中状态，不显示alert Toast提示')
        return

    # 获取对应类型的标签
    alert_label = window.mutator_alert_labels.get(mutator_type)
    if not alert_label:
        return

    # 清除已有布局
    if alert_label.layout() is not None:
        QWidget().setLayout(alert_label.layout())

    # 在Windows平台上，使用Windows API设置窗口样式
    if sys.platform == 'win32':
        try:
            import ctypes

            # 定义Windows API常量
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000

            # 获取窗口句柄
            hwnd = int(alert_label.winId())

            # 获取当前窗口样式
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

            # 添加透明样式
            new_ex_style = ex_style | WS_EX_TRANSPARENT | WS_EX_LAYERED

            # 设置新样式
            result = ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_ex_style)
            if result == 0:
                error = ctypes.windll.kernel32.GetLastError()
                window.logger.error(f'SetWindowLongW失败，错误码: {error}')

            # 强制窗口重绘
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0, 
                0x0001 | 0x0002 | 0x0004 | 0x0020  # SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED
            )

        except Exception as e:
            window.logger.error(f'设置Windows平台点击穿透失败: {str(e)}')
            window.logger.error(traceback.format_exc())
    else:
        # 非Windows平台使用Qt的方法
        alert_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    # 创建布局
    layout = QVBoxLayout(alert_label)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setAlignment(Qt.AlignLeft)

    # 创建一个QWidget作为提醒框
    alert_widget = QWidget()
    alert_widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 添加鼠标事件穿透
    alert_widget.setAttribute(Qt.WA_NoSystemBackground)  # 禁用系统背景
    alert_widget.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
    alert_layout = QHBoxLayout(alert_widget)
    alert_layout.setContentsMargins(0, 0, 0, 0)
    alert_layout.setAlignment(Qt.AlignLeft)

    # 根据突变因子类型设置图标和文本
    icon_name = f'{mutator_type}.png'
    icon_path = get_resources_dir('ico', 'mutator', icon_name)

    # 设置显示文本
    display_text = message

    if icon_path and os.path.exists(icon_path):
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 添加鼠标事件穿透
        icon_label.setAttribute(Qt.WA_NoSystemBackground)  # 禁用系统背景
        icon_label.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        alert_layout.addWidget(icon_label)

    # 创建文本标签
    text_label = QLabel(display_text)
    text_label.setStyleSheet(f'color: {config.MUTATOR_DEPLOYMENT_COLOR}; font-size: {config.TOAST_MUTATOR_FONT_SIZE}px')
    text_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 添加鼠标事件穿透
    text_label.setAttribute(Qt.WA_NoSystemBackground)  # 禁用系统背景
    text_label.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
    alert_layout.addWidget(text_label)

    # 将提醒框添加到布局中
    alert_widget.setLayout(alert_layout)
    layout.addWidget(alert_widget)

    # 设置固定宽度，避免位置偏移
    alert_label.setFixedWidth(250)

    # 设置提醒窗口位置
    current_screen = window.get_current_screen()
    screen_geometry = current_screen.geometry()
    # 根据突变因子类型设置不同的水平位置
    position_map = {
        'voidrifts': config.MUTATOR_RIFT_POS,  
        'propagator': config.MUTATOR_PROPAGATOR_POS,  
        'deployment': config.MUTATOR_DEPLOYMENT_POS,
        'killbots': config.MUTATOR_KILLBOTS_POS,
        'bombbots': config.MUTATOR_BOMBBOTS_POS
    }
    # 计算相对于屏幕的绝对位置
    x = screen_geometry.x() + int(screen_geometry.width() * position_map.get(mutator_type, 0.5)) - 125  # 使用固定宽度的一半
    y = int(window.height() * config.MUTATOR_TOAST_POSITION)  # 使用专门的突变因子提示位置配置
    alert_label.move(x, y)

    # 显示提醒标签并启动定时器
    alert_label.show()
    window.mutator_alert_timers[mutator_type].start(config.TOAST_DURATION)


def on_mutator_toggled(window, button, checked):
    """处理突变按钮状态改变"""
    if checked:
        # 切换到原始图标并添加阴影效果
        button.setIcon(button.original_icon)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(3)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 160))
        button.setGraphicsEffect(shadow)

        # 根据按钮索引加载对应的突变因子配置
        if button in window.mutator_buttons:
            button_index = window.mutator_buttons.index(button)
            if button_index < len(MUTATOR_TYPES):
                mutator_type = MUTATOR_TYPES[button_index]
                time_points = window.load_mutator_config(mutator_type)
                setattr(window, f'{mutator_type}_time_points', time_points)

                # 启动检查定时器（如果还没有启动）
                if not hasattr(window, 'mutator_timer'):
                    window.mutator_timer = QTimer()
                    window.mutator_timer.timeout.connect(window.check_mutator_alerts)
                    window.mutator_timer.start(1000)  # 每秒检查一次
    else:
        # 切换回灰色图标并移除阴影效果
        button.setIcon(button.gray_icon)
        button.setGraphicsEffect(None)

        # 清除对应突变因子的时间点和提醒记录
        if button in window.mutator_buttons:
            button_index = window.mutator_buttons.index(button)
            if button_index < len(MUTATOR_TYPES):
                mutator_type = MUTATOR_TYPES[button_index]
                # 清除时间点
                setattr(window, f'{mutator_type}_time_points', [])
                # 清除已提醒记录
                if hasattr(window, f'alerted_{mutator_type}_time_points'):
                    delattr(window, f'alerted_{mutator_type}_time_points')


def load_mutator_config(window, mutator_name):
    """加载突变因子配置文件"""
    try:
        # 获取配置文件路径
        config_path = mutator_config_path(mutator_name)
        window.logger.info(f'加载突变因子配置: {config_path}')

        if not config_path or not os.path.exists(config_path):
            window.logger.error(f'突变因子配置文件不存在: {config_path}')
            return []

        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        rows = parse_mutator_config_lines(lines)
        cache_mutator_messages(window, mutator_name, rows)
        time_points = [seconds for seconds, _text in rows]
        for seconds, _text in rows:
            window.logger.debug(f"添加时间点: {seconds}秒")

        window.logger.info(f'加载了 {len(time_points)} 个时间点: {time_points}')
        return sorted(time_points)  # 确保时间点是有序的

    except Exception as e:
        window.logger.error(f'加载突变因子配置失败: {str(e)}')
        window.logger.error(traceback.format_exc())
        return []


def check_mutator_alerts(window):
    """检查突变因子提醒"""
    try:
        # 从全局变量获取当前游戏时间
        from mainfunctions import most_recent_playerdata
        if most_recent_playerdata and isinstance(most_recent_playerdata, dict):
            current_time = most_recent_playerdata.get('time', 0)
            if not current_time:
                return

            current_seconds = int(float(current_time))
            window.logger.debug(f"当前游戏时间: {current_seconds}秒")

            # A new game resets the timer.  Clear per-game deduplication state
            # so the same mutator points can alert again in the next game.
            previous_seconds = getattr(window, '_last_mutator_time', None)
            if previous_seconds is not None and current_seconds < previous_seconds:
                for mutator_type in MUTATOR_TYPES:
                    setattr(window, f'alerted_{mutator_type}_time_points', set())
            window._last_mutator_time = current_seconds

            # 检查每个突变因子的时间点
            for i, mutator_type in enumerate(MUTATOR_TYPES):
                if i >= len(window.mutator_buttons):
                    continue

                # 检查对应按钮是否被选中
                if not window.mutator_buttons[i].isChecked():
                    continue

                time_points = []
                time_points_attr = f'{mutator_type}_time_points'
                if hasattr(window, time_points_attr):
                    time_points = getattr(window, time_points_attr)

                # 确保已提醒时间点集合存在
                alerted_points_attr = f'alerted_{mutator_type}_time_points'
                if not hasattr(window, alerted_points_attr):
                    setattr(window, alerted_points_attr, set())

                alerted_points = getattr(window, alerted_points_attr)
                for time_point in time_points:
                    # 如果这个时间点已经提醒过，跳过
                    if time_point in alerted_points:
                        continue

                    # 计算距离下一个时间点的秒数
                    time_diff = time_point - current_seconds
                    window.logger.debug(f"检查{mutator_type}时间点: {time_point}, 差值: {time_diff}")

                    # 如果在提醒时间范围内且时间差大于0（未来时间点）
                    if time_diff > 0 and time_diff <= config.MUTATION_FACTOR_ALERT_SECONDS:
                        from debug_utils import format_time_to_mmss
                        second_column_text = get_mutator_message(window, mutator_type, time_point)

                        window.logger.info(f"触发{mutator_type}突变因子提醒: {format_time_to_mmss(time_point)}处的事件")
                        window.show_mutator_alert(f"{time_diff} 秒后 {second_column_text}", mutator_type)

                        # 记录已提醒的时间点
                        alerted_points.add(time_point)

    except Exception as e:
        window.logger.error(f'检查突变因子提醒失败: {str(e)}')
        window.logger.error(traceback.format_exc())

