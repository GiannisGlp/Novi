# B0.5 — Health and Observability Workflow

**Status:** P0 workflow — implementation complete, validation pending  
**Domain:** Brain  
**Stage:** B0 Runtime Foundation  
**Date:** 2026-08-19  
**Predecessor:** `27_BRAIN_B0_4_SCHEDULER_EVENT_RUNTIME_WORKFLOW.md`

## Purpose

Provide the Stage-0 Brain with explicit health, metrics and structured diagnostics without coupling the runtime to a particular external observability vendor.

## Health model

Health checks use four states:

- `PASS` — check is healthy;
- `WARN` — degraded but potentially usable;
- `FAIL` — required capability is unhealthy;
- `UNKNOWN` — no sufficient evidence yet.

Aggregate health precedence is:

```text
FAIL > WARN > PASS > UNKNOWN
```

Health snapshots contain status, detail, individual checks and both wall-clock and monotonic timestamps.

## Metrics

Stage 0 provides a deterministic in-process metric registry with:

- metric name;
- numeric value;
- unit;
- normalized labels;
- deterministic snapshot ordering.

External exporters are intentionally deferred until runtime requirements justify them.

## Diagnostics

Structured diagnostics capture:

- severity (`DEBUG`, `INFO`, `WARN`, `ERROR`);
- message;
- structured context;
- wall-clock time;
- monotonic time.

This keeps operational information machine-readable and avoids making log text the only evidence source.

## Validation requirements

1. healthy checks aggregate to `PASS`;
2. `WARN` is surfaced when no failure exists;
3. `FAIL` dominates aggregate health;
4. invalid health status is rejected;
5. metric snapshots are deterministic;
6. labels are preserved;
7. diagnostics preserve structured context;
8. timestamps are present;
9. implementation remains vendor-neutral.

## Acceptance criteria

B0.5 can be marked **VALIDATED** only after the repository workflow passes against the current `main` revision.

This workflow does not mark B0 or the Brain domain complete.
