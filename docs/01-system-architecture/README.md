# 01 — System Architecture

**Status:** COMPLETE — architecture closure gate passed  
**Scope:** System boundaries, dependencies, runtime profiles, cross-cutting requirements, durable state, consistency, replication, recovery, privacy, observability, resource governance and future multi-agent coordination.

## Purpose

This folder defines the authoritative system-level architecture for **Novi**. It establishes the boundaries, responsibilities, dependencies, runtime environments, architectural principles, contracts and non-negotiable constraints that every other domain must follow.

This is the **system architecture domain**, not the implementation repository. Detailed subsystem behavior belongs in the corresponding domain folders, while technology adoption belongs in ADRs.

## Authority rules

```text
Novi North Star
      ↓
Project strategy
      ↓
System architecture
      ↓
Domain architecture
      ↓
Technology ADRs
      ↓
Implementation specifications
      ↓
Validation evidence
```

If two architecture documents conflict, the newer explicitly approved ADR or higher-authority document wins. No implementation may silently resolve an architectural conflict.

## What This Domain Defines

- What Novi is and is not.
- The autonomous cognitive-loop architecture.
- Major subsystem boundaries.
- Dependency direction.
- Contracts between cognition, perception, memory, knowledge, models, robotics, safety and external systems.
- Mac, simulation, edge and physical-runtime boundaries.
- Adaptive-intelligence versus protected-execution boundaries.
- Durable state and event semantics.
- Consistency and concurrency contracts.
- Replication and synchronization semantics.
- Recovery and disaster-resilience semantics.
- Privacy, retention and dependency-aware erasure semantics.
- Observability, evaluation, resource governance and lifespan reliability.
- Future multi-agent coordination boundaries.

## Architecture principles

1. Autonomous, not prompt-driven.
2. Intelligence is layered.
3. Models are replaceable behind capability interfaces.
4. The cognitive core is vendor-neutral.
5. Evidence is distinguishable from interpretation and verified knowledge.
6. Memory is structured and provenance-aware.
7. Safety and authorization remain outside adaptive model authority.
8. Physical actions require explicit capability and safety boundaries.
9. Local/offline operation is a tested runtime profile.
10. Simulation and physical execution share logical contracts.
11. Durable state is versioned and attributable.
12. Privacy applies to source data and material derivatives.
13. Everything critical is observable, auditable and recoverable.
14. Technology choices are benchmarked and adopted through ADRs.

## Core system boundary

```text
                        HUMAN / WORLD
                             │
                     SENSORS / INPUTS
                             │
                             ▼
                     ┌──────────────┐
                     │  PERCEPTION  │
                     └──────┬───────┘
                            │ evidence
                            ▼
                     ┌──────────────┐
                     │  WORLD MODEL │
                     └──────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          MEMORY         KNOWLEDGE      ATTENTION
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     GOALS / POLICY
                            │
                            ▼
                    AGENT / REASONING
                            │
                       proposals only
                            ▼
                 GOVERNANCE / SAFETY
                            │
                     capability calls
                            ▼
                         ROS 2
                            │
                  CONTROL / HARDWARE
                            │
                         WORLD
                            │
                            └──── feedback ────→ PERCEPTION
```

## Adaptive vs protected execution

### Adaptive intelligence may change

- interpretations;
- memories;
- knowledge candidates;
- learned routines;
- plans;
- model selections within policy;
- personality/social state within policy.

### Protected execution may not be changed through ordinary adaptive capabilities

- safety constraints;
- authorization rules;
- emergency-stop behavior;
- physical actuator limits;
- trusted identities/credentials;
- protected configuration;
- recovery authority.

## Runtime contract

The same logical capability interfaces must operate across:

```text
Development host
      ↓
Simulation
      ↓
Edge compute
      ↓
Physical robot
```

Only platform adapters, model runtimes, sensor drivers and performance-specific implementations may change.

## NVIDIA integration rule

NVIDIA is an important reference ecosystem for Novi's edge AI, robotics acceleration and simulation. NVIDIA-specific components must remain behind capability boundaries.

Current NVIDIA documentation explicitly recommends ROS 2 Jazzy for Isaac Sim testing, and current Isaac ROS documentation states that its packages are designed/tested with ROS 2 Jazzy.

Current Jetson AGX Orin documentation identifies JetPack 7.2 / L4T r39.2 as the latest JetPack release for the developer kit.

Therefore the current architecture baseline is:

```text
Novi capability contracts
        ↓
ROS 2 Jazzy boundary
        ↓
NVIDIA adapters where beneficial
        ↓
JetPack / CUDA / TensorRT / Isaac / DeepStream / Holoscan
```

These are implementation candidates, not semantic authorities.

## Documents in this domain

### P0 — system foundation

- `00_HIGH_LEVEL_ARCHITECTURE.md` — system context and major architecture.
- `01_DETAILED_SYSTEM_ARCHITECTURE.md` — components, data flow, lifecycle and failure semantics.
- `02_ARCHITECTURAL_PRINCIPLES.md` — mandatory architectural rules.
- `03_COMPONENT_BOUNDARIES.md` — ownership and dependency boundaries.
- `04_RUNTIME_PROFILES.md` — development, simulation, edge and physical profiles.
- `05_CROSS_CUTTING_REQUIREMENTS.md` — requirements spanning all domains.
- `10_ARCHITECTURE_VALIDATION_AND_TRACEABILITY.md` — requirements-to-architecture-to-test traceability and evidence rules.
- `11_ARCHITECTURE_DECISION_FRAMEWORK.md` — ADR requirements and technology-decision governance.

### P1 — durable/distributed system foundation

- `06_107_DURABLE_STATE_EVENT_LOG_EXECUTION_SEMANTICS.md`
- `07_108_TRANSACTIONS_CONCURRENCY_CONSISTENCY_AND_CONFLICT_RESOLUTION.md`
- `07_109_REPLICATION_SYNCHRONIZATION_AND_DISTRIBUTED_MEMORY_ARCHITECTURE.md`
- `08_110_RECOVERY_CHECKPOINTING_AND_DISASTER_RESILIENCE_ARCHITECTURE.md`
- `09_111_PRIVACY_RETENTION_DEPENDENCY_AWARE_ERASURE_AND_DATA_LIFECYCLE_ARCHITECTURE.md`
- `12_112_OBSERVABILITY_EVALUATION_AND_LIFESPAN_RELIABILITY.md`
- `13_113_RESOURCE_GOVERNANCE_SCHEDULING_AND_BUDGETS.md`
- `14_114_MULTI_AGENT_COORDINATION_DELEGATION_AND_SHARED_MEMORY.md`

### Closure artifacts

- `22_ARCHITECTURE_CLOSURE_AND_BASELINE.md` — canonical architecture closure register.
- `37_ARCH_CLOSE_009_ARCHITECTURE_TO_TEST_MAPPING.md` — ARCH-CLOSE-009 mapping.
- `38_ARCH_CLOSE_010_DEPENDENCY_NUMBERING_INTEGRITY_AUDIT.md` — ARCH-CLOSE-010 final audit.
- `39_ARCH_CLOSE_010_VALIDATION_EVIDENCE_2026-08-19.md` — executable validation evidence for ARCH-CLOSE-010.

## Required future architecture domains

System architecture must also define explicit interfaces with:

- cognition;
- world model;
- memory/knowledge;
- perception;
- models/inference;
- agent/tools;
- safety/security;
- ROS 2/control/navigation;
- NVIDIA platform;
- simulation/digital twin;
- hardware;
- audio/voice;
- data/storage;
- observability;
- testing/validation;
- deployment/operations;
- privacy/governance.

The system architecture must not duplicate those domain specifications; it defines their contracts and dependency direction.

## Closure result

All ten architecture closure workstreams have completed their current architecture-phase gates:

```text
ARCH-CLOSE-001  CLOSED
ARCH-CLOSE-002  CLOSED
ARCH-CLOSE-003  CLOSED
ARCH-CLOSE-004  CLOSED
ARCH-CLOSE-005  CLOSED
ARCH-CLOSE-006  CLOSED
ARCH-CLOSE-007  CLOSED
ARCH-CLOSE-008  CLOSED
ARCH-CLOSE-009  CLOSED
ARCH-CLOSE-010  CLOSED
```

The repository architecture-integrity workflow passes after the ARCH-CLOSE-010 remediation. The final program-level tracker is the canonical surface for recording the System Architecture domain as COMPLETE.

## Status

**Architecture status: COMPLETE for the current implementation phase.**

This does not mean Novi software or the physical robot is complete. Implementation proceeds through the domain completion gates defined by the canonical program tracker.
