# Novi Mac Testing Program

## Purpose

The Mac is Novi's primary development and ordinary testing environment. This program defines how Novi is installed, tested, debugged, benchmarked locally and kept aligned with GitHub CI without requiring NVIDIA hardware.

## Scope

- repository development;
- Python/Node toolchains where required;
- deterministic tests;
- Brain scenario testing;
- replayable fixtures;
- local benchmark/evidence generation;
- debugging and coverage;
- CI parity.

## Environment boundary

The Mac validates software correctness and behavior. NVIDIA-specific acceleration, TensorRT/Isaac ROS execution, GPU performance, power and thermal behavior are separate hardware-validation concerns.

## Program lifecycle

```text
SETUP → VERIFY → TEST → REPLAY → BENCHMARK → EVIDENCE → CI PARITY → ACCEPT
```

## Planned workstreams

- `01_MACHINE_SETUP.md`
- `02_TOOLCHAIN.md`
- `03_PYTHON_ENVIRONMENT.md`
- `04_REPOSITORY_SETUP.md`
- `05_TEST_EXECUTION.md`
- `06_BRAIN_TESTING.md`
- `07_SIMULATION.md`
- `08_DATASETS_AND_FIXTURES.md`
- `09_BENCHMARKING.md`
- `10_EVIDENCE_COLLECTION.md`
- `11_DEBUGGING.md`
- `12_CI_PARITY.md`
- `13_TEST_CHECKLIST.md`
- `14_MAC_TEST_ACCEPTANCE_GATE.md`

## Principle

A test that cannot be reproduced from the repository, pinned environment and versioned fixture is not a strong regression test.
