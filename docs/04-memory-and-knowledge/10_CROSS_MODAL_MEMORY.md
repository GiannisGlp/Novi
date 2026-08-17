# 10 — Cross-Modal Memory

**Status:** CANONICAL — CONSOLIDATED V1.1

## Purpose
Define how Novi fuses and preserves evidence from text, vision, audio, spatial sensors, structured data and other modalities.

## Core principle

```text
MODALITY-SPECIFIC EVIDENCE
        ↓
COMMON EVENT / ENTITY REFERENCES
        ↓
ALIGNMENT
        ↓
DEPENDENCY ANALYSIS
        ↓
FUSION
        ↓
MULTIMODAL MEMORY
```

Fusion must not erase modality provenance.

## Evidence model

Each modality-specific artifact retains source, timestamp, spatial context, quality, transformations, model/version and content reference. Derived embeddings and summaries point back to source evidence.

## Alignment contract

Fusion requires explicit:

```text
temporal alignment
spatial alignment
entity alignment
semantic alignment
sampling-rate compatibility
model/version compatibility
```

Misaligned timestamps, coordinate frames, identities or sampling rates must remain explicit uncertainty rather than silently corrected.

## Fusion levels

- early: raw/feature-level fusion;
- intermediate: aligned representations;
- late: decision/evidence fusion;
- post-hoc: derived memory linking.

The selected level is task-specific and must be recorded when material to interpretation.

## Evidence dependency and independence

Two modalities are not automatically independent. Multiple outputs may share the same sensor, model, upstream artifact, dataset or preprocessing chain. Evidence should retain dependency/independence groups so corroboration is not artificially inflated.

## Fusion uncertainty

Fusion should preserve at least:

```text
modality_quality
alignment_uncertainty
measurement_uncertainty
source_reliability
dependency_uncertainty
missingness
fusion_uncertainty
```

A fused representation must not appear more certain merely because more correlated signals were combined.

## Conflicts

Cross-modal disagreement is first-class:

```text
VISION ≠ AUDIO
SENSOR ≠ USER
MODEL A ≠ MODEL B
```

The system classifies disagreement before resolving it. `03` provides provenance/trust; `05` provides semantic belief revision.

Possible outcomes include:

```text
AGREEMENT
PARTIAL_AGREEMENT
CONFLICTED
INSUFFICIENT_ALIGNMENT
MISSING_MODALITY
UNRESOLVED
```

## Missing modalities

Absence of one modality is not negative evidence unless the observation process makes that inference valid.

## Current-state arbitration

When modalities disagree about current physical state, arbitration must use domain-specific authority, freshness, calibration, independence and uncertainty. There is no universal sensor-wins rule.

## Privacy

Multimodal data can expose sensitive identity, location, voice and behavioral information. Data minimization and derivative deletion follow `14` and the system erasure architecture.

## Evaluation

Evaluate alignment accuracy, fusion accuracy, uncertainty calibration, conflict detection, missing-modality robustness, common-source double-counting, stale-input handling and privacy leakage. Test both normal agreement and deliberately contradictory modalities.

## Safety invariants

1. Never erase modality provenance during fusion.
2. Never treat agreement as independent corroboration without checking dependencies.
3. Preserve uncertainty and missingness.
4. Keep model-derived observations distinct from raw sensor evidence.
5. Preserve source links through summaries and embeddings.
6. Apply privacy policy to derived multimodal representations.
7. Never manufacture certainty from correlated modalities.

## Integration

`03` provides provenance and uncertainty. `06` resolves entities across modalities. `07/08` align time and space. `09` can consume multimodal evidence for causal hypotheses. `11` evaluates skills involving multimodal competence. `13` governs model changes that alter fusion behavior. `14` governs privacy. `15/16` govern authorization and human escalation.