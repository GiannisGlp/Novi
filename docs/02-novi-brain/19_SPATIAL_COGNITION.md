# Novi Brain — Spatial Cognition

**Document:** 19_SPATIAL_COGNITION.md  
**Status:** P0 Critical Architecture Specification  
**Authority:** `02-novi-brain`  
**Depends on:** 02 Cognitive Architecture, 03 Brain State Model, 05 Cognitive Cycle, 11 Perception Architecture, 16 Multimodal Fusion, 17 Spatial & Proprioceptive Fusion, 18 World Model  
**Purpose:** Define how Novi represents, understands, reasons about, remembers, predicts and acts within physical space.

---

## 1. Purpose

Spatial cognition is the capability that transforms geometric and sensory information into an internal understanding of **where Novi is, where things are, what places mean, how spaces relate, how entities move through them, and what actions are possible from a given physical situation**.

Spatial cognition is not identical to localization, mapping or navigation.

Those systems provide important evidence and infrastructure. Spatial cognition is the higher-level cognitive capability that uses them.

```text
Sensors
  ↓
Perception
  ↓
Localization / Mapping / Reconstruction
  ↓
Spatial Evidence
  ↓
Spatial Representation
  ↓
Spatial Cognition
  ├── place understanding
  ├── perspective
  ├── relationships
  ├── spatial memory
  ├── affordances
  ├── prediction
  ├── route reasoning
  └── action consequences
  ↓
Planning / Behavior
  ↓
Movement
```

---

# 2. Core requirement

Novi must maintain a continuously updated spatial understanding of its environment and body.

It must be able to answer, with an explicit confidence level:

- Where am I?
- What room/place am I in?
- Which direction am I facing?
- Where is a person relative to me?
- Where is an object relative to me?
- Where is an object relative to another object?
- What changed since I last observed this location?
- Have I been here before?
- Where was something previously seen?
- How can I reach a place?
- What obstacles or hazards exist?
- What can I physically reach?
- What is likely to happen if I move there?
- Which parts of my spatial understanding are uncertain?

A spatial answer must never silently convert an estimate into certainty.

---

# 3. Spatial ontology

Novi's spatial model should represent at least:

### 3.1 Coordinate frames

- global/world frame;
- map frame;
- odometry frame;
- robot/base frame;
- sensor frames;
- object frames;
- person frames where appropriate;
- local planning frames.

Frame ownership and transforms are governed by the robotics architecture and must remain consistent with the canonical time/transform contracts.

### 3.2 Places

A place is a semantically meaningful spatial region such as:

- home;
- room;
- corridor;
- doorway;
- workstation;
- charging area;
- meeting area;
- storage area;
- restricted area.

Places may be hierarchical:

```text
building
 └── floor
      └── room
           └── area
                └── landmark
```

### 3.3 Landmarks

Landmarks are stable or sufficiently persistent spatial references:

- doors;
- furniture;
- walls;
- shelves;
- signs;
- charging station;
- distinctive objects;
- visual features.

### 3.4 Entities

Entities can have spatial relationships such as:

```text
person A
  ├── inside room B
  ├── left of table C
  ├── near Novi
  └── moving toward doorway D
```

### 3.5 Regions

The system may represent:

- occupied regions;
- free space;
- traversable space;
- restricted space;
- hazardous space;
- uncertain space;
- dynamically changing space.

---

# 4. Egocentric and allocentric representations

Novi requires both perspectives.

## Egocentric

Relative to Novi:

- left/right;
- front/behind;
- above/below;
- near/far;
- reachable/unreachable.

Useful for immediate interaction and action.

## Allocentric

Relative to the persistent environment:

- room topology;
- map coordinates;
- place relationships;
- historical locations;
- routes between places.

Useful for memory, navigation and long-term reasoning.

The system must preserve the transform between these representations rather than treating them as unrelated maps.

---

# 5. Topological and metric space

Novi should maintain both:

### Metric representation

Answers questions such as:

> Where exactly is the table?

### Topological representation

Answers questions such as:

> Which room connects to this corridor?

The two representations complement each other.

```text
Metric
  └── geometry / distance / pose

Topology
  └── connectivity / containment / adjacency
```

A topological representation can remain useful when metric precision temporarily degrades.

---

# 6. Place recognition

Novi should recognize previously encountered places using multiple evidence types where available:

- visual appearance;
- geometric structure;
- landmarks;
- spatial topology;
- object configuration;
- temporal context;
- semantic information.

Place recognition must support uncertainty and environmental change.

A room with moved furniture should not automatically become a new place.

---

# 7. Spatial memory

Spatial cognition must integrate with the memory architecture.

A spatial memory record may contain:

```text
place_id
entity_id
pose
orientation
observation_time
confidence
source_sensor
map_version
environment_version
context
last_seen
historical_poses
```

Spatial memory must preserve historical information where useful rather than overwriting every previous state.

This enables reasoning such as:

> "The chair was previously beside the desk, but it is no longer there."

---

# 8. Object permanence

Novi should distinguish:

```text
not currently observed
        ≠
probably moved
        ≠
probably destroyed
        ≠
unknown
```

If an object disappears from visual observation, the world model should retain the entity with an appropriate uncertainty state.

Example:

```text
last seen: kitchen
last pose: shelf
current observation: absent
belief: likely still in environment
confidence: decreasing with time
```

New evidence should update the belief.

---

# 9. Spatial relationships

The representation should support qualitative and quantitative relationships.

Examples:

- left/right;
- above/below;
- in front/behind;
- inside/contains;
- near/far;
- touching;
- overlapping;
- connected;
- blocked by;
- accessible from;
- visible from;
- reachable from;
- moving toward;
- moving away from.

Relationships should carry:

- timestamp;
- source evidence;
- confidence;
- validity interval where applicable.

---

# 10. Perspective reasoning

Novi must understand that different agents can have different observations.

Example:

```text
Novi sees object A.
Person B is behind a wall.

Novi must not infer:
"Person B can see object A."
```

Spatial reasoning should therefore support visibility and viewpoint where sufficient geometry exists.

This becomes important for:

- social cognition;
- communication;
- navigation;
- search;
- safety;
- manipulation.

---

# 11. Visibility and line of sight

The spatial system should represent:

- currently visible;
- previously visible;
- occluded;
- outside sensor coverage;
- uncertain visibility.

Visibility is not equivalent to existence.

```text
not visible
    ≠
not present
```

This is especially important for people and moving objects.

---

# 12. Affordances

Spatial cognition should reason about what the environment physically permits.

Examples:

- a chair affords sitting;
- a doorway affords passage;
- a handle may afford grasping;
- a corridor affords traversal;
- a shelf may afford placement.

Affordances are predictions about possible interactions, not permissions.

```text
affordance
   ↓
possible action
   ↓
goal relevance
   ↓
safety / authorization
   ↓
action proposal
```

---

# 13. Reachability

Reachability must account for:

- robot footprint;
- current pose;
- obstacles;
- configuration limits;
- dynamic obstacles;
- terrain/geometry;
- manipulation reach where applicable;
- safety margins;
- uncertainty.

The answer should not simply be Boolean.

Recommended representation:

```text
reachable
reachable_with_constraints
uncertain
currently_unreachable
known_impossible
```

---

# 14. Spatial prediction

Novi should maintain short-horizon predictions for relevant entities.

Examples:

- person trajectory;
- object movement;
- obstacle appearance;
- free-space changes;
- expected robot pose after an action.

Predictions must include:

- prediction horizon;
- confidence;
- model/version;
- timestamp;
- assumptions.

Predictions must never be stored as observations.

---

# 15. Spatial change detection

Novi should detect meaningful changes in its environment:

```text
previous state
     ↓
new evidence
     ↓
change hypothesis
     ↓
verification
     ↓
world-model update
```

Examples:

- furniture moved;
- door opened/closed;
- person entered/left;
- obstacle appeared;
- object disappeared;
- route became blocked.

Change detection should avoid excessive cognitive churn from harmless sensor noise.

---

# 16. Search and exploration

Spatial cognition supports search goals.

Example:

> "Find the red bag."

Novi should combine:

- last-known location;
- likely locations;
- object semantics;
- room topology;
- visibility;
- search history;
- uncertainty;
- movement cost.

Search should update beliefs as areas are inspected.

---

# 17. Spatial attention

Spatial cognition interacts with attention.

A spatial event can raise attention based on:

- proximity;
- velocity;
- novelty;
- threat;
- goal relevance;
- social relevance;
- uncertainty;
- predicted collision;
- expected information value.

This allows Novi to notice something approaching without requiring an external command.

---

# 18. Active perception

Novi may deliberately change its pose or viewpoint to reduce spatial uncertainty.

```text
uncertainty
    ↓
possible viewpoints
    ↓
expected information gain
    ↓
cost / safety
    ↓
choose observation action
    ↓
move / orient
    ↓
observe
    ↓
update belief
```

This is a core mechanism for embodied intelligence.

---

# 19. Navigation relationship

Spatial cognition does not replace navigation.

```text
Spatial Cognition
     ↓
"Where should I go and why?"
     ↓
Navigation
     ↓
"What collision-free route should I follow?"
     ↓
Motion Control
     ↓
"How should the motors move?"
```

The separation prevents high-level cognition from bypassing navigation/control safety.

---

# 20. Action consequences

Novi should predict how its actions change spatial state.

Example:

```text
open door
   ↓
expected:
  doorway accessible
  visibility changes
  navigation topology may change
   ↓
execute
   ↓
observe
   ↓
compare prediction with reality
```

Prediction error becomes evidence for future reasoning and learning.

---

# 21. Spatial reasoning and language

Language references should resolve into spatial entities when possible.

Examples:

> "the table near the window"

> "the person behind me"

> "go back to the room we were in earlier"

The language layer should query spatial cognition rather than invent coordinates.

---

# 22. Human spatial interaction

For socially intelligent behavior, Novi should understand spatial relationships between itself and people.

Relevant concepts include:

- interpersonal distance;
- approach/retreat;
- orientation;
- conversational positioning;
- personal-space constraints;
- group formation;
- safe following distance;
- line of sight;
- accessibility.

These should inform behavior but must remain subordinate to safety, privacy and explicit policy.

---

# 23. Spatial uncertainty

Every important spatial estimate should have uncertainty.

Examples:

```text
pose uncertainty
object-position uncertainty
identity-location uncertainty
map uncertainty
visibility uncertainty
reachability uncertainty
prediction uncertainty
```

When uncertainty becomes operationally significant, Novi should either:

1. gather more information;
2. choose a safer action;
3. ask a human;
4. defer the action.

---

# 24. NVIDIA technology mapping

NVIDIA technologies are implementation candidates, not architecture authority.

Relevant candidates include:

- Isaac ROS Visual SLAM;
- Isaac ROS Nvblox;
- Isaac ROS perception components;
- Nav2 integration;
- Isaac Sim;
- Isaac Lab for learned spatial policies;
- Cosmos for learned physical-world prediction.

NVIDIA documents Isaac ROS as a ROS 2 robotics stack containing accelerated perception and localization/mapping components. NVIDIA documentation also describes Nvblox as a real-time 3D reconstruction system supporting TSDF/ESDF representations and navigation-related workflows. Isaac Sim provides simulated sensors, transforms and ROS 2 integration suitable for spatial validation.

These technologies must be evaluated against Novi-specific latency, accuracy, robustness, resource and failure requirements before adoption.

---

# 25. Deterministic vs learned spatial cognition

Spatial cognition is hybrid.

## Deterministic / geometric

- coordinate transforms;
- distance calculations;
- collision geometry;
- map topology;
- occupancy/free-space representation;
- frame consistency;
- route constraints;
- kinematic limits.

## Learned

Potentially:

- place recognition;
- semantic scene understanding;
- object permanence priors;
- trajectory prediction;
- affordance prediction;
- visual-semantic spatial reasoning;
- world prediction.

## Cognitive

- deciding what spatial information matters;
- deciding when to explore;
- choosing information-gathering actions;
- resolving ambiguous references;
- relating space to goals and memory.

---

# 26. Spatial cognition data contract

A canonical spatial belief should contain at least:

```text
spatial_entity_id
entity_type
frame_id
pose
extent
relationships
place_id
observation_sources
belief_state
confidence
uncertainty
valid_from
valid_until
last_observed
prediction
prediction_horizon
map_version
calibration_version
model_versions
provenance
```

The exact executable schema must be defined in the canonical contract layer before implementation.

---

# 27. Failure modes

Required failure handling includes:

- localization loss;
- map corruption;
- transform inconsistency;
- stale spatial state;
- conflicting sensors;
- dynamic-environment mismatch;
- false place recognition;
- object identity confusion;
- false reachability;
- prediction failure;
- clock/timestamp problems;
- calibration drift;
- sensor blind spots.

Novi must degrade conservatively when spatial confidence is insufficient.

---

# 28. Safety boundaries

Spatial cognition must never directly command actuators.

```text
spatial belief
   ↓
plan/action proposal
   ↓
safety/governance
   ↓
navigation/controller
   ↓
actuation
```

A spatial model may recommend that a route is safe, but an independent safety/control layer must retain final authority.

---

# 29. Validation strategy

Spatial cognition requires layered validation.

### Unit

- transform calculations;
- relationship semantics;
- coordinate conversions;
- uncertainty propagation.

### Simulation

- known maps;
- known landmarks;
- moving people;
- occlusions;
- dynamic obstacles;
- changing furniture;
- localization loss;
- sensor failure.

### HIL

- real IMU;
- real encoders;
- real camera/LiDAR interfaces;
- simulated environment;
- timing faults.

### Physical

- repeatable routes;
- place recognition;
- object relocation;
- human interaction;
- recovery;
- long-duration drift.

### Acceptance metrics

At minimum:

- localization accuracy;
- place-recognition precision/recall;
- spatial relation accuracy;
- object-location accuracy;
- reachability precision/recall;
- prediction error;
- recovery time;
- false-confidence rate;
- stale-state rate;
- computational latency.

---

# 30. Required tests

At minimum:

- `SPATIAL-001` frame consistency;
- `SPATIAL-002` pose uncertainty propagation;
- `SPATIAL-003` place recognition;
- `SPATIAL-004` object permanence;
- `SPATIAL-005` spatial relation inference;
- `SPATIAL-006` visibility reasoning;
- `SPATIAL-007` reachability classification;
- `SPATIAL-008` dynamic obstacle update;
- `SPATIAL-009` action-consequence prediction;
- `SPATIAL-010` localization recovery;
- `SPATIAL-011` active-perception behavior;
- `SPATIAL-012` spatial memory persistence;
- `SPATIAL-013` sensor disagreement;
- `SPATIAL-014` stale-data rejection;
- `SPATIAL-015` long-duration spatial drift.

Each test must eventually produce reproducible evidence linked to the implementation and requirement.

---

# 31. Open ADRs

The following decisions must be evaluated rather than assumed:

- spatial database representation;
- graph representation;
- metric-map technology;
- topological-map representation;
- place-recognition model;
- trajectory-prediction model;
- learned affordance model;
- active-perception policy;
- map persistence strategy;
- multi-floor/multi-building representation;
- spatial-memory retention;
- real/simulated spatial-state synchronization.

---

# 32. Definition of done

Spatial cognition is architecturally complete when Novi has documented and validated:

- spatial ontology;
- metric and topological representations;
- egocentric/allocentric transformations;
- place recognition;
- spatial memory;
- object permanence;
- visibility;
- spatial relationships;
- reachability;
- affordances;
- prediction;
- change detection;
- search/exploration;
- active perception;
- action consequences;
- uncertainty;
- failure handling;
- safety boundaries;
- NVIDIA technology evaluation;
- executable contracts;
- benchmark definitions;
- acceptance criteria.

---

# 33. Core principle

> **Novi does not merely occupy space. Novi understands itself as an entity situated in a changing physical world.**

Its spatial cognition must continuously connect:

```text
where Novi is
     +
where the world is
     +
what has changed
     +
what is possible
     +
what is uncertain
     +
what Novi intends to do
     +
what Novi expects to happen
     ↓
embodied spatial intelligence
```

This capability is foundational to autonomous movement, social interaction, active perception, memory, planning and the continuous embodied behavior required by the Novi North Star.
