# 01 — System Architecture

## Purpose

This folder defines the authoritative system-level architecture for Novi/Wheely. It establishes the boundaries, responsibilities, dependencies, runtime environments, architectural principles, and non-negotiable constraints that every other domain must follow.

This is a **high-level architecture domain**. It deliberately does not contain the complete implementation specification for every subsystem. Detailed subsystem behavior belongs in the corresponding domain folders.

## What This Domain Defines

- What Novi is and is not.
- The autonomous cognitive-loop architecture.
- Major subsystem boundaries.
- Dependency direction.
- The relationship between cognition, perception, models, memory, robotics, and safety.
- Mac, simulation, Jetson, and physical-runtime boundaries.
- The distinction between adaptive intelligence and protected system infrastructure.
- Cross-cutting data, event, observability, and audit principles.
- Architectural requirements that downstream domains must satisfy.

## Core Architecture

```text
                         NOVI / WHEELY
                              │
                   ┌──────────▼──────────┐
                   │   Autonomous Core   │
                   └──────────┬──────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
  Perception             World Model             Memory
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              ▼
                         Attention
                              │
                         Goal Manager
                              │
                         Policy Engine
                              │
                         Agent Runtime
                              │
                         Nemotron LLM
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
               Tools       Knowledge    Planning
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                        Action Proposal
                              │
                         Safety Gateway
                              │
                             ROS 2
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
             Motors         Head          IoT
```

## Continuous Cognitive Loop

Novi is a continuously operating system. User messages are one source of events, not the trigger for the entire system.

```text
PERCEIVE
  → interpret observations
  → update world state
  → retrieve relevant memory
  → evaluate attention
  → update goals
  → decide whether action/reasoning is required
  → reason and plan
  → apply policy and safety constraints
  → act through approved capabilities
  → observe consequences
  → record experience
  → learn/update allowed state
  → repeat
```

## Architectural Layers

### Layer 1 — Physical and platform layer

Sensors, actuators, Jetson, cameras, microphones, speakers, display, motors, battery, networking, and other hardware.

### Layer 2 — Robotics middleware

ROS 2, Isaac ROS, navigation, sensor pipelines, hardware drivers, and device abstractions.

### Layer 3 — Perception

Vision, audio, speech recognition, face/voice identity, object detection, gesture/body-expression analysis, environmental sensing, and multimodal event generation.

### Layer 4 — Cognitive state

World model, people, places, objects, relationships, temporal state, spatial state, current situation, and active context.

### Layer 5 — Memory and knowledge

Episodic memory, semantic knowledge, spatial memory, procedural knowledge, embeddings, graph/relational data, provenance, verification, and retrieval.

### Layer 6 — Autonomy

Attention, curiosity, goals, internal state, prioritization, policy, planning, and continuous decision making.

### Layer 7 — Reasoning and agent runtime

Nemotron as the primary general-purpose reasoning candidate, tool calling, structured outputs, context construction, planning, and response generation.

### Layer 8 — Interaction

Speech, voice, screen, movement, head orientation, LEDs, social behavior, IoT interaction, and control application integration.

### Layer 9 — Safety and trust boundary

Protected policy, authorization, action validation, emergency stop, hardware limits, audit, and privileged execution.

## Dependency Rule

Dependencies flow downward through contracts. Higher-level intelligence may request capabilities, but it must not reach around the contract to manipulate lower-level implementation details.

For example:

```text
Nemotron
  ↓
ActionRequest
  ↓
PolicyEngine
  ↓
SafetyGateway
  ↓
NavigationService
  ↓
ROS 2
  ↓
Motor Controller
```

Never:

```text
Nemotron → motor driver
```

## Runtime Strategy

Novi must support the same logical interfaces across:

```text
Mac development
      ↓
Simulation
      ↓
Jetson edge runtime
      ↓
Physical robot
```

Only platform adapters and performance-specific implementations should change.

## Documentation Map

- `00_HIGH_LEVEL_ARCHITECTURE.md` — system overview, boundaries, and architectural choices.
- `01_DETAILED_SYSTEM_ARCHITECTURE.md` — detailed component topology, data flow, lifecycle, interfaces, and failure behavior.
- `02_ARCHITECTURAL_PRINCIPLES.md` — mandatory engineering rules and constraints.
- `03_COMPONENT_BOUNDARIES.md` — ownership and dependency boundaries between subsystems.
- `04_RUNTIME_PROFILES.md` — Mac, simulation, Jetson, and physical deployment profiles.
- `05_CROSS_CUTTING_REQUIREMENTS.md` — observability, configuration, audit, performance, reliability, and testing requirements.
- `06_107_DURABLE_STATE_EVENT_LOG_EXECUTION_SEMANTICS.md` — P1 durable-state substrate, event semantics, versioning, provenance, checkpoints, and execution/recovery contracts.

### P1 architecture sequence

```text
107 Durable State / Event Log / Execution Semantics
  ↓
108 Transactions / Concurrency / Consistency / Conflicts
  ↓
109 Replication / Synchronization / Distributed Memory
  ↓
110 Recovery / Checkpointing / Disaster Resilience
  ↓
111 Privacy / Retention / Dependency-Aware Erasure
  ↓
112 Observability / Evaluation / Lifespan Reliability
  ↓
113 Resource Governance / Scheduling / Budgets
  ↓
114 Multi-Agent Coordination / Delegation / Shared Memory
```

## Status

**Architecture status:** Proposed / Foundation

This folder is authoritative for system-level architectural decisions unless a newer Architecture Decision Record explicitly supersedes a statement.
