# 01 — Detailed System Architecture

## 1. Scope

This document is the detailed system-level specification for Novi. It defines subsystem responsibilities, interfaces, execution flow, state ownership, lifecycle, concurrency expectations, failure handling, and deployment boundaries.

It is intentionally more precise than `00_HIGH_LEVEL_ARCHITECTURE.md` and is the reference document for implementation decisions that affect multiple domains.

## 2. Canonical Runtime Topology

```text
┌───────────────────────────────────────────────────────────────────────┐
│                         NOVI APPLICATION RUNTIME                     │
│                                                                       │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────┐   │
│  │ Event Intake │──▶│ World Model  │──▶│ Attention / Situation   │   │
│  └──────────────┘   └──────┬───────┘   └────────────┬────────────┘   │
│                            │                         │                │
│                            ▼                         ▼                │
│                     ┌──────────────┐        ┌──────────────┐         │
│                     │ Memory / KB  │◀──────▶│ Goal Manager │         │
│                     └──────┬───────┘        └──────┬───────┘         │
│                            │                       │                  │
│                            └──────────┬────────────┘                  │
│                                       ▼                               │
│                              ┌────────────────┐                       │
│                              │ Agent Runtime  │                       │
│                              └───────┬────────┘                       │
│                                      │                                │
│                          ┌───────────▼───────────┐                    │
│                          │  Primary Reasoner     │                    │
│                          │ Nemotron 3 Nano       │                    │
│                          │ 30B-A3B candidate     │                    │
│                          └───────────┬───────────┘                    │
│                                      │                                │
│                           tool/action proposals                       │
│                                      ▼                                │
│                              ┌──────────────┐                         │
│                              │ Policy Layer │                         │
│                              └──────┬───────┘                         │
│                                     │                                 │
│                              ┌──────▼──────┐                          │
│                              │Safety Gate  │                          │
│                              └──────┬──────┘                          │
└─────────────────────────────────────┼─────────────────────────────────┘
                                      │
                               capability calls
                                      │
                           ┌──────────▼──────────┐
                           │      ROS 2 / HW     │
                           └──────────┬──────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
             Sensors               Motion              External
             /audio                /head                systems
```

## 3. Process Boundaries

The implementation should eventually separate components according to risk and performance rather than simply mirroring Python packages.

### 3.1 Application process

Contains:

- autonomy engine;
- world model coordination;
- memory/knowledge services;
- personality/social state;
- goal manager;
- agent runtime;
- non-critical tool orchestration.

### 3.2 Model worker processes

Models may be isolated to manage memory pressure, crashes, model lifecycle, and GPU resource ownership.

Requirements:

- explicit model lifecycle;
- health endpoint/state;
- bounded concurrency;
- request cancellation;
- timeout handling;
- metrics;
- deterministic configuration.

### 3.3 Robotics process graph

ROS 2 nodes own high-frequency robotics behavior and hardware integration.

### 3.4 Safety boundary

The privileged safety implementation must not run as ordinary adaptive application code. The final physical implementation should provide process/permission separation and, where necessary, independent hardware safety mechanisms.

## 4. Event Architecture

All environmental inputs should become normalized events before being consumed by higher-level cognition.

Canonical event shape:

```json
{
  "event_id": "evt_01",
  "timestamp": "2026-08-16T12:00:00Z",
  "source": "vision",
  "type": "person.detected",
  "subject_id": "person_123",
  "location_id": "room_living",
  "payload": {},
  "confidence": 0.94,
  "provenance": {
    "sensor": "camera_front",
    "model": "detector_v1",
    "frame_id": "frame_123"
  }
}
```

Events are append-oriented. Corrections should create new records rather than rewriting the historical observation.

## 5. Observation vs Interpretation

The system must explicitly distinguish:

```text
Observation
  ↓
Evidence
  ↓
Interpretation
  ↓
Hypothesis
  ↓
Fact / verified knowledge
```

Example:

```text
Observation:
A person is holding a mug.

Interpretation:
The person may be drinking coffee.

Hypothesis:
Vano may be drinking coffee in the morning.

Verified fact:
Vano confirmed that he likes morning coffee.
```

These should not be collapsed into one database record.

## 6. World Model Ownership

The world model owns current structured state. It must support versioned state changes and historical reconstruction where required.

Minimum domains:

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

The world model consumes events and emits state-change events.

## 7. Memory Ownership

Memory owns durable experience and learned context.

It must support:

- storage;
- retrieval;
- consolidation;
- deduplication;
- entity resolution;
- temporal queries;
- spatial queries;
- semantic retrieval;
- relationship retrieval;
- provenance;
- confidence;
- verification;
- decay/archival policies.

Memory must never be treated as an authoritative safety source.

## 8. Attention Architecture

Attention should combine:

- explicit user addressing;
- identity and relationship;
- event importance;
- safety relevance;
- novelty;
- current goals;
- current interaction state;
- emotional/social evidence;
- learned routines;
- confidence;
- interruption cost.

Suggested states:

```text
IDLE
OBSERVE
MONITOR
FOCUS
PREPARE
ENGAGE
URGENT
COOLDOWN
```

Transitions must be deterministic enough to test even when model-assisted reasoning is used for scoring or interpretation.

## 9. Personality Architecture

Personality consists of three layers:

### Stable traits

Examples:

- playful;
- curious;
- warm;
- humorous;
- energetic;
- cautious.

### Dynamic internal state

Examples:

- excited;
- focused;
- uncertain;
- curious;
- calm;
- socially engaged.

### Relationship state

Examples:

- stranger;
- visitor;
- acquaintance;
- friend;
- family;
- owner/primary user.

The final response style is derived from all three layers plus current context.

## 10. Autonomy Loop Scheduling

The autonomy runtime should support multiple clocks:

```text
High frequency:
  sensor/event processing

Medium frequency:
  attention and situation evaluation

Low frequency:
  memory consolidation
  routine discovery
  curiosity review
  maintenance

Event driven:
  explicit speech
  safety event
  direct request
  significant environmental change
```

This prevents the expensive reasoning model from running on every sensor tick.

## 11. Reasoning Invocation Policy

Nemotron should be invoked when reasoning provides sufficient value to justify its latency/resource cost.

Examples that may invoke the primary reasoner:

- ambiguous user requests;
- multi-step planning;
- memory synthesis;
- social response generation;
- novel situations;
- knowledge conflicts;
- tool selection;
- curiosity resolution;
- complex explanations.

Examples that should usually avoid the primary reasoner:

- emergency stop;
- simple sensor threshold checks;
- basic object counting;
- battery threshold alarms;
- motor safety limits;
- deterministic navigation control;
- raw speech/audio processing.

## 12. Tool Execution

The model produces structured tool requests. The application validates them before execution.

```text
model
  ↓
ToolRequest schema validation
  ↓
authorization/policy
  ↓
capability execution
  ↓
result normalization
  ↓
model/context update
```

A tool must never expose unrestricted shell, database, filesystem, or network access merely because the model requested it.

## 13. Data Generation and Schema Evolution

Novi may propose new data structures when existing structures cannot represent a recurring concept.

Required pipeline:

```text
Need identified
  ↓
Existing entity/type/attribute check
  ↓
Schema proposal
  ↓
Validation
  ↓
Policy check
  ↓
Migration plan
  ↓
Apply to managed storage
  ↓
Audit
```

Immutable storage is excluded from this process.

## 14. File System Boundary

The logical storage model should include:

```text
protected/
managed/
temporary/
```

The adaptive application receives explicit capabilities for managed and temporary storage. It does not receive unrestricted access to the host filesystem.

## 15. Database Boundary

Models never receive direct database credentials.

Preferred:

```text
Model
  ↓
Knowledge/Data Service
  ↓
validated operation
  ↓
SQLite/PostgreSQL/vector backend
```

This provides:

- validation;
- quotas;
- authorization;
- audit;
- migration control;
- backend independence.

## 16. Action Architecture

All physical actions follow:

```text
Reasoning
  ↓
Action Proposal
  ↓
Policy
  ↓
Safety Gateway
  ↓
Capability Adapter
  ↓
ROS 2
  ↓
Hardware
```

The action proposal should describe intent rather than low-level actuator commands whenever possible.

Example:

```json
{
  "action": "navigate_to",
  "destination": "kitchen",
  "constraints": {
    "speed_limit": "normal",
    "avoid_people": true
  }
}
```

The navigation stack converts the intent into motion commands.

## 17. Safety Architecture

Safety rules are enforced outside the model.

Minimum controls:

- schema validation;
- authorization;
- speed limits;
- collision constraints;
- restricted areas;
- emergency stop;
- battery protection;
- actuator health checks;
- watchdogs;
- timeout handling;
- audit logging.

## 18. Failure Handling

Each service must define:

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
- storage fault.

The default behavior for unsafe ambiguity is to fail closed.

## 19. Observability

Every significant autonomous cycle should have a trace ID linking:

```text
input events
→ context
→ retrieval
→ model calls
→ decisions
→ tool calls
→ policy decisions
→ action
→ result
→ memory update
```

Sensitive content must be redacted or access-controlled according to the privacy domain specification.

## 20. Lifecycle

Services should implement a consistent lifecycle:

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

Health status must be queryable without requiring the main reasoning model.

## 21. Resource Management

The Jetson deployment must treat unified memory as a shared system resource. Model residency should be configurable. Large models may be loaded on demand if benchmarks demonstrate that keeping every model resident harms perception or navigation latency.

The architecture must measure:

- CPU utilization;
- GPU utilization;
- memory usage;
- model load time;
- time to first token;
- tokens/second;
- perception latency;
- end-to-end interaction latency;
- thermal state;
- power consumption.

## 22. Mac-to-Jetson Contract

Mac implementations must implement the same logical contracts as Jetson implementations.

Example:

```text
Camera
 ├── MacCamera
 ├── SimulatedCamera
 └── JetsonCamera
```

Likewise:

```text
ModelRuntime
 ├── MacRuntime
 └── JetsonRuntime
```

The higher-level autonomy code imports only the interface.

## 23. Simulation Contract

Simulation must reproduce the logical semantics of physical sensors and actuators sufficiently for software validation.

A simulated action should generate a result event just as a physical action does.

Example:

```text
navigate_to(kitchen)
  ↓
simulator moves virtual robot
  ↓
robot.position_changed
  ↓
world model updates
```

## 24. Security Boundary

The following are protected from adaptive modification:

- safety policy;
- authentication/authorization policy;
- privileged credentials;
- protected system configuration;
- trusted software identity;
- emergency-stop configuration;
- hardware safety limits.

The model may propose changes to learnable state but cannot directly alter protected state.

## 25. Testing Strategy

The architecture requires four test classes:

### Unit

Pure subsystem behavior and data transformations.

### Integration

Cross-service contracts and event flows.

### Simulation

Autonomous behavior against virtual sensors, environments, and robot state.

### Hardware-in-loop / physical

Safety-critical and hardware-dependent behavior on Jetson and the robot.

## 26. Architectural Acceptance Criteria

The implementation satisfies the system architecture when:

- subsystem boundaries are enforceable;
- event flow is observable;
- no adaptive component bypasses safety;
- models are replaceable behind contracts;
- Mac and Jetson share core interfaces;
- memory/knowledge have provenance;
- autonomous loops are testable;
- schema evolution is governed;
- physical actions are auditable;
- failures degrade safely;
- simulation can exercise the same high-level behavior as the physical system.
