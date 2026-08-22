# 18 — World Model
> **⚠️ SUPERSEDED** — Canonical implementations now live in `MAC_BRAIN/` (see `MAC_BRAIN/PERFECTING_PLAN/`). This document is retained for historical reference only.


**Status:** SUPERSEDED — legacy Brain source document  
**Canonical owner:** `03-cognition/02_WORLD_MODEL.md`

## Purpose of this file

This file was originally written as a Brain-level World Model specification. The repository-wide architecture audit determined that this created a competing semantic authority.

The canonical semantic World Model now lives in:

`docs/03-cognition/02_WORLD_MODEL.md`

## Boundary

```text
Brain
  → sensor/model runtime, synchronization, embodied evidence and execution

Cognition / World Model
  → current semantic representation of the world

Memory / Knowledge
  → historical experience and durable knowledge

Autonomy
  → goal pursuit and behavioral decisions
```

Brain must not define a second World Model.

## Material disposition

The former Brain specification contained useful requirements around:

- epistemic categories;
- world-state provenance;
- spatial and temporal state;
- prediction;
- active perception;
- imagination/counterfactual boundaries;
- action-outcome grounding;
- prediction error;
- current-state vs memory separation.

Those requirements have been consolidated into the canonical Cognition World Model where they belong.

## Migration rule

Do not extend this document with new semantic World Model requirements.

If a requirement concerns runtime execution, sensor/model pipelines, embodied state integration or scheduling, place it in the appropriate Brain runtime document.

If it concerns semantic world representation, update `03-cognition/02_WORLD_MODEL.md`.

## Historical preservation

The complete pre-consolidation specification remains available in Git history for provenance and recovery. This file intentionally remains as the stable pointer so existing references do not silently become authoritative.
