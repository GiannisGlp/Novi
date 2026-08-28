# Brain — Dialogue, Unified Answering & Event-Driven Autonomy Maturation Plan

**Status: PLANNED / OPEN**
**Date:** 2026-08-28
**Workstream:** `docs/plans/01_BRAIN/`
**Governs:** how Novi talks and answers — one engine-owned path regardless of input modality (chat / voice / visual / event), improved natural dialogue, multitasking, and **autonomous (proactive) talking when it sees something, hears something, or something changes**.
**Extends, does not replace:** `UNIFIED_INPUT_NORTH_STAR.md` (one front door, one response path, InputBus), `15_VOICE_CONTINUOUS_DIALOG.md` (turn-taking authority, SCENARIO-V1), `19_COGNITION_MATURATION_PLAN.md` (shipped: thin-client web, speaking-lease × initiative, prediction→curiosity, verified tier, cadence), `06-soul/07_COMMUNICATION_AND_LIVING_LEXICON.md` (what Novi says), `16_MULTIMODAL_INTEGRATION.md`, `02_PERCEPTION/02_FACE_AND_OBJECT_RECOGNITION.md` (visual/spatial-event producers).

---

## 0. What already exists (verified against code, 2026-08-28)

The unified input + single-response spine is **already implemented and passing** (full suite ~1,624). Ground truth:

| Requirement (owner verbatim) | Implemented where | Status |
|---|---|---|
| "Input method shouldn't matter" — one front door for chat/voice/visual | `InputBus` (`novi/brain/input_bus.py`), `MacBrain.submit()` + `drain_inputs()` (`engine.py:429,463,523`) — 4 priority classes, coalescing, non-blocking producers | ✅ shipped |
| "Engine should always take control", "answer should come the same way" | `respond()` (`chat.py:736`) = single brain-owned reply path; sources converge on it, no per-route orchestration in `server.py` | ✅ shipped (plan 19 P1) |
| Multitasking / simultaneity / no loop stall | `step()` drains bus first; LLM composition outside locks; speaking lease gates spontaneous output vs composed replies (SCENARIO-V1) | ✅ shipped |
| Natural dialogue (content) | `dialogue.py` — ~1,080 lines: greeted/intro/clarification/continuation/emotional/joke/recall/realtime/reminder/physical-action matchers, quality guardrails (strips assistant phrasing, meta-referential, repetition), `natural_reply_fallback`, discourse + anaphora resolution, vocabulary scope, learned preferences | ✅ deep, shipped |
| Social initiative ("I've been neglected") | `_maybe_initiate` (`chat.py:1245`), `SocialInitiative` budget, souls-neglected trigger, speaking-lease fused | ✅ shipped |
| Prediction-error → curiosity | closed in plan 19 P3 | ✅ shipped |
| Verified cross-modal identity | closed plan 19 P4 | ✅ shipped |
| Word/fast reasoning, spoken reply path | reasoning router, deliberation, `speak()` via TTS | ✅ shipped |

**Model default today:** `DEFAULT_OLLAMA_MODEL = "qwen3:4b"` in `novi/brain/models/ollama_reasoning.py`, and mirrored in `narrator.py`, `summarizer.py`, `conversation_summarizer`, `dialogue.py`, `cli.py`. Web `available_models = ("qwen3:32b","qwen3:8b","qwen3:4b","nemotron-3.5-lightning")`. **Default flipped to qwen3:4b on 2026-08-28 (GAP-D closed).**

---

## 1. The gaps (what "autonomous in every way" still needs)

1. **GAP-A — No event-driven autonomous *speech*.** Today, input is *drained* and world-state updated, but non-text events (`scene.changed`, `presence.entered`, `identity.recognized`, `hearing.anomaly`) are admitted to world/memory and logged — they do **not feed a proactive utterance**. `_maybe_initiate` is *neglect/social* driven only. **Novi is almost always silent unless someone speaks first.** The ask — "talks autonomously when sees something, hears or changes" — is the single biggest open behavior.
2. **GAP-B — Event salience isn't routed into dialogue decisions.** `drain_inputs` admits non-text events to world context but never tells the reply engine "a salient event just happened; open a communicative act about it." No novelty/threshold model decides *which* events are worth *saying* (vs. silently remembering).
3. **GAP-C — Visual modality doesn't reach the spoke path.** Camera produces `detections`/`tracks`/`identities` into world state; nothing turns a *visual* novelty (unfamiliar object, person entered, "your mug moved") into a sentence.
4. **GAP-D — Default model is not qwen3:4b** (currently qwen3.8 / 32b default).
5. **GAP-E — Natural-dialogue breadth is heuristic-first.** The pattern matchers are strong but finite; long freeform natural conversation still depends on an LLM transport. Worth a thin "naturalisation" gap: multimodal grounding into the prompt already exists (`_assemble_world_context`, episodic narrative) but is the sole path; deterministic fallback replies are canned — acceptable for CI, thin for live autonomy.

(Note: some of GAP-A/C is actively being built in parallel — check `git status` before attributing. Grounding truth here is the working tree at time of writing.)

---

## 2. Objective (restated as testables)

- **O1 — Same engine, every modality:** any input (chat, voice, camera frame, room event) reaches the one `respond()` engine and yields the one brain-owned communicative act. (Acceptance: the north-star R1/R3 already pass; keep it true.)
- **O2 — Autonomous proactive speech:** when Novi sees a change, hears something noteworthy, or a person enters/leaves, it can *proactively* speak about it — bounded, prioritised, respecting the speaking lease, never looping on itself.
- **O3 — Natural multimodal dialogue:** a person can talk to Novi naturally (freeform, interruptions, anaphora, emotional, follow-ups) across text/voice — grounded in world, memory, relationships, identity.
- **O4 — default model = qwen3:4b** for the chat/reasoning path.

---

## 3. Design

### A) Event-driven autonomy stream (closes GAP-A/B/C) — the single largest slice
Introduce a **SalienceToUtterance** seam that turns *events* into *candidate utterances*, gated by the same speaking-lease and initiative budget, so proactive speech never collides with a composed reply:

```text
non-speech events (vision detections, scene change, presence, hearing anomaly)
   │   (admitted to world by drain_inputs today)
   ▼
EventSaliencePolicy (new, brain-owned, deterministic)
   ● novelty/threshold: is this worth SAYING vs silently noting?
     - unexpected entity appears (not in memory / novelty>k)
     - expected (remembered) entity disappeared ("your mug — it's gone")
     - person entered/left (identity tier known → greet; unknown → greet+"new to me")
     - hearing anomaly (anomaly + novelty>k)
   ● recency/cooldown: avoid repeating the same event (per-kind, per-entity cooldown)
   ● interest cap: max N spontaneous remarks per window; social-overload honored
   │
   ▼
   produces CandidateInitiative{kind, entity, text, reason, affordance}
   feeds _maybe_initiate → acquire_speaking_lease → speak()
```

- Wiring: consume **already-drained** events in `step()` (presence/scene/vision/audio) → SalienceEvaluator selects ≤1 candidate/cycle → emits `speech.autonomous` → route through the SAME `respond()`-style naturalization (so proactive speech reads like Novi, not a canned string) → speaking-lease + social budget guard.
- Vision promise: when `novi/perception` resolves a *recognized object/person* (or a proposal), the evaluator gets a named entity to talk about ("your red mug — I noticed it moved"). This is the bridge to GAP-C from the spatial-observation workstream.

**`CandidateInitiative` schema** (mirrors the existing `SocialInitiative.propose` return shape, extended with the event provenance so the naturalizer can ground the remark):

```text
CandidateInitiative{
  kind: str,            # "presence.greet" | "presence.farewell" | "novelty.comment"
                        # | "disappearance.note" | "identity.greet" | "hearing.anomaly"
  entity: str,          # named entity when known ("alice", "your red mug"), else ""
  text: str,            # naturalized utterance (post-guardrail)
  reason: str,          # machine-readable salience justification ("novel_entity:novelty=0.9")
  affordance: str,      # "greet" | "comment" | "ask" | "note" — what the act does
  source_event: dict,   # the drained event record (kind/source/seq) for traceability
}
```

**`EventSaliencePolicy` decision table** (deterministic; grounded in the event kinds already classified `PRI_EVENT` in `input_bus.py`):

| Event kind | Salient when | Cooldown (per kind+entity) | Example utterance |
|---|---|---|---|
| `presence.entered` | identity tier known → greet; unknown → greet + "new to me" | per-person | "Hey Alice — good to see you." |
| `presence.left` | remembered person/entity present before | per-person | "Alice headed out." |
| `scene.changed` | novelty > k (unexpected entity appears) | per-entity | "I noticed your red mug moved." |
| `identity.recognized` | recognized person not greeted this session | per-person | "Oh, it's you, Alice." |
| `hearing.anomaly` | anomaly + novelty > k | per-kind | "That sound was odd — did you hear it?" |

The policy reuses the `SocialInitiative` config pattern (`max_per_session`, `cooldown`, budget) so proactive speech shares one throttle with neglect-driven initiative; it never fires while `has_active_goal` or the speaking lease is held.

### B) Natural, unified spoken `respond()` — harden
- Keep `respond()` the one path; add an **autonomous-utterance variant** `respond_event(event, addressee_ctx)` that reuses the same political/affect/guardrail pipeline but is seeded from an event rather than text.
- Extend the dialogue naturalization guardrails coverage to proactive remarks (prevent "notification-speak").
- Ground proactive utterances in world/memory (the mug moved because memory says it was on the counter).

### C) Multitasking guarantee (verify, don't rebuild)
- Already structural. Add a **CONCURRENCY stress acceptance** (SCENARIO-V1 + a proactive remark both pending in the same tick ⇒ at most one utterance, ordered, resume decision recorded) as a permanent regression.

### D) Default model → qwen3:4b
- Change `DEFAULT_OLLAMA_MODEL` to `"qwen3:4b"` in `novi/brain/models/ollama_reasoning.py` (and the mirrored defaults in `narrator.py`, `summarizer.py`, `conversation_summarizer`, `dialogue.py`, `cli.py` where they call fall back to default).
- Keep `qwen3:32b / qwen3:8b / nemotron-3.5-lightning` in `available_models`; update web test expectations (`test_web.py` default assertions) to the new default; document the switch (`--ollama-model` still overrides, and the web model switcher still works).

---

## 4. Deterministic testing (CI, no hardware)
Synthetic providers (scripted frames/events, scripted STT/TTS, deterministic LLM stub):
- event→initiative gating: novel vs familiar, cooldown, repeated-event suppression, max-per-turn cap;
- autonomous speech respects speaking-lease (no collide with composed reply) — SCENARIO-V1 + proactive regression;
- proactive remark grounded in memory ("mug moved" references prior episode);
- naturalisation guardrails apply to autonomous remarks (no assistant-speak, no repeats);
- plurally: the same scripted input via chat submit, voice submit, event submit produce the same engine decision (modulo source fields);
- model default: `OllamaReasoningProvider().model == "qwen3:4b"` default; web `/api/model` returns default without explicit switch.

**Concrete test homes** (new files, following the existing `novi/brain/tests/` layout):
- `test_salience_policy.py` — pure unit tests of `EventSaliencePolicy`/`SurgeSalienceEvaluator`: novelty threshold, per-kind+entity cooldown, repeated-event suppression, max-per-window cap, `has_active_goal`/lease suppression. No engine needed.
- `test_autonomous_speech.py` — engine-level: scripted `presence.entered`/`scene.changed`/`hearing.anomaly` events → exactly one `speech.autonomous` per cycle, grounded in memory, guardrails applied, never colliding with a composed reply (SCENARIO-V1 + proactive in the same tick).
- `test_respond_event.py` — `respond_event(event, addressee_ctx)` returns the same engine decision as the equivalent chat/voice submit (modulo source fields).
- `test_model_default.py` — `OllamaReasoningProvider().model == "qwen3:4b"`; web `/api/model` default without explicit switch (update existing `test_web.py` assertions).

## 5. Evidence gates (on-Mac / real devices)
1. **Proactive run 001:** a person walks in → Novi greets them unprompted; an unfamiliar object appears → Novi comments/asks; an object it remembers disappears → Novi notes it. All recorded, reproducible trace (`speech.autonomous` events).
2. **Natural live session:** 10-minute natural voice dialog + 2 owner chat messages injected mid-conversation; no drop; multitask active.
3. **Regression wall green** with real devices (voice on) and absent (deterministic fallbacks).

## 6. Scope of first implementation (smallest closing diff)
1. `SurgeSalienceEvaluator` + `respond_event()` + autonomous utterance gating + tests (GAP-A/B/C core). (brain-engine-zone — per scoped footprint, in `novi/brain/`.) New: `novi/brain/salience.py` (policy + evaluator), `novi/brain/chat.py` `respond_event()`, tests per §4.
2. Wire into `step()`: seed Salience from drained event records + perception detections/identity.
3. Model default flip + test updates (trivial; safe separate patch).

## 7. Non-Do / boundaries
- No second DB; no cloud.
- No rewrite of dialogue content rules — soul docs remain authoritative for *what* Novi says; this plan adds *when* (proactiveness) and keeps the answer path unified.
- `novi/brain/` is a **parallel-workstation zone**: coordination edits inside it must be staged per scoped-footprint rule; `novi/web/ui/` (React SPA) untouched.
- Autonomy must never invent events (deterministic salience only; honest degradation).

## 8. Status
**PLANNED / OPEN.** Unified input + single response + dialogue depth are shipped (see §0). Registered in `00_BRAIN_IMPLEMENTATION_INDEX.md` (2026-08-28).

**Implementation (2026-08-28, smallest closing diff §6 + GAP-E grounding):** `novi/brain/salience.py` (`EventSaliencePolicy` + `SurgeSalienceEvaluator`), `respond_event()` in `chat.py` (with optional memory grounding), engine wiring (`event_autonomy_enabled` config, `_maybe_autonomous_speech` in `step()`, drained-event payload, `_memory_grounding`), the `qwen3:4b` default flip, and the SCENARIO-V1 concurrency regression are **implemented** with deterministic tests (`test_salience_policy.py`, `test_respond_event.py`, `test_autonomous_speech.py`, `test_model_default.py`). Full brain suite green (1,464 passed). Remaining: on-Mac evidence runs (§5).

---

## Appendix — model default inventory (current wiring)
`DEFAULT_OLLAMA_MODEL`:
- `novi/brain/models/ollama_reasoning.py:11` — **source of truth for reasoning** (`"qwen3:4b"` as of 2026-08-28)
- mirrored: `models/narrator.py:16`, `models/summarizer.py:15`, `dialogue.py:32`, `brain/cli.py` (fallback), and `novi/brain/models/conversation_summarizer` (via its own default)
- web default: `server.py` uses `DEFAULT_OLLAMA_MODEL`; `available_models=(qwen3:32b,qwen3:8b,qwen3:4b,nemotron-3.5-lightning)`; `test_web.py` asserts availability/switchability (not the default value).