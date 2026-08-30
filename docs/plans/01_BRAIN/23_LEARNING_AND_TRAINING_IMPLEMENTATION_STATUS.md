# Plan 23 — Learning & Training: Implementation Status

**Plan:** `23_NOVI_LEARNING_AND_TRAINING_PLAN.md`
**This document:** step-by-step implementation status for the whole plan.
**Date:** 2026-08-30
**Status:** Steps 01–09, 16, 18–21 (integration), 24–26, 29 **IMPLEMENTED** (deterministic, tested) — training *runs* (steps 10–15, 17, 20, 22–23) **PENDING** curated dataset volume + framework install.

---

## 0. Repository reconciliation (plan §4/§41 — audit before creating)

The plan's proposed `training/` tree was reconciled against the existing
repository before creation. Result (full table in `training/README.md`):

| Plan §41 target | Disposition |
|---|---|
| `training/` (configs, datasets, collection, training, models) | **Created** — new capability, no duplicate existed |
| `novi/brain/language/`, `interaction/`, `memory/` | **NOT created** — capabilities already exist (`verbalizer.py`/`dialogue.py`, `dialogue_policy.py`/`interaction_outcome.py`, `retrieval_policy.py`); learned components live in `training/integration/` and wire into those points |
| `novi/tests/training`, `novi/tests/evaluation` | **NOT created** — repo convention is colocated tests (`training/tests/`, added to pytest `testpaths`) |
| decision traces (plan §6.1) | **Reused** — `novi/brain/decision_trace.py` (plan 22 Phase 23); exporter consumes it |
| privacy (plan §7) | **Reused** — `novi/brain/privacy.py` classes/lexicon; sanitizer adds training-corpus governance |
| `benchmarks/` | **Kept separate** — performance baselines; behavioral eval lives in `training/evaluation/` |

---

## 1. Implementation sequence status (plan §40)

| # | Step | Status | Where |
|---|---|---|---|
| 01 | audit existing training/data infrastructure | ✅ DONE | `training/README.md` (reconciliation table) |
| 02 | define training schemas | ✅ DONE | `training/schemas.py` (canonical §5, annotation §9, policy §12, retrieval §13, grounding §14, preference §11, schema versions §29) |
| 03 | structured interaction trace export | ✅ DONE | `training/collection/trace_exporter.py` (consumes `DecisionTrace`, eligibility filter §6.2) |
| 04 | privacy/redaction pipeline | ✅ DONE | `training/collection/sanitizer.py` (consent, retention, PII redaction, biometric separation, abstract person ids, dataset purge §7) |
| 05 | dataset validation | ✅ DONE | `training/collection/validator.py` (all §8 reject rules + quality scoring + pipeline orchestrator) |
| 06 | dataset deduplication | ✅ DONE | `training/collection/deduplicator.py` (exact/near-dup + contradiction detection) |
| 07 | human annotation workflow | ✅ DONE | `training/collection/annotator.py` (fields §9, quorum, consensus, inter-annotator agreement) |
| 08 | initial curated dialogue dataset | ✅ DONE (seed) | `training/datasets/curated/seed_dialogue_v1.jsonl` — 70 examples, all 9 SFT task types, deterministic generator `build_seed.py` (byte-reproducible, hash-pinned) |
| 09 | baseline evaluation suite | ✅ DONE | `training/evaluation/` — 30 scenarios (§20), metrics (§19), benchmark runner, baseline report committed (`models/manifests/baseline_metrics_social_v1.json`: 30/30, safety 1.0) |
| 10 | train qwen3:8b Novi LoRA SFT | 🟡 PIPELINE READY, run pending | `training/training/train_sft.py` + backends (`mlx_sft.py`, `torch_sft.py`); smoke mode tested; needs ≥200 curated examples (have 70) + `mlx-lm` or `peft` |
| 11 | compare against baseline | ✅ TOOLING | `evaluate.py --candidate-dir` / `compare_baseline()` / shadow runner |
| 12 | deploy only to offline evaluation | ✅ (policy) | status lifecycle `candidate→staged→active` (§22) |
| 13 | create preference pairs | 🟡 schema+smoke ready | `train_dpo.py` (pairs dataset not yet collected) |
| 14 | train preference model/DPO adapter | 🟡 pipeline ready | `train_dpo.py` (trl backend) |
| 15 | evaluate SFT vs SFT+DPO | ✅ TOOLING | `evaluate.py`, `compare_baseline()` |
| 16 | memory retrieval ranking dataset | 🟡 schema+smoke ready | `retrieval` kind in `schemas.py`, `train_retriever.py` |
| 17 | train retrieval reranker | ✅ (real torch path) | `training/training/backends/torch_linear.py` — linear ranker trains now on MPS/CPU when dataset exists |
| 18 | integrate retrieval reranker | ✅ DONE | `training/integration/reranker.py` (learned + deterministic composite fallback, explainable) |
| 19 | dialogue-policy dataset | 🟡 schema+smoke ready | `policy` kind in `schemas.py`, `train_policy.py` |
| 20 | train policy scorer | ✅ (real torch path) | one-vs-rest linear per act; artifact consumed by scorer |
| 21 | integrate policy scorer behind guardrails | ✅ DONE | `training/integration/policy_scorer.py` (`select_action`: learned ranking + hard guardrails: user-busy silence, WARN-without-evidence downgrade, proactive cooldown) |
| 22 | multimodal grounding data | 🟡 schema ready | `grounding` kind in `schemas.py`; gated on stable perception→world pipeline (plan §15) |
| 23 | train multimodal grounding/ranking | 🟡 pipeline ready | `grounding.yaml` + linear backend |
| 24 | shadow-test integrated system | ✅ DONE | `training/evaluation/shadow.py` (wins/losses/parity, safety violations, `should_promote`) |
| 25 | add model registry | ✅ DONE | `training/models/registry.py` (named manifests enforced, lifecycle, schema compat §29) |
| 26 | add rollback | ✅ DONE | `training/models/rollback.py` (current/previous/known-good slots, §23 triggers) |
| 27 | run real-robot evaluation | ⏳ PENDING | hardware/robot gates (same status as plan 22 H1–H5) |
| 28 | collect new traces | ✅ (mechanism) | exporter + eligibility + sanitizer wired; volume grows with real use |
| 29 | repeat controlled improvement cycle | ✅ (loop defined) | plan §18/§24 loop encoded in pipeline + gates + shadow + registry |

---

## 2. Gates (plan §39)

| Gate | Status |
|---|---|
| T1 naturalness | ✅ baseline recorded (0.0 assistant/repetition rates); candidate comparison enforced by `evaluate.py` |
| T2 grounding | ✅ baseline recorded; `false_grounding_rate` gate |
| T3 memory | ✅ baseline recorded; precision/recall gate |
| T4 initiative | ✅ baseline recorded; `appropriate_initiative_rate` gate |
| T5 silence | ✅ silence scenarios (16/21/29) in catalog; silence rate tracked |
| T6 safety | ✅ floor 0.995 enforced (baseline: 1.0) |
| T7 latency | 🟡 measured on-device per routing tier (plan §30) at experiment time |
| T8 regression | ✅ full suite run in progress — 191 new `training/tests` green; brain suite re-run (see below) |

## 3. Hardware/framework audit (plan §31)

| Component | Audit result (2026-08-30) |
|---|---|
| Host | macOS, 36 GB unified memory, disk ~101 Gi free |
| torch | 2.13.0, **MPS available** |
| transformers | ✅ installed |
| peft / mlx-lm / trl / datasets | ❌ not installed (Python 3.14 venv; mlx has no 3.14 wheels) |
| Conclusion | LoRA SFT feasible on this Mac (torch+peft or a 3.11/3.12 venv with mlx-lm); real runs start once curated data reaches target (500–2,000, plan §32) |

## 4. Configs (committed, deterministic — plan §31)

`training/configs/`: `sft.yaml` (qwen3:8b, LoRA r=16, seed 20260830, min 200 examples),
`dpo.yaml` (beta 0.1, min 1,000 pairs), `retrieval.yaml`, `grounding.yaml`,
`evaluation.yaml` (T1–T8 gates). Every run records provenance: base model,
training commit, dataset version, hyperparameters, hardware, seed, framework
(`training/config.py::capture_provenance`).

## 5. Pending items (explicit, honest)

1. **Curated dataset volume** — 70 seed examples; first SFT needs ≥200 (§32 target 500–2,000). Grows via real interaction traces → eligibility → sanitize → validate → annotate.
2. **Framework install** — `pip install peft` (torch path) or `mlx-lm` in a 3.11/3.12 venv.
3. **Preference/retrieval/policy/grounding datasets** — schema + training paths exist; examples come from real traces/annotations.
4. **Real-robot evaluation (step 27)** — hardware gates, shared with plan 22 H1–H5.
5. **Candidate adapter inference** — `evaluate.py --candidate-dir` loading is wired at experiment time when the first adapter exists (until then `--replay` scores offline).

## 6. Definition of success (plan §44)

Novi is successfully trained when a new model version demonstrates measurable
improvement in natural conversation while remaining grounded in the same
explicit world, memory, identity and safety systems — i.e. a model that passed
T1–T8, won shadow comparison against the deterministic baseline, and is
registered in the model registry with a full provenance manifest. Training is
an improvement loop around Novi's brain, never a replacement for it.
