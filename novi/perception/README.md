# Novi Perception — Camera, Objects & Face Identity

Implementation of [`docs/plans/02_PERCEPTION/01_CAMERA_ACQUISITION.md`](../../docs/plans/02_PERCEPTION/01_CAMERA_ACQUISITION.md) and [`docs/plans/02_PERCEPTION/02_FACE_AND_OBJECT_RECOGNITION.md`](../../docs/plans/02_PERCEPTION/02_FACE_AND_OBJECT_RECOGNITION.md): real visual input for the brain on the Mac body — camera acquisition, object detection, tracking-lite, and tiered face identity — closing the face half of gap **G4** (identity providers) from the 2026-08-23 audit.

Like `novi/voice/`, this package is **self-contained**: it imports brain contracts (`CameraFrame`) read-only, and nothing in `novi.brain` depends on it. Engine integration is deliberately deferred until the parallel brain workstream lands.

## Package layout

```text
novi/perception/
├── __init__.py        Lazy exports (package importable module-by-module)
├── camera.py          CameraFeed — bounded queue, health, freshness
├── detection.py       Detection contract + DeterministicObjectDetector
├── tracking.py        ObjectTracker — IoU association + hysteresis
├── faces.py           FaceIdentifier — tiers, ambiguity refusal, privacy gate
├── pipeline.py        PerceptionPipeline — one call per frame
└── tests/
    ├── test_camera.py            (10)
    ├── test_detection.py         (6)
    ├── test_tracking.py          (8)
    ├── test_faces.py             (11)
    ├── test_pipeline.py          (5)
    └── test_fusion_scenario.py   (2)  ← doc-02 §3 acceptance scenario
```

43 tests total. Fully deterministic: no hardware, no threads in CI paths (the only thread lives behind `CameraFeed`'s scripted-provider tests), no model downloads.

## Data flow

```text
capture thread ──► bounded drop-oldest queue ──► poll() -> FrameRecord
                                                      │
                                     process_frame(rec.frame [, face_embedding])
                                                      │
                              ObjectDetector.detect(frame) -> [Detection]
                                                      │
                              ObjectTracker.update(dets) -> active [Track]
                                                      │                     └─► WorldObservation
                              FaceIdentifier.observe(embedding)              (detections+tracks+
                                                      │                       identities, all
                                                      ▼                       provenance-stamped)
                                        IdentityDecision{tier}
```

## Module reference

### `camera.CameraFeed`

Wraps any `CameraProvider` (`open/read/close` protocol; AVFoundation/OpenCV backend later):

- **Own capture thread** with a bounded queue; consumers `poll()` non-blocking — the cognitive loop never waits on camera I/O.
- **Drop-oldest under pressure**, counted in `.dropped` — drops are telemetry, never silent loss.
- **Health state machine**: `UNKNOWN → AVAILABLE → DEGRADED` (first failure) `→ FAILED` (sustained) `→ AVAILABLE` on recovery (counted in `.recoveries`) `→ OFFLINE` on stop. These states feed the hardware-health view (hardware docs §20).
- **Freshness**: `FrameRecord.age_s()` / `is_stale()` and feed-level `is_stale()` implement stale-vision handling — "currently visible" decays when frames stop arriving.

### `detection.Detection` / `DeterministicObjectDetector`

Frozen dataclass: `label`, `confidence ∈ [0,1]`, integer pixel bbox `(x,y,w,h)`, mandatory `frame_id` provenance (validated at construction).

The deterministic detector serves scripted detections keyed by frame id with a configurable confidence floor. Real backends — **SSDLite320 MobileNetV3** (README M1 primary), RT-DETR / YOLO-nano (benchmark-gated) — implement the same `ObjectDetector` protocol.

### `tracking.ObjectTracker`

Tracking-lite: no Kalman, no re-ID.

- **IoU-greedy association** across consecutive frames keeps one track id per physical object; first/last frame ids and hit/miss counters feed world-state `last_seen` decay.
- **Hysteresis**: `min_hits` before a track is *confirmed*, `max_age_frames` of misses before expiry into `lost_tracks` — no flicker at the confidence boundary.
- **Label stability**: a different label heavily overlapping an existing track raises (`label flip`) instead of silently spawning a duplicate or corrupting identity.

### `faces.FaceIdentifier`

Embedding-match identity with tiered trust:

| Tier | Meaning | Trigger |
|---|---|---|
| `UNKNOWN` | seen but not identified | below match bar — includes explicit **ambiguous** band (`tau_ambig ≤ sim < tau_match`) where Novi refuses to guess |
| `RECOGNIZED` | matched an enrolled person | cosine ≥ `tau_match` |
| `VERIFIED` | cross-modal confirmation | recognized **and** speaker person id agrees |

Rules that matter:

- **No-match → proposal, not guess**: unknown faces return `new_person_proposal=True`; enrollment happens conversationally upstream, never as a silent biometric write here.
- **Speaker disagreement holds** at RECOGNIZED (never escalates on conflict); verification requires the diarization→person binding to agree. The face gate wins: a stranger's face claiming Anna's speaker id stays UNKNOWN.
- **Privacy gate**: `set_privacy(False)` refuses all enrollment/observation (`PermissionError`) and audits every transition (`privacy-enabled`/`privacy-disabled` + reason). Detection/tracking continue without biometrics.
- Embeddings are plain vectors compared by cosine today; ArcFace-class backends slot in unchanged.

### `pipeline.PerceptionPipeline`

One call per frame: `process_frame(frame, face_embedding=None, speaker_person_id=None) -> WorldObservation`.

The observation carries detections, this frame's active tracks, and identity decisions — every element stamped with the frame id, so downstream world-state admits keep full provenance chains (feeding exit-contract B3 requirement 3, spatial/temporal binding / G7). Privacy-off disables only the face stage; objects are still seen. `snapshot()` exposes frames-processed, track table, and privacy state for web observers.

## The fusion acceptance scenario

`tests/test_fusion_scenario.py` runs doc-02 §3 deterministically:

1. Kitchen scene: cup + book detected and tracked; nobody identified.
2. Anna appears far/blurry → similarity 0.82 lands in the ambiguous band → **stays UNKNOWN** (never best-guesses).
3. Closer → exact embedding → **RECOGNIZED** as enrolled Anna.
4. She speaks → speaker binding agrees → **VERIFIED**.
5. Through all beats the cup keeps its single original track id; a total stranger yields `new_person_proposal` instead of an identity.

This is the perception half of SCENARIO-V1's promise; the voice package owns the turn-taking half.

## Integration boundaries (deliberately not done)

- **No engine wiring**: `BrainDriver` does not consume this package yet — integration starts after the parallel brain workstream settles. The seam will be world-state entity admits fed by `WorldObservation`.
- **No real camera backend**: AVFoundation/OpenCV provider implements `CameraProvider` next; CI keeps the scripted providers regardless (deterministic fallback rule of the regression wall).
- **No real detectors/embedders**: SSDLite/ArcFace-class models arrive as evidence-run validation per repo rules ("a candidate becomes official only after successful execution on the actual Mac").

## Resource parity (exit-contract rule)

SSDLite320, ArcFace-class embeddings, and IoU tracking all map to Orin/Thor-plausible deployments (TensorRT/onnx); embeddings stay small (≤512-d). No cloud vision APIs anywhere.

## Running

```bash
.venv/bin/python -m pytest novi/perception/tests -q                       # 43 tests
.venv/bin/python -m pytest novi/perception/tests/test_fusion_scenario.py -v   # the scenario
```

Full-suite status at implementation time: **1,489 passed** (perception + voice + entire pre-existing suite), zero regressions.
