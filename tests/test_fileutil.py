# -*- coding: utf-8 -*-

import os


def test_get_resources_dir_prefers_current_working_directory(tmp_path, monkeypatch):
    import fileutil

    resources_dir = tmp_path / "resources" / "maps"
    resources_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    assert fileutil.get_resources_dir("resources", "maps") == str(resources_dir)


def test_list_files_returns_only_files(tmp_path):
    import fileutil

    (tmp_path / "one.txt").write_text("1", encoding="utf-8")
    (tmp_path / "nested").mkdir()

    assert fileutil.list_files(str(tmp_path)) == ["one.txt"]
    assert fileutil.list_files(None) == []


def test_get_file_path_requires_directory_and_filename():
    import fileutil

    assert fileutil.get_file_path("root", "file.txt") == os.path.join("root", "file.txt")
    assert fileutil.get_file_path("", "file.txt") is None
    assert fileutil.get_file_path("root", "") is None
