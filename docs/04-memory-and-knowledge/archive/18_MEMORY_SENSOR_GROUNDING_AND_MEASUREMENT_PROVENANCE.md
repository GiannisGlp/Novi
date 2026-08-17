# 18 — Memory Sensor Grounding and Measurement Provenance

## Status

**DESIGN — V1 HIGH-LEVEL / DETAILED ARCHITECTURE**

## Purpose

Define how Novi converts physical sensor measurements into grounded observations without losing the information required to determine **what was measured, where, when, by which sensor, under which calibration and health conditions, with what uncertainty, and how the measurement was interpreted**.

This document bridges the physical hardware architecture and Novi's memory/knowledge architecture.

The central rule is:

> **A physical-world claim must retain enough provenance to reconstruct the measurement and understand its reliability.**

---

## 1. Why Grounding Is Necessary

Novi is a physical autonomous system. Its memories cannot treat a sensor measurement as equivalent to a model-generated statement.

For example:

```text
RAW MEASUREMENT
71.4 °C
      ↓
SENSOR
thermal_camera_01
      ↓
CALIBRATION
calibration_v12
      ↓
LOCATION
kitchen counter / frame coordinates
      ↓
TIME
acquisition timestamp
      ↓
HEALTH
sensor healthy
      ↓
UNCERTAINTY
measurement uncertainty
      ↓
INTERPRETATION
surface is unusually hot
      ↓
MEMORY / KNOWLEDGE
```

The interpretation must not replace the underlying evidence.

---

## 2. Grounding Layers

Novi distinguishes at least six layers:

```text
1. Raw signal / sensor output
2. Measurement
3. Perceptual observation
4. World-model state
5. Memory / claim
6. Knowledge / belief
```

Each layer must identify its parent evidence where technically possible.

Example:

```text
thermal frame
    ↓
temperature measurement
    ↓
hot-surface observation
    ↓
object X has thermal anomaly
    ↓
memory: object X was hot at T
    ↓
knowledge: object X frequently becomes hot during operation
```

The later statement must not erase the earlier evidence chain.

---

## 3. Sensor Identity

Every physical measurement source requires a stable logical sensor identity.

The identity should distinguish:

- robot ID;
- sensor ID;
- sensor instance;
- sensor type;
- manufacturer/model where known;
- hardware revision;
- firmware version;
- driver version;
- physical mounting position;
- logical coordinate frame;
- calibration version;
- health state.

A replacement sensor should normally receive a new physical instance identity even if it is the same model.

This prevents old measurements from being incorrectly attributed to a newly installed component.

---

## 4. Measurement Envelope

A normalized measurement should carry an envelope similar to:

```json
{
  "measurement_id": "meas_...",
  "sensor_id": "thermal_camera_01",
  "sensor_instance_id": "...",
  "measurement_type": "temperature",
  "value": 71.4,
  "unit": "degC",
  "acquired_at": "...",
  "received_at": "...",
  "frame_id": "thermal_camera_frame",
  "calibration_id": "cal_v12",
  "health_state": "healthy",
  "uncertainty": {
    "type": "estimated",
    "value": 1.2,
    "unit": "degC"
  },
  "quality": "good",
  "source_event_id": "evt_..."
}
```

Exact schema belongs to the event/ingestion implementation.

---

## 5. Acquisition Time vs Receive Time

Novi must distinguish:

**Acquisition time** — when the sensor says the measurement was captured.

**Receive time** — when Novi's compute system received the measurement.

They can differ significantly because of:

- USB buffering;
- network transport;
- driver queues;
- CPU scheduling;
- GPU processing;
- sensor internal buffering.

Physical-world reasoning should prefer acquisition time when it is trustworthy.

Receive time remains important for diagnosing transport latency and system behavior.

---

## 6. Clock Quality

Every timestamp should have an associated time-quality interpretation where practical.

Potential states include:

```text
synchronized
estimated
monotonic-only
unsynchronized
unknown
```

Novi must not manufacture precision that the hardware cannot support.

If two sensors have uncertain clock relationships, the system should preserve uncertainty rather than pretending that their measurements are perfectly simultaneous.

---

## 7. Coordinate Frames

Physical measurements require coordinate-frame information whenever spatial interpretation is involved.

Examples:

- robot base frame;
- camera frame;
- LiDAR frame;
- IMU frame;
- thermal-camera frame;
- world/map frame;
- object-local frame.

Transforms must have versioned provenance.

Example:

```text
camera frame
    ↓
extrinsic transform v8
    ↓
robot base frame
    ↓
map frame v14
```

A spatial memory must be able to identify which transform chain produced its coordinates.

---

## 8. Calibration Provenance

Calibration is part of measurement provenance, not optional metadata.

Where applicable, Novi should track:

- calibration identifier;
- calibration version;
- calibration date/time;
- calibration method;
- calibration environment;
- calibration validity period;
- calibration quality;
- operator/process responsible for calibration;
- whether calibration is known to be stale.

If calibration becomes invalid, affected measurements should be marked accordingly.

---

## 9. Sensor Health

Measurements should carry the sensor health state at or near acquisition time where possible.

Example states:

```text
healthy
warning
degraded
uncalibrated
faulted
offline
unknown
```

A measurement captured immediately before a sensor fault may remain valid, while later measurements may not.

Health is therefore temporal, not simply a current sensor property.

---

## 10. Measurement Uncertainty

Novi must distinguish:

- exact digital value;
- estimated physical value;
- measurement uncertainty;
- confidence in interpretation.

These are different concepts.

For example:

```text
temperature = 71.4 °C
measurement uncertainty = ±1.2 °C
interpretation confidence = 0.94
```

The model must not turn uncertainty into false precision.

---

## 11. Sensor-Specific Quality

Different sensors require different quality metrics.

### Camera

Potential quality indicators:

- exposure;
- focus;
- blur;
- frame drops;
- image saturation;
- illumination;
- lens obstruction.

### LiDAR

Potential indicators:

- scan completeness;
- return density;
- range validity;
- timestamp quality;
- contamination/obstruction.

### IMU

Potential indicators:

- saturation;
- bias estimate;
- drift;
- calibration state;
- sample timing.

### Microphone

Potential indicators:

- signal-to-noise ratio;
- clipping;
- channel health;
- synchronization;
- acoustic interference.

### Thermal camera

Potential indicators:

- calibration state;
- temperature range;
- saturation;
- emissivity assumptions;
- environmental conditions;
- frame quality.

### Battery/power sensors

Potential indicators:

- BMS health;
- current-sensor status;
- voltage validity;
- cell consistency;
- temperature validity.

Exact quality metrics will be defined in hardware-specific documents.

---

## 12. Physical Location

Measurements should retain the relevant spatial context when available.

This can include:

- robot pose;
- sensor pose;
- world/map coordinate;
- detected object position;
- room/area identity;
- relative distance;
- direction;
- coordinate uncertainty.

Spatial identity must not be confused with semantic identity.

For example:

```text
position = 2.1m in front of robot
```

does not automatically mean:

```text
object = coffee table
```

The latter requires perception/identity evidence.

---

## 13. Object Grounding

When a perception system identifies an object, Novi should preserve the relationship between:

```text
sensor evidence
      ↓
detection
      ↓
object hypothesis
      ↓
object identity
```

Object identity should include confidence and provenance.

If Novi later discovers that two object identities were incorrectly merged, historical evidence must remain recoverable.

---

## 14. Person Grounding

Person-related observations require additional care.

Novi should distinguish:

- detected human;
- person hypothesis;
- recognized person identity;
- verified identity;
- speaker identity;
- face recognition result;
- user-provided identity.

A face embedding or voice match should not automatically become a permanent identity claim without the relevant confidence, provenance and policy checks.

Sensitive biometric data requires stricter privacy handling as defined by the privacy architecture.

---

## 15. Audio Grounding

Audio events should preserve:

- microphone/source identity;
- channel;
- acquisition time;
- direction of arrival;
- estimated source position;
- speaker hypothesis;
- diarization segment;
- ASR result;
- ASR model/version;
- acoustic quality;
- confidence;
- relevant audio provenance.

Novi should distinguish:

```text
heard sound
vs
heard speech
vs
recognized words
vs
identified speaker
vs
interpreted meaning
```

Each is a different inference layer.

---

## 16. Thermal Grounding

Thermal sensing requires special handling because measured temperature can depend on physical and environmental assumptions.

Where available, Novi should retain:

- sensor temperature;
- measured temperature;
- apparent/radiometric temperature semantics;
- emissivity assumptions;
- distance;
- calibration state;
- environmental temperature;
- measurement uncertainty.

Novi must avoid treating every thermal-camera pixel as a universally exact physical temperature.

---

## 17. Motion Grounding

Motion observations should preserve the relevant combination of:

- IMU data;
- wheel/actuator encoders;
- visual odometry;
- LiDAR odometry;
- SLAM state;
- robot pose;
- velocity estimate;
- covariance/uncertainty where available.

A statement such as:

> "Novi moved 2 metres."

should be traceable to the motion-estimation evidence that produced it.

---

## 18. Sensor Fusion Provenance

When multiple sensors contribute to one conclusion, Novi should preserve all important parent evidence.

Example:

```text
camera frame ───────┐
LiDAR scan ─────────┤
IMU pose ───────────┤
                     ▼
              fused object state
                     │
                     ▼
                  memory
```

The fused state should identify:

- contributing measurements;
- fusion algorithm/version;
- transform versions;
- timestamp window;
- confidence/uncertainty;
- processing model/version.

---

## 19. Model-Generated Perception

When a neural model interprets sensor data, Novi must preserve the model identity.

Record where appropriate:

- model ID;
- model version/hash;
- runtime version;
- inference configuration;
- preprocessing version;
- postprocessing version;
- confidence;
- source measurement IDs.

This allows Novi to determine later that:

> "This memory was created using perception model X version Y."

If the model is replaced, historical inference should not be silently represented as if the new model produced it.

---

## 20. Measurement → Memory Promotion

Not every measurement becomes memory.

```text
measurement
    ↓
quality validation
    ↓
perception / interpretation
    ↓
admission policy
    ↓
memory candidate
    ↓
memory
```

High-frequency sensor streams should normally remain event/telemetry data unless they provide meaningful evidence for a memory or knowledge claim.

---

## 21. Measurement → Knowledge Promotion

Knowledge requires a higher threshold than raw observation.

Example:

```text
Observation:
object temperature = 71°C

Candidate interpretation:
object is hot

Repeated evidence:
object repeatedly becomes hot

Potential knowledge:
object becomes hot during operation
```

The final knowledge claim must preserve the evidence chain.

---

## 22. Contradictory Measurements

If sensors disagree:

```text
thermal camera: 71°C
contact sensor: 65°C
```

Novi must not silently choose one solely because it arrived later.

It should consider:

- calibration;
- sensor health;
- uncertainty;
- measurement geometry;
- sensor modality;
- temporal alignment;
- environmental conditions;
- known sensor biases.

The disagreement itself may be diagnostically valuable.

---

## 23. Sensor Failure as Knowledge

Repeated sensor failures should be represented as hardware-health knowledge rather than hidden inside raw logs.

Example:

```text
camera 2
→ repeated frame drops
→ degraded state
→ diagnostic event
→ hardware health memory
```

This allows autonomy to change behavior based on actual sensor reliability.

---

## 24. Replacement and Maintenance

Replacing a sensor should create a new hardware-instance lineage.

```text
sensor instance A
     ↓
removed
     ↓
sensor instance B
```

Historical measurements from A must remain associated with A.

Novi must never reinterpret historical measurements as though B produced them.

---

## 25. Calibration Changes

Calibration updates must be versioned.

```text
measurement 1 → calibration v1
measurement 2 → calibration v2
```

Reprocessing old measurements with a new calibration must produce a new derived result rather than silently rewriting the original measurement.

---

## 26. Data Retention

Raw sensor data and derived observations have different retention requirements.

For example:

```text
raw video/audio
→ short retention unless explicitly retained

measurement metadata
→ longer retention

memory/knowledge
→ policy-driven retention

calibration history
→ long-lived engineering provenance
```

The privacy and retention policies remain authoritative.

---

## 27. Privacy

Sensor grounding must not become a mechanism for bypassing privacy controls.

For sensitive sources, provenance may itself contain sensitive information.

Access policies therefore apply to:

- raw measurements;
- media;
- derived observations;
- identities;
- location information;
- biometric representations;
- provenance records.

A user deletion request must propagate through derived representations according to the deletion architecture.

---

## 28. Offline Operation

Grounding must work without network access.

Required local capabilities include:

- timestamping;
- sensor identity;
- calibration lookup;
- coordinate transforms;
- health assessment;
- local event storage;
- local measurement validation.

Network time synchronization or remote calibration services may improve accuracy when available, but must not be mandatory for core operation.

---

## 29. Confidence vs Measurement Quality

Novi must never collapse all uncertainty into one number.

At minimum distinguish:

```text
measurement quality
sensor health
measurement uncertainty
perception confidence
identity confidence
knowledge confidence
verification state
```

A high-confidence neural prediction from a degraded sensor is not equivalent to a high-quality physical measurement.

---

## 30. Auditability

For an important physical-world claim, Novi should be able to answer:

> What caused you to believe this?

The answer should be reconstructable through:

```text
knowledge claim
 ↓
claim version
 ↓
memory
 ↓
observation
 ↓
measurement
 ↓
sensor
 ↓
calibration
 ↓
health state
 ↓
source event
```

Not every raw byte must be retained forever, but the surviving provenance must be sufficient for the retention policy and required audit level.

---

## 31. Example — Hot Object

```text
ThermalCamera01
  frame 183920
  acquisition T1
  calibration v12
  health=healthy
       ↓
measurement
  apparent_temperature=71.4°C
  uncertainty=±1.2°C
       ↓
object detection
  object_hypothesis=pan
  confidence=0.91
       ↓
world model
  pan.position=(x,y,z)
       ↓
memory candidate
  pan was very hot at T1
       ↓
admission
       ↓
memory
       ↓
knowledge candidate after repetition
  pan frequently becomes hot during cooking
```

Every layer remains traceable to the physical evidence.

---

## 32. Example — Voice

```text
Microphone array
       ↓
raw acoustic event
       ↓
DoA estimate
       ↓
voice activity
       ↓
speaker hypothesis
       ↓
ASR
       ↓
transcript
       ↓
semantic interpretation
       ↓
possible memory
```

Novi must distinguish what it physically captured from what its models inferred.

---

## 33. Example — Navigation

```text
camera
LiDAR
IMU
encoders
   ↓
state estimation
   ↓
pose + uncertainty
   ↓
world model
   ↓
autonomy
```

A navigation decision should be able to identify the relevant state-estimation evidence and sensor-health conditions.

---

## 34. Failure and Degradation Rules

If grounding metadata is missing or invalid, Novi should downgrade confidence rather than inventing values.

Examples:

```text
missing calibration
→ measurement quality degraded

unknown timestamp alignment
→ temporal confidence degraded

sensor faulted
→ reject or heavily restrict measurement

unknown coordinate transform
→ no precise spatial claim
```

The system should prefer:

> "I cannot reliably determine the exact temperature."

over fabricated precision.

---

## 35. Testing Requirements

The implementation must test:

- timestamp mismatch;
- clock drift;
- stale calibration;
- sensor replacement;
- sensor failure;
- missing metadata;
- incorrect frame transforms;
- uncertainty propagation;
- conflicting sensors;
- duplicate measurements;
- delayed measurements;
- out-of-order events;
- corrupted measurements;
- model-version changes;
- deletion propagation;
- offline operation;
- replay of historical measurements.

Tests must verify that invalid provenance cannot silently become trusted knowledge.

---

## 36. Architectural Invariants

1. A measurement must never lose its source identity before becoming persistent evidence.
2. Acquisition time and receive time must remain distinguishable.
3. Calibration state must be versioned.
4. Sensor health must be considered when interpreting measurements.
5. Coordinate transforms must be versioned where spatial claims depend on them.
6. Model inference must remain distinguishable from physical measurement.
7. Confidence must not be treated as physical measurement accuracy.
8. Sensor disagreement must remain representable.
9. Historical measurements must remain attached to the hardware instance that produced them.
10. Deletion and privacy policy apply to grounded evidence and derived claims.
11. Offline operation must preserve grounding functionality.
12. Important knowledge must be traceable to evidence.
13. Novi must never invent missing calibration, timing, identity or spatial precision.

---

## 37. Relationship to Other Documents

This document depends on and connects:

```text
Hardware
   ↓
17 Event Log / Sensor Ingestion
   ↓
18 Sensor Grounding / Measurement Provenance
   ↓
Memory Admission
   ↓
Consolidation
   ↓
Knowledge Promotion
   ↓
Retrieval / Cognition / Autonomy
```

Hardware-specific details belong in `docs/05-hardware/`.

Memory policy remains authoritative for what is admitted, retained and deleted.

---

## 38. Final Principle

> **Novi should remember not only what it concluded, but why the physical world gave it reason to conclude it.**

For a physical autonomous system, provenance is part of intelligence. A robot that knows a fact without knowing whether it came from a healthy calibrated sensor, an uncertain model prediction, a user statement, or an old inference cannot reliably reason about that fact.

Grounding therefore forms the bridge between Novi's physical body and its long-term mind.
