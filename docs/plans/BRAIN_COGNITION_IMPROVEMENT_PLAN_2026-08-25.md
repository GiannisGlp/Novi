# Brain & Cognition Improvement Plan — 2026-08-25

**Governs:** the next phase of brain work — maturing cognition, reasoning, knowledge, and memory on top of the unified input architecture (`UNIFIED_INPUT_NORTH_STAR.md`, same folder).

**Status:** planned. Each phase lists exact files touched, acceptance criteria, and measured baselines where they exist.

---

## 0. Where the five pillars actually stand (evidence-based)

| Pillar | What exists | Real weakness |
|---|---|---|
| **Brain (loop)** | Unified InputBus, drain-per-cycle, one response path (`novi/brain/input_bus.py`, `engine.py step()`) | Inputs consumed but **cross-input reasoning is shallow** — each speech turn reasoned in isolation; no dialogue-level goals spanning cycles |
| **Cognition** | BeliefSystem, Expectations, PredictionEngine, SituationModel, Attention, Reflection (`novi/brain/{b1_cognition,prediction,situation_model,attention,reflection}.py`) | Predictions are only *"will this entity persist?"* — no cause→effect or temporal-sequence learning; reflection logs but rarely changes behavior |
| **Reasoning** | Router (confidence<0.6→LLM), Deliberative multi-round provider, deterministic fallback (`novi/brain/models/{router,deliberation,reasoning}.py`) | Router is **input-blind**: a factual question and a casual greeting get identical treatment; no cost-aware routing; deliberation rounds not persisted as reusable conclusions |
| **Knowledge** | Triple graph + contradiction detection, regex + LLM extraction (`novi/brain/kgraph.py`, `knowledge_extraction.py`) | Regex extraction is brittle; **no temporal validity** (facts never expire); paraphrases duplicate ("alice moved door" ≠ "door was moved by alice"); no relation taxonomy |
| **Memory** | Episodic store + FTS + vectors (MiniLM 384d), SummaryConsolidator, decay fields (`novi/brain/storage.py`, `consolidation.py`) | Consolidator runs but **nothing schedules it** like a sleep cycle; no replay-driven strengthening; recall doesn't boost consolidation targets |

Measured baselines (from `docs/audits/PERF_PROBE_2026-08-24.md`): neural step p95 144ms (18% of the 800ms tick), hash recall 2.4ms, MiniLM recall 7.8ms. All phases must keep step p95 ≤250ms (north star §6).

---

## P1 — Sleep cycle & memory maturation *(biggest bang — start here)*

Memory maturity compounds into everything else: better recall → better grounding → better replies.

**New:** `novi/brain/sleep_cycle.py`
- Background "sleep" phase every N cycles (default 500 ticks, configurable):
  1. Run `SummaryConsolidator` over episodic groups not yet summarized
  2. Decay memories whose `expires_at` passed / retention policy says so
  3. **Strengthen recalled memories** — bump confidence / clear decay flag for records with recent `last_accessed_at` (use it like a brain uses replay)
  4. Re-summarize stale summaries through the LLM narrator when available; deterministic path stays CI-safe
- Emits auditable events: `sleep.started`, `sleep.consolidated {groups, summaries}`, `sleep.decayed {count}`, `sleep.strengthened {ids}`

**Touch:** `engine.py` (schedule hook inside the auto-step loop), `consolidation.py` (expose per-group idempotency state), `storage.py` (strength/decay helpers), `scripts/mac-web.sh` env knob `NOVI_SLEEP_EVERY`.

**Accept criteria:**
- [ ] After 500 cycles with chatter, `summary`-type memories exist per entity group and raw episodes are marked consolidated
- [ ] A memory recalled 5× has measurably higher confidence than an untouched twin
- [ ] Full suite green; sleep phase adds <50ms to the tick that hosts it

---

## P2 — Input-aware reasoning router

The bus already classifies every input (interrupt > speech > event > ambient) — use that at routing time.

**Touch:** `novi/brain/models/router.py`, small plumbing in `engine.py` (pass input classes of the current cycle into `decide()`).

- Question/factual intents (`what/when/where/who/how/why`, entity lookups) → **always LLM**
- Greetings, acknowledgments, thanks, check-ins → **deterministic only** (skip the ~5s LLM latency; these already have warm canned replies in `chat.py`)
- Safety-relevant situations → **LLM mandatory**, never skip on latency
- Route cache: identical situation-hash within N cycles reuses the prior route decision
- Report per-class route counts in `/api/state` observability block

**Accept criteria:**
- [ ] Greeting turn replies in <100ms end-to-end without Ollama round-trip
- [ ] Factual question routes to LLM even at high deterministic confidence
- [ ] Route log shows per-input-class counts; suite green

---

## P3 — Temporal knowledge

Facts should have validity windows, and contradictions should become supersessions.

**Touch:** `novi/brain/storage.py` (schema migration in the one DB `novi/data/novi.db`), `kgraph.py`, `_learn_triples()` in `chat.py`.

- Add `valid_from` / `valid_until` (+ `superseded_by`) columns via migration; old rows default open-ended
- Contradiction handling: instead of flagging conflict, close the old triple's window and link to the successor (history preserved, current view clean)
- Source-confidence weighting: camera/perception-sourced facts outrank hearsay from speech when scoring retrieval
- Optional relation taxonomy constant (small closed set: `moved|is_at|likes|knows|owns|part_of`) to cut regex-extraction duplicates

**Accept criteria:**
- [ ] "alice moved the door" then later "alice moved the chair" leaves both triples queryable with non-overlapping validity windows
- [ ] Knowledge context endpoint returns only currently-valid facts by default, history on request
- [ ] Migration is idempotent; single-DB rule respected (no new database)

---

## P4 — Causal prediction v2

Teach Novi to be *surprised* — surprise drives curiosity initiatives.

**Touch:** `novi/brain/prediction.py`, `expectations` wiring already present in `engine.py`.

- Learn temporal sequences from the event log: "after A appears, B tends to appear within k cycles"
- Score sequence predictions like persistence predictions (confirmed/violated + rolling accuracy metric)
- Violated sequences emit expectation violations → existing curiosity/initiative path can act on them ("I expected the cup near the book — did someone move it?")

**Accept criteria:**
- [ ] Synthetic scenario: A→B co-occurrence learned within M repetitions, prediction fires on next A
- [ ] Violations surface as `prediction.violated` events and are visible in the web event log
- [ ] Persistence-prediction accuracy metric does not regress

---

## P5 — Deliberation memory

Persist *why*, not just *what*.

**Touch:** `novi/brain/chat.py` (`respond()` grounding), `storage.py` (new table or memory_type), `engine.py`.

- Persist each deliberation's winning rationale as a first-class memory (`memory_type="decision"`): situation, chosen action, rejected alternatives, reason
- Recall them on similar situations (embedding match) → Novi can explain "last time I chose X because Y" and avoid re-running rejected reasoning
- Surfaced in the UI reasoning trace as a "previous decision" line when a match exists

**Accept criteria:**
- [ ] Same situation twice → second run cites the first decision in its trace
- [ ] Decisions survive restart (single canonical DB)

---

## Sequencing & effort

| Phase | Effort | Depends on | Unlocks |
|---|---|---|---|
| P1 sleep cycle | ~half day | nothing | gist-level recall, memory hygiene |
| P2 router | ~half day | nothing (bus classes exist) | fast greetings, smart LLM spend |
| P3 temporal KG | ~1 day | P1 optional | honest fact expiry, cleaner contradictions |
| P4 causal prediction | ~1 day | P3 helps | surprise-driven curiosity |
| P5 deliberation memory | ~half day | P1 (memory types) | self-explanation, consistency |

Recommended order: **P1 → P2 → P3 → P4 → P5**. P1 and P2 are independent and could run in parallel subagents on disjoint files if speed matters.

## Non-goals (unchanged)

No cloud in the cognitive path; every capability stays Jetson-plausible local inference. Single canonical DB (`novi/data/novi.db`) — new subsystems add tables, never databases. Soul docs remain authoritative for anything communicative.
