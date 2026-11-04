# -*- coding: utf-8 -*-

from ui.timer_window import TimerWindow


class FakeLogger:
    def __init__(self):
        self.infos = []
        self.warnings = []
        self.errors = []

    def info(self, message):
        self.infos.append(message)

    def warning(self, message):
        self.warnings.append(message)

    def error(self, message):
        self.errors.append(message)


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


def test_handle_screenshot_hotkey_handles_empty_rect_list(monkeypatch):
    import ui.timer_window as timer_window

    window = type("Window", (), {})()
    window.logger = FakeLogger()
    window.rect_screenshots = []

    monkeypatch.setattr(timer_window.config, "DEBUG_SHOW_ENEMY_INFO_SQUARE", True)

    TimerWindow.handle_screenshot_hotkey(window)

    assert window.logger.infos == ["所有区域截图完成"]


def test_toggle_visibility_toggles_between_hide_and_show():
    window = type("Window", (), {})()
    window.logger = FakeLogger()
    window.visible = True
    hidden_calls = []
    shown_calls = []

    window.isVisible = lambda: window.visible
    window.hide = lambda: (setattr(window, "visible", False), hidden_calls.append(True))
    window.show = lambda: (setattr(window, "visible", True), shown_calls.append(True))

    TimerWindow.toggle_visibility(window)
    assert hidden_calls == [True]
    assert window.visible is False

    TimerWindow.toggle_visibility(window)
    assert shown_calls == [True]
    assert window.visible is True


def test_hide_subwindows_hides_all_attached_components():
    class FakeWidget:
        def __init__(self):
            self.hidden = False

        def hide(self):
            self.hidden = True

    class FakeToastManager:
        def __init__(self):
            self.toast_hidden = False

        def hide_toast(self):
            self.toast_hidden = True

    window = type("Window", (), {})()
    window.control_window = FakeWidget()
    window.commander_selector = FakeWidget()
    window.artifact_window = FakeWidget()
    window.toast_manager = FakeToastManager()
    window.mutator_alert_labels = {"mut1": FakeWidget(), "mut2": FakeWidget()}

    TimerWindow.hide_subwindows(window)

    assert window.control_window.hidden is True
    assert window.commander_selector.hidden is True
    assert window.artifact_window.hidden is True
    assert window.toast_manager.toast_hidden is True
    assert window.mutator_alert_labels["mut1"].hidden is True
    assert window.mutator_alert_labels["mut2"].hidden is True


def test_show_updates_control_window_position_and_shows_it():
    class FakeControlWindow:
        def __init__(self):
            self.shown = False

        def show(self):
            self.shown = True

    window = type("Window", (), {})()
    window.logger = FakeLogger()
    window.control_window = FakeControlWindow()
    position_updated = []
    window.update_control_window_position = lambda: position_updated.append(True)

    TimerWindow.show(window)

    assert position_updated == [True]
    assert window.control_window.shown is True
    assert "已显示SC2 Timer窗口" in window.logger.infos


def test_timer_window_get_text_returns_toggle_action_text():
    import config
    window = type("Window", (), {})()
    window.logger = FakeLogger()

    original_lang = getattr(config, "current_language", "zh")
    try:
        config.current_language = "zh"
        assert TimerWindow.get_text(window, "show_action") == "显示/隐藏"
        assert TimerWindow.get_text(window, "toggle_action") == "显示/隐藏"

        config.current_language = "en"
        assert TimerWindow.get_text(window, "show_action") == "Show/Hide"
        assert TimerWindow.get_text(window, "toggle_action") == "Show/Hide"
    finally:
        config.current_language = original_lang


