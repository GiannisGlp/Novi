# 05 — Cross-Cutting Requirements

## Purpose

These requirements apply across Novi rather than to one subsystem.

## 1. Reliability

Services must expose health state and recoverable failure behavior. A failed optional capability must not automatically crash the whole robot.

Required states:

```text
STARTING
READY
RUNNING
DEGRADED
RECOVERING
FAILED
STOPPING
STOPPED
```

## 2. Time

All events use synchronized timestamps. The system must distinguish event time from processing time.

Required fields:

```text
event_time
received_time
processed_time
```

Temporal reasoning must use event time wherever possible.

## 3. Identity

Identity results must include confidence and source. Face/voice recognition must not automatically imply authorization.

## 4. Provenance

Durable knowledge and important decisions must preserve source information.

Minimum provenance categories:

```text
sensor_observation
model_inference
user_statement
owner_verification
external_document
system_generated
simulation
```

## 5. Confidence

Confidence must be explicit when information is uncertain. The system must not use a confidence score as a substitute for verification where verification is required.

## 6. Auditability

At minimum, audit:

- model invocation;
- tool invocation;
- knowledge creation/update;
- schema changes;
- privileged actions;
- safety decisions;
- configuration changes;
- authentication/authorization events;
- hardware diagnostics.

## 7. Privacy

Sensitive data should be classified before storage. The system should support retention, deletion, access control, and local-only storage policies.

## 8. Resource Limits

Every autonomous subsystem must have configurable limits for:

- CPU;
- GPU;
- memory;
- storage;
- concurrency;
- queue depth;
- network usage;
- model context;
- action duration.

## 9. Backpressure

High-frequency sensor streams must not be allowed to overwhelm cognitive processing. Queues, sampling, prioritization, and aggregation must be used where necessary.

## 10. Cancellation

Long-running model and tool requests must support cancellation. A stale request must not remain capable of triggering a physical action after its context is invalid.

## 11. Idempotency

Where possible, tools that change external state must accept an operation ID and safely handle duplicate requests.

## 12. Configuration

Configuration should be typed, validated at startup, versioned, and environment-specific. Secrets must not be committed to source control.

## 13. Schema Versioning

Persistent data structures require schema versions and migration strategy. Generated schemas are still governed schemas.

## 14. Compatibility

Interfaces should use explicit versions when breaking changes are possible.

## 15. Testing

Every cross-cutting requirement must have automated validation where practical.

## 16. Performance

Measure rather than assume:

- sensor-to-event latency;
- event-to-attention latency;
- retrieval latency;
- model TTFT;
- model throughput;
- tool latency;
- action planning latency;
- end-to-end response latency.

## 17. Determinism

Tests must be able to reproduce important behavior by controlling clocks, random seeds, simulated sensor data, model settings, and event ordering where feasible.

## 18. Security

Never treat model-generated content as trusted input. Validate all model outputs before using them as commands, SQL, file paths, configuration, or tool parameters.

## 19. Explainability

The system should be able to expose an operational explanation such as:

```text
Observed X
→ retrieved Y
→ attention increased because Z
→ selected tool A
→ policy allowed A
→ safety allowed A
→ action completed
```

This is an audit trail, not a requirement to expose hidden chain-of-thought.

## 20. Upgradeability

Models, runtimes, JetPack versions, ROS 2 distributions, and hardware adapters must be version-pinned and tested before promotion.

## 21. Local-First Requirement

Core operation should not require an external API. Cloud integrations may be optional tools rather than foundational dependencies.

## 22. Data Integrity

Database and file writes must be transactional or atomic where appropriate. Corrupted or partially written data must not silently become authoritative knowledge.

## 23. Graceful Degradation

Example:

```text
VLM unavailable
  → basic detector continues

Nemotron unavailable
  → deterministic functions continue

Knowledge DB unavailable
  → temporary event buffer + safe degradation

Navigation unavailable
  → no movement; report degraded state
```

## 24. Safety Priority

When requirements conflict, safety takes precedence over task completion, personality, curiosity, latency, and convenience.
