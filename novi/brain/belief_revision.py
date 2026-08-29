"""Belief revision policy for the Mac Brain (06_AUTONOMY doc 03 Step 8).

Evidence is classified into reliability tiers and never silently overwrites
history: revision accepts the higher-tier claim, preserves the loser as a
contradiction record, and returns an auditable decision.

Canonical rule (doc 03): *a hallucinated model statement must never outrank
direct contradictory sensor evidence.* Tier ranking implements that as
lexicographic order, not a confidence threshold.

Tiers, strongest to weakest:
  DIRECT_OBSERVATION > MULTI_SENSOR_FUSION > USER_ASSERTION
  > RELIABLE_MEMORY > MODEL_INFERENCE > PREDICTION
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

# Evidence classes (doc 03 Step 8) with reliability rank (higher = stronger).
DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
MULTI_SENSOR_FUSION = "MULTI_SENSOR_FUSION"
USER_ASSERTION = "USER_ASSERTION"
RELIABLE_MEMORY = "RELIABLE_MEMORY"
MODEL_INFERENCE = "MODEL_INFERENCE"
PREDICTION = "PREDICTION"

_EVIDENCE_RANK: dict[str, int] = {
    DIRECT_OBSERVATION: 6,
    MULTI_SENSOR_FUSION: 5,
    USER_ASSERTION: 4,
    RELIABLE_MEMORY: 3,
    MODEL_INFERENCE: 2,
    PREDICTION: 1,
}

# Map world-model provenance transformations onto evidence classes.
_TRANSFORMATION_TO_CLASS: dict[str, str] = {
    "direct": DIRECT_OBSERVATION,
    "fusion": MULTI_SENSOR_FUSION,
    "memory": RELIABLE_MEMORY,
    "inference": MODEL_INFERENCE,
    "prediction": PREDICTION,
    "simulation": MODEL_INFERENCE,
}


def classify_evidence(*, source: str, transformation: str) -> str:
    """Classify an observation into an evidence class.

    ``USER_ASSERTION`` is a caller override (e.g. a direct user statement);
    otherwise the provenance transformation decides.
    """
    if source.lower().startswith("user"):
        return USER_ASSERTION
    return _TRANSFORMATION_TO_CLASS.get(transformation, MODEL_INFERENCE)


@dataclass(frozen=True)
class BeliefClaim:
    """One side of a belief-revision decision."""
    value: Any
    evidence_class: str
    confidence: float
    cycle: int = 0
    source: str = ""


@dataclass
class RevisionDecision:
    """Auditable outcome of a belief revision (doc 03 Step 8)."""
    decision_id: str
    accepted: bool                       # True: new claim becomes the belief
    basis: str                           # tier | confidence | recency | tie | contradiction
    winner: str                          # "new" | "old"
    new_claim: BeliefClaim
    old_claim: BeliefClaim
    explanation: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "accepted": self.accepted,
            "basis": self.basis,
            "winner": self.winner,
            "new_claim": self.new_claim.__dict__,
            "old_claim": self.old_claim.__dict__,
            "explanation": self.explanation,
        }


class BeliefRevisionPolicy:
    """Deterministic belief revision: tier > confidence > recency, ties keep old."""

    def __init__(self, *, rank: dict[str, int] | None = None) -> None:
        self._rank = dict(rank) if rank else _EVIDENCE_RANK
        self._decisions: list[RevisionDecision] = []

    def revise(self, *, new: BeliefClaim, old: BeliefClaim | None) -> RevisionDecision:
        """Decide whether ``new`` replaces ``old`` (None = no prior belief).

        The world model preserves the losing claim as a contradiction record;
        this policy only chooses the current belief and explains why.
        """
        if old is None:
            return self._record(True, "first_observation", "new", new, old, "no prior belief")

        new_rank = self._rank.get(new.evidence_class, 0)
        old_rank = self._rank.get(old.evidence_class, 0)

        # Tier comparison — the model-inference-vs-direct-observation rule
        # falls out of this: 2 < 6, so the model claim loses regardless of
        # confidence.
        if new_rank > old_rank:
            return self._record(True, "tier", "new", new, old,
                                f"{new.evidence_class} outranks {old.evidence_class}")
        if new_rank < old_rank:
            return self._record(False, "tier", "old", new, old,
                                f"{old.evidence_class} outranks {new.evidence_class}")

        # Same tier: confidence decides.
        if new.confidence > old.confidence:
            return self._record(True, "confidence", "new", new, old, "same tier, higher confidence")
        if new.confidence < old.confidence:
            return self._record(False, "confidence", "old", new, old, "same tier, lower confidence")

        # Same tier and confidence: recency decides.
        if new.cycle > old.cycle:
            return self._record(True, "recency", "new", new, old, "same tier/confidence, fresher")
        if new.cycle < old.cycle:
            return self._record(False, "recency", "old", new, old, "same tier/confidence, older")

        # Perfect tie: keep the old belief (no churn).
        return self._record(False, "tie", "old", new, old, "identical claims; keep current")

    def _record(self, accepted: bool, basis: str, winner: str,
                new: BeliefClaim, old: BeliefClaim | None, explanation: str) -> RevisionDecision:
        decision = RevisionDecision(
            decision_id=f"rev-{uuid4().hex[:12]}",
            accepted=accepted, basis=basis, winner=winner,
            new_claim=new,
            old_claim=old if old is not None else BeliefClaim(None, "NONE", 0.0),
            explanation=explanation,
        )
        self._decisions.append(decision)
        return decision

    def decisions(self) -> tuple[RevisionDecision, ...]:
        return tuple(self._decisions)
