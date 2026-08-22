# 03 — Cognition

## High-Level Description

The Cognition subsystem defines how Novi turns observations, world state, memory, knowledge, identity, goals, personality, and context into internal representations that support understanding, prediction, reasoning, social interpretation, planning, and learning.

Cognition is the layer between **what Novi perceives** and **what Novi decides to do**. It is not synonymous with the LLM. Nemotron is a primary reasoning-model candidate; Cognition is the larger system that supplies structured context to models, validates their outputs, maintains authoritative state, and combines probabilistic AI with deterministic software.

## Detailed Description

This directory specifies:

- cognitive architecture and ownership boundaries;
- world and situation representation;
- identity, person, and relationship reasoning;
- multimodal evidence fusion;
- temporal and causal reasoning;
- bounded context construction;
- prediction and expectation;
- personality, social cognition, and affect representation;
- reasoning-model orchestration and model routing;
- uncertainty, confidence, provenance, and contradiction handling;
- cognitive data schemas and APIs;
- failure/degraded modes;
- security and privacy boundaries;
- testing, scenarios, replay, and observability;
- open-source/local-first solution selection;
- NVIDIA and non-NVIDIA acceleration options;
- Mac → simulation → Jetson implementation strategy;
- architectural decision records and final audit.

## Canonical Documents

### Foundation

- `00_HIGH_LEVEL_COGNITION.md` — scope, invariants, cognitive pipeline, outputs, timescales, and degradation.
- `01_COGNITIVE_ARCHITECTURE.md` — components, ownership, data flow, concurrency, transactions, failure isolation, and testability.
- `02_WORLD_MODEL.md` — entities, relations, state, time, space, uncertainty, snapshots, persistence, and extensibility.
- `03_MULTIMODAL_COGNITION.md` — vision, audio, speech, sensors, temporal/spatial alignment, fusion, conflicts, and degradation.
- `04_REASONING_ENGINE.md` — deterministic reasoning, retrieval, specialized ML, general reasoning, structured output, tool requests, and hallucination containment.
- `05_UNCERTAINTY_PROVENANCE_AND_CONTRADICTIONS.md` — epistemic states, evidence, confidence, contradiction resolution, staleness, and user correction.

### Identity and Social Cognition

- `06_IDENTITY_AND_PERSON_MODEL.md` — person entities, biometric evidence, identity confidence, anonymous identities, privacy, and verification.
- `07_RELATIONSHIPS_AND_SOCIAL_COGNITION.md` — relationships, group context, familiarity, social boundaries, and interaction appropriateness.
- `11_PERSONALITY_EMOTION_AND_AFFECT.md` — stable personality traits, adaptive state, emotion hypotheses, internal affect, and personality learning.

### Temporal, Contextual, and Predictive Cognition

- `08_TEMPORAL_AND_CAUSAL_REASONING.md` — temporal relations, routines, causal hypotheses, counterfactuals, and causal confidence.
- `09_CONTEXT_ENGINE.md` — bounded context construction, relevance, freshness, provenance, privacy filtering, contradiction handling, and model independence.
- `10_PREDICTION_AND_EXPECTATION.md` — future-state predictions, routines, prediction error, and learning triggers.

### Models and Routing

- `12_COGNITIVE_ROUTING_AND_MODEL_SELECTION.md` — capability routing, local-first hierarchy, model registry, selection criteria, and fallback.
- `13_NEMOTRON_INTEGRATION.md` — primary reasoning-model candidate, structured context, typed outputs, tool proposals, local deployment, optimization, and fallback.

### Contracts and Reliability

- `14_COGNITIVE_DATA_MODEL.md` — canonical cognitive objects, stable IDs, provenance, lifecycle, contradictions, serialization, and schema versioning.
- `15_COGNITIVE_APIS_AND_CONTRACTS.md` — stable interfaces between cognition, memory, knowledge, perception, models, tools, policy, and audit.
- `16_COGNITIVE_FAILURE_MODES.md` — failure categories, degraded modes, fallbacks, and fail-safe behavior.
- `17_COGNITION_TESTING.md` — unit, contract, scenario, model, multimodal, replay, adversarial, simulation, hardware-in-loop, and endurance testing.
- `18_COGNITION_OBSERVABILITY.md` — traces, metrics, model telemetry, privacy, debugging, and auditability.

### Technology and Delivery

- `19_OPEN_SOURCE_AND_NVIDIA_INTEGRATION.md` — technology selection, open-source/local-first policy, NVIDIA evaluation, alternatives, cloud exceptions, adapters, and benchmarking.
- `20_COGNITION_IMPLEMENTATION_ROADMAP.md` — Mac semantic core, local multimodal cognition, memory/knowledge integration, simulation, Jetson optimization, physical integration, and hardening.

### Security, Scenarios, and Governance

- `21_COGNITIVE_SECURITY_AND_PRIVACY.md` — trust boundaries, prompt injection, capability security, sensitive data, minimization, authorization, immutable core, and local-first privacy.
- `22_COGNITIVE_SCENARIO_CATALOG.md` — canonical scenarios for identity, social behavior, learning, model failure, injection, offline operation, prediction error, and resource pressure.
- `23_COGNITIVE_DECISION_RECORDS.md` — durable architecture decisions and review triggers.
- `24_COGNITION_ARCHITECTURE_AUDIT.md` — final cross-document consistency audit and canonical ownership matrix.

## Core Principles

1. **Cognition is larger than an LLM.**
2. **Authoritative state lives outside the model context.**
3. **Probabilistic inference must remain distinguishable from verified fact.**
4. **Every important inference should retain evidence/provenance.**
5. **Contradictions are data, not errors to silently erase.**
6. **Context is retrieved and composed deliberately; databases are never blindly dumped into prompts.**
7. **The system should work locally and offline wherever practical.**
8. **Existing mature open-source solutions are preferred over reinventing equivalent components.**
9. **NVIDIA is a candidate/reference acceleration ecosystem, not a mandatory cognitive dependency.**
10. **Cloud services are exceptional and require explicit justification.**
11. **Safety and authorization remain outside model-generated cognition.**
12. **Identity is not authorization.**
13. **Predictions are not facts.**
14. **Personality influences style but cannot override policy or safety.**
15. **Cognition must be testable independently from physical hardware.**

## Canonical Boundary With Autonomy

```text
Perception
    ↓
Cognition
 ├── world / situation understanding
 ├── identity / relationships
 ├── memory / knowledge access
 ├── prediction
 ├── personality / social interpretation
 ├── context construction
 └── reasoning proposals
    ↓
Autonomy
 ├── attention / interaction decision
 ├── goal prioritization
 ├── action decision
 └── execution coordination
    ↓
Policy / Safety
    ↓
Capabilities / Hardware
```

Cognition can propose interpretations, candidate goals, questions, plans, and tool requests. Autonomy decides whether and when to pursue them. Policy and safety remain authoritative over consequential actions.

## Technology Selection Rule

For every capability:

```text
Need capability
    ↓
Existing mature solution?
    ↓
Open source + acceptable license?
    ↓
Local execution?
    ↓
Compatible with target hardware?
    ↓
Quality / accuracy sufficient?
    ↓
Latency / memory / power acceptable?
    ↓
Security / privacy / maintenance acceptable?
    ↓
Benchmark
    ↓
Choose best solution
```

Reference ecosystems include NVIDIA, PyTorch, TensorFlow, OpenCV, ONNX Runtime, Hugging Face, ROS 2, and NVIDIA Isaac, but the list is not exclusive.

## Final Status

**DESIGN COMPLETE — V1** (design/architecture level)

The final architecture audit is recorded in `24_COGNITION_ARCHITECTURE_AUDIT.md`. Future changes should normally be additive or captured as decision records unless new evidence demonstrates that an architectural boundary is wrong.

### Design-complete vs implementation-in-progress (reconciled 2026-08-22, gap-analysis Step 0)

"DESIGN COMPLETE — V1" is a **design/architecture** status. It does not mean the
Cognition **implementation** phase is complete. Implementation-phase documents
remain **IN PROGRESS** per the §35 completion gate of
`21_COGNITION_IMPLEMENTATION_SPECIFICATION.md` — most importantly, the canonical
typed cognitive contract layer (`22_COGNITIVE_DATA_CONTRACTS_AND_SCHEMAS.md`,
`26_COGNITIVE_TYPED_MODEL_IMPLEMENTATION_BASELINE.md`) is not yet implemented
(no Pydantic typed models; cognition emits dicts). Cognition may move to
`VALIDATED`/`COMPLETE` for the Mac phase only after that work lands with
validation evidence — see `docs/00-strategy/NOVI_BRAIN_GAP_ANALYSIS_AND_NEXT_STEPS.md`
Step 1 for the priority-ordered plan.

The next major domain is `04-memory-and-knowledge`.
