# 14 — Cognitive Data Model

## Status

**DESIGN**

## Purpose

Define the canonical semantic objects exchanged between cognition, autonomy, memory, knowledge, perception, models, and tools.

## Core Objects

```text
Observation
Event
Entity
Person
Relationship
Place
Object
Activity
Situation
Fact
Hypothesis
Prediction
Goal
Intention
Plan
ActionRequest
Outcome
Memory
KnowledgeCandidate
ContextPackage
ModelDecision
```

## Entity Model

All persistent real-world entities use stable internal IDs independent of names or model-generated labels.

Entities support:

- type
- attributes
- relationships
- provenance
- confidence
- lifecycle
- timestamps
- privacy classification
- source references

## Fact vs Hypothesis

A fact represents information accepted by the knowledge policy. A hypothesis represents an unresolved interpretation.

```text
Observation → inference → hypothesis → verification → fact
```

Not every hypothesis should become a fact.

## Provenance

Every derived cognitive object must be traceable to source evidence or another derived object. Provenance graphs should support:

- source
- transformation type
- model/tool used
- timestamp
- confidence
- verification status

## Lifecycle

Objects should support lifecycle states such as:

`candidate → active → stale → superseded → archived`

Historical records should be retained where required for audit or learning.

## Contradictions

Contradictory information is represented as separate claims with explicit relationships. Destructive overwrite should be avoided for important knowledge.

## Serialization

The semantic model must have a stable machine-readable representation suitable for:

- internal Python services
- ROS 2 message adapters
- local databases
- files
- model context rendering
- replay/testing

## Schema Versioning

Every persisted schema has a version. Migrations must be deterministic and tested against representative historical datasets.

## Acceptance Criteria

Cognitive objects have stable IDs, typed semantics, provenance, confidence, privacy metadata, lifecycle state, and versioned serialization.
