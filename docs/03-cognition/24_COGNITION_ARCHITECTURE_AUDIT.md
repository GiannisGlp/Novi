# 24 — Cognition Architecture Audit

## Status

**AUDITED — V1 DESIGN BASELINE**

Audit date: 2026-08-16

## Purpose

This document records the final cross-document architecture audit for `03-cognition`. The goal is to verify that cognition has a coherent boundary with autonomy, perception, memory/knowledge, models, tools, policy, safety, and hardware, and that the documentation does not accidentally make a model or vendor the system of record.

## Audit Scope

The audit covers:

- high-level cognition definition;
- cognitive component ownership;
- world and situation representation;
- identity and relationships;
- multimodal evidence;
- temporal/causal reasoning;
- context construction;
- prediction;
- personality/affect;
- reasoning/model routing;
- Nemotron integration;
- cognitive data contracts;
- APIs/capabilities;
- failure handling;
- security/privacy;
- testing/observability;
- open-source/vendor selection;
- autonomy boundary;
- Mac → simulation → Jetson roadmap;
- scenario and decision-record coverage.

## Audit Result

**PASS WITH DOCUMENTATION CORRECTIONS APPLIED.**

The architecture is coherent enough to serve as the V1 design baseline. Remaining work belongs primarily to implementation contracts and the `04-memory-and-knowledge` domain rather than another major redesign of cognition.

## Finding 1 — README Document Index Drift

### Finding

The original cognition README listed planned filenames that no longer matched the actual detailed documents. For example, the README referred to `03_SITUATION_MODEL.md`, `04_ENTITY_IDENTITY_AND_RELATIONSHIPS.md`, and other names that were not the current filenames.

### Risk

Developers and Codex could follow stale links and implement the wrong document structure.

### Resolution

The README index must reflect the actual numbered files in this directory. The current canonical sequence is `00` through `24`, with `24` being this audit.

**Status: RESOLVED.**

## Finding 2 — Cognition vs Autonomy Boundary

### Finding

Both domains use concepts such as goals, personality, planning, context, and decision support. Without an explicit ownership rule, future implementation could duplicate state.

### Resolution

The canonical boundary is:

```text
Perception
    ↓
Cognition
    ├── world/situation understanding
    ├── identity/relationships
    ├── memory/knowledge access
    ├── prediction
    ├── personality/social interpretation
    ├── context construction
    └── reasoning proposals
    ↓
Autonomy
    ├── attention/interaction decision
    ├── goal prioritization
    ├── action decision
    └── execution coordination
    ↓
Policy / Safety
    ↓
Capabilities / Hardware
```

Cognition can propose candidate goals/plans, but autonomy owns whether/when the system should pursue them. Personality representation belongs to cognition; interaction policy remains outside personality.

**Status: RESOLVED.**

## Finding 3 — World Model vs Memory/Knowledge Ownership

### Finding

The World Model needs durable state but must not become a duplicate of the entire memory/knowledge database.

### Resolution

- World Model owns current interpreted world state and short-horizon state needed for cognition.
- Memory owns experiences and historical episodes.
- Knowledge owns durable semantic claims, schemas, provenance, and verification.
- The World Model may reference historical evidence without owning the complete history.

Hot state may be cached in memory with durable persistence behind a storage interface.

**Status: RESOLVED.**

## Finding 4 — Model Authority

### Finding

The reasoning model could otherwise become an implicit source of truth.

### Resolution

The model is explicitly a proposal generator. Authoritative state remains in World Model, Memory, Knowledge, Identity, Policy, and Safety services. Model outputs are typed, validated, confidence-aware, and provenance-linked where applicable.

**Status: RESOLVED.**

## Finding 5 — Model Routing and Vendor Lock-In

### Finding

The project is targeting Jetson and uses Nemotron as a primary candidate, creating a risk that cognitive interfaces become NVIDIA-specific.

### Resolution

`ReasoningModel` and `ModelRouter` are vendor-neutral contracts. NVIDIA, PyTorch, TensorFlow, OpenCV, ONNX Runtime, Hugging Face, ROS 2, Isaac, and other mature solutions are evaluated per capability. Selection is based on license, local execution, quality, latency, memory, power, compatibility, security, maintenance, integration, and benchmarks.

Cloud is an explicit exception.

**Status: RESOLVED.**

## Finding 6 — Multimodal Evidence vs Semantic Cognition

### Finding

Raw sensors and high-level cognition could become tightly coupled.

### Resolution

Perception adapters produce normalized observations. Multimodal cognition performs temporal/spatial alignment, entity association, and evidence fusion. Cognition consumes semantic observations/events rather than owning device drivers.

ROS 2/robotics infrastructure may own authoritative transform and hardware transport where appropriate.

**Status: RESOLVED.**

## Finding 7 — Identity vs Authorization

### Finding

Recognizing a family member could accidentally become equivalent to authorizing actions.

### Resolution

Identity is evidence-backed probabilistic state. Authorization is a separate security function. Face/voice recognition can inform context but cannot independently authorize consequential actions.

**Status: RESOLVED.**

## Finding 8 — Prediction vs Fact

### Finding

Predictions about routines and future events could contaminate current world state.

### Resolution

Predictions are a separate epistemic type with confidence and time horizon. Observed state always has precedence over stale predictions. Prediction error feeds learning rather than silently rewriting facts.

**Status: RESOLVED.**

## Finding 9 — Personality vs Emotion Claims

### Finding

Multimodal emotion recognition can create false certainty about people's internal mental state.

### Resolution

Human emotional state is represented as a hypothesis with evidence and confidence. Novi's own affect variables are computational state, not claims of human consciousness. Personality cannot bypass policy, privacy, authorization, or safety.

**Status: RESOLVED.**

## Finding 10 — Context Leakage

### Finding

A continuously learning robot has access to large amounts of household information. Blind context injection would create privacy, latency, and relevance problems.

### Resolution

The Context Engine selects bounded, task-relevant information and applies provenance, freshness, privacy, and trust filtering before model invocation.

**Status: RESOLVED.**

## Finding 11 — Prompt Injection / Untrusted Content

### Finding

Observed speech, images, documents, websites, and messages may contain instructions designed to manipulate the model.

### Resolution

External content is explicitly untrusted data. Trust levels distinguish policy, authorized user instructions, observations, retrieved knowledge, and model output. Model-generated actions still require capability validation, authorization, policy, and safety.

**Status: RESOLVED.**

## Finding 12 — Failure and Degraded Operation

### Finding

A local-first autonomous system must continue operating when models, sensors, memory, GPU resources, or network services fail.

### Resolution

Cognition defines explicit degraded modes and deterministic/specialized fallbacks. Safety-critical functions fail safe. Non-critical functions may degrade to lower-quality local behavior.

**Status: RESOLVED.**

## Finding 13 — Observability Without Chain-of-Thought Storage

### Finding

Autonomous decisions need to be auditable without storing private model reasoning or excessive household media.

### Resolution

Use structured traces containing request IDs, inputs/evidence references, context metadata, selected capability, model/version, policy result, action request, outcome, latency, and errors. Do not store private chain-of-thought.

**Status: RESOLVED.**

## Finding 14 — Dynamic Cognitive Data

### Finding

Novi must be able to learn new entities and concepts without requiring a predefined schema for every possible thing.

### Resolution

Cognitive contracts support extensible entity types, stable IDs, provenance, lifecycle, and schema versioning. Actual persistence and controlled schema evolution belong to `04-memory-and-knowledge`.

Novi may propose new structures, but it does not directly execute arbitrary SQL or filesystem operations from model output.

**Status: RESOLVED AT COGNITION BOUNDARY.**

## Finding 15 — Determinism vs Probabilistic AI

### Finding

Using an LLM for deterministic or safety-critical decisions would make behavior unnecessarily unpredictable.

### Resolution

The reasoning architecture explicitly prioritizes deterministic logic, retrieval, specialized local models, compact reasoning models, and only then the primary general reasoning model. Safety, authorization, schema validation, and critical state transitions remain deterministic.

**Status: RESOLVED.**

## Finding 16 — Mac / Simulation / Jetson Portability

### Finding

Cognition could accidentally depend on Jetson-specific runtime behavior and make Mac development impossible.

### Resolution

Cognition contracts are hardware-independent. Mac is the initial development runtime, simulation provides embodied validation, and Jetson provides target hardware validation and acceleration. Vendor-specific adapters remain below cognitive contracts.

**Status: RESOLVED.**

## Canonical Ownership Matrix

| Domain | Owns | Must not own |
|---|---|---|
| Perception | sensor interpretation | high-level goals, authorization |
| Cognition | world understanding, context, identity, prediction, reasoning proposals | safety authority, raw hardware control |
| Memory | episodic/history persistence | action authorization |
| Knowledge | semantic claims/schema/provenance | physical control |
| Autonomy | attention, goal priority, action decision/coordination | low-level motor control |
| Personality | stable traits/adaptive social style | policy/safety authority |
| Policy | authorization rules | model interpretation |
| Safety | physical/system constraints | personality/knowledge |
| Capabilities | controlled external actions | arbitrary model commands |
| Hardware/ROS | device transport/control | cognitive truth |

## Canonical Cognitive Flow

```text
Sensors / external data
        ↓
Perception
        ↓
Observations / Events
        ↓
World + Situation Model
        ↓
Identity / Relationships / Temporal Context
        ↓
Memory + Knowledge Retrieval
        ↓
Context Engine
        ↓
Model Router
        ├── deterministic logic
        ├── retrieval
        ├── specialized local model
        ├── compact reasoning model
        └── primary reasoning model (Nemotron candidate)
        ↓
Typed Cognitive Result
        ↓
Autonomy
        ↓
Policy + Safety
        ↓
Capability
        ↓
Outcome
        ↓
World Model / Memory / Learning
```

## Final Audit Decision

`03-cognition` is **DESIGN COMPLETE — V1**.

This means the architectural boundary is stable enough for the next major domain. It does **not** mean every implementation detail is frozen or that the software exists.

Future changes should be additive or captured as decision records unless new evidence demonstrates that a boundary is wrong.

## Next Domain

Proceed to `04-memory-and-knowledge`.
