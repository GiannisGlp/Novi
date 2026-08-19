# B2 — Model Selection and Neural Architecture

**Status:** DECISION BASELINE
**Date:** 2026-08-19
**Domain:** Novi Brain
**Stage:** B2 — Real Local Model Capability
**Decision:** Adopt a multi-model neural capability architecture; do not make one foundation model the Novi brain.

## 1. Executive decision

Novi will use a capability-first neural architecture with replaceable model adapters. The first real model integration is **NVIDIA Nemotron 3 Nano Omni 30B-A3B** as the multimodal perception/context model. **NVIDIA Cosmos Reason2 8B** is the preferred second model for physical/spatiotemporal reasoning. **NVIDIA Isaac GR00T N1.7** is reserved for a later learned robot-skill/policy stage rather than the core cognitive runtime.

Novi must not depend semantically on NVIDIA product names. Models are implementations behind the existing `ModelRuntime` / `novi.model-invocation` contract.

## 2. Why one giant model is rejected

Novi is an autonomous physical system. Perception, world-state bookkeeping, reasoning, planning, learned skills, control and safety have different latency, determinism, provenance and verification requirements. A single model cannot safely become the authority for all of them.

The neural architecture is therefore:

```text
Sensors
  ↓
Specialist perception + multimodal model
  ↓
Structured evidence
  ↓
Deterministic world state + memory
  ↓
Physical reasoning model
  ↓
Cognition / planning
  ↓
Learned skill or policy candidate
  ↓
Deterministic governance + safety
  ↓
Controller
  ↓
Actuators
```

A learned model can propose; it cannot authorize physical action.

## 3. Candidate model decisions

### 3.1 Nemotron 3 Nano Omni 30B-A3B — SELECTED FOR B2.2

Role: multimodal perception/context sub-agent.

Capabilities relevant to Novi:

- unified video, audio, image and text understanding;
- multimodal reasoning;
- hybrid Mamba + Transformer architecture;
- mixture-of-experts design with 30B total / 3B active parameters;
- spatiotemporal visual processing;
- efficient video sampling;
- open weights, datasets and recipes;
- local and NVIDIA-accelerated deployment options.

Rationale: it provides a strong multimodal foundation without forcing Novi to maintain separate vision/audio/language semantic pipelines at the first cognitive boundary. It is a capability provider, not the whole Brain.

### 3.2 Cosmos Reason2 8B — SELECTED AS B2 FOLLOW-ON

Role: physical/spatiotemporal reasoning and planning-support model.

Capabilities relevant to Novi:

- spatial and temporal reasoning;
- physical common sense;
- 2D/3D point localization and bounding boxes;
- long-context reasoning up to 256K input tokens;
- robotics/physical-AI specialization;
- customizable/post-trainable architecture.

The 8B model requires approximately 32 GB GPU memory according to current NVIDIA documentation. The 2B variant requires approximately 24 GB. Therefore the 8B model is a future workstation/edge benchmark target, not a requirement for the current Mac-only development environment.

### 3.3 GR00T N1.7 — RESERVED FOR LEARNED SKILLS

Role: embodied VLA / robot policy provider.

NVIDIA reports approximately 32K hours of real demonstration and 8K hours of simulated data, a Cosmos Reason2-2B VLM backbone, ONNX/TensorRT export and a 3B base checkpoint.

GR00T is highly relevant to Novi but is not the core Brain model because its primary value is learned robot behavior/policy. Novi must keep the boundary:

```text
GR00T / learned policy
       ↓
ActionProposal
       ↓
Governance
       ↓
Safety
       ↓
Controller
```

GR00T must not bypass Novi safety or authorization.

### 3.4 Cosmos 3 family — SIMULATION / WORLD MODEL TRACK

Cosmos 3 is reserved primarily for physical-AI world modeling, synthetic data, scenario generation and later world-action research. Cosmos 3 Edge is particularly interesting for future Jetson Thor deployment because NVIDIA describes it as a 4B model for on-device vision reasoning and robot policy deployment.

It is not required for the first real local model integration.

### 3.5 Nemotron 3 Super / Ultra — NOT INITIAL EDGE TARGETS

These models are valuable for high-end reasoning and experimentation, but their resource envelope is not justified for the first small-robot runtime. They may be used later for offline planning, research comparison, teacher-model workflows or cloud/workstation evaluation without becoming mandatory dependencies.

## 4. Target Novi neural stack

```text
                           NOVI BRAIN
                               │
                    ┌──────────┴──────────┐
                    │                     │
          Nemotron 3 Nano Omni       Specialist models
          multimodal context        detection/depth/audio
                    │                     │
                    └──────────┬──────────┘
                               │
                        Structured Evidence
                               │
                               ▼
                     World State + Memory
                               │
                               ▼
                       Cosmos Reason2
                     physical reasoning
                               │
                               ▼
                          Cognition
                               │
                         Autonomy/Plan
                               │
                    ┌──────────┴──────────┐
                    │                     │
              learned skill          classical plan
                 / GR00T             / optimizer
                    │                     │
                    └──────────┬──────────┘
                               │
                         ActionProposal
                               │
                         Safety/Governance
                               │
                           Controller
                               │
                            Actuators
```

## 5. Deterministic responsibilities

The following remain deterministic or governed by explicit non-neural algorithms:

- authoritative world-state bookkeeping;
- memory persistence and retrieval semantics;
- identity and provenance;
- resource budgets;
- authorization;
- safety policy;
- emergency stop;
- actuator limits;
- controller interface;
- final physical action authorization.

Neural outputs are evidence, inference, prediction or candidate action—not authoritative reality.

## 6. Epistemic status

Every learned output that influences the world model must carry explicit epistemic status where applicable:

- `OBSERVED`
- `INFERRED`
- `PREDICTED`
- `SIMULATED`
- `COUNTERFACTUAL`
- `HYPOTHESIZED`
- `VERIFIED`

Predictions must retain model/version/input/world-state/scenario/uncertainty/provenance metadata.

## 7. Hardware strategy

### Development target

Novi remains portable and Mac-first for development. B2.2 must therefore keep the semantic runtime independent of CUDA, TensorRT and NVIDIA-specific APIs.

### NVIDIA workstation / edge target

The future NVIDIA backend can use:

- CUDA/CUDA-X;
- TensorRT / TensorRT-LLM;
- TensorRT Edge-LLM;
- vLLM where appropriate;
- Jetson Thor;
- Isaac ROS;
- Triton where serving scale requires it.

NVIDIA currently documents Cosmos Reason2 support on Hopper/Blackwell systems and Jetson AGX Thor, with 24 GB minimum for Reason2-2B and 32 GB for Reason2-8B. NVIDIA also documents TensorRT Edge-LLM support for Cosmos Reason2 and Nemotron-family models on Jetson/DRIVE Thor.

## 8. B2.2 first-model decision

The first real model adapter will target **Nemotron 3 Nano Omni 30B-A3B**.

Required adapter properties:

1. model identity and immutable artifact digest;
2. explicit model/version metadata;
3. runtime/backend metadata;
4. input modality declaration;
5. output schema declaration;
6. bounded invocation deadline;
7. cancellation/failure semantics;
8. resource usage reporting;
9. provenance;
10. deterministic test fixture;
11. model-health reporting;
12. no direct actuator or safety authority.

The model must be loaded through the existing `ModelRuntime` rather than creating a special model-specific execution path.

## 9. Benchmark plan

Before accepting the model as B2 complete, measure:

### Capability

- image understanding;
- video understanding;
- audio understanding;
- multimodal grounding;
- structured output reliability;
- spatial reasoning support;
- robustness to ambiguous scenes.

### Runtime

- cold-start time;
- warm invocation latency;
- p50/p95/p99 latency;
- throughput;
- peak RAM/VRAM/unified memory;
- CPU/GPU utilization;
- sustained thermal behavior;
- concurrency;
- cancellation behavior;
- timeout behavior;
- failure recovery.

### Robotics relevance

- obstacle interpretation;
- object identity consistency;
- temporal consistency;
- human/robot interaction understanding;
- instruction grounding;
- uncertainty behavior;
- hallucination rate on controlled scenarios.

No model is accepted merely because it runs.

## 10. B2 model comparison gate

The initial selection is provisional until benchmarked against at least one credible alternative in the same capability class. The comparison should record model version, artifact digest, runtime, hardware, quantization, prompt/input configuration, dataset/scenario version and exact evaluation results.

## 11. NVIDIA integration policy

NVIDIA is the preferred implementation ecosystem for the physical-AI path, but not a semantic dependency.

The stable dependency chain is:

```text
Novi capability contract
        ↓
Novi model runtime
        ↓
backend adapter
        ↓
NVIDIA runtime/model
```

Alternative backends must remain possible.

## 12. Research sources and current-state validation

Primary current NVIDIA sources reviewed for this decision include:

- NVIDIA Nemotron model catalog and Nemotron 3 Nano Omni technical material;
- NVIDIA Cosmos Reason2 documentation and prerequisites;
- NVIDIA TensorRT Edge-LLM physical-AI/robotics material;
- NVIDIA Isaac GR00T N1.7 technical material;
- NVIDIA Jetson Thor and Cosmos 3 Edge announcements.

Existing Novi research in `NVIDIA_Novi_Comprehensive_Research.md` and `NVIDIA_Novi_Physical_AI_Research_2026.md` is treated as architecture input and has been reconciled with current NVIDIA product documentation.

## 13. What this decision does NOT mean

It does not mean:

- Novi becomes NVIDIA-dependent;
- Nemotron becomes Novi's entire brain;
- Cosmos becomes the authoritative world state;
- GR00T controls motors;
- a VLM can authorize action;
- simulation becomes real-world evidence;
- a model replaces deterministic control;
- a 30B model must run on the robot;
- the first selected model can never be replaced.

## 14. Roadmap

```text
B2.1  Model Runtime Contract                 COMPLETE
   ↓
B2.2  Nemotron 3 Nano Omni adapter           NEXT
   ↓
B2.3  Model lifecycle / health / resources
   ↓
B2.4  Provenance + evaluation harness
   ↓
B2.5  Cosmos Reason2 integration
   ↓
B2.6  Neural perception specialists
   ↓
B2.7  B2 integration gate
   ↓
B3    Real perception
   ↓
B4    First meaningful cognitive behavior
   ↓
Later: GR00T / learned skills / Isaac Lab / sim-to-real
```

## 15. Final architectural decision

Novi will pursue **capability-composed physical intelligence**, not a monolithic neural brain.

The initial neural intelligence stack is:

**Nemotron 3 Nano Omni → multimodal understanding**

**Cosmos Reason2 → physical reasoning**

**GR00T → future learned robot skills**

**Cosmos 3 → future world modeling/synthetic-data/simulation track**

with deterministic memory, world-state, planning, governance, safety and control surrounding the models.

This is the baseline for B2 implementation and must be revisited when NVIDIA or the broader model ecosystem changes materially.
