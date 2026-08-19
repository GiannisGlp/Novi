# B0.4 — Scheduler and Event Runtime Workflow

**Status:** P0 workflow — implementation complete, validation pending  
**Domain:** Brain  
**Stage:** B0 Runtime Foundation  
**Date:** 2026-08-19  
**Predecessor:** `26_BRAIN_B0_3_SUPERVISOR_LIFECYCLE_WORKFLOW.md`

## Purpose

Establish the deterministic Stage-0 scheduler and event-runtime behavior needed to coordinate Brain work without introducing distributed infrastructure prematurely.

## Design

The Stage-0 scheduler is intentionally synchronous and deterministic. It is an execution substrate, not a final real-time robotics scheduler.

Tasks have:

- stable names;
- explicit priority;
- deterministic ordering (`priority` descending, then task name);
- duplicate-registration rejection;
- failure propagation through a scheduler-specific error;
- execution count;
- runtime event evidence.

The event bus records:

- event type;
- payload;
- correlation ID;
- causation ID where applicable;
- monotonic sequence;
- wall-clock timestamp;
- monotonic timestamp.

## Safety and lifecycle boundary

Scheduler execution must not become an authority for safety. The scheduler coordinates work; the safety gateway remains responsible for authorization decisions, and the supervisor remains responsible for lifecycle state.

A future multi-rate implementation may replace the synchronous scheduler behind the same runtime boundary after timing and hardware requirements are validated.

## Validation requirements

1. priority ordering;
2. deterministic execution order;
3. duplicate task rejection;
4. task failure wrapping;
5. scheduler event emission;
6. execution count;
7. event sequence monotonicity;
8. compatibility with Brain supervisor lifecycle;
9. no bypass of the safety gateway.

## Acceptance criteria

B0.4 can be marked **VALIDATED** only after the repository workflow passes against the current `main` revision.

This workflow does not mark B0 or the Brain domain complete.
