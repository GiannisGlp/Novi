# Novi Brain — Consolidated Gap Analysis & Next Steps

**Status:** Analysis deliverable (no code changes)
**Date:** 2026-08-22
**Scope:** All 12 completion-gate domains, reconciled against the live `MAC_BRAIN/` + `brain/` implementation and the project's own `MAC_BRAIN/PERFECTING_PLAN/` roadmap.
**Method:** 8 parallel domain analyses (strategy/governance, system-architecture, memory, brain, autonomy, cognition, soul/hardware, implementation-vs-docs) cross-checked against the code, test suite, and git history.

---

## 1. Executive Verdict

**Novi's Mac brain is far along, and the `PERFECTING_PLAN` implementation wave (Steps 1–6) is largely built and wired into the runtime, but it is not yet a "fully functional brain."** The problems are no longer missing subsystems. They are stale documentation that under-reports what is actually implemented, a missing typed-contract layer for cognition, real neural models that are only thin adapters, and deferred spatial, multi-person, and governance-review capabilities.

The project's own `MAC_BRAIN/PERFECTING_PLAN/` (13 files) is the canonical gap analysis and 6-step roadmap. This document reconciles it with the current code, corrects stale claims, and consolidates the 8 domain findings into one prioritized next-step plan.

---

## 2. What Is Actually Implemented (verified against code + tests)

The `MAC_BRAIN/runtime.py` orchestrator (~1460 lines) wires ~30 subsystems into a continuous loop:
perception → cognition → attention → situation → reasoning → governance → skill → closed-loop VERIFY → reflection → soul → social.

**Measured test baseline (this analysis):**
- MAC_BRAIN: **1013** passing (in this working session: prior rounds wrote +8 governance/runtime/durable-independence tests, +5 confirmation-flow, +17 event-bus contract, +11 goal-lifecycle/conflict, +13 audit-trail, +27 scenario/adversarial/endurance, +11 affect→communication mapping, +15 P1–P3 acceptance catalog/gate/runner, +14 spatial model, +9 typed cognition emission, +17 learning pipeline, +10 memory-class decision + schema-evolution hooks)
- brain: **105** passing
- web: **41** passing (slow, ~70s)
- contracts suite: **13** passing (executable validators via pytest shim)
- cognition typed contracts: **34** passing
- **Total: 1206** (fast suites = 1165 + web 41)

**Key implemented capabilities (all wired into `runtime.py`):**
- **Unified WorldModel** — typed entities/relations with epistemic status (OBSERVED/INFERRED/PREDICTED/SIMULATED/VERIFIED/UNKNOWN), contradictions preserved, snapshots, provenance.
- **SituationModel + ContextAssembler** — bounded, provenance-filtered context; `resolve_reference()` implements the "Bring me that cup" reference-resolution scenario.
- **AttentionRanker** — ranked attention candidates.
- **HardenedMemoryManager** — `WriteGate` (7-stage), `retrieve_with_states` (NO_RESULT/AMBIGUOUS/CONFLICTED/STALE/ABSTAIN), `IndependenceTracker`, `ContextualTrust`.
- **MultiSpeedRuntime** — deterministic System-0 safety tier that never waits on an LLM.
- **SkillExecutor + SkillContract** — navigate/inspect/find_object/pick/speak with preconditions/success/failure/timeout/recovery/safety.
- **GovernanceGuard** — "no action executes without grant"; degraded-mode blocks physical actions; confirmation grants.
- **AutonomyStateMachine** — 13 states, validated transition table, interruption/resume.
- **FailureHandler** — degraded modes, escalation, recovery.
- **ClosedLoopRuntime** — observe/plan/act/verify/recover/ask/stop + cross-system acceptance + completion gate.
- **EpisodeRecorder + NoviEpisode schema** — LeRobot/IsaacLab/ROSBag/NoviNative adapters.
- **Soul acceptance harness** — P0GateEvaluator (backward-compatible alias of `AcceptanceGateEvaluator`), full P0–P3 canonical catalog (53 scenarios), CommunicationDecision (fatigue/cooldown/silence/affect-aware), canonical `Lexicon` (replacing the removed `VocabularyScopeModel` duplicate); P0GateRunner wired as release gate with P1–P3 gate entry (`run_acceptance_gate`).
- **Real neural capability (limited):** SSDLite320 object detection (torchvision/MPS), faster-whisper STT. TTS = macOS `say`.
- **Durable SQLite store** — 10 domain tables, FTS5, vector memory, privacy/erasure, consolidation/decay/archival.
- **Web dashboard** — chat, reasoning trace, state, event log, goals+map, real sensing, model switcher (qwen3.8 ⇄ nemotron-3.5-lightning).

---

## 3. Consolidated Gaps (by priority)

### P0 — Documentation / governance integrity (cheapest, highest leverage)

1. **`MAC_BRAIN/32_IMPLEMENTATION_STATUS.md` is STALE.** It ends at natural-conversation round 49 and never documents the PERFECTING_PLAN wave (WorldModel, SkillExecutor, GovernanceGuard, MultiSpeedRuntime, ClosedLoopRuntime, EpisodeRecorder, P0GateEvaluator, VocabularyScopeModel, AutonomyStateMachine, FailureHandler, HardenedMemoryManager). Test counts wrong (claims 858/753+105/web 26; actual 950/804+105/41). The "known limitation" about goal-resume (lines 1290–1293) is outdated — goal-resume is implemented. "Next implementation slice" sections are stale. — **✅ FIXED**: PERFECTING_PLAN wave documented, counts reconciled (then 961; now 1013 MAC_BRAIN + 105 brain + 41 web + 13 contracts + 34 cognition = 1206), stale limitation and "Next implementation slice" removed, roadmap items 11/12/13/16/29/30 documented.
2. **`13_CONSOLIDATED_IMPROVEMENT_PLAN.md` and `32_IMPLEMENTATION_STATUS.md` disagree on test counts** (858 vs 848 vs actual 950) — **✅ FIXED**: both reconciled (1154 → now 1206).
3. **Contracts test suite not runnable:** `contracts/tests` require `jsonschema`, which is not installed and **not declared in `pyproject.toml`**. 0 tests run. `13_CONSOLIDATED` P3 misattributes this to "pytest required." — **✅ FIXED**: `jsonschema>=4.23,<5` declared in dev deps; pytest shim runs the executable validators (13 passing); CI gate added.
4. **Governance contradiction:** the Global Completion Gate says CLOSED / "no new implementation phase until every domain COMPLETE," yet the program is deep in Brain implementation. Needs explicit reconciliation (the gate's intent is that *new phases* wait; the current phase is the Brain phase — but the doc should say so). — **✅ FIXED**: §5.1 reconciliation added to `NOVI_GLOBAL_COMPLETION_GATE.md`.
5. **System Architecture marked COMPLETE** in the tracker, but ARCH-CLOSE evidence docs say PARTIALLY EVIDENCED. Duplicate numbering (16/17/19/20/21/22) and duplicate time-sync authority (17 vs 19) noted. — **✅ FIXED**: tracker reconciliation ("COMPLETE vs PARTIALLY EVIDENCED") + time-sync authority consolidated (17 SUPERSEDED by 19) + ARCH-CLOSE-010 addendum.
6. **Two overlapping autonomy boundary audits** (`12_AUTONOMY_BOUNDARY_AND_OWNERSHIP_AUDIT.md` vs `16_AUTONOMY_ARCHITECTURE_BOUNDARY_AUDIT.md`) with a file-numbering collision (two files numbered 12). The "Wheely" stale-reference claim in `16_AUTONOMY_ARCHITECTURE_BOUNDARY_AUDIT.md` is itself stale — grep finds "Wheely" only inside 16 (lines 655/670/701), not in 00/15. — **✅ FIXED**: 12 marked SUPERSEDED by 16; Wheely wording corrected in 16 sections 20/21/22.
7. **Docs status inconsistency (cognition):** README/24 claim "DESIGN COMPLETE — V1" while 21/22/26 are IN PROGRESS with unmet completion gates. — **✅ FIXED**: `docs/03-cognition/README.md` now distinguishes design-complete vs implementation-in-progress.

### P1 — Cognition typed-contract layer (the single biggest functional gap)

8. **Typed contract layer NOT implemented.** Docs 25/26 prescribe Pydantic v2 models, generated JSON Schema, and structural/semantic/provenance/cross-contract validators for canonical cognitive objects. **No Pydantic is used anywhere** (zero imports); code uses dataclasses. The `cognition/contracts/` package structure does not exist. — **✅ FIXED**: `cognition/contracts/` (12 canonical models + common types), `cognition/validation/` (structural/semantic/provenance/cross-contract + `validate_full`), `cognition/replay/` (fixtures/loader/runner), JSON Schema generation via `cognition.contracts.schemas`. 34 tests passing.
9. **Canonical cognitive objects missing from `contracts/registry.json`:** SituationState, PersonContext, AttentionCandidate, IntentHypothesis, Prediction, CognitiveDecisionRecord, CognitiveEvent are not registered contracts. — **✅ FIXED**: 7 cognition contracts registered (registry 18 → 25), each with generated `schema.json` (`$id` = `<contract_id>/1.0.0`).
10. **No replay fixtures or replay harness** (the 12 listed scenarios in the scenario catalog are not present as a replay runner). — **✅ FIXED**: `cognition/replay/` runs all 12 canonical scenarios (`replay_all`, `summarize`).
11. **No separate structural/semantic/provenance/cross-contract validators** — only `StructuredOutputValidator` and the lightweight `brain/contracts.py`. — **✅ FIXED**: `cognition/validation/structural.py`, `semantic.py`, `provenance.py`, `cross_contract.py`.
12. **Prediction, IntentHypothesis, CognitiveDecisionRecord, CognitiveEvent, PersonContext not typed objects** — cognition emits dicts/strings, not the canonical objects with correlation/causation IDs. — Typed models exist and are validated; the live pipeline now emits them (`MAC_BRAIN/cognition_typed.py` + `MacCognition.cycle_typed` + `MacBrain.cognition_typed`) — roadmap item 12 done.

### P2 — Memory contract completion

13. **`IndependenceTracker` not wired into the durable store path** (exists but not persisted) — **✅ FIXED**: group assigned + persisted on admit, rebuilt on reopen; store-level accessors `independence_group_of` / `independence_corroboration_count`.
14. **No L0–L6 schema-evolution hooks** (additive migrations exist in `storage._migrate`; explicit L0–L6 contract hooks remain open).
15. **Procedural / prospective / metamemory / autobiographical-continuity memory classes deferred** to body phase (heavy; decision needed on now-vs-defer).
16. **No simulated-episode-cannot-be-recalled-as-fact test** (PERFECTING_PLAN Step 2 done-bar) — **✅ **Fixed**: admission gate rejects SIMULATED-as-VERIFIED/OBSERVED; recall test proves a simulated prediction is never surfaced as fact (`test_simulated_episode_cannot_be_recalled_as_fact`).

### P3 — Real neural models (deferred by policy, but a gap to "fully functional")

17. **No real neural TTS** — macOS `say` only. Docs require expressive TTS, voice identity, streaming, interruption, turn-taking.
18. **Nemotron 3 Nano Omni / Cosmos Reason2 are thin adapters** (`b2_nemotron.py`, `b2_cosmos_reason.py` are Protocols/dataclasses). Real inference runs via Ollama (qwen3.8 default, nemotron-3.5-lightning switchable). No TensorRT/CUDA/Jetson/Isaac code.
19. **No real specialist perception models** (RT-DETR, ESS, FoundationStereo) — only deterministic backends.
20. **No model lifecycle/registry manager** (admission, versioning, capability routing) beyond the deterministic runtime.
21. **No streaming inference, real cancellation, batching, or concurrency control** in the model runtime.
22. **No model drift detection, shadow/canary deployment, or rollback.**

### P4 — Spatial / embodiment / multi-person

23. **Spatial/proprioceptive fusion unimplemented** — no SpatialStateEstimator/EmbodiedState, no coordinate frames, occupancy, rooms/floors/doors/zones, metric-vs-semantic link.
24. **No depth/LiDAR/IMU sensors** — only RGB camera (SSLDite). No 3D scene representation or localization.
25. **Multi-person group handling thin** — addressee discrimination, turn-taking, restrained interruption weaker than docs require. — **✅ PARTIAL**: addressee discrimination + turn-taking yielding in `CommunicationDecision` (S60/S61/`yielding_to_interruption`) now enforced and runner-tested; full multi-person group session modeling remains open.
26. **Affect→communication mapping and social-fatigue / "prefer silence" budget not fully enforced.** — **✅ FIXED**: `CommunicationDecision.should_speak` consumes affect (social-overload → `social_overload_reduction` silence, docs/06-soul/05 §14); `affect_expression()` maps affect → expression directive (tone/energy/verbosity/playful/warmth, calmer/quieter in serious contexts per §12/S30); `compose_reply` attaches the directive; `_maybe_initiate` suppresses proactive initiative under overload (15 tests).
27. **No active perception** (repositioning to reduce uncertainty) — no movement actuators. — **OPEN** (deferred to body/hardware phase; virtual-body actuation is Open Decision 10).

### P5 — Autonomy / safety / runtime completeness

28. **Autonomy event-bus contract not implemented** — `MacBrain._emit` appends plain dicts with no correlation/causation IDs or privacy class; no replay, dedup, backpressure, or access control. — **✅ FIXED**: `MAC_BRAIN/event_bus.py` (doc-10 envelope, replay, dedup, bounded backpressure, health, access control); `MacBrain._emit` publishes through the bus with per-cycle correlation domains and causal chaining (17 tests).
29. **No persistent audit trace** — observability is in-memory; no decision trace (trigger→context→decision→policy→action→outcome) with retention. — **✅ FIXED**: `MAC_BRAIN/audit_trail.py` (append-only, retention cap/age, correlation-grouped traces, user audit view, raw-media redaction); `MacBrain.step()` records every consequential action (13 tests).
30. **Confirmation flow not wired** — GovernanceGuard returns REQUIRE_CONFIRMATION and has `confirm()`, but the runtime treats non-ALLOW as not-authorized and never calls `confirm()`. — **✅ FIXED**: `MacBrain.step()` surfaces REQUIRE_CONFIRMATION as a pending request and holds execution; `confirm_action()`/`reject_confirmation()` complete or withdraw it (5 runtime tests).
31. **No resource-aware behavioral adaptation fed by real telemetry** (battery/compute/thermal/network) — MultiSpeedRuntime has resource modes but MacBrain never sets them. **✅ FIXED**: `MacBrain.step()` maps the FailureHandler degraded mode to resource modes each cycle, and now folds in a **real host telemetry feed** (`MAC_BRAIN/resource_telemetry.py`): samples CPU load (`os.getloadavg` normalized by core count) and memory pressure (psutil, or a bounded `sysctl`/`vm_stat` fallback on macOS), maps them to a resource mode, and combines with the failure-handler mode (most conservative wins). Wired via `MacBrain(telemetry=...)` + `_apply_resource_adaptation()`, emitting a `resource.telemetry` event each cycle. 15 tests (`test_resource_telemetry.py`).
32. **No cancellation/deadline enforcement on long-running actions** — `SkillContract.timeout_seconds` not enforced by SkillExecutor — **✅ FIXED**: `SkillExecutor.invoke` sets a monotonic deadline from `contract.timeout_seconds` and reports `TIMEOUT` on overrun; per-action cancellation remains open.
33. **No goal conflict resolution** — BoundedGoalController only supersedes by priority; goal lifecycle lacks paused/blocked/expired states. — **✅ FIXED**: full doc-04 lifecycle (paused/blocked/cancelled/expired + resumability + validity expiry) and conflict resolution (priority within kind, explicit-beats-curiosity, resource-constrained pause, recorded resolutions) in `BoundedGoalController` (11 tests).
34. **No plan validation** against capabilities/policy/resource/safety. — **✅ FIXED**: `PlanValidator` in `planner.py` (8 checks per docs/02-autonomy/05_DECISION_AND_PLANNING.md §Plan Validation: schema, capabilities, arguments, bounded length, spatial, safe termination, temporal, status lifecycle); `MacBrain.set_goal` emits a `plan.validated` verdict (13 adversarial + 1 scenario test). A valid plan still requires policy/safety authorization.
35. **No learning-candidate pipeline** — curiosity only spawns investigate goals; no validation questions, routine discovery, contradiction handling, or provenance learning candidates.
36. **No scenario (Given/When/Then) or adversarial tests** (prompt injection, conflicting sensors, stale world state, network loss, battery depletion). — **✅ PARTIAL**: 9 end-to-end scenario tests (`test_scenarios.py`: reach completion, curiosity discovery, preemption, resource-constrained pause, confirmation flow, audit trace) + 13 adversarial tests (`test_adversarial.py`: NaN/Inf targets, absurd distances, zero/negative budgets, duplicate goal ids, malformed goals, hostile plan inputs). Prompt-injection/sensor-conflict/network-loss/battery adversarial scenarios remain open.
37. **No endurance testing** (memory growth, event backlog, latency, thermal, drift). — **✅ PARTIAL**: 5 endurance tests (`test_endurance.py`): 1000-cycle runs, event-bus backpressure bounds, audit-trail retention cap, adopt/replan churn, long-horizon curiosity with bounded event bus. Latency/thermal profiling remains runtime instrumentation, not yet asserted.
38. **No deterministic replay of autonomy events.**
39. **No real-time safety-critical separation** — System-0 is in-process Python, not an independent deterministic tier.
40. **Orchestrator cognitive modes (REACTIVE/INTERACTIVE/DELIBERATIVE/EXPLORATORY/MAINTENANCE/RECOVERY) not implemented as distinct modes** — one `step()` path.

### P6 — Hardware / simulation / deployment (deferred to body phase — correctly)

41. **Hardware selection OPEN** — Jetson AGX Orin 64GB vs Thor undecided; no benchmarks.
42. **No ROS2/Isaac/Jetson/CUDA/TensorRT integration** — deferred (correct per plan).
43. **No simulation parity (Isaac Sim) or fault injection for real sensors.**
44. **No Jetson/NVIDIA runtime profile** — only no-hardware adapters.
45. **No hardware-in-loop or physical Novi.**

### P7 — Code hygiene / test infrastructure

46. **No dedicated test files for `governance_guard.py` or `multi_speed_runtime.py`** (covered only indirectly via `test_skill_governance.py`).
47. **Web tests slow/flaky** (~70s, sometimes 60s timeout).
48. **Legacy `brain/` dead code** — `brain/b1_loop.py` and `brain/b1_world.py` TemporalWorldModel marked LEGACY but retained; dual-brain import surface.
49. **No pre-commit hooks configured.** — **✅ FIXED**: `.pre-commit-config.yaml` added (ruff `--fix` + ruff-format); ran `ruff check --fix` across `MAC_BRAIN/brain/web/contracts/cognition` (296 safe auto-fixes: import sorting I001, trailing newlines W292, duplicate values B033) — full fast suite still green (1165). ~74 legacy non-auto-fixable lint items remain (mostly in LEGACY `brain/` scaffolds + tests) as a tracked backlog; new code is expected to be ruff-clean.
50. **`VocabularyScopeModel` is a dead duplicate of `Lexicon`** (soul domain). — **✅ FIXED**: removed from `soul_acceptance.py` (scope constants, `VocabularyEntry`, `VocabularyScopeModel`); runtime/chat re-pointed to the canonical `Lexicon`; chat's duplicate `vocab_scope.propose` block removed; dependent tests migrated to Lexicon equivalents (roadmap item 27).

---

## 4. Corrected Claims (subagent findings that were wrong or stale)

- **`PERFECTING_PLAN/` is NOT missing.** The autonomy subagent reported "dangling references" because it looked for the directory at the repo root. The code references (`PERFECTING_PLAN/04_GAP_ANALYSIS_AUTONOMY.md`, etc.) are relative to `MAC_BRAIN/`, and `MAC_BRAIN/PERFECTING_PLAN/` exists with all 13 files. **No dangling references.**
- **Multi-speed runtime IS wired** — `runtime.py:315` registers System-0 safety. `PERFECTING_PLAN` Priority 6's "not wired" claim is stale.
- **Soul acceptance DOES execute end-to-end** — `p0_gate_runner.py` is wired as a release gate. `PERFECTING_PLAN` Priority 7's "doesn't execute end-to-end" claim is stale.
- **Goal-resume IS implemented** — `32_IMPLEMENTATION_STATUS.md`'s "known limitation" (lines 1290–1293) is outdated.

---

## 5. Prioritized Next Steps (roadmap)

### Step 0 — Freeze scope & fix documentation (do first; cheap, unblocks everything)
- [x] 1. Update `MAC_BRAIN/32_IMPLEMENTATION_STATUS.md`: correct test counts (now **1013** MAC_BRAIN + 105 brain + 41 web + 13 contracts + 34 cognition = **1206**), document the PERFECTING_PLAN wave, remove the stale goal-resume limitation and the stale "Next implementation slice" sections.
- [x] 2. Reconcile `13_CONSOLIDATED_IMPROVEMENT_PLAN.md` test counts (858 vs 848 → 1154, now 1206 with cognition + Step 1/2/3 wave).
- [x] 3. Fix the contracts test suite: add `jsonschema` to `pyproject.toml` dev deps, install, run `contracts/tests`, add to CI.
- [x] 4. Reconcile the Global Completion Gate "CLOSED" wording with the active Brain phase; fix System Architecture COMPLETE-vs-PARTIALLY-EVIDENCED; resolve duplicate numbering and duplicate time-sync authority.
- [x] 5. Deprecate one of the two autonomy boundary audits (`12_AUTONOMY_BOUNDARY_AND_OWNERSHIP_AUDIT.md` vs `16_AUTONOMY_ARCHITECTURE_BOUNDARY_AUDIT.md`); fix the file-numbering collision; remove the stale "Wheely" claim in `16_AUTONOMY_ARCHITECTURE_BOUNDARY_AUDIT.md`.
- [x] 6. Reconcile cognition docs status (README/24 "DESIGN COMPLETE" vs 21/22/26 IN PROGRESS).

### Step 1 — Cognition world/context (biggest functional leverage)
- [x] 7. Implement the typed cognitive contract package (Pydantic v2): Observation, Evidence, Entity, Relation, WorldState, SituationState, PersonContext, AttentionCandidate, IntentHypothesis, Prediction, CognitiveDecisionRecord, CognitiveEvent; generate JSON Schema.
- [x] 8. Register the canonical cognitive objects in `contracts/registry.json`.
- [x] 9. Add structural/semantic/provenance/cross-contract validators enforcing ownership boundaries (Cognition cannot grant authorization/command hardware).
- [x] 10. Build the replay fixtures + replay harness (12 scenarios).
- [x] 11. Implement the spatial model (SpatialReference, coordinate frames, occupancy, metric-vs-semantic link) — `MAC_BRAIN/spatial_map.py` (SpatialMap: frames/regions/doors/occupancy, metric↔semantic placement, visibility_between, reachable_regions via doors + containment, `to_spatial_state()` feeding WorldState.spatial_state; `default_home_map()` kitchen/living_room/table_zone). Wired into `MacBrain(spatial_map=...)` + `brain.spatial`; 14 tests.
- [x] 12. Emit typed Prediction/IntentHypothesis/CognitiveDecisionRecord/CognitiveEvent/PersonContext from cognition — `MAC_BRAIN/cognition_typed.py` (`emit_cognitive_typed` → TypedCognitionOutput) + `MacCognition.cycle_typed` + `MacBrain.cognition_typed` (publishes `cognition.typed` on the event bus, stores `_last_typed_cognition`). All emitted objects pass `cognition.validation.validate_structurally` against canonical schemas; decision records are interpretation-only (never authorization); 9 tests.
- [x] 13. Implement knowledge-promotion pipeline + user-correction-with-provenance; routine detection; counterfactual engine — `MAC_BRAIN/learning_pipeline.py` (KnowledgePromotionPipeline with evidence/confidence thresholds — SIMULATED/PREDICTED never promote; UserCorrectionLog supersedes prior claims at authoritative confidence with provenance, history preserved as contradicted; RoutineDetector emits INFERRED hypotheses only; CounterfactualEngine returns SIMULATED hypothetical slices never merged into facts) + runtime wiring `observe_knowledge`/`correct_knowledge`/`observe_routine`/`counterfactual` with learning.* events; 17 tests.

### Step 2 — Memory hardening
- [x] 14. Wire `IndependenceTracker` into the durable store path (group assigned + persisted on admit, rebuilt on reopen; `independence_group_of` / `independence_corroboration_count` accessors).
- [x] 15. Add the simulated-episode-cannot-be-recalled-as-fact test (admission rejection + recall-path status preservation).
- [x] 16. Decide which memory classes (procedural/prospective/metamemory/autobiographical) to implement now vs defer. (L0–L6 schema-evolution hooks also remain.) — `MAC_BRAIN/memory_classes.py` records the decision: SEMANTIC/EPISODIC/SPATIAL/TEMPORAL/PREFERENCE/ROUTINE_CANDIDATE/PROCEDURAL_CANDIDATE implemented now; PROCEDURAL_COMPETENCE/PROSPECTIVE/METAMEMORY/AUTOBIOGRAPHICAL deferred to the body phase with rationale. L0–L6 `SchemaEvolutionGate`: L0–L3 autonomous, L4 proposal-gated, L5/L6 never autonomous. Wired as `brain.memory_classes` + `brain.schema_evolution`; 10 tests.

### Step 3 — Autonomy + skill contract + safety
- [x] 17. Implement the autonomy event-bus contract: `MAC_BRAIN/event_bus.py` implements the canonical doc-10 envelope (event_id/type/version/occurred_at/published_at/source/correlation_id/causation_id/priority/privacy_class/payload) with replay, dedup, bounded-queue backpressure, health metrics, and access control. `MacBrain._emit` now publishes through the bus; each cycle is one correlation domain with causal chaining. 17 new tests.
- [x] 18. Wire the confirmation flow (REQUIRE_CONFIRMATION → surface request → `confirm()` before execution): `MacBrain.step()` now surfaces REQUIRE_CONFIRMATION as a pending request (`governance.confirmation_required` event, `pending_confirmations()`), holds execution, and `confirm_action(grant_id)` / `reject_confirmation(grant_id)` complete or withdraw the request. 5 new runtime tests.
- [x] 19. Add resource-aware behavioral adaptation: `MacBrain.step()` now maps the FailureHandler degraded mode to MultiSpeedRuntime resource modes (FULL / REACTIVE_ONLY / DEGRADED / SAFE_MINIMUM) each cycle. Feeding from real telemetry (battery/compute/thermal/network) remains.
- [x] 20. Enforce `SkillContract.timeout_seconds`: `SkillExecutor` now sets a monotonic deadline and reports `TIMEOUT` on overrun (custom-handler seam for slow backends). Per-action cancellation — remaining.
- [x] 21. Add goal conflict resolution + full goal lifecycle: `BoundedGoalController` now supports the full doc-04 lifecycle (pending/active/paused/blocked/superseded/cancelled/expired/completed/failed) with resumability + validity expiry, and resolves conflicts per doc-04 §Goal Conflicts (priority within kind, explicit-reach-beats-curiosity, resource-constrained pause, recorded resolutions). 11 new tests.
- [x] 22. Add plan validation + scenario/adversarial/endurance suites: `PlanValidator` per docs/02-autonomy/05_DECISION_AND_PLANNING.md §Plan Validation (8 checks; `plan.validated` event on `set_goal`, runtime honors `resource_constrained` via `step()`); 9 scenario + 13 adversarial + 5 endurance tests.
- [x] 23. Add a persistent audit trace with retention + user audit view: `MAC_BRAIN/audit_trail.py` — append-only decision traces (correlation/goal/plan/action IDs, policy+safety results, outcome, timestamps), retention (count + age), correlation-grouped replay, privacy-safe user audit view, raw-media redaction. Wired into `MacBrain.step()` for every consequential action (13 tests).
- [x] 24. Add dedicated test files for `governance_guard.py` and `multi_speed_runtime.py`.

### Step 4 — Soul acceptance + communication
- [x] 25. Complete P1–P3 acceptance classes + remaining ~40 scenarios (P0 is done: 13 scenarios): full canonical catalog of 53 scenarios across the four priority classes (13 P0 + 33 P1 + 3 P2 + 4 P3) in `MAC_BRAIN/soul_acceptance.py` per docs/06-soul/08_BEHAVIORAL_SCENARIOS_AND_ACCEPTANCE.md §7-16; generalized `AcceptanceGateEvaluator` + `GateResult` (per-class gates §§18-20 with pending/inconclusive accounting so coverage stays honest), P1 scenario runners in `MAC_BRAIN/p0_gate_runner.py` (19 executed P1 scenarios pass against a live brain, S03/S04/S10/S11/S13/S20/S22/S31/S32/S40/S41/S45/S51/S53/S61/S63/S72/S73/S82), `run_acceptance_gate(brain, priority)` entry; P2/P3 remain catalog-only (pending). 15 new tests.
- [x] 26. Enforce affect→communication mapping + social-fatigue / "prefer silence" budget: `CommunicationDecision.should_speak` now takes affect and returns `social_overload_reduction` when social-comfort <0.35 && engagement <0.5 (docs/06-soul/05 §14); `affect_expression()` maps affect dims → expression directive (tone/energy/verbosity/playful/warmth; calmer + less playful in serious contexts per §12 and S30); `compose_reply` attaches the directive (incl. `_affect_serious_context` detection) and, under overload, produces silence (`social_overload_reduction` reason + event); `_maybe_initiate` suppresses proactive initiative under social overload (`speech.initiative_suppressed`). 15 new tests.
- [x] 27. Remove the dead `VocabularyScopeModel` duplicate of `Lexicon`: all scope constants/`VocabularyEntry`/`VocabularyScopeModel` removed from `soul_acceptance.py`; runtime/chat re-pointed to the canonical `Lexicon` (`MAC_BRAIN/lexicon.py`); chat's duplicate `vocab_scope.propose` block removed (canonical `self.lexicon.observe` remains); dependent tests migrated to Lexicon equivalents (7 old tests → 7 new Lexicon tests, net-zero count change).

### Step 5 — NVIDIA no-hardware experiments (record evidence)
- [x] 28. Run Exp 1 (reference resolution — implemented), Exp 2 (skill contract — implemented), Exp 3 (NoviEpisode demo dataset — schema+adapters implemented); produce evidence files with evidence-class labels (E0–E5). `MAC_BRAIN/nvidia_experiments.py` now labels each `ExperimentResult` with a validation evidence class (E2 reproducible for Exp 1/2, E3 integration for Exp 3, per docs/01-system-architecture/10_ARCHITECTURE_VALIDATION_AND_TRACEABILITY.md) alongside the OBSERVED/SIMULATED epistemic status; `scripts/mac/nvidia_evidence.py` runs all three experiments on the Mac (no hardware) and writes timestamped, E-class-labelled evidence records + manifest + `commit_sha.txt`/`collection_time.txt` into `IMPLEMENTATION_PLAN/EVIDENCE/mac/<stamp>/` with INDEX.md rows (new: `validation_class` field, 2 tests; all 3 experiments PASS).

### Step 6 — Closed-loop validation + acceptance gate
- [x] 29. Execute cross-system acceptance tests (Soul→Cognition→Memory→Autonomy→Safety→Brain) + completion-gate review + full-suite green — `scripts/mac/cross_system_acceptance.py` runs every priority gate (P0–P3) against a **fresh brain per gate** (gates mutate fatigue/cooldown/affect, so a shared instance made later gates order-dependent — now each gate is a clean-boot acceptance run), plus end-to-end pipeline checks (spatial model, typed cognition, learning pipeline, memory-class decision, event-bus observability) and the full fast suite + architecture-integrity checker. Evidence: `IMPLEMENTATION_PLAN/EVIDENCE/mac/20260822T225017Z/` — **PASS**: P0 13/13 complete, P1 33 (14 runners pending, zero violations), P2/P3 pending-only, 1165 fast-suite passed, integrity PASS.
- [x] 30. Resolve the `brain/` vs `MAC_BRAIN/` dual-brain cleanup (deprecate dead types, clean re-exports, add `MAC_BRAIN/ARCHITECTURE.md`) — dependency scan confirms strict one-way `MAC_BRAIN → brain` (0 reverse imports); Stage-0 scaffolds `brain/b1_loop.py`, `b1_autonomy.py`, `b1_execution.py`, `b1_outcomes.py` marked LEGACY (retained only for `brain/tests`); `MAC_BRAIN/ARCHITECTURE.md` refreshed (1013 MAC_BRAIN + 105 brain + 13 contracts + 34 cognition = 1165 fast, +41 web; new modules: spatial_map, cognition_typed, learning_pipeline, memory_classes, event_bus, audit_trail, soul_acceptance, p0_gate_runner).

### Deferred (body/hardware phase — do NOT start in brain phase)
31. Real neural TTS, Nemotron/Cosmos real inference, specialist perception models, model lifecycle registry, streaming/cancellation/batching, drift/shadow/canary/rollback.
32. Hardware selection (Jetson AGX Orin 64GB vs Thor) via benchmarks; ROS2/Isaac/Jetson/CUDA/TensorRT; simulation parity; hardware-in-loop; physical Novi.

---

## 6. Open Decisions Requiring Human Input

1. **Brain-phase scope:** keep real-model selection (B2.9), hardware, and ROS2/Isaac entirely out of the brain-phase core (recommended) vs start thin seams now?
2. **Acceptance priority:** cognition world/context first (Step 1, recommended) vs memory hardening first?
3. **Minimum governance guard:** deterministic only, or a GovernanceRequest/Decision contract between proposal and execution (docs require the latter)?
4. **Which memory classes** to fully implement now vs defer (procedural, prospective, metamemory, autobiographical continuity)?
5. **Which local LLM/embedding providers** to standardize behind the model runtime (Ollama is current default)? Confirm the embedding provider.
6. **Stand up the NoviEpisode schema + adapters now** (recommended yes, Step 5) so future Isaac/GR00T data stays portable?
7. **Hardware decision:** Jetson AGX Orin 64GB vs Thor — OPEN until representative workload benchmarks exist.
8. **Typed contract layer:** Pydantic v2 (as docs 25/26 prescribe) vs building on the existing dataclass WorldModel to avoid a migration?
9. **Legacy docs disposition:** do `docs/02-novi-brain` 01,02,05,18-22 stay SUPERSEDED vs removed? Is PERFECTING_PLAN plan-only with implementation decisions going through ADR?
10. **Should the Mac prototype's virtual body gain more actuation** (movement) to exercise active perception and spatial fusion before hardware?

---

## 7. Source Documents

- `docs/00-strategy/NOVI_GLOBAL_COMPLETION_GATE.md` (P0, 12 domains, gate CLOSED)
- `docs/00-strategy/NOVI_DOCUMENTATION_AND_IMPLEMENTATION_COMPLETION_TRACKER.md`
- `docs/00-strategy/NOVI_PRE_IMPLEMENTATION_READINESS_AUDIT.md` (GAP-001..020)
- `MAC_BRAIN/PERFECTING_PLAN/` (00, 03–13) — canonical gap analysis + 6-step roadmap
- `MAC_BRAIN/32_IMPLEMENTATION_STATUS.md` (stale — see P0)
- `IMPLEMENTATION_PLAN/00_IMPLEMENTATION_PROGRAM.md` (14 workstreams)
- Domain docs: `docs/01-system-architecture/`, `docs/02-novi-brain/`, `docs/03-cognition/`, `docs/04-memory-and-knowledge/`, `docs/02-autonomy/`, `docs/06-soul/`, `docs/05-hardware/`
