"""Emotional timing (plan 24, Phase 16).

Maturity requires timing: do not immediately respond to every emotional cue.
The decider weighs reaction delay, conversation phase, user speaking state,
pause sensitivity, interruption cost and cooldown (plan §20).

  - user pauses for 1 second → wait
  - user remains silent for 8 seconds after a distressing topic → evaluate
    whether support is useful

Thresholds are configurable and meant to be learned from evaluation, not
hard-coded as universal human rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EmotionalTiming:
    """Configurable timing parameters (plan §20)."""

    reaction_delay_seconds: float = 1.5
    pause_sensitivity: float = 0.5
    interruption_cost: float = 0.3
    cooldown_cycles: int = 3


class TimingDecider:
    """Decides whether to respond now, wait, or evaluate support."""

    def __init__(
        self,
        *,
        pause_threshold_seconds: float = 2.0,
        distress_silence_seconds: float = 8.0,
        cooldown_cycles: int = 3,
    ) -> None:
        self.pause_threshold_seconds = pause_threshold_seconds
        self.distress_silence_seconds = distress_silence_seconds
        self.cooldown_cycles = cooldown_cycles
        self.last_responded_cycle: int = -10**9

    def decide(
        self,
        *,
        user_pause_seconds: float = 0.0,
        user_speaking: bool = False,
        distressing_topic: bool = False,
        cycle: int = 0,
    ) -> dict[str, Any]:
        """Return {"action": "respond"|"wait"|"evaluate_support", "reason": str}."""
        if user_speaking:
            return {"action": "wait", "reason": "user_speaking"}
        if cycle - self.last_responded_cycle < self.cooldown_cycles:
            return {"action": "wait", "reason": "cooldown"}
        if distressing_topic and user_pause_seconds >= self.distress_silence_seconds:
            return {"action": "evaluate_support", "reason": "silence_after_distress"}
        if user_pause_seconds < self.pause_threshold_seconds:
            return {"action": "wait", "reason": "short_pause"}
        return {"action": "respond", "reason": "clear_turn"}

    def note_responded(self, *, cycle: int) -> None:
        self.last_responded_cycle = cycle

    def snapshot(self) -> dict[str, Any]:
        return {
            "pause_threshold_seconds": self.pause_threshold_seconds,
            "distress_silence_seconds": self.distress_silence_seconds,
            "cooldown_cycles": self.cooldown_cycles,
            "last_responded_cycle": self.last_responded_cycle,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "TimingDecider":
        decider = cls(
            pause_threshold_seconds=float(data.get("pause_threshold_seconds", 2.0)),
            distress_silence_seconds=float(data.get("distress_silence_seconds", 8.0)),
            cooldown_cycles=int(data.get("cooldown_cycles", 3)),
        )
        decider.last_responded_cycle = int(data.get("last_responded_cycle", -10**9))
        return decider
