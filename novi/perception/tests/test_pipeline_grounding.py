"""Tests: PerceptionPipeline optional grounding (plan Step 5.2/5.3/5.5).

ground_frame is an explicit, optional capability — it never runs on every
frame, never forces perception through ObjectDetector, and degrades
fail-closed when no grounding backend is attached. Associations to the
track table are conservative (candidates, never invented continuity).
"""

from __future__ import annotations

import pytest

from novi.brain.io import CameraFrame
from novi.perception.detection import DeterministicObjectDetector
from novi.perception.grounding import (
    GroundingObservation,
    SpatialInferenceMode,
    SpatialInferencePolicy,
    SpatialQuery,
)
from novi.perception.locate_anything import DeterministicLocateAnythingBackend
from novi.perception.pipeline import PerceptionPipeline, WorldObservation

W, H = 640, 480


def _frame(fid: str = "f1") -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at="t0", width=W, height=H, payload=b"")


def _detector() -> DeterministicObjectDetector:
    return DeterministicObjectDetector(
        scripted={"f1": [("cup", 0.91, (64, 96, 512, 288))]},
        confidence_floor=0.60,
    )


def _grounding() -> DeterministicLocateAnythingBackend:
    return DeterministicLocateAnythingBackend(
        scripted={
            ("f1", "the blue cup"): [("cup", (100, 200, 900, 800))],
            ("f1", "the red mug"): ["none"],
            ("f7", "the blue cup"): [("cup", (100, 200, 900, 800))],
        }
    )


def _query(text: str = "the blue cup", frame_id: str = "f1") -> SpatialQuery:
    return SpatialQuery(text=text, frame_id=frame_id, timestamp="t0")


class TestGroundFrame:
    def test_no_backend_is_fail_closed(self):
        pipeline = PerceptionPipeline(detector=_detector())
        outcome = pipeline.ground_frame(_frame(), _query(), SpatialInferencePolicy())
        assert not outcome.result.success
        assert outcome.result.backend_status == "unavailable"
        assert any("backend" in e for e in outcome.result.validation_errors)
        assert outcome.associations == []

    def test_ground_frame_associates_to_active_tracks(self):
        pipeline = PerceptionPipeline(detector=_detector(), grounding_backend=_grounding())
        pipeline.process_frame(_frame())  # seed tracker with the cup track
        outcome = pipeline.ground_frame(_frame(), _query(), SpatialInferencePolicy())
        assert outcome.result.success
        assert len(outcome.associations) == 1
        assoc = outcome.associations[0]
        assert assoc.status == "associated"
        assert assoc.track_id is not None
        assert isinstance(assoc.observation, GroundingObservation)
        assert assoc.observation.pixel_box == (64, 96, 512, 288)

    def test_ground_frame_preserves_provenance(self):
        pipeline = PerceptionPipeline(detector=_detector(), grounding_backend=_grounding())
        outcome = pipeline.ground_frame(_frame("f7"), _query("the blue cup", frame_id="f7"), SpatialInferencePolicy())
        assert outcome.frame_id == "f7"
        assert outcome.query == "the blue cup"
        assert outcome.result.frame_id == "f7"
        assert outcome.result.query == "the blue cup"
        assert outcome.result.observations[0].image_width == W
        assert outcome.result.observations[0].image_height == H

    def test_frame_query_mismatch_rejected(self):
        pipeline = PerceptionPipeline(detector=_detector(), grounding_backend=_grounding())
        with pytest.raises(ValueError, match="frame_id"):
            pipeline.ground_frame(_frame("f7"), _query(), SpatialInferencePolicy())

    def test_no_object_query_marks_absent(self):
        pipeline = PerceptionPipeline(detector=_detector(), grounding_backend=_grounding())
        outcome = pipeline.ground_frame(_frame(), _query("the red mug"), SpatialInferencePolicy())
        assert outcome.result.success
        assert outcome.result.no_object
        assert outcome.associations == []

    def test_ground_frame_does_not_disturb_tracker_state(self):
        pipeline = PerceptionPipeline(detector=_detector(), grounding_backend=_grounding())
        pipeline.process_frame(_frame())
        before = pipeline.tracker.track_count
        pipeline.ground_frame(_frame(), _query(), SpatialInferencePolicy())
        assert pipeline.tracker.track_count == before
        assert pipeline.snapshot()["frames_processed"] == 1

    def test_snapshot_reports_grounding_backend(self):
        pipeline = PerceptionPipeline(detector=_detector(), grounding_backend=_grounding())
        assert pipeline.snapshot()["grounding_backend"] == "available"
        bare = PerceptionPipeline(detector=_detector())
        assert bare.snapshot()["grounding_backend"] is None
