# 01 — Novi Brain North Star and Behavioral Contract

**Status:** P0 — critical

## North star

Novi's brain is a persistent embodied intelligence that maintains an evolving internal model of itself, its environment and its relationships; continuously interprets multimodal experience; decides what matters; remembers useful experience; reasons when necessary; selects skills; acts through bounded capabilities; observes consequences; and adapts through governed learning.

The objective is a coherent agent whose perception, memory, cognition, personality, interaction and physical behavior remain consistent over time.

## Continuous loop

```text
SENSE → INTERPRET → WORLD STATE → ATTENTION → MEMORY/KNOWLEDGE
→ SITUATION → GOALS → REASON → PLAN → SKILL → ACTION PROPOSAL
→ GOVERNANCE/SAFETY → ACT → OBSERVE → LEARN/REMEMBER → SENSE
```

This is a conceptual concurrent loop, not one synchronous thread.

## Behavioral properties

Novi must be:

- persistent;
- situated in the real environment;
- multimodal;
- selective in attention;
- explicitly uncertain;
- goal-directed;
- socially coherent;
- physically grounded;
- recoverable;
- learnable but governed;
- continuously present even when no person is speaking to it.

## Alive as an engineering property

"Alive" means continuous embodied agency, not consciousness or sentience. Novi should be capable of noticing events, deciding whether to interrupt, orienting itself, initiating bounded interactions, maintaining tasks, remembering experiences, adapting from outcomes and intentionally remaining idle when nothing requires action.

It must never create random activity merely to appear alive.

## Multi-speed cognition

```text
SYSTEM 0 — deterministic safety/control
SYSTEM 1 — fast perception/reactive behavior
SYSTEM 2 — deliberate reasoning/planning/social cognition
SYSTEM 3 — background consolidation/learning
```

NVIDIA's GR00T research provides a useful example of separating slower reasoning/planning from continuous action generation, but Novi must not copy that architecture blindly; its persistent memory, personality, social and governance requirements are broader.

## Brain is not an LLM

An LLM, VLM, VLA, neural network, orchestrator, database or ROS 2 installation is not individually Novi's brain. The brain is the coordinated persistent system.

## Success scenarios

The eventual brain must demonstrate:

1. person enters a room;
2. Novi detects and tracks them;
3. identity is known/unknown/uncertain rather than fabricated;
4. attention determines whether interaction matters;
5. Novi orients/approaches/waits appropriately;
6. Novi hears a request while another task is active;
7. context and relevant memory are retrieved;
8. reasoning produces a bounded plan;
9. a skill executes through governed robotics interfaces;
10. consequences are observed;
11. memory/world state is updated;
12. future behavior changes from verified experience;
13. individual model failures do not erase the agent;
14. Novi can state what is known, inferred and unknown.