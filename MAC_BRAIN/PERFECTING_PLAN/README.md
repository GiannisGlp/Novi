# NOVI — Perfecting Plan (Brain Phase)

**Type:** Analysis + roadmap (no code in this directory).
**Status:** Living plan — findings and the step-by-step roadmap for perfecting Novi's
brain-phase implementation, derived from a full audit of `docs/` (including the
NVIDIA robot-learning research) against the current codebase.

## Why this directory exists

You asked for a full analysis of `docs/` (including
`NOVI_NVIDIA_ROBOT_LEARNING_COGNITION_AUTONOMY_RESEARCH.md`), a comparison against
what is already implemented, the gaps, and a **plan** (not code) to perfect the brain
phase. The mind must follow the canonical authorities: **system architecture,
autonomy, brain, cognition, memory & knowledge, soul** — with NVIDIA treated as
acceleration/simulation only, never as Novi's semantics.

## How this directory is organised (by step)

- `00_EXECUTIVE_SUMMARY.md` — one-page verdict: what is done, the core gap, the
  recommended next move.
- `01_PHASE_OVERVIEW_AND_PRINCIPLES.md` — authority hierarchy, "mind before body",
  brain-phase scope, evidence classes, and the portability rule.
- `02_WHAT_IS_ALREADY_IMPLEMENTED.md` — evidence-driven map of code to docs.
- `03_GAP_ANALYSIS_SYSTEM_ARCHITECTURE.md`
- `04_GAP_ANALYSIS_AUTONOMY.md`
- `05_GAP_ANALYSIS_BRAIN.md`
- `06_GAP_ANALYSIS_COGNITION.md`
- `07_GAP_ANALYSIS_MEMORY_AND_KNOWLEDGE.md`
- `08_GAP_ANALYSIS_SOUL.md`
- `09_GAP_ANALYSIS_NVIDIA_INTEGRATION.md`
- `10_ROADMAP_BY_STEP.md` — the ordered, dependency-aware plan.
- `11_VALIDATION_AND_ACCEPTANCE.md` — how each step is proven done.
- `12_OPEN_QUESTIONS_AND_DECISIONS.md` — items that need a human/ADR call.

Each gap file states: (a) what the docs mandate, (b) what exists today, (c) the delta,
(d) the concrete next action. The roadmap file is the single place to start.

> Principle: `main` is canonical; this plan only proposes changes. Nothing here is
> implementation; implementation decisions still flow through the project ADR/validation
> process.

