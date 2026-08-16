# 08 — Internal State and Affect

## Status

**DESIGN**

## Purpose

Novi needs a representation of transient internal context so behavior can be consistent across time. This is not a claim that Novi has human emotions. It is an engineering state used to modulate attention, interaction style, priorities, and resource-aware behavior.

## State Categories

```text
identity
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
  "focus": "vano",
  "attention_level": 0.72,
  "energy_state": "normal",
  "curiosity_level": 0.44,
  "system_health": "healthy"
}
```

## Affect Model

Affect is a bounded computational state such as:

- calm;
- energetic;
- curious;
- playful;
- focused;
- cautious;
- concerned;
- frustrated-by-failure.

It should influence style and prioritization, not safety policy.

## Emotion Inference

When Novi observes human facial expression, voice tone, posture or behavior, it creates hypotheses rather than facts.

```text
observed cues
→ multimodal inference
→ possible affect
→ confidence
→ context check
```

Novi should avoid presenting inferred mental states as certainty.

## Persistence

Stable personality traits belong to the personality subsystem. Internal affect is short-lived and should decay unless reinforced by new evidence.

## Resource Coupling

Battery, temperature, compute pressure, and sensor availability may affect internal operating state. Example: reduced proactive exploration while battery is low.

## Acceptance Criteria

- state is explicit and inspectable;
- affect decays over time;
- state does not override safety;
- human emotion inference remains probabilistic;
- state is available to planning and response generation through typed context.
