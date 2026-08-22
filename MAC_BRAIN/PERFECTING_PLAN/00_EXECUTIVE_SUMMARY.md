# 00 — Executive Summary

## Verdict

Novi's brain phase is **far along but not complete**. The architecture, contracts,
autonomy loop, brain orchestrator, deterministic cognition, memory/knowledge kernel,
soul layer and the NVIDIA research are all real and substantial. The remaining work is
not "start over" — it is **closing defined gaps** in the order the docs already dictate.

## What is strong today
- **Authority + portability**: canonical owners exist per domain; "mind before body",
  vendor-neutral contracts, evidence-before-knowledge are baked into the docs and mostly
  into the code (MAC_BRAIN, contracts/).
- **Autonomy loop**: continuous, prompt-independent sensing→world→cognition→reason→act→
  reflect→consolidate is implemented (MAC_BRAIN runtime, brain/b1_*).
- **Brain coordination**: BrainSupervisor lifecycle, health/observability, B2 specialist
  model runtime behind Protocol boundaries (brain/b2_*, MAC_BRAIN/models/*).
- **Memory & knowledge**: storage, consolidation, knowledge graph, temporal, vector,
  identity, privacy all exist as real modules.
- **Soul**: identity/self-model, personality/affect/values, social relationships,
  dialogue (natural, non-assistant), social initiative, lexicon.
- **NVIDIA research**: a faithful research dossier + strategy that treats NVIDIA as
  acceleration/simulation only, never semantics.
- **Tests**: a broad green suite across brain/, MAC_BRAIN/, web/, contracts/.

## The core gap (the theme across every domain)
The docs are **canonical specification**, but several are ahead of the implementation
in fidelity. Specifically the brain phase has not yet delivered:

1. **Faithful MemoryRecord / provenance contract** — the code has memory classes and
   storage but the full contract (epistemic status, verification_state, independence
   groups, contextual trust, retrieval failure states, write gate, schema evolution,
   governance interface) is not fully realised.
2. **A full world/situation model** — world-state graph with entity types
   (Person/Place/Building/Room/Object), spatial + causal + temporal reasoning, beliefs
   with epistemic status, contradiction handling, and a **context assembler** that
   grounds dialogue/reasoning in the world (the NVIDIA "Bring me that cup" case).
3. **Recognition as real capability** — place/building typing exists, but voice/face
   recognition are provider boundaries with deterministic stubs; real models are
   deferred by policy (correct), so the wiring is the deliverable now.
4. **Skill/action contract + governance/authorization at the action boundary** —
   skills and the Safety/Authorization boundary exist partially; the full
   skill-contract (preconditions/success/failure/recovery) and governance interface are
   not complete.
5. **Soul acceptance (08)** and **Memory audit (18)** — the P0 behavioral/acceptance
   suites and cross-system boundary tests are specified but not yet executable.

## Recommended next move (see 10_ROADMAP)
Proceed in **dependency order**, not by enthusiasm:
- **Step 0** — freeze scope: agree the six-domain delta list and the acceptance bar
  (this plan).
- **Step 1** — close the **cognition world/situation + context** gap (biggest leverage,
  unlocks dialogue grounding, reference resolution, and the NVIDIA skill experiments).
- **Step 2** — mature **memory/knowledge** to the canonical MemoryRecord/provenance
  contract.
- **Step 3** — complete the **skill contract + governance** boundary.
- **Step 4** — turn the **soul** dialogue/social layer into contract-compliant,
  scenario-accepted behavior.
- **Step 5** — the **NVIDIA experiments** (skill contract, context-aware reference)
  that validate the architecture without hardware.
- **Step 6** — closed-loop validation and the acceptance gate.

Each step has an explicit done-bar (11_VALIDATION_AND_ACCEPTANCE.md).
