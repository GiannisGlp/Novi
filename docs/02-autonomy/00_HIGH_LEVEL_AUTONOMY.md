# 00 — High-Level Autonomy

## Status

**DESIGN** — authoritative high-level specification for the autonomy domain.

## Purpose

Novi's autonomy system is responsible for maintaining a continuous cycle of environmental awareness, behavioral attention, goal management, decision making, action requests, outcome observation, and controlled learning.

The autonomy subsystem answers five questions continuously:

1. **What is happening?** — Cognition supplies the semantic interpretation.
2. **What matters right now?** — Cognition supplies salience; Autonomy makes the behavioral attention decision.
3. **Should I do anything?** — Autonomy decides whether to pursue behavior.
4. **If so, what is the safest useful action?** — Cognition can propose strategies; Autonomy manages the task; policy/safety authorizes.
5. **What did I learn from the result?** — Autonomy identifies learning opportunities; Memory/Knowledge owns persistence and consolidation.

It must be possible for Novi to observe without interacting. Silence is a valid autonomous decision.

## Scope

Autonomy owns:

- continuous behavioral-loop orchestration;
- behavioral attention decisions;
- goal creation, prioritization, suspension, and completion;
- curiosity and information-seeking decisions;
- high-level behavioral planning;
- task sequencing and pursuit;
- action-request lifecycle;
- outcome assessment for task progress;
- autonomous behavioral state transitions;
- social interaction decisions;
- resource-aware behavioral adaptation;
- learning triggers;
- autonomy telemetry and behavioral audit records.

Autonomy does not own:

- raw sensor drivers;
- motor control;
- safety-critical actuator control;
- authoritative knowledge storage;
- raw media storage;
- model implementation internals;
- runtime scheduling implementation;
- ROS 2 transport internals;
- authentication and authorization primitives;
- the canonical semantic World Model or Situation Model.

## Core Runtime Contract

```text
observe
  ↓
consume cognition's current semantic state
  ↓
compute behavioral attention
  ↓
maintain goals
  ↓
select response strategy
  ↓
request reasoning / plan when needed
  ↓
commit or update behavioral task
  ↓
policy + safety validation
  ↓
execute through capability
  ↓
observe outcome
  ↓
update goal/task state
  ↓
create learning candidate when warranted
  ↓
repeat
```

The loop is asynchronous. Multiple observations may arrive while a plan is executing. New high-priority events can interrupt lower-priority work, subject to safety and cancellation rules.

## Autonomy Invariants

### A1 — No unrestricted action

The autonomy engine never receives direct unrestricted access to motors, filesystem paths, SQL execution, network sockets, or protected configuration.

### A2 — Safety outranks autonomy

If an autonomous intention conflicts with a safety rule, the safety rule wins. The autonomy engine must receive a structured denial or constraint and continue safely.

### A3 — Uncertainty is preserved

Autonomy must never convert an inference into a fact. Observations, inferred state, hypotheses, memories, and verified knowledge have distinct types and provenance owned by their canonical domains.

### A4 — Attention is selective

Perception events do not automatically cause speech, movement, screen changes, or tool execution. Cognition supplies semantic relevance; Autonomy makes the behavioral response decision.

### A5 — Human confirmation is a capability policy

Certain actions require explicit confirmation regardless of model confidence. Confirmation requirements are determined by policy, not by the LLM or autonomy engine.

### A6 — Learning cannot rewrite the protected core

Novi may update managed data and approved adaptive state. It cannot modify the immutable safety boundary, trust roots, or protected runtime without an externally authorized software-update process.

### A7 — Every consequential action is traceable

The system records what triggered an action, which state/evidence references were used, which capability was requested, what policy decision occurred, and what outcome was observed. The audit record must not contain hidden chain-of-thought or sensitive raw data unnecessarily.

### A8 — Deterministic behavior where possible

Safety, resource limits, state transitions, scheduling guarantees, and capability authorization should be deterministic and testable. Probabilistic models are used where perception, language, or semantic reasoning genuinely require them.

## Autonomy Levels

Novi should support progressively stronger autonomy modes:

### Level 0 — Passive observation

Perceive and record. No autonomous external action except mandatory safety behavior.

### Level 1 — Reactive

Respond to explicit user requests and high-confidence safety/environmental events.

### Level 2 — Context-aware

Use memory, relationships, environment state, and attention to decide when and how to respond.

### Level 3 — Goal-directed

Pursue explicitly authorized goals across multiple steps and recover from normal failures.

### Level 4 — Learning autonomy

Generate curiosity goals, learn from experience, form hypotheses, validate uncertain knowledge, and improve routines within policy.

### Level 5 — Long-horizon autonomy

Coordinate multiple goals and long-running activities with resource management and human oversight, while remaining bounded by the immutable safety system.

The first physical Novi release should target Levels 1–3. Level 4 should be introduced through controlled experiments. Level 5 requires explicit safety and reliability validation.

## Priority Model

A baseline priority ordering is:

```text
critical safety
    > physical safety
    > explicit emergency/user interruption
    > active user request
    > critical system maintenance
    > committed task
    > social opportunity
    > curiosity / exploration
    > background optimization
```

This ordering is not a single numeric score. Hard constraints can override scoring.

## Silence as a Decision

For every socially relevant event, the autonomy engine may produce:

- `NO_ACTION`
- `OBSERVE_ONLY`
- `INTERNAL_UPDATE`
- `SCREEN_ONLY`
- `NONVERBAL_SIGNAL`
- `SPEAK`
- `ASK_QUESTION`
- `TOOL_ACTION`
- `MULTI_STEP_PLAN`

The system must optimize for appropriate behavior rather than maximum interaction frequency.

## Relationship to Reasoning Models

A reasoning model is an implementation behind the Cognition model-selection contract. It may interpret context, generate candidate plans, select among exposed tools, explain options, and produce conversational responses. It is not the source of truth for world state, memory, authorization, or safety.

Autonomy supplies behavioral requirements and bounded context through contracts; Cognition owns semantic reasoning and model selection; Brain owns model execution/runtime.

## Resource Awareness

Autonomy must account for:

- battery level;
- compute utilization;
- thermal state;
- memory pressure;
- network availability;
- sensor availability;
- charging state;
- current task commitments;
- physical location.

When resources become constrained, non-critical goals can be paused or discarded. Safety and explicit high-priority tasks remain protected.

## Mac / Simulation / Jetson Parity

The same autonomy contracts must run in three environments:

```text
Mac runtime
  → virtual/synthetic sensors
  → real Mac camera/microphone where available

Simulation runtime
  → Isaac Sim / ROS 2 simulated sensors

Jetson runtime
  → physical sensors / actuators
  → selected Jetson acceleration
```

Only adapters and performance characteristics should differ; autonomy semantics must remain consistent.

## Acceptance Criteria

The high-level autonomy design is acceptable when the implementation can demonstrate that Novi:

1. runs continuously without requiring user prompts;
2. notices meaningful environmental events;
3. distinguishes events requiring action from events requiring observation only;
4. maintains goals and priorities;
5. manages multi-step behavioral tasks through capabilities;
6. respects safety and authorization boundaries;
7. observes action outcomes and recovers from normal failures;
8. creates controlled learning candidates without owning persistent memory;
9. maintains personality and relationship context without bypassing safety;
10. produces structured, auditable autonomy events;
11. behaves consistently across Mac, simulation, and Jetson runtimes;
12. remains operational when individual AI models or sensors are unavailable, using graceful degradation.
