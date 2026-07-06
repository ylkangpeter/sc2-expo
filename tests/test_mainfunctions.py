# -*- coding: utf-8 -*-


def test_get_game_screen_reports_matchmaking_when_active_screens_present(monkeypatch):
    import mainfunctions

    monkeypatch.setattr(mainfunctions.config, "debug_mode", True)
    monkeypatch.setattr(mainfunctions, "get_mock_screen_data", lambda: {"activeScreens": ["Screen"]})

    assert mainfunctions.get_game_screen() == "matchmaking"


def test_get_game_screen_reports_in_game_when_active_screens_empty(monkeypatch):
    import mainfunctions

    monkeypatch.setattr(mainfunctions.config, "debug_mode", True)
    monkeypatch.setattr(mainfunctions, "get_mock_screen_data", lambda: {"activeScreens": []})

    assert mainfunctions.get_game_screen() == "in_game"


def test_get_game_screen_returns_unknown_on_request_error(monkeypatch):
    import requests

    import mainfunctions

    class FailingSession:
        def get(self, *_args, **_kwargs):
            raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(mainfunctions.config, "debug_mode", False)
    monkeypatch.setattr(mainfunctions, "session", FailingSession())

    assert mainfunctions.get_game_screen() == "unknown"
