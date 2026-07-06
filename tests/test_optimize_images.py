# -*- coding: utf-8 -*-

import os
import subprocess
import sys


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
