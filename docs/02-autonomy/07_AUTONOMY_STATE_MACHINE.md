# 07 — Autonomy State Machine

## Status

**DESIGN**

## Purpose

The state machine defines deterministic lifecycle states for the autonomy runtime. Model outputs may influence transitions, but cannot bypass transition guards.

## States

```text
BOOTING
  ↓
INITIALIZING
  ↓
OBSERVING
  ↓
AWARE
  ├── INTERACTING
  ├── PLANNING
  ├── EXECUTING
  ├── LEARNING
  ├── MAINTENANCE
  └── SAFE_DEGRADED
```

Terminal/recovery states include `SHUTTING_DOWN`, `EMERGENCY_STOP`, and `FAULT_RECOVERY`.

## State Definitions

### BOOTING
Hardware/runtime initialization. No autonomous external action.

### INITIALIZING
Loads configuration, verifies dependencies, establishes sensor availability, loads models/services, and initializes world state.

### OBSERVING
Normal passive operation. Collects and processes observations.

### AWARE
A meaningful event or situation requires active cognitive processing.

### INTERACTING
Novi is actively engaged with a person or social interaction.

### PLANNING
A goal requires reasoning or multi-step planning.

### EXECUTING
An authorized capability is running.

### LEARNING
Background consolidation or approved learning is occurring.

### MAINTENANCE
Diagnostics, cleanup, indexing, model health or other maintenance work.

### SAFE_DEGRADED
One or more important components are unavailable. Novi continues only the subset of behavior considered safe.

### EMERGENCY_STOP
All non-essential physical actions are stopped. Recovery requires explicit hardware/software safety conditions.

## Transition Rules

Every transition has:

- source state;
- event/condition;
- guard;
- destination;
- side effects;
- audit event.

## Interruptions

High-priority events can interrupt lower-priority states. Examples:

```text
EXECUTING navigation
        ↓
person detected unexpectedly
        ↓
safety evaluation
        ↓
pause / stop / continue
```

The interruption policy is deterministic for safety-critical cases.

## State Persistence

Transient runtime state may be persisted for recovery. Recovery must not blindly resume an action whose physical assumptions may have become stale.

## Acceptance Criteria

- all transitions are explicit;
- invalid transitions are rejected;
- emergency conditions override normal operation;
- recovery revalidates world state;
- state changes are observable and auditable;
- simulation can deterministically exercise every state and transition.
