# 02 — Novi Cognitive Architecture

**Status:** P0 — critical

## Purpose

Novi must continuously exist as an embodied agent. A user request is one stimulus, not the event that starts the brain.

```text
WORLD → SENSE → PERCEIVE → INTERPRET → STATE → ATTENTION
→ REACT / THINK / WAIT → GOAL → PLAN/SKILL → ACTION
→ GOVERNANCE → SAFETY → ROBOTICS → WORLD
```

## Concurrent loops

### Reactive loop

Handles fast bounded responses: obstacle changes, contact, name detection, sudden events, local navigation and other time-sensitive events. It must not depend on an LLM.

### Deliberative loop

Handles ambiguity, long-horizon goals, planning, social reasoning, conflicting evidence and complex tasks.

### Background loop

Handles memory consolidation, map maintenance, diagnostics, model health, curiosity candidates and resource optimization. It must be interruptible and bounded.

## Event-driven cognition

Continuous awareness is combined with event-driven execution. Important events include person entry/exit, speech, obstacles, goal changes, task outcomes, sensor degradation, battery/thermal warnings and model failures. Events carry timestamp, provenance and confidence.

## Attention

Attention allocates computation using urgency, relevance, novelty, goal relevance, social relevance, risk, uncertainty, proximity, persistence and resource cost. Safety interrupts use the protected safety path rather than ordinary attention.

## World model

The world model represents entities, places, relationships, activities, environmental state, uncertainty and provenance. It distinguishes OBSERVED, INFERRED, REMEMBERED, PREDICTED, SIMULATED and COUNTERFACTUAL information.

## Self model

The self model contains identity, location, physical configuration, sensor/actuator health, capabilities, active goals/tasks, limitations, software/model versions, resource state, privacy state and safety state. It is grounded in authoritative telemetry rather than generated prose.

## Reasoning

Novi supports fast reasoning, deliberative reasoning, tool-assisted reasoning and predictive reasoning. No single neural model is required to perform all reasoning modes.

## Perception

Raw RGB, depth, LiDAR, IMU, audio, thermal, touch and proprioceptive inputs are transformed through acquisition, timestamping, calibration, preprocessing, neural/classical perception, tracking/fusion and structured evidence.

NVIDIA Isaac ROS is a strong candidate backend for accelerated ROS 2 perception and navigation. NVIDIA documents components including localization/mapping, 3D reconstruction, pose estimation and trajectory planning. citeturn0search0turn0search6

## Proactive behavior

Novi may initiate bounded behavior because of active goals, safety, appropriate social opportunity, environmental change, curiosity, maintenance or continuation of an existing plan. Proactive behavior is constrained by authorization, safety, privacy, context, confidence and resources.

## Autonomous movement

Cognitive intention flows through navigation/skills, action proposal, governance, safety and ROS 2/control. Cognitive models never directly command motors.

## Interaction

Novi should continuously combine presence detection, social context, body orientation, hearing, dialogue, expression and movement. Interaction is stateful and connected to memory and relationships.

## Failure

Missing/stale/contradictory evidence, model timeouts, memory failure, planner failure, skill failure, sensor failure and resource exhaustion produce explicit degraded states rather than silent hallucination.

## Acceptance

Implementation must demonstrate continuous perception, meaningful attention, appropriate reaction/deliberation, bounded action, consequence observation, memory/learning and continued operation without a human prompt restarting the cycle.