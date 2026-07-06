# -*- coding: utf-8 -*-


class FakeLogger:
    def __init__(self):
        self.errors = []
        self.infos = []

    def info(self, message):
        self.infos.append(message)

    def error(self, message):
        self.errors.append(message)


def test_init_global_hotkeys_normalizes_shortcuts_and_registers_handles(monkeypatch):
    from ui import hotkeys

    registered = []

    def fake_add_hotkey(shortcut, callback):
        registered.append((shortcut, callback))
        return f"handle:{shortcut}"

    class FakeSignal:
        def emit(self):
            pass

    class FakeWindow:
        def __init__(self):
            self.hotkey_handles = ["stale"]
            self.logger = FakeLogger()
            self.map_switch_signal = FakeSignal()
            self.lock_shortcut_signal = FakeSignal()
            self.screenshot_shortcut_signal = FakeSignal()
            self.toggle_artifact_signal = FakeSignal()
            self.cleanup_called = False

        def cleanup_global_hotkeys(self):
            self.cleanup_called = True
            self.hotkey_handles.clear()

    monkeypatch.setattr(hotkeys.keyboard, "add_hotkey", fake_add_hotkey)
    monkeypatch.setattr(hotkeys.config, "MAP_SHORTCUT", "Ctrl + M")
    monkeypatch.setattr(hotkeys.config, "LOCK_SHORTCUT", "Ctrl + L")
    monkeypatch.setattr(hotkeys.config, "SCREENSHOT_SHORTCUT", "Ctrl + S")
    monkeypatch.setattr(hotkeys.config, "SHOW_ARTIFACT_SHORTCUT", "Ctrl + A")

    window = FakeWindow()
    hotkeys.init_global_hotkeys(window)

    assert window.cleanup_called is True
    assert [shortcut for shortcut, _callback in registered] == ["ctrl+m", "ctrl+l", "ctrl+s", "ctrl+a"]
    assert window.hotkey_handles == ["handle:ctrl+m", "handle:ctrl+l", "handle:ctrl+s", "handle:ctrl+a"]


def test_cleanup_global_hotkeys_removes_handles_lifo(monkeypatch):
    from ui import hotkeys

    removed = []
    monkeypatch.setattr(hotkeys.keyboard, "remove_hotkey", removed.append)

    class FakeWindow:
        hotkey_handles = ["first", "second"]
        logger = FakeLogger()

    window = FakeWindow()
    hotkeys.cleanup_global_hotkeys(window)

    assert removed == ["second", "first"]
    assert window.hotkey_handles == []
