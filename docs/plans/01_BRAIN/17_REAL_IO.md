# Brain — Real I/O: Camera, Microphone, Speakers

## Objective

Connect real hardware to the multimodal stack so Novi can **see, hear, and speak in real time** on the Mac body: live camera frames into perception, microphone audio through local Whisper STT into the brain, and spoken replies out through the speakers.

Implements doc 15/16's deferred "real device" seams. Everything flows through the same deterministic-tested pipelines — real devices are provider swaps, not new architecture.

## Status

**IMPLEMENTED / LIVE-VERIFIED ON MAC HARDWARE** (see §6 evidence).

---

## 1. Camera (seeing)

```text
MacCamera (OpenCV, brain.io)
   → MacCameraAdapter      (perception.CameraProvider contract; ndarray → JPEG bytes)
   → CameraFeed            (capture thread + bounded drop-oldest queue + health)
   → background loop       (poll → encode b64 JPEG → mm_last_frame_b64 → PerceptionPipeline)
   → /preview image        + world-state detections
```

- Frames auto-flow once enabled; preview page shows the live image with recognition badges.
- Health states surface honestly (`available/degraded/failed`); stale detection when frames stop.

## 2. Microphone (hearing)

```text
MacMicrophone (sounddevice, brain.io)
   → RealMicrophone        (record(seconds) -> wav path dict)
   → WhisperSTTProvider    (faster-whisper base/int8, fully local; reuses brain's warm model when present)
   → MultimodalRuntime.voice_turn(text)  → BrainDriver.hear() → reply
```

- Empty transcripts (silence) handled gracefully: `ok=true`, empty text, no reply.
- STT failures degrade to `{"ok": false, "reason": "stt-failed: …"}` — never crash the loop.

## 3. Speakers (speaking)

```text
reply text → RealSpeaker → SayTTSProvider (/usr/bin/say)  → spoken aloud
                        └→ later: Piper/Kokoro neural voices
```

- `RealSpeaker.speak()` **never raises**: unavailable/error degrades to `{spoken: false, reason: …}`.
- Speak-back toggle (`speak_back_enabled`) governs whether replies are voiced after each listen.
- Direct speech available via `/api/voice/tts {text}`.

## 4. Web API additions

| Route | Method | Purpose |
|---|---|---|
| `/api/real/status` | GET | enabled flags per device + speak_back state |
| `/api/real/enable` | POST | `{camera?, mic?, speaker?}` → attach devices, honest per-device result |
| `/api/real/speakback` | POST | `{enabled}` toggle for spoken replies |
| `/api/voice/listen` | POST | `{seconds}` record → STT → brain → spoken reply (the talk button) |
| `/api/voice/tts` | POST | `{text}` speak arbitrary text |

Preview page v2 adds: enable button (camera+mic+speaker), listen button (records ~3 s, shows heard/reply), speak-back checkbox, live camera image.

## 5. Graceful degradation matrix

| Hardware missing | Behavior |
|---|---|
| No camera | `real_enable(camera=True)` → `{camera: false, camera_error}`; rest of system unaffected |
| No mic permission / sounddevice | listen raises actionable RuntimeError → HTTP 400 with message |
| No `say` binary | speaker marks unavailable; speaks return `{spoken: false, reason: "tts-unavailable"}`; chat still works |

CI never requires any of these devices — every path is tested with fakes.

## 6. Live verification evidence (this Mac)

- `real_enable(camera=True, mic=True, speaker=True)` → all three `True`.
- After 2 s: `camera_health=available`, `stale=false`, preview JPEG present.
- `tts_speak("Real I O enabled…")` → `{spoken: true, provider: say}` — audible.
- Voice round-trip with silence → graceful empty transcript.
- Spoken-WAV round-trip: macOS `say` renders *"Hello Novi, what can you do?"* to WAV → **Whisper transcribes it verbatim (conf 0.99)** → brain replies *"yeah, i'm listening."* → **spoken aloud** (`spoken: true`).

## 8. Speaker recognition (voices) — IMPLEMENTED & LIVE-VERIFIED

`novi/integration/real_io_voice.py`:

- **RealVoiceEmbedder** — Resemblyzer d-vector (256-d, L2-normalized), fully local CPU inference.
- **RealSpeakerRecognizer** — enroll(label, wav) / match(wav) with similarity floor; optional persistence into RecognitionStore (VOICE kind) so voiceprints survive restarts.

Web surface:

| Route | Purpose |
|---|---|
| `/api/recognition/voice` | `{name, wav_path?}` — enroll a voiceprint; omits wav_path to record 4 s from the live mic |

`voice_listen()` now auto-matches every recording against enrolled voices and returns `speaker` + `speaker_similarity`; the matched speaker becomes the addressee for the brain reply (cross-modal with face identity via `current_person`).

**Live evidence:** two speakers enrolled through the server API; fresh unseen takes identified correctly — Owner-take → Owner @ 0.94, Friend-take → Friend @ 0.95. Separation margin on real speech ≈ 0.92 same vs ≈ 0.46 cross.

Note: `resemblyzer` requires `pkg_resources`; pin `setuptools<81` in environments that lack it.

---

## Known limits & next steps

- Mic path is push-to-talk (fixed seconds), not continuous VAD streaming — the voice package's `TurnSegmenter` is ready for a streaming mic loop as the next slice.
- Face embeddings are deterministic vectors until an ArcFace-class encoder is attached; enrollment/matching flow is already live end-to-end.
- Dark-room sensitivity: auto-exposure needs ~2–3 s warm-up before detection confidence rises; consider software gain or an exposure-warmup guard in the camera loop.
