# -*- coding: utf-8 -*-

import io
import os
import subprocess
import sys

from PIL import Image


def test_scan_directory_loads_only_png_files(tmp_path, monkeypatch):
    import lightweight_image_util

    troops_dir = tmp_path / "troops"
    troops_dir.mkdir()
    Image.new("RGB", (1, 1), "black").save(troops_dir / "black.png")
    Image.new("RGB", (1, 1), "white").save(troops_dir / "white.PNG")
    (troops_dir / "notes.txt").write_text("ignore", encoding="utf-8")

    monkeypatch.setattr(lightweight_image_util, "get_resources_dir", lambda *parts: str(troops_dir))

    cache = lightweight_image_util.LightweightImageCache()
    cache.scan_directory()

    assert {path.name for path in map(type(troops_dir), cache.cache.keys())} == {"black.png", "white.PNG"}


def test_scan_directory_uses_correct_default_template_path(tmp_path, monkeypatch):
    import lightweight_image_util

    resources_dir = tmp_path / "resources"
    troops_dir = resources_dir / "screen_capture" / "troops"
    troops_dir.mkdir(parents=True)
    Image.new("RGB", (1, 1), "black").save(troops_dir / "black.png")

    def resources_path(*parts):
        if parts == ("resources",):
            return str(resources_dir)
        return None

    monkeypatch.setattr(lightweight_image_util, "get_resources_dir", resources_path)

    cache = lightweight_image_util.LightweightImageCache()
    cache.scan_directory()

    assert str(troops_dir / "black.png") in cache.cache


def test_scan_directory_does_not_create_missing_template_directory(tmp_path, monkeypatch):
    import lightweight_image_util

    resources_dir = tmp_path / "resources"
    resources_dir.mkdir()

    def resources_path(*parts):
        if parts == ("resources",):
            return str(resources_dir)
        return None

    monkeypatch.setattr(lightweight_image_util, "get_resources_dir", resources_path)
    lightweight_image_util.LightweightImageCache().scan_directory()

    assert not (resources_dir / "screen_capture").exists()


def test_compare_images_returns_empty_result_for_bad_image_bytes(monkeypatch):
    import lightweight_image_util

    monkeypatch.setattr(lightweight_image_util.LightweightImageCache, "scan_directory", lambda self: None)

    cache = lightweight_image_util.LightweightImageCache()

    assert cache.compare_images(b"not an image") == (None, 0.0)


def test_compare_images_returns_best_cached_match(monkeypatch):
    import lightweight_image_util

    monkeypatch.setattr(lightweight_image_util.LightweightImageCache, "scan_directory", lambda self: None)

    cache = lightweight_image_util.LightweightImageCache()
    cache.cache = {
        "black.png": Image.new("RGB", (2, 2), "black"),
        "white.png": Image.new("RGB", (2, 2), "white"),
    }
    image_bytes = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(image_bytes, format="PNG")

    assert cache.compare_images(image_bytes.getvalue()) == ("white", 1.0)


def test_lightweight_image_util_import_does_not_require_numpy():
    script = """
import builtins
original_import = builtins.__import__
def blocked_import(name, *args, **kwargs):
    if name == "numpy" or name.startswith("numpy."):
        raise ImportError("blocked numpy")
    return original_import(name, *args, **kwargs)
builtins.__import__ = blocked_import
import lightweight_image_util
print(lightweight_image_util.LightweightImageCache.__name__)
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
    assert "LightweightImageCache" in result.stdout
