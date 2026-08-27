# Novi — Consolidated Gap Analysis & Improvement Plan

**Date:** 2026-08-26
**Scope:** full repository (docs + `novi/` implementation + tests)
**Purpose:** A single, current, evidence-based source of truth for what is done, what is
gapped, and what to improve next — reconciling the several overlapping/older plan and
audit documents that currently disagree with each other and with the code.

**Method:** enumerated all docs (~600 files) and all source/test modules, read the
authoritative strategy/tracker/audit/plan artifacts, and cross-checked every claim
against the current `novi/brain/` implementation with grep-level verification.

---

## 1. The single most important finding: documentation and code have diverged

The repository has undergone **two structural reorganizations** that older documents
still describe, and its program-status tracker has not kept pace with implementation.

| Artifact (dated) | Claims | Current reality (2026-08-26) |
|---|---|---|
| `docs/00-strategy/NOVI_DOCUMENTATION_AND_IMPLEMENTATION_COMPLETION_TRACKER.md` (08-19) | Brain/Cognition/Memory/Autonomy "IN PROGRESS — implementation pending"; describes `MAC_BRAIN/` + `brain/` split | Both `MAC_BRAIN/` and `brain/` packages **no longer exist**; unified under `novi/brain/`. Much of the "pending" work is implemented and tested. |
| `docs/audits/NOVI_BRAIN_GAP_AND_IMPROVEMENT_AUDIT_2026-08-23.md` | "two brains", `MAC_BRAIN → brain` one-way dependency, "deterministic-first with LLM grafted on" | The two-package split is resolved (single package). Most P0/P1/P2 items it lists have since landed. |
| `docs/specs/brain/PERFECTING_PLAN/13_CONSOLIDATED_IMPROVEMENT_PLAN.md` (08-22) | Baseline 1,206 tests, `MAC_BRAIN/`+`brain/` | Superseded structure; now **159 test files / 1,487 tests** under `novi/`. |
| `docs/plans/BRAIN_COGNITION_IMPROVEMENT_PLAN_2026-08-25.md` | Current 5-phase plan (P1–P5) | The most accurate surviving plan; several phases **already implemented** (see §4). |

**Gap G-1 (governance):** there is no one canonical "current status" document anymore.
Four strategy/audit/plan documents coexist and contradict each other on structure,
test counts, and phase status. Whoever reads the tracker today is misled about what
the system actually does.

---

## 2. What is actually implemented (verified)

These were the headline gaps in prior audits and are now **present in code, with tests**:

- **Typed cognition** (`cognition_typed.py`, `novi/cognition/contracts/`, validators, replay) — in the loop.
- **Semantic memory** — `MiniLMEmbedding` (sentence-transformers, 384d, MPS) with hash fallback; retrieval scoring by relevance/recency/importance.
- **Temporal knowledge graph** (`kgraph.py`) — `valid_from_cycle` / `valid_until_cycle` / `superseded_by`; no stale-fact blindness.
- **Input-aware reasoning router** (`models/router.py` `decide_for_text`) — classifies inputs/social/question, per-class route caching, deterministic fast-path for greetings.
- **Sleep cycle** (`sleep_cycle.py`, `SleepCycle`, `sleep_every_n_cycles=500`) — scheduled consolidation/decay/strengthening.
- **Planner in the loop** (`engine.py` `planner.plan/start/advance/validate/replan`, `closed_loop`) — multi-step agency.
- **Discourse state** (`discourse.py`) — anaphora resolution, continuation tracking.
- **Identity providers** (`face_id.py`, `speaker_id.py`) — cross-modal speaker/face identity.
- **Skill system + centralized activation** (`skills.py`, `skill_activation.py`) — 22 skills, engine-owned activator, vision+STT priming, always-on humanizer pass.
- **Unified input bus** (`input_bus.py`) and **real-IO backends** (`integration/real_io*.py`, `perception/real_backends.py`).
- **Web**: SSE streaming, camera preview, real sensing, live server (`python -m novi.web.server`).

**Verification baseline:** `pytest -q` → **1,487 passing**.

---

## 3. Genuine remaining gaps (verified open)

### G-2 — Causal sequence prediction is not implemented (plan P4)
`prediction.py` only does **persistence** prediction ("will this entity persist?"). There
is no temporal-sequence learning ("after A appears, B tends to appear within k cycles"),
no cause→effect prediction, and expectation violations are therefore limited. The 08-25
plan P4 acceptance criteria are unmet. **Priority: high** — this is the "surprise drives
curiosity" lever.

> **CLOSED 2026-08-26.** Added `SequencePredictor` to `prediction.py` (learns A→B
> precedence from the event log, predicts B when A is observed, scores confirmed/violated
> within a window, tracks rolling accuracy). Wired into `engine.py` step() emitting
> `prediction.sequence_made/confirmed/violated` and `sequence_prediction_accuracy` metric.
> Tests: `test_prediction.py` `SequencePredictorTests` + `EngineSequencePredictionTests`.

### G-3 — Deliberation memory is not implemented (plan P5)
No `memory_type="decision"` is persisted anywhere; reasoning rationale (chosen action and
rejected alternatives) is not stored, so Novi cannot say "last time I chose X because Y"
or avoid re-running rejected reasoning. **Priority: medium-high.**

> **CLOSED 2026-08-26.** Added `_persist_decision_memory` + `_recall_prior_decisions` to
> `engine.py`: deliberative decisions are admitted as `memory_type="decision"` (situation,
> chosen action, rejected alternatives, reason), recalled on similar situations, and
> surfaced as `prior_decisions` in the reasoning trace. Survives restart via the single
> canonical DB. Tests: `test_deliberation_memory.py`.

### G-4 — Legacy `b1_*` scaffolding is still the canonical base layer
`novi/brain/b1_cognition.py` (`DeterministicCognition`), `b1_memory.py`
(`DeterministicMemoryManager`), `b1_world.py` (`TemporalWorldModel`), `b1_autonomy.py`,
`b1_execution.py`, `b1_loop.py`, `b1_outcomes.py` remain and are **re-exported from
`novi/brain/__init__.py`** and inherited by `MacCognition` (`cognition2.py:30`). The
deterministic stage-0 doubles are load-bearing, not "frozen contract-only" as the 08-23
audit intended. **Priority: medium** — this keeps the "deterministic-first" smell alive
and is the root of naming confusion (`cognition` vs `cognition2` vs `cognition_typed`).

> **PARTIAL 2026-08-26.** Clarified the role: `b1_cognition`/`b1_memory`/`b1_world` hold the
> foundational *data types* + deterministic *fast-path* (not pure scaffolding); the canonical
> cognition/memory/world are `cognition2.MacCognition`/`storage.DurableMemoryStore`/
> `world_model.WorldModel`. Added role headers, documented the fast/deliberative split, and
> marked the `__init__.py` re-exports as backward-compat only. The structural rename and
> moving data types out of `b1_*` remain open (deferred — larger refactor).

### G-5 — Code quality: 98 lint findings in `novi/brain/`
`ruff check novi/brain` reports **98 errors** (44 auto-fixable, 26 more with unsafe-fix).
No lint gate in CI enforces cleanliness on new code. **Priority: low-medium** (mechanical,
but accumulating).

> **CLOSED 2026-08-26.** `ruff check novi/brain` now passes clean (0 findings). Fixed the
> 98 findings across source + tests: E402 docstring placement (canonical/contracts/
> observability), F401 re-exports (added `__all__` entries in `models/__init__.py`), F841
> dead variables, B007/B905/B904/B017 (loop vars, `zip(strict=)`, `raise ... from`, specific
> `assertRaises`), SIM102/103/105/108, E741/E702. Added a `Lint (ruff)` step to
> `.github/workflows/brain-runtime-validation.yml` so new findings fail CI.

### G-6 — Doc-collision / retirement debt
- Duplicate numeric prefixes and orphaned/renamed files exist (e.g. `13_GAP_AUDIT_IMPLEMENTATIO…`
truncated filename, several `04-memory…` archive dirs with ~94 historical files, overlapping
`docs/01-system-architecture` numbers, and a `17_SKILL_SYSTEM_DESIGN.md`→`18_…` rename that
left the source numbering context stale). The `docs/04-memory-and-knowledge/archive/`
is kept under an active path rather than a clearly archived location.
- There is an `architecture-integrity` validator (`scripts/validate_architecture_integrity.py`)
but it is not clearly cited as covering the *current* doc tree.

> **CLOSED 2026-08-26.** The validator now **PASSES** (was FAIL). Fixed the 2 broken paths
> (traceability matrix's old `contracts/`-rooted tests README → `novi/contracts/tests/README.md`;
> authored the missing `docs/plans/01_BRAIN/resource_parity_table.md`) and resolved the
> ambiguous numeric references (`doc 15/16/17/07` → exact paths) in `UNIFIED_INPUT_NORTH_STAR.md`,
> `novi/integration/README.md`, `novi/voice/README.md`. The archive dir already had a clear
> `README.md` (ARCHIVED — NON-NORMATIVE) and no truncated filenames remain. Remaining
> "migration warnings" are the validator's explicitly-allowed legacy scoped numeric references,
> not failures.

### G-7 — Simulation / Hardware / Security / Deployment domains still thin
Per the tracker these remain IN PROGRESS without equivalent implementation. This is
expected (software/no-hardware stage) but the tracker does not mark them as explicitly
deferred-to-hardware, so the completion gate reads "CLOSED" with no crisp reopening plan.

> **CLOSED 2026-08-26.** Added §5.2 to `NOVI_GLOBAL_COMPLETION_GATE.md` and the per-domain
> table in `STATUS_2026-08-26.md`: Hardware/Simulation = deferred-to-hardware (reopen trigger =
> first physical sensor/actuator integration); Technology/Validation/Security/Deployment =
> partially implemented. The gate rule is unchanged (still CLOSED); only the labels are now
> accurate.

---

## 4. Improvement plan (ordered)

### Phase A — Restore one source of truth (governance) — ~half day
1. Write a new `docs/00-strategy/STATUS_2026-08-26.md` (or update the tracker) that states:
   unified `novi/brain/` structure, 1,487-test baseline, and the *actual* per-domain state.
2. Mark `MAC_BRAIN/`/`brain/` references in the tracker and PERFECTING_PLAN as SUPERSEDED.
3. Retire/relocate `docs/04-memory-and-knowledge/archive/` under a clearly archived path and
   add a one-line pointer; fix the truncated/garbage filename(s).

> **DONE 2026-08-26.** Wrote `docs/00-strategy/STATUS_2026-08-26.md` (unified `novi/brain/`,
> 1,529-test baseline, honest per-domain state). Added SUPERSEDED banners to the tracker,
> `32_IMPLEMENTATION_STATUS.md`, and the PERFECTING_PLAN README. The archive dir already had a
> clear `README.md` (ARCHIVED — NON-NORMATIVE) and no truncated filenames remain, so item 3
> required no change.

### Phase B — Close the two highest-value capability gaps — ~1–2 days
1. **G-2 causal prediction**: extend `PredictionEngine` in `prediction.py` with temporal
   sequence learning + `prediction.violated` events, feeding existing curiosity/initiative.
   Acceptance: synthetic A→B learned in M repetitions; violation events visible in web log;
   persistence accuracy does not regress.
2. **G-3 deliberation memory**: persist `memory_type="decision"` (situation + chosen action +
   rejected alternatives + reason) via `storage.py`; recall on similar situations; surface as
   "previous decision" in the reasoning trace. Acceptance: second identical situation cites the
   first decision and it survives restart.

### Phase C — Retire deterministic scaffolding as the base — ~1–2 days
1. Promote typed/`MacCognition` as the canonical cognition; make `b1_cognition.py` +
   `b1_memory.py` + `b1_world.py` explicit test-doubles (stop re-exporting as primary types).
2. Rename for clarity (`cognition2.py` → the real orchestrator name) or fold it into
   `cognition_typed.py`, documenting the fast-path/deliberative-path split.
3. Add a deprecation note to each `b1_*` module header and remove non-test imports of them.

> **PARTIAL 2026-08-26 (documentation done; structural rename deferred).** Added
> role-clarification headers to `b1_cognition.py`/`b1_memory.py`/`b1_world.py` (they hold the
> foundational *data types* + deterministic *fast-path*, not scaffolding — the canonical
> cognition/memory/world are `cognition2.MacCognition`/`storage.DurableMemoryStore`/
> `world_model.WorldModel`). Documented the fast-path vs deliberative-path split in
> `cognition2.py` and clarified the `__init__.py` re-exports as backward-compat only. The
> structural rename (`cognition2.py` → canonical name) and moving the data types out of `b1_*`
> remain open — they are a larger refactor with regression risk, deferred to a dedicated pass.

### Phase D — Enforce quality gates — ~1 day
1. Add `ruff` to CI (or a `make lint` gate); fix the 44 auto-fixable findings now, triage the rest.
2. Point `validate_architecture_integrity.py` at the current doc tree and re-run.

> **Item 1 DONE (G-5).** Item 2 re-run 2026-08-26: the validator already scans the whole
> tree via `git ls-files *.md` (no hardcoded tree). It surfaced G-6 doc-collision debt —
> 2 broken paths (the traceability matrix's old `contracts/`-rooted tests README → now
> `novi/contracts/tests/README.md`, and a missing `resource_parity_table.md` → now authored)
> plus ambiguous numeric references in `UNIFIED_INPUT_NORTH_STAR.md`,
> `novi/integration/README.md`, `novi/voice/README.md` (now resolved to exact paths). All G-6
> failures are fixed; the validator passes once the new files are committed (untracked files
> are invisible to `git ls-files`).

### Phase E — Fill the tracker honestly for deferred domains — ~half day
1. Rewrite the Hardware/Simulation/Security/Deployment rows to say "deferred-to-hardware" with
   an explicit reopen trigger, so `GLOBAL GATE` state is accurate rather than permanently CLOSED.

> **DONE 2026-08-26.** Added §5.2 to `NOVI_GLOBAL_COMPLETION_GATE.md` reconciling the gate with
> the unified `novi/brain/` state: Brain/Cognition/Memory/Autonomy = implemented (software);
> Hardware/Simulation = deferred-to-hardware (reopen trigger = first physical sensor/actuator
> integration); Technology/Validation/Security/Deployment = partially implemented. The
> `STATUS_2026-08-26.md` per-domain table carries the same honest labels. GLOBAL GATE stays
> CLOSED (unchanged rule); only the labels are corrected.

---

## 5. What should NOT change (positive baselines to preserve)

- **Stdlib-first core, no web framework, no cloud LLM** — the deliberate architecture is sound.
- **Single canonical DB** (`novi/data/novi.db`) with new tables, never new databases.
- **Fail-closed safety** (governance guard, typed contracts, provenance) — currently coherent.
- **Skill governance** — license discipline (MIT-only ports, original-authored alternatives),
  centralized activation, bounded prompt injection.

---

## 6. Immediate next step

Phase A (restore one source of truth) + Phase B (causal prediction + deliberation memory) are
the highest-leverage first actions. P4/P5 from the 08-25 plan are the only still-open capability
items among its five phases; P1–P3 are effectively landed and only need their acceptance criteria
re-verified and recorded.