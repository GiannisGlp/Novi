# Novi

Novi is a standalone project to build a persistent autonomous embodied AI system designed to perceive its environment, maintain a persistent world model and memory, reason and plan, develop relationships and personality, learn continuously, and safely act through a physical robotic body.

Novi is **not a voice assistant with wheels** and is not defined by a particular LLM, robot chassis, simulator, GPU vendor, or compute board.

## North Star

The end goal is:

> **Build Novi into a persistent, autonomous, embodied artificial intelligence that continuously perceives and understands its environment, maintains a coherent model of the world and itself, remembers and learns from experience, forms and pursues goals, reasons and plans, develops and uses skills, interacts naturally with people, and acts safely in the physical world — while remaining locally capable, inspectable, auditable, recoverable, and governed by explicit safety boundaries.**

See [`docs/00-strategy/NOVI_NORTH_STAR.md`](docs/00-strategy/NOVI_NORTH_STAR.md).

## Cognitive Loop

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
GOVERNANCE / SAFETY
   ↓
ACT
   ↓
OBSERVE RESULT
   ↓
LEARN / UPDATE
   ↓
CONTINUE
```

## Architecture

Novi uses a **hybrid cognitive architecture**.

Neural models are used where learning is appropriate:

- perception;
- speech;
- multimodal understanding;
- embeddings;
- reasoning;
- prediction;
- learned skills and policies.

Structured/deterministic systems own:

- persistent state;
- memory semantics;
- world-model semantics;
- provenance;
- authorization;
- governance;
- safety;
- hardware limits;
- recovery;
- audit.

The brain is the complete cognitive architecture, not the LLM alone.

## Core Principles

1. **Autonomous first** — Novi continuously observes and evaluates its environment rather than waiting for prompts.
2. **Hybrid intelligence** — neural models and structured systems are combined deliberately.
3. **Local/offline first** — core cognition, memory, safety and physical operation must not require cloud connectivity.
4. **Existing solution first** — use mature open-source solutions when they meet requirements; do not reinvent commodity infrastructure.
5. **Vendor-neutral semantic core** — NVIDIA is an important reference ecosystem, but Novi's contracts must not depend on NVIDIA product names.
6. **Specialized systems for specialized work** — perception, speech, navigation, control and safety are not LLM responsibilities.
7. **Memory is not just RAG** — Novi maintains episodic, semantic, spatial, temporal, procedural and verified knowledge with provenance.
8. **Observation is not truth** — observations, evidence, beliefs, predictions, simulations and counterfactuals remain distinguishable.
9. **Safety is outside adaptive intelligence** — the protected safety boundary cannot be modified by the AI.
10. **Simulation before physical actuation** — the same logical interfaces should operate against simulated and physical systems.
11. **Everything important is observable and auditable** — model calls, data changes, decisions, tool calls and physical actions have traceable records.
12. **Hardware is a consequence of workload** — final hardware is selected only after the software workload and physical requirements are measured.
13. **Connectivity is optional** — Wi-Fi/Bluetooth extend capabilities but never become mandatory for core operation.
14. **Learning is governed** — experience can improve memory, knowledge and skills, but cannot silently rewrite protected invariants.

## Development Strategy

```text
Architecture
    ↓
Cognitive software
    ↓
Synthetic inputs
    ↓
Real perception on development hardware
    ↓
Simulation
    ↓
SIL / HIL validation
    ↓
Hardware capability selection
    ↓
Physical robot
```

The project explicitly follows **build the mind before the body**.

Jetson AGX Orin 64GB is currently a reference hardware candidate, not a locked commitment. Current NVIDIA JetPack 7.2 supports the Jetson Orin family and uses Ubuntu 24.04/L4T 39.2. citeturn5search3

## Technology Policy

See:

- [`docs/TECHNOLOGY_REFERENCE.md`](docs/TECHNOLOGY_REFERENCE.md) — ecosystem catalog.
- [`docs/TECHNOLOGY_STACK_BASELINE.md`](docs/TECHNOLOGY_STACK_BASELINE.md) — implementation-oriented stack baseline.
- [`docs/00-strategy/NOVI_PRE_IMPLEMENTATION_READINESS_AUDIT.md`](docs/00-strategy/NOVI_PRE_IMPLEMENTATION_READINESS_AUDIT.md) — readiness and gap register.

Technology decisions must follow:

```text
Requirement
  ↓
Candidate solutions
  ↓
License/security review
  ↓
Local/offline check
  ↓
Benchmark
  ↓
ADR
  ↓
Adoption
```

## Hardware

See:

- [`docs/05-hardware/README.md`](docs/05-hardware/README.md)
- [`docs/05-hardware/00_HIGH_LEVEL_HARDWARE_ARCHITECTURE.md`](docs/05-hardware/00_HIGH_LEVEL_HARDWARE_ARCHITECTURE.md)
- [`docs/05-hardware/24_HARDWARE_SELECTION_AND_BOM_BASELINE.md`](docs/05-hardware/24_HARDWARE_SELECTION_AND_BOM_BASELINE.md)

The final physical BOM is deliberately deferred until the cognitive workload, robot geometry, power, thermal, sensor-FOV, synchronization and safety requirements are measured.

## Documentation Status

Novi is currently in the **architecture, research and pre-implementation preparation phase**.

A documented capability is not necessarily implemented.

Use these statuses explicitly:

```text
DESIGNED
PROPOSED
EVALUATING
PROTOTYPE
IMPLEMENTED
TESTED
INTEGRATED
SIMULATED
DEFERRED
BLOCKED
DEPRECATED
```

## Repository Structure

```text
docs/
├── 00-strategy/
├── 01-system-architecture/
├── 02-autonomy/
├── 03-cognition/
├── 04-memory-and-knowledge/
├── 05-hardware/
├── TECHNOLOGY_REFERENCE.md
└── TECHNOLOGY_STACK_BASELINE.md
```

The architecture domains remain authoritative for their respective subsystem semantics. Strategy documents define direction; technology references define candidates; ADRs define adopted implementation decisions.
