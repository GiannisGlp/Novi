# Mac Brain Testing

## Objective

Use the Mac to validate Brain behavior independently of NVIDIA hardware.

## Test categories

- component/contract tests;
- model-adapter tests with deterministic backends;
- scenario tests;
- replay tests;
- failure/degraded-mode tests;
- regression tests;
- stress tests that do not depend on NVIDIA-specific performance.

## Scenario pattern

```text
scenario input
   ↓
Brain
   ↓
structured output
   ↓
expected-result comparison
   ↓
PASS / FAIL
```

## What Mac results can prove

They can establish software correctness, contract integrity, state-machine behavior, deterministic failure behavior and scenario-level logic.

## What Mac results cannot prove

They cannot establish Jetson TensorRT performance, accelerator power/thermal behavior or Orin-vs-Thor suitability.
