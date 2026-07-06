# -*- coding: utf-8 -*-


def test_list_available_maps_reads_user_added_files_from_language_directory(tmp_path, monkeypatch):
    from ui import map_catalog

    maps_dir = tmp_path / "resources" / "maps" / "zh"
    maps_dir.mkdir(parents=True)
    (maps_dir / "往日神庙-A").write_text("00:30\tfirst\n", encoding="utf-8")
    (maps_dir / "mymap").write_text("00:10\tcustom\n", encoding="utf-8")
    (maps_dir / "nested").mkdir()

    monkeypatch.setattr(map_catalog, "get_resources_dir", lambda *parts: str(maps_dir))

    assert map_catalog.list_available_maps("zh") == ["mymap", "往日神庙-A"]


def test_list_available_maps_returns_empty_when_language_directory_missing(monkeypatch):
    from ui import map_catalog

    monkeypatch.setattr(map_catalog, "get_resources_dir", lambda *parts: None)

    assert map_catalog.list_available_maps("en") == []
