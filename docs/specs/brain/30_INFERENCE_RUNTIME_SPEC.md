# Inference Runtime Specification

**Status:** PROTOTYPE — contract implemented behind the Novi inference runtime (plan `12_AIRLLM_ADAPTATION_AND_INFERENCE_RUNTIME_PLAN.md`).
**Owner:** Novi project
**Scope:** the Novi-owned, backend-neutral inference runtime that cognition and autonomy call; the existing local path and the optional AirLLM backend both implement its contract.

---

## 1. Purpose

Novi's intelligence lives *above* the runtime. This spec defines the Novi-owned inference contract so that any backend — the existing Ollama/local path, AirLLM, and future Transformers/vLLM/TensorRT-LLM/llama.cpp runtimes — can be swapped without changing cognition, autonomy, planning, governance, or safety code.

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
        +------------------+
        |                  |
        v                  v
Existing/local backend   AirLLM backend
        |                  |
        +---------+--------+
                  |
                  v
             Model runtime
```

Rules:

1. Cognition never imports AirLLM (verified by grep — Gate A).
2. AirLLM never controls physical actuation.
3. The router never bypasses governance; a model response never proves an action succeeded.
4. The model is never the persistent source of truth.
5. Model/backend selection, model identity, and revision are observable.

## 3. Contracts

### 3.1 `InferenceRequest` (`novi/brain/inference/request.py`)

Typed, frozen, backend-neutral. Key fields: `request_id`, `trace_id`, `created_at`, `caller`, `purpose`, `model_policy`, `model_hint`, `messages` (the bounded context package — never direct memory access), `max_input_tokens`, `max_output_tokens`, `temperature`, `top_p`, `top_k`, `stop_sequences`, `stream`, `priority`, `deadline`, `latency_budget_ms`, `reasoning_budget`, `allow_background`, `conversation_id`, `mission_id`, and `backend_options` (the only backend-specific channel, validated against backend capabilities, never required by cognition).

Priorities: `CRITICAL > HIGH > NORMAL > LOW > BACKGROUND`. Inference priority never overrides the deterministic safety system.

### 3.2 `InferenceResponse` (`response.py`)

Required: `request_id`, `model_id`, `backend_id`, `text`, `finish_reason`, `input_tokens`, `output_tokens`, `latency_ms`, `time_to_first_token_ms`, `generation_tokens_per_second`, `cache_status`, `hardware_profile_id`, `warnings`, `trace_id`. Optional structured fields: `tool_calls`, `reasoning_metadata`, `structured_output`, `provider_metadata` (diagnostic only, never truth).

### 3.3 Error taxonomy (`errors.py`)

16 stable Novi errors — `InferenceError` plus `InferenceConfigurationError`, `ModelNotFoundError`, `ModelUnavailableError`, `BackendUnavailableError`, `BackendInitializationError`, `ModelCompatibilityError`, `TokenizationError`, `ContextLimitError`, `DeadlineExceededError`, `InferenceCancelledError`, `OutOfMemoryError`, `StorageCapacityError`, `ShardIntegrityError`, `GenerationError`, `BackendProtocolError`. Backends translate their exceptions into these categories; a raw backend exception never leaks through `MacBrain`.

### 3.4 `InferenceBackend` (`contracts.py`)

Operations: `backend_id()`, `capabilities()`, `validate_model()`, `prepare()`, `load()`, `unload()`, `generate()`, `stream()` (optional), `health()`, `metrics()`, `shutdown()` (idempotent). Lifecycle is explicit and validated (`lifecycle.py`): `UNKNOWN → REGISTERED → VALIDATING → PREPARING → READY → LOADING → LOADED → RUNNING → DRAINING → UNLOADED`, with `DEGRADED`/`FAILED`; invalid transitions (e.g. `FAILED → RUNNING`) raise `LifecycleTransitionError`. Backends may request a target state; the machine walks a validated path.

## 4. Runtime (`runtime.py`)

`InferenceRuntime` orchestrates: route → schedule → load → generate → telemetry.

- `BackendManager` owns registered backends; selection is observable.
- Fallback chain (deterministic, §30): primary backend failure → approved fallback model on the existing backend → structured deterministic behavior (mock) → explicit `finish_reason=ERROR` response ("ask for help / defer"). A fallback never silently changes a high-risk action's authority; warnings + telemetry record the path.
- `ModelRouter` (`router.py`) produces auditable `RoutingDecision{model, backend, execution_mode, reason, confidence, fallback}`. Deliberation levels `FAST/NORMAL/DELIBERATE/DEEP` map to provisional model hypotheses (`qwen3-4b/qwen3-8b/nemotron-3.5-lightning/qwen3.8-27b`) that the benchmark suite can overturn. No model is routable until `status == "approved"`; `qwen3.8:latest` is unroutable until its exact artifact identity is recorded.
- `InferenceScheduler` (`scheduler.py`): priority-class FIFO, deadline-aware, `max_concurrent` slots, cooperative cancellation via `CancellationToken`. Arrival policies: `wait | queue | cancel_background | switch_model | smaller_fallback`. Preemption is intentionally NOT implemented.
- `InferenceTelemetry` (`telemetry.py`): per-request records (queue/load/TTFT/generation, tokens, RAM before/after best-effort, failure class, fallback). Prompts are never logged by default.
- `InferenceHealth` (`health.py`): per-model lifecycle/residency + backend health + scheduler/telemetry views.

## 5. Model registry (`registry.py`)

Independent of AirLLM. `ModelSpec` records `id`, `family`, `role_candidates`, `backend_preferences`, `source_type`, `source_id`, `local_aliases`, `context_limit`, `capabilities`, `hardware_requirements`, `status`, `backend_artifacts`, `resolved`. Mapping is explicit: `local alias -> canonical model ID -> backend artifact`; missing mappings raise `InferenceConfigurationError` — never silently substitute a checkpoint. Initial registry contains exactly the five approved aliases; none routable by default.

## 6. Hardware capability (`capabilities.py`)

`HardwareProfile` snapshot (platform, OS, CPU, RAM, GPU, VRAM, compute backend, storage). Tri-state `supported | unsupported | unknown`; `unknown` is never promoted to `supported`. Stdlib-only `probe_hardware()` is conservative: GPU backend stays `unknown` unless confirmed.

## 7. AirLLM surface (`airllm/`)

All AirLLM imports are lazy. `compatibility.py` owns the version matrix (Python/Torch/Transformers/Accelerate/Safetensors/AirLLM/OS/arch/GPU) and refuses Transformers majors outside the validated range rather than upgrading project-wide. `loader.py` resolves artifacts and prepares/loads models with manifests. `shards.py` implements the `$NOVI_DATA/models/airllm/<model>/` layout, capacity gating (`StorageCapacityError`), manifests, and integrity verification. `cache.py` keys caches on model revision + backend + tokenizer revision + conversation + context hash + runtime config. `process.py` keeps the worker-mode interface compatible with in-process execution. `adapter.py` translates requests/responses and maps every AirLLM exception to the Novi taxonomy.

## 8. Integration (`adapter.py`, engine wiring)

`RuntimeBackedReasoningProvider` implements the existing `ReasoningProvider.decide()` contract through the runtime; `build_reasoning_request()`/`parse_reasoning_response()` bridge the two contracts. `MacBrain.__init__` accepts `inference_runtime=` and, when injected, uses the adapter; otherwise the default `ReasoningRouter` behavior is unchanged (1758 Brain tests green). The brain never constructs a backend.

## 9. Acceptance gates status (plan 12, §59)

| Gate | Status |
|---|---|
| A — Contract exists; existing reasoning path uses it; no cognition imports AirLLM | **PASS** (grep-verified) |
| C — MacBrain uses AirLLM through DI; existing tests green; no safety boundary change | **PASS (contract-level)** — runtime DI wired; AirLLM itself pending hardware validation |
| B/D/E/F/G — AirLLM smoke, benchmark, failure recovery, soak, production candidate | PENDING hardware/benchmark evidence |

AirLLM backend status: implemented behind the contract, disabled by default (`enabled=false`), `compression=none`, `delete_original=false`, `preparation_allowed=false`, `max_concurrent_requests=1` (plan 12, §34).
