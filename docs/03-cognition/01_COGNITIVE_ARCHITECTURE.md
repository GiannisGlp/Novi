# 01 — Cognitive Architecture

## Status

**DESIGN — CANONICAL COGNITION AUTHORITY**

**Ownership:** `03-cognition`

## Purpose

Define the component boundaries that turn observations and stored experience into a coherent cognitive state consumed by autonomy.

## Components

```text
                    COGNITION
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
  World Model      Situation Model   Identity
       │                │                │
       ├────────┬───────┴────────┬───────┤
       ▼        ▼                ▼       ▼
   Memory   Knowledge       Prediction  Social
       │        │                │       │
       └────────┴───────┬────────┴───────┘
                       ▼
                Context Builder
                       │
                       ▼
                 Reasoning Engine
                       │
                 structured output
                       ▼
                    Autonomy
```

## World Model

Authoritative semantic representation of current physical/social state:

- entities;
- locations;
- devices;
- objects;
- activities;
- spatial relations;
- occupancy;
- state transitions;
- current uncertainty;
- epistemic status;
- predictions and their provenance.

The detailed canonical specification is `03-cognition/02_WORLD_MODEL.md`.

## Situation Model

Interprets world state into meaningful current contexts such as:

- person is arriving home;
- conversation is occurring;
- user appears to be preparing food;
- navigation is blocked;
- an unfamiliar object is present.

Situations can overlap and have confidence, evidence, freshness and expiration. A situation is an interpretation of current context, not a replacement for the underlying World Model.

The Situation Model should expose at least:

```text
situation_id
world_state_version
active_entities
active_events
active_activities
relationships
Novi_state
current_place
active_goals/tasks
attention_targets
hazards/opportunities
social/interaction context
recent_changes
predictions
uncertainties
provenance
freshness
```

`02-novi-brain/21_SITUATION_MODEL.md` is legacy source material; it is not a competing canonical situation authority.

## Identity System

Resolves observations to known or unknown entities. Identity is probabilistic and can remain unresolved. Face recognition alone must not be treated as absolute identity.

## Self Model Boundary

Cognition owns Novi's **semantic self-model**:

- what Novi believes it can do;
- capability interpretation;
- self/other distinction;
- self-related reasoning;
- self-related prediction;
- semantic interpretation of current embodied state;
- capability confidence and limitations.

Brain/runtime and hardware remain authoritative for physical telemetry, configuration and actuator state. Memory owns autobiographical history. Autonomy owns current goals/tasks.

`02-novi-brain/22_SELF_MODEL.md` is legacy cross-domain source material, not a competing single-owner self-model.

The critical invariant is:

```text
language capability ≠ physical capability
physical capability ≠ authorization
authorization ≠ safe-now capability
commanded action ≠ executed action
```

## Memory Interface

Cognition requests relevant episodic, semantic, spatial, procedural, and relationship memories. Memory owns persistence; cognition owns interpretation of retrieved content.

## Knowledge Interface

Knowledge supplies structured facts and relationships with provenance and verification status. Cognition can propose new knowledge but persistence is mediated by the knowledge layer.

## Prediction Engine

Maintains expected states/events and compares future observations against expectations. Prediction errors can trigger attention, investigation, or learning.

## Social Cognition

Combines identity, relationship, conversation context, tone/body-expression evidence, history, and personality state to produce social context.

## Context Builder

Creates a bounded context package for a specific cognitive task. It selects:

- current situation;
- relevant entities;
- active goals;
- recent events;
- relevant memories;
- verified knowledge;
- uncertainty/contradictions;
- available capabilities;
- interaction policy;
- system constraints.

It must not indiscriminately include all available data.

## Reasoning Engine

The reasoning engine may use:

1. deterministic algorithms;
2. retrieval/ranking models;
3. specialized ML models;
4. the primary LLM;
5. multiple model calls where justified.

The architecture must not assume that every problem belongs to the LLM.

## Output Validation

Model output is parsed into typed structures. Invalid, incomplete, unsafe, or contradictory outputs are rejected or repaired using deterministic validation.

## Data Ownership

| Component | Owns | Does not own |
|---|---|---|
| World Model | current semantic interpreted state | raw sensor data, durable memory |
| Situation Model | active semantic situations | motor commands, goal authority |
| Identity | entity resolution | authorization |
| Memory | experience persistence | current action policy |
| Knowledge | verified facts/schema | hidden model state |
| Prediction | expectations | truth authority |
| Context Builder | context composition | source data ownership |
| Reasoning Engine | candidate interpretations/plans | safety authorization |
| Autonomy | action decisions | low-level motor control |
| Safety | action constraints | personality |

## Concurrency

Cognitive components must support asynchronous updates. A reasoning operation can finish after the world state has changed. Before consequential action, the system must verify that the plan remains valid against current state.

## Transactional Updates

Changes that update several cognitive representations should use transaction or event-sourcing semantics where consistency matters. Partial updates must be recoverable.

## Failure Isolation

A failing component should not corrupt the complete cognitive state. Each service exposes health and degraded modes.

## Testability

Every component must have deterministic unit-test interfaces. Integration tests use recorded/synthetic observations. Scenario tests exercise the complete cognitive pipeline.
