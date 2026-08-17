# 43 — Memory Spatial World Model and Place Memory

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## High-Level Description

This document defines how Novi represents, remembers, updates, queries and learns from the physical spaces it inhabits.

The spatial memory system is not merely a navigation map. It is the long-lived representation connecting **where Novi is, what exists there, what has happened there, how Novi reached the location, what has changed, and what Novi expects to find there**.

The system must support both:

- indoor operation, primarily in the home;
- outdoor operation when Novi is taken outside;
- GPS/GNSS when available;
- local visual/inertial/LiDAR localization;
- persistent place and landmark memory;
- visited-area history;
- semantic places and rooms;
- maps that evolve over time;
- uncertainty and conflicting observations;
- offline operation.

NVIDIA Isaac ROS provides relevant building blocks, including accelerated Visual SLAM, visual global localization and nvBlox-based 3D mapping. These are implementation candidates, not architectural dependencies. NVIDIA's current documentation also demonstrates camera/IMU VSLAM, saved maps, global relocalization and dense 3D mapping on Jetson-class hardware. citeturn0search10turn0search2turn0search4

## Detailed Description

### 1. Core Principle

> **A map tells Novi where things are; spatial memory tells Novi what places mean, what happened there, how reliable that knowledge is, and how the world has changed over time.**

A navigation map and a cognitive spatial model are therefore related but different.

```text
RAW SPATIAL SENSORS
        ↓
POSE / STATE ESTIMATION
        ↓
GEOMETRIC MAP
        ↓
LANDMARKS / PLACES / OBJECTS
        ↓
SPATIAL MEMORY
        ↓
WORLD MODEL
        ↓
COGNITION / AUTONOMY
```

### 2. Spatial Layers

Novi should maintain separate but linked spatial layers:

```text
L0 — SENSOR GEOMETRY
L1 — LOCALIZATION / POSE
L2 — GEOMETRIC MAP
L3 — NAVIGATION MAP / COSTMAP
L4 — SEMANTIC MAP
L5 — PLACE MEMORY
L6 — EPISODIC SPATIAL HISTORY
L7 — PREDICTIVE WORLD MODEL
```

A failure or update in one layer must not silently corrupt all others.

### 3. Pose

Pose represents Novi's estimated position and orientation at a time.

Conceptually:

```text
pose = position + orientation + timestamp + uncertainty + frame
```

Pose must include provenance and coordinate-frame information.

### 4. Coordinate Frames

The spatial system must use explicit coordinate frames.

Conceptually:

```text
world
  ↓
map
  ↓
odom
  ↓
base_link
  ├── camera frames
  ├── lidar frame
  ├── imu frame
  ├── thermal frame
  └── actuator frames
```

ROS TF/TF2 is an important implementation reference for this structure.

### 5. Map vs World

A map is a representation produced from observations.

The world is the physical environment.

Therefore:

```text
map ≠ world
```

Maps can be incomplete, stale, distorted or uncertain.

Novi must never assume that a stored map is a perfect copy of reality.

### 6. Indoor Spatial Model

For home operation, the semantic model should support:

```text
HOME
 ├── floor
 │    ├── room
 │    │    ├── zones
 │    │    ├── landmarks
 │    │    └── objects
 │    └── corridors
 └── outdoor areas
```

Examples:

- kitchen;
- bedroom;
- living room;
- hallway;
- garden;
- doorway;
- charging location;
- preferred interaction area.

These are semantic concepts backed by observations, not merely labels attached by the LLM.

### 7. Outdoor Spatial Model

When outside, Novi should support:

- GNSS coordinates;
- local map coordinates;
- roads/paths;
- parks;
- buildings;
- landmarks;
- visited regions;
- routes;
- known locations;
- uncertain/unmapped areas.

GPS/GNSS provides global positioning when available but should not be treated as the sole localization mechanism.

### 8. GNSS Independence

Novi must remain spatially functional without GNSS.

```text
GNSS available
   → global positioning + local localization

GNSS unavailable
   → local SLAM / visual / LiDAR / inertial localization
```

This is particularly important indoors and preserves the offline-first architecture.

### 9. Spatial Sensor Inputs

Potential spatial inputs include:

- stereo/RGB cameras;
- depth cameras;
- LiDAR;
- IMU/gyroscope/accelerometer;
- GNSS;
- wheel/actuator odometry;
- visual landmarks;
- audio localization;
- thermal observations;
- known map landmarks;
- barometric altitude where useful.

Sensor fusion must preserve source provenance.

### 10. Localization

Localization answers:

> Where is Novi now?

It should produce:

```text
pose
confidence
uncertainty
source(s)
time
coordinate frame
status
```

A pose without uncertainty is insufficient for robust autonomous behavior.

### 11. Mapping

Mapping answers:

> What geometry has Novi observed?

Possible representations include:

- occupancy grids;
- point clouds;
- voxel maps;
- signed distance representations;
- feature maps;
- topological graphs;
- semantic maps.

No single representation needs to serve every task.

### 12. NVIDIA Mapping Candidates

NVIDIA Isaac ROS Visual SLAM is a strong candidate for Jetson-based visual-inertial localization/mapping. Its current documentation supports multiple synchronized cameras and IMU fusion, and NVIDIA provides saved-map and load/localize workflows. citeturn0search3turn0search7

NVIDIA nvBlox is another candidate where dense 3D reconstruction and dynamic obstacle-aware mapping are useful. NVIDIA describes it as using RGB-D and/or LiDAR data to create dense 3D maps and temporal costmaps. citeturn0search10

These must be benchmarked against open alternatives before architecture lock-in.

### 13. Place

A **place** is a persistent semantic region recognized by Novi as meaningfully distinct.

Examples:

```text
home
kitchen
front door
charging station
local park
favorite route
supermarket
```

A place is not simply a GPS coordinate.

### 14. Place Identity

A place should have a stable internal identifier where confidence permits.

```text
place_id
name(s)
geometry
landmarks
semantic type
observations
visit history
confidence
```

Names can change without changing place identity.

### 15. Place Boundaries

Place boundaries can be:

- geometric;
- semantic;
- topological;
- probabilistic.

For example, a kitchen may be represented as a polygon/3D volume plus a semantic room node.

Boundaries may be uncertain or overlapping.

### 16. Place Recognition

Place recognition may use:

- visual features;
- LiDAR geometry;
- semantic landmarks;
- spatial topology;
- GNSS;
- map matching;
- temporal context.

Recognition should produce a ranked hypothesis rather than an unconditional identity.

### 17. Global Localization

When Novi starts without a known pose, it should be able to attempt global localization.

NVIDIA's Visual Global Localization provides a relevant implementation candidate for matching stereo imagery against a previously generated map and recovering a global pose. citeturn0search4

Alternative LiDAR/global-localization methods should remain possible.

### 18. Place Recognition Confidence

Example:

```text
candidate: kitchen
confidence: 0.91
support:
  visual landmark
  map geometry
  recent trajectory
```

A low-confidence place match should not be treated as authoritative.

### 19. Landmarks

Landmarks are persistent or semi-persistent features useful for spatial reasoning.

Examples:

- doorway;
- furniture cluster;
- distinctive wall feature;
- tree;
- sign;
- building;
- charging station;
- known object.

Landmarks require confidence and observation history.

### 20. Landmark Lifecycle

```text
DETECTED
  ↓
CANDIDATE
  ↓
TRACKED
  ↓
ESTABLISHED
  ↓
STALE
  ↓
REMOVED / ARCHIVED
```

A transient object should not automatically become a permanent landmark.

### 21. Object-to-Place Relationships

Spatial memory should support relationships such as:

```text
object X
  located_in → kitchen

chair Y
  near → table Z

door A
  connects → hallway / bedroom
```

Relationships should retain observation time and confidence.

### 22. Topological Memory

A topological graph can represent connectivity without requiring perfect metric geometry.

```text
kitchen
  ↕
hallway
  ↕
living room
  ↕
front door
```

This can remain useful when localization is uncertain.

### 23. Metric + Topological Representation

Novi should combine:

```text
metric map
+
topological graph
+
semantic place graph
```

Metric maps answer precise spatial questions.

Topological maps answer connectivity questions.

Semantic maps answer meaning questions.

### 24. Spatial Episodes

Spatial events should form episodes such as:

```text
left home
 ↓
walked to park
 ↓
visited north path
 ↓
returned home
```

These episodes connect spatial memory to document 31's episodic/autobiographical architecture.

### 25. Visit Memory

A visit should be represented as a temporal-spatial episode.

Possible fields:

```text
visit_id
place_id
start_time
end_time
entry_pose
exit_pose
route_reference
observations
people/context where authorized
purpose/goal if known
confidence
```

### 26. First Visit

The first sufficiently verified visit to a place can become an autobiographical milestone.

Example:

```text
first_visit(place_id)
```

It must be grounded in actual spatial evidence.

### 27. Repeated Visits

Repeated visits can reveal stable patterns:

```text
place
 ↓
visits
 ↓
routes
 ↓
time patterns
 ↓
place knowledge
```

Patterns should remain probabilistic rather than deterministic.

### 28. Personal Map

Novi's personal map can include:

```text
places Novi has visited
routes Novi has taken
landmarks Novi has observed
areas Novi has explored
areas not yet explored
places with high uncertainty
changes observed over time
```

This is more than a navigation map.

### 29. Exploration Memory

Novi should distinguish:

```text
KNOWN
PARTIALLY KNOWN
UNKNOWN
RECENTLY CHANGED
UNRELIABLE
INACCESSIBLE
```

This supports autonomous exploration without assuming that unknown means dangerous or that known means permanently safe.

### 30. Change Detection

The spatial model must detect environmental change.

Examples:

```text
chair moved
furniture rearranged
door closed/open
new obstacle
construction
seasonal vegetation change
park path blocked
```

Change detection should create observations first, not immediately rewrite long-term maps.

### 31. Persistent vs Dynamic Objects

The system should classify spatial entities by persistence.

```text
STATIC
SEMI_STATIC
DYNAMIC
UNKNOWN
```

A person walking through a room should not become part of the permanent room geometry.

### 32. Map Versioning

Maps must be versioned.

```text
map_v1
  ↓
map_v2
  ↓
map_v3
```

Map versions should retain:

- creation time;
- sensor/model provenance;
- calibration/configuration;
- source data references;
- optimization version;
- confidence/quality metrics.

### 33. Map Corrections

Corrections should be represented as changes rather than silently rewriting history.

Example:

```text
landmark believed at A
        ↓
new evidence
        ↓
landmark position corrected to B
```

Historical observations retain their original estimates.

### 34. Map Confidence

Confidence should exist at multiple levels:

```text
map confidence
region confidence
landmark confidence
pose confidence
relationship confidence
```

A high-confidence global map does not imply every landmark is accurate.

### 35. Localization Failure

When localization confidence falls:

```text
NORMAL
 ↓
DEGRADED
 ↓
UNCERTAIN
 ↓
LOST
```

Novi should respond according to autonomy/safety policy.

Possible responses:

- slow/stop;
- re-localize;
- use another sensor;
- return to known landmark;
- request assistance;
- wait for better observations.

### 36. Kidnapped-Robot Problem

Novi may be physically moved while powered or after restart.

The spatial system must detect disagreement between expected and observed pose.

Global relocalization mechanisms are important here; NVIDIA documents visual global localization specifically for recovering an initial global pose against a prebuilt map. citeturn0search2turn0search4

### 37. Spatial Memory Retrieval

Queries should support:

```text
Where have I been?
Where have I seen this object?
What happened here before?
What routes do I know?
What places are nearby?
When was I last here?
What changed since my last visit?
Where did I experience X?
```

Retrieval should combine spatial, temporal and semantic ranking.

### 38. Spatial Query Types

Examples:

```text
nearest(place)
visited(place)
last_visited(place)
visited_between(time)
observed_at(entity, place)
route_between(A, B)
changes_since(place, time)
unknown_regions(area)
```

These are conceptual interfaces; exact APIs belong to the API architecture.

### 39. Spatial Context for Cognition

The cognitive workspace should be able to receive a compact spatial context:

```text
current place
current pose
nearby landmarks
nearby objects
known routes
local obstacles
map confidence
localization confidence
recent spatial history
```

The entire map should not be placed into the LLM context.

### 40. Spatial Memory and Prediction

The world model can produce expectations such as:

```text
kitchen normally contains charging station
front door normally connects home ↔ outside
known route normally takes N minutes
```

Prediction remains separate from observation.

### 41. Spatial Prediction Error

Example:

```text
Expected:
charging station at location A

Observed:
station missing

        ↓
prediction error
        ↓
investigate
```

Only after sufficient evidence should long-term spatial knowledge change.

### 42. Environmental Change Episodes

Significant spatial changes can form episodes:

```text
room rearranged
construction started
new landmark appeared
route became blocked
```

These connect spatial memory with episodic memory and learning.

### 43. GPS/GNSS History

When permitted, Novi can maintain a trajectory history.

The trajectory should support:

- sampled positions;
- uncertainty;
- timestamps;
- route segmentation;
- place transitions;
- visit detection.

Raw high-rate GNSS data should not necessarily become permanent semantic memory.

### 44. Outdoor Journey Memory

An outdoor journey can become an episode:

```text
home
 ↓
street
 ↓
park
 ↓
shop
 ↓
home
```

Novi can later retrieve:

- route;
- places visited;
- duration;
- observations;
- anomalies;
- map changes.

### 45. Indoor/Outdoor Transition

Transitions such as leaving/entering the home should be explicit spatial events when sufficiently detected.

```text
INDOOR
 ↓
EXIT TRANSITION
 ↓
OUTDOOR
```

Localization source weighting may change during the transition.

### 46. Multi-Map Architecture

Novi may need multiple maps:

```text
home map
local neighborhood map
large outdoor map
temporary exploration map
semantic map
navigation costmap
```

These should be linked but not forced into one enormous representation.

### 47. Map Memory Budget

Map storage must obey resource governance.

Old or low-value map data may be:

- compressed;
- summarized;
- archived;
- downsampled;
- removed when policy permits.

Critical navigation data remains protected.

### 48. Storage Strategy

A practical architecture may use:

```text
SQLite
  semantic spatial metadata

files / object storage
  point clouds / map artifacts / trajectories

specialized indexes
  spatial retrieval

ROS map formats
  navigation interoperability
```

The exact implementation should be benchmarked on Jetson storage and workload.

### 49. Synchronization

Spatial state may synchronize selectively.

Potentially synchronized:

- approved semantic places;
- map versions;
- selected landmarks;
- route knowledge.

Robot-local:

- current pose;
- current sensor state;
- transient obstacles;
- local thermal state.

All synchronization is subject to privacy and conflict policy.

### 50. Conflict Resolution

Spatial conflicts should preserve competing evidence.

Example:

```text
Observation A:
door at position X

Observation B:
door at position Y

        ↓
conflict
        ↓
check calibration / time / map version
        ↓
resolve or maintain uncertainty
```

Novi must not simply select the newest observation without considering evidence quality.

### 51. Privacy

Spatial memory can be highly sensitive.

Examples:

- home layout;
- exact home location;
- frequently visited locations;
- routes;
- routines;
- locations of people.

Access and synchronization must therefore be privacy-controlled.

### 52. Offline-First Requirement

Core spatial memory must work without:

- Wi-Fi;
- Bluetooth;
- cloud APIs;
- remote map services.

External map data can be an optional enhancement.

### 53. Cloud Boundary

Cloud mapping services should only be considered when a required capability cannot reasonably be provided locally and after explicit privacy/security evaluation.

The default architecture remains local.

### 54. Map Integrity

Map artifacts should have integrity metadata.

Potential mechanisms:

- hashes;
- version IDs;
- provenance;
- source dataset IDs;
- creation software/version;
- calibration identifiers.

A corrupted or mismatched map should be rejected or quarantined.

### 55. Spatial Event Lineage

Every important spatial memory should be traceable to events.

```text
sensor observation
 ↓
pose estimate
 ↓
map update
 ↓
landmark/place update
 ↓
spatial memory
```

This connects directly to document 30.

### 56. Spatial Autobiography

Novi's autobiography can contain grounded spatial milestones:

```text
first outdoor trip
first visit to park
first known route
first time returning home autonomously
new place discovered
significant map change
```

These must be generated from actual event/visit evidence.

### 57. Place Preferences

Repeated spatial behavior may produce preference candidates.

Example:

```text
Novi repeatedly chooses route A
        ↓
preference candidate
        ↓
consider alternative explanations
        ↓
validate over repeated episodes
```

A preference is not proof that Novi intrinsically likes a location.

### 58. Spatial Learning

Novi can learn:

- travel times;
- landmark reliability;
- route reliability;
- typical environmental changes;
- localization quality by area;
- sensor-specific weaknesses in locations.

Learning must retain evidence and uncertainty.

### 59. Active Mapping

Novi may intentionally explore unknown areas to improve its map.

```text
unknown region
   ↓
information gain
   ↓
risk/cost
   ↓
exploration decision
   ↓
observation
   ↓
map update
```

Exploration remains subordinate to safety and authorized goals.

### 60. Spatial Attention

Spatial attention should prioritize:

- current navigation corridor;
- nearby hazards;
- uncertain localization areas;
- goal-relevant landmarks;
- unexpected changes;
- unexplored areas when exploration is active.

This integrates with document 35.

### 61. Spatial Failure Modes

The architecture must handle:

- GPS loss;
- GNSS multipath;
- camera failure;
- LiDAR failure;
- IMU drift;
- calibration errors;
- map corruption;
- stale maps;
- dynamic environments;
- localization jumps;
- false place recognition;
- duplicate places;
- incorrect loop closure;
- sensor time synchronization errors;
- moved landmarks;
- insufficient storage.

### 62. Sensor Time Synchronization

Spatial fusion depends strongly on temporal alignment.

Novi must retain timestamps and synchronization quality for sensor observations.

NVIDIA's current VSLAM documentation exposes explicit synchronization parameters and camera-count requirements, reinforcing that synchronized inputs are an implementation concern rather than an incidental detail. citeturn0search3

### 63. Loop Closure

Loop closure can improve map consistency when Novi revisits known areas.

However, incorrect loop closures can cause large map errors.

Therefore loop-closure decisions require validation and monitoring.

NVIDIA's Visual SLAM implementation explicitly uses loop closures and notes that they can cause pose/map corrections, which is why Novi must treat such changes as significant state transitions. citeturn0search5

### 64. Map Lifecycle

```text
CREATED
  ↓
VALIDATING
  ↓
ACTIVE
  ↓
UPDATED
  ↓
SUPERSEDED
  ↓
ARCHIVED
```

Corrupted or untrusted maps can enter:

```text
QUARANTINED
```

### 65. Spatial Knowledge Lifecycle

A semantic claim such as:

> "The charging station is in the living room"

should follow:

```text
observation
 ↓
candidate relationship
 ↓
validation
 ↓
spatial knowledge
 ↓
re-observation
 ↓
confirmed / changed / stale
```

### 66. Spatial Memory vs Navigation

Navigation asks:

> How do I get there safely now?

Spatial memory asks:

> What do I know about this place and my history there?

They share data but have different priorities.

### 67. Navigation Map vs Personal Map

```text
NAVIGATION MAP
optimized for safe movement

PERSONAL MAP
optimized for Novi's accumulated spatial understanding
```

The personal map may contain memories and relationships that are irrelevant to immediate navigation.

### 68. Spatial Context and Human Interaction

Spatial memory can support social context:

```text
person encountered
  at → kitchen
  time → evening
  during → conversation episode
```

This information remains subject to privacy controls and must not automatically imply a routine.

### 69. Spatial Context for Personality

Repeated experiences at places can influence interaction style only through the governed learning architecture.

For example:

```text
repeated pleasant outdoor episodes
        ↓
experience evidence
        ↓
possible preference candidate
```

The system must not infer a stable personality trait from one event.

### 70. Testing Strategy

Test at minimum:

- indoor localization;
- outdoor localization;
- GNSS loss;
- GNSS recovery;
- map creation;
- map loading;
- global relocalization;
- loop closure;
- dynamic obstacles;
- moved furniture;
- changed rooms;
- landmark recognition;
- place recognition;
- duplicate place prevention;
- spatial memory retrieval;
- visit detection;
- route history;
- map versioning;
- map corruption;
- storage exhaustion;
- sensor time skew;
- sensor failure;
- calibration changes;
- restart/recovery;
- offline operation;
- privacy filtering;
- synchronization conflicts;
- long-duration mapping.

### 71. Long-Term Evaluation

Because Novi is intended to evolve continuously, spatial evaluation must include months/years of accumulated state in addition to short navigation benchmarks.

Metrics should include:

- localization accuracy;
- relocalization success;
- map consistency;
- place-recognition precision/recall;
- false place merges;
- duplicate places;
- map drift;
- change-detection accuracy;
- memory retrieval usefulness;
- storage growth;
- recovery time;
- computational cost;
- thermal/power cost.

### 72. Architectural Invariants

1. Map and world are not the same thing.
2. Spatial state always carries coordinate-frame and temporal provenance where relevant.
3. Localization includes uncertainty.
4. GNSS is optional for core spatial functionality.
5. Indoor operation must work without GPS.
6. Navigation maps and personal spatial memory remain distinct.
7. Dynamic objects must not silently become permanent map geometry.
8. Historical spatial observations remain traceable.
9. Map updates are versioned.
10. Spatial conflicts preserve competing evidence until resolved.
11. Place recognition is probabilistic until sufficiently validated.
12. Spatial memory works offline.
13. Spatial data is privacy-sensitive and access-controlled.
14. High-rate raw sensor streams are not automatically permanent memory.
15. The LLM is not the authoritative source of geometry or pose.
16. Hardware/sensor implementations remain replaceable behind canonical interfaces.
17. NVIDIA Isaac ROS is a candidate accelerator, not an architectural lock-in.
18. Spatial learning must be evidence-backed.
19. Active exploration remains subject to safety, authorization and resource governance.
20. A stale map must never be treated as guaranteed current reality.

## Final Principle

> **Novi should not merely know where it is. It should build a grounded, evolving understanding of the places it inhabits and visits, remember what happened there, recognize what has changed, understand uncertainty, and use that accumulated spatial experience to become better at navigating and understanding its world.**

The spatial architecture therefore becomes the long-term bridge between Novi's physical body and its cognitive history: sensors produce evidence, localization establishes where Novi is, maps describe geometry, place memory gives locations meaning, episodic memory records experiences, and the predictive world model learns what Novi can reasonably expect next.
