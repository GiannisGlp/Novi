# Novi Brain Implementation Plan

**Status:** ACTIVE PROGRAM PLAN  
**Scope:** Novi Brain implementation, validation, evidence and hardware selection

## Purpose

This directory is the operational implementation plan for the Novi Brain. It is intentionally separate from architecture specifications and from experimental evidence. Architecture defines what Novi is; this plan defines how we implement and validate it.

## Governing lifecycle

Every implementation unit follows:

```text
PLAN → IMPLEMENT → UNIT TEST → CI PASS → REAL TEST → BENCHMARK → EVIDENCE → INTEGRATE → ACCEPT
```

A passing CI workflow proves software correctness within the deterministic test environment. It does not prove real-model capability, hardware suitability or autonomous-robot readiness.

## Program structure

- `01_IMPLEMENTATION_RULES.md` — mandatory engineering rules.
- `02_IMPLEMENTATION_LIFECYCLE.md` — stage lifecycle and definition of done.
- `03_TESTING_AND_VALIDATION_STRATEGY.md` — test layers and gates.
- `04_EVIDENCE_AND_BENCHMARKING.md` — reproducible experimental evidence.
- `05_HARDWARE_EVALUATION.md` — Orin 64GB vs Thor decision framework.
- `06_FAILURE_AND_DEGRADED_MODES.md` — failure containment and safe degradation.
- `07_ACCEPTANCE_GATES.md` — formal acceptance criteria.
- `B2_NEURAL_CAPABILITY/` — individual B2 implementation workstreams.
- `HARDWARE/` — detailed hardware evaluation workstreams.
- `EVIDENCE/` — evidence schemas, manifests and decision records.

## Current program phase

**Implementation testing / empirical validation.**

The Brain architecture, runtime boundaries, deterministic implementations, CI validation and neural-model adapters are established. The program is now transitioning from architectural implementation into real-model execution, benchmarking and evidence collection.

## B2 high-level sequence

```text
B2.1  Model Runtime                         COMPLETE
B2.2  Nemotron Adapter                      COMPLETE
B2.3  Real Inference Infrastructure         COMPLETE
B2.4  Provenance / Evaluation Harness       COMPLETE
B2.5  Cosmos Reason2 Adapter                COMPLETE
B2.6  Specialist Perception Boundary        COMPLETE
B2.7  Perception Evaluation                 COMPLETE
B2.8  Specialist Model Adapters              COMPLETE

B2.9  Real Neural Evaluation & Evidence      NEXT
B2.10 Nemotron Validation                    PLANNED
B2.11 Cosmos Reason2 Validation              PLANNED
B2.12 RT-DETR Validation                     PLANNED
B2.13 Depth Model Validation                 PLANNED
B2.14 Combined Neural Pipeline               PLANNED
B2.15 Resource / Thermal Validation          PLANNED
B2.16 Failure / Degraded-Mode Validation     PLANNED
B2.17 Orin 64GB Benchmark                    PLANNED
B2.18 Thor Benchmark                         PLANNED
B2.19 Hardware Head-to-Head                  PLANNED
B2.20 Hardware Decision                     PLANNED
B2.21 Full Neural Integration                PLANNED
B2.22 End-to-End Closed-Loop Validation      PLANNED
B2.23 B2 Acceptance Gate                     PLANNED
```

## Hardware decision status

**OPEN.** Jetson AGX Orin 64GB and Jetson AGX Thor are both candidates. No document in this plan may silently convert either candidate into the selected platform before the formal hardware decision gate.

## Model decision status

The current candidate stack is:

- Nemotron 3 Nano Omni — multimodal understanding.
- Cosmos Reason2 — physical/spatiotemporal reasoning.
- RT-DETR — object detection candidate.
- ESS — real-time stereo depth candidate.
- FoundationStereo — higher-quality stereo depth candidate.
- GR00T — future learned robot-skill/policy provider, not the central Brain.

Candidate status does not mean production acceptance. Acceptance requires evidence.

## Relationship to the program tracker

`NOVI_DOCUMENTATION_AND_IMPLEMENTATION_COMPLETION_TRACKER.md` remains the program-level dashboard. This directory contains the detailed execution plan and should be referenced by the tracker rather than duplicating all implementation detail there.

## Change control

If implementation evidence contradicts an assumption in this plan, record the evidence and decision first, then update the relevant plan document. Do not silently rewrite planned acceptance criteria after observing results.
