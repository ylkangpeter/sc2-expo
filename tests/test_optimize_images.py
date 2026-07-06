# -*- coding: utf-8 -*-

import os
import subprocess
import sys

from PIL import Image


def test_optimize_images_import_does_not_require_cv2_or_numpy():
    script = """
import builtins
original_import = builtins.__import__
def blocked_import(name, *args, **kwargs):
    if name in {"cv2", "numpy"} or name.startswith("numpy."):
        raise ImportError(f"blocked {name}")
    return original_import(name, *args, **kwargs)
builtins.__import__ = blocked_import
import optimize_images
print(optimize_images.compress_image.__name__)
"""
    env = {**os.environ, "PYTHONPATH": os.getcwd()}

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "compress_image" in result.stdout


def test_optimize_images_preserves_png_format_and_skips_svg_same_path(tmp_path):
    import optimize_images

    png_path = tmp_path / "sample.png"
    svg_path = tmp_path / "icon.svg"

    Image.new("RGB", (4, 4), "red").save(png_path)
    svg_path.write_text("<svg></svg>", encoding="utf-8")

    optimize_images.optimize_images(str(tmp_path))

    with Image.open(png_path) as image:
        assert image.format == "PNG"
        assert image.size == (4, 4)
    assert svg_path.read_text(encoding="utf-8") == "<svg></svg>"
