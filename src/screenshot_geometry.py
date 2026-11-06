# -*- coding: utf-8 -*-
"""Pure coordinate helpers for monitor screenshots."""

from typing import Tuple

Point = Tuple[int, int]
Rect = Tuple[int, int, int, int]


def scale_point(point, dpi_scale: float) -> Point:
    """Convert a logical point to physical screen coordinates."""
    return int(point[0] / dpi_scale), int(point[1] / dpi_scale)


def normalize_rect(start: Point, end: Point) -> Rect:
    """Return a rectangle with its corners ordered top-left to bottom-right."""
    return min(start[0], end[0]), min(start[1], end[1]), max(start[0], end[0]), max(start[1], end[1])


def move_rect(rect: Rect, dx: int = 0, dy: int = 0) -> Rect:
    """Translate a rectangle by a physical coordinate offset."""
    x1, y1, x2, y2 = rect
    return x1 + dx, y1 + dy, x2 + dx, y2 + dy


def clip_rect(rect: Rect, width: int, height: int) -> Rect:
    """Clip a rectangle to an image with the given dimensions."""
    x1, y1, x2, y2 = rect
    return (
        max(0, min(width, x1)),
        max(0, min(height, y1)),
        max(0, min(width, x2)),
        max(0, min(height, y2)),
    )
