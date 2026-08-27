# Unified Multi-Source Input Processing — North Star

**Status:** PLANNED
**Scope:** novi/brain (engine, agent), novi/web (server), novi/integration (multimodal bridge), novi/perception, novi/voice
**Governs:** how every input — terminal, web chat, camera frame, voice turn, room event — reaches the brain, and how every reply leaves it.
**Related:** `README.md` (North Star, Core Principles), `docs/plans/00_IMPLEMENTATION_PROGRAM.md` (lifecycle), `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md` (SCENARIO-V1, turn-taking), `docs/plans/01_BRAIN/16_MULTIMODAL_INTEGRATION.md` (one mind), `docs/plans/01_BRAIN/17_REAL_IO.md` (real devices), `docs/06-soul/07_COMMUNICATION_AND_LIVING_LEXICON.md` (communication rules)

---

## 1. North star

Novi is one mind, not a set of modality handlers. The repo already states this: the project goal is a system that "continuously perceives and understands its environment" rather than waiting for prompts (`README.md` §North Star, Core Principle 1 "Autonomous first"), and `novi/brain/agent.py` (module docstring) makes the brain source-agnostic: "The source never changes how the brain thinks — it only changes which modality fed the loop."

This document extends that principle to its conclusion:

1. **One front door.** Whatever produces an input — an HTTP handler, a CLI command, the STT loop, the camera pipeline, a door sensor — hands the same normalized object to the same bus, and the brain's cognitive step consumes them the same way every time. `docs/plans/01_BRAIN/16_MULTIMODAL_INTEGRATION.md` §1 calls this "one mind": modalities attach context to inputs the brain already accepts; they never bypass `BrainDriver`.
2. **Simultaneity is the normal case, not an edge case.** SCENARIO-V1 in `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md` ("absentee owner") is the reference: Novi is mid-conversation at home while the owner messages remotely, and nothing drops, stalls, or duplicates. Today that works only by accident of coarse locking (see §3). It should work by construction: producers enqueue without blocking, the cognitive loop drains continuously, and arbitration decides what gets said when.
3. **Everything gets processed; answering is a decision.** Every input is admitted into memory/cognition — a camera frame updates world state even when Novi says nothing. A reply is produced through exactly one path — the brain's own `respond()` (`novi/brain/chat.py`, "source-agnostic, brain-owned reply orchestration") — honoring `docs/06-soul/07_COMMUNICATION_AND_LIVING_LEXICON.md` §2: speech renders an approved communicative act; web/TTS layers never decide intentions. Silence remains valid output (`docs/06-soul/07_COMMUNICATION_AND_LIVING_LEXICON.md` §4, "Silence is not failure").
4. **Autonomy owns timing.** Per `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md`'s decided authority boundary: dialogue decides *what* to say, turn-taking decides *when*. The input architecture must leave that boundary intact — the bus delivers facts and demands to cognition; the policy layer arbitrates outbound utterances.

## 2. Requirements

Owner intent, restated as testable requirements:

| # | Requirement (owner verbatim intent) | Current capability | Gap | Planned mechanism |
|---|---|---|---|---|
| R1 | Optimize the code | Three near-copies of reply orchestration in `novi/web/server.py` (`chat_send` ~L402, `listen` ~L478, `chat_send_stream` ~L655) | Duplicated addressee/topic/learning/history logic; per-route behavior differences | Single `submit()` producer API + single response path; web handlers shrink to thin transport adapters |
| R2 | Brain handles multiple inputs, processes everything, comes with a response | `AgentInput` normalization + `BrainDriver.drive()` exist (`novi/brain/agent.py`) | Inputs arriving while another reply composes are queued ad hoc or skipped (background loop skips steps while `_chat_busy`) | Cognition-loop drain: every step consumes pending inputs; each yields an outcome (reply, initiative, or deliberate silence) |
| R3 | Same engine behavior wherever input comes from — terminal, web app, camera, voice | True only inside `BrainDriver`; web routes partially bypass it (`listen` calls `compose_reply`, not `respond`) | Source-dependent orchestration leaked into server code | All sources converge on bus → `drive()`; server keeps only transport concerns |
| R4 | Input can be anything: movement, voice, text, somebody entering the room | Vision/audio frames ingestible; identity events emitted in `novi/integration/multimodal.py` | Room/presence events have no route into cognition; no event-class priority exists | Event-priority class on the bus fed by perception/identity changes (P2) |
| R5 | Multiple inputs AT THE SAME TIME (owner messages remotely while Novi interacts at home) | Serialized by coarse locks: `BrainDriver.lock` held across the whole drive including the LLM call; `_chat_busy` freezes the auto-step loop | Concurrent sources block each other for seconds; a second input waits behind one slow reply | Lock-free enqueue; drain applies inputs under a briefly-held lock; LLM composition outside any shared lock |
| R6 | Reasonable decisions | Reasoning trace + governance exist per step (`engine.py step()`) | No cross-source arbitration at input time (who wins when two people speak at once?) | Priority classes (interrupt > speech > event > ambient) + coalescing; utterance-level arbitration stays in turn-taking (`docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md`) |
| R7 | Cognition improvements | One `step()` per driven input; idle ticks between requests | Steps are triggered by request instead of being a steady heartbeat that absorbs inputs | Step becomes the fixed consumption point; initiative machinery feeds off the same loop |
| R8 | Implementation against the defined docs and north star | Gate-doc family, evidence lineage, deterministic-CI conventions | This architecture existed only implicitly across docs 15/16/17 | This document is the binding reference; phases below name files, tests, and gates |

## 3. Current state (why this doc exists)

Ground truth in code, August 2026:

- `novi/brain/agent.py` — `BrainDriver.drive(AgentInput)` is the designed convergence point (factories `chat/command/voice/vision/audio_event/idle`; helpers `hear`, `command`, `transcribe_and_drive`, `hear_audio`). But `drive()` holds `self.lock` across the entire cycle including `_compose()` → `brain.respond()` → optional local LLM call. One slow reply blocks every other source at the driver for its full duration.
- `novi/web/server.py` — the largest consumer, and the main divergence. `chat_send` does dedup-window checking, sets `_chat_busy`, holds the lock across `ingest_transcript` + `step()`, then calls `brain.respond(...)` with conversation history assembled by the web layer. `listen` re-implements addressee resolution (`resolve_addressee`), topic tracking (`note_user_message`), and learning (`_learn_from_chat`) before calling `compose_reply` instead of `respond`. `chat_send_stream` is a third variant with its own streaming transport closure. `hear` ingests transcripts with no reply path at all.
- `novi/web/server.py` `_loop()` (~L336) — the background auto-step thread skips `brain.step()` whenever `_chat_busy` is set. The whole cognitive loop goes dark for the duration of an LLM call (the code comment cites 10+ s). Perception freshness, initiatives, and event handling all stall behind a single chat reply. The flag exists to suppress duplicate initiative messages — a symptom treated at the wrong layer.
- `novi/integration/multimodal.py` — correctly routes voice turns through `driver.hear()` and attaches person/place context, but its camera loop runs on its own cadence and emits into a private `_events` list that nothing in cognition consumes deterministically.

None of this contradicts the governing docs — `docs/plans/01_BRAIN/16_MULTIMODAL_INTEGRATION.md` deliberately kept the engine untouched ("additive integration"). But the seams accumulated in the wrong place: orchestration moved into the web server instead of staying in the brain. The fix moves the seam inward; it does not invent a second mind.

## 4. Target architecture

```text
SOURCES                          INPUT BUS                     BRAIN                         OUTPUTS
─────────                        ─────────                     ─────                         ───────
web chat (HTTP)          ─┐   priority queues, coalescing     MacBrain.step():             text ──► web chat / SSE
CLI / terminal            ├─► interrupt > speech >    ────►   1. bus.drain(brief lock)     say  ──► speakers (TTS)
voice STT turns           │   event > ambient                 2. admit to memory/world     trace──► event log (audit)
camera frames             │   never blocks producers          3. reason over fused batch
presence / room events   ─┘   drop-oldest per class            4. ONE response path:
                                                              respond()/initiative
                                                              (LLM outside all locks)
```

### 4.1 Data contract

- `AgentInput` (`novi/brain/agent.py`) stays the canonical normalized input. It gains provenance fields: `source_id` (producer identity, e.g. `web:http`, `voice:stt`, `perception:camera`), `submitted_at`, `correlation_id` (set by synchronous callers who await their own reply), and `priority_hint` (producers may request escalation; the bus clamps to policy).
- New `InputRecord` wraps an `AgentInput` with bus metadata: arrival sequence, class, coalesce key, deadline (for aging, §8). The record is what outcomes cite, so "which inputs produced this reply" is always answerable.
- `AgentOutcome` gains `consumed_inputs: list[input_ref]` and `published_to: list[sink]`.

### 4.2 InputBus (new module, `novi/brain/input_bus.py`)

- Four priority classes, matching the escalation order implied by `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md`'s channel-priority table:
  - **interrupt** — barge-in, safety-relevant signals;
  - **speech** — addressed text/voice from any person (web chat and in-room voice are the same class);
  - **event** — identity change, somebody entering the room, object moved, place changed;
  - **ambient** — camera frames, periodic telemetry, background audio features.
- `submit(record)` is lock-free for callers: a small mutex guards only the deque append; it never touches the driver lock or the engine, and returns within microseconds. Bounded queues with drop-oldest per class — the same backpressure policy as `novi/brain/event_bus.py` (doc-10 envelope contract) — so a misbehaving producer cannot wedge the brain.
- Coalescing: consecutive ambient frames collapse to latest; identical events inside a dedup window collapse (reusing EventBus dedup semantics keyed by envelope hash). Speech and interrupts are never coalesced away.
- Producers get a receipt (sequence number); synchronous callers may wait on their correlation id's published outcome — waiting happens caller-side on a per-correlation event, never on a lock the brain needs.

### 4.3 Drain inside the cognition step (`novi/brain/engine.py`)

`MacBrain.step()` opens with `bus.drain(limit=k)`: take up to k pending records, ordered by class then arrival. Each drained input flows through the existing admission paths (`ingest_transcript`, `ingest_audio_frame`, perception admits), fuses into one situation, and produces at most one outbound act per demand class. The step result reports consumed inputs and owed communications.

Consequences:

- The step heartbeat absorbs inputs continuously instead of being spawned per request (R7). An idle tick still steps (curiosity, world-model decay, consolidation); a busy tick drains more.
- Perception stays fresh during long replies by construction — the loop never stops stepping, so there is nothing to "resume".

### 4.4 One response path (`novi/brain/chat.py`, `novi/brain/agent.py`)

Every communicative outcome — regardless of source — is produced by `MacBrain.respond()` or its deterministic fallback (`natural_reply_fallback`). `BrainDriver` splits today's monolithic locked drive into three stages:

1. **apply** — mutate brain state under the driver lock (admissions, learning, world updates): milliseconds.
2. **compose** — run `respond()`/LLM **outside** any shared lock, tagged with the correlation id.
3. **publish** — re-acquire briefly to attach the finished reply to the outcome record and emit it to sinks.

History/recent-turn context is supplied to respond as plain data by whoever holds it; the brain validates and owns the decision. Initiative replies (`_maybe_initiative`) flow through the same publish stage, so they can no longer collide with composed replies (the race `_chat_busy` papers over).

### 4.5 Serialization without deadlock (R5, the SCENARIO-V1 core)

Remote owner sends a chat message while Novi talks with someone at home:

- Both producers call `bus.submit()` concurrently — no shared lock with the brain, so neither blocks the other, the step loop, or any HTTP endpoint.
- The next step drains both. Processing order is priority-then-FIFO: owner message and in-person utterance are both `speech` class, so both are reasoned over in arrival order within the same or adjacent cycles. Nothing lost, nothing waiting on an LLM.
- Outbound arbitration stays where `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md` put it: at most one spoken utterance at a time (speaking lease). If both demand speech, turn-taking acknowledges one socially ("one moment" — `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md` rule 3, relationship-preserving), answers per the channel table, and resumes the paused track explicitly.
- Deadlock freedom argument: there is no moment where a thread holding the brain/driver lock waits on an LLM or network, and no moment where the bus needs a lock the brain holds. Lock hold times are bounded by state-mutation cost and asserted in tests (§6).

### 4.6 Outputs

Replies fan out from the single published outcome, never recomputed per sink: web chat + SSE (streaming *publication*, replacing `chat_send_stream`'s private transport plumbing), `say`-based TTS gated by speak-back and the speaking lease, and the audit/event log. TTS-rendered texts are marked so the mic path can ignore self-voice (see §8).

### 4.6 Mapping to governing docs

This architecture implements, not replaces:

| Governing doc | What it already decided | What this doc adds |
|---|---|---|
| `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md` | Turn-taking ownership, speaking lease, channel priorities, SCENARIO-V1, latency budgets | The inbound plumbing that makes those policies operable under simultaneous sources |
| `docs/plans/01_BRAIN/16_MULTIMODAL_INTEGRATION.md` | "One mind", engine untouched, recognition context attachment | Moves the remaining orchestration seams out of web handlers into brain-owned drain/respond |
| `docs/plans/01_BRAIN/17_REAL_IO.md` | Real devices as provider swaps; graceful degradation per device | Device events enter through the same bus; degradation policy extends to producers |
| `docs/06-soul/07_COMMUNICATION_AND_LIVING_LEXICON.md` | Speech renders approved communicative acts; silence is valid | Guarantees every output sink draws from that single approved act |
| `novi/brain/event_bus.py` (doc-10 contract) | Envelopes, dedup, bounded backpressure, access levels | Reused semantics for the inbound bus; kept separate from outbound audit flow |

### 4.7 Failure and degradation

- **Bus full:** drop-oldest applies per class; ambient loss is benign by design. A dropped speech/interrupt item emits an audit event naming the producer — losing a person's words must never be silent.
- **LLM down:** respond falls back to `natural_reply_fallback` exactly as today; outcomes still publish, so sinks and correlation waiters resolve either way. No input is stranded waiting for a model.
- **Producer crash mid-correlation:** receipts carry no brain state; an unpublished correlation id simply expires. Sinks render "no outcome" rather than hanging — the caller-side wait has a deadline.
- **Brain restart:** the bus is in-memory state; durability stays where it belongs (memory store admissions, chat persistence). Producers re-submit after reconnect; coalescing makes ambient resubmission cheap.

## 5. Worked example — SCENARIO-V1 through the bus

Timeline for the absentee-owner scenario, all times in step ticks:

| Tick | Inputs submitted | Bus state | Step does | Published |
|---|---|---|---|---|
| n | Anna's voice turn "…and then?" (speech) | speech q=[anna] | drain anna → respond → compose starts (LLM, unlocked) | — |
| n+1 | Owner chat "ping" (speech), 4 camera frames (ambient) | speech q=[owner], ambient coalesced to 1 | previous compose still running; loop keeps ticking, perception fresh | — |
| n+2 | — | — | drain [anna-result applied? no—] drain [owner] → reason over both contexts; speaking lease held by home dialog | owner ack queued per policy |
| n+3 | — | — | publish anna reply (correlation c1) → SSE + say; publish owner reply (c2) → web chat; turn-taking sequences utterances | 2 outcomes, ordered |

Failure modes this replaces: today, tick n+1..n+3 would not run at all (auto-step skipped while busy), the owner's message would sit in an HTTP handler blocked on the driver lock, and the second reply would risk colliding with an initiative.

## 6. Acceptance criteria

Falsifiable checks; deterministic unless marked evidence-run:

- [ ] **R1/R3:** After rewiring, `respond(`/`compose_reply(` are called from exactly one package (`novi/brain/`); `novi/web/server.py` handlers contain no addressee/topic/learning/composition logic. Chat, CLI, voice-turn, and `/api/voice/turn` produce identical outcome records for the same scripted input, modulo source/provenance fields.
- [ ] **R2:** N=8 producer threads × M=4 modalities submit 200 mixed inputs against one brain: all delivered exactly once (input refs unique across outcomes, none missing), zero exceptions propagated to producers.
- [ ] **R2/R5:** With a 10 s artificial delay injected into one reply composition, subsequently submitted speech inputs are answered in later cycles; no input dropped; no producer blocked >10 ms in `submit()`; background step keeps ticking throughout (no busy-flag stall).
- [ ] **R4:** A scripted "person entered the room" identity event submitted mid-conversation appears in the next step's consumed-inputs list and reasoning trace.
- [ ] **R5/R8 (SCENARIO-V1):** Simulated interleaving of owner chat + in-home voice dialog completes both threads; home conversation pauses/resumes with the resume decision recorded; at most one outbound utterance at any instant (lease assertion).
- [ ] **R6:** Simultaneous submission across all four classes resolves interrupt > speech > event > ambient; 50 rapid ambient frames coalesce to ≤ 5 processed; duplicate event inside the window processed once.
- [ ] **R7:** p95 `step()` wall time excluding LLM composition ≤ 250 ms on the Mac prototype; max driver/engine lock hold ≤ 50 ms (asserted directly); an initiative-triggering condition fires exactly once (duplicate-initiative regression test).
- [ ] **R8:** Mac evidence run captures the above numbers into the EVIDENCE lineage (`docs/plans/EVIDENCE/` schema); CI covers every criterion not requiring hardware, using repo-standard fakes.

Felt-responsiveness budgets remain `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md` §Latency budgets (VAD endpoint ≤ 300 ms, short-utterance STT ≤ 1.5 s, TTS first audio ≤ 800 ms, barge-in reaction ≤ 500 ms) — measured in evidence runs, never CI gates.

## 7. Phased implementation plan

Each phase lands independently reviewable, fake-tested, and reaches INTEGRATED before the next begins (global lifecycle, `docs/plans/00_IMPLEMENTATION_PROGRAM.md`).

### P0 — Bus + engine drain (the spine)

- Touch points:
  - new `novi/brain/input_bus.py`: classes, queues, coalescing, aging, receipts;
  - `novi/brain/engine.py`: `step()` opens with `bus.drain()`; outcome reports consumed inputs;
  - `novi/brain/agent.py`: `BrainDriver.submit()`; apply/compose/publish split of `drive()`; existing helpers become thin wrappers.
- Tests: `novi/brain/tests/test_input_bus.py` (ordering, coalescing, backpressure/drop-oldest, exactly-once under threads, lock-hold bound), plus engine drain cases in the existing brain suite.
- Web untouched: direct brain calls keep working alongside the bus, so deployment risk stays zero until P1.

### P1 — Web rewiring onto the bus

- Touch points:
  - `novi/web/server.py`: `chat_send`, `listen`, `chat_send_stream`, `hear` become producers + correlation subscribers; delete `_chat_busy` gating and per-route reply logic; SSE streams publication events;
  - `novi/web/integration_api.py`: voice/recognition routes submit instead of calling the driver directly.
- Port-before-delete: dedup window and `[heard]` marker cleaning get tests against their new homes first (they are behaviors, not baggage).
- Acceptance landed here: R1/R3 identity check, R2 concurrency check, R5 stall check.

### P2 — Presence and events feed initiatives

- Touch points:
  - `novi/integration/multimodal.py`: identity changes, place changes, and `pending_enrollment_proposal` submit event-class inputs; private `_events` list becomes a projection of published outcomes;
  - `novi/perception/`: movement/room-event providers emit through the same API;
  - `turn_taking.py` (`docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md`): arbitrates outbound side; speaking lease enforced at publish;
  - SCENARIO-V1 simulation test (multi-track, deterministic fakes).
- Acceptance landed here: R4 presence check, R6 priority check, SCENARIO-V1 criterion.

### P3 — Performance budgets + evidence

- Touch points:
  - instrumentation of step latency, queue depths, lock-hold times following `novi/brain` observability conventions (`docs/specs/brain/21_OBSERVABILITY.md`);
  - Mac evidence pass capturing §6 numbers into the evidence lineage; tune tick rate and drain limits from measurements;
  - register this document in `docs/plans/01_BRAIN/00_BRAIN_IMPLEMENTATION_INDEX.md` (separate patch, per workstream convention).

## 8. Risks and tradeoffs

- **LLM latency vs the step tick.** Composition outside locks means a step can finish while its reply is still composing; late publishes need attribution. Mitigation: correlation ids; UI shows pending state instead of freezing the whole brain. Accepted tradeoff: a fresh world model during long replies is worth the bookkeeping.
- **Priority inversion.** A stream of speech-class inputs can starve events; an interrupt storm can starve everything. Mitigation: per-class bounds, aging (event/ambient items escalate after a deadline), per-class drain limits per step. Tested, not hoped for.
- **Dedup of echoed TTS / self-hearing.** Concurrent speaking and listening means Novi will hear its own `say` output. `docs/plans/01_BRAIN/15_VOICE_CONTINUOUS_DIALOG.md` names self-voice suppression; until acoustic echo cancellation exists, mark TTS-rendered texts and suppress matching transcripts within a window. Imperfect — residual self-hearing stays a logged known issue, not a silent one.
- **Ordering vs fusion.** Draining a batch means several inputs share one reasoning pass; per-input attribution gets fuzzier. Mitigation: outcomes list consumed inputs individually; admissions stay per-input even when the reply is joint.
- **Migration regressions in P1.** The web server carries subtle behaviors (dedup window, `[heard]` marker cleaning, chat persistence, summarization gating). Each is ported with a characterization test before its old home is deleted; double-send and duplicated-initiative regressions have dedicated tests.
- **Two buses problem.** `novi/brain/event_bus.py` (outbound, doc-10 envelopes) and the inbound InputBus stay deliberately separate: one carries observations outward for audit/UI, the other carries demands inward for cognition. Conflating them would make backpressure policy incoherent; keeping them distinct preserves the audited event trail.
- **Scope discipline.** No new cognition lives in the bus — it is plumbing with priorities. If a review finds intelligence creeping into queue policy, that logic belongs in cognition or turn-taking, not the bus.

## 9. Non-goals

No cloud transports anywhere in this path (local/offline-first, README Core Principle 3). No provider-contract changes — STT/TTS/camera swaps stay provider-level per `docs/plans/01_BRAIN/17_REAL_IO.md`. No rewrite of dialogue content rules — the soul docs remain authoritative for what Novi says. No hardware prerequisites: every phase must close on deterministic fakes before real devices are involved.
