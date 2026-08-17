# 15 — Autonomy Implementation Roadmap

## Status

**DESIGN** — roadmap and acceptance gates.

This roadmap describes the **Autonomy workstream**. It does not replace the Brain, Cognition, Memory/Knowledge, policy/safety, or hardware roadmaps.

## Phase 0 — Contracts

Implement and validate:

- autonomy event schemas;
- world-state consumption interfaces;
- goal/plan/action contracts;
- capability interfaces;
- policy interfaces;
- cognition request/response interfaces;
- memory/knowledge request interfaces;
- autonomy state machine;
- behavioral audit events.

**Exit:** all contracts have unit/contract tests and no component requires direct cross-layer access.

## Phase 1 — Mac Autonomous Runtime

Implement:

- event integration;
- autonomy state machine;
- behavioral attention;
- goals;
- deterministic behavioral planner;
- capability gateway interface;
- local camera/microphone adapters through Brain/runtime;
- simulated robot adapter;
- basic memory/knowledge integration;
- bounded continuous operation.

**Exit:** Novi can run continuously on the Mac, consume current cognitive state, remain silent when appropriate, manage goals, and perform safe simulated actions.

## Phase 2 — Reasoning Integration

Integrate the selected reasoning capability behind the Cognition contract.

Implement:

- bounded context requests;
- structured outputs;
- candidate strategy/plan handling;
- uncertainty;
- model timeouts;
- model failure fallback.

**Exit:** model-generated proposals pass deterministic validation, Autonomy can commit/replan tasks, and no model can bypass capability/safety boundaries.

## Phase 3 — Learning and Curiosity

Add:

- unknown detection through Cognition;
- curiosity goals;
- learning candidates;
- source/provenance references;
- validation questions;
- routine discovery;
- contradiction handling;
- controlled memory/knowledge integration.

**Exit:** Novi can investigate a meaningful unknown, learn a new fact through an authorized interaction, and request persistence with provenance without modifying protected software.

## Phase 4 — Simulation

Integrate ROS 2 and NVIDIA Isaac Sim where useful.

Implement:

- virtual sensors;
- virtual people/events;
- robot state;
- navigation scenarios;
- obstacle scenarios;
- autonomy replay;
- deterministic scenario seeds.

**Exit:** continuous autonomy scenarios can be executed repeatedly with reproducible results and explicit policy/safety outcomes.

## Phase 5 — NVIDIA Edge Runtime

Target Jetson hardware only after the Mac/simulation behavioral gates pass.

Integrate and benchmark through the appropriate Brain/robotics contracts:

- JetPack;
- CUDA;
- TensorRT;
- Isaac ROS;
- selected camera/perception acceleration;
- selected reasoning runtime;
- ROS 2/Nav2.

Use NVIDIA components wherever they are the best supported solution for the specific workload, not automatically.

**Exit:** sustained autonomous operation with measured resource, latency, thermal, and power characteristics.

## Phase 6 — Hardware-in-Loop

Connect physical sensors while keeping actuators safely isolated. Validate:

- perception;
- localization;
- event timing;
- behavioral task requests;
- safety reactions;
- diagnostics;
- recovery behavior.

**Exit:** all critical scenarios pass without uncontrolled actuator behavior.

## Phase 7 — Physical Novi

Enable physical capabilities progressively:

- motors;
- head/display;
- speakers/microphones;
- cameras;
- IMU;
- LiDAR/depth where selected;
- battery/charging;
- approved IoT integrations.

Start with restricted autonomy and expand only after measured validation.

## Phase 8 — Continuous Evolution

Introduce:

- long-term learning;
- relationship evolution;
- richer curiosity;
- personalized routines;
- advanced world-model reasoning;
- model upgrades;
- controlled adaptive behavior.

Every new autonomy capability receives regression, safety, privacy, and resource tests.

## Release Gates

No phase advances solely because a demo works. Required evidence includes:

- automated tests;
- scenario results;
- failure/recovery behavior;
- resource measurements;
- audit traces;
- safety tests;
- documentation updates;
- verified cross-domain contract behavior.

## Definition of Done for 02-autonomy

The autonomy domain is complete for V1 when:

1. the behavioral loop runs reliably;
2. attention controls interaction;
3. goals and tasks are explicit;
4. candidate reasoning and plans are separated from behavioral commitment;
5. actions use capability contracts;
6. safety is independent;
7. outcomes feed back into task state;
8. learning is controlled and persisted through Memory/Knowledge;
9. events are replayable;
10. the system is observable/auditable;
11. Mac, simulation, and physical profiles share the same autonomy contracts;
12. NVIDIA components are used wherever they are demonstrably appropriate;
13. no NVIDIA dependency leaks unnecessarily into vendor-neutral cognition or autonomy semantics.
