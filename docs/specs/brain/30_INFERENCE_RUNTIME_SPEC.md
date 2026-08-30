# Inference Runtime Specification

**Status:** PROTOTYPE — Novi-owned inference runtime implemented behind the existing (Ollama/local) path.
**Owner:** Novi project
**Scope:** the Novi-owned, backend-neutral inference runtime that cognition and autonomy call. AirLLM was removed by user decision (2026-08-30) after execution-verifying that its Mac (MLX) path provides no performance value on this machine; the runtime contract, router, scheduler, telemetry and fallback remain and serve the existing local path.

---

## 1. Purpose

Novi's intelligence lives *above* the runtime. This spec defines the Novi-owned inference contract so that any backend — the existing Ollama/local path today, and future local runtimes — can be swapped without changing cognition, autonomy, planning, governance, or safety code.

## 2. Dependency direction (invariant)

```text
Novi cognition/autonomy
        |
        v
Novi inference contract        <-- novi.brain.inference
        |
        v
Novi model router / scheduler
        |
        v
Existing/local backend   (future backends)
```

Rules:

1. Cognition never imports a backend directly.
2. The router never bypasses governance; a model response never proves an action succeeded.
3. The model is never the persistent source of truth.
4. Model/backend selection, model identity, and revision are observable.

## 3. Contracts

### 3.1 `InferenceRequest` (`novi/brain/inference/request.py`)

Typed, frozen, backend-neutral. Key fields: `request_id`, `trace_id`, `created_at`, `caller`, `purpose`, `model_policy`, `model_hint`, `messages` (the bounded context package — never direct memory access), `max_input_tokens`, `max_output_tokens`, `temperature`, `top_p`, `top_k`, `stop_sequences`, `stream`, `priority`, `deadline`, `latency_budget_ms`, `reasoning_budget`, `allow_background`, `conversation_id`, `mission_id`, and `backend_options` (backend-specific, validated against capabilities, never required by cognition).

Priorities: `CRITICAL > HIGH > NORMAL > LOW > BACKGROUND`. Inference priority never overrides the deterministic safety system.

### 3.2 `InferenceResponse` (`response.py`)

Required: `request_id`, `model_id`, `backend_id`, `text`, `finish_reason`, `input_tokens`, `output_tokens`, `latency_ms`, `time_to_first_token_ms`, `generation_tokens_per_second`, `cache_status`, `hardware_profile_id`, `warnings`, `trace_id`. Optional structured fields: `tool_calls`, `reasoning_metadata`, `structured_output`, `provider_metadata` (diagnostic only, never truth).

### 3.3 Error taxonomy (`errors.py`)

16 stable Novi errors — `InferenceError` plus `InferenceConfigurationError`, `ModelNotFoundError`, `ModelUnavailableError`, `BackendUnavailableError`, `BackendInitializationError`, `ModelCompatibilityError`, `TokenizationError`, `ContextLimitError`, `DeadlineExceededError`, `InferenceCancelledError`, `OutOfMemoryError`, `StorageCapacityError`, `ShardIntegrityError`, `GenerationError`, `BackendProtocolError`. Backends translate their exceptions into these categories; a raw backend exception never leaks through `MacBrain`.

### 3.4 `InferenceBackend` (`contracts.py`)

Operations: `backend_id()`, `capabilities()`, `validate_model()`, `prepare()`, `load()`, `unload()`, `generate()`, `stream()` (optional), `health()`, `metrics()`, `shutdown()` (idempotent). Lifecycle is explicit and validated (`lifecycle.py`): `UNKNOWN → REGISTERED → VALIDATING → PREPARING → READY → LOADING → LOADED → RUNNING → DRAINING → UNLOADED`, with `DEGRADED`/`FAILED`; invalid transitions (e.g. `FAILED → RUNNING`) raise `LifecycleTransitionError`.

## 4. Runtime (`runtime.py`)

`InferenceRuntime` orchestrates: route → schedule → load → generate → telemetry.

- `BackendManager` owns registered backends; selection is observable.
- Context-limit guard (plan 12 §25): requests exceeding the registry-recorded `context_limit` are rejected before dispatch with `ContextLimitError`.
- Deadline handling (plan 12 §21): a request expired before dispatch raises `DeadlineExceededError`; a generation that misses its deadline returns `finish_reason="deadline"` with a warning — never silent success.
- Fallback chain (deterministic, plan 12 §30): backend failure → approved fallback model on the existing backend → structured deterministic behavior (mock) → explicit `finish_reason="error"` response. A fallback never silently changes authority; warnings + telemetry record the path.
- `ModelRouter` (`router.py`) produces auditable `RoutingDecision{model, backend, execution_mode, reason, confidence, fallback}`. Deliberation levels `FAST/NORMAL/DELIBERATE/DEEP` map to provisional model hypotheses (`qwen3-4b/qwen3-8b/nemotron-3.5-lightning/qwen3.8-27b`) that benchmarks can overturn. No model is routable until `status == "approved"`; `qwen3.8:latest` is unroutable until its exact artifact identity is recorded.
- `InferenceScheduler` (`scheduler.py`): priority-class FIFO, deadline-aware, `max_concurrent` slots, cooperative cancellation via `CancellationToken`. Arrival policies: `wait | queue | cancel_background | switch_model | smaller_fallback`. Preemption is intentionally NOT implemented.
- `InferenceTelemetry` (`telemetry.py`): per-request records (queue/load/TTFT/generation, tokens, RAM before/after best-effort, failure class, fallback). Prompts are never logged by default.
- `InferenceHealth` (`health.py`): per-model lifecycle/residency + backend health + scheduler/telemetry views.

## 5. Model registry (`registry.py`)

`ModelSpec` records `id`, `family`, `role_candidates`, `backend_preferences`, `source_type`, `source_id`, `local_aliases`, `context_limit`, `capabilities`, `hardware_requirements`, `status`, `backend_artifacts`, `resolved`. Artifacts are resolved explicitly via `resolve_backend_artifact` — never silently substitute a checkpoint. The registry contains exactly the five approved aliases; none routable by default.

## 6. Hardware capability (`capabilities.py`)

`HardwareProfile` snapshot (platform, OS, CPU, RAM, GPU, VRAM, compute backend, storage). Tri-state `supported | unsupported | unknown`; `unknown` is never promoted to `supported`. Stdlib-only `probe_hardware()` is conservative.

## 7. Backends

- `MockBackend` — deterministic, CI-safe; load/unload, streaming, simulated failures.
- `ExistingBackend` — wraps the current local runtime (Ollama via an injected transport, or `MacModelProvider`); CI-safe when no transport is configured.

## 8. Integration (`adapter.py`, engine wiring)

`RuntimeBackedReasoningProvider` implements the existing `ReasoningProvider.decide()` contract through the runtime; `build_reasoning_request()`/`parse_reasoning_response()` bridge the two contracts. `MacBrain.__init__` accepts `inference_runtime=` and, when injected, uses the adapter; otherwise the default `ReasoningRouter` behavior is unchanged. The brain never constructs a backend.

## 9. Status

The inference runtime is `PROTOTYPE` — implemented and tested (70 inference + 1762 brain tests). AirLLM was removed 2026-08-30 by user decision (execution-verified: its Mac MLX path is ~100× slower than the existing Ollama path with no memory benefit for the models it can run); the runtime contract is backend-neutral and unchanged.
