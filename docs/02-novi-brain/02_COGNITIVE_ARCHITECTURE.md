# 02 — Novi Brain Cognitive Runtime Boundary
> **⚠️ SUPERSEDED** — Canonical implementations now live in `MAC_BRAIN/` (see `MAC_BRAIN/PERFECTING_PLAN/`). This document is retained for historical reference only.


**Status:** BOUNDARY REFERENCE — NOT CANONICAL COGNITIVE ARCHITECTURE
**Canonical cognitive architecture:** `docs/03-cognition/01_COGNITIVE_ARCHITECTURE.md`
**Owner:** `02-novi-brain`

> This document must not redefine what Cognition is. It records the Brain runtime implications and interfaces required to execute the canonical Cognition architecture.

## Runtime purpose

Novi must continuously exist as an embodied agent. A user request is one stimulus, not the event that starts the brain. The Brain runtime coordinates the concurrent execution of perception, cognition, memory, autonomy, governance and robotics.

```text
WORLD → SENSE → PERCEIVE → COGNITION → STATE → AUTONOMY
→ ACTION PROPOSAL → GOVERNANCE → ROBOTICS → WORLD
```

## Concurrent runtime loops

### Reactive execution

Provides fast bounded execution for time-sensitive events such as obstacle changes, contact, name detection, sudden events and local navigation. Reactive safety/control paths must not depend on an LLM.

### Deliberative execution

Provides scheduling and resource support for the canonical Cognition and Autonomy components handling ambiguity, long-horizon goals, planning and complex tasks.

### Background execution

Provides bounded, interruptible execution for memory consolidation, diagnostics, model health, map maintenance and resource optimization. The semantic ownership of these activities remains with their canonical domains.

## Event-driven runtime

The Brain runtime transports and schedules events such as person entry/exit, speech, obstacles, goal changes, task outcomes, sensor degradation, battery/thermal warnings and model failures. Events carry timestamp, provenance and confidence according to system contracts.

## Attention boundary

Cognition/Autonomy define the semantic and behavioral meaning of attention. Brain provides the runtime mechanisms for prioritization, scheduling, interruption, resource allocation and protected safety interrupts.

## World-model boundary

The semantic World Model is owned by `03-cognition`. Brain may maintain runtime state, transport evidence and cache/execute model outputs, but it must not create a competing semantic World Model.

## Self-model boundary

Brain owns authoritative runtime/telemetry facts such as current physical configuration, sensor/actuator health, resource state and software/model versions. Cognition owns semantic self-modeling; Memory owns autobiographical history; Autonomy owns current task/goal state.

## Reasoning boundary

Cognition owns reasoning semantics and cognitive model selection. Brain owns model execution infrastructure, scheduling, placement, batching, resource management and runtime fallback.

## Perception runtime

Raw RGB, depth, LiDAR, IMU, audio, thermal, touch and proprioceptive inputs are handled through acquisition, timestamping, calibration, preprocessing, model execution, tracking/fusion and structured evidence pipelines. The semantic interpretation of that evidence belongs to Cognition and other domain owners.

## Autonomous movement boundary

Cognitive/autonomy intent flows through navigation/skills, governance, safety and ROS 2/control. Brain runtime infrastructure must never allow cognitive models to directly command motors outside the governed capability interface.

## Interaction runtime

Brain provides execution infrastructure for presence detection, speech/audio, vision, dialogue transport, expression and movement interfaces. Interaction semantics, identity, relationships and social cognition remain owned by Cognition/Memory/Autonomy.

## Failure boundary

Runtime failures such as model timeouts, memory-service failure, sensor failure, resource exhaustion and network loss must produce explicit degraded states and trigger fallback. Domain-specific semantic responses remain owned by the relevant canonical domain.

## Acceptance

The Brain runtime is acceptable when it can continuously execute and coordinate the canonical Cognition, Memory, Autonomy, Governance and Hardware components without a user prompt restarting the system, while maintaining bounded latency, interruption, recovery and observability.
