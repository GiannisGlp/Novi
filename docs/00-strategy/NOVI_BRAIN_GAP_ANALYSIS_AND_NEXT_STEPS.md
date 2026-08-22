# Novi Brain — Consolidated Gap Analysis & Next Steps

**Status:** Analysis deliverable (no code changes)
**Date:** 2026-08-22
**Scope:** All 12 completion-gate domains, reconciled against the live `MAC_BRAIN/` + `brain/` implementation and the project's own `MAC_BRAIN/PERFECTING_PLAN/` roadmap.
**Method:** 8 parallel domain analyses (strategy/governance, system-architecture, memory, brain, autonomy, cognition, soul/hardware, implementation-vs-docs) cross-checked against the code, test suite, and git history.

---

## 1. Executive Verdict

**Novi's Mac brain is far along — and the `PERFECTING_PLAN` implementation wave (Steps 1–6) is largely built and wired into the runtime — but it is not yet a "fully functional brain."** The dominant problems are no longer missing subsystems; they are (a) **stale documentation that under-reports what is actually implemented**, (b) a **missing typed-contract layer** for cognition, (c) **real neural models that are thin adapters only**, and (d) **deferred spatial / multi-person / governance-review capabilities**.

The project's own `MAC_BRAIN/PERFECTING_PLAN/` (13 files) is the canonical gap analysis and 6-step roadmap. This document reconciles it with the current code, corrects stale claims, and consolidates the 8 domain findings into one prioritized next-step plan.

---

## 2. What Is Actually Implemented (verified against code + tests)

The `MAC_BRAIN/runtime.py` orchestrator (~1460 lines) genuinely wires ~30 subsystems into a continuous loop:
perception → cognition → attention → situation → reasoning → governance → skill → closed-loop VERIFY → reflection → soul → social.

**Measured test baseline (this analysis):**
- MAC_BRAIN: **804** passing
- brain: **105** passing
- web: **41** passing (slow, ~70s)
- **Total: 950** (fast suites = 909)
- contracts: **0 runnable** (blocked by missing `jsonschema`)

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
- **Soul acceptance harness** — P0GateEvaluator, VocabularyScopeModel, CommunicationDecision (fatigue/cooldown/silence); P0GateRunner wired as release gate.
- **Real neural capability (limited):** SSDLite320 object detection (torchvision/MPS), faster-whisper STT. TTS = macOS `say`.
- **Durable SQLite store** — 10 domain tables, FTS5, vector memory, privacy/erasure, consolidation/decay/archival.
- **Web dashboard** — chat, reasoning trace, state, event log, goals+map, real sensing, model switcher (qwen3.8 ⇄ nemotron-3.5-lightning).

---

## 3. Consolidated Gaps (by priority)

### P0 — Documentation / governance integrity (cheapest, highest leverage)

1. **`MAC_BRAIN/32_IMPLEMENTATION_STATUS.md` is STALE.** It ends at natural-conversation round 49 and never documents the PERFECTING_PLAN wave (WorldModel, SkillExecutor, GovernanceGuard, MultiSpeedRuntime, ClosedLoopRuntime, EpisodeRecorder, P0GateEvaluator, VocabularyScopeModel, AutonomyStateMachine, FailureHandler, HardenedMemoryManager). Test counts wrong (claims 858/753+105/web 26; actual 950/804+105/41). The "known limitation" about goal-resume (lines 1290–1293) is outdated — goal-resume is implemented. "Next implementation slice" sections are stale.
2. **`13_CONSOLIDATED_IMPROVEMENT_PLAN.md` and `32_IMPLEMENTATION_STATUS.md` disagree on test counts** (858 vs 848 vs actual 950).
3. **Contracts test suite not runnable:** `contracts/tests` require `jsonschema`, which is not installed and **not declared in `pyproject.toml`**. 0 tests run. `13_CONSOLIDATED` P3 misattributes this to "pytest required."
4. **Governance contradiction:** the Global Completion Gate says CLOSED / "no new implementation phase until every domain COMPLETE," yet the program is deep in Brain implementation. Needs explicit reconciliation (the gate's intent is that *new phases* wait; the current phase is the Brain phase — but the doc should say so).
5. **System Architecture marked COMPLETE** in the tracker, but ARCH-CLOSE evidence docs say PARTIALLY EVIDENCED. Duplicate numbering (16/17/19/20/21/22) and duplicate time-sync authority (17 vs 19) noted.
6. **Two overlapping autonomy boundary audits** (12 vs 16) with a file-numbering collision (two files numbered 12). The "Wheely" stale-reference claim in doc 16 is itself stale — grep finds "Wheely" only inside 16 (lines 655/670/701), not in 00/15.
7. **Docs status inconsistency (cognition):** README/24 claim "DESIGN COMPLETE — V1" while 21/22/26 are IN PROGRESS with unmet completion gates.

### P1 — Cognition typed-contract layer (the single biggest functional gap)

8. **Typed contract layer NOT implemented.** Docs 25/26 prescribe Pydantic v2 models, generated JSON Schema, and structural/semantic/provenance/cross-contract validators for canonical cognitive objects. **No Pydantic is used anywhere** (zero imports); code uses dataclasses. The `cognition/contracts/` package structure does not exist.
9. **Canonical cognitive objects missing from `contracts/registry.json`:** SituationState, PersonContext, AttentionCandidate, IntentHypothesis, Prediction, CognitiveDecisionRecord, CognitiveEvent are not registered contracts.
10. **No replay fixtures or replay harness** (the 12 listed scenarios in the scenario catalog are not present as a replay runner).
11. **No separate structural/semantic/provenance/cross-contract validators** — only `StructuredOutputValidator` and the lightweight `brain/contracts.py`.
12. **Prediction, IntentHypothesis, CognitiveDecisionRecord, CognitiveEvent, PersonContext not typed objects** — cognition emits dicts/strings, not the canonical objects with correlation/causation IDs.

### P2 — Memory contract completion

13. **`IndependenceTracker` not wired into the durable store path** (exists but not persisted).
14. **No L0–L6 schema-evolution hooks.**
15. **Procedural / prospective / metamemory / autobiographical-continuity memory classes deferred** to body phase (heavy; decision needed on now-vs-defer).
16. **No simulated-episode-cannot-be-recalled-as-fact test** (PERFECTING_PLAN Step 2 done-bar).

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
25. **Multi-person group handling thin** — addressee discrimination, turn-taking, restrained interruption weaker than docs require.
26. **Affect→communication mapping and social-fatigue / "prefer silence" budget not fully enforced.**
27. **No active perception** (repositioning to reduce uncertainty) — no movement actuators.

### P5 — Autonomy / safety / runtime completeness

28. **Autonomy event-bus contract not implemented** — `MacBrain._emit` appends plain dicts with no correlation/causation IDs or privacy class; no replay, dedup, backpressure, or access control.
29. **No persistent audit trace** — observability is in-memory; no decision trace (trigger→context→decision→policy→action→outcome) with retention.
30. **Confirmation flow not wired** — GovernanceGuard returns REQUIRE_CONFIRMATION and has `confirm()`, but the runtime treats non-ALLOW as not-authorized and never calls `confirm()`.
31. **No resource-aware behavioral adaptation fed by real telemetry** (battery/compute/thermal/network) — MultiSpeedRuntime has resource modes but MacBrain never sets them.
32. **No cancellation/deadline enforcement on long-running actions** — `SkillContract.timeout_seconds` not enforced by SkillExecutor.
33. **No goal conflict resolution** — BoundedGoalController only supersedes by priority; goal lifecycle lacks paused/blocked/expired states.
34. **No plan validation** against capabilities/policy/resource/safety.
35. **No learning-candidate pipeline** — curiosity only spawns investigate goals; no validation questions, routine discovery, contradiction handling, or provenance learning candidates.
36. **No scenario (Given/When/Then) or adversarial tests** (prompt injection, conflicting sensors, stale world state, network loss, battery depletion).
37. **No endurance testing** (memory growth, event backlog, latency, thermal, drift).
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
49. **No pre-commit hooks configured.**
50. **`VocabularyScopeModel` is a dead duplicate of `Lexicon`** (soul domain).

---

## 4. Corrected Claims (subagent findings that were wrong or stale)

- **`PERFECTING_PLAN/` is NOT missing.** The autonomy subagent reported "dangling references" because it looked for the directory at the repo root. The code references (`PERFECTING_PLAN/04_GAP_ANALYSIS_AUTONOMY.md`, etc.) are relative to `MAC_BRAIN/`, and `MAC_BRAIN/PERFECTING_PLAN/` exists with all 13 files. **No dangling references.**
- **Multi-speed runtime IS wired** — `runtime.py:315` registers System-0 safety. `PERFECTING_PLAN` Priority 6's "not wired" claim is stale.
- **Soul acceptance DOES execute end-to-end** — `p0_gate_runner.py` is wired as a release gate. `PERFECTING_PLAN` Priority 7's "doesn't execute end-to-end" claim is stale.
- **Goal-resume IS implemented** — `32_IMPLEMENTATION_STATUS.md`'s "known limitation" (lines 1290–1293) is outdated.

---

## 5. Prioritized Next Steps (roadmap)

### Step 0 — Freeze scope & fix documentation (do first; cheap, unblocks everything)
1. Update `MAC_BRAIN/32_IMPLEMENTATION_STATUS.md`: correct test counts to **950** (804 MAC_BRAIN + 105 brain + 41 web), document the PERFECTING_PLAN wave, remove the stale goal-resume limitation and stale "Next implementation slice" sections.
2. Reconcile `13_CONSOLIDATED_IMPROVEMENT_PLAN.md` test counts (858 vs 848 → 950).
3. Fix the contracts test suite: add `jsonschema` to `pyproject.toml` dev deps, install, run `contracts/tests`, add to CI.
4. Reconcile the Global Completion Gate "CLOSED" wording with the active Brain phase; fix System Architecture COMPLETE-vs-PARTIALLY-EVIDENCED; resolve duplicate numbering and duplicate time-sync authority.
5. Deprecate one of the two autonomy boundary audits (12 vs 16); fix the file-numbering collision; remove the stale "Wheely" claim in doc 16.
6. Reconcile cognition docs status (README/24 "DESIGN COMPLETE" vs 21/22/26 IN PROGRESS).

### Step 1 — Cognition world/context (biggest functional leverage)
7. Implement the typed cognitive contract package (Pydantic v2): Observation, Evidence, Entity, Relation, WorldState, SituationState, PersonContext, AttentionCandidate, IntentHypothesis, Prediction, CognitiveDecisionRecord, CognitiveEvent; generate JSON Schema.
8. Register the canonical cognitive objects in `contracts/registry.json`.
9. Add structural/semantic/provenance/cross-contract validators enforcing ownership boundaries (Cognition cannot grant authorization/command hardware).
10. Build the replay fixtures + replay harness (12 scenarios).
11. Implement the spatial model (SpatialReference, coordinate frames, occupancy, metric-vs-semantic link).
12. Emit typed Prediction/IntentHypothesis/CognitiveDecisionRecord/CognitiveEvent/PersonContext from cognition.
13. Implement knowledge-promotion pipeline + user-correction-with-provenance; routine detection; counterfactual engine.

### Step 2 — Memory hardening
14. Wire `IndependenceTracker` into the durable store path; add L0–L6 schema-evolution hooks.
15. Add the simulated-episode-cannot-be-recalled-as-fact test.
16. Decide which memory classes (procedural/prospective/metamemory/autobiographical) to implement now vs defer.

### Step 3 — Autonomy + skill contract + safety
17. Implement the autonomy event-bus contract (correlation/causation IDs, privacy class, replay, dedup, backpressure, access control).
18. Wire the confirmation flow (REQUIRE_CONFIRMATION → surface request → `confirm()` before execution).
19. Add resource-aware behavioral adaptation fed by real telemetry.
20. Enforce `SkillContract.timeout_seconds`; add per-action cancellation/deadline.
21. Add goal conflict resolution + full goal lifecycle (paused/blocked/expired).
22. Add plan validation; add scenario + adversarial test suites; add endurance testing.
23. Add a persistent audit trace with retention + user audit view.
24. Add dedicated test files for `governance_guard.py` and `multi_speed_runtime.py`.

### Step 4 — Soul acceptance + communication
25. Complete P1–P3 acceptance classes + remaining ~40 scenarios (P0 is done: 13 scenarios, 37 tests).
26. Enforce affect→communication mapping + social-fatigue / "prefer silence" budget.
27. Remove the dead `VocabularyScopeModel` duplicate of `Lexicon`.

### Step 5 — NVIDIA no-hardware experiments (record evidence)
28. Run Exp 1 (reference resolution — implemented), Exp 2 (skill contract — implemented), Exp 3 (NoviEpisode demo dataset — schema+adapters implemented); produce evidence files with evidence-class labels (E0–E5).

### Step 6 — Closed-loop validation + acceptance gate
29. Execute cross-system acceptance tests (Soul→Cognition→Memory→Autonomy→Safety→Brain) + completion-gate review + full-suite green.
30. Resolve the `brain/` vs `MAC_BRAIN/` dual-brain cleanup (deprecate dead types, clean re-exports, add `MAC_BRAIN/ARCHITECTURE.md`).

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
- `docs/00-strategy/NOVI_READINESS_AUDIT.md` (GAP-001..020)
- `MAC_BRAIN/PERFECTING_PLAN/` (00, 03–13) — canonical gap analysis + 6-step roadmap
- `MAC_BRAIN/32_IMPLEMENTATION_STATUS.md` (stale — see P0)
- `IMPLEMENTATION_PLAN/00_IMPLEMENTATION_PROGRAM.md` (14 workstreams)
- Domain docs: `docs/01-system-architecture/`, `docs/02-novi-brain/`, `docs/03-cognition/`, `docs/04-memory-and-knowledge/`, `docs/02-autonomy/`, `docs/06-soul/`, `docs/05-hardware/`
