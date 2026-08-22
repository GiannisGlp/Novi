"""Attention Candidates for the Mac Brain (PERFECTING_PLAN Step 1).

Cognition emits ranked AttentionCandidates for Autonomy to decide.
Each candidate carries scoring across salience, novelty, urgency, social,
relevance, and uncertainty dimensions.

Canonical authority: docs/03-cognition/02_WORLD_MODEL.md §Active Perception Boundary
                      docs/03-cognition/01_COGNITIVE_ARCHITECTURE.md (attention)
                      PERFECTING_PLAN/06_GAP_ANALYSIS_COGNITION.md

The flow:
  uncertain world state → attention identifies information gap →
  perception/orientation request → new evidence → world-state update

Cognition supplies candidates; Autonomy decides. The WorldModel does not
directly command actuators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .world_model import (
    INFERRED,
    UNKNOWN,
    WorldEntity,
    WorldModel,
)

# ---------------------------------------------------------------------------
# AttentionCandidate
# ---------------------------------------------------------------------------

# Scoring dimensions (docs/03-cognition + PERFECTING_PLAN/06)
SALIENCE = "salience"          # how prominent/noteworthy
NOVELTY = "novelty"             # how unexpected/new
URGENCY = "urgency"             # time-criticality
SOCIAL = "social"                # social-invitation / interaction relevance
RELEVANCE = "relevance"          # relevance to active goals
UNCERTAINTY = "uncertainty"     # epistemic gap that needs resolution

ALL_DIMENSIONS = frozenset({SALIENCE, NOVELTY, URGENCY, SOCIAL, RELEVANCE, UNCERTAINTY})


@dataclass
class AttentionCandidate:
    """A ranked attention candidate emitted by Cognition for Autonomy."""
    candidate_id: str
    target_type: str  # entity | relation | event | gap | goal
    target_id: str
    target_label: str
    scores: dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
    reason: str = ""
    suggested_action: str = ""  # observe | orient | ask | ignore | escalate
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "target_label": self.target_label,
            "scores": {k: round(v, 4) for k, v in self.scores.items()},
            "overall": round(self.overall, 4),
            "reason": self.reason,
            "suggested_action": self.suggested_action,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# AttentionRanker — produces candidates from the world model
# ---------------------------------------------------------------------------

class AttentionRanker:
    """Ranks world-state elements into AttentionCandidates for Autonomy.

    Cognition supplies candidates; Autonomy decides whether/what to act on.
    This module converts raw world-model state into scored, ranked candidates.
    """

    def __init__(
        self,
        *,
        novelty_threshold: float = 0.6,
        urgency_base: float = 0.3,
        uncertainty_boost: float = 0.4,
        social_boost: float = 0.3,
        relevance_boost: float = 0.5,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.novelty_threshold = novelty_threshold
        self.urgency_base = urgency_base
        self.uncertainty_boost = uncertainty_boost
        self.social_boost = social_boost
        self.relevance_boost = relevance_boost
        self.weights = weights or {
            SALIENCE: 0.15,
            NOVELTY: 0.20,
            URGENCY: 0.25,
            SOCIAL: 0.15,
            RELEVANCE: 0.15,
            UNCERTAINTY: 0.10,
        }

    def rank(
        self,
        world: WorldModel,
        *,
        active_goal_target: str | None = None,
        known_entities: set[str] | None = None,
        recent_event_types: set[str] | None = None,
    ) -> tuple[AttentionCandidate, ...]:
        """Produce ranked attention candidates from the current world model."""
        candidates: list[AttentionCandidate] = []
        known = known_entities or set()
        recent = recent_event_types or set()

        for entity in world.entities.values():
            if entity.lifecycle in ("archived", "superseded"):
                continue
            cand = self._candidate_for_entity(entity, active_goal_target, known, recent)
            if cand is not None:
                candidates.append(cand)

        # Sort by overall score descending.
        candidates.sort(key=lambda c: -c.overall)
        return tuple(candidates)

    def _candidate_for_entity(
        self,
        entity: WorldEntity,
        goal_target: str | None,
        known: set[str],
        recent: set[str],
    ) -> AttentionCandidate | None:
        scores: dict[str, float] = {}

        # Salience: confidence-weighted presence.
        scores[SALIENCE] = entity.confidence

        # Novelty: entity not previously known, or recently appeared.
        is_novel = entity.entity_id not in known or entity.lifecycle == "candidate"
        scores[NOVELTY] = 1.0 if is_novel else 0.2

        # Urgency: base + boost if the entity state suggests something time-critical.
        urgency = self.urgency_base
        state = entity.state_value("state") or ""
        if isinstance(state, str) and state in ("open", "moving", "alert", "emergency"):
            urgency = min(1.0, urgency + 0.4)
        scores[URGENCY] = urgency

        # Social: person entities get a social boost.
        scores[SOCIAL] = self.social_boost if entity.entity_type == "person" else 0.0

        # Relevance: matches the active goal target.
        relevance = 0.0
        if goal_target:
            if goal_target.lower() in entity.entity_id.lower():
                relevance = self.relevance_boost
            for lbl in entity.labels:
                if goal_target.lower() in lbl.lower():
                    relevance = self.relevance_boost
        scores[RELEVANCE] = relevance

        # Uncertainty: epistemic gaps that need resolution.
        uncertainty = 0.0
        if entity.epistemic_status in (UNKNOWN, INFERRED):
            uncertainty = self.uncertainty_boost
        scores[UNCERTAINTY] = uncertainty

        # Overall weighted score.
        overall = sum(scores.get(dim, 0.0) * self.weights.get(dim, 0.0) for dim in ALL_DIMENSIONS)

        # Suggested action (priority: uncertainty > social > novelty > relevance > ignore).
        if uncertainty > 0.3:
            suggested = "observe"
            reason = f"entity {entity.label()} has epistemic_status={entity.epistemic_status}"
        elif entity.entity_type == "person" and scores[SOCIAL] > 0:
            suggested = "ask"
            reason = f"person {entity.label()} present (social invitation)"
        elif is_novel:
            suggested = "orient"
            reason = f"entity {entity.label()} is novel"
        elif relevance > 0:
            suggested = "observe"
            reason = f"entity {entity.label()} relevant to active goal"
        else:
            suggested = "ignore"
            reason = f"entity {entity.label()} low overall salience"

        if overall < 0.05 and suggested == "ignore":
            return None  # skip very low-salience entities entirely

        return AttentionCandidate(
            candidate_id=f"att:{entity.entity_id}",
            target_type="entity",
            target_id=entity.entity_id,
            target_label=entity.label(),
            scores=scores,
            overall=overall,
            reason=reason,
            suggested_action=suggested,
            metadata={"epistemic_status": entity.epistemic_status, "entity_type": entity.entity_type},
        )

    def top_n(self, candidates: Iterable[AttentionCandidate], n: int = 5) -> tuple[AttentionCandidate, ...]:
        """Return the top-N candidates by overall score."""
        return tuple(sorted(candidates, key=lambda c: -c.overall)[:n])
