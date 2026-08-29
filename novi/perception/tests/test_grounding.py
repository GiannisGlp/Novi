"""Tests: typed Novi spatial-grounding contracts (plan Step 1.1 / Phase 1).

Covers SpatialQuery, SpatialInferencePolicy, GroundingObservation,
PointObservation, GroundingResult, SpatialBackendCapabilities and the
SpatialPerceptionBackend protocol — the canonical typed surface that hides
NVIDIA special tokens from the rest of Novi.
"""

from __future__ import annotations

import pytest

from novi.brain.io import CameraFrame
from novi.perception.grounding import (
    BackendState,
    GroundingObservation,
    GroundingResult,
    PointObservation,
    SpatialBackendCapabilities,
    SpatialInferenceMode,
    SpatialInferencePolicy,
    SpatialPerceptionBackend,
    SpatialQuery,
    sha256_hex,
)

W, H = 640, 480


def _query(**kw) -> SpatialQuery:
    base = dict(text="the blue cup", frame_id="f1", timestamp="t0")
    base.update(kw)
    return SpatialQuery(**base)


def _frame(fid: str = "f1") -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at="t0", width=W, height=H, payload=b"")


class TestSpatialQuery:
    def test_minimal_query_uses_hybrid_default(self):
        q = _query()
        assert q.text == "the blue cup"
        assert q.preferred_mode is SpatialInferenceMode.HYBRID
        assert q.requested_output == "both"
        assert q.max_results == 5

    def test_empty_text_rejected(self):
        with pytest.raises(ValueError, match="text"):
            _query(text="   ")

    def test_empty_frame_id_rejected(self):
        with pytest.raises(ValueError, match="frame"):
            _query(frame_id="")

    def test_bad_requested_output_rejected(self):
        with pytest.raises(ValueError, match="requested_output"):
            _query(requested_output="polygon")

    def test_max_results_must_be_positive(self):
        with pytest.raises(ValueError, match="max_results"):
            _query(max_results=0)

    def test_preferred_mode_must_be_enum(self):
        with pytest.raises(ValueError, match="preferred_mode"):
            _query(preferred_mode="hybrid")


class TestSpatialInferencePolicy:
    def test_defaults(self):
        p = SpatialInferencePolicy()
        assert p.mode is SpatialInferenceMode.HYBRID
        assert p.max_results == 5
        assert p.risk_class == "routine"

    def test_negative_latency_budget_rejected(self):
        with pytest.raises(ValueError, match="latency"):
            SpatialInferencePolicy(latency_budget_ms=-1)

    def test_zero_max_results_rejected(self):
        with pytest.raises(ValueError, match="max_results"):
            SpatialInferencePolicy(max_results=0)


class TestGroundingObservation:
    def _obs(self, **kw) -> GroundingObservation:
        base = dict(
            observation_id="obs-1",
            query="the blue cup",
            label="cup",
            source_box=(100, 200, 900, 800),
            image_width=W,
            image_height=H,
            model_id="nvidia/LocateAnything-3B",
            model_revision="c32291ca",
            backend_version="0.1.0",
            inference_mode=SpatialInferenceMode.HYBRID,
            frame_id="f1",
            timestamp="t0",
        )
        base.update(kw)
        return GroundingObservation(**base)

    def test_pixel_box_derived_from_source(self):
        obs = self._obs()
        assert obs.pixel_box == (64, 96, 512, 288)
        assert obs.source_box == (100, 200, 900, 800)  # source preserved

    def test_inverted_source_box_rejected(self):
        with pytest.raises(ValueError, match="x1"):
            self._obs(source_box=(900, 200, 100, 800))

    def test_out_of_range_source_box_rejected(self):
        with pytest.raises(ValueError, match="1000"):
            self._obs(source_box=(0, 0, 1001, 800))

    def test_frame_id_required(self):
        with pytest.raises(ValueError, match="frame_id"):
            self._obs(frame_id="")

    def test_model_revision_required(self):
        with pytest.raises(ValueError, match="revision"):
            self._obs(model_revision="")

    def test_optional_point_derives_pixel_point(self):
        obs = self._obs(source_point=(500, 500))
        assert obs.pixel_point == (320, 240)

    def test_confidence_bounds(self):
        with pytest.raises(ValueError, match="confidence"):
            self._obs(confidence=1.5)
        with pytest.raises(ValueError, match="confidence"):
            self._obs(confidence=-0.1)


class TestPointObservation:
    def _point(self, **kw) -> PointObservation:
        base = dict(
            observation_id="p-1",
            query="the cup handle",
            label="cup handle",
            source_point=(500, 500),
            image_width=W,
            image_height=H,
            model_id="nvidia/LocateAnything-3B",
            model_revision="c32291ca",
            backend_version="0.1.0",
            inference_mode=SpatialInferenceMode.HYBRID,
            frame_id="f1",
            timestamp="t0",
        )
        base.update(kw)
        return PointObservation(**base)

    def test_pixel_point_derived(self):
        assert self._point().pixel_point == (320, 240)

    def test_label_required(self):
        with pytest.raises(ValueError, match="label"):
            self._point(label="")

    def test_out_of_range_point_rejected(self):
        with pytest.raises(ValueError, match="1000"):
            self._point(source_point=(1001, 500))


class TestGroundingResult:
    def _result(self, **kw) -> GroundingResult:
        base = dict(
            query="the blue cup",
            observations=(),
            backend_status="available",
            model_id="nvidia/LocateAnything-3B",
            model_revision="c32291ca",
            backend_version="0.1.0",
            inference_mode=SpatialInferenceMode.HYBRID,
            frame_id="f1",
            timestamp="t0",
            latency_ms=12.5,
            success=True,
        )
        base.update(kw)
        return GroundingResult(**base)

    def test_success_with_validation_errors_rejected(self):
        with pytest.raises(ValueError, match="validation_errors"):
            self._result(validation_errors=("malformed token",))

    def test_fail_closed_empty_result_is_valid(self):
        r = self._result(success=False, backend_status="unavailable")
        assert r.observations == ()
        assert r.success is False

    def test_raw_hash_requires_sha256_hex(self):
        with pytest.raises(ValueError, match="raw_hash"):
            self._result(raw_hash="not-a-hash")
        ok = sha256_hex("<ref>cup</ref><box>1</box>")
        assert self._result(raw_hash=ok).raw_hash == ok

    def test_query_required(self):
        with pytest.raises(ValueError, match="query"):
            self._result(query="")

    def test_no_object_conflicts_with_observations(self):
        with pytest.raises(ValueError, match="no_object"):
            obs = self._obs()
            self._result(observations=(obs,), no_object=True)

    def _obs(self):
        return GroundingObservation(
            observation_id="obs-1",
            query="the blue cup",
            label="cup",
            source_box=(100, 200, 900, 800),
            image_width=640,
            image_height=480,
            model_id="nvidia/LocateAnything-3B",
            model_revision="c32291ca",
            backend_version="0.1.0",
            inference_mode=SpatialInferenceMode.HYBRID,
            frame_id="f1",
            timestamp="t0",
        )

    def test_no_object_empty_result_is_valid(self):
        r = self._result(no_object=True)
        assert r.no_object and r.observations == ()


class TestBackendState:
    def test_states_match_plan_enumeration(self):
        expected = {
            "available", "loading", "unavailable", "unsupported",
            "dependency_missing", "model_missing", "failed",
        }
        assert {s.value for s in BackendState} == expected


class TestSpatialBackendCapabilities:
    def test_usable_only_when_available(self):
        assert SpatialBackendCapabilities(state=BackendState.AVAILABLE).usable
        assert not SpatialBackendCapabilities(state=BackendState.MODEL_MISSING).usable
        assert not SpatialBackendCapabilities(state=BackendState.FAILED).usable

    def test_mode_supported(self):
        caps = SpatialBackendCapabilities(state=BackendState.AVAILABLE)
        assert caps.mode_supported(SpatialInferenceMode.HYBRID)
        assert not caps.mode_supported(SpatialInferenceMode.SLOW)


class TestSpatialPerceptionBackendProtocol:
    def test_runtime_checkable_against_stub(self):
        class _Stub:
            def capabilities(self):
                return SpatialBackendCapabilities(state=BackendState.UNAVAILABLE)

            def ground(self, image, query, policy):
                raise NotImplementedError

            def point(self, image, query, policy):
                raise NotImplementedError

            def detect(self, image, labels, policy):
                raise NotImplementedError

        assert isinstance(_Stub(), SpatialPerceptionBackend)
        assert not isinstance(object(), SpatialPerceptionBackend)
