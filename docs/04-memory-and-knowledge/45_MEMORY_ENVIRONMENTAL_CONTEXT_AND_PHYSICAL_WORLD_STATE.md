# 45 — Memory Environmental Context and Physical World State

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi observes, represents, validates, remembers and reasons about environmental and physical-world conditions that surround the robot and affect perception, navigation, interaction, safety and learning.

Environmental context includes measurable physical conditions such as temperature, illumination, sound levels, humidity and air-quality measurements where appropriate, as well as derived conditions such as visibility, surface state, obstacles, occupancy and environmental change.

This document deliberately separates **what a sensor measured**, **what Novi inferred**, and **what Novi believes about the environment**.

## Research and Technology Basis

The architecture is designed around standard robotics sensor-fusion principles and ROS 2-compatible interfaces, while allowing implementation by NVIDIA Isaac ROS, OpenCV, PyTorch, TensorFlow, ONNX Runtime, Hugging Face, other open-source components, or custom software.

NVIDIA's robotics stack provides accelerated perception components for cameras, stereo, LiDAR, visual SLAM, 3D reconstruction and navigation, and Isaac Sim can simulate multiple sensor classes for software-in-the-loop testing. citeturn0search0turn0search2turn0search3 NVIDIA's documented perception/navigation examples also demonstrate combining camera-derived depth with LiDAR and local navigation costmaps. citeturn0search9

NVIDIA is therefore a strong candidate for accelerated implementation on Novi's Jetson target, but this document does **not** make NVIDIA a mandatory dependency.

---

## 1. Core Principle

> **Environmental memory must represent measured reality with provenance and uncertainty, not an unrestricted narrative description of the world.**

The canonical progression is:

```text
SENSOR
  ↓
MEASUREMENT
  ↓
CALIBRATION / QUALITY CHECK
  ↓
OBSERVATION
  ↓
FUSION / ESTIMATION
  ↓
ENVIRONMENTAL STATE
  ↓
MEMORY / KNOWLEDGE
  ↓
PREDICTION
```

Each transition must remain distinguishable.

---

## 2. Environmental Context Layers

Novi should separate:

```text
RAW MEASUREMENT
What did the sensor report?

OBSERVATION
What detectable phenomenon was derived?

ESTIMATE
What is the best current estimate?

ENVIRONMENTAL STATE
What condition is the system currently representing?

MEMORY
What historical environmental information was retained?

KNOWLEDGE
What generalized environmental relationship has sufficient evidence?

PREDICTION
What condition is expected next?
```

---

## 3. Environment Categories

The architecture should support, where hardware permits:

- temperature;
- thermal radiation / apparent temperature;
- humidity;
- pressure;
- illumination;
- visible-light conditions;
- infrared conditions;
- sound level;
- acoustic events;
- air quality;
- particulate concentration;
- gases where appropriate sensors are installed;
- atmospheric conditions;
- wind where measurable;
- precipitation where measurable or externally supplied;
- visibility;
- surface condition;
- obstacles;
- free space;
- occupancy;
- environmental change;
- structural/physical anomalies.

Not every Novi build must contain every sensor.

---

## 4. Required vs Optional Sensors

Environmental sensing should be classified:

```text
CORE
required for safety or core operation

RECOMMENDED
strongly useful for intended operation

OPTIONAL
useful but not required

FUTURE
reserved interface for later hardware
```

This prevents the software architecture from assuming hardware that may not exist.

---

## 5. External vs Internal Environment

Novi must distinguish environmental state from its own internal physical state.

```text
EXTERNAL
room temperature
hot/cold objects
lighting
noise
air quality
obstacles
surface conditions

INTERNAL
CPU/GPU temperature
battery temperature
motor temperature
power electronics
storage
enclosure temperature
```

Both can influence cognition, but they have different authorities and safety policies.

---

## 6. Temperature Model

Temperature should be represented with:

- sensor ID;
- location;
- measured value;
- unit;
- calibration status;
- timestamp;
- measurement uncertainty;
- sensor health;
- spatial reference.

Novi should not assume that one temperature sensor represents an entire room or object.

---

## 7. Thermal Perception

A thermal camera or infrared sensor can provide spatial information about apparent thermal patterns.

The architecture must distinguish:

```text
thermal measurement
      ≠
true material temperature
```

Apparent temperature can be affected by emissivity, distance, reflections, environmental conditions and sensor characteristics.

Therefore thermal perception should preserve the sensor model and uncertainty.

---

## 8. Hot and Cold Detection

Novi should support semantic categories such as:

```text
warmer_than_background
cooler_than_background
potentially_hot
potentially_cold
thermal_anomaly
unknown
```

These are perception classifications, not universal safety guarantees.

For physical-contact safety, dedicated safety thresholds and hardware policies take precedence.

---

## 9. Thermal Spatial Mapping

Thermal observations can be associated with spatial regions:

```text
room
  ↓
thermal field
  ↓
hot region
  ↓
object candidate
```

Repeated observations may establish a persistent thermal characteristic.

Example:

```text
radiator area
  ↓
repeatedly warmer
  ↓
known thermal landmark
```

---

## 10. Illumination

Novi should represent lighting conditions using available sensors/cameras.

Possible states:

```text
bright
dim
dark
rapidly changing
backlit
high contrast
low contrast
unknown
```

These are contextual estimates and should not replace quantitative sensor measurements where those are required.

---

## 11. Lighting and Perception

Lighting conditions should influence perception confidence.

Example:

```text
low illumination
   ↓
visual confidence reduced
   ↓
use additional sensors
```

Potential responses include:

- camera exposure adjustment;
- IR illumination where appropriate;
- LiDAR reliance;
- thermal sensing;
- additional viewpoint;
- active lighting.

---

## 12. Sound Environment

Novi's microphone array can provide environmental acoustic context.

Possible measurements/observations:

- sound pressure level where calibrated;
- spectral characteristics;
- direction of arrival;
- speech likelihood;
- acoustic event class;
- persistent noise sources;
- transient sounds.

Sound level should not be confused with semantic meaning.

---

## 13. Acoustic Spatial Context

Novi can associate sound with direction and location estimates.

```text
microphone array
      ↓
direction of arrival
      ↓
source hypothesis
      ↓
spatial association
```

Multiple simultaneous sources require uncertainty-aware association.

---

## 14. Environmental Noise Memory

Novi may learn environmental acoustic patterns such as:

```text
normal household noise
recurring appliance noise
traffic noise
construction noise
unusual transient event
```

Retention should be minimized because audio can contain sensitive personal information.

---

## 15. Humidity and Pressure

If equipped, humidity and pressure sensors can provide local environmental context.

These can support:

- environmental state;
- sensor compensation;
- comfort-related context where explicitly designed;
- anomaly detection;
- scientific/environmental logging.

They should not be inferred as precise values without appropriate sensors.

---

## 16. Air Quality

Air-quality sensing is optional but potentially valuable for a home robot.

Possible measurements include, depending on sensor hardware:

- particulate matter;
- volatile organic compound indicators;
- CO₂;
- specific gases.

Each measurement must retain the exact sensor capability and limitations.

Novi must not infer a medically meaningful air-quality conclusion from an unrelated sensor.

---

## 17. Environmental Health Boundary

Environmental measurements are not automatically medical advice.

For example:

```text
CO₂ sensor reports elevated concentration
        ↓
environmental observation
```

It should not automatically become:

```text
"This person is medically unsafe."
```

Any health-related interpretation requires a separate validated policy and appropriate evidence.

---

## 18. Obstacles

Obstacles should be represented separately from semantic object identity.

```text
geometry
  ↓
obstacle
  ↓
possible object classification
```

Navigation safety can act on geometry even when the object identity is unknown.

---

## 19. Free Space

Novi should maintain an estimate of traversable/free space where required for navigation.

Free-space estimates should include:

- source sensors;
- timestamp;
- coordinate frame;
- confidence;
- dynamic/static classification where available.

---

## 20. Surface Conditions

Where sensors permit, Novi may detect or estimate surface conditions such as:

- dry;
- wet;
- reflective;
- uneven;
- obstructed;
- uncertain.

These classifications must not be treated as guaranteed physical properties without appropriate validation.

---

## 21. Dynamic Environment

The world is continuously changing.

Novi should distinguish:

```text
STATIC
slow-changing
DYNAMIC
TRANSIENT
UNKNOWN
```

Examples:

```text
wall → static
furniture → semi-static
person → dynamic
fallen object → transient/unknown
```

Classification remains revisable.

---

## 22. Environmental State as a Time Series

Environmental state should be represented over time.

```text
t0 → 20°C
t1 → 21°C
t2 → 23°C
```

A semantic memory can summarize this as:

```text
room warmed over the interval
```

but the underlying measurements remain available according to retention policy.

---

## 23. Spatial Environmental Fields

Where useful, Novi can represent environmental variables spatially:

```text
room
 ├── temperature field
 ├── illumination field
 ├── acoustic field
 └── occupancy field
```

The resolution must be proportional to sensor capability and application need.

---

## 24. Environmental Change Detection

A change candidate can be generated by comparing current observations with historical state:

```text
historical state
      +
current observation
      ↓
change candidate
      ↓
validation
      ↓
world-model update
```

One noisy measurement should not automatically create permanent knowledge.

---

## 25. Persistent Environmental Knowledge

Knowledge can be promoted when evidence is sufficient.

Example:

```text
repeated observations
      ↓
"this room is normally warmer near the radiator"
```

The claim must retain:

- evidence;
- time range;
- location;
- sensor provenance;
- confidence;
- environmental conditions.

---

## 26. Temporary Environmental Memory

Short-lived conditions may be retained only temporarily.

Examples:

```text
temporary loud noise
passing person
temporary hot object
temporary obstacle
brief lighting change
```

The memory system should avoid turning every transient event into permanent autobiographical knowledge.

---

## 27. Environmental Expectations

Environmental history can generate predictions:

```text
place + time + historical evidence
        ↓
expected environment
```

Example:

```text
kitchen
08:00
historically bright
        ↓
expect high illumination
```

Current observation always has authority to invalidate the expectation.

---

## 28. Prediction Error

Environmental prediction error should be explicit.

```text
expected: room quiet
actual: loud construction noise
        ↓
prediction error
        ↓
attention increase
        ↓
investigation
```

This connects environmental context to the attention and learning systems already defined.

---

## 29. Sensor Fusion

Environmental state may combine heterogeneous sensors.

Example:

```text
camera
LiDAR
thermal
microphones
IMU
environmental sensors
        ↓
quality-aware fusion
        ↓
environmental state
```

Fusion must account for:

- timestamp alignment;
- coordinate transforms;
- calibration;
- sensor quality;
- occlusion;
- field of view;
- sensor-specific failure modes.

---

## 30. Sensor Disagreement

Disagreement should remain visible.

Example:

```text
thermal sensor → hot region
camera → no obvious object
        ↓
uncertain thermal anomaly
```

Possible causes should be investigated rather than averaging incompatible semantics.

---

## 31. Sensor Failure

Environmental state must degrade gracefully when a sensor fails.

```text
thermal unavailable
      ↓
thermal state = UNKNOWN
      ↓
use other evidence where possible
```

Unknown is preferable to fabricated certainty.

---

## 32. Confidence and Uncertainty

Environmental observations should support confidence/uncertainty where meaningful.

For numerical sensors, preserve measurement uncertainty or accuracy metadata when available.

For semantic perception, preserve model confidence and validation state.

Confidence must not be treated as universal probability unless the model is actually calibrated that way.

---

## 33. Calibration

Environmental sensor calibration must be tracked.

Calibration records should include:

- sensor ID;
- calibration version;
- calibration date/time;
- method;
- validity criteria;
- result;
- reference standard where applicable.

Invalid calibration should affect downstream trust in measurements.

---

## 34. Environmental Context and Navigation

Environmental state can influence navigation.

Examples:

```text
low light
 ↓
visual confidence reduced

wet/uncertain surface
 ↓
route risk increased

obstacle detected
 ↓
route replanning

thermal hazard
 ↓
avoid region
```

Safety-critical decisions should rely on dedicated validated policies.

---

## 35. Environmental Context and Interaction

Environmental context can improve interaction.

Example:

```text
high household noise
 ↓
speech recognition confidence reduced
 ↓
Novi may move closer / change output / ask for repetition
```

The response should be considerate without assuming the cause of the environment incorrectly.

---

## 36. Environmental Context and Displays

Novi's planned displays can communicate environmental state when useful.

Examples:

- navigation state;
- thermal warning;
- sensor degradation;
- mapping state;
- charging state;
- environmental anomaly.

Display semantics should be defined by the interaction architecture rather than inferred ad hoc by the LLM.

---

## 37. Environmental Context and Lighting

RGB body lighting may communicate Novi's own state but must not be confused with environmental measurement.

```text
RGB lighting
 = Novi output

ambient-light sensor/camera
 = environmental input
```

This distinction is important for diagnostics and learning.

---

## 38. Environmental Context and Thermal Safety

Internal thermal state must have a dedicated safety path.

```text
internal temperature
        ↓
hardware/system telemetry
        ↓
thermal policy
        ↓
compute throttling / shutdown / protection
```

The cognitive model may receive thermal state, but cannot override hardware thermal protection.

---

## 39. Environmental Context and Curiosity

Environmental anomalies can create information-seeking goals.

Example:

```text
unexpected sound
      ↓
source uncertain
      ↓
attention increase
      ↓
active perception
```

Curiosity remains subordinate to safety, privacy, energy and autonomy policies.

---

## 40. Environmental Context and Memory Admission

An environmental observation should be retained when it is sufficiently:

- salient;
- repeated;
- goal-relevant;
- surprising;
- safety-relevant;
- useful for prediction;
- explicitly requested.

Memory admission rules from the dedicated memory-write policy remain authoritative.

---

## 41. Environmental Context and Episodic Memory

Important environmental conditions can become part of episodes.

Example:

```text
walk to park
 +
heavy rain
 +
poor visibility
 +
route deviation
 +
successful return
        ↓
journey episode
```

This allows Novi to learn from environmental conditions without treating every sensor reading as an autobiographical memory.

---

## 42. Environmental Context and Social Memory

Where authorized, environmental context can explain interaction outcomes.

Example:

```text
conversation failed
 +
high background noise
        ↓
possible explanation
```

This should remain a hypothesis unless sufficiently supported.

---

## 43. Environmental Context and Human Privacy

Environmental sensing can indirectly reveal people and routines.

Examples:

- recurring occupancy;
- household routines;
- conversations inferred from acoustic context;
- room usage;
- location patterns.

Therefore environmental memory must follow privacy, retention and deletion policies.

---

## 44. Environmental Data Retention

Different environmental data should have different retention classes.

```text
high-rate raw sensor data
 → short retention unless justified

semantic environmental observations
 → medium retention

stable environmental knowledge
 → long retention if useful

safety/audit records
 → policy-defined retention
```

No universal infinite retention is allowed.

---

## 45. Raw Sensor Data

Raw environmental streams may be large.

Novi should prefer:

- local ring buffers;
- event-triggered capture;
- compressed summaries;
- keyframes;
- references to durable files;
- selective retention.

The event architecture must not become an unbounded raw sensor archive.

---

## 46. File and SQLite Storage

Environmental data may be stored locally using appropriate formats.

For example:

```text
SQLite
  metadata
  observations
  events
  indexes

files/object storage
  images
  thermal frames
  audio clips
  point clouds
  datasets
```

The brain may generate and update local environmental datasets, subject to admission and integrity policies.

---

## 47. Offline-First Requirement

Environmental perception and memory must remain operational without network connectivity.

```text
Wi-Fi OFF
Bluetooth OFF
Cloud OFF
      ↓
local sensors
local processing
local memory
local world model
local cognition
      ↓
continue operating
```

Network services may enhance or synchronize the system but are not foundational requirements.

---

## 48. Synchronization

If environmental memories are synchronized, preserve:

- source robot;
- sensor provenance;
- event IDs;
- timestamps;
- map version;
- confidence;
- synchronization time.

Conflicts must not be resolved by simply choosing the newest record.

---

## 49. Environmental Conflict Resolution

Example:

```text
Robot observation A:
room = 22°C

Robot observation B:
room = 28°C
```

Resolution should consider:

- sensor calibration;
- location;
- timestamp;
- sensor type;
- spatial distance;
- measurement uncertainty.

The system may conclude:

```text
conflict unresolved
```

rather than fabricating a single value.

---

## 50. Environmental World Model

The world model should maintain a current projection such as:

```text
location
lighting
thermal context
sound context
occupancy
obstacles
free space
air/environmental measurements
known anomalies
uncertainty
```

This is a current projection, not the permanent memory store.

---

## 51. World-Model Versioning

Important environmental-state projections should be versioned where required for reproducibility.

```text
world_state_v100
world_state_v101
world_state_v102
```

Historical decisions should reference the relevant state/provenance context.

---

## 52. Simulation and Testing

Environmental sensing should be testable in simulation and replay.

NVIDIA Isaac Sim supports simulated cameras, LiDAR, IMU and other sensor types and can connect simulated sensor data to ROS 2, making it a strong candidate for sensor-pipeline testing and synthetic-data generation. citeturn0search3turn0search4

However, simulation must not be treated as proof that real-world sensor behavior is correct.

---

## 53. Real-World Validation

Every environmental perception subsystem should eventually be validated using:

```text
simulation
      +
controlled laboratory tests
      +
real household environments
      +
outdoor environments where relevant
      +
long-duration operation
```

Environmental corner cases must be explicitly tested.

---

## 54. Important Environmental Test Cases

Test at minimum:

- bright sunlight;
- darkness;
- rapidly changing illumination;
- reflective surfaces;
- glass;
- shadows;
- occlusion;
- steam/fog where relevant;
- hot/cold objects;
- thermal reflections;
- high background noise;
- multiple simultaneous sound sources;
- sensor disagreement;
- sensor failure;
- calibration drift;
- changing furniture;
- moving people;
- temporary obstacles;
- indoor/outdoor transitions;
- GNSS loss;
- high/low temperatures;
- high resource pressure.

---

## 55. Environmental Anomaly Detection

An anomaly is a deviation from an established expectation, not automatically a dangerous condition.

```text
expected
   ↓
observed deviation
   ↓
anomaly candidate
   ↓
classification
   ↓
response according to risk
```

Risk classification belongs to the safety/autonomy architecture.

---

## 56. Environmental Memory Promotion

A temporary observation may be promoted when evidence accumulates.

```text
single observation
       ↓
observation

repeated observation
       ↓
pattern candidate

validated pattern
       ↓
knowledge
```

This protects the knowledge base from noisy one-off events.

---

## 57. Environmental Forgetting

When environmental information becomes obsolete, Novi should be able to:

- expire it;
- downgrade confidence;
- archive it;
- summarize it;
- replace it with newer validated state.

Historical truth must remain distinguishable from current truth.

---

## 58. Architectural Invariants

1. Environmental measurements retain sensor and temporal provenance.
2. Sensor measurements are not automatically semantic truth.
3. External and internal thermal state are separate domains.
4. Thermal perception is not automatically equivalent to true material temperature.
5. Unknown is preferred to fabricated certainty.
6. Current environmental state outranks stale environmental memory for immediate decisions.
7. Temporary environmental observations do not automatically become permanent memories.
8. Environmental predictions are revisable.
9. Sensor disagreement is preserved and investigated.
10. Calibration and sensor health affect measurement trust.
11. Environmental data is privacy-sensitive.
12. Raw environmental streams must have bounded retention.
13. Core environmental processing remains local/offline-capable.
14. Environmental state can influence cognition but cannot override safety systems.
15. Environmental knowledge requires evidence proportional to its permanence and importance.
16. Simulation is a validation tool, not proof of real-world performance.
17. Hardware-independent semantic interfaces must remain available so better open-source/local solutions can replace individual implementations.
18. Internal thermal protection is independent of cognitive reasoning.

---

## 59. Final Principle

> **Novi should understand the physical environment as a changing, uncertain, measurable system—not as a static description generated by its language model.**

Environmental context becomes valuable when Novi can connect:

```text
what the sensors measured
        ↓
what was happening
        ↓
where it happened
        ↓
when it happened
        ↓
what Novi expected
        ↓
what changed
        ↓
what was learned
```

That creates an evidence-backed environmental history that can continuously improve perception, navigation, interaction, prediction and autonomy while remaining local-first, privacy-aware and replaceable at the implementation level.
