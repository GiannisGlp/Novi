# Novi — Global Completion Gate

**Status:** P0 / canonical program rule  
**Date:** 2026-08-18  
**Authority:** Novi program / North Star governance  

## 1. Purpose

This document establishes the hard rule for the Novi program:

> **No new implementation phase begins until every program-status domain is complete.**

Documentation, prototypes, individual domain completion, or a strong architecture do not open the gate.

The objective is to reach a point where implementation starts from a complete, researched, internally consistent and validated system definition rather than discovering architecture while coding.

## 2. Domains that must reach COMPLETE

All twelve domains are mandatory:

1. Soul
2. System Architecture
3. Brain
4. Cognition
5. Memory
6. Autonomy
7. Hardware
8. Technology
9. Simulation
10. Validation
11. Security
12. Deployment

There are no optional P0 domains.

## 3. Definition of COMPLETE

A domain is `COMPLETE` only when all applicable conditions are satisfied:

- authoritative documents exist;
- repository-wide duplication and ownership audit is complete;
- requirements are explicit;
- architecture is internally consistent;
- interfaces and schemas have canonical owners;
- implementation responsibilities are explicit;
- technology decisions are evidence-backed where applicable;
- NVIDIA/ROS/Apple/project primary sources have been checked where relevant;
- scientific claims are supported by appropriate research;
- failure and degradation behavior is defined;
- security and privacy implications are defined;
- resource constraints are defined;
- validation strategy exists;
- acceptance criteria exist;
- dependencies are closed or explicitly resolved;
- traceability to the North Star is established;
- completion evidence has been reviewed.

A document existing is never sufficient evidence of completion.

## 4. Program gate states

### CLOSED
At least one domain is not complete or a P0 cross-domain dependency remains unresolved.

### READY FOR FINAL AUDIT
All domain work is complete and only the final cross-domain consistency/evidence audit remains.

### OPEN
All twelve domains are complete, every P0 cross-domain workstream is closed, and the final readiness audit has passed.

## 5. Current state

**GLOBAL GATE: CLOSED**

Current domains requiring completion work remain:

- System Architecture
- Brain
- Cognition
- Memory
- Autonomy
- Hardware
- Technology
- Simulation
- Validation
- Security
- Deployment

Soul is the first domain currently treated as complete, subject only to normal consuming-domain cross-reference maintenance.

### 5.1 Reconciliation with the active Brain implementation phase (2026-08-22)

The gate rule is: **no *new* implementation phase begins** until every program-status
domain is complete (§1). The Mac Brain phase is the current, authorized phase under the
program tracker (`docs/00-strategy/NOVI_DOCUMENTATION_AND_IMPLEMENTATION_COMPLETION_TRACKER.md`)
and the `MAC_BRAIN/PERFECTING_PLAN/` roadmap — it is not a *new* phase. The gate therefore
does not forbid the ongoing Brain-phase work; it continues to forbid opening *additional*
phases (e.g. a hardware-implementation phase) while design/definition gaps in the incomplete
domains remain.

This does not relax the completion requirement: the Brain domain itself remains
IN PROGRESS (see gap analysis `docs/00-strategy/NOVI_BRAIN_GAP_ANALYSIS_AND_NEXT_STEPS.md`),
and every §10 readiness box must still be checked before the gate opens.

## 6. Completion campaign

We now work through the program status itself. We do **not** start another implementation workstream simply because one domain has reached a sufficient level for implementation.

The campaign is:

```text
SYSTEM ARCHITECTURE
        ↓
BRAIN
        ↓
COGNITION
        ↓
MEMORY
        ↓
AUTONOMY
        ↓
TECHNOLOGY
        ↓
HARDWARE
        ↓
SIMULATION
        ↓
TIME / SYNCHRONIZATION
        ↓
SECURITY
        ↓
DEPLOYMENT
        ↓
VALIDATION
        ↓
CROSS-DOMAIN AUDIT
        ↓
GLOBAL GATE
```

The order may change when dependency analysis proves a safer ordering, but **the completion requirement does not change**.

## 7. Cross-domain mandatory gates

The following are P0 program-wide workstreams:

### Contracts
Every interface has one semantic owner and one canonical contract.

### Time
System, monotonic, sensor, ROS, simulation and hardware clocks are defined, synchronized and traceable.

### Observability
A causal trace can follow perception/evidence through cognition, memory, autonomy, policy, action and outcome.

### Resources
CPU, GPU, unified memory, storage, network, power and thermal budgets are defined for the Mac-first system and future targets.

### Provenance
Models, datasets, memories, learned behaviors and generated artifacts have provenance/version/lifecycle semantics.

### Failure/degradation
The system defines safe behavior for missing, degraded or contradictory sensors, models, memory, network, compute, speech and actuation.

### Documentation integrity
No duplicate semantic authority, stale ownership, broken numbering or undocumented critical dependency remains.

## 8. Research standard

Every critical document must use the strongest applicable evidence available.

Preferred order:

1. NVIDIA official documentation for NVIDIA technologies;
2. ROS official documentation for ROS technologies;
3. Apple official documentation for Apple Silicon/macOS/MLX;
4. official documentation for adopted open-source projects;
5. peer-reviewed research for scientific claims;
6. relevant standards/specifications;
7. reputable secondary sources only where primary sources are insufficient.

Every material decision must distinguish:

```text
SOURCE-BACKED FACT
        ↓
NOVI INTERPRETATION
        ↓
NOVI ARCHITECTURAL DECISION
        ↓
VALIDATED RESULT
```

Vendor capability is not automatically a Novi architectural requirement.

## 9. Completion evidence

Each domain must maintain a completion record containing, as applicable:

- authoritative document inventory;
- requirements coverage;
- dependency map;
- technology decisions;
- source/research evidence;
- contracts/schema inventory;
- security/privacy review;
- failure/degradation review;
- resource review;
- validation matrix;
- acceptance results;
- unresolved risks;
- final completion decision.

## 10. Final readiness test

The gate can open only when all of the following are true:

```text
[ ] Soul COMPLETE
[ ] System Architecture COMPLETE
[ ] Brain COMPLETE
[ ] Cognition COMPLETE
[ ] Memory COMPLETE
[ ] Autonomy COMPLETE
[ ] Hardware COMPLETE
[ ] Technology COMPLETE
[ ] Simulation COMPLETE
[ ] Validation COMPLETE
[ ] Security COMPLETE
[ ] Deployment COMPLETE

[ ] Canonical contracts closed
[ ] Time/synchronization closed
[ ] Observability closed
[ ] Resource governance closed
[ ] Provenance closed
[ ] Failure/degradation closed
[ ] Documentation integrity closed

[ ] No unresolved P0 contradiction
[ ] No duplicate semantic authority
[ ] All P0 requirements have validation evidence
[ ] Mac-first environment fully specified
[ ] Reproducible deployment defined
[ ] Final cross-domain audit passed
```

Only after every box is checked does the project move to the next implementation phase.

## 11. Operating rule

For every subsequent task:

1. inspect this gate;
2. inspect the master program tracker;
3. identify the incomplete domain that owns the work;
4. audit existing documents before creating anything;
5. research authoritative sources;
6. complete the domain requirement;
7. validate and record evidence;
8. update program status;
9. commit to `main`;
10. verify the result on `main`.

> **Until the Global Completion Gate is OPEN, we are completing the definition of Novi — not starting a new implementation phase.**
