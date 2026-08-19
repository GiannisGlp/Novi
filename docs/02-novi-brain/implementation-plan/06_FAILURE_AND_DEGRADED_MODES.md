# 06 — Failure and Degraded Modes

Autonomous behavior must remain bounded when neural components fail, become slow or return uncertain evidence.

## Failure classes

- model unavailable;
- model load failure;
- malformed output;
- schema mismatch;
- timeout/deadline miss;
- resource exhaustion;
- stale sensor data;
- perception confidence collapse;
- conflicting neural evidence;
- runtime/driver failure;
- thermal throttling;
- communication failure.

## Required behavior

Failures must be explicit and observable. They must not silently become false confidence or unsafe action.

Examples:

```text
Depth unavailable
    ↓
Reduced world-state confidence
    ↓
Constrain autonomy
    ↓
Safe degraded behavior
```

```text
Reasoning model timeout
    ↓
Do not wait indefinitely
    ↓
Use bounded fallback behavior
    ↓
Record degradation event
```

```text
Invalid perception output
    ↓
Reject evidence
    ↓
Do not propagate malformed state
```

## Safety boundary

A neural failure must never directly trigger actuator behavior. Safety/governance remains authoritative.

## Testing

Every major neural capability must have explicit tests for unavailable backend, timeout, malformed output, stale input and resource exhaustion where technically applicable.
