# -*- coding: utf-8 -*-


class FakeLogger:
    def __init__(self):
        self.infos = []

    def info(self, message):
        self.infos.append(message)


def test_show_toast_returns_early_when_not_in_game(monkeypatch):
    import toast_manager

    manager = toast_manager.ToastManager.__new__(toast_manager.ToastManager)
    manager.logger = FakeLogger()
    manager.toast_container = None

    monkeypatch.setattr(toast_manager, "get_game_screen", lambda: "matchmaking")
    monkeypatch.setattr(toast_manager.config, "TOAST_ALLOWED", True)

    manager.show_toast("00:30\tmessage")

    assert manager.toast_container is None
    assert manager.logger.infos == ["非游戏中状态或禁用toast，不显示Toast提示"]


def test_show_toast_returns_early_when_toast_disabled(monkeypatch):
    import toast_manager

    manager = toast_manager.ToastManager.__new__(toast_manager.ToastManager)
    manager.logger = FakeLogger()
    manager.toast_container = None

    monkeypatch.setattr(toast_manager, "get_game_screen", lambda: "in_game")
    monkeypatch.setattr(toast_manager.config, "TOAST_ALLOWED", False)

    manager.show_toast("00:30\tmessage")

    assert manager.toast_container is None
    assert manager.logger.infos == ["非游戏中状态或禁用toast，不显示Toast提示"]


def test_parse_toast_message_accepts_free_form_and_empty_values():
    from toast_manager import parse_toast_message

    assert parse_toast_message("event") == ("event", ["event"], "event")
    assert parse_toast_message(None) == ("", [""], "")
    assert parse_toast_message("00:30\tmessage\tT1") == (
        "00:30\tmessage\tT1",
        ["00:30", "message", "T1"],
        "00:30 message",
    )
