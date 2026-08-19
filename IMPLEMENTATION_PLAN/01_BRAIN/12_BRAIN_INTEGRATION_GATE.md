# Brain — Integration Gate

## Objective

Formally determine whether the validated neural stack is ready to become part of the integrated Novi Brain.

## Required evidence

- model capability evidence;
- latency/throughput evidence;
- resource/thermal evidence;
- provenance evidence;
- concurrent pipeline evidence;
- failure/degraded-mode evidence;
- Mac CI and deterministic test evidence;
- hardware comparison evidence when hardware selection is in scope.

## Integration requirements

1. Neural outputs conform to canonical contracts.
2. Provenance is preserved across the pipeline.
3. No neural component bypasses authority/safety boundaries.
4. Timing/resource budgets are satisfied for the selected deployment configuration.
5. Failures are bounded and observable.
6. Evidence is reproducible from pinned configurations.

## Gate status

**OPEN.**

The gate is not passed merely because adapters and CI tests pass. It requires real-model and system-level evidence.
