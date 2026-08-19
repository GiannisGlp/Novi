# 25 — Brain Implementation Closure and Stage-0 Baseline

**Status:** P0 / critical / high importance — ACTIVE PROGRAM BASELINE  
**Domain:** Brain  
**Authority:** `docs/02-novi-brain/`  
**Program phase:** Brain implementation-readiness and Stage-0 execution  
**Date:** 2026-08-19  
**Predecessor:** `24_BRAIN_IMPLEMENTATION_BLUEPRINT.md`  

---

## 1. Purpose

This document formally starts the Novi **Brain** program phase following completion of System Architecture closure ARCH-CLOSE-001 through ARCH-CLOSE-010.

It does not replace the existing Brain architecture, model, lifecycle, state, perception, audio, self-model, world-model, or implementation documents. It consolidates their implementation implications into an executable closure plan and establishes the first implementation baseline.

The purpose is to answer five questions:

1. What does the Brain already have specified?
2. What is still missing before the Brain domain can be marked COMPLETE?
3. What is the smallest executable Brain that can be built and validated on the Mac?
4. Where do neural models, NVIDIA technologies and other accelerators fit without becoming semantic authorities?
5. What evidence is required before promoting the Brain from implementation-readiness to COMPLETE?

---

## 2. Program boundary

System Architecture is now complete. Brain is the next program domain.

The completion distinction is mandatory:

```text
SYSTEM ARCHITECTURE COMPLETE
        ↓
BRAIN IMPLEMENTATION PHASE
        ↓
BRAIN DOMAIN COMPLETE
        ↓
COGNITION / MEMORY / AUTONOMY / HARDWARE / ...
        ↓
GLOBAL NOVI READINESS
```

Brain completion does **not** mean the robot is complete. It means the Brain domain has a sufficiently explicit, implemented and validated runtime for the current implementation stage.

The first target is software-only Mac execution with simulated/mock embodiment. Physical hardware remains governed by Hardware and Deployment completion gates.

---

## 3. Existing Brain baseline

The repository already contains a substantial Brain specification set, including:

- `00_BRAIN_ARCHITECTURE_README.md`;
- Brain state model;
- model taxonomy;
- model lifecycle;
- model runtime;
- vision;
- audio/hearing;
- speech recognition;
- world model integration;
- self-model boundaries;
- architecture boundary/ownership audit;
- `24_BRAIN_IMPLEMENTATION_BLUEPRINT.md`.

The implementation blueprint establishes the central rule:

> **The Brain is an execution system, not a monolithic intelligence model.**

It explicitly defines Brain as the runtime coordinator of neural models, structured state, Soul, Memory, Cognition, Autonomy, planning, constraints, orchestration and safety. Neural networks are capability providers inside this system rather than the Brain itself.

The blueprint also establishes a modular-monolith first architecture and a Mac-first implementation sequence. The current baseline therefore starts from an existing architecture rather than inventing a new Brain architecture.

---

## 4. Canonical ownership rules

The following ownership boundaries are binding for implementation:

| Capability | Semantic authority | Brain responsibility |
|---|---|---|
| System contracts | System Architecture | Consume |
| Brain lifecycle | Brain | Own |
| Runtime orchestration | Brain | Own |
| Model execution | Brain runtime | Own execution |
| Perception execution | Brain runtime | Execute |
| Identity/personality/values/affect | Soul | Adapt/execute pathway |
| World state | Cognition | Adapt/execute |
| Situation model | Cognition | Adapt/execute |
| Reasoning/prediction | Cognition | Invoke |
| Long-term memory/knowledge | Memory | Adapt/execute |
| Goals/priorities/planning | Autonomy | Adapt/execute |
| Safety/authorization | System Architecture / Policy | Request/consume decision |
| Physical control | Hardware | Interface only |

Brain must not create competing definitions of Soul, World Model, Memory, Goals, Safety or physical control.

---

## 5. Stage-0 objective

The first executable Brain milestone is a **local, deterministic, contract-driven cognitive runtime**.

It must operate without physical robot hardware and without requiring a cloud service for its core lifecycle.

Target:

```text
Mac
 ↓
Novi Brain Supervisor
 ↓
Synthetic / prerecorded inputs
 ↓
Canonical observations/evidence
 ↓
Cognition / World Model interfaces
 ↓
Memory interfaces
 ↓
Autonomy interfaces
 ↓
ActionProposal
 ↓
Safety / governance
 ↓
Mock or simulated body
 ↓
ActionOutcome
 ↓
Observation / memory / state update
 ↓
next cycle
```

The first success criterion is not conversational intelligence. It is a **repeatable closed-loop runtime** with explicit state, contracts, provenance, observability and safe action boundaries.

---

## 6. Stage-0 implementation principles

### 6.1 Modular monolith first

The first Brain should run as one process where practical, while maintaining explicit component interfaces and event boundaries.

Initial logical components:

```text
novi-brain
├── supervisor
├── lifecycle
├── scheduler
├── event/runtime bus
├── sensor runtime
├── perception runtime
├── model runtime
├── brain state runtime
├── soul adapter
├── cognition adapter
├── memory adapter
├── autonomy adapter
├── safety adapter
├── body adapter
└── observability
```

Do not introduce distributed microservices merely for architectural appearance.

### 6.2 Deterministic core, learned capabilities

Deterministic components own lifecycle, contracts, persistence boundaries, authorization, safety, provenance and orchestration.

Learned models may provide perception, language understanding, multimodal interpretation, prediction or learned skills behind explicit contracts.

### 6.3 Models are untrusted inputs

Model output is treated as untrusted data until validated and governed.

```text
Model output
    ↓
Schema / semantic validation
    ↓
Structured state or proposal
    ↓
Cognition / Autonomy
    ↓
Safety / authorization
    ↓
Controller
```

### 6.4 No end-to-end neural control initially

Novi should not begin with an end-to-end neural policy controlling motors.

The first Brain should establish the structured control boundary and demonstrate that learned components can be replaced without changing the semantic architecture.

---

## 7. First implementation slice

The first code slice is deliberately narrow.

### Slice B0 — Runtime substrate

Implement:

- Python package/runtime structure;
- configuration loading;
- typed IDs and timestamps using canonical contracts;
- lifecycle state machine;
- structured errors;
- health state;
- event envelope handling;
- correlation/causality IDs;
- deterministic scheduler abstraction;
- observability/logging boundary;
- test harness;
- mock body interface.

### Exit criterion

A clean Mac environment can start the Brain, reach `READY`, accept a synthetic observation, process one deterministic cycle and shut down cleanly.

### Slice B1 — Closed simulated loop

Add:

- synthetic sensor source;
- perception stub producing canonical evidence;
- cognition adapter stub;
- memory adapter backed by the Stage-1 durable storage interfaces;
- autonomy adapter producing a constrained ActionProposal;
- safety adapter returning an explicit decision;
- mock body executing only authorized proposals;
- outcome event;
- replayable cycle trace.

### Exit criterion

The same input scenario produces a reproducible causal trace across repeated runs, subject to explicitly documented nondeterministic model components.

### Slice B2 — Real local model capability

Only after B0/B1 are stable, introduce a local model behind `ModelInvocation`.

The model must be replaceable and must not own system state.

Candidate model/runtime selection is a separate technology decision and requires benchmark/PoC evidence where material.

### Slice B3 — Real perception

Introduce a small local vision/audio capability using prerecorded or synthetic data.

No physical sensor dependency is required for this stage.

### Slice B4 — First meaningful cognitive behavior

Combine perception, Cognition, Memory, Autonomy, Soul and Safety into a continuous simulated environment.

The target is the first meaningful "Brain is alive" demonstration defined by the existing Brain blueprint.

---

## 8. Neural-network strategy

Neural networks are required only where learned computation provides a material advantage over deterministic algorithms or explicit symbolic/algorithmic logic.

Initial candidate roles:

| Capability | Initial approach | Reason |
|---|---|---|
| Sensor normalization | Deterministic | Contracts, timing and quality are explicit |
| Basic state management | Deterministic | Must be auditable/replayable |
| Object/scene perception | Learned model candidate | Strong fit for visual recognition |
| Speech recognition | Learned model candidate | Strong fit for acoustic recognition |
| Language understanding | Local LLM candidate | Flexible semantic interpretation |
| Multimodal interpretation | VLM candidate | Cross-modal reasoning |
| World-state bookkeeping | Deterministic structured state | Must remain explicit |
| Memory persistence | Deterministic database/event store | Durability/provenance |
| Planning | Hybrid | Rules/constraints + learned assistance where justified |
| Safety/authorization | Deterministic | Must not depend on model compliance |
| Motor safety/control boundary | Deterministic | Physical risk and bounded behavior |
| Learned action policy | Deferred | Requires simulation and safety evidence |

The default architecture is therefore hybrid rather than "neural network everywhere".

---

## 9. NVIDIA integration policy

NVIDIA technology is an implementation substrate, not a semantic authority.

The current NVIDIA ecosystem is highly relevant to the future Brain because NVIDIA positions Isaac as an open robotics platform containing CUDA-accelerated libraries, frameworks and AI models, with Isaac ROS providing CUDA-accelerated ROS 2 packages, Isaac Sim providing physically based simulation, and Jetson Orin/Thor providing edge deployment targets. These capabilities are relevant to perception, inference, simulation and physical deployment, but they do not replace Novi's contracts or domain ownership.

NVIDIA's current material also demonstrates an end-to-end physical-AI path involving simulation, model training/evaluation and deployment to Jetson platforms. This supports Novi's simulation-first and edge-promotion strategy, not a requirement to make NVIDIA components part of the Mac Brain core.

For the Mac Stage-0 implementation:

- do not require NVIDIA hardware;
- do not expose NVIDIA APIs in semantic contracts;
- keep model/runtime adapters vendor-neutral;
- record NVIDIA-specific deployment decisions in Technology/Deployment ADRs;
- validate NVIDIA edge backends later through the same capability interfaces.

For future NVIDIA edge deployment, version compatibility must be treated as a first-class deployment concern. NVIDIA's current TensorRT documentation states that Jetson/JetPack support is tied to the TensorRT version supplied by the JetPack release; therefore Brain model artifacts and runtime versions must be represented in the deployment/version tuple rather than assumed to be interchangeable.

NVIDIA also documents TensorRT as a hardware-specific inference runtime and provides Triton for model serving, while recommending edge-specific integration choices. These are future implementation options behind the Brain Model Runtime interface, not current semantic dependencies.

---

## 10. Model Runtime contract requirements

The Model Runtime must expose at least:

```text
ModelDescriptor
ModelArtifact
ModelVersion
ModelDigest
ModelCapabilities
ModelInput
ModelOutput
ModelInvocation
ModelResult
ModelHealth
ModelFailure
ModelResourceUsage
```

Every invocation must carry sufficient provenance to answer:

- which model ran;
- which artifact/digest ran;
- which runtime/backend ran;
- which configuration ran;
- which input correlation produced it;
- when it started/completed;
- what resource budget it consumed;
- whether the result was complete, degraded, cancelled or failed.

The Brain must support:

- loading/unloading;
- health checking;
- cancellation;
- timeout;
- resource limits;
- fallback/degraded operation;
- version compatibility checks;
- deterministic test fixtures where possible.

---

## 11. Runtime lifecycle

The Brain supervisor must implement explicit states:

```text
BOOTING
  ↓
INITIALIZING
  ↓
READY
  ↓
ACTIVE
  ↘
  DEGRADED
  ↓
RECOVERING
  ↓
ACTIVE

Any unsafe/terminal condition
  ↓
SAFE_STOP / FAILED
  ↓
SHUTTING_DOWN
```

Startup must validate required contracts, configuration, adapters and model artifacts before entering `READY`.

A failed optional capability must not automatically make the whole Brain unusable if a documented degraded mode exists.

---

## 12. Scheduler and multi-rate execution

The Brain is not one global-frequency loop.

The runtime must support separate cadence classes for:

- safety/watchdog;
- sensor acquisition;
- perception;
- world-state updates;
- cognition;
- memory operations;
- planning;
- speech/audio;
- UI/interaction;
- observability.

Each task requires:

- priority;
- desired rate/deadline;
- maximum tolerated lateness;
- cancellation policy;
- resource budget;
- degraded-mode behavior.

The scheduler must never allow a slow model invocation to block safety-critical or lifecycle-critical work.

---

## 13. State boundaries

Brain state is execution state only.

It may contain:

- lifecycle state;
- active tasks;
- invocation state;
- current runtime health;
- transient buffers;
- correlation state;
- resource counters;
- temporary coordination data.

It must not become the canonical owner of:

- Soul identity/personality;
- durable Memory;
- canonical World Model semantics;
- Autonomy goals;
- safety policy.

This prevents the Brain from becoming a hidden second architecture.

---

## 14. First test strategy

Every Brain capability follows:

```text
Specification
 ↓
Contract test
 ↓
Unit test
 ↓
Component test
 ↓
Integration test
 ↓
Scenario/replay test
 ↓
Failure/degradation test
 ↓
Performance benchmark
 ↓
Regression evidence
```

Stage-0 minimum evidence should include:

1. clean startup;
2. lifecycle transition correctness;
3. malformed input rejection;
4. contract validation;
5. event correlation;
6. deterministic replay;
7. cancellation;
8. timeout;
9. adapter failure;
10. model failure/degraded mode;
11. memory persistence/retrieval;
12. unauthorized action rejection;
13. safe-stop behavior;
14. graceful shutdown;
15. repeated-run stability.

---

## 15. Brain completion gate

Brain cannot be marked COMPLETE until all of the following are satisfied for the current implementation stage:

### Architecture

- ownership boundaries remain consistent with System Architecture;
- Brain runtime topology is implemented;
- lifecycle and scheduler semantics are executable;
- adapter contracts are explicit;
- model runtime boundary is explicit;
- degraded modes are specified.

### Implementation

- Stage-0 runtime starts cleanly;
- closed simulated loop executes;
- canonical contracts are used rather than local semantic duplicates;
- model invocation is isolated behind the model runtime interface;
- Soul/Cognition/Memory/Autonomy adapters are functional;
- Safety gateway cannot be bypassed;
- mock/simulated embodiment works.

### Validation

- contract tests pass;
- integration tests pass;
- replay/scenario tests pass;
- failure/degradation tests pass;
- resource/latency benchmarks exist;
- evidence is reproducible on the target Mac environment.

### Documentation

- implementation decisions are recorded;
- technology decisions have ADRs where required;
- NVIDIA/ROS/Apple/open-source claims are source-backed;
- known limitations and deferred physical validation are explicit;
- the program tracker is synchronized.

---

## 16. Immediate work queue

The Brain work begins in this order:

```text
B0.1  Repository/runtime package baseline
  ↓
B0.2  Canonical contract bindings
  ↓
B0.3  Supervisor + lifecycle
  ↓
B0.4  Scheduler/event loop
  ↓
B0.5  Health/errors/observability
  ↓
B0.6  Mock body + safety gateway
  ↓
B1.1  Synthetic observation source
  ↓
B1.2  Evidence/state adapters
  ↓
B1.3  Memory adapter
  ↓
B1.4  Autonomy ActionProposal
  ↓
B1.5  Outcome + replay
  ↓
B1.6  Closed-loop Stage-0 evidence
```

No large model-training effort is required for B0/B1.

No physical robot integration is required for B0/B1.

No NVIDIA hardware is required for B0/B1.

---

## 17. Research basis

### NVIDIA primary sources

- NVIDIA Isaac platform: https://developer.nvidia.com/isaac
- NVIDIA Jetson Thor physical-AI platform: https://developer.nvidia.com/blog/introducing-nvidia-jetson-thor-the-ultimate-platform-for-physical-ai/
- NVIDIA TensorRT installation and deployment documentation: https://docs.nvidia.com/deeplearning/tensorrt/latest/installing-tensorrt/installing.html
- NVIDIA TensorRT Jetson/JetPack compatibility guidance: https://docs.nvidia.com/deeplearning/tensorrt/latest/api/migration/tensorrt-10x-to-11x-jetson.html
- NVIDIA Triton Jetson documentation: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/jetson.html

### Novi internal authorities

- `docs/02-novi-brain/00_BRAIN_ARCHITECTURE_README.md`
- `docs/02-novi-brain/03_BRAIN_STATE_MODEL.md`
- `docs/02-novi-brain/07_MODEL_TAXONOMY.md`
- `docs/02-novi-brain/09_MODEL_LIFECYCLE.md`
- `docs/02-novi-brain/10_MODEL_RUNTIME.md`
- `docs/02-novi-brain/18_WORLD_MODEL.md`
- `docs/02-novi-brain/22_SELF_MODEL.md`
- `docs/02-novi-brain/23_ARCHITECTURE_BOUNDARY_AND_OWNERSHIP_AUDIT.md`
- `docs/02-novi-brain/24_BRAIN_IMPLEMENTATION_BLUEPRINT.md`
- completed System Architecture closure artifacts ARCH-CLOSE-001 through ARCH-CLOSE-010;
- canonical program tracker.

### Existing Novi NVIDIA research

The repository's existing NVIDIA research dossier is an additional research input. It establishes the same architectural principle used here: NVIDIA capabilities should be integrated behind Novi-owned capability interfaces rather than becoming semantic authorities.

---

## 18. Research/decision classification

Every future Brain technology claim must be labelled as one of:

1. **Source-backed fact** — directly supported by authoritative documentation;
2. **Novi architectural inference** — engineering conclusion derived from requirements and evidence;
3. **Novi adoption decision** — explicit choice recorded by an ADR/selection artifact;
4. **Validated implementation result** — supported by reproducible test or benchmark evidence.

No vendor capability becomes a Novi dependency merely because it exists.

---

## 19. Definition of the first meaningful Brain

The first meaningful Brain is not defined by model size, number of neural networks, GPU type or conversational fluency.

It is defined by the ability to maintain a continuous, auditable, bounded loop:

```text
observe
 → interpret
 → maintain state
 → remember
 → attend
 → reason
 → choose
 → govern
 → act/simulate
 → observe outcome
 → update
 → continue
```

The loop must continue without a user prompt being required for every cycle.

This is the operational target for Stage 0.

---

## 20. Status

```text
Brain domain:                 IN PROGRESS
Architecture baseline:       ESTABLISHED
Implementation baseline:     ESTABLISHED
Stage-0 runtime:              NOT YET IMPLEMENTED
Stage-0 closed loop:          NOT YET IMPLEMENTED
Model runtime:                SPECIFIED / IMPLEMENTATION PENDING
Physical deployment:          DEFERRED
NVIDIA edge integration:      DEFERRED TO EDGE/SIMULATION VALIDATION
Brain completion gate:        OPEN
```

This document is the starting baseline for Brain implementation and must be updated whenever a Brain boundary, technology choice, implementation contract, validation result or completion status materially changes.
