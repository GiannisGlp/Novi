# 23 — Observability & Diagnostics Architecture

**Status:** P0 normative system architecture
**Owner:** System Architecture
**Scope:** observability, diagnostics, tracing, health, evidence and failure investigation across Novi

## 1. Purpose

Novi must be diagnosable as a distributed embodied system before physical autonomy is trusted.

The system must let engineers answer:

- What happened?
- When did it happen?
- Which component produced it?
- Which version/configuration was active?
- What did Novi believe at the time?
- What action was proposed?
- What safety decision was made?
- What physically happened?
- Why did the behavior degrade or fail?

Observability is therefore a **system capability**, not a logging feature.

## 2. Core principle

> Every consequential behavior must be reconstructable from timestamped, correlated evidence without relying on undocumented inference.

## 3. Observability layers

```text
Hardware telemetry
      ↓
Runtime health
      ↓
Sensor / perception diagnostics
      ↓
Cognition diagnostics
      ↓
Autonomy diagnostics
      ↓
Safety / authorization diagnostics
      ↓
Action execution / outcome
      ↓
Persistent evidence and replay
```

## 4. Three pillars

### Metrics

Numerical measurements for health and performance:

- CPU/GPU utilization;
- memory;
- thermal state;
- power;
- latency;
- queue depth;
- dropped frames;
- inference rate;
- sensor rates;
- action success/failure;
- safety interventions.

### Logs/events

Structured events describing state changes, failures, decisions and lifecycle transitions.

### Traces

Correlation across a complete causal path:

```text
sensor observation
 → perception
 → evidence
 → cognition
 → autonomy
 → action proposal
 → safety decision
 → controller
 → actuator
 → outcome
```

## 5. Correlation model

Every consequential flow should carry:

```text
trace_id
span_id
correlation_id
causation_id
request_id where applicable
robot_id
component_id
contract_id
schema_version
configuration_id
model_id/model_version where applicable
timestamp semantics
```

Correlation IDs must survive domain boundaries unless there is a documented security/privacy reason not to propagate them.

## 6. Structured events

Human-readable logs are useful for development, but canonical diagnostic records must be structured.

Minimum fields:

```text
occurred_at
recorded_at
component
severity
event_type
status
message
correlation_id
causation_id
contract_id
schema_version
configuration_id
failure_code where applicable
```

Free-form text must never be the only record of a safety-critical event.

## 7. Severity

A common severity taxonomy should be used:

```text
TRACE
DEBUG
INFO
NOTICE
WARNING
ERROR
CRITICAL
EMERGENCY
```

Severity must describe operational impact, not developer opinion.

## 8. Health model

Every major subsystem should expose a machine-readable health state:

```text
UNKNOWN
STARTING
HEALTHY
DEGRADED
FAILED
RECOVERING
DISABLED
SAFE_STOP
```

Health state must include evidence and freshness.

## 9. Health is not a boolean

Avoid:

```text
camera_ok = true
```

when the real state may be:

```text
camera connected
frames arriving
frame rate degraded
exposure abnormal
timestamp uncertainty elevated
semantic perception unavailable
```

Health should distinguish transport, data quality and semantic capability.

## 10. Diagnostics by domain

### Brain

Expose:

- scheduler latency;
- queue pressure;
- model lifecycle;
- resource state;
- runtime faults;
- process/container health;
- dropped work;
- deadline misses.

### Cognition

Expose:

- active cognitive task;
- evidence sources;
- uncertainty;
- model selection;
- reasoning latency;
- prediction error;
- context construction;
- degraded cognitive capabilities.

### Memory/Knowledge

Expose:

- retrieval latency;
- admission/rejection;
- provenance failures;
- storage errors;
- index health;
- stale/corrupt records;
- consolidation state.

### Autonomy

Expose:

- active goals;
- plan state;
- interruptions;
- replanning;
- action proposals;
- blocked reasons;
- behavioral state transitions.

### Safety

Expose:

- authorization decisions;
- denied actions;
- constraint violations;
- watchdog events;
- emergency stops;
- degraded safety state.

### Hardware

Expose:

- sensor health;
- actuator health;
- battery/power;
- temperature;
- motor/controller faults;
- communications;
- physical safety state.

## 11. Decision observability

For consequential decisions, Novi must preserve the decision context required to reconstruct the decision without requiring hidden chain-of-thought.

Store structured evidence such as:

```text
input identifiers
relevant observations
selected model/capability
model version
confidence/uncertainty
candidate action
constraints considered
safety result
final action
outcome
```

Do not require storage of private internal reasoning traces merely to achieve auditability.

## 12. Model observability

Every production model invocation should be attributable to:

- model identity;
- model version/digest;
- runtime version;
- input schema version;
- output schema version;
- hardware/accelerator;
- latency;
- resource usage;
- result status;
- fallback/degradation path.

Model confidence must not be treated as truth.

## 13. Sensor observability

For every critical sensor stream track:

- nominal frequency;
- observed frequency;
- timestamp quality;
- dropped samples;
- sequence gaps;
- latency;
- calibration/version;
- health;
- frame/coordinate identity where relevant.

A perception failure should be distinguishable from a sensor transport failure.

## 14. Action observability

Every consequential action should produce:

```text
proposal
 → authorization
 → execution request
 → controller acceptance/rejection
 → physical execution evidence
 → outcome
```

The system must distinguish:

```text
requested
accepted
started
completed
failed
cancelled
interrupted
unknown
```

## 15. Failure codes

Subsystems should use stable machine-readable failure codes.

Example families:

```text
TIME_*
SENSOR_*
PERCEPTION_*
MODEL_*
MEMORY_*
COGNITION_*
AUTONOMY_*
SAFETY_*
CONTROL_*
HARDWARE_*
RESOURCE_*
DEPLOYMENT_*
CONTRACT_*
```

Codes must remain documented and versioned.

## 16. Resource and performance diagnostics

Observability must expose the budgets defined by the runtime resource architecture:

- deadline misses;
- CPU/GPU saturation;
- memory pressure;
- queue growth;
- thermal throttling;
- power constraints;
- inference latency;
- degraded-mode activation.

A performance problem must be diagnosable without guessing from user-visible behavior alone.

## 17. Distributed tracing

If Novi is deployed across multiple processes or machines, tracing should follow causal work across:

```text
sensor process
 → ROS 2 transport
 → perception process
 → cognition process
 → autonomy process
 → safety process
 → controller
```

Trace propagation must be compatible with the canonical contract correlation model.

## 18. Event bus diagnostics

The event system must expose:

- producer;
- consumer;
- event rate;
- queue depth;
- delivery latency;
- dropped events;
- retries;
- dead-letter/recovery state where used.

Events must not disappear silently.

## 19. Replay

Novi requires a deterministic-enough diagnostic replay capability for supported scenarios.

A replay package should contain, as permitted:

```text
sensor/evidence inputs
clock configuration
configuration IDs
model identities
contract versions
relevant memory snapshot/version
policy/safety configuration
runtime versions
observed outputs
expected/actual outcomes
```

Replay must clearly identify which components are deterministic and which are not.

## 20. Simulation and physical replay

Simulation and physical logs must use compatible contract semantics.

A simulation trace must identify:

```text
simulation_time
wall_time
simulator_version
scene/version
robot configuration
model versions
```

Physical traces must identify hardware configuration and calibration versions.

## 21. Privacy

Observability may contain highly sensitive information, including audio, images, transcripts, locations and interaction history.

Therefore:

- collect only what is necessary;
- classify sensitive records;
- apply retention rules;
- protect access;
- redact where possible;
- separate debugging evidence from ordinary product data;
- never assume logs are harmless.

Security/privacy classification follows the canonical contract and governance architecture.

## 22. Security

Diagnostic channels must be authenticated and access controlled where they cross trust boundaries.

Never expose unrestricted actuator controls through a diagnostics interface.

Diagnostics are observational unless explicitly authorized through the canonical control/safety path.

## 23. Storage and retention

Observability data should be categorized:

```text
ephemeral metrics
short-lived diagnostic logs
structured event history
incident evidence
long-term audit records
```

Retention must be proportional to operational, safety, debugging and privacy requirements.

## 24. Alerting

Alerts should be tied to actionable conditions, not raw metric noise.

Examples:

```text
persistent deadline misses
sensor timestamp degradation
safety intervention rate increase
thermal throttling
memory corruption
model crash loop
localization loss
controller rejection
contract incompatibility
```

Alerts must identify severity and recommended recovery path where known.

## 25. Startup diagnostics

Before enabling autonomous behavior, Novi should validate:

- configuration integrity;
- contract compatibility;
- model availability;
- sensor health;
- actuator health;
- time synchronization;
- safety controller state;
- resource headroom;
- storage availability;
- required runtime dependencies.

Failure of a required precondition must prevent the affected capability from being enabled.

## 26. Shutdown and crash diagnostics

On controlled shutdown, persist sufficient state to diagnose the final operational interval.

On crash/power loss, recovery should preserve crash evidence where the hardware/storage architecture permits.

The system must distinguish:

```text
clean shutdown
controlled safe-stop
process crash
kernel/OS failure
power loss
hardware reset
unknown termination
```

## 27. Diagnostic ownership

```text
System Architecture
  canonical observability contracts

Brain
  runtime instrumentation

Cognition
  semantic diagnostic context

Memory
  memory/knowledge diagnostics

Autonomy
  behavioral diagnostics

Safety
  authorization and safety evidence

Hardware
  physical telemetry
```

No domain creates a separate incompatible observability protocol.

## 28. NVIDIA integration

Where NVIDIA runtime components are used, Novi should integrate their available profiling and telemetry capabilities rather than inventing parallel GPU diagnostics.

Candidates include NVIDIA Nsight Systems for timeline/performance analysis and NVIDIA DCGM where supported for GPU telemetry in applicable deployments.

NVIDIA tooling remains implementation infrastructure; Novi's canonical diagnostic semantics remain system-owned.

## 29. Minimum P0 metrics

At minimum, production-capable prototypes should measure:

- end-to-end perception latency;
- perception rate/drop rate;
- cognition latency;
- autonomy decision latency;
- safety decision latency;
- action command latency;
- action outcome latency;
- CPU/GPU/RAM;
- temperature;
- power/battery;
- queue depth;
- event loss;
- sensor freshness;
- localization confidence;
- model failure/fallback count;
- safety intervention count;
- controller rejection count.

## 30. Definition of done

Observability architecture passes when:

- consequential actions are reconstructable;
- all critical components expose health;
- failures have stable identifiers;
- traces cross domain boundaries;
- timestamps use canonical semantics;
- model/configuration versions are attributable;
- resource/deadline failures are visible;
- sensor data quality is measurable;
- safety decisions are auditable;
- replay is possible for defined scenarios;
- privacy/security controls are defined;
- diagnostics cannot bypass safety/control;
- observability itself has bounded resource cost.

## 31. Architectural invariant

> **If Novi cannot explain, from evidence, what happened and why a consequential behavior occurred, that behavior is not ready for trusted autonomy.**
