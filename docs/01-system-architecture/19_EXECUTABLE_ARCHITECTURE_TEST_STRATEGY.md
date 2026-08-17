# 19 — Executable Architecture Test Strategy

**Status:** Normative architecture validation
**Priority:** P1 — required before architecture freeze

## 1. Purpose

Architecture is not considered validated because a document contains a design. Each critical architectural invariant must map to an executable verification method.

The required chain is:

```text
ARCH-REQ
   ↓
ARCH-DESIGN
   ↓
CONTRACT
   ↓
TEST
   ↓
EVIDENCE
   ↓
PROMOTION DECISION
```

## 2. Test Classes

### A. Contract tests

Verify canonical schemas, versions, required fields, validation rules, and compatibility.

### B. Unit tests

Verify deterministic domain logic such as reducers, policy evaluation, attention transitions, state machines, and normalization.

### C. Integration tests

Verify event flows, service boundaries, model adapters, storage adapters, ROS interfaces, and tool execution.

### D. Simulation tests

Verify end-to-end autonomy against simulated sensors, robot state, navigation and faults.

### E. Hardware-in-loop tests

Verify Jetson/runtime/driver integration while physical actuators remain controlled or isolated.

### F. Physical safety tests

Verify emergency stop, actuator limits, watchdogs, collision protection and failure states under controlled procedures.

### G. Soak tests

Verify sustained operation, resource growth, memory pressure, thermal behavior, queue behavior and recovery.

## 3. Architecture Invariants

The following must become automated gates.

| ID | Invariant | Minimum test |
|---|---|---|
| ARCH-001 | Model cannot directly invoke hardware | dependency/static analysis test |
| ARCH-002 | Physical actions pass policy and safety | integration test |
| ARCH-003 | Safety does not depend on LLM availability | fault-injection test |
| ARCH-004 | Durable critical mutations are attributable | event contract test |
| ARCH-005 | Committed events are immutable | storage integration test |
| ARCH-006 | Derived data cannot become authoritative implicitly | persistence contract test |
| ARCH-007 | Provenance survives projection | provenance integration test |
| ARCH-008 | Model implementations are replaceable | adapter contract test |
| ARCH-009 | Mac/simulation/Jetson share logical contracts | conformance suite |
| ARCH-010 | Offline core continues operating | network-isolation test |
| ARCH-011 | Revoked authority cannot authorize new consequential action | authorization test |
| ARCH-012 | Stale state cannot bypass safety | stale-state test |
| ARCH-013 | Duplicate events do not duplicate logical effects | idempotency test |
| ARCH-014 | Unknown external outcome is represented as unknown | failure-injection test |
| ARCH-015 | Historical corrections do not rewrite provenance | event-history test |
| ARCH-016 | Schema incompatibility blocks unsafe promotion | schema test |
| ARCH-017 | Resource budgets are measurable and enforceable | resource test |
| ARCH-018 | Recovery validates policy and authority before resume | recovery test |
| ARCH-019 | Privacy deletion cannot be defeated by stale replicas | lifecycle test |
| ARCH-020 | Significant autonomous cycles are traceable | observability test |

## 4. Static Architecture Checks

The repository should eventually contain automated checks for forbidden dependencies such as:

```text
LLM → motor driver
LLM → database credentials
LLM → unrestricted filesystem
LLM → GPIO
Web UI → database
Web UI → ROS hardware
Personality → safety policy implementation
Memory → motor controller
```

Static checks should be complemented by runtime tests. Static analysis cannot prove runtime isolation by itself.

## 5. Contract Conformance

Every implementation of a canonical interface must pass the same conformance suite.

Example:

```text
CameraContract
 ├── MacCamera       ✓
 ├── SimulatedCamera ✓
 └── JetsonCamera    ✓
```

Likewise:

```text
ModelRuntime
 ├── LocalModelRuntime
 ├── SimulatedModelRuntime
 └── JetsonModelRuntime
```

## 6. Offline Test

The offline profile must disable:

- Wi-Fi;
- Bluetooth;
- external network routes;
- cloud model APIs;
- external knowledge APIs;
- remote telemetry.

The test then verifies that core Novi functions remain available:

```text
perception
world model
memory
knowledge
attention
personality
local reasoning where configured
local interaction
safety
local diagnostics
physical capability within authorization envelope
```

Optional capabilities must degrade explicitly rather than causing hidden failure.

## 7. Model Failure Test

The reasoning model must be forcibly terminated during normal autonomy.

Expected behavior:

```text
model unavailable
      ↓
agent runtime = degraded
      ↓
deterministic safety continues
      ↓
non-LLM capabilities continue
      ↓
physical action restricted according to policy
      ↓
recovery / restart
```

The system must never enter an unsafe state merely because the model process crashed.

## 8. Sensor Failure Test

For each safety-relevant sensor:

```text
healthy
 ↓
stale
 ↓
missing
 ↓
contradictory
```

The architecture must define the resulting state.

A missing sensor must never silently become a zero-valued or apparently valid measurement.

## 9. Storage Failure Test

Inject:

- write failure;
- partial write;
- corrupted projection;
- unavailable database;
- full disk;
- restart during commit.

Verify that critical state is either recovered or explicitly degraded, never silently fabricated.

## 10. Concurrency Test

Concurrent operations must exercise:

- optimistic version conflicts;
- duplicate requests;
- stale reads;
- write-write conflicts;
- policy changes during action authorization;
- memory correction during retrieval;
- schema version changes during writes.

## 11. Recovery Test

At minimum:

```text
start operation
 ↓
checkpoint
 ↓
crash
 ↓
restart
 ↓
restore
 ↓
validate
 ↓
resume or safely abort
```

Repeat with an external side effect whose final result is deliberately made unknown to Novi.

## 12. Simulation Promotion Gate

No new physical autonomous behavior should progress to hardware merely because unit tests pass.

Promotion requires:

```text
Unit
 ↓
Integration
 ↓
Simulation
 ↓
Fault injection
 ↓
HIL
 ↓
Controlled physical test
```

A failure at a lower level blocks promotion.

## 13. Performance Tests

Every runtime profile must record:

- event latency;
- perception latency;
- attention latency;
- retrieval latency;
- model TTFT;
- model throughput;
- tool latency;
- action planning latency;
- end-to-end interaction latency;
- CPU;
- GPU;
- memory;
- storage;
- power;
- thermal state.

Novi must store the software/hardware tuple alongside benchmark results.

## 14. Soak Test

The Jetson target must eventually run a sustained workload representative of autonomous operation.

The soak test must measure:

- memory growth;
- queue growth;
- storage growth;
- model stability;
- sensor drops;
- thermal throttling;
- CPU/GPU saturation;
- recovery count;
- event-log growth;
- latency drift.

## 15. Evidence Requirements

A passing result must include:

```text
Test ID
Git commit
Hardware
Software tuple
Configuration
Input scenario
Expected result
Observed result
Logs/trace reference
Timestamp
Pass/fail
Reviewer or automated gate
```

A screenshot without the configuration tuple is insufficient for a reproducibility claim.

## 16. Architecture Freeze Rule

Architecture can be marked **validated** only when every P1 invariant has either:

1. a passing automated test; or
2. an explicitly documented reason why the test cannot yet be executed, together with an owner, dependency, and implementation gate.

This distinction prevents documentation from pretending that an unimplemented capability has been validated.
