# B1.1 — Closed Simulated Loop Workflow

**Status:** P0 workflow — implementation complete, validation pending  
**Domain:** Brain  
**Stage:** B1 Closed Simulated Loop  
**Date:** 2026-08-19  
**Predecessor:** `30_BRAIN_B0_STAGE_GATE_EVIDENCE_2026-08-19.md`

## 1. Purpose

B1.1 is the first implementation workflow after the B0 Runtime Foundation gate. Its purpose is to prove that Novi can execute a deterministic, stateful, multi-cycle cognitive loop rather than only execute isolated runtime primitives.

The workflow follows the canonical continuous-loop design already established for Novi:

```text
SENSE
 → INGEST
 → NORMALIZE
 → CORRELATE
 → INTERPRET
 → UPDATE WORLD MODEL
 → RETRIEVE CONTEXT
 → ATTEND
 → MAINTAIN GOALS
 → DECIDE
 → REASON / PLAN
 → POLICY / SAFETY
 → EXECUTE
 → OBSERVE OUTCOME
 → STORE EXPERIENCE
 → RETURN TO SENSE
```

The repository's continuous-loop specification explicitly requires continuous operation without a user prompt, typed action requests, safety checks, outcome observation, experience storage and deterministic replay. fileciteturn48file0L2-L2

## 2. Scope of B1.1

B1.1 uses deterministic simulation adapters rather than real cameras, neural networks, ROS 2, Jetson hardware or a physics simulator.

Implemented components:

```text
brain/b1_loop.py
├── SimulatedPerception
├── SimulatedCognition
├── SimulatedMemory
├── SimulatedAutonomy
└── ClosedSimulatedLoop
```

These are **simulation implementations behind ports**, not new semantic authorities. The Brain blueprint requires Brain to execute Cognition, Memory and Autonomy pathways while those domains retain semantic ownership. fileciteturn47file0L2-L2

## 3. First deterministic scenario

The scenario contains one persistent simulated entity:

```text
entity: test_object
state: present
initial distance: 1.0 m
```

Each cycle:

1. creates a timestamped runtime observation event;
2. interprets the observation into a situation;
3. updates current simulated world state;
4. retrieves prior experiences for the entity;
5. selects a goal based on current situation and retrieved memory;
6. creates an abstract `inspect` action proposal;
7. sends the proposal through the existing safety gateway;
8. executes the authorized action through the mock body;
9. records the outcome as an experience;
10. stores that experience for the next cycle.

The observation distance changes deterministically by cycle, making repeated runs reproducible while still demonstrating changing environmental input.

## 4. State continuity

The loop preserves three distinct state categories:

### Current world state

The latest interpreted situation for the simulated entity.

### Active goal state

The current autonomy-selected goal.

### Historical experience

Previously completed action/outcome records.

This separation follows the architecture rule that current working state, world state and retained memory must not be collapsed into one undifferentiated state store. The Brain blueprint explicitly requires Brain State Runtime to avoid duplicating canonical World Model, Soul or long-term Memory semantics. fileciteturn47file0L2-L2

## 5. Event lineage

Every cycle keeps a single correlation lineage through the simulated cognitive path:

```text
simulation observation
        ↓
perception
        ↓
cognition update
        ↓
goal selection
        ↓
action request
        ↓
action proposal
        ↓
safety decision
        ↓
action outcome
        ↓
memory experience
```

The runtime event bus remains responsible for sequencing and correlation metadata; the loop does not invent a second event infrastructure.

## 6. Safety boundary

B1.1 does not weaken the B0 safety boundary.

```text
Autonomy
   ↓
ActionProposal
   ↓
B0 Safety Gateway
   ↓
SafetyDecision
   ↓
Mock Body
```

No simulated autonomy component receives direct body access.

## 7. NVIDIA alignment

B1.1 intentionally does not require NVIDIA software yet. This preserves the vendor-neutral Brain interfaces established in the architecture.

The future simulation/deployment path remains compatible with NVIDIA's robotics stack: NVIDIA describes Isaac ROS as CUDA-accelerated packages and AI models built on ROS 2, while Isaac Sim provides physically based robotics simulation and ROS/ROS 2 integration. citeturn0search0turn0search7

NVIDIA also documents Isaac Sim as a platform for robot simulation, testing and synthetic-data workflows, including custom ROS 2 messages and robot-model import. citeturn0search1turn0search6

Therefore the B1.1 implementation deliberately establishes **semantic/runtime interfaces first**. A later workflow can replace the deterministic adapters with Isaac Sim/ROS 2 or another simulator without changing the Brain's semantic ownership model.

## 8. Acceptance tests

B1.1 must demonstrate:

- continuous multi-cycle execution;
- no user prompt required between cycles;
- world state persists between cycles;
- memory is retrieved by later cycles;
- goal selection remains deterministic;
- action proposals pass through safety;
- authorized actions reach the mock body;
- action outcomes become experiences;
- event correlation lineage is preserved;
- a non-active Brain cannot execute the loop;
- repeated deterministic scenarios produce equivalent semantic results.

## 9. Completion rule

B1.1 can be marked **VALIDATED** only after the repository workflow passes against the current `main` revision.

Passing B1.1 does **not** complete B1. It establishes the first deterministic closed-loop scenario and allows subsequent B1 workflows to add richer evidence, memory/world-state behavior, failure/recovery and replay requirements.

## 10. Next workflow

After B1.1 validation, the next workflow should expand the loop from a single deterministic happy path into **B1.2 — multi-event world-state and memory continuity**, including changing entities, stale observations, event correlation and outcome-driven state updates.
