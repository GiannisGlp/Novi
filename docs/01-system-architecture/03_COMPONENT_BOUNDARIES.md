# 03 — Component Boundaries

## Purpose

This document defines ownership boundaries so that the implementation does not become a monolith.

## Boundary Table

| Domain | Owns | May depend on | Must not own |
|---|---|---|---|
| Perception | sensor interpretation | hardware interfaces, model runtime | durable truth |
| World Model | current structured world state | events, identity, storage | raw sensor drivers |
| Memory | durable experience and retrieval | storage, embeddings, world model | motor control |
| Knowledge | structured facts/concepts/schema | memory, storage, verification | safety decisions |
| Attention | relevance/interaction state | events, world model, social state | hardware execution |
| Personality | stable traits/dynamic social behavior | identity, context, memory | safety policy |
| Autonomy | continuous loop/goals | all cognitive contracts | direct hardware drivers |
| Agent Runtime | model context/tool orchestration | model runtime, tools, memory | safety bypass |
| Models | inference | hardware runtime | business/world state |
| Tools | bounded capabilities | domain services | unrestricted system access |
| Policy | allowed behavior | context, safety rules | model weights |
| Safety | physical-action constraints | trusted state, hardware health | adaptive memory |
| ROS 2 | robotics middleware | hardware drivers | personality/LLM logic |
| Hardware | physical I/O | ROS 2/driver contracts | reasoning |
| Control App | monitoring/control UI | application APIs | direct DB/hardware access |
| Diagnostics | health/metrics/audit | system telemetry | autonomous policy |

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

A lower-level component must not import a higher-level cognitive component merely to satisfy a convenience requirement.

## Perception Boundary

Perception receives raw or near-raw sensor data and emits normalized observations. It may call specialized models. It does not decide what a person ultimately means or permanently store a verified fact.

## World Model Boundary

The world model is the authoritative structured representation of current state. It consumes events and maintains versions. It does not own raw media or model weights.

## Memory Boundary

Memory owns durable experiences and retrieval. It can reference world-model entities, but it must preserve provenance and historical context.

## Knowledge Boundary

Knowledge manages concepts, facts, relationships, sources, verification, and schema evolution. It must use controlled storage interfaces.

## Autonomy Boundary

Autonomy coordinates the cognitive loop. It may ask other services to perform work, but it does not implement their internals.

## Model Boundary

Models expose capabilities such as:

```text
reason
vision
transcribe
synthesize
embed
rerank
```

The rest of the system should not depend on a model's local tensor/runtime details.

## Tool Boundary

A tool is a bounded capability with an explicit input/output schema and authorization policy. Tools are not arbitrary plugins with unrestricted access.

## Safety Boundary

Safety is the last software gate before physical execution. It should remain available even if the general reasoning system is unhealthy.

## Hardware Boundary

Hardware adapters translate logical commands and sensor streams into physical interfaces. They must not contain high-level social or reasoning logic.

## Control Application Boundary

The control application observes and controls permitted administrative functions through APIs. It should not connect directly to the database or ROS graph for ordinary application features.

## Forbidden Dependency Examples

The following are architectural violations:

```text
LLM → motor driver
LLM → SQLite credentials
LLM → host filesystem
Web UI → SQLite
Web UI → motor GPIO
Personality → safety limits
Memory → motor controller
Camera driver → Nemotron
ROS driver → personality
```

## Allowed Examples

```text
LLM → Tool API → Navigation Service → Safety → ROS 2
LLM → Knowledge Service → Database
Camera → Perception → Event Bus → World Model
Web UI → Application API → Diagnostics
Autonomy → ModelRuntime → Nemotron
```
