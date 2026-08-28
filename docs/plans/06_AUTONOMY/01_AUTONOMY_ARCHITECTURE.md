# 01 — Autonomy Architecture

## Objective

Define the canonical control architecture that allows Novi to operate continuously without allowing an unconstrained language model to become the robot controller.

## Target architecture

```text
                 ┌───────────────────────────┐
                 │        Human / Goal        │
                 └─────────────┬─────────────┘
                               ↓
                    ┌────────────────────┐
                    │    Goal Manager     │
                    └─────────┬──────────┘
                              ↓
                    ┌────────────────────┐
                    │ Autonomy Supervisor │
                    │ state + authority   │
                    └─────────┬──────────┘
                              ↓
       ┌──────────────────────┼──────────────────────┐
       ↓                      ↓                      ↓
   World State             Memory                Prediction
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              ↓
                    ┌────────────────────┐
                    │ Decision / Planner │
                    └─────────┬──────────┘
                              ↓
                    ┌────────────────────┐
                    │ Safety / Governance│
                    └─────────┬──────────┘
                              ↓
                    ┌────────────────────┐
                    │   Skill Executor   │
                    └─────────┬──────────┘
                              ↓
                         Robot / Tools
                              ↓
                    ┌────────────────────┐
                    │ Verification       │
                    └─────────┬──────────┘
                              ↓
                     state + memory update
                              ↺
```

## Step-by-step implementation

### Step 1 — Create `AutonomyState`

Define explicit states rather than implicit booleans:

- `IDLE`
- `OBSERVING`
- `INTERPRETING`
- `GOAL_PENDING`
- `PLANNING`
- `AWAITING_AUTHORITY`
- `EXECUTING`
- `VERIFYING`
- `RECOVERING`
- `PAUSED`
- `SAFE_STOP`
- `COMPLETED`
- `FAILED`

Every transition must have an event, timestamp, reason and originating component.

### Step 2 — Define authority levels

At minimum:

- `PASSIVE`: observe, remember, answer.
- `ASSISTED`: propose actions but require approval.
- `BOUNDED_AUTONOMY`: execute pre-approved low-risk skills.
- `SUPERVISED_AUTONOMY`: execute longer plans while allowing interruption.
- `FULL_LOCAL_AUTONOMY`: future state, enabled only after explicit safety certification.

Authority is not equivalent to model confidence.

### Step 3 — Define autonomy cycle

Create a deterministic `AutonomySupervisor.tick()`:

1. ingest new events;
2. refresh world state;
3. expire stale observations;
4. evaluate active goal;
5. check safety conditions;
6. determine whether new information is required;
7. select/revise plan;
8. request policy approval;
9. execute at most the next bounded action;
10. verify it;
11. update state and memory;
12. schedule the next tick.

Never let one tick execute an unbounded sequence.

### Step 4 — Add leases and timeouts

Every active goal, plan and action gets:

- creation time;
- deadline;
- maximum execution duration;
- cancellation token;
- owner;
- authority level;
- retry budget.

Expired leases automatically transition to recovery or safe stop.

### Step 5 — Add event sourcing

Every autonomous transition must generate an immutable event:

```json
{
  "event_type": "ACTION_STARTED",
  "goal_id": "...",
  "plan_id": "...",
  "skill_id": "...",
  "authority": "BOUNDED_AUTONOMY",
  "reason": "goal_requires_object_search",
  "timestamp": "..."
}
```

This becomes the basis for debugging, evaluation and future learning.

### Step 6 — Separate proposal from execution

Model output may produce:

`ActionProposal`

but only the deterministic policy layer can create:

`AuthorizedAction`.

Only `AuthorizedAction` can reach the executor.

### Step 7 — Add cancellation semantics

Cancellation must be idempotent. A stop request must propagate through planner, executor and hardware adapter. A cancelled action cannot later resume accidentally.

### Step 8 — Add supervisor health checks

Monitor:

- perception freshness;
- world-model freshness;
- model availability;
- planner responsiveness;
- executor heartbeat;
- sensor heartbeat;
- action timeout rate;
- memory/storage health;
- CPU/GPU/thermal budget;
- safety monitor status.

A degraded dependency must reduce autonomy authority rather than silently continue.

## Required contracts

Implement and version:

- `AutonomyState`
- `AutonomyEvent`
- `Goal`
- `GoalStatus`
- `Plan`
- `PlanStep`
- `ActionProposal`
- `AuthorizedAction`
- `ActionResult`
- `VerificationResult`
- `RecoveryRequest`
- `AuthorityContext`
- `AutonomyHealth`

All contracts require provenance and timestamps.

## Tests

Unit tests must cover every legal state transition and reject every illegal transition. Integration tests must demonstrate interruption during observation, planning, execution and verification. Property tests should verify that no path can execute an action without authorization.

## Acceptance gate

`A-ARCH-01`: 10,000 simulated autonomy ticks with injected timeouts, stale sensors, cancellations and planner failures must never execute an unauthorized action and must always reach a terminal or recoverable state.
