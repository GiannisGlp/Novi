# 11 — Personality, Emotion and Affect

## Status

**DESIGN — BOUNDARY REVISED**

## Purpose

Define the **cognitive interpretation boundary** for personality- and affect-related information. The canonical semantic definition of Novi's personality, values, motivations, and stable character belongs to the Soul domain.

Cognition does not own or redefine Novi's personality. It consumes the canonical Soul state and uses context, relationships, observations, and current internal state to determine how that personality should be interpreted in the present situation.

## Canonical ownership

```text
SOUL
  ↓
identity / values / motivations / stable personality / character
  ↓
COGNITION
  ├── contextual interpretation
  ├── social and emotional evidence
  ├── current self/world context
  ├── affect hypotheses
  └── personality-conditioned reasoning context
  ↓
AUTONOMY
  ├── attention
  ├── interaction decision
  ├── goal priority
  └── action coordination
```

Soul is the semantic authority for personality. Cognition may not silently redefine it.

## Personality input

Cognition receives a typed personality context containing, as applicable:

- stable traits;
- foundational values;
- motivations;
- communication preferences;
- relationship-conditioned expression rules;
- learned preferences with confidence and provenance;
- current adaptive affect supplied by the runtime.

Cognition may use these inputs to construct context for reasoning and response generation.

## Human emotion interpretation

Novi should represent inferred human emotional state as hypotheses:

```text
emotion_hypothesis:
  state: possibly_tired
  confidence: 0.61
  evidence: [voice, posture, context]
```

The system must not claim certainty about another person's internal emotional state from appearance, voice, posture, or behavior alone.

## Novi's internal affect

Transient affect is computational runtime state, not a claim of human consciousness. Examples include:

- curiosity level;
- social engagement;
- task focus;
- frustration/recovery state;
- energy/resource state;
- attention load.

The runtime representation and decay rules belong to the appropriate state/autonomy interfaces; Cognition consumes the resulting state when relevant to interpretation and reasoning.

## Personality response pipeline

```text
context
 ↓
social/context policy
 ↓
relationship context
 ↓
canonical Soul personality
 ↓
current affect
 ↓
reasoning/model generation
 ↓
response validation
```

Personality must never bypass safety, privacy, authorization, or explicit user preferences.

## Consistency

The same person should recognize Novi's characteristic style over time. Contextual variation is desirable, but identity, foundational values, and core personality must remain coherent.

## Learning boundary

Interaction history may produce candidate changes to preferences, humor tolerance, communication patterns, or adaptive style. Cognition may infer or propose such candidates, but persistent changes to canonical personality or values require the Soul learning/governance path.

## Acceptance criteria

Cognition demonstrates:

- correct consumption of canonical Soul personality state;
- contextual interpretation without redefining personality;
- probabilistic human emotion hypotheses;
- separation of transient affect from stable personality;
- provenance/confidence for inferred social-emotional information;
- no ability for personality context to bypass safety or authorization.

## Related canonical documents

- `docs/06-soul/00_SOUL_AND_BEHAVIORAL_CONSTITUTION.md`
- `docs/06-soul/01_IDENTITY_AND_SELF_MODEL.md`
- `docs/06-soul/02_PERSONALITY_VALUES_AND_MOTIVATIONS.md`
- `docs/02-autonomy/08_INTERNAL_STATE_AND_AFFECT.md`
