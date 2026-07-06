# -*- coding: utf-8 -*-

"""Path helpers for UI modules that moved under the ui package."""

from pathlib import Path


def source_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config.py"
