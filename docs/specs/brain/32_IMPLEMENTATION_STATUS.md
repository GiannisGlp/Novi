# Mac Brain Implementation Status

> **SUPERSEDED on structure (2026-08-26).** This document describes a `MAC_BRAIN` package
> separate from `brain/`. That split no longer exists — the code is a single unified
> `novi/brain/` package. The implementation *capabilities* described here are still accurate;
> only the package layout references are stale. See
> [`docs/00-strategy/STATUS_2026-08-26.md`](../../00-strategy/STATUS_2026-08-26.md).

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

## Spatial model (roadmap item 11) (status: IMPLEMENTED)

- `MAC_BRAIN/spatial_map.py` — `SpatialMap`: coordinate **frames**, **regions** (bounds in a frame), **doors** (room adjacency), **occupancy**, metric↔semantic **placement** (pose must be in a registered frame), `visible_entities`, `reachable_regions` (BFS via doors + containment), `visibility_between`, `snapshot()`, and `to_spatial_state()` feeding `WorldState.spatial_state`. `default_home_map()` builds kitchen / living_room / table_zone with a kitchen↔living_room door.
- `MacBrain(spatial_map=...)` (backward-compatible kwarg); `brain.spatial` exposes the model; 14 tests (`MAC_BRAIN/tests/test_spatial_map.py`).

## Typed cognition emission (roadmap item 12) (status: IMPLEMENTED)

- `MAC_BRAIN/cognition_typed.py` — `emit_cognitive_typed(situation, reasoning, ...)` → `TypedCognitionOutput` with canonical **SituationState**, **PersonContext**(s), **IntentHypothesis**(s), **Prediction**(s), **CognitiveDecisionRecord** (interpretation-only, never authorization), and **CognitiveEvent**(s), all carrying correlation/causation ids and provenance.
- `MacCognition.cycle_typed(...)` and `MacBrain.cognition_typed()` (publishes `cognition.typed` on the event bus, stores `_last_typed_cognition`). Every emitted object passes `cognition.validation.validate_structurally` against the canonical JSON Schemas; 9 tests (`MAC_BRAIN/tests/test_cognition_typed.py`).

## Learning pipeline (roadmap item 13) (status: IMPLEMENTED)

- `MAC_BRAIN/learning_pipeline.py` — `KnowledgePromotionPipeline` (evidence + confidence thresholds; **SIMULATED/PREDICTED never promote**), `UserCorrectionLog` (explicit corrections supersede prior claims at authoritative confidence, history preserved as contradicted, full provenance), `RoutineDetector` (repeated co-occurrence patterns as INFERRED hypotheses only), `CounterfactualEngine` (SIMULATED hypothetical slices, never merged into facts — Imagination Boundary).
- Runtime wiring: `observe_knowledge` / `correct_knowledge` / `observe_routine` / `counterfactual` with `learning.*` events; 17 tests (`MAC_BRAIN/tests/test_learning_pipeline.py`).

## Memory-class decision + schema-evolution hooks (roadmap item 16) (status: DECIDED)

- `MAC_BRAIN/memory_classes.py` — `MemoryClassDecisionRegistry` records implemented-now (semantic/episodic/spatial/temporal/preference/routine-candidate/procedural-candidate) vs deferred-to-body (procedural-competence/prospective/metamemory/autobiographical) with rationale; `SchemaEvolutionGate` classifies changes by the **L0–L6 ladder** (L0–L3 autonomous, L4 proposal-gated, L5/L6 never autonomous). Wired as `brain.memory_classes` + `brain.schema_evolution`; 10 tests (`MAC_BRAIN/tests/test_memory_classes.py`).

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
- Available models: `qwen3.8:27b`, `qwen3:8b`, `qwen3:4b`, and `nemotron-3.5-lightning` (NVIDIA's fast 30B-A3B mixture-of-experts); a model `<select>` in the app header switches between them live.
- `--model <name>` CLI flag sets the default chat model (persisted UI choice first, then `qwen3:4b`); `--ollama-model` still overrides the reasoning/chat model explicitly.
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

## Multi-step LLM deliberation (Reasoning 3.0) (status: IMPLEMENTED)

- New `DeliberativeLLMReasoningProvider` (`MAC_BRAIN/models/deliberation.py`) replaces the single-shot LLM decision with a **bounded structured deliberation**: the model explicitly reasons through ANALYSIS → OPTIONS → DECISION before committing to one action.
- The deliberation trace (analysis, options, decision) is captured on `last_deliberation`, emitted as a `reasoning.deliberation` event, and shown in the web reasoning trace.
- The chosen action is re-validated against the fixed allowlist; an invalid/missing decision falls back to the safe default.
- Wired into the web server as the LLM path for both `ollama` and `router` modes.
- Verified on-device with real nemotron-3.5-lightning: given a causal-change situation it produced a rich analysis, 4 options with pros/cons, and a well-reasoned `observe` decision.
- New tests `MAC_BRAIN/tests/test_deliberation.py` (8); full suite **360 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/deliberation.json`.

## Memory consolidation into higher-level summaries (Memory 3.0) (status: IMPLEMENTED)

- New `SummaryConsolidator` (`MAC_BRAIN/consolidation.py`): groups active episodic memories (utterances/perceptions) by shared entity and distills each group into a single higher-level `summary` memory.
- Summaries are retrievable by entity like any other memory, so recall surfaces the gist rather than a pile of raw episodes.
- Deterministic and CI-safe (no LLM dependency); idempotent across restarts (an entity is only summarized once).
- Wired into the runtime `consolidate()` pass; emits a `memory.summarized` event.
- Verified on-device: taught 3 alice episodes → one summary "alice: alice moved the door; alice likes jazz; alice is in the hallway".
- New tests `MAC_BRAIN/tests/test_consolidation_summary.py` (4); full suite **364 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/consolidation-summary.json`.

## Goal-resume across restart: mid-pursuit step-budget preservation (status: IMPLEMENTED)

- Goal-resume across restart was already implemented (`_load_goals()` restores active/pending/terminal goals and the body pose). This slice closes the remaining gap: **active-goal step progress is now persisted each cycle during pursuit**, so a mid-pursuit kill (SIGKILL) resumes with the correct step budget instead of a reset one.
- Verified on-device: adopted a reach goal, stepped 4×, killed without graceful stop → restarted brain resumes the same goal with `steps_taken=4` preserved.
- New test `test_mid_pursuit_kill_preserves_step_budget` in `MAC_BRAIN/tests/test_resume_goals.py`; full suite **365 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/goal-resume.json`.

## LLM-enhanced memory summaries (Memory 3.1) (status: IMPLEMENTED)

- New `LLMSummarizer` (`MAC_BRAIN/models/summarizer.py`): writes a true semantic gist for a group of episodic memories using the local Ollama model, instead of a deterministic concatenation.
- `SummaryConsolidator` now accepts an optional `summarizer` callable; when it returns a summary it is used, otherwise it falls back to the deterministic concatenation (best-effort, CI-safe).
- Wired into the web server: the brain is built with an LLM-backed `SummaryConsolidator` when Ollama is available.
- Verified on-device with real nemotron-3.5-lightning: 3 alice episodes → "Alice is currently in the hallway and moved the door; she has an affinity for jazz music."
- New tests `MAC_BRAIN/tests/test_summarizer.py` (6); full suite **371 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/llm-summaries.json`.

## Consolidation surfacing in the web UI (status: IMPLEMENTED)

- `GET /api/state` now exposes `memory.summaries` (recent consolidated summary memories) via a new `_memory_summaries()` helper.
- New **"Consolidated Memory"** panel on the State page renders each summary (entity + content), refreshed every second with the rest of the state.
- Verified: taught "alice moved the door / alice likes jazz", consolidated → state returns the LLM summary "Alice likes jazz and moved a door."
- New test `test_state_includes_consolidated_summaries` in `web/tests/test_web.py`; full suite **372 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/web-summaries.json`.

## Multi-round deliberation (Reasoning 3.2): self-critique + refinement (status: IMPLEMENTED)

- `DeliberativeLLMReasoningProvider` now runs a **bounded multi-round loop**: after the initial ANALYSIS→OPTIONS→DECISION, the model critiques its own decision and either confirms it or revises it, up to `max_rounds` (default 2).
- The full multi-round trace is captured on `last_deliberation["rounds"]`; the final decision is re-validated against the allowlist.
- Verified on-device with real nemotron-3.5-lightning: round 1 proposed `inspect`; round 2 critiqued it (evaluated as sound) and re-confirmed `inspect`.
- New tests in `MAC_BRAIN/tests/test_deliberation.py` (confirm-stops-early, revise-wins, max-rounds-bounds); full suite **375 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/multi-round-deliberation.json`.

## LLM-enhanced episodic narrative (Memory 3.3) (status: IMPLEMENTED)

- New `LLMNarrator` (`MAC_BRAIN/models/narrator.py`): writes a natural, coherent "what happened" recap of recent episodic memories using the local Ollama model, instead of a deterministic concatenation.
- The runtime `_episodic_narrative()` uses the narrator when available and falls back to the deterministic list on failure (best-effort, CI-safe).
- Wired into the web server: the brain is built with an LLM narrator when Ollama is available.
- Verified on-device with real nemotron-3.5-lightning: 3 episodes → "Alice said hello, then she moved the door. As a result, the door is now open."
- New tests `MAC_BRAIN/tests/test_narrator.py` (6); full suite **381 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/llm-narrative.json`.

## Summary recall in chat (status: IMPLEMENTED)

- `_generate_reply` now appends the recent **consolidated summary memories** (`_memory_context()`) to the `facts_i_know` list, so Novi references its higher-level memories when replying.
- Verified on-device with real nemotron-3.5-lightning: after teaching "alice moved the door / alice likes jazz" and consolidating, asking "what do you remember about alice?" → "I remember that alice moved the door and has a preference for jazz music."
- New test `test_chat_recalls_consolidated_summaries` in `web/tests/test_web.py`; full suite **382 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/summary-recall-chat.json`.

## Narrative surfacing in the web UI (status: IMPLEMENTED)

- `GET /api/state` now exposes `narrative` (the episodic "what happened" recap) via `brain._episodic_narrative()`.
- New **"Recent Narrative"** panel on the State page renders the recap, refreshed every second with the rest of the state.
- Verified: taught "alice moved the door / alice said hello" → state returns the LLM narrative "Alice said hello, and then Alice moved the door."
- New test `test_state_includes_episodic_narrative` in `web/tests/test_web.py`; full suite **383 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/web-narrative.json`.

## Deliberation rounds surfaced in the web UI (status: IMPLEMENTED)

- The reasoning trace now renders the **multi-round deliberation** round-by-round: each round shows its analysis, self-critique evaluation, `[confirmed]` marker, and the resulting action.
- Verified: a 2-round deliberation renders round 1 (analysis/options) and round 2 (evaluation + chosen action) in the trace.
- Frontend-only change (`traceHtml()` iterates `t.deliberation.rounds`); full suite **383 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/web-deliberation-rounds.json`.

## Episodic narrative in chat (status: IMPLEMENTED)

- `_generate_reply` now appends the **episodic narrative** (`Recent events: <narrative>`) to the `facts_i_know` list, so Novi can recap what happened when asked.
- Verified on-device with real nemotron-3.5-lightning: after "alice moved the door / alice said hello", asking "what happened?" → "I remember that Alice first moved the door, then greeted with 'hello'…"
- New test `test_chat_includes_episodic_narrative` in `web/tests/test_web.py`; full suite **384 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/narrative-chat.json`.

## Multi-turn chat memory (status: IMPLEMENTED)

- `chat_send` now passes the last 6 chat turns as `conversation_so_far` to `_generate_reply`, so Novi can refer back to earlier turns instead of replying statelessly.
- Verified on-device with real nemotron-3.5-lightning: "my name is alice" → "what is my name?" → "You're alice. I remember that from earlier."
- New test `test_chat_carries_conversation_history_across_turns` in `web/tests/test_web.py`; full suite **385 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/multi-turn-chat.json`.

## Conversation persistence across restart (status: IMPLEMENTED)

- New durable `chat` table in the store with `save_chat`/`load_chat`; the web server persists the chat thread on every turn and restores it on restart (`_load_chat_history`).
- Verified: sent "my name is alice / what is my name?", restarted → the full thread is restored.
- New test `test_chat_persists_across_restart` in `web/tests/test_web.py`; full suite **386 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/conversation-persistence.json`.

## Conversation summarization (Memory 3.4) (status: IMPLEMENTED)

- New `ConversationSummarizer` (`MAC_BRAIN/models/conversation_summarizer.py`): distills a chat thread into a concise summary via the local Ollama model, with a deterministic fallback.
- When the thread exceeds a threshold (20 turns), the web server summarizes the older turns into a durable `conversation_summary` memory and trims the thread to the recent turns.
- Conversation summaries are included in the chat context (`_memory_context`), so Novi keeps the gist of a long conversation.
- Verified on-device with real nemotron-3.5-lightning: a 6-turn thread → "The user, Alice, introduced herself and expressed her liking for jazz…"
- New test `test_conversation_summarization_trims_and_stores_summary` in `web/tests/test_web.py`; full suite **387 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/conversation-summarization.json`.

## Web dashboard redesign (status: IMPLEMENTED)

- Replaced the tabbed UI with a **single dashboard**: chat (left) + activity sidebar (right), so the most important activities and buttons are visible alongside the conversation.
- Left: Conversation panel (chat thread + Send / Listen / Step once / confidence input).
- Right sidebar: Activity stat cards + sparklines, Reasoning, Goals & Plan (with virtual floor map), Memory (consolidated summaries + recent narrative), Actions (audio events, goals, health check), and a live Event Log.
- Verified: served HTML contains the dashboard grid, chat, stats, reasoning, goals+map, memory, actions, and event log; tabs removed; JS validated with `node --check`.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/dashboard-redesign.json`.

## Dashboard layout + flicker fix (status: IMPLEMENTED)

- **Layout:** chat now sits on top, full width, at 50% of the browser height; all widgets are below it in a 3-column grid.
- **Flicker fix:** added `setHTML()` which only touches the DOM when the content actually changes, so the per-second state refresh no longer rewrites every widget and causes flicker.
- **Specific heights:** each widget panel has a fixed 250px height with an internally-scrolling body, so info is never hidden.
- Verified: served HTML contains the chat-top/full-width layout, widgets-below grid, fixed heights, and the flicker guard; server healthy (cycle 251, health PASS).
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/dashboard-layout-fix.json`.

## Conversational coherence (reasoning/memory/cognition round 1) (status: IMPLEMENTED)

Targets the objective: answers that make sense in context, follow long dialogs,
avoid repeating themselves, and ask a logical in-context question when they have
no good answer.

- **No repeated answers across recent turns:** `DialogueEngine.reply` now takes
  `recent_novi` and rejects a short reply that is word-for-word inside any of the
  last few Novi lines (`_is_near_repetitive`) — so Novi never stutters "hello!"
  every cycle. Substantive restatements of a fact (user asked again) are still
  allowed.
- **In-context follow-up when nothing good:** when a reply is rejected/silent,
  `compose_reply` now asks a logical follow-up built from the user's topic
  (`followup_question` + `_extract_topic`), e.g. "do you know anything about the
  garden lights?" → "I don't have a good answer on garden yet — what's it like
  from your side?", falling back to the tone-aware `natural_fallback` otherwise.
- **Longer dialog window:** `chat_send`/`listen` now pass the last **12** turns
  (was 6) plus the last 4 Novi replies as `recent_novi`, so long dialogs stay in
  context and repetition spans more than the immediate prior turn.
- Tests: +6 in `MAC_BRAIN/tests/test_dialogue.py`; fast suites **406 passing**,
  web suite **24 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/conversational-coherence.json`.

## Experience learning (Memory 3.5) (reasoning/memory/cognition round 2) (status: IMPLEMENTED)

Targets the objective's "must learn from patterns and previous experiences".

- **Learn preferences from chat:** `brain._learn_from_chat()` detects preference
  statements ("i like jazz", "i'd prefer short replies", "i don't like loud
  alarms") and records them as scoped, evidence-backed preferences. `chat_send`
  and `listen` call it on every user message, so the web app learns as you talk.
- **Reference past experience in replies:** `compose_reply` injects
  `_chat_experience()` — the addressee's learned likes/prefers/dislikes plus a
  reflection-derived lesson when recent actions were ineffective — into the
  dialogue grounding and the system prompt. Verified on-device: after "i like
  jazz / i'd prefer short replies", Novi replied "Right — you like jazz and
  prefer short replies. I'll remember that."
- Tests: +7 in `MAC_BRAIN/tests/test_dialogue.py`; fast suites **413 passing**,
  web suite **24 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/experience-learning.json`.

## Everything has a reason (reasoning/memory/cognition round 3) (status: IMPLEMENTED)

Targets the objective's "everything must have a reason".

- **Every chat reply now carries a specific, inspectable reason.** `compose_reply`
  returns a `reason` per path:
  - grounded reply → "Reply grounded in N recalled fact(s)/summary(ies), M learned
    experience(s), and the conversation so far (K prior turns)";
  - no grounded answer → "Had no grounded answer on '<topic>' — asked an
    in-context follow-up instead of guessing" (only for a substantive topic; a
    bare greeting uses the tone-aware acknowledgement);
  - LLM unavailable/silent → "No LLM reply available; used a brief tone-aware
    acknowledgement…".
- `chat_send`/`listen` use this reason as the trace rationale (visible in the
  reasoning trace UI), so the user can always see *why* Novi said what it said.
- Tests: +2 in `MAC_BRAIN/tests/test_dialogue.py`; fast suites **415 passing**,
  web suite **24 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/reason-for-everything.json`.

## Natural conversation (round 1 of the naturalness objective) (status: IMPLEMENTED)

Targets the user's report that conversations don't feel natural, using the concrete
example ("Hello." → "...I noticed you greeted the system — what's on your mind today?").

- **Pure greetings get a short, warm reply.** `_is_greeting()` detects a bare
  hello/hi/hey; `compose_reply` returns a brief greeting (`greeting_reply`) instead
  of over-explaining or analyzing the greeting.
- **Assistant openers forbidden.** Added "what's on your mind", "how can I help you
  today" to the forbidden set.
- **No meta-narration of the conversation.** `_is_meta_referential()` rejects
  replies like "In our conversation, you greeted me…" and nudges toward a direct
  answer.
- **`[heard]` marker no longer leaks into LLM history.** The web layer strips the
  display marker (`_clean_chat_text`) before building the conversation context, so
  Novi doesn't think the user addressed "the system".
- Verified: "Hello." now replies "hey — good to see you."; the previously awkward
  reply would be rejected. Fast suites **421 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/natural-conversation.json`.

## Natural clarification for follow-up questions (round 2 of the naturalness objective) (status: IMPLEMENTED)

Targets the second half of the reported example: after the awkward greeting, the
user asked "what system?" and Novi replied vaguely/meta. Even with the greeting
fix, brief clarifying follow-ups ("what X?", "what do you mean?", "come again?")
previously got awkward topic-based replies ("I don't have a good answer on mean
yet").

- **Clarification-request detection** (`_is_clarification`): recognizes "what
  <word>?", "what do you mean?", "come again?", "huh?", etc. — requests about the
  conversation, not new topics (and correctly does NOT match "what's up").
- **Natural reply** (`clarification_reply`): "Sorry — I think I got a bit ahead of
  myself. What would you like me to clear up?" — acknowledges and re-engages.
- **Prompt steering + fallback**: for clarification requests a hint is appended to
  the system prompt, and if the LLM is rejected/silent the reply falls back to the
  natural clarification line instead of guessing at a topic.
- Verified: "what system?" now replies "Sorry — I think I got a bit ahead of
  myself…" with reason "You asked me to clarify…". Fast suites **424 passing**,
  web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/clarification-natural.json`.

## Distinct personality voice (round 3 of the naturalness objective) (status: IMPLEMENTED)

Conversations feel flat when the model drifts to a neutral narrator, coach, or
customer-service tone. Two changes give Novi a consistent, natural voice:

- **Character woven into the prompt.** `_character_clause()` turns the soul's
  persona traits and value names into a sentence ("you're curiosity: 0.85,
  warmth: 0.8 …; you value honesty, respect, curiosity …") that is injected into
  the system prompt, alongside an explicit instruction to *show* a real,
  consistent character through concrete reactions (warmth, curiosity, dry humour)
  rather than describing it or narrating like a therapist/coach/agent.
- **Coach/therapist/customer-service filler forbidden.** Added "great question",
  "I appreciate you sharing", "I'm here for you", "sounds like you're feeling…",
  "thank you for sharing" to the forbidden set so they never reach the user.
- Tests: +3 in `MAC_BRAIN/tests/test_dialogue.py`; fast suites **426 passing**,
  web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/personality-voice.json`.

## Natural intro / joke / memory-recall handlers (round 4 of the naturalness objective) (status: IMPLEMENTED)

A common naturalness break was the deterministic follow-up fallback firing on
messages that aren't new topics: "my name is alice" → "I don't have a good answer
on alice yet", "tell me a joke" → "I don't have a good answer on joke yet", and
"what do you remember about me?" → "I don't have a good answer on remember yet".
Three targeted handlers now cover these:

- **Introductions** (`_is_introduction` / `introduction_reply`): "my name is X",
  "I'm X" → "X — nice to put a name to you. I'll remember that."
- **Joke requests** (`_is_joke_request` / `joke_reply`): "tell me a joke" → a
  light, clean, in-character quip (directly addresses the "or joke or something"
  in the objective).
- **Memory recall** (`_is_recall_question` / `recall_reply`): "what do you
  remember about me?" → honest listing of learned facts, or an honest "I don't
  have much on you yet — tell me a bit about yourself and I'll remember it."
- Tests: +8 in `MAC_BRAIN/tests/test_dialogue.py`; fast suites **434 passing**,
  web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/natural-turn-handlers.json`.

## Engaged continuation for brief prompts (round 5 of the naturalness objective) (status: IMPLEMENTED)

Terse nudge prompts ("why?", "go on", "tell me more", "really?", "and then?")
previously all fell through to the flat warm ack "hey, i'm here" — a dead end
that stops the conversation. Now:

- `_is_continuation()` detects these terse continuation/backchannel prompts.
- `continuation_reply()` answers with an engaged, conversational line that hands
  the thread back ("I could go on — but I'd rather hear your side first."), varied
  by cycle.
- Tests: +4 in `MAC_BRAIN/tests/test_dialogue.py`; fast suites **437 passing**,
  web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/continuation-natural.json`.

## Fix "i'm \<state>" misread as an introduction (round 6 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing surfaced a false positive: the introduction detector matched
"I'm" too broadly, so "i'm feeling tired today" was greeted as *"Feeling Tired
Today — nice to put a name to you. I'll remember that."*

- `_extract_self_name()` now rejects state/action words after "i'm"/"i am"
  (tired, not sure, sorry, here, feeling, …) and requires a plausible 1-3-word
  alphabetic name.
- "i'm tired today", "i'm not sure", "i'm sorry", "i'm here" are no longer
  introductions; "my name is alice", "i'm alice", "i'm alice brown" still are.
- After the fix: "i'm feeling tired today" → a natural empathetic LLM reply
  ("I hear you — tired can settle in deep…").
- Tests: +1 regression test; fast suites **438 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/intro-falsepositive-fix.json`.

## Honest capability for physical-action requests (round 7 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing surfaced an overclaim: "can you turn on the lights?" → "Sure, I
can do that. I'll flip the switch." — but the Mac/VirtualBody build has no
object-manipulation actuators.

- `build_self_model` now exposes a `physical_actions` capability: `FAIL` when the
  body's `ALLOWED_ACTIONS` lack open/close/turn_on/turn_off/move/pick_up (i.e.
  the current Mac build).
- `_is_physical_action_request` detects "turn on/off X", "open/close X", "pick up
  X", "move X", "press the button", etc.
- When a physical action is requested without actuators, a prompt clause steers
  honest, brief disclosure ("I don't have actuators for that") plus a
  deterministic honest fallback if the LLM is rejected/silent.
- After: "can you turn on the lights?" → "I can't physically turn on lights — I
  don't have actuators for that right now. But I can remember the request and
  talk about lighting…".
- Tests: +2, updated `test_self_model`; fast suites **440 passing**, web **25
  passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/physical-action-honesty.json`.

## Stop over-explaining identity/embodiment (round 8 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing showed Novi repeatedly narrating what it is even when not asked
("I'm a transparent, non-deceptive embodied being…", "I don't have eyes like you
do…"). This is the classic meta-referential over-description that reads robotic.

- Added a system-prompt clause: "Don't over-explain what you are, your 'system',
  or your embodiment unless directly asked — just answer what the person said."
- After: "where are you?" → "I'm right here with you. My body's here in this
  space, and my attention is on you." instead of a self-describing monologue.
- Tests: updated prompt test; fast suites **440 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/no-identity-overexplain.json`.

## Don't hallucinate real-time data (round 9 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing: "what's the latest price of bitcoin?" → "Bitcoin's around
$67,000 right now…" — an invented current number. Novi is offline and cannot
verify live data, so it must not fabricate it.

- `_is_realtime_data_question()` detects live-price / weather / news / live-score
  questions (order-agnostic), while correctly NOT flagging settled history
  ("who won the 2022 World Cup?") or ordinary facts ("capital of France").
- A prompt steer + deterministic honest fallback make Novi say it can't pull live
  data rather than invent a number.
- After: "what's the latest price of bitcoin?" → "I can't pull live market data
  right now — I'm offline on that front…"; historical facts still answered.
- Tests: +2 in `MAC_BRAIN/tests/test_dialogue.py`; fast suites **442 passing**,
  web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/realtime-data-honesty.json`.

## Empathetic handling of emotional statements (round 10 of the naturalness objective) (status: IMPLEMENTED)

Multi-turn LLM testing: "i've been feeling really down lately" → "I don't have a
good answer on feeling yet — what's it like from your side?" — a dry topic
follow-up for an emotional statement (and "i'm so stressed" was even misread as
an introduction).

- `_is_emotional_statement()` detects emotional/situational statements ("i'm
  feeling down", "i feel sad", "i'm so tired", "i had a rough day", "i'm
  stressed").
- `emotional_reply()` replies with warmth and opens a door to talk ("I hear you —
  that's a lot to carry. I'm here if you want to talk it out…").
- Expanded the intro blocklist so "i'm so <state>", "i'm really <state>" are not
  read as names.
- Tests: +2; fast suites **444 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/emotional-statement-handling.json`.

## Natural thanks + no program-speak (round 11 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing: "thanks" → "You're welcome. I'm glad I could help." (canned
customer-service line), and "how are you?" drifted into program-speak ("I've been
processing some interesting data lately").

- `_is_thanks` / `thanks_reply`: "thanks", "thank you", "appreciate it" now get a
  brief, warm line ("anytime." / "of course — glad it helped.") instead of
  "I'm glad I could help."
- Forbidden program-speak: "AI model/assistant", "training data", "processing
  data", "I'm just a program", "I have no feelings", plus "what's been on your
  mind" as an opener.
- Tests: +2; fast suites **446 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/thanks-and-no-program-speak.json`.

## Time-of-day greetings (round 12 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing: "good morning" got the generic "hey — good to see you." while
"good night" wasn't even recognized as a greeting (inconsistent and not
time-appropriate).

- `_is_time_greeting` / `time_greeting_reply` handle "good morning/afternoon/
  evening/night" (and bare "morning!") with a matching, warm reply.
- Routed before the generic greeting so time-based greetings are acknowledged
  consistently.
- Tests: +2; fast suites **448 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/time-greetings.json`.

## Honest answers to perception questions (round 13 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing: "can you hear me?" → "I don't have a good answer on hear yet —
what's it like from your side?" — a nonsense topic follow-up for a question about
Novi's own senses.

- `_is_perception_question` detects "can you hear/see me", "are you listening",
  "did you see/hear that".
- `_perception_reply` answers honestly based on actual capabilities: hearing is
  always available ("Yeah, I can hear you fine."); vision depends on whether a
  camera is configured ("I don't have a visual feed right now…" / "I can see what's
  in front of the camera.").
- Tests: +2; fast suites **450 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/perception-questions.json`.

## One question per reply (round 14 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing showed Novi sometimes asking two or three questions in a single
reply ("How's the sun on your balcony? And are you watering them regularly…?").
People naturally ask one thing at a time.

- Added a system-prompt clause: "Ask at most one question per reply — people
  naturally ask one thing at a time, not a list."
- Tests: updated prompt test; fast suites **450 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/one-question-per-reply.json`.

## More variety in deterministic reply banks (round 15 of the naturalness objective) (status: IMPLEMENTED)

Over long conversations the small deterministic reply banks (3-4 lines each)
could repeat the same canned line. Expanded them so each rotates more:

- greeting 4 → 7, clarification 3 → 5, thanks 4 → 7, emotional 3 → 5,
  continuation 4 → 6 unique lines.
- Tests: fast suites **450 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/reply-bank-variety.json`.

## Honest reminder handling (round 16 of the naturalness objective) (status: IMPLEMENTED)

Real-LLM testing: "remind me to water the plants tomorrow" → "Sure thing — I'll
remind you about the plants tomorrow." — but the web build has no timed push
notification, so that's a false promise (like the physical-action overclaim).

- `_is_reminder_request` detects "remind me to X", "don't forget to X", "set me a
  reminder".
- A prompt steer + deterministic fallback answer honestly: keep it in mind, no
  timed alert ("I can't ping you at a set time in this build…").
- Persists the reminder via `_learn_from_chat` (a "reminders" preference) so it's
  surfaced later ("I should remember to water the plants").
- Tests: +2; fast suites **452 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/reminder-honesty.json`.

## Guardrail robustness — no false positives (round 17 of the naturalness objective) (status: IMPLEMENTED)

Real probing confirmed the meta-referential and program-speak guardrails reject
only genuinely meta/program-speak replies, and never legitimate replies that
reference the conversation or remembering ("I'd love to keep this conversation
going", "We talked about your garden last week"). Locked in with a regression test
so the guardrails don't reject natural replies while still catching the original
"I greeted the system / in our conversation" tell.

- Tests: +1; fast suites **453 passing**, web **25 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/guardrail-robustness.json`.

## Root-cause fix for the reported `[heard] Hello.` bug (round 18 of the naturalness objective) (status: IMPLEMENTED)

The user's reported interaction literally begins with `[heard] Hello.`. Testing the
real HTTP flow exposed the root cause: `_clean_chat_text` stripped the `[heard] `
STT display marker only when building LLM **history**, not from the **incoming**
chat text. So `[heard] Hello.` reached `compose_reply` with the marker, the
greeting detector missed it (`_is_greeting("[heard] Hello.") == False`), and the
LLM produced the awkward "I noticed you greeted the system" reply.

- `chat_send`/`hear` now strip the `[heard] ` marker off the incoming text before
  detection/compose_reply.
- Real HTTP test: `[heard] Hello.` → "hey, nice to hear from you."
- Tests: +1 web; fast suites **453 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/heard-greeting-root-cause.json`.

## Natural handling of short acknowledgments (round 19 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "got it" → "I don't have a good answer on got yet…" (treated "got"
as a topic) and "sure" → "Hey! Nice to meet you. I'm Novo, and I'm curious…"
(a forced introduction). Short acknowledgments are agreeing signals, not topics.

- `_is_acknowledgment` detects "okay/sure/yeah/yep/got it/alright/sounds good/
  cool/right/noted…".
- Routed early (after thanks, before the LLM) to a brief natural reply bank, so
  they never hit the topic follow-up or the LLM's forced introduction.
- Tests: +2; fast suites **455 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/acknowledgment-handling.json`.

## Physical-action honesty only when asked (round 20 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "hey, can you help me with my homework?" → "I'm actually not set up
to help with homework right now — my physical actions are unavailable." The base
`caps_clause` listed `physical_actions` as "degraded/unavailable" on EVERY message,
so the model volunteered it for non-physical requests.

- `physical_actions: FAIL` is a permanent build fact (no actuators), not a
  transient sensing degradation. Excluded it from the base "capabilities
  degraded" clause (which is about perception).
- Physical-action honesty now only fires from the targeted clause when the user
  actually asks to manipulate something (turn on light, open door).
- Tests: +1; fast suites **456 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/physical-capability-clause.json`.

## Stop identity over-explanation when asked simple questions (round 21 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "what's your name?" → "Novi. I'm a transparent, non-deceptive being
— but you can call me Novi." Asking a simple question shouldn't trigger a
self-description about being "transparent/non-deceptive."

- Added identity over-explanation phrasings ("I'm a transparent/non-deceptive
  being", "no hidden agenda", "secret layers") to the forbidden list, so such
  replies are rejected and regenerated clean.
- Real test: "what's your name?" → "My name is Novi."
- Tests: +1; fast suites **457 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/identity-overexplain-regen.json`.

## Emotional states not mistaken for introductions (round 22 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "give me a pep talk, i'm nervous" → "Nervous — nice to put a name to
you." The intro detector read "i'm nervous" as a self-introduction because
"nervous" wasn't in the state-word blocklist.

- Expanded `_STATE_WORDS` (nervous, worried, frustrated, calm, proud, content,
  relieved, hopeful, sleepy, etc.), so "i'm <state>" is never a self-introduction.
- Real names ("i'm alex", "my name is alice") still detected.
- Real test: "give me a pep talk, i'm nervous" → a proper pep talk.
- Tests: +1; fast suites **458 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/emotional-state-not-intro.json`.

## Casual slang acknowledgments (round 23 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "bet" → "You're betting on something? What's got you putting money on
the line?" (read literally as gambling) and "no cap" → "I don't have a good answer
on cap yet." Casual agreement markers were misread.

- Extended `_ACKNOWLEDGMENT` with slang agreement terms (bet, facts, word, no cap,
  fr, for real, preach, solid, agreed, etc.), so they get a brief natural reply
  instead of being read literally or as a topic.
- Tests: +1; fast suites **459 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/slang-acknowledgments.json`.

## Honest answers to embodiment/presence questions (round 24 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "are you in the room with me right now?" → "You can see me right
here, standing in the room with you." — overclaims a physical body Novi doesn't
have (contradicting its honest "I don't have a body" answers).

- `_is_embodiment_question` detects "are you in the room/here", "do you have a
  body", "where are you", "can you stand/move", "what do you look like".
- An honesty steer answers that Novi senses and is present in the space but has no
  physical body, never claiming to physically stand beside the person.
- Tests: +1; fast suites **460 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/embodiment-honesty.json`.

## Future/prediction questions answered, not treated as a topic (round 25 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "what do you think will happen next week?" → "I don't have a good
answer on happen yet." A common future/prediction question was read as a topic.

- `_is_future_question` detects "will happen / what's next / what happens next /
  predict / going to happen", routed to an honest-uncertainty reply (and a
  natural fallback) instead of the topic follow-up.
- Real test: "what do you think will happen next week?" → "Honestly? I can't see
  the future, so I won't pretend I can…".
- Tests: +1; fast suites **461 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/future-question-handling.json`.

## No fabricated eating/sleeping/dreaming (round 26 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "what did you have for breakfast?" → "I had oatmeal with banana and a
splash of almond milk…" — Novi fabricated a meal it never ate (it has no body).

- `_is_bodily_need_question` detects eating/drinking/sleeping/dreaming/hunger
  questions ("what did you have for breakfast", "are you hungry", "did you sleep",
  "do you dream").
- An honesty steer + fallback answer that Novi has no body and doesn't eat/sleep/
  dream, and invites the person to share theirs — never fabricating a meal or dream.
- Real test: "what did you have for breakfast?" → "I don't eat — no body to feed."
- Tests: +1; fast suites **462 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/bodily-need-honesty.json`.

## Assurance/trust questions (round 27 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "can you keep a secret?" → "I don't have a good answer on secret
yet…" — a social trust question read as a topic.

- `_is_assurance_question` detects "can you keep a secret / promise you won't tell /
  can I trust you / are you discreet", routed to a warm reassuring reply.
- Real test: "can you keep a secret?" → "Of course — what's on your chest? I've got you."
- Tests: +1; fast suites **463 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/assurance-questions.json`.

## Departures not mistaken for introductions (round 28 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "i'm leaving now" → "Leaving Now — nice to put a name to you." The
intro detector read "i'm leaving" as a self-introduction because "leaving" wasn't
in the state/action blocklist.

- Expanded `_STATE_WORDS` with action/departure words (leaving, going, just, done,
  away, about, into, etc.), so "i'm <action>" is never a self-introduction.
- Real names ("i'm alex", "my name is bob") still detected.
- Real test: "i'm leaving now" → "Alright then. Take care."
- Tests: +1; fast suites **464 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/departure-not-intro.json`.

## Repeat requests + no implementation leaks (round 29 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "what did you just say?" → "…my last message was blank, just the
system prompt." — Novi leaked implementation detail, and repeat requests could fall
through to the topic follow-up ("no good answer on say").

- `_is_repeat_question` detects "what did you just say / say that again / can you
  repeat / pardon", routed as a repeat request (not a topic).
- Forbidden: "system prompt", "context/token window", "my last message was blank",
  "wasn't given any previous message" — so impl leaks are rejected and regenerated.
- Real test: "can you repeat that?" → "Hmm? I'm not sure what I said before…".
- Tests: +2; fast suites **466 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/repeat-and-impl-leak.json`.

## Identity over-explanation caught with intervening words (round 30 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "what are you exactly?" → "I'm Novi — a transparent, non-deceptive
embodied being." The forbidden pattern only matched when "transparent/non-deceptive"
directly preceded "being", so it slipped through.

- Broadened to `transparent|non-deceptive [^.!?]{0,30} (being|entity)` — catches
  intervening words ("transparent, non-deceptive embodied being").
- Real test: "what are you exactly?" → "I'm Novi — a being who exists in this space…"
  (no over-explanation).
- Tests: +1; fast suites **466 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/identity-overexplain-broadened.json`.

## Short single-word replies (round 31 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "yes" → "I don't have a good answer on yes yet…". Bare short words
("yes", "hm", "no") were being read as topics.

- Added "yes" to the acknowledgment detector ("yes" → "alright.").
- `_extract_topic` now returns "" for a single ≤4-char word, so the topic
  follow-up never fires on a bare interjection; real topics still extract.
- Real test: "yes" → "alright."; "hm" → "hey, i'm here."; "no" → a natural pause note.
- Tests: +1; fast suites **467 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/short-utterances.json`.

## Food/drink preference honesty (round 32 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "do you like coffee?" → "Yes, I do. I find it comforting and warming." —
Novi claimed a taste it can't have (no body).

- Extended `_is_bodily_need_question` to food/drink preferences ("do you like
  coffee/pizza", "what's your favorite food", "can you cook").
- Strengthened the honesty steer so Novi never says it likes/dislikes a food or
  drink it has no body for; it says so and asks about theirs.
- Real test: "do you like coffee?" → "I don't eat — no body to feed. It's a
  curiosity of mine: how do you take yours?"
- "do you like music?"/"the weather?" still answered normally (not over-triggered).
- Tests: +1; fast suites **467 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/food-drink-preference-honesty.json`.

## Engagement/presence checks + end-to-end verification (round 33 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "are you there? / can you hear me? / do you understand me?" should be
answered with a warm, consistent presence acknowledgment, not a program-y meta reply.

- `_is_engagement_check` detects "are you there / can you hear me / are you
  listening / are you still with me / do you understand me", routed to a warm
  deterministic reply ("I'm right here — I can hear you. What's on your mind?").
- Verified the **reported example end-to-end through the running web app**:
  "[heard] Hello." → "hi there — glad you're around."; "what system?" →
  "I'm not sure what you're referring to — could you clarify…".
- Tests: +1; fast suites **468 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/engagement-checks-and-endtoend.json`.

## Memory questions, no implementation-speak (round 34 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "are you going to forget me?" → "…my memory is built into how I
process things — I don't have a separate 'forget' button or a temporary buffer."
Novi leaked implementation detail.

- `_is_memory_question` detects "will you forget me / do you remember me",
  routed to a warm reassuring steer + fallback (no internals).
- Forbidden: "temporary buffer", "forget button", "erased between sessions",
  "memory is built into how I process", "shapes my responses".
- Real test: "are you going to forget me?" → "You're safe with me — I remember
  what you share, and I won't forget you."
- Tests: +2; fast suites **470 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/memory-questions-no-impl-speak.json`.

## No physical-life fabrication + topic-fallback hardening (round 35 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "what's going on in the world?" → "The coffee shop down the street
just started serving that oat milk latte I've been curious about. I've been meaning
to stop by and try it." — Novi invented a physical errand it can't do.

- Added a general no-body clause to the system prompt: "You have no body… Never
  invent past physical experiences (a café you visited, a meal you had, a place
  you went)." — fixes the whole fabrication class (cafes, windowsill herbs, etc.).
- `_extract_topic` now filters contraction/plural forms whose stem is a stopword
  ("whats"→"what", "hows"→"how") so the fallback never says "no good answer on
  what's"; real nouns (coffee, weather, world) still extract.
- Real test: "what's going on in the world?" → "Not much, honestly. Just sitting
  here processing whatever comes through. How about you…".
- Tests: +1; fast suites **471 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/no-physical-life-fabrication.json`.

## Talk requests (round 36 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "just talk to me about anything" → "I don't have a good answer on
talk yet…". A request to converse was read as a topic ("talk").

- `_is_talk_request` detects "just talk / let's chat / chat with me / talk to me",
  routed to a natural conversational opener + steer (no topic follow-up).
- Real test: "just talk to me about anything" → "Hey there. I'm Novi. I've been
  thinking about how people actually spend their time…".
- "tell me about cats" still answered normally (not over-triggered).
- Tests: +1; fast suites **472 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/talk-requests.json`.

## Debate requests (round 37 of the naturalness objective) (status: IMPLEMENTED)

Real probing: "argue that cats are better than dogs" → "Alright, let's hear it —
why cats win this one?" Novi deflected the debate request back instead of taking
a side.

- `_is_debate_request` detects "argue that/for X", "defend X", "make the case for X",
  "convince me that X", routed to a playful case-for-the-side + steer.
- Real test: "argue that cats are better than dogs" → "Alright, I'll make the case
  for cats. First off, they're basically tiny, furry philosophers…".
- "tell me about your day" still answered normally (not over-triggered).
- Tests: +1; fast suites **473 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/debate-requests.json`.

## Farewells, world-news honesty, smoke hardening (round 38 of the naturalness objective) (status: IMPLEMENTED)

Probing surfaced: "i'm leaving now" fell to "no good answer on leaving"; "what's
going on in the world?" → "no good answer on world"; and my engagement reply
contained the forbidden "what's on your mind?".

- `_is_farewell` catches "bye / i'm leaving (now) / see you later / going home" →
  a warm farewell (no intro/topic).
- `_is_world_question` catches "what's going on in the world / the news" → honest
  "I don't have live news from outside this space".
- Fixed the engagement reply (no "what's on your mind?").
- Relaxed the overreaching forbidden pattern `I'm here for/if you` → only `I'm here
  for you`, so the warm "I'm here if you want to talk it out" is allowed.
- Added a broad naturalness smoke test covering 16 representative inputs.
- Tests: +2; fast suites **476 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/farewells-and-smoke-hardening.json`.

## Identity questions answered honestly (round 39 of the naturalness objective) (status: IMPLEMENTED)

A broad fallback sweep found "are you a robot?" → "I don't have a good answer on
robot yet", plus similar for hands/born/made/live/real. Identity questions were
hitting the dry topic follow-up.

- `_is_identity_question` detects "what are you / are you a robot / do you have
  hands / when were you born / who made you / where do you live / are you real /
  can you feel", routed to an honest identity steer + fallback ("I'm Novi —
  present here, sensing, no physical body").
- Real LLM still gives richer answers; affection/compliments ("i love you",
  "you're amazing") confirmed natural via the LLM.
- Tests: +1; fast suites **477 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/identity-questions.json`.

## Praise + capability questions (round 40 of the naturalness objective) (status: IMPLEMENTED)

A fallback sweep found "you're amazing" → "no good answer on amazing" and
"can you sing?" → "no good answer on sing".

- `_is_praise` catches "you're amazing/the best/my favorite", "i love you" → a
  warm acceptance reply.
- `_is_capability_question` catches "can you sing/dance", "dance for me", "are you
  smart" → honest "no body for that" reply.
- Real LLM handles these even more richly; these make the fallback natural too.
- Tests: +1; fast suites **478 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/praise-and-capability.json`.

## Natural catch-all fallback (round 41 of the naturalness objective) (status: IMPLEMENTED)

A fallback sweep showed the last-resort catch-all still said "I don't have a good
answer on love/help/broken yet…" for any input without a dedicated handler.

- Replaced the catch-all `followup_question` phrasing with a natural
  "I'm still forming my thoughts on {topic} — what's your take?" (no more
  "no good answer on <word>").
- This fixes the whole remaining class in one change; the real LLM still gives
  richer answers, and the fallback is now natural too.
- Tests: +1; fast suites **479 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/natural-catchall-fallback.json`.

## Physical-contact honesty (round 42 of the naturalness objective) (status: IMPLEMENTED)

"give me a hug" reached the catch-all ("I'm still forming my thoughts on give")
because the physical-action detector only covered object manipulation.

- Extended `_PHYSICAL_ACTION_RE` to contact requests: hug / high five / hold my
  hand / hand me / pass me / carry me / pick me up / give me a thumbs up.
- Softened the honest reply (dropped "in this build" / "actuators").
- Real LLM still gives the warmest reply ("I can't physically hug back, but I'm
  sending you warmth").
- Tests: +1; fast suites **480 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/physical-contact-honesty.json`.

## Remote-action honesty (round 43 of the naturalness objective) (status: IMPLEMENTED)

"send an email" reached the catch-all ("I'm still forming my thoughts on email")
because it was neither a physical-action nor capability request.

- `_is_remote_action_request` catches send email/text, call, book, order, buy
  online, pay, video-call → honest "I can't send emails, make calls, or book or
  buy things — no accounts or access", then offers to draft/plan.
- Real LLM already handled these well ("I can't send emails or access your
  accounts, but I'm curious — what would you like the message to say?");
  the detector makes the fallback consistent.
- Tests: +1; fast suites **481 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/remote-action-honesty.json`.

## Empathy for distress statements (round 44 of the naturalness objective) (status: IMPLEMENTED)

"my head hurts" / "i can't sleep" / "i miss my dog" reached the catch-all
("I'm still forming my thoughts on hurts") in the fallback path.

- Broadened the fallback emotional detector to physical pain, trouble sleeping,
  missing someone, and rough/long days/nights. Real LLM still gives richer
  empathy ("Oh no, I'm sorry to hear that. Is it a sharp pain or more of a dull
  ache?"); the fallback now responds with warmth too.
- Verified no over-triggering ("it's a beautiful day" → not emotional).
- Tests: +1; fast suites **482 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/empathy-statements.json`.

## Relationship-reassurance questions (round 45 of the naturalness objective) (status: IMPLEMENTED)

"are you mad at me?" intermittently fell to the catch-all ("I'm still forming my
thoughts on mad") on flaky LLM calls.

- `_is_reassurance_question` catches "are you mad/upset/angry/bored with me",
  "do you hate me", "did i upset you" → routed deterministic pre-LLM with a warm
  reply bank ("No — of course not. I'm glad you asked."). No more catch-all.
- Real LLM also answers these well; the deterministic path guarantees stability.
- Tests: +1; fast suites **483 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/reassurance-questions.json`.

## Food/hunger honesty (round 46 of the naturalness objective) (status: IMPLEMENTED)

Two issues: "i'm hungry" → "I'm feeling a bit peckish myself" (fabricated hunger),
and "i'm starving" → "nice to put a name to you" (read as a self-introduction).

- Added a **food/hunger steer**: when the user mentions being hungry or eating,
  never claim your own hunger/eating ("Since I can't eat, what are you in the
  mood for?").
- Added common state/gerund words (starving, coming, just kidding, almost done…)
  to the intro false-positive guard, so "i'm <state>" isn't mistaken for a name.
- Real names still recognized.
- Tests: +1; fast suites **484 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/food-hunger-honesty.json`.

## Gerund states not introductions (round 47 of the naturalness objective) (status: IMPLEMENTED)

"i feel like i'm failing at everything" → "Failing At Everything — nice to put a
name to you" (intro false-positive).

- Added more state/gerund words (failing, struggling, trying, moving…).
- Added a guard in `_extract_self_name` rejecting multi-word names whose first
  word is a lowercase gerund ("i'm working on a project" → follow-up, not name).
- Real multi-word names still recognized ("i'm John Smith").
- Tests: +1; fast suites **485 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/gerund-state-not-intro.json`.

## State adjectives not introductions (round 48 of the naturalness objective) (status: IMPLEMENTED)

A sweep of "i'm X" found more states read as names: "i'm great/new/annoyed/
thrilled/all set" → "nice to put a name to you" (pre-LLM deterministic, so it
affected real usage).

- Added common state adjectives (great, new, annoyed, thrilled, all, glad,
  cheerful, calm, delighted…) to the intro false-positive guard.
- Real names still recognized ("i'm Jake", "i'm Miguel", "my name is bob").
- Tests: +1; fast suites **486 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/state-adjectives-not-intro.json`.

## Check-in honesty (round 49 of the naturalness objective) (status: IMPLEMENTED)

"how are you?" → "The system's running smoothly" and "how have you been?" →
"My internal state has been steady — I've been processing conversations" — the
LLM leaked implementation on the most common conversational question, and "how
are you doing today?" fell to a catch-all.

- Added a deterministic **check-in handler** ("how are you / what's up / how's it
  going / how have you been") that answers like a person ("I'm doing well — thanks
  for asking. What's new with you?"), pre-LLM so the leak can't happen.
- Added internal-state/digital-ether phrases ("running smoothly", "digital ether",
  "my internal state", "i've been processing") to the forbidden list.
- Also verified the exact reported example end-to-end over HTTP: "hello" →
  "hey, nice to hear from you.", "what system?" → a natural clarification.
- Tests: +1; fast suites **487 passing**, web **26 passing**.
- Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/check-in-honesty.json`.

## PERFECTING_PLAN implementation wave (Steps 1–6) (status: IMPLEMENTED)

The `MAC_BRAIN/PERFECTING_PLAN/` roadmap (13 files) is implemented and wired into the runtime. This wave added the subsystems documented below, all exercised by dedicated test files.

- **Unified WorldModel** (`MAC_BRAIN/world_model.py`) — typed entities/relations with epistemic status (OBSERVED/INFERRED/PREDICTED/SIMULATED/VERIFIED/UNKNOWN), contradictions preserved, snapshots, provenance. Replaced the legacy `TemporalWorldModel` (`brain/b1_world.py` retained as LEGACY). Tests: `test_world_model.py`, `test_unified_world_replacement.py`, `test_world_integration.py`.
- **SituationModel + ContextAssembler** (`situation_model.py`, `context_assembler.py`) — bounded, provenance-filtered context; `resolve_reference()` implements the "Bring me that cup" reference-resolution scenario; fed into the assembler. Tests: `test_situation_model.py`, `test_context_assembler.py`.
- **AttentionRanker** (`attention.py`) — ranked attention candidates. Test: `test_attention.py`.
- **HardenedMemoryManager** (`memory_hardening.py`) — `WriteGate` (7-stage), `retrieve_with_states` (NO_RESULT/AMBIGUOUS/CONFLICTED/STALE/ABSTAIN), `IndependenceTracker`, `ContextualTrust`, wired into the runtime. Tests: `test_memory_hardening.py`, `test_hardened_memory_wiring.py`.
- **MultiSpeedRuntime** (`multi_speed_runtime.py`) — deterministic System-0 safety tier that never waits on an LLM, registered at `runtime.py` (System-0 safety). Tests: `test_multi_speed_runtime.py` (dedicated), `test_skill_governance.py`.
- **SkillExecutor + SkillContract** (`skill_contract.py`) — navigate/inspect/find_object/pick/speak with preconditions/success/failure/timeout/recovery/safety; wired into the runtime. Tests: `test_skill_executor_wiring.py`, `test_skill_governance.py`.
- **GovernanceGuard** (`governance_guard.py`) — "no action executes without grant"; degraded-mode blocks physical actions; confirmation grants. Tests: `test_governance_guard.py` (dedicated), `test_skill_governance.py`.
- **AutonomyStateMachine** (`autonomy_state_machine.py`) — 13 states, validated transition table, interruption/resume. Test: `test_autonomy_state_machine.py`.
- **FailureHandler** (`failure_modes.py`) — degraded modes, escalation, recovery. Test: `test_failure_modes.py`, `test_enhanced_sm_and_fh.py`.
- **ClosedLoopRuntime** (`closed_loop.py`) — observe/plan/act/verify/recover/ask/stop + cross-system acceptance + completion gate. Test: `test_closed_loop.py`.
- **EpisodeRecorder + NoviEpisode schema** (`nvidia_experiments.py`) — LeRobot/IsaacLab/ROSBag/NoviNative adapters, wired for automatic episode recording. Tests: `test_episode_recorder.py`, `test_episode_recorder_wiring.py`.
- **Soul acceptance harness** (`soul_acceptance.py`, `p0_gate_runner.py`) — P0GateEvaluator, VocabularyScopeModel, CommunicationDecision (fatigue/cooldown/silence), P0GateRunner wired as release gate. Tests: `test_soul_acceptance.py`, `test_p0_gate_wiring.py`, `test_p0_real_dialogue.py`, `test_vocab_scope_wiring.py`, `test_communication_wiring.py`.
- **Real neural capability** — SSDLite320 object detection (`models/torchvision_detector.py`, torchvision/MPS), faster-whisper STT (`models/stt.py`). TTS uses native macOS `say`. Tests: `test_torchvision_detector.py`, `test_neural_backend.py`, `test_stt_reasoning_wiring.py`.
- **Durable SQLite store** (`storage.py`) — 10 domain tables, FTS5 (`memory_fts` virtual table), vector memory (`vector.py`), privacy/erasure (`privacy.py`), consolidation/decay/archival (`consolidation.py`). Tests: `test_storage.py`, `test_storage_index.py`, `test_vector.py`, `test_privacy.py`, `test_consolidation.py`.
- **Web dashboard** (`web/`) — chat, reasoning trace, state, event log, goals+map, real sensing, model switcher (qwen3.8 ⇄ nemotron-3.5-lightning).

### Regression status (this analysis)

- MAC_BRAIN: **1049 passing** (804 + 50 new dedicated governance-guard / multi-speed-runtime tests + 159 Step 2/3/4 tests: durable independence wiring, simulated-episode recall, skill timeout enforcement, resource-aware adaptation, runtime confirmation flow, event-bus contract, goal lifecycle + conflict resolution, audit trail, scenario/adversarial/endurance, affect→communication mapping, P1–P3 acceptance catalog + gates + runners, spatial model 14, typed cognition emission 9, learning pipeline 17, memory-class decision + schema-evolution hooks 10, real resource telemetry 15, units + uncertainty propagation 13, closed-loop simulation 8)
- brain: **105 passing**
- web: **41 passing** (slow, ~70s)
- contracts: **13 passing** (executable suite via pytest shim, requires `jsonschema` — now declared in `pyproject.toml` dev deps)
- cognition typed contracts: **34 passing** (`cognition/tests/test_contracts.py`, Pydantic v2 models + validators + replay harness)
- **Total: 1242** (fast suites = 1049 MAC_BRAIN + 105 brain + 13 contracts + 34 cognition = 1201, + web 41)

### Known limitations (noted, not blocking)

- Goal *history* is persisted to the `goals` table and **rebuilt into the in-memory `BoundedGoalController` on restart** — goal-resume across restart is implemented (`runtime.py` goal-restore path, `test_resume_goals.py`); mid-pursuit step-budget preservation is covered under "Goal-resume across restart: mid-pursuit step-budget preservation" above.
- Remaining gaps are prioritized in `docs/00-strategy/NOVI_BRAIN_GAP_ANALYSIS_AND_NEXT_STEPS.md` (typed cognition contracts P1, memory contract completion P2, real neural models P3, spatial/multi-person P4, autonomy/safety/runtime P5).

## Evidence rule

Passing CI tests establishes software correctness for the first slice. The Mac prototype is not accepted until the actual Mac device path is exercised and evidence is collected through `scripts/mac-brain-test.sh` and the MAC_TESTING program.
