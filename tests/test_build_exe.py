# -*- coding: utf-8 -*-


def test_build_command_keeps_external_assets_out_of_onefile(monkeypatch):
    import build_exe

    commands = []

    monkeypatch.setattr(build_exe, "clean_build_folders", lambda: None)
    monkeypatch.setattr(build_exe.os, "system", lambda command: commands.append(command) or 1)

    build_exe.build_exe(use_upx=False, separate_libs=False)

    assert commands
    assert '"SC2 Timer.spec"' in commands[0]
    assert "src/main.py" not in commands[0]
    assert '--add-data="img;img"' not in commands[0]
    assert '--add-data="scripts/*;."' not in commands[0]


def test_build_command_passes_packaging_mode_through_environment(monkeypatch):
    import build_exe

    commands = []

    monkeypatch.setattr(build_exe, "clean_build_folders", lambda: None)
    monkeypatch.setattr(build_exe.os, "system", lambda command: commands.append(command) or 1)

    build_exe.build_exe(use_upx=False, separate_libs=True)

    assert commands
    assert "--upx-dir" not in commands[0]
    assert build_exe.os.environ["SC2_TIMER_USE_UPX"] == "0"
    assert build_exe.os.environ["SC2_TIMER_SEPARATE_LIBS"] == "1"
