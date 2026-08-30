"""Unified grounding / reference resolution (plan 22, Phase 12).

Resolves deictic and definite references — this / that / it / there / here /
him / her / the blue one / the mug / the thing I showed you — against
candidate entities ranked by:

    recent mention + visual salience + gaze + pointing + spatial relation
  + grammatical role + object compatibility + conversation topic + memory

If confidence is below threshold the resolver says so: ambiguous references
trigger clarification and a physical action must never proceed on an
unresolved ambiguity (plan §16).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

RESOLVED = "RESOLVED"
AMBIGUOUS = "AMBIGUOUS"
UNRESOLVED = "UNRESOLVED"

_DEMONSTRATIVES = re.compile(r"\b(this|that|these|those|it|the)\b", re.IGNORECASE)
_PERSONAL = re.compile(r"\b(him|her|he|she)\b", re.IGNORECASE)
_LOCATIVES = re.compile(r"\b(there|here)\b", re.IGNORECASE)
_DEFINITE_NP = re.compile(r"\bthe ([a-z][a-z0-9 ]{1,24})\b", re.IGNORECASE)


@dataclass
class CandidateEntity:
    entity_id: str
    label: str
    entity_type: str = "object"  # object | person | place
    signals: dict[str, float] = field(default_factory=dict)

    @property
    def score(self) -> float:
        weights = {
            "recent_mention": 1.0,
            "visual_salience": 1.0,
            "pointing": 2.0,
            "gaze": 1.2,
            "topic": 0.8,
            "compatibility": 1.0,
            "definite": 1.5,   # "the mug" — strong linguistic evidence
            "person": 1.5,     # "him/her" — strong person evidence
            "spatial": 0.6,
            "memory": 0.7,
        }
        total = sum(weights.get(k, 0.5) * v for k, v in self.signals.items())
        return max(0.0, min(1.0, total / (1.0 + sum(weights.get(k, 0.5) for k in self.signals))))

    def snapshot(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "label": self.label,
            "entity_type": self.entity_type,
            "score": round(self.score, 3),
            "signals": {k: round(v, 3) for k, v in self.signals.items()},
        }


@dataclass
class Resolution:
    status: str  # RESOLVED | AMBIGUOUS | UNRESOLVED
    entity_id: str = ""
    label: str = ""
    confidence: float = 0.0
    candidates: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "entity_id": self.entity_id,
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "candidates": list(self.candidates),
            "reason": self.reason,
        }


class ReferenceResolver:
    """Deterministic reference resolver over world-model entities."""

    def __init__(self, *, threshold: float = 0.6, clarification_threshold: float = 0.45) -> None:
        self.threshold = threshold
        self.clarification_threshold = clarification_threshold

    # ---- candidate collection ----

    def candidates(
        self,
        text: str,
        *,
        entities: list[CandidateEntity],
        recent_mentions: dict[str, float] | None = None,
        topic: str = "",
    ) -> list[CandidateEntity]:
        """Score all entities against the reference cues in ``text``."""
        mentions = recent_mentions or {}
        low = text.lower()
        for cand in entities:
            if cand.entity_id in mentions:
                cand.signals["recent_mention"] = min(1.0, mentions[cand.entity_id])
            if topic and (topic.lower() in cand.label.lower() or cand.label.lower() in topic.lower()):
                cand.signals["topic"] = 1.0
            if _DEFINITE_NP.search(low) and cand.label.lower() in low:
                cand.signals["definite"] = 1.0
            if cand.entity_type == "person" and _PERSONAL.search(low):
                cand.signals["person"] = 1.0
            if _DEMONSTRATIVES.search(low):
                cand.signals.setdefault("compatibility", 0.6)
        return entities

    # ---- resolution ----

    def resolve(
        self,
        text: str,
        *,
        entities: list[CandidateEntity],
        recent_mentions: dict[str, float] | None = None,
        topic: str = "",
        pointing: dict[str, float] | None = None,  # entity_id -> pointing strength
        gaze: dict[str, float] | None = None,      # entity_id -> gaze strength
    ) -> Resolution:
        """Resolve a reference; never silently guess (plan §16)."""
        low = text.lower()
        pointing = pointing or {}
        gaze = gaze or {}

        has_reference = bool(
            _DEMONSTRATIVES.search(low)
            or _PERSONAL.search(low)
            or _LOCATIVES.search(low)
            or _DEFINITE_NP.search(low)
        )
        if not has_reference:
            return Resolution(UNRESOLVED, reason="no_reference_in_text")

        scored = self.candidates(
            text, entities=entities, recent_mentions=recent_mentions, topic=topic
        )
        for cand in scored:
            if cand.entity_id in pointing:
                cand.signals["pointing"] = min(1.0, pointing[cand.entity_id])
            if cand.entity_id in gaze:
                cand.signals["gaze"] = min(1.0, gaze[cand.entity_id])

        ranked = sorted(scored, key=lambda c: c.score, reverse=True)
        if not ranked:
            return Resolution(UNRESOLVED, reason="no_candidates")

        best = ranked[0]
        second = ranked[1] if len(ranked) > 1 else None
        if best.score >= self.threshold:
            if second is not None and best.score - second.score < 0.15:
                return Resolution(
                    AMBIGUOUS,
                    candidates=[c.snapshot() for c in ranked[:2]],
                    confidence=best.score,
                    reason="close_candidates",
                )
            return Resolution(
                RESOLVED,
                entity_id=best.entity_id,
                label=best.label,
                confidence=best.score,
                candidates=[c.snapshot() for c in ranked[:3]],
                reason="top_candidate",
            )
        if best.score >= self.clarification_threshold:
            return Resolution(
                AMBIGUOUS,
                candidates=[c.snapshot() for c in ranked[:3]],
                confidence=best.score,
                reason="below_threshold_needs_clarification",
            )
        # A reference with candidates but very low confidence still demands
        # clarification ("The mug onto the shelf?") — never a silent guess.
        return Resolution(
            AMBIGUOUS,
            candidates=[c.snapshot() for c in ranked[:3]],
            confidence=best.score,
            reason="low_confidence_needs_clarification",
        )

    # ---- plan §16 examples ----

    def grounding_verification(self, resolution: Resolution) -> bool:
        """A physical action may only proceed on a resolved reference."""
        return resolution.status == RESOLVED and resolution.confidence >= self.threshold
