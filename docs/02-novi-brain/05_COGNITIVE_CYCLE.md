# 05 — Novi Cognitive Runtime Cycle

**Status:** BOUNDARY REFERENCE — NOT CANONICAL AUTONOMY LOOP
**Canonical behavioral loop:** `docs/02-autonomy/01_CONTINUOUS_COGNITIVE_LOOP.md`
**Owner:** `02-novi-brain`

> This document does not define a second autonomy loop. It defines how the Brain runtime executes and coordinates the canonical continuous behavior loop.

## Runtime purpose

The Brain runtime must continuously support:

```text
WORLD → PERCEPTION → EVIDENCE → WORLD STATE → ATTENTION
→ REACT / DELIBERATE / WAIT → GOALS/INTENT → PLAN/SKILL
→ ACTION PROPOSAL → GOVERNANCE/SAFETY → ACT
→ OBSERVE OUTCOME → UPDATE/LEARN → CONTINUE
```

The behavioral meaning and policy of these stages belongs to Autonomy, Cognition, Memory and System Architecture. Brain provides execution, scheduling, transport, synchronization and recovery.

## Runtime stages

### 1. Perceive

Schedule and consume RGB, depth, LiDAR, IMU, encoders, microphones, thermal, environmental sensors and external events at appropriate rates.

### 2. Evidence

Transport structured observations containing source, timestamp, frame where relevant, confidence, calibration and processing/model version.

### 3. World-state update

Coordinate updates to the canonical world state. Brain must not redefine semantic world-state ownership.

### 4. Attention

Provide runtime scheduling/resource mechanisms for the attention policy defined by Cognition/Autonomy. Safety interrupts use the protected safety path.

### 5. React / deliberate / wait

Schedule reactive, deliberative and intentional-wait execution according to the canonical autonomy policy.

### 6. Goals and intent

Execute and transport the goal/intent decisions produced by Autonomy and Cognition.

### 7. Planning and skills

Provide runtime support for planning/skill components and enforce their capability interfaces. Plans define what should happen; skills define how known actions are performed according to their canonical domain contracts.

### 8. Action proposal

Transport structured action proposals containing target, reason, confidence, constraints, expected outcome, required capabilities, deadline and cancellation conditions.

### 9. Governance and safety

Route proposals through the authoritative governance/safety interfaces. A runtime path must never treat proposal generation as authorization.

### 10. Act

Execute only approved capabilities through robotics/control interfaces and return acceptance, progress, completion, failure and unexpected outcome.

### 11. Observe outcome

Coordinate perception and telemetry needed to determine whether the expected world change occurred.

### 12. Learn/remember

Route meaningful outcomes to the canonical Memory/Knowledge and learning pipelines through governed admission.

## Multi-rate operation

Control/safety, perception, tracking, interaction, planning, reasoning and learning operate at different frequencies. Slow cognition must never block fast safety/control.

## Parallel execution

Camera, audio, localization, conversation and background work may operate concurrently. Shared state must obey system ownership and consistency contracts.

## Interruptions

Brain implements scheduling, cancellation and preemption mechanisms. The semantic priority policy is owned by Autonomy/System Architecture.

## Spontaneous behavior

Brain may execute self-initiated behavior only when a bounded request is produced by an authoritative policy/domain and includes reason, resource budget, safety constraints, cancellation path and observability.

## Degraded runtime

If a capability fails, Brain recomputes available runtime capabilities and continues in a safe degraded mode where permitted. Examples include lighter models under GPU pressure, reduced navigation confidence after sensor loss and local operation after network loss.

## Prediction boundary

Prediction semantics belong to Cognition. Brain provides the runtime required to execute predictive models and return their results with provenance and timing.

## Acceptance

The Brain runtime is acceptable when it continuously executes the canonical autonomy loop, supports bounded latency and interruption, safely routes actions through governance, observes outcomes, supports memory/learning and recovers from individual component failures without requiring a human prompt to restart the cycle.
