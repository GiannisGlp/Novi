# Brain — Multimodal Integration (Voice + Perception + Recognition)

## Objective

Wire the voice (`novi/voice/`), perception (`novi/perception/`) and a durable recognition store into the running brain, expose them over the web app with a live preview page, and persist every enrolled person/voice/noise/place so Novi recognizes them across restarts.

Implemented by `novi/integration/` (bridge + store) and additive web handlers in `novi/web/integration_api.py`. Engine (`engine.py`) untouched — the bridge drives the existing source-agnostic `BrainDriver`, honoring "the brain is one mind; modalities are inputs".

## Status

**IMPLEMENTED / CI VALIDATED** (deterministic paths; real-model evidence runs pending hardware providers).

---

## 1. Architecture

```text
                    ┌───────────────────────────┐
 camera frames ───► │   MultimodalRuntime       │ ◄── voice turns
 (perception)       │  ┌─────────────────────┐  │     (voice_loop / STT)
                    │  │ PerceptionPipeline  │  │
                    │  │ FaceIdentifier      │  │     chat messages
                    │  └─────────────────────┘  │
                    │           │               │
                    │  RecognitionStore (SQLite)│  faces·voices·noises·places
                    └───────────┬───────────────┘
                                │ person/place context
                                ▼
                          BrainDriver.hear()  → MacBrain.respond()
                                │                     (one mind)
                                ▼
                        reply (+ web chat mirror)
```

Key properties:

1. **One mind.** Voice and perception never bypass `BrainDriver`; they attach context (who is present, where we are) to inputs the brain already accepts.
2. **Additive integration.** `NoviWebServer` gains the surface via `IntegrationMixin`; engine files untouched; parallel workstreams undisturbed.
3. **Deterministic CI.** Scripted detectors/embeddings; real Whisper/SSDLite/ArcFace backends drop into the same protocols as evidence runs.

## 2. Components

### `novi/integration/multimodal.py` — MultimodalRuntime

- `process_camera_frame(frame, face_embedding=None, speaker_person_id=None)` → runs perception; recognized faces set `current_person` (+ tier); ambiguous → event; unknown → `pending_enrollment_proposal`.
- `_update_place(labels)` → matches seen objects against enrolled place landmarks → sets `current_place`; stamped onto events.
- `voice_turn(text, speaker_label=None)` → `driver.hear(text, person=…, source="voice")` with recognized speaker attached.
- `recognize_person(name, face_embedding=…, voice_embedding=…)` → enrolls into FaceIdentifier **and** RecognitionStore under one canonical id (`person-anna`), keeping label resolution stable ("Anna", not an internal id).
- `snapshot()` → live state for observers (person, tier, place, proposal flag, perception telemetry, recent events).

### `novi/integration/recognition_store.py` — RecognitionStore

Durable SQLite (WAL) enrollment memory:

| Kind | Stored as | Recognized by |
|---|---|---|
| FACE | embedding vector | cosine ≥ tau_match (privacy-gated) |
| VOICE | embedding vector | cosine ≥ tau_match (privacy-gated) |
| NOISE | descriptor JSON | descriptor key/value overlap |
| PLACE | landmark list | subset match on landmarks |

Rules: provenance mandatory on every write; biometric kinds refused when privacy off (transitions audited in-store); survives reopen (tested).

### `novi/web/integration_api.py` — IntegrationMixin

Adds to `NoviWebServer`: lazy `_integration_init()` (non-fatal if unavailable), runtime methods used by handlers, chat mirroring for voice turns (`[voice] …` entries appear in the shared conversation).

## 3. HTTP surface

GET:

| Route | Purpose |
|---|---|
| `/preview` | live preview page (camera badges, person/tier/place, detections) |
| `/api/preview` | preview payload JSON |
| `/api/perception/state` | runtime snapshot + enrollments |
| `/api/recognition[?kind=face\|voice\|noise\|place]` | enrollment listing |

POST:

| Route | Body | Purpose |
|---|---|---|
| `/api/perception/frame` | `{frame_id, captured_at, face_embedding?, speaker_person_id?}` | run one frame through perception |
| `/api/voice/turn` | `{text, speaker_label?, confidence?}` | voice turn → brain → reply (mirrored to chat) |
| `/api/recognition/person` | `{name, face_embedding?, voice_embedding?, frame_id}` | enroll/update a person |
| `/api/recognition/enroll` | `{kind: noise\|place, label, descriptor}` | enroll noise/place |
| `/api/recognition/privacy` | `{enabled, reason}` | privacy toggle (audited) |

## 4. Preview

`static/preview.html` polls `/api/preview` at 1 Hz: camera health badge, stale warning, recognized person + tier, current place, last detections. When a real camera provider feeds base64 JPEGs (`mm_last_frame_b64`), the image renders inline. Deliberately dependency-free like the rest of the web app.

## 5. End-to-end acceptance

`novi/integration/tests/test_e2e_scenario.py`:

1. Enroll Anna (person API) + kitchen by landmarks (place API).
2. Frame with Anna's embedding → identity `recognized`.
3. Kitchen frame (cup scripted) → `current_place == "kitchen"`.
4. Anna speaks via `/api/voice/turn` → brain replies, addressee Anna, mirrored to chat.
5. Owner chats in parallel through the normal channel — same brain.
6. Preview reflects live state.
7. Server stopped → recognition store reopened → Anna + kitchen survive.

Full suite at implementation time: **1532 passed**, zero regressions.

## 6. Resource parity & next steps

All components are small-model/Jetson-plausible (cosine matching, stdlib SQLite). Next seams, in order: real camera provider feeding `mm_last_frame_b64`; real STT/TTS behind the voice loop; browser microphone capture on `/preview`; world-state entity admits from `WorldObservation` (G7 spatial binding); wire `speaker_person_id` from diarization once voiceprints are enrolled.

Parity note: no cloud APIs anywhere in this path.
