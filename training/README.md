# Novi — Learning & Training Workspace

Implements `docs/plans/01_BRAIN/23_NOVI_LEARNING_AND_TRAINING_PLAN.md`.

This directory is the **data + model layer** for improving *how Novi behaves and
communicates*. It is deliberately separated from the deterministic brain
(`novi/brain/`): the brain stores what Novi *currently knows* (world model,
memory, identity); this workspace produces the *learned behavior* (verbalization,
dialogue policy, retrieval/grounding ranking) that the brain may consult —
always behind deterministic guardrails.

## Core decision (plan §0)

| Layer | Owns | Train? |
|---|---|---|
| Deterministic brain (`novi/brain/`) | perception, identity, world model, memory, safety/governance, current state | **No** |
| Learned layer (this workspace) | dialogue policy, retrieval ranking, grounding ranking, natural language realization, interaction preferences | **Yes** |
| Model | Qwen-based local model + Novi adapter | LoRA/QLoRA only |

Never train live facts ("Vano is here", "the mug is on the desk") into weights.
Those belong in the world model and memory store.

## Repository reconciliation (plan §4 + §41 — audit before creating)

Plan §4 proposed a `training/` tree; §41 required reconciling against the
current repository to avoid duplicate structures. Audit result (2026-08-30):

| Capability | Where it lives today | Disposition |
|---|---|---|
| Decision traces (plan §6.1 fields) | `novi/brain/decision_trace.py` (`DecisionTrace`/`TraceRecorder`, plan 22 Phase 23) | **Reuse** — exporter here consumes it |
| Interaction outcomes + corrections | `novi/brain/interaction_outcome.py` (`InteractionOutcome`, plan 22 Phase 18) | **Reuse** — exporter consumes it |
| Deterministic dialogue policy (act set) | `novi/brain/dialogue_policy.py` (`DialoguePolicy`, acts incl. SILENCE/RESPOND/CLARIFY/CONTINUE/GREETING/…) | **Reuse** — learned scorer ranks candidates behind it |
| Composite retrieval scoring | `novi/brain/retrieval_policy.py` (plan 22 Phase 5; 11 weighted signals + penalties) | **Reuse** — learned reranker augments it |
| Privacy classification / retention / erasure | `novi/brain/privacy.py` (privacy classes, purpose binding, ERASE w/ propagation) | **Reuse** — sanitizer delegates to it |
| Performance baselines | `benchmarks/` (model profiles, gate runner, learning bench) | **Keep separate** — behavioral evaluation lives here |
| Runtime SQLite store | `novi/data/` (runtime artifact, gitignored) | **Not a dataset dir** — training data lives here |
| Tests | colocated per package (`novi/brain/tests/`, `novi/web/tests/`, …) | **Follow convention** — `training/tests/` |

The plan's `novi/brain/language/`, `novi/brain/interaction/`, `novi/brain/memory/`
targets are **not** created literally: the corresponding capabilities already
exist as `verbalizer.py`/`dialogue.py`, `dialogue_policy.py`/`interaction_outcome.py`,
`retrieval_policy.py`. New learned components live here under `integration/` and
are wired into the brain at the same points plan 22 established.

## Directory map

```text
training/
├── configs/          committed, deterministic training configurations (plan §31)
├── datasets/         raw/ cleaned/ curated/ sft/ dpo/ retrieval/ grounding/ evaluation/ (dirs created on demand)
├── collection/       trace export → sanitize → validate → dedup → annotate
├── training/         train_sft / train_dpo / train_retriever / train_policy / evaluate
├── models/           adapter registry + manifests + rollback
├── integration/      learned components behind deterministic guardrails
├── evaluation/       30-scenario behavioral benchmark + metrics + shadow comparison
└── tests/            colocated tests (TDD)
```

## Ground rules

- **Deterministic in CI**: every pipeline runs without hardware/models in a
  smoke mode; real training is opt-in and framework-adaptive (see `training/`).
- **Privacy first**: raw traces are never exported verbatim; `sanitizer.py`
  applies redaction, abstract person IDs (`person:owner_001`) and retention
  before anything becomes a dataset (plan §7–§8).
- **Quality gates**: no example enters `curated/` without passing
  `validator.py`; no model is registered without a manifest and an evaluation
  report; no checkpoint is ever deployed unnamed (plan §22, §39).
- **No automatic learning from raw experience**: the improvement loop is
  human-reviewed curation → training → evaluation → shadow → registry →
  controlled deployment (plan §18/§24).
