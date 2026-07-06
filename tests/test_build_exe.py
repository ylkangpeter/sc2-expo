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


def test_parse_args_accepts_boolean_flags_without_values():
    import build_exe

    args = build_exe.parse_args(["--separate-libs", "--use-upx"])

    assert args.separate_libs is True
    assert args.upx is True


def test_parse_args_accepts_explicit_zero_values():
    import build_exe

    args = build_exe.parse_args(["--separate-libs", "0", "--upx", "0"])

    assert args.separate_libs is False
    assert args.upx is False


def test_create_zip_includes_entire_onedir_bundle(tmp_path, monkeypatch):
    import zipfile

    import build_exe

    bundle_dir = tmp_path / "dist" / "SC2 Timer"
    internal_dir = bundle_dir / "_internal"
    internal_dir.mkdir(parents=True)
    (bundle_dir / "SC2 Timer.exe").write_text("exe", encoding="utf-8")
    (internal_dir / "Qt5Core.dll").write_text("dll", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    build_exe.create_zip(separate_libs=True)

    with zipfile.ZipFile(tmp_path / "dist" / "SC2_Timer.zip") as zip_file:
        assert sorted(zip_file.namelist()) == [
            "SC2 Timer.exe",
            "_internal/Qt5Core.dll",
        ]
