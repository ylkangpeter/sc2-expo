# -*- coding: utf-8 -*-
"""Pure commander selection helpers used by the Qt selector."""

from collections.abc import Iterable, Mapping


def available_commanders(
    avatar: Iterable[Iterable[str]],
    blacklist: Iterable[str],
    commander_urls: Mapping[str, Mapping[str, str]],
    region: str,
) -> list[str]:
    """Return commanders that have a configured URL for ``region``."""

    blocked = set(blacklist)
    selected = []
    for row in avatar:
        for commander in row:
            if commander in blocked:
                continue
            region_urls = commander_urls.get(commander, {})
            if region_urls.get(region, ''):
                selected.append(commander)
    return selected
