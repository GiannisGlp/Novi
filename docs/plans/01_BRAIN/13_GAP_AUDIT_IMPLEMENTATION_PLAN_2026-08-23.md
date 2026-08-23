# Gap Audit Follow-Up — Implementation Status & Plan
**Date:** 2026-08-23
**Source:** [`docs/audits/NOVI_BRAIN_GAP_AND_IMPROVEMENT_AUDIT_2026-08-23.md`](../../audits/NOVI_BRAIN_GAP_AND_IMPROVEMENT_AUDIT_2026-08-23.md)
**Method:** every audit claim re-verified against the current code (post-consolidation layout, `MAC_BRAIN/` → `novi/brain/`). File:line evidence below is from the working tree at commit `ff8b2a6`.

---

## 1. What the audit asked for that is ALREADY DONE

The audit predates several commits; a large part of its P0 slice has landed. Do **not** redo these.

| Audit item | Status | Evidence |
|---|---|---|
| Default web reasoning to `router` | ✅ Done | `novi/web/server.py:75` (`reasoning: str = "router"`), CLI default too (line 1295) |
| MiniLM embeddings replacing hash-only recall | ✅ Done | `novi/brain/vector.py:55-100` — `MiniLMEmbedding` (all-MiniLM-L6-v2, MPS, lazy) with `HashingEmbedding` fallback |
| Live state/attention/context/soul/identity/memory endpoints | ✅ Done | `novi/web/server.py`: `/api/state`, `/api/attention`, `/api/context`, `/api/soul`, `/api/identity`, `/api/memory`, `/api/knowledge` |
| SSE event stream + streaming chat tokens | ✅ Done | `/api/events/stream` + frontend `EventSource` (`index.html:890`); token SSE via `POST /api/chat/stream` (`index.html:728`) |
| Planner wired into `step()` | ✅ Done | `engine.py:877` emits `plan.created`; `step()` advances plans (`engine.py:598-603`) and completes them (`777-780`) |
| Brain-owned reply orchestration | ✅ Done | `novi/brain/chat.py:586` `respond()`; web is a thin client (`ff8b2a6`) |
| Identity provider boundary (face/speaker injectable) | ✅ Boundary done | `engine.py:142-143, 231-232` constructor params; `_identify_face` delegates (`1684-1690`) — but no concrete providers yet (see §2) |
| P0 gate surfaced in web | ✅ Done | `/api/p0-gate` → `brain.p0_gate()` (`server.py:1149-1153`) |
| Affect reaching dialogue tone | ✅ Largely done | `chat.py:563-567` attaches `affect_expression(affect)` directive per docs/06-soul/05 §12/§14; praise signal handled in `dialogue.py:703-727` |

## 2. What is STILL MISSING (verified gaps)

Ordered by leverage. These are the implementation targets.

### G1 — Typed cognition not canonical in the loop (audit P0, still open)
`Brain.cognition_typed()` exists (`engine.py:1469`) and caches `_last_typed_cognition`, but **nothing calls it inside `step()`** — it remains a debug entry point. The main loop still runs on the legacy `Situation` dataclass; typed `SituationState/PersonContext/IntentHypothesis/Prediction` are not emitted per cycle.
Evidence: zero call sites of `self.cognition_typed()` in `engine.py`.

### G2 — Addressee resolution is still regex (audit P0, still open)
`web/server.py:412` and `:594` still do `addressee = next((ref for ref in self.brain._entities_in_text(text) ...))` — capitalized-word regex that invents people. "I am X" is learned as a `likes` preference, not as identity via the speech modality. The `PersonIdentity` tier system exists but chat does not use it for addressee resolution.

### G3 — No discourse state / anaphora (audit §2.5, open)
`discourse.py` does not exist. Topic extraction stays keyword-based (`dialogue.py:_extract_topic`); "is it still there?" cannot resolve `it`. `ContextPackage` is produced by `ContextAssembler` but `compose_reply` still builds prompts ad hoc rather than from one grounding package.

### G4 — Face/speaker providers unimplemented (audit §2.5/P1, open)
The injection boundary exists (see §1 row 7) but no concrete `face_id.py`/`speaker_id.py` modules exist; defaults are `None`. Cross-modal verification to `verified` tier can never trigger today.

### G5 — BeliefSystem is linear, not Bayesian (audit §2.1, open)
`cognition.py:24-25` — `LEARN_GAIN = 0.25`, `CONTRADICTION_FLIP_EVIDENCE = 2`; update is additive clamp (`:71`), contradiction handling threshold-based (`:77`). No source-class weighting, no multiplicative decay.

### G6 — Memory classes registered but not enforced (audit §2.2, open)
`MemoryClassDecisionRegistry` is instantiated (`engine.py:324-325`) but only consumed for `.snapshot()` status output (`engine.py:1831`). Admission (`utterance/perception/goal_outcome`) does not route through `decide()`; everything stays flat.

### G7 — Spatial/temporal context never filled (audit P2, open)
Zero matches for `spatial_context`/`temporal_context` in `engine.py` admits — `retrieve("kitchen")` cannot find things seen in the kitchen.

### G8 — Consolidation time-based only; importance = confidence (audit §2.2, open)
No `importance` weighting anywhere in `consolidation.py`/`storage.py`; `_memory_score` uses `record.confidence` as importance proxy. No cognition-derived importance score.

### G9 — Knowledge graph has no reasoning (audit §2.3, open)
`kgraph.py`: no networkx overlay, no multi-hop query, no triple embeddings/semantic search, no LLM-grounded triple extraction. Note: `networkx` is installed transitively but NOT declared in `pyproject.toml` extras — needs an explicit optional extra or pure-python fallback to respect the stdlib-core constraint.

### G10 — Prediction → expectation → learning loop missing (audit §2.1/lever 4, open)
No `PredictionEngine`; `CosmosReason2` adapter exists but nothing invokes it from the loop; `ExpectationSystem` stays hardcoded (`consistency=2`), not prediction-error driven. Only docstring mention of PREDICTED in `engine.py:1730`.

### G11 — Soul doesn't learn or steer attention (audit §2.4, open)
No `Soul.learn_from_interaction`, no `motivation_priority()` consumed by `AttentionRanker`/`BoundedGoalController` (zero matches in `soul.py`/`attention.py`/`autonomy.py`). Traits are static; affect reaches dialogue but personality never drifts.

### G12 — Benchmarks & evidence for the new capabilities absent (audit §3/P2, open)
No `vector_bench` (p99 retrieve @5k), no reasoning-calibration harness, no prediction-accuracy metric. `benchmarks/` holds only `arch_close_003_gate.py`; storage benchmark exists but measures SQLite, not semantic recall.

### G13 — `ARCHITECTURE_CLARITY.md` never written (audit §0 fix, open)
Also breaks the architecture-integrity CI gate today (unresolved reference from the gap audit itself).

---

## 3. Implementation Plan

Sequencing principle: close the two open P0 gaps first (smallest diff, highest coherence gain), then context awareness (the stated user priority), then memory/cognition semantics, then the learning loops, then measurement.

### Phase A — Close the open P0 gaps *(start here; ~1-2 days)* — **DONE 2026-08-23**

Implementation status (verified: full suite 1,299 passed, smoke `--cycles 1` exit 0):

- [x] **A1** `cognition_typed()` now runs inside every `step()` with the same knowledge/goal/recall grounding as the legacy cycle (`engine.py`); pass-through params added; step result exposes `typed_situation_id`; `cognition.typed` emitted per cycle. Tests: `novi/brain/tests/test_typed_cognition_loop.py` (5).
- [x] **A2** `ChatMixin.resolve_addressee()` implements identity-first resolution (explicit person → speech self-introduction binds name at 0.6/probable → bound-name preference → legacy regex fallback). `respond()` and both `web/server.py` chat paths route through it. `ingest_transcript` no longer invents identities from third-party mentions; `_INTRO` extended to cover "it's me X"; introduced names stored lowercase per entity-ref convention. Tests: `test_identity_addressee.py` (8) + updated `test_identity.py` pin.
- Remaining from original A2 text: surfacing the identity tier in the chat header payload (small UI follow-up, deferred to Phase B3).

**A1. Make typed cognition canonical in `step()`** — closes G1 ✅ *(implemented 2026-08-23; see Phase A status above)*
- Files: `novi/brain/engine.py` (+ tests in `novi/brain/tests/test_cognition_typed.py`)
- Change: call `self.cognition_typed(observations)` inside `step()` after perception/world update; treat the returned snapshot as the canonical situation record; keep legacy `Situation` as a projection built *from* the typed snapshot (backward-compat shim). Emit `cognition.typed` on the event bus with the snapshot id.
- Tests: same world+memory input → identical situation id (determinism); step output contains typed fields; legacy projection equality.
- Acceptance: `GET /api/context` serves the typed snapshot; two competing Situation types no longer both authoritative.

**A2. Identity-first addressee resolution** — closes G2 ✅ *(implemented 2026-08-23; see Phase A status above)*
- Files: `novi/web/server.py`, `novi/brain/chat.py`, `novi/brain/identity.py`
- Change: in the reply path, resolve addressee as `identity.current_speaker() → speech self-introduction ("i am X" → identity.observe(name=X, modality="speech", confidence=0.6)) → regex fallback last`. Persist via existing `save_identity`; surface tier in the chat header payload.
- Tests: "I am Maya" then "what's my name" retains Maya via identity store, not entity regex; regex path covered by fallback tests.
- Acceptance: audit check #2 partially green without vision (speech modality, tier `probable` until cross-modal).

### Phase B — Context awareness: what are we talking about *(~3-5 days)*

**B1. `DiscourseState`** — closes G3 ✅ *(implemented 2026-08-23)*
- New file: `novi/brain/discourse.py`; wired via `MacBrain.discourse` + `ChatMixin.note_user_message()`.
- 20-turn sliding window `{topic, entities, last_intent}`; pronoun/anaphora resolution feeding `compose_reply(topic_hint=...)` grounding (knowledge lookup + explicit "continuing the conversation about" fact); `discourse.updated` event; `/api/context` serves the snapshot.
- Topic selection prefers known world/person/common labels (`privacy.COMMON_ENTITY_LABELS`, deduplicated with chat entity extraction) over the lexical longest-word heuristic.
- Tests: `novi/brain/tests/test_discourse.py` (13).

**B2. Concrete identity providers** — closes G4 ✅ *(implemented 2026-08-23)*
- New files: `novi/brain/speaker_id.py` (`VoiceprintSpeakerID` — deterministic spectral voiceprints from WAV, lazy numpy, cosine matching, enroll/identify), `novi/brain/face_id.py` (`OpenCVFaceID` — gradient-histogram faceprint over the detection crop; `InsightFaceFaceID` import-guarded upgrade path).
- Shared `IdentityMatch` result type in `identity.py`; `_identify_face` now forwards the camera frame payload so providers see pixels.
- Both degrade gracefully (unavailable ⇒ `None` evidence), keeping the loop deterministic and offline-first. Cross-modal promotion to `verified` flows through the existing `PersonIdentity` modality accumulation.
- Tests: `novi/brain/tests/test_identity_providers.py` (9).

**B3. Unify prompt grounding on `ContextPackage`** ✅ *(implemented 2026-08-23)*
- `_compose_reply_impl` assembles the world-context package once per reply and sources knowledge/memory facts from its provenance-tagged layers (legacy queries remain as fallback); the package is reused in the LLM user payload instead of being assembled twice.
- `respond()` no longer drops the grounding record: it surfaces `grounding` with `context_items` / `context_knowledge_items` / `context_memory_items` / `discourse_topic_hint`, making "why did you say that" answerable by inspecting one object.
- Topic selection refined to earliest-mention-wins ("the plant in the kitchen" → plant).
- Tests: `novi/brain/tests/test_reply_grounding.py` (4).

**Phase B complete.**

### Phase C — Memory semantics *(~1 week)*

**C1. Bayesian belief update** — closes G5 ✅ *(implemented 2026-08-23)*
- `cognition.BeliefSystem.observe` fuses evidence with noisy-OR (`1-(1-prior)(1-evidence)`) instead of linear `LEARN_GAIN` accumulation: diminishing returns, asymptotic to 1, never decreasing on confirmation.
- Source-class weighting before fusion: DIRECT_SENSOR .9 / MODEL_INFERENCE .6 / USER_STATEMENT .5 (case-insensitive; unknown → sensor weight).
- Contradictions decay confidence multiplicatively (`×0.7`, proportional doubt) instead of fixed `-0.15`; repeated contradiction still flips with fresh evidence (`CONTRADICTION_FLIP_EVIDENCE=2` unchanged).
- `Belief.last_source` recorded and round-tripped through snapshots (legacy snapshots without it still load).
- Tests: `novi/brain/tests/test_belief_bayes.py` (9).
**C2. Enforce memory classes at admission** — closes G6 ✅ *(implemented 2026-08-23)*
- `memory_classes.classify_memory()` deterministically routes engine `memory_type`s to canonical classes (utterance/audio_event/perception/goal_outcome → EPISODIC; knowledge/fact/summary/triple → SEMANTIC; preference/routine/procedural candidates → their classes; unknown → safe EPISODIC).
- New `MemoryClassDecisionRegistry.gate(memory_type)` returns (allowed, class, state); deferred classes are refused instead of stored flat.
- All four engine admission sites (utterance, audio_event, perception, goal_outcome) route through the gate via `_gate_memory()`: implemented records are stamped with `provenance["memory_class"]` (enabling episodic-only consolidation routing downstream), deferred ones emit `memory.class_deferred` and are not admitted.
- Tests: `novi/brain/tests/test_memory_class_gate.py` (8).
**C3. Fill spatial/temporal context** — closes G7 ✅ *(implemented 2026-08-23)*
- `SpatialMap.region_at(x, y)` resolves the body pose to a semantic region ("kitchen"/"living_room").
- Engine helpers `_spatial_context()` (body x/y/place) and `_temporal_context()`; all four admission sites now carry both.
- Temporal context is **cycle-only by design**: wall-clock would enter the record identity hash and break duplicate-admission idempotency.
- `retrieve(..., place=...)` filter added to all retrieval paths — `b1_memory`, `DurableMemoryStore.retrieve/retrieve_indexed/retrieve_semantic`, `HardenedMemoryManager.retrieve/retrieve_indexed/retrieve_with_states` — so "what did I see in the kitchen" is answerable.
- Tests: `novi/brain/tests/test_admit_context.py` (5, both store backends).
**C4. Learned importance + weighted consolidation** — closes G8 ✅ *(implemented 2026-08-23)*
- New `novi/brain/importance.py`: `ImportanceModel` fuses evidence confidence (0.40), attention salience (0.25) and novelty (0.35), with the Soul's curiosity trait scaling the novelty term; `novelty_for(count)` decays repeats to a floor. Deterministic, bounded [0,1].
- Engine stamps `provenance["importance"]` on perception admissions (`_importance_for` = model score from detection confidence, latest attention ranking, first-sight novelty); `record_importance()` accessor falls back to confidence for unstamped records.
- Recall formula upgraded to the plan's `_memory_score := 0.4·relevance + 0.25·recency + 0.2·importance + 0.15·provenance_trust` (trust = verification status × source class).
- `MemoryConsolidator`: archival candidates are ranked by **importance × recency** (lowest priority archives first) and records at `PROTECTED_IMPORTANCE ≥ 0.8` are exempted from automatic archival — cherished memories decay but survive.
- Tests: `novi/brain/tests/test_importance.py` (9).

**Phase C complete.**

Acceptance: audit check #1 (paraphrased recall via MiniLM cosine >0.7) plus retrieval finds place-scoped memories.

### Phase D — Knowledge reasoning & prediction loop *(~1-2 weeks)*

**D1. kgraph graph overlay** — closes G9 part 1 ✅ *(implemented 2026-08-23)*
- `graph = ["networkx>=3.0"]` declared in pyproject extras; kgraph degrades to a pure-python path when absent.
- `EntityKnowledgeGraph.query(entity, predicate=None, hops=N)`: BFS multi-hop traversal over outward *and* inward edges, deterministic ordering, hop distances included.
- `EntityKnowledgeGraph.pagerank()`: confidence-weighted PageRank via networkx on the undirected entity view (importance = strength of participation regardless of argument order); offline fallback is normalized weighted degree. `top_entities(limit)` for ranked importance.
- Tests: `novi/brain/tests/test_kgraph_analytics.py` (9).

**D2. Triple embeddings** — closes G9 part 2 ✅ *(implemented 2026-08-23)*
- New `novi/brain/triple_index.py`: each triple embeds as `"subject predicate object"` through the brain's standard embedder (MiniLM/MPS, hashing fallback offline).
- `semantic_search(text, limit)` ranks triples by cosine with deterministic tie-breaking; incremental sync hooks into the graph's `on_change` chain **preserving** the existing persistence callback.
- Wired into `MacBrain` as `self.triple_index` at init (pre-populated from any persisted graph). Vectors are computed lazily on first search and the embedder is a per-process singleton — brain construction stays ~0.2s and offline-safe (an eager first cut doubled suite time to 200s; fixed).
- Tests: `novi/brain/tests/test_triple_index.py` (6).
**D3. LLM triple extraction** — closes G9 part 3: Ollama path emitting constrained JSON triples behind the FORBIDDEN guard; deterministic regex stays as fallback.
**D4. PredictionEngine** — closes G10: deterministic spatial predictor first (emits `PREDICTED` entities, never overwriting OBSERVED); compare vs next-cycle observations → drive `ExpectationSystem` by prediction error; exercise the CosmosReason2 adapter behind `ModelRuntime` (`prediction.requested` trigger).
Acceptance: audit lever 4 measurable — `prediction_accuracy` logged to MetricRegistry.

### Phase E — Soul learning, benchmarks, docs closure *(~1 week)*

**E1. `Soul.learn_from_interaction(person, interaction_type, delta≤0.01)`** with decay-to-baseline over ~100 cycles; `motivation_priority()` weights `AttentionRanker` relevance and goal priority. Closes G11. Acceptance: audit check #5 (playfulness 0.60→0.64 over 5 play interactions, then decay).
**E2. Benchmarks** — closes G12: `benchmarks/vector_bench.py` (p99 retrieve <50ms @5k records), reasoning-calibration harness, prediction-accuracy counter; persist results under `mac_test_results/`.
**E3. `docs/ARCHITECTURE_CLARITY.md`** — closes G13 and turns the failing architecture-integrity gate green; also fix the stale `contracts/tests/...` links in the traceability matrix (same gate).

### Explicitly out of scope / already satisfied

- SSE streaming, live widgets, router default, planner wiring, p0-gate button — done (§1).
- No new web framework; no cloud LLM deps (audit §6 constraint upheld).
- Resource-aware model selection (nemotron/qwen/deterministic by `ResourceMode`): `ResourceMode` exists and gates failure modes (`engine.py:1109-1114`); extend health-driven model pick as a small D-phase follow-up once D4 lands.

### Definition of done (per phase)

1. New/updated unit tests added; full suite green (`pytest`, currently 1,285 passing).
2. `ruff check` clean on touched files; smoke test `python -m novi.brain.cli --cycles 1` exit 0.
3. Corresponding acceptance check from audit §7 demonstrated and evidence JSON persisted under `mac_test_results/`.
