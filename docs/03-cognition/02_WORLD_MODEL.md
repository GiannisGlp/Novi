# 02 — World Model

## Status

**DESIGN — CANONICAL COGNITION AUTHORITY**

**Ownership:** `03-cognition`

## Purpose

The World Model is Novi's structured representation of what it currently believes about the physical and social environment. It is the bridge between perception and reasoning.

## Design Principle

The World Model is **not a transcript** and not a database dump. It is a time-aware, uncertainty-aware representation of relevant entities, relations, states, events, and situations.

## Canonical Boundary

This document is the canonical semantic World Model specification. `02-novi-brain/18_WORLD_MODEL.md` is retained as a legacy Brain source document and must not be treated as a competing authority.

The boundary is:

```text
Brain/runtime
  → acquires, synchronizes and exposes embodied evidence

Cognition/World Model
  → interprets and maintains the current semantic world state

Memory/Knowledge
  → retains historical experience and durable knowledge

Autonomy
  → uses the current world state to pursue goals and behavior
```

The World Model must never override authoritative live hardware/runtime telemetry with historical memory.

## Core Entity Types

Initial types include:

- Person
- Animal
- Robot
- Object
- Room
- Building
- Place
- Device
- Vehicle
- Activity
- Event
- Concept
- Organization
- Project

The model must support extensible entity types through the Knowledge/Data subsystem.

## Entity Identity

Each entity has:

- stable internal ID;
- type;
- labels/names;
- aliases;
- observations;
- confidence;
- provenance;
- temporal validity;
- spatial state where applicable.

Unknown entities can exist without being prematurely classified.

## Relations

Examples:

```text
Vano --located_in--> living_room
coffee_machine --located_in--> kitchen
Vano --uses--> coffee_machine
front_door --connects--> hallway
Novi --near--> Vano
```

Relations are timestamped and confidence-aware.

## State

State may include:

- location;
- orientation;
- activity;
- device state;
- occupancy;
- open/closed;
- on/off;
- temperature estimate;
- motion state;
- conversational state;
- interaction mode.

State must distinguish observed state from inferred state.

## Temporal Model

The World Model supports:

- current state;
- previous state;
- active intervals;
- point events;
- expected future state;
- validity windows;
- freshness;
- state-version lineage.

Example:

```text
front_door = OPEN
valid_from = 18:03:11
valid_until = unknown
source = contact_sensor
```

A later observation can close the interval.

## Spatial Model

The World Model should represent:

- rooms;
- floors;
- doors;
- zones;
- coordinates;
- map frames;
- semantic landmarks;
- object locations;
- person locations;
- robot location;
- metric geometry;
- topological connectivity;
- visibility and reachability state.

Metric localization and semantic location are separate but linked.

## Observation vs Belief

Example:

```text
Observation:
  camera detects a person-shaped object.

Inference:
  person likely Vano.

Belief:
  Vano is probably in the kitchen.

Verified fact:
  Vano confirmed he is in the kitchen.
```

These must not collapse into a single boolean fact.

## Epistemic State

Every important world-state element should preserve an explicit epistemic category such as:

```text
OBSERVED
INFERRED
FUSED
REMEMBERED
PREDICTED
SIMULATED
COUNTERFACTUAL
VERIFIED
UNKNOWN
```

Predictions and hypothetical states must never overwrite current observed state.

## Contradictions

If camera says a person is in the kitchen while an older observation says the person is in the bedroom, the system evaluates timestamps and evidence quality. It does not simply overwrite one record.

Contradictory evidence remains visible until resolved, expires, or is superseded by stronger evidence.

## World-State Snapshots

The system should support snapshots for debugging/replay:

```text
snapshot_id
created_at
world_version
entities
relations
active_situations
active_events
uncertainty_summary
provenance_summary
```

Snapshots may reference rather than duplicate large media.

## World Model Updates

Updates originate from:

- perception events;
- user statements;
- verified knowledge;
- IoT state;
- navigation state;
- internal action outcomes;
- learned routines.

Each update carries source and confidence.

## Active Perception Boundary

The World Model exposes uncertainty and information gaps to Cognition/Attention. It may therefore cause a request for additional evidence:

```text
uncertain world state
      ↓
attention identifies information gap
      ↓
perception/orientation request
      ↓
new evidence
      ↓
world-state update
```

The World Model does not directly command actuators.

## Prediction and Future State

The World Model may expose deterministic and learned predictions, including:

- human/object trajectories;
- likely environmental changes;
- expected action outcomes;
- alternative future branches.

Each prediction must contain its originating world-state version, model/source, assumptions, horizon, confidence and expiration. Predictions remain hypotheses.

## Imagination Boundary

Planning, simulation and counterfactual reasoning may construct hypothetical states:

```text
REAL CURRENT STATE
        ≠
PREDICTED FUTURE
        ≠
SIMULATED FUTURE
        ≠
COUNTERFACTUAL
```

A hypothetical state may influence planning but cannot become factual world state without new evidence.

## Action Outcome Grounding

The World Model closes the perception-action loop:

```text
action proposal
    ↓
execution
    ↓
observed outcome
    ↓
world-state update
    ↓
prediction error
    ↓
reasoning / memory / learning
```

The system must distinguish **commanded**, **controller-accepted**, **physically-executed**, and **world-observed** outcomes.

## Persistence

The World Model should have a hot in-memory representation for low-latency decisions backed by durable persistence where needed. SQLite is an initial local candidate; the implementation must keep the repository interface independent of the storage engine.

Historical retrieval belongs to Memory/Knowledge rather than the hot World Model.

## Performance

World-state queries required for immediate decisions should be bounded and predictable. Large historical retrieval belongs to memory/knowledge retrieval services.

## Security and Privacy

Location and household state can be sensitive. Access must follow identity and privacy policy. External tools should receive only the minimum world state required for their task.

## Acceptance Criteria

Demonstrate that Novi can:

1. represent known and unknown entities;
2. track people and objects over time;
3. maintain spatial relationships;
4. distinguish observation from inference;
5. preserve epistemic categories;
6. resolve conflicting observations;
7. expose current state quickly;
8. preserve world-state lineage;
9. keep predictions separate from facts;
10. request additional evidence when uncertainty is operationally important;
11. replay historical state through the appropriate memory interface;
12. preserve provenance;
13. survive partial sensor failure;
14. evolve entity types without changing the core architecture.
