# 15 — Architecture File Audit & Gap Register

**Date:** 2026-08-17  
**Status:** P0 audit record  
**Scope:** Every file currently present in `docs/01-system-architecture/`.

## 1. Audit rule

Every architecture file is treated as critical/high importance.

For each file, the audit checks:

1. purpose and scope;
2. authority level;
3. terminology consistency;
4. cross-document dependencies;
5. interface completeness;
6. failure/recovery semantics;
7. security/privacy;
8. resource constraints;
9. technology assumptions;
10. source validation;
11. testability;
12. implementation readiness.

## 2. Current file inventory

The directory currently contains the system README, files `00` through `09`, plus newly established validation/decision documents and architecture files `12`–`14`. The original directory inventory included `00`–`09` and README. fileciteturn13file0L2-L3

## 3. File-by-file assessment

### README.md

**Role:** domain authority/index.

**Audit result:** Updated.

Critical fixes:

- removed stale Wheely identity;
- clarified authority hierarchy;
- added P0/P1/P2 document map;
- added validation and ADR documents;
- established future architecture interfaces.

### 00_HIGH_LEVEL_ARCHITECTURE.md

**Role:** system context.

**Audit result:** Updated.

Critical fixes:

- Novi standalone identity;
- vendor-neutral semantic boundary;
- model no longer treated as architectural authority;
- explicit governance/safety separation;
- hardware selection deferred until measured workload;
- runtime/simulation boundary strengthened.

### 01_DETAILED_SYSTEM_ARCHITECTURE.md

**Role:** cross-domain implementation architecture.

**Audit result:** Updated.

Critical fixes:

- explicit process boundaries;
- versioned model runtime interface;
- event envelope semantics;
- action/control hierarchy;
- resource and failure behavior;
- recovery/privacy requirements;
- ROS 2/ros2_control/Nav2 boundary;
- NVIDIA capability adapters.

### 02_ARCHITECTURAL_PRINCIPLES.md

**Role:** normative constraints.

**Audit result:** Updated.

Critical fixes:

- removed model-specific architectural dependency;
- added versioned contracts;
- added resource-bounded intelligence;
- added provenance/semantic-loss principles;
- added recovery/privacy principles;
- added evidence-backed technology adoption.

### 03_COMPONENT_BOUNDARIES.md

**Role:** ownership and dependency control.

**Audit result:** Updated.

Critical fixes:

- added explicit contract fields;
- added model-runtime, ros2_control and navigation ownership;
- strengthened security/authority boundaries;
- added NVIDIA implementation boundary.

### 04_RUNTIME_PROFILES.md

**Role:** deployment/runtime profiles.

**Audit result:** Updated.

Critical fixes:

- separated portable simulation from NVIDIA high-fidelity simulation;
- added HIL profile;
- replaced final hardware assumptions with candidate status;
- added version/compatibility validation;
- added promotion gates.

NVIDIA currently documents Isaac Sim ROS 2 integration with Jazzy and Ubuntu 24.04, supporting the current architecture candidate. citeturn0search4

### 05_CROSS_CUTTING_REQUIREMENTS.md

**Role:** system-wide non-functional/operational requirements.

**Audit result:** Updated.

Critical fixes:

- explicit resource/power/thermal coupling;
- measured-vs-derived telemetry;
- failure-state vocabulary;
- documentation traceability;
- versioned NVIDIA runtime compatibility.

### 06_107_DURABLE_STATE_EVENT_LOG_EXECUTION_SEMANTICS.md

**Role:** durable state/event semantics.

**Audit result:** Strong foundation; requires P0 implementation-baseline review.

Critical follow-up:

- reconcile its dependency references `95–106` against current authoritative domain documents;
- define the minimum Stage-1 local implementation subset separately from future distributed features;
- complete concrete event schemas in a dedicated contract location;
- benchmark candidate storage implementations;
- explicitly test crash/replay/idempotency semantics.

The semantic design itself is strong: immutable events, versioned state, provenance, snapshots and recovery are already defined. fileciteturn21file0L2-L2

### 07_108_TRANSACTIONS_CONCURRENCY_CONSISTENCY_AND_CONFLICT_RESOLUTION.md

**Role:** concurrency/consistency semantics.

**Audit result:** Strong foundation; P1 implementation follow-up.

Critical follow-up:

- map every state class to an explicit consistency level;
- define local-storage transaction semantics;
- create executable conflict test vectors;
- distinguish semantic conflicts from storage conflicts;
- document which guarantees are actually provided by the selected backend.

The document correctly distinguishes consistency contracts rather than assuming one universal model. fileciteturn22file0L2-L2

### 07_109_REPLICATION_SYNCHRONIZATION_AND_DISTRIBUTED_MEMORY_ARCHITECTURE.md

**Role:** distributed state.

**Audit result:** Strong future architecture; not a Stage-1 implementation blocker unless multiple nodes are required.

Critical follow-up:

- define replication only after 107/108 local semantics are implemented and tested;
- specify node identity and trust architecture in security domain;
- specify deletion/tombstone behavior jointly with 111;
- create partition/failover test scenarios;
- define authority/fencing model for physical actions.

The document correctly distinguishes strongly consistent, causally consistent, eventual, mergeable and local-only state. fileciteturn23file0L2-L2

### 08_110_RECOVERY_CHECKPOINTING_AND_DISASTER_RESILIENCE_ARCHITECTURE.md

**Role:** recovery/resilience.

**Audit result:** Strong foundation; requires implementation-specific RPO/RTO and recovery tests.

Critical follow-up:

- define Stage-1 local recovery contract;
- define checkpoint contents concretely;
- create restore/fault-injection matrix;
- define model/version compatibility on resume;
- define safe-stop behavior;
- test unknown external-side-effect outcomes.

The document correctly treats recovery as a governed state transition rather than a process restart. fileciteturn24file0L2-L2

### 09_111_PRIVACY_RETENTION_DEPENDENCY_AWARE_ERASURE_AND_DATA_LIFECYCLE_ARCHITECTURE.md

**Role:** privacy/data lifecycle.

**Audit result:** Strong foundation; requires concrete data classifications and retention schedules.

Critical follow-up:

- define Novi data classes;
- define purpose taxonomy;
- map all stores/replicas/backups;
- define deletion/tombstone schemas;
- define training-data boundary;
- define access-control matrix;
- create erasure/recovery integration tests.

The document correctly treats privacy as a lifecycle/dependency-graph property and cites ICO guidance for minimization/retention. fileciteturn25file0L2-L2

### 10_ARCHITECTURE_VALIDATION_AND_TRACEABILITY.md

**Role:** evidence governance.

**Audit result:** New P0 control document.

### 11_ARCHITECTURE_DECISION_FRAMEWORK.md

**Role:** ADR/technology governance.

**Audit result:** New P0 control document.

### 12_112_OBSERVABILITY_EVALUATION_AND_LIFESPAN_RELIABILITY.md

**Role:** observability and long-duration evaluation.

**Audit result:** New P1 architecture foundation.

### 13_113_RESOURCE_GOVERNANCE_SCHEDULING_AND_BUDGETS.md

**Role:** resource/power/thermal scheduling.

**Audit result:** New P1 architecture foundation.

### 14_114_MULTI_AGENT_COORDINATION_DELEGATION_AND_SHARED_MEMORY.md

**Role:** future multi-agent architecture.

**Audit result:** New P2 future architecture; explicitly deferred.

### 15_ARCHITECTURE_FILE_AUDIT.md

**Role:** this audit.

**Audit result:** active audit record; must be updated whenever architecture changes materially.

## 4. Cross-document gaps that remain

The directory is materially stronger, but the following work remains before the architecture domain is fully implementation-ready:

### ARCH-GAP-001 — Canonical contract schemas

Create authoritative schemas for:

- EventEnvelope;
- Observation;
- Evidence;
- WorldStateChange;
- MemoryRecord;
- KnowledgeRecord;
- Goal;
- Plan;
- ActionProposal;
- Authorization;
- SafetyDecision;
- ActionExecution;
- ActionOutcome;
- ModelInvocation;
- HardwareHealth;
- DeploymentManifest.

### ARCH-GAP-002 — Consistency mapping

Map each durable state class to the actual consistency guarantee required and provided.

### ARCH-GAP-003 — Local durable-state implementation decision

Select and benchmark the Stage-1 storage backend.

### ARCH-GAP-004 — Runtime version tuple

Freeze a tested development/simulation/edge compatibility tuple through ADRs.

### ARCH-GAP-005 — Safety architecture contract

Connect this system architecture to the dedicated safety/security domain and physical safety case.

### ARCH-GAP-006 — Time synchronization

Define system clock, sensor timestamps, ROS time, simulation time, hardware timestamps and drift handling.

### ARCH-GAP-007 — Resource budgets

Create measured initial budgets for development, simulation and edge workloads.

### ARCH-GAP-008 — Deployment manifest

Define the exact artifact/version manifest required to reproduce a Novi runtime.

### ARCH-GAP-009 — Architecture-to-test mapping

Populate requirement IDs and executable test IDs.

### ARCH-GAP-010 — Domain dependency audit

Verify every architecture dependency reference (especially 95–106) points to an existing current authoritative document and does not rely on stale numbering.

## 5. NVIDIA source validation baseline

Current authoritative NVIDIA sources used during this audit include:

- Jetson AGX Orin documentation: JetPack 7.2 / L4T r39.2. citeturn1search1
- Isaac Sim ROS 2 documentation: Humble/Jazzy recommended; Ubuntu 24.04/Jazzy workflow. citeturn0search4turn0search7
- Isaac ROS documentation: ROS 2 Jazzy compatibility. citeturn0search6
- DeepStream 9.1 documentation: Jetson Orin and JetPack 7.2/L4T r39.2 compatibility. citeturn0search0turn0search1
- DeepStream migration documentation: TensorRT 10.x compatibility/version constraints. citeturn0search9

These sources validate technology facts. They do not replace Novi's own benchmark and ADR process.

## 6. Architecture readiness

**Current status: P0 architecture consolidation — NOT YET IMPLEMENTATION READY.**

The system architecture is now sufficiently structured to continue closing the remaining gaps systematically.

The next work should be:

```text
Canonical schemas/contracts
        ↓
Stage-1 durable-state implementation decision
        ↓
Consistency mapping
        ↓
Time/synchronization architecture
        ↓
Safety/security contract integration
        ↓
Runtime/version ADRs
        ↓
Resource budgets
        ↓
Architecture validation matrix
        ↓
P0 architecture approval
```

No production implementation should begin before these gates are closed.
