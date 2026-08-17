# 06 — Novi Neural Network Strategy

**Status:** P0 — proposed architecture

## Executive decision

Novi will use a **hybrid learned-and-deterministic architecture**. We will not build the first Novi version around one neural network, one LLM, one VLM, one VLA or one NVIDIA model, and we will not train a foundation model from scratch as an initial prerequisite.

```text
existing mature models
 → Novi adapters/contracts
 → Novi-specific benchmarks
 → targeted adaptation when justified
 → specialist models / skills
 → possible Novi-specific research
```

## Neural responsibilities

Neural models are appropriate for:

- object detection and segmentation;
- depth and pose estimation;
- tracking features;
- speech recognition/synthesis;
- embeddings and reranking;
- multimodal understanding;
- language/reasoning;
- prediction/world modeling;
- learned policies/VLA;
- imitation/RL skills;
- personalization where governed.

## Deterministic responsibilities

Deterministic systems own:

- emergency stop;
- motor/actuator limits;
- hard safety constraints;
- timing and watchdogs;
- exact geometry/transforms;
- state transactions;
- authorization;
- audit integrity;
- resource scheduling;
- artifact verification;
- protected recovery.

## Capability ownership

| Capability | Approach |
|---|---|
| Safety/control | deterministic |
| Detection/segmentation | neural + deterministic validation |
| Localization/mapping | hybrid |
| Speech | neural + deterministic stream control |
| Dialogue/reasoning | foundation model + grounding/governance |
| Memory | deterministic semantics + neural retrieval |
| World model | hybrid |
| Planning | hybrid |
| Navigation | robotics algorithms + learned perception/prediction |
| Manipulation | hybrid/VLA where justified |
| Personality | persistent state + model generation |
| Curiosity | hybrid |
| Learning | governed hybrid pipeline |

## Model tiers

```text
T0 deterministic/reactive
T1 tiny always-on learned models
T2 specialist perception/speech
T3 multimodal models
T4 reasoning models
T5 world/policy/VLA models
T6 offline learning/consolidation
```

Higher tiers should run less frequently and only when their additional capability justifies latency/resource cost.

## NVIDIA mapping

NVIDIA Isaac ROS provides CUDA-accelerated ROS 2 packages and reference workflows for perception, navigation and manipulation. NVIDIA documents capabilities including Visual SLAM, nvBlox, pose estimation and trajectory planning. citeturn0search0turn0search6

NVIDIA Cosmos is a candidate for physical-world reasoning, future-state prediction, world generation and action/policy research. NVIDIA describes Cosmos 3 as an omni-model with reasoning, world and action generation. citeturn0search12turn0search14

GR00T is a candidate robot foundation/VLA layer. Riva is a candidate speech layer. CUDA/TensorRT are deployment/acceleration layers. None becomes Novi's semantic authority.

## Model-selection rule

A model must be evaluated on task quality, grounding, robustness, uncertainty, latency, memory, power, thermal impact, concurrency, offline operation, failure behavior, reproducibility, license, provenance, security, hardware compatibility and rollback.

## Training progression

### Phase 1

Use existing mature models and build Novi's cognitive architecture.

### Phase 2

Fine-tune/post-train only when a measured benchmark gap justifies it.

### Phase 3

Learn task-specific skills using demonstrations, imitation learning, RL, policy distillation or VLA post-training.

### Phase 4

Train Novi-specific specialist models where sufficient data/evidence exists.

### Phase 5

Consider foundation-model research only as a separate research program.

## Continual learning

Runtime experience first updates governed memory/knowledge and evaluation datasets. Production model weights must not silently change because of one interaction.

```text
experience → evaluation signal → offline training → benchmark
→ safety/security review → controlled promotion → rollback available
```

## Neural boundary

A learned model can propose an interpretation, prediction, plan or action. It cannot directly bypass governance or control.

```text
model → structured proposal → validation → governance → safety → controller
```

## Acceptance

The strategy is complete only when each cognitive capability has an explicit decision: neural, deterministic or hybrid; candidate model class; benchmark; runtime constraints; failure behavior; and adoption gate.