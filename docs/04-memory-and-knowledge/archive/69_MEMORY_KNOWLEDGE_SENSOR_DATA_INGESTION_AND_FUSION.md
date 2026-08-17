# 69 — Memory Knowledge Sensor Data Ingestion and Fusion

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi acquires, timestamps, validates, calibrates, synchronizes, fuses, stores, and reasons over physical-world sensor data.

This document connects Novi's hardware/sensor architecture with perception, localization, world-state estimation, memory, knowledge, safety, and learning.

## Core Principle

> **A sensor measurement is evidence about the physical world, not automatically ground truth. Sensor fusion must preserve uncertainty, provenance, timing, calibration, sensor health, and disagreement.**

NIST guidance on cyber-physical systems emphasizes accurate sensor timestamps and reference time; NIST's spatial/temporal alignment work also treats alignment of disparate sensor streams as a prerequisite for coherent fusion. citeturn0search24turn0search25

NVIDIA Isaac ROS similarly exposes explicit synchronization thresholds, camera/IMU fusion, frame transforms and sensor-specific calibration in its robotics pipelines. citeturn0search2turn0search3

---

## 1. Sensor Families

Novi's planned sensor architecture may include:

```text
VISION
 ├── RGB cameras
 ├── stereo/depth cameras
 └── wide-angle/peripheral cameras

DEPTH / GEOMETRY
 ├── LiDAR
 └── depth sensors

THERMAL
 ├── environmental temperature
 ├── internal thermal sensors
 └── thermal imaging where required

AUDIO
 ├── microphone array
 └── speaker/actuator state

MOTION
 ├── IMU
 ├── gyroscope
 ├── accelerometer
 └── magnetometer where useful

POSITION
 ├── GNSS/GPS
 └── local positioning / localization

PROXIMITY / ENVIRONMENT
 ├── ToF/proximity
 ├── ambient light
 ├── pressure where useful
 └── other environment sensors

SYSTEM HEALTH
 ├── CPU/GPU temperature
 ├── battery voltage/current
 ├── battery temperature
 ├── motor state
 ├── storage health
 └── sensor health
```

The final sensor list is governed by the hardware architecture documents.

---

## 2. Sensor Data Is Layered

Novi must distinguish:

```text
RAW MEASUREMENT
      ↓
VALIDATED MEASUREMENT
      ↓
CALIBRATED MEASUREMENT
      ↓
TIME-ALIGNED MEASUREMENT
      ↓
OBSERVATION
      ↓
FUSED STATE ESTIMATE
      ↓
INTERPRETED PERCEPTION
      ↓
WORLD MODEL
      ↓
MEMORY / KNOWLEDGE
```

Each layer has different uncertainty and provenance.

---

## 3. Raw Data Preservation

Raw sensor data should be retained only where required by policy, debugging, safety, calibration, research, or audit requirements.

When raw data is not retained, derived observations must preserve sufficient provenance for the applicable purpose.

Privacy policy applies to raw sensor streams.

---

## 4. Sensor Identity

Every sensor should have a stable identity and metadata including where practical:

- sensor ID;
- sensor type;
- physical mounting location;
- orientation;
- calibration version;
- firmware version;
- sampling characteristics;
- driver/interface version;
- health state.

---

## 5. Coordinate Frames

Physical measurements must declare their coordinate frame where applicable.

Conceptually:

```text
world / map
     ↓
odometry
     ↓
robot/base
     ↓
sensor frame
```

Transforms must be versioned and validated.

A measurement without a known frame must not be silently treated as if it were in the correct frame.

---

## 6. Extrinsic Calibration

Novi must maintain the spatial relationship between sensors and the robot body.

Examples:

```text
camera → base
LiDAR  → base
IMU    → base
thermal → base
```

Changes in physical mounting require calibration validation.

---

## 7. Intrinsic Calibration

Sensor-specific calibration must be represented where applicable:

- camera intrinsics;
- lens distortion;
- depth calibration;
- LiDAR characteristics;
- IMU calibration/noise model;
- microphone geometry;
- thermal sensor calibration.

Calibration versions belong in sensor provenance.

---

## 8. Calibration Is Not Permanent

Calibration can drift because of:

- mechanical movement;
- temperature;
- aging;
- impact;
- sensor replacement;
- firmware changes.

Novi should detect conditions requiring recalibration or validation.

---

## 9. Timestamping

Every sensor measurement should carry an explicit timestamp.

Where possible distinguish:

```text
sensor acquisition time
hardware timestamp
transport time
ingestion time
processing time
```

These timestamps must not be conflated.

NIST specifically identifies timestamp accuracy and stable reference time as important for sensor data integration. citeturn0search24

---

## 10. Time Synchronization

Sensor fusion requires appropriate temporal alignment.

```text
camera @ t1
IMU    @ t2
LiDAR  @ t3
GPS    @ t4
        ↓
TIME ALIGNMENT
        ↓
FUSION WINDOW
```

The required synchronization tolerance is application-dependent and must be defined per fusion pipeline rather than globally assumed.

NVIDIA's current robotics tooling exposes explicit synchronization thresholds for multi-camera pipelines, illustrating that synchronization is an engineering parameter rather than an implicit guarantee. citeturn0search2turn0search7

---

## 11. Clock Health

Monitor:

- clock drift;
- offset;
- timestamp discontinuity;
- synchronization loss;
- monotonicity violations.

If timing becomes unreliable, affected fusion outputs must be degraded or rejected as appropriate.

---

## 12. Measurement Quality

Each measurement or derived observation should carry quality information where practical:

```text
VALID
DEGRADED
STALE
OUTLIER
MISSING
UNAVAILABLE
```

Quality is distinct from truth.

---

## 13. Sensor Health

Sensor health should consider:

- heartbeat;
- expected rate;
- dropped messages;
- noise;
- saturation;
- temperature;
- calibration validity;
- communication errors;
- physical obstruction;
- self-test state.

---

## 14. Sensor Failure

If a sensor fails:

```text
sensor failure
      ↓
health state
      ↓
remove/reduce sensor contribution
      ↓
fallback / degraded fusion
```

The fusion system must not continue treating failed data as healthy.

---

## 15. Sensor Disagreement

Sensors may disagree.

Example:

```text
camera → object at 2.0 m
LiDAR  → object at 2.4 m
```

Novi should preserve the disagreement and evaluate:

- timing;
- calibration;
- occlusion;
- measurement uncertainty;
- sensor health;
- environmental conditions.

It must not simply average contradictory measurements without considering uncertainty.

---

## 16. Outlier Rejection

Fusion pipelines should identify implausible measurements using appropriate statistical, physical, temporal, or model-based checks.

An outlier should be marked rather than silently deleted when provenance matters.

---

## 17. Sensor Fusion

Fusion may combine complementary modalities:

```text
RGB
 + depth
 + LiDAR
 + IMU
 + GPS
      ↓
FUSED STATE
```

Fusion algorithms may include filters, optimization, probabilistic estimation, learned models, or combinations thereof.

The algorithm choice belongs to the relevant subsystem implementation.

---

## 18. Uncertainty Propagation

Fusion must propagate or otherwise represent uncertainty.

```text
measurement uncertainty
       ↓
fused uncertainty
       ↓
world-state confidence
```

A fused estimate should not appear more certain merely because more sensors were involved.

---

## 19. Correlated Sensors

Multiple sensors may share correlated error sources.

Examples:

- common clock;
- common calibration error;
- common model;
- same physical obstruction;
- same environmental artifact.

Therefore:

```text
3 sensors agree
```

does not automatically mean three independent confirmations.

---

## 20. Sensor Independence

Fusion metadata should preserve enough information to reason about whether evidence is independent or correlated.

This connects directly to external evidence cross-validation in document 66.

---

## 21. Camera Pipeline

Camera data may flow through:

```text
image
 ↓
quality check
 ↓
calibration / rectification
 ↓
time alignment
 ↓
perception
 ↓
tracking
 ↓
3D association
 ↓
world state
```

NVIDIA Isaac ROS supports stereo and visual SLAM pipelines with explicit camera synchronization and calibration parameters, providing a practical reference architecture. citeturn0search2turn0search5

---

## 22. LiDAR Pipeline

LiDAR should preserve:

- timestamp;
- sensor frame;
- calibration;
- point validity;
- range/intensity information where available;
- environmental limitations.

LiDAR may contribute to:

- obstacle detection;
- geometry;
- mapping;
- localization;
- free-space estimation.

---

## 23. Thermal Pipeline

Thermal sensing should support two distinct goals:

```text
ENVIRONMENTAL THERMAL PERCEPTION
        ↓
where is hot/cold?

SYSTEM THERMAL HEALTH
        ↓
is Novi overheating?
```

These must not be conflated.

Internal thermal sensors should be authoritative for protected component temperature where appropriately placed; thermal cameras/sensors can provide environmental information.

---

## 24. Audio Pipeline

Multiple microphones should support:

```text
audio
 ↓
quality
 ↓
time alignment
 ↓
voice activity
 ↓
direction-of-arrival estimation
 ↓
speaker/scene analysis
```

Direction of arrival is an estimate and can degrade due to:

- reverberation;
- noise;
- occlusion;
- microphone mismatch;
- multiple simultaneous sources.

---

## 25. Speaker State

Speaker output should be treated as an actuator state, not an environment sensor.

Novi should track:

- playback state;
- volume;
- active channel;
- timing;
- audio route.

This is important for separating Novi's own speech from external sounds.

---

## 26. IMU Pipeline

IMU data should retain:

- accelerometer measurements;
- gyroscope measurements;
- optional magnetometer data;
- timestamp;
- calibration/noise model;
- frame.

IMU data can support:

- orientation estimation;
- motion estimation;
- visual-inertial odometry;
- stabilization;
- event detection.

NVIDIA's visual SLAM tooling explicitly exposes IMU fusion and noise-model parameters, reinforcing the need to model IMU characteristics rather than treating measurements as exact. citeturn0search2

---

## 27. GPS/GNSS Pipeline

GNSS should be treated as one localization source.

Record where available:

- fix type;
- estimated accuracy;
- satellite/solution quality;
- timestamp;
- coordinate reference;
- availability state.

GNSS should not automatically override local localization when its quality is poor.

---

## 28. Indoor Localization

Because Novi is primarily a home robot, indoor localization should not depend on GPS.

Possible local sources include:

```text
visual SLAM
LiDAR SLAM
odometry
IMU
landmarks
map matching
```

The localization architecture should fuse appropriate sources according to environmental conditions.

---

## 29. Outdoor Localization

When outside, Novi may combine:

```text
GNSS
 + visual localization
 + IMU
 + LiDAR / mapping
 + odometry
```

No single source should be assumed universally reliable.

---

## 30. Spatial Memory

Sensor fusion feeds Novi's spatial memory:

```text
sensor observations
      ↓
localization
      ↓
map / world model
      ↓
places / objects / routes
      ↓
spatial memory
```

This supports the requirement that Novi can remember where it has been and build a map over time.

---

## 31. Map Provenance

Every important map layer should retain provenance for:

- sensor source;
- mapping session;
- calibration state;
- time interval;
- localization confidence;
- map version.

---

## 32. Dynamic vs Static World

Novi must distinguish:

```text
STATIC STRUCTURE
walls, floors, fixed furniture

DYNAMIC STATE
people, pets, moved objects, temporary obstacles
```

A person standing in a doorway should not automatically become a permanent wall in long-term spatial memory.

---

## 33. Temporal World State

The world model should preserve time:

```text
object at location A at t1
object at location B at t2
```

This supports movement reasoning and historical spatial memory.

---

## 34. Sensor-to-Memory Provenance

A remembered physical-world claim should be traceable:

```text
memory
 ↓
observation
 ↓
sensor(s)
 ↓
timestamp
 ↓
calibration
 ↓
fusion algorithm/version
 ↓
source measurements
```

This enables later re-evaluation.

---

## 35. Observation vs Fact

A sensor observation should not automatically become an absolute fact.

Example:

```text
camera detected person
```

is different from:

```text
person is definitely John
```

The second requires identity evidence and authorization appropriate to the operation.

---

## 36. Current State Authority

For physical-state questions, recent trusted sensor measurements generally take precedence over stale historical memory.

```text
old memory: hallway clear
current LiDAR: obstacle present
        ↓
CURRENT STATE WINS
```

The exact authority policy belongs to the safety/perception architecture.

---

## 37. Safety-Critical Fusion

Safety-critical decisions should use validated, health-monitored sensing paths and dedicated safety logic where required.

The general-purpose memory/knowledge system must not be the sole safety authority.

---

## 38. Sensor Failure and Safety

If a safety-relevant sensor fails:

```text
failure
 ↓
uncertainty increases
 ↓
capability restricted
 ↓
conservative behavior / safe state
```

A missing sensor must never be interpreted as absence of danger.

---

## 39. Sensor Data Privacy

Cameras, microphones, GPS, thermal sensing and other sensors can collect personal or sensitive information.

Sensor retention must follow documents 61–64.

Transient processing should be preferred where persistent storage is unnecessary.

---

## 40. Raw Sensor Retention

Raw streams should not be retained indefinitely by default.

Retention depends on:

- purpose;
- debugging requirements;
- safety requirements;
- user policy;
- privacy classification;
- storage capacity;
- deletion policy.

---

## 41. Sensor Data Security

Sensor data must be protected against:

- unauthorized access;
- spoofing;
- replay;
- tampering;
- injection;
- stale-data reuse.

Where authenticity mechanisms exist, they should be used.

---

## 42. Replay Detection

A captured old sensor message must not be mistaken for a current measurement.

Use appropriate:

- timestamps;
- sequence numbers;
- monotonic counters;
- freshness windows;
- source identity.

---

## 43. Sensor Spoofing

Novi should consider spoofing risks such as:

- visual deception;
- LiDAR interference;
- GNSS spoofing/jamming;
- audio injection;
- magnetic interference;
- malicious wireless sensor data.

Critical decisions should use cross-checks and health/confidence mechanisms where appropriate.

---

## 44. Sensor Occlusion

The system should detect likely occlusion or obstruction:

```text
camera blocked
LiDAR obscured
microphone obstructed
thermal sensor covered
```

Occluded data should be marked degraded rather than treated as normal absence.

---

## 45. Environmental Conditions

Sensor quality can change with:

- darkness;
- bright light;
- rain;
- fog;
- dust;
- reflective surfaces;
- heat;
- cold;
- acoustic reverberation;
- electromagnetic interference.

The fusion layer should expose relevant quality changes to downstream reasoning.

---

## 46. Sensor Rate Management

Not all sensors require the same update rate.

```text
IMU → high frequency
camera → medium/high
LiDAR → medium
GPS → lower
thermal/environment → application dependent
```

Actual rates must be determined from hardware and control requirements.

---

## 47. Backpressure

If downstream processing cannot keep up:

```text
producer > consumer
       ↓
backpressure / controlled dropping
```

Critical data must receive priority according to system policy.

Dropped data should be observable.

---

## 48. Compute and Thermal Awareness

Sensor fusion can be computationally expensive.

Under thermal or power pressure:

```text
reduce background perception
 ↓
reduce noncritical fusion
 ↓
reduce logging
 ↓
preserve safety and core localization
```

The system must never sacrifice thermal protection to maintain a high-rate perception pipeline.

---

## 49. Offline-First Operation

Core sensor ingestion and fusion must operate without Wi-Fi, Bluetooth or cloud services.

```text
NETWORK OFF
     ↓
LOCAL SENSORS
     ↓
LOCAL FUSION
     ↓
LOCAL WORLD STATE
     ↓
LOCAL MEMORY
```

Network connectivity can add external localization or knowledge but is not required for fundamental physical awareness.

---

## 50. Network Reconnection

When connectivity returns, remote information remains external evidence and cannot silently override local sensor truth.

Historical synchronization must preserve timestamps, provenance and uncertainty.

---

## 51. Fusion Algorithm Versioning

Every persisted fused observation should retain, where practical:

- fusion algorithm/version;
- calibration version;
- model version;
- sensor set used;
- time window;
- confidence/uncertainty.

This permits later reprocessing.

---

## 52. Reprocessing

If calibration or fusion algorithms improve:

```text
raw/source evidence
      ↓
new processing
      ↓
new derived state
```

Historical derived states should not be silently rewritten without preserving lineage.

---

## 53. Sensor Substitution

If a sensor is replaced:

```text
sensor A
 ↓
removed
 ↓
sensor B
```

The system must distinguish the two identities and their calibration histories.

---

## 54. Sensor Health as Memory

Persistent sensor faults may become operational knowledge:

```text
camera 2
 → intermittent failure
 → diagnosed on date/time
```

Such knowledge belongs to system health memory, not environmental world memory.

---

## 55. Sensor Event Memory

Meaningful events may be retained as compact observations:

```text
2026-08-17 14:22
obstacle detected
location: hallway
source: LiDAR + camera
confidence: high
```

Raw frames do not need to be retained to remember the event unless policy requires them.

---

## 56. Evaluation

Sensor fusion should be evaluated for:

- localization accuracy;
- orientation accuracy;
- detection accuracy;
- temporal alignment;
- spatial alignment;
- false positives;
- false negatives;
- uncertainty calibration;
- sensor failure response;
- degraded-mode behavior;
- map consistency;
- replay resistance;
- spoofing resilience;
- resource consumption.

---

## 57. Simulation and Replay

Sensor pipelines should support recorded/replayed datasets where practical.

This enables deterministic regression testing of:

- perception;
- localization;
- fusion;
- failure handling;
- memory formation.

Simulation/replay data must remain clearly marked as non-live evidence.

---

## 58. Simulation Does Not Equal Reality

A simulated sensor measurement must never be treated as a real-world observation.

```text
SIMULATION
   ≠
REAL-WORLD SENSOR DATA
```

This distinction must propagate through memory and knowledge.

---

## 59. World-State Confidence

The world model should expose confidence/uncertainty for relevant entities and states.

Example:

```text
hallway obstacle
estimated position: 1.8 m
confidence: 0.93
sources: LiDAR + camera
age: 120 ms
```

The exact representation is implementation-specific.

---

## 60. Sensor Fusion and Knowledge Promotion

A fused observation can become memory, but durable knowledge requires the normal admission and promotion rules.

```text
fused observation
      ↓
context
      ↓
uncertainty
      ↓
provenance
      ↓
memory
      ↓
knowledge if justified
```

---

## 61. Architectural Invariants

1. Sensor measurements are evidence, not automatic truth.
2. Raw, calibrated, aligned, observed, fused and interpreted data are distinct layers.
3. Every sensor has a stable identity and health state.
4. Coordinate frames are explicit.
5. Calibration is versioned.
6. Timestamps distinguish acquisition from ingestion and processing.
7. Time synchronization is an explicit engineering parameter.
8. Clock failure degrades affected fusion.
9. Sensor quality is distinct from truth.
10. Failed sensors cannot continue contributing as healthy sources.
11. Sensor disagreement is preserved and evaluated.
12. Correlated sensors do not count as independent evidence merely because they are separate devices.
13. Uncertainty must propagate through fusion.
14. Current trusted sensing generally outranks stale historical physical-state memory.
15. Safety-critical sensing is not delegated solely to general memory/knowledge.
16. Sensor absence is not evidence of absence of danger.
17. Raw sensor data is retained only according to explicit policy.
18. Sensor-derived data inherits privacy controls.
19. Replay and spoofing defenses are required for critical data paths.
20. Simulation data is never represented as real-world observation.
21. Fused outputs retain provenance and algorithm/calibration versions.
22. Sensor replacement creates a new sensor identity/history.
23. Core sensing and fusion work offline.
24. Network data cannot silently override trusted local physical sensing.
25. Sensor failures must degrade capabilities safely rather than produce fabricated certainty.

## 62. Final Principle

> **Novi should never ask one imperfect sensor to tell it what reality is. It should build the best defensible estimate from synchronized, calibrated, health-aware, provenance-preserving evidence—and remain honest about what it does not know.**
