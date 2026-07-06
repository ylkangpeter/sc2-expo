# -*- coding: utf-8 -*-


def test_identify_map_matches_localized_player_names():
    from IdentifyMap import identify_map

    players = [{"name": f"player-{index}"} for index in range(7)]
    players[4]["name"] = "感染体"
    players[5]["name"] = "感应塔"

    assert identify_map(players) == "亡者之夜"


def test_identify_map_returns_none_when_player_count_does_not_match():
    from IdentifyMap import identify_map

    players = [{"name": "感染体"}, {"name": "感应塔"}]

    assert identify_map(players) is None


def test_identify_map_returns_none_when_required_name_does_not_match():
    from IdentifyMap import identify_map

    players = [{"name": f"player-{index}"} for index in range(7)]
    players[4]["name"] = "感染体"
    players[5]["name"] = "wrong"

    assert identify_map(players) is None
