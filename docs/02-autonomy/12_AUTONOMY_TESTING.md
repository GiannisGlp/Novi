# 12 — Autonomy Testing

## Status

**DESIGN**

## Purpose

Autonomy must be tested as a behavioral system, not only as individual functions. Tests must cover perception uncertainty, memory, planning, interruptions, failures, learning, safety, and long-running operation.

## Test Layers

```text
unit
→ contract
→ integration
→ scenario
→ simulation
→ hardware-in-loop
→ endurance
```

## Deterministic Unit Tests

Test:

- priority calculations;
- attention gates;
- state transitions;
- goal lifecycle;
- plan validation;
- policy checks;
- event correlation;
- retry/cancellation;
- confidence handling.

## Contract Tests

Every service must be testable against typed contracts independent of its implementation.

## Scenario Tests

Scenarios should describe a starting world, events, expected state transitions, allowed actions, forbidden actions, and final state.

Example:

```text
Scenario: person enters home
Given front door closed
And Vano is away
When door opens
And face recognition identifies Vano
Then world model says Vano is home
And autonomy may greet only if social policy permits
And no unrelated action is started
```

## Adversarial Scenarios

Test:

- conflicting sensor observations;
- false face recognition;
- hallucinated tool names;
- malformed tool arguments;
- stale world state;
- repeated events;
- network loss;
- model timeout;
- sensor failure;
- battery depletion;
- obstacle appearing during navigation;
- prompt injection through external content;
- malicious or misleading user/tool data.

## Learning Tests

Verify that:

- hypotheses remain hypotheses until validated;
- source/provenance is retained;
- contradictions are detected;
- user-confirmed information is recorded correctly;
- learning cannot alter immutable safety data;
- repeated observations can form routines;
- deletion requests propagate according to policy.

## Simulation

Use NVIDIA Isaac Sim when physical/sensor realism or ROS 2 integration materially improves testing. Simulation should provide reproducible scenarios and configurable noise.

## Hardware-in-Loop

Before physical autonomy, run selected components with real Jetson hardware while motors/actuators remain simulated or safely isolated.

## Endurance

Run continuous autonomy for long periods and measure:

- memory growth;
- event backlog;
- thermal state;
- model latency;
- CPU/GPU utilization;
- storage growth;
- failed/recovered services;
- behavior drift.

## Acceptance Gates

A feature should not move from simulation to physical deployment until:

1. unit/contract tests pass;
2. scenario tests pass;
3. safety tests pass;
4. replay tests pass;
5. resource limits are known;
6. failure recovery is demonstrated.
