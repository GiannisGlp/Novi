# Novi

Novi is the clean implementation repository for **Wheely**: an autonomous embodied AI system designed to perceive its environment, maintain a persistent world model and memory, reason and plan, develop relationships and personality, learn continuously, and safely act through a physical robotic body.

This repository is intentionally separate from the original `Wheely` research/prototype repository. The original repository remains a reference and research archive. Novi is the implementation target.

## Project Vision

Novi is not intended to be a voice assistant with wheels. It is intended to operate as a continuously running autonomous cognitive system:

```text
PERCEIVE
   ↓
UNDERSTAND
   ↓
UPDATE WORLD MODEL
   ↓
REMEMBER
   ↓
ATTEND
   ↓
DECIDE
   ↓
REASON
   ↓
PLAN
   ↓
SAFETY CHECK
   ↓
ACT
   ↓
OBSERVE RESULT
   ↓
LEARN
   ↓
CONTINUE
```

The system should be able to run first on a development Mac, then in simulation, and finally on the target **NVIDIA Jetson AGX Orin 64GB** hardware without redesigning the cognitive architecture.

## Core Architectural Principles

1. **Autonomous first** — Novi continuously observes and evaluates its environment rather than waiting for prompts.
2. **One primary general reasoning model initially** — NVIDIA Nemotron 3 Nano 30B-A3B is the primary candidate; specialized models remain separate for perception, speech, embeddings, and other modality-specific tasks.
3. **Vendor-neutral core** — NVIDIA is the reference deployment platform, but the cognitive core is not hard-coded to NVIDIA APIs.
4. **Specialized systems for specialized work** — perception, speech, navigation, hardware control, and safety do not become LLM responsibilities.
5. **Memory is not just RAG** — Novi maintains episodic, semantic, spatial, temporal, procedural, and verified knowledge with provenance.
6. **Learning is evidence-driven** — observations, hypotheses, facts, and owner-verified knowledge remain distinguishable.
7. **Schema evolution is controlled** — Novi may create new data structures when necessary, but through a governed Data/Knowledge capability layer.
8. **Safety is outside adaptive intelligence** — the immutable safety boundary cannot be modified by the AI.
9. **Simulation before hardware** — the same logical interfaces should work with simulated and physical sensors and actuators.
10. **Everything is observable and auditable** — autonomous decisions, data changes, model calls, tool calls, and physical actions have traceable records.

## Documentation Structure

Documentation is organized by system domain. Every domain folder must contain a `README.md` that provides the high-level purpose, scope, terminology, dependencies, and document map. Detailed engineering specifications are stored in separate documents beneath the domain.

The first domain is:

```text
01-system-architecture/
```

It defines the system-wide architecture and the boundaries that all later domains must follow.

Planned domains include:

```text
01-system-architecture/
02-autonomy/
03-cognition/
04-world-model/
05-memory/
06-knowledge-base/
07-perception/
08-personality-and-social/
09-models-and-inference/
10-agent-and-tools/
11-safety-and-security/
12-robotics-and-ros2/
13-nvidia-platform/
14-simulation-and-digital-twin/
15-hardware/
16-audio-and-voice/
17-navigation-and-mapping/
18-iot-and-external-systems/
19-data-and-storage/
20-control-app/
21-observability-diagnostics-audit/
22-testing-and-validation/
23-data-generation-and-training/
24-deployment-and-operations/
25-privacy-and-governance/
26-development-process/
```

The exact list may evolve, but new domains must preserve the documentation rules defined by `01-system-architecture`.

## Documentation Levels

Each domain will be documented at multiple levels:

### High-level

Explains what the subsystem is, why it exists, what decisions have been made, its boundaries, and how it connects to other subsystems.

### Detailed specification

Defines exact responsibilities, interfaces, state, data models, workflows, failure modes, lifecycle behavior, security constraints, performance requirements, and acceptance criteria.

### Implementation

Defines packages, modules, classes, functions, configuration, runtime dependencies, deployment details, and test requirements.

### Validation

Defines how the subsystem is tested on Mac, simulation, Jetson, and physical hardware where applicable.

## Development Environments

### Mac development

The Mac is the primary early development environment. It should support the majority of the cognitive system, knowledge system, personality, autonomy loop, camera/microphone experimentation, UI, simulation adapters, and automated tests.

### Simulation

NVIDIA Isaac Sim and ROS 2 are the reference robotics simulation path. Simulation must expose the same logical contracts used by the physical robot.

### Jetson

The target edge platform is NVIDIA Jetson AGX Orin 64GB. NVIDIA CUDA, TensorRT, Isaac ROS, JetPack, and related tooling are used where they provide measurable benefits.

### Physical robot

The physical body is introduced only after the software can operate against simulated hardware and has passed the required safety and integration tests.

## Repository Rules

- Do not add a feature without identifying its architectural domain.
- Do not bypass subsystem interfaces to access another subsystem's implementation directly.
- Do not let LLM code directly control motors, safety-critical hardware, or protected storage.
- Do not silently change an architectural contract; document the decision.
- Do not treat an observation as a verified fact without provenance and appropriate validation.
- Do not allow autonomous schema evolution to modify immutable system/safety data.
- Prefer small, independently testable changes.
- Every significant subsystem must have unit, integration, and failure-mode tests appropriate to its risk.

## Current Status

Novi is currently in the **architecture and documentation foundation phase**. No assumption should be made that a documented capability is already implemented.

The documentation must explicitly distinguish:

```text
DESIGNED
PROPOSED
PROTOTYPE
IMPLEMENTED
TESTED
INTEGRATED
SIMULATED
DEFERRED
BLOCKED
DEPRECATED
```

## Relationship to the Original Wheely Repository

`GiannisGlp/Wheely` contains prior research, prototypes, experiments, architecture work, and detailed knowledge-base material. It is a reference source rather than the implementation base for Novi.

Useful material may be selectively migrated into Novi after review. Novi should not be created by copying the old codebase wholesale.
