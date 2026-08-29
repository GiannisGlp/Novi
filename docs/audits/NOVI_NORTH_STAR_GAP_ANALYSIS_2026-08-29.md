# Novi — North Star Gap Analysis & Brain Improvement Roadmap

**Date:** 2026-08-29
**Scope:** full repository (`novi/brain/`, `novi/perception/`, `novi/contracts/`, `novi/web/`, docs)
**Purpose:** A single, current, evidence-based answer to *"what do we need, what did we miss, and how do we improve the brain to reach the north star?"* — reconciling the five north-star capability pillars against the actual implementation, and giving a prioritized roadmap.
**Method:** five parallel evidence-based pillar audits (continuity/agency, perception/world-model, memory/learning, reasoning/cognition, safety/governance) cross-checked against the code, tests, and the 2026-08-29 gap-remediation plan. Every claim below is tied to a file/class/function.

**Baseline (verified):** unified `novi/brain/` package (~80 modules), 212 test files, ~1,780 web+brain tests passing, `ruff` clean on `novi/brain`, single canonical DB (`novi/data/novi.db`), stdlib-first core with optional local LLM (Ollama). Most recent commit (2026-08-29) fixed the LLM pipeline: step 5.3s→0.125s, chat 44–60s→~13s.

---

## 1. The single most important finding

**The brain has strong, well-tested *components* but the north-star *loop* is not closed.** The five pillars each contain mature, tested machinery (epistemic world model, durable memory, deliberation, governance, autonomy supervisor). But the highest-value artifacts are frequently **not wired into the production engine** — they exist as tested islands. The north star is defined by the *integrated loop* (perceive → evidence → world model → memory → attention → goals → reason → plan → govern → act → observe → learn → continue), and that loop has several broken or bypassed links.

The recurring pattern across all five audits:

| Pillar | Strong component | Wiring gap |
|---|---|---|
| Perception | `novi/perception/` (264 tests) | **Not consumed by the brain engine at all** — camera/tracking/grounding never reaches the world model in the live system |
| Safety | `AutonomySupervisor` (A-ARCH-01: 10k ticks, zero unauthorized) | **Not the production action path** — engine uses `governance_guard → body.execute()` only; `SafetyPolicy`/`RuntimeSafetyMonitor` not wired |
| Reasoning | `ReasoningRouter` + LLM deliberation providers | **CLI-only** — engine defaults to deterministic `DeliberativeReasoningProvider` |
| Memory | Durable store, consolidation, sleep cycle | Retrieval ranks by **vector similarity alone** on primary paths; learning subsystems are **in-memory only** |
| Continuity | Goal persistence (`_load_goals`), identity persistence | Goal/self-model not first-class world-model citizens; no action→consequence model |

---

## 2. Where Novi actually stands (per pillar, evidence-based)

### 2.1 Continuity & Agency — **strong, mostly wired**
- **Persistent identity & goals across restart:** `_persist_goal`/`_load_goals` (`engine.py:1300,1320`) resume bounded goals across restart; `_persist_identity` (`engine.py:1773`) WAL-persists person bindings. `_persist_decision_memory`/`_recall_prior_decisions` (`engine.py:2228,2262`) persist deliberation rationale.
- **Bounded agency:** `BoundedGoalController` (`autonomy.py:112`) — goals are bounded (max_steps), resumable, arbitrated (`GoalArbitration`, safety goals dominate A-GOAL-01). `Planner` (`planner.py:242`) with plan/start/advance/fail/cancel/replan + `PlanValidator`.
- **Curiosity/initiative:** `_spawn_curiosity_goals` (`engine.py:1360`) creates bounded investigate goals for novel entities; `_spawn_surprise_goal` (`engine.py:1382`) drives investigation on sequence violations. `SleepCycle` (`sleep_cycle.py`) scheduled at `sleep_every_n_cycles=500` (`engine.py:1183`).
- **Gaps:** self-model (`self_model.py`) is read-only dialogue honesty, not a `ROBOT` world-model entity the planner queries; no action→consequence model; `replan` rebuilds the same template plan (`planner.py:298`).

### 2.2 Perception & World Model — **strong core, broken integration**
- **World model core is excellent:** `WorldModel` (`world_model.py`) with 10 epistemic statuses, hypothetical-never-overwrites-real guards, contradiction preservation, per-field TTL/freshness, provenance. Tests: `test_world_model.py`, `test_world_state_grounding.py`.
- **Active perception excellent:** `active_perception.py` (bounded search, never hallucinates success), `spatial_map.py` (frames/poses/uncertainty), `kgraph.py` (temporal validity windows), `situation_model.py`, `attention.py`, `salience.py`, `fusion.py` (noisy-OR + uncertainty).
- **THE critical gap:** `novi/perception/` (camera, tracking, faces, grounding, locate-anything — 264 tests) is **not imported by `novi/brain/` at all**. The engine populates the world model via the thin legacy `_update_unified_world` (`engine.py:1573`) which only writes a `presence` field. Camera/tracking/face/grounding evidence never reaches the world model in the live system.
- **Other gaps:** uncertainty (σ) not propagated end-to-end (only isolated in `Pose2D`/`fusion`); coordinate frames not linked to world model (entity `location` is a semantic string; `unified_world` and `spatial` are separate objects); event/activity modeling is skeletal (`add_event` appends unstructured dicts); robot self-state/capabilities not in world model.

### 2.3 Memory & Learning — **mature substrate, partial north-star compliance**
- **Strong durable substrate:** `DurableMemoryStore` (`storage.py`) — SQLite WAL, FTS5 + vector, soft/hard delete, schema versioning, persistence proven. `memory_hardening.py` (WriteGate, CanonicalMemoryRecord with epistemic_status/provenance/integrity_hash, typed retrieval failure states). `consolidation.py` (decay, archival, contradiction supersede). `importance.py` (importance×recency). `learning_pipeline.py` (promotion, corrections, routines, counterfactuals). `sleep_cycle.py` (replay strengthening).
- **Gaps vs north star:**
  1. **Retrieval ranks by vector similarity alone** on `retrieve`/`retrieve_indexed`/`retrieve_semantic` — the north star explicitly forbids this. Only `retrieve_with_states` and chat's `_memory_score` (`chat.py:243`) incorporate time/provenance/confidence.
  2. **Retention not enforced at the store** — expiry only runs on sleep/consolidation cadence; no capacity eviction; `retention_policy_ref` is an inert string.
  3. **Learning subsystems are in-memory only** — `KnowledgePromotionPipeline`, `RoutineDetector`, `UserCorrectionLog`, `CounterfactualEngine`, `ReflectionEngine`, `RegressionMemory` all lost on restart. **Learning does not change behavior** — no mechanism feeds learned knowledge into action selection.
  4. **Memory-type separation is nominal** — all classes in one `memory_records` table; no working-memory buffer; procedural/prospective/metamemory/autobiographical explicitly deferred.
  5. **Replay strengthening is a flat +0.02 bump**, not re-consolidation; `kgraph.contradicted()` is dead code (nothing sets that status).

### 2.4 Reasoning & Cognition — **strong plumbing, deterministic default**
- **Strong plumbing:** `ReasoningProvider` protocol + 3 providers (`reasoning.py`); `ReasoningRouter` with input-aware routing (`router.py` `decide_for_text`); `DeliberativeLLMReasoningProvider` (ANALYSIS→OPTIONS→DECISION + self-critique); `BeliefSystem` (Bayesian noisy-OR); `MacCognition` (hypotheses + temporal/causal inferences); `PredictionEngine` + `SequencePredictor`; `ContextAssembler` (bounded, provenance-filtered, 6 layers); heavily-guardrailed `DialogueEngine` (~30 intent detectors).
- **Gaps vs north star:**
  1. **Default runtime uses deterministic heuristic** — engine defaults to `DeliberativeReasoningProvider` (`engine.py:184`); the LLM providers and router are **CLI-only** (`cli.py:69-77`). No genuine grounded LLM reasoning in the default path.
  2. **Cross-input reasoning is shallow** — each turn reasoned in isolation; `DiscourseState` tracks topic but doesn't feed prior conclusions back.
  3. **Hypothesis formation is template-based**; `IntentHypothesis.alternatives=[]` hard-coded empty (`cognition_typed.py:155`).
  4. **Alternative evaluation not principled** — no explicit scoring on expected-success/cost/risk.
  5. **Prediction error → plan revision loop not closed** — violations spawn curiosity goals but don't revise active plans.
  6. **Decision explanation not surfaced** — chat `reason` is a generic "grounded in N facts" template.

### 2.5 Safety, Governance, Contracts, Observability — **strong artifacts, not the production path**
- **Strong, well-tested:** `GovernanceGuard` (wired, `engine.py:983`); `AutonomyStateMachine` (13 states, wired); `AutonomySupervisor` (12-step loop, leases, A-ARCH-01 10k-tick zero-unauthorized — **not wired**); `SafetyPolicy`/`RuntimeSafetyMonitor` (**not wired**); `AuditTrail` (append-only, redaction, wired); `EventBus` (typed, correlation, wired); `Privacy` (erasure with dependency propagation); `ResourceTelemetry`; `FailureModes` (wired); `Recovery`; `ScenarioSuite` (15 scenarios, hard gate); `BehaviorTree`; `novi/contracts/` (35 versioned JSON Schemas).
- **Gaps vs north star + P0 list:**
  1. **Physical authority boundary (P0 #3) — PARTIAL, biggest gap.** Production path is `governance_guard → body.execute()` with **no `SafetyPolicy` gate, no `RuntimeSafetyMonitor`, no command compiler, no parameter allow-list/bounds, no rate limit, no actuator watchdog/expiry**. The strongest safety artifacts (supervisor, SafetyPolicy) are not the production execution path.
  2. **Two divergent state machines** — `AutonomyStateMachine` (13 states, wired) vs `AutonomySupervisor.AutonomyState` (14 states, not wired); no single canonical machine matching the plan's BOOT/SELF_TEST/SAFE_IDLE/READY/AUTONOMOUS/DEGRADED/FAULT/EMERGENCY_STOP/RECOVERY.
  3. **Security/threat model (P0 #13) — MISSING.** No `security.py`; no systematic threat model across input surfaces.
  4. **Architecture-to-code truth matrix (P0 #1) — MISSING.** The 2026-08-29 plan names Task 01 as the immediate next action; the matrix document does not exist.
  5. **Decision observability/replay (P0 #10) — PARTIAL.** No end-to-end decision trace reconstructing a full run.
  6. **Simulation release gate (P0 #12) — WEAK.** `run_suite()` is a test, not a gate wired to physical deployment.

---

## 3. What we need / what we missed (consolidated)

**The north star is an *integrated loop*, not a collection of components.** What we missed is not capability — it is **integration and enforcement**:

1. **The perception→world→cognition loop is broken** (perception package unwired). This is the single most north-star-critical miss: Novi cannot "perceive its environment and maintain a coherent world model" in the live system.
2. **The safety boundary is not the production path** (supervisor/SafetyPolicy unwired). Novi cannot "act safely in the physical world" with the strongest safety artifacts bypassed.
3. **Grounded reasoning is not the default** (router/LLM CLI-only). Novi cannot "reason over grounded state" by default.
4. **Retrieval ignores time/provenance/confidence** on primary paths, and **learning doesn't change behavior**. Novi cannot "learn from experience" in a way that alters future action.
5. **No security/threat model** and **no architecture-to-code truth matrix** — the two P0 items that gate trustworthiness and prevent duplicate/conflicting systems.
6. **The brain does not fully own all output.** The reply *composition* is brain-owned (`respond()` is source-agnostic), but the raw LLM transport is injected by the surface, and the voice loop is **test-only** — so "the response must always come from the brain, regardless of surface" is design intent, not yet a strict guarantee. (Roadmap items 1d and 3e close this.)

---

## 4. Prioritized roadmap to the north star

Ordered by leverage (each closes a north-star loop link or a P0 safety/trust gate). Each item lists files to touch and an acceptance criterion.

### Phase 1 — Close the perception→world→cognition loop (highest leverage)
- **1a. Wire `novi/perception/` into the engine.** Make `PerceptionPipeline.process_frame`/`ground_frame` the brain's perception path, feeding `WorldObservation`/`GroundingOutcome` into `WorldModel` via the already-built `world_state_adapter.admit_grounding_outcome`. Replace/augment legacy `_update_unified_world`.
  - Files: `engine.py`, `perception/pipeline.py`, `perception/world_state_adapter.py`, `brain/__init__.py`.
  - Accept: a `MacBrain.step()` run with a scripted pipeline produces `OBSERVED` world-model entities and `HYPOTHESIZED` candidates surfaced by `context_assembler.assemble`.
- **1b. Propagate uncertainty end-to-end.** Add σ to `WorldEntity.state`/`WorldRelation`, combine in quadrature on fusion, expose in `uncertainty_summary()`.
  - Files: `world_model.py`, `fusion.py`, `situation_model.py`, `context_assembler.py`.
  - Accept: fusing two observations yields σ smaller than either input; `uncertainty_summary()` reports per-field σ.
- **1c. Link world model to spatial map + robot self-state.** Give `WorldEntity` a `spatial_ref`; maintain a `ROBOT` entity; resolve `visible_entities` by region via `SpatialMap.region_at`.
  - Files: `world_model.py`, `spatial_map.py`, `engine.py`, `self_model.py`.
  - Accept: robot pose at `(x,y)` resolves to `"kitchen"` via `region_at`; `pose_in(frame)` converts through parent transform.
- **1d. Wire a production voice loop through `brain.respond()`.** `VoiceLoop` (`voice/voice_loop.py`) is currently **test-only** — no production instantiation. Instantiate it in the live server with `reply_fn` bound to `brain.respond()`, so spoken replies are the same brain-owned communicative act as web/CLI (grounded in soul/identity/memory, no-assistant/no-repetition rules enforced), not a surface-local LLM call.
  - Files: `voice/voice_loop.py`, `web/server.py` (or a new voice runtime), `brain/chat.py`.
  - Accept: a spoken turn produces its reply via `brain.respond()` (verified by an integration test asserting the reply carries the brain's grounding/guardrails), and the voice loop is exercised in the live server, not only in tests.

### Phase 2 — Make the safety boundary the production path (P0 #3, #4)
- **2a. Route action execution through `AutonomySupervisor` + `SafetyPolicy`.** Insert `SafetyPolicy.evaluate()` + `RuntimeSafetyMonitor.check()` around `body.execute()`; use supervisor leases/one-action-per-tick.
  - Files: `engine.py`, `autonomy_supervisor.py`, `safety_policy.py`, `autonomy.py`.
  - Accept: A-ARCH-01 10k-tick zero-unauthorized holds on the **production** path; e-stop interrupts mid-move within response budget.
- **2b. Unify the two state machines** into one canonical machine (BOOT…RECOVERY) consumed by both engine and supervisor.
  - Files: `autonomy_state_machine.py`, `autonomy_supervisor.py`, `engine.py`.
  - Accept: engine and supervisor always agree on state; every plan-required state/transition tested.
- **2c. Implement the physical authority boundary:** `actuator-command` contract + command compiler (bounds/allow-list/rate-limit/expiry) + watchdog.
  - Files: new `actuator_boundary.py`, `contracts/execution/actuator-command/1.0.0/schema.json`, `engine.py`.
  - Accept: out-of-bounds model command rejected at boundary; expired authorization cannot reach actuator.

### Phase 3 — Make grounded reasoning the default (north-star §5.5)
- **3a. Wire `ReasoningRouter` + LLM deliberation into the engine by default**, with cost-aware routing (LLM only when warranted; per-route cost tracked).
  - Files: `engine.py:184`, `models/router.py`, `cli.py`.
  - Accept: low-confidence substantive conclusion routes to LLM and yields deliberated `ActionIntent`; high-confidence stays deterministic; route counts + cost recorded.
- **3b. Add explicit alternative evaluation** (score options on expected-success/cost/risk; select by score; persist scores).
  - Files: `models/deliberation.py`, `models/reasoning.py`, `engine.py`.
- **3c. Close prediction-error → plan-revision loop.**
  - Files: `planner.py`, `engine.py`, `prediction.py`.
  - Accept: a violating observation marks the active plan failed/replanned and generates a new plan.
- **3d. Make dialogue-level reasoning non-isolated** (feed discourse topic + prior conclusions into next turn; populate `IntentHypothesis.alternatives`).
  - Files: `chat.py`, `discourse.py`, `cognition_typed.py`.
- **3e. Give the brain its own default LLM transport (brain owns the reply end-to-end).** Today the surface injects the raw `llm_chat` callable into `brain.respond()` (`_compose_reply_impl`, `chat.py:923,965`); when it's `None` the brain falls back to deterministic. Move a default LLM provider *inside* `MacBrain` so surfaces pass only the message and the brain owns the reply regardless of source. Surfaces may still override for model tiering, but the default is brain-owned.
  - Files: `brain/chat.py` (`_compose_reply_impl`), `brain/engine.py`, `web/server.py` (stop injecting `_llm_chat`).
  - Accept: `brain.respond(text)` produces a grounded LLM reply with no transport argument; a surface that injects nothing still gets the brain's default provider, and the no-assistant/no-repetition guardrails still apply.

### Phase 4 — Make memory retrieval and learning north-star compliant
- **4a. Rank retrieval by time/provenance/confidence**, not vector similarity alone. Add `retrieve_ranked(query, *, min_confidence, provenance_scope, recency_weight, importance_weight, trust_weight)` fusing vector + recency + importance + trust; apply to `retrieve_semantic`/`retrieve_indexed`.
  - Files: `storage.py`, `importance.py`, `chat.py`.
  - Accept: a low-confidence/stale record and a high-confidence/recent record with equal vector similarity → the high-confidence/recent one returns first.
- **4b. Enforce retention + capacity eviction at the store** (per-type TTL + size cap; honor `expires_at` automatically).
  - Files: new `retention.py`, `storage.py`, `consolidation.py`.
- **4c. Persist learning subsystems and connect them to behavior** (routines/corrections/reflections/lessons survive restart; promoted routine changes action selection; protected invariants untouched).
  - Files: `learning_pipeline.py`, `reflection.py`, `recovery.py`, `storage.py`, `engine.py`.
- **4d. Real replay-driven strengthening + fix contradiction handling** (re-encode recalled records, strengthen supporting triples, make `kgraph.contradicted()` reachable).
  - Files: `sleep_cycle.py`, `kgraph.py`, `consolidation.py`, `storage.py`.

### Phase 5 — Trust gates (P0 #1, #13, #10, #12)
- **5a. Architecture-to-code truth matrix (Task 01).** Map every documented component/interface/state to exact implementation paths, symbols, and tests; mark unsupported claims. This is the immediate next action per the 2026-08-29 plan and should be **started now** to freeze the baseline before architecture-changing work.
  - Files: new `docs/01-system-architecture/ARCHITECTURE_IMPLEMENTATION_MATRIX.md`.
- **5b. Security/threat-model module** (`security.py`) enumerating threats across input surfaces with prevention/detection/containment/recovery + adversarial tests.
- **5c. End-to-end decision trace/replay** (trace ID → observations → world-state version → route → model version → memory refs → tool calls → policy/safety → action → result → confidence → degradation → latency; no raw media).
- **5d. Wire simulation as a release gate** (block physical deployment on `run_suite()` verdict).

---

## 5. What should NOT change (positive baselines to preserve)

- **Stdlib-first core, no web framework, no cloud LLM** — the deliberate architecture is sound and now fast (step 0.125s).
- **Single canonical DB** (`novi/data/novi.db`) — new tables, never new databases.
- **Fail-closed safety** (governance guard, typed contracts, provenance) — coherent where wired.
- **Epistemic discipline** in the world model (hypothetical never overwrites observed) — a genuine strength.
- **Skill governance** — license discipline, centralized activation, bounded prompt injection.

---

## 6. Immediate next actions (this week)

1. **Start Task 01 (architecture-to-code truth matrix)** — freezes the baseline and is the documented immediate next step.
2. **Wire the perception package into the engine (Phase 1a)** — the single highest-leverage north-star gap.
3. **Route action execution through the supervisor + SafetyPolicy (Phase 2a)** — the single highest-leverage safety gap.
4. **Wire the reasoning router + LLM into the engine default (Phase 3a)** — makes grounded reasoning real.

These four close the loop links the north star centers on and are independent enough to run in parallel on disjoint files.
