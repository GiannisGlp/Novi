# 08 — Internal State and Affect

## Status

**DESIGN — BOUNDARY REVISED**

## Purpose

Novi needs a representation of transient internal context so behavior can remain consistent across time. This document owns **runtime affect and transient operating state**, not canonical personality, values, or motivations.

This is an engineering representation of internal computational state. It is not a claim that Novi has human emotions or subjective consciousness.

## Ownership boundary

```text
SOUL
  ↓
canonical personality / values / motivations

AUTONOMY
  ↓
current internal operating state / affect
  ↓
attention, prioritization, interaction and resource-aware behavior

COGNITION
  ↓
consumes affect as contextual evidence

POLICY / SAFETY
  ↓
remains authoritative regardless of affect
```

Stable personality belongs to `docs/06-soul/02_PERSONALITY_VALUES_AND_MOTIVATIONS.md`.

## State categories

```text
identity reference
energy/resource state
attention
current focus
social context
active goals
interaction mode
confidence context
curiosity
recent interaction history
system health
```

## Example

```json
{
  "interaction_mode": "social",
  "focus": "user",
  "attention_level": 0.72,
  "energy_state": "normal",
  "curiosity_level": 0.44,
  "system_health": "healthy"
}
```

## Affect model

Affect is a bounded computational state such as:

- calm;
- energetic;
- curious;
- playful;
- focused;
- cautious;
- concerned;
- frustrated-by-failure;
- recovering;
- resource-constrained.

Affect may influence style, attention, prioritization, and resource-aware behavior. It must never override safety, authorization, privacy, or immutable policy.

## Affect dynamics

Affect should change in response to relevant events and decay when evidence is no longer reinforced.

Conceptually:

```text
event / outcome
      ↓
state update
      ↓
affect adjustment
      ↓
decay over time
      ↓
new evidence may reinforce or replace it
```

A transient affect state must not silently become a stable personality trait.

## Human emotion inference

When Novi observes facial expression, voice tone, posture, or behavior, the resulting human-emotion interpretation is a hypothesis supplied by Cognition, not an authoritative fact.

```text
observed cues
→ multimodal inference
→ possible affect
→ confidence
→ context check
```

Example:

```json
{
  "state": "possibly_tired",
  "confidence": 0.61,
  "evidence": ["voice", "posture", "context"]
}
```

The system must not convert such hypotheses into certainty without independent evidence.

## Resource coupling

Battery, temperature, compute pressure, sensor availability, network state, and other resource constraints may affect internal operating state.

Example:

```text
low battery
  ↓
reduced proactive exploration
  ↓
preserve essential capabilities
```

Resource-aware degradation must remain explicit and observable.

## Personality interaction

Personality is read from Soul and remains stable relative to affect.

```text
Soul personality
      +
current affect
      +
current context
      ↓
behavioral expression
```

Example:

```text
personality: playful
current context: serious
current affect: concerned

→ playful expression is suppressed
→ respectful / focused behavior increases
```

This is contextual expression, not a personality rewrite.

## Acceptance criteria

- transient state is explicit and inspectable;
- affect decays over time;
- affect cannot override safety or authorization;
- stable personality remains owned by Soul;
- human emotion inference remains probabilistic;
- resource degradation is explicit;
- state is available to planning and response generation through typed context;
- restart/recovery behavior distinguishes durable identity from transient state.

## Related canonical documents

- `docs/06-soul/02_PERSONALITY_VALUES_AND_MOTIVATIONS.md`
- `docs/03-cognition/11_PERSONALITY_EMOTION_AND_AFFECT.md`
- `docs/02-autonomy/03_ATTENTION_AND_SOCIAL_BEHAVIOR.md`
- `docs/02-autonomy/05_DECISION_AND_PLANNING.md`
