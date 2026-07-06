# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import types

from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


def test_image_cache_returns_highest_similarity_match():
    from lightweight_image_util import LightweightImageCache

    cache = LightweightImageCache()
    target = Image.new("RGB", (2, 2), "black")
    cache.cache = {
        os.path.join("fixtures", "white.png"): Image.new("RGB", (2, 2), "white"),
        os.path.join("fixtures", "black.png"): Image.new("RGB", (2, 2), "black"),
    }

    best_match, similarity = cache.get_most_similar_image(target)

    assert best_match == "black"
    assert similarity == 1.0


def test_image_cache_mse_uses_signed_math_for_pixel_differences():
    from lightweight_image_util import LightweightImageCache

    cache = LightweightImageCache()
    black = Image.new("RGB", (1, 1), "black")
    white = Image.new("RGB", (1, 1), "white")

    assert cache.mse(black, white) == 65025.0


def test_screenshot_create_buttons_imports_tkinter_locally(monkeypatch):
    import image_util

    class FakeButton:
        def __init__(self, *args, **kwargs):
            self.placed = False

        def lift(self):
            pass

        def place(self, **kwargs):
            self.placed = True

        def destroy(self):
            pass

    class FakeWindow:
        def winfo_height(self):
            return 500

    fake_tkinter = types.SimpleNamespace(Button=FakeButton)
    monkeypatch.setitem(sys.modules, "tkinter", fake_tkinter)

    tool = image_util.ScreenshotTool.__new__(image_util.ScreenshotTool)
    tool.ui_window = FakeWindow()
    tool.confirm_button = None
    tool.cancel_button = None

    tool.create_buttons(10, 10, 100, 100)

    assert isinstance(tool.confirm_button, FakeButton)
    assert isinstance(tool.cancel_button, FakeButton)


def test_image_util_import_does_not_require_win32ui():
    script = """
import builtins
original_import = builtins.__import__
def blocked_import(name, *args, **kwargs):
    if name == "win32ui":
        raise ImportError("blocked win32ui")
    return original_import(name, *args, **kwargs)
builtins.__import__ = blocked_import
import image_util
print(image_util.ScreenshotTool.__name__)
"""
    env = {**os.environ, "PYTHONPATH": os.path.abspath("src")}

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "ScreenshotTool" in result.stdout


def test_capture_screen_core_uses_imagegrab_monitor_bbox(monkeypatch):
    import image_util

    monitor_handle = object()
    captured_image = Image.new("RGB", (400, 400), "red")
    grab_calls = []

    monkeypatch.setattr(image_util.win32api, "EnumDisplayMonitors", lambda: [(monitor_handle, None, None)])
    monkeypatch.setattr(
        image_util.win32api,
        "GetMonitorInfo",
        lambda handle: {"Monitor": (100, 200, 500, 600)} if handle is monitor_handle else {},
    )
    monkeypatch.setattr(
        image_util.ImageGrab,
        "grab",
        lambda *, bbox, all_screens: grab_calls.append((bbox, all_screens)) or captured_image,
    )

    tool = image_util.ScreenshotTool.__new__(image_util.ScreenshotTool)
    tool.dpi = 1
    tool.root = None

    result = tool.capture_screen_core((10, 20), (110, 120), save_file=False)

    assert grab_calls == [((100, 200, 500, 600), True)]
    assert result.size == (100, 100)


def test_capture_screen_rect_saves_qrect_area(tmp_path, monkeypatch):
    import image_util

    class FakeRect:
        def x(self):
            return 10

        def y(self):
            return 20

        def width(self):
            return 30

        def height(self):
            return 40

    class FakeScreenshotTool:
        def capture_screen_core(self, start_pos, end_pos, save_file):
            assert start_pos == (10, 20)
            assert end_pos == (40, 60)
            assert save_file is False
            return Image.new("RGB", (30, 40), "blue")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(image_util, "ScreenshotTool", FakeScreenshotTool)

    saved_path = image_util.capture_screen_rect(FakeRect())

    assert saved_path is not None
    assert os.path.exists(saved_path)
    assert Image.open(saved_path).size == (30, 40)


def test_detect_troop_timeout_callback_does_not_crash_on_found_flag(monkeypatch):
    import show_fence

    callbacks = []

    class FakeScreenshotTool:
        pass

    class FakeImageCache:
        pass

    class ImmediateThread:
        def __init__(self, target, daemon=False):
            self.target = target
            self.daemon = daemon

        def start(self):
            self.target()

    times = iter([0, 999])

    monkeypatch.setattr(show_fence.config, "DEBUG_SHOW_ENEMY_INFO_SQUARE", True)
    monkeypatch.setattr(show_fence.config, "GAME_ICO_RECONGIZE_TIMEOUT", 1)
    monkeypatch.setattr(show_fence.image_util, "ScreenshotTool", FakeScreenshotTool)
    monkeypatch.setattr(show_fence.image_util, "ImageCache", FakeImageCache)
    monkeypatch.setattr(show_fence.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(show_fence.time, "time", lambda: next(times))
    monkeypatch.setattr(show_fence.time, "sleep", lambda _seconds: None)

    show_fence.detect_troop(callbacks.append)

    assert callbacks == [{"success": False, "reason": "timeout"}]
