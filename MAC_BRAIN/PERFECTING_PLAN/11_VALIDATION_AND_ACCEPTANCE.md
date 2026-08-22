# 11 — Validation and Acceptance

## Method (from docs)
Completion needs evidence, not documents. Evidence classes: E0 assertion -> E1 vendor/
standards -> E2 reproducible benchmark -> E3 integration -> E4 physical -> E5 long-
duration. Critical claims may not remain E0. Deterministic CI (reproducible, injected
deterministic backends) is separate from real-model benchmarks.

## Per-step done-bars (summary)
- Step 1: world/context unit + reference-resolution tests; provenance-filtered bounded
  context asserted; full suite green.
- Step 2: admission/write-gate + retrieval-failure-state tests; simulated-episode-cannot-
  be-fact test; suite green.
- Step 3: skill-contract tests; governance guard asserted on every proposed action;
  System-0 safety invariant test; suite green.
- Step 4: (08) P0 acceptance gate green; scenario + adversarial tests; suite green.
- Step 5: NVIDIA experiments produce evidence files (skill contract, reference, demo
  dataset) with evidence-class labels.
- Step 6: cross-system acceptance + closed-loop verify tests; full suite + acceptance
  report; global-completion-gate review.

## Standing gates
- No new phase until the previous step's done-bar is met.
- Any real NVIDIA/model/hardware selection requires: pinned platform tuple + Novi
  benchmark + integration test + ADR. Do not accept by TOPS/demo.
- Neural models only propose; deterministic safety/authorization stays explicit.
- "Document exists" is never completion — every gap maps to an executable check.
- Provenance: claim -> source -> version -> requirement -> benchmark -> decision -> ADR.

