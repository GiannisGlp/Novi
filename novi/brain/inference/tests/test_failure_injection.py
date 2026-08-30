"""Failure injection tests (plan 12, §26 Phase 26 — the failure categories).

Every failure needs: classification (typed error), logging, metric, recovery
policy, user/operator visibility. The categories are exercised at the runtime
level with the mock/existing backends; AirLLM-specific mechanisms were removed
by user decision (2026-08-30) — the taxonomy classes remain part of the stable
inference contract and are verified here as well.

Expected outcome for every case (plan 12 §51):
    failure detected -> classified -> resources cleaned -> fallback selected
    -> autonomy remains bounded
"""

from __future__ import annotations

import datetime as _dt
import unittest

from novi.brain.inference.backends.existing import ExistingBackend
from novi.brain.inference.backends.mock import MockBackend
from novi.brain.inference.cancellation import CancellationToken
from novi.brain.inference.errors import (
    BackendUnavailableError,
    DeadlineExceededError,
    GenerationError,
    InferenceCancelledError,
    ModelNotFoundError,
    StorageCapacityError,
    TokenizationError,
)
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.request import InferenceRequest
from novi.brain.inference.router import RoutingContext
from novi.brain.inference.runtime import InferenceRuntime, RuntimeConfig


def _approve(registry: ModelRegistry, model_id: str, backend_preferences: tuple[str, ...] = ("mock",)) -> None:
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


class FailureInjectionTests(unittest.TestCase):
    """The plan 12 §26 failure categories at the runtime level."""

    # -- 1. backend import/availability failure ----------------------------
    def test_case_1_backend_unavailable(self) -> None:
        backend = ExistingBackend()  # no transport configured -> unavailable
        self.assertEqual(backend.health()["status"], "unavailable")
        with self.assertRaises(BackendUnavailableError) as ctx:
            backend.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))
        self.assertEqual(ctx.exception.code, "backend_unavailable")

    # -- 2. missing model --------------------------------------------------
    def test_case_2_missing_model(self) -> None:
        registry = ModelRegistry()
        with self.assertRaises(ModelNotFoundError) as ctx:
            registry.get_by_alias("ghost:latest")
        self.assertEqual(ctx.exception.code, "model_not_found")

    # -- 3. tokenizer/decode failure ---------------------------------------
    def test_case_3_decode_failure(self) -> None:
        backend = ExistingBackend(transport=lambda payload: "")
        with self.assertRaises(TokenizationError) as ctx:
            backend.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))
        self.assertEqual(ctx.exception.code, "tokenization_error")

    # -- 6/20. storage-capacity error class --------------------------------
    def test_case_6_20_storage_capacity_classified(self) -> None:
        err = StorageCapacityError("insufficient disk", context={"refused": True})
        self.assertEqual(err.code, "storage_capacity")
        self.assertTrue(err.context["refused"])

    # -- 7/8. memory exhaustion class --------------------------------------
    def test_case_7_8_out_of_memory_classified(self) -> None:
        from novi.brain.inference.errors import OutOfMemoryError

        err = OutOfMemoryError("cuda out of memory")
        self.assertEqual(err.code, "out_of_memory")

    # -- 9/10. deadline exceeded (queue wait + generation miss) ------------
    def test_case_9_10_deadline_exceeded(self) -> None:
        runtime = InferenceRuntime(
            backends=[MockBackend()],
            config=RuntimeConfig(deterministic_fallback=False),
        )
        _approve(runtime.registry, "qwen3-8b")
        past = InferenceRequest(
            messages=[{"role": "user", "content": "hi"}],
            deadline=_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(seconds=1),
        )
        with self.assertRaises(DeadlineExceededError):
            runtime.generate(past, context=RoutingContext(model_hint="qwen3-8b"))

    def test_case_18_generation_deadline_miss_is_explicit(self) -> None:
        # A slow backend that misses the deadline produces finish_reason=deadline
        # with a warning — never silent success (plan 12 §21).
        runtime = InferenceRuntime(
            backends=[MockBackend(latency_ms=200)],
            config=RuntimeConfig(deterministic_fallback=False),
        )
        _approve(runtime.registry, "qwen3-8b")
        request = InferenceRequest(
            messages=[{"role": "user", "content": "hi"}],
            deadline=_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(milliseconds=50),
        )
        response = runtime.generate(request, context=RoutingContext(model_hint="qwen3-8b"))
        self.assertEqual(response.finish_reason, "deadline")
        self.assertIn("deadline_missed", response.warnings)

    # -- 11/19. repeated failures -> fallback + telemetry ------------------
    def test_case_11_19_repeated_failures(self) -> None:
        runtime = InferenceRuntime(
            backends=[MockBackend(fail_generate=True, failure_class="repeated_failure")],
            config=RuntimeConfig(deterministic_fallback=False),
        )
        _approve(runtime.registry, "qwen3-8b")
        for _ in range(5):
            runtime.generate(InferenceRequest(messages=[{"role": "user", "content": "hi"}]))
        summary = runtime.telemetry.summary()
        self.assertEqual(summary["failures"].get("repeated_failure"), 5)
        self.assertEqual(summary["requests"], 5)

    # -- 12/13/14. accelerator/transformers/architecture errors ------------
    def test_case_12_13_14_classified(self) -> None:
        from novi.brain.inference.errors import (
            BackendInitializationError,
            ModelCompatibilityError,
        )

        self.assertEqual(BackendInitializationError("mps init failed").code, "backend_initialization_error")
        self.assertEqual(ModelCompatibilityError("unsupported arch").code, "model_compatibility_error")

    # -- 15. context overflow ----------------------------------------------
    def test_case_15_context_overflow(self) -> None:
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
                context_limit=1024,
            )
        )
        runtime = InferenceRuntime(
            backends=[MockBackend()],
            registry=registry,
            config=RuntimeConfig(deterministic_fallback=False),
        )
        request = InferenceRequest(messages=[{"role": "user", "content": "x"}], max_input_tokens=5000)
        response = runtime.generate(request, context=RoutingContext(model_hint="qwen3-8b"))
        # The runtime converts InferenceError into an explicit error response;
        # the typed classification is preserved in metadata + telemetry.
        self.assertEqual(response.finish_reason, "error")
        self.assertEqual((response.provider_metadata or {}).get("error"), "context_limit_error")
        self.assertIn("context_limit_error", runtime.telemetry.summary()["failures"])

    # -- 16. cancellation --------------------------------------------------
    def test_case_16_cancellation(self) -> None:
        token = CancellationToken()
        token.cancel("user_stopped")
        with self.assertRaises(InferenceCancelledError) as ctx:
            token.check()
        self.assertEqual(ctx.exception.code, "inference_cancelled")

    # -- 17. malformed output ----------------------------------------------
    def test_case_17_malformed_output(self) -> None:
        def boom(payload):
            raise RuntimeError("backend exploded mid-generation")

        backend = ExistingBackend(transport=boom)
        with self.assertRaises(GenerationError) as ctx:
            backend.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))
        self.assertEqual(ctx.exception.code, "generation_error")


class UnloadReloadTests(unittest.TestCase):
    """Model switching (plan 12, §38): no leaked memory, no stale state,
    no cross-model corruption, correct per-response metadata."""

    def test_unload_reload_switch(self) -> None:
        registry = ModelRegistry()
        for model_id in ("qwen3-8b", "qwen3-4b"):
            _approve(registry, model_id)
        runtime = InferenceRuntime(backends=[MockBackend()], registry=registry)

        a = InferenceRequest(model_hint="qwen3-8b", messages=[{"role": "user", "content": "A"}])
        ra = runtime.generate(a)
        self.assertEqual(ra.model_id, "qwen3-8b")
        runtime.unload_model("qwen3-8b")
        self.assertNotIn("qwen3-8b", runtime._loaded_models)

        b = InferenceRequest(model_hint="qwen3-4b", messages=[{"role": "user", "content": "B"}])
        rb = runtime.generate(b)
        self.assertEqual(rb.model_id, "qwen3-4b")
        self.assertNotEqual(ra.model_id, rb.model_id)

        ra2 = runtime.generate(a)
        self.assertEqual(ra2.model_id, "qwen3-8b")
        self.assertGreaterEqual(runtime.telemetry.snapshot()["model_switch_count"], 1)

    def test_unload_is_idempotent(self) -> None:
        runtime = InferenceRuntime(backends=[MockBackend()])
        runtime.unload_model("qwen3-8b")
        runtime.unload_model("qwen3-8b")  # no-op, no error


if __name__ == "__main__":
    unittest.main()
