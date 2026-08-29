"""Tests: prediction verification via grounding (plan Step 21).

If Novi predicts an object will appear, grounding verifies the expectation;
a grounding failure must report UNKNOWN (never infer absence). The verified
present-set plugs into the brain's PredictionEngine.observe(present, cycle).
"""

from __future__ import annotations

from novi.perception.grounding import GroundingObservation, GroundingResult, SpatialInferenceMode
from novi.perception.prediction_verification import verify_predicted_presence

W, H = 640, 480


def _obs(observation_id: str, label: str) -> GroundingObservation:
    return GroundingObservation(
        observation_id=observation_id,
        query="q",
        label=label,
        source_box=(100, 100, 500, 500),
        image_width=W,
        image_height=H,
        model_id="nvidia/LocateAnything-3B",
        model_revision="c32291ca",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
    )


def _result(observations=(), *, success=True, no_object=False, errors=()):
    return GroundingResult(
        query="q",
        observations=tuple(observations),
        backend_status="available",
        model_id="m",
        model_revision="r",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
        latency_ms=1.0,
        success=success,
        validation_errors=errors,
        no_object=no_object,
    )


class TestVerifyPredictedPresence:
    def test_matching_label_present(self):
        verification = verify_predicted_presence(_result([_obs("o1", "cup")]), ("cup",))
        assert verification.verdicts[0].present is True
        assert verification.verdicts[0].matched_observation_id == "o1"

    def test_missing_label_absent(self):
        verification = verify_predicted_presence(_result([_obs("o1", "cup")]), ("book",))
        assert verification.verdicts[0].present is False

    def test_fuzzy_label_match(self):
        verification = verify_predicted_presence(_result([_obs("o1", "the blue cup")]), ("cup",))
        assert verification.verdicts[0].present is True

    def test_failed_result_is_unknown_not_absent(self):
        verification = verify_predicted_presence(_result(errors=("boom",), success=False), ("cup",))
        assert verification.verdicts[0].present is None
        assert not verification.all_known

    def test_no_object_is_explicit_absence(self):
        verification = verify_predicted_presence(_result(no_object=True), ("cup",))
        assert verification.verdicts[0].present is False
        assert verification.all_known

    def test_present_set_feeds_prediction_engine(self):
        verification = verify_predicted_presence(
            _result([_obs("o1", "cup"), _obs("o2", "laptop")]), ("cup", "book", "laptop")
        )
        assert verification.as_present_set() == {"cup", "laptop"}
