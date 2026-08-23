# Perception Implementation Workstream

## Scope

Camera, stereo/depth, object detection, segmentation, tracking and sensor-fusion perception capabilities required by Novi.

## Initial relationship to Brain

The Brain currently contains specialist neural perception contracts and candidate model adapters. This workstream will eventually own the broader robot perception system, including sensor pipelines, calibration, synchronization and fusion.

## Planned documents

- `01_CAMERA_ACQUISITION.md` — live camera pipeline on the Mac body (acquisition, timing, health, world-state delivery)
- `02_FACE_AND_OBJECT_RECOGNITION.md` — object detection + face identity into PersonIdentity tiers (closes gap G4)

## Planned progression

1. Define sensor requirements.
2. Define perception outputs and ownership.
3. Validate camera/stereo pipeline.
4. Benchmark object detection and depth candidates.
5. Add tracking and segmentation only where requirements justify them.
6. Integrate perception into world state.
7. Validate perception under representative physical scenarios.

## Status

**PLANNED.** Brain specialist perception is currently the active precursor. Mac-body acquisition and recognition docs are defined; implementation follows the sequencing in each document.
