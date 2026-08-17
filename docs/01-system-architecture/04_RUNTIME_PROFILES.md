# 04 — Runtime Profiles

**Status:** P0 runtime architecture specification

## Purpose

Novi must operate through common contracts across development, simulation, edge and physical deployment. Profiles define environment-specific implementations and constraints without changing semantic contracts.

## Profile A — Development Host

### Purpose

Primary software-development environment.

### Provides

- cognitive runtime;
- autonomy;
- world model;
- memory/knowledge;
- personality;
- attention;
- local camera/audio where available;
- reference model runtimes;
- UI;
- synthetic events;
- simulated hardware;
- unit/integration tests;
- local development storage.

### Does not represent

- Jetson GPU/thermal behavior;
- physical actuator latency;
- final sensor interfaces;
- final edge power envelope.

The host hardware is therefore a development target, not evidence of physical-runtime readiness.

## Profile B — Portable Robotics Simulation

### Purpose

Validate robotics interfaces and autonomous behavior against virtual sensors/actuators.

### Candidate stack

```text
Gazebo + ROS 2
      ↕
Novi robotics adapters
      ↕
Novi cognition/autonomy
```

### Required simulated capabilities

- camera;
- depth;
- LiDAR;
- IMU;
- audio events;
- robot pose;
- joints/encoders;
- battery/power state;
- navigation;
- people/objects;
- environmental changes;
- deterministic seeds;
- fault injection.

## Profile C — NVIDIA High-Fidelity Simulation

### Candidate

NVIDIA Isaac Sim.

NVIDIA's current documentation recommends ROS 2 Humble and Jazzy and provides an Ubuntu 24.04/Jazzy workflow. citeturn0search4

### Required validation

- ROS 2 topic/service/action interoperability;
- simulated sensor timing;
- calibration metadata;
- robot state;
- physics parameters;
- deterministic/reproducible scenarios where possible;
- synthetic-data provenance;
- fault injection;
- scenario/version manifests.

Isaac Sim is an advanced simulation candidate, not Novi's semantic world-model authority.

## Profile D — NVIDIA Edge

### Current candidate

Jetson AGX Orin family; exact production module remains subject to workload and hardware selection.

NVIDIA's current AGX Orin developer-kit documentation identifies JetPack 7.2 / L4T r39.2 as the latest JetPack release. citeturn1search1

### Reference software layers

```text
JetPack
 ↓
Ubuntu/L4T
 ↓
CUDA
 ↓
TensorRT / GPU runtime
 ↓
ROS 2 Jazzy
 ↓
Novi capability adapters
```

Additional NVIDIA components such as Isaac ROS and DeepStream are workload-specific.

DeepStream 9.1 supports Jetson Orin and uses JetPack 7.2/L4T r39.2 for its Jetson package. citeturn0search0turn0search1

### Purpose

Measure:

- actual inference latency;
- perception throughput;
- CPU/GPU/unified-memory behavior;
- sensor concurrency;
- storage throughput;
- power;
- thermal behavior;
- recovery;
- sustained operation.

## Profile E — Hardware-in-the-Loop

HIL combines real selected hardware interfaces with controlled simulation.

Examples:

```text
real compute + simulated sensors
real motor controller + simulated world
real sensors + simulated cognition
real safety controller + simulated faults
```

HIL is a promotion gate, not a final acceptance test.

## Profile F — Physical Robot

Physical deployment combines the validated edge runtime with:

- selected compute;
- sensors;
- actuators;
- motor/controller system;
- displays;
- audio;
- battery/BMS;
- power distribution;
- network interfaces;
- independent safety mechanisms.

Physical hardware must expose the same logical capability contracts used by simulation.

## Capability Matrix

| Capability | Development | Portable Sim | Isaac Sim | Edge | Physical |
|---|---|---|---|---|---|
| Autonomy | Yes | Yes | Yes | Yes | Yes |
| World model | Yes | Yes | Yes | Yes | Yes |
| Memory/knowledge | Yes | Yes | Yes | Yes | Yes |
| Personality | Yes | Yes | Yes | Yes | Yes |
| Camera | Host | Virtual | Virtual | Edge | Physical |
| Audio | Host | Virtual | Virtual/event | Edge | Physical |
| Navigation | Mock/limited | Yes | Yes | Yes | Yes |
| ROS 2 | Optional | Yes | Yes | Yes | Yes |
| Isaac ROS | Optional | Candidate | Candidate | Candidate | Candidate |
| TensorRT | Host-dependent | Host-dependent | Host-dependent | Candidate | Candidate |
| DeepStream | Optional | Optional | Optional | Workload-dependent | Workload-dependent |
| Motors | Mock | Virtual | Virtual | HIL | Physical |
| Safety hardware | Mock | Simulated | Simulated | HIL | Required |

"Candidate" means not automatically enabled; it requires workload validation and an ADR.

## Configuration

Profiles should be explicit, e.g.:

```text
NOVI_PROFILE=development
NOVI_PROFILE=simulation
NOVI_PROFILE=isaac-sim
NOVI_PROFILE=edge
NOVI_PROFILE=hil
NOVI_PROFILE=physical
```

Configuration must never change semantic contracts.

## Promotion Path

```text
Unit
 ↓
Integration
 ↓
Portable simulation
 ↓
High-fidelity simulation
 ↓
Edge software validation
 ↓
HIL
 ↓
Controlled physical
 ↓
Bounded autonomy
 ↓
Extended autonomy
```

A failed lower-stage gate blocks promotion.
