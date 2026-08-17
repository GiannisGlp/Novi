# Novi Brain Architecture

**Status:** P0 — critical architecture workstream  
**Owner:** `02-novi-brain`

This directory defines the **embodied brain runtime and integration layer** of Novi: perception pipelines, model execution, embodied state coordination, runtime orchestration, continuous execution, and protected interfaces to cognition, autonomy, policy and hardware.

**Important boundary:** this directory is **not** the canonical owner of semantic cognition, long-term memory/knowledge, autonomy policy, or safety authority. Those responsibilities live in their canonical domains.

## Canonical ownership rule

```text
02-novi-brain           → coordinates and executes the embodied brain
03-cognition            → understands, reasons, predicts and represents the current situation
04-memory-and-knowledge → remembers, retrieves and maintains long-term knowledge
02-autonomy             → chooses and pursues goals and behavioral tasks
policy / safety         → permits, constrains or denies consequential actions
hardware / controllers  → executes physical control
```

> **Brain coordinates. Cognition understands. Memory remembers and knows. Autonomy chooses and pursues. Policy permits or denies. Hardware executes.**

The complete boundary decision is recorded in `23_ARCHITECTURE_BOUNDARY_AND_OWNERSHIP_AUDIT.md`.

## Core runtime contract

```text
SENSE → PERCEIVE → INTERPRET → UPDATE STATE → ATTEND
→ REACT / THINK / WAIT → GOAL → PLAN / SKILL
→ PROPOSE ACTION → GOVERN / SAFETY → ACT
→ OBSERVE RESULT → LEARN / REMEMBER → CONTINUE
```

The loop is continuous and multi-rate. User prompts are only one source of stimuli. The behavioral semantics of the loop are owned by Autonomy/Cognition; Brain owns runtime execution and coordination.

## Brain responsibilities

The Brain directory owns or coordinates:

- brain lifecycle;
- cognitive-cycle execution;
- model runtime and execution placement/routing;
- perception runtime and sensor/model pipelines;
- embodied runtime state integration;
- synchronization and runtime health;
- interfaces to Cognition, Memory, Autonomy, Policy and Hardware;
- runtime-level degradation, fallback and resource coordination;
- speech/audio/vision execution infrastructure.

It does **not** create competing canonical versions of:

- the North Star;
- semantic World Model;
- Situation Model;
- temporal/causal reasoning;
- semantic spatial reasoning;
- long-term memory/knowledge;
- behavioral goal authority;
- safety authority;
- motor-control authority.

## Consolidation completed

The previous Brain semantic specifications have now been converted to explicit boundary/source documents:

```text
01_BRAIN_NORTH_STAR_AND_BEHAVIORAL_CONTRACT.md
02_COGNITIVE_ARCHITECTURE.md
05_COGNITIVE_CYCLE.md
18_WORLD_MODEL.md
19_SPATIAL_COGNITION.md
20_TEMPORAL_COGNITION.md
21_SITUATION_MODEL.md
22_SELF_MODEL.md
```

Their canonical information now lives in the correct owners:

```text
North Star
  → 00-strategy/NOVI_NORTH_STAR.md

World Model
  → 03-cognition/02_WORLD_MODEL.md

Temporal + causal reasoning
  → 03-cognition/08_TEMPORAL_AND_CAUSAL_REASONING.md

Situation Model
  → 03-cognition/01_COGNITIVE_ARCHITECTURE.md
  → 03-cognition/09_CONTEXT_ENGINE.md

Semantic Self Model
  → 03-cognition/01_COGNITIVE_ARCHITECTURE.md

Historical self/spatial/temporal memory
  → 04-memory-and-knowledge

Behavioral cognitive loop
  → 02-autonomy

Runtime execution of these capabilities
  → 02-novi-brain
```

The former full specifications remain available through Git history for provenance and recovery. They are no longer active semantic authorities.

**Do not create replacement semantic Brain documents for these concepts. Extend the canonical owner instead.**

## NVIDIA alignment

NVIDIA technologies are candidate implementation building blocks, not Novi semantic authorities. Relevant ecosystems include Isaac ROS, Isaac Sim, Isaac Lab, GR00T, Cosmos, Riva, CUDA/TensorRT and Jetson. Each adoption requires official-source validation, Novi-specific benchmarks and an ADR.

## Evidence standard

```text
Claim → authoritative source → version/platform → Novi requirement
→ benchmark/experiment → decision → ADR
```

For NVIDIA-specific claims, current NVIDIA documentation/research is primary vendor evidence. Independent research is required for broader claims.

## Completion rule

This workstream is complete only when the Brain runtime and embodied integration can be specified in implementation-ready detail, while every semantic responsibility has exactly one canonical owner and all cross-domain contracts are explicit and audited.
