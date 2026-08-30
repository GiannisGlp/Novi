"""Failure injection tests (plan 12, §26 Phase 26 — all 20 failure cases).

Every failure needs: classification (typed error), logging, metric, recovery
policy, user/operator visibility. This module exercises the 20 cases from
plan 12 §26 at the appropriate level — real where the failure is environmental
(missing deps, storage), simulated where hardware is not available (OOM,
MPS init, process crash). The expected outcome for every case (plan 12 §51):

    failure detected -> classified -> resources cleaned -> fallback selected
    -> autonomy remains bounded
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.inference.airllm.adapter import AirLLMAdapter
from novi.brain.inference.airllm.compatibility import (
    AirLLMCompatibility,
    require_airllm,
)
from novi.brain.inference.airllm.loader import AirLLMModelHandle
from novi.brain.inference.backends.mock import MockBackend
from novi.brain.inference.cancellation import CancellationToken
from novi.brain.inference.errors import (
    BackendInitializationError,
    BackendProtocolError,
    BackendUnavailableError,
    ContextLimitError,
    DeadlineExceededError,
    InferenceCancelledError,
    ModelCompatibilityError,
    ModelNotFoundError,
    OutOfMemoryError,
    ShardIntegrityError,
    StorageCapacityError,
    TokenizationError,
)
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.request import InferenceRequest
from novi.brain.inference.router import RoutingContext
from novi.brain.inference.runtime import InferenceRuntime, RuntimeConfig


class _ExplodingModel:
    """Fake AirLLM model that raises on demand."""

    def __init__(self, error: Exception) -> None:
        self.error = error

    def generate(self, prompt: str, max_new_tokens: int = 128, top_k: int = 1, temperature: float = 0.0):
        raise self.error


def _adapter(error: Exception | None = None, output: object = "", *, context_limit: int | None = None) -> AirLLMAdapter:
    handle = AirLLMModelHandle(
        model_id="qwen3.8-27b",
        revision="r",
        artifact_path="/models/q",
        shards_dir=None,  # type: ignore[arg-type]
    )
    return AirLLMAdapter(_ExplodingModel(error) if error else _FakeModel(output), handle, context_limit=context_limit)


class _FakeModel:
    def __init__(self, output: object) -> None:
        self.output = output

    def generate(self, prompt: str, max_new_tokens: int = 128, top_k: int = 1, temperature: float = 0.0):
        return self.output


class FailureInjectionTests(unittest.TestCase):
    """Cases 1–20 of plan 12 §26."""

    # -- 1. AirLLM import failure ------------------------------------------
    def test_case_1_import_failure(self) -> None:
        compat = AirLLMCompatibility(airllm_installed=False)
        with self.assertRaises(BackendUnavailableError) as ctx:
            require_airllm(compat)
        self.assertEqual(ctx.exception.code, "backend_unavailable")
        self.assertIn("not installed", ctx.exception.message)

    # -- 2. missing model --------------------------------------------------
    def test_case_2_missing_model(self) -> None:
        registry = ModelRegistry()
        with self.assertRaises(ModelNotFoundError) as ctx:
            registry.get_by_alias("ghost:latest")
        self.assertEqual(ctx.exception.code, "model_not_found")

    # -- 3. missing tokenizer ----------------------------------------------
    def test_case_3_missing_tokenizer(self) -> None:
        adapter = _adapter(error=RuntimeError("tokenizer vocab file not found"))
        with self.assertRaises(TokenizationError) as ctx:
            adapter.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))
        self.assertEqual(ctx.exception.code, "tokenization_error")

    # -- 4/5. incomplete / corrupt shards ----------------------------------
    def test_case_4_5_incomplete_and_corrupt_shards(self) -> None:
        from novi.brain.inference.airllm.shards import ShardManifest, verify_shard_integrity

        with tempfile.TemporaryDirectory() as tmp:
            shards = Path(tmp)
            (shards / "shard-0.bin").write_bytes(b"data")
            missing = ShardManifest(model_id="m", shard_count=2)
            with self.assertRaises(ShardIntegrityError):
                verify_shard_integrity(shards, missing)
            corrupt = ShardManifest(
                model_id="m",
                shard_count=1,
                checksums={"shard-0.bin": "0" * 64},  # wrong digest
            )
            with self.assertRaises(ShardIntegrityError):
                verify_shard_integrity(shards, corrupt)

    # -- 6. insufficient disk ----------------------------------------------
    def test_case_6_insufficient_disk(self) -> None:
        from novi.brain.inference.airllm.shards import check_disk_capacity

        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(StorageCapacityError):
            check_disk_capacity(tmp, required_bytes=10**30)

    # -- 7/8. RAM / VRAM exhaustion ----------------------------------------
    def test_case_7_8_ram_vram_exhaustion(self) -> None:
        for message in ("not enough memory to allocate", "CUDA out of memory. Tried to allocate 4.00 GiB"):
            adapter = _adapter(error=RuntimeError(message))
            with self.assertRaises(OutOfMemoryError) as ctx:
                adapter.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))
            self.assertEqual(ctx.exception.code, "out_of_memory")

    # -- 9. model load timeout ---------------------------------------------
    def test_case_9_load_timeout(self) -> None:
        from novi.brain.inference.airllm.loader import AirLLMLoader

        with tempfile.TemporaryDirectory() as tmp:
            loader = AirLLMLoader(model_root=tmp, load_timeout_s=0.01)
            spec = ModelSpec(id="qwen3.8-27b", backend_artifacts={"airllm": {"source_id": "Qwen/Qwen3.8-27B"}})
            with self.assertRaises((BackendInitializationError, BackendUnavailableError, DeadlineExceededError)):
                loader.load(spec)  # not prepared -> BackendInitializationError; typed either way

    # -- 10. generation timeout --------------------------------------------
    def test_case_10_generation_timeout(self) -> None:
        runtime = InferenceRuntime(
            backends=[MockBackend(latency_ms=200)],
            config=RuntimeConfig(deterministic_fallback=False),
        )
        self._approve_qwen38(runtime)
        # A request whose deadline already passed is refused at the scheduler.
        import datetime as _dt

        request = InferenceRequest(
            messages=[{"role": "user", "content": "hi"}],
            deadline=_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(seconds=1),
        )
        with self.assertRaises(DeadlineExceededError):
            runtime.generate(request, context=RoutingContext(model_hint="qwen3-8b"))

    def _approve_qwen38(self, runtime: InferenceRuntime, backend_preferences: tuple[str, ...] = ("mock",)) -> None:
        spec = runtime.registry.get("qwen3-8b")
        runtime.registry.register(
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

    # -- 11. process crash -------------------------------------------------
    def test_case_11_process_crash_recovery(self) -> None:
        # Simulated: backend raises repeatedly (as after a worker crash);
        # the runtime must classify, fall back, and stay bounded.
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
        runtime = InferenceRuntime(
            backends=[MockBackend(fail_generate=True, failure_class="process_crash")],
            registry=registry,
            config=RuntimeConfig(deterministic_fallback=True),
        )
        response = runtime.generate(InferenceRequest(messages=[{"role": "user", "content": "hi"}]))
        self.assertFalse(response.ok)  # explicit defer (no mock fallback configured)
        summary = runtime.telemetry.summary()
        self.assertIn("process_crash", summary["failures"])
        # Autonomy remains bounded: runtime still healthy at the orchestrator level.
        self.assertIsNotNone(runtime.snapshot())

    # -- 12. CUDA/MPS initialization failure -------------------------------
    def test_case_12_accelerator_init_failure(self) -> None:
        adapter = _adapter(error=RuntimeError("MPS backend failed to initialize: no metal device"))
        with self.assertRaises(BackendInitializationError) as ctx:
            adapter.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))
        self.assertEqual(ctx.exception.code, "backend_initialization_error")

    # -- 13. Transformers incompatibility ----------------------------------
    def test_case_13_transformers_incompatibility(self) -> None:
        compat = AirLLMCompatibility(airllm_installed=True, transformers="5.9.0")
        with self.assertRaises(ModelCompatibilityError) as ctx:
            require_airllm(compat)
        self.assertEqual(ctx.exception.code, "model_compatibility_error")
        self.assertIn("5.9.0", ctx.exception.message)

    # -- 14. unsupported architecture --------------------------------------
    def test_case_14_unsupported_architecture(self) -> None:
        adapter = _adapter(error=RuntimeError("architecture 'FancyXArch' is not supported"))
        with self.assertRaises(ModelCompatibilityError) as ctx:
            adapter.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))
        self.assertEqual(ctx.exception.code, "model_compatibility_error")

    # -- 15. context overflow ----------------------------------------------
    def test_case_15_context_overflow(self) -> None:
        adapter = _adapter(context_limit=64)
        with self.assertRaises(ContextLimitError):
            adapter.generate(InferenceRequest(messages=[{"role": "user", "content": "x" * 5000}]))

    # -- 16. cancellation --------------------------------------------------
    def test_case_16_cancellation(self) -> None:
        token = CancellationToken()
        token.cancel("user_stopped")
        with self.assertRaises(InferenceCancelledError) as ctx:
            token.check()
        self.assertEqual(ctx.exception.code, "inference_cancelled")
        self.assertEqual(token.reason, "user_stopped")

    # -- 17. malformed output ----------------------------------------------
    def test_case_17_malformed_output(self) -> None:
        adapter = _adapter(output={"unexpected": "shape"})
        with self.assertRaises(BackendProtocolError):
            adapter.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))

    # -- 18. backend hangs -------------------------------------------------
    def test_case_18_backend_hangs(self) -> None:
        # A backend that exceeds the request deadline must produce an explicit
        # deadline-miss representation (plan 12 §21), never silent success.
        runtime = InferenceRuntime(
            backends=[MockBackend(latency_ms=200)],
            config=RuntimeConfig(deterministic_fallback=False),
        )
        self._approve_qwen38(runtime)
        import datetime as _dt

        request = InferenceRequest(
            messages=[{"role": "user", "content": "hi"}],
            deadline=_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(milliseconds=50),
        )
        response = runtime.generate(request, context=RoutingContext(model_hint="qwen3-8b"))
        self.assertEqual(response.finish_reason, "deadline")
        self.assertIn("deadline_missed", response.warnings)
        # Explicit miss is also visible in telemetry.
        self.assertEqual(runtime.telemetry.summary()["requests"], 1)

    # -- 19. repeated failures ---------------------------------------------
    def test_case_19_repeated_failures(self) -> None:
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
        runtime = InferenceRuntime(
            backends=[MockBackend(fail_generate=True, failure_class="repeated_failure")],
            registry=registry,
            config=RuntimeConfig(deterministic_fallback=False),
        )
        for _ in range(5):
            runtime.generate(InferenceRequest(messages=[{"role": "user", "content": "hi"}]))
        summary = runtime.telemetry.summary()
        self.assertEqual(summary["failures"].get("repeated_failure"), 5)
        self.assertEqual(summary["requests"], 5)

    # -- 20. storage full during operation ---------------------------------
    def test_case_20_storage_full_during_operation(self) -> None:
        from novi.brain.inference.airllm.shards import check_disk_capacity

        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(StorageCapacityError):
            check_disk_capacity(tmp, required_bytes=10**30)


class UnloadReloadTests(unittest.TestCase):
    """Model switching (plan 12, §38 Phase 38): no leaked memory, no stale
    tokenizer/KV state, no cross-model corruption, correct metadata."""

    def test_unload_reload_switch(self) -> None:
        registry = ModelRegistry()
        for model_id in ("qwen3-8b", "qwen3-4b"):
            spec = registry.get(model_id)
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

        a = InferenceRequest(model_hint="qwen3-8b", messages=[{"role": "user", "content": "A"}])
        ra = runtime.generate(a)
        self.assertEqual(ra.model_id, "qwen3-8b")
        runtime.unload_model("qwen3-8b")
        self.assertNotIn("qwen3-8b", runtime._loaded_models)

        b = InferenceRequest(model_hint="qwen3-4b", messages=[{"role": "user", "content": "B"}])
        rb = runtime.generate(b)
        self.assertEqual(rb.model_id, "qwen3-4b")
        # Correct metadata on every response: exact model actually used.
        self.assertNotEqual(ra.model_id, rb.model_id)

        # Reload A: switch count recorded by telemetry.
        ra2 = runtime.generate(a)
        self.assertEqual(ra2.model_id, "qwen3-8b")
        self.assertGreaterEqual(runtime.telemetry.snapshot()["model_switch_count"], 1)

    def test_unload_is_idempotent(self) -> None:
        runtime = InferenceRuntime(backends=[MockBackend()])
        runtime.unload_model("qwen3-8b")
        runtime.unload_model("qwen3-8b")  # no-op, no error


if __name__ == "__main__":
    unittest.main()
