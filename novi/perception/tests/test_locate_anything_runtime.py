"""Tests: LocateAnything runtime boundary + capability probing
(plan Step 0.3, Step 3.2/3.3, §19 step 7).

The runtime module must import cleanly without torch/transformers installed,
and probing must report the seven capability states. Heavy dependencies are
never imported at module scope — tests inject fake environments and fake
model bundles.
"""

from __future__ import annotations

import pytest

from novi.perception.grounding import BackendState, SpatialInferenceMode
from novi.perception.locate_anything_runtime import (
    LocateAnythingRuntime,
    ProbeEnvironment,
    probe_capabilities,
)


class _FakeTorch:
    def __init__(self, mps: bool = True, cuda: bool = False, explode: bool = False):
        self.backends = type("b", (), {"mps": type("m", (), {"is_available": lambda: mps})()})()
        self.cuda = type("c", (), {"is_available": lambda: cuda})()
        self._explode = explode

    def __getattribute__(self, name):
        if name == "_explode":
            return super().__getattribute__(name)
        if super().__getattribute__("_explode"):
            raise RuntimeError("torch broken")
        return super().__getattribute__(name)


def _env(**kw) -> ProbeEnvironment:
    base = dict(
        torch=_FakeTorch(),
        transformers=object(),
        model_dir_present=True,
        model_revision="c32291ca",
        device="mps",
        mem_gb=36.0,
        detail_notes=(),
    )
    base.update(kw)
    return ProbeEnvironment(**base)


class TestProbeStates:
    def test_missing_torch_is_dependency_missing(self):
        caps = probe_capabilities(_env(torch=None))
        assert caps.state is BackendState.DEPENDENCY_MISSING
        assert not caps.usable

    def test_missing_transformers_is_dependency_missing(self):
        caps = probe_capabilities(_env(transformers=None))
        assert caps.state is BackendState.DEPENDENCY_MISSING

    def test_missing_model_dir_is_model_missing(self):
        caps = probe_capabilities(_env(model_dir_present=False))
        assert caps.state is BackendState.MODEL_MISSING
        assert not caps.usable

    def test_torch_probe_explosion_is_failed(self):
        caps = probe_capabilities(_env(torch=_FakeTorch(explode=True)))
        assert caps.state is BackendState.FAILED
        assert not caps.usable

    def test_available_reports_provenance_and_device(self):
        caps = probe_capabilities(_env())
        assert caps.usable
        assert caps.state is BackendState.AVAILABLE
        assert caps.model_id == "nvidia/LocateAnything-3B"
        assert caps.model_revision == "c32291ca"
        assert caps.device == "mps"

    def test_no_device_reports_unavailable(self):
        caps = probe_capabilities(_env(device=None))
        assert caps.state is BackendState.UNAVAILABLE

    def test_mode_reporting(self):
        caps = probe_capabilities(_env())
        assert caps.mode_supported(SpatialInferenceMode.HYBRID)


class TestRuntime:
    def test_probe_without_runtime_deps(self):
        rt = LocateAnythingRuntime(env_builder=lambda: _env(torch=None))
        caps = rt.probe()
        assert caps.state is BackendState.DEPENDENCY_MISSING

    def test_load_without_deps_raises_capability_error(self):
        rt = LocateAnythingRuntime(env_builder=lambda: _env(torch=None))
        with pytest.raises(RuntimeError, match="dependency_missing"):
            rt.load()

    def test_infer_requires_usable_backend(self):
        rt = LocateAnythingRuntime(env_builder=lambda: _env(torch=None))
        with pytest.raises(RuntimeError, match="dependency_missing"):
            rt.infer(image=None, prompt="the cup", mode=SpatialInferenceMode.HYBRID)

    def test_loader_missing_model_raises_model_missing(self):
        def loader():
            raise RuntimeError("model_missing: revision not found")

        rt = LocateAnythingRuntime(loader=loader, env_builder=lambda: _env())
        with pytest.raises(RuntimeError, match="model_missing"):
            rt.load()

    def test_infer_with_fake_bundle_returns_raw_text_and_latency(self):
        class FakeBundle:
            device = "mps"

            def __init__(self):
                self.calls: list[tuple[object, str, SpatialInferenceMode]] = []

            def generate(self, image, prompt, mode):
                self.calls.append((image, prompt, mode))
                return "<ref>cup</ref><box>100 200 900 800</box>", 42.0

        def loader():
            return FakeBundle()

        rt = LocateAnythingRuntime(loader=loader, env_builder=lambda: _env())
        raw, latency = rt.infer(image="img", prompt="the blue cup", mode=SpatialInferenceMode.HYBRID)
        assert raw == "<ref>cup</ref><box>100 200 900 800</box>"
        assert latency == 42.0

    def test_infer_loads_model_only_once(self):
        loads = []

        class FakeBundle:
            def generate(self, image, prompt, mode):
                return "<box>none</box>", 1.0

        def loader():
            loads.append(1)
            return FakeBundle()

        rt = LocateAnythingRuntime(loader=loader, env_builder=lambda: _env())
        rt.infer(None, "q1", SpatialInferenceMode.FAST)
        rt.infer(None, "q2", SpatialInferenceMode.FAST)
        assert len(loads) == 1

    def test_unload_resets_model(self):
        loads = []

        class FakeBundle:
            def generate(self, image, prompt, mode):
                return "<box>none</box>", 1.0

        def loader():
            loads.append(1)
            return FakeBundle()

        rt = LocateAnythingRuntime(loader=loader, env_builder=lambda: _env())
        rt.infer(None, "q", SpatialInferenceMode.FAST)
        rt.unload()
        rt.infer(None, "q", SpatialInferenceMode.FAST)
        assert len(loads) == 2

    def test_loader_raising_generic_error_is_failed(self):
        def loader():
            raise RuntimeError("oom during load")

        rt = LocateAnythingRuntime(loader=loader, env_builder=lambda: _env())
        with pytest.raises(RuntimeError, match="failed"):
            rt.load()
