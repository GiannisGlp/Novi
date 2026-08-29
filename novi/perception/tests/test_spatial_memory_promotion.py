"""Tests: selective durable-memory promotion criteria (plan Step 7.3 / 24).

Only stable/salient spatial observations should be promoted to durable
memory. This is the perception-side selectivity criterion: repeated,
track-stable observations with bounded center drift qualify; single
sightings and drifting observations do not. (The durable store itself —
novi/integration/observation_recorder.py — is memory's; this module decides
WHAT deserves promotion.)
"""

from __future__ import annotations

from dataclasses import dataclass

from novi.perception.grounding import GroundingObservation, SpatialInferenceMode
from novi.perception.spatial_memory_promotion import PromotionDecision, promotion_candidate

W, H = 640, 480


@dataclass(frozen=True)
class _Sighting:
    box: tuple[int, int, int, int]  # normalized (x1, y1, x2, y2)
    track_id: int | None = None
    label: str = "cup"


def _obs(sighting: _Sighting, i: int) -> GroundingObservation:
    x1, y1, x2, y2 = sighting.box
    return GroundingObservation(
        observation_id=f"s{i}",
        query="the cup",
        label=sighting.label,
        source_box=(x1, y1, x2, y2),
        image_width=W,
        image_height=H,
        model_id="m",
        model_revision="r",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id=f"f{i}",
        timestamp=f"t{i}",
    )


def _history(sightings) -> list[tuple[GroundingObservation, int | None]]:
    return [(_obs(s, i), s.track_id) for i, s in enumerate(sightings)]


class TestPromotionCriterion:
    def test_stable_repeated_observations_promote(self):
        sightings = [
            _Sighting((400, 400, 500, 500), track_id=3),
            _Sighting((402, 401, 499, 500), track_id=3),
            _Sighting((401, 400, 500, 501), track_id=3),
        ]
        decision = promotion_candidate(_history(sightings))
        assert decision.promote
        assert decision.stability_score > 0.9

    def test_single_sighting_does_not_promote(self):
        decision = promotion_candidate(_history([_Sighting((400, 400, 500, 500), track_id=3)]))
        assert not decision.promote
        assert "observations" in decision.reason

    def test_large_center_drift_does_not_promote(self):
        sightings = [
            _Sighting((100, 100, 200, 200), track_id=3),
            _Sighting((800, 800, 900, 900), track_id=3),
            _Sighting((100, 100, 200, 200), track_id=3),
        ]
        decision = promotion_candidate(_history(sightings))
        assert not decision.promote
        assert "drift" in decision.reason

    def test_track_change_does_not_promote(self):
        sightings = [
            _Sighting((400, 400, 500, 500), track_id=3),
            _Sighting((401, 400, 500, 500), track_id=4),  # different track
            _Sighting((402, 401, 500, 500), track_id=4),
        ]
        decision = promotion_candidate(_history(sightings))
        assert not decision.promote
        assert "track" in decision.reason

    def test_unassociated_sightings_do_not_promote(self):
        sightings = [
            _Sighting((400, 400, 500, 500), track_id=None),
            _Sighting((401, 400, 500, 500), track_id=None),
            _Sighting((402, 401, 500, 500), track_id=None),
        ]
        decision = promotion_candidate(_history(sightings))
        assert not decision.promote

    def test_reason_and_score_present(self):
        decision = promotion_candidate([])
        assert isinstance(decision, PromotionDecision)
        assert decision.reason
