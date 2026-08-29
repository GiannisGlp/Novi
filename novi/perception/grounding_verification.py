"""Grounding re-observation verification (plan Step 9.2 — geometry part).

Governance owns whether an action is permitted; this module owns the
deterministic GEOMETRY of verification: does a second grounding pass on the
same query and frame agree with the first?

Fail-closed rules:
- results must share the same query text and frame id (provenance integrity);
- a failed or empty result on either side is NEVER verified;
- verification is greedy best-pair IoU >= threshold on box observations;
  points are ignored for geometric agreement (no area).

Pure stdlib, deterministic, safe in CI.
"""

from __future__ import annotations

from dataclasses import dataclass

from novi.perception.grounding import GroundingObservation, GroundingResult
from novi.perception.tracking import _iou


@dataclass(frozen=True)
class VerificationOutcome:
    verified: bool
    best_iou: float
    first_count: int
    second_count: int


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def verify_grounding_agreement(
    first: GroundingResult,
    second: GroundingResult,
    *,
    iou_threshold: float = 0.5,
) -> VerificationOutcome:
    """Verify a re-observation agrees with the original grounding pass."""
    if _norm(first.query) != _norm(second.query):
        raise ValueError(
            f"verification requires the same query: {first.query!r} vs {second.query!r}"
        )
    if first.frame_id != second.frame_id:
        raise ValueError(
            f"verification requires the same frame: {first.frame_id!r} vs {second.frame_id!r}"
        )

    first_boxes = [o.pixel_box for o in first.observations if isinstance(o, GroundingObservation)]
    second_boxes = [o.pixel_box for o in second.observations if isinstance(o, GroundingObservation)]

    if not first.success or not second.success or not first_boxes or not second_boxes:
        return VerificationOutcome(verified=False, best_iou=0.0, first_count=len(first_boxes), second_count=len(second_boxes))

    best_iou = 0.0
    for a in first_boxes:
        for b in second_boxes:
            best_iou = max(best_iou, _iou(a, b))
    return VerificationOutcome(
        verified=best_iou >= iou_threshold,
        best_iou=round(best_iou, 4),
        first_count=len(first_boxes),
        second_count=len(second_boxes),
    )
