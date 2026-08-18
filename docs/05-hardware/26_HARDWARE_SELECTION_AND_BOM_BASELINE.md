# Novi — Hardware Selection & BOM Baseline

**Date:** 2026-08-17  
**Status:** P0 engineering baseline / components not yet frozen  
**Purpose:** Turn the high-level hardware architecture into an engineering-ready selection framework without prematurely committing Novi to a physical build.

> **Important:** Jetson AGX Orin 64GB remains a reference candidate, not a final commitment. Hardware selection must follow measured software workload and physical constraints.

---

# 1. Hardware philosophy

The physical robot is an embodiment of Novi, not the definition of Novi.

The hardware must therefore satisfy the cognitive and physical requirements while remaining replaceable behind stable interfaces.

Selection order:

```text
North Star capability
        ↓
Functional requirement
        ↓
Interface requirement
        ↓
Performance requirement
        ↓
Safety requirement
        ↓
Power/thermal requirement
        ↓
Mechanical requirement
        ↓
Candidate components
        ↓
Benchmarks
        ↓
BOM decision
```

---

# 2. System-level hardware architecture

```text
                           NOVI BODY
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
      COMPUTE              SENSING               OUTPUT
        │                     │                     │
   Edge computer       ┌──────┼──────┐       ┌──────┼──────┐
   storage             │      │      │       │      │      │
                       Vision Audio Motion   Voice Display Light
                       │      │      │
                       └──────┼──────┘
                              ↓
                       TIME / CALIBRATION
                              ↓
                         SENSOR FUSION
                              ↓
                          NOVI CORE
                              │
                       GOVERNANCE/SAFETY
                              │
                    CONTROL / ROS 2 / MCU
                              │
                           ACTUATORS
                              │
                         POWER SYSTEM
```

---

# 3. Compute

## Candidate A — Jetson AGX Orin 64GB

Current reference target because it provides substantial memory and NVIDIA robotics/AI ecosystem compatibility.

NVIDIA currently lists JetPack 7.2 / Jetson Linux 39.2 for Jetson Orin, with Ubuntu 24.04, CUDA 13.2.1 and TensorRT 10.16.2. citeturn5search3

The current Jetson AGX Orin developer kit documentation identifies JetPack 7.2 as the latest JetPack release for the developer kit. citeturn4search1

## Selection requirements

The final compute platform must satisfy:

- cognitive runtime latency;
- LLM/VLM memory requirements;
- perception throughput;
- sensor I/O;
- camera bandwidth;
- storage bandwidth;
- ROS 2 workload;
- simulation-independent runtime;
- power envelope;
- thermal envelope;
- physical dimensions;
- boot/recovery requirements;
- offline operation;
- secure update path.

## Required benchmark

Measure at minimum:

- P50/P95/P99 model latency;
- perception FPS;
- inference throughput;
- CPU utilization;
- GPU utilization;
- RAM;
- GPU memory;
- storage I/O;
- startup time;
- power draw;
- thermal behavior;
- throttling;
- failure/recovery time.

These are explicitly recommended by the NVIDIA research before selecting the edge platform. fileciteturn23file0L11-L27

---

# 4. Storage

Required storage classes:

```text
Boot / OS
Model artifacts
Application
Durable Novi state
Event history
Knowledge graph
Vector indexes
Media/keyframes
Logs/traces
Recovery artifacts
```

## Requirements

- high endurance;
- sufficient sustained write rate;
- power-loss resilience appropriate to design;
- health telemetry;
- encryption capability;
- replacement procedure;
- backup/export;
- recovery testing.

**Baseline candidate:** NVMe-class local storage where the selected compute carrier supports it.

Exact capacity must be derived from model sizes, event rate, media retention and recovery policy.

---

# 5. Vision system

## Required capabilities

- forward RGB;
- wide environmental coverage;
- side/rear coverage as needed;
- downward/floor awareness;
- depth;
- low-light capability where justified.

## Selection criteria

- resolution;
- frame rate;
- FOV;
- rolling/global shutter;
- low-light performance;
- HDR;
- depth accuracy;
- synchronization;
- interface;
- latency;
- power;
- driver support;
- ROS 2 support;
- Jetson compatibility;
- mechanical placement.

## Candidate families

Evaluate, rather than preselect:

- MIPI CSI-2 camera modules;
- USB3 cameras;
- stereo depth cameras;
- RGB-D cameras;
- event cameras if later research demonstrates value;
- industrial/GMSL camera systems for a future high-bandwidth design.

The final choice must follow FOV and synchronization analysis.

---

# 6. Depth sensing

Depth may be provided by:

- stereo cameras;
- active RGB-D;
- ToF;
- LiDAR-derived geometry.

Required outputs:

- depth map/point cloud;
- confidence/quality;
- timestamp;
- calibration identity;
- sensor pose.

Depth must be treated as evidence, not automatically as truth.

---

# 7. LiDAR

Required for robust spatial geometry and navigation redundancy.

Selection criteria:

- 2D vs 3D;
- horizontal/vertical FOV;
- range;
- angular resolution;
- point rate;
- update rate;
- indoor/outdoor behavior;
- reflective/transparent surface behavior;
- ROS 2 driver maturity;
- power;
- mechanical envelope;
- eye-safety classification where applicable.

**Initial recommendation:** evaluate a 2D LiDAR for navigation baseline and a 3D LiDAR only if the world-model/perception requirements justify the cost, power and data volume.

Do not assume that more sensing is automatically better.

---

# 8. IMU and proprioception

Minimum:

- accelerometer;
- gyroscope.

Potential:

- magnetometer;
- wheel encoders;
- joint encoders;
- actuator position;
- actuator velocity;
- current/load/torque;
- motor temperature.

Selection requirements:

- noise density;
- bias stability;
- sample rate;
- timestamp quality;
- synchronization;
- mounting orientation;
- calibration;
- temperature behavior.

---

# 9. Audio input

Use a microphone array rather than a single microphone.

Required capabilities:

- far-field capture;
- beamforming;
- acoustic echo cancellation;
- noise suppression;
- voice activity detection;
- direction of arrival;
- speaker localization;
- diarization;
- acoustic event detection.

Hardware selection criteria:

- number of microphones;
- geometry;
- sample rate;
- synchronized capture;
- SNR;
- enclosure acoustics;
- speaker feedback rejection;
- interface;
- driver support.

---

# 10. Audio output

Multiple speakers are preferred where spatial interaction is part of the design.

Requirements:

- speech intelligibility;
- volume;
- frequency response;
- enclosure integration;
- low-latency playback;
- echo cancellation compatibility;
- power consumption.

---

# 11. Thermal sensing

Two independent domains must remain distinct.

## External thermal sensing

Purpose:

- hot/cold object detection;
- environmental thermal understanding;
- thermal anomaly detection;
- safety around hot surfaces.

## Internal thermal monitoring

Monitor:

- compute;
- battery;
- motor/actuator;
- power electronics;
- storage;
- high-current components.

Internal protection must not depend on the thermal AI/perception stack.

---

# 12. Environmental sensors

Candidate sensors:

- ambient temperature;
- humidity;
- pressure;
- CO2;
- VOC;
- particulate matter;
- ambient light;
- smoke where justified.

Each sensor must justify its contribution to the North Star or safety/environmental requirements.

---

# 13. Tactile/contact/force sensing

Required minimum safety/interaction mechanisms:

- bumper/contact switches;
- actuator current/load monitoring;
- physical contact detection.

Optional:

- force sensors;
- tactile arrays;
- pressure sensors.

Vision must not be the only mechanism for detecting contact.

---

# 14. Actuation

The final body design determines actuator count and type.

Every actuator must expose, where technically possible:

```text
command
position
velocity
current
load/torque
temperature
fault state
```

The control architecture must support:

- hard limits;
- software limits;
- current limits;
- acceleration/deceleration limits;
- watchdog timeout;
- safe disable;
- command acknowledgement;
- actual-vs-commanded comparison.

---

# 15. Motor/control architecture

Recommended hierarchy:

```text
Novi cognition
      ↓
Skill
      ↓
Action request
      ↓
Governance
      ↓
Safety
      ↓
ROS 2
      ↓
ros2_control
      ↓
Motor/actuator controller
      ↓
Motor
```

A dedicated MCU or motor controller should own the lowest-level deterministic control and fault handling where appropriate.

The LLM must never be the final motor authority.

---

# 16. Power architecture

Required subsystems:

```text
Battery
 ↓
BMS
 ↓
Main protection / fuse
 ↓
Power distribution
 ├── compute
 ├── sensors
 ├── displays
 ├── audio
 ├── actuators
 └── auxiliary systems
```

Telemetry:

- pack voltage;
- current;
- state of charge;
- state of health;
- temperature;
- charge state;
- estimated runtime;
- instantaneous power;
- rail health.

Required calculations:

- peak load;
- continuous load;
- actuator surge;
- compute worst case;
- sensor worst case;
- thermal/power coupling;
- battery runtime.

---

# 17. Battery/BMS

The battery system requires:

- cell chemistry decision;
- nominal voltage;
- capacity;
- peak current;
- continuous current;
- BMS;
- over-current protection;
- over-voltage/under-voltage protection;
- over-temperature protection;
- charging strategy;
- connector safety;
- physical containment;
- service/replacement procedure.

Battery selection must follow a formal electrical and thermal safety review.

---

# 18. Safety controller

Novi needs an independent physical safety path.

Minimum conceptual elements:

```text
Physical E-STOP
      ↓
Safety controller / power isolation
      ↓
Actuator enable
```

Additional:

- watchdog;
- motor-enable interlock;
- battery protection;
- over-temperature cutback;
- over-current protection;
- safe boot state;
- safe shutdown;
- communication-loss behavior.

Safety must function when:

- LLM is unavailable;
- GPU crashes;
- ROS 2 crashes;
- network is unavailable;
- perception fails;
- storage fails;
- software hangs.

---

# 19. Connectivity

Core local interfaces:

- USB;
- Ethernet;
- CAN/CAN-FD;
- UART;
- I2C;
- SPI;
- GPIO;
- PCIe where required.

Optional:

- Wi-Fi;
- Bluetooth.

Connectivity must never be required for core safe operation.

---

# 20. Displays and expressive hardware

## Face/eye display

Target: approximately 5 inches.

Purpose:

- eyes;
- gaze;
- expression;
- conversational state;
- attention/social cues.

## Body display

Target: approximately 5–7 inches.

Purpose:

- maps;
- diagnostics;
- detailed information;
- occasional interaction.

## RGB lighting

Use for semantic, non-safety-critical state indication:

- listening;
- speaking;
- thinking;
- navigation;
- charging;
- offline;
- warning;
- privacy.

Safety warnings require independent mechanisms.

---

# 21. Mechanical architecture

Before final component purchasing, define:

- overall dimensions;
- mass budget;
- center of gravity;
- payload;
- drive geometry;
- wheel size;
- turning radius;
- ground clearance;
- sensor mounting points;
- display mounting;
- speaker/microphone geometry;
- cable routing;
- battery compartment;
- compute cooling path;
- service access;
- removable panels;
- fasteners;
- ingress protection where needed.

Mechanical CAD must become the source for final mounting and sensor FOV validation.

---

# 22. Sensor placement and FOV design

Create a physical FOV coverage model before finalizing cameras/LiDAR.

The model should answer:

- what percentage of the environment is visible;
- blind spots;
- floor visibility;
- obstacle visibility;
- human face visibility;
- object detection range;
- sensor overlap;
- calibration targets;
- occlusion.

The final sensor count should be derived from this model rather than intuition.

---

# 23. Time synchronization

Define a common timing architecture for:

- cameras;
- LiDAR;
- IMU;
- microphones;
- encoders;
- actuator feedback;
- compute timestamps.

The specification must distinguish:

```text
sensor timestamp
system timestamp
ROS timestamp
simulated timestamp
recorded timestamp
```

Where high-rate multi-sensor synchronization requires it, evaluate hardware timestamping and PTP.

---

# 24. Calibration

Every physical sensor must have:

- sensor ID;
- model;
- serial number;
- firmware;
- calibration version;
- calibration date;
- extrinsic transform;
- intrinsic parameters where applicable;
- uncertainty;
- calibration health.

Calibration artifacts must be versioned and included in provenance.

---

# 25. Hardware health model

Novi must maintain:

```text
AVAILABLE
DEGRADED
FAILED
DISABLED
CALIBRATION_REQUIRED
THERMALLY_LIMITED
POWER_LIMITED
UNKNOWN
```

Hardware health becomes part of the cognitive context.

Example:

```text
LiDAR degraded
    ↓
spatial confidence reduced
    ↓
Novi world-model uncertainty increases
    ↓
navigation policy becomes more conservative
```

---

# 26. Privacy hardware

Cameras and microphones require explicit privacy states.

Required:

- visible privacy indication;
- software state;
- hardware disable path where appropriate;
- diagnostics that respect privacy state;
- biometric-processing controls;
- audit record for privacy-state transitions.

---

# 27. Hardware BOM structure

The final BOM should contain at least:

| Category | Required fields |
|---|---|
| Compute | model, memory, power, interfaces, software compatibility |
| Storage | model, capacity, endurance, interface, power |
| Camera | model, sensor, FOV, resolution, FPS, interface, sync |
| Depth | model, range, accuracy, interface, power |
| LiDAR | model, range, FOV, rate, interface, power |
| IMU | model, range, noise, rate, interface |
| Encoder | type, resolution, interface |
| Microphone | array geometry, SNR, rate, interface |
| Speaker | power, impedance, response, interface |
| Thermal | range, resolution, interface |
| Display | size, resolution, brightness, interface, power |
| LED | type, zones, controller, power |
| Motor | torque, speed, voltage, current, feedback |
| Motor controller | interface, current, safety, firmware |
| Battery | chemistry, voltage, Ah/Wh, current |
| BMS | current, telemetry, protection |
| Power | converters, rails, fuses, telemetry |
| Safety MCU | MCU, watchdog, I/O, isolation |
| Connectivity | radio, Ethernet, CAN, USB |
| Mechanical | chassis, mounts, fasteners, cooling |

Each row must include:

- primary candidate;
- alternative;
- selection status;
- reason;
- test evidence;
- supplier/source;
- cost;
- availability;
- replacement path;
- dependency risk.

---

# 28. Hardware selection gates

A component is not approved until it passes:

1. functional requirement;
2. interface compatibility;
3. driver/software compatibility;
4. performance requirement;
5. power requirement;
6. thermal requirement;
7. mechanical requirement;
8. safety requirement;
9. privacy/security requirement;
10. availability/sourcing requirement;
11. lifecycle/replacement requirement;
12. validation test.

---

# 29. What must be measured before final compute selection

The cognitive/software prototype must produce a workload profile:

```text
LLM memory
VLM memory
Perception FPS
Camera count
Camera resolution/FPS
Depth rate
LiDAR point rate
Audio rate
World-model update rate
Memory query rate
Planning latency
ROS CPU load
Storage write rate
Peak GPU load
Average GPU load
Power envelope
Thermal envelope
```

Only then should the final compute board be selected.

NVIDIA's research explicitly recommends this benchmark-first approach. fileciteturn23file0L11-L27

---

# 30. Current hardware status

| Area | Status |
|---|---|
| High-level hardware architecture | Defined |
| Compute capability requirements | Defined conceptually |
| Final compute board | **Not frozen** |
| Camera selection | Missing |
| Depth selection | Missing |
| LiDAR selection | Missing |
| IMU selection | Missing |
| Audio hardware | Missing |
| Thermal hardware | Missing |
| Displays | Conceptual only |
| Lighting | Conceptual only |
| Actuators | Not frozen |
| Motor controller | Missing |
| Battery/BMS | Missing |
| Power architecture | Missing detailed design |
| Safety controller | Missing detailed design |
| Mechanical CAD | Missing |
| Sensor synchronization | Missing |
| Calibration specification | High-level only |
| Sensor fusion hardware requirements | High-level only |
| Hardware BOM | **Missing** |
| Hardware validation plan | **Missing** |

---

# 31. Physical hardware freeze gate

Do not freeze the physical BOM until:

- software workload is measured;
- robot body geometry is defined;
- sensor FOV coverage is modeled;
- power budget is calculated;
- thermal budget is calculated;
- safety architecture is defined;
- synchronization architecture is defined;
- driver/ROS compatibility is tested;
- simulation equivalents exist;
- component alternatives are identified;
- validation procedures exist.

This is intentionally later than Stage 1–5 of the cognitive implementation.
