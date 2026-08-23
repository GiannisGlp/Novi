# 07 — Gap Analysis: Memory & Knowledge

## Docs: 04-memory-and-knowledge (canonical 01-18)
- MemoryRecord contract (memory_id, type, subject/evidence refs, provenance, epistemic
  status, confidence, verification_state, temporal/spatial scope, privacy, retention,
  derivation, lifecycle, version, integrity).
- Memory classes: working, session, episodic, semantic, procedural, prospective,
  relationship, spatial, temporal, preference, operational, metamemory.
- Write gate + admission decision + lifecycle/failure states; idempotency; supersession;
  dependency-aware retention/erasure.
- Provenance/trust: contextual trust(source, claim, context, time, consequence);
  confidence != verification; independence groups (common source != corroboration).
- Consolidation: promotion episode -> knowledge only on repeated + independent evidence;
  retrieval failure states (NO_RESULT/LOW_CONFIDENCE/AMBIGUOUS/CONFLICTED/STALE/
  UNAUTHORIZED/DEGRADED/ABSTAIN); candidate_k > final_k.
- Knowledge graph: belief revision (SUPPORTS/REFINES/QUALIFIES/CONTRADICTS/SUPERSEDES/
  INVALIDATES), rebuildable from evidence+claims+revision.
- Entity resolution pipeline (must allow UNKNOWN/AMBIGUOUS); cross-modal identity.
- Schema evolution L0-L6; model/memory co-evolution; governance (GovernanceRequest/
  Decision, ALLOW/DENY/RESTRICT/REQUIRE_HUMAN/ESCALATE); human oversight review machine;
  privacy lifecycle. Memory never mutates schema; memory never authorizes.

## Exists today
- Durable SQLite store, consolidation/decay/archival, vector recall, privacy/governance,
  knowledge graph with belief revision, temporal primitives, narrative/summary, identity
  tiers + cross-modal (voice/face) seams, skill objects partially.

## Delta (what's missing)
- **Faithful MemoryRecord contract**: full field set + epistemic/verification state +
  enforcement at admission is not complete (records exist but not all carry the contract).
- **Write gate + admission pipeline** (identity -> integrity -> privacy -> instruction/
  data separation -> poisoning -> retention -> policy) not a single enforced gate.
- **Retrieval failure states** (NO_RESULT/AMBIGUOUS/CONFLICTED/STALE/ABSTAIN) not fully
  surfaced to callers.
- **Contextual trust + independence groups** (two observations from one source are not
  independent) not modelled.
- **Procedural/skill memory, prospective/intention memory, metamemory, episodic
  autobiographical continuity** largely absent.
- **Machine-governance engine + human-oversight review machine** are contract-only.
- **Cross-modal identity assurance** (UNKNOWN/AMBIGUOUS states) partially done.

## Next action (roadmap Step 2)
- Harden storage/admission/retrieval to the canonical MemoryRecord contract with typed
  epistemic/verification state, failure states, and contextual trust. Add governance/
  oversight interfaces behind contracts. Do not chase every memory class at once.

