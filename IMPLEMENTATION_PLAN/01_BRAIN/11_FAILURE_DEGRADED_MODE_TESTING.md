# Brain — Failure and Degraded-Mode Testing

## Objective

Prove that neural failures reduce capability in bounded, observable ways rather than becoming unsafe or silently corrupting world state.

## Required scenarios

- model unavailable;
- model load failure;
- timeout/deadline miss;
- malformed output;
- stale sensor frame;
- invalid confidence/validity;
- memory exhaustion;
- runtime/driver failure;
- thermal throttling;
- conflicting evidence;
- partial pipeline failure.

## Expected behavior

Failures are surfaced, invalid evidence is rejected, provenance remains observable and safety/governance retains authority. The Brain must have bounded fallbacks where the system requirements allow them.

## Mac validation

Implement and execute deterministic failure tests locally and in CI.

## NVIDIA validation

Repeat relevant scenarios with actual model/runtime failures and resource stress.

## Acceptance

No tested neural failure may bypass safety/authority boundaries or silently produce trusted invalid evidence.
