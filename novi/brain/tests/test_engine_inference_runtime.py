"""Plan 12, §43 Phase 43: MacBrain remains model/backend agnostic.

The brain receives a ``ReasoningProvider``; an injected ``InferenceRuntime``
backs the reasoning provider through the runtime-backed adapter. The brain
must never construct a backend directly, and with no runtime injected the
default reasoning behavior must be unchanged.
"""

from __future__ import annotations

import unittest

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.inference.adapter import RuntimeBackedReasoningProvider
from novi.brain.inference.backends.mock import MockBackend
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.runtime import InferenceRuntime
from novi.brain.models.router import ReasoningRouter


class EngineInferenceRuntimeTests(unittest.TestCase):
    def test_default_behavior_unchanged_without_runtime(self) -> None:
        brain = MacBrain(config=MacBrainConfig(max_cycles=0))
        self.assertIsInstance(brain.reasoning, ReasoningRouter)
        self.assertIsNone(brain.inference_runtime)

    def test_runtime_injection_uses_adapter(self) -> None:
        runtime = InferenceRuntime(backends=[MockBackend()])
        brain = MacBrain(config=MacBrainConfig(max_cycles=0), inference_runtime=runtime)
        self.assertIs(brain.inference_runtime, runtime)
        self.assertIsInstance(brain.reasoning, RuntimeBackedReasoningProvider)

    def test_explicit_reasoning_override_wins(self) -> None:
        class CustomProvider:
            def decide(self, **kwargs):
                from novi.brain.models.reasoning import ActionIntent

                return ActionIntent(action="wait", parameters={}, rationale="custom")

        runtime = InferenceRuntime(backends=[MockBackend()])
        brain = MacBrain(
            config=MacBrainConfig(max_cycles=0),
            inference_runtime=runtime,
            reasoning=CustomProvider(),  # type: ignore[arg-type]
        )
        self.assertIsInstance(brain.reasoning, CustomProvider)

    def test_runtime_backed_provider_end_to_end(self) -> None:
        registry = ModelRegistry()
        spec = registry.get("qwen3-8b")
        registry.register(
            ModelSpec(
                id=spec.id,
                family=spec.family,
                role_candidates=spec.role_candidates,
                backend_preferences=("mock",),
                source_type=spec.source_type,
                source_id=spec.source_id,
                local_aliases=spec.local_aliases,
                status="approved",
            )
        )
        runtime = InferenceRuntime(backends=[MockBackend()], registry=registry)
        brain = MacBrain(config=MacBrainConfig(max_cycles=0), inference_runtime=runtime)
        intent = brain.reasoning.decide(conclusion="c", confidence=0.5, situation={})
        self.assertTrue(intent.action)
        # Telemetry proves the runtime executed a real request.
        self.assertGreaterEqual(runtime.telemetry.request_count, 1)


if __name__ == "__main__":
    unittest.main()
