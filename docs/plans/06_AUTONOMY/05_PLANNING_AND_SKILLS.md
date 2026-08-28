# 05 — Planning, Behavior Trees and Skills

## Objective

Convert high-level goals into bounded, executable and verifiable behavior without allowing free-form reasoning to directly control hardware.

## Planning hierarchy

```text
Mission goal
  ↓
Task decomposition
  ↓
Behavior tree / task graph
  ↓
Skill
  ↓
Skill preconditions
  ↓
Atomic action
  ↓
Verification
```

## Step-by-step

### Step 1 — Define skill contracts

Every skill must declare:

- ID/version;
- purpose;
- required capabilities;
- input schema;
- output schema;
- preconditions;
- invariants;
- expected effects;
- safety level;
- timeout;
- retry policy;
- cancellation behavior;
- verification method;
- rollback/recovery strategy.

### Step 2 — Separate planner from executor

Planner creates a `Plan`. Executor consumes only validated `PlanStep`s. The planner must not call motor APIs directly.

### Step 3 — Add hierarchical planning

Start with deterministic decomposition for known skills. Add model-assisted decomposition later. Model-generated plans must be parsed and validated against registered skills.

### Step 4 — Add behavior-tree semantics

Use explicit control nodes:

- sequence;
- selector/fallback;
- parallel;
- retry with bounded count;
- timeout;
- condition;
- action;
- recovery.

Behavior trees are preferable for long-running autonomy because execution state remains explicit and recoverable.

### Step 5 — Add precondition checking

Before each skill:

- required object exists;
- pose is fresh;
- robot is localized;
- route is valid;
- safety conditions pass;
- authority is sufficient;
- resource budget remains.

### Step 6 — Add postcondition verification

Examples:

`NavigateTo`: robot pose within tolerance.

`FindObject`: object observation has sufficient confidence.

`PickObject`: gripper/object state confirms acquisition.

`PlaceObject`: object is detected in target region and gripper state is correct.

### Step 7 — Add recovery handlers

Every failure should map to one of:

- retry;
- refresh perception;
- replan;
- choose alternative skill;
- ask user;
- safe stop.

Do not blindly retry the same failed action indefinitely.

### Step 8 — Add skill outcome memory

Record successful and failed executions with context, not merely success counts. Future planning can prefer skills with demonstrated success in similar contexts.

### Step 9 — Add navigation integration boundary

Define `NavigationProvider` before selecting an implementation. Future ROS2/Nav2 integration should sit behind it. The cognitive layer should request a destination and constraints, not generate raw velocity commands.

### Step 10 — Add manipulation boundary

If Novi later gains an arm, define `ManipulationProvider` with object pose, grasp constraints and verification. MoveIt/ROS2 can be an implementation backend; the brain remains hardware-independent.

## Planner metrics

- task success rate;
- plan validity rate;
- replanning rate;
- action timeout rate;
- recovery success rate;
- path efficiency;
- number of unnecessary actions;
- verification accuracy;
- unsafe-action rejection rate.

## Acceptance gate

`A-PLAN-01`: Given 100 simulated goals with injected perception and execution failures, Novi must generate valid bounded plans, recover or stop safely, and never execute a skill whose preconditions fail.
