# Novi — Perception Architecture

**Status:** Proposed / P0 critical architecture specification  
**Version:** 1.0  
**Date:** 2026-08-17  
**Authority:** `docs/02-novi-brain/` brain architecture; system contracts remain governed by `docs/01-system-architecture/`

## 1. Purpose

Perception is Novi's continuous interface to the physical world.

The purpose of this document is to define how raw sensor signals become trustworthy, time-aware, uncertainty-aware evidence that can update Novi's world model, trigger attention, support interaction, enable navigation and inform action.

Perception is **not** a single neural network and is not synonymous with computer vision.

The canonical pipeline is:

```text
WORLD
  ↓
SENSORS
  ↓
DRIVERS / ACQUISITION
  ↓
TIME + FRAME NORMALIZATION
  ↓
QUALITY / HEALTH CHECKS
  ↓
PREPROCESSING
  ↓
SPECIALIST PERCEPTION
  ↓
TRACKING / ESTIMATION
  ↓
MULTI-SENSOR FUSION
  ↓
SPATIAL / TEMPORAL REPRESENTATION
  ↓
EVIDENCE
  ↓
ATTENTION + WORLD MODEL
```

The architecture must preserve the distinction between:

- raw observation;
- processed measurement;
- model inference;
- fused estimate;
- world-model belief;
- prediction;
- action consequence.

## 2. Behavioral objective

Novi should continuously sense its environment even when no person is interacting with it.

Perception must therefore support:

- continuous environmental awareness;
- rapid detection of salient events;
- human presence and activity awareness;
- object and scene understanding;
- localization and spatial awareness;
- obstacle and free-space understanding;
- self-motion estimation;
- sound/event awareness;
- interaction grounding;
- active perception;
- uncertainty and confidence;
- graceful degradation;
- replay and diagnosis.

The objective is not to maximize the number of detected objects. The objective is to maintain the **best actionable estimate of the relevant world state** within resource, latency, privacy and safety constraints.

## 3. NVIDIA reference validation

NVIDIA's current Isaac ROS package catalog provides dedicated components for mapping/localization, Nvblox 3D reconstruction, object detection, pose estimation, visual SLAM and NITROS transport. citeturn0search3

NVIDIA's current Isaac ROS Perceptor architecture is especially relevant to Novi because it combines synchronized multi-camera data, image processing, learned depth estimation, Visual SLAM and Nvblox into a 3D reconstruction pipeline that can feed downstream planning. citeturn0search1

NVIDIA's current Nvblox documentation describes aligned TSDF, color, mesh and ESDF voxel layers and supports dynamic/people reconstruction through segmentation/detection. citeturn0search0

NVIDIA's current Visual SLAM documentation supports multi-camera, visual-inertial and RGB-D tracking modes and explicitly models timestamp synchronization between image streams. citeturn0search11

NVIDIA's Isaac Sim 6.0 documentation supports RGB/RGB-D cameras, 2D/3D RTX LiDAR, contact sensors, IMUs, radar and ultrasonic sensors through its ROS 2 integration. citeturn0search12

These sources validate the availability of relevant building blocks. They do **not** prove that a particular sensor suite or NVIDIA pipeline is optimal for Novi. Novi adoption requires its own benchmark, hardware compatibility test and ADR.

## 4. Perception layers

### P0 — Acquisition

Responsibilities:

- receive sensor data;
- timestamp data;
- validate transport;
- identify sensor source;
- preserve calibration identity;
- expose health state.

No cognitive inference occurs here.

### P1 — Normalization

Responsibilities:

- coordinate/frame normalization;
- image format normalization;
- calibration application;
- synchronization;
- unit normalization;
- quality checks;
- rate control.

### P2 — Fast perception

Always-on or near-always-on capabilities:

- motion/change detection;
- person/object presence;
- sound activity;
- obstacle/free-space cues;
- sensor anomaly detection;
- basic tracking;
- immediate safety-relevant perception.

These components should have predictable latency and modest compute requirements.

### P3 — Specialist perception

Examples:

- object detection;
- segmentation;
- depth estimation;
- pose estimation;
- face/person cues where permitted;
- activity recognition;
- semantic scene understanding;
- acoustic-event classification;
- speech activity detection.

### P4 — Fusion and estimation

Combine compatible evidence into:

- tracked entities;
- robot pose;
- velocity estimates;
- free space;
- occupancy;
- 3D scene representation;
- object tracks;
- audio-visual associations;
- confidence estimates.

### P5 — Cognitive grounding

Translate perception outputs into canonical Novi evidence:

```text
Observation
Measurement
Evidence
Entity
Relationship
WorldStateChange
```

This layer decides what is semantically meaningful enough to enter cognitive processing. It must not silently convert uncertain inference into fact.

## 5. Sensor classes

The architecture supports the following classes without requiring all of them on the first robot:

| Sensor | Primary contribution | Typical downstream use |
|---|---|---|
| RGB camera | appearance/color | objects, people, scenes, interaction |
| Stereo/RGB-D | depth + appearance | geometry, obstacle awareness, 3D |
| LiDAR | geometric range | mapping, obstacle detection, localization |
| IMU | inertial motion | VIO, stabilization, state estimation |
| wheel/actuator encoders | proprioception | odometry/control feedback |
| microphone array | sound/audio | speech, acoustic events, direction |
| contact/tactile | physical contact | manipulation/safety |
| radar | motion/range in difficult visibility | complementary perception |
| thermal | heat signatures | specialized detection |
| environmental sensors | physical environment | context/health |

The exact physical sensor set is controlled by the hardware architecture and must be selected through requirements and benchmark evidence.

## 6. Time semantics

Perception is invalid if its temporal semantics are ambiguous.

Every sensor message must carry or be associated with:

- sensor timestamp;
- acquisition sequence where available;
- host receipt time;
- clock domain;
- frame ID;
- sensor configuration/calibration version;
- source identity.

The perception system must distinguish:

```text
sensor time
host time
ROS time
simulation time
recording time
processing time
```

A downstream component must be able to determine whether an observation is fresh, delayed, stale or reordered.

## 7. Spatial semantics

Every spatial observation must be associated with a known frame and calibration version.

The canonical chain is conceptually:

```text
sensor frame
   ↓
robot/body frame
   ↓
odometry/local frame
   ↓
map/world frame
```

Transforms must come from the authoritative TF2/robot-state system rather than duplicated application-specific transforms.

Calibration changes must be versioned and must invalidate or appropriately annotate dependent derived data.

## 8. Camera perception

Camera processing should be decomposed into:

```text
capture
 ↓
calibration
 ↓
rectification
 ↓
quality assessment
 ↓
fast features
 ↓
optional depth
 ↓
object/segmentation models
 ↓
tracking
 ↓
3D grounding
 ↓
scene understanding
```

NVIDIA documents GPU-accelerated image processing as part of Isaac ROS Perceptor and provides current Isaac ROS packages for object detection, segmentation, depth and pose estimation. citeturn0search1turn0search3

Novi must not assume that every camera frame requires every model. Model routing should select processing according to attention, task, confidence and resource budget.

## 9. Depth perception

Depth may come from:

- stereo;
- RGB-D hardware;
- learned depth estimation;
- LiDAR;
- fused reconstruction.

Depth must carry quality/confidence metadata.

NVIDIA's current Isaac ROS Perceptor combines learned stereo depth with Visual SLAM and Nvblox to create a 3D representation. citeturn0search1

Novi should benchmark depth sources for:

- near-field accuracy;
- far-field accuracy;
- low-light behavior;
- reflective/transparent surfaces;
- dynamic scenes;
- latency;
- compute cost;
- failure detection.

## 10. LiDAR perception

LiDAR should provide geometry that complements cameras rather than being treated as a duplicate camera.

Required processing may include:

- filtering;
- motion compensation where applicable;
- ground/free-space extraction;
- obstacle representation;
- scan matching/localization;
- 3D fusion.

NVIDIA's current Isaac ROS catalog explicitly supports Nvblox and related perception workflows with LiDAR examples. citeturn0search2

## 11. IMU and proprioception

IMU and actuator feedback are part of Novi's **self-perception**.

Novi must maintain estimates of:

- orientation;
- angular velocity;
- acceleration;
- velocity;
- wheel/actuator state;
- motion confidence;
- sensor health.

These signals should be fused with visual/geometric observations where appropriate.

NVIDIA's current cuVSLAM implementation supports visual-inertial tracking and exposes IMU-related configuration. citeturn0search11

## 12. Audio perception

Audio perception must be treated as a parallel sensory system.

Pipeline:

```text
microphones
 ↓
acquisition/synchronization
 ↓
voice activity / acoustic events
 ↓
source localization where available
 ↓
speech recognition when relevant
 ↓
audio-visual association
 ↓
evidence
```

Audio events may trigger attention without speech being present.

Examples:

- name/voice detected;
- door closing;
- glass breaking;
- alarm;
- unusual impact;
- nearby movement sound.

## 13. Multi-sensor fusion

Fusion must distinguish:

### Agreement
Multiple sensors support the same hypothesis.

### Complementarity
Sensors provide different dimensions of the same event.

### Conflict
Sensors disagree.

### Missingness
A sensor is unavailable.

### Staleness
A sensor is technically available but its data is too old.

Conflict must not be resolved by blindly averaging measurements.

The fusion layer should retain:

- source evidence;
- timestamp;
- confidence;
- correlation assumptions;
- fusion method;
- resulting uncertainty;
- rejected evidence and reason where diagnostically important.

## 14. Tracking and identity continuity

Detection answers:

> What might be here now?

Tracking answers:

> Is this the same entity observed previously?

Tracking must maintain uncertainty and avoid turning a temporary association into permanent identity.

Canonical tracked entities may include:

- people;
- robots;
- vehicles;
- objects;
- sounds/sources;
- regions/places.

Identity resolution belongs to the cognition/memory boundary; perception supplies evidence, not unquestionable identity truth.

## 15. Spatial world representation

Novi should maintain multiple representations rather than one universal map.

Potential layers:

```text
2D navigation map
3D occupancy
ESDF / distance field
mesh
semantic objects
tracked dynamic entities
robot pose
places
interaction zones
```

NVIDIA's current Nvblox documentation describes TSDF, color, mesh and ESDF layers and dynamic/people reconstruction. citeturn0search0

Novi should keep the geometric representation and semantic world model linked but independently versioned.

## 16. Active perception

Novi should sometimes **change how it senses** the world.

Examples:

- rotate toward a sound;
- move to improve camera visibility;
- inspect an ambiguous object from another angle;
- approach a person to hear better when appropriate;
- change sensor processing rate;
- request another modality;
- illuminate a scene if hardware permits.

Active perception is an action and therefore must pass the normal action-governance and safety boundary.

## 17. Attention interface

Perception should not forward everything to the expensive cognitive stack.

Each salient event should be scored using factors such as:

```text
novelty
urgency
proximity
uncertainty
relevance to current goal
social relevance
safety relevance
persistence
prediction error
```

The attention system then decides whether to:

- ignore;
- continue monitoring;
- update world state;
- interrupt current cognition;
- request deeper perception;
- trigger immediate reaction.

## 18. Prediction error

Perception should compare expected and observed state.

Example:

```text
predicted: person remains at doorway
observed: person moved rapidly toward robot
```

The discrepancy should increase attention and potentially change the cognitive mode.

This is a core mechanism for making Novi responsive rather than merely reactive to externally issued commands.

## 19. Uncertainty

Every learned or probabilistic perception result must expose uncertainty appropriate to the model.

At minimum, the system must distinguish:

- confidence in detection;
- confidence in classification;
- confidence in tracking;
- confidence in localization;
- confidence in depth/geometry;
- confidence in temporal association.

A high-confidence model output is still an inference, not a verified fact.

## 20. Perception degradation

The system must remain operational when sensors fail.

Examples:

```text
camera failure
 ↓
reduce visual capabilities
 ↓
retain LiDAR/IMU/audio
 ↓
reduce confidence
 ↓
change behavior
```

```text
LiDAR failure
 ↓
retain camera/depth/IMU
 ↓
reduce spatial confidence
 ↓
restrict navigation if required
```

```text
GPU perception failure
 ↓
fast deterministic/specialist fallback
 ↓
degraded cognition
 ↓
safe behavior
```

Degradation state must be visible to the brain orchestrator and safety system.

## 21. Simulation parity

Every major perception pipeline should have:

- simulated sensor source;
- recorded real sensor source;
- deterministic replay;
- fault injection;
- ground-truth comparison where possible.

NVIDIA's current Isaac Sim documentation supports RGB/RGB-D, LiDAR, IMU and other sensor simulation with ROS 2 integration. citeturn0search12turn0search13

Isaac ROS provides current tutorials for Visual SLAM, Nvblox, object detection, segmentation, depth estimation and pose estimation against Isaac Sim. citeturn0search2

## 22. Data provenance

Every derived perception result must be traceable to:

- source sensor(s);
- sensor configuration;
- calibration version;
- timestamp(s);
- preprocessing version;
- model ID/version where applicable;
- model artifact digest;
- runtime version;
- fusion algorithm/version;
- confidence/uncertainty;
- simulation/real classification.

This allows Novi to answer:

> "Why did you believe that?"

with evidence rather than a post-hoc explanation generated by an LLM.

## 23. Privacy

Perception can process highly sensitive information.

The architecture must support:

- local processing where possible;
- explicit retention policies;
- configurable raw-frame retention;
- access control;
- redaction/anonymization where appropriate;
- audit logging;
- deletion workflows;
- separation between transient perception and durable memory.

A detected person is not automatically a durable memory record.

## 24. Performance model

Each perception component must have a declared budget:

- frequency;
- latency P50/P95/P99;
- CPU;
- GPU;
- memory;
- power;
- bandwidth;
- storage;
- maximum tolerated staleness.

The brain orchestrator may reduce processing rates or switch models when budgets are exceeded.

## 25. Reference NVIDIA mapping

| Novi capability | NVIDIA candidate/reference | Adoption status |
|---|---|---|
| GPU image processing | Isaac ROS Image Pipeline | Candidate |
| Visual odometry/SLAM | Isaac ROS Visual SLAM / cuVSLAM | Candidate |
| 3D reconstruction | Isaac ROS Nvblox | Candidate |
| object detection | Isaac ROS RT-DETR / other supported detectors | Candidate |
| segmentation | Isaac ROS segmentation packages | Candidate |
| depth | Isaac ROS ESS / FoundationStereo / other supported methods | Candidate |
| pose estimation | Isaac ROS FoundationPose / CenterPose / DOPE | Candidate |
| synchronized multi-camera perception | Isaac ROS Nova/Perceptor patterns | Candidate |
| simulation sensors | Isaac Sim | Candidate |
| GPU message transport | NITROS | Candidate |

The current Isaac ROS package catalog supports these broad categories. citeturn0search3

No row becomes an implementation dependency until a Novi ADR records version, platform, benchmark and validation evidence.

## 26. Required perception contracts

Perception must expose machine-readable contracts for:

- `SensorObservation`;
- `PerceptionMeasurement`;
- `Detection`;
- `Track`;
- `PoseEstimate`;
- `DepthEstimate`;
- `SceneRepresentation`;
- `AudioEvent`;
- `PerceptionHealth`;
- `PerceptionFailure`;
- `Evidence`.

These contracts must reference the canonical system contracts defined in `01-system-architecture` rather than creating conflicting definitions.

## 27. Validation strategy

Every perception component must be evaluated at four levels.

### A. Component

- correctness;
- latency;
- resource use;
- failure handling.

### B. Pipeline

- timestamp alignment;
- throughput;
- end-to-end latency;
- data loss;
- fusion correctness.

### C. Scenario

Test:

- normal room;
- moving people;
- low light;
- occlusion;
- clutter;
- reflective surfaces;
- rapid motion;
- sensor dropout;
- contradictory sensors;
- novel objects;
- unexpected events.

### D. Long-duration

Measure:

- drift;
- memory growth;
- dropped messages;
- thermal effects;
- calibration stability;
- model/runtime failures;
- recovery.

## 28. Acceptance criteria

Perception architecture is not implementation-complete until:

- [ ] every sensor has a defined purpose;
- [ ] every sensor has a time/frame contract;
- [ ] calibration is versioned;
- [ ] sensor health is observable;
- [ ] raw and derived data are distinguishable;
- [ ] inference and fact are distinguishable;
- [ ] uncertainty is represented;
- [ ] multi-sensor conflicts are handled;
- [ ] tracking semantics are defined;
- [ ] spatial representation is defined;
- [ ] active perception has an action boundary;
- [ ] degraded modes exist;
- [ ] simulation/replay exists;
- [ ] provenance exists;
- [ ] privacy rules exist;
- [ ] performance budgets are measurable;
- [ ] NVIDIA candidate components have version/platform validation;
- [ ] Novi-specific benchmarks exist;
- [ ] safety-critical perception paths have independent validation.

## 29. Decisions intentionally deferred

The following must not be guessed in this document:

- exact camera model;
- exact LiDAR model;
- exact microphone array;
- final sensor count;
- exact perception neural networks;
- exact inference runtime;
- final Jetson configuration;
- final sensor rates;
- final compute budgets.

Those decisions belong to hardware selection, model evaluation and ADRs after measurable requirements exist.

## 30. Core principle

> **Novi does not see the world because a neural network classified an image. Novi sees the world by continuously maintaining a time-aware, spatially grounded, uncertainty-aware evidence stream produced from multiple sensors and models, and by using that evidence to update its world model and behavior.**
