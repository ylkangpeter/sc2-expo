# -*- coding: utf-8 -*-

from commander_logic import available_commanders


def test_available_commanders_filters_blacklist_and_missing_region_urls():
    avatar = [["raynor", "kerrigan"], ["artanis"]]
    urls = {
        "raynor": {"CN": "raynor-url"},
        "kerrigan": {"KR": "kerrigan-url"},
        "artanis": {},
    }

    assert available_commanders(avatar, ["kerrigan"], urls, "CN") == ["raynor"]
