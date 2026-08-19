# B0.3 — Brain Supervisor and Lifecycle Workflow

**Status:** P0 workflow — implementation complete, validation pending  
**Domain:** Brain  
**Stage:** B0 Runtime Foundation  
**Date:** 2026-08-19  
**Predecessor:** `25_BRAIN_IMPLEMENTATION_CLOSURE_AND_STAGE_0_BASELINE.md`

## Purpose

Harden the Stage-0 Brain supervisor so lifecycle transitions, health state, degraded operation, recovery, safe-stop, failure and shutdown are explicit, bounded and testable.

## Lifecycle model

```text
BOOTING
  ↓
INITIALIZING
  ├────────→ FAILED → SHUTTING_DOWN
  ↓
READY
  ↓
ACTIVE
  ├──→ DEGRADED ──→ RECOVERING ──→ ACTIVE
  ├──→ SAFE_STOP ──→ SHUTTING_DOWN
  └──→ SHUTTING_DOWN
```

The runtime rejects transitions not explicitly allowed by the lifecycle table.

## Implemented controls

- Startup is only valid from `BOOTING`.
- `BOOTING → INITIALIZING → READY → ACTIVE` is explicit.
- Degraded operation is explicit and carries a reason.
- Recovery is explicit and returns to `ACTIVE` only after the recovery transition.
- Failure is explicit during boot/initialization/recovery.
- Safe-stop is distinct from normal shutdown.
- Safe-stopped or failed runtimes cannot execute a cycle.
- Shutdown is terminal and idempotent once already shutting down.
- Health status tracks lifecycle state.
- Lifecycle changes emit runtime events.
- Event correlation/causation is preserved through the action path.

## Validation requirements

The workflow tests:

1. normal startup;
2. repeated-start rejection;
3. invalid transition rejection;
4. degraded state;
5. recovery;
6. safe-stop;
7. failure and shutdown;
8. cycle gating;
9. deterministic closed-cycle behavior;
10. safety bypass rejection.

## Acceptance criteria

B0.3 can be marked **VALIDATED** only after the repository workflow passes against the current `main` revision.

This workflow does not mark the Brain domain complete. It is one implementation workflow within Stage B0.
