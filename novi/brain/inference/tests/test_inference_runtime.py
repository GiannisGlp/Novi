"""Inference runtime tests (plan 12, §18 Phase 13, §30 Phase 25, §43–44)."""

from __future__ import annotations

import unittest

from novi.brain.inference.adapter import (
    RuntimeBackedReasoningProvider,
    build_reasoning_request,
    parse_reasoning_response,
)
from novi.brain.inference.backends.existing import ExistingBackend
from novi.brain.inference.backends.mock import MockBackend
from novi.brain.inference.errors import BackendUnavailableError
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.request import InferenceRequest
from novi.brain.inference.response import FinishReason, InferenceResponse
from novi.brain.inference.router import RoutingContext
from novi.brain.inference.runtime import InferenceRuntime, RuntimeConfig


class InferenceRuntimeTests(unittest.TestCase):
    def _runtime(self, *, with_existing: bool = True, registry: ModelRegistry | None = None) -> InferenceRuntime:
        backends = [MockBackend()]
        if with_existing:
            backends.append(ExistingBackend(transport=lambda payload: "existing transport answer"))
        return InferenceRuntime(backends=backends, registry=registry or ModelRegistry())

    def _approve(
        self, registry: ModelRegistry, model_id: str, backend_preferences: tuple[str, ...] = ("existing",)
    ) -> None:
        spec = registry.get(model_id)
        registry.register(
            ModelSpec(
                id=spec.id,
                family=spec.family,
                role_candidates=spec.role_candidates,
                backend_preferences=backend_preferences,
                source_type=spec.source_type,
                source_id=spec.source_id,
                local_aliases=spec.local_aliases,
                status="approved",
            )
        )

    def test_generate_with_mock_backend(self) -> None:
        registry = ModelRegistry()
        self._approve(registry, "qwen3-8b", backend_preferences=("mock",))
        runtime = self._runtime(registry=registry)
        request = InferenceRequest(model_hint="qwen3-8b", messages=[{"role": "user", "content": "hi"}])
        response = runtime.generate(request)
        self.assertEqual(response.backend_id, "mock")
        self.assertIn("mock", response.text)
        self.assertTrue(response.ok)
        self.assertGreaterEqual(runtime.telemetry.request_count, 1)

    def test_generate_through_existing_backend(self) -> None:
        registry = ModelRegistry()
        self._approve(registry, "qwen3-8b")
        runtime = self._runtime(registry=registry)
        request = InferenceRequest(
            model_hint="qwen3-8b",
            messages=[{"role": "user", "content": "hi"}],
            backend_options={"force_backend": "existing"},
        )
        # Route via explicit context forcing the existing backend preference.
        decision_context = RoutingContext(reasoning_complexity="NORMAL")
        response = runtime.generate(request, context=decision_context)
        # Default routing selects "existing" for qwen3-8b (preference order).
        self.assertEqual(response.backend_id, "existing")
        self.assertEqual(response.text, "existing transport answer")

    def test_load_unload_lifecycle(self) -> None:
        runtime = self._runtime()
        runtime.load_model("qwen3-8b", backend_id="mock")
        self.assertIn("qwen3-8b", runtime._loaded_models)
        runtime.unload_model("qwen3-8b")
        self.assertNotIn("qwen3-8b", runtime._loaded_models)
        # Idempotent unload
        runtime.unload_model("qwen3-8b")

    def test_shutdown_is_idempotent(self) -> None:
        runtime = self._runtime()
        runtime.shutdown()
        runtime.shutdown()

    def test_snapshot_exposes_state(self) -> None:
        runtime = self._runtime()
        snapshot = runtime.snapshot()
        self.assertIn("hardware", snapshot)
        self.assertIn("registry", snapshot)
        self.assertIn("scheduler", snapshot)
        self.assertIn("telemetry", snapshot)
        self.assertIn("health", snapshot)

    def test_fallback_on_backend_failure(self) -> None:
        registry = ModelRegistry()
        self._approve(registry, "qwen3-8b", backend_preferences=("mock",))
        self._approve(registry, "qwen3-4b")
        failing = MockBackend(fail_generate=True, failure_class="simulated_failure")
        runtime = InferenceRuntime(
            backends=[failing, ExistingBackend(transport=lambda payload: "fallback answer")],
            registry=registry,
        )
        request = InferenceRequest(messages=[{"role": "user", "content": "hi"}])
        response = runtime.generate(request)
        # Deterministic fallback chain: existing backend (transport) then mock.
        self.assertTrue(response.warnings)
        self.assertIn("fallback_from", (response.provider_metadata or {}))
        # Telemetry records the failure class.
        summary = runtime.telemetry.summary()
        self.assertIn("simulated_failure", summary["failures"])

    def test_missing_model_raises(self) -> None:
        from novi.brain.inference.errors import ModelNotFoundError

        runtime = self._runtime()
        request = InferenceRequest(model_hint="no-such-model")
        with self.assertRaises(ModelNotFoundError):
            runtime.generate(request)

    def test_backend_manager_unknown_backend(self) -> None:
        runtime = self._runtime()
        with self.assertRaises(BackendUnavailableError):
            runtime.backends.get("nope")

    def test_airllm_not_routed_until_validated_combination(self) -> None:
        # Plan 12 Step 33-34: AirLLM is routable ONLY when the backend is
        # enabled AND the exact (model, compute backend) combination carries
        # validation evidence. qwen3.8-27b prefers airllm but no combination
        # is validated yet.
        registry = ModelRegistry()
        self._approve(registry, "qwen3.8-27b", backend_preferences=("airllm", "existing"))
        self._approve(registry, "qwen3-8b")
        runtime = InferenceRuntime(
            backends=[MockBackend(), ExistingBackend(transport=lambda p: "ok")],
            registry=registry,
            config=RuntimeConfig(airllm_enabled=True),  # enabled, but no validated combos
        )
        decision = runtime.router.route(RoutingContext(reasoning_complexity="DEEP"))
        self.assertEqual(decision.backend, "existing")
        # Even with a validated combination for a DIFFERENT hardware backend
        # (cuda), mps (this machine) is not in the validated set.
        runtime2 = InferenceRuntime(
            backends=[MockBackend(), ExistingBackend(transport=lambda p: "ok")],
            registry=registry,
            config=RuntimeConfig(
                airllm_enabled=True,
                validated_airllm_combinations=(("qwen3.8-27b", "cuda"),),
            ),
        )
        decision2 = runtime2.router.route(RoutingContext(reasoning_complexity="DEEP"))
        self.assertEqual(decision2.backend, "existing")

    def test_rollback_config_disables_airllm(self) -> None:
        # Plan 12 §55: rollback is one configuration change, not a rewrite.
        config = RuntimeConfig.rollback_to_existing()
        self.assertEqual(config.default_backend, "existing")
        self.assertFalse(config.airllm_enabled)
        self.assertEqual(config.validated_airllm_combinations, ())


class ReasoningAdapterTests(unittest.TestCase):
    def test_build_request_is_backend_neutral(self) -> None:
        request = build_reasoning_request(conclusion="c", confidence=0.5, situation={"a": 1}, recall=[1, 2])
        self.assertEqual(request.purpose, "decide")
        self.assertEqual(request.reasoning_budget, "NORMAL")
        self.assertTrue(request.messages)
        # No backend-specific fields on the public contract.
        self.assertNotIn("airllm", request.backend_options)

    def test_parse_response_default_on_failure(self) -> None:
        response = InferenceResponse(
            request_id="r",
            model_id="m",
            backend_id="b",
            text="",
            finish_reason=FinishReason.ERROR,
        )
        parsed = parse_reasoning_response(response)
        self.assertEqual(parsed["action"], "observe")
        self.assertEqual(parsed["confidence"], 0.0)

    def test_runtime_backed_provider_decides(self) -> None:
        registry = ModelRegistry()
        spec = registry.get("qwen3-8b")
        registry.register(
            ModelSpec(
                id=spec.id,
                family=spec.family,
                role_candidates=spec.role_candidates,
                backend_preferences=spec.backend_preferences,
                source_type=spec.source_type,
                source_id=spec.source_id,
                local_aliases=spec.local_aliases,
                status="approved",
            )
        )
        runtime = InferenceRuntime(backends=[MockBackend()], registry=registry)
        provider = RuntimeBackedReasoningProvider(runtime)
        intent = provider.decide(
            conclusion="person_alice_is_relevant_to_current_situation", confidence=0.9, situation={}
        )
        self.assertTrue(intent.action)
        self.assertIsNotNone(provider.last_response)
        self.assertEqual(intent.action, "observe")

    def test_runtime_unavailable_degrades_to_default(self) -> None:
        registry = ModelRegistry()
        runtime = InferenceRuntime(backends=[], registry=registry)  # no backends at all
        provider = RuntimeBackedReasoningProvider(runtime, default_action="wait")
        intent = provider.decide(conclusion="c", confidence=0.5, situation={})
        self.assertEqual(intent.action, "wait")


if __name__ == "__main__":
    unittest.main()
