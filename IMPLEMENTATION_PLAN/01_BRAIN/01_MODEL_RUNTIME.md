# Brain — Model Runtime

## Objective

Provide a stable, hardware-neutral runtime boundary through which Novi can load, invoke, monitor and shut down neural capability providers.

## Current state

**IMPLEMENTED / CI VALIDATED.**

## Responsibilities

- model lifecycle;
- backend selection;
- request correlation;
- timeout/deadline handling;
- structured output validation;
- health reporting;
- provenance capture;
- bounded failure behavior.

## Non-responsibilities

The runtime does not decide autonomy, safety authorization or actuator commands.

## Validation

Mac CI validates contracts, lifecycle behavior, invalid outputs and deterministic failure paths. NVIDIA-specific backends are validated separately when hardware is available.

## Acceptance

The runtime is accepted when deterministic tests pass, backend failures are bounded and every production-relevant invocation can be traced to model/runtime/configuration identity.
