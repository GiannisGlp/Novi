# 04 — Runtime Profiles

## Purpose

Novi must run through a common set of contracts across development, simulation, edge deployment, and physical hardware. This document defines the expected runtime profiles.

## Profile A — Mac Development

### Purpose

Primary software-development environment using the user's MacBook Pro M3 Pro 36GB.

### Available

- application runtime;
- autonomy engine;
- world model;
- knowledge base;
- memory;
- personality;
- attention;
- local camera;
- microphone/audio;
- local model runtimes where supported;
- web/control UI;
- synthetic events;
- simulated hardware;
- unit/integration tests;
- local SQLite and files.

### Not representative of

- CUDA/TensorRT performance;
- Jetson thermals;
- Jetson memory behavior;
- physical robotics latency;
- Jetson camera/GPIO interfaces.

## Profile B — Simulation

### Purpose

Run the same high-level software against virtual sensors and actuators.

### Reference stack

```text
Isaac Sim
  ↕
ROS 2
  ↕
Novi adapters
  ↕
Autonomy/Cognition
```

### Simulation should provide

- virtual camera;
- depth data;
- LiDAR;
- IMU;
- microphone/audio events;
- robot pose;
- doors;
- people;
- objects;
- obstacles;
- battery state;
- navigation;
- controllable fault injection.

## Profile C — Jetson Edge

### Target

NVIDIA Jetson AGX Orin 64GB.

### Reference NVIDIA stack

- JetPack;
- CUDA;
- TensorRT;
- Isaac ROS;
- ROS 2;
- NVIDIA-supported inference/runtime tooling where validated.

### Purpose

Validate actual edge inference, resource usage, perception throughput, audio/vision concurrency, and sustained operation.

## Profile D — Physical Robot

### Hardware

- Jetson AGX Orin 64GB;
- cameras;
- microphone array;
- speakers;
- display;
- head pan/tilt mechanism;
- wheel/motor controllers;
- IMU;
- optional LiDAR/depth sensing;
- environmental sensors;
- battery and power management;
- physical emergency stop.

### Requirements

Physical deployment must add no new cognitive behavior merely because hardware is real. It should expose the same logical capabilities used by simulation.

## Capability Matrix

| Capability | Mac | Simulation | Jetson | Physical |
|---|---:|---:|---:|---:|
| Autonomy loop | Yes | Yes | Yes | Yes |
| World model | Yes | Yes | Yes | Yes |
| Knowledge/memory | Yes | Yes | Yes | Yes |
| Personality | Yes | Yes | Yes | Yes |
| Camera | Mac camera | Simulated | Jetson camera | Physical |
| Audio | Mac audio | Simulated | Jetson audio | Physical |
| Navigation | Simulated | Yes | Yes | Yes |
| ROS 2 | Optional/dev | Yes | Yes | Yes |
| Isaac ROS | No/limited | Yes | Yes | Yes |
| TensorRT | No | GPU host dependent | Yes | Yes |
| Jetson performance | No | No | Yes | Yes |
| Motor control | Simulated | Simulated | HIL/driver | Physical |
| Safety hardware | Simulated | Simulated | Software validation | Required |

## Configuration

Runtime behavior should be selected by explicit profile configuration, for example:

```text
NOVI_PROFILE=mac
NOVI_PROFILE=simulation
NOVI_PROFILE=jetson
NOVI_PROFILE=physical
```

Configuration must not alter architectural contracts.

## Promotion Path

```text
Mac unit tests
   ↓
Mac integration tests
   ↓
Simulation tests
   ↓
Jetson software tests
   ↓
Hardware-in-loop
   ↓
Physical controlled tests
   ↓
Autonomous validation
```

A failed lower stage blocks promotion to the next stage.
