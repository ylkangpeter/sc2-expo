# -*- coding: utf-8 -*-

"""Map catalog helpers for files under resources/maps/<language>."""

from fileutil import get_resources_dir, list_files


def list_available_maps(language: str) -> list[str]:
    maps_dir = get_resources_dir("resources", "maps", language)
    if not maps_dir:
        return []
    return sorted(list_files(maps_dir))
