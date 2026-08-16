# 08 — Temporal and Causal Reasoning

## Status

**DESIGN**

## Purpose

Novi needs to understand not only what is happening, but when things happened, what changed, what usually happens next, and which events may be related.

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

Example:

```text
front door opened
  ↓
Vano left home
  ↓
home became empty
```

The system should retain uncertainty when event ordering is ambiguous.

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

## Counterfactuals

For planning, Novi may reason about expected consequences:

> If I move to the kitchen, I expect to be closer to the user.

These are planning predictions, not recorded facts.

## Causal Confidence

Every inferred causal relation should retain evidence and confidence. Failed predictions should update the confidence of the causal hypothesis.

## Safety

Causal reasoning must not be used as the sole basis for dangerous physical actions. Consequential actions require current sensor verification and policy authorization.

## Acceptance Criteria

Novi can answer and reason about event order, duration, recurrence, expected next events, and causal hypotheses while clearly separating observations from inferences.
