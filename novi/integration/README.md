# Novi Integration — Engine Bridge, Web API & Recognition Memory

Implementation of [`docs/plans/01_BRAIN/16_MULTIMODAL_INTEGRATION.md`](../../docs/plans/01_BRAIN/16_MULTIMODAL_INTEGRATION.md): wires the voice (`novi/voice/`) and perception (`novi/perception/`) capability packages into the running brain, exposes them over the web app with a live preview page, and persists every enrolled person / voice / noise / place so Novi recognizes them across restarts.

Like `novi/voice/` and `novi/perception/`, this package is **self-contained**. It drives the brain through the existing source-agnostic `BrainDriver` — `engine.py` was not modified — and the web surface is additive via a mixin.

## Package layout

```text
novi/integration/
├── __init__.py                  (empty; import submodules directly)
├── recognition_store.py         RecognitionStore — durable enrollment memory
├── multimodal.py                MultimodalRuntime — the bridge
└── tests/
    ├── test_recognition_store.py   (9)
    ├── test_multimodal.py          (7)
    └── test_e2e_scenario.py        (1)  ← end-to-end acceptance scenario
```

Plus its web half:

```text
novi/web/integration_api.py     IntegrationMixin (runtime + handler methods)
novi/web/static/preview.html    /preview live page
novi/web/tests/test_integration_api.py  (7)
```

24 integration-layer tests. Fully deterministic: scripted detectors/embeddings, in-memory or temp SQLite, no hardware, no model downloads.

## The one rule that shapes everything

**The brain is one mind.** Voice and perception never bypass `BrainDriver`; they attach context (who is present, where we are) to inputs the brain already accepts. The bridge translates modality results into *person* and *place* context on `hear()`-style calls — nothing more.

## Architecture

```text
                    ┌───────────────────────────┐
 camera frames ───► │   MultimodalRuntime       │ ◄── voice turns
 (perception)       │  ┌─────────────────────┐  │     (STT transcripts)
                    │  │ PerceptionPipeline  │  │
                    │  │ FaceIdentifier      │  │     chat messages
                    │  └─────────────────────┘  │
                    │           │               │
                    │  RecognitionStore (SQLite)│  faces·voices·noises·places
                    └───────────┬───────────────┘
                                │ person/place context
                                ▼
                          BrainDriver.hear()  → MacBrain.respond()
                                                        (one mind)
```

## Components

### `RecognitionStore` — persistent recognition memory

SQLite (WAL-mode, stdlib `sqlite3`), one table of enrollment records:

| Kind | Stored as | Recognized by | Privacy-gated |
|---|---|---|---|
| `FACE` | embedding vector | cosine ≥ tau_match (default 0.90) | yes |
| `VOICE` | embedding vector | cosine ≥ tau_match | yes |
| `NOISE` | descriptor JSON (`{"band": "high", …}`) | key/value overlap | no |
| `PLACE` | landmark list (`{"landmarks": ["cup", …]}`) | subset match on landmarks | no |

Rules:

- **Provenance mandatory**: every enrollment requires `frame_id` or a `provenance` dict — writes without origin are rejected.
- **Privacy gate**: biometric kinds (`face`, `voice`) raise `PermissionError` when disabled; noises/places keep working. Every toggle is audited in-store with its reason.
- **Durable**: survives process restart (tested by close/reopen).
- Canonical ids: `recognize_person()` enrolls under stable human ids (`person-anna`), so matches resolve to "Anna", never an internal sequence number.

### `MultimodalRuntime` — the bridge

One instance per server, wrapping a shared `BrainDriver`:

| Method | What it does |
|---|---|
| `process_camera_frame(frame, face_embedding?, speaker_person_id?)` | runs perception → updates `current_person` (+ tier) from recognized faces, sets `pending_enrollment_proposal` for unknowns, resolves `current_place` from seen landmarks |
| `voice_turn(text, speaker_label=None)` | transcript → `driver.hear(text, person=…, source="voice")` → brain reply |
| `recognize_person(name, face_embedding?, voice_embedding?)` | dual enrollment (FaceIdentifier + store) under one canonical id |
| `say(text, via_voice=…)` | explicit chat/hear path with current person attached |
| `snapshot()` | live state: person, tier, place, proposal flag, perception telemetry, recent events |

Every step emits provenance events (`perception.frame`, `identity.recognized`, `identity.proposal`, `identity.ambiguous`, `voice.turn`, `person.enrolled`) for the web UI and audit trail.

### `IntegrationMixin` (in `novi/web/integration_api.py`)

Mixed into `NoviWebServer` (the only edit to `server.py`, plus route dispatch). Provides lazy `_integration_init()` — non-fatal if anything fails, so minimal deployments and existing tests run unchanged — plus the handler methods listed below. Voice turns mirror into the shared web chat as `[voice] …` entries so the UI shows the full exchange.

## HTTP surface

GET:

| Route | Purpose |
|---|---|
| `/preview` | live preview page |
| `/api/preview` | preview payload JSON |
| `/api/perception/state` | runtime snapshot + all enrollments |
| `/api/recognition[?kind=face\|voice\|noise\|place]` | filtered enrollment listing |

POST (JSON body):

| Route | Body | Purpose |
|---|---|---|
| `/api/perception/frame` | `{frame_id, captured_at, face_embedding?, speaker_person_id?}` | one frame through perception |
| `/api/voice/turn` | `{text, speaker_label?, confidence?}` | voice turn → brain → reply |
| `/api/recognition/person` | `{name, face_embedding?, voice_embedding?, frame_id}` | enroll/update a person |
| `/api/recognition/enroll` | `{kind: noise\|place, label, descriptor}` | enroll noise/place |
| `/api/recognition/privacy` | `{enabled, reason}` | privacy toggle (audited) |

## Preview page

`static/preview.html` polls `/api/preview` every second and shows: camera health badge (available/degraded/failed/offline), stale warning, recognized person + identity tier, current place, and last-frame detections. When a real camera provider supplies base64 JPEGs (`mm_last_frame_b64`), the image renders inline. Dependency-free, dark-theme, consistent with the main UI. Link back to `/` included.

## The end-to-end acceptance test

`tests/test_e2e_scenario.py` runs the whole loop through a real `NoviWebServer`:

1. Enroll Anna via the person API.
2. Enroll the kitchen by its landmarks.
3. Frame with Anna's face embedding → identity **recognized**.
4. Kitchen frame (cup detected) → `current_place == "kitchen"`.
5. Anna speaks via voice turn → brain replies with her as addressee, mirrored to chat.
6. Owner chats in parallel through the normal channel — same brain, separate entry point.
7. Preview reflects live state (person = Anna).
8. Server stopped → store reopened → **Anna and the kitchen survive**.

## Verification

- 24 integration-layer tests green.
- Live smoke over real HTTP: `/preview` serves HTML; `/api/preview`, `/api/perception/state`, `/api/recognition` return JSON; POST frame returns detections/tracks/identities/place/proposal; POST voice turn gets a genuine brain reply.
- Full suite at implementation time: **1,532 passed**, zero regressions.

## Integration boundaries — real devices now live (doc 17)

Real camera, microphone, and speakers are implemented and live-verified: see [`17_REAL_IO.md`](../../docs/plans/01_BRAIN/17_REAL_IO.md) and `novi/integration/real_io.py`. `real_enable(camera/mic/speaker)` attaches hardware; `/api/voice/listen` records → local Whisper → brain → spoken reply; `/preview` shows the live image. Remaining seams:

- Continuous VAD streaming mic (the voice package's TurnSegmenter is ready for it)
- Real SSDLite320 detector + ArcFace-class face embeddings (evidence-run gated)
- World-state entity admits from `WorldObservation` (G7 spatial binding), deferred until the parallel brain workstream settles
- Speaker identity: enroll voiceprints to light up the `verified` tier cross-modally

## Resource parity (exit-contract rule)

Cosine matching, stdlib SQLite, descriptor lookups — trivially Jetson-plausible. No cloud APIs anywhere in this path.
