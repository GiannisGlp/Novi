"""Deliberation memory record (plan Step 7.4 / 22).

When a grounding query is ambiguous, Novi records the visual decision so
later reasoning can learn from it. Schema (plan Step 7.4): query,
candidates, selected target, rejected candidates, evidence, outcome.

Pure builder over a GroundingResult; the brain's deliberation memory stores
the resulting record.
"""

from __future__ import annotations

from dataclasses import dataclass

from novi.perception.grounding import GroundingResult


@dataclass(frozen=True)
class DeliberationRecord:
    query: str
    frame_id: str
    timestamp: str
    candidates: tuple[str, ...]  # observation ids
    selected: str | None
    rejected: tuple[str, ...]
    reason: str | None
    evidence: tuple[str, ...]
    outcome: str  # "selected" | "ambiguous" | "none"

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "candidates": list(self.candidates),
            "selected": self.selected,
            "rejected": list(self.rejected),
            "reason": self.reason,
            "evidence": list(self.evidence),
            "outcome": self.outcome,
        }


def build_deliberation_record(
    result: GroundingResult,
    *,
    selected_observation_id: str | None = None,
    reason: str | None = None,
    outcome: str | None = None,
    evidence: tuple[str, ...] = (),
) -> DeliberationRecord:
    candidates = tuple(o.observation_id for o in result.observations)
    if selected_observation_id is not None and selected_observation_id not in candidates:
        raise ValueError(
            f"selected {selected_observation_id!r} is not among candidates {candidates}"
        )
    rejected = tuple(c for c in candidates if c != selected_observation_id)
    if outcome is None:
        if selected_observation_id is not None:
            outcome = "selected"
        elif len(candidates) > 1:
            outcome = "ambiguous"
        else:
            outcome = "none"
    return DeliberationRecord(
        query=result.query,
        frame_id=result.frame_id,
        timestamp=result.timestamp,
        candidates=candidates,
        selected=selected_observation_id,
        rejected=rejected,
        reason=reason,
        evidence=evidence,
        outcome=outcome,
    )
