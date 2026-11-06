# -*- coding: utf-8 -*-

from game_session import GameSessionTracker, stable_player_fingerprint


def test_fingerprint_is_independent_of_api_player_order():
    players = [
        {"id": 2, "name": "Amon", "type": "computer"},
        {"id": 1, "name": "Player", "type": "user"},
    ]
    assert stable_player_fingerprint(players) == stable_player_fingerprint(reversed(players))


def test_tracker_detects_clock_reset_with_same_roster():
    tracker = GameSessionTracker()
    players = [{"id": 1, "name": "Player", "type": "user"}]

    assert tracker.observe(players, 120) is True
    assert tracker.observe(players, 121) is False
    assert tracker.observe(players, 0) is True


def test_tracker_keeps_last_time_when_response_omits_display_time():
    tracker = GameSessionTracker()
    players = [{"id": 1, "name": "Player", "type": "user"}]

    tracker.observe(players, 120)
    tracker.observe(players, None)
    assert tracker.observe(players, 0) is True
