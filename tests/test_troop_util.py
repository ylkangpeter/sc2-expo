# -*- coding: utf-8 -*-


def test_troop_loader_builds_troop_and_army_mappings(tmp_path, monkeypatch):
    import troop_util

    race_dir = tmp_path / "protoss"
    race_dir.mkdir()
    config_file = race_dir / "神族-Protoss.txt"
    config_file.write_text("# comment\n1\tzealot.png\n2\tstalker.png\n", encoding="utf-8")

    monkeypatch.setattr(troop_util.fileutil, "get_resources_dir", lambda *parts: str(tmp_path))

    loader = troop_util.TroopLoader()

    assert loader.get_army("神族") == "protoss"
    assert loader.get_army("Protoss") == "protoss"
    assert loader.get_troop_config("神族", 1) == "zealot.png"
    assert loader.get_troop_config("Protoss", 2) == "stalker.png"
    assert loader.get_troop_config("missing", 1) is None
