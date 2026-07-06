# -*- coding: utf-8 -*-

import io

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
