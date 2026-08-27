# Novi — Full Project Analysis
**Date:** 2026-08-23
**Scope:** entire repository — code, tests, contracts, CI, docs, evidence, environment
**Method:** executed, not inferred — full pytest run, ruff lint/format, architecture-integrity gate, brain smoke test, registry/schema cross-check, git and dependency inspection.

---

## 1. Executive Summary

Novi is in a **healthy, consolidating state**: the full test suite (1,285 tests) passes, the deterministic brain runs end-to-end, M1 real neural perception has real Mac/MPS execution evidence, and the package consolidation (`MAC_BRAIN` → `novi.brain`) is essentially complete. The working tree is clean at commit `ff8b2a6` (885 commits).

Three concrete defects were found and should be fixed before the next push to `main`, because two of them break CI gates:

| # | Finding | Severity | Where |
|---|---|---|---|
| 1 | Architecture-integrity gate **FAILS**: 6 unresolved document references | High (CI-blocking) | `scripts/validate_architecture_integrity.py` output |
| 2 | Three GitHub workflows still reference the removed root-level `contracts/` tree | High (CI broken/no-op) | `.github/workflows/{contracts-validation,consistency-matrix-validation,recovered-architecture-gates}.yml` |
| 3 | 129 ruff lint errors; 165 of ~695 Python files would be reformatted | Medium (hygiene) | repo-wide |

---

## 2. Verification Results (executed this session)

### 2.1 Test suite — PASS

```text
pytest (testpaths: novi/brain/tests, novi/web/tests, novi/contracts/tests, novi/cognition/tests)
======================= 1285 passed in 95.65s ========================
```

- 116 test files across four suites.
- Coverage spans the whole cognitive stack: b0/b1/b2 stage gates, autonomy state machine, memory hardening, storage, governance/skill executor wiring, soul/soul acceptance, dialogue, world model, closed loop, typed cognition contracts, web chat fixes.

### 2.2 Brain runtime smoke test — PASS

```text
python -m novi.brain.cli --cycles 1   → exit 0
run_id: abc321d3-4f2c-494b-9a03-f819a9ba8c8c  (evidence JSON emitted)
```

This is the same gate used by the `brain-runtime-validation.yml` CI workflow.

### 2.3 Architecture integrity — FAIL

```text
ARCHITECTURE INTEGRITY: FAIL
- docs/01-system-architecture/50_ARCH_CLOSE_009_FINAL_TRACEABILITY_MATRIX_2026-08-19.md:
    unresolved document path: novi/contracts/tests/README.md            (×5)
- docs/audits/NOVI_BRAIN_GAP_AND_IMPROVEMENT_AUDIT_2026-08-23.md:
    unresolved document path: docs/ARCHITECTURE_CLARITY.md         (×1)
```

Root cause: contracts moved from root `contracts/` → `novi/contracts/` (commits `8dd80ef`, `bae36f3`) but the traceability matrix still cites the old paths. The referenced audit promised a `docs/ARCHITECTURE_CLARITY.md` that was never created. This script is itself a CI gate (`architecture-integrity.yml`), so **pushes to main currently fail CI**.

> **Since fixed (2026-08-26):** the traceability matrix now cites `novi/contracts/tests/README.md`
> (the `contracts/` → `novi/contracts/` move was applied), and `docs/ARCHITECTURE_CLARITY.md` was
> authored. The FAIL output above is the historical 2026-08-23 state, retained for traceability.

Fix options: update the matrix links to `novi/contracts/tests/README.md` (and compatibility README), and either author `docs/ARCHITECTURE_CLARITY.md` or reword the audit reference.

### 2.4 CI workflow drift — 3 workflows stale

Workflows referencing paths that no longer exist after consolidation:

| Workflow | Broken references |
|---|---|
| `contracts-validation.yml` | `contracts/**` paths, `python contracts/tests/...` commands |
| `consistency-matrix-validation.yml` | `contracts/tests/integration/test_consistency_state_matrix.py` |
| `recovered-architecture-gates.yml` | `contracts/tests/integration/*.py`, `contracts/resource_budgets.stage1.json` |

The correct location is now `novi/contracts/…`. Note also that `novi/contracts/resource_budgets.stage1.json` was not found on disk — verify whether it was dropped intentionally or needs restoring under the new tree. The two remaining workflows (`brain-runtime-validation.yml`, `architecture-integrity.yml`) use valid paths.

### 2.5 Lint & format

```text
ruff check .        → 129 errors (50 auto-fixable with --fix)
ruff format --check → 165 files would be reformatted, 530 already formatted
```

Error profile (all low-risk mechanical classes):

```text
46  I001   unsorted-imports          [*] auto-fixable
22  F841   unused-variable           [ ]
12  E402   module-import-not-at-top  [ ] (often intentional sys.path setup — consider noqa)
 9  SIM102 collapsible-if
 8  SIM105 suppressible-exception
 6  B017   assert-raises-exception   [ ] (tests only)
 5  F401   unused-import             [-]
 4  B007 / 4 E741 / 4 SIM103 / 3 E702 / 3 SIM108 / 2 B905 / 1 SIM300
```

Recommended: run `ruff check --fix` for I001/F401, then triage F841/E402 manually (E402 in scripts is usually deliberate bootstrap ordering). Formatting can land as a single dedicated no-op-content commit.

### 2.6 Contract registry vs schemas — PASS

All **25 registered contracts** resolve to schema files on disk under `novi/contracts/`:

```text
registry contracts: 25
missing schema files: 0
```

Versioned extras exist too (`event-envelope` 1.1.0 and 2.0.0 alongside 1.0.0), exercised by the compatibility fixtures.

### 2.7 Repository hygiene — PASS

- No `__pycache__`, `.pyc`, `.venv`, `.pytest_cache`, or `.ruff_cache` files tracked (verified via `git ls-files`); 1,334 tracked files total.
- Working tree clean; last commit `ff8b2a6` "Route web chat through brain-owned respond(); web becomes thin client" (2026-08-23).

---

## 3. Codebase Shape

```text
Python LOC by area:
  novi/brain      38,309   (canonical implementation)
  novi/cognition   2,466   (typed Pydantic contract layer + replay + validation)
  novi/web         1,989   (thin HTTP client over brain.respond())
  novi/contracts   1,182   (JSON schemas + executable suite)

Largest brain modules (complexity hotspots):
  engine.py                1,921
  dialogue.py              1,087
  storage.py               1,052
  chat.py                  1,005
  memory_hardening.py        838
  soul_acceptance.py         822
  p0_gate_runner.py          672
```

Observations:

- **Consolidation is complete in code.** `novi/web/server.py` imports exclusively from `novi.brain.*`; the only remaining `MAC_BRAIN` mentions are historical notes in `novi/brain/__init__.py` docstrings. No import references remain.
- `engine.py` at ~1.9k lines is the single largest module and a candidate for decomposition along the same seams the codebase already uses elsewhere (perception / cognition / autonomy submodules exist as separate files).
- The b0/b1/b2 module families (`b1_*`, `b2_*`) map to documented stage gates and have matching test files — good traceability.

## 4. Environment & Dependencies

- venv: **Python 3.14.7**, macOS 26.5.1 arm64 (Apple Silicon).
- Neural stack installed and functional: torch 2.13.0 (+ MPS available), torchvision 0.28.0, faster-whisper 1.2.1, sentence-transformers 6.0.0, onnxruntime 1.29.0.
- Structured stack: pydantic 2.13.4, jsonschema 4.26.0, Pint 0.25.3, uncertainties 3.2.3, simpy 4.1.2, opencv 5.0.0, sounddevice 0.5.6.
- Dev tooling: pytest 9.1.1, ruff 0.16.4 — both match `pyproject.toml` floors.
- Note: local dev runs 3.14 while CI pins 3.12; `requires-python >=3.11`. Worth adding one newer Python to the CI matrix eventually so 3.14 stays covered by automation rather than only locally.

## 5. Validation Status & Evidence

- **M1 (Real Neural Perception) is genuinely validated**: `mac_test_results/M1/latest.json` records SSDLite320 MobileNetV3 running on **MPS** (`device: mps`, load 0.36 s, inference 5.65 s) producing real detections ("tv" @ 0.56 conf) against `test-image.png`, with full provenance block and commit SHA pinning. Camera capture evidence exists alongside (`camera-*.json`).
- `neural_environment.json` documents the exact neural environment (MPS built + available).
- The project's own validation-state ladder (DESIGNED → … → INTEGRATED) is respected: perception providers carry execution evidence rather than just documentation.

## 6. Documentation

Extensive and mostly consistent: 40+ numbered specs under `docs/specs/brain/`, a 14-domain plans tree, technology reference/baseline, strategy and hardware docs. Two documentation defects found (both already listed above): stale `contracts/…` links in the final traceability matrix, and the never-written `docs/ARCHITECTURE_CLARITY.md`.

One staleness note: `docs/audits/NOVI_BRAIN_GAP_AND_IMPROVEMENT_AUDIT_2026-08-23.md` predates the merge-under-one-namespace commits and describes a two-brain layout (`brain/` vs `MAC_BRAIN/`). Its domain-by-domain gap analysis (Bayesian belief upgrade, planner-not-wired-into-step, HashingEmbedding vector search, typed-contracts not in main loop) remains valuable as a backlog, but its structural claims are superseded.

## 7. Recommended Actions (priority order)

1. **Repair CI gates** — update the traceability-matrix links to `novi/contracts/...`, create or de-reference `docs/ARCHITECTURE_CLARITY.md`; repoint the three stale workflows at `novi/contracts/**` and confirm whether `resource_budgets.stage1.json` must be restored. Verify with `python scripts/validate_architecture_integrity.py` → PASS.
2. **Lint pass** — `ruff check --fix`, then hand-triage the remaining ~79 findings (mostly F841/E402/SIM).
3. **Format pass** — one dedicated `ruff format` commit (165 files, content-neutral).
4. **Backlog from the gap audit** — wire the planner into `step()`, promote typed-cognition emission into the main loop, Bayesian belief upgrade, semantic embeddings replacing `HashingEmbedding`.
5. **Decompose `engine.py`** opportunistically when next touched.
6. Optionally extend the CI Python matrix beyond 3.12.

---

## 8. Verdict

**Green core, red edges.** The product code is tested (1,285 passing), smoke-runnable, contract-complete, evidence-backed, and cleanly consolidated into one namespace. What is broken lives entirely in meta-layer plumbing: doc traceability links, workflow paths, and lint debt. Items 1–3 are small, mechanical, and would return the repository to fully-green CI.
