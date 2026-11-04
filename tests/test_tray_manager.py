# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QSystemTrayIcon
from tray_manager import TrayManager
import config


class FakeLogger:
    def __init__(self):
        self.infos = []

    def info(self, msg):
        self.infos.append(msg)


def test_tray_manager_get_toggle_action_text_reads_word_conf():
    class FakeParent:
        def get_text(self, key):
            if key == 'toggle_action':
                return '显示/隐藏'
            return key

    manager = TrayManager.__new__(TrayManager)
    manager.parent = FakeParent()
    assert manager.get_toggle_action_text() == '显示/隐藏'


def test_tray_manager_get_toggle_action_text_fallback():
    class FakeParent:
        def get_text(self, key):
            return key

    manager = TrayManager.__new__(TrayManager)
    manager.parent = FakeParent()
    config.current_language = 'zh'
    assert manager.get_toggle_action_text() == '显示/隐藏'

    config.current_language = 'en'
    assert manager.get_toggle_action_text() == 'Show/Hide'
    config.current_language = 'zh'  # restore


def test_tray_manager_toggle_visibility_delegates_to_parent():
    calls = []

    class FakeParent:
        def toggle_visibility(self):
            calls.append('toggled')

    manager = TrayManager.__new__(TrayManager)
    manager.parent = FakeParent()
    manager.toggle_visibility()

    assert calls == ['toggled']


def test_tray_manager_toggle_visibility_fallback_when_parent_has_is_visible():
    class FakeParent:
        def __init__(self):
            self.visible = True
            self.hidden = False
            self.shown = False

        def isVisible(self):
            return self.visible

        def hide(self):
            self.hidden = True
            self.visible = False

        def show(self):
            self.shown = True
            self.visible = True

    parent = FakeParent()
    manager = TrayManager.__new__(TrayManager)
    manager.parent = parent

    manager.toggle_visibility()
    assert parent.hidden is True
    assert parent.visible is False

    manager.toggle_visibility()
    assert parent.shown is True
    assert parent.visible is True


def test_tray_manager_on_tray_activated_calls_toggle_on_trigger():
    calls = []

    manager = TrayManager.__new__(TrayManager)
    manager.toggle_visibility = lambda: calls.append('triggered')

    manager.on_tray_activated(QSystemTrayIcon.Trigger)
    assert calls == ['triggered']

    manager.on_tray_activated(QSystemTrayIcon.Context)
    assert calls == ['triggered']  # not called for context menu
