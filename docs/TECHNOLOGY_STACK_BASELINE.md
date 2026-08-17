# Novi — Consolidated Technology Stack Baseline

**Date:** 2026-08-17  
**Status:** Proposed P0 baseline / requires ADR approval before irreversible adoption  
**Purpose:** Consolidate the existing Technology Reference, Novi architecture, and NVIDIA research into one implementation-oriented technology map.

> This document answers **what technology exists, where it belongs, why it is considered, and when it should be used**. It does not make every candidate mandatory.

---

# 1. Technology philosophy

Novi follows:

1. capability-first interfaces;
2. local/offline-first operation;
3. open-source-first where practical;
4. mature existing solution before custom implementation;
5. benchmark before adoption;
6. NVIDIA-preferred where NVIDIA is objectively the best implementation;
7. vendor-neutral semantic/core architecture;
8. deterministic infrastructure for state, safety and authorization;
9. learned models for perception, reasoning, prediction and learned skills;
10. reproducible versions and provenance for every important external artifact.

The NVIDIA research explicitly recommends this capability-first architecture. fileciteturn22file0L55-L66

---

# 2. Recommended baseline stack

```text
NOVI SEMANTIC CORE
──────────────────────────────────────────────
Python cognitive runtime
C++ performance/robotics runtime
Typed contracts / schemas
Durable state + event log
World model
Memory / knowledge
Governance / safety
OpenTelemetry-compatible observability

ROBOTICS
──────────────────────────────────────────────
ROS 2 Jazzy
TF2
ros2_control
Navigation2
Gazebo Harmonic
Isaac ROS adapter

AI / MODELS
──────────────────────────────────────────────
PyTorch
Hugging Face ecosystem
ONNX / ONNX Runtime where useful
Local LLM/VLM service interface
Speech model interface
Embedding/reranking interface
Future VLA/skill interface

NVIDIA ACCELERATION
──────────────────────────────────────────────
CUDA / CUDA-X
TensorRT
TensorRT-LLM
JetPack
Jetson candidate
Isaac ROS
Isaac Sim
Isaac Lab
OpenUSD / Omniverse
Holoscan
DeepStream
NeMo / Nemotron
TAO
Cosmos
GR00T

DATA / OPERATIONS
──────────────────────────────────────────────
Structured local database
Vector index
Knowledge graph
Object/media store
Model registry
Dataset registry
Containers
CI/CD
Artifact manifests
Backups/recovery

PHYSICAL SYSTEM
──────────────────────────────────────────────
Sensors
Sensor synchronization
MCU/safety controller
Motor controller
Battery/BMS
Power distribution
Thermal system
Emergency stop
Diagnostics
```

---

# 3. Core programming languages

## Python — primary cognitive language

Use for:

- cognition;
- autonomy;
- memory orchestration;
- world model services;
- reasoning orchestration;
- model integration;
- evaluation;
- data pipelines;
- simulation orchestration;
- test harnesses.

Python should not be used for hard real-time motor control.

## C++ — robotics/performance language

Use for:

- ROS 2 nodes where performance matters;
- hardware interfaces;
- sensor processing;
- high-rate pipelines;
- real-time/control-adjacent components;
- custom acceleration where profiling proves it necessary.

## Shell/scripts

Use only for:

- setup;
- orchestration;
- reproducible environment management;
- deployment;
- CI utilities.

Scripts must not become the architecture.

---

# 4. ROS 2 baseline

## Recommended baseline: ROS 2 Jazzy

Jazzy supports Ubuntu 24.04 and is supported until May 2029. citeturn1search4

The newest ROS 2 LTS is Lyrical Luth, released in May 2026 and supported until May 2031. It targets Ubuntu 26.04. citeturn3search2turn3search1

Current JetPack 7.2 uses Ubuntu 24.04/L4T 39.2, so Jazzy is currently the safer common baseline for the Mac/Linux development and future Jetson target. citeturn5search3

This must become an ADR rather than an assumption.

## ROS responsibilities

ROS 2 owns:

- robotics message transport;
- nodes;
- services/actions;
- lifecycle;
- transforms;
- robot/sensor integration;
- simulation integration.

Novi cognition must not depend directly on vendor-specific ROS hardware drivers.

---

# 5. ros2_control

Use `ros2_control` as the primary candidate control abstraction.

It provides controller management, hardware abstraction, command/state interfaces, joint limits and lifecycle behavior. citeturn3search3turn3search5

Canonical boundary:

```text
Novi Action/Skill
      ↓
Capability Adapter
      ↓
ROS 2 Action/Command
      ↓
ros2_control
      ↓
Hardware Interface
      ↓
Motor Controller / MCU
      ↓
Actuator
```

Novi must never directly issue low-level motor commands from the LLM.

---

# 6. Navigation

## Navigation2

Use Navigation2 as the first navigation-stack candidate instead of building a navigation system from scratch.

Nav2 provides planning/control/behavior infrastructure and current documentation supports modern Gazebo integration. citeturn0search0turn0search7

Novi owns:

- navigation intent;
- goals;
- semantic destinations;
- high-level constraints;
- autonomy decisions.

Nav2 owns:

- navigation planning;
- path following;
- local control;
- recovery behaviors;
- navigation lifecycle.

---

# 7. Localization and mapping

Required capability families:

- TF2;
- wheel odometry;
- IMU fusion;
- visual odometry/SLAM;
- LiDAR SLAM/localization;
- map storage/versioning;
- localization confidence;
- map/world-model linkage.

Candidate technologies must be evaluated rather than hard-coded here.

Selection criteria:

- indoor performance;
- dynamic environments;
- sensor combinations;
- CPU/GPU cost;
- recovery after tracking loss;
- simulation compatibility;
- Jetson compatibility;
- provenance of maps.

---

# 8. Simulation

## Portable baseline

**Gazebo Harmonic + ROS 2** should be the portable robotics simulation baseline for ordinary navigation/control integration. Nav2 documents modern Gazebo Harmonic-or-newer integration for ROS 2 Jazzy and newer. citeturn0search7

## NVIDIA reference

**Isaac Sim** should be evaluated for:

- high-fidelity sensors;
- synthetic data;
- physical-AI workloads;
- digital twins;
- fault injection;
- advanced perception;
- learned policy evaluation.

## Robot learning

**Isaac Lab** is the primary NVIDIA candidate for:

- reinforcement learning;
- imitation learning;
- policy training;
- skill evaluation;
- sim-to-real.

The NVIDIA research specifically recommends simulation as development infrastructure rather than a demonstration layer. fileciteturn22file0L350-L377

---

# 9. OpenUSD

Use OpenUSD as:

- simulation scene representation;
- spatial interoperability layer;
- digital-twin representation;
- bridge between CAD/assets and simulation.

Do **not** use OpenUSD as Novi's semantic memory database.

Novi remains authoritative for:

- identity;
- evidence;
- provenance;
- beliefs;
- memory;
- permissions;
- causal semantics;
- privacy.

This boundary is explicitly supported by the NVIDIA research. fileciteturn22file0L150-L163

---

# 10. AI model development

## PyTorch

Primary development/training/research framework candidate.

Use for:

- vision;
- speech;
- multimodal models;
- embeddings;
- fine-tuning;
- learned policies;
- research experiments.

## Hugging Face

Use for:

- model discovery;
- model cards;
- datasets;
- tokenizers;
- pretrained models;
- evaluation assets.

Every model must be independently checked for license, provenance, quality and deployment feasibility.

## ONNX

Use as an interoperability option when moving models between frameworks/runtimes is beneficial.

---

# 11. Inference architecture

Novi must define a vendor-neutral interface:

```text
NoviInference
     ↓
Model Runtime Adapter
     ├── CPU/reference
     ├── ONNX Runtime
     ├── TensorRT
     ├── TensorRT-LLM
     ├── vLLM / SGLang where appropriate
     └── other validated backend
```

The interface must expose:

- model ID/version;
- capability;
- input schema;
- output schema;
- streaming;
- cancellation;
- timeout;
- resource requirements;
- health;
- provenance;
- safety constraints.

## TensorRT

TensorRT is the preferred NVIDIA inference-optimization candidate. Current general TensorRT documentation describes optimization across multiple precisions and model classes. citeturn2search0

Important compatibility rule: TensorRT 11.2.1 currently does **not** support JetPack; Jetson deployments must use the TensorRT 10.x release supported by their JetPack version. citeturn2search4

JetPack 7.2 currently ships TensorRT 10.16.2. citeturn5search3

This makes version locking and deployment manifests mandatory.

## TensorRT-LLM

Evaluate for optimized local LLM inference on NVIDIA hardware.

## Triton

Evaluate when multiple models, concurrency, standardized serving or model lifecycle complexity justifies a model server.

Do not introduce Triton into the first brain runtime solely because it is available.

---

# 12. Perception stack

Perception is a pipeline:

```text
Sensor
 ↓
Driver / acquisition
 ↓
Timestamp + calibration
 ↓
Preprocessing
 ↓
Neural/classical inference
 ↓
Tracking
 ↓
Sensor fusion
 ↓
World-state estimate
 ↓
Novi Evidence
```

## OpenCV

Use for:

- calibration;
- image transformations;
- geometric vision;
- preprocessing;
- quality checks;
- classical algorithms.

## Isaac ROS

Evaluate for accelerated perception, visual SLAM, depth, object detection/tracking and Jetson deployment.

## DeepStream

Evaluate for high-throughput multi-camera/video pipelines. Current DeepStream documentation supports Jetson Orin and JetPack 7.2. citeturn5search4

## Holoscan

Evaluate when sensor throughput/synchronization/latency requires a dedicated high-rate streaming architecture. Current Holoscan Sensor Bridge releases support AGX Orin with JetPack 7.2. citeturn4search7

Do not use all three by default. Choose boundaries based on measured workload.

---

# 13. Speech/audio

Novi requires two separate capabilities:

```text
Audio perception
  ↓
ASR / speaker / acoustic events
  ↓
Cognitive evidence

Cognitive response
  ↓
TTS
  ↓
Audio output
```

Candidate families:

- Whisper-family local ASR;
- NVIDIA Riva where justified;
- local TTS engines;
- microphone-array DSP;
- beamforming/AEC/noise suppression;
- speaker diarization/identification models.

The final choices require a benchmark on Novi's target microphones and acoustic environment.

---

# 14. LLM/VLM/VLA stack

Novi should support several model classes:

```text
LLM
VLM
embedding model
reranker
speech model
perception model
world model
VLA
learned dynamics
skill policy
```

The primary reasoning model remains a **candidate**, not an architectural dependency.

Current candidates should be evaluated using the same benchmark harness.

Evaluation dimensions:

- reasoning;
- grounding;
- tool use;
- structured output reliability;
- multimodal understanding;
- context length;
- latency;
- memory;
- quantization;
- local operation;
- failure modes;
- licensing.

---

# 15. World models

Cosmos and other world-model technologies are candidates for:

- physical prediction;
- future-state generation;
- synthetic data;
- scenario generation;
- policy evaluation.

They must not replace Novi's world model.

```text
Novi World Model
      ↕
world-model backend
      ↓
prediction
      ↓
PREDICTED state
```

Predicted state must never be recorded as an observed historical event.

---

# 16. Robot foundation/VLA models

GR00T and future VLA systems are candidate **skill/policy backends**.

Canonical boundary:

```text
VLA
 ↓
Action Proposal
 ↓
Validation
 ↓
Governance
 ↓
Safety
 ↓
Controller
```

GR00T is research/skill infrastructure, not Novi's cognitive authority.

---

# 17. Data and storage technology categories

The implementation must select technologies for five distinct storage classes:

```text
1. Durable event/state storage
2. Semantic knowledge/relationships
3. Vector retrieval/indexing
4. Media/object storage
5. Ephemeral caches
```

Do not collapse these into one database without a demonstrated reason.

Selection requirements:

- embedded/local operation;
- transactions;
- crash recovery;
- backup/export;
- schema evolution;
- encryption;
- Mac development;
- Jetson deployment path;
- offline operation;
- performance under long-lived workloads.

Candidate technologies should be benchmarked before adoption.

---

# 18. Observability

Use OpenTelemetry-compatible instrumentation for:

- traces;
- metrics;
- logs;
- model calls;
- tool calls;
- event processing;
- perception latency;
- planning latency;
- action latency;
- CPU/GPU/RAM;
- power/thermal state;
- sensor health;
- recovery.

Novi's audit model must remain richer than ordinary application telemetry.

---

# 19. Containers and reproducibility

Use containers where they improve reproducibility, especially for:

- model runtimes;
- ROS integration environments;
- simulation;
- GPU dependencies;
- CI;
- deployment.

Every deployable build must have a manifest containing:

```text
source commit
application version
OS
ROS version
GPU/runtime versions
model versions
model digests
container image digest
configuration digest
hardware target
```

The NVIDIA research explicitly recommends deployment manifests of this kind. fileciteturn22file1L1215-L1237

---

# 20. Security technology

Required capabilities:

- secure local storage;
- least-privilege service identities;
- signed artifacts;
- secret storage;
- secure boot where available;
- encrypted transport where required;
- authenticated tool calls;
- model integrity verification;
- update authorization;
- audit trails;
- physical-access assumptions.

Threats include model/data poisoning, sensor spoofing, prompt injection, memory poisoning, malicious tools, compromised models and unauthorized updates. fileciteturn22file0L435-L450

---

# 21. Model/data lifecycle

Use a governed lineage:

```text
RAW DATA
 ↓
PROVENANCE
 ↓
PRIVACY CLASSIFICATION
 ↓
CURATION
 ↓
DATASET VERSION
 ↓
TRAINING / FINE-TUNING
 ↓
EVALUATION
 ↓
MODEL VERSION
 ↓
OPTIMIZATION
 ↓
DEPLOYMENT ARTIFACT
 ↓
RUNTIME
 ↓
MONITORING
```

NeMo, NeMo Curator, TAO, PyTorch and other tooling are candidates behind this process.

Raw Novi memory must never silently become training data. fileciteturn22file1L1386-L1407

---

# 22. Later NVIDIA infrastructure

Only introduce these when measured requirements justify them:

- Triton at model-serving scale;
- OSMO for physical-AI workflow orchestration;
- RAPIDS for large evaluation/data workloads;
- cuOpt for constraint-heavy planning;
- Dynamo for distributed inference;
- NCCL/NIXL for multi-GPU/distributed inference.

The research explicitly classifies these as later-scale infrastructure rather than first-runtime requirements. fileciteturn22file0L531-L538

---

# 23. Technology adoption states

Every technology must have one of:

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

No technology becomes `ADOPTED` without an ADR/evaluation record.

---

# 24. Required evaluation record

For every major technology/model:

- requirement;
- candidates;
- exact versions;
- license;
- supported OS;
- supported hardware;
- offline capability;
- security;
- privacy;
- quality;
- latency P50/P95/P99;
- throughput;
- CPU;
- GPU;
- RAM/VRAM;
- power;
- thermal impact;
- startup time;
- failure/recovery behavior;
- maintenance status;
- integration complexity;
- fallback;
- decision;
- test date;
- benchmark artifacts.

The NVIDIA research specifically recommends these benchmark dimensions before selecting edge hardware. fileciteturn23file0L11-L27

---

# 25. Immediate P0 technology decisions

The following must be resolved before implementation:

1. ROS 2 distribution/Ubuntu baseline.
2. Event/state storage technology.
3. Knowledge-graph technology.
4. Vector retrieval technology.
5. Object/media storage.
6. Initial LLM.
7. Initial VLM.
8. ASR.
9. TTS.
10. Embedding/reranker.
11. Perception pipeline baseline.
12. Navigation/localization stack.
13. Simulation baseline.
14. Model-serving strategy.
15. Container strategy.
16. Observability implementation.
17. Model/data registry.
18. Security/secrets strategy.
19. CI/test environment.
20. Jetson capability contract, without yet purchasing the final hardware.

---

# 26. Explicit non-goals for the first implementation

Do not initially require:

- custom foundation-model pretraining;
- distributed inference;
- multi-agent robotics;
- fleet learning;
- advanced VLA deployment;
- complex world-model deployment;
- Dynamo;
- NCCL/NIXL;
- RAPIDS;
- cuOpt;
- full physical hardware;
- final mechanical BOM.

These remain future capabilities unless an early benchmark proves they are necessary.

---

# 27. Version policy

Technology facts are time-sensitive.

The current baseline was audited on **2026-08-17**.

Before an ADR is approved, verify:

- exact release;
- compatibility matrix;
- license;
- security advisories;
- supported hardware;
- supported OS;
- model card;
- API stability;
- benchmark results.

This is particularly important for NVIDIA because JetPack, CUDA, TensorRT and model ecosystems evolve rapidly. NVIDIA currently lists JetPack 7.2 / Jetson Linux 39.2 with Ubuntu 24.04, CUDA 13.2.1 and TensorRT 10.16.2 for Jetson Orin. citeturn5search3

---

# 28. Bottom line

Novi should not be implemented as a pile of NVIDIA products.

It should be implemented as:

```text
Novi semantic contracts
        ↓
Novi-owned cognitive architecture
        ↓
portable capability interfaces
        ↓
validated backend implementations
        ↓
NVIDIA acceleration where useful
        ↓
measured deployment
```

This preserves the North Star while giving Novi access to the strongest current physical-AI ecosystem without becoming dependent on any single vendor, model, simulator or runtime.
