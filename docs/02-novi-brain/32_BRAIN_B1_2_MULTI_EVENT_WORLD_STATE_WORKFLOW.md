# B1.2 — Multi-Event World-State and Memory Continuity Workflow

**Status:** P0 workflow — implementation complete, validation pending  
**Domain:** Brain  
**Stage:** B1 Closed Simulated Loop  
**Date:** 2026-08-19  
**Predecessor:** `31_BRAIN_B1_1_CLOSED_SIMULATED_LOOP_WORKFLOW.md`

## Purpose

Move B1 from a single repeated synthetic entity to a deterministic miniature world containing multiple entities, changing state, temporal events and stale observations.

## Scenario

The deterministic world contains:

- `alice` — a person whose location changes;
- `door` — an environment state that opens and closes;
- `object_a` — an object that moves from table to shelf.

The six-cycle scenario produces:

```text
C1  Alice enters living room
C2  Door opens
C3  Object A moves table → shelf
C4  Alice leaves living room
C5  Door closes
C6  Alice returns to living room
```

## Ground truth versus observation

Ground truth is maintained separately from the observed world state. Sensor observations contain source, captured cycle, confidence and state. The Brain must infer/maintain current state from observations rather than receiving ground truth directly.

## Temporal protection

A state update with an older capture cycle than the current entity state is rejected as stale. The stale observation is retained as diagnostic evidence, but it cannot regress current world state.

## Event correlation

Events are represented by deterministic semantic keys and duplicate correlation is suppressed. This establishes the Stage-0/B1 foundation for later multi-modal correlation without pretending that the simulator is already a full probabilistic event-correlator.

## Acceptance criteria

1. multiple entities coexist;
2. entity state changes across cycles;
3. ground truth remains separate from observed state;
4. events are correlated exactly once;
5. stale observations cannot regress current state;
6. stale evidence remains inspectable;
7. final state is deterministic;
8. complete scenario is replayable;
9. observations carry confidence/source/capture metadata;
10. existing B0 safety/runtime boundaries remain intact.

## Non-goals

This workflow does not yet implement a production world model, probabilistic sensor fusion, neural perception, real robot sensors, or durable Memory & Knowledge. Those belong to later workflows.

## Exit condition

B1.2 becomes **VALIDATED** only after the repository workflow passes against the resulting `main` revision.
