# 10 — Cross-Modal Memory

**Status:** CANONICAL — CONSOLIDATED V1

## Purpose
Define how Novi fuses and preserves evidence from text, vision, audio, spatial sensors, structured data and other modalities.

## Core principle

```text
MODALITY-SPECIFIC EVIDENCE
        ↓
COMMON EVENT / ENTITY REFERENCES
        ↓
FUSION
        ↓
MULTIMODAL MEMORY
```

Fusion must not erase modality provenance.

## Evidence model

Each modality-specific artifact retains source, timestamp, spatial context, quality, transformations, model/version and content reference. Derived embeddings and summaries point back to source evidence.

Multimodal foundation-model research supports treating vision, language and other modalities as distinct but composable evidence channels; Novi therefore avoids collapsing raw evidence into an opaque single representation. citeturn0academia24

## Alignment

Fusion requires temporal, spatial, entity and semantic alignment. Misaligned timestamps, coordinate frames, identities or sampling rates must be explicit uncertainty rather than silently corrected.

## Fusion levels

- early: raw/feature-level fusion;
- intermediate: aligned representations;
- late: decision/evidence fusion;
- post-hoc: derived memory linking.

The selected level is task-specific.

## Independence

Two modalities are not automatically independent. Multiple outputs may share the same model, sensor, source or upstream artifact. Evidence independence must be represented explicitly.

## Conflicts

Cross-modal disagreement is first-class:

```text
VISION ≠ AUDIO
SENSOR ≠ USER
MODEL A ≠ MODEL B
```

The system classifies disagreement before resolving it. `03` provides provenance/trust; `05` provides semantic belief revision.

## Missing modalities

Absence of one modality is not negative evidence unless the observation process makes that inference valid.

## Privacy

Multimodal data can expose sensitive identity, location, voice and behavioral information. Data minimization and derivative deletion follow `14` and `111`.

## Safety invariants

1. Never erase modality provenance during fusion.
2. Never treat agreement as independent corroboration without checking dependencies.
3. Preserve uncertainty and missingness.
4. Keep model-derived observations distinct from raw sensor evidence.
5. Preserve source links through summaries and embeddings.
6. Apply privacy policy to derived multimodal representations.

## Integration

`06` resolves entities across modalities. `07/08` align time and space. `09` can consume multimodal evidence for causal hypotheses. `11` evaluates skills involving multimodal competence. `104/13` govern model changes that alter fusion behavior.