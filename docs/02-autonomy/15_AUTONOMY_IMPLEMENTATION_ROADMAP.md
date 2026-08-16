# 15 — Autonomy Implementation Roadmap

## Status

**DESIGN** — roadmap and acceptance gates.

## Phase 0 — Contracts

Implement:

- event schemas;
- world-state interfaces;
- goal/plan/action contracts;
- capability interfaces;
- policy interfaces;
- model interface;
- audit events.

**Exit:** all contracts have unit/contract tests and no component requires direct cross-layer access.

## Phase 1 — Mac Autonomous Runtime

Implement:

- event bus;
- autonomy state machine;
- attention;
- goals;
- deterministic planner;
- capability gateway;
- local camera/microphone adapters;
- simulated robot adapter;
- basic memory/knowledge integration.

**Exit:** Novi can run continuously on the Mac, observe the user/environment, remain silent when appropriate, and perform safe simulated actions.

## Phase 2 — Reasoning Integration

Add Nemotron behind the reasoning contract.

Implement:

- context builder;
- structured outputs;
- tool selection;
- plan generation;
- uncertainty;
- model timeouts;
- model failure fallback.

**Exit:** model-generated plans pass deterministic validation and cannot bypass capability/safety boundaries.

## Phase 3 — Learning and Curiosity

Add:

- unknown detection;
- learning candidates;
- source/provenance;
- validation questions;
- routine discovery;
- contradiction handling;
- controlled schema/data evolution.

**Exit:** Novi can learn a new fact from an interaction and retain it with provenance without modifying protected software.

## Phase 4 — Simulation

Integrate ROS 2 and NVIDIA Isaac Sim where useful.

Implement:

- virtual sensors;
- virtual people/events;
- robot state;
- navigation scenarios;
- obstacle scenarios;
- autonomy replay.

**Exit:** continuous autonomy scenarios can be executed repeatedly with deterministic test seeds.

## Phase 5 — NVIDIA Edge Runtime

Target Jetson AGX Orin 64GB.

Integrate and benchmark:

- JetPack;
- CUDA;
- TensorRT;
- Isaac ROS;
- selected camera/perception acceleration;
- Nemotron runtime;
- ROS 2/Nav2.

Use NVIDIA components wherever they are the best supported solution for the specific workload, not automatically.

**Exit:** sustained autonomous operation with measured resource, latency, thermal, and power characteristics.

## Phase 6 — Hardware-in-Loop

Connect physical sensors while keeping actuators safely isolated. Validate:

- perception;
- localization;
- event timing;
- navigation requests;
- safety reactions;
- diagnostics.

**Exit:** all critical scenarios pass without uncontrolled actuator behavior.

## Phase 7 — Physical Wheely

Enable:

- motors;
- head/display;
- speakers/microphones;
- cameras;
- IMU;
- LiDAR/depth where selected;
- battery/charging;
- IoT integrations.

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
- documentation updates.

## Definition of Done for 02-autonomy

The autonomy domain is complete for V1 when:

1. the continuous loop runs reliably;
2. attention controls interaction;
3. goals and plans are explicit;
4. actions use capability contracts;
5. safety is independent;
6. outcomes feed back into state;
7. learning is controlled;
8. events are replayable;
9. the system is observable/auditable;
10. Mac, simulation, and Jetson profiles share the same autonomy contracts;
11. NVIDIA components are used wherever they are the demonstrably appropriate solution;
12. no NVIDIA dependency leaks unnecessarily into vendor-neutral cognition.
