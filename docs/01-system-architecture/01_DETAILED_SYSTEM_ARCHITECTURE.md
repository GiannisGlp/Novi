# 01 — Detailed System Architecture

**Status:** P0 detailed system specification  
**Authority:** Cross-domain implementation architecture; technology-specific choices require ADRs.

## 1. Scope

This document defines subsystem responsibilities, interfaces, execution flow, state ownership, lifecycle, concurrency expectations, failure handling, deployment boundaries and security boundaries for Novi.

It is more precise than `00_HIGH_LEVEL_ARCHITECTURE.md` and must be reconciled with domain specifications before implementation.

## 2. Canonical Runtime Topology

```text
┌───────────────────────────────────────────────────────────────────────┐
│                         NOVI APPLICATION RUNTIME                     │
│                                                                       │
│  Event Intake → World Model → Attention / Situation                  │
│       │              │                 │                              │
│       └──────────────┼─────────────────┘                              │
│                      ↓                                                │
│                Memory / Knowledge ↔ Goals                              │
│                      ↓                                                │
│                 Agent Runtime                                          │
│                      ↓                                                │
│             Model Runtime Interface                                    │
│                      ↓                                                │
│              Proposal / Tool Request                                   │
│                      ↓                                                │
│             Governance / Policy                                        │
│                      ↓                                                │
│                Safety Gateway                                          │
└──────────────────────┼────────────────────────────────────────────────┘
                       ↓ capability call
              ROS 2 / robotics services
                       ↓
       ros2_control / Nav2 / sensor interfaces
                       ↓
                    hardware
                       ↓
                    sensors
                       └──────── feedback ───────→ event intake
```

## 3. Process Boundaries

The implementation must separate components according to safety, resource and failure characteristics.

### 3.1 Cognitive application boundary

Contains:

- autonomy orchestration;
- world-model coordination;
- memory/knowledge APIs;
- attention;
- personality/social state;
- goal management;
- agent/tool orchestration.

It does not directly own privileged hardware access.

### 3.2 Model runtime boundary

Models execute behind a versioned inference capability interface.

Requirements:

- explicit model ID/version;
- lifecycle;
- health;
- bounded concurrency;
- timeout;
- cancellation;
- resource accounting;
- structured input/output contracts;
- provenance;
- failure classification.

Candidate implementations may include CPU/reference runtimes, ONNX Runtime, TensorRT/TensorRT-LLM and other validated runtimes.

### 3.3 Robotics boundary

ROS 2 owns robotics communication and integration. High-frequency control and hardware interaction must remain outside the general reasoning runtime.

### 3.4 Safety boundary

The physical safety path must remain available even if cognitive/model processes are unhealthy. The eventual physical implementation must include an independent hardware safety mechanism for actuator power/enable as required by the safety case.

## 4. Event Architecture

All consequential environmental and state-changing inputs are normalized into typed events.

Canonical semantic envelope:

```text
EventEnvelope
├── event_id
├── event_type
├── schema_version
├── occurred_at
├── recorded_at
├── producer_id
├── actor_context
├── authority_context
├── subject_refs[]
├── causation_id
├── correlation_id
├── payload
├── provenance_refs[]
├── policy_context
├── model_context (optional)
├── state_revision
└── integrity_metadata
```

`occurred_at` and `recorded_at` are distinct. Causation must never be inferred from wall-clock time alone.

## 5. Observation vs Interpretation

Novi must distinguish:

```text
Observation
  ↓
Evidence
  ↓
Interpretation
  ↓
Hypothesis
  ↓
Verified knowledge / current state
```

Each transition must preserve provenance and uncertainty.

## 6. World Model Ownership

The world model owns current structured state for:

- people;
- places;
- rooms;
- objects;
- devices;
- spatial relationships;
- social relationships;
- current activities;
- routines;
- temporal context;
- active situations.

It consumes events and emits versioned state changes. It does not own raw sensor drivers, model weights or safety authority.

## 7. Memory and Knowledge Ownership

Memory owns durable experiences and retrieval. Knowledge owns structured concepts/facts/relationships and verification state.

Both must preserve:

- provenance;
- confidence/uncertainty;
- temporal validity;
- source identity;
- revision history;
- deletion/retention metadata.

Neither is a safety-authority store.

## 8. Attention Architecture

Attention considers:

- direct addressing;
- identity/relationship;
- event importance;
- safety relevance;
- novelty;
- current goals;
- interaction state;
- social evidence;
- learned routines;
- confidence;
- interruption cost;
- available resources.

Suggested states:

```text
IDLE → OBSERVE → MONITOR → FOCUS → PREPARE → ENGAGE
                  ↘                 ↘
                   COOLDOWN ←────── URGENT
```

State transitions must be testable without requiring a particular LLM.

## 9. Personality Architecture

Personality has three conceptual layers:

### Stable traits

Examples: curiosity, warmth, humor, playfulness, caution.

### Dynamic state

Examples: focused, uncertain, calm, curious, socially engaged.

### Relationship state

Examples: stranger, visitor, acquaintance, friend, family, owner/primary user.

These are semantic state, not merely prompt text.

## 10. Autonomy Scheduling

The autonomy runtime supports multiple clocks:

```text
High frequency:
  sensor/event handling

Medium frequency:
  attention/situation evaluation

Low frequency:
  consolidation/maintenance/curiosity review

Event driven:
  speech, safety events, direct requests, significant change
```

The expensive reasoning model must not run on every sensor tick.

## 11. Reasoning Invocation Policy

A model may be invoked when its expected value exceeds its latency/resource cost and the request is within policy.

Typical candidates:

- ambiguity resolution;
- multi-step planning;
- memory synthesis;
- social reasoning;
- novel situations;
- knowledge conflict analysis;
- tool selection;
- explanations.

Typical non-model responsibilities:

- emergency stop;
- hard actuator limits;
- deterministic sensor thresholds;
- watchdogs;
- safety interlocks;
- low-level control.

## 12. Tool Execution

```text
model proposal
  ↓
schema validation
  ↓
authorization / policy
  ↓
resource checks
  ↓
capability execution
  ↓
result normalization
  ↓
event/audit
  ↓
context update
```

Tools must expose only the capability they are designed to provide. No model receives unrestricted shell, filesystem, database or network authority.

## 13. Data and Schema Evolution

Novi may propose new structures but must use:

```text
need
 ↓
existing-schema check
 ↓
proposal
 ↓
compatibility validation
 ↓
policy review
 ↓
migration plan
 ↓
managed application
 ↓
audit
```

Immutable event history is not rewritten as a convenience.

## 14. Filesystem Boundary

Logical storage classes:

```text
protected/
managed/
temporary/
```

Adaptive components receive explicit capabilities, not arbitrary host filesystem access.

## 15. Database Boundary

Models never receive direct database credentials.

```text
Model
 ↓
Data/Knowledge Service
 ↓
validated operation
 ↓
storage backend
```

This provides authorization, quotas, audit, migration control and backend independence.

## 16. Action Architecture

All physical actions follow:

```text
Reasoning / policy proposal
        ↓
Action Proposal
        ↓
Governance
        ↓
Safety Gateway
        ↓
Capability Adapter
        ↓
ROS 2
        ↓
ros2_control / Nav2 / hardware interface
        ↓
physical system
```

The model proposes semantic intent; it does not generate raw motor commands as the physical authority.

## 17. Safety Architecture

Minimum software controls:

- schema validation;
- authorization;
- capability scoping;
- speed/force constraints;
- restricted areas;
- collision constraints;
- emergency-stop integration;
- battery protection;
- actuator health checks;
- watchdogs;
- timeout/cancellation;
- audit.

Physical safety must be independently capable of disabling hazardous actuation.

## 18. Failure Handling

Every service must define:

- startup failure;
- dependency unavailable;
- model unavailable;
- malformed request;
- timeout;
- cancellation;
- resource exhaustion;
- stale sensor data;
- contradictory evidence;
- hardware fault;
- storage fault;
- security incident.

Unsafe ambiguity fails closed or transitions to the defined safe degraded state.

## 19. Observability

Every consequential autonomous cycle should carry a trace/correlation identity linking, as applicable:

```text
input events
→ context
→ retrieval
→ model calls
→ decisions/proposals
→ policy
→ safety
→ tools/actions
→ result
→ memory/state update
```

Sensitive payloads are redacted or access-controlled according to the privacy architecture.

## 20. Lifecycle

Services should expose:

```text
DISCOVER
 ↓
INITIALIZE
 ↓
READY
 ↓
RUNNING
 ↓
DEGRADED / RECOVERING
 ↓
STOPPING
 ↓
STOPPED
```

Health must be queryable without requiring the primary reasoning model.

## 21. Resource Management

The edge runtime must measure:

- CPU;
- GPU;
- RAM/VRAM/unified memory;
- model load time;
- time to first token;
- model throughput;
- perception latency;
- end-to-end latency;
- thermal state;
- power;
- storage I/O.

NVIDIA's DeepStream documentation also recommends component-level latency measurement when diagnosing pipeline performance, reinforcing the requirement for component-level observability. citeturn0search10

## 22. Mac-to-Edge Contract

Example capability:

```text
Camera
 ├── DevelopmentCamera
 ├── SimulationCamera
 └── EdgeCamera
```

and:

```text
ModelRuntime
 ├── ReferenceRuntime
 └── EdgeRuntime
```

Higher-level autonomy code imports only the capability contract.

## 23. Simulation Contract

Simulation must reproduce the logical semantics of physical sensors and actuators sufficiently for software validation.

Example:

```text
navigate_to(kitchen)
 ↓
simulation executes
 ↓
position/state events
 ↓
world model updates
```

NVIDIA Isaac Sim provides a ROS 2 bridge and currently documents Jazzy as an officially tested/recommended distribution. citeturn0search4turn0search7

## 24. Security Boundary

Protected from adaptive modification:

- safety policy;
- authentication/authorization policy;
- privileged credentials;
- trusted software identity;
- emergency-stop configuration;
- hardware safety limits;
- protected recovery authority.

## 25. Testing Strategy

Required test classes:

### Unit

Pure subsystem behavior, schemas and transformations.

### Integration

Cross-service contracts and event flows.

### Simulation

Autonomous behavior against controlled virtual sensors/worlds.

### HIL / physical

Hardware-dependent, safety-critical and timing-sensitive behavior.

### Failure injection

Crashes, stale data, duplicate events, model failures, storage faults, network loss and safety transitions.

### Long-duration

Memory growth, event growth, thermal drift, repeated recovery and autonomous continuity.

## 26. Architecture Acceptance Criteria

The architecture passes when:

- subsystem boundaries are enforceable;
- contracts are explicit and versioned;
- event/state semantics are testable;
- adaptive components cannot bypass governance/safety;
- models are replaceable;
- development/simulation/edge share logical interfaces;
- provenance survives projection;
- autonomous loops are testable;
- schema evolution is governed;
- physical actions are auditable;
- failures degrade safely;
- recovery is defined;
- privacy/deletion semantics survive replication and recovery.
