# 44 — Memory Spatial-Temporal Reasoning and Trajectory Memory

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi represents, stores, retrieves and reasons about movement through space and time. This document connects localization, maps, trajectories, visits, places, episodes, goals and observations so Novi can answer not only **where** something happened, but also **when, for how long, along which route, under what conditions, and what happened during the journey**.

## Core Principle

> **Novi's spatial memory must be temporal: a location without time is incomplete, and a trajectory without provenance is not reliable history.**

---

## 1. Spatial-Temporal Model

Novi should represent physical experience as:

```text
ENTITY
  + LOCATION
  + TIME
  + STATE
  + UNCERTAINTY
  + PROVENANCE
```

A place is not simply a coordinate. A trajectory is not simply a list of coordinates.

---

## 2. Coordinate vs Place

Separate:

```text
POSITION
exact/estimated geometric location

PLACE
semantic region/location with identity

LANDMARK
recognizable spatial reference

ZONE
operational/geometric area
```

Example:

```text
position → 51.x, 0.x
zone → garden
place → home
landmark → front door
```

---

## 3. Time Model

Spatial events should distinguish:

- occurred time;
- recorded time;
- estimated time;
- time interval;
- duration;
- time uncertainty;
- clock source.

Novi must not treat a timestamp with unknown clock quality as perfectly accurate.

---

## 4. Trajectory

A trajectory is a time-ordered representation of movement through space.

Conceptually:

```text
pose(t0)
   ↓
pose(t1)
   ↓
pose(t2)
   ↓
...
   ↓
pose(tN)
```

The underlying representation may be compressed or sampled, but it must preserve sufficient information for required spatial reasoning.

---

## 5. Pose Provenance

Each important pose estimate should be traceable to its localization system and relevant sensors.

Possible sources:

- visual-inertial odometry;
- LiDAR localization;
- wheel/actuator odometry;
- GNSS;
- map matching;
- fused state estimation.

The source and confidence must remain available for important derived memories.

---

## 6. Coordinate Frames

Trajectory records must identify coordinate frames.

Examples:

```text
map
odom
base
sensor frames
GNSS/global frame
```

A trajectory must not be interpreted correctly without knowing its frame semantics and transform history.

---

## 7. Trajectory Segments

Long trajectories should be represented as segments rather than one unbounded object.

```text
trip_001
 ├── segment_001
 ├── segment_002
 └── segment_003
```

Segments can correspond to:

- continuous motion;
- different localization regimes;
- different environments;
- pauses;
- route branches;
- transport transitions.

---

## 8. Visit

A visit represents a temporally bounded presence at a place or region.

Conceptually:

```text
visit
 ├── place_id
 ├── arrival
 ├── departure
 ├── duration
 ├── entry route
 ├── exit route
 ├── observations
 ├── actions
 └── uncertainty
```

A visit is a derived semantic object, not simply a GPS point.

---

## 9. Visit Detection

A visit can be inferred from:

- localization;
- place recognition;
- dwell time;
- trajectory behavior;
- semantic observations.

The system must allow:

```text
visit confirmed
visit probable
visit uncertain
```

---

## 10. Arrival and Departure

Arrival/departure events should be explicit when detected.

```text
place.exit
place.entry
```

They should retain evidence and uncertainty.

---

## 11. Route

A route is an intended or observed path between locations.

Distinguish:

```text
planned route
actual route
preferred route
historical route
hypothetical route
```

A planned route must never be stored as evidence that it was actually travelled.

---

## 12. Route Execution

A route execution should link:

```text
goal
 ↓
planned route
 ↓
actual trajectory
 ↓
outcome
```

This enables Novi to learn route reliability without confusing plans with experience.

---

## 13. Route Deviation

Novi should detect when actual movement diverges from a planned route.

Possible causes:

- obstacle;
- user interruption;
- localization error;
- new route choice;
- safety intervention;
- environmental change.

Deviation itself should not automatically be classified as failure.

---

## 14. Temporal Episodes

Spatial-temporal data should connect to episodic memory.

```text
trajectory
 + observations
 + goals
 + actions
 + outcomes
 + time
        ↓
spatial episode
```

This allows Novi to remember a journey as an experience rather than merely a line on a map.

---

## 15. Journey Memory

A journey can include:

- origin;
- destination;
- route;
- stops;
- people encountered;
- objects encountered;
- environmental conditions;
- actions;
- failures;
- notable events;
- outcome.

Large raw sensor data should remain referenced rather than duplicated unnecessarily.

---

## 16. Temporal Place History

A place should support historical state.

Example:

```text
HOME

2027-01
  furniture arrangement A

2027-06
  furniture arrangement B

2028-02
  new obstacle/landmark
```

Novi can then reason about change over time.

---

## 17. Change Detection

Spatial change can be detected by comparing observations over time.

```text
historical map
      +
current observation
      ↓
change candidate
      ↓
verification
      ↓
spatial update
```

A temporary object should not automatically become permanent map structure.

---

## 18. Persistent vs Temporary Objects

Novi should distinguish:

```text
persistent landmark
semi-persistent object
temporary obstacle
moving object
unknown observation
```

Persistence requires repeated evidence or other reliable confirmation.

---

## 19. Temporal Prediction

Spatial history can support predictions:

```text
place + time context
        ↓
expected state
```

Examples:

- expected route congestion;
- likely occupancy patterns;
- known recurring obstacles;
- typical visit duration;
- normal environmental conditions.

Predictions remain probabilistic and revisable.

---

## 20. Recurrence

Repeated trajectories can reveal patterns.

```text
Monday 08:00
Monday 08:05
Monday 08:10
...
```

Novi may learn recurring patterns only under the appropriate privacy and confidence policies.

A pattern is not proof that the future will repeat exactly.

---

## 21. Time-of-Day Context

Spatial memories may include context such as:

- morning;
- afternoon;
- evening;
- night;
- weekday/weekend;
- season.

Exact timestamps remain the authoritative temporal evidence.

---

## 22. Duration Reasoning

Novi should distinguish:

```text
arrival time
departure time
dwell duration
travel duration
idle duration
uncertain duration
```

Durations derived from uncertain timestamps must preserve uncertainty.

---

## 23. Temporal Ordering

When exact times are unavailable, Novi can preserve partial ordering.

Example:

```text
A happened before B
B happened before C
```

without inventing exact timestamps.

---

## 24. Event-Time vs Processing-Time

As established in the event architecture:

```text
occurred_at
≠
recorded_at
```

This is particularly important for offline journeys where data may be uploaded or processed later.

---

## 25. Offline Spatial Operation

Novi must remain capable of local spatial reasoning without Wi-Fi/Bluetooth/cloud.

Local capabilities may include:

- localization;
- local mapping;
- trajectory recording;
- place recognition;
- local route memory;
- local spatial retrieval.

Cloud synchronization is optional.

---

## 26. GNSS Integration

GNSS can provide global positioning outdoors but should not be treated as universally available or perfectly accurate.

Novi should represent:

- fix quality;
- accuracy estimate;
- satellite/solution state where available;
- signal availability;
- coordinate reference;
- timestamp quality.

Indoor operation must not depend on GNSS.

---

## 27. Indoor/Outdoor Transition

Novi should detect and model transitions such as:

```text
home interior
   ↓
front door
   ↓
outside
   ↓
street
```

Different localization sources may become authoritative at different points.

The transition itself can become a spatial event.

---

## 28. Multi-Source Localization

Novi may combine:

```text
VIO
LiDAR
GNSS
odometry
place recognition
map matching
```

The fusion layer must retain source quality and uncertainty.

---

## 29. Localization Failure

When localization becomes uncertain:

```text
confidence ↓
      ↓
slow/stop risky movement where required
      ↓
active perception / relocalization
      ↓
recover or degrade safely
```

A low-confidence trajectory must not silently become precise autobiographical history.

---

## 30. Trajectory Compression

High-rate trajectories can be compressed using controlled methods such as:

- temporal sampling;
- geometric simplification;
- keyframes;
- segment summaries.

Compression must preserve the information required for safety, audit and intended memory queries.

---

## 31. Keyframes

Important trajectory keyframes may correspond to:

- place transitions;
- landmarks;
- significant turns;
- action events;
- anomalies;
- localization changes;
- user interactions.

Keyframes provide efficient retrieval without storing every sample in the semantic memory layer.

---

## 32. Spatial-Temporal Indexing

Useful indexes include:

- place ID;
- spatial region;
- time interval;
- event ID;
- trajectory ID;
- visit ID;
- entity ID;
- landmark ID.

Queries should support combinations such as:

```text
where + when
where + what
when + what
where + who
where + goal
```

---

## 33. Queries Novi Should Eventually Support

Examples:

```text
Where was I yesterday at 18:00?
Have I been here before?
What route did I take last time?
What changed here since my previous visit?
How long did I stay?
What happened during that journey?
Which places have I never explored?
Where did I last see object X?
When did I first discover this place?
```

Answers must include uncertainty where required.

---

## 34. Temporal Retrieval

Retrieval should rank evidence by:

- spatial relevance;
- temporal relevance;
- semantic relevance;
- provenance;
- confidence;
- recency where appropriate;
- task relevance.

Recency must not automatically beat stronger historical evidence.

---

## 35. Historical Reconstruction

Novi should be able to reconstruct an episode from:

```text
events
+ trajectories
+ visits
+ observations
+ actions
+ memory references
```

The reconstruction must distinguish recorded evidence from inferred narrative.

---

## 36. Uncertainty Propagation

Spatial uncertainty should propagate into derived memories.

Example:

```text
pose uncertainty high
      ↓
place association uncertain
      ↓
visit confidence reduced
      ↓
autobiographical claim qualified
```

Do not discard uncertainty during projection.

---

## 37. Map Versioning

Spatial reasoning must identify map versions where relevant.

```text
map_v10
 ↓
map_v11
 ↓
map_v12
```

Historical trajectories should retain the map/localization context used to interpret them.

---

## 38. Map Change vs World Change

A difference between maps can arise from:

- actual environmental change;
- localization error;
- sensor error;
- mapping algorithm change;
- coordinate-frame change.

Novi must not assume every difference is a physical-world change.

---

## 39. Spatial Relationships

Novi should represent relationships such as:

```text
inside
outside
near
far
left_of
right_of
in_front_of
behind
above
below
connected_to
between
along_route
```

These should be grounded in coordinate frames and observations where possible.

---

## 40. Route Learning

Repeated route outcomes can support route preferences.

Example:

```text
route A
  travel time: low
  obstacle frequency: low

route B
  travel time: high
  obstacle frequency: high
```

Novi can learn a preference for A while keeping the underlying evidence accessible.

---

## 41. Route Preference vs Route Truth

A preferred route is not necessarily the shortest or safest route under every condition.

Current planning must recompute against current state.

Historical preference is a planning input, not a command.

---

## 42. Personal Exploration Map

Novi should maintain a derived representation of explored vs unexplored areas where appropriate.

```text
known
partially known
uncertain
unexplored
```

This supports exploration planning and curiosity.

---

## 43. Exploration History

Exploration episodes should record:

- area explored;
- time;
- route;
- observations;
- discoveries;
- confidence;
- safety events;
- outcome.

Repeated exploration can improve the map and world model.

---

## 44. Place Familiarity

Place familiarity can be derived from:

- number of visits;
- recency;
- spatial coverage;
- successful localization;
- known landmarks;
- stable observations.

Familiarity is not certainty.

---

## 45. Temporal Familiarity

Novi may know:

```text
I know this place well during daytime.
I have little evidence about this place at night.
```

This is more useful than one global familiarity score.

---

## 46. Social-Spatial Context

Where privacy policy permits, spatial episodes may link to social context:

```text
place
 + people observed
 + interactions
 + time
```

These links must respect the social-memory and privacy architecture.

---

## 47. Action-Spatial Context

Actions can be associated with location and time:

```text
at kitchen
at 19:04
speech action
```

This helps Novi understand outcomes in physical context.

---

## 48. Spatial Prediction Error

A mismatch between predicted and observed spatial state should generate a prediction-error candidate.

Examples:

```text
expected door position
vs
observed door position

expected route clear
vs
obstacle detected
```

The mismatch should trigger investigation proportional to risk.

---

## 49. Memory Promotion

Spatial observations can become memories when they are:

- repeated;
- salient;
- goal-relevant;
- surprising;
- useful for navigation;
- useful for future prediction;
- important to the user's explicit request.

Admission remains governed by the memory policy.

---

## 50. Forgetting Spatial Data

Not every trajectory should be retained forever.

Retention should distinguish:

```text
raw trajectory
semantic route
visit summary
landmark memory
long-term autobiographical significance
```

Privacy and storage policy remain authoritative.

---

## 51. Privacy

Location history can be highly sensitive.

Spatial memories may reveal:

- home location;
- routines;
- travel patterns;
- time away from home;
- places visited;
- social associations.

Access, retention and synchronization must therefore be tightly controlled.

---

## 52. Security

An attacker must not be able to silently rewrite spatial history to manipulate Novi's beliefs about where it has been.

Integrity protection is required for critical spatial records and synchronization.

---

## 53. Synchronization

Spatial history may be synchronized selectively between local stores or approved devices.

Conflict resolution must distinguish:

```text
same journey duplicated
vs
conflicting trajectories
vs
new independent journey
```

The immutable event model provides lineage for reconciliation.

---

## 54. Recovery

After restart/recovery, Novi should rebuild spatial state from:

```text
verified map state
+ localization state
+ trajectory checkpoints
+ spatial events
+ place memories
```

Current localization must be re-established before movement resumes.

---

## 55. Continuous Operation

Spatial storage must remain bounded.

Controls include:

- trajectory segmentation;
- compression;
- keyframes;
- summaries;
- retention policies;
- map versioning;
- background compaction.

The robot must not accumulate unlimited raw trajectories.

---

## 56. Resource Awareness

Spatial processing can be expensive.

Under resource pressure Novi may:

- reduce non-critical mapping frequency;
- defer historical trajectory summarization;
- reduce optional global relocalization;
- postpone map optimization;
- preserve safety-critical localization.

Safety-critical localization must have protected resources.

---

## 57. Testing Requirements

Test:

- indoor localization;
- outdoor GNSS localization;
- indoor/outdoor transition;
- VIO drift;
- LiDAR localization;
- GNSS loss;
- sensor disagreement;
- trajectory reconstruction;
- route deviation;
- visit detection;
- duration estimation;
- temporal ordering;
- map versioning;
- environmental change detection;
- localization uncertainty;
- spatial retrieval;
- privacy filtering;
- synchronization conflicts;
- crash recovery;
- trajectory compression;
- long-duration operation;
- exploration mapping.

---

## 58. Architectural Invariants

1. Spatial memory always has temporal context.
2. Coordinates are not automatically places.
3. Planned routes are not evidence of completed travel.
4. Actual trajectories retain localization provenance.
5. Current reality outranks stale map assumptions for immediate safety.
6. Localization uncertainty propagates into derived spatial memories.
7. Map differences are not automatically physical-world changes.
8. GNSS is optional and unavailable in some environments.
9. Core spatial operation remains local and offline-capable.
10. Historical trajectories remain distinct from current pose.
11. Raw trajectory retention is bounded by policy.
12. Spatial history is privacy-sensitive.
13. Spatial synchronization preserves lineage and detects conflicts.
14. Route preferences do not override current planning and safety.
15. Exploration is bounded by safety and resource policy.
16. Spatial predictions remain revisable.
17. Spatial history must be auditable and protected from unauthorized mutation.

---

## 59. Final Principle

> **Novi should not merely know where it is; it should understand where it has been, when it was there, how it got there, what it experienced, how certain that history is, and how the physical world has changed since then.**

This temporal-spatial layer turns Novi's map from a static navigation artifact into a persistent, evidence-backed model of its embodied history.
