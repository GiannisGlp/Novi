# Novi — Documentation & Implementation Completion Tracker

**Status:** Canonical master tracker  
**Priority:** P0 / critical  
**Owner:** Novi architecture and implementation program  
**Updated:** 2026-08-18  

---

## 1. Purpose

This document is the canonical program-level tracker for closing the remaining documentation, technology-selection, engineering, validation, and implementation-readiness gaps before Novi enters serious production implementation.

It exists to prevent the project from drifting into implementation while critical architectural decisions, contracts, technology choices, safety requirements, hardware decisions, validation methods, or deployment requirements remain undefined.

Every item in this tracker is treated as a **critical/high-importance architectural artifact** unless explicitly downgraded through a documented decision.

This tracker is not itself a replacement for domain specifications. Each domain remains responsible for its authoritative documents, contracts, research evidence, decisions, and acceptance criteria.

---

## 2. North-star completion rule

Novi is implementation-ready only when every required domain reaches its defined completion gate and the cross-domain traceability chain is closed:

```text
North Star
    ↓
Requirements
    ↓
Architecture
    ↓
Domain specification
    ↓
Technology decision
    ↓
Contracts / schemas
    ↓
Implementation plan
    ↓
Tests / validation
    ↓
Evidence
    ↓
Readiness gate
```

A domain marked **Complete** means its documentation and architectural decisions are sufficient for the current implementation stage; it does not mean the corresponding production software or physical robot is finished.

---

# 3. Program status

| Domain | Current status | Target | Completion gate |
|---|---|---|---|
| Soul | ██████████ | Complete | Canonical behavioral specification + acceptance suite |
| System Architecture | ██████████ | Strong / near-complete | Architecture validation + traceability gate |
| Brain | █████████░ | Strong | Implementation contracts + runtime validation |
| Cognition | ████████░░ | Needs implementation layer | Executable cognition architecture + contracts |
| Memory | █████████░ | Strong, implementation pending | Concrete storage/retrieval implementation baseline |
| Autonomy | ████████░░ | Implementation pending | Executable autonomy/runtime specification |
| Hardware | █████░░░░░ | Incomplete | Engineering selection + BOM + safety + validation |
| Technology | ██████░░░░ | Selection pending | Technology baseline + ADRs + compatibility matrix |
| Simulation | ████░░░░░░ | Incomplete | Robot/sensor/world/scenario/SIL-HIL architecture |
| Validation | ██████░░░░ | Needs unification | End-to-end validation hierarchy + evidence model |
| Security | █████░░░░░ | Incomplete | Threat model + controls + security validation |
| Deployment | ████░░░░░░ | Incomplete | Reproducible deployment + artifact/version strategy |

---

# 4. Completion states

Use only these states in this document and domain trackers:

- **NOT STARTED** — no authoritative work completed.
- **IN PROGRESS** — active documentation/research/engineering work.
- **BLOCKED** — cannot proceed until a named dependency is resolved.
- **REVIEW** — drafted and undergoing architecture/research validation.
- **VALIDATED** — requirements, sources, decisions and acceptance criteria have been checked.
- **COMPLETE** — domain completion gate is satisfied for the current implementation phase.
- **SUPERSEDED** — replaced by a newer authoritative artifact; retained only for traceability.

Never mark a domain Complete merely because a document exists.

---

# 5. Domain completion plans

## 5.1 Soul — COMPLETE

### Authority
`docs/06-soul/`

### Completed scope

- Soul and behavioral constitution
- identity and self-model
- personality, values and motivations
- social intelligence and interaction
- relationships and social development
- affect/internal life/emotional expression
- learning/development/adaptation
- communication and living lexicon
- behavioral scenarios and acceptance criteria

### Completion gate

- Soul owns enduring identity, personality, values, motivations, social disposition and behavioral continuity.
- Cognition, Memory, Autonomy, Brain, Policy and Hardware boundaries are explicit.
- Behavioral invariants and acceptance scenarios exist.
- No competing personality authority remains in Cognition or Autonomy.

### Remaining audit
Cross-reference every consuming domain and remove stale ownership language as discovered.

**Status: COMPLETE**

---

## 5.2 System Architecture — STRONG

### Authority
`docs/01-system-architecture/`

### Must complete

1. Validate canonical component boundaries.
2. Resolve duplicate/legacy numbered documents and naming inconsistencies.
3. Ensure every cross-domain contract has one canonical owner.
4. Complete architecture traceability from North Star to implementation.
5. Validate runtime profiles and deployment boundaries.
6. Validate durable state, concurrency, replication, recovery and privacy semantics against actual implementation plans.
7. Complete architecture completion gate.
8. Keep NVIDIA platform validation current where NVIDIA components are selected.

### Exit criteria

- No unresolved P0 architecture contradiction.
- Every system boundary has an owner.
- Every P0 interface has a canonical contract.
- Architecture validation document passes.

**Status: STRONG — validation/cleanup required**

---

## 5.3 Brain — STRONG

### Authority
`docs/02-novi-brain/`

### Must complete

1. Finalize Brain implementation blueprint.
2. Define executable runtime component graph.
3. Define scheduler/orchestrator semantics.
4. Define event loop and lifecycle.
5. Define model invocation abstraction.
6. Define Soul adapter.
7. Define Cognition adapter.
8. Define Memory adapter.
9. Define Autonomy adapter.
10. Define Policy/Safety gateway interface.
11. Define perception/audio/actuation adapter boundaries.
12. Define health, backpressure, degradation and recovery behavior.
13. Define Mac-first runtime profile.
14. Define transition from Mac to simulation and edge/robot targets.

### Exit criteria

A minimal Brain runtime can be implemented without inventing missing architecture while preserving domain ownership.

**Status: STRONG — implementation contracts remain**

---

## 5.4 Cognition — NEEDS IMPLEMENTATION LAYER

### Authority
`docs/03-cognition/`

### Required next master artifact

`COGNITION_IMPLEMENTATION_SPECIFICATION.md`

### Must define

- perception evidence ingestion
- multimodal evidence fusion
- world model implementation
- situation model
- attention inputs
- temporal reasoning
- causal reasoning
- social understanding
- identity interpretation
- relationship interpretation
- uncertainty representation
- confidence/provenance propagation
- prediction
- model routing/selection
- reasoning execution
- structured vs neural responsibility
- inference budgets
- update rates
- degraded modes
- failure recovery
- interfaces to Soul, Memory and Autonomy
- observability
- test strategy

### Exit criteria

The Mac Brain can instantiate Cognition from explicit components and contracts without inventing missing semantics.

**Status: NEXT MAJOR WORKSTREAM**

---

## 5.5 Memory — STRONG / IMPLEMENTATION PENDING

### Authority
`docs/04-memory-and-knowledge/`

### Must complete

- concrete local durable-event implementation
- structured state store decision
- episodic memory implementation
- semantic memory implementation
- relationship memory implementation
- autobiographical memory implementation
- vector retrieval decision
- knowledge graph decision
- embedding/reranking strategy
- retention and forgetting execution
- provenance implementation
- privacy/erasure implementation
- schema migration
- backup/recovery
- indexing strategy
- memory performance budgets
- Mac storage baseline

### Exit criteria

A complete memory write → persist → retrieve → update → forget → recover cycle is implementable and testable on Mac.

**Status: STRONG — implementation baseline pending**

---

## 5.6 Autonomy — IMPLEMENTATION PENDING

### Authority
`docs/02-autonomy/`

### Must complete

- attention manager
- goals
- priorities
- initiative
- interruption policy
- idle behavior
- curiosity
- planning
- replanning
- commitment handling
- action proposal
- action selection
- action cancellation
- resource budgets
- autonomy degradation
- policy/safety integration
- execution feedback
- cross-domain contracts

### Exit criteria

Novi can continuously decide whether to attend, wait, speak, investigate, plan or act without bypassing Soul, Cognition, Memory or Safety ownership.

**Status: IMPLEMENTATION PENDING**

---

## 5.7 Hardware — INCOMPLETE

### Authority
`docs/05-hardware/`

### Must complete

- compute selection
- cameras
- depth/LiDAR
- IMU
- microphones/audio
- displays/lighting if required
- actuators
- motor controllers
- power architecture
- battery/BMS
- thermal architecture
- networking
- storage
- tactile sensing
- emergency stop
- watchdogs
- connectivity loss behavior
- calibration
- sensor synchronization
- mechanical architecture
- electrical architecture
- interfaces/connectors
- BOM
- sourcing/replacement strategy
- serviceability
- physical safety case
- validation plan

### Exit criteria

Every physical subsystem has a selected baseline, alternative, interface, power/thermal requirements, safety considerations, calibration procedure and validation criteria.

**Status: INCOMPLETE — P0 before physical actuation**

---

## 5.8 Technology — SELECTION PENDING

### Authority
`docs/TECHNOLOGY_REFERENCE.md` and `docs/TECHNOLOGY_STACK_BASELINE.md`

### Must complete

Create and maintain a canonical implementation stack covering:

- OS
- language/runtime policy
- Python/C++/Rust boundaries
- ROS 2 distribution
- Ubuntu compatibility
- ROS middleware/DDS/RMW
- ros2_control
- Navigation2
- simulation platform
- perception backend
- audio pipeline
- STT
- TTS
- LLM runtime
- VLM runtime
- embeddings
- reranking
- inference serving
- databases
- vector retrieval
- knowledge graph
- event log
- observability/OpenTelemetry
- containers
- CI
- artifact/model registry
- dataset/version management
- secrets
- OTA/update strategy
- CAD/URDF/USD pipeline
- firmware tooling

### Decision rule
Every technology adopted for Novi must have:

1. requirement mapping;
2. candidate comparison;
3. authoritative-source validation;
4. license/security review;
5. platform compatibility review;
6. benchmark/PoC where material;
7. explicit ADR/selection record.

**Status: SELECTION PENDING — P0**

---

## 5.9 Simulation — INCOMPLETE

### Must complete

- robot URDF/Xacro
- USD representation
- physics parameters
- sensor models
- environment assets
- CAD → URDF/USD pipeline
- human/agent simulation
- noise models
- sensor failure models
- actuator failure models
- deterministic seeds
- scenario schema
- ground truth
- SIL architecture
- HIL architecture
- simulation provenance
- sim-to-real validation

### Exit criteria

A deterministic scenario can run Novi's cognitive/runtime stack against a simulated embodied world and produce measurable ground-truth comparisons.

**Status: INCOMPLETE**

---

## 5.10 Validation — NEEDS UNIFICATION

### Must create

A single validation hierarchy:

```text
UNIT
  ↓
COMPONENT
  ↓
INTEGRATION
  ↓
SYSTEM
  ↓
SIL
  ↓
HIL
  ↓
CONTROLLED PHYSICAL
  ↓
LONG-DURATION
  ↓
REAL-WORLD
```

### Must define

- requirement traceability
- test ownership
- test data
- ground truth
- behavioral metrics
- cognitive metrics
- latency budgets
- resource budgets
- safety metrics
- recovery metrics
- model evaluation
- simulation evaluation
- physical evaluation
- regression policy
- longitudinal evaluation
- acceptance evidence
- release gates

**Status: NEEDS UNIFICATION — P0**

---

## 5.11 Security — INCOMPLETE

### Must create

A consolidated physical-AI threat model covering:

- prompt injection
- tool abuse
- memory poisoning
- model poisoning
- dataset poisoning
- sensor spoofing
- adversarial perception
- unauthorized model updates
- compromised dependencies
- supply-chain attacks
- credential theft
- network compromise
- inference endpoint compromise
- privacy leakage
- malicious physical access
- firmware compromise
- update/rollback attacks

### Must define

- threat actors
- assets
- trust boundaries
- attack paths
- controls
- monitoring
- incident response
- recovery
- security tests
- residual risk

**Status: INCOMPLETE — P0**

---

## 5.12 Deployment — INCOMPLETE

### Must create

A reproducible deployment architecture covering:

- Mac development profile
- simulation profile
- edge profile
- physical robot profile
- OS version
- firmware versions
- ROS version
- CUDA/TensorRT/Isaac versions where applicable
- containers
- Python/C++ dependencies
- model versions/hashes
- datasets
- configuration
- database schema
- secrets
- artifact registry
- release manifests
- rollback
- OTA/update strategy
- health checks
- migration strategy

### Exit criteria

Given a versioned deployment manifest, another machine can reproduce the same Novi software/runtime environment within defined tolerances.

**Status: INCOMPLETE — P0**

---

# 6. Cross-domain workstreams

These cannot be completed by one domain in isolation.

## X-001 — Canonical contracts

Every interface must have one authoritative owner.

```text
Soul ↔ Cognition
Soul ↔ Memory
Soul ↔ Autonomy
Cognition ↔ Memory
Cognition ↔ Autonomy
Autonomy ↔ Policy
Policy ↔ Hardware
Brain ↔ all domains
```

**Gate:** no duplicate semantic authority.

## X-002 — Time and synchronization

Define system, monotonic, ROS, simulation, sensor and hardware clocks; timestamp semantics; synchronization; drift; ordering and failure behavior.

**Priority:** P0.

## X-003 — Observability

Trace the complete causal path:

```text
sensor
 → perception
 → evidence
 → world state
 → memory
 → cognition
 → autonomy
 → policy
 → action
 → outcome
```

**Priority:** P0.

## X-004 — Resource governance

Define CPU/GPU/RAM/VRAM/unified-memory/storage/network/power/thermal budgets for the Mac-first system and future edge targets.

**Priority:** P0.

## X-005 — Data/model provenance

Every model, dataset, learned behavior and durable memory artifact must have provenance, version and lifecycle semantics.

**Priority:** P0.

## X-006 — Failure and degradation architecture

Define what Novi does when sensors, models, memory, network, GPU, storage, speech, navigation or actuators fail.

**Priority:** P0.

---

# 7. Recommended execution order

The work should proceed in dependency order rather than simply following folder numbering:

```text
1. Cognition Implementation Specification
        ↓
2. Mac Brain Technology Baseline
        ↓
3. Model Evaluation & Selection Matrix
        ↓
4. Perception Implementation Architecture
        ↓
5. World Model Implementation
        ↓
6. Memory Implementation Baseline
        ↓
7. Autonomy Implementation Specification
        ↓
8. Time / Synchronization
        ↓
9. Simulation Architecture
        ↓
10. Data / Dataset Architecture
        ↓
11. Security / Threat Model
        ↓
12. Deployment / Reproducibility
        ↓
13. Unified Validation Program
        ↓
14. Cross-domain readiness audit
        ↓
15. MAC BRAIN STAGE 0 IMPLEMENTATION
```

Hardware engineering proceeds in parallel where it does not depend on final software selections, but **physical actuation remains gated by the safety case and hardware validation**.

---

# 8. Research and validation policy

Every critical document must be researched against valid primary or authoritative sources where applicable.

Preferred source order:

1. official NVIDIA documentation for NVIDIA technologies;
2. official ROS documentation for ROS technologies;
3. official Apple documentation for Apple Silicon/macOS/MLX;
4. official project documentation for adopted open-source projects;
5. peer-reviewed research for scientific claims;
6. standards/specifications for safety, networking, timing and interfaces;
7. reputable secondary sources only when primary documentation is insufficient.

Do not convert vendor capability claims directly into Novi architecture. Record the distinction between:

- **source-backed fact**;
- **Novi architectural inference**;
- **Novi adoption decision**;
- **validated implementation result**.

Every technology selection should be benchmarked or prototyped when the decision materially affects performance, compatibility, safety or architecture.

---

# 9. Documentation quality gate

Every new critical document must contain, where applicable:

- purpose;
- scope;
- authority/ownership;
- terminology;
- requirements;
- architecture;
- interfaces/contracts;
- data/state definitions;
- lifecycle;
- failure modes;
- security/privacy;
- resource constraints;
- dependencies;
- implementation implications;
- validation strategy;
- acceptance criteria;
- traceability;
- authoritative references;
- open decisions;
- explicit non-goals;
- revision/change history.

No document is considered complete merely because it is long. It is complete when its claims, decisions, interfaces and acceptance criteria are sufficiently explicit to implement and validate without inventing critical missing behavior.

---

# 10. Implementation readiness gate

Novi may enter the first serious Brain implementation stage only when:

- [ ] Soul completion gate remains green.
- [ ] System Architecture has no unresolved P0 contradictions.
- [ ] Brain runtime contracts are explicit.
- [ ] Cognition implementation specification is complete.
- [ ] Memory implementation baseline is complete.
- [ ] Autonomy implementation specification is complete.
- [ ] Technology stack is selected and validated.
- [ ] Mac development environment is reproducible.
- [ ] Model candidates have been benchmarked.
- [ ] Perception pipeline has an implementation baseline.
- [ ] World Model implementation is defined.
- [ ] Time/synchronization semantics are defined.
- [ ] Simulation architecture is sufficient for the first closed-loop tests.
- [ ] Security P0 threat model exists.
- [ ] Deployment manifest exists.
- [ ] Validation hierarchy and acceptance evidence are defined.
- [ ] Cross-domain contracts have no unresolved ownership conflicts.

Physical robot implementation has an additional gate:

- [ ] Hardware selection/BOM complete.
- [ ] Mechanical/electrical architecture complete.
- [ ] Physical safety case complete.
- [ ] E-stop/watchdog/safe-state validated.
- [ ] Sensor calibration/synchronization validated.
- [ ] Controlled physical validation plan approved.

---

# 11. Change-control rule

This document is the program-level map, not the place to duplicate detailed domain specifications.

When a domain changes:

1. update its authoritative domain document;
2. update the affected completion state here;
3. update cross-domain dependencies;
4. update the readiness gate if necessary;
5. record the architectural decision/ADR when a technology or boundary changes;
6. re-run the relevant validation/traceability checks.

If this tracker conflicts with a domain authority, the conflict must be resolved explicitly; neither document should silently override the other.

---

# 12. Current next action

**Next document:** `COGNITION_IMPLEMENTATION_SPECIFICATION.md`

Before creating it:

1. audit all existing Cognition files for duplicate implementation material;
2. identify canonical Cognition ownership;
3. map existing contracts and schemas;
4. identify missing implementation details;
5. research current authoritative technologies;
6. write the specification;
7. validate it against Brain, Memory, Soul and Autonomy;
8. commit directly to `main`;
9. update this tracker.

This sequence continues until every domain reaches its completion gate.
