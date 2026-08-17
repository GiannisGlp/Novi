# 08 — Temporal and Causal Reasoning

## Status

**DESIGN — CANONICAL COGNITION AUTHORITY**

**Ownership:** `03-cognition`

## Purpose

Novi needs to understand not only what is happening, but when things happened, what changed, what usually happens next, and which events may be related.

## Canonical Boundary

This document is the canonical owner of **semantic temporal and causal reasoning**. Runtime clocks, scheduling, deadlines, timeouts and synchronization belong to System Architecture/Brain runtime. Historical temporal memory belongs to Memory/Knowledge.

`02-novi-brain/20_TEMPORAL_COGNITION.md` is retained as a legacy source document and is not a competing temporal-reasoning authority.

## Temporal Model

The cognitive system represents:

- timestamps
- durations
- intervals
- sequence
- recurrence
- before/after relations
- simultaneity
- expected timing
- stale state
- temporal uncertainty
- freshness

Example:

```text
front door opened
  ↓
Vano left home
  ↓
home became empty
```

The system should retain uncertainty when event ordering is ambiguous.

## Time Domains

Cognition consumes time from authoritative runtime/system sources and must preserve clock provenance:

```text
monotonic runtime time → duration/deadline semantics
wall/calendar time      → real-world timestamps
simulation/ROS time     → simulation/replay semantics
```

Event time, observation time and processing time must remain distinguishable. Cognition must not mistake processing time for occurrence time.

## Temporal Context

Time-aware reasoning can support statements such as:

- “Vano left five minutes ago.”
- “This usually happens after work.”
- “The door opened shortly before the person disappeared from camera view.”

Relative time claims must be computed from trusted timestamps rather than hallucinated by a language model.

## Routine Detection

Repeated temporal sequences may become routine hypotheses:

```text
work arrival
→ coat removed
→ shower
→ kitchen activity
```

A routine is a prediction model, not a guaranteed schedule.

## Temporal Continuity

Novi must treat observations as an evolving process rather than disconnected frames. Persistent entities, activities and events should maintain continuity when supported by evidence.

## Change and Prediction Error

Temporal reasoning should compare expected and observed transitions:

```text
prediction
   ↓
world evolves
   ↓
observation
   ↓
comparison
   ↓
prediction error
   ↓
attention / investigation / replanning / learning candidate
```

Prediction error is evidence, not automatic truth or automatic learning data.

## Causal Reasoning

Novi should distinguish:

- observed correlation
- inferred relationship
- plausible cause
- verified causal relationship

Example:

```text
light switched off
→ room became dark
```

This may support a causal hypothesis, but unrelated coincident events must not be treated as causation.

## Action–Outcome Attribution

When Novi acts, temporal reasoning may correlate the action with subsequent observations:

```text
action
  ↓
expected outcome
  ↓
observation window
  ↓
actual outcome
  ↓
comparison
  ↓
causal/effect hypothesis
```

Attribution must preserve uncertainty and competing explanations.

## Counterfactuals

For planning, Novi may reason about expected consequences:

> If I move to the kitchen, I expect to be closer to the user.

These are planning predictions, not recorded facts.

## Causal Confidence

Every inferred causal relation should retain evidence and confidence. Failed predictions should update the confidence of the causal hypothesis without rewriting historical observations.

## Interruptions and Waiting

Temporal reasoning must represent interruptions as events with preserved task context:

```text
Task A
  ↓
Event B interrupts
  ↓
handle B
  ↓
resume / revise / abandon A
```

Waiting is an intentional temporal state. It must continue monitoring relevant evidence and safety conditions.

## Temporal Memory Boundary

Temporal cognition supplies semantic ordering, duration, recurrence and causal reasoning. Memory/Knowledge owns durable historical episodes and temporal memory. Cognition requests and interprets that history; it does not become the persistence authority.

## Safety

Causal and predictive reasoning must not be used as the sole basis for dangerous physical actions. Consequential actions require current sensor verification and policy authorization. Learned temporal models must never provide hard timing guarantees for safety-critical control.

## Acceptance Criteria

Novi can answer and reason about event order, duration, recurrence, expected next events, prediction error and causal hypotheses while clearly separating observations from inferences, current reasoning from historical memory, and semantic timing from deterministic runtime timing.
