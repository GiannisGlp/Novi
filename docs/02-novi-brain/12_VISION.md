# Novi Brain — 12 Vision

**Status:** PROPOSED / P0 critical architecture specification  
**Authority:** Brain architecture domain; implementation requires ADRs and benchmark evidence  
**Date:** 2026-08-17

## 1. Purpose

This document defines Novi's visual intelligence system: how visual sensors become trustworthy, temporally coherent, spatially grounded evidence that can be consumed by the brain.

Vision is not a single neural network. It is a continuous perception subsystem composed of sensing, calibration, image processing, learned models, geometry, tracking, scene understanding, uncertainty estimation, temporal integration and active perception.

The visual system must support the North Star requirement that Novi continuously senses its environment, notices relevant changes, recognizes people and objects where permitted, understands spatial relationships, reacts to events and contributes grounded information to memory, interaction, navigation and action.

---

# 2. Non-goals

Vision does not:

- directly authorize physical actions;
- directly command motors;
- define long-term semantic memory;
- decide Novi's personality;
- treat neural-model output as ground truth;
- replace localization/navigation/control;
- permanently retain raw visual data by default.

Visual outputs are evidence and estimates. Higher-level cognition determines meaning and relevance subject to governance and safety.

---

# 3. Core visual pipeline

```text
CAMERA HARDWARE
      ↓
CAPTURE / DRIVER
      ↓
TIMESTAMP + FRAME ID
      ↓
CALIBRATION / RECTIFICATION
      ↓
IMAGE QUALITY CHECK
      ↓
PREPROCESSING
      ↓
FAST VISUAL PERCEPTION
      ↓
SPECIALIST MODELS
      ├── detection
      ├── segmentation
      ├── depth
      ├── pose
      └── recognition/embedding
      ↓
TEMPORAL TRACKING
      ↓
GEOMETRIC GROUNDING
      ↓
MULTI-CAMERA / DEPTH / LIDAR FUSION
      ↓
SCENE REPRESENTATION
      ↓
UNCERTAINTY + PROVENANCE
      ↓
VISUAL EVIDENCE
      ↓
ATTENTION / WORLD MODEL / MEMORY / ACTION CONTEXT
```

The pipeline must be able to operate at multiple rates. High-rate perception remains active while expensive scene reasoning runs selectively.

---

# 4. Visual sensing architecture

Novi should not assume that one camera can provide all visual information.

Candidate camera roles:

- forward navigation camera;
- wide-angle situational camera;
- depth/stereo camera;
- optional rear/side coverage;
- optional close-range camera for manipulation;
- optional dedicated low-light/IR camera;
- optional event camera for later research.

Final camera count, optics, baseline, resolution and frame rate are hardware decisions driven by coverage, latency, power, bandwidth and compute requirements.

## 4.1 RGB

RGB provides appearance, color, texture, semantic cues and general visual information.

Required metadata:

- sensor ID;
- timestamp;
- frame ID;
- exposure metadata where available;
- intrinsic calibration ID;
- distortion model;
- image encoding;
- resolution;
- capture configuration;
- hardware/firmware version.

## 4.2 Stereo/depth

Depth supports:

- obstacle distance;
- 3D localization;
- scene reconstruction;
- object range;
- spatial interaction;
- navigation.

Depth must carry validity/confidence information where available. Invalid/infinite depth must never be silently converted into a valid measurement.

## 4.3 Multi-camera coverage

Multiple cameras can provide complementary fields of view and redundancy.

Cross-camera identity and track association must be confidence-scored and calibration-dependent. A detection in camera A must not automatically become the same entity in camera B.

NVIDIA's current DeepStream/Metropolis documentation demonstrates multi-camera tracking architectures using calibrated cameras, per-camera perception metadata, embeddings and global association. citeturn1search2turn1search12

---

# 5. Camera calibration

Every physical camera requires versioned calibration.

Required calibration classes:

- intrinsics;
- distortion;
- stereo extrinsics;
- camera-to-robot transform;
- camera-to-camera transforms;
- temporal offset;
- rolling-shutter characteristics where applicable.

Calibration artifact must include:

```text
calibration_id
sensor_id
method
parameters
reference_frames
capture_conditions
quality_metrics
creation_time
software/tool version
operator/procedure
checksum
validity status
```

A calibration change is a versioned deployment change, not an informal configuration edit.

NVIDIA's current multi-view 3D tracking documentation explicitly identifies camera calibration as a prerequisite for geometric reasoning. citeturn1search12

---

# 6. Image quality gate

Before expensive inference, Novi should evaluate whether an image is usable.

Quality signals may include:

- exposure;
- saturation;
- blur;
- noise;
- motion blur;
- lens obstruction;
- dropped frames;
- compression damage;
- low-light condition;
- depth validity;
- temporal freshness.

A low-quality frame should lower confidence rather than silently producing an ordinary-confidence result.

---

# 7. Visual preprocessing

Preprocessing may include:

- resize;
- crop;
- normalization;
- color conversion;
- distortion correction;
- stereo rectification;
- denoising;
- exposure handling;
- ROI selection;
- temporal filtering.

Preprocessing must be deterministic and versioned where it affects model behavior.

Preprocessing must not alter evidence provenance: the system records the source frame and transformation chain.

---

# 8. Fast visual perception

Fast visual perception exists to keep Novi continuously aware.

Typical outputs:

- person/object detections;
- approximate classes;
- bounding regions;
- coarse segmentation;
- motion;
- depth/range;
- tracking updates;
- scene-change signals;
- anomaly signals.

Fast perception should favor predictable latency and availability over maximum semantic richness.

This layer is one of the primary mechanisms that allows Novi to remain responsive without invoking a large reasoning model for every frame.

---

# 9. Object detection

Detection answers:

> What candidate objects/entities appear in this visual input, approximately where are they, and with what confidence?

A detection record should contain at minimum:

- detector/model ID;
- model version;
- timestamp;
- frame ID;
- class hypotheses;
- bounding geometry;
- confidence;
- image quality;
- calibration ID;
- inference latency;
- provenance.

Novi must preserve the distinction between detection and identification.

```text
DETECTED PERSON
      ≠
KNOWN PERSON
      ≠
IDENTIFIED PERSON
```

---

# 10. Segmentation

Segmentation provides finer spatial understanding than bounding boxes.

Candidate types:

- semantic segmentation;
- instance segmentation;
- panoptic-style representations;
- freespace segmentation;
- dynamic/static segmentation.

Segmentation should be selected according to downstream need rather than used universally.

NVIDIA Isaac ROS provides image segmentation and related accelerated perception packages, while DeepStream provides real-time detection/tracking pipelines. citeturn1search1turn1search3

---

# 11. Depth estimation

Depth can originate from:

- stereo;
- active depth cameras;
- LiDAR-assisted fusion;
- learned monocular/multi-view depth;
- simulator ground truth during development.

Learned depth must be treated as an estimate with uncertainty. Sensor depth and learned depth must retain distinct provenance.

The visual system should be able to compare depth sources and detect disagreement.

---

# 12. Pose estimation

Pose estimation may include:

- human 2D/3D pose;
- object 6D pose;
- robot/camera pose from visual odometry/SLAM.

Object pose is useful for manipulation and interaction, but must not bypass action governance.

NVIDIA Isaac ROS includes pose-estimation capabilities and NVIDIA's manipulation reference workflows combine detection, segmentation, pose, reconstruction and motion planning. citeturn1search1

---

# 13. Tracking

Detection is frame-local; tracking creates temporal continuity.

Novi should maintain tracks for relevant entities with:

- track ID;
- observation history;
- current state estimate;
- velocity estimate where justified;
- confidence;
- source sensors;
- last observation time;
- predicted state;
- identity hypotheses;
- lifecycle state.

Track lifecycle:

```text
candidate
 ↓
confirmed
 ↓
active
 ↓
temporarily lost
 ↓
reacquired / expired
```

A predicted track is not equivalent to a current observation.

NVIDIA DeepStream's current perception stack includes multi-object tracking and NVIDIA documents multi-camera tracking with global association and re-identification embeddings. citeturn1search0turn1search2

---

# 14. Person understanding

Novi's visual system should separate:

1. person detection;
2. person tracking;
3. appearance description;
4. identity hypothesis;
5. identity verification;
6. relationship/context lookup.

Identity must be privacy-governed and confidence-scored.

The system must support an explicit unknown-person state.

Novi must never infer identity solely because an embedding is similar to a remembered person.

---

# 15. Object understanding

Object understanding should progress from cheap to expensive:

```text
object candidate
 ↓
class
 ↓
attributes
 ↓
3D location
 ↓
state
 ↓
relationship to other objects
 ↓
functional interpretation
 ↓
contextual significance
```

The last stages can require multimodal reasoning and should not run continuously for every object.

---

# 16. Scene understanding

Scene understanding converts individual observations into a structured situation.

Candidate outputs:

- room/area type;
- free space;
- surfaces;
- doors/openings;
- furniture;
- people;
- objects;
- activities;
- spatial relationships;
- dynamic regions;
- hazards;
- novelty;
- uncertainty.

The scene representation should be incrementally updated rather than regenerated from scratch on every frame.

---

# 17. Visual SLAM and spatial grounding

Visual perception must integrate with the robot's spatial system.

NVIDIA Isaac ROS Visual SLAM is a candidate for visual-inertial localization. NVIDIA describes it as a high-performance ROS 2 VSLAM package. citeturn1search3

Nvblox is a candidate for dense 3D reconstruction and navigation-oriented spatial representation. NVIDIA documents RGB-D and/or LiDAR inputs and temporal costmaps for navigation. citeturn1search4

Novi must nevertheless preserve a semantic distinction:

```text
SLAM map
 ≠
Novi world model
 ≠
Novi semantic memory
```

The robotics stack supplies spatial estimates; the brain interprets and persists higher-level meaning.

---

# 18. Visual attention

Vision should not treat all pixels as equally important.

Attention may be triggered by:

- movement;
- unexpected appearance;
- disappearance;
- proximity;
- speech-associated visual activity;
- known person;
- goal-relevant object;
- safety-relevant object;
- unusual behavior;
- change in environment;
- uncertainty;
- user interaction.

Attention produces requests such as:

```text
observe longer
increase frame rate
crop region
switch camera
request depth
request multimodal reasoning
track entity
relocalize
```

This is **active perception**: Novi can change what it observes based on what it needs to know.

---

# 19. Visual memory

Vision should not permanently store every frame.

Instead, the visual system should promote selected information:

```text
raw frame
 ↓
perception metadata
 ↓
track/event
 ↓
important episode
 ↓
semantic/spatial memory
```

Raw imagery may be retained temporarily for:

- debugging;
- safety investigation;
- explicit user-authorized memory;
- training/evaluation;
- incident analysis;

subject to privacy and retention policy.

---

# 20. Multimodal grounding

Visual observations should be fused with:

- audio;
- speech;
- spatial state;
- proprioception;
- memory;
- goals;
- time;
- navigation state.

Example:

```text
camera: person detected
microphone: speech detected
ASR: "Novi"
memory: known person
world: person 2.5 m away
attention: high
```

This should become a coherent interaction context rather than four unrelated events.

---

# 21. Uncertainty

Every visual output that can be uncertain should carry uncertainty.

Novi should distinguish:

- model confidence;
- measurement uncertainty;
- tracking confidence;
- calibration uncertainty;
- identity confidence;
- temporal freshness;
- cross-sensor agreement.

Confidence must not be treated as a universal probability unless the model and calibration justify that interpretation.

---

# 22. Failure handling

Required failure classes:

| Failure | Expected behavior |
|---|---|
| Camera disconnected | mark unavailable; use other sensors |
| Frame drops | lower freshness/confidence |
| Severe blur | suppress/degrade inference |
| Lens obstruction | detect degraded camera state |
| Bad calibration | quarantine affected geometry |
| Depth invalid | do not fabricate distance |
| Detector unavailable | use degraded perception |
| Tracker failure | restart/reinitialize safely |
| GPU unavailable | switch to fallback/degraded path |
| Model timeout | preserve last valid state with freshness bound |
| Contradictory sensors | retain disagreement and lower confidence |
| Clock problem | reject/flag invalid temporal fusion |

Vision failure must never silently become certainty.

---

# 23. Privacy and human sensing

Person-related perception is privacy-sensitive.

The system must define:

- whether identification is enabled;
- which identities are authorized;
- local processing requirements;
- retention period;
- deletion behavior;
- consent/notice requirements;
- access control;
- audit requirements.

Novi should prefer anonymous detection/tracking unless identity is actually required for a capability.

---

# 24. Simulation and synthetic data

Isaac Sim is a major candidate for visual development and validation.

Current NVIDIA Isaac Sim 6.0 documentation supports ROS 2 camera publishing and synthetic RGB, depth, point-cloud, bounding-box and semantic/instance labels. citeturn0search0turn0search7

The simulation environment must preserve the distinction:

```text
SIMULATED GROUND TRUTH
        ≠
MODEL PREDICTION
        ≠
REAL SENSOR OBSERVATION
```

Simulation should be used for:

- regression tests;
- perception benchmarking;
- synthetic-data generation;
- fault injection;
- edge cases;
- calibration experiments;
- sensor placement;
- model comparison.

---

# 25. Real-world data collection

Real visual datasets should capture representative conditions:

- day/night;
- indoor/outdoor;
- bright/dim;
- cluttered/empty;
- stationary/moving camera;
- different distances;
- occlusion;
- people density;
- reflective surfaces;
- transparent surfaces;
- motion blur;
- sensor degradation.

Each dataset must use the project data/artifact provenance rules.

---

# 26. Model selection strategy

Novi should prefer existing mature models before training new models.

Selection dimensions:

- accuracy;
- latency;
- memory;
- power;
- robustness;
- licensing;
- offline operation;
- hardware compatibility;
- calibration requirements;
- failure behavior;
- maintenance;
- dataset/domain suitability.

NVIDIA Isaac ROS provides multiple accelerated perception components and NITROS paths for GPU/Jetson workloads. citeturn1search3

DeepStream is a candidate where streaming/multi-camera video analytics justify its pipeline architecture. NVIDIA documents detector + tracker pipelines and tuning workflows. citeturn1search0turn1search2

Neither is automatically adopted.

---

# 27. Visual inference hierarchy

Novi should use the smallest adequate model.

```text
T0  geometry / deterministic checks
 ↓
T1  lightweight always-on vision
 ↓
T2  specialist detector/segmenter/depth/tracker
 ↓
T3  multimodal visual understanding
 ↓
T4  deliberative reasoning
 ↓
T5  world prediction / embodied model
```

This hierarchy prevents expensive models from becoming the default path for ordinary perception.

---

# 28. Performance requirements

Final numerical requirements must be established by benchmark, not guessed.

Measure at minimum:

- capture latency;
- preprocessing latency;
- inference P50/P95/P99;
- tracking latency;
- fusion latency;
- end-to-end sensor-to-evidence latency;
- frame drops;
- GPU utilization;
- CPU utilization;
- memory;
- power;
- thermal behavior;
- recovery time.

For always-on safety-relevant perception, worst-case and degraded-mode behavior matter more than average FPS.

NVIDIA publishes performance measurements for Isaac ROS components across AGX Orin, Orin NX and discrete GPUs, but Novi must benchmark its exact sensor configuration and workload before making hardware decisions. citeturn1search3

---

# 29. Validation matrix

Every adopted visual capability requires:

### Functional

- correct output schema;
- correct coordinate frame;
- correct timestamp;
- expected behavior across representative scenes.

### Accuracy

- detection metrics;
- segmentation metrics;
- depth error;
- tracking metrics;
- pose error;
- localization error;
- false positive/negative analysis.

### Temporal

- latency;
- jitter;
- stale-data handling;
- dropped frames;
- recovery.

### Robustness

- lighting;
- blur;
- occlusion;
- clutter;
- sensor failure;
- adversarial/ambiguous cases.

### Safety

- no direct actuation authority;
- invalid-data rejection;
- bounded stale-state use;
- safe degraded operation.

### Reproducibility

- model digest;
- calibration version;
- preprocessing version;
- runtime version;
- hardware;
- dataset version;
- configuration digest.

---

# 30. Required visual evidence contract

Every visual observation entering the brain must be traceable to:

```text
observation_id
sensor_id
frame_id
capture_timestamp
processing_timestamp
frame_of_reference
calibration_id
model_id/version if applicable
preprocessing version
source type
quality
confidence/uncertainty
upstream observation IDs
runtime version
```

The brain must be able to answer:

> What did Novi see, when did it see it, how did it infer it, from which sensor/model, and how certain was it?

---

# 31. Recommended initial Novi visual stack

**Development / simulation:**

- Isaac Sim camera/depth/semantic outputs;
- ROS 2 Jazzy interface;
- RViz2/replay tooling;
- synthetic ground truth datasets.

**General robotics perception candidates:**

- Isaac ROS image processing;
- Isaac ROS Visual SLAM;
- Isaac ROS Nvblox;
- specialist detection/segmentation/depth models;
- ROS 2 image/TF interfaces.

**Streaming video candidate:**

- DeepStream when multi-stream/high-throughput processing justifies it.

**Higher-level understanding:**

- VLM routed through Novi's model runtime, not directly embedded in the sensor driver.

This is a candidate baseline, not an adoption decision.

---

# 32. Decisions deliberately deferred

The following must not be finalized until benchmarks exist:

- exact camera models;
- camera count;
- stereo baseline;
- depth sensor;
- LiDAR requirement;
- detector model;
- segmentation model;
- depth model;
- face/identity model;
- tracker;
- VSLAM implementation;
- Nvblox adoption;
- DeepStream adoption;
- Jetson model;
- TensorRT optimization;
- VLM selection;
- perception frame rates.

---

# 33. Critical invariants

1. **Visual inference is evidence, not truth.**
2. **Detection is not identity.**
3. **Prediction is not observation.**
4. **Simulation is not reality.**
5. **A stale observation cannot silently become current.**
6. **A failed sensor must become explicit degraded state.**
7. **Calibration is versioned.**
8. **Time and coordinate frames are part of every spatial observation.**
9. **No visual model directly commands actuators.**
10. **Privacy controls apply to person-related perception.**
11. **Raw frames are not automatically long-term memory.**
12. **The smallest adequate model should be preferred.**
13. **Every important perception result must be reproducible from provenance.**
14. **Novi must remain perceptually alive even when expensive cognition is unavailable.**

---

# 34. Acceptance gate

This document is not implementation-complete until:

- [ ] visual evidence schema is executable;
- [ ] sensor interface contract is executable;
- [ ] camera calibration artifact is defined;
- [ ] simulation camera dataset exists;
- [ ] baseline detector benchmark exists;
- [ ] tracking benchmark exists;
- [ ] depth benchmark exists;
- [ ] visual latency budget exists;
- [ ] failure injection tests exist;
- [ ] privacy policy is implemented;
- [ ] model candidates are benchmarked;
- [ ] Isaac ROS candidates are tested;
- [ ] hardware workload benchmark is completed;
- [ ] all adopted components have ADRs;
- [ ] real-world validation dataset exists before claiming real-world readiness.

---

# 35. Conclusion

Novi's visual system is not a camera connected to an AI model.

It is a continuous sensory intelligence pipeline that turns physical photons into temporally and spatially grounded evidence, maintains uncertainty, tracks change, selectively reasons about important visual events, and continuously supplies the rest of the brain with a changing model of the world.

That architecture is what allows Novi to **look around, notice people, notice changes, understand where things are, react quickly, remember meaningful experiences and remain perceptually present even when higher-level cognition is idle.**

NVIDIA's current Isaac ROS and Isaac Sim ecosystems provide strong candidate building blocks for this pipeline, but Novi-specific validation remains mandatory before adoption. citeturn1search3turn0search0
