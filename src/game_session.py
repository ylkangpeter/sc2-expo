# -*- coding: utf-8 -*-
"""Pure game-session state tracking used by the SC2 API poller.

Keeping this logic independent from Qt and the HTTP loop makes session-boundary
behavior easy to test and prevents UI code from owning mutable game identity.
"""

from dataclasses import dataclass
import json
from typing import Any, Iterable, Mapping, Optional


def stable_player_fingerprint(players: Iterable[Mapping[str, Any]]) -> int:
    """Return a stable fingerprint for the current player roster.

    The API does not guarantee player order, so only stable identity fields are
    used and the records are sorted before hashing.
    """

    canonical_players = sorted(
        (
            {
                "id": player.get("id", ""),
                "name": player.get("name", ""),
                "type": player.get("type", ""),
            }
            for player in players
        ),
        key=lambda player: (
            str(player["id"]),
            str(player["name"]),
            str(player["type"]),
        ),
    )
    # Python's hash is intentionally process-local, which is sufficient here:
    # the tracker only compares values during one process lifetime.
    return hash(json.dumps(canonical_players, sort_keys=True))


@dataclass
class GameSessionTracker:
    """Detect a new game from roster changes or a game-clock reset."""

    current_id: Optional[int] = None
    last_display_time: Optional[float] = None

    def observe(
        self,
        players: Iterable[Mapping[str, Any]],
        display_time: Any = None,
    ) -> bool:
        """Record one API response and return whether it starts a new game."""

        new_id = stable_player_fingerprint(players)
        time_went_back = False
        if display_time is not None and self.last_display_time is not None:
            try:
                time_went_back = float(display_time) < float(self.last_display_time)
            except (TypeError, ValueError):
                time_went_back = False

        is_new = new_id != self.current_id or time_went_back
        self.current_id = new_id
        if display_time is not None:
            self.last_display_time = display_time
        return is_new

    def reset(self) -> None:
        self.current_id = None
        self.last_display_time = None
