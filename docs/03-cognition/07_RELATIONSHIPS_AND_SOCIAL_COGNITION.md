# 07 — Relationships and Social Cognition

## Status

**DESIGN**

## Purpose

Define how Novi understands relationships, social context, familiarity, interaction history, and socially appropriate behavior.

## Relationship Model

A relationship is an evidence-backed evolving entity, not a hard-coded label.

Examples:

- unknown
- visitor
- acquaintance
- friend
- colleague
- household member
- family
- trusted user

The model can contain confidence, evidence, history, reciprocal context, and last-confirmed time.

## Social Context

Novi should reason about:

- who is present
- who is speaking
- who is being addressed
- what activity is occurring
- whether a conversation is private or shared
- whether Novi is part of the interaction
- previous interactions
- current relationship state
- appropriate tone

## Relationship Evolution

Repeated interactions may strengthen familiarity. Contradictory evidence can weaken or revise a relationship hypothesis. Important relationship changes should be confirmed where practical rather than inferred from one interaction.

## Social Boundaries

Relationship familiarity does not automatically grant access to private information or capabilities. Authorization is a separate security concept.

## Group Context

Novi must support multiple people simultaneously and avoid assuming that every utterance or action is directed toward Novi.

## Social Cognition and Personality

Social cognition determines context and appropriateness. Personality determines style after policy determines that interaction is permitted.

```text
social understanding
        ↓
interaction policy
        ↓
personality style
        ↓
response
```

## Acceptance Criteria

Novi can adapt interaction to relationship and group context while preserving privacy, uncertainty, and authorization boundaries.
