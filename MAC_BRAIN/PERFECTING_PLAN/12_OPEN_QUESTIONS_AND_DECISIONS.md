# 12 — Open Questions and Decisions

Items that need a human/ADR call before or during the steps (not blocking Step 0/1).

## Scope
- Confirm the brain-phase boundary: keep real-model selection (B2.9), hardware, and
  ROS2/Isaac entirely out of the brain-phase core (recommended) vs start thin seams now.
- Confirm acceptance priority: world/context first (Step 1) vs memory hardening first.
  Recommendation: Step 1 (cognition) first — it unlocks the most (dialogue grounding,
  reference resolution, skill experiments).

## Autonomy / safety
- What is the minimum governance/authorization guard for the brain phase (deterministic
  only, or a GovernanceRequest/Decision contract between proposal and execution)?
  Docs require the latter for safety. Recommend the contract guard in Step 3.

## Memory
- Which memory classes to fully implement now vs. defer (procedural, prospective,
  metamemory, autobiographical continuity are heavy). Recommend implementing the
  MemoryRecord contract + write gate + retrieval states first; add classes incrementally.

## NVIDIA / models
- Which local LLM/embedding providers to standardize behind the model runtime
  (Ollama is the current default). Confirm the embedding provider.
- Whether to stand up the NoviEpisode schema + adapters now (recommend yes, Step 5) so
  future Isaac/GR00T data stays portable.

## Doc / ownership
- Confirm the legacy docs (docs/02-novi-brain 01,02,05,18-22) stay SUPERSEDED; avoid
  creating competing docs (freeze rule).
- Confirm that PERFECTING_PLAN is a plan only and that implementation decisions still go
  through ADR/validation.

## Next human decision
Review 10_ROADMAP (Step 0-6) and 11_VALIDATION; confirm scope + Step order, then we
proceed to Step 1 implementation on the next round.

