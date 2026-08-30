"""Initiative scoring (plan 22, Phase 11).

Builds on the existing SocialInitiative instead of replacing it (plan §15).

Target score:

    initiative_score = relevance × confidence × social_opportunity × novelty
                     × expected_value × urgency
                     - interruption_cost - repetition_penalty - fatigue_penalty

Bands (starting configuration, meant to be measured and tuned):
    < 0.25 SILENCE · 0.25–0.50 HOLD · 0.50–0.70 MONITOR · 0.70–0.85 CONSIDER
    > 0.85 INITIATE

Plus the three hard gates:
- Task 11.1 per-person cooldown — no repeated greetings from tracker spam;
- Task 11.2 per-event deduplication — a stable event identity/hash;
- Task 11.3 conversation suppression — proactive candidates queue/hold while
  a user is speaking or Novi is composing (safety-critical events override).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

SILENCE = "SILENCE"
HOLD = "HOLD"
MONITOR = "MONITOR"
CONSIDER = "CONSIDER"
INITIATE = "INITIATE"


@dataclass
class InitiativeScore:
    score: float
    band: str
    components: dict[str, float] = field(default_factory=dict)
    penalties: dict[str, float] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "band": self.band,
            "components": {k: round(v, 3) for k, v in self.components.items()},
            "penalties": {k: round(v, 3) for k, v in self.penalties.items()},
        }


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


class InitiativeScorer:
    """The plan §15 target formula with its policy bands."""

    def score(
        self,
        *,
        relevance: float = 0.0,
        confidence: float = 0.0,
        social_opportunity: float = 0.0,
        novelty: float = 0.0,
        expected_value: float = 0.0,
        urgency: float = 0.0,
        interruption_cost: float = 0.0,
        repetition_penalty: float = 0.0,
        fatigue_penalty: float = 0.0,
    ) -> InitiativeScore:
        components = {
            "relevance": _clamp01(relevance),
            "confidence": _clamp01(confidence),
            "social_opportunity": _clamp01(social_opportunity),
            "novelty": _clamp01(novelty),
            "expected_value": _clamp01(expected_value),
            "urgency": _clamp01(urgency),
        }
        penalties = {
            "interruption_cost": _clamp01(interruption_cost),
            "repetition_penalty": _clamp01(repetition_penalty),
            "fatigue_penalty": _clamp01(fatigue_penalty),
        }
        product = 1.0
        for value in components.values():
            product *= value
        # Geometric mean of the multiplicative signals: the plan's product
        # form, normalized so the policy bands are actually reachable
        # (six 0.9 signals ≈ 0.9, not 0.53). The bands stay tunable config.
        n = max(1, len(components))
        geometric = product ** (1.0 / n)
        raw = geometric - sum(penalties.values())
        score = _clamp01(raw)
        band = self.band_for(score)
        return InitiativeScore(score=score, band=band, components=components, penalties=penalties)

    @staticmethod
    def band_for(score: float) -> str:
        if score > 0.85:
            return INITIATE
        if score >= 0.70:
            return CONSIDER
        if score >= 0.50:
            return MONITOR
        if score >= 0.25:
            return HOLD
        return SILENCE


def stable_event_key(event: dict[str, Any]) -> str:
    """Task 11.2: a stable identity/hash for an event so multiple sensors
    cannot produce repeated speech for the same underlying happening."""
    kind = event.get("kind", "")
    entity = event.get("entity", "") or ""
    payload = event.get("payload") or {}
    stable = json.dumps(
        {"kind": kind, "entity": entity, "payload": payload},
        sort_keys=True, default=str,
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]


class InitiativeGate:
    """Hard gates around initiative (Tasks 11.1–11.3)."""

    def __init__(self, *, per_person_cooldown_cycles: int = 60, event_ttl_cycles: int = 300) -> None:
        self.per_person_cooldown_cycles = per_person_cooldown_cycles
        self.event_ttl_cycles = event_ttl_cycles
        self._last_spoken: dict[str, int] = {}
        self._seen_events: dict[str, int] = {}

    def allow(
        self,
        *,
        person: str,
        cycle: int,
        event_key: str = "",
        user_speaking: bool = False,
        novi_composing: bool = False,
        safety: bool = False,
    ) -> tuple[bool, str]:
        """(allowed, reason). Safety overrides every suppression (plan §11.3)."""
        if safety:
            return True, "safety_override"
        key = (person or "").lower()
        if event_key:
            seen = self._seen_events.get(event_key, -10**9)
            if cycle - seen < self.event_ttl_cycles:
                return False, "event_dedup"
        last = self._last_spoken.get(key, -10**9)
        if cycle - last < self.per_person_cooldown_cycles:
            return False, "per_person_cooldown"
        if user_speaking or novi_composing:
            return False, "conversation_suppression"
        return True, "ok"

    def note_spoken(self, *, person: str, cycle: int, event_key: str = "") -> None:
        self._last_spoken[(person or "").lower()] = cycle
        if event_key:
            self._seen_events[event_key] = cycle

    def reset(self) -> None:
        self._last_spoken.clear()
        self._seen_events.clear()
