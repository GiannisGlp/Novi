# 05 — Novi Continuous Cognitive Cycle

**Status:** P0 — critical

## Purpose

The cognitive cycle is the primary mechanism behind Novi's continuous embodied existence.

```text
WORLD → PERCEPTION → EVIDENCE → WORLD STATE → ATTENTION
→ REACT / DELIBERATE / WAIT → GOALS/INTENT → PLAN/SKILL
→ ACTION PROPOSAL → GOVERNANCE/SAFETY → ACT
→ OBSERVE OUTCOME → UPDATE/LEARN → CONTINUE
```

## Stages

### 1. Perceive

Consume RGB, depth, LiDAR, IMU, encoders, microphones, thermal, environmental sensors and external events at appropriate rates.

### 2. Evidence

Convert raw inputs into structured observations containing source, timestamp, frame where relevant, confidence, calibration and processing/model version.

### 3. World-state update

Integrate evidence with entities, relationships, activities, changes, uncertainty and temporal history. Contradictory evidence must remain visible.

### 4. Attention

Prioritize safety, human interaction, active goals, novelty, uncertainty, environmental changes and scheduled obligations.

### 5. React / deliberate / wait

React when delay is costly; deliberate for multi-step/ambiguous problems; wait when no useful or required action exists. Waiting is an intentional state.

### 6. Goals and intent

Evaluate active goals, human requests, persistent obligations, safety requirements and bounded curiosity/maintenance. Possible decisions: observe, ask, respond, continue, change task, plan, act or wait.

### 7. Planning and skills

Plans define what should happen; skills define how known actions are performed. Skills expose preconditions, inputs, outputs, constraints, effects, failure and cancellation conditions.

### 8. Action proposal

Produce a structured intention with target, reason, confidence, constraints, expected outcome, required capabilities, deadline and cancellation conditions. It is not authorization.

### 9. Governance and safety

Authorization, capability validation, physical constraints and safety must approve the proposal before execution. Rejected actions are observable.

### 10. Act

Execution occurs through robotics/control. Cognition receives acceptance, progress, completion, failure and unexpected outcome.

### 11. Observe outcome

Perception checks whether the world changed as expected. Unexpected outcomes cause replanning or safe fallback.

### 12. Learn/remember

Meaningful outcomes can become episodic memory, knowledge, skill metrics, planner feedback or model evaluation data through governed admission.

## Multi-rate operation

Control/safety, perception, tracking, attention, interaction, planning, long-horizon reasoning and learning operate at different frequencies. Slow cognition must never block fast safety/control.

## Parallel cognition

Camera, audio, localization, conversation and background memory work may operate concurrently. Shared state must obey ownership and consistency contracts.

## Interruptions

Conceptual priority is safety > immediate human interaction > critical goal > ordinary goal > curiosity > maintenance. Exact policy must be benchmarked.

## Spontaneous behavior

Self-initiated behavior is permitted only when it has a reason, bounded scope, resource budget, safety constraints, cancellation path and observability.

## Degraded cycle

If a capability fails, recompute available capabilities and continue in a safe degraded mode. Examples: lighter models under GPU pressure, reduced navigation confidence after LiDAR loss, local operation after network loss.

## Prediction

Candidate actions may be evaluated using learned or deterministic prediction. Predictions remain distinct from historical observations.

## Acceptance

Novi must demonstrate continuous perception, meaningful attention, appropriate reaction/deliberation, bounded action, consequence observation, memory/learning and continued operation without requiring a human prompt to restart the cycle.