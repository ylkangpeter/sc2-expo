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


def test_identify_map_returns_none_when_player_name_is_missing():
    from IdentifyMap import identify_map

    players = [{"name": f"player-{index}"} for index in range(9)]
    players[6].pop("name")

    assert identify_map(players) is None


def test_identify_map_uses_api_map_hint_for_schedule_variant():
    from IdentifyMap import identify_map

    players = [{"name": f"player-{index}"} for index in range(9)]
    players[6]["name"] = "神庙"
    players[8]["name"] = "岩石"

    assert identify_map(players, "往日神庙-B") == "往日神庙-B"
