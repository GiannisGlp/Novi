# 03 — Component Boundaries

**Status:** P0 normative architecture specification

## Purpose

Define ownership boundaries so Novi remains composable, testable, secure and replaceable rather than becoming a monolith.

## Boundary Table

| Domain | Owns | May depend on | Must not own |
|---|---|---|---|
| Perception | sensor interpretation/evidence | sensor interfaces, model runtime, calibration | durable truth, authorization |
| World Model | current structured world state | events, identity, storage | raw sensor drivers, safety authority |
| Memory | durable experience/retrieval | storage, embeddings, world model | motor control, authorization |
| Knowledge | facts/concepts/relationships/schema | memory, storage, verification | physical safety decisions |
| Attention | relevance/interaction state | events, world model, social state | hardware execution |
| Personality | stable/dynamic social behavior | identity, context, memory | safety policy |
| Autonomy | continuous loop/goals | cognitive contracts | direct hardware drivers |
| Agent Runtime | model/tool orchestration | model runtime, tools, memory | safety bypass |
| Model Runtime | model execution | compute/runtime adapters | business/world state authority |
| Tools | bounded capabilities | domain services | unrestricted system access |
| Policy/Governance | authorization and allowed behavior | context, identity, policy state | model weights |
| Safety | physical constraints/safe-state enforcement | trusted state, hardware health | adaptive memory |
| ROS 2 | robotics middleware | drivers, controllers, navigation | personality/LLM logic |
| ros2_control | controller/hardware abstraction | hardware interfaces | cognitive policy |
| Navigation | path planning/execution | map/localization/robot state | social reasoning |
| Hardware | physical I/O | driver/control contracts | reasoning |
| Control App | administrative UI | application APIs | direct DB/ROS/hardware access |
| Diagnostics | health/metrics/audit | telemetry | autonomous policy |

## Dependency Direction

```text
UI / Control App
      ↓
Application APIs
      ↓
Autonomy / Cognition
      ↓
Domain Interfaces
      ↓
Platform Adapters
      ↓
ROS 2 / OS / Hardware
```

Lower-level components must never import higher-level cognitive components merely for convenience.

## Contract rule

Every boundary should define:

```text
INPUT SCHEMA
OUTPUT SCHEMA
ERROR MODEL
VERSION
AUTHORITY
TIME SEMANTICS
RESOURCE LIMITS
OBSERVABILITY
SECURITY
PRIVACY
RECOVERY
```

## Perception Boundary

Receives sensor data and calibration context. Produces normalized observations/evidence with timestamps, confidence, provenance and sensor/model identity.

It does not permanently assert verified knowledge without downstream governance.

## World Model Boundary

Authoritative for current structured state. Consumes events and maintains revisions. It does not own raw media, model weights or safety policy.

## Memory Boundary

Authoritative for durable experience and retrieval semantics. It references world entities while preserving historical context and provenance.

## Knowledge Boundary

Owns concepts, facts, relationships, verification and schema evolution. It does not authorize physical actions.

## Autonomy Boundary

Coordinates continuous cognition, goals and decision flow. It requests capabilities; it does not implement their physical internals.

## Model Boundary

Models expose stable capability interfaces such as:

```text
reason
vision
transcribe
synthesize
embed
rerank
predict
act_propose
```

The rest of Novi must not depend on tensor/runtime-specific details.

## Tool Boundary

A tool has explicit input/output schemas, authorization, quotas, timeout, cancellation and audit behavior.

A tool is not an unrestricted plugin system.

## Policy Boundary

Policy determines whether a requested capability is permitted under identity, purpose, state, scope and current governance.

## Safety Boundary

Safety is the final software gate before physical execution and must integrate with independent hardware safety mechanisms.

Safety must remain functional if the reasoning model is unavailable.

## Hardware Boundary

Hardware adapters translate logical capability requests and sensor streams into physical interfaces. They must not contain high-level social/reasoning logic.

## Control Application Boundary

The control UI interacts through authenticated application APIs and never receives direct database credentials or unrestricted ROS/hardware access.

## Forbidden Dependencies

```text
LLM → motor driver
LLM → DB credentials
LLM → host filesystem
LLM → unrestricted network
Web UI → SQLite directly
Web UI → motor GPIO
Personality → safety limits
Memory → motor controller
Camera driver → reasoning model
ROS driver → personality
Model → authorization authority
Vector index → semantic truth authority
```

## Allowed Examples

```text
Model → Tool API → Navigation → Policy → Safety → ROS 2
Model → Knowledge Service → validated storage
Camera → Perception → Event → World Model
Web UI → Application API → Diagnostics
Autonomy → ModelRuntime → selected model
```

## NVIDIA boundary

NVIDIA implementations such as Isaac ROS, TensorRT, DeepStream and related accelerators remain behind the relevant capability boundaries. NVIDIA's current documentation shows Isaac ROS packages tested with ROS 2 Jazzy, while DeepStream 9.1 supports Jetson Orin and is based on JetPack 7.2/L4T r39.2. citeturn0search6turn0search0

These facts validate compatibility candidates; they do not grant those products architectural authority.
