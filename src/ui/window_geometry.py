# -*- coding: utf-8 -*-
"""Pure geometry helpers used by the overlay window."""


def find_screen_for_window(window_geometry, screens, fallback=None):
    """Return the screen containing the window center, or ``fallback``."""
    center = window_geometry.center()
    for screen in screens:
        if screen.geometry().contains(center):
            return screen
    return fallback


def clamp_window_position(x, y, screen_geometry, window_width, window_height):
    """Keep a child window fully inside a screen rectangle."""
    min_x = screen_geometry.x()
    max_x = min_x + max(0, screen_geometry.width() - window_width)
    min_y = screen_geometry.y()
    max_y = min_y + max(0, screen_geometry.height() - window_height)
    return min(max(x, min_x), max_x), min(max(y, min_y), max_y)
