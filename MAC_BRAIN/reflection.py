"""Reflection / self-correction for the Mac Brain (Reasoning 2.0).

After Novi executes an action, the runtime records whether the action had its
intended effect (e.g. did the body move, did new detections appear). The
``ReflectionEngine`` keeps the latest assessment and a short history, and the
next reasoning decision can consult it to avoid repeating ineffective actions.

Boundaries:
  - Reflection is a learning signal, not an asserted fact; it never overrides
    Policy/Safety and never rewrites observed state.
  - Effectiveness is judged by observable outcome proxies, not intent inference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Reflection:
    cycle: int
    action: str
    intent: str
    effective: bool
    note: str
    confidence: float = 0.8

    def snapshot(self) -> dict[str, Any]:
        return {
            "cycle": self.cycle,
            "action": self.action,
            "intent": self.intent,
            "effective": self.effective,
            "note": self.note,
            "confidence": self.confidence,
        }


class ReflectionEngine:
    """Tracks the effectiveness of recent actions to inform future decisions."""

    def __init__(self, history_limit: int = 20) -> None:
        self._history: list[Reflection] = []
        self._last: Reflection | None = None
        self._history_limit = history_limit

    def record(self, *, cycle: int, action: str, intent: str, effective: bool, note: str = "") -> Reflection:
        reflection = Reflection(cycle=cycle, action=action, intent=intent, effective=effective, note=note)
        self._history.append(reflection)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit:]
        self._last = reflection
        return reflection

    def last(self) -> Reflection | None:
        return self._last

    def recent_ineffective(self, *, window: int = 3) -> bool:
        """True if the most recent actions were largely ineffective (self-correction trigger)."""
        recent = self._history[-window:]
        if not recent:
            return False
        return sum(1 for r in recent if not r.effective) >= max(1, len(recent) - 1)

    def snapshot(self) -> list[dict[str, Any]]:
        return [r.snapshot() for r in self._history]

    @classmethod
    def from_snapshot(cls, rows: list[dict[str, Any]]) -> "ReflectionEngine":
        engine = cls()
        for row in rows:
            engine.record(
                cycle=int(row.get("cycle", 0)),
                action=str(row.get("action", "")),
                intent=str(row.get("intent", "")),
                effective=bool(row.get("effective", True)),
                note=str(row.get("note", "")),
            )
        return engine
