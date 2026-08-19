# 02 — Implementation Lifecycle

Every Brain implementation unit progresses through explicit states.

```text
PLANNED
  ↓
DESIGNED
  ↓
IMPLEMENTED
  ↓
UNIT TESTED
  ↓
CI VALIDATED
  ↓
REAL MODEL TESTED
  ↓
BENCHMARKED
  ↓
EVIDENCE RECORDED
  ↓
INTEGRATED
  ↓
ACCEPTED
```

## Definitions

### Planned
Scope, dependencies, risks and acceptance criteria are documented.

### Designed
The interface, ownership and data flow are agreed and documented.

### Implemented
Executable code exists and follows the approved contract.

### Unit tested
Deterministic tests cover normal and important failure paths.

### CI validated
The repository workflow executes the relevant tests successfully.

### Real model tested
The actual selected checkpoint/runtime has been executed outside the deterministic CI environment.

### Benchmarked
Performance and capability have been measured using a versioned workload.

### Evidence recorded
Results are stored with complete provenance and reproducibility metadata.

### Integrated
The component works with the surrounding Brain components under representative workloads.

### Accepted
The formal acceptance gate passes and the completion tracker is updated.

## Rework rule

Failure at any stage returns the work to the earliest affected stage. A benchmark failure does not justify weakening the acceptance threshold without an explicit decision record.

## Completion rule

A component is not considered production-ready merely because code and CI are green. Real-model and system-level validation are required wherever the component participates in physical intelligence.
