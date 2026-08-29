"""Tests: grounding re-observation verification (plan Step 9.2).

High-risk actions require re-observation + verification. Governance owns
permission; this module owns the deterministic GEOMETRY of verification:
does a second grounding pass on the same query agree with the first?
Fail-closed: no result, failed result, or empty result is never "verified".
"""

from __future__ import annotations

import pytest

from novi.perception.grounding import GroundingObservation, GroundingResult, SpatialInferenceMode
from novi.perception.grounding_verification import VerificationOutcome, verify_grounding_agreement

W, H = 640, 480


def _box(frame_id: str = "f1", box=(100, 100, 400, 300), label: str = "cup", query: str = "the cup") -> GroundingObservation:
    return GroundingObservation(
        observation_id=f"o-{frame_id}",
        query=query,
        label=label,
        source_box=(int(box[0] * 1000 / W), int(box[1] * 1000 / H), int((box[0] + box[2]) * 1000 / W), int((box[1] + box[3]) * 1000 / H)),
        image_width=W,
        image_height=H,
        model_id="deterministic",
        model_revision="local",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id=frame_id,
        timestamp="t0",
    )


def _result(observations, frame_id: str = "f1", query: str = "the cup", success: bool = True) -> GroundingResult:
    return GroundingResult(
        query=query,
        observations=tuple(observations),
        backend_status="available",
        model_id="deterministic",
        model_revision="local",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id=frame_id,
        timestamp="t0",
        latency_ms=1.0,
        success=success,
    )


class TestVerification:
    def test_agreeing_boxes_verify(self):
        first = _result([_box(box=(100, 100, 400, 300))])
        second = _result([_box(box=(105, 102, 398, 299))])
        outcome = verify_grounding_agreement(first, second)
        assert outcome.verified
        assert outcome.best_iou > 0.5

    def test_disjoint_boxes_do_not_verify(self):
        first = _result([_box(box=(100, 100, 400, 300))])
        second = _result([_box(box=(10, 10, 60, 60))])
        outcome = verify_grounding_agreement(first, second)
        assert not outcome.verified

    def test_empty_second_pass_is_fail_closed(self):
        first = _result([_box()])
        second = _result([])
        outcome = verify_grounding_agreement(first, second)
        assert not outcome.verified

    def test_failed_first_pass_is_fail_closed(self):
        first = _result([], success=False)
        second = _result([_box()])
        outcome = verify_grounding_agreement(first, second)
        assert not outcome.verified

    def test_best_pair_wins_across_multiple_boxes(self):
        first = _result([_box(label="a", box=(0, 0, 40, 40)), _box(label="b", box=(100, 100, 400, 300))])
        second = _result([_box(label="b", box=(105, 102, 398, 299))])
        outcome = verify_grounding_agreement(first, second)
        assert outcome.verified
        assert outcome.best_iou > 0.5

    def test_query_mismatch_rejected(self):
        first = _result([_box()], query="the cup")
        second = _result([_box()], query="the mug")
        with pytest.raises(ValueError, match="query"):
            verify_grounding_agreement(first, second)

    def test_frame_mismatch_rejected(self):
        first = _result([_box()], frame_id="f1")
        second = _result([_box()], frame_id="f2")
        with pytest.raises(ValueError, match="frame"):
            verify_grounding_agreement(first, second)

    def test_outcome_carries_counts(self):
        first = _result([_box()])
        second = _result([_box()])
        outcome = verify_grounding_agreement(first, second)
        assert isinstance(outcome, VerificationOutcome)
        assert outcome.first_count == 1 and outcome.second_count == 1
