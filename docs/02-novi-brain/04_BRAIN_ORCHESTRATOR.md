# 04 — Novi Brain Orchestrator

**Status:** P0 — critical

The Brain Orchestrator makes Novi behave as one persistent agent rather than independent models and robotics processes. It coordinates attention, execution, model routing, memory/context, goals, skills, resources, interruptions and recovery; it does not own every subsystem.

## Runtime

Novi is not `prompt → process → answer → sleep`. It continuously observes, updates state, selects attention, checks goals, reacts/deliberates/waits, executes bounded work, observes outcomes and repeats.

## Cognitive modes

- **REACTIVE:** fast bounded response.
- **INTERACTIVE:** human conversation/social interaction.
- **DELIBERATIVE:** reasoning and planning.
- **EXPLORATORY:** bounded curiosity/information gathering.
- **MAINTENANCE:** memory, diagnostics and housekeeping.
- **RECOVERY:** degraded/failure handling.

## Scheduling

Combine event-driven, deadline/scheduled, state-change-driven and background work. Safety-critical interrupts bypass ordinary cognitive priority arbitration.

## Attention arbitration

Candidates are scored using safety, urgency, human interaction, goal relevance, consequence, uncertainty, novelty, social relevance and resource cost. The decision records why a candidate was selected/deferred.

## Context construction

Build model context from current evidence, relevant world state, memories, active goal, interaction state, active skill, constraints, uncertainty, capabilities and resources. Do not pass complete historical state to every model.

## Model routing

Route by task, modality, latency, quality, confidence, context size, hardware, power/thermal budget, privacy, offline requirement, health and version. Every route is observable and versioned.

## Action orchestration

```text
model/reasoner → structured intention → goal/plan → skill
→ action proposal → governance → safety → robotics/control
```

Models never directly emit motor authority.

## Interruption

A lower-priority task can be paused for a higher-priority interaction, goal or environmental change. The paused task retains state and can be resumed, revised or cancelled. Safety interrupts are independent.

## Parallelism

Independent perception, audio, localization, conversation and background tasks can run concurrently, subject to ownership and consistency constraints.

## Resource-aware execution

Track CPU, GPU, RAM, VRAM, temperature, power, battery, storage, network and model availability. Select `FULL_COGNITION`, `DEGRADED_COGNITION`, `REACTIVE_ONLY` or `SAFE_MINIMUM` as appropriate.

## Failure handling

Every operation has timeout, retry, fallback, cancellation, classification, observability and recovery behavior. Physical-action model timeouts never cause blind continuation.

## Continuous-life behavior

The orchestrator enables bounded autonomous activity: situational awareness, active goals, meaningful environmental observation, maintenance, curiosity, appropriate greetings and body orientation. It must also allow intentional inactivity.

## Learning feedback

`plan → action → outcome → expectation comparison → experience → memory → evaluation`. Ordinary runtime must not silently retrain production models.

## Security

Treat external content, model output, tool responses and sensor-derived events as untrusted until validated. Protect against prompt injection, memory poisoning, spoofing and unauthorized capability invocation.

## Offline

Core orchestration must continue without network access for safety, state continuity, memory, bounded interaction and physical control.

## Acceptance

Test continuous operation, simultaneous modalities, human interruption during navigation, high-priority obstacle during conversation, model timeout/disagreement, memory outage, GPU pressure, thermal degradation, network loss, restart/recovery, conflicting goals, stale sensors and long-duration replayable operation.