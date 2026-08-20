"""Temporal and causal cognition for the Mac Brain.

Implements docs/03-cognition/08 (temporal & causal reasoning) as a deterministic,
model-independent layer:
  - an event **timeline** with cycle ordering and recency/freshness;
  - **sequence/recurrence** tracking;
  - **causal-link learning** (A is observed within a window before/with B) with a
    confidence tier (observed / inferred / plausible_cause / verified);
  - **prediction** of the most likely event after a current event;
  - **stale state** detection.

Boundaries honored (docs/03-cognition 08):
  - Observations are separated from inferences; historical episodes remain owned by
    Memory, this layer owns semantic ordering/recurrence/causal prediction.
  - Causal/predictive confidence is never a hard timing guarantee for safety-critical
    control and never rewrites observed history.
  - Event time vs observation vs processing time stay distinguishable; ambiguous
    ordering preserves uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VERIFIED_COUNT = 6
VERIFIED_CONFIDENCE = 0.7
PLAUSIBLE_COUNT = 3
PLAUSIBLE_CONFIDENCE = 0.55


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


@dataclass
class CausalLink:
    cause: str
    effect: str
    confidence: float
    evidence_count: int
    relation: str  # observed | inferred | plausible_cause | verified

    def snapshot(self) -> dict[str, Any]:
        return {"cause": self.cause, "effect": self.effect, "confidence": round(self.confidence, 3), "evidence_count": self.evidence_count, "relation": self.relation}


class TemporalModel:
    """Bounded event series + on-demand causal-link inference."""

    def __init__(self, window: int = 3, history_cap: int = 200, timeline_depth: int = 20) -> None:
        self.window = window
        self.history_cap = history_cap
        self.timeline_depth = timeline_depth
        self._series: list[tuple[int, frozenset[str]]] = []
        self._timeline: list[dict[str, Any]] = []
        self._last_seen: dict[str, int] = {}

    def record(self, events: set[str], *, cycle: int, now: str = "") -> None:
        events = set(events)
        self._series.append((cycle, frozenset(events)))
        if len(self._series) > self.history_cap:
            self._series = self._series[-self.history_cap:]
        for event in events:
            self._last_seen[event] = cycle
        self._timeline.append({"cycle": cycle, "events": sorted(events), "now": now})
        if len(self._timeline) > self.timeline_depth:
            self._timeline = self._timeline[-self.timeline_depth:]

    def _occurrences(self, event: str) -> list[int]:
        return [i for i, (_, s) in enumerate(self._series) if event in s]

    def _follows_within_window(self, i: int, event: str) -> bool:
        base = self._series[i][0]
        for j in range(i, len(self._series)):
            if self._series[j][0] - base > self.window:
                break
            if event in self._series[j][1]:
                return True
        return False

    def _tier(self, count: int, confidence: float) -> str:
        if count >= VERIFIED_COUNT and confidence >= VERIFIED_CONFIDENCE:
            return "verified"
        if count >= PLAUSIBLE_COUNT and confidence >= PLAUSIBLE_CONFIDENCE:
            return "plausible_cause"
        return "inferred" if count >= 2 else "observed"

    def causal_confidence(self, cause: str, effect: str) -> CausalLink | None:
        oc = self._occurrences(cause)
        if not oc:
            return None
        hits = sum(1 for i in oc if self._follows_within_window(i, effect))
        if hits == 0:
            return None
        conf = hits / len(oc)
        return CausalLink(cause, effect, _clamp01(conf), hits, self._tier(hits, conf))

    def expected_after(self, event: str, *, limit: int = 5, min_confidence: float = 0.3) -> list[CausalLink]:
        links = []
        seen = set()
        for (_, s) in self._series:
            for other in s:
                if other != event and other not in seen:
                    seen.add(other)
        for other in seen:
            link = self.causal_confidence(event, other)
            if link is not None and link.confidence >= min_confidence:
                links.append(link)
        links.sort(key=lambda link: -link.confidence)
        return links[:limit]

    def top_links(self, *, limit: int = 8) -> list[CausalLink]:
        all_events = {e for (_, s) in self._series for e in s}
        links = []
        for cause in all_events:
            for effect in all_events:
                if cause == effect:
                    continue
                link = self.causal_confidence(cause, effect)
                if link is not None:
                    links.append(link)
        links.sort(key=lambda link: (-link.evidence_count, -link.confidence))
        return links[:limit]

    def recency(self, event: str, cycle: int) -> float:
        last = self._last_seen.get(event)
        if last is None:
            return 0.0
        return max(0.0, 1.0 - (cycle - last) / 20.0)

    def is_stale(self, event: str, cycle: int, *, stale_after: int = 10) -> bool:
        last = self._last_seen.get(event)
        return last is None or (cycle - last) >= stale_after

    def timeline(self, limit: int = 5) -> list[dict[str, Any]]:
        return self._timeline[-limit:]

    def snapshot(self) -> dict[str, Any]:
        return {
            "series": [(c, sorted(s)) for (c, s) in self._series],
            "last_seen": dict(self._last_seen),
            "timeline": self._timeline[-self.timeline_depth:],
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "TemporalModel":
        model = cls()
        model._series = [(c, frozenset(s)) for (c, s) in data.get("series", [])]
        model._last_seen = {k: int(v) for k, v in data.get("last_seen", {}).items()}
        model._timeline = list(data.get("timeline", []))
        return model
