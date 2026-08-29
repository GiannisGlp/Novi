"""Selective durable-memory promotion criterion (plan Step 7.3 / 24).

Only stable/salient spatial observations deserve promotion to durable
memory ("blue cup near desk" after repeated observations — not after a
single glimpse). This module is the perception-side selectivity decision:

- repeated sightings (>= min_observations),
- all associated to the SAME track (temporal continuity),
- bounded center drift in normalized [0,1000] space.

Candidates (never-associated observations) do not promote — they lack
continuity. The durable store itself is memory's
(novi/integration/observation_recorder.py); this decides WHAT qualifies.
Pure stdlib, deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

from novi.perception.grounding import GroundingObservation

Sighting = tuple[GroundingObservation, int | None]  # (observation, track_id)


@dataclass(frozen=True)
class PromotionDecision:
    promote: bool
    reason: str
    stability_score: float


def _center(box: tuple[int, int, int, int]) -> tuple[float, float]:
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def promotion_candidate(
    history: list[Sighting],
    *,
    min_observations: int = 2,
    max_center_drift_norm: float = 60.0,
) -> PromotionDecision:
    """Decide whether a spatial observation history deserves durable memory."""
    if len(history) < min_observations:
        return PromotionDecision(
            promote=False,
            reason=f"only {len(history)} observations (need >= {min_observations})",
            stability_score=0.0,
        )
    track_ids = {track_id for _, track_id in history}
    if None in track_ids:
        return PromotionDecision(
            promote=False,
            reason="sightings never associated to a track (candidates lack continuity)",
            stability_score=0.0,
        )
    if len(track_ids) > 1:
        return PromotionDecision(
            promote=False,
            reason=f"track changed across sightings ({sorted(t for t in track_ids if t is not None)})",
            stability_score=0.0,
        )
    centers = [_center(obs.source_box) for obs, _ in history]
    max_drift = max(_dist(a, b) for a in centers for b in centers)
    if max_drift > max_center_drift_norm:
        return PromotionDecision(
            promote=False,
            reason=f"center drift {max_drift:.0f} exceeds {max_center_drift_norm:.0f}",
            stability_score=round(max(0.0, 1.0 - max_drift / 1000.0), 4),
        )
    return PromotionDecision(
        promote=True,
        reason=f"stable across {len(history)} sightings (drift {max_drift:.0f})",
        stability_score=round(1.0 - max_drift / 1000.0, 4),
    )
