# Novi AirLLM Adaptation and Inference Runtime Plan

**Workstream:** 06_AUTONOMY / Brain Runtime
**Status:** PROTOTYPE — inference runtime contract implemented; AirLLM backend implemented behind the contract (disabled by default); hardware validation and benchmarking pending
**Priority:** P0 architecture / P1 initial optimization
**Target branch:** `main`
**Date:** 2026-08-30
**Owner:** Novi project

---

## 0. Implementation progress

Updated 2026-08-30 (first implementation round). Status vocabulary per §65: the inference runtime is `PROTOTYPE`, the AirLLM backend is `PROTOTYPE` (implemented behind the contract; not `TESTED`/`INTEGRATED` until hardware evidence exists).

| Step (§66) | Status | Evidence |
|---|---|---|
| 1. Audit inference/model calls | DONE | `benchmarks/inference-audit.json` (57 sites; 24 migrate-to-runtime) |
| 2. Capture baseline benchmarks | DONE | `benchmarks/baseline/*.json` — real measurements for 4 running Ollama models (qwen3.8:27b TTFT 14.5s/6.7 tps, qwen3:8b 15.8s/25.4 tps, qwen3:4b 16.5s/46.5 tps, nemotron 10.8s/44.6 tps; 0% error, 8/8 prompts ok) |
| 3. Define `InferenceRequest`/`InferenceResponse` | DONE | `novi/brain/inference/request.py`, `response.py` (+ tests) |
| 4. Error taxonomy | DONE | `novi/brain/inference/errors.py` (16 categories) |
| 5. Define `InferenceBackend` | DONE | `novi/brain/inference/contracts.py` (+ lifecycle in `lifecycle.py`) |
| 6. Mock backend | DONE | `novi/brain/inference/backends/mock.py` |
| 7. Existing reasoning provider behind runtime | DONE | `novi/brain/inference/adapter.py` (`RuntimeBackedReasoningProvider`), `backends/existing.py` |
| 8. Complete existing Brain test suite | DONE | 1758 passed |
| 9. Model registry | DONE | `novi/brain/inference/registry.py` |
| 10. Register five aliases without enabling routing | DONE | registry contains exactly the five; `routable()==()` by default |
| 11. Hardware capability detection | DONE | `novi/brain/inference/capabilities.py` (`probe_hardware`) |
| 12. Runtime lifecycle | DONE | `novi/brain/inference/runtime.py`, `lifecycle.py` |
| 13. Scheduler + cancellation | DONE | `novi/brain/inference/scheduler.py`, `cancellation.py` |
| 14. Telemetry | DONE | `novi/brain/inference/telemetry.py` |
| 15. AirLLM optional dependency | DONE | `pyproject.toml` `novi[airllm]` extra (not in base install) |
| 16. AirLLM compatibility adapter | DONE | `novi/brain/inference/airllm/`, `backends/airllm.py` (lazy imports, disabled default) |
| 17. Resolve exact HF artifact for `qwen3.8:27b` | DONE (blocker recorded) | `Qwen/Qwen3.8-27B` sha `1d4bf0f2ff60…`; architecture `Qwen3_5ForConditionalGeneration`; config requires `transformers 5.8.0.dev0` which conflicts with the validated AirLLM stack (4.57.1, cap `<5.13`) — registry records `airllm_eligible=false`; no checkpoint substitution |
| 18. Prepare Qwen3.8-27B into AirLLM shards | BLOCKED (environment) | checkpoint is 55.6 GB (HF tree); source + shards + reserve ≈ 112 GB required vs 58 GiB free — `check_disk_capacity` refuses with typed `StorageCapacityError` (verified). Also blocked on the Step 17 Transformers conflict (AirLLM `airllm_qwen3_5.py` documents "Needs transformers 5.8+"). Backend remains an implemented, platform-blocked provider (§17) |
| 19–22. Shard integrity, smoke, tokenizer, warm inference | PENDING | gated on Step 18 |
| 23. Integrate AirLLM backend through reasoning seam | DONE (stub-verified) | `test_airllm_seam.py`: runtime backed by AirLLMBackend serves `MacBrain`-compatible `decide()` end-to-end; routing selects airllm only with a validated (model, hardware) combination |
| 24. Complete Brain regression suite | DONE | 1762 brain + 113 inference tests green (rounds 1–2) |
| 25. Run Novi cognitive benchmark suite | DONE (existing backend) | baseline harness scores deterministic quality per prompt (§36): all 4 running models 8/8 prompts + 8/8 quality checks, 0% error |
| 26. Compare AirLLM against baseline | PENDING | gated on Step 18; baseline comparison data ready in `benchmarks/baseline/` |
| 29. Test offline operation | DONE (runtime level) | `test_offline_operation.py`: mock + local-transport existing backends complete generation with zero network calls |
| 30. Long-duration soak tests | HARNESS DONE, durations gated | `novi/brain/benchmarks/soak.py` (CI-safe verified); 1h/4h/8h/24h require target hardware |
| 27. Failure recovery | DONE (mock-level) | `test_failure_injection.py`: all 20 cases of §26 exercised (import failure → cancellation, OOM, hang, crash, storage full…) with typed classification |
| 28. Model unload/reload | DONE | `UnloadReloadTests`: switch A→B→A with correct per-response metadata, idempotent unload |
| 33. Router eligibility rules | DONE | `RuntimeConfig.airllm_enabled` + `validated_airllm_combinations`; runtime validator gate: AirLLM routable ONLY for enabled + (model, compute-backend) pairs with execution evidence |
| 34. Enable AirLLM only for validated combos | DONE | empty validated set by default → router never selects AirLLM until evidence exists |
| 35. Fallback and rollback configuration | DONE | `RuntimeConfig.rollback_to_existing()` — one config change disables AirLLM, contract unchanged (§55) |
| 23–37. Integration, regression, benchmarks, failure, soak, compression, prefetch, eligibility | PENDING | gated on Steps 17–22 |

Docs: `docs/specs/brain/30_INFERENCE_RUNTIME_SPEC.md`, `31_MODEL_COMPATIBILITY_MATRIX.md`, `32_RUNTIME_BENCHMARK_SPEC.md`.

---

## 1. Purpose

This document defines the complete implementation plan for adapting AirLLM to Novi without coupling Novi's cognition, autonomy, memory, planning, governance, or safety systems to AirLLM.

The goal is not to make AirLLM "the brain". The goal is to introduce a vendor/framework-neutral inference runtime inside the Novi Brain and implement AirLLM as one backend of that runtime.

Novi's North Star explicitly states that Novi is not defined by a particular LLM, robot chassis, simulator, GPU vendor, compute board, or inference framework. The repository also requires a hybrid architecture in which neural models perform learning-appropriate work while deterministic systems own persistent state, provenance, governance, safety, hardware limits, recovery, and audit. Therefore AirLLM must remain behind an inference contract.

Current repository context:

- `novi/brain/` is the canonical implementation namespace for the executable brain.
- `novi/brain/engine.py` currently wires the Mac Brain, cognition, perception, memory, planner, governance, telemetry, and the existing `ReasoningProvider`/`DeliberativeReasoningProvider` interfaces.
- `docs/plans/06_AUTONOMY/00_AUTONOMY_IMPLEMENTATION_INDEX.md` defines the autonomy workstream and requires model proposals to remain behind deterministic validation and safety boundaries.
- The current development platform is the Mac prototype; final NVIDIA/Jetson hardware is deliberately not locked.
- Current candidate LLMs are restricted to the project's current set: `qwen3.8:27b`, `qwen3:8b`, `nemotron-3.5-lightning:latest`, `qwen3.8:latest`, and `qwen3:4b`. Larger models are future candidates, not current dependencies.

AirLLM's current upstream implementation uses a memory-frugal wrapper around Hugging Face causal language models. It splits checkpoints into per-layer shards, instantiates the underlying Transformers model on the `meta` device, installs hooks that stream module weights from storage to the execution device and release them after execution, and supports per-expert streaming for compatible MoE architectures. The current upstream README explicitly lists Qwen3.8-27B support and documents approximately 3.33 GB VRAM for its reference setup. The project also supports configurable prefetching, shard storage, compression, and deletion of original checkpoints. These characteristics make AirLLM a useful candidate for constrained deep-model inference, but they also make disk I/O, startup/sharding, latency, cache policy, and hardware compatibility first-class Novi concerns.

## 2. Architectural decision

### 2.1 Decision

Adopt AirLLM as an **optional inference backend** behind a Novi-owned inference runtime abstraction.

Do not expose AirLLM classes, configuration objects, tokenizer details, shard paths, or exceptions to cognition/autonomy modules.

The only permitted dependency direction is:

```text
Novi cognition/autonomy
        |
        v
Novi inference contract
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

### 2.2 Non-goals

This plan does not:

1. replace the Novi cognitive architecture with an agent framework;
2. make an LLM responsible for motor control;
3. put AirLLM in the safety boundary;
4. make AirLLM mandatory for every model;
5. assume that a model is compatible merely because it can be downloaded;
6. assume that AirLLM is faster than the current runtime;
7. select a permanent Novi foundation model before benchmarking;
8. lock final robot hardware around AirLLM;
9. introduce cloud inference as a dependency;
10. redesign memory semantics as part of the AirLLM integration.

---

# 3. Current Novi integration point

`novi/brain/engine.py` currently accepts a `ReasoningProvider` and defaults to `DeliberativeReasoningProvider()`. This is the most important existing seam for the first integration.

The implementation must first map the existing reasoning provider contract into a new runtime abstraction rather than replacing `engine.py` with direct AirLLM calls.

Target dependency direction:

```text
MacBrain
  |
  +--> ReasoningProvider-compatible adapter
          |
          +--> Novi InferenceRuntime
                  |
                  +--> ModelRouter
                  |
                  +--> BackendManager
                          |
                          +--> Existing backend
                          +--> AirLLMBackend
```

The first implementation must preserve all current behavior when AirLLM is disabled.

The default path must remain usable on the Mac prototype without requiring CUDA or AirLLM.

---

# 4. Required new architecture

Create a Novi-owned inference subsystem under the canonical `novi/brain/` namespace.

Recommended structure:

```text
novi/brain/inference/
├── __init__.py
├── contracts.py
├── runtime.py
├── request.py
├── response.py
├── errors.py
├── capabilities.py
├── registry.py
├── router.py
├── scheduler.py
├── lifecycle.py
├── cancellation.py
├── telemetry.py
├── health.py
├── backends/
│   ├── __init__.py
│   ├── base.py
│   ├── existing.py
│   └── airllm.py
├── airllm/
│   ├── __init__.py
│   ├── adapter.py
│   ├── loader.py
│   ├── shards.py
│   ├── cache.py
│   ├── process.py
│   └── compatibility.py
└── tests/
    ├── test_contracts.py
    ├── test_registry.py
    ├── test_router.py
    ├── test_scheduler.py
    ├── test_airllm_adapter.py
    ├── test_airllm_compatibility.py
    ├── test_airllm_lifecycle.py
    └── test_inference_runtime.py
```

Do not create a second top-level brain namespace. The existing repository explicitly establishes `novi/brain/` as canonical.

---

# 5. Phase 0 — Repository and dependency audit

Before writing implementation code:

### 5.1 Inventory all model calls

Search the entire repository for:

- `ReasoningProvider`;
- `DeliberativeReasoningProvider`;
- `generate`;
- `chat`;
- `completion`;
- model names;
- Ollama endpoints/processes;
- Hugging Face Transformers imports;
- `torch` model loading;
- tokenizer loading;
- `asyncio` model execution;
- subprocesses used for model serving;
- HTTP calls to local inference servers.

For each call record:

```text
caller
purpose
input shape
output shape
sync/async
latency expectation
streaming requirement
error behavior
current backend
```

### 5.2 Identify direct coupling

No cognitive module may continue adding direct backend calls after this workstream starts.

Any direct model invocation found must be classified as:

- retain temporarily;
- migrate to runtime;
- remove;
- test-only fixture.

### 5.3 Capture baseline

Before AirLLM is installed, record baseline measurements for each currently executable model/backend:

- startup time;
- first-token latency;
- generation latency;
- tokens/second;
- peak RAM;
- peak VRAM when applicable;
- CPU utilization;
- disk I/O;
- power if measurable;
- error rate;
- output correctness on a fixed prompt suite.

Store machine-readable results under the benchmark area rather than relying on screenshots or manually written claims.

Acceptance gate: no AirLLM performance claim may later be made without comparison to this baseline.

---

# 6. Phase 1 — Define the inference contracts

## 6.1 `InferenceRequest`

Create a typed immutable request contract.

Required fields:

```text
request_id
created_at
caller
purpose
model_policy
model_hint
messages/context
max_input_tokens
max_output_tokens
temperature
top_p
top_k (if supported)
stop_sequences
stream
priority
deadline
latency_budget
reasoning_budget
allow_background
conversation_id
mission_id
trace_id
```

Do not put backend-specific fields into the public contract.

If a backend needs a provider-specific option, represent it through a validated capability/options object that is explicitly marked backend-specific and never required by cognition.

## 6.2 Request priorities

At minimum:

```text
CRITICAL
HIGH
NORMAL
LOW
BACKGROUND
```

Important rule: inference priority must not override the deterministic safety system. A CRITICAL inference request still cannot directly authorize an action.

## 6.3 `InferenceResponse`

Required fields:

```text
request_id
model_id
backend_id
text
finish_reason
input_tokens
output_tokens
latency_ms
time_to_first_token_ms
generation_tokens_per_second
cache_status
hardware_profile_id
warnings
trace_id
```

Optional structured fields:

```text
tool_calls
reasoning_metadata
structured_output
provider_metadata
```

Provider metadata must be treated as diagnostic data, not truth.

## 6.4 Error taxonomy

Define stable Novi errors:

```text
InferenceError
InferenceConfigurationError
ModelNotFoundError
ModelUnavailableError
BackendUnavailableError
BackendInitializationError
ModelCompatibilityError
TokenizationError
ContextLimitError
DeadlineExceededError
InferenceCancelledError
OutOfMemoryError
StorageCapacityError
ShardIntegrityError
GenerationError
BackendProtocolError
```

AirLLM exceptions must be translated into these categories.

Never leak a raw AirLLM exception through `MacBrain`.

---

# 7. Phase 2 — Backend interface

Create a `InferenceBackend` protocol/abstract interface.

Required operations:

```text
backend_id()
capabilities()
validate_model(model_spec)
prepare(model_spec)
load(model_spec)
unload(model_spec)
generate(request)
stream(request)
health()
metrics()
shutdown()
```

Lifecycle must be explicit:

```text
REGISTERED
  -> VALIDATING
  -> PREPARING
  -> READY
  -> LOADING
  -> LOADED
  -> RUNNING
  -> DRAINING
  -> UNLOADED
  -> FAILED
```

The runtime must never assume a model is ready merely because its files exist.

---

# 8. Phase 3 — Model registry

Create a registry independent of AirLLM.

Each model specification must include:

```yaml
id: qwen3.8-27b
family: qwen3.8
role_candidates:
  - deep_reasoning
  - multimodal_reasoning
backend_preferences:
  - airllm
  - existing
source_type: huggingface
source_id: Qwen/Qwen3.8-27B
local_aliases:
  - qwen3.8:27b
context_limit: null
capabilities:
  text: true
  vision: true
  tool_calling: null
  structured_output: null
hardware_requirements: {}
status: candidate
```

Do not copy an Ollama tag into a Hugging Face identifier without an explicit mapping.

The current local model aliases are runtime-specific names. AirLLM requires a compatible Hugging Face model repository or local Hugging Face checkpoint path. The registry therefore needs an explicit mapping layer:

```text
local alias -> canonical model ID -> backend artifact
```

Never silently substitute a different checkpoint.

---

# 9. Phase 4 — Current model inventory

The initial registry must contain exactly the currently approved candidates and no additional model should become a production dependency without a documented adoption decision.

## 9.1 Qwen3 4B

Role candidate:

- lightweight reasoning;
- classification;
- intent parsing;
- simple dialogue;
- background summarization;
- cheap fallback.

AirLLM status: optional evaluation target, not mandatory.

Reason: its small size means the memory advantage of AirLLM may not justify the streaming/storage overhead.

## 9.2 Qwen3 8B

Role candidate:

- default general cognition;
- ordinary dialogue;
- lightweight planning;
- tool selection;
- context interpretation.

AirLLM status: benchmark only unless constrained hardware demonstrates a meaningful advantage.

## 9.3 Nemotron 3.5 Lightning

Role candidate:

- agentic planning;
- long-running task orchestration;
- tool-oriented reasoning;
- multi-step cognitive work.

Backend selection must be benchmark-driven.

Do not assume that the model's total parameter count determines its runtime behavior. Measure actual latency, memory, context behavior, tool calling, and reliability on Novi tasks.

AirLLM integration must not be declared compatible solely from family name. Compatibility is an execution result.

## 9.4 Qwen3.8 27B

Primary AirLLM evaluation target.

The current AirLLM project explicitly documents Qwen3.8-27B support and a reference VRAM figure around 3.33 GB. Upstream also documents the required modern Transformers stack for this model. Novi must nevertheless reproduce compatibility on the exact checkpoint and exact target hardware rather than trusting the upstream claim alone.

Use this model as the first end-to-end AirLLM target because it provides a meaningful test of memory reduction without immediately introducing a much larger future model.

## 9.5 Qwen3.8 latest

Do not assume the local tag corresponds to the 27B checkpoint.

The registry must require:

```text
exact resolved model ID
revision/hash when available
architecture
parameter count
modality
context limit
quantization
backend compatibility
```

It must not be admitted to the AirLLM production pool until those facts are resolved.

---

# 10. Phase 5 — AirLLM dependency isolation

Add AirLLM as an optional dependency, not a mandatory dependency of the base Novi Brain.

Preferred packaging behavior:

```text
core Novi installation
    -> no AirLLM requirement

Novi AirLLM extra
    -> installs tested AirLLM stack
```

Use a dedicated optional dependency group/extra according to the repository's existing packaging mechanism.

Pin or constrain versions according to the validated compatibility matrix.

AirLLM currently declares dependencies including Torch, Transformers, Accelerate, Safetensors, Hugging Face Hub and related packages. Its current package metadata constrains Transformers below 5.13. Novi must treat the AirLLM dependency set as an isolated compatibility surface rather than allowing arbitrary project-wide dependency upgrades.

Do not globally upgrade Transformers solely to satisfy AirLLM.

Create a compatibility lock/test matrix:

```text
Python
Torch
Transformers
Accelerate
Safetensors
AirLLM
OS
architecture
GPU backend
```

The matrix must be tested in CI where practical and on the actual Mac/NVIDIA target machines where CI cannot reproduce the hardware.

---

# 11. Phase 6 — AirLLM adapter

Implement `AirLLMBackend` behind `InferenceBackend`.

Responsibilities only:

1. resolve the canonical model artifact;
2. validate the architecture;
3. create/load AirLLM model;
4. configure shard directory;
5. configure optional compression;
6. configure prefetching;
7. tokenize input;
8. execute generation;
9. decode output;
10. translate errors;
11. collect telemetry;
12. unload resources cleanly.

The adapter must not contain:

- goal logic;
- planning logic;
- memory semantics;
- safety decisions;
- autonomy state transitions;
- relationship logic;
- action authorization.

---

# 12. Phase 7 — AirLLM model preparation pipeline

AirLLM may transform a model into layer-wise shards before inference. This must be treated as a managed deployment operation, not something that happens unpredictably during a live autonomy cycle.

Pipeline:

```text
Model manifest
  ↓
Artifact verification
  ↓
Disk capacity check
  ↓
Source checkpoint acquisition
  ↓
Checksum/revision record
  ↓
AirLLM shard preparation
  ↓
Shard integrity verification
  ↓
Manifest creation
  ↓
Warm-load test
  ↓
Generation smoke test
  ↓
Promote to READY
```

Preparation must happen before deployment into the live brain.

Do not allow first-ever model sharding to occur in a safety-critical or latency-sensitive autonomous loop.

---

# 13. Phase 8 — Shard storage management

Define a Novi-managed storage layout.

Recommended:

```text
$NOVI_DATA/
└── models/
    └── airllm/
        ├── manifests/
        ├── qwen3.8-27b/
        │   ├── source/
        │   ├── shards/
        │   ├── metadata.json
        │   ├── manifest.json
        │   └── health.json
        └── future-model/
```

Do not place large model artifacts inside the Git repository.

The manifest must record:

```text
model ID
revision
source
architecture
AirLLM version
Transformers version
Torch version
shard count
shard sizes
total bytes
checksum information
creation timestamp
hardware used for validation
compression mode
prefetch mode
status
```

---

# 14. Phase 9 — Storage safety

Before preparing a model, calculate:

```text
required source storage
+ temporary transformation storage
+ shard storage
+ safety reserve
```

AirLLM's own documentation warns that model splitting can be very disk intensive and that insufficient storage can produce safetensors errors. Novi must therefore fail early with a typed `StorageCapacityError`.

Required behavior:

```text
insufficient disk
    -> refuse preparation
    -> emit diagnostic
    -> do not delete anything
```

Deletion of original checkpoints must never be automatic during the first adoption phase.

Only after verified recovery and restore procedures exist may `delete_original` become an explicit administrative option.

---

# 15. Phase 10 — Model integrity

For every prepared model:

1. record upstream revision;
2. record local file hashes where practical;
3. verify all expected shard files exist;
4. verify no unexpected missing layer exists;
5. load tokenizer;
6. run a deterministic smoke prompt;
7. compare generated output format;
8. mark manifest healthy only after all checks pass.

A partially prepared model must never be selected by the router.

---

# 16. Phase 11 — Device abstraction

AirLLM must not assume CUDA everywhere.

Create a `HardwareProfile` containing:

```text
platform
OS
CPU model
CPU cores
RAM total
RAM available
GPU vendor
GPU model
VRAM total
VRAM available
compute backend
storage type
storage free space
thermal state if available
power state if available
```

The runtime must distinguish:

```text
supported
unsupported
unknown
```

Never turn `unknown` into `supported` by assumption.

The Mac prototype is an important validation target because the repository explicitly treats Mac as the current development platform. AirLLM's upstream documentation has Apple Silicon/MacOS guidance, but Novi must execute a representative workload on the actual development machine before declaring the backend Mac-compatible.

---

# 17. Phase 12 — Mac-first validation

The first AirLLM implementation must not disturb the current Mac Brain milestone.

Acceptance sequence:

```text
Current Mac Brain tests green
        ↓
Inference abstraction introduced
        ↓
Current backend still green
        ↓
AirLLM installed in isolated environment
        ↓
AirLLM import smoke test
        ↓
Qwen3.8-27B model preparation
        ↓
single prompt
        ↓
Novi reasoning provider
        ↓
full cognition cycle
```

If AirLLM cannot run on the actual Mac, the backend remains an implemented but platform-blocked provider. The rest of Novi must remain fully functional.

---

# 18. Phase 13 — Runtime lifecycle

The runtime must control model lifecycle.

States:

```text
UNKNOWN
REGISTERED
VALIDATING
PREPARING
READY
LOADING
LOADED
RUNNING
DRAINING
UNLOADED
DEGRADED
FAILED
```

Transitions must be validated.

Examples:

```text
FAILED -> RUNNING
```

is forbidden.

```text
READY -> LOADING -> LOADED -> RUNNING
```

is valid.

Shutdown must be idempotent.

---

# 19. Phase 14 — Warm and cold execution

Measure separately:

### Cold path

```text
process start
→ backend initialization
→ model load
→ first generation
```

### Warm path

```text
model already prepared
→ request
→ generation
```

### Re-load path

```text
model A
→ unload
→ model B
→ generation
```

### Recovery path

```text
model load failure
→ cleanup
→ health check
→ fallback model
```

Novi's router must know which path is being used when evaluating latency.

---

# 20. Phase 15 — Scheduler

Introduce a scheduler between the router and backend.

The scheduler must prevent competing large-model requests from exhausting resources.

Inputs:

```text
priority
deadline
estimated memory
estimated duration
model residency
current load
```

Queue classes:

```text
CRITICAL
HIGH
NORMAL
LOW
BACKGROUND
```

The scheduler must support cancellation.

If a high-priority request arrives while a background deep-reasoning request is running, the runtime must be able to apply a configured policy:

- wait;
- queue;
- cancel background request;
- switch model;
- use a smaller fallback.

Do not implement preemption until the backend lifecycle is proven safe. Start with cooperative cancellation at request boundaries.

---

# 21. Phase 16 — Deadline-aware routing

Every inference request should carry a latency budget.

Example policy:

```text
interactive dialogue: short
normal planning: medium
complex deliberation: long
reflection: background
```

The router must not select AirLLM for a request whose deadline it cannot plausibly meet according to recent telemetry.

A deadline miss must be represented explicitly rather than silently treated as success.

---

# 22. Phase 17 — Model router

The router is Novi-owned and backend-neutral.

Inputs:

```text
task type
reasoning complexity
context length
required modality
required tool capability
latency budget
available RAM
available VRAM
thermal state
power mode
current model residency
backend health
historical performance
```

Output:

```text
model
backend
execution mode
reason
confidence
```

The router must record why a model was selected.

Example:

```json
{
  "model": "qwen3.8-27b",
  "backend": "airllm",
  "reason": "deep_reasoning + available constrained VRAM",
  "fallback": "qwen3-8b"
}
```

This is an auditable decision, not hidden heuristic behavior.

---

# 23. Phase 18 — Initial model policy

Do not permanently assign model roles until benchmarking is complete.

Initial hypotheses for evaluation only:

```text
qwen3:4b
  -> lightweight/default fallback

qwen3:8b
  -> general cognition candidate

nemotron-3.5-lightning:latest
  -> agentic planning/tool-use candidate

qwen3.8:27b
  -> deep reasoning candidate

qwen3.8:latest
  -> unresolved until exact artifact identity/capabilities are recorded
```

These are routing hypotheses, not permanent architecture facts.

The benchmark suite must be able to overturn them.

---

# 24. Phase 19 — Context management

The inference runtime must receive a bounded context package rather than directly reading all Novi memory.

Flow:

```text
Memory
  ↓
Attention / retrieval
  ↓
ContextAssembler
  ↓
InferenceRequest
  ↓
Tokenizer
  ↓
Backend
```

This preserves the existing Novi distinction between memory semantics and model context.

The model must not become the source of truth for persistent memory.

---

# 25. Phase 20 — Token accounting

Track:

```text
input tokens
output tokens
context tokens
truncated tokens
estimated context utilization
```

Before generation:

```text
context estimate
→ compare against model limit
→ compress/retrieve less if necessary
→ reject only when safe fallback is impossible
```

Do not allow accidental context overflow to crash the autonomy loop.

---

# 26. Phase 21 — Streaming

Implement streaming as an optional runtime capability.

AirLLM must expose streaming only if the actual backend behavior supports safe incremental output.

Cognition must not depend on streaming.

Streaming is for:

- user-facing dialogue;
- incremental UI;
- telemetry;
- cancellation.

Planning/action execution must consume a validated final response or structured result.

Never execute an action because a partial token stream happens to contain an apparent command.

---

# 27. Phase 22 — Structured output

The inference runtime must support validated structured outputs where the backend/model supports them.

For Novi:

```text
LLM output
  ↓
parse
  ↓
schema validation
  ↓
semantic validation
  ↓
governance
  ↓
action proposal
```

AirLLM itself must not be responsible for governance validation.

---

# 28. Phase 23 — Tool calls

Tool calls must be represented as proposals.

```text
Model
 ↓
ToolCallProposal
 ↓
Schema validation
 ↓
Authority check
 ↓
Safety check
 ↓
Execution
 ↓
Observation
 ↓
Verification
```

The AirLLM backend must simply return the model output/tool-call representation.

---

# 29. Phase 24 — Safety boundary

Non-negotiable rule:

> AirLLM cannot directly command the body.

The allowed path remains:

```text
LLM
 ↓
Reasoning result
 ↓
Planner
 ↓
ActionProposal
 ↓
GovernanceGuard
 ↓
Safety boundary
 ↓
SkillExecutor
 ↓
Virtual/physical body
```

AirLLM must never receive credentials, motor-controller authority, safety override capability, or unrestricted hardware APIs.

---

# 30. Phase 25 — Fallback strategy

The runtime must have a deterministic fallback policy.

Example:

```text
AirLLM unavailable
    ↓
try approved local backend
    ↓
smaller approved model
    ↓
structured deterministic behavior
    ↓
ask for help / defer
```

Fallback must never silently change a high-risk action's authority.

For a task requiring deep reasoning, using a smaller model may produce a lower-confidence result. That confidence must be represented and may require re-planning or human confirmation.

---

# 31. Phase 26 — Failure handling

Test at minimum:

1. AirLLM import failure;
2. missing model;
3. missing tokenizer;
4. incomplete shards;
5. corrupt shard;
6. insufficient disk;
7. insufficient RAM;
8. insufficient VRAM;
9. model load timeout;
10. generation timeout;
11. process crash;
12. CUDA/MPS initialization failure;
13. Transformers incompatibility;
14. unsupported architecture;
15. context overflow;
16. cancellation;
17. malformed output;
18. backend hangs;
19. repeated failures;
20. storage becomes full during operation.

Every failure needs:

```text
classification
logging
metric
recovery policy
user/operator visibility
```

---

# 32. Phase 27 — Process isolation

The first AirLLM implementation may run in-process only if resource cleanup is proven reliable.

If model lifecycle or memory fragmentation makes this unsafe, introduce an isolated worker process:

```text
Novi Brain
   |
   v
Inference Worker
   |
   v
AirLLM
```

Worker responsibilities:

- load model;
- accept inference RPC;
- return response;
- report health;
- release resources;
- terminate on fatal corruption.

Do not introduce a process boundary prematurely if it makes the Mac prototype substantially harder to debug. Keep the interface compatible with either in-process or worker execution.

---

# 33. Phase 28 — Resource telemetry

Integrate with existing Novi `ResourceTelemetry`, diagnostics, health and metric infrastructure visible in `novi/brain/engine.py`.

Every inference call should emit:

```text
request_id
model_id
backend_id
start_time
end_time
queue_time
load_time
TTFT
generation_time
input_tokens
output_tokens
tokens_per_second
RAM before/after
VRAM before/after if available
disk read bytes if available
failure class
fallback used
```

Do not log prompts by default when they may contain private user information. Store only the minimum content required for debugging and audit, using existing Novi privacy/governance policies.

---

# 34. Phase 29 — Benchmark suite

Create `novi/brain/tests/` and a benchmark area under the existing documentation/plans structure.

Benchmarks must cover both infrastructure and cognitive quality.

## Infrastructure benchmarks

- cold start;
- warm request;
- reload;
- model switch;
- first token;
- tokens/sec;
- peak memory;
- disk throughput;
- repeated requests;
- long context;
- cancellation;
- failure recovery.

## Novi cognitive benchmarks

- dialogue;
- instruction following;
- scene interpretation supplied as text/structured input;
- spatial reasoning;
- task decomposition;
- planning;
- replanning;
- tool selection;
- tool argument generation;
- uncertainty expression;
- memory-grounded answer;
- contradiction handling;
- refusal of unauthorized actions;
- recovery after failed tool execution.

---

# 35. Phase 30 — AirLLM vs current backend comparison

For Qwen3.8-27B, compare:

```text
existing/native backend
vs
AirLLM
```

Use exactly the same:

- model revision;
- prompt suite;
- tokenizer;
- generation settings;
- hardware;
- temperature;
- max output tokens.

Report:

```text
quality delta
TTFT delta
throughput delta
peak VRAM delta
peak RAM delta
disk IO delta
startup delta
failure rate delta
```

No adoption decision may be made from VRAM alone.

---

# 36. Phase 31 — Quality regression protection

Create golden tests for outputs that have deterministic structured requirements.

Do not compare free-form text with exact string equality unless the task is explicitly deterministic.

Instead validate:

- schema validity;
- required fields;
- tool name;
- argument correctness;
- safety classification;
- plan validity;
- completion criteria.

Track quality regressions separately from latency regressions.

---

# 37. Phase 32 — Model capability matrix

Create a machine-readable capability matrix:

```yaml
model: qwen3.8-27b
backend: airllm
status: evaluating
capabilities:
  text_generation: true
  vision: true
  tool_calling: unknown
  structured_output: unknown
  streaming: unknown
hardware:
  mac_apple_silicon: unknown
  cuda: unknown
```

Every `true` capability must have evidence.

Every `unknown` capability is unavailable to the router until validated.

---

# 38. Phase 33 — Compatibility testing

Test combinations explicitly.

At minimum:

```text
AirLLM version
Transformers version
Torch version
Python version
Qwen3.8-27B revision
Mac/MPS
NVIDIA/CUDA when available
```

For every failure, capture:

```text
environment
model
backend version
stack trace
reproduction command
expected result
actual result
workaround if any
```

Do not hide compatibility workarounds inside random runtime conditionals. Put them behind a documented compatibility layer.

---

# 39. Phase 34 — AirLLM-specific configuration

Novi configuration should expose only safe semantic settings.

Example:

```yaml
inference:
  default_backend: existing
  airllm:
    enabled: false
    model_root: ${NOVI_DATA}/models/airllm
    prefetching: true
    compression: none
    delete_original: false
    preparation_allowed: false
    max_concurrent_requests: 1
    worker_mode: in_process
```

Important defaults:

```text
enabled = false until validated
compression = none initially
delete_original = false
preparation_allowed = false in live runtime
max_concurrent_requests = 1
```

The first production phase should be conservative.

---

# 40. Phase 35 — Compression evaluation

AirLLM supports optional 4-bit and 8-bit block-wise compression.

Do not enable this during initial compatibility validation.

First establish:

```text
full precision/reference
```

Then separately benchmark:

```text
8-bit
4-bit
```

Measure:

- quality;
- latency;
- storage;
- VRAM;
- CPU/RAM;
- task success.

Adopt compression only if the evidence shows a meaningful Novi benefit with acceptable quality degradation.

---

# 41. Phase 36 — Prefetch evaluation

AirLLM supports prefetching to overlap model loading and computation for supported paths.

Test:

```text
prefetch=false
prefetch=true
```

Measure:

- layer load latency;
- end-to-end generation;
- disk queue depth;
- CPU utilization;
- RAM;
- thermal impact.

Do not assume upstream speedup numbers transfer directly to Novi hardware.

---

# 42. Phase 37 — Model residency policy

Do not keep every model loaded.

Define residency states:

```text
NOT_PREPARED
PREPARED
COLD
WARM
ACTIVE
DRAINING
```

The router may prefer a slightly less capable model if switching to a cold giant model would violate the request deadline.

Residency becomes part of routing cost.

---

# 43. Phase 38 — Model switching

Test:

```text
Qwen 8B
→ Nemotron
→ Qwen 27B
→ Qwen 8B
```

Verify:

- no leaked memory;
- no stale tokenizer;
- no stale KV state;
- no cross-model conversation corruption;
- no incorrect model metadata in telemetry.

A request must always be tagged with the exact model actually used.

---

# 44. Phase 39 — Context and cache isolation

Never reuse a KV cache across:

- different models;
- incompatible tokenizer revisions;
- different conversations;
- different security/authority contexts.

Cache keys must include sufficient identity:

```text
model revision
backend
tokenizer revision
conversation/session
context hash
runtime configuration
```

---

# 45. Phase 40 — Privacy and audit

AirLLM is local infrastructure, which supports Novi's local/offline-first principle, but local does not mean automatically safe.

Audit:

- model artifact provenance;
- local file permissions;
- Hugging Face credentials if used;
- logs;
- prompts;
- generated outputs;
- temporary files;
- caches.

Never put Hugging Face tokens into repository configuration.

Use environment/secret management already approved by the project.

---

# 46. Phase 41 — Security of model artifacts

Treat model files as untrusted external artifacts until verified.

Record:

```text
source
revision
hashes
license
download time
operator
```

Do not execute arbitrary code from model repositories without reviewing the loading mechanism and required `trust_remote_code` behavior.

Prefer model architectures supported directly by the validated Transformers stack.

---

# 47. Phase 42 — Offline operation

After model preparation, Novi must be able to execute inference without Internet access.

Test:

```text
network disabled
↓
model already prepared
↓
Novi inference
↓
successful generation
```

If a runtime unexpectedly attempts network access during normal inference, classify this as an integration defect.

---

# 48. Phase 43 — Brain integration

Modify `MacBrain` only through dependency injection.

Current pattern:

```python
self.reasoning = reasoning or DeliberativeReasoningProvider()
```

Target pattern:

```text
MacBrain
  receives ReasoningProvider
       |
       +-- existing provider
       +-- runtime-backed provider
```

Do not make `MacBrain` instantiate `AirLLMBackend` directly.

A future constructor may accept an `InferenceRuntime`, but the brain should not know which backend implements it.

---

# 49. Phase 44 — Existing reasoning compatibility

Create an adapter around the existing reasoning contract.

Responsibilities:

```text
existing reasoning request
      ↓
InferenceRequest
      ↓
InferenceRuntime
      ↓
InferenceResponse
      ↓
existing reasoning response
```

This allows all current cognition tests to remain valid while the backend changes underneath.

---

# 50. Phase 45 — Autonomy integration

Autonomy modules should request cognitive work through semantic operations such as:

```text
reason
plan
interpret
summarize
choose
reflect
```

They should not request:

```text
run_airllm
load_qwen27b
stream_layer
```

The latter are runtime implementation details.

---

# 51. Phase 46 — Deliberation levels

Define semantic reasoning levels:

```text
FAST
NORMAL
DELIBERATE
DEEP
```

Map them to models/backends through policy.

Initial hypothesis:

```text
FAST       -> Qwen3 4B
NORMAL     -> Qwen3 8B
DELIBERATE -> Nemotron 3.5 Lightning
DEEP       -> Qwen3.8 27B / AirLLM
```

These mappings remain provisional until Novi-Bench validates them.

---

# 52. Phase 47 — Background reasoning

Deep AirLLM inference is especially suitable for non-real-time work if benchmarks show acceptable resource use.

Examples:

- post-mission reflection;
- difficult plan generation;
- knowledge synthesis;
- long-horizon scenario analysis;
- offline skill improvement proposals.

Background inference must yield to safety-critical workloads.

---

# 53. Phase 48 — Real-time boundary

AirLLM must not sit in the hard real-time control loop.

Hard real-time path:

```text
sensor
→ perception/control
→ deterministic safety
→ motor control
```

Soft cognitive path:

```text
world state
→ model reasoning
→ plan proposal
→ validation
→ skill execution
```

AirLLM belongs only in the second path.

---

# 54. Phase 49 — Simulation validation

Before any AirLLM-backed reasoning can influence physical action:

```text
AirLLM
 ↓
Novi planner
 ↓
simulation
 ↓
verification
```

Run the same inference request suite against virtual and future physical interfaces.

The model backend must be replaceable without changing the simulation contract.

---

# 55. Phase 50 — Long-running soak tests

Run at least:

```text
1 hour
4 hours
8 hours
24 hours when hardware permits
```

Track:

- memory growth;
- disk usage;
- shard corruption;
- model reload failures;
- latency drift;
- thermal behavior;
- repeated generation failures;
- scheduler starvation;
- stale state.

A backend is not production-ready merely because one prompt succeeds.

---

# 56. Phase 51 — Failure injection

Deliberately inject:

```text
remove shard
corrupt shard
fill disk
kill worker
interrupt generation
force OOM
break tokenizer
kill network
restart runtime
restart Mac
```

Expected outcome:

```text
failure detected
→ classified
→ resources cleaned
→ fallback selected
→ autonomy remains bounded
```

---

# 57. Phase 52 — Observability dashboard

Expose runtime metrics through existing Novi diagnostics rather than creating an independent monitoring system.

Required views:

```text
Current model
Current backend
Model state
Queue depth
Active requests
TTFT
Tokens/sec
RAM
VRAM
Disk
Failures
Fallback count
Model switches
```

---

# 58. Phase 53 — Evidence artifacts

Every milestone must produce machine-readable evidence.

Recommended artifacts:

```text
benchmarks/
  hardware-profile.json
  qwen3.8-27b-airllm.json
  qwen3.8-27b-baseline.json
  compatibility-matrix.json
  soak-test.json
  failure-injection.json
```

The evidence must include timestamps and software/model versions.

---

# 59. Phase 54 — Acceptance gates

## Gate A — Contract

PASS when:

- inference contract exists;
- existing reasoning path uses it;
- no cognition module imports AirLLM.

## Gate B — AirLLM smoke

PASS when:

- AirLLM imports;
- Qwen3.8-27B prepares;
- one generation succeeds;
- model metadata is recorded.

## Gate C — Novi integration

PASS when:

- `MacBrain` can use AirLLM through dependency injection;
- existing tests remain green;
- no safety boundary changes.

## Gate D — Benchmark

PASS when:

- AirLLM and baseline are compared;
- quality and performance evidence exists.

## Gate E — Failure recovery

PASS when:

- all critical failure cases are handled;
- fallback behavior is verified.

## Gate F — Long-running

PASS when:

- soak test succeeds;
- no unacceptable resource leak exists.

## Gate G — Production candidate

PASS only when:

- all previous gates pass;
- exact model revision is recorded;
- exact software versions are recorded;
- hardware profile is recorded;
- rollback procedure is tested;
- documentation is complete.

---

# 60. Phase 55 — Rollback

Rollback must be one configuration change, not a source-code rewrite.

Example semantic policy:

```text
backend = existing
```

must disable AirLLM while preserving the same inference contract.

Rollback triggers:

- repeated backend failures;
- latency regression;
- quality regression;
- memory instability;
- thermal issues;
- storage corruption;
- incompatible dependency update.

---

# 61. Phase 56 — Future large-model readiness

Once the abstraction is stable, larger models may be added without changing cognition.

Future flow:

```text
new model
 ↓
registry
 ↓
compatibility test
 ↓
AirLLM preparation
 ↓
benchmark
 ↓
router eligibility
```

No future model is automatically production-enabled merely because AirLLM claims support.

---

# 62. Phase 57 — Alternative backends

The runtime must remain capable of adding future backends such as:

```text
Transformers
vLLM
TensorRT-LLM
llama.cpp
other validated local runtime
```

These are future implementation options, not current requirements.

The contract must therefore avoid backend-specific assumptions such as:

- CUDA-only tensors;
- Transformers-only tokenizer APIs;
- AirLLM-specific shard names;
- HTTP-only execution;
- process-only execution.

---

# 63. Phase 58 — NVIDIA transition

When Novi moves from Mac development to NVIDIA hardware:

1. capture the new hardware profile;
2. install a validated runtime environment;
3. benchmark existing model paths;
4. benchmark AirLLM;
5. compare against optimized NVIDIA serving backends;
6. update routing policy only from evidence;
7. keep semantic contracts unchanged.

The final NVIDIA stack must be selected based on the measured workload, consistent with Novi's existing hardware policy.

---

# 64. Phase 59 — Performance decision framework

AirLLM is adopted for a specific model/backend/hardware combination only if it provides a meaningful system-level advantage.

Use a weighted decision:

```text
cognitive quality
latency
VRAM reduction
RAM usage
storage overhead
power
reliability
operational complexity
maintenance burden
```

A large VRAM reduction does not automatically win if it makes an interactive cognitive workload unusably slow.

---

# 65. Phase 60 — Documentation changes

Update/create:

```text
docs/plans/06_AUTONOMY/12_AIRLLM_ADAPTATION_AND_INFERENCE_RUNTIME_PLAN.md

docs/specs/brain/<inference-runtime-spec>.md

docs/specs/brain/<model-compatibility-matrix>.md

docs/specs/brain/<runtime-benchmark-spec>.md
```

Also update the autonomy implementation index to reference this workstream.

Do not claim AirLLM is implemented until code and evidence exist.

Use the repository's existing status vocabulary:

```text
DESIGNED
PROPOSED
EVALUATING
PROTOTYPE
IMPLEMENTED
TESTED
INTEGRATED
SIMULATED
DEFERRED
BLOCKED
DEPRECATED
```

Initial status should be `PROPOSED`/`EVALUATING`.

---

# 66. Exact implementation sequence

The implementation must proceed in this order.

### Step 1
Audit all existing inference/model calls.

### Step 2
Capture baseline benchmarks.

### Step 3
Define `InferenceRequest` and `InferenceResponse`.

### Step 4
Define stable inference error taxonomy.

### Step 5
Define `InferenceBackend`.

### Step 6
Implement a mock backend.

### Step 7
Move existing reasoning provider behind the runtime.

### Step 8
Run the complete existing Brain test suite.

### Step 9
Implement model registry.

### Step 10
Register the five current model aliases without enabling new routing automatically.

### Step 11
Implement hardware capability detection.

### Step 12
Implement runtime lifecycle.

### Step 13
Implement scheduler and request cancellation.

### Step 14
Implement telemetry.

### Step 15
Add AirLLM as an optional dependency.

### Step 16
Create AirLLM compatibility adapter.

### Step 17
Resolve the exact Hugging Face artifact corresponding to `qwen3.8:27b`.

### Step 18
Prepare Qwen3.8-27B into AirLLM shards outside the live Brain loop.

### Step 19
Verify shard integrity.

### Step 20
Run single-prompt AirLLM smoke test.

### Step 21
Run tokenizer/context tests.

### Step 22
Run repeated warm inference.

### Step 23
Integrate AirLLM backend through the existing reasoning provider seam.

### Step 24
Run complete Brain regression suite.

### Step 25
Run Novi cognitive benchmark suite.

### Step 26
Compare AirLLM against the baseline backend.

### Step 27
Test failure recovery.

### Step 28
Test model unload/reload.

### Step 29
Test offline operation.

### Step 30
Run long-duration soak tests.

### Step 31
Evaluate compression separately.

### Step 32
Evaluate prefetching separately.

### Step 33
Implement router eligibility rules.

### Step 34
Enable AirLLM only for explicitly validated model/hardware combinations.

### Step 35
Add fallback and rollback configuration.

### Step 36
Update documentation and evidence.

### Step 37
Only then mark the backend `TESTED`/`INTEGRATED`.

---

# 67. Exact first production target

The first production-like AirLLM target is:

```text
Model:
    Qwen3.8-27B

Backend:
    AirLLM

Purpose:
    deep/deliberative reasoning

Execution:
    local/offline

Default concurrency:
    1

Compression:
    disabled initially

Prefetch:
    benchmarked, not assumed

Original checkpoint deletion:
    disabled

Real-time motor control:
    prohibited

Router status:
    disabled until validation
```

This gives Novi one concrete target without contaminating the architecture with an irreversible decision.

---

# 68. Definition of done

The AirLLM adaptation is complete only when all of the following are true:

### Architecture

- [ ] inference abstraction exists;
- [ ] backend interface exists;
- [ ] AirLLM is behind the interface;
- [ ] cognition does not import AirLLM;
- [ ] autonomy does not import AirLLM;
- [ ] safety does not import AirLLM.

### Current models

- [ ] all five approved current model aliases are represented in the registry;
- [ ] exact artifact identity is recorded for each enabled model;
- [ ] no unverified model is routable.

### AirLLM

- [ ] dependency isolation is implemented;
- [ ] compatibility matrix exists;
- [ ] Qwen3.8-27B preparation works;
- [ ] shards are integrity checked;
- [ ] cold inference works;
- [ ] warm inference works;
- [ ] unload works;
- [ ] reload works;
- [ ] cancellation works or is explicitly unsupported and safely bounded;
- [ ] errors are translated;
- [ ] telemetry works.

### Novi integration

- [ ] `MacBrain` remains model/backend agnostic;
- [ ] existing reasoning behavior remains functional;
- [ ] memory remains outside the model;
- [ ] planning remains outside the model;
- [ ] governance remains outside the model;
- [ ] safety remains outside the model;
- [ ] action verification remains outside the model.

### Performance

- [ ] baseline exists;
- [ ] AirLLM benchmark exists;
- [ ] quality comparison exists;
- [ ] latency comparison exists;
- [ ] memory comparison exists;
- [ ] storage impact is measured;
- [ ] power/thermal impact is measured where hardware permits.

### Reliability

- [ ] failure injection passes;
- [ ] fallback passes;
- [ ] rollback passes;
- [ ] offline test passes;
- [ ] soak test passes.

### Documentation

- [ ] plan updated;
- [ ] inference specification updated;
- [ ] compatibility matrix updated;
- [ ] benchmark evidence committed;
- [ ] implementation status updated;
- [ ] autonomy index updated.

---

# 69. Final Novi architecture after adoption

The resulting architecture should be:

```text
                           NOVI BRAIN
                               |
        +----------------------+----------------------+
        |                                             |
   Cognition                                      Autonomy
        |                                             |
        +----------------------+----------------------+
                               |
                       Semantic reasoning
                               |
                       Inference Runtime
                               |
              +----------------+----------------+
              |                                 |
          Model Router                     Scheduler
              |                                 |
              +----------------+----------------+
                               |
                       Backend Interface
                               |
              +----------------+----------------+
              |                |                |
          Existing         AirLLM          Future backend
          backend             |             (optional)
                              |
                       Qwen3.8-27B
                              |
                    layer/expert streaming
                              |
                       local storage
                              |
                    CPU / RAM / GPU
```

The critical property is that **Novi's intelligence remains above the runtime**.

AirLLM is a mechanism for executing a model under constrained resources. It is not the definition of Novi's cognition.

---

# 70. Architectural invariants

These rules must remain true after implementation:

1. Novi cognition never imports AirLLM.
2. AirLLM never controls physical actuation.
3. The model router never bypasses governance.
4. The model never becomes the persistent source of truth.
5. A model response never proves that an action succeeded.
6. Model selection is observable.
7. Backend selection is observable.
8. Model identity and revision are observable.
9. Failures are typed and recoverable.
10. AirLLM can be disabled without recompiling cognition.
11. A future backend can replace AirLLM without changing cognition contracts.
12. A future larger model can be added through registry + validation rather than architecture changes.
13. Core Novi operation remains locally capable and offline-capable.
14. The final physical hardware remains a measured consequence of workload.
15. Every production claim is backed by execution evidence.

---

# 71. Immediate next actions

The next implementation work should **not** begin by installing AirLLM into the existing Brain.

Do this first:

```text
1. Audit current inference seams.
2. Define the Novi inference contracts.
3. Wrap the existing reasoning provider.
4. Preserve all existing tests.
5. Add model registry.
6. Add backend abstraction.
7. Add telemetry.
8. Only then add AirLLM.
9. Use Qwen3.8-27B as the first AirLLM target.
10. Benchmark before changing routing policy.
```

This sequence protects the existing executable Mac Brain while creating the abstraction required for future local models, AirLLM, NVIDIA runtimes, and substantially larger models.

---

## References

- AirLLM repository and current documentation: https://github.com/lyogavin/airllm
- AirLLM base streaming implementation: https://github.com/lyogavin/airllm/blob/main/air_llm/airllm/airllm_base.py
- Qwen3.8 official repository/model documentation: https://github.com/QwenLM/Qwen3.8
- Novi repository: https://github.com/GiannisGlp/Novi
- Novi autonomy implementation index: `docs/plans/06_AUTONOMY/00_AUTONOMY_IMPLEMENTATION_INDEX.md`
- Novi Brain implementation: `novi/brain/`

External-source claims must be revalidated at implementation time because model support, dependency versions, and hardware support can change.
