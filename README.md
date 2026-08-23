# Novi

Novi is a standalone project to build a persistent autonomous embodied AI system designed to perceive its environment, maintain a persistent world model and memory, reason and plan, develop relationships and personality, learn continuously, and safely act through a physical robotic body.

Novi is **not a voice assistant with wheels** and is not defined by a particular LLM, robot chassis, simulator, GPU vendor, or compute board.

## North Star

The end goal is:

> **Build Novi into a persistent, autonomous, embodied artificial intelligence that continuously perceives and understands its environment, maintains a coherent model of the world and itself, remembers and learns from experience, forms and pursues goals, reasons and plans, develops and uses skills, interacts naturally with people, and acts safely in the physical world — while remaining locally capable, inspectable, auditable, recoverable, and governed by explicit safety boundaries.**

See [`docs/00-strategy/NOVI_NORTH_STAR.md`](docs/00-strategy/NOVI_NORTH_STAR.md).

## Current Development Stage

Novi has moved from architecture/pre-implementation preparation into **executable Brain implementation and Mac prototype validation**.

The current focus is building the first working Novi Brain on a Mac before committing to final robot compute hardware.

### Mac Brain prototype

The [`novi/brain/`](novi/brain/) package is the canonical home for the Novi brain implementation, its documentation, models, tests, scenarios and evidence.

The Mac acts as Novi's temporary body:

```text
Mac camera ───────┐
                  ▼
             Perception
                  │
Microphone ──► Audio
                  │
                  ▼
             World State
                  │
              Memory
                  │
              Cognition
                  │
        Reasoning / Planning
                  │
              Autonomy
                  │
           Action Proposal
                  │
             Virtual Body
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
     Speakers        Virtual actions
```

The Mac prototype is **capability-first and model-agnostic**. Real Mac-compatible neural models are used where practical; NVIDIA-specific models and acceleration remain future deployment providers rather than Mac prerequisites.

### Current Mac milestone

**M1 — Real Neural Perception** is the current implementation milestone.

The first concrete neural candidate is a Torchvision SSDLite320 MobileNetV3 object detector behind Novi's `ObjectDetector` capability interface. The model is deliberately replaceable: a candidate becomes an official Mac provider only after successful execution on the actual Mac with representative inputs and evidence.

M1 progression:

```text
PyTorch / torchvision
        ↓
MPS verification
        ↓
SSDLite MobileNetV3
        ↓
test-image.png
        ↓
real detections
        ↓
Novi perception
        ↓
world state
        ↓
real Mac camera
        ↓
continuous perception
```

See [`docs/specs/brain/34_M1_REAL_NEURAL_PERCEPTION.md`](docs/specs/brain/34_M1_REAL_NEURAL_PERCEPTION.md) and [`docs/specs/brain/33_MAC_FIRST_RUN_GUIDE.md`](docs/specs/brain/33_MAC_FIRST_RUN_GUIDE.md).

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

Jetson AGX Orin 64GB remains a reference hardware candidate, not a locked commitment. Jetson AGX Thor remains under consideration. Final hardware selection will follow measured software workload, AI model requirements, power, thermal, sensor, synchronization and safety constraints.

## Technology Policy

See:

- [`docs/TECHNOLOGY_REFERENCE.md`](docs/TECHNOLOGY_REFERENCE.md) — ecosystem catalog.
- [`docs/TECHNOLOGY_STACK_BASELINE.md`](docs/TECHNOLOGY_STACK_BASELINE.md) — implementation-oriented stack baseline.
- [`docs/00-strategy/NOVI_PRE_IMPLEMENTATION_READINESS_AUDIT.md`](docs/00-strategy/NOVI_PRE_IMPLEMENTATION_READINESS_AUDIT.md) — readiness and gap register.
- [`docs/specs/brain/31_MAC_MODEL_COMPATIBILITY_MATRIX.md`](docs/specs/brain/31_MAC_MODEL_COMPATIBILITY_MATRIX.md) — Mac model compatibility policy.

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

For Mac AI models specifically, installation alone does not establish compatibility. A model must execute a representative Novi workload on the actual Mac and produce valid outputs through the canonical capability interface.

## Hardware

See:

- [`docs/05-hardware/README.md`](docs/05-hardware/README.md)
- [`docs/05-hardware/00_HIGH_LEVEL_HARDWARE_ARCHITECTURE.md`](docs/05-hardware/00_HIGH_LEVEL_HARDWARE_ARCHITECTURE.md)
- [`docs/05-hardware/26_HARDWARE_SELECTION_AND_BOM_BASELINE.md`](docs/05-hardware/26_HARDWARE_SELECTION_AND_BOM_BASELINE.md)

The final physical BOM is deliberately deferred until the cognitive workload, robot geometry, power, thermal, sensor-FOV, synchronization and safety requirements are measured.

## Repository Structure

```text
novi/
├── brain/          # brain unit (reasoning, cognition, soul, memory, knowledge, context)
├── cognition/      # typed cognition contracts (Pydantic)
├── contracts/      # canonical JSON schemas
└── web/            # thin brain runner / HTTP interface

docs/
├── 00-strategy/
├── 01-system-architecture/
├── 02-autonomy/
├── 03-cognition/
├── 04-memory-and-knowledge/
├── 05-hardware/
├── TECHNOLOGY_REFERENCE.md
└── TECHNOLOGY_STACK_BASELINE.md

scripts/
└── Mac Brain setup, diagnostics and test runners
```

`novi/` is the single canonical namespace. There is no separate `MAC_BRAIN/` package.

## Validation Status

The deterministic Mac Brain implementation and CI integration have been validated. The first real neural object-detection provider is implemented and the Mac validation campaign is now progressing through M1.

The project distinguishes implementation from validation:

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

A documented capability is not automatically considered validated. Evidence from real execution is required before a capability is promoted to a higher validation state.
