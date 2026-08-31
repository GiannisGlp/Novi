"""Backchannel behavior (plan 24, Phase 17).

Natural non-content responses (yeah, right, okay, mm-hm, I see, exactly) used
only when appropriate. Backchannels never interrupt speech — they occur during
pauses, are bounded by a cooldown, and are suppressed when the user has
completed a full turn and expects a real response.

Deterministic and hardware-free.
"""

from __future__ import annotations

from typing import Any

BACKCHANNELS = ("yeah", "right", "okay", "mm-hm", "I see", "exactly")

MIN_PAUSE_SECONDS = 0.8
MAX_PAUSE_SECONDS = 2.5
COOLDOWN_CYCLES = 6


class BackchannelManager:
    """Decides when a backchannel is appropriate (plan §17)."""

    def __init__(self, *, cooldown_cycles: int = COOLDOWN_CYCLES) -> None:
        self.cooldown_cycles = cooldown_cycles
        self.tokens = list(BACKCHANNELS)
        self.last_backchannel_cycle: int = -10**9

    def opportunity(
        self,
        *,
        user_speaking: bool,
        pause_seconds: float,
        turn_complete: bool = False,
        cycle: int = 0,
    ) -> str | None:
        """Return a backchannel token, or None when inappropriate."""
        if user_speaking:
            return None  # never interrupt speech (plan §17)
        if turn_complete:
            return None  # user expects a real response, not a filler
        if not (MIN_PAUSE_SECONDS <= pause_seconds <= MAX_PAUSE_SECONDS):
            return None
        if cycle - self.last_backchannel_cycle < self.cooldown_cycles:
            return None
        self.last_backchannel_cycle = cycle
        return self.tokens[cycle % len(self.tokens)]

    def snapshot(self) -> dict[str, Any]:
        return {
            "cooldown_cycles": self.cooldown_cycles,
            "tokens": list(self.tokens),
            "last_backchannel_cycle": self.last_backchannel_cycle,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "BackchannelManager":
        manager = cls(cooldown_cycles=int(data.get("cooldown_cycles", COOLDOWN_CYCLES)))
        tokens = data.get("tokens")
        if tokens:
            manager.tokens = list(tokens)
        manager.last_backchannel_cycle = int(data.get("last_backchannel_cycle", -10**9))
        return manager
