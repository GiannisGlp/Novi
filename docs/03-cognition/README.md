# 03 — Cognition

## High-Level Description

The Cognition subsystem defines how Novi turns observations, world state, memory, knowledge, identity, goals, personality, and context into internal representations that support understanding, prediction, reasoning, social interpretation, planning, and learning.

Cognition is the layer between **what Novi perceives** and **what Novi decides to do**. It is not synonymous with the LLM. Nemotron is a primary reasoning-model candidate; Cognition is the larger system that supplies structured context to models, validates their outputs, maintains authoritative state, and combines probabilistic AI with deterministic software.

## Detailed Description

This directory will specify:

- cognitive architecture and boundaries;
- world representation and situation models;
- entity, identity, and relationship reasoning;
- temporal and causal reasoning;
- multimodal fusion;
- working context and attention memory;
- reasoning-model orchestration;
- personality and social cognition interfaces;
- uncertainty, confidence, provenance, and contradiction handling;
- prediction and expectation;
- cognitive state and internal representations;
- learning and knowledge formation;
- cognition APIs and schemas;
- model-independent contracts;
- local/open-source solution selection;
- NVIDIA and non-NVIDIA acceleration options;
- simulation and test strategy.

## Planned Documents

- `00_HIGH_LEVEL_COGNITION.md` — scope, responsibilities, invariants, and cognitive architecture.
- `01_COGNITIVE_ARCHITECTURE.md` — components, boundaries, data flow, lifecycle, and dependencies.
- `02_WORLD_MODEL.md` — representation of people, places, objects, devices, activities, state, and environment.
- `03_SITUATION_MODEL.md` — current context, active situations, hypotheses, and state transitions.
- `04_ENTITY_IDENTITY_AND_RELATIONSHIPS.md` — entity resolution, person identity, relationship state, and trust.
- `05_TEMPORAL_AND_CAUSAL_REASONING.md` — time, sequence, causality, prediction, and event relationships.
- `06_MULTIMODAL_COGNITION.md` — fusion of vision, audio, speech, sensors, text, and other modalities.
- `07_WORKING_CONTEXT_AND_CONTEXT_PACKAGING.md` — what information is supplied to reasoning models and why.
- `08_REASONING_ENGINE.md` — deterministic reasoning, model reasoning, planning support, and verification.
- `09_NEMOTRON_INTEGRATION.md` — model contract, context interface, tool calling, structured output, fallback, and benchmarking.
- `10_PERSONALITY_AND_SOCIAL_COGNITION.md` — persistent traits, adaptive state, social interpretation, and response style.
- `11_PREDICTION_AND_EXPECTATION.md` — expected events, anomaly detection, prediction errors, and learning triggers.
- `12_UNCERTAINTY_PROVENANCE_AND_CONTRADICTIONS.md` — confidence, evidence, source quality, conflict resolution, and epistemic state.
- `13_COGNITIVE_STATE.md` — working state, attention context, goals, affect hypotheses, and resource awareness.
- `14_COGNITIVE_DATA_MODEL.md` — schemas and versioning for cognitive state and derived representations.
- `15_COGNITIVE_APIS_AND_CONTRACTS.md` — service interfaces and capability boundaries.
- `16_SOLUTION_SELECTION.md` — open-source/local-first evaluation and technology selection process.
- `17_NVIDIA_AND_ACCELERATION.md` — Jetson, CUDA, TensorRT, Isaac ROS and other acceleration candidates where useful.
- `18_COGNITION_TESTING.md` — unit, scenario, replay, adversarial, simulation, and hardware validation.
- `19_COGNITION_OBSERVABILITY.md` — metrics, decision metadata, provenance, debugging, and auditability.
- `20_COGNITION_IMPLEMENTATION_ROADMAP.md` — implementation order and migration gates.

## Core Principles

1. **Cognition is larger than an LLM.**
2. **Authoritative state lives outside the model context.**
3. **Probabilistic inference must remain distinguishable from verified fact.**
4. **Every important inference should retain evidence/provenance.**
5. **Contradictions are data, not errors to silently erase.**
6. **Context is retrieved and composed deliberately; databases are never blindly dumped into prompts.**
7. **The system must work locally and offline wherever practical.**
8. **Existing mature open-source solutions are preferred over reinventing equivalent components.**
9. **NVIDIA is a preferred option when it is objectively the best fit, not a mandatory dependency.**
10. **Cloud services are exceptional and must have an explicit justification.**
11. **Safety and authorization remain outside model-generated cognition.**
12. **Cognition must be testable independently from physical hardware.**

## Relationship to Autonomy

```text
Perception
    ↓
World Model / Situation Model
    ↓
Cognition
 ┌──┼───────────────┐
 │  │               │
Memory Knowledge Identity
 └──┼───────────────┘
    ↓
Context
    ↓
Reasoning
    ↓
Autonomy
    ↓
Planning / Action
```

Autonomy decides whether and when Novi should act. Cognition provides the understanding and reasoning substrate used by that decision process.
