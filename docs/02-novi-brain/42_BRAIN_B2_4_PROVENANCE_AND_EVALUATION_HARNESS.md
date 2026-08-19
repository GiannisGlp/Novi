# B2.4 — Provenance and Evaluation Harness

## Status

IMPLEMENTED — deterministic evaluation baseline.

## Purpose

B2.4 establishes reproducible evidence collection around model inference without making model output a semantic authority. It separates model execution from evaluation and preserves enough provenance to compare model/backend/configuration runs later on Orin 64GB, Thor, workstation, or other supported hardware.

## Architecture

```text
EvaluationCase
      ↓
InferenceEvaluationHarness
      ↓
Model invoker
      ↓
ModelResult
      ↓
checks + output digest + provenance
      ↓
EvaluationResult
```

## Provenance captured

Each evaluation result records:

- invocation ID;
- model ID and version;
- artifact digest;
- runtime;
- backend;
- input/output schema versions;
- latency;
- deterministic output digest.

The artifact digest is especially important for hardware comparisons: the same model artifact must be used when comparing backends or devices.

## Evaluation model

Evaluation cases are explicit and versionable. Each case contains:

- stable case ID;
- modality;
- input fixture/payload;
- expected output properties.

The baseline harness evaluates completion, output presence, provenance and required properties. It returns `PASS` or `FAIL` rather than silently accepting partial output.

## Why this is a gate

A model that loads successfully is not necessarily suitable for Novi. Suitability requires evidence across capability, latency, resource use and failure behavior. B2.4 provides the common evidence format needed for those later measurements.

## Hardware neutrality

No hardware is selected by this stage. The same evaluation case must later run against:

- development Mac backend where supported;
- NVIDIA workstation backend;
- Jetson AGX Orin 64GB candidate;
- Jetson AGX Thor candidate.

Hardware selection remains an evidence-driven decision.

## Robotics evaluation direction

Later B2 evaluation suites should include:

1. image scene interpretation;
2. object identification;
3. spatial relationships;
4. temporal/video understanding;
5. audio events;
6. instruction following;
7. structured scene extraction;
8. uncertainty/abstention behavior;
9. latency deadlines;
10. resource limits;
11. degraded/failure cases.

These cases must use representative robot data rather than generic language benchmarks alone.

## Determinism

The harness uses an output digest to make results comparable. It does not require raw model output to be byte-identical across every backend; numerical generation can legitimately vary. Semantic acceptance criteria should therefore be explicit and versioned.

## Safety boundary

The evaluation harness cannot authorize or execute actions. Model outputs remain evidence/candidate cognition inputs. Any action proposal must continue through Novi's existing authorization and safety boundary.

## Acceptance criteria

- evaluation cases have stable IDs;
- results contain model and artifact provenance;
- output digests are recorded;
- expected-property failures are visible;
- serialized results are structured;
- no action execution path is introduced;
- the harness can be reused by future real-model and hardware benchmarks.

## Next

B2.5 should introduce the physical-reasoning capability evaluation and backend integration for Cosmos Reason2, followed by a combined multimodal/physical reasoning benchmark before the B2 integration gate.
