# Novi Brain Architecture

**Status:** P0 — critical architecture workstream

This directory defines the complete Novi brain: perception, cognition, memory, world representation, attention, reasoning, planning, skills, interaction, learning, orchestration and protected execution.

Novi is not one neural network or one LLM. It is a hybrid embodied cognitive system composed of learned models, deterministic systems, persistent state and an orchestrator.

## North-star question

> What computational system must exist for Novi to continuously perceive, understand, remember, decide, act, interact, learn and adapt as one coherent embodied agent?

## Core loop

```text
SENSE → PERCEIVE → INTERPRET → UPDATE STATE → ATTEND
→ REACT / THINK / WAIT → GOAL → PLAN / SKILL
→ PROPOSE ACTION → GOVERN / SAFETY → ACT
→ OBSERVE RESULT → LEARN / REMEMBER → CONTINUE
```

The loop is continuous and multi-rate. User prompts are only one source of stimuli.

## NVIDIA alignment

NVIDIA technologies are candidate implementation building blocks, not Novi semantic authorities. Relevant ecosystems include Isaac ROS, Isaac Sim, Isaac Lab, GR00T, Cosmos, Riva, CUDA/TensorRT and Jetson. Each adoption requires official-source validation, Novi-specific benchmarks and an ADR.

NVIDIA documents Isaac ROS as CUDA-accelerated ROS 2 packages for perception, navigation and related robotics workloads. citeturn0search0

## Evidence standard

```text
Claim → authoritative source → version/platform → Novi requirement
→ benchmark/experiment → decision → ADR
```

For NVIDIA-specific claims, current NVIDIA documentation/research is primary vendor evidence. Independent research is required for broader claims.

## Completion rule

This workstream is complete only when we can specify in implementation-ready detail how Novi perceives, maintains state, remembers, attends, reasons, plans, learns, interacts, moves, routes models, handles failures, allocates resources, and remains continuously embodied and responsive.