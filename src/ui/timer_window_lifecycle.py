"""Window lifecycle behavior for the main overlay."""

import threading
import traceback
import sys

from PyQt5.QtWidgets import QApplication

from ui.timer_window_actions import hide_subwindows, toggle_visibility


class TimerWindowLifecycleMixin:
    """Keep shutdown and visibility behavior separate from UI event handlers."""

    def request_quit(self):
        """从托盘退出菜单发起真正退出。"""
        self._is_quitting = True
        try:
            import mainfunctions

            close_request = getattr(mainfunctions, 'request_app_close', None)
            if close_request is not None:
                close_request()
            else:
                mainfunctions.APP_CLOSING = True
        except Exception:
            pass

        self._wait_for_game_check_thread()
        try:
            if hasattr(self, 'tray_manager') and self.tray_manager is not None:
                self.tray_manager.dispose()
            self.cleanup_global_hotkeys()
            self.logger.info('已清理所有全局快捷键')
        except Exception as exc:
            self.logger.error(f'清理全局快捷键失败: {str(exc)}')
            self.logger.error(traceback.format_exc())
        QApplication.instance().quit()

    def _wait_for_game_check_thread(self):
        """Stop the API poller before Qt objects are torn down."""
        thread = getattr(self, 'game_check_thread', None)
        if thread is None or not thread.is_alive():
            return
        if thread is threading.current_thread():
            return

        try:
            import mainfunctions

            timeout = getattr(mainfunctions, 'SC2_REQUEST_TIMEOUT_SECONDS', 6) + 1
            thread.join(timeout=timeout)
            if thread.is_alive():
                self.logger.warning('游戏轮询线程未在退出超时内结束')
        except Exception as exc:
            self.logger.error(f'等待游戏轮询线程退出失败: {exc}')

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if not self._is_quitting:
            event.ignore()
            self.hide()
            return

        try:
            try:
                import mainfunctions

                close_request = getattr(mainfunctions, 'request_app_close', None)
                if close_request is not None:
                    close_request()
                else:
                    mainfunctions.APP_CLOSING = True
            except Exception:
                pass
            self._wait_for_game_check_thread()
            if hasattr(self, 'tray_manager') and self.tray_manager is not None:
                self.tray_manager.dispose()
            self.cleanup_global_hotkeys()
            self.logger.info('已清理所有全局快捷键')
        except Exception as exc:
            self.logger.error(f'清理全局快捷键失败: {str(exc)}')
            self.logger.error(traceback.format_exc())

        super().closeEvent(event)

    def hide_subwindows(self):
        """隐藏所有关联的子窗口及浮动组件"""
        hide_subwindows(self)

    def hide(self):
        """隐藏主窗口及所有关联组件"""
        try:
            super().hide()
        except TypeError:
            pass
        self.hide_subwindows()
        if hasattr(self, 'logger'):
            self.logger.info('已隐藏SC2 Timer窗口')

    def show(self):
        """显示主窗口及控制窗口"""
        try:
            super().show()
        except TypeError:
            pass
        if hasattr(self, 'control_window') and self.control_window is not None:
            self.update_control_window_position()
            self.control_window.show()
        if hasattr(self, 'logger'):
            self.logger.info('已显示SC2 Timer窗口')

    def toggle_visibility(self):
        """切换主窗口及关联窗口的显示/隐藏状态"""
        toggle_visibility(self)

    def hideEvent(self, event):
        """窗口隐藏事件，隐藏所有关联子窗口"""
        super().hideEvent(event)
        self.hide_subwindows()

    def showEvent(self, event):
        """窗口显示事件，确保窗口始终保持在最上层"""
        super().showEvent(event)
        if sys.platform == 'win32':
            import win32gui
            import win32con

            hwnd = int(self.winId())
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        self.enforce_click_through_state()
        if hasattr(self, 'control_window') and self.control_window is not None:
            self.update_control_window_position()
            self.control_window.show()
