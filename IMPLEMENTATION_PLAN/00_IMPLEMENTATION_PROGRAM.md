# Novi Implementation Program

**Status:** ACTIVE  
**Scope:** Entire Novi robot platform

## Purpose

This is the master execution plan for building Novi from validated software architecture into a tested autonomous robot. It is intentionally broader than the Brain and covers every major subsystem and the integration between them.

## Current phase

**Implementation testing / empirical validation.**

The architecture and initial software contracts are established. Brain adapters and deterministic CI validation are in place. The next program objective is to execute real-model experiments, collect reproducible evidence, validate the complete neural workload and then continue through the remaining robot subsystems.

## Global lifecycle

```text
PLAN
  ↓
DESIGN
  ↓
IMPLEMENT
  ↓
UNIT TEST
  ↓
CI PASS
  ↓
REAL TEST
  ↓
BENCHMARK
  ↓
EVIDENCE
  ↓
INTEGRATE
  ↓
SYSTEM VALIDATE
  ↓
ACCEPT
```

## Global development environment

Novi is **Mac-first for development and ordinary testing**. The repository's core tests and deterministic CI must remain runnable without NVIDIA hardware.

NVIDIA hardware is an external validation/deployment environment for real accelerator inference, performance, power, thermal and hardware-specific integration testing. It is not a prerequisite for developing the core architecture.

```text
Mac
 ├── development
 ├── unit tests
 ├── contract tests
 ├── deterministic integration tests
 └── lightweight/local model experiments where practical

NVIDIA hardware
 ├── real neural model execution
 ├── accelerator benchmarking
 ├── power/thermal testing
 ├── Isaac ROS/TensorRT validation
 └── eventual hardware selection
```

## Major workstreams

```text
IMPLEMENTATION_PLAN/
├── 01_BRAIN/
├── 02_PERCEPTION/
├── 03_LOCALIZATION/
├── 04_MAPPING/
├── 05_NAVIGATION/
├── 06_AUTONOMY/
├── 07_CONTROL/
├── 08_HARDWARE/
├── 09_SENSORS/
├── 10_SIMULATION/
├── 11_SAFETY/
├── 12_POWER/
├── 13_COMMUNICATIONS/
├── 14_DEPLOYMENT/
└── EVIDENCE/
```

## Program rules

1. Architecture and contracts define ownership.
2. Models are replaceable capability providers, not hidden authorities.
3. Hardware choices remain open until measured requirements justify a decision.
4. CI validates software correctness; real hardware validates deployment behavior.
5. Every real experiment produces provenance-rich evidence.
6. Failure and degraded behavior are acceptance requirements, not optional polish.
7. Acceptance criteria must be explicit before a workstream is declared complete.
8. Safety and execution authority remain outside neural inference.
9. The implementation plan records intended work; evidence records what actually happened.
10. Decisions that change architecture, model or hardware direction require an explicit decision record.

## Current priority

Complete the Brain real-model validation plan first because it provides the perception/reasoning infrastructure required by later autonomy work. Do not interpret this priority as making the Brain the entire robot architecture.

## Program completion

Novi is not complete when all source files exist. The program completes only when the integrated robot satisfies its system acceptance criteria in representative physical scenarios, including degraded and failure conditions.
