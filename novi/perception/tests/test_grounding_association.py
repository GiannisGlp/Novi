"""Tests: grounding -> tracking association (plan Step 5.4).

Grounding observations are per-frame geometry; ObjectTracker owns temporal
continuity. Association is conservative: boxes associate by IoU, points by
centroid distance — and when association is uncertain the observation stays a
"candidate" instead of inventing continuity.
"""

from __future__ import annotations

from dataclasses import replace

from novi.perception.grounding import (
    GroundingObservation,
    GroundingResult,
    PointObservation,
    SpatialInferenceMode,
)
from novi.perception.grounding_association import (
    GroundingAssociation,
    GroundingOutcome,
    associate_grounding_to_tracks,
)
from novi.perception.tracking import Track

W, H = 640, 480


def _box_obs(observation_id: str = "la-f1-0", label: str = "cup", box=(100, 100, 200, 200)) -> GroundingObservation:
    return GroundingObservation(
        observation_id=observation_id,
        query="the blue cup",
        label=label,
        source_box=(int(box[0] * 1000 / W), int(box[1] * 1000 / H), int((box[0] + box[2]) * 1000 / W), int((box[1] + box[3]) * 1000 / H)),
        image_width=W,
        image_height=H,
        model_id="deterministic",
        model_revision="local",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
    )


def _point_obs(label: str = "handle", xy=(320, 240)) -> PointObservation:
    return PointObservation(
        observation_id="la-f1-p0",
        query="the cup handle",
        label=label,
        source_point=(int(xy[0] * 1000 / W), int(xy[1] * 1000 / H)),
        image_width=W,
        image_height=H,
        model_id="deterministic",
        model_revision="local",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
    )


def _track(tid: int, label: str, bbox) -> Track:
    return Track(
        track_id=tid,
        label=label,
        bbox=bbox,
        first_frame_id="f0",
        last_frame_id="f1",
        hits=3,
        confirmed=True,
    )


def _result(observations) -> GroundingResult:
    return GroundingResult(
        query="the blue cup",
        observations=tuple(observations),
        backend_status="available",
        model_id="deterministic",
        model_revision="local",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
        latency_ms=1.0,
        success=True,
    )


class TestBoxAssociation:
    def test_overlapping_box_associates_to_track(self):
        track = _track(7, "cup", (90, 90, 220, 220))  # heavy overlap with obs box
        outcome = associate_grounding_to_tracks(
            _result([_box_obs()]), [track], frame_id="f1", query="the blue cup"
        )
        assert len(outcome.associations) == 1
        assoc = outcome.associations[0]
        assert assoc.track_id == 7
        assert assoc.status == "associated"
        assert assoc.iou is not None and assoc.iou > 0.5

    def test_disjoint_box_stays_candidate(self):
        track = _track(7, "cup", (500, 400, 80, 60))
        outcome = associate_grounding_to_tracks(
            _result([_box_obs()]), [track], frame_id="f1", query="q"
        )
        assert outcome.associations[0].track_id is None
        assert outcome.associations[0].status == "candidate"

    def test_below_threshold_iou_stays_candidate(self):
        track = _track(7, "cup", (300, 300, 60, 60))  # small corner overlap
        outcome = associate_grounding_to_tracks(
            _result([_box_obs()]), [track], frame_id="f1", query="q", iou_threshold=0.5
        )
        assert outcome.associations[0].status == "candidate"

    def test_best_iou_track_wins(self):
        near = _track(1, "cup", (95, 95, 210, 210))
        far = _track(2, "cup", (150, 150, 160, 160))
        outcome = associate_grounding_to_tracks(
            _result([_box_obs()]), [near, far], frame_id="f1", query="q"
        )
        assert outcome.associations[0].track_id == 1


class TestPointAssociation:
    def test_point_near_centroid_associates(self):
        track = _track(3, "cup", (250, 170, 140, 140))  # centroid (320, 240)
        outcome = associate_grounding_to_tracks(
            _result([_point_obs()]), [track], frame_id="f1", query="q"
        )
        assert outcome.associations[0].track_id == 3
        assert outcome.associations[0].status == "associated"

    def test_point_far_from_centroid_stays_candidate(self):
        track = _track(3, "cup", (10, 10, 40, 40))
        outcome = associate_grounding_to_tracks(
            _result([_point_obs()]), [track], frame_id="f1", query="q"
        )
        assert outcome.associations[0].track_id is None
        assert outcome.associations[0].status == "candidate"


class TestGroundingOutcome:
    def test_outcome_carries_provenance(self):
        result = _result([_box_obs()])
        outcome = associate_grounding_to_tracks(result, [], frame_id="f1", query="the blue cup")
        assert outcome.frame_id == "f1"
        assert outcome.query == "the blue cup"
        assert outcome.result is result

    def test_mixed_associations_preserved_in_order(self):
        cup_track = _track(1, "cup", (90, 90, 220, 220))
        result = _result([_box_obs("a", "cup", (100, 100, 200, 200)), _point_obs("handle", (10, 10))])
        outcome = associate_grounding_to_tracks(result, [cup_track], frame_id="f1", query="q")
        assert [a.status for a in outcome.associations] == ["associated", "candidate"]
        assert [a.track_id for a in outcome.associations] == [1, None]

    def test_empty_result_yields_empty_outcome(self):
        outcome = associate_grounding_to_tracks(_result([]), [], frame_id="f1", query="q")
        assert outcome.associations == []
