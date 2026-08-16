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
3. **Open-source and local first** — the default solution must be open source, locally runnable, and suitable for offline/private operation.
4. **Best existing solution first** — before implementing a subsystem ourselves, evaluate mature existing open-source local solutions from NVIDIA, TensorFlow, PyTorch, OpenCV, ROS, Hugging Face, or other relevant ecosystems. Do not reinvent a capability that already meets our requirements.
5. **Vendor-neutral core** — NVIDIA is the reference deployment platform, but the cognitive core is not hard-coded to NVIDIA APIs. A different vendor or framework can be selected when it is objectively better for the specific requirement.
6. **NVIDIA-preferred where appropriate** — when an NVIDIA component is the best fit for the target Jetson/robotics workload, use it rather than creating an unnecessary replacement.
7. **Specialized systems for specialized work** — perception, speech, navigation, hardware control, and safety do not become LLM responsibilities.
8. **Memory is not just RAG** — Novi maintains episodic, semantic, spatial, temporal, procedural, and verified knowledge with provenance.
9. **Learning is evidence-driven** — observations, hypotheses, facts, and owner-verified knowledge remain distinguishable.
10. **Schema evolution is controlled** — Novi may create new data structures when necessary, but through a governed Data/Knowledge capability layer.
11. **Safety is outside adaptive intelligence** — the immutable safety boundary cannot be modified by the AI.
12. **Simulation before hardware** — the same logical interfaces should work with simulated and physical sensors and actuators.
13. **Everything is observable and auditable** — autonomous decisions, data changes, model calls, tool calls, and physical actions have traceable records.
14. **Connectivity is optional** — Wi-Fi and Bluetooth extend Novi's capabilities but are never prerequisites for core cognition, perception, autonomy, memory, personality, safety, local interaction, or hardware operation.
15. **Offline-first core** — Novi must remain fully functional in an isolated environment with no Wi-Fi, no Bluetooth, and no external network access. Connectivity-dependent features must degrade gracefully and recover through controlled synchronization when connectivity returns.

## Formal Connectivity Architecture Rule

> **Novi must be fully operational without Wi-Fi, Bluetooth, or external network access. Connectivity may extend Novi's capabilities but must never be a mandatory dependency for core perception, cognition, autonomy, memory, personality, safety, local interaction, diagnostics, or physical operation.**

The connectivity state may change what optional capabilities are available, but it must not determine whether the core system can operate.

```text
                         NOVI CORE
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
      Perception         Cognition          Memory
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                    Local capabilities
                            │
               ┌────────────┴────────────┐
               │                         │
             Wi-Fi                 Bluetooth
            OPTIONAL                OPTIONAL
```

When connectivity is unavailable, Novi continues local operation. Network-dependent tasks may queue, defer, expire, or be disabled according to their capability contract. Reconnection must not bypass privacy, authorization, provenance, deletion, or safety policies.

## Solution Selection Policy

Novi follows a **local-first, open-source-first, existing-solution-first** policy.

For every significant technical capability, the engineering process should first ask:

```text
Does a mature solution already exist?
        ↓
Is it open source with an acceptable license?
        ↓
Can it run locally on our target environment?
        ↓
Does it meet our accuracy / latency / memory / power requirements?
        ↓
Is it maintained and sufficiently mature?
        ↓
Does it integrate cleanly with Novi's interfaces?
        ↓
YES → adopt / integrate / wrap it
NO  → evaluate alternatives
        ↓
Still no suitable local solution?
        ↓
Consider a cloud service only as an explicit exception
```

## Cloud Exception Policy

Cloud services are **not the default architecture**. A cloud dependency may be considered only when no suitable local open-source solution exists or the capability is genuinely impractical locally, and only after privacy, security, latency, cost, availability, vendor lock-in, retention, and graceful-degradation implications are documented.

Cloud use must never silently become mandatory for core autonomous operation if local operation is technically feasible.

## Development Environments

### Mac development

The Mac is the primary early development environment. It should support the majority of the cognitive system, knowledge system, personality, autonomy loop, camera/microphone experimentation, UI, simulation adapters, and automated tests.

### Simulation

NVIDIA Isaac Sim and ROS 2 are the reference robotics simulation path. Simulation must expose the same logical contracts used by the physical robot. Other simulation technologies should be considered when they provide a better fit for a specific workload.

### Jetson

The target edge platform is NVIDIA Jetson AGX Orin 64GB. NVIDIA CUDA, TensorRT, Isaac ROS, JetPack, and related tooling are used where they provide measurable benefits. Alternative local frameworks remain acceptable when they better satisfy a specific requirement.

### Physical robot

The physical body is introduced only after the software can operate against simulated hardware and has passed the required safety and integration tests.

## Repository Rules

- Do not add a feature without identifying its architectural domain.
- Do not bypass subsystem interfaces to access another subsystem's implementation directly.
- Do not let LLM code directly control motors, safety-critical hardware, or protected storage.
- Do not silently change an architectural contract; document the decision.
- Do not treat an observation as a verified fact without provenance and appropriate validation.
- Do not allow autonomous schema evolution to modify immutable system/safety data.
- Prefer existing mature open-source local solutions over custom implementations when they satisfy requirements.
- Compare NVIDIA and non-NVIDIA alternatives for important infrastructure decisions instead of assuming NVIDIA is always best.
- Prefer small, independently testable changes.
- Every significant subsystem must have unit, integration, and failure-mode tests appropriate to its risk.
- No subsystem may introduce an implicit network dependency into the offline-capable core.

## Documentation Structure

Documentation is organized by system domain. Every domain folder must contain a `README.md` that provides the high-level purpose, scope, terminology, dependencies, and document map. Detailed engineering specifications are stored in separate documents beneath the domain.

The first domain is `01-system-architecture/`. It defines the system-wide architecture and the boundaries that all later domains must follow.

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
