# Novi Voice — Continuous Listening, Speech & Turn-Taking

Implementation of [`docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md`](../../docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md): real-time voice interaction on the Mac body that runs **concurrently** with every other brain capability — never as a blocking chat session.

## The one design decision that shapes everything

**Autonomy owns turn-taking.** Dialogue decides *what* to say; `turn_taking.py` decides *when* Novi speaks, listens, yields, or defers. This is what makes the absentee-owner scenario work: voice is just another track the autonomy layer arbitrates, alongside navigation, observation, and hearing.

## Package layout

```text
novi/voice/
├── __init__.py        Lazy exports (package importable module-by-module)
├── vad.py             TurnSegmenter — speech turns from the AudioFrame stream
├── stt.py             STTProvider protocol + DeterministicSTTProvider
├── tts.py             TTSProvider protocol + Say / Deterministic providers
├── turn_taking.py     Autonomy-owned speaking-lease policy (the core)
├── voice_loop.py      VoiceLoop — frames → VAD → STT → reply → TTS
└── tests/
    ├── test_vad.py            (8)
    ├── test_stt.py            (5)
    ├── test_tts.py            (5)
    ├── test_turn_taking.py    (10)
    ├── test_voice_loop.py     (8)
    └── test_scenario_v1.py    (2)  ← acceptance scenario, executable
```

38 tests total. All deterministic: no hardware, no threads, no sleeps, no model downloads — CI-safe by construction.

## Data flow

```text
mic stream ──► feed_frame() ──► TurnSegmenter (VAD-gated)
                                   │ closes a SpeechTurn on
                                   │ trailing silence or cap
                                   ▼
                              STTProvider.transcribe(frames) -> Transcript
                                   │ empty transcript → dropped (never invents)
                                   ▼
                              reply_fn(text, person=...) -> reply text
                                   │
                                   ▼
                        TurnTakingPolicy.request_speak(...)
                                   │ lease granted or queued
                                   ▼
                              TTSProvider.synthesize(reply) -> AudioOut
                                   │
        drain() ◄──────────────────┘   caller pulls finished utterances
```

The loop is **pull-based**: callers feed frames as they arrive and drain replies when ready. Scheduling belongs to the autonomy layer above; this package is the deterministic pipeline underneath.

## Module reference

### `vad.TurnSegmenter`

Continuous listening means continuous *ingestion*, not continuous decoding.

- Speech frames open a turn; `endpoint_frames` consecutive silence closes it (inter-word pauses don't).
- `max_utterance_frames` forces a boundary so long speech can't starve STT.
- Closed turns carry provenance: frame list, first/last timestamps, duration, peak RMS, `forced_by_cap`.
- `feed()` returns turns closed by that exact frame; `drain_closed()` accumulates; `pending` reports open-turn state; `reset()` clears.

### `stt.STTProvider` / `DeterministicSTTProvider`

Protocol: `transcribe(frames) -> Transcript{text, confidence, provider, audio_first, audio_last}`.

The deterministic provider keys on the first frame's `captured_at`, mapping to scripted text. Unknown audio transcribes to `""` with zero confidence — **fail quiet, never fabricate**. A real Whisper/distil-whisper backend implements the same protocol later (MPS now, TensorRT on Jetson).

### `tts.TTSProvider` / `DeterministicTTSProvider` / `SayTTSProvider`

Protocol: `synthesize(text) -> AudioOut{text, provider, spoken}`.

- **Deterministic**: records every utterance for CI assertions (`tts.utterances`); nothing is played.
- **Say**: shells out to macOS `/usr/bin/say` — the day-one audible stub proving the path end-to-end. Raises `RuntimeError` when unavailable so callers fall back cleanly. Empty text rejected at both providers.

Piper/Kokoro-class neural TTS slots in behind the same protocol later.

### `turn_taking.TurnTakingPolicy` — the core

Channels and priorities (lower = more urgent):

| Channel | Priority | Meaning |
|---|---|---|
| `PERSON_VOICE` | 0 | a physically-present person |
| `OWNER_CHAT` | 0 | owner's direct message from afar |
| `AMBIENT` | 2 | background/social commentary |
| `SYSTEM` | 3 | diagnostics/status |

Rules enforced:

1. **One voice lease at a time.** Second requester queues (`reason="queued"`).
2. **Never cut mid-word.** Higher-*or*-equal-priority inbound while speaking → `yield-after-sentence`: current utterance finishes, inbound queues, interrupted ref recorded.
3. **Resume explicitly.** When queue drains, an interrupted exchange resumes LIFO before idle (`release-resume`). Resume restores the *utterance* ref, not the conversation label.
4. **Release auto-grants** the next entry by (priority, arrival order), logged distinctly as `release-next` for provenance.
5. **Exchange-in-flight counts too.** Owner message arriving between Anna's sentences still yields gracefully — the social contract holds even when no lease is held.
6. **Every decision is logged** (`event_log`) with kind, reason, channel, refs, and cycle number. Cycles are caller-supplied — no clocks, replayable interleavings.

### `voice_loop.VoiceLoop`

Wires everything: `feed_frame()` → segmenter → STT → your `reply_fn` → lease request → TTS → `drain()`.

Extras: `begin_exchange(ref)` opens an interaction context; `notify_owner_message(ref)` surfaces the arbitration decision; `person` attribute carries recognized identity into replies; `snapshot()` serves web observers (`/api` state surface later); `events` mirrors policy decisions plus per-stage provenance (`turn-transcribed`, `reply-spoken`).

Empty transcripts never reach `reply_fn`; empty replies never reach TTS.

## SCENARIO-V1 — the executable acceptance test

From `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md`, now green in CI (`tests/test_scenario_v1.py`):

> Owner at work, Novi at home. Novi navigates, observes, hears ambient events, mid-conversation with Anna (recognized via face-ID). Owner messages from work. Novi finishes Anna's sentence first, handles the message, resumes Anna's turn — and navigation ticks between every single frame.

Assertions prove nothing was dropped: both Anna turns answered, nav cycles ≥ threshold, observation and hearing tracks intact, yield decision carries the interrupted ref, resume restores her turn.

## Integration boundaries (what this deliberately does NOT do)

- **No brain changes.** This package imports brain contracts (`AudioFrame`) read-only; `novi.brain` has zero dependence on it. Wiring into `BrainDriver.drive()` as `AgentInput(modality="voice")` is a future patch in `novi/brain/agent.py` territory — kept separate so other workstreams proceed undisturbed.
- **No real audio I/O yet.** Mic capture and speaker output are the next slice; the protocols above are their contracts. Real-model validation runs happen on-Mac as evidence runs, never in CI.
- **No hardware-array features.** Beamforming/DoA defer to hardware docs §8.

## Resource parity (exit-contract rule)

Whisper-class STT, Silero-class VAD, and Piper/Kokoro TTS all map to Orin/Thor-plausible deployments (TensorRT/onnx). No cloud APIs anywhere in the voice path. The deterministic providers double as the hardware-absent fallbacks required by the regression wall.

## Running

```bash
.venv/bin/python -m pytest novi/voice/tests -q          # just voice (38 tests)
.venv/bin/python -m pytest novi/voice/tests/test_scenario_v1.py -v   # the scenario
```

Full-suite status at implementation time: **1,427 passed** (voice included), zero regressions.
