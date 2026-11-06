# -*- coding: utf-8 -*-

from screenshot_geometry import clip_rect, move_rect, normalize_rect, scale_point


def test_scale_and_normalize_coordinates():
    assert scale_point((101, 203), 2) == (50, 101)
    assert normalize_rect((110, 80), (20, 140)) == (20, 80, 110, 140)


def test_move_and_clip_rect_to_monitor_image():
    rect = move_rect((100, 200, 500, 600), -100, -200)
    assert rect == (0, 0, 400, 400)
    assert clip_rect((-10, 20, 500, 700), 400, 400) == (0, 20, 400, 400)
