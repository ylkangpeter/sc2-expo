# -*- coding: utf-8 -*-

"""Map schedule parsing and time helpers for the timer UI."""

import os
import time
import traceback
from dataclasses import dataclass
from typing import Iterable

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QTableWidgetItem

import config
from fileutil import get_resources_dir


@dataclass(frozen=True)
class ScheduleRow:
    time_text: str
    event_text: str
    army_text: str
    raw_text: str


def parse_time_to_seconds(value: str) -> int | None:
    parts = str(value or "").strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return None
    return None


def format_game_time(seconds: float | int) -> str:
    total_seconds = int(float(seconds or 0))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes:02d}:{remaining_seconds:02d}"


def detect_map_variant(map_name: str, all_map_names: Iterable[str]) -> tuple[str, str, tuple[str, str]] | None:
    if "-" not in map_name:
        return None
    prefix, suffix = map_name.rsplit("-", 1)
    all_names = list(all_map_names)
    for other_map in all_names:
        if other_map == map_name or not other_map.startswith(prefix + "-"):
            continue
        other_suffix = other_map.rsplit("-", 1)[1]
        if other_suffix in {"左", "右"} and suffix in {"左", "右"}:
            return ("LR", suffix, ("左", "右"))
        if other_suffix in {"A", "B"} and suffix in {"A", "B"}:
            return ("AB", suffix, ("A", "B"))
    return None


def parse_schedule_content(content: str) -> list[ScheduleRow]:
    rows: list[ScheduleRow] = []
    for raw_line in str(content or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            rows.append(
                ScheduleRow(
                    time_text=parts[0],
                    event_text=parts[1],
                    army_text=parts[2] if len(parts) >= 3 else "",
                    raw_text=line,
                )
            )
        else:
            rows.append(ScheduleRow(time_text="", event_text=line, army_text="", raw_text=line))
    return rows

def update_game_time(window):
    """更新游戏时间显示"""
    window.logger.debug('开始更新游戏时间')
    start_time = time.time()

    try:
        # 从全局变量获取游戏时间
        from mainfunctions import most_recent_playerdata
        if most_recent_playerdata and isinstance(most_recent_playerdata, dict):
            game_time = most_recent_playerdata.get('time', 0)
            window.logger.debug(f'从全局变量获取的原始时间数据: {game_time}')

            current_seconds = int(float(game_time))
            formatted_time = format_game_time(current_seconds)

            window.current_time = formatted_time
            if window.time_label.text() != formatted_time:
                window.time_label.setText(formatted_time)

            # 更新地图信息（如果有）
            map_name = most_recent_playerdata.get('map')
            if map_name:
                window.logger.debug(f'地图信息更新: {map_name}')

            window.logger.debug(f'游戏时间更新: {formatted_time} (格式化后), 原始数据: {game_time}')

            # 根据当前时间调整表格滚动位置和行颜色
            try:
                if window._last_ui_second is not None and current_seconds < window._last_ui_second:
                    window._last_centered_row = None
                    window._last_toast_event_key = None

                if window._last_ui_second == current_seconds:
                    return
                window._last_ui_second = current_seconds

                parsed_rows = []
                active_event_row = -1
                active_event_seconds = None

                for row in range(window.table_area.rowCount()):
                    time_item = window.table_area.item(row, 0)
                    if not (time_item and time_item.text()):
                        continue

                    row_seconds = parse_time_to_seconds(time_item.text())
                    if row_seconds is None:
                        continue

                    parsed_rows.append((row, row_seconds))

                    if active_event_row == -1 and row_seconds >= current_seconds:
                        active_event_row = row
                        active_event_seconds = row_seconds

                if active_event_row == -1 and parsed_rows:
                    active_event_row, active_event_seconds = parsed_rows[-1]

                # 第二次遍历：设置颜色
                for row, row_seconds in parsed_rows:
                    time_item = window.table_area.item(row, 0)
                    event_item = window.table_area.item(row, 1)
                    army_item = window.table_area.item(row, 2)
                    # 根据时间差设置颜色
                    if row < active_event_row:
                        time_item.setForeground(QBrush(QColor(128, 128, 128, 255)))
                        time_item.setBackground(QBrush(QColor(0, 0, 0, 0)))
                        if event_item:
                            event_item.setForeground(QBrush(QColor(128, 128, 128, 255)))
                            event_item.setBackground(QBrush(QColor(0, 0, 0, 0)))
                    elif row == active_event_row:
                        time_item.setForeground(QBrush(QColor(config.TABLE_NEXT_FONT_COLOR[0], config.TABLE_NEXT_FONT_COLOR[1], config.TABLE_NEXT_FONT_COLOR[2])))
                        time_item.setBackground(QBrush(QColor(config.TABLE_NEXT_FONT_BG_COLOR[0], config.TABLE_NEXT_FONT_BG_COLOR[1], config.TABLE_NEXT_FONT_BG_COLOR[2], config.TABLE_NEXT_FONT_BG_COLOR[3])))
                        if event_item:
                            event_item.setForeground(QBrush(QColor(config.TABLE_NEXT_FONT_COLOR[0], config.TABLE_NEXT_FONT_COLOR[1], config.TABLE_NEXT_FONT_COLOR[2])))
                            event_item.setBackground(QBrush(QColor(config.TABLE_NEXT_FONT_BG_COLOR[0], config.TABLE_NEXT_FONT_BG_COLOR[1], config.TABLE_NEXT_FONT_BG_COLOR[2], config.TABLE_NEXT_FONT_BG_COLOR[3])))
                    elif row_seconds > current_seconds and (row_seconds - current_seconds) <= config.TIME_ALERT_SECONDS:
                        time_item.setForeground(QBrush(QColor(0, 191, 255)))
                        time_item.setBackground(QBrush(QColor(0, 191, 255, 30)))
                        if event_item:
                            event_item.setForeground(QBrush(QColor(0, 191, 255)))
                            event_item.setBackground(QBrush(QColor(0, 191, 255, 30)))
                    else:
                        time_item.setForeground(QBrush(QColor(255, 255, 255)))
                        time_item.setBackground(QBrush(QColor(0, 0, 0, 0)))
                        if event_item:
                            event_item.setForeground(QBrush(QColor(255, 255, 255)))
                            event_item.setBackground(QBrush(QColor(0, 0, 0, 0)))

                if active_event_row >= 0 and active_event_seconds is not None:
                    time_diff = active_event_seconds - current_seconds
                    toast_event_key = (active_event_row, active_event_seconds)
                    if 0 < time_diff <= config.TIME_ALERT_SECONDS and window._last_toast_event_key != toast_event_key and not window.toast_manager.is_toast_visible():
                        time_item = window.table_area.item(active_event_row, 0)
                        event_item = window.table_area.item(active_event_row, 1)
                        army_item = window.table_area.item(active_event_row, 2)
                        if time_item and event_item:
                            toast_message = f"{time_item.text()}\t{event_item.text()}" + (f"\t{army_item.text()}" if army_item else "")
                            window.show_toast(toast_message, config.TOAST_DURATION)
                            window._last_toast_event_key = toast_event_key

                window.center_table_on_row(active_event_row)
            except Exception as e:
                window.logger.error(f'调整表格滚动位置和颜色失败: {str(e)}\n{traceback.format_exc()}')

        else:
            window.logger.debug('未获取到有效的游戏时间数据')
            window.time_label.setText("00:00")

    except Exception as e:
        window.logger.error(f'获取游戏时间失败: {str(e)}\n{traceback.format_exc()}')
        # 如果获取失败，显示默认时间
        window.time_label.setText("00:00")

    window.logger.debug(f'本次更新总耗时：{time.time() - start_time:.2f}秒\n')


def on_map_selected(window, map_name):
    """处理地图选择变化事件"""
    # 检查是否是由用户手动选择触发的
    if not window.manual_map_selection and window.sender() == window.combo_box:
        window.manual_map_selection = True
        window.logger.info('用户手动选择了地图')

    all_map_names = [window.combo_box.itemText(i) for i in range(window.combo_box.count())]
    variant = detect_map_variant(map_name, all_map_names)
    if variant is not None:
        _variant_type, current_suffix, button_labels = variant
        window.version_buttons[0].setText(button_labels[0])
        window.version_buttons[1].setText(button_labels[1])
        for btn in window.version_buttons:
            btn.setChecked(btn.text() == current_suffix)
        window.map_version_group.show()
    else:
        window.map_version_group.hide()

    try:
        map_file_path = get_resources_dir('resources', 'maps', config.current_language, map_name)
        window.logger.info(f'尝试加载地图文件: {map_file_path}')

        # 读取地图文件内容
        if os.path.exists(map_file_path):
            with open(map_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            window.logger.info(f'成功读取地图文件内容: {map_name}\n文件内容:\n{content}')

            # 清空表格现有内容
            window.table_area.setRowCount(0)
            window.logger.info('已清空表格现有内容')

            schedule_rows = parse_schedule_content(content)
            window.logger.info('解析到的有效行数: {}'.format(len(schedule_rows)))
            window.logger.info('解析后的行内容:\n{}'.format('\n'.join(row.raw_text for row in schedule_rows)))

            # 设置表格行数
            window.table_area.setRowCount(len(schedule_rows))
            window.logger.info(f'设置表格行数为: {len(schedule_rows)}')

            # 填充表格内容
            for row, schedule_row in enumerate(schedule_rows):
                parts = [schedule_row.time_text, schedule_row.event_text]
                if schedule_row.army_text:
                    parts.append(schedule_row.army_text)
                window.logger.info(f'处理第{row+1}行: {schedule_row.raw_text}, 拆分结果: {parts}')

                if schedule_row.time_text:
                    # 创建时间单元格
                    time_item = QTableWidgetItem(schedule_row.time_text)
                    time_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    time_item.setForeground(QBrush(QColor(255, 255, 255)))  # 修改时间列文字颜色为白色
                    window.table_area.setItem(row, 0, time_item)

                    # 创建事件单元格
                    event_item = QTableWidgetItem(schedule_row.event_text)
                    event_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    event_item.setForeground(QBrush(QColor(255, 255, 255)))  # 设置事件列文字颜色为白色
                    window.table_area.setItem(row, 1, event_item)

                    if schedule_row.army_text:
                        army_item = QTableWidgetItem(schedule_row.army_text)
                        army_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                        army_item.setForeground(QBrush(QColor(255, 255, 255)))  # 设置事件
                        window.table_area.setItem(row, 2, army_item)
                        window.logger.info(f'已添加表格内容 - 行{row+1}: 时间={schedule_row.time_text}, 事件={schedule_row.event_text}, {schedule_row.army_text}')
                    else:
                        window.logger.info(f'已添加表格内容 - 行{row+1}: 时间={schedule_row.time_text}, 事件={schedule_row.event_text}')
                else:
                    # 对于不符合格式的行，将整行内容显示在事件列
                    event_item = QTableWidgetItem(schedule_row.event_text)
                    event_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    event_item.setForeground(QBrush(QColor(255, 255, 255)))  # 设置事件列文字颜色为白色

                    window.table_area.setItem(row, 0, event_item)
                    window.table_area.setSpan(row, 0, 1, 3)  # 将当前行的两列合并为一列

                    window.logger.info(f'已添加不规范行内容到合并单元格 - 行{row+1}: {schedule_row.event_text}')

            # 验证表格内容
            row_count = window.table_area.rowCount()
            window.logger.info(f'最终表格行数: {row_count}')
            for row in range(row_count):
                time_item = window.table_area.item(row, 0)
                event_item = window.table_area.item(row, 1)
                time_text = time_item.text() if time_item else 'None'
                event_text = event_item.text() if event_item else 'None'
                window.logger.info(f'验证第{row+1}行内容: 时间={time_text}, 事件={event_text}')

        else:
            window.logger.error(f'地图文件不存在: {map_name}')
            return

    except Exception as e:
        window.logger.error(f'加载地图文件时出错: {str(e)}\n{traceback.format_exc()}')

