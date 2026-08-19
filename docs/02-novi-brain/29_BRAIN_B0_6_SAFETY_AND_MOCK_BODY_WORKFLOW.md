# B0.6 — Safety Gateway and Mock Body Workflow

**Status:** P0 workflow — implementation complete, validation pending  
**Domain:** Brain  
**Stage:** B0 Runtime Foundation  
**Date:** 2026-08-19  
**Predecessor:** `28_BRAIN_B0_5_HEALTH_AND_OBSERVABILITY_WORKFLOW.md`

## Purpose

Establish the Stage-0 physical-action boundary so no proposed action can reach the embodiment adapter without an explicit safety decision.

## Mandatory execution boundary

```text
ActionProposal
      ↓
Proposal validation
      ↓
Safety Gateway
      ↓
SafetyDecision
   ┌──┴──┐
 DENY   ALLOW
  ↓       ↓
Reject  Mock Body
          ↓
      ActionOutcome
```

The body adapter has no alternate execution path.

## Safety policy for Stage 0

Stage 0 uses a deliberately narrow allow-list. `inspect` is the only action currently authorized for mock-body execution.

Protected/bypass actions such as `disable_safety`, `emergency_stop_bypass` and `unsafe_motor_override` are always denied.

Unknown actions are denied until explicitly introduced through a future safety/authorization decision and corresponding contract/tests.

This is not the final physical safety policy. It is the minimum software boundary required before simulated embodiment can be trusted as a test subject.

## Implemented controls

- required action name;
- required correlation ID;
- protected-action rejection;
- unknown-action rejection;
- explicit `SafetyDecision` for every proposal;
- body rejection of every denied decision;
- rejected-outcome recording;
- successful execution only after authorization;
- action outcome generation;
- event evidence for safety decisions and completion;
- no direct body execution in the normal Brain cycle.

## Validation requirements

1. unknown action denied;
2. protected action denied;
3. missing action rejected;
4. denied proposal cannot execute;
5. rejected action is recorded;
6. authorized `inspect` action executes;
7. body execution count proves authorization boundary;
8. safety decision preserves correlation identity;
9. normal Brain cycle remains operational;
10. safe-stop remains enforced by the supervisor.

## Acceptance criteria

B0.6 can be marked **VALIDATED** only after the repository workflow passes against the current `main` revision.

This workflow does not mark B0 or the Brain domain complete. It is the final implementation workflow of Stage B0.
