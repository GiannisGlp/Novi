# 46 — Memory Object and Entity Lifecycle

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## High-Level Description

This document defines how Novi represents physical and conceptual entities over time: discovery, observation, identification, tracking, re-identification, persistence, change, disappearance, relationships, provenance, memory promotion and forgetting.

The purpose is to prevent a common robotics failure mode: treating a detection in one frame as a permanent, certain identity.

NVIDIA's current Isaac ROS ecosystem provides replaceable perception building blocks for object detection, segmentation and 3D pose/tracking, including DetectNet, RT-DETR, YOLOv8, Grounding DINO, FoundationPose and Segment Anything 2. These are perception capabilities; Novi's canonical entity lifecycle remains above them and vendor-neutral. citeturn0search6turn0search4turn0search5

## Core Principle

> **A detection is an observation, not an identity. An identity is a hypothesis until sufficient evidence establishes continuity.**

---

## 1. Entity Concept

An entity is a persistent reference to something Novi may reason about across observations.

Examples:

- person;
- animal;
- object;
- vehicle;
- place;
- landmark;
- room;
- device;
- environmental feature;
- software/service entity;
- abstract entity.

The same lifecycle framework should support physical and non-physical entities while allowing type-specific policies.

---

## 2. Observation vs Entity

Never collapse:

```text
sensor observation
      ≠
detection
      ≠
track
      ≠
identity hypothesis
      ≠
verified entity
      ≠
durable knowledge
```

Example:

```text
camera frame
 ↓
person detection
 ↓
track-017
 ↓
possible person-A
 ↓
identity confidence increases
```

---

## 3. Entity Lifecycle

Canonical lifecycle:

```text
UNKNOWN
  ↓
DETECTED
  ↓
TRACKED
  ↓
IDENTITY_HYPOTHESIS
  ↓
ESTABLISHED
  ↓
ACTIVE
  ↓
UPDATED
  ↓
MISSING
  ↓
REAPPEARED / RESOLVED
  ↓
INACTIVE / HISTORICAL
  ↓
FORGOTTEN / RETAINED SUMMARY
```

Not every entity needs every state.

---

## 4. Detection

A detection records that a perception system produced an observation.

It should include, where available:

- timestamp;
- sensor/source;
- frame ID;
- class hypothesis;
- confidence;
- location/geometry;
- image/depth references;
- model/version;
- calibration context.

Detection data should be immutable evidence where practical.

---

## 5. Tracking

Tracking associates observations across time.

```text
frame t0 → track A
frame t1 → track A
frame t2 → track A
```

A track is not automatically a persistent identity.

Tracking confidence should be explicit.

---

## 6. Multi-Sensor Association

An entity may be observed by:

- multiple cameras;
- LiDAR;
- thermal sensors;
- microphones/audio localization;
- depth sensors;
- other approved modalities.

Association should consider:

- timestamp;
- spatial consistency;
- coordinate transforms;
- appearance/features;
- geometry;
- motion;
- sensor reliability.

Conflicting evidence must remain visible.

---

## 7. Identity Hypothesis

An identity hypothesis states:

```text
observation X
may correspond to entity Y
```

It must include confidence and supporting evidence.

Identity confidence is not a probability of moral character, trustworthiness or authorization.

---

## 8. Re-Identification

When an entity disappears and later returns, Novi may attempt re-identification.

Evidence may include:

- spatial continuity;
- appearance;
- geometry;
- known object features;
- motion continuity;
- contextual consistency;
- approved biometric mechanisms where explicitly permitted.

A re-identification failure should produce a new hypothesis rather than silently forcing identity continuity.

---

## 9. Person Identity

Person identity is especially sensitive.

Novi must distinguish:

```text
person detected
known person hypothesis
verified person identity
authorized user
administrator
```

Recognition must never itself grant permission.

Biometric processing must follow the privacy architecture and applicable requirements.

---

## 10. Object Identity

For ordinary objects, identity may be based on:

- class;
- instance appearance;
- geometry;
- persistent features;
- location/context;
- user-provided labels;
- manufacturer/serial information when legitimately available.

Example:

```text
"mug"
 ≠
"my blue mug"
 ≠
verified physical instance #42
```

---

## 11. Place and Landmark Identity

Places and landmarks require spatial-temporal continuity.

A place may remain the same semantic place even when its physical appearance changes.

A landmark can be reclassified or retired if evidence indicates it no longer exists.

---

## 12. Object Persistence

Novi should not assume an object is permanent because it appeared once.

Persistence may require:

- repeated observations;
- stable spatial location;
- stable features;
- explicit user confirmation;
- known persistent map structure.

---

## 13. Temporary Objects

Temporary entities include:

- bags;
- packages;
- chairs moved temporarily;
- tools in use;
- transient obstacles.

Temporary observations should not unnecessarily pollute the long-term world model.

---

## 14. Moving Entities

Moving entities require state such as:

- position;
- velocity estimate;
- direction;
- track confidence;
- predicted position;
- last observation.

Prediction must not be treated as observation.

---

## 15. Disappearance

When an entity leaves perception:

```text
ACTIVE
 ↓
MISSING
```

Missing does not mean destroyed, deleted or gone from the world.

The system should retain an uncertainty window before declaring an entity inactive.

---

## 16. Reappearance

A missing entity can:

```text
reappear and match
reappear but identity uncertain
reappear as a new entity
remain unresolved
```

The decision must preserve evidence.

---

## 17. Entity Death / Removal

For physical objects, disappearance can eventually be classified as:

- removed;
- destroyed;
- relocated;
- inaccessible;
- unknown.

The system must not infer destruction merely from loss of visibility.

---

## 18. Entity Change

An established entity can change:

```text
appearance
location
state
ownership/context
relationships
capabilities
```

Changes should update the entity state without erasing historical versions.

---

## 19. Versioned Entity State

Conceptually:

```text
entity-42
 ├── state-v1
 ├── state-v2
 └── state-v3
```

Historical observations remain linked to the state valid at that time.

---

## 20. Temporal Identity

Entity identity must be time-aware.

Example:

```text
same physical room
but
furniture state changed
```

The entity remains the room while its observed state evolves.

---

## 21. Entity Relationships

Entities may have relationships such as:

```text
located_in
near
owned_by
used_by
part_of
attached_to
connected_to
seen_with
associated_with
```

Relationships have timestamps, provenance and confidence where appropriate.

---

## 22. Ownership

Novi must distinguish:

```text
observed association
user assertion
verified ownership
```

It must not infer ownership merely from proximity or repeated use unless the relevant policy explicitly permits that inference.

---

## 23. Entity Attributes

Attributes should include:

- value;
- source;
- timestamp;
- confidence;
- validity interval;
- provenance;
- verification state.

Example:

```text
color = blue
source = camera observation
confidence = high
observed_at = T
```

---

## 24. Attribute Change

If a mug is observed as blue and later red, Novi should consider:

- lighting;
- sensor differences;
- occlusion;
- image-processing error;
- object replacement;
- actual change.

It should investigate persistent contradictions before rewriting stable knowledge.

---

## 25. Entity Merge

Two entity records may be merged only when evidence supports identity equivalence.

```text
entity-A
entity-B
   ↓
identity evidence
   ↓
merge candidate
   ↓
validated merge
```

The original record lineage must remain recoverable.

---

## 26. Entity Split

If one entity record incorrectly combines two real entities, Novi must support splitting it.

```text
entity-X
   ↓
new evidence
   ↓
entity-A + entity-B
```

Historical observations should be reassigned only with provenance showing the correction.

---

## 27. Identity Uncertainty

Novi must be comfortable with:

```text
unknown
ambiguous
possible match
likely match
verified match
```

Forcing every observation into a known identity is prohibited.

---

## 28. Sensor Failure

If a sensor becomes unreliable, entity tracking confidence should degrade appropriately.

The system should not interpret sensor blindness as world disappearance.

---

## 29. Occlusion

Occlusion should be represented separately from disappearance.

Example:

```text
person visible
 ↓
walks behind wall
 ↓
not observed
```

The likely continued existence of the entity is a prediction, not a new observation.

---

## 30. Active Reacquisition

When an entity is important to an active goal, Novi may use active perception to reacquire it:

- camera movement;
- additional camera;
- LiDAR scan;
- thermal observation;
- audio localization;
- movement to a better viewpoint.

This must be bounded by safety and resource policy.

---

## 31. Entity Salience

Not every entity deserves equal long-term retention.

Salience may consider:

- safety relevance;
- active goals;
- repeated occurrence;
- user importance;
- novelty;
- prediction value;
- historical significance;
- explicit request.

Salience affects processing/retention, not truth.

---

## 32. Memory Promotion

A transient observation can become durable memory when justified by the memory admission policy.

```text
observation
 ↓
track
 ↓
repeated/salient evidence
 ↓
memory candidate
 ↓
admission policy
 ↓
durable memory
```

No automatic promotion merely because an LLM described the entity.

---

## 33. Memory Demotion

A memory may be downgraded when:

- evidence becomes stale;
- identity confidence falls;
- contradictory evidence appears;
- relevance declines.

Demotion does not necessarily mean deletion.

---

## 34. Forgetting

Entity memories may eventually be:

```text
raw observation → deleted
track history → compressed
semantic memory → retained
identity record → retained only when justified
```

Retention follows privacy, legal, storage and user policy.

---

## 35. Privacy-Sensitive Entities

People and sensitive entities require stricter handling than ordinary objects.

Potentially sensitive attributes should not be retained merely because a perception model can produce them.

Data minimization is the default.

---

## 36. Entity Security

Critical entity records must be protected against unauthorized modification.

An attacker must not be able to silently change:

- who a person is;
- who owns an object;
- where an entity is;
- whether an entity is authorized;
- historical evidence.

---

## 37. Authorization Boundary

Entity identity must never directly become action authorization.

```text
recognized person
      ↓
authentication
      ↓
authorization policy
      ↓
permitted action
```

This is especially important for physical actions.

---

## 38. Entity and Memory Provenance

Important entity facts should retain:

- observation IDs;
- sensor/source;
- model/version;
- timestamp;
- location;
- transform context;
- confidence;
- verification status;
- memory IDs derived from them.

This permits audit and correction.

---

## 39. Entity Contradictions

Contradictions should be represented explicitly.

Example:

```text
Observation A: object at kitchen
Observation B: object at hallway
```

Possible explanations:

- object moved;
- duplicate object;
- localization error;
- identity association error.

Novi should investigate rather than arbitrarily selecting one.

---

## 40. World Model Integration

Entity state feeds the world model:

```text
perception
 ↓
entity state
 ↓
spatial model
 ↓
world model
 ↓
cognition
```

The world model should know whether information is observed, estimated, predicted or historical.

---

## 41. Interaction Integration

Entities can connect to social memory and interaction history.

```text
person entity
 + conversation
 + location
 + time
 + relationship context
```

This integration must follow social-memory and privacy policies.

---

## 42. Language Integration

Natural language references such as:

> "Bring me the blue mug."

should resolve through entity grounding:

```text
"blue mug"
 ↓
object class
 + attribute
 + spatial context
 + recent observations
 ↓
candidate entities
 ↓
confidence
 ↓
ask if ambiguous
```

Language alone must not create a physical entity.

---

## 43. Goal Integration

Goals can create temporary entity priorities.

Example:

```text
Goal: find the keys
        ↓
keys become high-salience entities
        ↓
search / tracking / memory retrieval
```

Once the goal ends, salience can return to normal.

---

## 44. Object Search

For a search request, Novi should use:

- last known location;
- historical trajectories;
- object identity confidence;
- environmental change;
- current perception;
- user-provided information.

"Last seen" must not become "currently there."

---

## 45. Lifecycle Events

Useful entity events include:

```text
entity.detected
entity.tracked
entity.identity_hypothesis_created
entity.identity_confirmed
entity.updated
entity.relationship_changed
entity.missing
entity.reappeared
entity.merged
entity.split
entity.retired
entity.forgotten
```

Events should be immutable where practical.

---

## 46. Local-First Operation

Entity detection, tracking and memory must operate locally without Wi-Fi or Bluetooth.

Cloud services may be optional accelerators or synchronization mechanisms only when explicitly approved.

---

## 47. Vendor-Neutral Perception

Novi should expose canonical interfaces such as:

```text
Detection
Track
Segmentation
PoseEstimate
EntityHypothesis
EntityState
```

Implementations may use:

- NVIDIA Isaac ROS;
- OpenCV;
- PyTorch;
- TensorFlow;
- ONNX Runtime;
- Hugging Face;
- other open-source local solutions.

NVIDIA's current Isaac ROS catalog already includes multiple interchangeable detection and segmentation approaches and 3D pose estimation components, reinforcing the value of keeping Novi's entity semantics above the perception layer. citeturn0search9turn0search1

---

## 48. Simulation and Testing

Entity lifecycle testing should use real sensor recordings, synthetic data and simulation where useful.

Isaac ROS currently provides Isaac Sim examples for object detection and 3D pose workflows, while multi-camera reconstruction examples support dynamic scenes. citeturn0search0turn0search10

Simulation is not sufficient by itself; real-world validation is required for final behavior.

---

## 49. Performance and Resource Budgets

Entity processing must be resource-aware.

Under pressure, Novi may:

- lower tracking frequency for low-priority entities;
- reduce re-identification attempts;
- defer semantic enrichment;
- retain safety-critical tracks;
- preserve current navigation obstacles.

Safety-critical perception receives protected resources.

---

## 50. Testing Requirements

Test:

- single-object detection;
- multi-object tracking;
- occlusion;
- reappearance;
- re-identification;
- duplicate objects;
- object movement;
- sensor disagreement;
- camera failure;
- LiDAR failure;
- thermal observation disagreement;
- identity merge;
- identity split;
- map changes;
- person recognition boundaries;
- authorization separation;
- privacy filtering;
- memory promotion;
- forgetting;
- crash recovery;
- long-duration tracking;
- resource pressure;
- offline operation.

---

## 51. Architectural Invariants

1. A detection is not an identity.
2. A track is not a verified identity.
3. Identity uncertainty must remain representable.
4. Prediction is not observation.
5. Occlusion is not disappearance.
6. Loss of sensing is not proof of entity removal.
7. Person recognition never grants authorization.
8. Historical entity state is not overwritten without provenance.
9. Entity merges and splits preserve lineage.
10. Sensor disagreement is retained and investigated.
11. Sensitive entity data follows stricter privacy policy.
12. Memory promotion requires an explicit admission path.
13. Forgetting may remove detail without rewriting historical truth.
14. Current perception can supersede stale state for immediate decisions.
15. Core entity processing works offline.
16. Perception vendors remain replaceable behind canonical Novi interfaces.
17. Safety-critical entities receive protected processing resources.
18. Entity records must be protected from unauthorized mutation.

---

## 52. Final Principle

> **Novi should remember entities as evolving, uncertain, time-bound beings or things—not as static labels attached to sensor detections.**

The lifecycle architecture therefore preserves the difference between what Novi saw, what it tracked, what it believes it recognized, what has been verified, what changed, and what it is justified in remembering.
