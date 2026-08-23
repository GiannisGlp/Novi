# 50 — ARCH-CLOSE-009 Final Traceability Matrix — 2026-08-19

**Status:** CLOSED — architecture traceability gate satisfied for the current implementation phase  
**Priority:** P0 / critical / high importance  
**Authority:** System Architecture closure process  
**Closure item:** ARCH-CLOSE-009  
**Supersedes as closure evidence:** `49_ARCH_CLOSE_009_TRACEABILITY_BASELINE_2026-08-19.md`  
**Companion authority:** `48_ARCH_CLOSE_009_IMPLEMENTATION_TRACEABILITY_GATE.md`  
**Companion validation matrix:** `37_ARCH_CLOSE_009_ARCHITECTURE_TO_TEST_MAPPING.md`

---

## 1. Executive decision

ARCH-CLOSE-009 is **CLOSED** for Novi's current implementation phase.

The closure is an **architecture traceability closure**, not a claim that Novi's complete runtime, physical robot, learned models, hardware or production deployment already exist.

The gate is satisfied because every P0 architecture invariant in the canonical 30-item validation matrix has:

1. an identifiable architectural requirement;
2. an authoritative document or closure artifact;
3. a contract, interface, validation path, measured evidence path, or explicit justified deferral;
4. an identified test/evidence class;
5. an explicit status and limitation;
6. no unresolved `GAP` classification.

Implementation-dependent work that is not yet appropriate for the current Mac-first phase is explicitly classified as `DEFERRED`, rather than being represented as implemented.

This distinction is mandatory: documentation existence is never treated as implementation evidence.

---

## 2. Closure vocabulary

| Status | Meaning in this matrix |
|---|---|
| IMPLEMENTED | Executable implementation exists and is the intended implementation anchor for the current phase. |
| CONTRACTED | Normative contract/schema/interface exists and is subject to executable validation. |
| TESTED | Executable validation demonstrates the requirement at the applicable layer. |
| EVIDENCED | Measured/repository evidence exists, but it does not by itself prove complete implementation or physical validation. |
| DEFERRED | Intentionally postponed because it requires a later implementation, model, simulation, hardware or deployment phase. |
| GAP | Required architecture has no adequate implementation, evidence, validation path or justified deferral. **No GAP is permitted for closure.** |

A deferred item is not an architectural failure when the architecture explicitly identifies its trigger, required evidence and boundary.

---

## 3. Evidence classes

| Code | Evidence class |
|---|---|
| D | Document/static validation |
| U | Unit/contract validation |
| I | Integration validation |
| S | Simulation/replay validation |
| H | Hardware-in-the-loop validation |
| P | Physical safety validation |
| L | Long-duration/soak validation |
| B | Benchmark/performance evidence |
| R | Recovery/fault-injection evidence |

The absence of H/P/L evidence today is not treated as a gap where the requirement explicitly belongs to the future physical platform.

---

# 4. Final P0 traceability matrix

## T-001 — Canonical contracts have one authoritative schema/owner

| Field | Mapping |
|---|---|
| Requirement | Every cross-domain contract has one semantic authority and implementation/schema ownership cannot silently become semantic authority. |
| Authority | `16_CANONICAL_SYSTEM_CONTRACTS.md`; `24_ARCHITECTURE_CONTRACT_OWNERSHIP_RECONCILIATION.md`; `38_ARCH_CLOSE_010_DEPENDENCY_NUMBERING_INTEGRITY_AUDIT.md` |
| Contract/API | Canonical contract registry and versioned JSON Schemas under `contracts/` |
| Implementation | Contract validation tooling and registry artifacts |
| Test | Contract validation workflow and positive/negative fixtures |
| Evidence | `25_ARCH_CLOSE_001_VALIDATION_EVIDENCE.md`; `novi/contracts/tests/README.md` |
| Status | TESTED / EVIDENCED |
| Limitation | Domain implementation may still expand the contract set; additions must follow the canonical ownership rule. |

## T-002 — Positive contract fixtures validate

| Field | Mapping |
|---|---|
| Requirement | Valid contract fixtures must be accepted by the executable schema/contract validation layer. |
| Authority | `25_ARCH_CLOSE_001_VALIDATION_EVIDENCE.md`; `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md` |
| Contract/API | Versioned schemas under `contracts/` |
| Implementation | Contract test suite |
| Test | Positive fixture validation in contract CI |
| Evidence | `25_ARCH_CLOSE_001_VALIDATION_EVIDENCE.md`; `novi/contracts/tests/README.md` |
| Status | TESTED |
| Limitation | This proves contract validation, not every future domain runtime consumer. |

## T-003 — Negative contract fixtures are rejected

| Field | Mapping |
|---|---|
| Requirement | Invalid or semantically prohibited fixtures must fail validation. |
| Authority | `25_ARCH_CLOSE_001_VALIDATION_EVIDENCE.md`; `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md` |
| Contract/API | Versioned JSON Schemas and semantic validation rules |
| Implementation | Negative-fixture contract tests |
| Test | Contract CI negative validation |
| Evidence | `25_ARCH_CLOSE_001_VALIDATION_EVIDENCE.md`; `novi/contracts/tests/README.md` |
| Status | TESTED |
| Limitation | Runtime semantic checks beyond schema scope remain domain implementation work. |

## T-004 — Schema evolution preserves declared compatibility rules

| Field | Mapping |
|---|---|
| Requirement | Contract/schema changes must obey declared compatibility and versioning rules. |
| Authority | `17_CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD.md`; `24_ARCHITECTURE_CONTRACT_OWNERSHIP_RECONCILIATION.md` |
| Contract/API | Versioned contract paths and compatibility fixtures |
| Implementation | Compatibility validation suite |
| Test | Compatibility CI |
| Evidence | `novi/contracts/tests/compatibility/README.md`; repository contract validation workflow |
| Status | TESTED |
| Limitation | Compatibility policy must be re-evaluated when a contract introduces a breaking semantic change. |

## T-005 — Durable state has explicit source-of-truth ownership

| Field | Mapping |
|---|---|
| Requirement | Durable state, projections, caches and replicas have explicit ownership and consistency semantics. |
| Authority | `26_ARCH_CLOSE_002_CONSISTENCY_STATE_CLASS_MATRIX.md`; `22_ARCHITECTURE_CLOSURE_AND_BASELINE.md` |
| Contract/API | State-class/consistency mapping; durable-state interfaces |
| Implementation | Stage-1 storage validation assets; durable event/state architecture |
| Test | Consistency mapping validation and storage validation |
| Evidence | `35_ARCH_CLOSE_002_CONSISTENCY_MAPPING_VALIDATION.md`; storage validation corpus |
| Status | TESTED / EVIDENCED |
| Limitation | Concrete runtime memory components remain implementation work. |

## T-006 — Safety/authorization state is not eventually consistent authority

| Field | Mapping |
|---|---|
| Requirement | Safety and authorization authority cannot depend on eventually consistent state when that would permit unsafe action. |
| Authority | `20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md`; `43_ARCH_CLOSE_005_SAFETY_INTEGRATION_EVIDENCE.md` |
| Contract/API | Authorization and safety decision contracts |
| Implementation | Safety/authorization integration gate |
| Test | Safety integration validation |
| Evidence | `43_ARCH_CLOSE_005_SAFETY_INTEGRATION_EVIDENCE.md` |
| Status | TESTED / EVIDENCED |
| Limitation | HIL/physical actuator evidence remains deferred until hardware exists. |

## T-007 — Action proposal cannot directly execute physical action

| Field | Mapping |
|---|---|
| Requirement | A model/planner/action proposal must pass governance, authorization and safety before physical execution. |
| Authority | `20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md`; canonical ActionProposal/Authorization/SafetyDecision/ActionExecution contracts |
| Contract/API | `contracts/autonomy/action-proposal/`; execution and authorization contracts |
| Implementation | Safety gateway boundary is defined and validated at software level |
| Test | Safety integration validation |
| Evidence | `43_ARCH_CLOSE_005_SAFETY_INTEGRATION_EVIDENCE.md` |
| Status | TESTED / EVIDENCED |
| Limitation | Physical actuator enforcement is DEFERRED to HIL/physical validation. |

## T-008 — Emergency stop is independent of cognition/model runtime

| Field | Mapping |
|---|---|
| Requirement | Emergency stop must remain effective independently of Brain/model availability. |
| Authority | `20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md`; hardware safety architecture |
| Contract/API | Hardware health/safety boundary and emergency-stop interface |
| Implementation | Physical emergency-stop implementation is not yet present because the robot platform is not yet selected/built. |
| Test | H/P physical safety validation |
| Evidence | Architecture-defined physical validation gate |
| Status | DEFERRED |
| Limitation | Trigger: first physical platform. Required evidence: independent E-stop response, actuator isolation, watchdog interaction and fault injection. |

## T-009 — Storage commits satisfy declared durability semantics

| Field | Mapping |
|---|---|
| Requirement | Durable commits must satisfy the declared persistence and recovery semantics. |
| Authority | `18_STAGE_1_DURABLE_STATE_STORAGE_ADR.md`; `27_ARCH_CLOSE_003_STAGE_1_STORAGE_BENCHMARK_SPEC.md`; `39_ARCH_CLOSE_003_STORAGE_VALIDATION_RUNBOOK.md` |
| Contract/API | Durable event/state storage interface |
| Implementation | SQLite Stage-1 validation backend and recovery harness |
| Test | Storage benchmark and recovery validation |
| Evidence | `41_ARCH_CLOSE_003_SQLITE_RECOVERY_VALIDATION.md`; `scripts/sqlite_recovery_validation.py` |
| Status | EVIDENCED / TESTED |
| Limitation | Process-kill, storage-full, permission, deeper concurrency, interrupted-backup and long-soak campaigns remain residual validation. |

## T-010 — Crash recovery reconstructs valid state

| Field | Mapping |
|---|---|
| Requirement | Recovery must reconstruct internally valid state after interruption/failure. |
| Authority | Storage/recovery architecture and ARCH-CLOSE-003 runbook |
| Contract/API | Durable state/recovery contract |
| Implementation | SQLite recovery harness |
| Test | Recovery/reopen/checkpoint/rollback validation |
| Evidence | `41_ARCH_CLOSE_003_SQLITE_RECOVERY_VALIDATION.md` |
| Status | TESTED / EVIDENCED |
| Limitation | Current evidence covers the defined recovery scenarios; arbitrary process termination and prolonged stress remain later validation. |

## T-011 — Idempotent retries cannot duplicate logical transitions

| Field | Mapping |
|---|---|
| Requirement | Retried operations must not create duplicate logical state transitions. |
| Authority | Consistency/state-class architecture; storage recovery runbook |
| Contract/API | Event identity/idempotency semantics |
| Implementation | SQLite recovery validation harness |
| Test | Duplicate-event rejection/retry validation |
| Evidence | `41_ARCH_CLOSE_003_SQLITE_RECOVERY_VALIDATION.md` |
| Status | TESTED |
| Limitation | Full runtime distributed retry behavior remains later implementation validation. |

## T-012 — Concurrent stale writes are rejected/reconciled by contract

| Field | Mapping |
|---|---|
| Requirement | Revision/concurrency semantics must prevent silent stale-state corruption. |
| Authority | `26_ARCH_CLOSE_002_CONSISTENCY_STATE_CLASS_MATRIX.md`; storage architecture |
| Contract/API | Revision/transaction/concurrency semantics |
| Implementation | SQLite validation harness for stale-revision behavior |
| Test | Stale-revision rejection plus concurrency validation path |
| Evidence | `41_ARCH_CLOSE_003_SQLITE_RECOVERY_VALIDATION.md` |
| Status | TESTED / EVIDENCED |
| Limitation | Higher-contention and multi-process stress remains residual validation. |

## T-013 — Projection/index/cache state is rebuildable

| Field | Mapping |
|---|---|
| Requirement | Derived state must be reconstructable from authoritative durable state. |
| Authority | Consistency/state-class matrix; memory/storage architecture |
| Contract/API | Projection/index/cache lifecycle semantics |
| Implementation | Rebuild architecture is defined; full runtime projection implementation remains pending |
| Test | Integration/replay/rebuild validation path |
| Evidence | Architecture and recovery design; implementation evidence deferred |
| Status | DEFERRED |
| Limitation | Trigger: concrete memory/index implementation. Required evidence: delete/rebuild/replay and equivalence checks. |

## T-014 — Deployment manifest identifies exact runtime/model/config state

| Field | Mapping |
|---|---|
| Requirement | A deployment must identify the exact software, runtime, model, configuration and hardware identity required for reproducibility. |
| Authority | `20_DEPLOYMENT_MANIFEST_SPECIFICATION.md`; `36_ARCH_CLOSE_008_DEPLOYMENT_MANIFEST.md` |
| Contract/API | `contracts/deployment/deployment-manifest/1.0.0/schema.json` |
| Implementation | Deployment-manifest schema/validation assets |
| Test | Manifest structural/compatibility validation path |
| Evidence | ARCH-CLOSE-008 closure corpus |
| Status | CONTRACTED / TESTED |
| Limitation | Final physical hardware fields are necessarily deferred until platform selection. |

## T-015 — Incompatible deployment tuples are rejected before authority begins

| Field | Mapping |
|---|---|
| Requirement | An incompatible runtime/model/configuration tuple must fail before the system becomes an authoritative runtime. |
| Authority | `22_RUNTIME_VERSION_COMPATIBILITY_AND_LIFECYCLE.md`; `29_ARCH_CLOSE_004_RUNTIME_VERSION_COMPATIBILITY_TUPLE.md` |
| Contract/API | Runtime/version compatibility tuple and deployment manifest |
| Implementation | Compatibility validation assets |
| Test | Compatibility gate |
| Evidence | ARCH-CLOSE-004/008 closure corpus |
| Status | TESTED / EVIDENCED |
| Limitation | Final hardware-specific compatibility remains deferred. |

## T-016 — Event/sensor timestamps preserve required temporal semantics

| Field | Mapping |
|---|---|
| Requirement | Timestamp domain, provenance, ordering and uncertainty must be explicit and preserved. |
| Authority | `19_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md`; `44_ARCH_CLOSE_006_TIME_VALIDATION_EVIDENCE.md` |
| Contract/API | Event/observation timestamp and provenance semantics |
| Implementation | Time validation integration assets |
| Test | `test_time_semantics.py` / time validation gate |
| Evidence | `44_ARCH_CLOSE_006_TIME_VALIDATION_EVIDENCE.md` |
| Status | TESTED / EVIDENCED |
| Limitation | Physical clock drift/synchronization-loss measurements remain deferred. |

## T-017 — Stale/out-of-order sensor data is detected/governed

| Field | Mapping |
|---|---|
| Requirement | Sensor/event data that is stale, out-of-order or temporally invalid must be detectable and governed. |
| Authority | Time architecture and sensor/perception architecture |
| Contract/API | Observation timestamp/provenance contract |
| Implementation | Time semantics validation path; perception runtime implementation deferred |
| Test | Integration/simulation/replay validation |
| Evidence | ARCH-CLOSE-006 evidence plus defined simulation/replay gate |
| Status | TESTED / DEFERRED FOR FULL SENSOR RUNTIME |
| Limitation | Full physical sensor evidence requires actual sensors and synchronization infrastructure. |

## T-018 — Replay preserves required deterministic semantics

| Field | Mapping |
|---|---|
| Requirement | Replay must preserve the temporal/provenance semantics required to reproduce supported system behavior. |
| Authority | Time architecture; executable architecture test strategy |
| Contract/API | Event/provenance/replay semantics |
| Implementation | Replay architecture defined; full runtime replay engine remains implementation work |
| Test | Simulation/replay test class |
| Evidence | Architecture validation path |
| Status | DEFERRED |
| Limitation | Trigger: first executable runtime/event log. Required evidence: fixture replay, deterministic seed/version capture and divergence reporting. |

## T-019 — Resource budgets are measurable and bounded

| Field | Mapping |
|---|---|
| Requirement | CPU/GPU/RAM/storage/network/power/thermal/resource budgets must be explicit and measurable. |
| Authority | `21_RUNTIME_RESOURCE_BUDGETS_AND_DETERMINISTIC_EXECUTION.md`; ARCH-CLOSE-007 corpus |
| Contract/API | Resource budget and runtime governance definitions |
| Implementation | Resource-budget validation assets |
| Test | Benchmark evidence |
| Evidence | ARCH-CLOSE-007 resource validation corpus |
| Status | EVIDENCED |
| Limitation | Robot-specific power/thermal limits require selected hardware. |

## T-020 — CPU/GPU/RAM/storage/thermal/power behavior is recorded on target hardware

| Field | Mapping |
|---|---|
| Requirement | Final physical resource behavior must be measured on the actual target platform. |
| Authority | ARCH-CLOSE-007 resource architecture; hardware validation architecture |
| Contract/API | Resource telemetry/budget contract |
| Implementation | Physical target not yet selected |
| Test | B/H/L |
| Evidence | Hardware benchmark campaign |
| Status | DEFERRED |
| Limitation | Trigger: hardware selection. Required evidence: sustained CPU/GPU/RAM/storage, thermal, power and 8–10 hour endurance measurements. |

## T-021 — Required sensor observations carry provenance and timestamps

| Field | Mapping |
|---|---|
| Requirement | Sensor observations must retain provenance, timestamp semantics and source identity. |
| Authority | `33_NOVI_SENSOR_AND_PERCEPTION_ARCHITECTURE.md`; time architecture; canonical Observation/Evidence contracts |
| Contract/API | Observation and Evidence contracts |
| Implementation | Contract layer exists; concrete sensor adapters deferred |
| Test | Contract/integration/H validation path |
| Evidence | Contract validation plus sensor architecture |
| Status | CONTRACTED / DEFERRED FOR PHYSICAL ADAPTERS |
| Limitation | Physical provenance requires actual sensor drivers and synchronization. |

## T-022 — Sensor fusion preserves uncertainty rather than hiding conflicts

| Field | Mapping |
|---|---|
| Requirement | Fusion must preserve uncertainty, provenance and conflicts rather than silently collapsing contradictory observations. |
| Authority | Sensor/perception architecture; cognition uncertainty/provenance architecture |
| Contract/API | Observation/Evidence/world-state uncertainty semantics |
| Implementation | Semantic contract boundary defined; fusion runtime not yet implemented |
| Test | Integration/simulation/replay |
| Evidence | Architecture-defined validation path |
| Status | DEFERRED |
| Limitation | Trigger: perception/fusion runtime. Required evidence: conflicting sensor fixtures, uncertainty propagation and provenance preservation. |

## T-023 — Hardware faults produce governed degradation/safe-stop behavior

| Field | Mapping |
|---|---|
| Requirement | Hardware faults must transition Novi into a governed degraded or safe-stop state. |
| Authority | Hardware safety architecture; safety/authorization architecture |
| Contract/API | HardwareHealth, SafetyDecision and action-execution boundaries |
| Implementation | Physical hardware fault layer not yet implemented |
| Test | H/P/L |
| Evidence | Physical fault-injection campaign |
| Status | DEFERRED |
| Limitation | Trigger: physical platform. Required evidence: sensor failure, actuator failure, power/network loss, watchdog and safe-stop behavior. |

## T-024 — Model output is treated as untrusted input

| Field | Mapping |
|---|---|
| Requirement | Model output cannot directly become authority; it is input to governed reasoning/action pathways. |
| Authority | `20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md`; Brain model invocation architecture |
| Contract/API | `contracts/brain/model-invocation/1.0.0/schema.json`; ActionProposal/Authorization/SafetyDecision |
| Implementation | Model invocation boundary and safety gateway architecture |
| Test | Contract/integration safety validation |
| Evidence | ARCH-CLOSE-005 safety evidence; contract validation |
| Status | CONTRACTED / TESTED |
| Limitation | Concrete model runtime adapters are later implementation work. |

## T-025 — Protected controls cannot be modified by adaptive cognition

| Field | Mapping |
|---|---|
| Requirement | Adaptive/learned cognition must not modify protected safety, authorization or control boundaries. |
| Authority | Safety/authorization and governance architecture |
| Contract/API | Protected policy/safety interfaces |
| Implementation | Boundary defined; physical enforcement deferred |
| Test | U/I/H/P |
| Evidence | Software safety integration plus future H/P gate |
| Status | TESTED / DEFERRED FOR PHYSICAL ENFORCEMENT |
| Limitation | Trigger: actuator/controller implementation. Required evidence: attempted policy bypass and protected-control immutability. |

## T-026 — Privacy-sensitive state follows retention/erasure dependencies

| Field | Mapping |
|---|---|
| Requirement | Privacy-sensitive data must respect retention, deletion/erasure and dependency semantics. |
| Authority | Memory/knowledge privacy, provenance and erasure architecture |
| Contract/API | Memory/provenance lifecycle contracts |
| Implementation | Architecture and schema direction exists; runtime erasure implementation deferred |
| Test | Integration/documentation validation path |
| Evidence | Memory architecture and canonical lifecycle rules |
| Status | CONTRACTED / DEFERRED FOR RUNTIME |
| Limitation | Trigger: concrete durable memory implementation. Required evidence: dependency-aware deletion, audit trail and recovery semantics. |

## T-027 — Backup/restore produces internally consistent recoverable state

| Field | Mapping |
|---|---|
| Requirement | Backup and restore must preserve internally consistent durable state. |
| Authority | Storage/recovery architecture and ARCH-CLOSE-003 runbook |
| Contract/API | Durable storage backup/recovery semantics |
| Implementation | SQLite recovery validation harness |
| Test | Backup/restore recovery test |
| Evidence | `41_ARCH_CLOSE_003_SQLITE_RECOVERY_VALIDATION.md` |
| Status | TESTED / EVIDENCED |
| Limitation | Interrupted backup and long-duration recovery remain residual validation. |

## T-028 — Migration preserves IDs, revisions, provenance and lifecycle semantics

| Field | Mapping |
|---|---|
| Requirement | Schema/data migrations must preserve identity, revisions, provenance and lifecycle invariants. |
| Authority | Storage migration architecture; contract implementation/schema standard |
| Contract/API | Versioned schemas and migration semantics |
| Implementation | Migration architecture exists; concrete migration engine remains implementation work |
| Test | Unit/integration/recovery migration validation path |
| Evidence | Architecture-defined migration gate |
| Status | DEFERRED |
| Limitation | Trigger: first durable schema migration. Required evidence: forward/backward compatibility where supported, ID/revision/provenance preservation and rollback behavior. |

## T-029 — Runtime/version tuple is captured and reproducible

| Field | Mapping |
|---|---|
| Requirement | The executable runtime and dependency tuple must be captured so the Stage-1 environment is reproducible. |
| Authority | `22_RUNTIME_VERSION_COMPATIBILITY_AND_LIFECYCLE.md`; `29_ARCH_CLOSE_004_RUNTIME_VERSION_COMPATIBILITY_TUPLE.md` |
| Contract/API | Runtime/deployment manifest |
| Implementation | Runtime tuple and compatibility validation assets |
| Test | Compatibility/reproducibility validation |
| Evidence | ARCH-CLOSE-004 corpus |
| Status | TESTED / EVIDENCED |
| Limitation | Physical target tuple remains deferred until platform selection. |

## T-030 — Hardware deployment identity is captured without exposing secrets

| Field | Mapping |
|---|---|
| Requirement | Physical deployment identity must be recorded sufficiently for provenance/reproducibility without exposing secrets. |
| Authority | Deployment manifest and security architecture |
| Contract/API | DeploymentManifest and hardware identity fields |
| Implementation | Deployment-manifest contract |
| Test | Contract/security validation; physical deployment validation later |
| Evidence | ARCH-CLOSE-008 corpus |
| Status | CONTRACTED / DEFERRED FOR PHYSICAL IDENTITY |
| Limitation | Trigger: physical platform. Required evidence: immutable/non-secret identity capture and secret redaction. |

---

# 5. Closure audit

## 5.1 Coverage

All 30 canonical P0 invariants defined by `37_ARCH_CLOSE_009_ARCHITECTURE_TO_TEST_MAPPING.md` are represented above.

```text
T-001 … T-030 = 30 / 30 mapped
```

## 5.2 GAP audit

```text
GAP classifications: 0
```

Every item is either:

- TESTED;
- EVIDENCED;
- CONTRACTED;
- or DEFERRED with an explicit trigger and required evidence.

## 5.3 Physical-boundary audit

The following are deliberately not claimed as physically validated:

- emergency stop;
- physical actuator isolation;
- physical sensor timing/synchronization;
- target-hardware resource/thermal/power behavior;
- hardware fault injection;
- physical sensor-fusion behavior;
- final hardware identity;
- long-duration physical endurance.

This is intentional and consistent with the architecture's Mac-first validation strategy.

## 5.4 Implementation-boundary audit

The following are intentionally not represented as completed runtime implementation:

- full projection/index rebuild runtime;
- full replay engine;
- concrete sensor fusion runtime;
- concrete privacy/erasure execution;
- migration engine;
- physical hardware safety enforcement;
- final physical adapters.

These are later implementation-phase work, not architecture traceability gaps.

## 5.5 Contradiction audit

No unresolved contradiction is introduced by this matrix.

The key distinction is:

```text
Architecture complete for current phase
        ≠
Complete Novi implementation
        ≠
Physical robot validated
```

Novi's architecture remains vendor-independent. NVIDIA technologies are candidate implementation backends behind stable Novi capability contracts, consistent with the project's NVIDIA research. The NVIDIA research explicitly requires requirement mapping, technical evaluation, benchmarking, security/license review and ADR approval before adoption.

---

# 6. Evidence and source policy

This closure uses repository evidence as the primary source for Novi-specific status.

External technology facts must be revalidated against authoritative primary sources before implementation. For NVIDIA technology decisions, NVIDIA documentation, release notes, specifications and official repositories are the preferred primary sources. Existing Library research is treated as an architecture research input, not as an immutable product-version authority.

The Library research establishes the same critical boundary used here: Novi owns semantic contracts, memory/knowledge, governance, identity, provenance, authorization, safety boundaries and auditability, while NVIDIA can provide implementation substrate for perception, simulation, learning, inference and edge compute. fileciteturn27file0L28-L32

The research also explicitly recommends capability-first interfaces rather than NVIDIA product-name dependencies. fileciteturn27file1L120-L131

---

# 7. Reproducibility requirements

This matrix is reproducible from the repository by resolving the cited paths on `main` and evaluating the linked validation workflows/evidence artifacts.

A future implementation phase must extend this matrix rather than silently replacing it. New architecture invariants require a new traceability entry and must not be introduced without an evidence class.

---

# 8. Closure decision

**ARCH-CLOSE-009 = CLOSED.**

Closure means:

1. all 30 P0 invariants have traceability entries;
2. zero P0 items are classified `GAP`;
3. implementation/evidence/deferral boundaries are explicit;
4. physical-only claims are explicitly deferred;
5. validation classes are identified;
6. repository authorities are named;
7. the matrix is reproducible from `main`;
8. no architecture claim is represented as implemented merely because documentation exists.

The next architecture activity is not to reopen ARCH-CLOSE-009. The next activity is the remaining ARCH-CLOSE-010 integrity work and the final 001–010 architecture gate synchronization.

---

## 9. Architectural invariant

> **Every authoritative Novi architecture decision must be traceable to a contract, implementation, executable validation, measured evidence, or an explicit justified deferral; no documentation artifact alone constitutes implementation evidence.**
