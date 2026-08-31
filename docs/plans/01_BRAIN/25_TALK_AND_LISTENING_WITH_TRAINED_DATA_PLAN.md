# Plan 25 — Talk and Listening with the Trained Data

**Status:** IMPLEMENTING
**Date:** 2026-08-31
**Depends on:** plan 23 (dialogue SFT/DPO adapters), plan 24 (emotional SFT/DPO adapters)

## Goal

Now that Novi has trained data for learning and emotional maturity, improve
Novi's talk and listening: make dialog, answer and talk, hear the user and
talk back — **everything with the trained data**.

## Current state

- Trained LoRA adapters exist and are registered:
  - `novi-qwen3-8b-dialogue-v1` (active) — plan-23 `situation_to_prompt` format
  - `novi-qwen3-8b-emotional-v1` (active) — plan-24 `emotional_situation_to_prompt` format
- The brain's reply path (`_compose_reply_impl` → `DialogueEngine.reply`) uses an
  `llm_chat` transport: injected override → brain-owned Ollama (`default_llm_chat`)
  → deterministic fallback. **The trained adapters are NOT wired in.**
- The voice package (`novi/voice/`) has a deterministic full-duplex `VoiceLoop`
  (frames → VAD → STT → reply_fn → TTS) but **no consumer wires it to the brain**.

## Part A — Trained-adapter reply transport (talk with the trained data)

New module `novi/brain/trained_reply.py`:

- `TrainedReplyTransport` — an `llm_chat`-compatible callable
  `(*, system, user, temperature, timeout) -> str | None` that:
  - lazily loads the base model (Qwen3-8B) once and attaches both LoRA adapters
    via PEFT multi-adapter (`dialogue`, `emotional`);
  - parses the brain's `user` JSON payload, derives the communicative act from
    the user line, and renders the **training prompt format** (situation + act),
    not the system/user prompt — that is what the adapters were fine-tuned on;
  - routes emotional statements to the emotional adapter, everything else to
    the dialogue adapter;
  - generates, strips Qwen3 `thinking` blocks, returns text (None on any failure
    so the reply pipeline's deterministic fallback applies).
- Pure helpers (unit-testable without a model): `derive_dialogue_act`,
  `derive_emotional_act`, `build_dialogue_prompt`, `build_emotional_prompt`.
- Model loading is injectable (`loader=`), so tests substitute a fake model.

Config additions to `MacBrainConfig`:

- `trained_reply_enabled: bool = False`
- `trained_dialogue_adapter: str = ""`
- `trained_emotional_adapter: str = ""`
- `trained_base_model: str = "Qwen/Qwen3-8B"`

Wiring: `default_llm_chat()` resolution order becomes
injected override → **trained transport** (when enabled + configured) →
brain-owned Ollama → None. The trained transport inherits the
no-assistant/no-repetition guardrails for free because it is passed through
`DialogueEngine.reply(llm_chat=...)`.

## Part B — Voice loop end-to-end (hear + talk back)

New module `novi/brain/voice_session.py`:

- `VoiceSession` wires the voice package's `VoiceLoop` with real providers:
  - `TurnSegmenter` (VAD-gated turn segmentation),
  - `WhisperSTTProvider` (hear — faster-whisper),
  - `SayTTSProvider` (talk back — macOS `say`),
  - `reply_fn` = `brain.respond(text, person=person)["text"]` (talk with the
    trained data — the brain's default transport is the trained adapter).
- `feed_frame(frame)` / `drain()` delegate to the loop; providers are
  injectable so tests use the deterministic STT/TTS.

## Part C — Tests (TDD)

- `novi/brain/tests/test_trained_reply.py`:
  - act derivation (greeting/farewell/thanks/clarify/continue/repair/respond;
    emotional celebrate/support/repair/respond);
  - prompt builders produce the training format (field names + JSON);
  - transport contract with a fake loader: correct adapter selected, prompt
    rendered, thinking stripped, None on load failure;
  - `default_llm_chat` resolution: trained transport wins over Ollama when
    enabled; disabled → Ollama/None unchanged.
- `novi/brain/tests/test_voice_session.py`:
  - `VoiceSession` wires the loop with deterministic STT/TTS and the brain's
    `respond` as `reply_fn`; a scripted turn produces a spoken reply.

## Part D — Web-server trained-transport wiring

The web chat surface (`novi/web/server.py`) prefers the trained transport when
configured, so the browser chat also talks with the trained data:

- New constructor params after `chat_llm`: `trained_reply_enabled`,
  `trained_dialogue_adapter`, `trained_emotional_adapter`, `trained_base_model`
  — all forwarded into `MacBrainConfig`.
- New `_reply_transport()` helper: returns `brain.default_llm_chat()` when
  `trained_reply_enabled` and a transport is available, else the Ollama
  `_llm_chat` when `chat_llm` is on and Ollama is up, else None.
- The chat, listen, and streaming endpoints use `_reply_transport()`; the trace
  records `llm_reply_rejected` when a transport existed but the reply was
  rejected, `no_llm_transport` otherwise.
- CLI flags: `--trained-reply`, `--trained-dialogue-adapter`,
  `--trained-emotional-adapter`, `--trained-base-model`.

## Part E — Review fixes

Code review (WARNING — 2 HIGH) findings addressed:

- **H1** — `derive_dialogue_act` no longer emits FAREWELL/ACKNOWLEDGE (outside
  the dialogue adapter's fine-tuned vocabulary); farewell → GREETING, thanks →
  RESPOND.
- **H2** — prompt builders are defensive against malformed payloads
  (non-dict `relationship`/`world_context`/`surroundings`, non-dict
  `visible_entities`), and prompt building is wrapped in the transport's
  try/except so nothing raises into cognition.
- **M1** — celebration phrases route to the emotional adapter (the distress
  detector alone missed them).
- **M2** — the thinking-block regex anchors at the start of the generated text
  and no longer over-matches prose.
- **M3** — a failed base-model load backs off (cooldown) instead of retrying on
  every call.
- **M4** — single-adapter configs attach and route correctly; generation
  failures are recorded in `last_error` for observability.
- **M5** — the brain's `system` guardrails are carried into the prompt as a
  bounded `System` line.
- **L1/L3/L4/L7** — deduplicated `_is_correction_like` (import from chat.py),
  readable goal rendering, "I am" celebration forms, `feed_frame` return type.
- **L2** — `VoiceSession.person` is a property synced to the loop so a later
  assignment is what the reply path uses.

## Part F — Commit

Commit to `main` (no push) per the Novi git workflow.

## Out of scope

- Training new adapters (plans 23/24 done).
- Real microphone capture frontend (the voice package's feed contract already
  accepts any AudioFrame stream; a mic frontend is a later body concern).
