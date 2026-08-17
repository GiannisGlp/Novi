# 99 — Memory Knowledge Spatial Memory and Spatial State Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi represents, stores, updates, retrieves, reasons over and governs spatial knowledge and spatial state across memory, perception, localization, mapping, navigation, entities and time.

99 resolves the second major spatial dependency identified by 96 after identity (97) and temporal reasoning (98). It conforms to 95 and is designed to provide the spatial foundation for 100 Causal World Modeling and 101 Cross-Modal Memory.

## 1. Core Principle

> **Spatial memory is a time-aware, uncertainty-bearing model of relationships between entities, observations and places; coordinates are evidence, not the complete meaning of a place.**

Novi must distinguish:

```text
COORDINATE
LOCATION ESTIMATE
PLACE
REGION
OBJECT
LANDMARK
ROUTE
TOPOLOGY
GEOMETRY
SPATIAL RELATION
SPATIAL STATE
SPATIAL MEMORY
```

A single coordinate or map representation cannot adequately represent all of these.

## 2. Why Spatial Memory Is a Foundational Layer

Many downstream capabilities require spatial identity and relationships:

```text
ENTITY
  ↓
WHERE?
  ↓
WHEN?
  ↓
RELATIONSHIP
  ↓
ACTION
```

Incorrect spatial association can cause:

- wrong memories;
- incorrect navigation;
- stale world models;
- privacy leakage through location;
- unsafe actions;
- incorrect causal inference;
- incorrect place identity;
- false relationship formation.

Recent work on semantic-spatial memory shows that combining semantic and spatial memory can improve spatial reasoning in embodied systems, rather than treating location as a simple coordinate lookup. [1] fileciteturn167file0

## 3. Spatial Memory Is Not One Representation

Novi should support multiple complementary representations:

```text
METRIC
TOPOLOGICAL
SEMANTIC
LANDMARK
ROUTE
REGION / AREA
OBJECT-CENTRIC
SCENE / GRAPH
TRAJECTORY
GEOGRAPHIC
```

No single representation is universally sufficient.

## 4. Metric Representation

Metric spatial memory represents measurable geometry:

```text
POINT
LINE
POLYGON
DISTANCE
ANGLE
ORIENTATION
ALTITUDE
```

It is appropriate when quantitative spatial relationships matter.

## 5. Topological Representation

Topological memory represents relationships such as:

```text
CONNECTED_TO
ADJACENT_TO
CONTAINS
INSIDE
OUTSIDE
DISCONNECTED_FROM
OVERLAPS
```

Topological relationships can remain useful when exact coordinates are uncertain.

Research on embodied navigation supports combining topological representations with semantic relations rather than forcing all spatial knowledge into one representation. [2] fileciteturn168file0

## 6. Semantic Spatial Representation

Spatial memory should represent meaningful entities and relations:

```text
KITCHEN
 ├─ contains → TABLE
 ├─ adjacent_to → HALLWAY
 └─ near → WINDOW
```

This permits natural-language spatial queries without discarding geometric information.

## 7. Place vs Coordinate

```text
COORDINATE
 ≠
PLACE
```

A place can have:

- boundaries;
- aliases;
- historical names;
- changing geometry;
- semantic meaning;
- relationships;
- multiple coordinate representations.

## 8. Spatial Identity

Spatial entities should have stable internal identifiers compatible with 97:

```text
PLACE_ID
OBJECT_ID
LANDMARK_ID
REGION_ID
ROUTE_ID
```

Coordinates and labels remain attributes or observations.

## 9. Reference Frames

Every spatial measurement should specify its reference frame where relevant:

```text
WORLD / MAP FRAME
LOCAL FRAME
ROBOT / BODY FRAME
CAMERA FRAME
DEVICE FRAME
SCREEN / IMAGE FRAME
```

A vector without a reference frame is incomplete spatial information.

## 10. Coordinate Systems

Spatial data may use:

- geographic latitude/longitude;
- projected coordinate systems;
- local Cartesian frames;
- altitude/elevation references;
- indoor local maps.

Conversions must preserve uncertainty and provenance.

## 11. Spatial Uncertainty

Novi must represent uncertainty in:

```text
POSITION
ORIENTATION
BOUNDARY
DISTANCE
RELATIONSHIP
MAP ALIGNMENT
ENTITY ASSOCIATION
```

A location estimate must not be represented with more precision than its evidence supports.

## 12. Localization vs Spatial Memory

```text
LOCALIZATION
→ estimate current pose/state

SPATIAL MEMORY
→ retain spatial knowledge across time
```

They interact but are not interchangeable.

Current localization should remain authoritative for current pose when available.

## 13. Current State vs Historical Spatial Memory

```text
CURRENT LOCALIZATION
      ≠
HISTORICAL LOCATION
```

A memory that an object was at location A yesterday cannot establish that it remains there today.

This follows 95's current-state supremacy rule and 98's temporal validity model.

## 14. Spatiotemporal State

Spatial state should be modeled jointly with time:

```text
ENTITY
 ↓
LOCATION / RELATION
 ↓
VALID TIME INTERVAL
 ↓
CONFIDENCE
 ↓
PROVENANCE
```

Example:

```text
DEVICE X
at ROOM A
[T1–T2]
```

## 15. Spatial Observations

An observation should preserve:

- observer/source;
- timestamp/capture time;
- estimated position;
- reference frame;
- observed entities;
- uncertainty;
- environmental context;
- provenance.

## 16. Egocentric vs Allocentric Memory

Novi should distinguish:

```text
EGOCENTRIC
→ relative to observer

ALLOCENTRIC
→ relative to environment/world
```

A robot observing "left of me" must not automatically convert this into an enduring world relation without pose and frame information.

## 17. Perspective Transformation

```text
CAMERA FRAME
 ↓
BODY FRAME
 ↓
LOCAL MAP FRAME
 ↓
WORLD / GLOBAL FRAME
```

Every transformation should preserve transformation metadata and uncertainty.

## 18. Landmark Memory

Landmarks are salient spatial anchors:

```text
LANDMARK
 ├─ identity
 ├─ location
 ├─ visual/semantic features
 ├─ validity interval
 └─ provenance
```

A landmark can support localization without being a perfect coordinate anchor.

## 19. Route Memory

Route memory records traversed or inferred sequences:

```text
A → B → C → D
```

It should retain:

- direction;
- time;
- conditions;
- agent;
- confidence;
- observed vs inferred segments.

## 20. Survey / Map Memory

Survey memory represents broader environment structure:

```text
PLACE A
 ├─ north_of → PLACE B
 ├─ connected_to → PLACE C
 └─ contains → PLACE D
```

Research on cognitive maps distinguishes route-like and map-like spatial knowledge and shows the importance of structured representations for flexible navigation. [4] fileciteturn170file0

## 21. Spatial Aliasing

Different locations can produce similar observations:

```text
OBSERVATION X
   ↙      ↘
PLACE A  PLACE B
```

The system must not assume identical sensory observations imply identical locations.

Cognitive-map research explicitly addresses aliasing by separating observations according to context. [4] fileciteturn170file0

## 22. Context-Dependent Spatial Identity

The same landmark appearance may occur in multiple places.

Spatial identity should use:

```text
OBSERVATION
 +
CONTEXT
 +
TEMPORAL STATE
 +
RELATIONSHIPS
```

before establishing a persistent spatial association.

## 23. Object-Centric Spatial Memory

Novi should support queries such as:

```text
WHERE IS OBJECT X?
WHAT IS NEAR OBJECT X?
WHAT CONTAINS OBJECT X?
WHAT WAS NEAR OBJECT X?
```

These should resolve through 97 identity and 98 temporal state.

## 24. Relative Spatial Relations

Represent:

```text
LEFT_OF
RIGHT_OF
ABOVE
BELOW
FRONT_OF
BEHIND
NEAR
FAR
INSIDE
OUTSIDE
CONTAINS
TOUCHING
OVERLAPPING
DISCONNECTED
```

The validity of a relation depends on its reference frame and context.

## 25. Directional Relations

Terms such as "left" and "right" are frame-dependent.

```text
LEFT_OF(A,B)
```

must specify the frame or convention when ambiguity is possible.

## 26. Distance Is Contextual

"Near" should not be a universal fixed distance.

It can depend on:

- entity type;
- environment;
- task;
- scale;
- movement context;
- sensor accuracy.

Metric distance and qualitative proximity should therefore remain distinct.

## 27. Spatial Relations Carry Provenance

Every important relation should be traceable:

```text
RELATION
 ↓
OBSERVATION / INFERENCE
 ↓
SOURCE
 ↓
TIME
```

This integrates directly with 92.

## 28. Observed vs Inferred Spatial Relations

```text
OBSERVED:
"Camera detected object X inside room A"

INFERRED:
"Object X probably remains inside room A"
```

These must not share the same epistemic status.

## 29. Spatial Beliefs

A spatial belief is derived through evidence fusion:

```text
SPATIAL EVIDENCE
 ↓
91 ARBITRATION
 ↓
SPATIAL BELIEF
```

Conflicting spatial evidence remains visible.

## 30. Map Versioning

Maps change:

```text
MAP v1
 ↓
construction
 ↓
MAP v2
```

Spatial memory must retain map/version context for historical interpretation.

## 31. Dynamic Environments

The world is not static.

Examples:

- furniture moves;
- roads close;
- buildings change;
- temporary obstacles appear;
- doors open/close;
- people move.

Spatial memory must represent persistence and change rather than treating one map as permanent truth.

## 32. Static vs Dynamic Spatial Knowledge

```text
STATIC / SLOWLY CHANGING
→ building geometry

DYNAMIC
→ person location
→ vehicle location
→ obstacle state
```

Retention and refresh policies should differ accordingly.

## 33. Spatial Memory Decay

Stale spatial knowledge should lose retrieval priority or current-state eligibility according to policy.

```text
OLD LOCATION
 ↓
DECAY
 ↓
VERIFY BEFORE USE
```

Decay must not erase historical evidence.

## 34. Spatial Change Detection

New observations should be compared against stored spatial state:

```text
EXPECTED
   vs
OBSERVED
   ↓
CHANGE HYPOTHESIS
```

A change hypothesis should not automatically rewrite historical memory.

## 35. Contradictory Spatial Evidence

Example:

```text
Memory: DEVICE X in ROOM A
Sensor: DEVICE X in ROOM B
```

The correct state is initially:

```text
CONFLICTED
```

not immediate overwriting.

Arbitration should consider sensor reliability, timestamps, identity confidence and physical plausibility.

## 36. Spatial Constraints

Spatial reasoning may use constraints such as:

```text
OBJECT INSIDE ROOM
ROOM INSIDE BUILDING
BUILDING AT LOCATION
```

Constraints must be domain-specific and must not be treated as universal physical laws without justification.

## 37. Containment Hierarchies

Support nested spatial entities:

```text
COUNTRY
 ↓
CITY
 ↓
BUILDING
 ↓
FLOOR
 ↓
ROOM
 ↓
OBJECT
```

Containment relationships need temporal validity and provenance.

## 38. Spatial Graph

The spatial knowledge graph should support:

```text
NODE = entity/place/landmark/region
EDGE = spatial relation
```

Edges should support:

- validity interval;
- confidence;
- source;
- provenance;
- version;
- uncertainty.

## 39. Metric + Graph Hybrid

Novi should not choose between metric maps and graphs globally.

```text
METRIC LAYER
      ↕
TOPOLOGICAL LAYER
      ↕
SEMANTIC LAYER
```

Different queries can use different representations.

Recent navigation research similarly combines topological and semantic structures to connect spatial memory with reasoning. [2] fileciteturn168file0

## 40. Spatial Retrieval

Queries should be resolved according to task:

```text
WHERE?
NEAR WHAT?
HOW FAR?
HOW TO GET THERE?
WHAT CHANGED?
WHAT WAS THERE?
WHAT IS INSIDE?
WHAT IS CONNECTED?
```

Retrieval should combine semantic and spatial cues rather than relying on text similarity alone. Recent Meta-Memory work explicitly demonstrates joint semantic-spatial retrieval for location reasoning. [1] fileciteturn167file0

## 41. Spatial Context Assembly

A spatial context package may contain:

```text
CURRENT POSE
RELEVANT MAP REGION
LANDMARKS
ENTITY LOCATIONS
RELATIONSHIPS
RECENT OBSERVATIONS
HISTORICAL CONTEXT
UNCERTAINTY
PROVENANCE
```

Only the minimum sufficient spatial context should be supplied to reasoning.

## 42. Spatial Memory Does Not Authorize Movement

```text
SPATIAL MEMORY
 ↓
NAVIGATION CONTEXT
 ↓
PLANNING
 ↓
CURRENT PERCEPTION
 ↓
SAFETY CHECK
 ↓
ACTION
```

A remembered obstacle-free route cannot authorize movement through the current environment.

## 43. Current Perception Supremacy for Safety

For immediate physical safety:

```text
CURRENT SENSOR / LOCALIZATION
        >
STALE SPATIAL MEMORY
```

Historical maps remain useful for planning but must be revalidated before consequential action.

## 44. Route Feasibility

A remembered route is not automatically currently feasible.

It must be checked against:

- current obstacles;
- access restrictions;
- localization;
- route closures;
- environmental changes;
- safety constraints.

## 45. Spatial Privacy

Precise location can be highly sensitive.

Spatial memory must support:

```text
ACCESS CONTROL
PRECISION REDUCTION
RETENTION LIMITS
PURPOSE LIMITATION
AUDITING
ERASURE
```

A less precise location may be sufficient for some tasks and safer for others.

## 46. Location Precision Policy

Novi should support policy-driven precision:

```text
EXACT COORDINATE
BUILDING
NEIGHBORHOOD
CITY
REGION
UNKNOWN
```

Precision must not be increased merely because a lower-level representation exists internally.

## 47. Cross-User Spatial Boundaries

One user's location history must not automatically become another user's spatial memory.

Shared places should be separated from private trajectories.

## 48. Spatial Erasure

Deletion of spatial memories must evaluate:

```text
TRAJECTORIES
LOCATION HISTORY
PLACE ASSOCIATIONS
MAP ANNOTATIONS
RELATIONSHIPS
INDEXES
CACHES
DERIVED INFERENCES
```

This integrates 87 and 92.

## 49. Spatial Security Threats

Threats include:

- location poisoning;
- fake landmarks;
- malicious map updates;
- route manipulation;
- spoofed localization;
- GPS/GNSS deception;
- sensor compromise;
- spatial inference attacks;
- cross-user location leakage;
- stale-map exploitation.

## 50. Spatial Provenance

A spatial claim should be traceable to:

```text
SENSOR / SOURCE
 ↓
OBSERVATION
 ↓
TRANSFORMATION
 ↓
SPATIAL ESTIMATE
 ↓
SPATIAL MEMORY
 ↓
DERIVED BELIEF
```

## 51. Map Integrity

Maps and spatial models require integrity metadata:

- source;
- version;
- update time;
- transformation history;
- confidence;
- coverage;
- known limitations.

External maps should not automatically become authoritative internal state.

## 52. Collaborative Spatial Memory

Multiple agents can contribute spatial observations:

```text
AGENT A ─┐
AGENT B ─┼→ SPATIAL EVIDENCE
AGENT C ─┘
```

Contributions must retain agent identity, trust domain and provenance.

## 53. Spatial Conflict Across Agents

Different agents can report different positions or maps.

Resolve through 91 using:

- timestamp;
- localization quality;
- source reliability;
- frame alignment;
- independence;
- physical constraints.

## 54. Spatial Synchronization

Distributed spatial memory requires:

- map versioning;
- causal ordering;
- conflict handling;
- update provenance;
- deletion propagation.

## 55. Spatial Memory Efficiency

Spatial memory can become very large.

A recent 2026 survey of 52 systems highlights that persistent map size alone does not capture runtime memory cost and proposes measuring memory growth, query latency, completeness and throughput degradation. [3] fileciteturn169file0

Therefore Novi must measure both:

```text
PERSISTENT SIZE
RUNTIME MEMORY
QUERY COST
UPDATE COST
LATENCY
COMPLETENESS
```

## 56. Hierarchical Spatial Memory

For scale, use multiple levels:

```text
GLOBAL
 ↓
REGION
 ↓
LOCAL MAP
 ↓
ROOM / AREA
 ↓
OBJECT
```

Queries should load only the necessary spatial resolution.

## 57. Spatial Memory Compression

Compression must preserve task-critical semantics.

```text
RAW OBSERVATIONS
 ↓
LANDMARKS / TOPOLOGY / SEMANTIC GRAPH
 ↓
COMPACT SPATIAL MEMORY
```

Derived representations must retain lineage to source observations.

## 58. No Representation Is Automatically Authoritative

```text
GPS
MAP
SLAM
VISION
TEXT
MEMORY
```

Each is a source of evidence with domain-specific limitations.

## 59. Spatial Evidence Fusion

Spatial fusion may combine:

```text
LOCALIZATION
VISION
MAP
ODOMETRY
LANDMARKS
USER REPORTS
OTHER AGENTS
```

Fusion must account for correlated sources and uncertainty.

## 60. Semantic-Spatial Fusion

Semantic reasoning and spatial reasoning should be linked without collapsing one into the other.

```text
SEMANTIC GRAPH
      ↕
SPATIAL GRAPH
      ↕
METRIC MAP
```

Recent embodied-navigation work demonstrates practical value in explicitly coupling semantic and topological/spatial memory. [2] fileciteturn168file0

## 61. Spatial Learning

New spatial memories should pass through the memory admission and consolidation pipeline:

```text
OBSERVATION
 ↓
SPATIAL EVIDENCE
 ↓
VALIDATION
 ↓
SPATIAL MEMORY CANDIDATE
 ↓
CONSOLIDATION
```

Repeated self-generated spatial descriptions do not count as independent evidence.

## 62. Spatial Reconsolidation

Retrieving a map or location does not automatically rewrite it.

```text
RETRIEVAL
 ≠
MAP UPDATE
```

Updates require new evidence and validation.

## 63. Spatial Temporal Queries

Novi should support:

```text
WHERE WAS X AT T?
WHEN WAS X HERE?
WHAT CHANGED BETWEEN T1 AND T2?
WHICH ROUTE WAS VALID AT T?
```

These queries depend jointly on 97 and 98.

## 64. Spatial Prediction

Predicted future location must be represented as prediction:

```text
CURRENT STATE
 ↓
MODEL
 ↓
PREDICTED LOCATION
```

It must not be stored as observed fact until validated.

## 65. Spatial Counterfactuals

Counterfactual spatial reasoning should remain separate from historical memory:

```text
"If the door were closed..."
```

must not alter the remembered actual state.

## 66. Navigation vs Spatial Memory

```text
SPATIAL MEMORY
→ what the environment is/was believed to be

NAVIGATION
→ how to act through it
```

Navigation may consume spatial memory but remains responsible for current planning and safety.

## 67. Spatial Causality Boundary

```text
A is north of B
        ≠
A caused B
```

Spatial correlation and proximity are evidence for causal hypotheses, not causal proof. This prepares the architecture for 100.

## 68. Evaluation Dataset Classes

Evaluate:

- static scenes;
- changing scenes;
- long trajectories;
- spatial aliases;
- ambiguous landmarks;
- noisy localization;
- map changes;
- multi-agent maps;
- privacy-sensitive locations;
- adversarial spatial inputs;
- cross-modal spatial queries.

## 69. Evaluation Metrics

At minimum:

```text
LOCALIZATION ERROR
RELATION ACCURACY
MAP CONSISTENCY
TEMPORAL VALIDITY
SPATIAL RETRIEVAL ACCURACY
ROUTE FEASIBILITY
CONFLICT DETECTION
STALE-MEMORY RATE
PROVENANCE COMPLETENESS
MEMORY GROWTH
QUERY LATENCY
UPDATE LATENCY
```

For navigation tasks also measure downstream safety and task success rather than map accuracy alone.

## 70. Longitudinal Evaluation

Evaluate spatial memory over accumulated experience:

```text
DAY 1
 ↓
DAY 10
 ↓
DAY 100
 ↓
DAY 1000
```

Measure map drift, stale relations, memory growth, retrieval degradation and propagation of incorrect spatial beliefs.

## 71. Spatial Error Propagation

A wrong spatial identity can propagate:

```text
WRONG ENTITY
 ↓
WRONG LOCATION
 ↓
WRONG RELATION
 ↓
WRONG MAP
 ↓
WRONG PLAN
 ↓
WRONG ACTION
```

This is why 97 must remain upstream of 99.

## 72. Human Correction

Corrections should be represented as new evidence:

```text
OLD SPATIAL BELIEF
 ↓
CORRECTION / NEW OBSERVATION
 ↓
ARBITRATION
 ↓
NEW SPATIAL STATE
```

Historical observations are not silently rewritten.

## 73. Spatial Model Versioning

Spatial model changes should retain:

- version;
- source;
- timestamp;
- transformation lineage;
- affected region;
- compatibility information.

## 74. Spatial Schema Migration

Migration must preserve spatial semantics and reference frames.

A coordinate conversion must not silently change meaning through datum, projection or axis-order mistakes.

## 75. Spatial Model Failure States

Support:

```text
UNKNOWN_LOCATION
LOW_LOCALIZATION_CONFIDENCE
STALE_MAP
FRAME_UNCERTAIN
MAP_CONFLICT
SPATIAL_ALIAS
INSUFFICIENT_COVERAGE
OUT_OF_MAP
```

These are meaningful states, not generic errors.

## 76. Safe Spatial Degradation

If spatial memory is unavailable:

```text
FULL SPATIAL MEMORY
 ↓
LIMITED LOCAL STATE
 ↓
CURRENT PERCEPTION ONLY
 ↓
SAFE FALLBACK / ABSTAIN
```

The fallback depends on task consequence.

## 77. Implementation Components

Logical components should include:

```text
Spatial Observation Store
Spatial Entity Registry
Coordinate / Frame Registry
Localization Interface
Map Store
Spatial Graph
Landmark Store
Trajectory Store
Spatial Retrieval Engine
Spatial Fusion Engine
Change Detection Engine
Spatial Policy Engine
Spatial Evaluation Harness
```

## 78. Storage Independence

The architecture may use:

- relational storage;
- graph databases;
- spatial databases;
- vector indexes;
- raster/tile stores;
- point-cloud stores;
- object storage;
- event logs.

No storage choice may weaken provenance, uncertainty, lifecycle or deletion semantics.

## 79. Research Limitations

Current research does not establish one universally optimal spatial-memory representation. Recent surveys show substantial tradeoffs between accuracy, representation type, runtime memory and deployment cost. [3] fileciteturn169file0

Therefore 99 does not mandate:

- occupancy grids;
- scene graphs;
- topological maps;
- neural implicit maps;
- 3D Gaussian representations;
- any particular SLAM system.

The representation should be selected by task, environment, hardware, uncertainty, latency and memory budget.

## 80. Architectural Invariants

1. Coordinate is not place identity.
2. Localization is not spatial memory.
3. Current state is distinct from historical spatial memory.
4. Spatial claims are time-aware.
5. Spatial measurements require reference frames where relevant.
6. Spatial uncertainty must remain explicit.
7. Egocentric and allocentric representations are distinct.
8. Relative directions are frame-dependent.
9. Location is evidence, not identity proof.
10. Spatial observations do not automatically become durable maps.
11. Observed spatial relations are distinct from inferred relations.
12. Semantic and metric spatial representations are complementary.
13. Topology and geometry are not interchangeable.
14. Spatial aliases must remain resolvable under context.
15. Map versions must remain traceable.
16. Dynamic environments require refresh and validity policies.
17. Stale spatial memory cannot override current safety perception.
18. Historical location does not establish current location.
19. Spatial memory cannot authorize physical action.
20. Route memory is not current route feasibility.
21. Correlated spatial sources are not independent confirmations.
22. External maps are evidence, not automatic authority.
23. Spatial privacy must be policy-controlled.
24. Precise location should be disclosed only when necessary and authorized.
25. Spatial deletion must consider derived trajectories, relationships and inferences.
26. Spatial updates must preserve provenance.
27. Spatial conflicts are first-class states.
28. Spatial predictions are not observations.
29. Counterfactual spatial states must not alter historical memory.
30. Spatial reasoning must remain compatible with temporal reasoning.
31. Spatial identity depends on the identity architecture of 97.
32. Spatial causal inference must remain separate from temporal/spatial correlation.
33. Spatial memory must be evaluated longitudinally.
34. Spatial memory must have explicit resource budgets.
35. No single spatial representation is universally authoritative.

## 81. Integration With 95

99 implements 95's requirements for:

- current-state supremacy;
- provenance;
- evidence arbitration;
- privacy;
- security;
- deletion;
- distributed state;
- evaluation;
- bounded context assembly.

## 82. Integration With 97

97 provides:

```text
ENTITY IDENTITY
      ↓
OBJECT / PERSON / PLACE ASSOCIATION
      ↓
SPATIAL RELATION
```

99 must not create an identity merely because an entity appears at a location.

## 83. Integration With 98

98 provides:

```text
VALID TIME
CAPTURE TIME
REVISION TIME
CURRENT TIME
```

99 attaches spatial states and relations to those temporal semantics.

## 84. Integration With 100

99 supplies spatial relationships to causal reasoning while explicitly preventing:

```text
PROXIMITY
 +
TEMPORAL ORDER
 ≠
CAUSALITY
```

100 must treat spatial information as causal evidence only when independently justified.

## 85. Integration With 101

99 provides the spatial abstraction layer through which images, audio, text and sensor streams can be spatially aligned.

## 86. Final Reference Architecture

```text
             WORLD / ENVIRONMENT
                    ↓
             OBSERVATIONS
                    ↓
          ┌───────────────────┐
          │ IDENTITY (97)     │
          └─────────┬─────────┘
                    ↓
          ┌───────────────────┐
          │ TIME (98)         │
          └─────────┬─────────┘
                    ↓
          ┌───────────────────┐
          │ SPATIAL MEMORY    │
          │                   │
          │ metric            │
          │ topology          │
          │ semantic          │
          │ landmarks         │
          │ routes            │
          │ trajectories      │
          └─────────┬─────────┘
                    ↓
          ┌───────────────────┐
          │ SPATIAL FUSION    │
          └─────────┬─────────┘
                    ↓
          ┌───────────────────┐
          │ RETRIEVAL         │
          └─────────┬─────────┘
                    ↓
          ┌───────────────────┐
          │ WORKING CONTEXT   │
          └─────────┬─────────┘
                    ↓
          ┌───────────────────┐
          │ REASONING / PLAN  │
          └─────────┬─────────┘
                    ↓
          CURRENT PERCEPTION
                    ↓
          SAFETY / AUTHORIZATION
                    ↓
                 ACTION
```

## 87. Final Principle

> **Novi's spatial memory should provide a structured, time-aware and uncertainty-aware model of where entities, places and relationships are or were, while never confusing remembered geography with current reality. Spatial memory informs reasoning and planning; current perception, authorization and safety systems remain authoritative for consequential action.**

99 therefore establishes spatial memory as the bridge between identity and temporal state on one side, and causal world modeling and cross-modal intelligence on the other.