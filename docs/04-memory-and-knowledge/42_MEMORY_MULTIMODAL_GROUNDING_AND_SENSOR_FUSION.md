# 42 — Memory Multimodal Grounding and Sensor Fusion

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## High-Level Description

This document defines how Novi combines information from multiple physical and digital modalities into grounded representations of the world and of Novi's own state.

Novi will have multiple cameras, LiDAR, microphones, speakers, IMU/gyroscope, GNSS/GPS, thermal sensing, displays, lighting, power/thermal telemetry and other sensors. No single sensor is assumed to be universally authoritative. Each modality has different strengths, failure modes, latency, resolution, uncertainty and environmental limitations.

The architecture therefore treats sensor fusion as a layered evidence problem:

```text
RAW SENSOR DATA
      ↓
CALIBRATION / TIME ALIGNMENT
      ↓
PER-SENSOR QUALITY ESTIMATION
      ↓
FEATURES / OBSERVATIONS
      ↓
GEOMETRIC + SEMANTIC ASSOCIATION
      ↓
STATE ESTIMATION / FUSION
      ↓
GROUNDED WORLD MODEL
      ↓
COGNITION / MEMORY / AUTONOMY
```

The system must preserve provenance so Novi can distinguish:

- what a sensor directly observed;
- what a fusion algorithm estimated;
- what a model inferred;
- what cognition hypothesized;
- what has subsequently been verified.

## Core Principle

> **Novi must fuse evidence without erasing uncertainty, provenance, timing, modality differences or contradictions.**

---

## 1. Why Multimodal Fusion Exists

Different sensors answer different questions.

| Modality | Typical strengths | Typical limitations |
|---|---|---|
| RGB camera | appearance, text, color, recognition | lighting, occlusion, depth ambiguity |
| Depth camera | local depth geometry | range, reflective/transparent surfaces, lighting depending on technology |
| LiDAR | geometry, ranging, mapping | material/reflectivity effects, sparse semantics |
| IMU | rapid motion/orientation dynamics | drift over time |
| GNSS/GPS | global outdoor position | poor indoors/urban obstruction, signal dependence |
| Thermal | temperature patterns, heat sources | lower spatial detail, emissivity/environment effects |
| Microphone array | speech/audio and direction-of-arrival | noise, reverberation, occlusion |
| Wheel/actuator odometry | motion estimate | slip, mechanical error |
| Power/BMS | battery and electrical state | does not describe external world |
| System telemetry | compute/thermal health | internal-only |

Fusion should exploit complementary information rather than force every sensor into one universal representation.

---

## 2. Sensor Evidence Hierarchy

The architecture distinguishes:

```text
RAW MEASUREMENT
    ↓
CALIBRATED MEASUREMENT
    ↓
OBSERVATION
    ↓
ESTIMATE
    ↓
INTERPRETATION
    ↓
KNOWLEDGE
```

For example:

```text
LiDAR returns point
      ↓
point cloud
      ↓
obstacle observation
      ↓
tracked obstacle estimate
      ↓
"chair"
      ↓
semantic knowledge candidate
```

Each transition must remain traceable.

---

## 3. No Single-Sensor Truth Rule

Novi must not automatically trust a modality simply because it is normally reliable.

Instead, trust should depend on:

- sensor health;
- calibration;
- timestamp quality;
- environmental suitability;
- measurement consistency;
- expected operating range;
- recent failures;
- cross-modal agreement.

Example:

```text
Camera says: object present
LiDAR says: geometry present
Thermal says: warm region

→ stronger combined evidence
```

But disagreement must remain representable.

---

## 4. Sensor Identity

Every sensor should have a stable logical identity.

At minimum:

- sensor ID;
- modality;
- hardware component ID;
- physical frame;
- calibration version;
- firmware/software version;
- capability profile;
- health state.

Historical observations must retain the sensor identity that produced them.

---

## 5. Coordinate Frames

All spatial sensors must be connected to a controlled transform tree.

Conceptually:

```text
world
  ↓
map
  ↓
odom
  ↓
base_link
  ├── camera_front
  ├── camera_rear
  ├── camera_left
  ├── camera_right
  ├── lidar
  ├── imu
  ├── thermal_camera
  └── microphone_array
```

The exact tree will be defined by the hardware and robotics architecture.

NVIDIA Isaac Sim's ROS 2 documentation explicitly uses TF trees to represent sensor positions and supports publishing camera transforms and odometry; this is a suitable implementation reference rather than a requirement that Novi's semantic layer be NVIDIA-specific. citeturn0search5

---

## 6. Calibration

Fusion is only as good as calibration.

Required calibration classes may include:

- camera intrinsics;
- camera distortion;
- camera-to-camera extrinsics;
- camera-to-LiDAR extrinsics;
- IMU alignment;
- thermal-camera calibration;
- microphone geometry;
- actuator/odometry calibration;
- GNSS antenna reference;
- temporal offsets.

Calibration records must be versioned.

---

## 7. Calibration Validity

Every fusion-critical calibration should have a status:

```text
VALID
DEGRADED
EXPIRED_FOR_REVIEW
INVALID
UNKNOWN
```

An invalid calibration must reduce or block use of the affected fusion path where required.

---

## 8. Time Synchronization

Multimodal fusion requires accurate temporal relationships.

Each measurement should carry:

- sensor timestamp;
- acquisition timestamp where available;
- ingestion timestamp;
- processing timestamp;
- clock/source information;
- synchronization quality.

Novi must not silently treat asynchronously captured measurements as simultaneous.

NVIDIA's Isaac Sim multi-sensor ROS 2 examples explicitly emphasize common timestamps and simulation time when visualizing multiple sensor streams. citeturn0search0turn0search1

---

## 9. Latency Awareness

Each observation should retain relevant latency metadata.

For example:

```text
camera frame captured T0
processed T0 + 80 ms
workspace assembled T0 + 120 ms
```

A moving object can change substantially during this interval.

Fusion must account for this where the estimator requires it.

---

## 10. Sensor Quality Score

Each observation may include a quality descriptor based on measurable factors.

Possible fields:

```text
signal_quality
calibration_quality
temporal_quality
range_validity
occlusion
noise_estimate
health_state
```

A quality score is metadata, not a universal truth probability.

---

## 11. Sensor Health

Sensor health should be supplied by the hardware/runtime layer whenever possible.

Examples:

```text
camera_front = healthy
lidar = degraded
thermal = unavailable
imu = healthy
microphone_array = healthy
```

Fusion should consume this state.

---

## 12. Camera Fusion

Multiple cameras can provide:

- wider field of view;
- overlapping views;
- depth/stereo information;
- tracking continuity;
- redundancy;
- semantic recognition;
- visual localization.

The architecture should maintain camera-specific observations before merging them into higher-level tracks.

---

## 13. Camera-to-LiDAR Fusion

Camera and LiDAR provide complementary information.

Conceptually:

```text
camera image
    +
LiDAR point cloud
    ↓
spatial registration
    ↓
object / surface association
    ↓
3D semantic observation
```

The association must depend on calibrated transforms and timestamps.

NVIDIA Isaac Sim supports camera and RTX LiDAR simulation and ROS 2 publication of point clouds and laser scans, making it useful for testing these interfaces before hardware is available. citeturn0search0turn0search2

---

## 14. Thermal Fusion

Thermal sensing should be treated as an independent modality.

Potential uses include:

- identifying warm/cold regions;
- detecting heat sources;
- assisting object/environment interpretation;
- detecting abnormal internal temperature;
- improving perception in some lighting conditions.

Thermal readings must not automatically be interpreted as object identity or human emotion.

---

## 15. Internal vs External Thermal Sensing

Novi needs two conceptually separate thermal systems:

```text
INTERNAL THERMAL STATE
  CPU/GPU
  battery
  motors
  power electronics
  enclosure zones

EXTERNAL THERMAL PERCEPTION
  environment
  objects
  surfaces
  heat sources
```

Internal thermal state is authoritative for system protection.

External thermal perception is environmental evidence.

---

## 16. Audio Fusion

The microphone array should support:

- speech capture;
- direction-of-arrival estimation;
- source separation where feasible;
- acoustic event detection;
- speaker association hypotheses.

Audio localization must retain uncertainty.

Example:

```text
source direction = 42°
uncertainty = ±8°
```

---

## 17. Audio-Visual Association

Novi should be able to associate:

```text
voice direction
      +
camera observation
      +
tracking
      ↓
possible speaking person
```

This is an association hypothesis, not automatic identity verification.

---

## 18. Speaker Identity Boundary

A voice can be evidence for identity but must not automatically establish identity.

```text
voice similarity
      ↓
identity candidate
      ↓
additional evidence
      ↓
identity confidence
```

Authorization remains a separate security system.

---

## 19. IMU Fusion

IMU data is useful for:

- rapid orientation estimation;
- motion detection;
- inertial propagation;
- stabilization;
- detecting sudden movement.

IMU drift requires correction using additional information such as visual, LiDAR, wheel or GNSS observations.

---

## 20. State Estimation

The fused state may include:

```text
position
orientation
linear velocity
angular velocity
acceleration
covariance/uncertainty
```

The estimator must expose uncertainty rather than returning only a point estimate.

ROS ecosystem research includes state-estimation approaches capable of fusing multiple sensor inputs, including configurable combinations of sensor fields. This is an implementation reference for Novi's estimator layer, not a mandate to use a specific package. citeturn0search24

---

## 21. Localization Sources

Novi may combine:

```text
IMU
+ wheel/odometry
+ camera/VIO
+ LiDAR localization
+ GNSS
+ map matching
```

The estimator should dynamically account for source availability and quality.

---

## 22. Indoor / Outdoor Localization

The localization architecture must support different environments.

### Indoors

Prefer combinations such as:

- LiDAR;
- visual odometry;
- IMU;
- map matching;
- wheel odometry.

### Outdoors

Potentially add:

- GNSS;
- visual localization;
- LiDAR;
- IMU;
- odometry.

GNSS must not be assumed available merely because hardware exists.

---

## 23. GPS/GNSS as Evidence

GNSS should produce observations with quality metadata such as:

- fix type;
- estimated accuracy;
- satellite/solution quality where available;
- timestamp;
- source;
- covariance/uncertainty.

A poor GNSS solution should not override a stronger local estimate merely because it is globally referenced.

---

## 24. Map Fusion

Novi's spatial memory should combine:

```text
local sensor observations
        ↓
localization
        ↓
map representation
        ↓
place/landmark memory
        ↓
visited-area history
```

Historical maps and current observations must remain distinguishable.

---

## 25. World Model

The fused world model should represent entities such as:

```text
objects
people
rooms
surfaces
obstacles
places
routes
heat sources
sound sources
robot pose
```

Each entity should retain:

- source observations;
- timestamps;
- confidence/uncertainty;
- spatial extent;
- semantic labels;
- track identity where applicable;
- provenance.

---

## 26. Track Identity

An object track is not necessarily a permanent identity.

```text
track_17
```

means:

> the system believes these observations belong to the same physical entity over a period.

It does not automatically mean:

> this is permanently object/person X.

---

## 27. Cross-Modal Association

Association should consider:

- spatial proximity;
- temporal proximity;
- motion consistency;
- appearance;
- geometry;
- audio direction;
- thermal pattern;
- semantic compatibility.

No single association signal should automatically dominate all contexts.

---

## 28. Contradictory Sensors

Contradictions are expected.

Example:

```text
camera → object at 2 m
LiDAR  → geometry at 2.4 m
```

The system should preserve the discrepancy and evaluate:

- calibration;
- timestamp offset;
- sensor noise;
- object motion;
- occlusion;
- measurement geometry.

It must not silently average contradictory evidence when doing so could hide a fault.

---

## 29. Sensor Failure Detection

Persistent disagreement can indicate:

- sensor failure;
- calibration drift;
- transform error;
- clock error;
- environmental limitation;
- model failure.

Cross-modal disagreement should therefore contribute to diagnostics.

---

## 30. Graceful Degradation

If one modality fails:

```text
camera failure
   ↓
LiDAR + IMU + other sensors
   ↓
reduced capability
```

Novi should continue if safe and sufficiently observable.

This supports the broader requirement that Novi remain locally functional and not depend on one external service.

---

## 31. Missing Data

Missing observations must be explicit.

Valid states include:

```text
NOT_AVAILABLE
NOT_DETECTED
NOT_MEASURED
INVALID
DROPPED
UNKNOWN
```

These must not be encoded as ordinary zero values.

---

## 32. Sensor Dropout

Fusion pipelines should tolerate temporary dropout where the estimator can safely propagate state.

Long dropout should increase uncertainty and eventually trigger degraded mode or recovery behavior.

---

## 33. Occlusion

Visual occlusion should be represented explicitly where possible.

For example:

```text
object was tracked
camera view lost
LiDAR still sees geometry
```

The track may continue with reduced semantic certainty.

---

## 34. Environmental Conditions

Fusion quality can depend on:

- darkness;
- bright sunlight;
- fog;
- rain;
- reflective surfaces;
- transparent surfaces;
- dust;
- thermal gradients;
- acoustic reverberation;
- electromagnetic interference.

The perception stack should expose relevant degradation indicators.

---

## 35. Semantic Fusion

Semantic fusion combines modality-specific interpretations.

Example:

```text
camera detector:
chair, 0.86

LiDAR geometry:
vertical object cluster

map:
known chair location

→ stronger grounded chair hypothesis
```

The final semantic representation must retain its constituent evidence.

---

## 36. Language Grounding

Language references should resolve against the fused world model.

Example:

> "Bring me the red cup."

Possible grounding pipeline:

```text
language
 ↓
object constraints:
  type = cup
  color = red
 ↓
world model candidates
 ↓
spatial/contextual ranking
 ↓
candidate object
 ↓
verification
```

If multiple candidates remain, Novi should clarify or gather additional evidence.

---

## 37. Pointing and Gesture Grounding

If supported by perception, pointing/gaze can contribute to language grounding.

```text
"that one"
   +
pointing direction
   +
objects in direction
   ↓
candidate reference
```

Gesture evidence remains uncertain and context-dependent.

---

## 38. Active Sensor Selection

Novi may actively change sensing behavior when uncertainty justifies the cost.

Examples:

```text
uncertain object
  ↓
rotate camera

uncertain sound source
  ↓
orient microphone/camera

uncertain obstacle
  ↓
use LiDAR/depth

uncertain thermal condition
  ↓
request thermal observation
```

This must be bounded by safety and resource policies.

---

## 39. Sensor Scheduling

Sensors should have configurable operating modes:

```text
OFF
LOW_RATE
NORMAL
HIGH_RATE
BURST
SAFETY_CRITICAL
```

The scheduler may adjust rates based on:

- task;
- motion;
- uncertainty;
- battery;
- thermal state;
- compute pressure.

---

## 40. Sensor Fusion and Attention

Attention should determine when deeper fusion is worth the cost.

```text
routine observation
 → lightweight processing

uncertain/high-value observation
 → deeper multimodal fusion
```

This prevents every sensor from being processed at maximum complexity continuously.

---

## 41. Resource-Aware Fusion

Fusion workloads must respond to:

- GPU utilization;
- CPU utilization;
- memory pressure;
- thermal state;
- power consumption;
- inference latency.

Optional fusion should be reduced before critical localization/safety functions.

---

## 42. NVIDIA / Isaac ROS Strategy

NVIDIA Isaac ROS is a strong candidate for accelerated ROS 2 perception and sensor-processing components on Jetson. NVIDIA describes Isaac ROS as high-performance, low-latency ROS 2 packages designed for autonomous robots and Jetson/NVIDIA platforms. citeturn0search9

Relevant NVIDIA/Isaac capabilities should be evaluated for:

- camera processing;
- image transport;
- visual odometry/VSLAM;
- LiDAR processing;
- depth;
- object detection;
- segmentation;
- GPU-accelerated data movement;
- simulation/testing.

But Novi's canonical fusion interfaces remain vendor-neutral.

---

## 43. NVIDIA Is Not the Only Implementation

The architecture explicitly permits:

- NVIDIA Isaac ROS;
- ROS 2 ecosystem packages;
- OpenCV;
- PyTorch;
- TensorFlow;
- ONNX Runtime;
- Hugging Face models;
- custom C++/Python components;
- other open-source robotics/perception systems.

Selection criteria are:

1. open-source availability where possible;
2. local execution;
3. hardware compatibility;
4. accuracy;
5. latency;
6. power consumption;
7. reliability;
8. maintainability;
9. license compatibility;
10. reproducibility.

Cloud services are exceptional fallbacks only where no acceptable local solution exists.

---

## 44. Simulation

Multimodal fusion should be testable in simulation before hardware deployment.

Isaac Sim currently supports simulated cameras, LiDAR, ROS 2 bridges, transforms, timestamps and multi-sensor visualization. citeturn0search0turn0search4turn0search5

Simulation should test:

- sensor placement;
- calibration;
- timing;
- noise;
- occlusion;
- missing sensors;
- environmental changes;
- fusion algorithms;
- failure recovery.

---

## 45. Real Hardware Validation

Simulation is not sufficient.

Hardware validation must test:

- real sensor latency;
- real calibration error;
- mechanical vibration;
- thermal effects;
- electromagnetic interference;
- lighting;
- acoustic environment;
- sensor mounting tolerances;
- real-world failure modes.

---

## 46. Data Recording

Sensor-fusion development should support local recording of synchronized datasets.

Recordings should include:

- sensor data or references;
- timestamps;
- TF/calibration state;
- software/model versions;
- hardware configuration;
- environment metadata where appropriate;
- resulting fused state.

Privacy-sensitive recordings must follow retention policy.

---

## 47. Deterministic Replay

Recorded sensor sessions should be replayable where technically feasible.

```text
recorded sensors
      ↓
replay
      ↓
same fusion pipeline
      ↓
compare outputs
```

This enables regression testing without requiring repeated physical experiments.

---

## 48. Provenance

Every fused observation should be able to answer:

```text
Which sensors contributed?
Which timestamps?
Which calibration?
Which transforms?
Which algorithm/model?
Which software version?
What uncertainty?
What quality checks?
```

This is essential for debugging and memory provenance.

---

## 49. Memory Admission

Not every fused observation becomes memory.

The memory admission layer decides whether an observation is:

```text
transient
working context
episodic candidate
semantic candidate
spatial memory candidate
health event
learning candidate
```

Fusion should therefore provide evidence, not decide retention by itself.

---

## 50. World Model vs Memory

The world model represents current estimated reality.

Memory represents retained history.

```text
CURRENT WORLD MODEL
"What is probably true now?"

MEMORY
"What has Novi retained about what happened before?"
```

A stale memory must not override current sensor evidence without explicit reasoning.

---

## 51. Uncertainty Propagation

Fusion should propagate uncertainty where practical.

For example:

```text
camera localization uncertainty
        +
IMU uncertainty
        +
LiDAR uncertainty
        ↓
pose estimate + covariance
```

Downstream systems should be able to use that uncertainty.

---

## 52. Confidence Is Not Probability by Default

A value called `confidence` must have a defined meaning.

Novi should not mix:

- classifier confidence;
- estimator covariance;
- heuristic quality score;
- epistemic uncertainty;
- aleatoric uncertainty.

Schemas should name these quantities precisely.

---

## 53. Contradiction Preservation

The fusion layer should preserve important conflicts.

Example:

```text
Observation A: person at location X
Observation B: no person at X
```

Rather than immediately deleting one observation, the system may retain:

- timestamps;
- sensor identities;
- quality;
- possible explanations;
- final resolution.

This is valuable for diagnostics and learning.

---

## 54. Safety-Critical Fusion

Safety functions must define their own sensor redundancy and failure policy.

The general cognitive fusion layer must not assume that a general-purpose perception model is sufficient for safety.

Safety-critical decisions should use validated, deterministic or appropriately certified mechanisms where required by the target application.

---

## 55. Security

Sensor data is an input boundary.

The system must consider:

- spoofed inputs;
- replayed messages;
- malformed data;
- compromised peripherals;
- time manipulation;
- false transforms;
- unauthorized sensor configuration.

Sensor data should not automatically become trusted facts merely because it arrived through an internal software interface.

---

## 56. Privacy

Cameras, microphones, GNSS and thermal sensors can produce sensitive information.

Fusion can increase sensitivity because multiple modalities may jointly reveal more than any individual sensor.

Therefore:

```text
fusion capability
    ≠
unlimited retention
```

Privacy policy applies to fused representations as well as raw data.

---

## 57. Offline Operation

Core fusion must operate without Wi-Fi, Bluetooth or cloud access.

```text
network unavailable
      ↓
local sensors
      ↓
local fusion
      ↓
local world model
      ↓
local cognition/autonomy
```

External services may enrich information when explicitly enabled but cannot be required for basic embodied operation.

---

## 58. Failure Modes

The architecture must test:

- camera failure;
- LiDAR failure;
- IMU drift;
- GNSS dropout;
- microphone failure;
- thermal sensor failure;
- clock drift;
- transform corruption;
- calibration corruption;
- sensor disagreement;
- high latency;
- packet loss;
- duplicated measurements;
- out-of-order measurements;
- stale measurements;
- compute overload;
- thermal throttling;
- low battery;
- network loss.

---

## 59. Fusion Recovery

Recovery should follow:

```text
fault detected
   ↓
identify affected modality
   ↓
down-weight / disable affected path
   ↓
recompute state if possible
   ↓
increase uncertainty
   ↓
notify cognition
   ↓
repair / recalibrate / recover
   ↓
validate before restoring full trust
```

A recovered sensor should not instantly return to full trust without health validation.

---

## 60. Testing Matrix

Testing must include:

### Temporal

- synchronized streams;
- offset streams;
- jitter;
- clock drift;
- delayed measurements.

### Spatial

- correct calibration;
- calibration error;
- transform error;
- moving sensors;
- mechanical shifts.

### Environmental

- darkness;
- bright light;
- reflective surfaces;
- transparent surfaces;
- noise;
- heat/cold;
- outdoor GNSS conditions.

### Failure

- missing sensors;
- corrupted messages;
- intermittent sensors;
- sensor replacement;
- thermal throttling.

### Semantic

- ambiguous objects;
- conflicting labels;
- multiple people;
- multiple sound sources;
- language references.

---

## 61. Evaluation Metrics

Measure at least:

- localization accuracy;
- tracking accuracy;
- sensor-fusion latency;
- synchronization error;
- false association rate;
- missed detection rate;
- identity-switch rate;
- uncertainty calibration;
- degraded-mode performance;
- recovery time;
- compute utilization;
- power consumption;
- thermal impact.

Metrics must be evaluated on representative Novi hardware and environments.

---

## 62. Architectural Invariants

1. No sensor is universally authoritative for every problem.
2. Raw measurement, observation, estimate and knowledge remain distinct.
3. Sensor provenance is preserved.
4. Sensor timestamps are mandatory for fusion-relevant data.
5. Calibration is versioned and validity-aware.
6. Coordinate transforms are explicit and controlled.
7. Uncertainty is preserved where practical.
8. Contradictions are not silently erased when they may indicate faults.
9. Missing data is explicit.
10. Sensor failure causes graceful degradation where safe.
11. Recovered sensors require validation before full trust.
12. Current world state and historical memory remain separate.
13. Language grounding uses the fused world model rather than raw guesses.
14. Sensor fusion does not automatically create durable memory.
15. Safety-critical fusion has independent requirements.
16. Core fusion works locally without network access.
17. NVIDIA components are candidates, not mandatory dependencies.
18. Open-source/local solutions are preferred when they meet requirements.
19. Cloud services are exceptional fallbacks.
20. Simulation is valuable but cannot replace hardware validation.
21. Deterministic replay should be supported where feasible.
22. Privacy applies to raw and fused sensor information.
23. Sensor data is an input boundary and must be treated as potentially untrusted.

---

## 63. Reference Implementation Direction

The initial implementation should be layered rather than monolithic:

```text
Sensor Drivers
      ↓
ROS 2 Interfaces
      ↓
Time + TF + Calibration
      ↓
Per-Sensor Preprocessing
      ↓
State Estimation / Tracking
      ↓
Multimodal Association
      ↓
World Model
      ↓
Memory / Knowledge
      ↓
Cognitive Workspace
```

Potential technologies should be selected through benchmarked adapters rather than embedded directly into semantic contracts.

NVIDIA Isaac ROS should be evaluated first for Jetson-accelerated robotics/perception components because it is designed around ROS 2 and NVIDIA hardware, while alternatives remain explicitly permitted. citeturn0search9

---

## 64. Final Principle

> **Novi should not merely collect many sensors; it should understand what each sensor knows, what each sensor cannot know, how reliable the evidence is, when the measurements occurred, how they relate spatially, and how multiple independent observations change the overall estimate.**

The result should be a grounded, uncertainty-aware world model that can support memory, language, cognition and autonomy without pretending that inference is observation or that confidence is certainty.
