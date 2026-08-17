# 23 — Memory Spatial Memory and Place History

## Status

**DESIGN — V1 HIGH-LEVEL / DETAILED ARCHITECTURE**

## Purpose

Define how Novi represents places it knows about, physically visits, maps, revisits, and remembers. Spatial memory connects global positioning, local maps, place recognition, routes, objects, visits, experiences, and long-term knowledge.

> **Novi must distinguish where it is, what it has mapped, what it has visited, what it knows about a place, and what it remembers happening there.**

This document complements the robotics navigation stack. SLAM/localization estimates pose and builds maps; spatial memory turns physical experience into persistent semantic and episodic knowledge.

## 1. Spatial Representation Layers

Novi should maintain complementary representations:

```text
GLOBAL GEOSPATIAL
GNSS coordinates / outdoor world
        ↓
METRIC MAP
geometry / occupancy / point clouds / trajectories
        ↓
TOPOLOGICAL MAP
rooms / places / entrances / paths / connections
        ↓
SEMANTIC MAP
objects / landmarks / people / functions
        ↓
EPISODIC SPATIAL MEMORY
visits / events / experiences anchored to place and time
        ↓
SPATIAL KNOWLEDGE
persistent facts and learned patterns about places
```

No single representation is sufficient.

## 2. Global vs Local Position

Novi must distinguish:

- global position: latitude/longitude/altitude;
- local position: x/y/z within a map;
- relative position: position relative to another object, place, or robot frame.

GNSS provides a global reference when available. SLAM and local state estimation provide local spatial understanding.

Indoor operation must not depend on GNSS.

## 3. GNSS / GPS

Outdoor spatial memory should accept multi-constellation GNSS where supported, including GPS, Galileo, GLONASS and BeiDou.

A GNSS observation should retain:

- receiver identity;
- acquisition timestamp;
- latitude/longitude;
- altitude where valid;
- estimated accuracy;
- fix type;
- constellation/satellite quality where available;
- receiver health;
- correction/source status;
- coordinate reference information.

RTK is an optional future capability and must be justified by actual accuracy requirements.

Novi must never treat a GNSS fix as exact merely because coordinates were returned.

## 4. Indoor Localization

When GNSS is unavailable, Novi should use complementary local systems such as:

- LiDAR SLAM;
- visual SLAM;
- visual-inertial odometry;
- wheel/actuator odometry;
- IMU;
- depth sensing;
- landmark/place recognition.

Candidate existing solutions must be evaluated before implementing equivalent functionality, including ROS 2 Nav2/SLAM Toolbox and NVIDIA Isaac ROS Visual SLAM.

## 5. Spatial State Fusion

```text
GNSS ──────┐
LiDAR ─────┤
Cameras ───┤
IMU ───────┤──→ STATE ESTIMATION → ROBOT POSE
Encoders ──┤                         ↓
Depth ─────┘                    SPATIAL MEMORY
```

Memory must preserve pose provenance and uncertainty.

## 6. Place Identity

A place is a persistent semantic concept, not merely a coordinate.

Examples:

- home;
- kitchen;
- bedroom;
- park entrance;
- street intersection;
- favorite bench;
- trail section.

A place may contain spatial extent, representative coordinates, local-map regions, semantic type, aliases, landmarks, visit history, memories, and confidence.

## 7. Known vs Visited vs Mapped

These states are independent:

```text
KNOWN   = Novi has information about the place
VISITED = Novi physically experienced the place
MAPPED  = Novi has a spatial representation of the place
```

Novi must never claim physical experience merely because it has information about a place.

## 8. Place Recognition

Place recognition determines whether current observations correspond to a known place. Evidence may include:

- visual landmarks;
- LiDAR geometry;
- semantic objects;
- GNSS proximity;
- learned descriptors;
- temporal context;
- route context.

Recognition produces a hypothesis with confidence and provenance, not an unconditional identity.

## 9. Metric Maps

Maps may contain:

- occupancy grids;
- point clouds;
- depth geometry;
- traversability;
- trajectories;
- landmarks.

The final choice between 2D, 3D or hybrid mapping must be benchmarked against Novi's actual hardware and environments.

## 10. Semantic Maps

A semantic map adds meaning to geometry:

```text
metric:
wall at position X

semantic:
wall belongs to kitchen

knowledge:
kitchen contains refrigerator
```

Semantic mapping must remain linked to geometric evidence.

## 11. Topological Map

Novi should maintain relationships between places:

```text
Home
 ├── Hallway
 │    ├── Kitchen
 │    └── Bedroom
 └── Front Door
       ↓
     Street
       ↓
     Park
```

Topology remains useful when precise metric localization is temporarily unavailable.

## 12. Place Graph

The knowledge graph may represent:

```text
Home --contains--> Kitchen
Home --contains--> Bedroom
Home --connected_to--> Garden
Park --contains--> Lake
Park --visited_at--> Visit-847
```

Spatial memory therefore integrates with Novi's existing relationship/knowledge-graph architecture.

## 13. Visit Episodes

A visit is an episode, not a boolean:

```text
Visit 42
  place = Park
  started = T1
  ended = T2
  entry_position = P1
  exit_position = P2
  route = R7
  observations = [...]
  memories = [...]
```

This lets Novi remember what happened during a visit, not merely that it occurred.

## 14. Spatially Anchored Memory

Memories may be associated with:

- exact position;
- region;
- place;
- route segment;
- object location;
- room;
- geofence;
- visit episode.

Example:

```text
Memory: "We saw a dog here."
Place: Park / north path
Time: T1
Location uncertainty: ±R
```

## 15. Spatial Uncertainty

Location must never be represented more precisely than the evidence supports.

If GNSS accuracy is approximately 8 m, Novi cannot infer an exact doorway without additional evidence.

Uncertainty must propagate into place recognition, retrieval, and knowledge promotion.

## 16. Indoor / Outdoor Transition

Novi should recognize transitions between local and global environments:

```text
Home local map
      ↓
Front door
      ↓
Outdoor localization
      ↓
Street / global map
```

The transition itself may become a spatial event.

## 17. Global-to-Local Alignment

When both GNSS and local mapping are available, Novi may maintain a transform between global and local frames.

That transform must be versioned and carry uncertainty. Rebuilding a local map must not silently invalidate historical spatial references.

## 18. Map Versioning

Maps evolve:

```text
Home map v1 → v2 → v3
```

Changes may result from furniture movement, construction, seasonal conditions, improved calibration, or improved SLAM.

Historical memories remain associated with the spatial representation that produced them.

## 19. Dynamic Environment

Novi must distinguish persistent structure from temporary entities:

```text
wall       → persistent structure
chair      → movable object
person     → dynamic entity
pet        → dynamic entity
parked car → temporary observation
```

Dynamic observations must not automatically corrupt long-term maps.

## 20. Map Change Detection

When revisiting a place, compare previous state with current observations:

```text
previous map/state
        vs
current observations
        ↓
unchanged / minor change / significant change / unknown
```

Changes should remain observations until sufficiently verified.

## 21. "Have I Been Here Before?"

The query should combine:

- current observations;
- place recognition;
- map geometry;
- GNSS proximity where available;
- landmarks;
- route context;
- uncertainty.

Possible answers:

- yes, confidently;
- probably;
- uncertain;
- no evidence of previous visit.

Lack of evidence must not be interpreted as proof that Novi has never visited.

## 22. "What Happened Here?"

Spatial retrieval should combine:

- current place;
- spatial radius/region;
- route segment;
- object/location relationships;
- time;
- visit episode;
- semantic relevance.

```text
current position
      ↓
nearby spatial memories
      ↓
distance + relevance + time + confidence + provenance
      ↓
retrieval
```

## 23. Spatial Retrieval

A memory query can combine:

```text
semantic similarity
+
spatial proximity
+
temporal relevance
+
place identity
+
confidence
+
provenance
```

Spatial context is a first-class retrieval dimension.

## 24. Routes and Trails

Novi may retain traversed routes as experiences:

```text
Route 17
  Home → Park
  distance
  duration
  conditions
  observations
  incidents
```

Repeated routes may produce knowledge such as frequently used paths or blocked segments, subject to current safety/navigation constraints.

## 25. Spatial Learning

Repeated visits can strengthen place representations:

```text
Visit 1  → rough place hypothesis
Visit 5  → stable landmark recognition
Visit 20 → high-confidence place model
```

Repeated correlated observations must not be mistaken for independent evidence.

## 26. Spatial Knowledge Promotion

One observation should generally remain an observation. Repeated, independently supported evidence can become knowledge.

Example:

```text
Observation → park contains lake
Repeated independent visits → confirmed
Knowledge → park contains lake
```

The knowledge claim retains its supporting evidence.

## 27. Spatial Conflict Resolution

Examples:

```text
old map: table here
new map: table moved

GNSS: position A
SLAM: position B

recognizer: Park A
recognizer: Park B
```

Use document 20's conflict architecture. Preserve competing evidence until a valid resolution exists.

## 28. Map Synchronization

Maps may be synchronized between authorized replicas, but synchronization must not bypass canonical memory state.

Maps should be versioned and integrity checked. Derived maps may be regenerated when necessary.

## 29. Privacy

Location history can expose highly sensitive information.

Spatial memory therefore requires:

- retention policy;
- deletion;
- access control;
- synchronization restrictions;
- protection of home coordinates;
- protection of recurring routines;
- privacy-safe diagnostics.

A private home map must not automatically become remotely accessible.

## 30. Offline Operation

Spatial memory must work without network access.

Offline Novi must still be able to:

- localize where possible;
- build/update local maps;
- recognize known places;
- store visit episodes;
- retrieve spatial memories;
- record trajectories;
- synchronize later.

GNSS does not require Internet access for basic positioning, although correction services can improve accuracy.

## 31. Storage Strategy

Separate:

```text
high-frequency sensor data → controlled retention
maps                    → long-lived derived artifacts
place metadata           → long-lived semantic state
visit episodes           → policy-driven retention
spatial memories         → long-lived when valuable
```

Raw sensor streams must not automatically become permanent memory.

## 32. Failure and Degradation

If GNSS fails:

```text
outdoor global positioning degraded
local navigation may continue
```

If LiDAR fails, mapping/localization may degrade while other modalities compensate. If cameras fail, visual place recognition degrades.

The spatial system must expose these limitations to autonomy and cognition.

## 33. Existing Solutions

Novi should reuse mature open/local robotics solutions where they satisfy requirements instead of rebuilding equivalent functionality.

Candidates to evaluate include:

- ROS 2 Nav2;
- SLAM Toolbox;
- AMCL;
- NVIDIA Isaac ROS Visual SLAM;
- cuVSLAM/Isaac ROS components where appropriate;
- open-source place-recognition systems;
- standard ROS coordinate-frame and sensor interfaces.

These are candidates, not permanent commitments. Final selection requires benchmarking on Novi's actual sensors, environments and Jetson target.

## 34. Testing

Test at minimum:

- indoor localization;
- outdoor GNSS localization;
- GNSS loss and multipath;
- map reuse;
- loop closure;
- place recognition;
- changed furniture;
- lighting changes;
- seasonal changes;
- people/pets;
- moved objects;
- map version migration;
- spatial uncertainty;
- incorrect place recognition;
- conflicting localization sources;
- offline operation;
- repeated visits;
- synchronization;
- location-history deletion;
- privacy enforcement.

## 35. Metrics

Measure:

- localization error;
- place-recognition precision/recall;
- false place matches;
- map drift;
- loop-closure correctness;
- map-change detection;
- spatial-memory retrieval precision;
- visit reconstruction quality;
- uncertainty calibration;
- CPU/GPU/memory usage;
- latency;
- storage growth;
- recovery time.

## 36. Architectural Invariants

1. Global and local position are distinct.
2. GNSS is not a substitute for local mapping.
3. Local mapping works without Internet access.
4. Known, visited and mapped are distinct states.
5. A place is a semantic entity, not merely a coordinate.
6. Spatial memories retain temporal/spatial provenance.
7. Spatial uncertainty is preserved.
8. Historical maps are not silently rewritten.
9. Dynamic objects do not automatically corrupt persistent maps.
10. Place recognition is probabilistic.
11. Spatial memory integrates with general provenance and conflict resolution.
12. Location history is privacy-sensitive.
13. Derived maps are not automatically canonical semantic truth.
14. Mature open/local solutions should be reused where suitable.
15. Spatial cognition remains functional without Wi-Fi, Bluetooth or cloud services.

## 37. Final Principle

> **Novi should build a persistent understanding of the places it physically experiences, not merely store GPS coordinates.**

The intended result is a robot that connects global location, local geometry, semantic places, routes, objects, visits and experiences into coherent spatial memory while remaining uncertain whenever the evidence does not justify certainty.
