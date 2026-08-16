# 06 — Identity and Person Model

## Status

**DESIGN**

## Purpose

Define how Novi represents people, identities, identity evidence, familiarity, and person-specific context without treating recognition as certainty.

## Identity Layers

Identity is composed of separate layers:

```text
sensor observation
  → person detection
  → identity candidates
  → identity evidence
  → identity resolution
  → person entity
  → relationship/context
```

Face recognition, voice recognition, gait/body cues, name references, device presence, and behavioral patterns are evidence sources. No single weak signal should be treated as authoritative for consequential actions.

## Person Entity

A person entity may contain:

- stable internal ID
- known names/aliases
- identity evidence references
- face embeddings references
- speaker embeddings references
- relationship classifications
- familiarity score
- interaction history references
- preferences
- privacy/consent state
- verification state
- provenance
- timestamps

Biometric vectors should be stored separately from ordinary semantic profile data and protected with stricter access controls.

## Identity Confidence

Novi must distinguish:

- detected person
- probable identity
- verified identity
- unknown person
- ambiguous identity

A recognition model's confidence is not equivalent to authorization.

## Identity Fusion

Multiple signals can strengthen identity:

```text
face
+ voice
+ contextual location
+ conversation reference
+ historical presence
      ↓
identity hypothesis
```

Contradictory evidence must reduce confidence or create an ambiguity state rather than being silently discarded.

## Unknown People

Unknown people may receive temporary identities for an interaction/session. Novi can remember that the same anonymous individual appeared repeatedly without assigning a real name until sufficient evidence or user confirmation exists.

## Privacy

Person data is household/private by default. Novi must minimize retention of raw biometric data and support deletion, retention policies, and user-directed correction.

## Acceptance Criteria

Novi can distinguish people reliably enough for its intended interaction scenarios, preserves uncertainty, handles ambiguous identities, and never uses probabilistic recognition as an unrestricted authorization mechanism.
