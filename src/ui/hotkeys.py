# -*- coding: utf-8 -*-

import traceback
import importlib

import keyboard

import config

def init_global_hotkeys(window):
    """初始化全局快捷键"""
    try:
        window.cleanup_global_hotkeys()

        # 解析快捷键配置
        map_shortcut = config.MAP_SHORTCUT.replace(' ', '').lower()
        lock_shortcut = config.LOCK_SHORTCUT.replace(' ', '').lower()
        screenshot_shortcut = config.SCREENSHOT_SHORTCUT.replace(' ', '').lower()
        artifact_shortcut = config.SHOW_ARTIFACT_SHORTCUT.replace(' ', '').lower()

        # 注册全局快捷键
        window.hotkey_handles.append(keyboard.add_hotkey(map_shortcut, window.map_switch_signal.emit))
        window.hotkey_handles.append(keyboard.add_hotkey(lock_shortcut, window.lock_shortcut_signal.emit))
        window.hotkey_handles.append(keyboard.add_hotkey(screenshot_shortcut, window.screenshot_shortcut_signal.emit))
        window.hotkey_handles.append(keyboard.add_hotkey(artifact_shortcut, window.toggle_artifact_signal.emit))
        window.logger.info(f'成功注册全局快捷键: {config.MAP_SHORTCUT}, {config.LOCK_SHORTCUT}, {config.SCREENSHOT_SHORTCUT}')

    except Exception as e:
        window.logger.error(f'注册全局快捷键失败: {str(e)}')
        window.logger.error(traceback.format_exc())


def cleanup_global_hotkeys(window):
    """清理本窗口注册的全局快捷键"""
    while getattr(window, 'hotkey_handles', []):
        hotkey_handle = window.hotkey_handles.pop()
        try:
            keyboard.remove_hotkey(hotkey_handle)
        except Exception as e:
            window.logger.error(f'移除全局快捷键失败: {str(e)}')
            window.logger.error(traceback.format_exc())


def reset_global_hotkeys(window):
    """重置 keyboard 模块的全局 hook 并重新注册快捷键。"""
    global keyboard
    try:
        keyboard.unhook_all()
        keyboard = importlib.reload(keyboard)
        window.hotkey_handles = []
        init_global_hotkeys(window)
        window.logger.info('已重置全局快捷键 hook')
    except Exception as e:
        window.logger.error(f'重置全局快捷键失败: {str(e)}')
        window.logger.error(traceback.format_exc())

