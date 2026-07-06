# -*- coding: utf-8 -*-

import os
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
