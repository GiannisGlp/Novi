# 00 — High-Level Hardware Architecture

## Status

**ARCHITECTURE — HIGH LEVEL / V1**

## Purpose

Define the physical hardware architecture required for Novi without prematurely locking exact components.

This document answers **what physical capabilities Novi needs**. Detailed engineering documents will later answer **which exact components, how they are wired, how they are mounted, how they are calibrated, and how they are validated**.

## 1. Hardware Architecture

```text
                         NOVI HARDWARE
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
      COMPUTE              SENSING               OUTPUT
        │                     │                     │
   Jetson Orin 64GB     ┌─────┼─────┐       ┌──────┼──────┐
        │                │     │     │       │      │      │
     Storage           Vision Audio Motion  Voice Displays Lighting
        │                │     │     │       │      │      │
        └────────────────┼─────┼─────┼───────┴──────┴──────┘
                         │     │     │
                    Sensor Fusion / World Model
                         │
                  Diagnostics + Health
                         │
                  Power + Thermal System
                         │
                    Safety Controller
```

## 2. Compute

Initial target:

**NVIDIA Jetson AGX Orin 64GB**

Responsibilities include:

- local AI inference;
- perception processing;
- sensor processing;
- cognition;
- memory;
- autonomy;
- local voice processing;
- hardware diagnostics;
- local networking services;
- application/runtime orchestration.

The design must keep critical operation local.

## 3. Vision System

Novi requires multiple cameras because one camera cannot provide complete environmental coverage.

The high-level system should consider:

- forward-facing RGB camera;
- wide-angle environmental cameras;
- side/rear coverage where required;
- downward-facing camera for floor/obstacle awareness;
- depth camera/sensor;
- optional low-light/IR capability.

Exact count and placement will be determined by the mechanical design and field-of-view analysis.

## 4. Environmental Thermal Sensing

Novi should have an environmental thermal camera or equivalent thermal sensing capability.

Purpose:

- detect hot/cold surfaces;
- identify thermal anomalies;
- improve environmental understanding;
- assist with safety around hot objects;
- support physical-world knowledge.

Thermal measurements must retain sensor identity, calibration state and uncertainty when converted into persistent knowledge.

## 5. Internal Thermal Monitoring

Separate sensors/telemetry must monitor Novi itself:

- Jetson CPU/GPU/SoC;
- battery;
- motors/actuators;
- power electronics;
- storage;
- other heat-producing components.

The system must detect thermal stress and degrade workloads before unsafe temperatures are reached.

## 6. Spatial and Proximity Sensing

Novi should use complementary spatial sensors:

- LiDAR;
- depth sensing;
- ToF/proximity sensors;
- ultrasonic sensors where useful;
- short-range IR/proximity sensing where useful.

LiDAR and cameras should complement rather than unnecessarily duplicate one another.

## 7. Motion and Orientation

Novi requires an IMU containing at least:

- accelerometer;
- gyroscope.

A magnetometer may be included where it provides useful value and does not introduce unacceptable magnetic interference.

The system should also support:

- wheel encoders;
- actuator position feedback;
- motor current/torque feedback;
- motion/fall detection.

## 8. Audio Input

Novi requires a microphone array rather than relying on a single microphone.

The audio system should support:

- far-field capture;
- beamforming;
- acoustic echo cancellation;
- noise suppression;
- voice activity detection;
- direction of arrival;
- speaker localization;
- speaker diarization;
- speaker identification where permitted;
- acoustic event detection.

The objective is for Novi to understand not only **what** was said, but approximately **where the sound originated**.

## 9. Audio Output

Multiple speakers should provide:

- clear speech;
- spatially useful audio;
- sufficient volume;
- local voice interaction;
- audio feedback for system states.

Speaker placement should be considered together with microphone placement to minimize acoustic feedback.

## 10. Face / Eye Display

A small approximately **5-inch display** is planned for Novi's face.

Primary purposes:

- eyes;
- visual expressions;
- gaze/attention representation;
- simple conversational feedback;
- emotional/social expression;
- basic status.

The display is an output modality, not part of the cognitive dependency chain.

## 11. Body Display

A second approximately **5–7-inch display** is planned on the body.

It should remain mostly idle and become active when additional information is useful, such as:

- detailed information;
- maps;
- diagnostics;
- system state;
- notifications;
- occasional user interaction.

## 12. RGB Lighting

Multi-zone RGB lighting around the body can provide ambient and semantic feedback.

Potential zones:

- head;
- neck;
- body;
- arms;
- base;
- rear.

Potential states:

- listening;
- speaking;
- thinking;
- attention;
- navigation;
- charging;
- sleep;
- offline;
- warning;
- error;
- privacy.

RGB is supplementary. Safety-critical warnings must have independent mechanisms.

## 13. Actuation

The final mechanical design determines exact actuators, but the hardware architecture should support feedback for:

- position;
- velocity;
- current;
- torque/load where available;
- temperature;
- commanded vs actual movement.

This enables Novi to detect stalls, unexpected resistance and actuator faults.

## 14. Power and Battery

Novi requires a battery/power subsystem with telemetry for:

- voltage;
- current;
- state of charge;
- state of health;
- battery temperature;
- charging state;
- power consumption;
- estimated remaining runtime.

Power management must be integrated with autonomy so Novi can reduce nonessential computation when energy is limited.

## 15. Environmental Sensors

The architecture should allow optional environmental sensors such as:

- ambient temperature;
- humidity;
- pressure;
- CO₂;
- VOC/air quality;
- particulate matter;
- ambient light;
- smoke detection where appropriate.

Exact selection will depend on the intended operating environment.

## 16. Contact and Tactile Sensing

Novi should have physical contact sensing appropriate to its mechanical design:

- bumper/contact switches;
- force sensors;
- tactile sensors in selected areas;
- actuator load/current sensing.

Vision should not be the only mechanism used to detect physical contact.

## 17. Hardware Safety

Safety must be independent of the AI model and network.

The final architecture should include appropriate mechanisms such as:

- physical emergency stop;
- motor power cut-off;
- hardware interlocks;
- watchdogs;
- over-temperature protection;
- battery protection;
- over-current protection;
- safe actuator defaults.

Exact implementation depends on the mechanical/electrical design and risk assessment.

## 18. Connectivity

Novi will have:

- Wi-Fi;
- Bluetooth.

These are optional capabilities, not core dependencies.

Novi must remain fully functional without:

- Wi-Fi;
- Bluetooth;
- Internet;
- cloud services.

Additional local interfaces may include:

- USB;
- Ethernet;
- CAN/CAN-FD;
- UART;
- I2C;
- SPI;
- PCIe;
- GPIO.

Selection depends on the final hardware architecture.

## 19. Storage

Novi needs reliable local storage for:

- operating system;
- models;
- databases;
- memories;
- embeddings;
- logs;
- sensor metadata;
- selected media;
- recovery artifacts.

Storage health and available capacity must be continuously monitored.

## 20. Hardware Self-Awareness

Novi must continuously maintain a hardware-health view.

```text
hardware
   ↓
telemetry
   ↓
health assessment
   ↓
fault detection
   ↓
capability state
   ↓
autonomy/cognition
```

Example:

```text
Camera 2 unavailable
        ↓
vision coverage degraded
        ↓
Novi knows the limitation
        ↓
autonomy adjusts behavior
```

The robot must not silently assume every sensor is healthy.

## 21. Sensor Calibration and Measurement Quality

Every sensor capable of generating physical-world facts should have a calibration identity and health state.

Where applicable:

```text
sensor ID
model
firmware
calibration version
time synchronized
measurement uncertainty
health state
```

This information becomes part of the provenance chain when measurements enter Novi's memory.

## 22. Sensor Fusion

Novi should combine complementary sensors before forming high-confidence physical-world state.

```text
RGB ─────┐
Depth ───┤
LiDAR ───┤
IMU ─────┤
Thermal ─┤──→ SENSOR FUSION → WORLD MODEL
Audio ───┤
Encoders ┘
```

No single modality should unnecessarily dominate when independent evidence is available.

## 23. Privacy Hardware

Cameras, microphones and biometric-capable sensors require explicit privacy states.

The design should consider:

- physical indicators;
- software-controlled privacy state;
- hardware-level microphone/camera disable paths where appropriate;
- clear user feedback;
- privacy-safe diagnostic behavior.

## 24. Hardware Degradation

Hardware failure should result in explicit capability degradation.

```text
FULL
  ↓
DEGRADED
  ↓
LIMITED
  ↓
SAFE MODE
```

The exact thresholds and transitions will be defined in the safety and diagnostics documents.

## 25. Design Philosophy

Novi should be designed as a **sensor-rich autonomous physical system**, not as an LLM placed inside a robot shell.

The hardware architecture therefore treats:

- perception;
- audio;
- motion;
- thermal awareness;
- spatial awareness;
- physical interaction;
- power;
- safety;
- diagnostics;
- environmental awareness;

as first-class systems that provide grounded information to cognition and autonomy.

## 26. Future Detailed Work

This high-level document deliberately does not select final parts.

Future engineering must determine:

- exact sensor models;
- camera count and placement;
- thermal-camera specification;
- LiDAR technology and range;
- microphone-array geometry;
- speaker placement;
- display interfaces and brightness;
- RGB LED topology;
- actuator architecture;
- battery chemistry and pack design;
- BMS;
- power rails;
- cooling system;
- connectors;
- wiring harness;
- PCB design;
- mechanical mounting;
- EMI/EMC;
- calibration;
- synchronization;
- thermal and power budgets;
- environmental ratings;
- safety validation;
- manufacturing and serviceability.

All final component selections must be validated against the real Novi prototype and Jetson AGX Orin 64GB workload rather than assumed from theoretical specifications alone.
