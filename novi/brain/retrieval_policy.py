"""Composite memory retrieval policy (plan 22, Phase 5, Tasks 5.3–5.4).

Task 5.3: primary retrieval is *not* similarity-only. The composite score:

    semantic_relevance + temporal_relevance + person_relevance
  + situation_relevance + goal_relevance + causal_relevance
  + importance + confidence + provenance_quality + spatial_relevance
  + novelty − contradiction_penalty − staleness_penalty

Vector/FTS similarity is one signal among many, never the decision.

Task 5.4: retrieval is explainable — every scored memory carries its
contributions and a human-readable "why retrieved" reason list, so the
context builder can trace each memory to its source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

# Default weights (normalized; penalties applied on top, clamped to [0, 1]).
DEFAULT_WEIGHTS: dict[str, float] = {
    "semantic": 0.22,
    "temporal": 0.10,
    "person": 0.10,
    "situation": 0.10,
    "goal": 0.08,
    "causal": 0.05,
    "importance": 0.12,
    "confidence": 0.06,
    "provenance": 0.07,
    "spatial": 0.05,
    "novelty": 0.05,
}
CONTRADICTION_PENALTY = 0.25
STALENESS_PENALTY = 0.15
_STALE_AFTER_DAYS = 30.0
_HYPOTHETICAL_STATUSES = frozenset({"PREDICTED", "SIMULATED", "COUNTERFACTUAL", "HYPOTHESIZED"})


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class RetrievalContext:
    """Situation-dependent retrieval signals (all optional, all probabilistic)."""

    person: str = ""
    situation: str = ""  # situation type/label, e.g. "conversation_occurring"
    goal: str = ""  # active goal target, e.g. "test_camera"
    location: str = ""  # current place, e.g. "office"
    recently_retrieved: set[str] = field(default_factory=set)
    now: datetime | None = None


@dataclass
class ScoredMemory:
    memory_id: str
    record: Any
    score: float
    contributions: dict[str, float] = field(default_factory=dict)
    penalties: dict[str, float] = field(default_factory=dict)
    why: list[str] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "score": round(self.score, 4),
            "contributions": {k: round(v, 4) for k, v in self.contributions.items()},
            "penalties": {k: round(v, 4) for k, v in self.penalties.items()},
            "why": list(self.why),
        }


class RetrievalScorer:
    """Deterministic, explainable composite retrieval scorer."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = dict(DEFAULT_WEIGHTS if weights is None else weights)

    # ---- signal extraction (defensive: any record shape) ----

    def _text(self, record: Any) -> str:
        content = getattr(record, "content", "")
        return str(content) if content is not None else ""

    def _entities(self, record: Any) -> tuple[str, ...]:
        refs = getattr(record, "entity_refs", ()) or ()
        return tuple(str(r) for r in refs)

    def _created_at(self, record: Any) -> datetime | None:
        raw = getattr(record, "created_at", "") or ""
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:  # noqa: BLE001 - malformed timestamps score as neutral
            return None

    # ---- individual signals ----

    def _temporal(self, record: Any, now: datetime) -> float:
        created = self._created_at(record)
        if created is None:
            return 0.5  # unknown age: neutral
        age_s = max(0.0, (now - created).total_seconds())
        return 1.0 / (1.0 + age_s / 3600.0)

    def _person(self, record: Any, ctx: RetrievalContext) -> float:
        if not ctx.person:
            return 0.0
        target = ctx.person.strip().lower()
        if target in {e.lower() for e in self._entities(record)}:
            return 1.0
        return 1.0 if target in self._text(record).lower() else 0.0

    def _situation(self, record: Any, ctx: RetrievalContext) -> float:
        if not ctx.situation:
            return 0.0
        target = ctx.situation.strip().lower()
        return 1.0 if target in self._text(record).lower() else 0.0

    def _goal(self, record: Any, ctx: RetrievalContext) -> float:
        if not ctx.goal:
            return 0.0
        target = ctx.goal.strip().lower()
        if target in {e.lower() for e in self._entities(record)}:
            return 1.0
        return 0.8 if target in self._text(record).lower() else 0.0

    def _causal(self, record: Any, ctx: RetrievalContext) -> float:
        mtype = str(getattr(record, "memory_type", "")).lower()
        if mtype in ("causal_link", "temporal"):
            return 0.9
        text = self._text(record).lower()
        if "cause" in text or "because" in text or "led to" in text:
            return 0.6
        return 0.0

    def _importance(self, record: Any) -> float:
        from .importance import record_importance

        return _clamp01(record_importance(record))

    def _confidence(self, record: Any) -> float:
        return _clamp01(float(getattr(record, "confidence", 0.0) or 0.0))

    def _provenance(self, record: Any) -> float:
        from .importance import provenance_trust

        return _clamp01(provenance_trust(record))

    def _spatial(self, record: Any, ctx: RetrievalContext) -> float:
        if not ctx.location:
            return 0.0
        target = ctx.location.strip().lower()
        return 1.0 if target in self._text(record).lower() else 0.0

    def _novelty(self, record: Any, ctx: RetrievalContext) -> float:
        return 0.0 if getattr(record, "memory_id", "") in ctx.recently_retrieved else 1.0

    # ---- penalties ----

    def _contradiction(self, record: Any) -> float:
        status = str(getattr(record, "verification_status", "") or "").lower()
        if "contradict" in status or bool(getattr(record, "contradicted", False)):
            return CONTRADICTION_PENALTY
        eclass = str(getattr(record, "evidence_class", "") or "").upper()
        if eclass in _HYPOTHETICAL_STATUSES:
            return CONTRADICTION_PENALTY * 0.8
        return 0.0

    def _staleness(self, record: Any, now: datetime) -> float:
        created = self._created_at(record)
        if created is None:
            return 0.0
        age_days = max(0.0, (now - created).total_seconds()) / 86400.0
        if age_days > _STALE_AFTER_DAYS:
            return STALENESS_PENALTY
        return 0.0

    # ---- composition ----

    def score(self, record: Any, *, relevance: float, context: RetrievalContext | None = None) -> ScoredMemory:
        """Score one record. ``relevance`` is the semantic/vector similarity
        signal (0..1), supplied by the retrieval layer (rank proxy, cosine,
        FTS score) — one signal, never the decision."""
        ctx = context or RetrievalContext()
        now = ctx.now or datetime.now(timezone.utc)
        memory_id = str(getattr(record, "memory_id", ""))

        contributions = {
            "semantic": _clamp01(relevance),
            "temporal": self._temporal(record, now),
            "person": self._person(record, ctx),
            "situation": self._situation(record, ctx),
            "goal": self._goal(record, ctx),
            "causal": self._causal(record, ctx),
            "importance": self._importance(record),
            "confidence": self._confidence(record),
            "provenance": self._provenance(record),
            "spatial": self._spatial(record, ctx),
            "novelty": self._novelty(record, ctx),
        }
        penalties = {
            "contradiction": self._contradiction(record),
            "staleness": self._staleness(record, now),
        }
        weighted = sum(self.weights.get(k, 0.0) * v for k, v in contributions.items())
        total = _clamp01(weighted - sum(penalties.values()))

        why: list[str] = []
        for name, value in sorted(contributions.items(), key=lambda kv: kv[1], reverse=True):
            if value >= 0.5 and len(why) < 3:
                why.append(f"{name}={value:.2f}")
        for name, value in penalties.items():
            if value > 0:
                why.append(f"{name}_penalty={value:.2f}")
        if not why:
            why.append("no_strong_signal")

        return ScoredMemory(
            memory_id=memory_id,
            record=record,
            score=total,
            contributions=contributions,
            penalties=penalties,
            why=why,
        )

    def rank(
        self,
        records: list[Any],
        *,
        relevance_for: Callable[[int, Any], float],
        context: RetrievalContext | None = None,
        limit: int = 8,
    ) -> list[ScoredMemory]:
        """Rank records by the composite score; always bounded (Task 4.3 / §25)."""
        scored = [
            self.score(record, relevance=relevance_for(idx, record), context=context)
            for idx, record in enumerate(records)
        ]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[: max(1, limit)]
