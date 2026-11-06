# -*- coding: utf-8 -*-

from ui.window_geometry import clamp_window_position, find_screen_for_window


class FakeRect:
    def __init__(self, x, y, width, height, center=None):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._center = center

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._width

    def height(self):
        return self._height

    def center(self):
        return self._center if self._center is not None else (self._x, self._y)

    def contains(self, point):
        return point == self._center


class FakeScreen:
    def __init__(self, geometry):
        self._geometry = geometry

    def geometry(self):
        return self._geometry


def test_find_screen_uses_window_center_and_fallback():
    center = object()
    matching = FakeScreen(FakeRect(0, 0, 100, 100, center=center))
    other = FakeScreen(FakeRect(100, 0, 100, 100, center=object()))
    fallback = object()

    assert find_screen_for_window(FakeRect(0, 0, 20, 20, center), [other, matching], fallback) is matching
    assert find_screen_for_window(FakeRect(0, 0, 20, 20, object()), [other], fallback) is fallback


def test_clamp_window_position_preserves_screen_origin():
    screen = FakeRect(-1920, 100, 1920, 1080)

    assert clamp_window_position(-2500, -50, screen, 100, 50) == (-1920, 100)
    assert clamp_window_position(-100, 500, screen, 100, 50) == (-100, 500)
