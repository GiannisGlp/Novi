# 02 — World Model

## Status

**DESIGN**

## Purpose

The World Model is Novi's structured representation of what it currently believes about the physical and social environment. It is the bridge between perception and reasoning.

## Design Principle

The World Model is **not a transcript** and not a database dump. It is a time-aware, uncertainty-aware representation of relevant entities, relations, states, events, and situations.

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
Wheely --near--> Vano
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
- validity windows.

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
- robot location.

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

## Contradictions

If camera says a person is in the kitchen while an older observation says the person is in the bedroom, the system evaluates timestamps and evidence quality. It does not simply overwrite one record.

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

## Persistence

The World Model should have a hot in-memory representation for low-latency decisions backed by durable persistence where needed. SQLite is an initial local candidate; the implementation must keep the repository interface independent of the storage engine.

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
5. resolve conflicting observations;
6. expose current state quickly;
7. replay historical state;
8. preserve provenance;
9. survive partial sensor failure;
10. evolve entity types without changing the core architecture.
