# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import json


def test_mainfunctions_import_does_not_require_requests():
    script = """
import builtins
original_import = builtins.__import__
def blocked_import(name, *args, **kwargs):
    if name == "requests" or name.startswith("requests."):
        raise ImportError("blocked requests")
    return original_import(name, *args, **kwargs)
builtins.__import__ = blocked_import
import mainfunctions
print(mainfunctions.get_troop_from_game())
"""
    env = {**os.environ, "PYTHONPATH": os.path.abspath("src")}

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


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
    import mainfunctions

    def raise_request_error(_path):
        raise OSError()

    monkeypatch.setattr(mainfunctions.config, "debug_mode", False)
    monkeypatch.setattr(mainfunctions, "get_sc2_json", raise_request_error)

    assert mainfunctions.get_game_screen() == "unknown"


def test_get_game_screen_returns_unknown_when_active_screens_missing(monkeypatch):
    import mainfunctions

    monkeypatch.setattr(mainfunctions.config, "debug_mode", True)
    monkeypatch.setattr(mainfunctions, "get_mock_screen_data", lambda: {})

    assert mainfunctions.get_game_screen() == "unknown"


def test_request_app_close_sets_and_reset_close_flag():
    import mainfunctions

    mainfunctions.reset_app_close()
    assert mainfunctions.APP_CLOSING is False
    assert mainfunctions.APP_STOP_EVENT.is_set() is False
    mainfunctions.request_app_close()
    assert mainfunctions.APP_CLOSING is True
    assert mainfunctions.APP_STOP_EVENT.is_set() is True
    mainfunctions.reset_app_close()
    assert mainfunctions.APP_STOP_EVENT.is_set() is False


def test_get_sc2_json_closes_connection_after_success(monkeypatch):
    import mainfunctions

    class FakeResponse:
        def read(self):
            return b'{"activeScreens": []}'

    class FakeConnection:
        instances = []

        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout
            self.request_args = None
            self.closed = False
            self.__class__.instances.append(self)

        def request(self, method, path):
            self.request_args = (method, path)

        def getresponse(self):
            return FakeResponse()

        def close(self):
            self.closed = True

    monkeypatch.setattr(mainfunctions.http.client, "HTTPConnection", FakeConnection)

    assert mainfunctions.get_sc2_json("/ui") == {"activeScreens": []}
    connection = FakeConnection.instances[0]
    assert (connection.host, connection.port, connection.timeout) == ("localhost", 6119, 6)
    assert connection.request_args == ("GET", "/ui")
    assert connection.closed is True


def test_get_sc2_json_closes_connection_when_json_decode_fails(monkeypatch):
    import mainfunctions

    class FakeResponse:
        def read(self):
            return b"not-json"

    class FakeConnection:
        instances = []

        def __init__(self, *_args, **_kwargs):
            self.closed = False
            self.__class__.instances.append(self)

        def request(self, *_args):
            pass

        def getresponse(self):
            return FakeResponse()

        def close(self):
            self.closed = True

    monkeypatch.setattr(mainfunctions.http.client, "HTTPConnection", FakeConnection)

    try:
        mainfunctions.get_sc2_json("/ui")
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("expected JSONDecodeError")

    assert FakeConnection.instances[0].closed is True
