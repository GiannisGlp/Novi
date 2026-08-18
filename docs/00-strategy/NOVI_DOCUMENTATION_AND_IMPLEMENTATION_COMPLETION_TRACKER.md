# Novi — Documentation & Implementation Completion Tracker

**Status:** Canonical master tracker  
**Priority:** P0 / critical  
**Owner:** Novi architecture and implementation program  
**Updated:** 2026-08-18  

---

## 1. Purpose

This is the canonical program-level tracker for closing the documentation, architecture, technology-selection, engineering, validation, security and deployment gaps before Novi enters serious implementation.

Every item is treated as a **critical/high-importance architectural artifact** unless explicitly downgraded by a documented decision.

This tracker does not replace domain authorities. Each domain owns its authoritative specifications, contracts, research evidence, decisions and acceptance criteria.

---

## 2. North-star completion rule

Novi is implementation-ready only when every required domain reaches its completion gate and the cross-domain traceability chain is closed:

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

A domain marked **COMPLETE** means its documentation and architectural decisions are sufficient for the current implementation stage. It does **not** mean production software or the physical robot is finished.

---

# 3. Program status — SYNCHRONIZED

| Domain | Current status | Current assessment | Immediate closure target |
|---|---|---|---|
| Soul | **COMPLETE** | ██████████ | Cross-domain stale-reference audit only |
| System Architecture | **IN PROGRESS** | █████████░ | Close ARCH-CLOSE-001..010 and pass architecture gate |
| Brain | **IN PROGRESS** | █████████░ | Close runtime/adapter/contracts and validation gaps |
| Cognition | **IN PROGRESS** | █████████░ | Complete implementation contracts, typed models and validation |
| Memory | **IN PROGRESS** | █████████░ | Complete concrete storage/retrieval implementation baseline |
| Autonomy | **IN PROGRESS** | ████████░░ | Complete executable autonomy/runtime specification |
| Hardware | **IN PROGRESS** | █████░░░░░ | Complete engineering baseline, BOM and safety case |
| Technology | **IN PROGRESS** | ██████░░░░ | Complete technology baseline, ADRs and compatibility evidence |
| Simulation | **IN PROGRESS** | ████░░░░░░ | Complete deterministic robot/sensor/world/SIL-HIL architecture |
| Validation | **IN PROGRESS** | ██████░░░░ | Complete unified evidence and release-gate hierarchy |
| Security | **IN PROGRESS** | █████░░░░░ | Complete physical-AI threat model and security validation |
| Deployment | **IN PROGRESS** | ████░░░░░░ | Complete reproducible manifests, artifact/version and rollback strategy |

**Important:** the previous tracker labels were stale relative to repository work completed after the tracker was created. This synchronization deliberately does **not** promote any domain to COMPLETE merely because documents now exist. Completion requires its documented gate and evidence.

---

# 4. Completion states

Use only these states:

- **NOT STARTED** — no authoritative work completed.
- **IN PROGRESS** — active documentation/research/engineering work.
- **BLOCKED** — cannot proceed until a named dependency is resolved.
- **REVIEW** — drafted and undergoing architecture/research validation.
- **VALIDATED** — requirements, sources, decisions and acceptance criteria checked.
- **COMPLETE** — domain completion gate satisfied for the current implementation phase.
- **SUPERSEDED** — replaced by a newer authoritative artifact; retained for traceability.

Never mark a domain COMPLETE merely because a document exists.

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

Soul owns enduring identity, personality, values, motivations, social disposition and behavioral continuity. Cognition, Memory, Autonomy, Brain, Policy and Hardware boundaries are explicit, with behavioral invariants and acceptance scenarios.

**Status: COMPLETE**

---

## 5.2 System Architecture — IN PROGRESS

### Authority
`docs/01-system-architecture/`

### Current work

The architecture has a strong foundation and now has an explicit closure register:

`docs/01-system-architecture/22_ARCHITECTURE_CLOSURE_AND_BASELINE.md`

The closure campaign contains:

1. canonical contracts;
2. consistency mapping;
3. Stage-1 durable storage;
4. runtime/version tuple;
5. safety integration;
6. time synchronization;
7. resource budgets;
8. deployment manifest;
9. architecture-to-test traceability;
10. dependency/numbering integrity.

### Exit criteria

- no unresolved P0 architecture contradiction;
- every system boundary has an owner;
- every P0 interface has one canonical contract;
- architecture validation and traceability gate passes;
- closure evidence exists for the ten ARCH-CLOSE workstreams.

**Status: IN PROGRESS — closure required**

---

## 5.3 Brain — IN PROGRESS

### Authority
`docs/02-novi-brain/`

### Completed/advanced work

- Brain implementation blueprint;
- Mac-first implementation strategy;
- runtime/component boundary definition;
- Soul adapter boundary;
- Cognition/Memory/Autonomy adapter direction;
- model invocation abstraction direction;
- health/degradation/recovery requirements.

### Must complete

- executable runtime component graph;
- scheduler/orchestrator semantics;
- event loop/lifecycle;
- model invocation implementation contract;
- Soul/Cognition/Memory/Autonomy adapters;
- Policy/Safety gateway;
- perception/audio/actuation adapters;
- backpressure/resource governance;
- Mac runtime profile;
- simulation/edge promotion path;
- runtime validation evidence.

### Important boundary
Soul owns identity/personality/values/affect semantics. Brain consumes these through an adapter and must not recreate a competing semantic authority.

**Status: IN PROGRESS — strong architecture, implementation closure pending**

---

## 5.4 Cognition — IN PROGRESS

### Authority
`docs/03-cognition/`

### Completed/advanced work

- `21_COGNITION_IMPLEMENTATION_SPECIFICATION.md`
- `22_COGNITIVE_DATA_CONTRACTS_AND_SCHEMAS.md`
- `25_COGNITIVE_CONTRACT_RECONCILIATION_AND_IMPLEMENTATION_BASELINE.md`
- `26_COGNITIVE_TYPED_MODEL_IMPLEMENTATION_BASELINE.md`
- existing World Model, multimodal cognition, reasoning, uncertainty/provenance, identity/social cognition and prediction specifications.

### Must complete

- typed model implementation;
- JSON Schema generation;
- structural/semantic/provenance validators;
- replay fixtures;
- World Model runtime;
- Situation Model runtime;
- attention/social cognition runtime;
- reasoning/prediction runtime;
- model routing;
- resource/update-rate budgets;
- degraded modes and recovery;
- Brain/Memory/Autonomy integration;
- benchmark and validation evidence.

### Exit criteria

The Mac Brain can instantiate Cognition from explicit components and contracts without inventing missing semantics, and the resulting implementation passes its contract/replay/behavioral validation.

**Status: IN PROGRESS — implementation layer established, validation pending**

---

## 5.5 Memory — IN PROGRESS

### Authority
`docs/04-memory-and-knowledge/`

### Must complete

- concrete local durable-event implementation;
- structured state store decision;
- episodic/semantic/relationship/autobiographical memory implementation;
- vector retrieval and knowledge graph decisions;
- embedding/reranking strategy;
- retention/forgetting execution;
- provenance/privacy/erasure implementation;
- schema migration;
- backup/recovery;
- indexing and performance budgets;
- Mac storage baseline.

### Exit criteria

A complete memory write → persist → retrieve → update → forget → recover cycle is implementable, reproducible and testable on Mac.

**Status: IN PROGRESS — architecture strong, implementation baseline pending**

---

## 5.6 Autonomy — IN PROGRESS

### Authority
`docs/02-autonomy/`

### Must complete

- attention manager;
- goals/priorities;
- initiative/interruption policy;
- idle behavior and curiosity;
- planning/replanning;
- commitment handling;
- action proposal/selection/cancellation;
- resource budgets;
- degradation;
- policy/safety integration;
- execution feedback;
- cross-domain contracts;
- runtime tests.

### Exit criteria

Novi can continuously decide whether to attend, wait, speak, investigate, plan or act without bypassing Soul, Cognition, Memory or Safety ownership.

**Status: IN PROGRESS — implementation pending**

---

## 5.7 Hardware — IN PROGRESS

### Authority
`docs/05-hardware/`

### Must complete

- compute;
- cameras/depth/LiDAR;
- IMU;
- microphones/audio;
- displays/lighting if required;
- actuators and motor controllers;
- power/BMS/thermal;
- networking/storage;
- tactile sensing;
- emergency stop/watchdogs;
- connectivity-loss behavior;
- calibration/synchronization;
- mechanical/electrical architecture;
- interfaces/connectors;
- BOM and sourcing/replacement strategy;
- serviceability;
- physical safety case;
- validation plan.

### Exit criteria

Every physical subsystem has a selected baseline, alternative, interface, power/thermal requirements, safety considerations, calibration procedure and validation criteria.

**Status: IN PROGRESS — P0 before physical actuation**

---

## 5.8 Technology — IN PROGRESS

### Authority
`docs/TECHNOLOGY_REFERENCE.md`, `docs/TECHNOLOGY_STACK_BASELINE.md` and applicable ADRs.

### Must complete

Create and validate the canonical implementation stack for:

- OS and language/runtime boundaries;
- Python/C++/Rust policy;
- ROS 2 and middleware/DDS/RMW;
- ros2_control and Navigation2;
- simulation;
- perception/audio/STT/TTS;
- LLM/VLM/embedding/reranking runtimes;
- inference serving;
- databases/vector retrieval/knowledge graph/event log;
- observability;
- containers/CI;
- model/artifact/dataset versioning;
- secrets and updates/OTA;
- CAD/URDF/USD;
- firmware tooling.

### Decision rule
Every adopted technology requires requirement mapping, candidate comparison, authoritative-source validation, license/security review, platform compatibility review, benchmark/PoC where material, and an explicit ADR/selection record.

**Status: IN PROGRESS — P0 technology selection**

---

## 5.9 Simulation — IN PROGRESS

### Must complete

- robot URDF/Xacro;
- USD representation;
- physics parameters;
- sensor/environment models;
- CAD → URDF/USD pipeline;
- human/agent simulation;
- noise/failure models;
- deterministic seeds;
- scenario schema and ground truth;
- SIL/HIL architecture;
- simulation provenance;
- sim-to-real validation.

### Exit criteria

A deterministic scenario can run Novi's cognitive/runtime stack against a simulated embodied world and produce measurable ground-truth comparisons.

**Status: IN PROGRESS — incomplete**

---

## 5.10 Validation — IN PROGRESS

### Required hierarchy

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

- requirement traceability;
- test ownership;
- test data and ground truth;
- behavioral/cognitive metrics;
- latency/resource budgets;
- safety/recovery metrics;
- model evaluation;
- simulation/physical evaluation;
- regression policy;
- longitudinal evaluation;
- acceptance evidence;
- release gates.

**Status: IN PROGRESS — P0 unification required**

---

## 5.11 Security — IN PROGRESS

### Must create

A consolidated physical-AI threat model covering prompt/tool abuse, memory/model/dataset poisoning, sensor spoofing, adversarial perception, unauthorized model updates, compromised dependencies/supply chain, credential/network/inference compromise, privacy leakage, physical access, firmware compromise and update/rollback attacks.

### Must define

- threat actors;
- assets;
- trust boundaries;
- attack paths;
- controls;
- monitoring;
- incident response/recovery;
- security tests;
- residual risk.

**Status: IN PROGRESS — P0**

---

## 5.12 Deployment — IN PROGRESS

### Must create

A reproducible deployment architecture for:

- Mac development;
- simulation;
- edge;
- physical robot;
- OS/firmware/ROS versions;
- CUDA/TensorRT/Isaac where applicable;
- containers and dependencies;
- model hashes/versions;
- datasets/configuration;
- database schema;
- secrets;
- artifact registry;
- release manifests;
- rollback/OTA;
- health checks;
- migrations.

### Exit criteria

Given a versioned deployment manifest, another machine can reproduce the same Novi software/runtime environment within defined tolerances.

**Status: IN PROGRESS — P0**

---

# 6. Cross-domain P0 workstreams

## X-001 — Canonical contracts

Every interface has one authoritative owner. The current closure campaign is `ARCH-CLOSE-001` in `22_ARCHITECTURE_CLOSURE_AND_BASELINE.md`.

Canonical system-level contracts must be reconciled with domain semantic models before executable schemas are created. Cognition, Memory, Autonomy, Brain and Hardware must not silently create competing system-level authorities.

**Status: IN PROGRESS — reconciliation required.**

## X-002 — Time and synchronization

Define system, monotonic, ROS, simulation, sensor and hardware clocks; timestamp semantics; synchronization; drift; ordering and failure behavior.

**Status: IN PROGRESS — P0.**

## X-003 — Observability

Trace the complete causal path:

```text
sensor → perception → evidence → world state → memory → cognition → autonomy → policy → action → outcome
```

**Status: IN PROGRESS — P0.**

## X-004 — Resource governance

Define CPU/GPU/RAM/unified-memory/storage/network/power/thermal budgets for Mac-first and future edge targets.

**Status: IN PROGRESS — P0.**

## X-005 — Data/model provenance

Every model, dataset, learned behavior and durable memory artifact must have provenance, version and lifecycle semantics.

**Status: IN PROGRESS — P0.**

## X-006 — Failure and degradation

Define behavior when sensors, models, memory, network, GPU, storage, speech, navigation or actuators fail.

**Status: IN PROGRESS — P0.**

---

# 7. System Architecture closure sequence

The program is currently working through System Architecture closure before starting another major implementation phase:

```text
ARCH-CLOSE-001  Canonical contracts             🟠 reconciliation required
ARCH-CLOSE-002  Consistency mapping             🟡
ARCH-CLOSE-003  Stage-1 durable storage         🟡
ARCH-CLOSE-004  Runtime/version tuple           🟡
ARCH-CLOSE-005  Safety integration              🟡
ARCH-CLOSE-006  Time synchronization            🟡
ARCH-CLOSE-007  Resource budgets                🟡
ARCH-CLOSE-008  Deployment manifest             🟡
ARCH-CLOSE-009  Architecture → test mapping     🟡
ARCH-CLOSE-010  Dependency/numbering integrity  🟡
                         ↓
                Final architecture audit
                         ↓
              SYSTEM ARCHITECTURE COMPLETE
```

**Current work item:** ARCH-CLOSE-001 — reconcile canonical system contracts with the master data/artifact catalog and domain contracts, assign one authority to every contract/artifact type, then create the executable contract registry and schemas.

---

# 8. Global completion rule

No new major implementation phase begins merely because one domain becomes sufficiently mature.

The program enters serious Brain implementation only when:

```text
ALL 12 DOMAINS = COMPLETE
        +
ALL P0 CROSS-DOMAIN GATES = COMPLETE
        +
NO P0 CONTRADICTIONS
        +
NO DUPLICATE AUTHORITIES
        +
ALL P0 REQUIREMENTS HAVE VALIDATION EVIDENCE
        +
MAC ENVIRONMENT IS REPRODUCIBLE
        +
DEPLOYMENT STRATEGY IS REPRODUCIBLE
        ↓
GLOBAL READINESS
        ↓
MAC BRAIN STAGE 0
```

Physical robot implementation additionally requires the hardware engineering and physical safety gates.

---

# 9. Research and validation policy

Every critical document must be researched against valid primary or authoritative sources where applicable.

Preferred source order:

1. official NVIDIA documentation for NVIDIA technologies;
2. official ROS documentation for ROS technologies;
3. official Apple documentation for Apple Silicon/macOS/MLX;
4. official project documentation for adopted open-source projects;
5. peer-reviewed research for scientific claims;
6. applicable standards/specifications;
7. reputable secondary sources only where primary documentation is insufficient.

Every claim must distinguish between:

- source-backed fact;
- Novi architectural inference;
- Novi adoption decision;
- validated implementation result.

Technology selections require benchmarking or a PoC when the decision materially affects performance, compatibility, safety or architecture.

---

# 10. Documentation quality gate

Every critical document must contain, where applicable:

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

No document is complete merely because it is long. It is complete when its claims, decisions, interfaces and acceptance criteria are sufficiently explicit to implement and validate without inventing critical missing behavior.

---

# 11. Change-control rule

When a domain changes:

1. update its authoritative domain document;
2. update the affected completion state here;
3. update cross-domain dependencies;
4. update the readiness gate if necessary;
5. record the ADR when a technology or boundary changes;
6. re-run the relevant validation/traceability checks.

If this tracker conflicts with a domain authority, resolve the conflict explicitly; neither document silently overrides the other.

---

# 12. Current program position

The repository has moved from broad conceptual documentation into **architecture closure and implementation-readiness work**. The next work is not to start code prematurely; it is to close the remaining P0/P1 gates systematically.

Current highest-priority sequence:

```text
1. System Architecture closure
      ↓
2. Canonical contract reconciliation
      ↓
3. Executable contract registry/schemas
      ↓
4. Remaining architecture P0 gates
      ↓
5. Re-synchronize this tracker
      ↓
6. Close the next program-status domain
```

This tracker must be updated whenever a domain, cross-domain gate or authoritative dependency materially changes.