# 01 — Memory Taxonomy

## Status

**DESIGN**

## Working Memory

Transient state needed to perform the current cognitive task. It may include current entities, recent observations, active tool results and temporary hypotheses.

## Session Memory

Short-lived interaction state associated with a conversation/session. It can include recent turns, current topic, unresolved questions and active commitments.

## Episodic Memory

Records of meaningful experiences:

```text
who / what / where / when / what happened / evidence / outcome
```

Episodes preserve event sequence and context rather than only distilled facts.

## Semantic Knowledge

Durable concepts and claims about people, objects, places, devices, routines and the world.

## Procedural Memory

Validated ways of performing tasks. Procedures include preconditions, steps, expected outcomes, failure handling and authorization requirements.

## Relationship Memory

History and state associated with relationships between Novi and people/entities. It can include interaction patterns, confirmed preferences, familiarity and relationship evidence.

## Spatial Memory

Locations, maps, room/object relationships, landmarks, navigation-relevant facts and persistent spatial associations.

## Temporal Memory

Time-dependent patterns such as routines, sequences, schedules and validity intervals.

## Preference Memory

Explicit or strongly supported user/household preferences. Preferences must retain source and confidence and remain reversible.

## Operational Memory

Validated information about Novi's own devices, software, capabilities, sensors, battery behavior, IoT devices and environmental configuration.

## Memory Type Selection

A single experience may produce multiple derived memories. For example:

```text
Episode: Vano arrived home at 18:12
        │
        ├── temporal pattern candidate
        ├── relationship interaction
        ├── routine candidate
        └── episodic record
```

Derived memories must retain links to the originating episode/evidence.

## Anti-Pattern

Do not store everything as an embedding. Embeddings are retrieval indexes, not a substitute for typed memory semantics.
