# 06 — Action Execution and Feedback

## Status

**DESIGN**

## Purpose

This document defines the boundary between autonomous planning and real execution. Plans become executable only through typed capabilities, policy validation, safety checks, execution monitoring, and outcome verification.

## Action Lifecycle

```text
proposal
→ validated
→ authorized
→ dispatched
→ accepted
→ running
→ completed / failed / cancelled / safety-stopped
→ outcome verified
→ experience recorded
```

## Capability Gateway

All actions pass through a Capability Gateway. Examples include:

- navigation;
- speech output;
- display;
- head movement;
- lighting;
- smart-home control;
- media control;
- diagnostics;
- memory operations;
- file/data operations.

The gateway provides typed schemas, authorization, rate limits, timeouts and observability.

## Physical Actions

Motor and actuator commands must be separated from high-level semantic requests.

```text
Nemotron: "go to kitchen"
        ↓
Navigation capability
        ↓
Nav2 / Isaac ROS / controller
        ↓
Safety limits
        ↓
Motor control
```

The language model never generates raw motor PWM/velocity commands.

## NVIDIA Integration Principle

Where NVIDIA provides a mature component appropriate to the workload, prefer it at the acceleration boundary rather than reimplementing equivalent GPU functionality. Candidate components include Isaac ROS for hardware-accelerated ROS 2 perception/robotics pipelines and TensorRT for supported inference optimization. The capability contract remains Novi-owned and vendor-neutral.

## Outcome Verification

Every consequential action defines an observable success condition. The system should verify the result using the most authoritative available source.

Examples:

- IoT command → device state telemetry;
- navigation → localization + arrival condition;
- speech → playback completion;
- display → application acknowledgement;
- charging → battery telemetry.

## Timeouts

All actions have deadlines. A timeout produces an explicit outcome and does not imply success.

## Cancellation

Actions must support cancellation where physically and technically possible. Safety cancellation has priority over normal cancellation.

## Idempotency

Retryable commands require idempotency keys or state-aware execution to avoid duplicate effects.

## Feedback

Execution feedback updates:

- world model;
- goal state;
- task state;
- memory;
- diagnostics;
- audit trail.

## Recovery

Recovery strategy is capability-specific but must use common result classes:

```text
retry
replan
fallback
ask_user
stop
safe_shutdown
```

## Acceptance Criteria

- no direct LLM-to-actuator path;
- all actions have typed requests;
- safety can interrupt execution;
- outcomes are verified;
- failures are persisted;
- retries are safe;
- execution can be replayed in simulation.
