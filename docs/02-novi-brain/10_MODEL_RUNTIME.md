# 10 — Novi Model Runtime

**Status:** P0 — critical architecture specification  
**Scope:** execution of learned models inside Novi's brain  
**Parent:** `06_NEURAL_NETWORK_STRATEGY.md`, `07_MODEL_TAXONOMY.md`, `08_MODEL_ROUTING_AND_SELECTION.md`, `09_MODEL_LIFECYCLE.md`  
**Authority:** Novi architecture; NVIDIA documentation is used to validate NVIDIA-specific runtime capabilities, not to define Novi semantics.

---

## 1. Purpose

The model runtime is the execution layer between the Brain Orchestrator and deployed model artifacts.

It answers:

- where a model executes;
- how it is loaded;
- how inputs are prepared;
- how inference is scheduled;
- how memory is allocated;
- how concurrent requests are handled;
- how latency deadlines are enforced;
- how model state is isolated;
- how failures are detected and contained;
- how resources are measured;
- how inference is observed and audited;
- how a model is unloaded, replaced or rolled back.

The runtime must make models **replaceable implementation components**, not architectural authorities.

---

# 2. Fundamental boundary

```text
Brain Orchestrator
        │
        │ ModelInvocation
        ▼
Novi Model Runtime Contract
        │
        ├── Model Registry / Artifact Resolver
        ├── Admission Controller
        ├── Scheduler
        ├── Execution Worker
        ├── Memory Manager
        ├── Runtime Adapter
        ├── Health Monitor
        └── Telemetry / Audit
                │
                ▼
        Model Backend
        ├── TensorRT
        ├── ONNX Runtime
        ├── PyTorch/runtime
        ├── Triton
        ├── specialized speech runtime
        └── other approved backend
                │
                ▼
              Hardware
```

A model must never receive unrestricted access to:

- motors;
- safety systems;
- durable semantic memory;
- credentials;
- arbitrary filesystem paths;
- arbitrary network access;
- deployment configuration.

Those capabilities remain outside the model runtime.

---

# 3. Runtime responsibilities

The runtime owns:

1. artifact resolution;
2. compatibility checking;
3. model loading;
4. warm-up;
5. input/output validation;
6. execution scheduling;
7. concurrency control;
8. memory/resource accounting;
9. deadline enforcement;
10. health checks;
11. timeout/cancellation handling;
12. backend-specific optimization;
13. metrics/tracing;
14. model unload/reload;
15. runtime isolation;
16. deterministic provenance of each invocation.

The runtime does **not** own:

- goal selection;
- personality;
- memory semantics;
- truth/knowledge authority;
- action authorization;
- physical safety policy;
- final robot control.

---

# 4. Runtime profiles

Novi should support multiple execution profiles because not every model should run in the same process or with the same scheduling policy.

## 4.1 Always-on profile

For low-latency continuous models:

- visual detection;
- tracking;
- VAD;
- acoustic event detection;
- health/anomaly models.

Requirements:

- bounded latency;
- predictable resource use;
- no unbounded queues;
- graceful degradation;
- automatic recovery.

## 4.2 Interactive profile

For user-facing inference:

- ASR;
- dialogue;
- VLM interpretation;
- TTS;
- interaction reasoning.

Requirements:

- responsiveness;
- interruption;
- cancellation;
- streaming where supported;
- priority over background workloads.

## 4.3 Deliberative profile

For expensive reasoning/planning/prediction:

- long-horizon reasoning;
- complex planning;
- world-model rollouts;
- scenario comparison.

Requirements:

- explicit compute budget;
- deadline;
- cancellation;
- checkpointable state where appropriate;
- never block safety or basic perception.

## 4.4 Embodied policy profile

For VLA/policy inference:

- fixed action representation;
- strict input/output schema;
- fixed control rate requirements;
- action horizon;
- embodiment compatibility;
- safety validation before deployment.

A policy runtime must not directly bypass the approved robot-control interface.

## 4.5 Background profile

For:

- embedding generation;
- memory consolidation;
- evaluation;
- dataset processing;
- model preparation;
- offline learning.

Background work is preemptible and must never starve interactive, reactive or safety-critical workloads.

---

# 5. Runtime request contract

Every inference invocation should contain, at minimum:

```text
invocation_id
model_id
model_version
artifact_digest
runtime_backend
runtime_version
input_schema_version
requested_output_schema
priority
deadline
cancellation_token
context_reference
correlation_id
trace_id
resource_class
privacy_classification
safety_classification
```

The runtime must reject requests that are incompatible with the deployed model contract.

---

# 6. Input handling

The runtime must validate before execution:

- modality;
- tensor/data type;
- dimensions;
- shape range;
- sampling rate;
- timestamp validity;
- calibration/version where applicable;
- schema version;
- maximum payload size;
- freshness/deadline;
- provenance requirements.

Invalid input must result in an explicit structured failure, not silent coercion where coercion could alter meaning.

---

# 7. Output handling

Every model output must be validated before returning to the orchestrator.

Validate:

- schema;
- type;
- dimensions;
- required fields;
- confidence range;
- timestamps;
- model identity;
- artifact identity;
- execution status;
- uncertainty metadata where supported.

Malformed output is a model/runtime failure.

It must never be treated as valid evidence merely because the model returned bytes.

---

# 8. Scheduling

The runtime scheduler should use explicit priority classes rather than implicit process ordering.

Suggested classes:

```text
P0  safety / emergency support
P1  immediate perception / reaction
P2  active interaction
P3  navigation / active task cognition
P4  deliberation / prediction
P5  background learning / maintenance
```

P0 safety mechanisms should remain outside the adaptive model runtime wherever possible.

The runtime must prevent priority inversion from allowing background inference to block urgent interaction/perception.

---

# 9. Deadlines

Each invocation has a deadline appropriate to its cognitive role.

A request that misses its deadline is not equivalent to a successful late response.

Possible outcomes:

```text
completed_on_time
completed_late
cancelled
expired
failed
fallback_requested
```

The orchestrator decides what semantic consequence follows.

---

# 10. Cancellation and interruption

Novi must support cancellation for expensive inference where the backend permits it.

Typical causes:

- higher-priority event;
- user interruption;
- goal change;
- stale context;
- deadline exceeded;
- resource pressure;
- safety transition.

Cancellation must be observable.

A cancelled model must not continue producing hidden side effects.

---

# 11. Concurrency

The runtime must distinguish:

- independent stateless inference;
- stateful sequence inference;
- streaming inference;
- mutually exclusive models;
- shared GPU models;
- models requiring dedicated resources.

Concurrency policy must be model-specific.

NVIDIA Triton provides per-model scheduling, concurrent model execution, dynamic batching and sequence batching; these are useful backend capabilities but do not replace Novi's higher-level cognitive scheduler. citeturn0search3turn0search12

For stateful inference, Triton's sequence batching can route correlated requests to the same model instance. citeturn0search1

Novi must preserve semantic ownership of sequence identity even when a backend provides the transport/runtime mechanism.

---

# 12. Batching

Batching is allowed only when it is compatible with the cognitive deadline.

For example:

- background embeddings → batching is usually appropriate;
- offline dataset inference → large batching may be appropriate;
- real-time obstacle detection → latency takes priority;
- conversational response → excessive queueing is unacceptable.

Triton's dynamic batching can combine inference requests while exposing queue delay, priority and timeout controls. citeturn0search1

Novi must measure end-to-end latency rather than optimizing throughput in isolation.

---

# 13. Model instances

The runtime may maintain multiple instances of a model when measured workload justifies it.

NVIDIA Triton supports multiple model instances per GPU and configurable scheduling. citeturn0search14

Novi's policy must consider:

- VRAM/RAM cost;
- startup time;
- concurrency;
- latency;
- thermal load;
- power;
- contention with other models;
- model state isolation.

No instance multiplication should be enabled merely because the backend supports it.

---

# 14. GPU/CPU resource governance

The runtime must expose resource requirements before admitting expensive inference.

Track at least:

- CPU utilization;
- GPU utilization;
- VRAM;
- RAM;
- accelerator utilization;
- inference queue depth;
- power;
- temperature;
- storage I/O;
- network I/O where applicable.

The Brain Orchestrator may deny, defer or downgrade an inference request based on current resource state.

---

# 15. TensorRT

TensorRT is a candidate optimized backend for approved NVIDIA GPU deployments.

NVIDIA documents optimization profiles for dynamic shapes; runtime input dimensions must fall within the profiles established for the engine. citeturn0search4turn0search10

Therefore a Novi TensorRT deployment must record:

- engine digest;
- source model digest;
- TensorRT version;
- CUDA version;
- GPU target;
- optimization profiles;
- precision;
- build environment;
- calibration data where applicable;
- benchmark evidence.

A serialized TensorRT engine must not be assumed portable between arbitrary GPUs. NVIDIA's Triton documentation explicitly notes that TensorRT plans are specific to GPU CUDA Compute Capability. citeturn0search0

This is why engine artifacts belong to deployment artifacts, not the canonical model identity.

---

# 16. Triton

NVIDIA Triton is a candidate model-serving backend, particularly where multiple models, concurrency, batching, model management and standardized inference interfaces provide measurable value.

Triton supports TensorRT, PyTorch, ONNX and other backends, model repositories, model management APIs, health endpoints and metrics. citeturn0search3

However:

> **Triton is a model-serving runtime, not Novi's brain orchestrator.**

Novi's orchestrator remains responsible for semantic routing, attention, goals, deadlines and cognitive context.

Triton should therefore be introduced only where benchmark evidence shows that its serving layer improves Novi's actual workload.

---

# 17. Backend abstraction

Novi should expose a backend-neutral interface conceptually equivalent to:

```text
load(model_artifact)
unload(model_id)
health(model_id)
capabilities(model_id)
invoke(request)
cancel(invocation_id)
metrics(model_id)
```

Actual implementations may use:

- TensorRT;
- Triton;
- ONNX Runtime;
- PyTorch;
- speech-specific runtimes;
- VLA/policy-specific runtimes.

The cognitive architecture must not depend on one backend API.

---

# 18. Warm-up

Models may require warm-up before production use.

Warm-up evidence must measure:

- cold-start latency;
- first inference;
- steady-state latency;
- memory after loading;
- thermal impact;
- compilation/JIT effects where relevant.

The runtime should distinguish:

```text
UNLOADED
LOADING
WARMING
READY
DEGRADED
DRAINING
FAILED
UNLOADING
```

---

# 19. Model admission

A model cannot become executable merely because its artifact exists.

Admission requires:

1. approved model identity;
2. compatible deployment target;
3. artifact integrity;
4. runtime compatibility;
5. schema compatibility;
6. safety classification;
7. benchmark evidence;
8. resource budget;
9. policy approval;
10. rollback target.

---

# 20. Health monitoring

The runtime must monitor:

- liveness;
- readiness;
- latency;
- error rate;
- timeout rate;
- queue depth;
- memory;
- GPU/CPU use;
- thermal state;
- output validity;
- numerical anomalies;
- model drift signals where measurable.

A model may be:

```text
healthy
healthy_but_degraded
unhealthy
quarantined
retired
```

---

# 21. Failure isolation

A model failure must not automatically crash the brain.

Failure classes include:

- load failure;
- incompatible artifact;
- out-of-memory;
- timeout;
- process crash;
- backend crash;
- invalid output;
- numerical failure;
- hardware failure;
- resource exhaustion.

Fallback sequence:

```text
failed model
   ↓
retry only if safe/useful
   ↓
alternate approved model
   ↓
deterministic/specialist fallback
   ↓
degraded cognition
   ↓
safe state
```

The exact fallback is capability-specific and belongs in routing policy.

---

# 22. Model state

The runtime distinguishes:

- immutable model parameters;
- inference-session state;
- KV/cache state;
- streaming state;
- sequence state;
- temporary tensors;
- durable Novi memory.

These are not interchangeable.

In particular:

```text
model weights ≠ memory
KV cache ≠ memory
GPU cache ≠ memory
session state ≠ identity
```

Durable memory remains owned by Novi's memory architecture.

---

# 23. Streaming

Streaming is preferred where it improves real-time interaction, including:

- ASR;
- TTS;
- audio event processing;
- video perception;
- multimodal interaction;
- incremental language generation where appropriate.

Streaming interfaces must define:

- partial-result semantics;
- final-result semantics;
- cancellation;
- timestamps;
- ordering;
- backpressure;
- buffer limits.

---

# 24. Backpressure

The runtime must not allow unbounded inference queues.

When demand exceeds capacity it should:

1. drop obsolete work where semantically safe;
2. coalesce compatible work;
3. reduce frequency;
4. downgrade model complexity;
5. defer background work;
6. preserve safety and urgent perception.

Backpressure decisions must be observable.

---

# 25. Privacy

Model execution must respect input privacy classification.

A locally available model should be preferred when a data class is prohibited from leaving the device.

The runtime must not silently route private sensor/audio/video data to an external endpoint.

Any remote inference path must be explicitly authorized by deployment/privacy policy.

---

# 26. Offline operation

Core brain capabilities must continue without internet access where the capability has an approved local implementation.

The runtime must distinguish:

```text
LOCAL_READY
REMOTE_OPTIONAL
REMOTE_REQUIRED
OFFLINE_DEGRADED
UNAVAILABLE
```

A remote model failure must not unexpectedly remove safety, basic perception or physical control.

---

# 27. Determinism and reproducibility

Where deterministic/reproducible inference is required, record:

- model artifact;
- runtime version;
- backend;
- hardware;
- configuration;
- precision;
- seeds where applicable;
- preprocessing version;
- postprocessing version;
- input artifact;
- output artifact.

Exact numerical determinism is not assumed for every GPU/model workload; reproducibility requirements must be specified per capability.

---

# 28. Observability

Each inference must be traceable without storing unnecessary private raw sensor content.

Minimum record:

```text
invocation_id
model_id/version
artifact_digest
runtime/backend
input schema
output schema
start/end timestamps
duration
queue delay
resource snapshot
status
fallback
error class
trace/correlation ID
```

Content logging must follow privacy and retention policy.

---

# 29. Security boundary

The runtime is part of the trusted computing boundary but model weights are not automatically trusted code.

Required controls include:

- artifact integrity;
- provenance;
- approved registry;
- least privilege;
- restricted filesystem access;
- restricted network access;
- signed deployment artifacts where supported;
- resource quotas;
- process/container isolation where appropriate;
- auditability;
- rollback.

---

# 30. Resource-aware cognition

The runtime exposes resource state to the orchestrator but does not decide Novi's goals.

Example:

```text
battery low
   ↓
resource state
   ↓
orchestrator
   ↓
reduce expensive deliberation
   ↓
maintain essential perception
   ↓
continue safe interaction/navigation
```

Thermal pressure must similarly cause graceful degradation rather than uncontrolled failure.

---

# 31. Real-time separation

Safety-critical real-time control must not depend on an unconstrained neural inference process.

The model runtime may provide:

- perception;
- estimates;
- predictions;
- policy proposals.

A separate robotics/control layer remains responsible for deterministic control execution and physical limits.

---

# 32. Simulation and HIL

The model runtime must be usable against:

- synthetic inputs;
- Isaac Sim/Gazebo sensor streams;
- recorded datasets;
- hardware-in-the-loop inputs;
- real sensors.

This allows identical model contracts to be tested across increasingly realistic environments.

The runtime record must identify the source as:

```text
REAL
SIMULATED
SYNTHETIC
REPLAY
HIL
```

and never silently mix these provenance classes.

---

# 33. Performance benchmark

Every production model/backend combination requires a Novi benchmark containing:

- cold-start latency;
- warm latency P50/P95/P99;
- throughput;
- queue latency;
- memory;
- GPU utilization;
- CPU utilization;
- power;
- temperature;
- error/timeout rate;
- concurrency behavior;
- quality metrics;
- degraded behavior.

NVIDIA's Triton documentation provides performance-analysis workflows for evaluating batching and concurrent model execution. citeturn0search14

The benchmark must use representative Novi workloads rather than relying solely on vendor benchmark numbers.

---

# 34. Runtime selection policy

Novi should not automatically adopt Triton, TensorRT, ONNX Runtime or another backend.

The selection process is:

```text
model capability requirement
        ↓
backend candidates
        ↓
compatibility check
        ↓
local/offline check
        ↓
benchmark
        ↓
resource/thermal test
        ↓
failure test
        ↓
security/license review
        ↓
ADR
        ↓
adopt / wrap / defer / reject
```

---

# 35. Initial implementation recommendation

For the first Novi cognitive implementation, prefer the smallest runtime architecture that can support:

1. local specialist models;
2. one local reasoning model;
3. structured model invocation contracts;
4. cancellation/timeouts;
5. resource accounting;
6. health monitoring;
7. fallback;
8. complete provenance.

Do **not** introduce a distributed inference platform merely because the architecture may eventually scale.

Triton should be evaluated when Novi's measured workload demonstrates that multi-model serving, batching, concurrent execution or standardized model management justifies the additional operational complexity.

---

# 36. Runtime state machine

```text
            ┌───────────┐
            │ UNLOADED  │
            └─────┬─────┘
                  ↓
              LOADING
                  ↓
              WARMING
                  ↓
                READY
              ↙       ↘
        DEGRADED      DRAINING
           ↓              ↓
        FAILED ←────── UNLOADING
           ↓
      QUARANTINED
```

Transitions must be auditable.

---

# 37. Acceptance criteria

The model runtime is architecturally acceptable only when it can demonstrate:

- [ ] model admission control;
- [ ] artifact integrity verification;
- [ ] runtime/backend compatibility;
- [ ] explicit scheduling;
- [ ] deadlines;
- [ ] cancellation;
- [ ] bounded queues;
- [ ] concurrency control;
- [ ] resource accounting;
- [ ] thermal/power awareness;
- [ ] health monitoring;
- [ ] model failure isolation;
- [ ] fallback;
- [ ] offline operation;
- [ ] privacy enforcement;
- [ ] provenance;
- [ ] reproducibility metadata;
- [ ] simulation/replay support;
- [ ] benchmark evidence;
- [ ] no direct model-to-motor authority.

---

# 38. Open decisions

The following remain ADR decisions rather than assumptions:

- whether the first runtime uses an in-process executor, Triton or a hybrid;
- whether each model class gets its own process boundary;
- exact IPC mechanism;
- exact GPU memory management strategy;
- exact model cache policy;
- Jetson-specific runtime limits after representative benchmarks;
- which models require TensorRT conversion;
- which models remain in native runtime form;
- whether remote inference is ever enabled;
- exact observability backend.

---

# 39. Architectural invariant

> **The model runtime executes intelligence; it does not own Novi's identity, memory, goals, safety authority or body.**

That boundary is essential to keeping Novi replaceable, inspectable, recoverable and safe while allowing its learned intelligence to evolve.
