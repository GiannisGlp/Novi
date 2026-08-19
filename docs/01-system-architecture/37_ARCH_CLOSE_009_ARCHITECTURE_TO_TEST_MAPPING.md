# 37 — ARCH-CLOSE-009 Architecture-to-Test Mapping

**Status:** CLOSED — final traceability recorded  
**Priority:** P0 / critical / high importance  
**Authority:** System Architecture  
**Closure item:** ARCH-CLOSE-009  
**Final traceability:** `50_ARCH_CLOSE_009_FINAL_TRACEABILITY_MATRIX_2026-08-19.md`

## 1. Purpose

Every P0 architectural invariant must have an explicit validation path and an evidence class. This matrix prevents architecture from becoming a collection of untestable statements.

The 30-row P0 baseline defined here has now been executed as an architecture traceability audit. The final closure matrix maps each invariant to authority, contract/API, implementation anchor or justified deferral, test/evidence and limitations.

A row is not considered implemented merely because a test identifier exists. The referenced test/evidence must execute and produce an auditable result, or the requirement must be explicitly deferred with a trigger and required evidence.

## 2. Evidence classes

| Code | Evidence |
|---|---|
| D | document/static validation |
| U | unit/contract test |
| I | integration test |
| S | simulation/replay test |
| H | hardware-in-the-loop test |
| P | physical safety test |
| L | long-duration/soak test |
| B | benchmark/performance evidence |
| R | recovery/fault-injection evidence |

## 3. P0 architecture matrix

| ID | Architectural invariant | Primary evidence | Secondary evidence | Gate |
|---|---|---|---|---|
| T-001 | Canonical contracts have one authoritative schema/owner | U | D | contract CI |
| T-002 | Positive contract fixtures validate | U | I | contract CI |
| T-003 | Negative contract fixtures are rejected | U | I | contract CI |
| T-004 | Schema evolution preserves declared compatibility rules | U/I | D | compatibility CI |
| T-005 | Durable state has explicit source-of-truth ownership | D/U | I | architecture/storage |
| T-006 | Safety/authorization state is not eventually consistent authority | U/I | H/P | safety gate |
| T-007 | Action proposal cannot directly execute physical action | I | H/P | safety gate |
| T-008 | Emergency stop is independent of cognition/model runtime | H/P | I | physical safety |
| T-009 | Storage commits satisfy declared durability semantics | I/R | B | storage gate |
| T-010 | Crash recovery reconstructs valid state | R/I | L | storage gate |
| T-011 | Idempotent retries cannot duplicate logical transitions | U/I | R | storage gate |
| T-012 | Concurrent stale writes are rejected/reconciled by contract | I | B | storage gate |
| T-013 | Projection/index/cache state is rebuildable | I/S | R | storage/memory |
| T-014 | Deployment manifest identifies exact runtime/model/config state | U/I | D | deployment gate |
| T-015 | Incompatible deployment tuples are rejected before authority begins | I | U | deployment gate |
| T-016 | Event/sensor timestamps preserve required temporal semantics | U/I | H/S | time gate |
| T-017 | Stale/out-of-order sensor data is detected/governed | I/S | H | time/perception |
| T-018 | Replay preserves required deterministic semantics | S | I | validation gate |
| T-019 | Resource budgets are measurable and bounded | B | H/L | resource gate |
| T-020 | CPU/GPU/RAM/storage/thermal/power behavior is recorded on target hardware | B/H | L | resource gate |
| T-021 | Required sensor observations carry provenance and timestamps | U/I | H | sensor gate |
| T-022 | Sensor fusion preserves uncertainty rather than hiding conflicts | I/S | H | perception gate |
| T-023 | Hardware faults produce governed degradation/safe-stop behavior | H/P | L | hardware safety |
| T-024 | Model output is treated as untrusted input | U/I | H/P | security/safety |
| T-025 | Protected controls cannot be modified by adaptive cognition | U/I | H/P | security |
| T-026 | Privacy-sensitive state follows retention/erasure dependencies | U/I | D | privacy gate |
| T-027 | Backup/restore produces internally consistent recoverable state | R/I | B | storage gate |
| T-028 | Migration preserves IDs, revisions, provenance and lifecycle semantics | U/I | R | storage gate |
| T-029 | Runtime/version tuple is captured and reproducible | U/I | D | compatibility gate |
| T-030 | Hardware deployment identity is captured without exposing secrets | U | D | deployment/security |

## 4. Final closure state

The final traceability audit recorded all 30 invariants in:

`50_ARCH_CLOSE_009_FINAL_TRACEABILITY_MATRIX_2026-08-19.md`

```text
T-001 through T-030 = 30 / 30 mapped
GAP classifications = 0
```

The matrix distinguishes executable evidence from architectural contracts and future physical/model/runtime work. Physical-only claims are explicitly deferred rather than falsely promoted to software evidence.

## 5. Mac-first validation strategy

The first validation environment is the user's Mac. This is appropriate for:

- contract validation;
- storage/recovery experiments;
- runtime compatibility;
- model invocation lineage;
- replay;
- sensor mocks and recorded datasets;
- perception pipeline integration;
- deployment manifest validation.

The Mac is not treated as evidence of final robot performance, thermal behavior, battery life, motor safety or physical sensor reliability.

## 6. Physical promotion gate

When the first physical Novi platform is available, the validation matrix must be extended with:

- actual sensor timestamps and synchronization;
- camera/LiDAR throughput;
- IMU/gyroscope behavior;
- motor-control latency;
- emergency-stop response;
- hardware fault injection;
- CPU/GPU/RAM/power/thermal measurements;
- 8–10 hour endurance target;
- vibration/environmental behavior;
- degraded-network/disconnected behavior.

These are future evidence requirements, not ARCH-CLOSE-009 gaps.

## 7. Closure criterion

ARCH-CLOSE-009 is closed because:

1. every P0 architecture invariant has a validation identifier;
2. each identifier has an evidence class;
3. implementation-dependent requirements have an implementation/evidence anchor or justified deferral;
4. physical-only claims are explicitly marked pending until hardware exists;
5. results are recorded in the final traceability matrix;
6. no P0 invariant is left without a validation path;
7. zero GAP classifications remain.

## 8. Architectural invariant

> **No P0 architecture claim is considered closed without a defined validation path and recorded evidence appropriate to the claim.**
