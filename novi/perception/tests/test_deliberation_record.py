"""Tests: deliberation memory record (plan Step 7.4 / 22).

When a grounding query is ambiguous, Novi records the decision: query,
candidates, selected target, rejected candidates, evidence, outcome — the
exact schema from plan Step 7.4.
"""

from __future__ import annotations

import pytest

from novi.perception.deliberation_record import DeliberationRecord, build_deliberation_record
from novi.perception.grounding import GroundingObservation, GroundingResult, SpatialInferenceMode

W, H = 640, 480


def _obs(observation_id: str, label: str) -> GroundingObservation:
    return GroundingObservation(
        observation_id=observation_id,
        query="find the cup",
        label=label,
        source_box=(100, 100, 300, 300),
        image_width=W,
        image_height=H,
        model_id="m",
        model_revision="r",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
    )


def _result(observations) -> GroundingResult:
    return GroundingResult(
        query="find the cup",
        observations=tuple(observations),
        backend_status="available",
        model_id="m",
        model_revision="r",
        backend_version="0.1.0",
        inference_mode=SpatialInferenceMode.HYBRID,
        frame_id="f1",
        timestamp="t0",
        latency_ms=1.0,
        success=True,
    )


class TestDeliberationRecord:
    def test_selection_records_rejected_candidates(self):
        result = _result([_obs("c1", "cup"), _obs("c2", "cup")])
        record = build_deliberation_record(result, selected_observation_id="c1", reason="closer to desk")
        assert record.candidates == ("c1", "c2")
        assert record.selected == "c1"
        assert record.rejected == ("c2",)
        assert record.reason == "closer to desk"
        assert record.outcome == "selected"

    def test_no_selection_with_multiple_candidates_is_ambiguous(self):
        result = _result([_obs("c1", "cup"), _obs("c2", "cup")])
        record = build_deliberation_record(result)
        assert record.outcome == "ambiguous"
        assert record.selected is None

    def test_single_candidate_without_selection_is_none(self):
        result = _result([_obs("c1", "cup")])
        record = build_deliberation_record(result)
        assert record.outcome == "none"

    def test_selection_must_be_a_candidate(self):
        result = _result([_obs("c1", "cup")])
        with pytest.raises(ValueError, match="candidate"):
            build_deliberation_record(result, selected_observation_id="ghost")

    def test_query_and_frame_provenance(self):
        record = build_deliberation_record(_result([_obs("c1", "cup")]))
        assert record.query == "find the cup"
        assert record.frame_id == "f1"

    def test_to_dict_shape(self):
        record = build_deliberation_record(
            _result([_obs("c1", "cup"), _obs("c2", "cup")]),
            selected_observation_id="c1",
            reason="closest to requested person",
            evidence=("c1 overlaps track-3",),
        )
        d = record.to_dict()
        assert d["query"] == "find the cup"
        assert d["selected"] == "c1"
        assert d["rejected"] == ["c2"]
        assert d["evidence"] == ["c1 overlaps track-3"]
