# 06 — Gap Analysis: Cognition

## Docs (03-cognition)
Cognition turns observations/evidence into understanding: world model (entities incl.
Place/Building/Room), situation model, identity & relationships, spatial + causal +
temporal reasoning, prediction, fusion, attention candidates, context construction,
hybrid reasoning (deterministic + retrieval + ML + LLM), structured outputs, epistemic
states (OBSERVED/INFERRED/HYPOTHESIS/PREDICTED/VERIFIED/UNKNOWN), contradiction handling,
silence as a valid output. Cognition > LLM; authoritative state lives outside the model.

## Exists today
- Belief + prediction (cognition.py), situation understanding grounded in KG
  (cognition2.py), temporal/causal (temporal.py), multimodal fusion (fusion.py),
  reflection/self-correction, identity tiers (identity.py), entity KG with
  place/building/room typing (kgraph.py). Local reasoning (reasoning.py) + LLM
  (ollama_reasoning, router, deliberation).

## Delta (what's missing) — the biggest gap for the brain phase
- **A unified world/context model**: a time-aware, uncertainty-aware entity/relation
  graph with epistemic status on every node, snapshots, and contradictions preserved.
  Pieces exist (kgraph, temporal, cognition2) but are not one coherent "current world
  state" the whole brain queries.
- **Context assembler**: bounded, provenance-filtered context for dialogue/reasoning
  (the NVIDIA "Bring me that cup" reference-resolution case). Current dialogue grounding
  is good but not yet driven by a structured context/attention assembler.
- **Situation model**: participants, addressee, activities, risks, uncertainty as a
  derived view.
- **Spatial model**: rooms/floors/doors/zones, reference-frame transforms, metric-vs-
  semantic link, occupancy. Only coarse body pose exists.
- **Attention candidates**: Cognition should emit ranked AttentionCandidates (salience/
  novelty/urgency/social/relevance/uncertainty) for Autonomy to decide.
- **Epistemic discipline end-to-end**: prediction != fact, inference != observation is
  partially handled (reflection, provenance) but not enforced as a typed contract at the
  world-model boundary.
- **Failure-mode runtime**: graceful degradation when a capability is missing/degraded.

## Next action (roadmap Step 1)
- Build a single WorldModel/Context model with typed entities + epistemic status,
  a ContextAssembler, and AttentionCandidate emission. Ground dialogue/reasoning in it.
  This unlocks reference resolution and the NVIDIA skill experiments.

