# 48 — ARCH-CLOSE-009 Architecture → Implementation Traceability Gate

**Status:** GATE DEFINED — execution pending  
**Priority:** P0  
**Authority:** System Architecture  
**Scope:** Verify that authoritative architecture claims have corresponding implementation/contracts/tests or an explicit deferred status.

## 1. Purpose

Novi has a substantial architecture corpus. ARCH-CLOSE-009 prevents documentation from becoming an independent reality by requiring every closure-critical architectural claim to map to executable contracts, code, tests, workflows, evidence, or an explicit hardware/deployment deferral.

The repository already contains consistency and state-class matrices, architecture completion/closure gates, a Brain implementation blueprint, storage and recovery architecture, and a completion tracker. fileciteturn387file0 fileciteturn387file3 fileciteturn387file4 fileciteturn387file5

## 2. Traceability classes

Every closure-critical item must be classified as exactly one of:

- **IMPLEMENTED** — executable implementation exists.
- **CONTRACTED** — normative contract/schema exists and is enforced by validation.
- **TESTED** — executable test/gate demonstrates the requirement.
- **EVIDENCED** — measured evidence exists but does not yet constitute implementation.
- **DEFERRED** — intentionally postponed because it depends on hardware, model, or later phase.
- **GAP** — required architecture has no adequate implementation/evidence/deferral.

`GAP` is the only unacceptable class for an architecture closure claim.

## 3. Traceability chain

For each item record:

```text
architecture requirement
        ↓
authoritative document
        ↓
contract / interface / schema
        ↓
implementation
        ↓
test / validation gate
        ↓
evidence
        ↓
status + limitations
```

A document without an implementation/evidence mapping must not be described as implemented.

## 4. Priority scope

The first execution pass covers:

1. System architecture closure items ARCH-CLOSE-001 through ARCH-CLOSE-010;
2. safety authorization and emergency-stop boundaries;
3. time semantics;
4. durable state/storage;
5. Brain orchestration/cognitive cycle boundaries;
6. memory/knowledge contracts;
7. model/inference boundaries;
8. deployment/runtime boundaries;
9. resource budgets;
10. sensor/actuator interface contracts.

## 5. Existing implementation anchors

Known repository anchors include:

- contract validation suites;
- safety authorization integration gate;
- time semantics integration gate;
- resource-budget validation assets;
- SQLite storage benchmark/recovery harness;
- architecture completion/closure documents;
- Brain implementation blueprint;
- memory/knowledge schema and migration architecture;
- durable event-log and execution semantics;
- transaction/concurrency/consistency architecture;
- recovery/checkpointing architecture.

The existence of these files is not itself sufficient; each must be mapped to the requirement it satisfies.

## 6. Required audit output

Produce a machine-readable and human-readable matrix with columns:

| Requirement | Authority | Contract/API | Implementation | Test | Evidence | Status | Gap / limitation |
|---|---|---|---|---|---|---|---|

The audit must distinguish:

- implementation present;
- implementation planned;
- test present;
- test passing;
- evidence measured;
- physical validation pending.

## 7. No false closure

The following do **not** constitute implementation by themselves:

- architecture prose;
- TODO lists;
- filenames;
- passing documentation lint;
- a unit test for a different layer;
- a Mac benchmark used to claim robot performance;
- software safety tests used to claim physical safety;
- a model being named without an executable inference integration.

## 8. Deferred hardware boundary

The following may legitimately remain `DEFERRED` while Mac-first development continues:

- final Jetson/Thor selection;
- CUDA/JetPack/TensorRT versions;
- physical sensor drivers;
- physical actuator drivers;
- battery/thermal measurements;
- HIL/physical safety validation.

A deferred item must state its trigger for activation and required evidence.

## 9. Closure criteria

ARCH-CLOSE-009 can close only when:

1. all P0 closure requirements have a traceability entry;
2. no P0 item is classified `GAP`;
3. every `IMPLEMENTED` claim points to implementation and executable validation;
4. every `EVIDENCED` claim states limitations;
5. every `DEFERRED` claim states why and when it becomes actionable;
6. contradictory architecture claims are identified and resolved;
7. the matrix is reproducible from the repository.

## 10. Architectural invariant

> **Every authoritative Novi architecture decision must be traceable to implementation, executable validation, measured evidence, or an explicit justified deferral. Documentation alone never closes an implementation requirement.**
