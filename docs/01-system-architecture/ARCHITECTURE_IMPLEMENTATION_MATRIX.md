# Architecture-to-Code Truth Matrix (Task 01)

**Date:** 2026-08-29
**Authority:** `plans/01_SYSTEM_ARCHITECTURE_IMPLEMENTATION_GAP_REMEDIATION_PLAN.md` (Task 01 — Truth inventory) and `docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md` (§5a: "should be started now to freeze the baseline before architecture-changing work").
**Method:** every document under `docs/01-system-architecture/` was read; each distinct documented component, interface, state, dependency, and completion claim was verified against the actual repository (`novi/brain/`, `novi/perception/`, `novi/contracts/`, `novi/web/`, `scripts/`, test suites) via grep/ls and, where cheap, call-site inspection. No file path or symbol was recorded without verification. This matrix reconciles two independent half-inventories (docs 00–19 and docs 20–50).

**Purpose:** freeze the documentation-vs-implementation baseline. Any claim that is documented but not implemented is marked explicitly — the plan's rule: *unsupported claims are named, not hidden*.

---

## 1. Status legend

| Status | Meaning |
|---|---|
| IMPLEMENTED | Wired into the production `MacBrain` runtime path with tests |
| PARTIAL | Implemented with tests but not fully production-wired, or subset of the documented surface |
| STUB/ISLAND | Exists with passing tests but is **not imported by the engine** (a tested island) |
| TEST-ONLY | Enforced only as a contract/integration test gate, not a runtime path |
| EVIDENCED | Validated by a committed script + result artifact, not runtime code |
| CONTRACTED | JSON Schema + fixtures exist; no runtime generator/validator |
| CLAIM-UNSUPPORTED | Documented but no implementation found (or docs mark it deferred) |

## 2. Executive summary

- **Items mapped:** ~173 truth items across 50 numbered documents (+ README, policy/evidence docs without code claims).
- **IMPLEMENTED ≈ 82 · PARTIAL ≈ 27 · TEST-ONLY ≈ 20 · EVIDENCED ≈ 10 · CONTRACTED ≈ 6 · STUB/ISLAND ≈ 8 · CLAIM-UNSUPPORTED ≈ 21.** (Approximate: policy/evidence documents with no code claims are reported as single-line entries and excluded from counts.)
- **Genuinely implemented and wired** (safe to trust): durable-state/event-log substrate (docs 107/108/110), storage schema versioning + recovery validation (`scripts/sqlite_recovery_validation.py`, all 7 checks PASS artifact), contract registry + 18 versioned schemas + CI validation pipeline, governance guard, audit trail, privacy/retention/erasure, observability (health/metrics/diagnostics/traces/replay), resource telemetry + budgets, world model epistemic discipline, attention, bounded autonomy + state machine, MacCognition/temporal/consolidation, and the `novi/perception/` capability package (detection/tracking/pipeline/grounding with its own 264-test suite).
- **Biggest documented-but-missing or island gaps** (the actionable residue):
  1. **Safety boundary is not the production path** — `safety_policy.py` (SafetyPolicy, RuntimeSafetyMonitor), `AutonomySupervisor`, and `runtime.py`'s validate/authorize live as tested islands; the engine path is `governance_guard → body.execute()` only. (North-star Phase 2a/2b.)
  2. **Recovery as a runtime behavior** — `recovery.py` (FailureClassifier, RecoveryPlanner, RegressionMemory, Lesson) is an unwired island. (Phase 4c.)
  3. **Deployment-manifest / startup compatibility validation** — schema + fixtures exist; no runtime startup validation, drift check, or version-tuple validator. (CLAIM-UNSUPPORTED in runtime.)
  4. **Replication/distributed memory (109), multi-agent coordination (114), RPO/RTO tiers, soak/long-duration harness** — documented, deferred, absent from code (explicitly non-blocker per doc 15).
  5. **Physical sensor/hardware adapters (IMU/gyro, LiDAR, GNSS, thermal, night-vision), physical E-stop, `ClockProvider` adapter** — requirements exist (docs 33/34), no drivers/adapters. Deferred until hardware selection.
  6. **Truth-matrix-adjacent:** some ARCH-CLOSE gates are TEST-ONLY (consistency matrix, time semantics, safety/authorization integration) — legitimate gates, but the underlying runtime behaviors are partial (e.g. no `ClockProvider`, no full replay engine, projection rebuild deferred).
- **Undocumented implemented behavior worth documenting** (surprises found in code, absent from the docs): `MacBrain`'s integrated orchestration (the docs describe the subsystems, not the one-runtime composition), `multi_speed_runtime` degradation scheduler, `AutonomySupervisor`'s lease/one-action-per-tick machinery, the hardened in-memory memory-manager fallback path, `sleep_cycle` scheduling, grounding RPC service (`grounding_service`/`grounding_rpc`/`grounding_client`), LocateAnything runtime/geometry/parse, `EventBus.replay`/`since` sequence semantics, `AuditTrail.trace_for_action`/`by_goal`.
- **Freeze:** as of this commit, this matrix is the implementation baseline for the P0 remediation plan. Architecture-changing work (Phases 1–3 of the north-star doc) updates rows here in the same change, or claims no longer hold.

---

## 2. Per-document inventory — docs 00–19 (core architecture)

Compiled from a verified audit of `docs/01-system-architecture/00–19`. Paths/symbols verified by grep/read at matrix time.

### Doc 00: HIGH_LEVEL_ARCHITECTURE — system context & subsystems
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Perception converts sensor→observations | `novi/perception/pipeline.py`, `camera.py`, `detection.py` | `PerceptionPipeline`, `CameraFeed`, `DeterministicObjectDetector` | `novi/perception/tests/test_pipeline.py`, `test_camera.py` | IMPLEMENTED | (pre-Phase-1a note) wired into `novi/web/server.py:46`; engine wiring landed later 2026-08-29 |
| World model = current structured state | `novi/brain/world_model.py` | `WorldModel`, `WorldEntity`, `WorldRelation`, `Provenance` | `test_world_model.py` | IMPLEMENTED | `engine.py:187 self.unified_world` |
| Memory & knowledge with provenance | `novi/brain/storage.py`, `world_model.py` | `DurableMemoryStore`, `Provenance` | `test_storage.py`, `test_world_model.py` | IMPLEMENTED | `engine.py:226` |
| Attention ≠ model invocation | `novi/brain/attention.py` | `AttentionRanker`, `AttentionCandidate` | `test_attention.py` | IMPLEMENTED | `engine.py:194` |
| Personality & social state | `novi/brain/soul.py`, `social.py`, `identity.py` | `PersonIdentity` | `test_soul.py`, `test_social.py` | IMPLEMENTED | |
| Autonomy continuous loop | `novi/brain/autonomy.py`, `autonomy_state_machine.py`, `engine.py` | `BoundedGoalController`, `AutonomyStateMachine` | `test_autonomy_state_machine.py`, `test_b1_autonomy.py` | IMPLEMENTED | `engine.py:217,237` |
| Agent/model runtime, replaceable models | `novi/brain/agent.py`, `b2_model_runtime.py` | `Planner`, model runtime | `test_agent.py`, `test_b2_model_runtime.py` | PARTIAL | Agent runtime present; model-runtime abstraction partial |
| Governance & safety separate from model | `novi/brain/governance_guard.py`, `safety_policy.py` | `GovernanceGuard`, `SafetyPolicy` | `test_governance_guard.py`, `test_safety_policy.py` | PARTIAL | Governance wired; `SafetyPolicy` is an island |
| ROS 2 / robotics boundary | — | — | — | CLAIM-UNSUPPORTED | No ROS 2 code in repo |
| High/medium/low-rate autonomy clocks | `novi/brain/multi_speed_runtime.py` | `MultiSpeedRuntime`, `SYSTEM_0`, `ResourceMode` | `test_multi_speed_runtime.py` | IMPLEMENTED | `engine.py:196` |
| Governed learning (no self-modification) | `novi/brain/learning_pipeline.py`, `consolidation.py` | `MemoryConsolidator` | `test_consolidation.py` | IMPLEMENTED | `engine.py:251` |

### Doc 01: DETAILED_SYSTEM_ARCHITECTURE — process boundaries & event architecture
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Canonical EventEnvelope | `novi/brain/event_bus.py` | `EventEnvelope` | `test_event_bus.py` | IMPLEMENTED | `event_bus.py:62` |
| Event log immutable, replayable | `novi/brain/event_bus.py` | `EventBus.replay`, `.since`, `.publish` | `test_event_bus.py` | IMPLEMENTED | wired `engine.py:421,2515` |
| occurred_at vs recorded_at distinct | `novi/brain/event_bus.py` | `EventEnvelope` fields | `test_event_bus.py` | IMPLEMENTED | |
| Observation→Evidence→Knowledge chain | `novi/brain/canonical.py`, `world_model.py` | `observation_payload`, `Provenance` | `test_canonical.py` | PARTIAL | Payload builders exist; full chain partial |
| Attention state machine (IDLE→ENGAGE) | `novi/brain/attention.py` | `AttentionRanker` | `test_attention.py` | PARTIAL | Ranking exists; explicit state machine not found |
| Tool execution: schema→auth→resource→audit | `novi/brain/governance_guard.py`, `skills.py` | `GovernanceGuard.evaluate` | `test_governance_guard.py`, `test_skill_governance.py` | PARTIAL | Auth/audit present; resource checks partial |
| Lifecycle DISCOVER→STOPPED | `novi/brain/autonomy_state_machine.py` | `AutonomyStateMachine` | `test_autonomy_state_machine.py` | IMPLEMENTED | `engine.py:217` |
| Resource measurement (CPU/GPU/RAM/thermal) | `novi/brain/resource_telemetry.py` | `ResourceTelemetry` | `test_resource_telemetry.py` | IMPLEMENTED | `engine.py:215` |
| Mac-to-edge capability contract | `novi/perception/camera.py` | `CameraProvider` protocol | `test_camera.py` | PARTIAL | Camera contract exists; ModelRuntime contract partial |
| Simulation contract | — | — | — | CLAIM-UNSUPPORTED | No simulator code |

### Doc 02: ARCHITECTURAL_PRINCIPLES — normative constraints
Pure policy prose; principles are satisfied by the components mapped in docs 00/01 above. No separate table.

### Doc 03: COMPONENT_BOUNDARIES — ownership & forbidden dependencies
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Forbidden-dependency static checks | `scripts/validate_architecture_integrity.py` | `main()` | — | PARTIAL | Script exists; CI workflow exists (see doc 38 evidence) |
| Model capability interfaces | `novi/brain/b2_model_runtime.py`, `b2_specialist_models.py` | model runtime | `test_b2_model_runtime.py` | PARTIAL | |
| Policy boundary (permission evaluation) | `novi/brain/governance_guard.py` | `GovernanceGuard.evaluate` | `test_governance_guard.py` | IMPLEMENTED | `engine.py:195` |
| Safety boundary (final gate) | `novi/brain/safety_policy.py` | `SafetyPolicy`, `RuntimeSafetyMonitor` | `test_safety_policy.py` | STUB/ISLAND | Not imported by engine (Phase 2a target) |
| Control app boundary (no direct DB/ROS) | `novi/web/server.py` | `NoviWebServer` | `novi/web/tests/test_web.py` | IMPLEMENTED | Web uses app APIs |

### Doc 04: RUNTIME_PROFILES — deployment profiles
Profiles A–F are deployment policy. **Profiles B–F (portable sim, Isaac Sim, edge, HIL, physical) are CLAIM-UNSUPPORTED in code; Profile A (development, Mac) is IMPLEMENTED via `MacBrain` + `novi/web/server.py`.**

### Doc 05: CROSS_CUTTING_REQUIREMENTS
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Health/lifecycle queryable without model | `novi/brain/observability.py` | `HealthMonitor`, `HealthCheck`, `default_health_checks` | `test_observability.py`, `test_observability_engine.py` | IMPLEMENTED | `engine.py:399` |
| Time semantics (event/received/processed) | `novi/brain/event_bus.py`, `temporal.py` | `EventEnvelope`, `TemporalModel` | `test_event_bus.py`, `test_temporal.py` | IMPLEMENTED | `engine.py:332` |
| Provenance classes | `novi/brain/world_model.py` | `Provenance` | `test_world_model.py` | PARTIAL | Class taxonomy partial |
| Auditability (model/tool/knowledge/schema/privileged) | `novi/brain/audit_trail.py` | `AuditTrail.record`, `.by_correlation` | `test_audit_trail.py` | IMPLEMENTED | `engine.py:426` |
| Privacy classification & retention | `novi/brain/privacy.py` | `Classification`, `classify`, `sweep`, `erase_memory` | `test_privacy.py` | IMPLEMENTED | `engine.py:393` |
| Resource limits & backpressure | `novi/brain/resource_telemetry.py`, `input_bus.py` | `ResourceTelemetry`, `InputBus` | `test_resource_telemetry.py`, `test_input_bus.py` | IMPLEMENTED | `engine.py:215,175` |
| Cancellation | `novi/brain/autonomy_supervisor.py` | `CancellationToken` | `test_autonomy_supervisor.py` | STUB/ISLAND | Supervisor not wired into engine |
| Idempotency | `novi/brain/storage.py`, `scripts/sqlite_recovery_validation.py` | `DurableMemoryStore` | `test_storage.py` | IMPLEMENTED | Duplicate-idempotency validated |
| Schema versioning & migrations | `novi/brain/storage.py` | `._migrate`, `._check_schema_compatible` | `test_storage.py` | IMPLEMENTED | `storage.py:279,313` |
| Graceful degradation | `novi/brain/failure_modes.py`, `multi_speed_runtime.py` | `DegradedMode`, `ResourceMode` | `test_multi_speed_runtime.py` | IMPLEMENTED | `engine.py:626` |
| Measured vs derived telemetry | `novi/brain/observability.py` | `RuntimeMetric` | `test_observability.py` | PARTIAL | Classification partial |

### Doc 06 (107): DURABLE STATE & EVENT LOG
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Authoritative event log + materialized state | `novi/brain/event_bus.py`, `storage.py` | `EventBus`, `DurableMemoryStore` | `test_event_bus.py`, `test_storage.py` | IMPLEMENTED | |
| Events immutable | `novi/brain/event_bus.py` | append-only `publish` | `test_event_bus.py` | IMPLEMENTED | |
| State versioned | `novi/brain/storage.py` | revision tracking | `test_storage.py` | IMPLEMENTED | |
| Durability classes A–D | — | — | — | CLAIM-UNSUPPORTED | No class enum in code |
| Transaction/commit semantics | `novi/brain/storage.py`, `scripts/sqlite_recovery_validation.py` | SQLite transactions | `test_storage.py` | IMPLEMENTED | |
| Idempotency | `scripts/sqlite_recovery_validation.py` | duplicate-idempotency check | — | IMPLEMENTED | `sqlite_recovery_validation.py:85-102` |
| Causality/ordering (causation_id, correlation_id) | `novi/brain/event_bus.py` | `EventEnvelope` | `test_event_bus.py` | IMPLEMENTED | |
| Snapshots/checkpoints | `scripts/sqlite_recovery_validation.py` | `wal_checkpoint` | — | PARTIAL | Script-validated, not a store API |
| Schema/reducer evolution | `novi/brain/storage.py` | `_migrate`, `_check_schema_compatible` | `test_storage.py` | IMPLEMENTED | |
| Provenance/dependency graph | `novi/brain/storage.py` | `dependent_ids`, `gate_governance` | `test_storage.py` | IMPLEMENTED | `storage.py:689,706` |
| Failure semantics | `novi/brain/recovery.py` | `FailureClass` | `test_recovery.py` | STUB/ISLAND | Not wired into engine |
| Offline-first | `novi/brain/engine.py` | `MacBrain` (local) | `test_acceptance.py` | IMPLEMENTED | |
| Storage selection (SQLite) | `novi/brain/storage.py`, `scripts/storage_benchmark.py` | `DurableMemoryStore` | `test_storage.py` | IMPLEMENTED | SQLite WAL |

### Doc 07 (108): TRANSACTIONS/CONSISTENCY/CONFLICTS
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status |
|---|---|---|---|---|
| Consistency classes C0–C5 | `novi/contracts/resource_budgets.stage1.json` (+ ADR mapping) | — | — | PARTIAL |
| Optimistic concurrency / check-and-set | `novi/brain/storage.py` | revision checks | `test_storage.py` | PARTIAL |
| Conflict resolution (LWW, merge, escalate) | `novi/brain/autonomy.py` | `ConflictResolution`, `GoalArbitration.resolve_conflict` | `test_b1_autonomy.py` | PARTIAL (goal-level only) |
| Transaction status model | — | — | — | CLAIM-UNSUPPORTED |
| Idempotency / retry safety | `scripts/sqlite_recovery_validation.py` | duplicate-idempotency | — | IMPLEMENTED |
| Concurrency testing | `novi/brain/tests/test_storage.py` | — | — | PARTIAL |

### Doc 07 (109): REPLICATION/DISTRIBUTED MEMORY
**CLAIM-UNSUPPORTED (deliberately deferred).** Doc 15 marks 109 as "not a Stage-1 implementation blocker"; no replication/sync/node-identity/tombstone code. Single-node only.

### Doc 08 (110): RECOVERY/CHECKPOINTING
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Failure classification | `novi/brain/recovery.py` | `FailureClassifier`, `FailureClass` | `test_recovery.py` | STUB/ISLAND | Not wired into engine |
| Recovery planning | `novi/brain/recovery.py` | `RecoveryPlanner`, `RecoveryPlan` | `test_recovery.py` | STUB/ISLAND | |
| Regression memory / lessons | `novi/brain/recovery.py` | `RegressionMemory`, `Lesson` | `test_recovery.py` | STUB/ISLAND | |
| Checkpoint/replay/restore | `scripts/sqlite_recovery_validation.py` | checkpoint/reopen, backup/restore | — | PARTIAL | Script, not runtime API |
| Crash recovery (SQLite) | `novi/brain/storage.py` | `DurableMemoryStore` | `test_storage.py` | IMPLEMENTED | WAL |
| RPO/RTO tiers | — | — | — | CLAIM-UNSUPPORTED | |

### Doc 09 (111): PRIVACY/RETENTION/ERASURE
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Data classification | `novi/brain/privacy.py` | `Classification`, `classify` | `test_privacy.py` | IMPLEMENTED | `privacy.py:80,116` |
| Retention policy & expiry | `novi/brain/privacy.py` | `retention_seconds_for`, `expiry_for`, `sweep` | `test_privacy.py` | IMPLEMENTED | `privacy.py:134-199` |
| Purpose-aware access | `novi/brain/privacy.py` | `purpose_allowed`, `authorize` | `test_privacy.py` | IMPLEMENTED | |
| Erasure (right-to-be-forgotten) | `novi/brain/privacy.py` | `erase_memory`, `forget_entity` | `test_privacy.py` | IMPLEMENTED | wired `engine.py:1869-1874` |
| Dependency-aware deletion | `novi/brain/storage.py` | `dependent_ids`, `gate_governance` | `test_storage.py` | IMPLEMENTED | |
| Tombstones / replication erasure | — | — | — | CLAIM-UNSUPPORTED | |
| Erasure verification | `novi/brain/privacy.py` | `ErasureReport` | `test_privacy.py` | PARTIAL | |

### Doc 10: ARCHITECTURE VALIDATION & TRACEABILITY
| Documented claim | Implementation path(s) | Test evidence | Status |
|---|---|---|---|
| Architecture invariants as automated tests | `novi/brain/tests/test_arch_close_gate.py`, `test_b0_stage_gate.py` | gates exist | PARTIAL (not all 20 invariants) |
| Requirement IDs / traceability | `novi/contracts/registry.json` + `novi/contracts/tests/validate_registry.py` | — | PARTIAL |
| Benchmark reproducibility | `scripts/storage_benchmark.py`, `novi/brain/benchmarks/` | — | PARTIAL (storage only) |

### Doc 11: ARCHITECTURE DECISION FRAMEWORK — policy prose only. No code claims.

### Doc 12 (112): OBSERVABILITY/EVALUATION
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Health model (HEALTHY/DEGRADED/FAILED) | `novi/brain/observability.py` | `HealthRegistry`, `HealthMonitor` | `test_observability.py` | IMPLEMENTED | `engine.py:399` |
| Metrics registry | `novi/brain/observability.py` | `MetricRegistry`, `MetricsRegistry` | `test_observability.py` | IMPLEMENTED | `engine.py:400` |
| Diagnostics | `novi/brain/observability.py` | `Diagnostics` | `test_observability.py` | IMPLEMENTED | |
| Traces / correlation | `novi/brain/audit_trail.py` | `by_correlation`, `trace_for_action` | `test_audit_trail.py` | IMPLEMENTED | `audit_trail.py:219-223` |
| Lifespan/soak reliability | — | — | — | CLAIM-UNSUPPORTED | No soak harness |

### Doc 13 (113): RESOURCE GOVERNANCE/SCHEDULING
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status |
|---|---|---|---|---|
| Resource telemetry | `novi/brain/resource_telemetry.py` | `ResourceTelemetry` | `test_resource_telemetry.py` | IMPLEMENTED |
| Priority classes P0–P4 | `novi/brain/multi_speed_runtime.py` | `ResourceMode`, `SYSTEM_0` | `test_multi_speed_runtime.py` | PARTIAL |
| Admission control / scheduling | `novi/brain/multi_speed_runtime.py` | `MultiSpeedRuntime` | `test_multi_speed_runtime.py` | PARTIAL |
| Resource budgets | `novi/contracts/resource_budgets.stage1.json` | — | `test_resource_budgets.py` | IMPLEMENTED |

### Doc 14 (114): MULTI-AGENT COORDINATION
**CLAIM-UNSUPPORTED / explicitly deferred (P2).** `novi/brain/agent.py` is a single-agent runtime, not multi-agent coordination.

### Doc 15: ARCHITECTURE FILE AUDIT — audit record; no code claims.

### Doc 16: CANONICAL_SYSTEM_CONTRACTS
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status |
|---|---|---|---|---|
| EventEnvelope contract | `novi/contracts/system/event-envelope/1.0.0/schema.json` + `novi/brain/event_bus.py` | `EventEnvelope` | `novi/contracts/tests/test_executable_suite.py` | IMPLEMENTED |
| Observation/Evidence/Entity/Relationship contracts | `novi/contracts/system/*/1.0.0/schema.json` | — | `novi/contracts/tests/` | IMPLEMENTED |
| MemoryRecord/KnowledgeRecord contracts | `novi/contracts/memory/*/1.0.0/schema.json` | — | `novi/contracts/tests/` | IMPLEMENTED |
| Goal/Plan/ActionProposal contracts | `novi/contracts/autonomy/*/1.0.0/schema.json` | — | `novi/contracts/tests/` | IMPLEMENTED |
| Authorization/SafetyDecision contracts | `novi/contracts/safety/*/1.0.0/schema.json` | — | `novi/contracts/tests/` | IMPLEMENTED |
| Contract registry | `novi/contracts/registry.json`; `novi/brain/contracts.py:46` | `ContractRegistry` | `validate_registry.py` | IMPLEMENTED |

### Doc 16: SOLUTION_SELECTION_POLICY — policy prose only.

### Doc 17: CONTRACT_IMPLEMENTATION_AND_SCHEMA_STANDARD
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status |
|---|---|---|---|---|
| Machine-readable JSON schemas per contract | `novi/contracts/<domain>/<contract>/<version>/schema.json` | — | `test_executable_suite.py` | IMPLEMENTED |
| Contract registry | `novi/contracts/registry.json` | `ContractRegistry` | `validate_registry.py` | IMPLEMENTED |
| Contract validation | `novi/brain/contracts.py:96` | `validate_contract` | `test_contracts.py` | IMPLEMENTED |
| Positive/negative fixtures | `novi/contracts/tests/fixtures/` | — | `novi/contracts/tests/` | IMPLEMENTED |

### Doc 17: TIME_SYNC (superseded by 19) — superseded; see Doc 19.

### Doc 18: NVIDIA_PLATFORM_VALIDATION_MATRIX
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status |
|---|---|---|---|---|
| Jetson AGX Orin / JetPack 7.2 baseline | `novi/brain/nvidia_experiments.py`, `b2_nemotron.py` | — | `test_b2_nemotron.py` | PARTIAL (no hardware validation) |
| ModelRuntime abstraction | `novi/brain/b2_model_runtime.py` | — | `test_b2_model_runtime.py` | PARTIAL |
| Validation tuple / deployment manifest | `novi/contracts/deployment/` | — | — | PARTIAL (schemas only) |

### Doc 18: STAGE_1_DURABLE_STATE_STORAGE_ADR
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| SQLite Stage-1 candidate | `novi/brain/storage.py` | `DurableMemoryStore` | `test_storage.py` | IMPLEMENTED | |
| Gate (ARCH-CLOSE-003) | `novi/brain/benchmarks/arch_close_003_gate.py` | — | — | IMPLEMENTED | |
| Benchmark evidence | `docs/01-system-architecture/evidence/ARCH-CLOSE-003-*.json` | — | — | IMPLEMENTED | |
| Fault-injection/backup validation | `scripts/sqlite_recovery_validation.py` | `check()` | — | IMPLEMENTED | 7 checks PASS |
| ADR status | — | — | — | PARTIAL | ADR says PROPOSED; code already adopted SQLite |

### Doc 19: EXECUTABLE_ARCHITECTURE_TEST_STRATEGY
| Documented claim | Implementation path(s) | Test evidence | Status |
|---|---|---|---|
| Contract tests | `novi/contracts/tests/` | `test_executable_suite.py` | IMPLEMENTED |
| Unit tests (reducers/policy/attention) | `novi/brain/tests/` | broad suite | IMPLEMENTED |
| Integration tests (event flows) | `test_event_bus.py`, `test_world_integration.py` | — | IMPLEMENTED |
| ARCH-001..020 invariant gates | `test_arch_close_gate.py`, `test_b0_stage_gate.py` | — | PARTIAL |
| Offline test | — | — | CLAIM-UNSUPPORTED |
| Model-failure test | `FailureHandler` in engine; dedicated test uncertain | — | PARTIAL |
| Static forbidden-dependency checks | `scripts/validate_architecture_integrity.py` | — | PARTIAL (script + CI workflow exist) |

### Doc 19: TIME_SYNC (canonical)
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Clock domains (wall/monotonic/ROS/sim/hardware) | `novi/brain/temporal.py` | `TemporalModel` | `test_temporal.py` | PARTIAL | No clock-domain enum |
| occurred_at/recorded_at/processed_at | `novi/brain/event_bus.py` | `EventEnvelope` | `test_event_bus.py` | IMPLEMENTED | |
| Monotonic time for timeouts | `novi/brain/autonomy_supervisor.py` | `SimClock` | `test_autonomy_supervisor.py` | STUB/ISLAND | Supervisor not wired |
| Stale-data freshness | `novi/perception/camera.py` | `FrameRecord.is_stale`, `CameraFeed.is_stale` | `test_camera.py` | IMPLEMENTED | |
| Action validity windows | `novi/brain/autonomy_supervisor.py` | `AuthorizedAction.expired` | `test_autonomy_supervisor.py` | STUB/ISLAND | Not wired (Phase 2c target) |

---

## 3. Per-document inventory — docs 20–50 (+ README)

### Doc 20: 20_DEPLOYMENT_MANIFEST_SPECIFICATION.md
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Machine-readable manifest schema (§3, §36) | `novi/contracts/deployment/deployment-manifest/1.0.0/schema.json` | deployment_id, source_commit, OS, JetPack, CUDA, TensorRT, digests | positive fixture | CONTRACTED | No runtime generator/validator in `novi/brain/` |
| Startup validation before RUNNING (§6) | none | — | — | CLAIM-UNSUPPORTED | No manifest-load/validate in `runtime.py` |
| Immutable identity / drift detection (§5, §13) | none | — | — | CLAIM-UNSUPPORTED | |
| Policy/model binding, rollback, promotion (§9–12) | none | — | — | CLAIM-UNSUPPORTED | Policy-only prose |

### Doc 20: 20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| ActionProposal distinct from authorization (§6–7) | `novi/brain/governance_guard.py:47`; `novi/brain/runtime.py:170` | `ActionProposal`, `GovernanceGuard.evaluate`, `runtime.validate_proposal` | `test_governance_guard.py`; `novi/contracts/tests/integration/test_safety_authorization_integration.py` | IMPLEMENTED | Wired at `engine.py:985` |
| Authorization decision (§7) | `novi/brain/governance_guard.py:70,112` | `GovernanceGrant` | `test_governance_guard.py` | IMPLEMENTED | ALLOW/DENY/MODIFY/PAUSE/STOP/DEGRADED_MODE |
| Safety decision / policy evaluation (§7, §20) | `novi/brain/safety_policy.py:42,170` | `SafetyDecision`, `SafetyPolicy.evaluate` | `test_safety_policy.py` | PARTIAL | Used by `canonical.py`, not engine runtime gate |
| Emergency stop independent of model (§10) | `novi/brain/autonomy_state_machine.py:254` | EMERGENCY transition (priority 100) | `test_autonomy_state_machine.py` | IMPLEMENTED (software) | Physical E-stop deferred (T-008) |
| Safety modes / degraded operation (§18–19) | `autonomy_state_machine.py:36`; `multi_speed_runtime.py` | state enums | `test_autonomy_state_machine.py` | IMPLEMENTED | |
| Capability validity before authorization (§13) | `novi/contracts/tests/integration/test_safety_authorization_integration.py` | `can_execute()` | same | TEST-ONLY | No runtime capability registry |
| Safety telemetry / audit (§24) | `audit_trail.py:129`; `event_bus.py:97` | — | `test_audit_trail.py` | IMPLEMENTED | `engine.py:1084` |
| Command validity / stale rejection (§12) | integration gate | `within_window()`, `can_execute()` | same | TEST-ONLY | Expired authorization rejected in gate only |

### Doc 21 (gate): ARCHITECTURE_COMPLETION_GATE — completion-gate policy prose; no code claims.
### Doc 21 (runtime): RESOURCE BUDGETS & DETERMINISTIC EXECUTION
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Execution classes S0–S5 with budgets | `novi/contracts/resource_budgets.stage1.json` | `execution_classes` | `test_resource_budgets.py` | IMPLEMENTED | |
| Resource telemetry (CPU/RAM) | `novi/brain/resource_telemetry.py:74` | `ResourceTelemetry.sample` | `test_resource_telemetry.py` | IMPLEMENTED | wired `engine.py:62` |
| Bounded queues / stale work | `novi/perception/camera.py:63` | `CameraFeed` (queue 8), `FrameRecord.is_stale` | `test_camera.py` | IMPLEMENTED | |
| Model admission / fallback (§11, §23) | none | — | — | CLAIM-UNSUPPORTED | No admission-control code |
| Graceful degradation ladder (§16) | `novi/brain/multi_speed_runtime.py` | `ResourceMode` | `test_resource_telemetry.py` | PARTIAL | |

### Doc 22 (closure): ARCHITECTURE_CLOSURE_AND_BASELINE — closure register only; per-workstream status in evidence docs.
### Doc 22 (runtime): RUNTIME_VERSION_COMPATIBILITY
| Documented claim | Implementation path(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|
| Machine-readable version manifest | `novi/contracts/deployment/deployment-manifest/1.0.0/schema.json` | fixture | CONTRACTED | No runtime manifest |
| Compatibility matrix | `novi/contracts/tests/compatibility/compatibility_matrix.json` | `test_compatibility_matrix.py` | IMPLEMENTED (contract-level) | Not hardware stack |
| Startup compatibility checker | none | — | CLAIM-UNSUPPORTED | |
| Runtime/version tuple capture | `novi/storage-benchmark-result.json` | env fields | EVIDENCED | Artifacts only |

### Doc 23: OBSERVABILITY & DIAGNOSTICS
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Health model/registry | `novi/brain/observability.py:64,186` | `HealthRegistry`, `HealthMonitor` | `test_observability.py` | IMPLEMENTED | |
| Metrics registry | `observability.py:93,216` | `MetricsRegistry` | `test_observability.py` | IMPLEMENTED | |
| Structured events/diagnostics | `observability.py:246`; `event_bus.py:97` | `Diagnostics`, `EventBus` | `test_event_bus.py` | IMPLEMENTED | |
| Audit/decision observability | `audit_trail.py:129` | `AuditTrail`, `trace_for_action` | `test_audit_trail.py` | IMPLEMENTED | |
| Correlation IDs/trace | `event_bus.py:117` | `publish(correlation_id, causation_id)` | `test_event_bus.py` | IMPLEMENTED | |
| Replay (§19) | `event_bus.py:207` | `EventBus.replay` | `test_event_bus.py` | IMPLEMENTED (in-memory) | Full runtime replay deferred (T-018) |

### Doc 24: CONTRACT_OWNERSHIP_RECONCILIATION
| Documented claim | Implementation path(s) | Test evidence | Status |
|---|---|---|---|
| Canonical registry of 18 system contracts | `novi/contracts/registry.json` | `test_executable_suite.py` | IMPLEMENTED |
| AuthorizationDecision canonical name | `novi/contracts/safety/authorization-decision/1.0.0/schema.json` | fixture | IMPLEMENTED |
| ActionProposal canonical | `novi/contracts/autonomy/action-proposal/1.0.0/schema.json` | fixture | IMPLEMENTED |
| Action chain proposal→…→outcome | `novi/contracts/tests/integration/test_safety_authorization_integration.py` | `can_execute()` | TEST-ONLY |

### Doc 25 (ARCH-CLOSE-001): contract CI pipeline — `.github/workflows/contracts-validation.yml` runs registry/fixtures/compatibility/evolution/semantics/consumers/persistence stages. **IMPLEMENTED (CI gate exists).**
### Doc 26 (ARCH-CLOSE-002): state-class matrix — `test_consistency_state_matrix.py` validates doc matrix (TEST-ONLY); durable storage `storage.py:216` (IMPLEMENTED); idempotency/stale-revision via `scripts/sqlite_recovery_validation.py` (EVIDENCED).
### Doc 27: storage benchmark spec — spec only; harness in `scripts/storage_benchmark.py` (docs 40/41).
### Doc 28: SQLite technology definition — `storage.py:241` WAL + serialized threading (IMPLEMENTED); durability/backup/migration checks via recovery script (EVIDENCED).
### Doc 29 (ARCH-CLOSE-004): runtime tuple — mechanism doc; tuple evidence in benchmark artifacts (EVIDENCED); **no runtime tuple validator**.
### Doc 30 (ARCH-CLOSE-006): time sync gate — monotonic deadlines/clock domains are TEST-ONLY semantic gates; **`ClockProvider` adapter CLAIM-UNSUPPORTED**; causal metadata `temporal.py:37` IMPLEMENTED (`engine.py:962`).
### Doc 31 (ARCH-CLOSE-007): resource budget baseline — `novi/contracts/resource_budgets.stage1.json` resources + S0–S5 budgets; `test_resource_budgets.py`. IMPLEMENTED.
### Doc 32: compute platform comparison — research baseline; **no code claims**; hardware selection deferred.
### Doc 33: SENSOR & PERCEPTION ARCHITECTURE
| Documented claim | Implementation path(s) | Symbol(s) | Test evidence | Status | Evidence notes |
|---|---|---|---|---|---|
| Camera capture / stale frames | `novi/perception/camera.py:63` | `CameraFeed`, `FrameRecord.is_stale` | `test_camera.py` | IMPLEMENTED | |
| Object detection | `novi/perception/detection.py:39,43` | `ObjectDetector`, `Detection` | `test_detection.py` | IMPLEMENTED | |
| Object tracking | `novi/perception/tracking.py:53` | `ObjectTracker`, `Track` | `test_tracking.py` | IMPLEMENTED | |
| Perception pipeline / world observation | `novi/perception/pipeline.py:30,41` | `PerceptionPipeline`, `WorldObservation` | `test_pipeline.py` | IMPLEMENTED | **as of 2026-08-29 also wired into `MacBrain` (Phase 1a)** |
| Sensor fusion / grounding (§15) | `novi/perception/grounding.py:146`; `grounding_service.py` | `GroundingObservation`, `SpatialQuery` | `test_grounding.py` | IMPLEMENTED | |
| IMU/gyro, LiDAR, GNSS, thermal, night-vision (§3) | none | — | — | CLAIM-UNSUPPORTED | Hardware deferred |

### Doc 34: gyro & night-vision addendum — requirements only; **no implementation (deferred).**
### Doc 35 (ARCH-CLOSE-002): consistency mapping validation — `test_consistency_state_matrix.py`. TEST-ONLY.
### Doc 36 (ARCH-CLOSE-008): deployment manifest contract — schema present (CONTRACTED); **startup validation / rollback lifecycle CLAIM-UNSUPPORTED in runtime.**
### Doc 37 (ARCH-CLOSE-009): architecture-to-test mapping — matrix definition; per-invariant status in doc 50.
### Doc 38 (ARCH-CLOSE-010): dependency numbering audit — `scripts/validate_architecture_integrity.py` + `.github/workflows/architecture-integrity-validation.yml`. IMPLEMENTED.
### Doc 39 (003 runbook) / (010 evidence): runbook + committed validator evidence — both files verified. IMPLEMENTED (executable gate).
### Doc 40 / 41 (ARCH-CLOSE-003): storage benchmark + recovery validation — `scripts/storage_benchmark.py` (write p99 0.121ms, read p99 0.00417ms) and 7-check recovery harness, result JSONs committed (EVIDENCED). SQLite selected: `storage.py:216` (IMPLEMENTED).
### Doc 42 (ARCH-CLOSE-004): runtime version tuple — baseline doc; Python 3.14.6 / SQLite 3.53.4 recorded (EVIDENCED); no runtime validator.
### Doc 43 (ARCH-CLOSE-005): safety integration evidence — integration gate TEST-ONLY; proposal→authorization→safety execution boundary `governance_guard.py`/`runtime.py` IMPLEMENTED.
### Doc 44 (ARCH-CLOSE-006): time validation evidence — `test_time_semantics.py`. TEST-ONLY.
### Doc 45 (ARCH-CLOSE-007): resource & storage policy — budgets IMPLEMENTED; 2× reserve rule + storage-full safety CLAIM-UNSUPPORTED (policy only).
### Doc 46 (ARCH-CLOSE-007): full resource model — model/policy; no code.
### Doc 47 (ARCH-CLOSE-008): deployment & hardware integration — `CameraProvider` protocol IMPLEMENTED; startup gate sequence CLAIM-UNSUPPORTED; offline operation via local SQLite IMPLEMENTED.
### Docs 48/49 (ARCH-CLOSE-009): traceability gate + superseded baseline — definitions only.
### Doc 50 (ARCH-CLOSE-009 FINAL): final traceability matrix (T-001…T-030) — verified anchors (selection):
| Invariant | Status | Evidence |
|---|---|---|
| T-001–004 contracts/fixtures | TESTED | contracts CI |
| T-006–007 safety not eventual; proposal≠execution | TESTED | integration gate |
| T-008 e-stop | DEFERRED (physical) | `test_autonomy_state_machine.py` (software) |
| T-009–012 storage durability/idempotency | EVIDENCED/TESTED | recovery script + result JSON |
| T-013 projection rebuild | DEFERRED | none |
| T-014/015 deployment manifest | CONTRACTED | schema only; **no runtime rejection path** |
| T-016/017 time semantics | TESTED | semantic gate |
| T-018 replay | DEFERRED (full engine) | in-memory only |
| T-019/020 resource budgets | EVIDENCED | target-hardware measurement deferred |
| T-021/022 sensor provenance/fusion | CONTRACTED/DEFERRED | physical adapters deferred |
| T-024 model output untrusted | CONTRACTED/TESTED | `GovernanceGuard` |
| T-026 privacy erasure runtime | CONTRACTED/DEFERRED | partial |
| T-030 hardware identity | CONTRACTED/DEFERRED | manifest schema only |

### README.md (docs/01-system-architecture) — index doc; closure claims consistent with evidence docs 38/39/50 (verified: validator + CI workflow exist).

---

## 4. Unsupported claims (explicit list)

Documented but **not implemented in code** (mostly deliberate deferrals, but stated here so no claim is trusted without checking):

1. ROS 2 / robotics boundary (doc 00); simulation contract (doc 01); runtime profiles B–F (doc 04).
2. Runtime deployment-manifest validation, drift/compat checking, startup compatibility validation, rollback/promotion lifecycle (docs 20, 22, 36 — schemas CONTRACTED, runtime absent).
3. Model admission control/fallback (doc 21); explicit transaction status model (doc 107-108); durability classes A–D enum (doc 107).
4. Replication/distributed memory (doc 109) and multi-agent coordination (doc 114) — deferred by the docs themselves.
5. RPO/RTO tiers (doc 110); soak/long-duration reliability harness (doc 112).
6. `ClockProvider` clock adapter (doc 109/19) — temporal.py is a causal model, not a clock adapter.
7. Physical sensor adapters: IMU/gyro, LiDAR, GNSS, thermal, night-vision (docs 33/34); physical E-stop (T-008); hardware identity (T-030).
8. 2× storage reserve rule and storage-full safety response (doc 45).
9. Full offline/network-isolation test (doc 19).

## 5. Undocumented implementation behavior (code exists, docs silent)

- `novi/brain/audit_trail.py` `AuditTrail` — full audit/redaction/retention engine (doc 05 mentions auditability generically).
- `novi/brain/autonomy_supervisor.py` `AutonomySupervisor` — tick-based supervisor with leases, cancellation, health, e-stop; **not wired into `MacBrain`** (engine uses `BoundedGoalController` + `AutonomyStateMachine`) — Phase 2a target.
- `novi/brain/recovery.py` `RegressionMemory`/`CounterfactualRecorder` — counterfactual learning, distinct from the docs' checkpoint/recovery semantics.
- `novi/brain/memory_hardening.py` `HardenedMemoryManager` — in-memory fallback store when no `store_path`.
- `novi/brain/consolidation.py` — consolidation/summarization; `novi/brain/sleep_cycle.py` — sleep-cycle scheduling.
- `novi/brain/self_model.py`, `soul_acceptance.py` — self-model honesty surfaces.
- `novi/perception/grounding_service.py` `GroundingServer` + `grounding_rpc.py`/`grounding_client.py` — HTTP grounding RPC service.
- `novi/perception/locate_anything*.py` — LocateAnything runtime/geometry/parse.
- `novi/brain/lerobot_export.py`, `teleop.py`, `closed_loop.py` — teleop/closed-loop experiment modules.
- `novi/brain/engine.py` `MacBrain.step()` — the integrated orchestration itself (docs describe the pieces, not the integrated runtime loop).

## 6. Maintenance rule

Any architecture-changing PR must update the affected rows here (or have its claims struck). This file is the frozen baseline referenced by the north-star gap analysis and the P0 remediation plan's Task 01, completed 2026-08-29 (same day as plan publication; before Phase 2 architecture changes landed).