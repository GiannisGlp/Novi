# 13 — Consolidated Improvement Plan

**Generated:** 2026-08-22
**Source:** Full-repository analysis (848 tests at generation time; reconciled baseline now **1154** — see Test Baseline), ~60 Python modules, ~200 docs, contracts, web server
**Purpose:** Actionable improvement plan derived from comprehensive gap, bug, and quality analysis of the entire Novi project at the current Mac Brain phase.

---

## Analysis Summary

### What Was Inspected

- `MAC_BRAIN/` — 55 Python modules, 65 test files, 33 program docs, AI_MODELS, COMPONENTS, EVIDENCE, PERFECTING_PLAN, SCENARIOS
- `brain/` — 21 Python modules, 18 test files
- `web/` — server.py (717 lines), static/index.html, 26 tests
- `contracts/` — registry, JSON Schemas across 8 domains, compatibility/validation tests
- `docs/` — 200+ markdown files across 8 domains (00-strategy through 06-soul, plus 02-novi-brain, 05-hardware)
- `IMPLEMENTATION_PLAN/` — 14 domain workstreams + evidence archive (~90 timestamped evidence records)
- `MAC_TESTING/` — 15-file Mac testing program
- `scripts/` — 24 shell/Python scripts for setup, testing, benchmarking, evidence collection
- Git history — 20 most recent commits spanning the PERFECTING_PLAN implementation wave

### Test Baseline (reconciled 2026-08-22, gap-analysis wave; updated for typed-cognition + Step 2/3/4 tests)

| Suite | Count | Status |
|-------|-------|--------|
| MAC_BRAIN/tests | 961 | ✅ All passing (was 743 at generation; +50 dedicated governance-guard / multi-speed-runtime tests; +107 Step 2/3/4 tests in this wave) |
| brain/tests | 105 | ✅ All passing |
| web/tests | 41 | ✅ All passing (slow, ~70s; was 26 — web timeout fixed) |
| contracts/tests | 13 | ✅ All passing via pytest shim (jsonschema now in `pyproject.toml` dev deps) |
| cognition/tests | 34 | ✅ All passing (new typed-cognition package: Pydantic v2 models, validators, replay harness) |
| **Total** | **1154** | |

---

## Priority 1: Clean the `brain/` → `MAC_BRAIN/` Dependency

### Context
`MAC_BRAIN/` **is** the main brain — the canonical implementation. `brain/` is a Stage-0 library that `MAC_BRAIN/` imports as a dependency for base types (`MemoryRecord`, `SpecialistPerception`, `BrainSupervisor`, `Lifecycle`, etc.). The relationship is library → consumer, not two competing implementations.

### Problem
- `brain/b1_loop.py` has `Situation`, `Goal`, `Experience` dataclasses that `MAC_BRAIN/` redefines independently — these are dead code in the library and confusing
- `MAC_BRAIN/runtime.py` is 2217 lines — the orchestrator has grown very large
- The import surface from `brain` is scattered: `MAC_BRAIN/` imports from `brain.b1_cognition`, `brain.b1_memory`, `brain.b1_world`, `brain.b2_perception`, `brain.runtime`, and `brain.contracts` in 66 places
- `brain/__init__.py` exports contracts but nothing from the cognitive modules that `MAC_BRAIN/` actually depends on

### Recommendation
1. **Deprecate dead types in `brain/b1_loop.py`**: `Situation`, `Goal`, `Experience` are redefined in `MAC_BRAIN/` — mark them deprecated in `brain/` or remove if nothing else imports them
2. **Add clean re-exports to `brain/__init__.py`**: The types `MAC_BRAIN/` imports most often (`MemoryRecord`, `SpecialistPerception`, `Detection`, `DeterministicPerceptionBackend`, `BrainSupervisor`, `Lifecycle`, `utc_now`) should be importable from `brain` directly
3. **Split `MAC_BRAIN/runtime.py`**: Extract the chat/dialogue orchestration into `MAC_BRAIN/chat.py` to reduce the orchestrator's size
4. **Add `MAC_BRAIN/ARCHITECTURE.md`**: Document that `MAC_BRAIN/` is the canonical brain, `brain/` is its portable library dependency, and the dependency direction is one-way

### Files Affected
- `brain/__init__.py` — add cognitive re-exports
- `brain/b1_loop.py` — deprecate or remove dead types
- `MAC_BRAIN/runtime.py` — extract chat orchestration
- New: `MAC_BRAIN/ARCHITECTURE.md`

---

## Priority 2: Complete Project Infrastructure

### Problem
- ~~No CI/CD~~ — **Correction:** 5 GitHub Actions workflows already exist (`brain-runtime-validation.yml`, `architecture-integrity-validation.yml`, `consistency-matrix-validation.yml`, `contracts-validation.yml`, `recovered-architecture-gates.yml`). They run on push/PR for brain/ and MAC_BRAIN/ paths.
- No `pyproject.toml` — no way to `pip install -e .` — **✅ Fixed** (`pyproject.toml` created)
- No `ruff.toml` — linting config is in `pyproject.toml` `[tool.ruff]` section — **✅ Done**
- No `requirements.txt` at project root
- No pre-commit hooks
- Dependencies like `torch`, `faster-whisper`, `sounddevice`, `opencv-python` are implicit/optional but not declared — **✅ Fixed** via `[project.optional-dependencies]`

### Recommendation
1. ~~Create `pyproject.toml`~~ ✅ Done
2. Add web tests to the existing CI workflow
3. Add `.pre-commit-config.yaml` with ruff + basic checks
4. Consider a `requirements.txt` for quick setup or document `pip install -e ".[dev]"` in README

### Files to Create
- `.pre-commit-config.yaml`

---

## Priority 3: Fix Stale Documentation and Test Discrepancy

### Problem
- `32_IMPLEMENTATION_STATUS.md` had stale test counts ("201 passed"/"858 passed") — **✅ Fixed** in the gap-analysis wave: counts now reported as 961 MAC_BRAIN + 105 brain + 41 web + 13 contracts + 34 cognition = 1154
- The implementation status doc's stale "Next implementation slice" section — **✅ Fixed** (replaced with PERFECTING_PLAN wave documentation)
- `mac_brain_evidence.json` at root is noted as "first-slice artifact left in place" — should it be archived?

### Recommendation
1. Update `32_IMPLEMENTATION_STATUS.md`: **✅ Done** in the gap-analysis wave —
   stale counts corrected, "Next implementation slice" replaced with a
   "PERFECTING_PLAN implementation wave" section, goal-resume limitation removed,
   and dedicated `test_governance_guard.py` / `test_multi_speed_runtime.py` added.
2. Archive or delete `mac_brain_evidence.json` if it's superseded by the timestamped evidence in `IMPLEMENTATION_PLAN/EVIDENCE/mac/`

---

## Priority 4: Fix Web Test Timeouts

### Problem
Each of 26 web tests creates and destroys a full `NoviWebServer` instance, each spawning a background brain thread. Cumulative resource contention causes 60s+ timeouts.

### Recommendation
1. Use `setUpClass`/`tearDownClass` to share one server instance
2. Add explicit `server.stop()` with timeout guards
3. Consider mocking the background thread for unit-level tests and keeping integration tests separate

### Files Affected
- `web/tests/test_web.py`

---

## Priority 5: Complete MemoryRecord Contract — ✅ PARTIALLY DONE

### Problem
The `brain/b1_memory.py` `MemoryRecord` dataclass has the fields but lacks:
- Full write gate pipeline (identity → integrity → privacy → separation → poisoning → retention)
- Typed retrieval failure states (`NO_RESULT`, `AMBIGUOUS`, `CONFLICTED`, `STALE`, `ABSTAIN`)
- Independence groups for contextual trust
- Schema evolution hooks

### What Was Implemented
1. **DurableMemoryStore now supports WriteGate**: When `write_gate=WriteGate()` is passed, admission runs through the full 7-stage pipeline
2. **DurableMemoryStore now has `retrieve_with_states()`**: Returns `RetrievalResult` with typed failure states (NO_RESULT, AMBIGUOUS, CONFLICTED, STALE, ABSTAIN)
3. **Schema migrated**: 8 new columns added to `memory_records` (epistemic_status, evidence_class, source_class, independence_group, lifecycle_state, integrity_hash, derivation, governance_status) — backward compatible
4. **MacBrain wired**: Both in-memory (HardenedMemoryManager) and durable (DurableMemoryStore) paths use the same WriteGate, so durability never regresses hardening
5. **10 new tests**: Write gate admission/rejection, retrieval failure states, conflict detection, backward compatibility, field persistence

### Tests Added
- `MAC_BRAIN/tests/test_storage.py`: 10 new `HardenedDurableStoreTests` (write gate admit, simulated-as-fact rejection, poisoning rejection, missing provenance, retrieval states, conflict detection, field persistence, backward compatibility)

### Remaining
- Independence groups for contextual trust (IndependenceTracker exists but not wired into durable path)
- Schema evolution hooks (L0-L6 migration framework)
- Procedural/prospective/metamemory memory classes (deferred to body phase)

---

## Priority 6: Implement System-0 Safety Tier (Multi-Speed Runtime)

### Problem
The PERFECTING_PLAN Step 3 calls for a System-0 deterministic safety/reactivity tier that never waits on an LLM. The `multi_speed_runtime.py` exists but is not wired into the main loop. Currently all reasoning — even safety-critical — can be routed through the LLM.

### Recommendation
1. Implement `SafetyReactor` class with hardcoded safety rules (collision-stop, emergency-pause, actuator-limit-enforce)
2. Wire it into `MacBrain.step()` as a pre-action gate that runs before any reasoning
3. Ensure System-0 cannot be bypassed by model output, goal priority, or affect state
4. Add tests for safety-gating of every action type

### Files Affected
- `MAC_BRAIN/multi_speed_runtime.py`
- `MAC_BRAIN/runtime.py`
- New: `MAC_BRAIN/tests/test_safety_reactor.py`

---

## Priority 7: Build Soul Acceptance Harness — ✅ DONE

### Problem
`docs/06-soul/08_BEHAVIORAL_SCENARIOS_AND_ACCEPTANCE.md` defines P0-P3 acceptance classes and scenario format, but:
- The acceptance harness doesn't execute end-to-end
- `test_soul_acceptance.py` exists but is limited
- No automated constitutional-violation detection

### What Was Done
1. **Full canonical catalog (53 scenarios):** `MAC_BRAIN/soul_acceptance.py` now defines the complete P0–P3 catalog per docs/06-soul/08_BEHAVIORAL_SCENARIOS_AND_ACCEPTANCE.md §7-16 — 13 P0 (S01/S02/S60/S70/S71/A01-A08) + 33 P1 (S03/S04/S10/S11/S13/S20–S23/S30–S33/S40–S45/S50/S51/S53/S61–S64/S72/S73/S80–S84) + 3 P2 (S12/S52/S54) + 4 P3 (S90–S93).
2. **Generalized class gates:** `AcceptanceGateEvaluator` + `GateResult` evaluate any priority class (P0 gate: zero constitutional/privacy/escalation/identity/safety violations; P1–P3 per docs/06-soul/08 §18-20), with pending/inconclusive accounting so a partially-instrumented gate stays honest about coverage. `P0GateEvaluator`/`P0GateResult` preserved as backward-compatible aliases.
3. **Scenario runners:** `MAC_BRAIN/p0_gate_runner.py` executes 19 P1 scenarios deterministically against a live brain (`run_acceptance_gate(brain, priority)`); all implemented P1 runners pass end-to-end; P2/P3 remain catalog-only (pending) until their runners are implemented.
4. **Tests:** 15 new tests (9 catalog-format + 6 class-gate semantics) in `test_soul_acceptance.py`; the full catalog/`ScenarioFormatTests`/`P0GateEvaluatorTests`/runtime wiring tests all green.

### Files Created/Modified
- `MAC_BRAIN/soul_acceptance.py` (full P1-P3 catalog + AcceptanceGateEvaluator + GateResult + affect_expression)
- `MAC_BRAIN/p0_gate_runner.py` (P1-P3 runners + run_acceptance_gate)
- `MAC_BRAIN/tests/test_soul_acceptance.py` (catalog + gate + runner tests)

---

## Priority 8: Skill Contract + Governance Guard

### Problem
- `skill_contract.py` defines skill interfaces but the governance/authorization boundary between proposal and execution is not a hard enforcement point
- The guard should be: no action executes without a governance grant, even deterministic ones
- System-0 safety (Priority 6) is the prerequisite for this

### Files to Create/Modify
- `MAC_BRAIN/skill_contract.py` (enhance with governance interface)
- `MAC_BRAIN/governance_guard.py` (enhance)
- New: `MAC_BRAIN/tests/test_governance_hard_boundary.py`

---

## Priority 9: Documentation Cleanup — ✅ PARTIALLY DONE

### Problem
- 200+ markdown files, ~94 in `docs/04-memory-and-knowledge/archive/` alone
- PERFECTING_PLAN notes `docs/02-novi-brain` docs 01,02,05,18-22 are SUPERSEDED
- No deprecation banners
- Navigation is difficult

### What Was Done
1. **Added SUPERSEDED banners** to all 8 identified legacy docs:
   - `docs/02-novi-brain/01_BRAIN_NORTH_STAR_AND_BEHAVIORAL_CONTRACT.md`
   - `docs/02-novi-brain/02_COGNITIVE_ARCHITECTURE.md`
   - `docs/02-novi-brain/05_COGNITIVE_CYCLE.md`
   - `docs/02-novi-brain/18_WORLD_MODEL.md`
   - `docs/02-novi-brain/19_SPATIAL_COGNITION.md`
   - `docs/02-novi-brain/20_TEMPORAL_COGNITION.md`
   - `docs/02-novi-brain/21_SITUATION_MODEL.md`
   - `docs/02-novi-brain/22_SELF_MODEL.md`
   Each banner: `> **⚠️ SUPERSEDED** — Canonical implementations now live in \`MAC_BRAIN/\` (see \`MAC_BRAIN/PERFECTING_PLAN/\`). This document is retained for historical reference only.`

### Remaining
- Move all archives to `docs/archive/` root for consistency (large refactor, defer)
- Merge overlapping specifications (defer to body phase)

### Low Priority — Defer to Body Phase
- Real neural model selection/benchmarks
- Jetson/CUDA/TensorRT/ROS2/Isaac integration
- Physical robot hardware

---

## Implementation Order

```
Week 1:  Priority 2 (infrastructure) + Priority 4 (web tests)
Week 2:  Priority 3 (doc fixes) + Priority 1 (dual-brain docs)
Week 3:  Priority 6 (System-0 safety tier)
Week 4:  Priority 5 (MemoryRecord contract) + Priority 8 (governance guard)
Week 5:  Priority 7 (soul acceptance harness)
Week 6:  Priority 9 (doc cleanup)
```

Each priority has a clear done-bar (testable, verifiable). Infrastructure first because everything else builds on it. Safety before governance because the governance guard depends on System-0.

---

## Bugs Register

| # | Bug | Severity | Priority |
|---|-----|----------|----------|
| 1 | Web tests timeout (26 tests each created/destroyed full server — now uses shared `setUpClass`) — **✅ Fixed** | Medium | P4 |
| 2 | `32_IMPLEMENTATION_STATUS.md` says "201 passed" — actual is 848 — **✅ Fixed** | Low | P3 |
| 3 | No version-compatibility check on durable store open — **✅ Fixed** (schema_version table + migration tracking + future-major rejection) | Medium | P5 |
| 4 | No `pyproject.toml` — undeclared dependencies — **✅ Fixed** | Medium | P2 |
| 5 | `brain/__init__.py` missing re-exports for cognitive types MAC_BRAIN depends on — **✅ Fixed** | Low | P1 |
| 6 | `mac_brain_evidence.json` at root is stale first-slice artifact — **✅ Fixed** (archived) | Low | P3 |
| 7 | Dead types in `brain/b1_loop.py` (`Situation`, `Goal`, `Experience`) — redefined in MAC_BRAIN — **✅ Fixed** (LEGACY docstring) | Low | P1 |

---

## Evidence of Analysis Completeness

- All **1154** tests run (MAC_BRAIN: 961 ✅, brain: 105 ✅, web: 41 ✅, contracts: 13 ✅, cognition: 34 ✅) — reconciled during the gap-analysis wave and updated with typed-cognition + Step 2/3/4 tests
- All ~60 Python source files inspected
- All 12 PERFECTING_PLAN documents read
- All 8 doc domains and their READMEs reviewed
- Git history examined (20 recent commits)
- Contract registry and JSON Schemas validated
- Web server and static UI reviewed
- IMPLEMENTATION_PLAN and MAC_TESTING programs reviewed
- Evidence archive inventoried (~90 timestamped records)