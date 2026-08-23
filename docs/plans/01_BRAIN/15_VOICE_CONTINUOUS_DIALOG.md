# Brain — Voice: Continuous Listening & Dialog

## Objective

Give Novi real-time, continuous voice interaction on the Mac body: always-on listening (VAD-gated), speech-to-text, text-to-speech, and full-duplex dialog that runs *concurrently* with every other brain capability — not as a blocking chat session.

Voice is an input/output modality layered over the existing source-agnostic brain. It introduces no new cognition; it feeds `AgentInput(modality="voice")` into `BrainDriver.drive()` and renders replies through a pluggable TTS provider.

## Authority boundary (decided)

**Turn-taking is owned by the autonomy layer, not the dialogue layer.**

Rationale: Novi must multitask across channels. Reference scenario (**SCENARIO-V1 "absentee owner"**):

> Owner is at work. Novi is at home: navigating, observing, hearing ambient events, mid-conversation with a person at home. The owner sends a chat message from work. Novi answers the message **without dropping** any other capability — the home conversation pauses gracefully, resumes after, navigation continues throughout.

Therefore dialogue (`chat.py`) decides **what** to say; a dedicated autonomy-owned policy module (`turn_taking.py`) decides **when** Novi speaks, listens, yields, or defers, arbitrating between simultaneous communication demands:

```text
                    ┌────────────────────────────┐
 input channels ──► │  AUTONOMY / TURN-TAKING    │ ◄── motivations,
 (voice, chat,      │  priority + interruption   │     soul, active goals
  events)           │  policy (turn_taking.py)   │
                    └──────────┬─────────────────┘
                               │ speaking lease / listen state
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        voice dialog      web/chat reply    other tracks
        (person at home)  (owner at work)   (navigate/observe)
```

## Provider contracts

### STT (speech → text)

Extends the existing STT provider boundary (`DeterministicSTTProvider` stub):

```text
STTProvider (protocol)
  transcribe(audio_segment, *, sample_rate) -> Transcript
  Transcript: {text, language, confidence, word_timestamps?, provenance}
```

- Candidate model class: Whisper / distil-whisper, local PyTorch (MPS). Jetson-parity: same weights, TensorRT backend later.
- Gated by VAD (Silero-class): no transcription during silence — continuous *listening*, not continuous *decoding*.

### VAD + diarization

- VAD segments speech turns from the continuous audio stream (`AudioFrame` flow already exists).
- Diarization labels "who spoke when" locally; speaker labels pair with identity providers (see `02_FACE_AND_OBJECT_RECOGNITION.md`) for cross-modal identity verification.

### TTS (text → speech)

New provider boundary, symmetric with STT:

```text
TTSProvider (protocol)
  synthesize(text, *, voice_profile) -> AudioOut
```

- Day-one stub: macOS `say` (proves the loop end-to-end).
- Target candidates: Piper / Kokoro-class local neural TTS (command-invoked provider pattern).
- Self-voice suppression: echo/self-voice reference so Novi does not hear itself as a user.

## Full-duplex integration with the cognitive loop

```text
mic stream ─► VAD ─► segment ─► STT ─► AgentInput(voice) ─┐
                                                          ├─► BrainDriver.drive()
camera/events ─► ... ─► AgentInput(...) ─────────────────┤         │
                                                          │         ▼
reply.text ◄─ respond()/compose_reply ◄───────────────────┘   cognitive loop
     │                                                         keeps stepping
     ▼                                                              (B1 loop)
TTS ─► speakers            (step() never blocks on speech)
```

Requirements:

1. `drive()` remains non-blocking for voice; long STT/TTS run as background track work under autonomy scheduling.
2. The cognitive loop continues stepping while Novi speaks/listens (world state stays fresh mid-conversation).
3. Barge-in: speech from a human while Novi speaks raises a FAST-layer interrupt; `turn_taking` policy decides pause/yield/resume per interrupt priority.
4. End-of-turn detection: silence duration + semantic completeness; no fixed timeouts alone.

## Turn-taking policy (autonomy-owned)

`turn_taking.py` maintains a **speaking lease** and a channel priority table:

| Channel | Typical priority | May be preempted by |
|---|---|---|
| Physical person present (voice) | high | safety event, higher-priority person |
| Owner direct message (chat) | high | safety events |
| Ambient/social listening | background | any active exchange |
| System/diagnostic announcements | low | anything |

Rules:

1. At most one outbound utterance at a time (single voice channel).
2. A pending higher-priority inbound message does not cut Novi off mid-word: finish the current sentence, yield within bounded time, handle, then resume the prior track explicitly (resume, restart, or abandon recorded as a decision).
3. Owner messages during a home conversation get acknowledged socially ("one moment") rather than silently ignored — relationship-preserving behavior per docs/06-soul.
4. All arbitration decisions emit provenance events (channel, priority, decision, reason).

## Latency budgets (Mac prototype)

| Stage | Budget |
|---|---|
| VAD endpoint | ≤ 300 ms after speech ends |
| STT (short utterance) | ≤ 1.5 s |
| Brain reply composition | existing respond() budget |
| TTS start (first audio) | ≤ 800 ms |
| Barge-in reaction | ≤ 500 ms |

Budgets are targets for felt responsiveness, measured in evidence runs, not CI gates (CI stays deterministic).

## Deterministic testing

All hardware-dependent pieces inject fakes (matching repo conventions): scripted mic streams, canned transcripts, deterministic TTS. CI validates: turn arbitration tables, preemption/resume semantics, SCENARIO-V1 as a simulated multi-track test, no loop-blocking, provenance emission. Real-model validation happens on-Mac as evidence runs.

## Resource parity

Whisper/distil-whisper, Silero-VAD, Piper/Kokoro all have Orin/Thor-plausible deployments (TensorRT/onnx). No cloud APIs anywhere in the voice path. Mac speakers/mic are the temporary body peripherals; array features (beamforming, DoA) defer to hardware docs §8 and are out of scope here.

## Evidence gates

- SCENARIO-V1 simulation passes deterministically in CI.
- Live evidence run: 10-minute natural voice session with a person, ≥ 2 owner chat messages injected mid-conversation, zero dropped tracks, barge-in handled, latencies logged against budgets.
- Regression wall green with voice providers present (fakes active) and absent (deterministic fallbacks).

## Status

**PLANNED / DOC PHASE.** Implementation sequencing: STT+VAD loop → TTS stub → turn_taking policy → live evidence run.
