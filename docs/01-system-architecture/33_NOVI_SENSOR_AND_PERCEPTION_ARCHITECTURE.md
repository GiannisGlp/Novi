# 33 — Novi Sensor and Perception Architecture

**Status:** Requirements baseline — component selection pending  
**Priority:** P0  
**Authority:** System Architecture / Hardware integration boundary  
**Decision:** Define the complete sensing envelope now; defer final hardware selection until the functional Novi software baseline has been validated on the user's Mac and the real workload has been measured.

## 1. Purpose

This document defines what Novi should be able to sense, why each sensing modality exists, its role in perception/localization/safety, candidate implementation classes, expected data characteristics, and the information that must be captured before final component selection.

The objective is not to purchase every sensor immediately. The objective is to prevent the hardware architecture from accidentally omitting an important sensing modality and to preserve the option to select components later using measured requirements.

## 2. Design principle

Novi should use **sensor diversity**, not a single "magic" sensor.

No single sensor is assumed to be universally reliable. Camera, depth, LiDAR, IMU, wheel odometry, GNSS, thermal and audio observations should be fused where useful, with uncertainty and provenance preserved.

NVIDIA's Isaac ROS Visual SLAM documentation explicitly describes the value of combining visual, inertial and other independent odometry sources because each modality has different failure modes. Its current Visual SLAM implementation supports multi-camera, visual-inertial and RGB-D tracking modes. citeturn0search0turn0search2

## 3. Target sensing envelope

| Modality | Target | Primary purpose | Priority | Selection state |
|---|---|---|---|---|
| RGB cameras | Multiple | visual perception, recognition, navigation, interaction | P0 | Open |
| RGB-D cameras | Multiple | depth, obstacle geometry, 3D perception, near-field interaction | P0 | Open |
| 3D LiDAR | 1 | geometry, navigation, mapping, redundancy | P0 | Open |
| 2D LiDAR | Optional | planar navigation / redundancy / low-cost fallback | P1 | Open |
| GNSS/GPS | 1 | global outdoor position | P0 | Open |
| RTK GNSS | Optional | high-accuracy outdoor positioning | P1 | Open |
| IMU | 1+ | orientation, acceleration, inertial odometry | P0 | Open |
| Wheel encoders | Every driven wheel/axle | odometry, velocity, slip detection | P0 | Open |
| Thermal camera | 1 | thermal awareness, humans/animals, equipment, low-light/night redundancy | P0 | Open |
| Ambient temperature | 1+ | environment + thermal model | P1 | Open |
| Microphone array | 4–8+ microphones | speech capture, source direction, beamforming | P0 | Open |
| Speakers | 2+ | speech, alerts, interaction | P0 | Open |
| Ultrasonic/ToF proximity | Several | very-near obstacle detection / docking / redundancy | P1 | Open |
| Bumper/contact switches | Multiple zones | physical collision detection | P0 safety | Open |
| Cliff/drop sensors | Multiple | stairs/edges/drop-off detection | P0 for relevant mobility | Open |
| Light/ambient sensor | 1 | exposure/environment context | P2 | Open |
| Magnetometer | 1 | heading aid where magnetically clean | P2 | Open |
| Barometer | 1 | pressure/relative elevation context | P2 | Open |
| UWB | Optional | local ranging / indoor localization | P1 | Open |
| Wi-Fi/Bluetooth | 1 | networking/provisioning/peripherals | P0 | Open |
| Cellular | Optional | remote connectivity outside Wi-Fi | P1 | Open |
| Power/current/voltage sensors | Multiple rails | energy model, fault detection, battery estimation | P0 | Open |
| Motor temperature/current | Per drive channel where practical | actuator health, overload/slip/fault detection | P0 safety | Open |
| Compute temperature | SoC + board + enclosure | thermal protection | P0 | Open |

## 4. RGB camera system

### Requirement

Novi should have multiple RGB viewpoints rather than one forward-facing camera.

Initial topology to evaluate:

- front wide-angle;
- front/forward high-quality camera;
- rear camera;
- left side camera;
- right side camera;
- optional upward/downward camera depending on chassis and manipulation requirements.

The final number is workload-dependent. NVIDIA's current Isaac ROS Visual SLAM implementation supports multiple cameras and documents a default two-camera stereo configuration, with support for multi-camera tracking. citeturn0search0

### Capture requirements to measure

- resolution;
- FPS;
- global vs rolling shutter;
- HDR/dynamic range;
- exposure control;
- low-light performance;
- lens/FOV;
- synchronization;
- interface bandwidth;
- power;
- calibration stability.

### Why multiple RGB cameras

They provide:

- wider coverage;
- fewer blind spots;
- visual redundancy;
- better human interaction coverage;
- visual odometry diversity;
- better object tracking across the robot's surroundings.

## 5. RGB-D / depth camera system

At least one high-quality RGB-D camera should be evaluated, with multiple units strongly preferred if the chassis permits.

A current example is the RealSense D455: its manufacturer specifies a global-shutter RGB camera, 87° × 58° FOV, approximately 0.6–6 m ideal range, an integrated IMU, and improved depth performance from its 95 mm stereo baseline. citeturn1search8

Candidate placement:

- forward;
- rear;
- optional side/near-field pair.

Depth is useful for:

- obstacle geometry;
- free-space estimation;
- manipulation/interaction;
- people distance;
- near-field collision avoidance;
- 3D scene understanding.

## 6. 3D LiDAR

Novi should reserve physical and compute interfaces for a 3D LiDAR.

Primary uses:

- geometric mapping;
- obstacle detection independent of RGB appearance;
- localization redundancy;
- operation in darkness;
- robust range measurements;
- 3D reconstruction.

NVIDIA's Isaac ROS nvBlox supports RGB-D and/or LiDAR data for dense 3D mapping and temporal costmaps for navigation. citeturn0search6

Final LiDAR selection must consider:

- range;
- vertical FOV;
- horizontal FOV;
- scan pattern;
- points/sec;
- update rate;
- range accuracy;
- reflective/black-surface behavior;
- sunlight behavior;
- power;
- interface;
- weight;
- mechanical vibration sensitivity;
- weather rating;
- price.

## 7. GNSS / GPS

Novi should have global navigation capability outdoors.

Baseline:

- multi-constellation GNSS;
- position, velocity and timing output;
- antenna with known placement;
- timestamp quality;
- quality indicators and fix status.

Optional high-accuracy tier:

- RTK GNSS;
- correction service/base station support;
- centimeter-class positioning where conditions permit.

GNSS must **never** be treated as the sole localization source. Indoor environments, urban canyons, foliage, multipath and intentional/unintentional interference can degrade it.

## 8. IMU

The IMU is a core sensor and should be treated as a high-rate timing and motion source.

Required measurements:

- 3-axis acceleration;
- 3-axis angular velocity;
- temperature;
- timestamp;
- calibration state;
- covariance/quality information.

Preferred:

- magnetometer as a separate/optional source;
- hardware timestamping;
- known noise characteristics;
- temperature compensation;
- vibration characterization.

Isaac ROS Visual SLAM explicitly supports IMU fusion and uses IMU measurements to improve tracking when visual features are insufficient. citeturn0search2turn0search9

## 9. Wheel encoders

Every driven wheel/axle should provide encoder feedback.

Required outputs:

- position/ticks;
- velocity;
- direction;
- timestamp;
- fault/disconnect state.

Wheel odometry provides an independent motion estimate and enables detection of:

- wheel slip;
- stalled motors;
- unexpected motion;
- encoder failure;
- actuator asymmetry.

## 10. Thermal perception

A thermal camera is part of the intended Novi sensing envelope, not merely an optional gadget.

Use cases:

- people detection in difficult lighting;
- animals;
- hot/cold objects;
- equipment overheating;
- battery/drive thermal awareness;
- night/low-light redundancy;
- environmental understanding.

A low-power FLIR Lepton-class module is an example of the available design space. Current Lepton variants include radiometric 80×60 and 160×120 options, with some models providing absolute temperature output; the manufacturer lists approximately 150 mW typical operating consumption for Lepton 2.5. citeturn1search0turn1search1

Important distinction:

**Thermal imaging ≠ safety-certified temperature measurement.**

Critical battery/motor/compute temperatures should also use dedicated temperature sensors.

## 11. Audio perception

Novi should have a **microphone array**, not a single microphone.

Target:

- 4 microphones minimum;
- 6–8 microphones preferred for a serious prototype;
- geometry distributed around the robot;
- synchronized sampling;
- known microphone positions;
- wind/noise mitigation;
- echo cancellation support.

This enables:

- speech capture;
- voice activity detection;
- direction of arrival (DoA);
- beamforming;
- speaker separation where feasible;
- localization of a speaking person;
- better rejection of motor/fan noise.

The microphone array should produce both audio and **source-direction estimates with confidence**, rather than handing raw audio directly to the cognition layer without provenance.

## 12. Speakers

Minimum:

- stereo or spatially separated speakers.

Preferred:

- multiple speakers positioned to support spatial interaction;
- dedicated emergency/attention sounder where required;
- independent volume control;
- echo reference to the microphone subsystem.

Novi should distinguish:

```text
speech output
system notification
warning
emergency alarm
```

A safety alarm must not depend on the generative speech model.

## 13. Near-field sensors

RGB-D and LiDAR should not be the only physical protection against very-close obstacles.

Evaluate:

- ultrasonic sensors;
- short-range ToF sensors;
- bumper/contact switches;
- cliff/drop sensors.

These sensors should be inexpensive, independent and physically simple where possible.

For safety-critical functions, sensor independence matters more than AI sophistication.

## 14. Environmental sensors

Optional but recommended:

- ambient temperature;
- humidity;
- pressure/barometer;
- ambient light;
- air-quality sensing only if a specific mission requires it.

These should not be added merely because they exist. Each sensor needs a defined Novi use case.

## 15. Localization stack

Novi should be capable of fusing:

```text
GNSS / RTK
      +
IMU
      +
wheel odometry
      +
visual odometry / VSLAM
      +
LiDAR localization
      +
RGB-D geometry
      +
optional UWB
      ↓
state estimator
      ↓
pose + velocity + covariance
```

No single modality is the global truth in every environment.

## 16. Hardware health sensing

The robot must sense itself as well as its environment.

Required health telemetry should include:

- battery voltage;
- battery current;
- battery temperature;
- state of charge estimate;
- BMS alarms;
- compute voltage/current where measurable;
- SoC temperature;
- board temperature;
- enclosure temperature;
- motor current;
- motor temperature;
- motor-controller temperature;
- fan state;
- storage health;
- sensor connectivity.

This information feeds `HardwareHealth` and the safety/degradation architecture rather than being treated as ordinary perception.

## 17. Connectivity and time

The sensor architecture must reserve:

- Ethernet;
- USB;
- CSI/MIPI or equivalent camera interfaces;
- CAN/CAN-FD where required;
- UART;
- GPIO;
- I2C/SPI for low-level sensors;
- Wi-Fi;
- Bluetooth;
- optional cellular;
- optional UWB.

The platform must support timestamping and synchronization across sensor modalities.

The AGX Orin developer kit, for example, exposes multiple USB ports, Ethernet, camera MIPI CSI, PCIe, audio and GPIO/automation interfaces, illustrating the breadth of interfaces the compute platform must accommodate. citeturn0search1

## 18. Recommended sensor redundancy philosophy

The goal is not maximum sensor count. The goal is **independent failure modes**.

Examples:

| Capability | Primary | Independent backup |
|---|---|---|
| Position | VIO/LiDAR/odometry fusion | GNSS outdoors |
| Obstacle geometry | LiDAR + depth | RGB / proximity |
| Motion | IMU + encoders | VSLAM/LiDAR |
| Human perception | RGB | thermal/depth |
| Speech | microphone array | alternate microphone path |
| Temperature | dedicated sensors | thermal camera |
| Collision | depth/LiDAR | bumper/proximity |
| Power | BMS telemetry | independent voltage/current monitor |
| Compute health | SoC telemetry | external board/ambient sensor |

## 19. Mac-first development strategy

**Do not wait for the final robot hardware to start Novi.**

The software should be developed first against:

1. recorded sensor datasets;
2. synthetic sensor streams;
3. simulated sensors;
4. replayable ROS 2 bags;
5. mock sensor drivers;
6. laptop cameras/microphones where available;
7. progressively real hardware.

The user's Mac is therefore a **functional-development and architecture-validation platform**, not the final performance reference.

The initial objective is to prove:

- sensor contracts;
- synchronization;
- perception interfaces;
- cognition interfaces;
- memory ingestion;
- localization interfaces;
- autonomy interfaces;
- safety boundaries;
- data provenance;
- replayability.

Performance can initially be slower.

The important question is whether the complete pipeline is **functionally correct and measurable**.

## 20. Why this strategy is sound

The final Jetson target should be selected after the software pipeline and model workload exist.

NVIDIA explicitly positions Jetson AGX Orin as a development/prototyping platform capable of emulating the Orin module family, and its robotics stack includes Isaac ROS, Visual SLAM and other accelerated workflows. citeturn0search3turn0search4

This means we can first establish the workload and then measure its behavior on candidate hardware instead of choosing the computer first and forcing the architecture around it.

## 21. Model-development implications

The Mac phase should support model experimentation without assuming the final robot will run the exact same model configuration.

For every candidate AI model we must eventually record:

- model identifier/version;
- parameter count;
- precision/quantization;
- RAM requirement;
- GPU memory requirement;
- context length;
- KV-cache behavior;
- inference latency;
- throughput;
- concurrent-model behavior;
- startup time;
- power;
- fallback model;
- safety classification.

The final model selection is therefore a **later evidence-based decision**.

## 22. Initial physical build — not yet final BOM

The first hardware prototype should reserve interfaces for at least:

```text
1× compute module/system
1× production-capable carrier
1× NVMe
multiple RGB cameras
multiple RGB-D cameras
1× 3D LiDAR
1× GNSS antenna + receiver
1× IMU
wheel encoders
1× thermal camera
4–8× microphone array
2+ speakers
near-field proximity sensors
bumper/contact sensors
cliff sensors
battery/BMS telemetry
motor telemetry
thermal telemetry
Wi-Fi/Bluetooth
Ethernet/CAN
MCU / real-time control subsystem
hardware emergency-stop path
```

The final quantities and part numbers remain open.

## 23. Sensor selection gate

Before purchasing final components, each candidate must be scored on:

- functional coverage;
- accuracy;
- range;
- update rate;
- latency;
- synchronization;
- interface;
- CPU/GPU load;
- memory/bandwidth;
- power;
- size/weight;
- environmental rating;
- mechanical integration;
- driver quality;
- ROS 2 support;
- Isaac ROS compatibility where relevant;
- calibration tooling;
- availability;
- lifecycle/support;
- cost;
- privacy/security implications.

## 24. Explicit decision

**No final sensor BOM is approved yet.**

The sensing requirements are now defined so that later component decisions can be made deliberately.

The compute platform also remains open between the AGX Orin 64GB and Thor-class options. The final decision should occur only after the functional Novi software, sensor pipeline and AI model workload have been demonstrated and measured.

## 25. Definition of done

This document becomes an approved hardware sensor baseline when:

- every P0 sensing capability has a selected implementation;
- sensor interfaces are mapped to the chosen carrier/MCU;
- power and thermal budgets are measured;
- timestamp/synchronization requirements are validated;
- ROS 2 drivers are tested;
- calibration procedures exist;
- sensor failure/degradation behavior is defined;
- representative datasets exist;
- sensor fusion is validated;
- the physical safety layer has independent sensing where required.

Until then this document is a **requirements and architecture baseline**, not a final shopping list.

## 26. Research references

Primary sources consulted for this baseline include NVIDIA Isaac ROS and Jetson documentation, RealSense product documentation, and Teledyne FLIR OEM documentation. These sources establish examples and integration capabilities; they do not constitute approval of any specific final component.

- NVIDIA Isaac ROS Visual SLAM: citeturn0search0turn0search2
- NVIDIA Isaac ROS platform overview / nvBlox: citeturn0search6
- NVIDIA Jetson AGX Orin: citeturn0search4
- NVIDIA Jetson AGX Orin developer-kit hardware interfaces: citeturn0search1
- RealSense D455: citeturn1search8
- Teledyne FLIR Lepton OEM: citeturn1search0turn1search1
