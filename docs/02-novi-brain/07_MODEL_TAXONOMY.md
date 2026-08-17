# 07 — Novi Model Taxonomy

**Status:** P0 — critical

This document classifies every learned-model family Novi may use. It does not select final model versions.

## L0 — Deterministic intelligence

Geometry, transforms, safety, control, constraints, scheduling, state transactions and hardware interfaces.

## L1 — Always-on learned models

Low-latency models for voice activity, lightweight event detection, object presence, tracking assistance and anomaly detection.

Requirements: low latency, bounded resource use, predictable failure and offline execution.

## L2 — Specialist perception models

### Vision

- detection;
- segmentation;
- depth;
- pose;
- tracking;
- re-identification where authorized;
- optical flow;
- scene classification;
- visual embeddings.

### Audio

- acoustic-event classification;
- speaker embeddings;
- diarization;
- sound-source localization;
- prosody/emotion proxies.

### Speech

- ASR;
- TTS;
- language identification;
- speech enhancement.

## L3 — Representation models

Embeddings and multimodal representations for semantic retrieval, entity matching, temporal association and world-state grounding.

Embeddings are retrieval representations, not truth.

## L4 — Multimodal foundation models

VLMs and audio/vision/language models for scene interpretation, social context, grounding, multimodal question answering and complex perception.

They produce evidence/interpretation proposals, not authoritative state.

## L5 — Language/reasoning models

LLMs/reasoners for dialogue, task decomposition, planning assistance, ambiguity resolution, tool selection and explanation.

They operate from grounded context and must produce structured outputs.

## L6 — Predictive/world models

Models that predict possible future states, trajectories, interactions or scenarios. NVIDIA Cosmos is a relevant candidate ecosystem; NVIDIA documents Cosmos 3 as supporting reasoning, world generation and action generation. citeturn0search12turn0search13

World-model output is always classified as prediction/simulation/counterfactual rather than observation.

## L7 — Embodied policy/VLA models

Models mapping language/state/perception to actions or action chunks. Candidate classes include VLA models, robot foundation models, imitation policies and learned controllers. NVIDIA GR00T is a candidate ecosystem.

Every policy must declare embodiment, sensors, action space, control rate, training distribution and known limitations.

## L8 — Learned skill models

Specialized policies for tasks such as approach, grasp, follow, inspect, interact or navigate. Skills must expose preconditions, effects, constraints, cancellation and failure semantics.

## L9 — Learning/adaptation models

Models used offline for fine-tuning, post-training, imitation, reinforcement learning, distillation, evaluation or personalization.

Production adaptation requires promotion gates and rollback.

## Capability matrix

| Model class | Primary output | Typical frequency | Authority |
|---|---|---:|---|
| L1 | fast evidence | continuous | none |
| L2 | structured perception | continuous/event | none |
| L3 | representations | on demand | none |
| L4 | multimodal interpretation | event/task | none |
| L5 | reasoning/proposal | task-dependent | none |
| L6 | possible futures | planning/evaluation | none |
| L7 | action/policy proposal | task-dependent | none |
| L8 | bounded skill execution proposal | task-dependent | none |
| L9 | candidate model artifacts | offline | none |

## Model metadata

Every candidate model must have model ID, version, source, license, digest, tokenizer/preprocessor, inputs, outputs, parameters/architecture, quantization, runtime, hardware target, benchmark results, limitations, safety classification and provenance.

## Selection principle

Use the **smallest validated model/capability that reliably solves the task**. Larger models are not automatically better for real-time embodiment.

## Non-neural boundary

Do not use neural models for emergency stop, hard actuator limits, safety authorization, artifact verification, audit integrity, deterministic geometry or watchdogs.

## Acceptance

Every model family must map to a Novi capability contract, benchmark, resource profile, failure mode and lifecycle policy before production adoption.