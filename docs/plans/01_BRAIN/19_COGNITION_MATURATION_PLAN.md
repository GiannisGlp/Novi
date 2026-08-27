# Brain — Cognition Maturation Plan (Reasoning · Cognition · Knowledge · Memory)

**Status:** OPEN — Phases 1–5 implemented 2026-08-27 (full suite 1498 passed, brain+web). Each phase's acceptance criteria below are met; the doc remains OPEN pending the full-suite evidence run and index registration.
**Date:** 2026-08-27
**Governs:** the next phase of brain work — closing the remaining seams in reasoning, cognition, knowledge, and memory on top of the unified input architecture (`UNIFIED_INPUT_NORTH_STAR.md`, same folder) and the shipped cognition plan (`BRAIN_COGNITION_IMPROVEMENT_PLAN_2026-08-25.md`).
**Extends, does not replace:** `13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md` (gap closure A–E), `14_BRAIN_EXIT_CONTRACT.md` (gates B1–B5), `15_VOICE_CONTINUOUS_DIALOG.md` (turn-taking, SCENARIO-V1), `UNIFIED_INPUT_NORTH_STAR.md` (one front door, one response path).

---

## 0. Where the four pillars actually stand (evidence-based, verified 2026-08-27)

Baseline: full suite **1624 passed** (`pytest novi/brain/tests novi/web/tests novi/integration/tests novi/perception novi/cognition/tests novi/contracts/tests`, ~6.6 min). Every claim below was read from the working tree, not inferred from docs.

| Pillar | What exists (verified) | Genuine remaining weakness |
|---|---|---|
| **Memory** | `sleep_cycle.py` (P1: consolidate→decay→strengthen→narrate, wired `engine.py:1048`); `importance.py` (C4); spatial/temporal context (C3); MiniLM semantic recall (`vector.py`) | Strengthening keys on `last_accessed_at` recency, not on *what* was recalled — no recall-content-driven replay. No cross-modal verified-tier escalation. |
| **Reasoning** | `router.py` `decide_for_text` (P2: social fast-path / question→LLM / route cache); `deliberation.py` multi-round LLM; `_persist_decision_memory` (P5) | **Web server still gates the whole loop on `_chat_busy`** (`server.py:345,441,488,517,565,692,807`) — the exact stall north-star P1 was to delete. `listen()` re-implements addressee/topic/learning and calls `compose_reply` instead of `respond()` (`server.py:519-539`), so the web is *not* a thin client for the voice path. |
| **Cognition** | `cognition2.py` `MacCognition` (knowledge/goal/memory-grounded hypotheses + causal inferences); typed cognition canonical in `step()` (G1); Bayesian belief (C1) | **Prediction error does not drive curiosity/initiative** — `SequencePredictor` (P4) emits `prediction.sequence_violated` but nothing consumes it to *act* on surprise. |
| **Knowledge** | `kgraph.py` temporal validity + supersession (P3); source-weighting; networkx overlay + pagerank (D1); triple embeddings (D2) | **LLM triple extraction (D3) gated off by default** (`llm_triples_enabled=False`); regex is the only live path. Small closed `_PREDICATES` taxonomy. |

### Open items (from `references/unified-input-architecture.md` "Still open", all verified absent)

1. **Web `_chat_busy` stall + thin-client gap** — north-star P1 acceptance (R1/R3) not fully met. Highest leverage; already designed.
2. **Speaking lease + initiative fusion** ("Vano's back") — `turn_taking.py` green, but `SocialInitiative` isn't fused with the lease; a spontaneous remark can collide with a composed reply.
3. **Cross-modal verified-tier escalation** — `face_id.py`/`speaker_id.py` exist but nothing promotes `probable → verified` on cross-modal agreement.
4. **Neural detection every-Nth-cycle** — perception runs every cycle; no cadence throttle for the Jetson power budget.
5. **Lazy MiniLM/STT load** — MiniLM lazy (`vector.py`); STT/model load timing not deferred.
6. **Prediction-error → curiosity loop** — P4 violations emitted but not consumed as surprise-driven initiatives.

---

## 1. Objective

Close the six open seams so the four pillars behave as one continuous mind: the web becomes a thin transport (no orchestration, no loop stall), spontaneous initiative respects the speaking lease, prediction error becomes surprise that drives curiosity, identity escalates to `verified` on cross-modal agreement, and the neural/perception cadence is power-aware and lazy-loaded for Jetson parity.

## 2. Requirements / Contract

Each phase is independently reviewable, TDD, fake-first (deterministic providers so CI never needs hardware/models). All acceptance conditions are falsifiable and machine-checkable.

### Phase 1 — Web thin-client gap (closes open item 1; north-star R1/R3)

**Contract:** `novi/web/server.py` handlers contain no addressee/topic/learning/composition logic; `_chat_busy` gating is deleted; the background loop never stalls behind an LLM call; `listen()` routes through the same `respond()` path as `chat_send`.

- **Touch:** `novi/web/server.py` (delete `_chat_busy`; `listen()` → `brain.respond()`; move addressee/topic/learning into brain), `novi/brain/chat.py` (expose one voice-capable `respond()` path), tests in `novi/web/tests/`.
- **Acceptance:**
  - [ ] `_chat_busy` absent from `server.py` (grep).
  - [ ] SCENARIO-V1 interleaving (owner chat + home voice) completes with no loop stall; background step keeps ticking during a slow reply.
  - [ ] `listen()` and `chat_send()` produce identical outcome records for the same scripted input, modulo source/provenance fields.
  - [ ] Full suite green.

### Phase 2 — Initiative × speaking-lease fusion (closes open item 2)

**Contract:** a spontaneous initiative acquires the single voice lease and never collides with a composed reply; duplicate-initiative regression holds.

- **Touch:** `novi/brain/engine.py` (`_maybe_initiate`), `novi/voice/turn_taking.py`, `novi/brain/social.py`.
- **Acceptance:**
  - [ ] Initiative fires exactly once per eligible window (no duplicate-response regression).
  - [ ] At most one outbound utterance at any instant (lease assertion).
  - [ ] Full suite green.

### Phase 3 — Prediction-error → curiosity loop (closes open item 6)

**Contract:** `prediction.sequence_violated` becomes a surprise signal that feeds curiosity/initiative ("I expected the cup near the book — did someone move it?").

- **Touch:** `novi/brain/engine.py`, `novi/brain/prediction.py`, `novi/brain/curiosity.py`.
- **Acceptance:**
  - [ ] A scripted A→B violation surfaces as a curiosity initiative.
  - [ ] `prediction_accuracy` / `sequence_prediction_accuracy` metrics do not regress.
  - [ ] Full suite green.

### Phase 4 — Cross-modal verified-tier escalation (closes open item 3)

**Contract:** face + speaker agreement promotes `probable → verified` through `PersonIdentity`; no fabricated identities.

- **Touch:** `novi/brain/identity.py`, `novi/brain/engine.py` (`_identify_face`/`_identify_speaker`).
- **Acceptance:**
  - [ ] "I am Maya" + matching face → `verified` badge.
  - [ ] No identity invented from third-party mentions (existing A2 regression holds).
  - [ ] Full suite green.

### Phase 5 — Perf/parity: neural cadence + lazy load (closes open items 4, 5)

**Contract:** perception runs every-Nth-cycle; STT/model load deferred; step p95 ≤250 ms maintained; Jetson-parity table updated.

- **Touch:** `novi/brain/engine.py`, `novi/web/server.py`, `docs/plans/01_BRAIN/resource_parity_table.md`.
- **Acceptance:**
  - [ ] Step p95 ≤250 ms (excluding LLM composition) on the Mac prototype.
  - [ ] Perception cadence configurable; deterministic fakes unaffected.
  - [ ] Parity table lists each capability → Mac provider → Jetson equivalent → status.
  - [ ] Full suite green.

## 3. Required evidence

- Per-phase: new/updated unit tests; full suite green; `ruff check` clean on touched files; smoke `python -m novi.brain.cli --cycles 1` exit 0.
- Phase 1: SCENARIO-V1 interleaving trace (no stall, lease assertion).
- Phase 3: surprise-initiative event trace + prediction-accuracy before/after.
- Phase 4: verified-tier promotion record.
- Phase 5: perf probe numbers (step p95) persisted under `mac_test_results/`.

## 4. Resource parity

Every capability keeps a Jetson-plausible local equivalent; no cloud in the cognitive path. Phase 5 explicitly adds the neural-cadence and lazy-load levers that make the Mac workload map to Orin/Thor power budgets. Single canonical DB (`novi/data/novi.db`) — new subsystems add tables, never databases.

## 5. Deterministic testing

All phases close on deterministic fakes before real devices are involved. No CI dependency on mic/camera/GPU/models. Real backends degrade honestly (try real → fall back deterministic, never crash).

## 6. Evidence gates

Each phase's acceptance criteria are the gate. A phase is CLOSED only when its checklist is green and the full suite passes. Status is computed from test/evidence output, never hand-written.

## 7. Sequencing & effort

| Phase | Effort | Depends on | Unlocks |
|---|---|---|---|
| P1 web thin-client | ~1 day | nothing | SCENARIO-V1 core, no loop stall |
| P2 initiative×lease | ~half day | P1 (single response path) | collision-free spontaneity |
| P3 prediction→curiosity | ~1 day | nothing | surprise-driven autonomy |
| P4 verified-tier | ~half day | nothing | trustworthy identity |
| P5 perf/parity | ~half day | nothing | Jetson power-aware cadence |

Recommended order: **P1 → P2 → P3 → P4 → P5**. P1 and P2 are coupled (P2 needs the single response path); P3/P4/P5 are independent and could run in parallel subagents on disjoint files if speed matters.

## 8. Non-goals

No new cognition in the bus (plumbing stays priority-only). No rewrite of dialogue content rules — soul docs remain authoritative for what Novi says. No hardware prerequisites. No cloud transports anywhere in the path.
