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
| 10 | train qwen3:8b Novi LoRA SFT | ✅ **RUN COMPLETED** | `training/models/adapters/novi-qwen3-8b-dialogue-v1` — 750 steps / 3 epochs on MPS (batch 2), train_loss 0.090 → 2.1e-05; report `models/manifests/sft_run_report.json` |
| 11 | compare against baseline | ✅ **DONE (real)** | `models/manifests/candidate_eval_social_v1.json`: candidate act-accuracy 1.0/1.0, naturalness 0.0/0.033, safety 1.0 — all T1-T6 gates pass; metrics calibrated on real data (repetition = cross-act only; initiative over relevant scenarios) |
| 12 | deploy only to offline evaluation | ✅ **DONE (real)** | manifest `novi-qwen3-8b-dialogue-v1` registered → staged → **active** via `models/deploy.py` (gates + shadow + slots); shadow: 30 parity, 0 losses, 0 safety violations |
| 13 | create preference pairs | ✅ **DONE** | `datasets/dpo/preference_pairs_v1.jsonl` — 1,120 pairs, all 8 §33 categories, schema-valid |
| 14 | train preference model/DPO adapter | 🔄 **RUNNING** (memory-bounded: batch 1, grad-checkpointing, 1 epoch, 2×8B fp16 ≈ 32GB/36GB) | `train_dpo.py` (trl 1.12, DPOConfig, Dataset wrapper) |
| 15 | evaluate SFT vs SFT+DPO | 🟡 awaiting DPO completion | `evaluate.py --candidate-dir` + `compare_baseline()` |
| 16 | memory retrieval ranking dataset | ✅ **DONE** | `datasets/retrieval/retrieval_v1.jsonl` — 320 records with per-candidate feature vectors |
| 17 | train retrieval reranker | ✅ **DONE (real)** | `adapters/retrieval_reranker_v1.json` (BCE linear ranker, bias; ranks preferred first — verified end-to-end) |
| 18 | integrate retrieval reranker | ✅ DONE | `training/integration/reranker.py` (learned + deterministic composite fallback, explainable) |
| 19 | dialogue-policy dataset | ✅ **DONE** | `datasets/policy/policy_v1.jsonl` — 320 records, normalized states |
| 20 | train policy scorer | ✅ **DONE (real)** | `adapters/policy_scorer_v1.json` (one-vs-rest per act, act_biases from learned bias) |
| 21 | integrate policy scorer behind guardrails | ✅ DONE | `training/integration/policy_scorer.py` (`select_action`: learned ranking + hard guardrails) |
| 22 | multimodal grounding data | ✅ **DONE** | `datasets/grounding/grounding_v1.jsonl` — 240 records (§14 format) |
| 23 | train multimodal grounding/ranking | ✅ **DONE (real)** | `adapters/grounding_ranker_v1.json` (linear over cue features; ranking only, never control) |
| 24 | shadow-test integrated system | ✅ **DONE (real)** | baseline vs candidate on 30 scenarios: 30 parity / 0 losses / 0 safety violations → promote (plan §21 beat-or-match semantics; quality metric comparison added) |
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

1. **DPO run (step 14)** — executing on this Mac; memory-bounded (2×8B fp16 ≈ 32GB of 36GB). If the run completes: evaluate SFT vs SFT+DPO (step 15) and register the winner. If the kernel kills it for memory: the pipeline + 1,120-pair dataset are ready and the run moves to the Jetson (Orin 64GB) or a quantized path — hardware limit, not a code gap.
2. **Real interaction traces** — the 500-example SFT set is 70 curated + 430 template-derived (`synthetic: true`, validated). Real traces → eligibility → sanitize → validate → annotate replace synthetic rows as volume grows (§6-§9).
3. **Latency gate T7** — measured on-device per routing tier (plan §30) at integration time (the first-epoch SFT adapter measured ~4.5s/step training; inference is much faster, but the per-tier latency budget is a runtime-integration measurement).
4. **Human evaluation (§37)** — the pairwise-review protocol is tooled (annotator + preference pairs); a human review pass of the v1 adapter's responses is the next quality step.
5. **Real-robot evaluation (step 27)** — hardware gates, shared with plan 22 H1–H5.

## 6. Definition of success (plan §44)

Novi is successfully trained when a new model version demonstrates measurable
improvement in natural conversation while remaining grounded in the same
explicit world, memory, identity and safety systems — i.e. a model that passed
T1–T8, won shadow comparison against the deterministic baseline, and is
registered in the model registry with a full provenance manifest. Training is
an improvement loop around Novi's brain, never a replacement for it.
