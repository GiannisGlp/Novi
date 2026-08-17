# Novi — Master Documentation Index & Authority Map

**Date:** 2026-08-17  
**Status:** P0 documentation control baseline

## Purpose

This document defines how Novi documentation is organized and which document wins when multiple documents discuss the same subject.

Novi currently has a substantial amount of architecture material. Without an authority map, the project risks implementing contradictory assumptions from different documents.

---

# 1. Authority hierarchy

When documents conflict, use this order:

```text
North Star
   ↓
Project-level strategy
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

# 2. Strategy authority

## `00-strategy/NOVI_NORTH_STAR.md`

Defines:

- ultimate product goal;
- meaning of the brain;
- required cognitive properties;
- success criteria;
- permanent architectural principles.

## `00-strategy/NOVI_DEVELOPMENT_STRATEGY_AND_IMPLEMENTATION_PLAN.md`

Defines:

- staged implementation approach;
- hybrid AI strategy;
- mind-before-body strategy;
- technology-selection philosophy;
- development sequence.

## `00-strategy/NOVI_PRE_IMPLEMENTATION_READINESS_AUDIT.md`

Defines:

- current readiness;
- discovered gaps;
- P0 decisions;
- implementation gate.

## `00-strategy/NOVI_DATA_AND_ARTIFACTS_MASTER_CATALOG.md`

Defines:

- required data;
- datasets;
- schemas;
- models;
- simulation assets;
- deployment artifacts;
- validation evidence.

---

# 3. System architecture authority

`01-system-architecture/` is authoritative for:

- system boundaries;
- dependency direction;
- runtime profiles;
- durable state;
- event semantics;
- concurrency;
- recovery;
- privacy;
- cross-cutting requirements.

The domain README explicitly states that it is the system-level architecture authority. fileciteturn12file0L2-L2

---

# 4. Autonomy authority

`02-autonomy/` is authoritative for:

- continuous cognitive loop;
- attention;
- goals;
- curiosity;
- planning;
- action execution;
- autonomy state;
- autonomy safety boundaries;
- runtime;
- autonomy testing and observability.

---

# 5. Cognition authority

`03-cognition/` is authoritative for:

- cognitive architecture;
- world-model semantics;
- multimodal cognition;
- reasoning;
- uncertainty;
- identity/person model;
- social cognition;
- temporal/causal reasoning;
- context construction;
- prediction;
- personality/affect;
- model routing;
- cognitive data/API contracts;
- cognitive failure modes;
- cognitive testing.

---

# 6. Memory and knowledge authority

`04-memory-and-knowledge/` is authoritative for:

- memory taxonomy;
- lifecycle/admission;
- provenance;
- retrieval;
- knowledge graph;
- identity/entity resolution;
- temporal/spatial memory;
- causal modeling;
- cross-modal memory;
- skills/competence verification;
- schema evolution;
- memory governance;
- human oversight.

The `archive/` tree is historical/reference material. It must not override the consolidated current documents without an explicit migration decision.

---

# 7. Hardware authority

`05-hardware/` is authoritative for physical-system requirements.

Current authoritative documents:

- `00_HIGH_LEVEL_HARDWARE_ARCHITECTURE.md`
- `24_HARDWARE_SELECTION_AND_BOM_BASELINE.md`
- `README.md`

`24_HARDWARE_SELECTION_AND_BOM_BASELINE.md` is the current master for hardware selection requirements until the detailed hardware specifications are decomposed into their own files.

---

# 8. Technology authority

## `TECHNOLOGY_REFERENCE.md`

Catalog of candidate ecosystems and technologies.

## `TECHNOLOGY_STACK_BASELINE.md`

Implementation-oriented proposed stack and technology boundaries.

## ADRs

Actual adoption decisions live in ADRs.

Therefore:

```text
Technology Reference
      ↓
Stack Baseline
      ↓
Benchmark
      ↓
ADR
      ↓
Adopted Technology
```

---

# 9. Research authority

The two Library documents are research inputs:

- `NVIDIA_Novi_Comprehensive_Research.md`
- `NVIDIA_Novi_Physical_AI_Research_2026.md`

They are not project architecture authority and do not automatically approve NVIDIA technology.

The research itself explicitly separates vendor capability claims, architectural implications and adoption decisions. fileciteturn23file0L195-L241

---

# 10. Required future domain documents

The README's planned domain structure remains the long-term decomposition:

```text
01-system-architecture
02-autonomy
03-cognition
04-world-model
05-memory
06-knowledge-base
07-perception
08-personality-and-social
09-models-and-inference
10-agent-and-tools
11-safety-and-security
12-robotics-and-ros2
13-nvidia-platform
14-simulation-and-digital-twin
15-hardware
16-audio-and-voice
17-navigation-and-mapping
18-iot-and-external-systems
19-data-and-storage
20-control-app
21-observability-diagnostics-audit
22-testing-and-validation
23-data-generation-and-training
24-deployment-and-operations
25-privacy-and-governance
26-development-process
```

The current repository has consolidated domains for the first system-architecture, autonomy, cognition, memory/knowledge and hardware work. The remaining planned domains must be created when their specifications are sufficiently mature to become authoritative.

The pre-implementation audit tracks this work as a gap rather than pretending those domains already exist.

---

# 11. Required document metadata

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

# 12. Document lifecycle

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

A document marked `ARCHIVED` is not an active authority unless explicitly referenced by a current document.

---

# 13. Pre-implementation documentation gate

The project is documentation-ready only when:

- [ ] every P0 domain has an authoritative specification;
- [ ] all major cross-domain interfaces are defined;
- [ ] all major technology choices have an ADR or explicit evaluation status;
- [ ] hardware capability requirements are defined;
- [ ] physical safety requirements are defined;
- [ ] simulation requirements are defined;
- [ ] data/model artifacts are defined;
- [ ] validation criteria exist;
- [ ] all stale project terminology has been removed;
- [ ] no current implementation plan depends on an undocumented assumption.

---

# 14. Final rule

> **If we cannot point to the document that defines what a component is, why it exists, what it consumes, what it produces, where it runs, what technology implements it, how it fails, how it is tested, and what proves it works, it is not ready for implementation.**
