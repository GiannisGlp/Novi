# Novi Technology Reference

**Status:** Living ecosystem/reference catalog  
**Last audited:** 2026-08-17  
**Authority:** Candidate/reference technologies only. Adoption requires an ADR and benchmark.

## Purpose

This document is the canonical catalog of technology ecosystems Novi may evaluate, integrate, wrap or use.

It is deliberately different from `TECHNOLOGY_STACK_BASELINE.md`:

- **Technology Reference:** what exists and what it can provide.
- **Technology Stack Baseline:** what Novi currently proposes to use and where.
- **ADR:** what Novi has actually adopted.

## Selection rule

```text
Novi requirement
      ↓
Mature existing solution?
      ↓
Open/local/offline?
      ↓
Compatible license/security?
      ↓
Meets quality/latency/memory/power?
      ↓
Integrates behind Novi contract?
      ↓
Benchmark
      ↓
ADR
      ↓
Adopt / Wrap / Defer / Reject
```

No vendor, model, database, simulator or runtime is a semantic authority merely because it appears in this document.

---

# 1. NVIDIA ecosystem

## Jetson / JetPack

**Role:** edge compute candidate.

Current reference: Jetson AGX Orin 64GB.

NVIDIA currently lists JetPack 7.2 / Jetson Linux 39.2 for Jetson Orin, with Ubuntu 24.04, CUDA 13.2.1 and TensorRT 10.16.2. citeturn5search3

**Novi status:** Reference / candidate. Final hardware remains workload-driven.

## CUDA / CUDA-X

GPU acceleration foundation.

**Use:** accelerated inference, perception, simulation, data processing.

**Rule:** CUDA stays below Novi capability interfaces.

## TensorRT

Inference optimization/runtime for NVIDIA GPUs.

Current general TensorRT release is 11.2.1, but NVIDIA documents that TensorRT 11.2.1 does not support JetPack; Jetson deployments must use the TensorRT 10.x version supplied by the selected JetPack release. citeturn2search0turn2search4

**Use:** optimized deployment after model selection and benchmarking.

## TensorRT-LLM

LLM inference optimization.

**Use:** evaluate for local NVIDIA LLM deployment.

## Isaac ROS

CUDA-accelerated ROS 2 packages for perception, localization, mapping, navigation and related robotics workloads.

**Use:** perception/robotics acceleration behind ROS/Novi contracts.

## Isaac Sim

High-fidelity robotics simulation, sensors, synthetic data and validation.

**Use:** advanced simulation/SIL/synthetic-data workloads.

## Isaac Lab

Robot-learning/simulation framework.

**Use:** RL, imitation learning, policy training, evaluation, sim-to-real.

## GR00T

Embodied/robot foundation-model and VLA research ecosystem.

**Use:** future learned skills/policies; never direct authorization.

## Cosmos

Physical-AI/world-model ecosystem.

**Use:** prediction, physical reasoning, scenario generation, synthetic data, policy evaluation.

**Rule:** prediction remains distinct from observed history.

## OpenUSD / Omniverse

3D world/spatial interoperability and simulation representation.

**Use:** robot/environment assets, digital twins, simulation scenes.

**Rule:** not Novi's semantic memory database.

## NuRec

Neural reconstruction/3D Gaussian-splatting ecosystem.

**Use:** real-world capture → reconstructed scene → simulation/spatial reasoning.

## Holoscan

High-rate multimodal sensor processing.

**Use:** evaluate when sensor throughput/synchronization/latency justifies it.

Current Holoscan Sensor Bridge 2.7 supports AGX Orin with JetPack 7.2. citeturn4search7

## DeepStream / Metropolis

High-throughput video analytics and multi-camera pipelines.

Current DeepStream documentation supports Jetson Orin and JetPack 7.2. citeturn5search4

## NeMo / Nemotron

Model training, customization, evaluation, deployment and reasoning-model ecosystem.

**Use:** candidate local LLM/VLM/reasoning models and later customization.

## NeMo Agent Toolkit

Agent workflow profiling, evaluation, optimization and tool integration.

**Use:** later agent evaluation/optimization; not semantic authority.

## NeMo Curator

Data curation, filtering and dataset preparation.

**Use:** future training-data pipelines.

## TAO

Vision/VLM post-training and customization.

**Use:** domain-specific perception models when general models are insufficient.

## OSMO

Physical-AI workflow orchestration across simulation/training/evaluation infrastructure.

**Use:** later development infrastructure; not robot runtime.

## RAPIDS

GPU data and graph analytics.

**Use:** later large-scale evaluation/data workloads.

## cuOpt

Constrained optimization and routing.

**Use:** later planning/optimization backend.

## Dynamo / NCCL / NIXL

Distributed inference and GPU communication infrastructure.

**Use:** later scale only; not first Novi runtime.

## PhysX / Warp / Newton

Physics/simulation technologies.

**Use:** simulation/robot-learning workloads selected by simulator requirements.

---

# 2. ROS 2 ecosystem

## ROS 2

Robotics middleware.

### Current distribution candidates

- **Jazzy Jalisco:** LTS, Ubuntu 24.04, supported until May 2029. citeturn1search4
- **Kilted Kaiju:** non-LTS, Ubuntu 24.04, support through December 2026. citeturn1search0turn1search2
- **Lyrical Luth:** newest LTS, Ubuntu 26.04, supported until May 2031. citeturn3search2turn3search1

**Novi current baseline candidate:** Jazzy, because the current JetPack 7.2 target is Ubuntu 24.04. Re-evaluate if the edge OS changes.

## ros2_control

Real-time robot-control framework with controller manager, hardware abstraction, lifecycle and command/state interfaces. citeturn3search3turn3search5

**Novi role:** physical actuator boundary.

## Navigation2

Navigation planning/control/behavior stack.

**Novi role:** high-level navigation intent; Nav2 performs navigation execution.

Nav2 supports modern Gazebo integration for Jazzy and newer. citeturn0search0turn0search7

## TF2 / robot_state_publisher

Transforms and robot state representation.

**Novi role:** physical/simulation coordinate-frame infrastructure.

## rosbag2

ROS data recording/playback.

**Novi role:** transport-level recording and replay; not semantic memory.

## DDS / RMW

Candidate middleware implementations:

- Fast DDS;
- Cyclone DDS;
- Zenoh RMW;
- other ROS-supported RMWs.

Selection should be benchmarked against latency, reliability, discovery behavior and offline operation.

---

# 3. Simulation

## Gazebo Harmonic

Portable robotics simulation baseline.

**Use:** ROS 2 integration, navigation, control, sensor simulation.

## Isaac Sim

NVIDIA advanced simulation candidate.

**Use:** high-fidelity physical-AI simulation, synthetic data, digital twins, advanced sensors and policy validation.

## OpenUSD

Scene representation/interchange.

## Physics engines

Candidate families:

- PhysX;
- Newton;
- other simulator-native physics engines.

The simulator and physics engine must be selected based on the target workload.

---

# 4. AI/ML ecosystem

## PyTorch

Primary deep-learning development candidate.

## TensorFlow / TFLite

Alternative ML/edge ecosystem when an existing solution is materially better.

## Hugging Face

Model/dataset ecosystem.

Every model must be independently reviewed for license, provenance and suitability.

## ONNX

Model interchange format.

## ONNX Runtime

Portable inference runtime/fallback candidate.

## vLLM / SGLang

Candidate local LLM serving runtimes for workstation/server-class environments.

They must remain behind `NoviInference` and are not assumed suitable for Jetson deployment.

---

# 5. Computer vision

## OpenCV

Classical vision, calibration, image processing, geometry, tracking and preprocessing.

## Specialized neural perception

Candidate classes:

- object detection;
- segmentation;
- depth;
- pose;
- optical flow;
- tracking;
- re-identification;
- visual embeddings;
- VLMs.

Exact model selection belongs in the model evaluation matrix.

---

# 6. Speech/audio

Candidate technologies:

- Whisper-family ASR;
- NVIDIA Riva;
- local TTS engines;
- microphone-array DSP;
- beamforming;
- acoustic echo cancellation;
- noise suppression;
- VAD;
- diarization;
- speaker identification;
- acoustic event detection.

All speech components must expose structured outputs and provenance rather than directly modifying semantic memory.

---

# 7. Data/storage ecosystem

Novi needs separate technology categories for:

1. durable event/state storage;
2. relational/structured state;
3. knowledge graph;
4. vector retrieval/index;
5. media/object storage;
6. caches;
7. backup/archive.

Candidate families to evaluate include:

- embedded SQL/relational databases;
- PostgreSQL-class relational systems;
- graph databases or relational graph representations;
- pgvector-class vector indexing;
- local object stores/filesystems;
- content-addressed artifact storage.

**Selection rule:** no database becomes semantic authority merely because it is convenient.

---

# 8. Data/model lifecycle

Required technology capabilities:

- dataset versioning;
- model registry;
- artifact registry;
- content hashing;
- provenance;
- evaluation datasets;
- model cards;
- license tracking;
- deployment manifests;
- rollback.

Candidate ecosystems include:

- Git/GitHub for source;
- DVC/compatible dataset versioning where useful;
- MLflow/model-registry-class systems where justified;
- object storage/artifact repositories;
- NVIDIA NeMo/TAO tooling for later model lifecycle work.

The final choice must remain compatible with local/offline development.

---

# 9. Observability

Candidate stack:

- OpenTelemetry;
- Prometheus-compatible metrics;
- structured logs;
- trace storage;
- Grafana-class visualization.

Novi's audit records remain semantically richer than ordinary telemetry.

---

# 10. Build/deployment

Candidate technologies:

- Docker/OCI containers;
- Dev Containers;
- CMake/colcon for ROS/C++;
- Python virtual environments/uv-class tooling;
- GitHub Actions;
- reproducible lockfiles;
- signed artifacts;
- SBOM generation;
- OTA/update tooling.

The final deployment strategy must include rollback and recovery.

---

# 11. Security

Required capability families:

- secure boot;
- hardware-backed identity where available;
- key storage;
- secret management;
- signed models/artifacts;
- access control;
- encrypted storage;
- encrypted transport;
- update authorization;
- audit.

Threats include:

- model poisoning;
- sensor spoofing;
- prompt injection;
- memory poisoning;
- malicious tools;
- compromised models;
- unauthorized updates;
- supply-chain compromise;
- credential theft;
- privacy leakage.

---

# 12. Hardware ecosystem categories

The hardware architecture must evaluate:

- edge compute;
- NVMe storage;
- RGB cameras;
- depth cameras;
- LiDAR;
- IMU;
- encoders;
- microphone arrays;
- speakers;
- thermal cameras;
- environmental sensors;
- tactile/contact sensors;
- displays;
- RGB lighting;
- motor/actuator systems;
- motor controllers;
- MCU/safety controller;
- battery;
- BMS;
- power converters;
- fuses/protection;
- Ethernet/USB/CAN/UART/I2C/SPI;
- cooling;
- mechanical chassis;
- connectors/cabling.

Exact part selection is defined by `docs/05-hardware/26_HARDWARE_SELECTION_AND_BOM_BASELINE.md` and later BOM records.

---

# 13. Technology status vocabulary

Every entry should eventually have one of:

```text
REFERENCE
CANDIDATE
EVALUATING
ADOPTED
WRAPPED
DEFERRED
REJECTED
DEPRECATED
```

No `ADOPTED` decision is valid without an evaluation record and ADR where the decision is architecturally significant.

---

# 14. Non-negotiable boundaries

```text
LLM/VLM/VLA
   ≠ authorization

Vector retrieval
   ≠ truth

World-model prediction
   ≠ observation

Simulation
   ≠ historical reality

GPU memory
   ≠ semantic memory

KV cache
   ≠ long-term memory

OpenUSD
   ≠ Novi knowledge graph

Optimizer
   ≠ authorization

NVIDIA product
   ≠ Novi architecture
```

These boundaries come directly from the current Novi architecture and NVIDIA research. fileciteturn22file0L403-L418 fileciteturn22file0L435-L440

---

# 15. Current 2026 reference notes

- ROS 2 Lyrical is the newest LTS, but the current JetPack 7.2 Orin stack is Ubuntu 24.04; therefore Novi currently favors Jazzy for the shared robot baseline. citeturn3search2turn5search3
- JetPack 7.2 supports Jetson Orin and includes CUDA 13.2.1 and TensorRT 10.16.2. citeturn5search3
- General TensorRT 11.2.1 is not currently the JetPack runtime; Jetson must use the TensorRT 10.x line supported by its JetPack. citeturn2search4
- DeepStream 9.1 supports Jetson Orin and JetPack 7.2. citeturn5search4
- Nav2's modern Gazebo guidance targets Gazebo Harmonic or newer with ROS 2 Jazzy or newer. citeturn0search7

All version information must be revalidated before final ADR approval.
