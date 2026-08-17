# 83 — Memory Knowledge Semantic Memory and World Model

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define Novi's persistent semantic knowledge layer and embodied world model: the structured representation of entities, properties, relationships, rules, places, objects, people, environments and concepts that can be reused across episodes and tasks while remaining grounded in evidence and current state.

## Core Principle

> **Novi's world model is a structured, revisable representation of what the system currently has reason to believe about the world—not the world itself.**

## 1. Position in Architecture

```text
OBSERVATIONS / EPISODES
        ↓
PROVENANCE + VALIDATION
        ↓
SEMANTIC MEMORY / WORLD MODEL
        ↓
RETRIEVAL
        ↓
WORKING MEMORY
        ↓
REASONING / PLANNING
        ↓
ACTION
        ↓
NEW OBSERVATIONS
```

## 2. Semantic Memory vs Episodic Memory

```text
EPISODIC
"Novi saw the red bag on the table at 18:20."

SEMANTIC
"The red bag is associated with the table."
```

Semantic knowledge is reusable across episodes, but must retain lineage to the evidence that supports it where required.

## 3. World Model vs Map

A map is primarily spatial representation.

The world model can include:

- spatial structure;
- entities;
- properties;
- relationships;
- temporal state;
- affordances;
- uncertainty;
- rules;
- agent state.

The map is therefore one component of the broader world model.

## 4. World Model vs Reality

The system must never assume that its internal model is complete.

```text
WORLD
  ↓ sensing
MODEL
  ↓ reasoning
BELIEF
```

Unknown regions and uncertain entities must remain representable.

## 5. Entity Model

Core entity classes may include:

```text
PERSON
ANIMAL
OBJECT
DEVICE
PLACE
ROOM
BUILDING
VEHICLE
ORGANIZATION
EVENT
CONCEPT
AGENT
```

The ontology must remain extensible.

## 6. Entity Identity

Each persistent entity should have a stable internal identifier where possible.

Identity resolution may combine:

- visual features;
- audio features;
- names;
- metadata;
- spatial continuity;
- interaction history;
- external identifiers.

Identity remains uncertain when evidence is insufficient.

## 7. Identity vs Appearance

```text
ENTITY
  ≠
CURRENT APPEARANCE
```

An object can change appearance without necessarily becoming a new entity.

## 8. Properties

Entities can have properties such as:

```text
color
size
material
location
owner
state
capability
role
preference
```

Properties should carry validity and provenance where appropriate.

## 9. Relationships

Relationships are first-class semantic objects.

Examples:

```text
PERSON --owns--> OBJECT
OBJECT --located_at--> PLACE
PERSON --visited--> PLACE
OBJECT --part_of--> DEVICE
PLACE --connected_to--> PLACE
```

Relationships can themselves have time, scope, uncertainty and provenance.

## 10. Temporal Semantics

Knowledge should distinguish:

```text
VALID_FROM
VALID_UNTIL
OBSERVED_AT
ASSERTED_AT
RETIRED_AT
```

This prevents historical facts from being mistaken for current state.

## 11. Current State vs Historical State

```text
CURRENT STATE
    ↕
HISTORICAL STATES
```

A property can change while its historical values remain traceable where retention permits.

## 12. State Transitions

World-model state can be represented as transitions:

```text
OPEN
 ↓
CLOSED
 ↓
LOCKED
```

The transition should be linked to evidence rather than treated as arbitrary overwrite.

## 13. Uncertainty

Entities and relationships may be:

```text
CONFIRMED
PROVISIONAL
UNCERTAIN
CONTESTED
UNKNOWN
```

Uncertainty must be explicit rather than hidden inside a single score.

## 14. Unknown as First-Class State

Novi must be able to represent:

```text
UNKNOWN
NOT OBSERVED
NOT APPLICABLE
NOT AUTHORIZED
NOT CURRENTLY AVAILABLE
```

These states must not collapse into `false`.

## 15. Spatial World Model

Spatial knowledge can include:

- rooms;
- buildings;
- streets;
- landmarks;
- regions;
- routes;
- coordinates;
- topology;
- occupancy;
- traversability.

Spatial uncertainty remains attached to relevant facts.

## 16. Coordinate Frames

Novi may operate with multiple frames:

```text
WORLD / MAP FRAME
LOCAL ROBOT FRAME
CAMERA FRAME
LIDAR FRAME
BODY FRAME
```

Transform metadata must remain available to prevent invalid spatial reasoning.

## 17. Localization

Localization can combine:

- GNSS;
- visual localization;
- LiDAR localization;
- inertial estimation;
- map matching;
- landmarks.

The world model must retain localization uncertainty and source context.

## 18. Visited Places

The world model can represent:

```text
visited
observed
mapped
currently occupied
currently accessible
preferred
historically associated
```

These are distinct predicates.

## 19. Route Knowledge

Routes may contain:

- origin;
- destination;
- segments;
- historical traversal;
- travel time;
- obstacles;
- uncertainty;
- map version.

Historical route success does not guarantee current traversability.

## 20. Dynamic Objects

The model should distinguish static and dynamic entities.

```text
TABLE
 → relatively static

PERSON
 → dynamic
```

Dynamic state requires more frequent refresh.

## 21. Object Tracking

Object continuity can use:

- sensor observations;
- temporal continuity;
- spatial continuity;
- appearance/features;
- identity evidence.

Tracking uncertainty must remain explicit.

## 22. Person Model

A person entity may contain:

- identity hypothesis;
- relationship to user/household;
- preferences;
- interaction history;
- authorization scope;
- privacy classification.

Sensitive attributes require stricter handling.

## 23. Household Model

Novi may model a household as a set of entities and relationships:

```text
HOUSEHOLD
 ├── PEOPLE
 ├── ROOMS
 ├── OBJECTS
 ├── DEVICES
 └── ROUTINES
```

Membership and permissions must not be inferred solely from physical presence.

## 24. Ownership vs Possession

```text
OWNS
 ≠
CURRENTLY HOLDS
```

The world model must distinguish legal/declared ownership from transient physical possession where relevant.

## 25. Affordances

The world model may represent possible interactions:

```text
chair → sit_on
button → press
handle → grasp
```

Affordance inference is probabilistic and environment-dependent.

## 26. Rules

Rules can represent known constraints:

```text
DOOR locked → cannot normally pass
BATTERY low → charging preferred
```

Rules must be sourced and scoped.

Safety constraints remain outside ordinary semantic knowledge when they require hard real-time authority.

## 27. User Preferences

Preferences can be represented as scoped semantic knowledge:

```text
PERSON → prefers → X
```

They require:

- owner;
- scope;
- source;
- validity;
- confidence/status.

## 28. Concepts

Semantic memory can represent concepts and hierarchies:

```text
DEVICE
 ├── COMPUTER
 └── SENSOR
```

Concept hierarchy does not automatically imply every subclass relationship is valid for every object.

## 29. Ontology Evolution

The ontology must support:

- adding concepts;
- deprecating concepts;
- splitting concepts;
- merging concepts;
- mapping old schemas to new schemas.

Historical data must remain interpretable after schema evolution.

## 30. Semantic Relationships and Provenance

Every important semantic assertion should be traceable to:

```text
source evidence
 ↓
transformation
 ↓
assertion
```

The semantic layer must not erase provenance established by document 74.

## 31. Evidence vs Assertion

```text
OBSERVATION
 ≠
ASSERTION
 ≠
RULE
 ≠
INFERENCE
```

This distinction must remain machine-readable.

## 32. Knowledge Promotion

Semantic assertions enter durable knowledge through the promotion lifecycle of document 76 and revision rules of document 77.

The world model must not bypass evidence quality thresholds.

## 33. Consolidation

Episodes can update semantic knowledge:

```text
EPISODES
 ↓
PATTERN
 ↓
SEMANTIC ASSERTION
```

The abstraction architecture in document 78 controls this process.

## 34. Recall

Semantic memory is retrieved through document 80 and inserted into working memory through document 81.

The world model is not directly dumped into the reasoning context.

## 35. Active World State

Working memory can hold a bounded projection of the semantic world model:

```text
CURRENT LOCATION
CURRENT OBJECTS
CURRENT PEOPLE
CURRENT TASK
CURRENT ENVIRONMENT
```

This projection must be refreshed from current observations.

## 36. Sensor Fusion

Multiple sensors can update the same world-model entity:

```text
CAMERA ─┐
LIDAR ──┼→ OBJECT STATE
IMU ────┤
THERMAL ┘
```

Fusion should preserve source evidence and uncertainty.

## 37. Current Sensor Authority

For rapidly changing physical state:

```text
CURRENT SENSOR EVIDENCE
        ↓
CURRENT WORLD STATE
```

Older semantic knowledge may provide priors but must not override fresh authoritative measurements.

## 38. Thermal World Model

Thermal information can represent:

- environmental temperature;
- object temperature;
- internal component state;
- historical thermal behavior.

Safety-critical thermal protection remains governed by real-time control systems.

## 39. Audio World Model

Audio observations can support:

- sound events;
- source hypotheses;
- acoustic landmarks;
- room acoustics.

Source identity remains uncertain unless sufficiently validated.

## 40. Camera World Model

Vision can update:

- objects;
- people hypotheses;
- scene structure;
- visual landmarks;
- object state.

Vision-derived assertions retain model/version and confidence metadata.

## 41. Map Integration

Maps provide spatial structure but can be stale.

The world model should associate map facts with:

- map source;
- version;
- timestamp;
- coordinate reference;
- confidence.

## 42. World-Model Drift

World models can become stale because:

- objects move;
- rooms change;
- roads change;
- people relocate;
- hardware changes;
- software interpretations change.

Drift should trigger revalidation or state decay where appropriate.

## 43. Belief Revision

When new evidence conflicts with semantic knowledge:

```text
OLD ASSERTION
      ↓
NEW EVIDENCE
      ↓
RE-EVALUATE
      ↓
UPDATE / DEMOTE / CONTEST / SUPERSEDE
```

The historical assertion remains traceable when retention permits.

## 44. Contradictory World Models

The system should support temporary conflicting hypotheses:

```text
Object X
 ├── located at A
 └── located at B
```

rather than silently selecting one when evidence is insufficient.

## 45. Causal Knowledge

Causal relationships require stronger evidence than simple correlation.

```text
A associated_with B
```

must not automatically become:

```text
A causes B
```

## 46. Counterfactual State

What-if worlds must be isolated from actual world state.

```text
ACTUAL WORLD MODEL
        ≠
COUNTERFACTUAL MODEL
```

## 47. Planning Interface

Planning may query the world model for:

- capabilities;
- constraints;
- current state;
- routes;
- object relationships;
- likely outcomes.

Planning results remain hypotheses until executed and observed.

## 48. Action Feedback

After action:

```text
PLAN
 ↓
ACTION
 ↓
OBSERVATION
 ↓
WORLD MODEL UPDATE
```

This closes the perception-action-learning loop.

## 49. Negative State

The model should avoid treating absence of observation as proof of absence.

```text
not observed
 ≠
not present
```

## 50. Accessibility

World-model facts can include accessibility state:

```text
UNKNOWN
ACCESSIBLE
BLOCKED
RESTRICTED
TEMPORARILY UNAVAILABLE
```

Accessibility is dynamic and must not be inferred solely from historical visits.

## 51. Safety Boundary

The semantic world model informs reasoning but cannot override:

- collision avoidance;
- motor protection;
- thermal protection;
- battery protection;
- emergency controls;
- authorization gates.

## 52. Privacy Boundary

The world model can encode highly sensitive relationships and routines.

Privacy classifications must propagate to derived semantic assertions.

## 53. Access Control

World-model access should be scoped by:

- identity;
- role;
- task;
- privacy classification;
- authorization;
- local/shared ownership.

## 54. Shared World Model

If multiple Novi instances synchronize semantic knowledge, each assertion should retain:

- source agent;
- synchronization status;
- version/causal metadata;
- trust context;
- conflict state.

## 55. Offline Operation

The local world model must remain usable offline.

Remote enrichment is optional and must not silently replace local authoritative state.

## 56. Caching and Indexing

Graph, vector and relational indexes are derived representations.

They must respect updates, deletion, authorization and invalidation.

## 57. Explainability

For important world-model assertions, Novi should be able to answer:

```text
Why does Novi believe this?
When was it observed?
What evidence supports it?
Could it be stale?
What contradicts it?
What would change the belief?
```

Answers should use actual provenance rather than generated justification.

## 58. Testing

Test:

- entity resolution;
- identity ambiguity;
- relationship updates;
- temporal validity;
- spatial uncertainty;
- coordinate transforms;
- sensor fusion;
- stale maps;
- dynamic objects;
- contradictory state;
- world-model drift;
- ontology migration;
- deletion propagation;
- privacy leakage;
- unauthorized access;
- distributed merge;
- offline synchronization;
- causal overclaiming;
- counterfactual isolation;
- safety boundary violations;
- current-sensor precedence.

## 59. Architectural Invariants

1. The world model is a belief representation, not reality itself.
2. Semantic memory remains distinct from episodic memory.
3. Evidence, assertions, inferences and rules remain distinct.
4. Important assertions preserve provenance.
5. Unknown is not equivalent to false.
6. Historical and current state remain distinct.
7. Relationships are first-class and can carry uncertainty and validity.
8. Entity identity remains uncertain when evidence is insufficient.
9. Current physical state is refreshed from authoritative current sensing.
10. Historical knowledge cannot override current safety state.
11. Visited places are distinct from currently accessible places.
12. Causal claims require stronger evidence than correlation.
13. Counterfactual state cannot mutate actual world state.
14. Semantic knowledge cannot bypass promotion/revision policies.
15. Privacy restrictions propagate through derived knowledge.
16. Distributed assertions retain source and synchronization context.
17. Offline local operation remains available.
18. Indexes cannot resurrect deleted or unauthorized knowledge.
19. Important assertions remain explainable through actual provenance.
20. World-model updates are testable, auditable and reversible where policy requires.

## 60. Final Principle

> **Novi's world model should be a living, evidence-grounded representation of entities, relationships, places, states and rules—continually updated by experience, explicit about uncertainty, and always subordinate to current authoritative sensing, safety and authorization.**

This semantic/world-model layer connects Novi's episodic history to its practical understanding of the people, places, objects and environments in which it operates.