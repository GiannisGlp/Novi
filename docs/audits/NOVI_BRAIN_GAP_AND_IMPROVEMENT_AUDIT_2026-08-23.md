# Novi Brain — Gap Audit & Improvement Blueprint
**Date:** 2026-08-23
**Scope:** `brain/` (portable core) + `MAC_BRAIN/` (canonical Mac runtime) + `web/server.py` + `docs/02-novi-brain` + `docs/06-soul` + `IMPLEMENTATION_PLAN/01_BRAIN`
**Goal:** Identify every gap between what Novi promises (North Star, Soul Constitution, Cognitive Loop) and what currently runs on the Mac, and map a concrete path to a fully autonomous brain with reasoning, soul, cognition, memory, knowledge, NN, and context awareness.

---

## 0. The one thing to fix first: you have two brains

This is the root confusion in the repo.

```
brain/           → portable, deterministic stage-0 scaffolding (95% mock)
  • DeterministicCognition (alice/speech detector)
  • DeterministicMemoryManager (hash-map, keyword search)
  • DeterministicAutonomy (observe only)
  • DeterministicModelBackend / NemotronBackend / CosmosBackend (echo)

MAC_BRAIN/       → canonical executable brain (this is what web/server.py actually runs)
  • MacBrain (99k lines) composing BrainSupervisor + perception + world + cognition2 + identity + kgraph + memory_hardening + dialogue + attention + consolidation + ...
```

`web/server.py` imports `from MAC_BRAIN.runtime import MacBrain`. The `brain/` package is **not** the web brain. It is the contract/types layer that MAC_BRAIN depends on. `MAC_BRAIN → brain` (one way). The docs saying `MAC_BRAIN` is canonical are correct, but the top-level README and `brain/runtime.py` still read as if `brain/` is the brain. That split explains why your `web/server.py` feels thin — the real logic lives in `MAC_BRAIN/runtime.py` + `chat.py` + `dialogue.py`, not in `brain/`.

**Fix:** Stop extending `brain/` directly. All new work goes to `MAC_BRAIN/`. Keep `brain/` as frozen contracts + deterministic test doubles. Add a `docs/ARCHITECTURE_CLARITY.md` that states this in one paragraph and rename `brain/` header to `brain — contracts & test doubles (not the runtime)`.

---

## 1. Current truth vs. North Star

| North Star property | What docs promise | What runs today | Verdict |
|---|---|---|---|
| **Continuity** | Persistent identity, history, goals survive restart | `DurableMemoryStore` (SQLite WAL) does persist memories, goals, soul, lexicon, identity, knowledge — good. But `BrainSupervisor` lifecycle is still stage-0 synthetic; no real recovery from `FAILED` beyond `shutdown()`. | 65% — persistence exists, resilience does not |
| **Situated understanding** | World model of people/objects/rooms/relations with uncertainty | `UnifiedWorldModel` with epistemic status is solid. But `TemporalWorldModel` in `brain/` is still toy; spatial map is a single `default_home_map()` with no SLAM, no occupancy, no frame tree. | 55% |
| **Agency** | Goals, priorities, initiative, investigation | `BoundedGoalController` + `AutonomyStateMachine` + curiosity triggers exist but goals are synthetic `reach/investigate` with fixed step budgets, never derived from reasoning. Planner exists but `MacBrain.step()` never calls it. | 45% |
| **Memory & learning** | Episodic/semantic/spatial/procedural, provenance, consolidation | `HardenedMemoryManager`/`DurableMemoryStore` + `WriteGate` + retrieval states is the best part of the codebase. Gap: vector search is `HashingEmbedding` (feature hash, 256d), not semantic; no episodic→semantic promotion validated; no temporal/spatial indexing. | 60% |
| **Reasoning & planning** | Grounded reasoning, hypotheses, plans | `DeterministicCognition` → `MacCognition` adds hypotheses/inferences but they are template strings, not model outputs. `DeliberativeReasoningProvider` via Ollama exists but is optional and not on by default. No planning in the loop. | 35% |
| **Embodied action** | Governed skill execution → body | `GovernanceGuard` + `SkillExecutor` + `VirtualBody` allowlist is correct architecture. Closed-loop `OBSERVE→ORIENT→DECIDE→ACT→VERIFY` exists in `closed_loop.py` but `MacBrain.step()` uses a shortcut path that skips it for most actions. | 50% |
| **Social continuity** | Stable personality + relationships + communication style | `Soul` (traits/values/affect), `PersonIdentity` (detected/probable/verified), `Relationships`, `Lexicon`, `SocialIntelligence` all exist — but affect is a decay-toward-baseline vector with hardcoded bump deltas, not grounded in social outcomes. Dialogue `FORBIDDEN` list is excellent, but the system prompt builder lives in `chat.py` and is not tested against soul specs. | 50% |

**Bottom line:** You are past stage-0, but the brain is still **deterministic-first with LLM grafted on**. The next step is to flip it: **LLM/NM-first with deterministic guardrails**, keeping the same safety boundaries.

---

## 2. Domain-by-domain gaps

### 2.1 Cognition — the most critical gap

**Current:**
- `brain/b1_cognition.py`: `salient = {alice, open, moved, speech}`. That's a demo detector, not cognition.
- `MAC_BRAIN/cognition2.py:MacCognition`: adds `relations/goal/recalled` but `reason()` still calls `super().reason()` and appends templated hypotheses/inferences (`_CAUSAL_PREDICATES` set, distance checks).
- `MAC_BRAIN/cognition.py:BeliefSystem`: `LEARN_GAIN=0.25`, `CONTRADICTION_FLIP_EVIDENCE=2` — linear confidence, threshold flip. No Bayes, no source weighting.
- `MAC_BRAIN/cognition.py:ExpectationSystem`: `consistency=2` consecutive frames → violation. No temporal decay, no spatial expectation.
- `cognition_typed.py:emit_cognitive_typed` exists and is clean, but `MacBrain.cognition_typed()` is a separate debug entry point — the main `step()` never emits typed contracts.

**Gap:**
- No grounded inference. Hypotheses are strings, not probabilistic alternatives.
- No uncertainty propagation (entity confidence 0.95 does not flow into reasoning confidence).
- No prediction: `CosmosReason2` adapter exists in `brain/b2_cosmos_reason.py` / `MAC_BRAIN/models/` but `step()` never calls it.
- No theory of mind: `identity_for("person")` is vision-only label, not a person model with intent/attention.

**Make it smarter — concrete upgrades:**

1. **Promote `cognition_typed` into the main loop.** Every `step()` should emit `cognition.typed` and store `SituationState + PersonContext + IntentHypothesis + Prediction` as the canonical situation, not the legacy `Situation` dataclass. Legacy `Situation` becomes a projection for backward compat.

2. **Replace templated `MacCognition.reason()` with a two-engine design:**
   ```
   MacCognition (orchestrator)
     ├─ Fast path: DeterministicCognition ( <5ms, never blocks safety )
     └─ Deliberative path: LLM reasoning via ReasoningRouter (Ollama nemotron/qwen)
         • Input: ContextPackage (bounded, 2000 tokens) from ContextAssembler
         • Output: { hypotheses: [ {text, confidence, basis[]} ], inferences: [], rationale }
         • Guard: LLM output is hypothesis only — never writes world state directly
   ```
   The fast path runs every cycle; the deliberative path runs when `active_goal` exists or `attention_ranker` reports `uncertainty>0.4`.

3. **Upgrade `BeliefSystem` to Bayesian belief:** replace `LEARN_GAIN` with `confidence = 1 - (1-prior)*(1-evidence)` weighted by source class (`DIRECT_SENSOR` 0.9, `MODEL_INFERENCE` 0.6, `USER_STATEMENT` 0.5). Contradictions should decay confidence multiplicatively, not subtract 0.15.

4. **Wire `CosmosReason2` for prediction:** Add a `PredictionEngine` that takes `WorldModel.snapshot() + SituationModel.current_situations + known dynamics` and returns `PREDICTED` entities/relations (marked `PREDICTED`, never overwriting `OBSERVED`). `expectationViolation` should compare `PREDICTED` vs next-cycle `OBSERVED` — that closes the learning loop.

5. **Metric:** Log `reasoning_latency_ms`, `hypothesis_count`, `prediction_accuracy` (predicted vs observed entity still present next cycle) to `MetricRegistry` — you cannot improve what you do not measure.

### 2.2 Memory — strong foundation, weak recall

**Current:** The hardened layer is genuinely well designed — `WriteGate` (identity→integrity→privacy→poisoning→retention), `retrieve_with_states` (NO_RESULT/AMBIGUOUS/CONFLICTED/STALE), `DurableMemoryStore` with WAL, FTS via `retrieve()`, and `MemoryConsolidator + SummaryConsolidator` (including `LLMSummarizer` for gist). This is the most complete domain.

**Gap:**
- `vector.py:HashingEmbedding` is a signed feature hash — keywords, not semantics. `"cat" near "sofa"` and `"feline on couch"` have 0 overlap. You advertise semantic recall but deliver keyword recall.
- No memory classes enforced at admission: `memory_classes.py:MemoryClassDecisionRegistry` exists but `MacBrain.admit()` does not route through it for `utterance/perception/goal_outcome` — everything is flat.
- Consolidation is time-based (`default_ttl_seconds`), not importance/relevance/recency weighted. No importance score from soul/autonomy.
- Retrieval falls back to FTS rank + recency weighting (`_memory_score: 0.5*relevance + 0.3*recency + 0.2*importance`) — importance is just `record.confidence`, not learned importance.
- Spatial/temporal context fields exist on `MemoryRecord` but are `None` in every `admit()` call today.

**Upgrades:**

1. **Real embeddings, local, offline, MPS-native.** Replace `HashingEmbedding` provider with `sentence-transformers/all-MiniLM-L6-v2` (80 MB, runs on MPS via `torch` + `transformers` already in `pyproject.toml:neural`). Keep hashing as fallback when `torch` absent. Implementation is already stubbed in `storage.py:_vector_insert` — just swap provider:
   ```python
   # MAC_BRAIN/vector.py — new provider
   class MiniLMEmbedding:
       def __init__(self, model_id="sentence-transformers/all-MiniLM-L6-v2"):
           from sentence_transformers import SentenceTransformer
           self.model = SentenceTransformer(model_id, device="mps" if torch.backends.mps.is_available() else "cpu")
       def embed(self, text): return normalize(self.model.encode(text, normalize_embeddings=True).tolist())
   ```
   Benchmark on `test-image.png` perceptions already — add `MAC_BRAIN/benchmarks/vector_bench.py` that proves p99 retrieve < 50ms at 5k records.

2. **Enforce memory classes.** In `MacBrain._admit_detections` and `ingest_transcript`, call `MemoryClassDecisionRegistry.decide(memory_type, content, provenance)` and store the `memory_class` (episodic/semantic/spatial/etc.) + `mind_type`. Route episodic consolidation only on episodic.

3. **Importance from cognition.** Score importance as `soul.traits["curiosity"] * cognition.reasoning.confidence + attention_candidate.overall` and store it. Then `_memory_score` becomes `0.4*semantic_cosine + 0.25*recency + 0.2*importance + 0.15*provenance_trust`.

4. **Spatial/temporal indexing.** Fill `temporal_context={"cycle":, "wall_time":}` and `spatial_context={"x_m": body.x_m, "y_m": body.y_m, "place": spatial.current_place}` on every admit. Then `retrieve("kitchen")` actually finds things seen in the kitchen.

5. **Make summaries retrievable by entity.** `SummaryConsolidator` already emits `summary` memories — but `knowledge.extract_from_text` is regex-based. Add an `LLM gist` path that you already have (`LLMSummarizer`) and ensure summaries carry `entity_refs` for the grouped entity.

### 2.3 Knowledge — triple store without reasoning

**Current:** `kgraph.py:EntityKnowledgeGraph` is a dict of triples with `evidence_count` and `confidence = 1-(1-a)(1-b)`, conflict = highest confidence wins / others `contradicted`. Extraction via `extract_from_text` is regex over known labels.

**Gap:** No ontology, no transitive reasoning (`alice likes jazz → alice is person → person can like music` does not exist), no embedding search over triples, no temporal validity.

**Upgrades:**

1. **Add `networkx` graph over triples.** Use `networkx.DiGraph` (already a permissible dep) to run PageRank for entity importance and `shortest_path` for query expansion (`"who likes jazz?"` → find `likes` edge). Add `kgraph.query(entity, predicate=None, hops=1)`.

2. **Embed triples.** When `MiniLMEmbedding` exists, embed `f"{subject} {predicate} {object}"` and support `knowledge.semantic_search("jazz preferences", limit=5)` via cosine over triple embeddings — separate from memory vector search.

3. **Ground extraction in LLM.** `DialogueEngine` already calls Ollama. Add a `knowledge.extract_via_llm(text, allowed_predicates)` path that prompts the local LLM to emit `subject/predicate/object` JSON (with your `FORBIDDEN` guard). Deterministic regex stays as fallback, LLM wins when available.

### 2.4 Soul — implemented but not felt

**Current:** `soul.py: Soul` is a clean deterministic personality model: `TRAITS` (7), `VALUES` (8), `MOTIVATIONS` (8), each with `DEFAULT_*` weights, plus `AffectState` with `AffectState.bump/delta` and `decay(0.9)`. `PersonIdentity` tiers and `Lexicon` per-person scoping are thoughtful. `dialogue.py` strips assistant mode.

**Gap:**
- Affect is affect-on-a-schedule: `goal_completed → satisfaction+0.25`, `novel_detected → curiosity+0.2` — but no mapping from real social signal (`praise`, `reassurance_request`, `embodiment_question`). Affect never reaches `compose_reply`'s tone decision except via `soul.tone()` which is a static map.
- Personality is static: `DEFAULT_TRAITS` never learn. `LearnedPreferences` learns likes, but not that Novi becomes more playful with a specific person.
- No soul audit: the `P0GateRunner` exists but `web/server.py` never surfaces it.

**Upgrades:**

1. **Close affect → dialogue.** Pass `soul.affect.snapshot()` + `personIdentity.tier` into `DialogueEngine._build_system_prompt`. Map `frustration > 0.6 → tone patience -0.2`, `curiosity > 0.7 → ask a follow-up question` (you already have `followup_question` helper but never gate it on affect).

2. **Let soul learn slowly.** Add `Soul.learn_from_interaction(person, interaction_type, delta=0.01)` that nudges `traits["playfulness"]` when a person consistently triggers joke requests and Novi succeeds. Cap delta at `0.01` per interaction, decay back to baseline over 100 cycles — personality drifts, but cannot jump.

3. **Wire soul to autonomy weighting.** `Motivations` already define `understand/help/learn/...`. Use `soul.motivation_priority("explore")` to weight `AttentionRanker.weights[RELEVANCE]` and `BoundedGoalController` priority — the curious Novi literally investigates more.

4. **Expose soul in the web UI.** Add a `/api/soul` endpoint and a small affect bar (7 traits sparklines + current affect dims) so you see who Novi is becoming. This makes the "soul" testable.

### 2.5 Context awareness — "who / what are we talking about"

This is the user's explicit ask. Two subproblems.

**Who am I talking to:**
- `identity.py: PersonIdentity` tiers are correct (cross-modal `CROSS_MODAL_COUNT=2`, `VERIFIED 0.8`/`PROBABLE 0.55`), but `MacBrain._identify_face` is a stub, `speaker_id`/`face_id` providers are `None` by default, and `chat_send` infers the person from `brain._entities_in_text(text)` regex (capitalized words not in stopwords). That regex invents people.
- No voice fingerprint, no face embedding. A user saying "I am Georg" is learned as `likes` preference, not as identity.

**Fix:**
- Add `MAC_BRAIN/face_id.py` (InsightFace or `face_recognition` on CPU, behind `vision` optional dep) and `MAC_BRAIN/speaker_id.py` (ECAPA-TDNN via `speechbrain` or simple `webrtcvad` + energy fingerprint — start simple). Both implement a common `IdentityProvider: observe(embedding, cycle) -> IdentityBelief`.
- In `web/server.py:chat_send`, stop inferring `addressee` from regex. Instead: `person = body.identity_for_current_speaker() or regex_fallback`. When the user says `"I am X"`, call `identity.observe(person="person", name=X, modality="speech", confidence=0.6)` and wait for cross-modal verification before treating it as `verified`.
- Persist `PersonIdentity` via `DurableMemoryStore.save_identity` (already incremental) and surface the current tier in the web chat header: `● Georg · verified 0.92` vs `○ unknown · detected`.

**What are we talking about:**
- `dialogue.py:_extract_topic` is keyword matching. `ContextAssembler` is built for this (`ContextRequest(speaker_label, utterance, token_budget, situations)`) and is used in `_assemble_world_context`, but the resulting `ContextPackage` is never passed to `compose_reply`'s history — `compose_reply` builds its own prompt from `knowledge + history + world_context` ad hoc.
- No discourse memory: after 3 turns about "the kitchen", the 4th "is it still open?" has no anaphora resolution.

**Fix:**
- Unify: `MacBrain.compose_reply` should take a `ContextPackage` (already produced by `ContextAssembler`) as its single grounding object. The package should contain: `immediate` (speaker, utterance), `situational` (visible entities, relations, situations, attention_top), `memory` (recalled summaries), `knowledge` (kgraph hits), `relationship` (tier + lexicon scope), `long-horizon` (active goal + temporal). This makes "what we're talking about" auditable.
- Add `MAC_BRAIN/discourse.py: DiscourseState` — a 20-turn sliding window with `{topic, entities, last_intent}` updated by the LLM (or `_extract_topic` fallback). When `is_continuation` or pronoun `it/that`, resolve to `discourse.topic`. Emit `discourse.updated` events.
- In the web UI, render the `ContextPackage` item count and topic badge so you can see why Novi said what it said.

### 2.6 Reasoning, NN, and autonomy — where the "intelligence" should live

**Current:** `b2_model_runtime.py:ModelRuntime` is a clean boundary (register/load/health/invoke with `validate_contract`). But all backends are deterministic. `brain/b2_nemotron.py:DeterministicNemotronBackend` just counts `images/audio/video`. `b2_cosmos_reason.py` is similar. `ReasoningRouter` exists but `web/server.py` defaults to `reasoning="deterministic"` — most users never enable `ollama`/`router`.

**Upgrades:**

1. **Default to `router` on the web, not `deterministic`.** Change `NoviWebServer(reasoning="router")`. When Ollama is down, `ReasoningRouter` already falls back to deterministic — but the user should not need to pass `--reasoning router` to get intelligence. Probe once at startup and stay router.

2. **Bind Nemotron and Cosmos as real providers:**
   - `NemotronAdapter` via Ollama `nemotron-3.5-lightning` (you list it in `available_models` but `NoviWebServer._build_reasoning` creates `DeliberativeLLMReasoningProvider` for both qwen and nemotron — add a `NemotronAdapter` branch that sets `think:false` and a different system prompt).
   - `CosmosReason2` via a local placeholder until NVIDIA hardware is selected — but wire the adapter so that when `world_model.entities` include a spatial situation (`door: open → close` prediction), `_emit("prediction.requested")` triggers `CosmosReasonBackend.invoke()` behind the same `ModelRuntime` boundary. Even before hardware exists, the path is exercised with a deterministic spatial predictor.

3. **Planner in the loop.** `planner.py:Planner` already plans `Goal → [Steps]`. `MacBrain.goals` enqueues `Goal` but `step()` executes one `move_forward/turn` directly without a `Plan`. Change: when `goals.active` exists and `planner` can produce a `Plan`, `MacBrain.step()` should `plan = planner.plan(goal, world.snapshot())` and then execute `plan.next_step()`. Emit `plan.created` / `plan.step`. This turns "autonomy" from single-action into multi-step agency.

4. **Resource-aware model routing.** `ResourceTelemetry` already samples host CPU/memory; `MultiSpeedRuntime(SYSTEM_0/SYSTEM_1/SYSTEM_2)` already gates cognition tiers. Extend `ModelRuntime` health to `ResourceMode {FULL_COGNITION, DEGRADED_COGNITION, REACTIVE_ONLY, SAFE_MINIMUM}` and pick `nemotron-3.5-lightning` in `FULL`, `qwen3.8` in `DEGRADED`, deterministic in `REACTIVE_ONLY`. Emit `resource.mode_changed`.

### 2.7 Web / server.py — the lived experience

**What works:** Pure stdlib server (no pip install to see Novi), bounded event log (500), bounded chat (200 with summarization), `chat-busy` lock to prevent LLM / auto-step races, dedup window, Ollama re-probe TTL, model switching, `DemoCamera` so it runs without permissions, theme toggle. The `index.html` polling guards (`chatRefreshing/eventRefreshing`, `chatEpoch`) and `renderedChatSeq` dedup are well thought out.

**Gaps and fixes (prioritized):**

**P0 — streaming + true context display:**

- **Stream LLM tokens.** `_llm_chat` currently `num_predict:512` and `timeout:120`, blocking the `chat_send` lock for seconds. Switch to Ollama `stream:true` with `urllib` chunked read and yield `text_delta` over Server-Sent Events (`GET /api/chat/stream?after=`). Frontend appends tokens progressively — Novi feels alive instead of frozen. Fallback to single-shot `stream:false` when the model is deterministic.

- **Stop polling, use SSE for events.** `fetch /api/events?after=` every 1.2s is wasteful and adds 0.6s average latency to initiative messages. Add `GET /api/events/stream` (SSE, `text/event-stream`) that holds the connection and pushes `event_bus` entries as they arrive. Keep `/api/events?after=` as history fallback. The `event_bus` already has `correlation_id/causation_id` — SSE is the natural transport.

- **World + attention + soul panels.** The `widgets` grid currently shows narrow cards. Replace placeholder state with four live cards backed by new endpoints:
  ```
  GET /api/state          → current unifiedWorld.entities + lifecycle
  GET /api/attention      → AttentionCandidate[0..4] (scores + suggested_action)
  GET /api/context        → ContextPackage.to_dict() (visible_entities/relations/situations)
  GET /api/soul           → Soul.snapshot() + affect + PersonIdentity snapshot
  ```
  Render entity chips with `epistemic_status` color (OBSERVED=green, PREDICTED=dashed, CONTRADICTED=amber). Click an entity → `GET /api/knowledge?entity=door`.

**P0 — input handling:**

- Add `POST /api/chat` validation: max 2000 chars, empty → no-op, `Content-Type` check, `429` when `chat_busy` instead of silently queuing. Log `web.error` when Ollama returns non-200.

**P1 — UI improvements:**

- **Camera preview.** When `camera_mode=="real"`, `GET /api/camera/frame` (base64 JPEG of the last `CameraFrame`) and render it in a `Camera` card. You already have `CameraFrame.payload` — expose it.
- **Face/speaker identity badge.** Next to the chat input, show `identity.tier` for the current speaker (reuse `GET /api/identity`).
- **Memory explorer.** `GET /api/memory?query=alice&limit=10` already possible via `retrieve()` — add a search box in a `Memory` card that renders `memory_type`, `confidence`, `privacy_class`, and `entity_refs` chips.
- **P0 gate button.** `POST /api/p0_gate` → `brain.p0_gate()` → render `violation_count` in a banner. Makes constitutional compliance visible.

**P1 — server architecture:**

- Extract `NoviWebServer` into `web/server.py` + `web/handlers.py` — `server.py` is 828 lines, mixing HTTP parsing with brain orchestration. Handlers for `/api/chat`, `/api/state`, `/api/events/stream` should not live in one class.
- Add `RequestHandler.log_message` override that writes to `audit_trail` (privacy-safe) instead of stdout.
- Add `?store=` validation: `Path(store_path).parent.mkdir(parents=True, exist_ok=True)` already exists but `store_path` is not sanitized — guard against `..` traversal.

---

## 3. How to make Novi smarter — the 8 levers

These are not feature requests. Each lever has a measurable effect on the North Star properties.

1. **Bounded semantic recall (lever = relevance).** Hashed → MiniLM embeddings. Expected lift: recall precision +25–35% on paraphrased queries (`"feline on couch"` → cat memories). Measure with `vector_bench` at 5k rows.
2. **Typed cognition in the loop (lever = coherence).** One canonical `SituationState` per cycle, not two competing `Situation` types. Expected lift: cognition becomes replayable/diffable — you can unit-test that the same world + same memory → same situation id.
3. **Deliberative reasoning as a tier (lever = reasoning).** Fast deterministic + router fallback. Expected lift: reasoning that references actual memories/knowledge instead of "a person spoke". Measure `reasoning.confidence` calibration (reasoning that says 0.9 should be right 90% of the time — add `evaluation.py` harness).
4. **Prediction → expectation violation → learning (lever = learning).** Cosmos/spatial predictor that emits `PREDICTED` entities, then compares to next `OBSERVED`. Expected lift: Novi notices when something moved when it shouldn't have, and learns the expectation (the `ExpectationSystem` becomes data-driven, not hardcoded `consistency=2`).
5. **Planner + closed loop (lever = agency).** Single action → plan → verify. Expected lift: `reach (8,0)` becomes a visible 4-step plan instead of opaque `move_forward` spam — autonomy becomes legible and testable.
6. **Affect grounded in outcome (lever = soul).** Satisfaction/frustration from `goal_outcome` memories, not just event names. Expected lift: a Novi that fails repeatedly becomes more cautious, not just annoyed by a string match — personality emerges from experience.
7. **Discourse state + anaphora (lever = context awareness).** "What are we talking about" becomes a first-class `DiscourseState` instead of last-utterance keyword scan. Expected lift: multi-turn conversations stop resetting topic on every message — `Natural fallbacks` drop by half.
8. **SSE streaming (lever = liveness).** Polling → event-driven. Expected lift: initiative messages (the neglected → greeting path in `SocialInitiative`) appear in <200ms instead of 1.2s poll jitter — Novi feels present.

---

## 4. Prioritized roadmap

### P0 — before the next demo (1–2 weeks)

- [ ] Flip `web/server.py` default to `reasoning="router"` and verify Ollama fallback still passes `brain/tests`.
- [ ] Wire `cognition_typed` into `MacBrain.step()` as the canonical situation.
- [ ] Replace `HashingEmbedding` with `MiniLMEmbedding` behind the same provider boundary; keep hash fallback.
- [ ] Add `GET /api/state`, `/api/attention`, `/api/context`, `/api/soul`, `/api/identity` and render them in `index.html` widgets (entity chips + attention list + affect bars).
- [ ] Add SSE `GET /api/events/stream` and `GET /api/chat/stream` (stream tokens); keep polling as fallback.
- [ ] Wire `Planner.plan(goal)` into `MacBrain.step()` when a goal is active; emit `plan.*` events.
- [ ] Fix `web/server.py:chat_send` to use `PersonIdentity` + `DiscourseState` instead of `_entities_in_text` regex for addressee resolution; add `POST /api/p0_gate` button.

**Gate:** Demo script `python -m web.server --store novi_web.db` shows streaming replies, world chips, attention candidates, soul bars, and a 3-step plan for `--goal-target 8,0` — all without passing extra flags.

### P1 — makes Novi feel continuous (2–4 weeks)

- [ ] `face_id.py` + `speaker_id.py` behind `vision`/`audio` optionals; cross-modal verification to `verified`.
- [ ] `discourse.py:DiscourseState` with anaphora resolution; wire into `ContextAssembler`.
- [ ] `kgraph` embedding search (`semantic_search`) + LLM triple extraction (when Ollama available).
- [ ] `Soul.learn_from_interaction` (0.01 cap, decay) + motivation-weighted `AttentionRanker`/`BoundedGoalController`.
- [ ] `PredictionEngine` (deterministic spatial predictor first, Cosmos adapter behind the same boundary) + `ExpectationSystem` driven by prediction errors.
- [ ] `networkx` graph over `kgraph` for `shortest_path`/`pagerank`; `knowledge.context(entity, hops=2)`.
- [ ] Web: camera preview card, memory explorer search, P0 gate banner, SSE reconnection with `Last-Event-ID`.

### P2 — embodied + measurable (1–2 months)

- [ ] Fill `MemoryRecord.spatial_context`/`temporal_context` on every admit; add spatial query `retrieve(place="kitchen")`.
- [ ] Enforce `MemoryClassDecisionRegistry` at admission; episodic→semantic promotion benchmark.
- [ ] `ResourceTelemetry → ModelRuntime health → ResourceMode` routing (`nemotron`/`qwen`/`deterministic`).
- [ ] Replace `b1_world.py:TemporalWorldModel` usage in MAC_BRAIN with `UnifiedWorldModel` exclusively; deprecate `b1_world` imports from new code (it stays for `brain/tests`).
- [ ] Benchmarks: `vector_bench`, `reasoning calibration`, `prediction accuracy`, `plan success rate`, `discourse topic retention`. Persist to `IMPLEMENTATION_PLAN/EVIDENCE/mac/`.
- [ ] `ARCHITECTURE_CLARITY.md` + deprecation notices on `brain/` modules that are scaffolding.

---

## 5. Concrete patch proposals — where to cut

| File | Change | Size |
|---|---|---|
| `web/server.py` | `reasoning="router"` default; add `GET /api/state|attention|context|soul|identity|p0_gate`, `GET /api/events/stream` (SSE), `GET /api/chat/stream` (token SSE), `GET /api/camera/frame`, `GET /api/memory?query=`; validate input; sanitize `store_path` | ~250 lines |
| `web/static/index.html` | Replace `fetch` polls with `EventSource`; render 4 new widget cards (Entities, Attention, Context, Soul); camera `<img>`; identity badge; memory search; P0 gate button; streaming bubble | ~300 lines |
| `MAC_BRAIN/runtime.py` | Call `cognition_typed()` inside `step()` and store `TypedCognitionOutput`; call `planner.plan(goals.active)` when active; fill `spatial/temporal_context` on admits; route through `MemoryClassDecisionRegistry` | ~120 lines |
| `MAC_BRAIN/cognition2.py` | Add `Deliberative path` branch that builds a `ContextPackage` and calls `ReasoningRouter` for hypotheses; fast path remains deterministic | ~180 lines |
| `MAC_BRAIN/cognition.py` | Replace `LEARN_GAIN` linear with Bayesian update keyed by `source_class`; decay contradictions multiplicatively | ~40 lines |
| `MAC_BRAIN/vector.py` | Add `MiniLMEmbedding(SentenceTransformer)` provider; `EmbeddingIndex` auto-selects `MiniLM` when `sentence_transformers` importable, else `HashingEmbedding` | ~90 lines |
| `MAC_BRAIN/face_id.py` *(new)* | `InsightFaceEmbedding` behind `vision` optional; `SpeakerEmbedding` behind `audio` optional; both implement `IdentityProvider` | ~200 lines |
| `MAC_BRAIN/discourse.py` *(new)* | `DiscourseState(topic, entities, last_intent, history[20])` + pronoun resolution | ~120 lines |
| `MAC_BRAIN/kgraph.py` | Add `networkx.DiGraph` overlay + `semantic_search()` via `vector.py` | ~100 lines |
| `MAC_BRAIN/soul.py` | Add `Soul.learn_from_interaction(delta<0.01)` + `motivation_priority()` consumed by `attention.py`/`autonomy.py` | ~60 lines |

---

## 6. Tech & dependency hygiene

The project already made the right call to keep `core` stdlib-only. Keep that:

```
core (stdlib)        ← brain contracts, runtime, web server — always works
neural (torch)       ← SSDLite + MiniLM — MPS on Mac, no cloud
audio (sounddevice)  ← microphone/speaker — real sensing when available
vision (opencv)      ← camera + face — real perception when available
llm (Ollama)         ← qwen/nemotron — local reasoning, never required
typed (pydantic)     ← typed cognition contracts — optional hardening
metrology (pint)     ← units/uncertainty — optional, never blocks loop
simulation (simpy)   ← closed-loop sim — deterministic replay
```

Do not add a web framework (`fastapi`, `flask`) — the stdlib server is a deliberate constraint that forces the brain to own its contracts. SSE is stdlib-compatible (`wfile.write(b"data: ...\n\n")`).

Do not add `openai`, `anthropic`, or any cloud LLM as a dependency — the `Ollama` path is correct for offline-first. Cloud can be a `RemoteModelBackend` behind `ModelRuntime`, never a direct import.

---

## 7. How to tell it's getting smarter — 5 acceptance checks

1. **Memory:** Say `"My dog Bixie loves swimming"` → later say `"what does my dog like?"` → retrieved memory contains `Bixie likes swimming` via semantic cosine > 0.7, not just keyword `"dog"`. (`MiniLMEmbedding` + `semantic_search`.)
2. **Who:** Say `"I am Maya"` in chat, then show your face to the camera (when `face_id` enabled) → `PersonIdentity.tier("person") == "verified"` with `modalities=["speech","vision"]` and `confidence >= 0.8`. The header badge reads `● Maya · verified 0.84`.
3. **What:** After 3 turns about `"the plant on the shelf"`, say `"is it still there?"` → `DiscourseState.topic == "plant"` → `ContextAssembler` resolves `it → plant` → `knowledge.context("plant")` hits → reasoning hypothesis references `plant`. No fallback to generic memory dump.
4. **Agency:** `POST /api/goals {"kind":"reach","target":[8,0],"priority":1}` → `GET /api/attention` shows a 4-step plan `["orient","move_forward","move_forward","verify"]` → world shows `VirtualBody` moved and `goal.status == "completed"` within `max_steps`. The plan is visible, not just interpolated moves.
5. **Soul:** After 5 successful play interactions (`joke_request` → Novi tells a joke → user says `"haha great"`), `GET /api/soul` shows `traits.playfulness` nudged from `0.60 → 0.64` and `affect.satisfaction` briefly elevated, then decayed — personality learned, not hardcoded.

---

## 8. What I built for you in this audit

- This file: `NOVI_BRAIN_GAP_AND_IMPROVEMENT_AUDIT_2026-08-23.md` (the full audit).
- Next steps are offered, not auto-applied: P0 patches are scoped and ready to cut. Say which P0 slice you want first (streaming, attention/soul widgets, MiniLM recall, or planner wiring) and it lands as a verified, tested diff — or say "do all P0" and it ships as a bounded branch.

---

*Style note:* This audit was written against the project's own docs as truth (North Star, Soul Constitution, Cognitive Architecture). The brain is not the LLM — the brain is the system that decides when an LLM may speak, what it may ground its reply in, and whether acting on what it said is allowed. The gaps above are where that decision is still made by templates, hashes, and regex instead of by bounded, inspectable learned context.
