# Mac Brain Implementation Status

## First executable slice

**Status: IMPLEMENTED — pending Mac execution.**

### Implemented

- `MAC_BRAIN` Python package;
- Mac camera adapter with optional OpenCV dependency;
- Mac microphone recorder with optional sounddevice dependency;
- Mac speaker adapter using native macOS `say`;
- virtual body with an explicit action allowlist;
- Mac Brain orchestrator composing the existing Novi B1/B2 runtime;
- existing perception/world/cognition/memory components reused rather than duplicated;
- Mac model provider boundary using the existing B2 model runtime and real-inference policy;
- deterministic Mac model provider tests;
- Mac Brain runtime tests;
- CLI launcher;
- Mac Brain test/evidence runner.

## Current execution path

```text
Mac camera / static image / microphone
   ↓
MacCamera / ImageCamera / MacMicrophone
   ↓
SpecialistPerception (neural)   ← optional Whisper STT
   ↓
TemporalWorldModel
   ↓
DeterministicCognition
   ↓
ReasoningProvider (deterministic | Ollama LLM)
   ↓
BrainSupervisor / safety
   ↓
VirtualBody
```

## M1 runtime integration (status: IMPLEMENTED)

Real neural perception now runs **through the live runtime**, not only standalone:

- `NeuralPerceptionBackend` (`MAC_BRAIN/models/neural_backend.py`) bridges `torchvision:ssdlite320_mobilenet_v3_large` output into the canonical `PerceptionBackend` contract.
- CLI paths: `--neural` (real backend), `--neural-image PATH` (headless static image), `--neural --live-camera` (real camera).
- Verified on-device on MPS: `python -m MAC_BRAIN.cli --neural --neural-image test-image.png --cycles 2` → detections `["tv", "laptop"]` flow through perception → world state → cognition → reasoning → authorized virtual action.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/M1-runtime-latest.json`.

The first slice therefore proves integration and runtime behavior with **real neural capability**, not only deterministic fixtures.

## Speech-to-text (status: IMPLEMENTED)

- `WhisperSTTProvider` (`MAC_BRAIN/models/stt.py`) — real offline STT via faster-whisper; one-time model download into the git-ignored `mac_test_results/STT/models` cache.
- `DeterministicSTTProvider` — CI/test fallback.
- `MacBrain.listen(seconds)` records via `MacMicrophone` and transcribes locally.
- CLI: `--transcribe PATH` (headless file transcription) and `--listen SECONDS` (live mic).
- Verified on-device: transcribed a TTS-generated WAV to "Hello world this is a speech to text test." (confidence 0.99).

## Reasoning + real actions (status: IMPLEMENTED)

- `DeterministicReasoningProvider` — bounded symbolic mapping of cognition conclusions to actions (default, CI-safe).
- `LLMReasoningProvider` / `OllamaReasoningProvider` — real local LLM reasoning through `MacModelProvider` + Ollama; the model is offered a fixed action allowlist and its choice is re-validated.
- The hardcoded `inspect` in `MacBrain.step()` is replaced with reasoning-driven action selection. The safety gateway allowlist now matches the virtual-body actions (`inspect/observe/wait/stop/move_forward/turn_left/turn_right`).
- Verified on-device: deterministic mapping yields `wait` for no-salience; the qwen3.8 LLM yields `observe` for the same neural input.

## Cognition + memory integration (status: IMPLEMENTED)

Speech transcripts and neural detections now flow into cognition **and** memory.

- `DeterministicCognition` recognizes a transient `speech` observation → conclusion `human_speech_observed` (speech is surfaced through the current cycle only, not a persistent world entity).
- `MacBrain.ingest_transcript(transcription)` admits the utterance to memory (`memory_type="utterance"`, with provenance + extracted entity refs) and runs a cognition pass over it.
- `MacBrain._admit_detections(...)` admits each detection to memory (`memory_type="perception"`) during `step()`, so detections are now durable evidence, not just transient world state.
- `MacBrain.listen()` / CLI `--listen` and `--transcribe` all feed transcripts through `ingest_transcript` (cognition + memory).
- Verified on-device: transcribing a WAV yields `human_speech_observed` and a retrievable utterance memory record; a neural cycle admits `tv`/`laptop` as perception memory records.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/STT-cognition-memory.json`, `perception-memory.json`.

## Bounded goals + virtual movement (status: IMPLEMENTED)

- `MAC_BRAIN/autonomy.py` — `Goal` (bounded: kind, target, priority, `max_steps`), `GoalState` (`active/completed/failed`), and `BoundedGoalController` that turns a reach goal into multi-cycle `turn_left/turn_right/move_forward` commands. Every cycle counts toward the step budget, so a goal can never move forever: it reaches its target within budget (`completed`) or is forced to `failed`.
- `MacBrain.set_goal(...)` adopts a goal; `step()` lets the active goal drive the action instead of the reactive one-shot action. Emits `goal.adopted` / `goal.status` events.
- CLI: `--goal-target X,Y` + `--goal-steps N` runs a bounded reach goal through the live runtime.
- Verified on-device: reach `(8,0)` moved forward and completed within the 0.5 m threshold; reach `(0,10)` turned to heading 90° then moved forward and completed.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/GOAL-reach.json`, `GOAL-turn.json`.

## Next implementation slice

## Memory recall into the autonomous loop (status: IMPLEMENTED)

- `MacBrain._recall_context(...)` retrieves relevant memories (queried from salient entities + detections) via the memory manager, then passes them as `recall` context into `reasoning.decide(...)`.
- `ReasoningProvider.decide` now accepts a `recall` argument; `DeterministicReasoningProvider` reflects it in the rationale (`recalled N relevant memories`), and `LLMReasoningProvider`/`OllamaReasoningProvider` pass the recalled memories to the model.
- Goal outcomes are admitted to memory (`memory_type="goal_outcome`), so past goal behavior is recallable.
- Emits `memory.recall` events.
- Verified on-device: detecting `alice` recalled 2 relevant memories; reasoning rationale showed `(recalled 2 relevant memories)`; the Ollama LLM path reported `recalled=1`.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/memory-recall.json`.

## Durable storage (Stage-1 per ADR-DATA-001) (status: IMPLEMENTED)

- `MAC_BRAIN/storage.py` — `DurableMemoryStore`, the ADR-DATA-001 candidate baseline: **SQLite, WAL journal mode, local, single-node**, offline. It is a durable persistence layer *below* the memory/autonomy semantics (it does not own cognition, memory, or authorization).
- Persists `MemoryRecord` (memory_type, content, confidence, verification, provenance, entity/event refs, temporal/spatial context) and bounded goal history to disk.
- `MacBrain(store_path=...)` uses the durable store as its memory when a path is given (falls back to the in-memory manager otherwise); `set_goal`/goal-terminal persist goal history; `stop()` closes the store.
- CLI: `--store PATH` enables durable storage.
- Verified on-device: after a full process restart on the same DB, **3 memory records + goal history survived**, `alice said hello` was retrievable, and `PRAGMA journal_mode` = `wal`.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/durability.json` (+ the persisted `novi-state.db`).

## Autonomous goal creation / curiosity (status: IMPLEMENTED)

- `Goal.investigate(entity, ...)` — a bounded curiosity goal (observe a target for up to `max_steps` cycles, then complete) alongside the existing movement (`reach`) goal.
- `MacBrain._spawn_curiosity_goals(...)` — per `04_GOALS_CURIOSITY_AND_LEARNING.md`, curiosity is now a **goal source**: when perception surfaces a *novel* entity (never seen before) and no goal is active, the brain auto-creates a bounded investigate goal. It never interrupts an active goal, and it won't re-spawn for the same entity.
- Config: `curiosity_enabled` (default True), `curiosity_investigate_steps` (default 5). Emits `curiosity.triggered`.
- Verified on-device: novel `gizmo` → `curiosity.triggered` → observe×5 → goal completed → durable `goal_outcome`, persisted after restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/curiosity.json`.

## Memory consolidation / decay (status: IMPLEMENTED)

- `MAC_BRAIN/consolidation.py` — `MemoryConsolidator` + `ConsolidationConfig` implementing the operations from `04_MEMORY_CONSOLIDATION_RETRIEVAL_AND_CONTEXT.md`: **expiry** (per-type TTL), **confidence decay** (exponential after a grace period), **archival** (below min confidence), and **contradiction resolution** (supersede the older/lower-confidence of conflicting same-entity facts).
- Lifecycle state (`active`/`archived`/`expired`/`superseded`) lives on the durable-store row (not the canonical `MemoryRecord`); archived/expired/superseded records are excluded from active retrieval but their historical rows are preserved.
- `DurableMemoryStore` gained a state column (with migration for existing DBs), `active_rows()`, `set_state()`, `set_confidence()`, `get_state()`, and active-only `retrieve`/`active_count`.
- `MacBrain.consolidate()` runs the pass (durable store only), auto-invoked in the loop via `consolidation_every`; emits `memory.consolidated`.
- Verified on-device: conflicting facts → older `superseded`, newer kept; old perception → `expired`; decayed-below-min → `archived`.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/consolidation.json`.

## Goal scheduling / priority (status: IMPLEMENTED)

- `BoundedGoalController` now supports a **priority queue** (`enqueue`/`pending_goals`) with the goal lifecycle extended to `PENDING` and `SUPERSEDED`.
- Scheduling (`_reconcile`): the highest-priority pending goal is promoted to active; a queued goal with **higher priority than the active goal safely supersedes it** (lower-priority goals are recorded as `superseded`, never deleted). An explicit `adopt` (e.g. user command) also supersedes.
- `MacBrain.enqueue_goal(...)` queues goals; `_sync_goal_states()` persists the full lifecycle (pending/active/superseded/completed/failed) to the durable store. Emits `goal.queued`.
- Verified on-device: a low-priority investigate goal was `superseded` by a higher-priority one, which `completed`; both states survived a process restart on the same DB.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/scheduling.json`.

## SQLite adoption gate (ARCH-CLOSE-003) (status: EVIDENCE PRODUCED)

- `MAC_BRAIN/benchmarks/arch_close_003_gate.py` — reproducible benchmark + fault-injection/recovery harness targeting the real `DurableMemoryStore`, per `27_ARCH_CLOSE_003_STAGE_1_STORAGE_BENCHMARK_SPEC.md`.
- **Decision: ADOPT** — all six mandatory correctness/recovery checks PASS: commit→reopen persistence, uncommitted rollback, duplicate idempotency, checkpoint→reopen integrity, backup→restore, malformed-migration isolation.
- Mac baseline: SQLite 3.53.4, **WAL**, write p50/p95/p99 ≈ 0.10/0.15/0.18 ms, ~9.3k events/s, **zero writer conflicts**. Full-scan retrieval (p99 ≈ 34 ms at ~2k rows) is noted as a scaling consideration for large memory (index/FTS roadmap).
- Evidence: `docs/01-system-architecture/evidence/ARCH-CLOSE-003-MAC-NOVI-002-storage-benchmark-result.json` (+ `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/arch-close-003-gate-result.json`). Automated test: `MAC_BRAIN/tests/test_arch_close_gate.py`.
- The PROPOSED→ADOPTED status change of ADR-DATA-001 remains the architecture authority's decision; this evidence is the required prerequisite.

## Soul layer (identity, personality, affect) (status: IMPLEMENTED)

- `MAC_BRAIN/soul.py` — `Soul`, `Identity`, `Personality`, `AffectState` implementing the P0 Soul spec (docs/06-soul): stable identity/personality/values, motivational priorities, and a transient affect model that decays toward baseline and shapes current expression.
- Model-independent and deterministic (no LLM); the boundary is enforced: **values never replace safety/policy, motivations never authorize, affect never rewrites personality**, and affect is computational state (no claim of human emotion).
- Affect updates from cycle events (goal success/failure, novel detections, speech, uncertainty) and drives a `tone()` expression used in speech.
- Durable persistence: `DurableMemoryStore` gains a `soul` table; durable identity/personality/values/motivations persist across restart while transient affect is not persisted (per 05_…§24).
- `MacBrain` wires soul in: `step()` updates affect and reports `soul.tone`; `stop()` persists the durable soul snapshot; `speak()` carries the tone.
- Verified on-device: success raised satisfaction (0.53) and cut frustration (~0.0); a bounded goal failure raised frustration (0.20) and caution (0.43); durable identity `Novi` and `non_harm`=1.0 survived restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/soul.json`.

## Social intelligence & relationships (status: IMPLEMENTED)

- `MAC_BRAIN/social.py` — `Relationship`, `RelationshipCategory`, `Relationships`, `SocialIntelligence` implementing the P0 social spec (docs/06-soul 03/04).
- **Relationship model** is multi-dimensional (familiarity, trust, respect, shared history, interaction frequency/quality, preference/boundary knowledge, stability) with independent evolution; categories (tiers) derive from evidence and one interaction never redefines a relationship. **Role ≠ permission** (no authorization lives in the relationship).
- **Social intelligence** gives relationship-sensitive expression (stranger → polite/reserved; friend → warm/playful; serious context suppresses playfulness) and a disciplined participation gate (silence is valid; cooldowns and duplicate-suppression prevent over-eager speech; direct address participates).
- Boundaries honored: Soul owns relationship *meaning/expression*; durability lives in `DurableMemoryStore` (new `relationships` table); interpretation stays out of this layer.
- `MacBrain` wires it in: `step()` notes an interaction when a person is detected, emits `social.interaction`, reports `social` in the result; `stop()` persists relationships durably.
- Verified on-device: first_meeting→visitor→familiar→friend as familiarity grew; stranger tone `polite` vs friend `warm`; participation gate responded when addressed and stayed silent during cooldown; relationship `alice`/friend/16 interactions survived restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/social.json`.

## Learned preferences & living lexicon (status: IMPLEMENTED)

- `MAC_BRAIN/lexicon.py` — `Lexicon`, `LexiconEntry`, `LexiconStatus`, `Scope`, `LearnedPreferences`, `CommunicationPreference` implementing the P0 learning spec (docs/06-soul 06) and living-lexicon spec (07).
- **Living lexicon**: seed vocabulary plus candidate→validated→adopted lifecycle with provenance, frequency, confidence, and scope. A single unusual phrase is never globally adopted; a relationship-scoped word stays scoped and is **not used when a stranger is present** (privacy gating) or with other people. Supports deprecate/reject retirement.
- **Learned preferences**: scoped, evidence-backed, revisable communication preferences (name, pronunciation, response length, detail, humor, greeting, …). Confidence rises with evidence and explicit statements; an explicit correction **supersedes** the older value with strong confidence rather than silently overwriting history; stale/learned assumptions are overridden by current context; a person's preference never leaks to others.
- Boundaries honored: preferences are distinct from personality and **never a permission**; learned vocabulary does not grant disclosure; current context overrides stale learning; all changes retain provenance/reversibility.
- `DurableMemoryStore` gains `lexicon` and `preferences` tables; `MacBrain` exposes `observe_expression`, `learn_preference`, `record_correction` and persists on `stop()`.
- Verified on-device: `rizz` observed→validated→adopted as frequency grew; relationship word `bubby` stayed scoped, usable privately, suppressed with a stranger present; preference confidence rose 0.3→0.65 with evidence/explicitness; a correction flipped `short`→`detailed` while others kept the default; both survived restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/lexicon.json`.

## Deepened cognition: beliefs & prediction/expectation (status: IMPLEMENTED)

- `MAC_BRAIN/cognition.py` — `BeliefSystem` and `ExpectationSystem` implementing docs/03-cognition 04/10 (reasoning engine, prediction & expectation) behind the existing cognition contract.
- **Beliefs/knowledge**: per-entity beliefs accumulate confidence with evidence, and a single contradicting observation does **not** silently flip an established belief — it records a contradiction and weakens confidence; only repeated strong contradiction flips it (provenance-preserving revision).
- **Prediction/expectation**: learns steady-state presence expectations from experience and flags an `expected_present_now_absent` violation when a stable pattern breaks. Predictions are explicitly marked as predicted (never overwrite observed state); violations emit `cognition.expectation_violation` / `cognition.predicted`.
- `DurableMemoryStore` gains `beliefs` + `expectations` tables; `MacBrain.step()` updates beliefs/expectations from each cycle's detections and persists on `stop()`.
- Verified on-device: belief confidence rose 0.9→1.0 with evidence; a single contradiction kept the value and dropped confidence to 0.85; a repeated contradiction flipped the belief; a steady entity's unexpected absence produced an expectation violation (confidence 1.0); both survived restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/cognition.json`.

## Retrieval index / FTS (status: IMPLEMENTED)

- `DurableMemoryStore` now maintains an **FTS5 virtual table** (`memory_fts`) over memory content + entity refs, kept in sync on insert and forget.
- New `retrieve_indexed(...)`: finds candidate `memory_id`s via `MATCH`, then fetches/JSON-parses only the matched subset (instead of the prior full-scan + parse-every-row path). Falls back to the full-scan `retrieve` when the query is empty or the FTS engine rejects a query, so it is always safe. The Mac Brain's `_recall_context` uses `retrieve_indexed` when the store supports it (in-memory manager falls back to `retrieve`).
- `retrieve` is unchanged and remains the always-correct reference path; `test_storage_index.py` asserts result parity between the two.
- Benchmark (on-device): full-scan vs indexed read latency at N active records —
  - 500 → 4.07 ms vs 1.37 ms (**3.0×**)
  - 2,000 → 16.61 ms vs 1.71 ms (**9.7×**)
  - 5,000 → 41.89 ms vs 2.28 ms (**18.4×**)
  The speedup grows with size because the scan path parses every row while the FTS path parses only matched rows.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/retrieval-benchmark.json`.

## Temporal & causal cognition (status: IMPLEMENTED)

- `MAC_BRAIN/temporal.py` — `TemporalModel` + `CausalLink` implementing docs/03-cognition/08 (temporal & causal reasoning): a bounded **event series/timeline** with cycle ordering, **recency/freshness**, **stale-state** detection, and on-demand **causal-link learning** (A within a window before/with B) with a confidence tier (`observed → inferred → plausible_cause → verified`).
- **Prediction**: `expected_after(event)` ranks the most likely next events from learned sequences.
- Boundaries honored: observations are separated from inferences; memory owns durable history; causal/predictive confidence is never a hard timing guarantee and never rewrites observed history; event-time vs processing-time stay distinguishable.
- `DurableMemoryStore` gains a `temporal` table; `MacBrain.step()` records each cycle's observed + acted events, emits `cognition.temporal`, reports `temporal` in the result, and persists on `stop()`.
- Verified on-device: a repeated `door_open → alice_present → light_on` routine produced **verified** causal links (confidence 1.0) with reverse links lower (0.89); `expected_after(door_open)` → alice_present/light_on; a diluted signal→lamp relationship landed at confidence 0.5; recency 0.95 and stale detection worked; all links survived restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/temporal.json`.

## Multimodal fusion (status: IMPLEMENTED)

- `MAC_BRAIN/fusion.py` — `MultimodalFusion`, `ModalityObservation`, `FusedEvent` implementing docs/03-cognition/03 and 02-novi-brain/16: normalizes observations from independent modalities, **temporal alignment** via a bounded freshness window (stale evidence rejected), **entity association**, and **confidence-weighted evidence fusion** (noisy-OR) that rises with cross-modal agreement while **retaining all per-modality provenance**.
- **Conflict handling**: when the same entity has several strong disagreeing values, both are preserved, confidence is reduced, and no false certainty is set. **Graceful degradation**: a failed/missing modality does not block the rest. Fusing is deterministic and replayable.
- `DurableMemoryStore` gains a `fusion` table; `MacBrain` buffers speech observations in `ingest_transcript`, fuses them with vision detections each `step()`, emits `fusion.completed`, reports `fusion` in the result, and persists on `stop()`.
- Verified on-device: vision(0.6)+speech(0.6) → fused **0.84** across {vision,speech} with both contributions kept; a vision `on` vs speech `off` conflict preserved both at reduced confidence 0.5; a missing modality degraded gracefully; a 1-hour-old observation was rejected as stale; deterministic replay matched; fused events survived restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/fusion.json`.

## Semantic / vector memory (status: IMPLEMENTED)

- `MAC_BRAIN/vector.py` — `EmbeddingProvider` (protocol seam), `HashingEmbedding` (deterministic, offline, local; no weights/cloud), `EmbeddingIndex` (add/remove/search by cosine similarity), `cosine`/`normalize`. A real local embedding model (e.g. a sentence-transformers adapter on MPS) can be plugged in behind the same seam later.
- `DurableMemoryStore` gains a `vectors` table + a persistent `EmbeddingIndex`: every admitted record is embedded (L2-normalized, 256-d), removed on `forget`, loaded on reopen. New `retrieve_semantic(query, entity, memory_type, limit)` ranks by cosine similarity.
- `MacBrain.recall_semantic(query)` exposes semantic recall and emits `memory.semantic_recall`.
- Verified on-device: query "lamp"/"plant"/"door" each ranked the correct record first; embeddings are deterministic; cosine ranks similar > unrelated; indexing 5,000 records took ~0.87s and a 5,000-doc vector search ~0.03s; vectors persist and are removed across reopen/forget.
- Honest scope: the default `HashingEmbedding` is token-overlap (lexical) similarity — synonym-level semantics (e.g. "light" vs "lamp") require the real-model adapter, which is documented as the seam.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/vector-memory.json`.

## Interactive live brain demo (status: IMPLEMENTED)

- `MAC_BRAIN/live.py` — `LiveSession` ties the real local senses into one loop: camera stream (real Mac camera, static image, or deterministic fallback), periodic speech-to-text (local Whisper, or a deterministic transcript injection for offline/test), reasoning (local LLM via Ollama when available, else deterministic), **soul tone expression**, and **text-to-speech** via macOS `say` (gracefully skipped if absent).
- CLI: `python -m MAC_BRAIN.cli --live [--rounds N] [--live-steps N] [--listen-seconds S] [--demo-hear TEXT] [--say] [--neural --neural-image IMG --device mps]`.
- Everything degrades gracefully — a missing camera/microphone/model/voice falls back rather than aborting, so the demo is fully offline and testable with fakes.
- Verified on-device: offline deterministic run looped 2 rounds (saw=none, heard injected transcript, tone=warm, composed reply, wrote evidence JSON + durable DB); a **neural** live round on a static image detected **tv, laptop** via MPS, toned `curious`, and composed a reply naming what it saw and heard. Emits `live.round_completed`.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/live-demo.json`, `live-neural.json`, `live.db`.

## Resume goals across restart (status: IMPLEMENTED)

- Closes the resume-goals durability gap: `MacBrain._load_goals()` rebuilds **active / pending / terminal** goal state into the `BoundedGoalController` on startup against the durable store. The active goal is resumed with its step budget and `steps_taken` preserved (still bounded), pending goals are re-queued by priority, and terminal goals are loaded into history without being re-inflated as active.
- `stop()` now persists goal lifecycle (`_sync_goal_states`) and the **virtual body pose** (`save_body`/`load_body`) so a resumed reach goal continues from its true position instead of resetting to the origin.
- Fixed: reach-goal targets reload as **tuples** (they were JSON lists, which the controller treated as invalid and failed).
- Verified on-device: a reach goal at steps_taken=3 / pose x=1.5 shut down and, after restart with the same store, resumed as `active` with steps_taken=3, pose restored to x=1.5, and continued `move_forward` x=2.0→3.0 (no origin reset). Pending and terminal goals also resume correctly.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/resume-goals.json`.

## Identity / person recognition (status: IMPLEMENTED)

- `MAC_BRAIN/identity.py` — `PersonIdentity` + `IdentityBelief` implementing the Cognition person model (docs/03-cognition 03 example, docs/06-soul/04, docs/02-autonomy/03): combines camera detections, face observations, and naming (speech) into a per-person **identity belief** with explicit **detected / probable / verified** tiers, confidence, and per-modality provenance.
- **Boundaries**: recognition confidence is never authorization; uncertain identity is preserved as uncertainty (a low-confidence name stays `detected`, never asserted); a tier is always revisable as evidence arrives.
- `MacBrain` observes person presence from vision each `step()`, binds a spoken name from `ingest_transcript`, emits `identity.observed`/`identity.named`, reports `identity` in the result, and persists it durably.
- Verified on-device: person present → `detected` (no name); naming raises to `probable`; vision+speech agreement → `verified` at 0.997 across {vision,speech}; a low-confidence name stayed `detected` (uncertainty preserved); verified identity survived restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/identity.json`.

## Reasoning model router + structured output (status: IMPLEMENTED)

- `MAC_BRAIN/models/router.py` — `ReasoningRouter` selects between the deterministic provider and the local LLM (Ollama/qwen) by task confidence: confident situations route to deterministic (fast/safe/explainable), uncertain situations escalate to the LLM; if the LLM is unavailable or errors, it degrades to deterministic. Route + reason are tracked (`reasoning.route` event, route counts).
- `MAC_BRAIN/models/validation.py` — `StructuredOutputValidator` + `action_output_spec`: validates/coerces a reasoning model's JSON output against the allowed-action schema (required field, enum allowlist, type coercion, defaults). `LLMReasoningProvider` now runs every response through it; a failing/out-of-allowlist result is rejected and replaced with the safe default.
- CLI: `--reasoning router [--route-threshold N]`. `MacBrain` emits `reasoning.route` and reports `reasoning_route` each step.
- Verified on-device: confident 0.9 → deterministic; uncertain 0.4 → llm; llm unavailable → graceful deterministic fallback (`llm_error`); valid output accepted; `action:"hack"` rejected with error; missing required field rejected; invalid LLM output fell back to default `wait`. Route counts tracked. Brain wiring reports the route and emits events.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/router-validation.json`.

## Entity knowledge graph (status: IMPLEMENTED)

- `MAC_BRAIN/kgraph.py` — `EntityKnowledgeGraph` + `KnowledgeTriple` maintains a durable **entity→relation→entity** graph with confidence (noisy-OR over agreeing evidence), provenance, entity typing (person/place/object), and **contradiction handling** that preserves all evidence rather than overwriting (the highest-confidence object stays active; the rest are marked `contradicted`).
- Deterministic **triple extraction** from episodic text/entity-refs via a small predicate lexicon (`extract_from_text`). Typed queries (`triples`, `leading`, `context`), conflict detection, and snapshot/from_snapshot persistence.
- `MacBrain` learns triples from spoken utterances (`_learn_triples`), emits `knowledge.updated` / `knowledge.contradiction` / `knowledge.recalled`, exposes `retrieve_knowledge(entity)`, reports graph counts each step, and persists durably.
- Boundaries (docs/04-memory-and-knowledge/12): learning is memory-level, never schema mutation; knowledge is evidence-backed and revisable; knowledge feeds reasoning, it is not authorization.
- Verified on-device: speech → learned triple (alice→moved→door); `alice located_near kitchen` then `...garden` → conflict flagged, `kitchen` stays active, `garden` contradicted; extraction and typing correct; graph survived restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/kgraph.json`.

## Multi-step planning context (status: IMPLEMENTED)

- `MAC_BRAIN/planner.py` — `Planner`, `Plan`, `PlanStep`: decomposes a goal into an ordered, **typed** step plan (determine → execute → verify) with per-step expected outcomes, tracks each step's status (pending/active/completed/failed/cancelled), and supports **replanning/cancellation** when observations invalidate assumptions (docs/02-autonomy/01).
- `MacBrain` generates a plan on `set_goal` (`plan.created`), advances it one step per cycle (`plan.step` → `plan.completed`/`plan.failed` on goal terminal), feeds the current plan into reasoning (situation context), exposes `current_plan()`/`replan_goal()`, reports the plan each step, and persists plans durably so a resumed goal keeps its plan.
- Boundaries: plans are context; the controller and Policy/Safety still gate every executed action; a plan is always revisable.
- Verified on-device: a reach goal decomposed into evaluate→navigate→verify (with expected outcomes); advancement moves through the steps and completes; replan yields a fresh plan; brain wiring reported the active step and emitted `plan.created`/`plan.step`/`plan.completed`; a resumed goal kept its plan across restart.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/planner.json`.

## Memory privacy & erasure governance (status: IMPLEMENTED)

- `MAC_BRAIN/privacy.py` — `PrivacyGovernance` implements docs/04-memory-and-knowledge/14: deterministic **privacy classification** (public/operational/personal/sensitive/credential/biometric/location/communication/derived), per-class **retention & expiry**, **purpose limitation + consent**, and governed operations **RESTRICT / DELETE(GENERALIZE) / ERASE**.
- Erasure is **physical** (`hard_delete` — cannot be undone by recovery) and **propagates to dependent derived representations** (`dependency_refs`) so derived data never outlives its source. A **right-to-be-forgotten** (`forget_entity`) erases all records referencing a person and their dependents.
- **Authorization gate** (`authorize_ids`) is enforced in the brain's recall so retrieval never exposes records above a sensitivity limit or outside an allowed purpose.
- Store gained governance primitives: `hard_delete`, `update_memory`, `set_expiry`, `records_by_entity`, `dependent_ids`, `count_by_class`, `expired_ids`, `gate_governance`, plus `purpose`/`consent` columns (migrated).
- `MacBrain` classifies at admission (utterance/perception/goal), purpose-binds + expires each record, gates recall, and exposes `forget_memory`/`forget_entity`/`restrict_memory`/`generalize_memory`/`privacy_status`. Emits `privacy.gate`/`privacy.erased`/`privacy.entity_erased`/`privacy.restricted`/`privacy.generalized`.
- Verified on-device: credential/personal/location/derived/operational classification; purpose+expiry binding; erasure propagated to a dependent record (both physically gone); sensitive record blocked from retrieval; right-to-be-forgotten erased 2 records; restrict→`restricted`; generalize→`derived` coarse summary; retention sweep removed an expired record.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/privacy-governance.json`.

## Non-speech audio / hearing (status: IMPLEMENTED)

- `MAC_BRAIN/audio.py` — `Hearing`, `AudioFrame`, `AudioEvent`, `AudioQuality` implement the offline-hearing subset of docs/02-novi-brain/13: VAD-style **speech/non-speech** classification, **sound-event detection** over an extensible taxonomy (knock/footstep/door/impact/object_fall/glass_break/alarm/appliance/machinery/vehicle/animal/clap/cry/laugh/cough/sneeze/unknown), acoustic **anomaly/novelty** representation (unknown sounds are never forced into a class), optional **direction-of-arrival** (uncertain), and **audio-quality** monitoring (clip/saturation/silence/excess_noise/channel_fault).
- Determinism boundary (mirrors perception): a real SED model/front-end (future/Jetson) supplies an `AudioFrame` feature descriptor; the deterministic `Hearing` turns that evidence into typed, confident `AudioEvent`s and **degrades gracefully when ASR is absent** (a failed model never makes Novi deaf).
- `MacBrain.ingest_audio_frame(frame)` detects events, monitors quality, admits attention-worthy events to durable memory (governed/classified), feeds audio into **multimodal fusion**, and reports hearing each step. Emits `hearing.event` / `hearing.voice` / `hearing.anomaly` / `hearing.quality`.
- Verified on-device: silence / speech(VAD) / alarm(beep) / knock / unknown(anomaly) / impact; quality clip-saturation-silence-fault; a knock→alarm fed fusion as an `audio` modality, was admitted to memory, and reported in the step result.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/audio-hearing.json`.

## Health & observability loop (status: IMPLEMENTED)

- `MAC_BRAIN/observability.py` — implements docs/02-novi-brain/28:
  - **Health**: PASS / WARN / FAIL / UNKNOWN checks over all brain subsystems with aggregate precedence `FAIL > WARN > PASS > UNKNOWN`; snapshots carry status, detail, individual checks, and wall-clock + monotonic timestamps. A failing check degrades to FAIL without crashing the brain.
  - **Metrics**: deterministic in-process `MetricRegistry` (name, value, unit, normalized labels) with stable snapshot ordering; external exporters intentionally deferred (vendor-neutral).
  - **Diagnostics**: bounded structured log (severity DEBUG/INFO/WARN/ERROR, message, structured context, wall-clock + monotonic time).
- `MacBrain` runs the health loop + records metrics each cycle (`_update_observability`), exposes `health_report()` / `metrics_snapshot()` / `add_diagnostic()`, and emits `observability.health` / `observability.metrics` / `observability.diagnostic`. Health/metrics reported in the step result.
- Verified on-device: FAIL dominates / WARN surfaces / PASS when healthy; a durable brain reports all 12 subsystems `PASS`; a non-durable brain correctly reports `WARN` (governance disabled — degraded but usable); metrics snapshot is deterministically ordered with labels preserved; diagnostics carry structured context + dual timestamps.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/observability.json`.

## Live web app (status: IMPLEMENTED)

- `web/server.py` — `NoviWebServer` + a stdlib-only HTTP server (no web framework, no installs) that owns a running `MacBrain` on a background auto-step thread and exposes a JSON API + a single-page browser UI. All brain access is serialized through a lock; the store connection is cross-thread safe for this serialized pattern.
- `web/static/index.html` — dark terminal UI with all four requested interactions:
  - **Live chat / "hear this"**: type what Novi hears → `POST /api/chat` → Novi replies with its reasoning trace.
  - **Live chat + reasoning trace**: a running conversation (`POST /api/chat`, `GET /api/chat`); each message shows Novi's **conclusion, confidence, action, rationale, reasoning route** (deterministic vs local qwen), and how many memories it recalled — so you can follow exactly *how* Novi decided. When the local `qwen3.8` model (Ollama) is reachable, Novi generates a real conversational reply grounded in recalled knowledge and its current mood (`route: ollama:qwen3.8`, `action: respond`); if Ollama is offline it falls back to the deterministic conclusion. The UI shows a "thinking…" indicator while the model generates.
  - **Live state dashboard**: reasoning (conclusion/confidence/action/route), Soul affect + tone, active goal + plan + history, knowledge counts, hearing, memory, and a live PASS/WARN/FAIL/UNKNOWN health badge — polled every second.
  - **Action buttons**: step once, reach a goal, hear audio events (knock/alarm/footstep/unknown), health check.
  - **Live event log**: every brain event (cognition, memory, hearing, privacy, knowledge, observability, …) streamed with per-event seq cursors.
- Deterministic camera by default (no webcam permissions needed); durable store optional via `--store`.
- `scripts/mac-web.sh` launcher (`http://127.0.0.1:8080`).
- Verified on-device over real HTTP: served the UI, state cycle/health(PASS), `/api/hear` accepted `alice moved the door` → `human_speech_observed`, `/api/audio` heard `alarm`, `/api/goal` adopted reach(2,2) active, health report PASS, and the event log carried 20 distinct event types.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/web-app.json`.

## Incremental knowledge persistence (status: IMPLEMENTED)

- The knowledge graph previously flushed to the durable store **only on graceful `stop()`**; a crash/hard kill lost anything learned since the last clean shutdown.
- Now every triple is written **immediately** as it is learned: `EntityKnowledgeGraph` gained an `on_change` hook fired after each `add()` (covers reconcile/evidence bumps too), and `MacBrain` attaches it to a `_persist_knowledge()` that calls `DurableMemoryStore.save_knowledge()` (immediate WAL commit) whenever the memory is durable.
- Verified on-device: told Novi "alice moved the door", then `SIGKILL`-ed the process (no graceful stop); a fresh process on the same store still had `(alice, moved, door)`. No knowledge lost on crash.
- New tests: `MAC_BRAIN/tests/test_knowledge_persistence.py` (persisted-before-stop, reload-on-start, graph hook fires).
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/incremental-knowledge-persistence.json`.

## Web: real sensing + reasoning router + live task view (status: IMPLEMENTED)

- **Real sensing**: the web server accepts `--camera real` (live webcam instead of the demo camera) and, with it, real microphone speech-to-text via faster-whisper. A new **🎤 Listen** button (`POST /api/listen`) records from the mic, transcribes locally, ingests it, and replies in chat. `/api/listen` is gated on real sensing and degrades cleanly otherwise.
- **Reasoning router in the web**: the server accepts `--reasoning {deterministic,ollama,router}` (+ `--route-threshold`); `router` builds the confidence-based `ReasoningRouter` so uncertain steps escalate to the local qwen, and the `reasoning_trace.route` in `/api/state` reflects which backend decided. Falls back to deterministic on LLM error.
- **Live task view**: `state()` now exposes the active plan and `active_goal.distance_to_goal`; the UI adds a **Goals & Plan** panel with plan steps and a small **virtual floor map** (canvas) showing Novi's position/heading moving toward the goal target (green G) as it plans and navigates.
- New tests: router built, listen gating, plan + goal distance in state (web tests → 14).
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/web-real-sensing-router-task.json`.

## Learn names from discussion + incremental identity persistence (status: IMPLEMENTED)

- **Entity extraction** (`MacBrain._entities_in_text`) previously only recognized a hardcoded handful (`alice`, `door`, …) — a brand-new name like `Vano` was invisible, so Novi couldn't learn people from conversation. It now also recognizes capitalized proper nouns (plus the known person-name labels and perceived world entities), so new people/places are learned from natural discussion.
- **Identity persistence**: person-name bindings (who Novi has recognized) were only saved on graceful `stop()`; now `identity.observe` triggers `_persist_identity()` → `save_identity()` immediately (WAL), mirroring the incremental knowledge persistence.
- **Chat recall**: the web reply context now includes known people, so Novi can say *"yes, I remember you — you're Vano."*
- Verified on-device: told Novi *"Hi novi, its me Vano"* → identity recorded `person→vano`; then `SIGKILL` (no graceful stop) → a fresh process on the same store still held the binding.
- New tests: name learned from conversation; identity persisted-before-stop and reloads-on-start (334 passing).
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/learn-names-identity-persistence.json`.

## Switchable LLM (qwen ⇄ NVIDIA Nemotron 3.5 Lightning) (status: IMPLEMENTED)

- Added a runtime model switcher in the web app: `GET/POST /api/model` returns/sets the active chat+reasoning model.
- Available models: `qwen3.8:latest` and `nemotron-3.5-lightning` (NVIDIA's fast 30B-A3B mixture-of-experts); a model `<select>` in the app header switches between them live.
- `--model <name>` CLI flag sets the default (now `nemotron-3.5-lightning` for speed); `--ollama-model` still overrides the reasoning/chat model explicitly.
- New test `test_model_switcher` (web/tests); 335 passing.
- **Nemotron fix**: 3.5 Lightning is a chain-of-thought model; without a top-level `think:false` it exhausts the token budget thinking and returns an empty `content`. Set `think:false` in chat (`_llm_chat`) and the reasoning provider, with a CoT→`thinking`-parse fallback. Replies dropped from qwen's ~20–40s to **~1.4s**.

## Web UI redesign (status: IMPLEMENTED)

- Tabbed SPA: **Chat / State / Event Log**; Event Log moved to its own page.
- **Live chat is now full-window**: your messages bubble on the **right**, Novi's on the **left** (with avatar + trace), scrollbar hidden but still scrollable (`scrollbar-width:none`), input pinned to the bottom.
- Loaders & spinners: thinking spinner while Novi replies, spinner on the send button, pulsing Novi logo, fade-in bubble animation, rotating "awake" empty-state.
- Live **graphs**: Confidence and Knowledge-growth sparklines on the State page.
- Model dropdown moved to a tidy header control.

## Cognition 2.0: situation understanding + memory-grounded reasoning (status: IMPLEMENTED)

- New `MacCognition` (`MAC_BRAIN/cognition2.py`) replaces the shallow salience classifier. It grounds reasoning in:
  - **knowledge-graph relations** relevant to salient entities,
  - **active-goal context** (kind/target/distance/progress),
  - **recalled memories** retrieved before reasoning.
- `Situation`/`ReasoningResult` extended (backward-compatible) with `relations`, `goal`, `recalled`, `hypotheses`, `inferences`.
- `reason()` now emits **multiple hypotheses** with confidence and **temporal/causal inferences** (e.g. knowledge `alice moved door` + alice salient → *"alice likely moved door"*), and refines the headline conclusion (`causal_change_inferred`, `goal_relevant_change`).
- Runtime `step()` does a two-pass cognition (preliminary situation → recall → full cognition grounded in knowledge+goal+memory) and passes a serializable situation to the reasoning providers.
- New conclusions mapped in the deterministic action map (`causal_change_inferred→inspect`, `goal_relevant_change→observe`).
- Web reasoning trace now shows inferences + hypotheses.
- Verified on-device: taught "alice moved the door", detected alice → conclusion `causal_change_inferred`, inference "alice likely moved door", hypotheses from knowledge/goal/memory, action `inspect`.
- New tests `MAC_BRAIN/tests/test_cognition2.py` (5); full suite **341 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/cognition2.json`.

## Reasoning 2.0: deliberative action selection + reflection/self-correction (status: IMPLEMENTED)

- New `DeliberativeReasoningProvider` (default) scores candidate actions from the full situation (conclusion, confidence, knowledge relations, goal context, recalled memories, latest reflection) instead of a single conclusion→action lookup.
- New `ReflectionEngine` (`MAC_BRAIN/reflection.py`): after each action the runtime judges whether it had its intended observable effect (body moved for move/turn; something salient/inferred to attend for inspect/observe) and records a `reasoning.reflection` event.
- The latest reflection is fed into the next reasoning decision: an ineffective action is penalized and `observe` boosted (self-correction).
- Verified on-device: reflection events emitted each cycle with `effective`/`action`/`note`; deliberative provider picks `inspect` for causal change, `wait` for no salience, `observe` for person/speech, and avoids repeating an ineffective action.
- New tests `MAC_BRAIN/tests/test_reasoning2.py` (7); full suite **348 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/reasoning2.json`.

## Memory 2.0: importance-weighted retrieval + episodic narrative (status: IMPLEMENTED)

- `_recall_context` now scores recall candidates by **relevance × recency × importance** (`0.5·relevance + 0.3·recency + 0.2·importance`) instead of raw FTS rank, so the most useful memories win the top slots.
- New `_episodic_narrative()` reconstructs a short narrative from recent episodic memories (utterances/perceptions), surfaced in the reasoning situation.
- Verified on-device: taught "alice moved the door / alice likes jazz / the door is open" → narrative reconstructed; recall for `alice` returns the relevant utterances.
- New tests `MAC_BRAIN/tests/test_memory2.py` (4); full suite **352 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/memory2.json`.

## Next implementation slice

- **Regression:** full suite `python -m pytest MAC_BRAIN/tests brain/tests` → **201 passed**.
- **End-to-end durable run** (`EVIDENCE/mac/<stamp>/integration.json`): a scripted perception sequence drove the whole pipeline (perception → memory admit/recall/consolidation → cognition → reasoning → goals → action → soul → social → lexicon/preferences/beliefs), then a **restart** re-opened the same store and every subsystem reported persisted state:
  - `memory_active_after_restart=6`, `soul_identity=Novi`, `alice_relationship=friend`,
    `lexicon_buddy_status=scoped`, `pref_response_length=detailed` (correction superseded),
    `belief_lamp={value:true, contradictions:1}`, `expectation_violations_fired=2`,
    tone `warm`, and the full emitted event stream.
- **Durability surface audit:** the store now persists **10 domain tables** (`memory_records`,
  `goals`, `soul`, `relationships`, `lexicon`, `preferences`, `beliefs`, `expectations`,
  `memory_fts`, plus the consolidated state tables) — all constructed on init, loaded on
  restart, and saved on `stop()`.
- **Cleanup:** removed stray `$DEST/` scratch dirs, a `_cap.py` leftover, empty evidence
  directories from failed captures, and consolidated a single clean evidence index
  (`IMPLEMENTATION_PLAN/EVIDENCE/mac/INDEX.md`).
- **Known limitation (noted, not blocking):** goal *history* is persisted to the `goals`
  table but is not rebuilt into the in-memory `BoundedGoalController` on restart — so a
  restart does not resume an interrupted goal. Bounded goals are short-lived by design, so
  this is acceptable for the current stage; resuming goals across restart is a future item.
- `mac_brain_evidence.json` (tracked, first-slice artifact) left in place.

## Evidence rule

Passing CI tests establishes software correctness for the first slice. The Mac prototype is not accepted until the actual Mac device path is exercised and evidence is collected through `scripts/mac-brain-test.sh` and the MAC_TESTING program.
