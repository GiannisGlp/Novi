# 05 — Decision and Planning

## Status

**DESIGN** — implementation-oriented specification.

## Purpose

Decision and planning transform current world state, attention, goals, memory, personality context, and available capabilities into a bounded action proposal. The planner must distinguish reasoning from authorization.

## Decision Pipeline

```text
World State + Events + Goals + Memory
                 ↓
          Context Builder
                 ↓
        Deterministic Prechecks
                 ↓
          Reasoning Model
                 ↓
        Candidate Intentions
                 ↓
       Plan Construction
                 ↓
       Plan Validation
                 ↓
       Policy / Safety
                 ↓
        Action Requests
```

## Deterministic Prechecks

Before invoking a language model, the system should resolve simple cases through deterministic logic where possible:

- direct tool lookup;
- known device state;
- current time;
- battery/diagnostic thresholds;
- active navigation status;
- explicit policy restrictions;
- duplicate request detection.

This reduces latency and prevents unnecessary model calls.

## Reasoning Model Contract

Nemotron is the primary general reasoning candidate. The autonomy engine supplies a structured context package rather than unrestricted database access.

The model may:

- interpret semantic context;
- propose goals;
- propose plans;
- select among exposed tools;
- request additional information;
- formulate responses;
- identify uncertainty;
- propose learning candidates.

The model may not:

- authorize itself;
- bypass safety;
- execute arbitrary code;
- issue unrestricted SQL/filesystem operations;
- directly command motors;
- alter immutable system policy.

## Context Package

A model context should include only what is relevant:

```text
current situation
recent events
relevant entities
relevant memories
verified knowledge
active goals
available capabilities
constraints
relationship context
personality state
resource state
```

Every retrieved fact should retain provenance metadata outside the generated text.

## Candidate Plans

The model may produce one or more candidate plans. Each plan has:

- goal reference;
- assumptions;
- steps;
- dependencies;
- preconditions;
- expected outcomes;
- risk class;
- resource estimate;
- timeout;
- cancellation conditions;
- fallback/recovery strategy.

## Plan Validation

Plans are validated before execution:

1. schema validation;
2. capability existence;
3. argument validation;
4. authorization;
5. resource availability;
6. spatial constraints;
7. safety policy;
8. temporal validity;
9. conflict with active goals;
10. idempotency requirements.

A valid plan is not automatically an authorized plan.

## Tool Selection

Tools are exposed through typed capability descriptions. The model selects capabilities by semantic contract, not by discovering arbitrary executable commands.

Example:

```text
capability: lighting.set_state
arguments:
  room: living_room
  state: on
risk: low
confirmation: none
```

## Information-Seeking Plans

If context is insufficient, the planner should prefer the least costly information source:

```text
current state
→ memory
→ knowledge base
→ sensor observation
→ passive observation
→ local tool
→ user question
→ external service (if authorized)
```

## Replanning

A plan must be invalidated or reconsidered when:

- a critical precondition changes;
- the world model changes materially;
- a tool fails;
- a safety condition changes;
- a person enters a relevant space;
- localization confidence drops;
- resources become constrained;
- the user changes the goal.

## Goal Conflicts

The planner must not silently choose between conflicting high-priority goals. It should apply deterministic priority/policy rules or request clarification.

## Human Confirmation

Confirmation is required by policy for configured risk classes. Model confidence cannot remove a confirmation requirement.

## Planning Depth

The system should use adaptive planning depth:

- immediate deterministic action for trivial tasks;
- short plan for simple multi-step tasks;
- deeper reasoning for ambiguous or long-horizon goals.

The planner must avoid unnecessary long plans when a shorter verified strategy exists.

## Failure and Recovery

Each action has an expected outcome. If the outcome differs:

```text
failure
 ↓
classify
 ├── transient → retry
 ├── changed world → replan
 ├── unavailable capability → fallback
 ├── authorization → stop/ask
 └── safety → stop safely
```

## Acceptance Criteria

Demonstrate:

- deterministic handling of simple tasks;
- structured Nemotron planning;
- validated tool calls;
- multi-step planning;
- replanning after environmental changes;
- explicit uncertainty;
- policy enforcement independent of model output;
- safe cancellation;
- reproducible planning tests.
