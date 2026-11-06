"""Actions used by :class:`TimerWindow`.

The main window remains the owner of state and Qt widgets.  These functions
keep command handlers small and make the state transitions independently
testable without constructing the complete overlay window.
"""

import traceback

import config
import image_util


def handle_screenshot_hotkey(window):
    """Capture all configured debug rectangles for ``window``."""
    if not config.DEBUG_SHOW_ENEMY_INFO_SQUARE:
        return

    try:
        successful_captures = 0
        for rect in window.rect_screenshots:
            try:
                save_path = image_util.capture_screen_rect(rect)
                if save_path:
                    window.logger.info(f'成功保存截图到: {save_path}')
                    successful_captures += 1
                else:
                    window.logger.warning(
                        f'截图保存失败: {rect.x()}, {rect.y()}, '
                        f'{rect.width()}, {rect.height()}'
                    )
            except Exception as capture_error:
                window.logger.error(f'区域截图失败: {str(capture_error)}')
                window.logger.error(traceback.format_exc())

        if successful_captures == len(window.rect_screenshots):
            window.logger.info('所有区域截图完成')
        else:
            window.logger.warning(
                f'部分区域截图失败: 成功{successful_captures}/'
                f'{len(window.rect_screenshots)}'
            )
    except Exception as exc:
        window.logger.error(f'截图处理失败: {str(exc)}')
        window.logger.error(traceback.format_exc())


def handle_lock_shortcut(window):
    """Toggle the lock control and publish its new clickability state."""
    window.logger.info(f'检测到锁定快捷键组合: {config.LOCK_SHORTCUT}')
    window.control_window.is_locked = not window.control_window.is_locked
    window.control_window.update_icon()
    window.control_window.state_changed.emit(not window.control_window.is_locked)


def handle_map_switch_hotkey(window):
    """Switch between the selected map's available A/B variants."""
    window.logger.info(f'检测到地图切换快捷键组合: {config.MAP_SHORTCUT}')
    if not window.map_version_group.isVisible():
        window.logger.info('当前地图不支持A/B版本切换')
        return

    window.logger.info('当前地图支持A/B版本切换')
    current_btn = next(
        (button for button in window.version_buttons if button.isChecked()),
        None,
    )
    if current_btn is None:
        return

    current_idx = window.version_buttons.index(current_btn)
    next_button = window.version_buttons[(current_idx + 1) % len(window.version_buttons)]
    window.logger.info(
        f'从版本 {current_btn.text()} 切换到版本 {next_button.text()}'
    )
    next_button.click()


def hide_subwindows(window):
    """Hide every auxiliary widget owned by the main window."""
    for name in ('control_window', 'commander_selector', 'artifact_window'):
        widget = getattr(window, name, None)
        if widget is not None:
            widget.hide()

    toast_manager = getattr(window, 'toast_manager', None)
    if toast_manager is not None:
        toast_manager.hide_toast()

    for label in getattr(window, 'mutator_alert_labels', {}).values():
        label.hide()


def toggle_visibility(window):
    """Toggle the main window and its auxiliary controls."""
    if window.isVisible():
        window.hide()
    else:
        window.show()
