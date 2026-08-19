# Novi Mac Brain Prototype Program

**Status:** ACTIVE  
**Purpose:** Build the first executable incarnation of the Novi Brain on a Mac before final robot hardware is selected.

## North star

Build a real, continuously running Novi Brain that can use the Mac camera, microphone and speakers as its temporary body; perceive and interpret its environment; maintain world state and memory; reason and plan; pursue bounded goals; propose and execute virtual actions; recover from tested failures; and produce reproducible evidence of its behavior.

## The Mac is a temporary body, not a toy

The Brain, contracts, cognition, memory, autonomy and evidence mechanisms should be real implementations. Hardware-dependent interfaces are replaced by Mac-compatible adapters or virtual devices.

```text
Mac camera       -> real sensor input
Mac microphone   -> real sensor input
Mac speakers     -> real output
AI models        -> real where practical
Brain            -> real implementation
Memory           -> real implementation
Cognition        -> real implementation
Autonomy         -> real bounded implementation
Virtual body     -> simulated actuation
```

## Core loop

```text
OBSERVE
  -> INTERPRET
  -> UPDATE WORLD STATE
  -> RECALL MEMORY
  -> REASON
  -> SELECT/UPDATE GOAL
  -> PLAN
  -> PROPOSE ACTION
  -> VALIDATE
  -> ACT
  -> OBSERVE AGAIN
```

## Program phases

1. Mac I/O foundation.
2. AI/model runtime integration.
3. Perception and audio understanding.
4. World-state engine.
5. Memory.
6. Cognition and reasoning.
7. Goals and planning.
8. Bounded autonomy.
9. Virtual body and action system.
10. Closed-loop operation.
11. Failure/recovery.
12. Continuous operation and acceptance.

## Hardware boundary

No final robot compute platform is selected by this program. Jetson AGX Orin 64GB and Jetson AGX Thor remain candidates. The Mac prototype must preserve interfaces so NVIDIA implementations can replace Mac backends later.

## AI boundary

AI models are capability providers. They do not own safety authorization, actuator authority or durable semantic ownership. Model providers must be replaceable behind stable Novi interfaces.

## Success condition

Mac Brain v0.1 is accepted only when representative scenarios demonstrate multimodal perception, memory, reasoning, bounded goal execution, virtual action, continuous closed-loop behavior and tested recovery, with evidence for each capability.
