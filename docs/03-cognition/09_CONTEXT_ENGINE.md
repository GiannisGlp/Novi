# 09 — Context Engine

## Status

**DESIGN**

## Purpose

The Context Engine constructs the smallest sufficient context for cognition and reasoning from current state, relevant memory, knowledge, social context, active goals, and recent events.

## Context Sources

```text
current world state
recent events
person identity/relationship
conversation state
active goals
relevant memories
verified knowledge
uncertain hypotheses
tool state
resource state
personality state
        ↓
Context Engine
        ↓
bounded context package
```

## Context Selection

Context selection should optimize for relevance, freshness, confidence, and task requirements rather than maximum retrieval volume.

The engine should avoid injecting unrelated personal data, stale memories, duplicate facts, or low-confidence hypotheses unless they are relevant to resolving uncertainty.

## Context Layers

1. **Immediate:** current utterance/event and current sensor state.
2. **Situational:** active people, place, activity, task, and recent events.
3. **Relevant memory:** recent and semantically related experiences.
4. **Knowledge:** verified facts and applicable learned concepts.
5. **Relationship:** person-specific context and interaction style.
6. **Long-horizon:** durable goals, routines, preferences, and relevant history.

## Context Provenance

Every retrieved item should retain its source and confidence. The model-facing representation may summarize information, but the underlying provenance remains available to the system.

## Context Budget

The engine must support model-specific token/context budgets. It should rank and compress information rather than blindly exceeding the model context window.

## Contradiction Handling

Conflicting memories or knowledge should be represented explicitly. The context package can state:

```text
known: A
conflicting report: B
confidence(A): 0.72
confidence(B): 0.41
verification: pending
```

The model must not be forced to treat a contradiction as a single fact.

## Privacy Filtering

Before context is passed to a model, policy filters should remove data the model does not need. Sensitive information should be minimized and scoped to the current task.

## Model Independence

The Context Engine must not depend on Nemotron-specific prompt formatting. It produces a structured semantic package that can be rendered for different reasoning models.

## Acceptance Criteria

The system can construct task-relevant, provenance-preserving, privacy-filtered context packages for multiple model types and reliably exclude irrelevant or stale information.
