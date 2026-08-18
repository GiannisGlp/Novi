# Novi — Master Documentation Index & Authority Map

**Date:** 2026-08-18  
**Status:** P0 — documentation control baseline  
**Owner:** `00-strategy`

## Purpose

This document defines how Novi documentation is organized, which document wins when multiple documents discuss the same subject, and where semantic ownership stops at domain boundaries.

Novi already contains substantial architecture material. **This index is a consolidation control document, not a reason to create more architecture documents.** When a concept already has an authoritative owner, new material must be merged into that owner or recorded as an implementation/reference document.

---

# 1. Authority hierarchy

When documents conflict, use this order:

```text
North Star
   ↓
Project strategy
   ↓
System architecture
   ↓
Domain architecture
   ↓
Detailed subsystem specification
   ↓
ADR / adopted technology decision
   ↓
Implementation specification
   ↓
Validation evidence
```

A validation result can invalidate an implementation assumption and trigger a new ADR, but it does not silently rewrite architecture.

---

# 2. Canonical domain ownership

## Strategy — `00-strategy/`

Owns:

- product North Star;
- permanent architectural principles;
- development strategy and sequencing;
- readiness gates;
- master data/artifact planning.

**North Star authority:** `NOVI_NORTH_STAR.md`.

There must be exactly one Novi North Star. Brain documents may define runtime contracts derived from it but must not redefine the product North Star.

## System architecture — `01-system-architecture/`

Owns:

- system boundaries;
- dependency direction;
- runtime profiles;
- durable state;
- event semantics;
- concurrency;
- recovery;
- privacy/security cross-cutting requirements;
- architecture governance;
- technology/solution selection policy;
- cross-domain contracts.

`16_SOLUTION_SELECTION_POLICY.md` is the canonical project-wide solution-selection policy. It is not an Autonomy responsibility.

## Brain — `02-novi-brain/`

Owns the **embodied brain runtime and integration layer**:

- brain lifecycle;
- cognitive-cycle execution/orchestration;
- model execution infrastructure;
- perception runtime/pipelines;
- embodied state integration;
- runtime synchronization and health;
- interfaces between cognition, memory, autonomy, policy and hardware;
- runtime degradation/fallback/resource coordination;
- speech/audio/vision execution infrastructure.

Brain does **not** own semantic cognition, long-term memory/knowledge, behavioral goal authority, safety authority or motor-control authority.

Canonical boundary statement: `docs/02-novi-brain/00_BRAIN_ARCHITECTURE_README.md`.

## Autonomy — `02-autonomy/`

Owns:

- continuous autonomous behavior;
- attention as a behavioral/resource policy;
- goals and goal lifecycle;
- planning and task selection;
- curiosity/proactive behavior policy;
- skill selection/execution coordination;
- action proposals and behavioral state;
- autonomy-specific safety boundaries;
- autonomy testing and observability.

Autonomy owns the behavioral loop. Brain executes/orchestrates the runtime mechanisms used by that loop.

## Cognition — `03-cognition/`

Owns the semantic intelligence of Novi:

- cognitive architecture;
- world-model semantics;
- situation/context interpretation;
- multimodal interpretation;
- reasoning;
- uncertainty;
- identity/person semantics;
- social cognition;
- temporal/causal reasoning;
- semantic spatial reasoning;
- prediction;
- personality/affect;
- cognitive model routing/selection;
- cognitive data/API contracts;
- cognitive failure modes and tests.

## Memory and knowledge — `04-memory-and-knowledge/`

Owns:

- memory taxonomy;
- admission/lifecycle;
- provenance;
- retrieval;
- knowledge graph;
- identity/entity resolution;
- temporal/spatial historical memory;
- causal memory;
- cross-modal memory;
- skills/competence evidence;
- schema evolution;
- memory governance and human oversight.

The `archive/` tree is historical/reference material and does not override consolidated current documents without an explicit migration decision.

## Hardware — `05-hardware/`

Owns physical-system requirements and hardware selection. Current master selection baseline is `26_HARDWARE_SELECTION_AND_BOM_BASELINE.md` until detailed specifications are decomposed into their own authoritative files.

---

# 3. Boundary model

The same real-world concept may legitimately appear in multiple domains **only when each occurrence has a different responsibility**. Repetition of a concept is acceptable at an interface; competing definitions are not.

| Concept | Canonical owner | Other domains may describe |
|---|---|---|
| North Star | Strategy | derived behavioral/runtime implications |
| Cognitive semantics | Cognition | Brain execution path |
| Continuous behavior loop | Autonomy | Brain scheduling/execution |
| World Model | Cognition | Brain transport/runtime state |
| Situation Model | Cognition | Autonomy consumption |
| Current physical self/runtime state | Brain + authoritative telemetry | Cognition semantic self-model; Memory history; Autonomy task state |
| Historical memory/knowledge | Memory | Cognition retrieval/use |
| Temporal/causal reasoning | Cognition | System clock/timestamps; Memory historical records |
| Semantic spatial reasoning | Cognition | Brain localization/runtime; Memory spatial history |
| Model/cognitive selection | Cognition | Brain model execution/runtime |
| Technology selection | System Architecture | domains provide requirements and benchmarks |
| Physical control | Hardware/controllers | Brain/Autonomy submit bounded requests |

**Rule:** an interface description is not a second semantic authority.

---

# 4. Consolidation rules for existing Brain documents

The following documents were created before the cross-domain ownership boundary was fully consolidated:

```text
02-novi-brain/01_BRAIN_NORTH_STAR_AND_BEHAVIORAL_CONTRACT.md
02-novi-brain/02_COGNITIVE_ARCHITECTURE.md
02-novi-brain/05_COGNITIVE_CYCLE.md
02-novi-brain/18_WORLD_MODEL.md
02-novi-brain/19_SPATIAL_COGNITION.md
02-novi-brain/20_TEMPORAL_COGNITION.md
02-novi-brain/21_SITUATION_MODEL.md
02-novi-brain/22_SELF_MODEL.md
```

These must **not** be treated as competing semantic authorities.

Consolidation policy:

1. preserve unique runtime/integration information in the canonical Brain documents;
2. move semantic definitions to their canonical Cognition/Autonomy/Memory owners;
3. mark documents that retain only boundary/reference material as `SUPERSEDED / BOUNDARY REFERENCE`;
4. remove stale cross-references after migration;
5. do not create replacement duplicates merely to preserve the old document names.

The existing Brain boundary audit is the migration guide.

---

# 5. Model routing boundary

Model selection is deliberately split:

```text
COGNITION
Which capability/model is appropriate for this cognitive task?
              ↓
BRAIN RUNTIME
Where and how does the selected model execute?
              ↓
HARDWARE
What physical compute/resources execute it?
```

This is a boundary, not duplicated ownership.

---

# 6. Technology and research authority

`TECHNOLOGY_REFERENCE.md` is a candidate ecosystem/reference catalog.

`TECHNOLOGY_STACK_BASELINE.md` is the implementation-oriented proposed stack.

`01-system-architecture/16_SOLUTION_SELECTION_POLICY.md` defines the evaluation process.

ADRs record actual adoption decisions.

```text
Technology Reference
      ↓
Stack Baseline
      ↓
Requirement
      ↓
Benchmark / evaluation
      ↓
ADR
      ↓
Adopted implementation
```

The NVIDIA research documents in the Library are research inputs. They are not project architecture authority and do not automatically approve NVIDIA technology.

---

# 7. No-new-domain rule

The long-term domain list is a planning aid, not a requirement to create 26 directories immediately.

A new domain/document is justified only when all of the following are true:

1. the responsibility cannot remain coherent inside an existing canonical domain;
2. it has an independent lifecycle and architecture boundary;
3. it has distinct interfaces/contracts;
4. the split reduces ambiguity rather than creating another authority;
5. the existing domain cannot reasonably own it.

**Do not create a new document simply because a topic is important.** Important topics belong in the correct existing authority unless the boundary itself requires decomposition.

---

# 8. Document lifecycle

```text
DRAFT
 ↓
REVIEW
 ↓
PROPOSED
 ↓
APPROVED
 ↓
AUTHORITATIVE
 ↓
SUPERSEDED / DEPRECATED
```

`ARCHIVED` means historical/reference material. It must not silently override a current authoritative document.

Every authoritative document should state:

- status;
- date;
- owner/domain;
- scope;
- dependencies;
- supersedes/superseded-by if applicable;
- related ADRs;
- validation status.

---

# 9. Documentation freeze and consolidation gate

Until the current architecture is consolidated:

- [ ] no new semantic architecture documents are created for already-owned concepts;
- [ ] duplicate Brain semantic documents are migrated or marked boundary-only;
- [ ] cross-domain ownership is explicit;
- [ ] technology selection has one canonical policy;
- [ ] stale references to superseded authorities are removed;
- [ ] every P0 capability has exactly one semantic owner;
- [ ] major interfaces are defined;
- [ ] technology choices have ADR/evaluation status;
- [ ] hardware capability requirements exist;
- [ ] safety requirements exist;
- [ ] simulation/data/model/validation requirements exist;
- [ ] no implementation plan depends on an undocumented assumption.

Only after this gate passes should new architectural domains be considered.

---

# 10. Final rule

> **If we cannot point to the one document that owns a concept, and separately identify the documents that merely consume, execute, observe or validate it, the architecture is not consolidated.**

> **Do not solve documentation duplication by creating another document. Solve it by assigning authority, merging unique information, and superseding the duplicate.**
