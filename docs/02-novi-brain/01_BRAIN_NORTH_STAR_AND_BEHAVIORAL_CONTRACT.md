# 01 — Novi Brain Behavioral Contract
> **⚠️ SUPERSEDED** — Canonical implementations now live in `MAC_BRAIN/` (see `MAC_BRAIN/PERFECTING_PLAN/`). This document is retained for historical reference only.


**Status:** BOUNDARY REFERENCE — NOT CANONICAL NORTH STAR
**Canonical North Star:** `docs/00-strategy/NOVI_NORTH_STAR.md`
**Owner:** `02-novi-brain`

> This document does not define a second Novi North Star. The project North Star is owned exclusively by `00-strategy/NOVI_NORTH_STAR.md`. This document records the implications that the Brain runtime must support.

## Brain runtime interpretation

Novi's brain runtime must support a persistent embodied intelligence that maintains an evolving internal model of itself, its environment and its relationships; continuously interprets multimodal experience; participates in attention, memory, cognition and autonomy; acts through bounded capabilities; observes consequences; and supports governed learning.

The objective is a coherent agent whose perception, memory, cognition, personality, interaction and physical behavior remain consistent over time. The semantic definitions belong to the canonical Cognition, Memory and Autonomy domains.

## Runtime contract

```text
SENSE → PERCEIVE → INTERPRET → WORLD STATE → ATTENTION →
REACT / THINK / WAIT → GOAL → PLAN → SKILL → ACTION PROPOSAL →
GOVERNANCE / SAFETY → ACT → OBSERVE → LEARN / REMEMBER → CONTINUE
```

This is a conceptual concurrent runtime contract, not a definition of ownership for each stage.

## Behavioral implications for Brain

The Brain runtime must support:

- continuous operation independent of a user prompt;
- multi-modal input and model execution;
- multi-rate execution;
- interruption and cancellation;
- bounded action proposals;
- protected safety/governance interfaces;
- runtime degradation and recovery;
- observation of action outcomes;
- persistent operation when individual models or services fail.

## Alive as an engineering property

"Alive" is an engineering property defined by the North Star: continuous embodied agency, not consciousness or sentience. The Brain runtime must provide the infrastructure for noticing, scheduling, executing, observing and remaining intentionally idle when appropriate. It must not manufacture activity merely to appear alive.

## Multi-speed runtime

```text
SYSTEM 0 — deterministic safety/control
SYSTEM 1 — fast perception/reactive execution
SYSTEM 2 — deliberate reasoning/planning execution
SYSTEM 3 — background consolidation/learning execution
```

The exact semantic policy for these modes belongs to the canonical domains that use them.

## Brain is not a model

An LLM, VLM, VLA, neural network, orchestrator, database or ROS 2 installation is not individually Novi's brain. The Brain is the coordinated runtime/integration system that connects the canonical cognitive, memory, autonomy, policy and hardware capabilities.

## Success scenarios

The scenarios below are retained as integration acceptance examples, not as semantic ownership:

1. a person enters a room;
2. perception produces evidence;
3. identity is resolved as known/unknown/uncertain;
4. Cognition produces a situation interpretation;
5. Autonomy determines whether interaction matters;
6. relevant memory is retrieved;
7. a bounded plan/skill is selected;
8. governance and safety approve or reject the action;
9. the robotics interface executes the approved capability;
10. consequences are observed;
11. canonical world state and memory are updated;
12. future behavior can change from verified experience;
13. individual model failures do not erase the agent;
14. Novi can distinguish known, inferred and unknown information.

## Boundary

The Brain directory must not redefine the canonical:

- North Star — `00-strategy`;
- semantic World Model — `03-cognition`;
- Situation Model — `03-cognition`;
- temporal/causal reasoning — `03-cognition`;
- semantic spatial reasoning — `03-cognition`;
- long-term memory/knowledge — `04-memory-and-knowledge`;
- behavioral goal authority — `02-autonomy`;
- safety authority — system/policy layer;
- motor-control authority — hardware/controllers.
