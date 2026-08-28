# Perception Implementation Workstream

## Scope

Camera, stereo/depth, object detection, segmentation, tracking, spatial grounding and sensor-fusion perception capabilities required by Novi.

## Initial relationship to Brain

The Brain currently contains specialist neural perception contracts and candidate model adapters. This workstream will eventually own the broader robot perception system, including sensor pipelines, calibration, synchronization and fusion.

## Planned documents

- `01_CAMERA_ACQUISITION.md` — live camera pipeline on the Mac body (acquisition, timing, health, world-state delivery)
- `02_FACE_AND_OBJECT_RECOGNITION.md` — object detection + face identity into PersonIdentity tiers (closes gap G4)
- `../../07-locate-anything/README.md` — NVIDIA LocateAnything research and integration record
- `../LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md` — LocateAnything implementation plan

## LocateAnything relationship

NVIDIA LocateAnything is treated as an **optional language-conditioned spatial-grounding backend**, complementary to the existing SSDLite detector.

- SSDLite remains the fast continuous category detector.
- LocateAnything provides open-vocabulary grounding, referring-expression localization, dense detection and point grounding.
- Both feed Novi-owned typed perception/world-state contracts.
- LocateAnything never directly controls planning, governance or actuators.

## Planned progression

1. Define sensor requirements.
2. Define perception outputs and ownership.
3. Validate camera/stereo pipeline.
4. Benchmark object detection and depth candidates.
5. Evaluate LocateAnything as the language-conditioned grounding candidate.
6. Add tracking and segmentation only where requirements justify them.
7. Integrate perception into world state.
8. Validate perception under representative physical scenarios.

## Status

**PLANNED.** Brain specialist perception is currently the active precursor. LocateAnything research is documented and the implementation plan is ready; implementation starts only after the compatibility and licensing gates in the LocateAnything plan are satisfied.
