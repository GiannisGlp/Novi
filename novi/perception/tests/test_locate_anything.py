"""Tests: LocateAnything backends (plan Step 3.1/3.4/3.5, §19 step 5).

- DeterministicLocateAnythingBackend: scripted grounding results keyed by
  (frame_id, query) — the CI backend that needs no model, no torch, no GPU;
- LocateAnythingBackend: the thin Novi adapter. Model specifics stay behind
  the runtime boundary, so the adapter is tested here against an injected
  fake runtime returning scripted raw text (including malformed output).
"""

from __future__ import annotations

import pytest

from novi.brain.io import CameraFrame
from novi.perception.grounding import (
    BackendState,
    GroundingObservation,
    PointObservation,
    SpatialInferenceMode,
    SpatialInferencePolicy,
    SpatialQuery,
    sha256_hex,
)
from novi.perception.locate_anything import (
    DeterministicLocateAnythingBackend,
    LocateAnythingBackend,
)

W, H = 640, 480


def _frame(fid: str = "f1") -> CameraFrame:
    return CameraFrame(frame_id=fid, captured_at="t0", width=W, height=H, payload=b"")


def _query(text: str = "the blue cup", requested_output: str = "both") -> SpatialQuery:
    return SpatialQuery(text=text, frame_id="f1", timestamp="t0", requested_output=requested_output)


def _policy(mode: SpatialInferenceMode = SpatialInferenceMode.HYBRID, **kw) -> SpatialInferencePolicy:
    return SpatialInferencePolicy(mode=mode, **kw)


class TestDeterministicBackend:
    def _backend(self) -> DeterministicLocateAnythingBackend:
        return DeterministicLocateAnythingBackend(
            scripted={
                ("f1", "the blue cup"): [
                    ("cup", (100, 200, 900, 800)),
                    ("handle", (500, 500)),
                ],
                ("f1", "the red mug"): ["none"],
            }
        )

    def test_capabilities_available_with_deterministic_provenance(self):
        caps = self._backend().capabilities()
        assert caps.usable
        assert caps.state is BackendState.AVAILABLE
        assert caps.model_id == "deterministic"
        assert caps.model_revision == "local"

    def test_scripted_boxes_and_points(self):
        result = self._backend().ground(_frame(), _query(), _policy())
        assert result.success
        assert result.no_object is False
        assert len(result.observations) == 2
        box = result.observations[0]
        assert isinstance(box, GroundingObservation)
        assert box.label == "cup"
        assert box.pixel_box == (64, 96, 512, 288)
        assert box.frame_id == "f1"
        point = result.observations[1]
        assert isinstance(point, PointObservation)
        assert point.pixel_point == (320, 240)

    def test_requested_output_point_filters_boxes(self):
        result = self._backend().ground(_frame(), _query(requested_output="point"), _policy())
        assert result.success
        assert all(isinstance(o, PointObservation) for o in result.observations)
        assert len(result.observations) == 1

    def test_requested_output_box_filters_points(self):
        result = self._backend().ground(_frame(), _query(requested_output="box"), _policy())
        assert result.success
        assert all(isinstance(o, GroundingObservation) for o in result.observations)

    def test_scripted_none_marks_no_object(self):
        result = self._backend().ground(_frame(), _query("the red mug"), _policy())
        assert result.success
        assert result.no_object
        assert result.observations == ()

    def test_unscripted_query_is_valid_empty(self):
        result = self._backend().ground(_frame(), _query("something unseen"), _policy())
        assert result.success
        assert result.observations == ()
        assert not result.no_object

    def test_detect_delegates_by_labels(self):
        backend = DeterministicLocateAnythingBackend(
            scripted={("f1", "cup, book"): [("cup", (0, 0, 100, 100))]}
        )
        result = backend.detect(_frame(), ("cup", "book"), _policy())
        assert result.success
        assert [o.label for o in result.observations] == ["cup"]

    def test_point_method_forces_point_output(self):
        result = self._backend().point(_frame(), _query(), _policy())
        assert result.success
        assert all(isinstance(o, PointObservation) for o in result.observations)


class _FakeRuntime:
    """Scripted raw-text runtime; raises when asked for a failing query."""

    def __init__(self, raw_by_query: dict[str, str | BaseException], latency_ms: float = 3.5):
        self._raw = raw_by_query
        self._latency = latency_ms
        self.calls: list[tuple[str, SpatialInferenceMode]] = []

    def infer(self, image, prompt: str, mode: SpatialInferenceMode) -> tuple[str, float]:
        self.calls.append((prompt, mode))
        item = self._raw.get(prompt)
        if item is None:
            return "", self._latency
        if isinstance(item, BaseException):
            raise item
        return item, self._latency


class TestLocateAnythingAdapter:
    def _backend(self, raw: dict[str, str | BaseException]) -> tuple[LocateAnythingBackend, _FakeRuntime]:
        runtime = _FakeRuntime(raw)
        backend = LocateAnythingBackend(runtime=runtime)
        return backend, runtime

    def test_capabilities_reflect_runtime(self):
        backend, _ = self._backend({"q": "<ref>cup</ref><box>100 200 900 800</box>"})
        caps = backend.capabilities()
        assert caps.usable
        assert caps.model_id == "nvidia/LocateAnything-3B"
        assert caps.model_revision == "c32291ca5e996f5a7a485845b4f57a233936bba0"

    def test_box_output_becomes_typed_observation_with_provenance(self):
        raw = "<ref>cup</ref><box>100 200 900 800</box>"
        backend, runtime = self._backend({"the blue cup": raw})
        result = backend.ground(_frame(), _query(), _policy())
        assert result.success
        assert result.latency_ms == 3.5
        assert result.raw_hash == sha256_hex(raw)
        assert result.backend_status == "available"
        obs = result.observations[0]
        assert obs.pixel_box == (64, 96, 512, 288)
        assert obs.model_id == "nvidia/LocateAnything-3B"
        assert obs.model_revision == "c32291ca5e996f5a7a485845b4f57a233936bba0"
        assert obs.inference_mode is SpatialInferenceMode.HYBRID
        assert obs.provenance == "locate_anything"

    def test_policy_mode_propagates_to_runtime_and_observations(self):
        backend, runtime = self._backend({"q": "<ref>cup</ref><box>0 0 10 10</box>"})
        backend.ground(_frame(), _query("q"), _policy(SpatialInferenceMode.SLOW))
        assert runtime.calls[0][1] is SpatialInferenceMode.SLOW

    def test_malformed_output_is_fail_closed(self):
        backend, _ = self._backend({"q": "<ref>cup</ref><box>900 200 100 800</box>"})
        result = backend.ground(_frame(), _query("q"), _policy())
        assert not result.success
        assert result.validation_errors
        assert result.observations == ()

    def test_none_output_marks_no_object(self):
        backend, _ = self._backend({"q": "<box>none</box>"})
        result = backend.ground(_frame(), _query("q"), _policy())
        assert result.success
        assert result.no_object
        assert result.observations == ()

    def test_runtime_exception_is_fail_closed(self):
        backend, _ = self._backend({"q": RuntimeError("gpu exploded")})
        result = backend.ground(_frame(), _query("q"), _policy())
        assert not result.success
        assert any("gpu exploded" in e for e in result.validation_errors)

    def test_point_query_returns_point_observations(self):
        raw = "<ref>handle</ref><box>500 500</box>"
        backend, _ = self._backend({"the handle": raw})
        result = backend.ground(_frame(), _query("the handle", requested_output="point"), _policy())
        assert result.success
        assert len(result.observations) == 1
        assert isinstance(result.observations[0], PointObservation)

    def test_excessive_results_truncated_and_fail_closed(self):
        raw = (
            "<ref>a</ref><box>0 0 1 1</box>"
            "<ref>b</ref><box>0 0 1 1</box>"
            "<ref>c</ref><box>0 0 1 1</box>"
        )
        backend, _ = self._backend({"q": raw})
        result = backend.ground(_frame(), _query("q"), _policy(max_results=2))
        assert not result.success
        assert len(result.observations) == 2
        assert any("max_results" in e for e in result.validation_errors)
