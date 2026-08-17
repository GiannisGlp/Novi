# Novi — Pre-Implementation Readiness Audit

**Date:** 2026-08-17  
**Status:** Architecture/research consolidation  
**Purpose:** Establish exactly what exists, what is missing, what must be decided, and what must be documented before production implementation begins.

---

## 1. Audit conclusion

Novi has a strong conceptual architecture and unusually deep memory/knowledge documentation, but it is **not yet implementation-ready**.

The repository currently contains the North Star, development strategy, system architecture, autonomy, cognition, memory/knowledge, a high-level hardware architecture, and a technology reference. The recursive repository inventory confirms that the current hardware folder contains only the hardware README, the high-level hardware architecture, and GNSS/GPS documentation, while the README describes many additional hardware documents that do not yet exist. fileciteturn17file0L2-L2

The two Library research documents are valuable architecture inputs, not adoption decisions. They explicitly require requirements, benchmarks, security/license review, and ADRs before technologies are adopted. fileciteturn22file0L17-L21 fileciteturn23file0L195-L241

**Decision:** Do not begin production implementation yet. First close the documentation, technology-selection, hardware-engineering, validation, and environment-reproducibility gaps listed below.

---

# 2. What is already strong

## 2.1 North Star

`docs/00-strategy/NOVI_NORTH_STAR.md` now defines the long-term product goal and measurable cognitive properties.

## 2.2 Development strategy

`NOVI_DEVELOPMENT_STRATEGY_AND_IMPLEMENTATION_PLAN.md` defines the hybrid neural/structured approach, staged development, simulation-first strategy, hardware deferral, and technology-selection philosophy. fileciteturn15file0L2-L6

## 2.3 System architecture

The system architecture already establishes:

- continuous cognition;
- perception/world model/memory separation;
- attention, goals, policy and agent runtime;
- LLM as a reasoning component;
- action proposal and safety gateway;
- ROS 2 as robotics boundary;
- Mac → simulation → edge → physical runtime separation. fileciteturn12file0L2-L2

## 2.4 Cognitive architecture

The cognition domain is unusually detailed and includes world model, uncertainty, provenance, identity, relationships, temporal/causal reasoning, personality/affect, model selection, APIs/contracts, failure modes, testing, observability and architecture audit.

## 2.5 Memory/knowledge

The memory domain contains a consolidated architecture plus extensive archived source material covering taxonomy, lifecycle, provenance, retrieval, graph relationships, identity, temporal/spatial memory, causal modeling, schema evolution, privacy, governance, distributed state, recovery and evaluation.

The existence of both consolidated documents and archived source material is good, but the implementation baseline must clearly identify which documents are authoritative and which are historical/reference material.

## 2.6 Durable execution substrate

The 107 durable-state architecture is already a strong foundation: it defines immutable events, versioned state, provenance, snapshots, recovery semantics, idempotency, causality and offline operation. fileciteturn26file0L2-L2

## 2.7 NVIDIA research

The Library research covers the physical-AI lifecycle from perception through world models, planning, learned skills, simulation, optimized inference, deployment and validation. It also explicitly distinguishes NVIDIA capability claims, Novi architectural inferences and adoption decisions. fileciteturn22file0L23-L66 fileciteturn23file0L195-L241

---

# 3. Critical gaps discovered

## GAP-001 — Project identity cleanup

The repository README still describes Novi as the implementation repository for **Wheely**. That contradicts the current North Star and the explicit decision that Novi is a standalone project.

**Required:** remove all stale Wheely identity from canonical Novi documentation. Historical/reference relationships can be documented separately without making Wheely a project dependency.

**Priority:** P0.

---

## GAP-002 — Hardware folder is only partially realized

The hardware README describes documents `01` through `23`, covering compute, cameras, thermal sensing, LiDAR/depth, IMU, audio, displays, lighting, actuators, power, thermal management, environmental sensors, tactile sensing, safety, connectivity, storage, diagnostics, calibration, sensor fusion, mechanics, privacy and validation. Only the high-level hardware architecture and GNSS document are currently present in the repository inventory. fileciteturn19file0L2-L2 fileciteturn17file0L2-L2

**Required:** create the missing hardware engineering specifications or consolidate them into authoritative master documents with explicit traceability.

**Priority:** P0 before physical implementation; P1 before simulation-only implementation.

---

## GAP-003 — No complete hardware selection/BOM baseline

The high-level hardware architecture correctly avoids prematurely selecting parts, but it does not yet provide a complete engineering selection matrix.

The final hardware work still needs:

- exact component candidates;
- alternatives;
- electrical requirements;
- interfaces;
- power;
- thermal limits;
- mechanical constraints;
- calibration;
- synchronization;
- drivers/firmware;
- supply/replacement strategy;
- safety ratings;
- BOM;
- validation criteria.

The hardware README explicitly leaves these for later. fileciteturn19file0L2-L2

**Required:** add a hardware selection and BOM baseline before purchasing final robot hardware.

**Priority:** P0 for physical-design readiness.

---

## GAP-004 — Technology reference is incomplete as an implementation stack

`TECHNOLOGY_REFERENCE.md` is a good ecosystem catalog, but it omits several technologies required to make the system executable as a complete stack.

Missing or insufficiently specified categories include:

- ROS 2 distribution policy;
- Navigation2;
- ros2_control;
- Gazebo/modern Gazebo;
- SLAM/localization;
- TF2/robot state publication;
- sensor drivers and message standards;
- DDS/RMW selection;
- GStreamer/video transport;
- model serving alternatives such as vLLM/SGLang where relevant;
- speech recognition/TTS runtime candidates;
- data/storage technologies;
- vector/embedding retrieval;
- knowledge-graph implementation candidates;
- observability/OpenTelemetry;
- container/build/reproducibility strategy;
- CI/test infrastructure;
- secrets/credential management;
- software update/OTA strategy;
- firmware tooling;
- model registry/artifact storage;
- dataset/version management;
- simulation asset pipeline;
- CAD/URDF/USD conversion pipeline;
- time synchronization/PTP where high-rate sensors require it.

**Required:** consolidate these into `TECHNOLOGY_STACK_BASELINE.md` and keep `TECHNOLOGY_REFERENCE.md` as the ecosystem catalog.

**Priority:** P0.

---

## GAP-005 — ROS 2 distribution decision is unresolved

As of August 2026, ROS 2 Lyrical Luth is the newest LTS release and is supported until May 2031. citeturn3search2

However, current JetPack 7.2 for Jetson Orin is based on Ubuntu 24.04/L4T 39.2. citeturn5search3

Lyrical targets Ubuntu 26.04, while ROS 2 Jazzy supports Ubuntu 24.04 and remains supported until May 2029. citeturn3search1turn1search4

**Current recommendation:** baseline **ROS 2 Jazzy** for the initial cross-platform robot architecture unless a later JetPack/OS combination makes Lyrical the better validated target. This is an architectural compatibility decision, not a statement that Jazzy is the newest ROS release.

**Required ADR:** `ROS 2 distribution + Ubuntu + JetPack compatibility`.

**Priority:** P0.

---

## GAP-006 — Robotics control stack is underspecified

ROS 2 is named, but the complete control boundary should explicitly include `ros2_control`, controller types, hardware interfaces, update rates, command/state interfaces, lifecycle behavior, and deterministic control ownership.

`ros2_control` currently provides controller manager, hardware abstraction, joint limits, lifecycle and hardware-component interfaces suitable for this role. citeturn3search3turn3search5

**Required:** define `Novi → ROS 2 → ros2_control → hardware interface → motor controller` as the canonical physical control boundary.

**Priority:** P0 for hardware integration; P1 for simulation.

---

## GAP-007 — Navigation/localization stack is not yet selected

The architecture mentions navigation but does not establish the baseline stack.

**Current candidate baseline:** Navigation2 for planning/control/behavior, with SLAM/localization and robot-localization components selected through an evaluation record. Nav2 supports modern Gazebo integration and provides the standard navigation stack rather than requiring Novi to reinvent navigation. citeturn0search0turn0search7

**Required:** navigation architecture + mapping/localization decision record.

**Priority:** P1 until simulation; P0 before mobile hardware.

---

## GAP-008 — Perception pipeline needs an explicit backend boundary

The NVIDIA research correctly identifies perception as a pipeline rather than one model:

```text
sensor
 → calibration
 → synchronization
 → preprocessing
 → detection/segmentation/depth
 → tracking
 → fusion
 → world-state estimate
 → Novi evidence
 → memory/knowledge
```

fileciteturn22file0L931-L946

The repository still needs a concrete decision on when to use OpenCV, ROS image pipelines, Isaac ROS, DeepStream, Holoscan, or custom Python/C++ processing.

**Required:** perception backend decision matrix and canonical evidence schemas.

**Priority:** P0.

---

## GAP-009 — Model stack is not actually frozen

The README currently names Nemotron 3 Nano 30B-A3B as the primary candidate, but the research explicitly says model selection must be evaluated and benchmarked rather than assumed. The North Star also says the brain is the whole cognitive architecture, not a single model.

**Required:** create a model evaluation matrix covering LLM, VLM, speech, embeddings, reranker, perception and future VLA candidates.

Each candidate must have:

- exact model/version;
- license;
- parameter size;
- context;
- quantization options;
- local runtime;
- memory footprint;
- latency;
- quality benchmarks;
- tool-use performance;
- multimodal capability;
- Jetson feasibility;
- failure modes;
- privacy/security notes.

**Priority:** P0 for brain implementation.

---

## GAP-010 — Inference runtime architecture is incomplete

The current reference mentions TensorRT, TensorRT-LLM, Triton and alternatives, but does not define which runtime is used for which model class.

Current NVIDIA documentation shows TensorRT 11.2.1 as the current general release, but NVIDIA explicitly states that this release does not support JetPack; Jetson deployments remain on the TensorRT 10.x release supplied by their JetPack version. citeturn2search0turn2search4

Current JetPack 7.2 includes TensorRT 10.16.2. citeturn5search3

**Required:** inference architecture and artifact compatibility matrix.

**Priority:** P0.

---

## GAP-011 — Storage implementation is intentionally unspecified but now needs a selection study

The architecture defines semantics but not the actual local persistence implementation.

We need a comparison for:

- durable event log;
- relational/structured state;
- graph relationships;
- vector retrieval;
- object/media storage;
- caches;
- backups;
- local encryption;
- migration/recovery.

**Priority:** P0 for Stage 1/2 implementation.

---

## GAP-012 — Data and dataset architecture needs to become executable

The research defines provenance, real/synthetic flags, dataset versions, transformations and evaluation lineage, but the repository needs actual schemas, storage layout and lifecycle contracts. fileciteturn22file0L493-L505

**Required:** data architecture + dataset manifest + model/data registry specification.

**Priority:** P0.

---

## GAP-013 — Simulation representation and asset pipeline need completion

OpenUSD is correctly treated as a spatial/simulation representation rather than Novi's semantic memory. fileciteturn22file0L150-L163

Still missing:

- robot URDF/Xacro contract;
- USD representation strategy;
- sensor simulation models;
- environment asset pipeline;
- CAD → URDF/USD conversion;
- physics parameter source of truth;
- scenario schema;
- deterministic seed policy;
- fault injection;
- simulation provenance;
- SIL/HIL boundaries.

**Priority:** P0 before meaningful simulation work.

---

## GAP-014 — Safety engineering is not yet a complete physical safety case

The architecture has a strong logical safety gateway, but physical safety requires a separate safety case:

- hazard analysis;
- risk classification;
- emergency stop;
- motor-power isolation;
- watchdog architecture;
- safe-state definition;
- battery protection;
- over-current/over-temperature protection;
- speed/force limits;
- recovery after communication loss;
- human proximity behavior;
- fault injection;
- test evidence.

**Priority:** P0 before physical actuation.

---

## GAP-015 — Mechanical/electrical architecture is absent

The high-level hardware document deliberately stops before:

- chassis dimensions;
- center of gravity;
- wheel/drive geometry;
- actuator sizing;
- mounting interfaces;
- cable routing;
- connectors;
- PCB/MCU design;
- battery pack geometry;
- BMS;
- power rails;
- fusing;
- cooling;
- EMI/EMC;
- serviceability.

**Priority:** P0 before hardware purchase/build.

---

## GAP-016 — Time synchronization needs a dedicated specification

Multi-camera, LiDAR, IMU, audio and actuator fusion depends on time alignment.

The hardware architecture mentions synchronization, but no authoritative timing architecture currently defines:

- clock source;
- timestamp semantics;
- hardware vs software timestamps;
- PTP requirements;
- ROS time vs system time vs sensor time;
- simulated time;
- drift detection;
- synchronization failure behavior.

**Priority:** P0.

---

## GAP-017 — Deployment/reproducibility architecture is missing

The research explicitly recommends a deployment manifest containing hardware, firmware, JetPack, Jetson Linux, CUDA, TensorRT, ROS 2, Isaac ROS, containers, model versions, configuration and application version. fileciteturn22file1L1215-L1237

**Required:** deployment manifest, container strategy, version lock, artifact registry, rollback and update strategy.

**Priority:** P0.

---

## GAP-018 — Observability needs an implementation baseline

The architecture has observability documents, but the end-to-end metric contract should be consolidated:

```text
sensor timestamp
 → perception
 → evidence
 → memory
 → reasoning
 → planning
 → governance
 → action
 → outcome
```

with latency, throughput, queue time, CPU/GPU/RAM, power, thermal state, model latency and failure/recovery metrics. fileciteturn22file0L470-L488

**Priority:** P0.

---

## GAP-019 — Security threat model needs to cover the whole physical-AI supply chain

The research identifies model/data poisoning, sensor spoofing, adversarial perception, prompt injection, memory poisoning, malicious tools, compromised models, unauthorized updates, supply-chain attacks, credential theft, inference endpoint compromise and privacy leakage. fileciteturn22file0L435-L450

**Required:** consolidated threat model spanning software, models, data, hardware, network and physical access.

**Priority:** P0.

---

## GAP-020 — Validation program is not yet unified

Novi needs one validation hierarchy:

```text
UNIT
 ↓
INTEGRATION
 ↓
SYSTEM
 ↓
SIL
 ↓
HIL
 ↓
CONTROLLED PHYSICAL
 ↓
LONG-DURATION AUTONOMY
```

Model, memory, cognition, planning, navigation, safety, hardware and end-to-end tests must map into this hierarchy.

The research explicitly recommends SIL/HIL, simulation benchmarks, physical benchmarks and a safety test suite. fileciteturn23file0L99-L105

**Priority:** P0.

---

# 4. Technology consolidation decision

The technology stack should be divided into four classes.

## Class A — Core architecture candidates

- Python for cognitive orchestration.
- C++ for robotics/performance-sensitive components.
- ROS 2.
- ros2_control.
- Navigation2.
- OpenCV.
- PyTorch.
- ONNX/ONNX Runtime where useful.
- local model-serving interface.
- structured local persistence.
- vector retrieval as a secondary mechanism.
- graph/relationship representation.
- OpenTelemetry/observability.
- Docker/containerized reproducibility where compatible.

## Class B — NVIDIA acceleration candidates

- Jetson.
- JetPack.
- CUDA/CUDA-X.
- TensorRT.
- TensorRT-LLM.
- Isaac ROS.
- Isaac Sim.
- Isaac Lab.
- Holoscan.
- DeepStream.
- NeMo/Nemotron.
- TAO.
- OpenUSD/Omniverse.
- Cosmos.
- GR00T.

These remain behind capability adapters. The research explicitly recommends this architecture. fileciteturn22file0L55-L66

## Class C — Later research/scale candidates

- Triton.
- NeMo Agent Toolkit.
- OSMO.
- RAPIDS.
- cuOpt.
- Dynamo.
- NCCL/NIXL.
- advanced world models.
- learned dynamics.
- VLA/robot foundation models.

These should not be pulled into the first runtime simply because they exist.

## Class D — Explicitly not architectural authorities

- any LLM;
- any VLM/VLA;
- vector database;
- optimizer;
- simulator;
- GPU runtime;
- OpenUSD;
- cloud service;
- model-serving framework.

None of these may become the semantic source of truth, authorization authority, or safety authority.

---

# 5. Current technology baseline recommendation

For the documentation baseline, use:

```text
Language/runtime
  Python + C++

Robotics
  ROS 2 Jazzy baseline
  ros2_control
  Navigation2

Simulation
  Gazebo Harmonic for portable robotics simulation
  Isaac Sim as NVIDIA reference / advanced physical-AI simulation
  OpenUSD as spatial/simulation interchange

AI development
  PyTorch
  Hugging Face ecosystem
  ONNX where useful

Inference
  vendor-neutral NoviInference API
  CPU/reference backend
  GPU backend
  TensorRT/TensorRT-LLM adapter for NVIDIA

Perception
  OpenCV + ROS sensor pipeline
  Isaac ROS / DeepStream / Holoscan evaluated by workload

Memory/data
  durable event/state store
  structured knowledge graph
  vector retrieval index
  object/media store
  model/data registry

Observability
  OpenTelemetry-compatible telemetry

Deployment
  reproducible containers/artifacts
  versioned manifests

Safety
  deterministic policy + hardware safety controller
```

ROS 2 Jazzy is recommended as the initial stable cross-platform baseline because it supports Ubuntu 24.04 and remains supported through May 2029, while the newest LTS Lyrical targets Ubuntu 26.04 and current JetPack 7.2 uses Ubuntu 24.04. citeturn1search4turn3search2turn5search3

This decision should be revisited if the physical target OS changes.

---

# 6. Hardware baseline recommendation

Do not purchase the final robot BOM yet.

Define the required capabilities first:

```text
Compute
  → measured edge workload

Vision
  → multi-camera RGB + depth

Spatial
  → LiDAR + depth/proximity

Motion
  → IMU + encoder/proprioception

Audio
  → microphone array + speakers

Thermal
  → external thermal sensing + internal component telemetry

Physical interaction
  → bump/contact/load sensing

Output
  → face display + optional body display + status lighting

Power
  → battery + BMS + telemetry + protection

Safety
  → independent E-stop + power isolation + watchdogs

Connectivity
  → Ethernet/USB/CAN/UART/I2C/SPI as required; Wi-Fi/Bluetooth optional

Storage
  → high-endurance local NVMe-class storage where supported

Time
  → synchronized multi-sensor timestamp architecture
```

Exact components are a later engineering decision driven by measured workload and mechanical/electrical constraints.

---

# 7. Required documentation set before implementation

The repository should ultimately contain authoritative documents for:

### Strategy

- North Star
- development strategy
- pre-implementation readiness audit
- implementation master plan
- decision/ADR process

### Architecture

- high-level architecture
- detailed architecture
- component boundaries
- runtime profiles
- cross-cutting requirements
- durable state/event semantics
- concurrency/consistency
- recovery
- privacy
- observability
- resource governance

### Cognition/autonomy

- cognitive architecture
- world model
- evidence/provenance
- identity
- social model
- attention
- goals
- planning
- reasoning
- prediction
- personality/affect
- model routing
- failure modes
- testing
- scenarios

### Memory/knowledge

- taxonomy
- lifecycle/admission
- provenance
- retrieval/context
- knowledge graph
- identity resolution
- temporal/spatial memory
- causal model
- cross-modal memory
- skill verification
- schema evolution
- privacy/governance
- human oversight
- integration/reference model
- final traceability

### AI/model/data

- model architecture
- model selection matrix
- inference runtime
- model registry
- model provenance
- embeddings/reranking
- speech stack
- VLM/VLA strategy
- dataset architecture
- data governance
- training/fine-tuning
- synthetic-data strategy
- evaluation

### Robotics

- ROS 2 baseline
- ros2_control
- navigation
- localization
- mapping
- TF/time
- sensor interfaces
- actuator interfaces
- robot description
- capability/skill interface

### NVIDIA

- Jetson capability contract
- JetPack compatibility
- CUDA/TensorRT deployment
- Isaac ROS evaluation
- Isaac Sim integration
- Isaac Lab learning
- OpenUSD pipeline
- Cosmos evaluation
- GR00T/VLA evaluation
- Holoscan/DeepStream boundary

### Hardware

- compute
- cameras
- depth
- LiDAR
- IMU/encoders
- audio
- displays
- lighting
- actuators
- power/BMS
- thermal
- environment
- tactile/force
- safety
- connectivity
- storage
- diagnostics
- calibration/time sync
- sensor fusion
- mechanics
- privacy
- validation
- BOM/selection

### Operations

- deployment
- containers
- CI/CD
- model/data artifacts
- configuration
- secrets
- OTA/update
- rollback
- diagnostics
- backups
- disaster recovery

### Validation

- test strategy
- cognitive benchmark
- memory benchmark
- perception benchmark
- model benchmark
- planning benchmark
- navigation benchmark
- SIL
- HIL
- hardware safety validation
- sim-to-real
- long-duration autonomy
- release gates

---

# 8. Implementation-readiness gate

Production implementation should not begin until the following are true:

- [ ] Novi identity is clean and independent of Wheely.
- [ ] North Star is accepted.
- [ ] canonical architecture is reconciled with domain documents.
- [ ] canonical terminology is frozen.
- [ ] major contracts are defined.
- [ ] event/state semantics are defined.
- [ ] memory/world-model schemas are defined.
- [ ] evidence/provenance semantics are defined.
- [ ] storage technology selection is completed.
- [ ] model selection study is completed for initial cognitive models.
- [ ] inference runtime baseline is selected.
- [ ] speech stack is selected.
- [ ] perception backend boundaries are selected.
- [ ] ROS 2 distribution/OS baseline is selected.
- [ ] ros2_control boundary is defined.
- [ ] navigation/localization stack is selected.
- [ ] simulation interface is defined.
- [ ] robot description strategy is defined.
- [ ] dataset/model registry is defined.
- [ ] observability contract is defined.
- [ ] security threat model is approved.
- [ ] physical safety case is defined before physical actuation.
- [ ] hardware capability specification exists.
- [ ] hardware selection matrix exists.
- [ ] power/thermal/mechanical budgets exist before final hardware selection.
- [ ] sensor synchronization design exists.
- [ ] deployment/reproducibility manifest exists.
- [ ] SIL/HIL validation plan exists.
- [ ] initial cognitive benchmark exists.
- [ ] Stage 1 acceptance criteria are executable.

Until these gates are satisfied, Novi remains in **architecture/research preparation**.

---

# 9. The correct order from here

```text
AUDIT
  ↓
CONSOLIDATE
  ↓
FILL DOCUMENTATION GAPS
  ↓
DEFINE CONTRACTS
  ↓
SELECT TECHNOLOGIES
  ↓
BENCHMARK MODELS
  ↓
DEFINE HARDWARE CAPABILITY REQUIREMENTS
  ↓
DESIGN SIMULATION
  ↓
FREEZE P0 ARCHITECTURE
  ↓
ONLY THEN
  ↓
IMPLEMENT NOVI KERNEL
```

This preserves the project's explicit strategy: the robot body and Jetson are consequences of a validated cognitive architecture, not prerequisites for creating it.

---

# 10. Audit status

**Current readiness:** NOT READY FOR PRODUCTION IMPLEMENTATION.

**Reason:** architecture is strong, but the technology, hardware, robotics, simulation, deployment, safety and validation layers still contain unresolved decisions and missing authoritative documents.

**Next objective:** close P0 documentation and decision gaps, then freeze a pre-implementation baseline.
