# Novi — Documentation & Implementation Completion Tracker

**Status:** Canonical master tracker  
**Priority:** P0 / critical  
**Owner:** Novi architecture and implementation program  
**Updated:** 2026-08-19  

> **SUPERSEDED for implementation-state claims (2026-08-26).** This tracker remains the
> authority for the *documentation/architecture closure* program, but its implementation-state
> claims (Brain/Cognition/Memory/Autonomy "IN PROGRESS — implementation pending", the
> `MAC_BRAIN`/`brain` split, "MAC BRAIN STAGE 0") are out of date. The code is now a single
> unified `novi/brain/` package with 1,529 passing tests. See
> [`STATUS_2026-08-26.md`](STATUS_2026-08-26.md) for the current source of truth and
> [`../audits/NOVI_CONSOLIDATED_GAP_ANALYSIS_2026-08-26.md`](../audits/NOVI_CONSOLIDATED_GAP_ANALYSIS_2026-08-26.md)
> for the reconciled gap list.

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
| System Architecture | **COMPLETE** | ██████████ | Architecture closure complete; integrity gate passed |
| Brain | **IN PROGRESS** | ██████████ | Complete remaining Brain domain completion gate |
| Cognition | **IN PROGRESS** | █████████░ | Complete implementation contracts, typed models and validation |
| Memory | **IN PROGRESS** | █████████░ | Complete concrete storage/retrieval implementation baseline |
| Autonomy | **IN PROGRESS** | ████████░░ | Complete executable autonomy/runtime specification |
| Hardware | **IN PROGRESS** | █████░░░░░ | Complete engineering baseline, BOM and safety case |
| Technology | **IN PROGRESS** | ██████░░░░ | Complete technology baseline, ADRs and compatibility evidence |
| Simulation | **IN PROGRESS** | ████░░░░░░ | Complete deterministic robot/sensor/world/SIL-HIL architecture |
| Validation | **IN PROGRESS** | ██████░░░░ | Complete unified evidence and release-gate hierarchy |
| Security | **IN PROGRESS** | █████░░░░░ | Complete physical-AI threat model and security validation |
| Deployment | **IN PROGRESS** | ████░░░░░░ | Complete reproducible manifests, artifact/version and rollback strategy |

**Important:** System Architecture is now marked COMPLETE because the ten ARCH-CLOSE workstreams have been closed and the final architecture-integrity validation passed. This does not promote any downstream implementation domain to COMPLETE. Downstream domains retain their existing evidence-based status.

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

## 5.2 System Architecture — COMPLETE

### Authority
`docs/01-system-architecture/`

### Completed scope

The System Architecture closure campaign has completed all ten P0 workstreams:

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

The final dependency/numbering integrity gate was closed through executable repository validation. The validation evidence is recorded in:

`docs/01-system-architecture/39_ARCH_CLOSE_010_VALIDATION_EVIDENCE_2026-08-19.md`

The architecture-integrity validator is:

`scripts/validate_architecture_integrity.py`

and its CI workflow is:

`.github/workflows/architecture-integrity-validation.yml`

### Final closure evidence

```text
ARCH-CLOSE-001  CLOSED
ARCH-CLOSE-002  CLOSED
ARCH-CLOSE-003  CLOSED
ARCH-CLOSE-004  CLOSED
ARCH-CLOSE-005  CLOSED
ARCH-CLOSE-006  CLOSED
ARCH-CLOSE-007  CLOSED
ARCH-CLOSE-008  CLOSED
ARCH-CLOSE-009  CLOSED
ARCH-CLOSE-010  CLOSED
                         ↓
             SYSTEM ARCHITECTURE COMPLETE
```

### Reconciliation: COMPLETE vs PARTIALLY EVIDENCED (2026-08-22, gap-analysis Step 0)

Two closure-evidence documents (`43_ARCH_CLOSE_005_SAFETY_INTEGRATION_EVIDENCE.md`,
`44_ARCH_CLOSE_006_TIME_VALIDATION_EVIDENCE.md`) carry **Status: PARTIALLY EVIDENCED**.
This is not a contradiction with the domain status above: COMPLETE means the
architecture and its executable closure evidence are sufficient for the current
**software/no-hardware** stage. The PARTIALLY EVIDENCED designation on those two
files refers to *physical-world* validation (hardware safety integration,
physical sensor-clock synchronization and long-duration drift budgets) that is
deferred until hardware-in-loop exists. Those items must **re-open** the
corresponding ARCH-CLOSE items when hardware arrives; they do not block the
current Brain phase.

### Completion gate

- no unresolved P0 architecture contradiction identified in the closure campaign;
- system boundaries and ownership are established;
- P0 interface authority is explicitly governed;
- architecture validation and traceability gates are closed;
- closure evidence exists for all ten ARCH-CLOSE workstreams;
- repository dependency/numbering integrity validation passes.

### Scope boundary

**COMPLETE** means the system architecture and its closure evidence are sufficient for the current implementation stage. It does **not** mean the Brain, Cognition, Memory, Autonomy, Hardware, Technology, Simulation, Validation, Security or Deployment implementation domains are complete.

**Status: COMPLETE — System Architecture closure achieved 2026-08-19.**

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

**Status: IN PROGRESS — B0 complete; B1 closed-loop integration gate complete; remaining Brain domain completion work continues**

### Current Brain implementation progress

| Stage | Status | Evidence | Next |
|---|---|---|---|
| B0 Runtime Foundation | **COMPLETE** | Integrated B0 Stage Gate passed; `30_BRAIN_B0_STAGE_GATE_EVIDENCE_2026-08-19.md` | Closed |
| B1.1 Closed Simulated Loop | **VALIDATED** | GitHub Actions Brain runtime validation | Closed |
| B1.2 Multi-Event World State | **VALIDATED** | GitHub Actions Brain runtime validation | Closed |
| B1.3 Cognition Integration | **VALIDATED** | GitHub Actions Brain runtime validation; 48/48 tests passed | Closed |
| B1.4 Memory Integration | **VALIDATED** | GitHub Actions Brain CI passed | Closed |
| B1.5 Autonomy / ActionProposal | **VALIDATED** | GitHub Actions Brain CI passed | Closed |
| B1.6 Outcome + Replay | **VALIDATED** | GitHub Actions Brain CI passed | Closed |
| B1.7 Authorization / Safety | **VALIDATED** | GitHub Actions Brain CI passed | Closed |
| B1.8 Simulated Execution | **VALIDATED** | GitHub Actions Brain CI passed; fail-closed safety requirement validated | Closed |
| B1 Integration Gate | **COMPLETE** | End-to-end B1 gate passed in GitHub Actions; PR #12 merged to `main` | Closed |

B1 remains an implementation stage inside Brain and does not constitute Brain domain completion.

### B1 completion gate

The B1 closed cognitive-control loop has been integrated and validated end-to-end:

```text
World
  ↓
Temporal World Model
  ↓
Cognition
  ↓
Memory
  ↓
Autonomy / ActionProposal
  ↓
Authorization + Safety
  ↓
Simulated Execution
  ↓
Outcome Evaluation
  ↓
Replay
```

The gate validates deterministic semantic composition, explicit authorization/safety requirements, simulated-only execution, successful outcome evaluation, replay recording and denial of unauthorized execution. The B1 integration gate is evidence for the Brain implementation stage only; it does not close the full Brain domain.

**B1 STATUS: COMPLETE — closed-loop integration gate passed 2026-08-19.**

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

**Status: COMPLETE for current architecture closure; executable registry/schema evidence retained in ARCH-CLOSE-001 artifacts.**

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

The System Architecture closure sequence is complete:

```text
ARCH-CLOSE-001  Canonical contracts             CLOSED
ARCH-CLOSE-002  Consistency mapping             CLOSED
ARCH-CLOSE-003  Stage-1 durable storage         CLOSED
ARCH-CLOSE-004  Runtime/version tuple           CLOSED
ARCH-CLOSE-005  Safety integration              CLOSED
ARCH-CLOSE-006  Time synchronization            CLOSED
ARCH-CLOSE-007  Resource budgets                CLOSED
ARCH-CLOSE-008  Deployment manifest             CLOSED
ARCH-CLOSE-009  Architecture → test mapping     CLOSED
ARCH-CLOSE-010  Dependency/numbering integrity  CLOSED
                         ↓
                Final architecture audit
                         ↓
              SYSTEM ARCHITECTURE COMPLETE
```

**Current work item:** System Architecture closure is complete. The next program implementation sequence is Brain B1, while remaining cross-domain P0 work continues under the canonical program gates.

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

The repository has moved from broad conceptual documentation into **architecture closure and implementation-readiness work**. System Architecture closure is now complete, and the Brain implementation program has completed the B1 closed simulated cognitive-control loop integration gate.

Current highest-priority sequence:

```text
1. System Architecture closure                     COMPLETE
      ↓
2. Brain B0 Runtime Foundation                    COMPLETE
      ↓
3. Brain B1.1 Closed Simulated Loop               VALIDATED
      ↓
4. Brain B1.2 Multi-Event World State             VALIDATED
      ↓
5. Brain B1.3 Cognition Integration               VALIDATED / CI
      ↓
6. Brain B1.4 Memory Integration                  VALIDATED / CI
      ↓
7. Brain B1.5 Autonomy / ActionProposal            VALIDATED / CI
      ↓
8. Brain B1.6 Outcome + Replay                    VALIDATED / CI
      ↓
9. Brain B1.7 Authorization / Safety              VALIDATED / CI
      ↓
10. Brain B1.8 Simulated Execution                 VALIDATED / CI
      ↓
11. Brain B1 Integration Gate                     COMPLETE / CI
      ↓
12. Remaining Brain domain completion work        NEXT
      ↓
13. Re-synchronize this tracker at each gate
      ↓
14. Close the next program-status domain
```

This tracker must be updated whenever a domain, cross-domain gate or authoritative dependency materially changes.
