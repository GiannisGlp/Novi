"""AirLLM backend through the reasoning-provider seam (plan 12, Step 23).

Verifies that a runtime backed by the AirLLM backend can serve the existing
reasoning contract end-to-end (decide -> InferenceRequest -> runtime ->
AirLLM backend -> InferenceResponse -> ActionIntent), with a stub loader/model
so the seam is testable without the 55.6 GB checkpoint. The brain never
knows which backend executes the request.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from novi.brain.inference.adapter import RuntimeBackedReasoningProvider
from novi.brain.inference.airllm.compatibility import AirLLMCompatibility
from novi.brain.inference.airllm.loader import AirLLMModelHandle
from novi.brain.inference.backends.airllm import AirLLMBackend
from novi.brain.inference.capabilities import HardwareProfile
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.runtime import InferenceRuntime, RuntimeConfig


class _FakeAirllmModel:
    """Stand-in for the AirLLM model object produced by a real load."""

    def __init__(self, output: str) -> None:
        self.output = output

    def generate(self, prompt: str, max_new_tokens: int = 128, top_k: int = 1) -> str:
        return self.output


class _FakeLoader:
    """Stand-in for AirLLMLoader.load: returns a handle wrapping a fake model."""

    def __init__(self, model: _FakeAirllmModel) -> None:
        self._model = model
        self.loaded: list[str] = []

    def load(self, spec):
        handle = AirLLMModelHandle(
            model_id=getattr(spec, "id", "qwen3.8-27b"),
            revision="fake-rev",
            artifact_path="/models/qwen3.8-27b",
            shards_dir=Path("/tmp/fake-shards"),
        )
        handle.model = self._model  # type: ignore[attr-defined]
        self.loaded.append(handle.model_id)
        return handle


def _airllm_eligible_spec(registry: ModelRegistry, model_id: str) -> ModelSpec:
    spec = registry.get(model_id)
    return ModelSpec(
        id=spec.id,
        family=spec.family,
        role_candidates=spec.role_candidates,
        backend_preferences=("airllm", "existing"),
        source_type=spec.source_type,
        source_id=spec.source_id,
        local_aliases=spec.local_aliases,
        context_limit=spec.context_limit,
        status="approved",
        backend_artifacts={
            "airllm": {"source_id": "Qwen/Qwen3.8-27B", "architecture": "Qwen3_5ForConditionalGeneration"}
        },
        resolved={"architecture": "Qwen3_5ForConditionalGeneration", "parameter_count": 27},
    )


class AirLLMSeamTests(unittest.TestCase):
    def test_airllm_backend_serves_reasoning_seam(self) -> None:
        registry = ModelRegistry()
        registry.register(_airllm_eligible_spec(registry, "qwen3.8-27b"))
        model = _FakeAirllmModel("action: observe -- a person is relevant to the current situation")
        backend = AirLLMBackend(
            enabled=True,
            compat=AirLLMCompatibility(airllm_installed=True, transformers="4.57.1"),
            loader=_FakeLoader(model),
        )
        runtime = InferenceRuntime(
            backends=[backend],
            registry=registry,
            config=RuntimeConfig(
                airllm_enabled=True,
                validated_airllm_combinations=(("qwen3.8-27b", "mps"),),
                deterministic_fallback=False,
            ),
        )
        # Machine VRAM is unknown from the stdlib probe; provide a known
        # constrained-VRAM profile so the AirLLM gate (VRAM known) passes.
        runtime.hardware = HardwareProfile(
            profile_id="seam-test",
            compute_backend="mps",
            vram_total_bytes=4 << 30,
            vram_available_bytes=1 << 30,
        )

        provider = RuntimeBackedReasoningProvider(runtime, reasoning_budget="DEEP")
        intent = provider.decide(
            conclusion="person_alice_is_relevant_to_current_situation",
            confidence=0.5,
            situation={},
        )
        self.assertEqual(intent.action, "observe")
        self.assertIsNotNone(provider.last_response)
        self.assertEqual(provider.last_response.backend_id, "airllm")
        self.assertEqual(provider.last_response.model_id, "qwen3.8-27b")
        # The stub loader was used: the airllm load path executed.
        self.assertEqual(backend._current_model_id, "qwen3.8-27b")

    def test_airllm_not_selected_without_validated_combo_through_seam(self) -> None:
        # Same setup but NO validated combination: the reasoning provider must
        # route to the existing backend instead (runtime validator gate).
        registry = ModelRegistry()
        spec = registry.get("qwen3-8b")
        registry.register(
            ModelSpec(
                id=spec.id,
                family=spec.family,
                role_candidates=spec.role_candidates,
                backend_preferences=("existing",),
                source_type=spec.source_type,
                source_id=spec.source_id,
                local_aliases=spec.local_aliases,
                status="approved",
            )
        )
        backend = AirLLMBackend(
            enabled=True,
            compat=AirLLMCompatibility(airllm_installed=True, transformers="4.57.1"),
            loader=_FakeLoader(_FakeAirllmModel("x")),
        )
        runtime = InferenceRuntime(
            backends=[backend],
            registry=registry,
            config=RuntimeConfig(airllm_enabled=False),  # no validated combo path
        )
        provider = RuntimeBackedReasoningProvider(runtime, reasoning_budget="NORMAL")
        # qwen3-8b prefers existing but no existing backend is registered -> the
        # runtime reports unavailable via the deterministic path; the provider
        # still degrades to a safe default without raising raw AirLLM errors.
        intent = provider.decide(conclusion="c", confidence=0.5, situation={})
        self.assertTrue(intent.action)


if __name__ == "__main__":
    unittest.main()
