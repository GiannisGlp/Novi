# Novi Perception — Camera, Objects, Face Identity & Language Grounding

Implementation of [`docs/plans/02_PERCEPTION/01_CAMERA_ACQUISITION.md`](../../docs/plans/02_PERCEPTION/01_CAMERA_ACQUISITION.md) and [`docs/plans/02_PERCEPTION/02_FACE_AND_OBJECT_RECOGNITION.md`](../../docs/plans/02_PERCEPTION/02_FACE_AND_OBJECT_RECOGNITION.md): real visual input for the brain on the Mac body — camera acquisition, object detection, tracking-lite, tiered face identity, and optional language-conditioned spatial grounding (NVIDIA LocateAnything, see [`docs/plans/LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md`](../../docs/plans/LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md)) — closing the face half of gap **G4** (identity providers) and the grounding half of the LocateAnything plan from the 2026-08-23 audit.

Like `novi/voice/`, this package is **self-contained**: it imports brain contracts (`CameraFrame`) read-only, and nothing in `novi.brain` depends on it. Engine integration is deliberately deferred until the parallel brain workstream lands.

## Package layout

```text
novi/perception/
├── __init__.py        Lazy exports (package importable module-by-module)
├── camera.py          CameraFeed — bounded queue, health, freshness
├── detection.py       Detection contract + DeterministicObjectDetector
├── tracking.py        ObjectTracker — IoU association + hysteresis
├── faces.py           FaceIdentifier — tiers, ambiguity refusal, privacy gate
├── pipeline.py        PerceptionPipeline — one call per frame (+ optional ground_frame)
├── grounding.py       SpatialQuery/GroundingObservation/GroundingResult/... typed contracts
├── locate_anything_geometry.py   [0,1000] source-coordinate validation + pixel conversion
├── locate_anything_parse.py      strict NVIDIA token parser (<ref>/<box>/none)
├── locate_anything.py            LocateAnythingBackend + DeterministicLocateAnythingBackend
├── locate_anything_runtime.py    optional runtime boundary (lazy torch/transformers)
├── grounding_association.py      grounding -> track association (candidates, never invented)
├── active_grounding.py           escalation policy, budgets, dedup, short-term cache
├── grounding_verification.py     re-observation agreement (plan Step 9.2 geometry)
├── world_state_adapter.py        GroundingOutcome -> world-model admission (Step 18, protocol-based)
├── prediction_verification.py    predicted-presence verification via grounding (Step 21)
├── deliberation_record.py        ambiguity decision record, plan Step 7.4 schema (Step 22)
├── spatial_memory_promotion.py   durable-memory promotion criterion (Step 24)
├── benchmark_metrics.py          IoU@k, center error, P/R/FP/FN, latency percentiles
├── benchmark_corpus.py           versioned eval-set loader/validator (corpus-v1.json)
├── benchmark.py                  run_grounding_benchmark -> BenchmarkReport
├── benchmark_compare.py          SSDLite-only vs SSDLite+grounding (plan Step 26)
└── tests/
    ├── test_camera.py                    (10)
    ├── test_detection.py                 (6)
    ├── test_tracking.py                  (8)
    ├── test_faces.py                     (11)
    ├── test_pipeline.py                  (6)
    ├── test_real_backends.py             (5)  ← SSDLite-on-MPS adapter
    ├── test_fusion_scenario.py           (2)  ← doc-02 §3 acceptance scenario
    ├── test_locate_anything_geometry.py  (22)
    ├── test_grounding.py                 (29)
    ├── test_locate_anything_parse.py     (28)
    ├── test_locate_anything.py           (16)
    ├── test_locate_anything_runtime.py   (15)
    ├── test_grounding_association.py     (9)
    ├── test_pipeline_grounding.py        (7)
    ├── test_active_grounding.py          (21)
    ├── test_grounding_verification.py    (8)
    ├── test_benchmark_metrics.py         (15)
    ├── test_benchmark_corpus.py          (11)
    ├── test_benchmark.py                 (6)
    ├── test_benchmark_compare.py         (5)
    ├── test_world_state_adapter.py       (5)
    ├── test_prediction_verification.py   (6)
    ├── test_deliberation_record.py       (6)
    └── test_spatial_memory_promotion.py  (6)
```

264 tests total. Fully deterministic: no hardware, no threads in CI paths (the only thread lives behind `CameraFeed`'s scripted-provider tests), no model downloads. The LocateAnything + benchmark + seam modules import cleanly without torch/transformers installed.

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

optional, on demand only:
                            ground_frame(frame, query, policy)
                                                      │
                              SpatialPerceptionBackend.ground(...) -> GroundingResult
                                                      │         (strict parser + typed
                                                      │          GroundingObservation /
                                                      │          PointObservation, fail-closed)
                                                      ▼
                              associate_grounding_to_tracks -> GroundingOutcome
                                                      │         (associated | candidate)
                                                      ▼
                              (cognition/world-state seam: candidates are proposals, never facts)
```

## Grounding modules (LocateAnything workstream)

### `grounding` — typed spatial contracts (LocateAnything plan Phase 1)

`SpatialQuery` (one language-conditioned request), `GroundingResult` (typed
answer: observations + backend state + provenance + raw-hash), and the
observation records `GroundingObservation` (box) / `PointObservation`
(point). Source coordinates stay integer-normalized `[0, 1000]`; pixel boxes
are derived once via `locate_anything_geometry`. Fail-closed: malformed
output ⇒ `success=False` + validation errors — never a guessed observation,
never an implied "absent". `no_object` distinguishes "model says nothing is
there" from "backend failed" (plan Step 9.4).

### `locate_anything_parse` / `locate_anything_geometry`

Strict parser for the documented token format `<ref>label</ref><box><x1><y1><x2><y2></box>` /
`<box><x><y></box>` / `<box>none</box>` — no permissive regex, no silent repair
(plan Step 2.1/2.2). The released model renders each coordinate as a special
token (`<4><207><20><231>`) and the no-object marker as `None`; both are
accepted as the documented encodings, and every coordinate still passes the
strict integer/`[0,1000]`/non-inverted validation. Geometry validates bounds,
rejects inverted/zero-area boxes, and converts to Novi's canonical pixel
`(x,y,w,h)` with floor/ceil clamping so every valid source box keeps positive
pixel area.

### `locate_anything` — backends

`DeterministicLocateAnythingBackend` is the CI backend (scripted results
keyed by frame_id+query — no model, no torch). `LocateAnythingBackend` is
the thin adapter: capability state, prompt hand-off, strict parsing,
provenance, fail-closed results. It never imports the heavy runtime.

### `locate_anything_runtime` — optional runtime boundary

The ONLY module where torch/transformers may be imported, and only inside
functions. Probes the seven capability states (`available | loading |
unavailable | unsupported | dependency_missing | model_missing | failed`);
missing LocateAnything never crashes Novi startup. The real bundle follows
the upstream `LocateAnythingWorker` call shape; loaders are injectable so
tests never touch a model.

### `grounding_association` — grounding → tracking

Conservative per-frame association: boxes by IoU, points by centroid
distance; uncertain matches stay **candidates** (plan Step 5.4) — grounding
never invents temporal continuity.

### `active_grounding` — escalation policy + budgets + dedup + cache

Perception-side half of active perception (plan Phase 6): when to spend
expensive grounding (low SSDLite confidence, ambiguous description, planner
request, prediction violation, expected-but-missing), with a typed
`GroundingBudget` per request (time/compute/retries/frames/risk), dedup of
(frame, query) pairs, and a short-lived LRU cache. Cognition owns query
text; perception owns budgeted execution.

### Brain-zone seams (plan steps 18/21/22/24 — perception side)

The brain workstream owns the world model, prediction engine, deliberation
memory, and durable store. These perception-side seams make the wiring
trivial for them, each protocol-based and tested against fakes:

- `world_state_adapter.admit_grounding_outcome(world, outcome)` — associated
  observations update track entities with OBSERVED state; candidates become
  CANDIDATE/HYPOTHESIZED entities (proposals, never overwriting observed);
  provenance stamped; failed/no-object results admit nothing.
- `prediction_verification.verify_predicted_presence(result, labels)` —
  verified-present set feeds `PredictionEngine.observe(present, cycle)`;
  failures report UNKNOWN, never absence.
- `deliberation_record.build_deliberation_record(result, ...)` — the plan
  Step 7.4 schema: query, candidates, selected, rejected, evidence, outcome.
- `spatial_memory_promotion.promotion_candidate(history)` — stability
  criterion (repeated, same-track, bounded drift) for durable-memory
  promotion; candidates never promote.

### Benchmark (plan Phase 10, steps 25–26)

- `benchmark_corpus` — loads/validates the versioned eval set
  (`docs/07-locate-anything/benchmark/corpus-v1.json`): every record carries
  image hash/dims, query, [0,1000]-normalized target boxes, category, and
  rights/provenance; GT is honest (vision-annotated with caveat notes).
- `benchmark_metrics` — IoU@0.5/0.75/0.90/0.95, mean IoU, center error,
  precision/recall/FP/FN, malformed rate, latency percentiles (pure).
- `benchmark` — `run_grounding_benchmark(backend, corpus, policy)` →
  `BenchmarkReport` (per-record + aggregates).
- `benchmark_compare` — the plan's most important experiment: **baseline
  Novi (SSDLite) vs Novi + LocateAnything** on the same corpus, with delta
  aggregates. CI runs deterministic backends; `scripts/mac-locateanything-benchmark.py`
  runs the real models on MPS and writes evidence JSON.

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

- **No engine wiring**: `BrainDriver` does not consume this package yet — integration starts after the parallel brain workstream settles. The seam will be world-state entity admits fed by `WorldObservation` and `GroundingOutcome` (associated observations and **candidates** — candidates are proposals, never facts; the brain's memory policy decides promotion).
- **No real camera backend**: AVFoundation/OpenCV provider implements `CameraProvider` next; CI keeps the scripted providers regardless (deterministic fallback rule of the regression wall).
- **No real detectors/embedders**: SSDLite/ArcFace-class models arrive as evidence-run validation per repo rules ("a candidate becomes official only after successful execution on the actual Mac"). Same rule gates `LocateAnythingBackend` — see `docs/07-locate-anything/07_MAC_FEASIBILITY.md` for the MPS decision gate.
- **Grounding is never mandatory**: `ground_frame` runs only when cognition asks; no backend ⇒ fail-closed result.
- **No 3D claims**: a 2D box is not a 3D position; depth/intrinsics/extrinsics/pose are future work (plan Phase 8).

## Resource parity (exit-contract rule)

SSDLite320, ArcFace-class embeddings, and IoU tracking all map to Orin/Thor-plausible deployments (TensorRT/onnx); embeddings stay small (≤512-d). No cloud vision APIs anywhere. LocateAnything is a 7.8 GB local model (pinned revision) behind the optional `locateanything` extra; the Jetson path is the same adapter over a CUDA runtime (plan Phase 12).

## Running

```bash
.venv/bin/python -m pytest novi/perception/tests -q                       # 264 tests
.venv/bin/python -m pytest novi/perception/tests/test_fusion_scenario.py -v   # the scenario
scripts/mac-locateanything-env.sh         # isolated LocateAnything venv + pinned model (gitignored)
scripts/mac-locateanything-experiment.py  # Phase 4 Mac feasibility evidence (run with .venv-locateanything)
scripts/mac-locateanything-benchmark.py   # real-model benchmark: SSDLite vs SSDLite+LocateAnything (corpus-v1.json)
```

Full-suite status at implementation time: **1,489 passed** (perception + voice + entire pre-existing suite), zero regressions.
