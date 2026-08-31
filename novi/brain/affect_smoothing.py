"""Temporal affect smoothing (plan 24, Phase 4).

Avoid reacting to single frames or words. Each affective signal is smoothed
over a short-term window with:

  - a recency-weighted moving average (EMA) so one loud word cannot spike the
    estimate;
  - a minimum evidence count before a signal may transition to "high";
  - a confidence threshold — low-confidence evidence never triggers a
    transition;
  - hysteresis — once "high", a small drop does not flip back to "low";
  - a cooldown after a drop — a rapid re-rise cannot immediately flip back to
    "high" (prevents calm → tense → calm → tense oscillation from noisy
    sensor readings);
  - exponential decay — without new evidence the estimate falls toward
    baseline (plan §28).

Deterministic and hardware-free: cycle-based, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class SmoothedSignal:
    """One smoothed affective signal (plan §8)."""

    name: str
    value: float = 0.0  # smoothed estimate [0,1]
    confidence: float = 0.0  # latest observation confidence [0,1]
    evidence_count: int = 0  # confident observations in the current window
    state: str = "low"  # low | high
    last_updated_cycle: int = 0
    cooldown_until_cycle: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 3),
            "confidence": round(self.confidence, 3),
            "evidence_count": self.evidence_count,
            "state": self.state,
            "last_updated_cycle": self.last_updated_cycle,
            "cooldown_until_cycle": self.cooldown_until_cycle,
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "SmoothedSignal":
        return cls(
            name=str(data.get("name", "")),
            value=float(data.get("value", 0.0)),
            confidence=float(data.get("confidence", 0.0)),
            evidence_count=int(data.get("evidence_count", 0)),
            state=str(data.get("state", "low")),
            last_updated_cycle=int(data.get("last_updated_cycle", 0)),
            cooldown_until_cycle=int(data.get("cooldown_until_cycle", 0)),
        )


class AffectSmoother:
    """Cycle-based temporal smoother over named affective signals."""

    def __init__(
        self,
        *,
        min_evidence: int = 2,
        confidence_threshold: float = 0.5,
        hysteresis: float = 0.15,
        cooldown_cycles: int = 3,
        decay_rate: float = 0.1,
        window_cycles: int = 5,
        alpha: float = 0.7,
    ) -> None:
        self.min_evidence = min_evidence
        self.confidence_threshold = confidence_threshold
        self.hysteresis = hysteresis
        self.cooldown_cycles = cooldown_cycles
        self.decay_rate = decay_rate
        self.window_cycles = window_cycles
        self.alpha = alpha
        self._signals: dict[str, SmoothedSignal] = {}

    def observe(
        self,
        name: str,
        *,
        value: float,
        confidence: float,
        cycle: int,
    ) -> SmoothedSignal:
        """Feed one observation; returns the updated smoothed signal."""
        sig = self._signals.setdefault(name, SmoothedSignal(name=name))
        value = _clamp01(value)
        confidence = _clamp01(confidence)

        gap = max(0, cycle - sig.last_updated_cycle)
        if gap > 1:
            # exponential decay over the skipped cycles
            sig.value *= (1.0 - self.decay_rate) ** (gap - 1)
        if gap > self.window_cycles:
            # the short-term window expired — start a fresh evidence count
            sig.evidence_count = 0

        # recency-weighted moving average
        sig.value = _clamp01(sig.value * (1.0 - self.alpha) + value * self.alpha)
        sig.confidence = confidence
        sig.last_updated_cycle = cycle
        if confidence >= self.confidence_threshold:
            sig.evidence_count += 1

        # transitions are blocked during a cooldown (no oscillation)
        if cycle < sig.cooldown_until_cycle:
            return sig

        if (
            sig.state == "low"
            and sig.evidence_count >= self.min_evidence
            and sig.value >= self.confidence_threshold
        ):
            sig.state = "high"
            sig.evidence_count = 0
        elif sig.state == "high" and sig.value < self.confidence_threshold - self.hysteresis:
            sig.state = "low"
            sig.evidence_count = 0
            sig.cooldown_until_cycle = cycle + self.cooldown_cycles
        return sig

    def get(self, name: str) -> SmoothedSignal | None:
        return self._signals.get(name)

    def all(self) -> list[SmoothedSignal]:
        return list(self._signals.values())

    def snapshot(self) -> dict[str, Any]:
        return {"signals": {name: sig.snapshot() for name, sig in self._signals.items()}}

    @classmethod
    def from_snapshot(cls, data: dict[str, Any] | None) -> "AffectSmoother":
        smoother = cls()
        if not data:
            return smoother
        for name, raw in data.get("signals", {}).items():
            smoother._signals[name] = SmoothedSignal.from_snapshot(raw)
        return smoother
