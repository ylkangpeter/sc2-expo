# -*- coding: utf-8 -*-

from ui.timer_window import TimerWindow


class FakeLogger:
    def __init__(self):
        self.infos = []

    def info(self, message):
        self.infos.append(message)


def test_center_table_on_row_clamps_scroll_and_caches_row():
    class FakeViewport:
        def height(self):
            return 40

    class FakeScrollBar:
        def __init__(self):
            self.values = []

        def minimum(self):
            return 0

        def maximum(self):
            return 100

        def value(self):
            return self.values[-1] if self.values else 0

        def setValue(self, value):
            self.values.append(value)

    class FakeTable:
        def __init__(self):
            self.scrollbar = FakeScrollBar()

        def rowCount(self):
            return 4

        def rowHeight(self, _row):
            return 20

        def viewport(self):
            return FakeViewport()

        def verticalScrollBar(self):
            return self.scrollbar

    window = type("Window", (), {})()
    window.table_area = FakeTable()
    window._last_centered_row = None

    TimerWindow.center_table_on_row(window, 2)
    TimerWindow.center_table_on_row(window, 2)

    assert window.table_area.scrollbar.values == [30]
    assert window._last_centered_row == 2


def test_handle_map_switch_hotkey_clicks_next_checked_version():
    class FakeButton:
        def __init__(self, text, checked=False):
            self._text = text
            self._checked = checked
            self.clicked = False

        def isChecked(self):
            return self._checked

        def text(self):
            return self._text

        def click(self):
            self.clicked = True

    class FakeGroup:
        def isVisible(self):
            return True

    window = type("Window", (), {})()
    window.logger = FakeLogger()
    window.map_version_group = FakeGroup()
    window.version_buttons = [FakeButton("A", checked=True), FakeButton("B")]

    TimerWindow.handle_map_switch_hotkey(window)

    assert window.version_buttons[0].clicked is False
    assert window.version_buttons[1].clicked is True


def test_handle_lock_shortcut_toggles_control_window_and_emits_state():
    class FakeSignal:
        def __init__(self):
            self.emitted = []

        def emit(self, value):
            self.emitted.append(value)

    class FakeControlWindow:
        def __init__(self):
            self.is_locked = True
            self.icon_updates = 0
            self.state_changed = FakeSignal()

        def update_icon(self):
            self.icon_updates += 1

    window = type("Window", (), {})()
    window.logger = FakeLogger()
    window.control_window = FakeControlWindow()

    TimerWindow.handle_lock_shortcut(window)

    assert window.control_window.is_locked is False
    assert window.control_window.icon_updates == 1
    assert window.control_window.state_changed.emitted == [True]
