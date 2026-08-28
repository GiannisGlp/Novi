# 07 — LocateAnything

This directory is the canonical Novi research and integration record for NVIDIA LocateAnything.

## Documents

1. `00_SOURCE_INDEX.md` — all primary NVIDIA/upstream sources and authority hierarchy.
2. `01_NVIDIA_RESEARCH.md` — detailed technical analysis of the research contribution, PBD, inference modes, data and benchmarks.
3. `02_MODEL_AND_RUNTIME_SPEC.md` — model architecture, input/output format, runtime, dependencies, deployment paths and compatibility constraints.
4. `03_DATA_TRAINING_EVALUATION.md` — training data schema, task formats, training system, evaluation suite and Novi-specific benchmark requirements.
5. `04_NOVI_INTEGRATION_ANALYSIS.md` — exact architectural fit with the current Novi perception, tracking, world model, memory, prediction, reasoning and safety layers.
6. `05_LICENSE_SECURITY_AND_RISKS.md` — model/code licensing, supply-chain, privacy, safety and operational risks.

## Implementation plan

The implementation plan lives at:

`docs/plans/LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md`

It is deliberately separate from the research documents so that implementation state can be updated without rewriting the research record.

## Recommended architectural role

LocateAnything is a **language-conditioned spatial perception backend**.

It is not:

- Novi's world model;
- memory;
- identity system;
- planner;
- governance layer;
- navigation system;
- actuator controller.

The intended first integration is:

```text
real camera frame
      ↓
Novi perception policy
      ↓
LocateAnything
      ↓
strict parser
      ↓
GroundingObservation
      ↓
tracking / world state
      ↓
memory / prediction / cognition
```

## Important constraints

- Keep SSDLite as the fast baseline.
- Treat Apple MPS support as an experiment; NVIDIA documents H100/A100 testing.
- Keep LocateAnything dependencies optional.
- Pin model revisions.
- Never trust raw model output as world truth.
- Do not infer 3D position from 2D boxes without depth/calibration.
- The currently released LocateAnything-3B model weights are restricted to non-commercial research/evaluation use under NVIDIA's published model license.
- The current released weights do not support visual-prompt inference out of the box, despite upstream worker plumbing for the feature.
