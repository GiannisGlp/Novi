# 02 — Autonomy

**Status:** P0 — critical behavioral architecture workstream

## High-Level Description

The Autonomy subsystem defines Novi's **behavioral agency**: how Novi continuously decides what deserves behavioral attention, maintains goals, chooses whether to pursue them, manages tasks, requests capabilities, observes outcomes, recovers from failure, and continues operating without requiring a user prompt for every cycle.

Autonomy is not a second cognition engine, memory system, brain runtime, or safety authority.

The canonical separation is:

```text
02-novi-brain           → coordinates and executes the embodied runtime
03-cognition            → understands, reasons, predicts and represents current semantic state
04-memory-and-knowledge → remembers, retrieves and maintains durable knowledge
02-autonomy             → chooses and pursues goals and behavioral tasks
policy / safety         → permits, constrains or denies consequential actions
hardware / controllers  → executes physical control
```

> **Brain coordinates. Cognition understands. Memory remembers and knows. Autonomy chooses and pursues. Policy permits or denies. Hardware executes.**

The complete Autonomy boundary is defined in `16_AUTONOMY_ARCHITECTURE_BOUNDARY_AUDIT.md`.

## What Autonomy Owns

Autonomy owns:

- continuous behavioral-loop orchestration;
- behavioral attention decisions;
- goal creation, prioritization and lifecycle;
- goal conflict resolution;
- curiosity and information-seeking decisions;
- high-level behavioral planning;
- task sequencing and pursuit;
- interruption, cancellation and replanning;
- capability-request lifecycle;
- outcome-driven task management;
- autonomy state machine;
- resource-aware behavioral adaptation;
- controlled learning triggers;
- autonomy-specific behavioral audit and telemetry.

Autonomy does **not** own:

- semantic truth or the canonical World Model;
- semantic Situation Model interpretation;
- long-term memory or knowledge persistence;
- cognitive model selection;
- model execution/runtime implementation;
- raw perception/sensor drivers;
- motor control;
- final safety authorization;
- immutable safety rules.

## Relationship to Cognition

Cognition and Autonomy are adjacent but distinct:

```text
Cognition
  semantic interpretation
  world/situation understanding
  reasoning
  prediction
  candidate strategies/plans
          ↓
Autonomy
  goal selection
  behavioral commitment
  task lifecycle
  interruption/replanning
  outcome-based completion
          ↓
Policy / Safety
  permission / constraints
          ↓
Capability / Hardware
  execution
```

Cognition may propose a goal or plan. Autonomy decides whether and when to pursue it, subject to policy and available resources.

## Relationship to Memory

Autonomy requests context and may generate learning candidates. Memory owns persistence, retrieval, consolidation, provenance and durable knowledge.

```text
Autonomy:
  "This experience may be worth remembering."

Memory:
  "I decide whether/how it is admitted, stored, retrieved and retained."
```

## Relationship to Brain Runtime

Autonomy specifies behavioral runtime requirements. Brain/system architecture implements the underlying process lifecycle, scheduling, model execution, resource management, sensor pipelines and service infrastructure.

```text
Autonomy requirement:
  bounded planning latency + cancellation

Brain/runtime:
  scheduler + executor + timeout + cancellation primitives
```

Autonomy must not become a second runtime implementation.

## Relationship to Safety

Autonomy proposes and requests actions. Independent policy/safety remains authoritative.

```text
Autonomy
   ↓ request
Policy / Safety
   ↓ allow / constrain / deny
Capability Gateway
   ↓
Hardware / external system
```

Model confidence never overrides a safety or confirmation requirement.

## Detailed Description

### Foundation

- `00_HIGH_LEVEL_AUTONOMY.md` — scope, invariants, autonomy levels, priorities, silence, resource awareness, and cross-platform requirements.
- `01_CONTINUOUS_COGNITIVE_LOOP.md` — the continuous **autonomous behavioral** loop.
- `02_AUTONOMY_DATA_AND_EVENTS.md` — behavioral data vocabulary for observations, events, situations, goals, intentions, plans, actions, outcomes, and learning candidates.
- `03_ATTENTION_AND_SOCIAL_BEHAVIOR.md` — behavioral attention, interaction thresholds, social response decisions, non-interruption and personality integration.
- `04_GOALS_CURIOSITY_AND_LEARNING.md` — goals, prioritization, curiosity, investigation and controlled learning triggers.

### Decision and Execution

- `05_DECISION_AND_PLANNING.md` — autonomy context construction, behavioral planning, task commitment, validation, replanning and confirmation; Cognition remains the semantic reasoning authority.
- `06_ACTION_EXECUTION_AND_FEEDBACK.md` — capability-request lifecycle, execution monitoring, outcome verification, cancellation and recovery.
- `07_AUTONOMY_STATE_MACHINE.md` — deterministic autonomy states, guards, interruptions and recovery; distinct from Brain/runtime and safety state machines.
- `08_INTERNAL_STATE_AND_AFFECT.md` — transient behavioral state, attention, interaction mode, resource state and bounded affect; not the personality/self-history authority.
- `09_AUTONOMY_SAFETY_BOUNDARIES.md` — the autonomy-facing safety contract; canonical safety authority remains outside Autonomy.

### Runtime Infrastructure / Contracts

- `10_AUTONOMY_EVENT_BUS.md` — autonomy event contract, delivery requirements, replay and correlation; transport implementation may be owned by system/Brain infrastructure.
- `11_AUTONOMY_RUNTIME.md` — autonomy runtime requirements; system/Brain owns the implementation of process lifecycle, scheduling and model runtime.
- `12_AUTONOMY_TESTING.md` — behavioral unit, contract, scenario, simulation, HIL and endurance testing.
- `13_AUTONOMY_OBSERVABILITY_AND_AUDIT.md` — structured behavioral traces, metrics, privacy-aware audit and reproducibility.

### NVIDIA / Robotics Integration

- `14_AUTONOMY_NVIDIA_INTEGRATION.md` — how NVIDIA technologies fit behind Novi contracts, including JetPack, CUDA, TensorRT, Isaac ROS, Isaac Sim, DeepStream, Nemotron and Nav2.
- `15_AUTONOMY_IMPLEMENTATION_ROADMAP.md` — contracts → Mac runtime → reasoning → learning → simulation → Jetson → hardware → continuous evolution.
- `16_AUTONOMY_ARCHITECTURE_BOUNDARY_AUDIT.md` — **canonical ownership and separation audit**.

## NVIDIA-First, Not NVIDIA-Locked

Novi will actively use NVIDIA technology when NVIDIA provides an existing, mature solution that is appropriate for the requirement. NVIDIA components remain implementation choices behind Novi contracts; they do not become semantic authorities.

```text
Does NVIDIA provide a suitable component?
        ↓ yes
Does it materially improve the workload?
        ↓ yes
Is it supported and maintainable?
        ↓ yes
Use NVIDIA implementation behind a Novi contract.
```

If a non-NVIDIA component is objectively better for a specific workload, it may be used behind the same contract.

## Architectural Principles

1. **Continuous, not request-driven:** autonomy remains active when nobody is speaking to Novi.
2. **Behavior, not truth:** Autonomy acts on cognition's current understanding; it does not define truth itself.
3. **Attention before interaction:** detecting something does not imply speaking or acting.
4. **Memory is separate from reasoning and behavior:** Autonomy may request or propose memory operations; Memory owns persistence.
5. **Goals are explicit:** autonomous behavior is represented as inspectable goal/task state.
6. **Actions are capabilities:** Autonomy requests typed capabilities rather than touching hardware/storage directly.
7. **Safety is authoritative:** autonomy may propose, while policy/safety can deny, constrain, delay or require confirmation.
8. **Learning is controlled evolution:** autonomy can trigger learning/investigation; persistence and consolidation remain controlled by Memory/Knowledge.
9. **Uncertainty is first-class:** autonomy consumes confidence/provenance and must not manufacture certainty.
10. **Vendor-neutral contracts:** NVIDIA and other implementations remain behind contracts.
11. **Simulation first:** autonomy behavior must be testable on Mac and simulation before physical hardware.
12. **Everything consequential is observable:** behavioral decisions and actions have structured traces without storing private chain-of-thought.

## Relationship to Other Domains

```text
Perception / runtime
        ↓
Cognition → semantic state / reasoning / predictions
        ↓
Autonomy → attention / goals / tasks / behavior
        ↓
Policy / Safety
        ↓
Capabilities / Hardware
        ↓
Outcome
        ↓
Cognition + Memory + Autonomy update
```

Autonomy is the layer that turns Novi's understanding into **bounded ongoing behavior**.

## Implementation Status

This directory is a specification baseline. A document may be marked:

- `DESIGN`
- `IMPLEMENTATION READY`
- `IMPLEMENTED`
- `VALIDATED`
- `DEPRECATED`

A design document must not be interpreted as implemented behavior until corresponding code and tests exist.
