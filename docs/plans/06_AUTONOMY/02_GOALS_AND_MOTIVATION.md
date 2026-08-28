# 02 — Goals, Motivation and Autonomy Policy

## Objective

Give Novi a principled mechanism for deciding **what it should do next**, rather than equating autonomy with continuously calling an LLM.

## Goal hierarchy

Use four levels:

1. **Mission goals** — persistent objectives defined by the user/project.
2. **Active goals** — current objectives selected from mission goals and environmental needs.
3. **Subgoals** — concrete outcomes required by the active goal.
4. **Actions** — atomic executable operations.

Example:

```text
Mission: keep the workspace organized
  ↓
Active goal: return mug to kitchen
  ↓
Subgoals:
  1. locate mug
  2. determine safe route
  3. acquire mug
  4. navigate to kitchen
  5. place mug
  6. verify placement
```

## Step-by-step

### Step 1 — Define goal schema

A goal must contain:

- stable ID;
- natural-language description;
- structured objective when possible;
- source (`human`, `routine`, `safety`, `prediction`, `exploration`, `system`);
- priority;
- urgency;
- deadline;
- required capabilities;
- authority requirement;
- success conditions;
- failure conditions;
- cancellation conditions;
- resource budget;
- privacy classification.

### Step 2 — Add goal lifecycle

`PROPOSED → ACCEPTED → ACTIVE → BLOCKED → SUSPENDED → COMPLETED/FAILED/CANCELLED/EXPIRED`.

A goal cannot become `ACTIVE` until authority and preconditions pass.

### Step 3 — Build goal arbitration

Rank candidate goals using a deterministic score:

```text
priority
+ urgency
+ safety relevance
+ predicted value
+ user preference
+ information value
- resource cost
- risk
- interruption cost
```

The score is a decision aid, not permission to bypass safety.

### Step 4 — Add conflict resolution

Examples:

- user asks Novi to move while a safety stop is active → safety wins;
- routine conflicts with explicit user request → explicit user request wins;
- exploration conflicts with active task → active task wins unless exploration is safety-critical;
- stale goal competes with fresh goal → freshness/urgency policy decides.

Every arbitration decision must record why one goal won.

### Step 5 — Add goal persistence

Persist active and suspended goals across restart, but revalidate all physical preconditions after restart. Never resume a physical action merely because it was active before shutdown.

### Step 6 — Add autonomy modes

Expose modes through policy, not prompts:

- `manual`
- `assist`
- `bounded`
- `supervised`
- `paused`
- `safe_stop`

Mode changes require an audit event.

### Step 7 — Add resource-aware motivation

Goals should be aware of:

- battery/energy;
- compute budget;
- thermal state;
- network availability;
- actuator wear;
- time budget;
- sensor availability.

The goal manager should be able to postpone low-value tasks when resources are constrained.

### Step 8 — Add autonomous background goals carefully

Potential sources:

- stale world-state refresh;
- unfinished routine;
- predicted user need;
- curiosity/information gain;
- maintenance;
- map improvement.

Background goals must have lower authority than explicit safety and user goals.

## Goal anti-patterns

Do not:

- create infinite self-generated goals;
- reward activity instead of useful outcomes;
- allow goals to modify their own authority;
- let an LLM silently redefine success criteria;
- continue a goal when the world has materially changed.

## Tests

Create deterministic arbitration fixtures with 2–10 competing goals. Test priority inversion, deadlines, safety overrides, user cancellation, resource depletion, stale goals and restart.

## Acceptance gate

`A-GOAL-01`: Given 100 generated mixed-priority goals, Novi must choose the same winner for the same world/policy state and produce an auditable explanation. Safety goals must dominate all lower-authority goals.
