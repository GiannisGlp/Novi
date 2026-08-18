# 22 — Architecture Closure and Baseline

**Status:** P0 closure workstream
**Priority:** P0
**Authority:** System Architecture
**Scope:** Close the remaining architecture gaps before the System Architecture domain can be marked `COMPLETE`.

## 1. Purpose

This document is the execution register for the final System Architecture closure campaign. It does not replace existing architecture authorities. It identifies the remaining gaps, their authoritative source documents, required evidence, completion criteria, and dependencies.

## 2. Completion rule

System Architecture may be marked `COMPLETE` only when every P0/P1 closure item below has either:

1. an authoritative decision and implementation contract;
2. objective validation evidence where implementation-dependent;
3. traceability to a test/validation artifact; and
4. no unresolved contradiction with another authoritative domain.

## 3. Closure workstreams

| ID | Workstream | Current state | Completion evidence |
|---|---|---|---|
| ARCH-CLOSE-001 | Canonical contracts | 🟡 | Registry + executable schemas + ownership + validation rules |
| ARCH-CLOSE-002 | Consistency mapping | 🟡 | State-class matrix with required/provided guarantees |
| ARCH-CLOSE-003 | Stage-1 durable storage | 🟡 | ADR + benchmark + recovery evidence |
| ARCH-CLOSE-004 | Runtime/version tuple | 🟡 | Tested compatibility manifest |
| ARCH-CLOSE-005 | Safety integration | 🟡 | Cross-domain safety/control contracts + traceability |
| ARCH-CLOSE-006 | Time synchronization | 🟡 | Clock contract + synchronization/error budget |
| ARCH-CLOSE-007 | Resource budgets | 🟡 | Initial measured CPU/GPU/RAM/storage/thermal budgets |
| ARCH-CLOSE-008 | Deployment manifest | 🟡 | Reproducible manifest and validation procedure |
| ARCH-CLOSE-009 | Architecture-to-test mapping | 🟡 | Requirement → test/evidence matrix |
| ARCH-CLOSE-010 | Dependency/numbering integrity | 🟡 | Full cross-reference audit with no stale authoritative references |

## 4. Authority boundaries

Existing documents remain authoritative for their domains. This file is a closure register only.

- System architecture: system topology, boundaries, runtime profiles, cross-domain contracts.
- Cognition: cognitive semantics and cognition implementation contracts.
- Soul: identity, personality, values, motivations, social character and affect semantics.
- Memory/Knowledge: durable knowledge, memory and provenance semantics.
- Autonomy: goals, attention, planning, initiative and action selection.
- Hardware: physical components, interfaces and physical safety constraints.
- Security: security threat model and protected controls.
- Validation: evidence and verification strategy.

No closure task may silently move semantic ownership between these domains.

## 5. ARCH-CLOSE-001 — Canonical contracts

Close the remaining architecture-level contract gap by producing a canonical registry for at least:

- EventEnvelope
- Observation
- Evidence
- WorldStateChange
- MemoryRecord
- KnowledgeRecord
- Goal
- Plan
- ActionProposal
- Authorization
- SafetyDecision
- ActionExecution
- ActionOutcome
- ModelInvocation
- HardwareHealth
- DeploymentManifest

The registry must point to the authoritative schema and define versioning, compatibility, provenance, timestamps, privacy classification and validation requirements.

## 6. ARCH-CLOSE-002 — Consistency mapping

Create a state-class matrix covering:

- source-of-truth owner;
- durability requirement;
- consistency class;
- transaction requirement;
- concurrency model;
- conflict policy;
- replication requirement;
- recovery requirement;
- deletion/erasure behavior.

The matrix must distinguish Stage-1 local requirements from future distributed requirements.

## 7. ARCH-CLOSE-003 — Stage-1 durable storage

The Stage-1 implementation must select storage through the existing technology decision framework rather than assumption. The decision must include alternatives, benchmark criteria, crash/replay behavior, transaction semantics, backup/recovery behavior and Mac compatibility.

No storage technology becomes architectural truth merely because it is convenient for the prototype.

## 8. ARCH-CLOSE-004 — Runtime/version tuple

Define a reproducible compatibility tuple for the Mac-first development environment and future promotion targets. At minimum record:

- macOS version;
- Python/runtime versions;
- compiler/toolchain where applicable;
- ML frameworks;
- model runtimes;
- ROS 2 profile where applicable;
- simulator version;
- database/storage version;
- schema version;
- Novi software revision.

Each vendor-dependent component requires primary-source validation and a Novi-specific compatibility test.

## 9. ARCH-CLOSE-005 — Safety integration

System architecture must connect the software authorization hierarchy to the dedicated security/safety and hardware domains. The closure evidence must demonstrate that:

- model output is untrusted input;
- adaptive state cannot modify protected safety state;
- physical action requires authorization and safety gates;
- emergency stop is independent of the reasoning model;
- hardware faults produce governed degradation/safe-stop behavior.

## 10. ARCH-CLOSE-006 — Time synchronization

Close the time architecture with implementation requirements for:

- wall-clock time;
- monotonic time;
- event time;
- processing time;
- simulation time;
- sensor timestamps;
- hardware timestamps;
- clock synchronization;
- drift/error bounds;
- stale and out-of-order data;
- replay determinism.

The result must define which timestamps are authoritative for each class of decision.

## 11. ARCH-CLOSE-007 — Resource budgets

Define measured initial budgets for the Mac-first runtime:

- CPU;
- GPU;
- unified memory;
- storage;
- model residency;
- queue depth/backpressure;
- thermal/power where measurable;
- latency budgets by critical loop.

Budgets must be treated as hypotheses until benchmark evidence validates them.

## 12. ARCH-CLOSE-008 — Deployment manifest

Define a machine-readable deployment manifest containing all artifacts required to reproduce a Novi runtime, including software versions, model identifiers/hashes, configuration, schemas, data migrations and hardware profile.

The manifest must support validation before startup and provenance after execution.

## 13. ARCH-CLOSE-009 — Architecture-to-test mapping

Every P0 architecture invariant must map to a validation identifier. The matrix must distinguish:

- static/document validation;
- unit/contract tests;
- integration tests;
- simulation tests;
- HIL tests;
- physical safety tests;
- long-duration/soak tests.

An architectural statement without a validation path is not considered fully closed.

## 14. ARCH-CLOSE-010 — Dependency and numbering integrity

Audit all architecture references and numbering. Every reference must point to an existing current document or explicitly identified external standard. Stale historical numbering must not be treated as authority.

The audit must also detect duplicate authorities, circular ownership and conflicting definitions.

## 15. Research requirements

All factual technology claims must be validated against primary sources where available, especially:

- NVIDIA official documentation;
- Apple official documentation;
- ROS 2 official documentation;
- relevant standards;
- peer-reviewed research for scientific claims.

Secondary sources may provide context but cannot establish a P0 technology decision by themselves.

## 16. Architecture completion gate

The System Architecture domain becomes `COMPLETE` only after:

```text
ARCH-CLOSE-001 ✓
ARCH-CLOSE-002 ✓
ARCH-CLOSE-003 ✓
ARCH-CLOSE-004 ✓
ARCH-CLOSE-005 ✓
ARCH-CLOSE-006 ✓
ARCH-CLOSE-007 ✓
ARCH-CLOSE-008 ✓
ARCH-CLOSE-009 ✓
ARCH-CLOSE-010 ✓
        ↓
Final architecture audit
        ↓
No P0/P1 contradiction
        ↓
Architecture = COMPLETE
```

Until then, the program status must remain `IN PROGRESS` for System Architecture.

## 17. Required update

When each closure item is completed, update this register with:

- completion date;
- commit/reference;
- evidence location;
- tests/benchmarks;
- remaining risks;
- reviewer/status.

The global program tracker must not be marked complete based solely on document existence; closure requires evidence.
