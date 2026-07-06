# -*- coding: utf-8 -*-


def test_game_time_mock_applies_time_factor_and_pause_duration(monkeypatch):
    import debug_utils

    times = iter([100.0, 103.0, 104.0, 110.0, 112.0])
    monkeypatch.setattr(debug_utils.time, "time", lambda: next(times))

    game_time = debug_utils.GameTimeMock(time_factor=2.0)

    assert game_time.get_current_time() == 6.0

    game_time.pause()
    assert game_time.get_current_time() == 8.0

    game_time.resume()
    assert game_time.get_current_time() == 12.0


def test_get_mock_screen_data_defaults_to_in_game():
    import debug_utils

    debug_utils._game_screen_mock = None

    assert debug_utils.get_mock_screen_data() == {"activeScreens": []}
