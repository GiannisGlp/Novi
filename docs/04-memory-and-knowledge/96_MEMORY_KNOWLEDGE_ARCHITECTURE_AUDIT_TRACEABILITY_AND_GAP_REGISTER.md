# 96 — Memory Knowledge Architecture Audit, Traceability and Gap Register

## Status

**NORMATIVE AUDIT — CRITICAL / V1 ARCHITECTURE GATE**

## Purpose

Document 96 audits the Novi memory-and-knowledge architecture against the normative reference model in Document 95 and the preceding foundational documents in `docs/04-memory-and-knowledge/`.

Its purpose is not to add another memory subsystem. It establishes whether the existing architecture is coherent enough to continue specification and implementation, identifies unresolved gaps, records traceability obligations, and defines the priority order for documents 97+.

> **No new memory capability should be considered architecturally complete until its responsibilities, interfaces, evidence model, provenance, privacy, security, lifecycle, evaluation and failure behavior have been reconciled with Document 95.**

## 1. Audit Scope

The audit covers four layers:

```text
FOUNDATIONAL MEMORY DOCUMENTS
        ↓
SPECIALIZED ARCHITECTURE 70–94
        ↓
95 REFERENCE MODEL
        ↓
IMPLEMENTATION-READINESS GAPS
```

The audit evaluates:

- conceptual consistency;
- responsibility boundaries;
- data-model continuity;
- lifecycle semantics;
- provenance and lineage;
- evidence and belief separation;
- retrieval behavior;
- privacy and access control;
- deletion and retention;
- distributed consistency;
- security;
- safety;
- evaluation;
- research support;
- implementation readiness.

## 2. Normative Baseline

Document 95 establishes the system-wide invariants. The most important are:

```text
MEMORY ≠ AUTHORITY
RETRIEVAL ≠ TRUTH
SIMILARITY ≠ EVIDENCE
EVIDENCE ≠ BELIEF
BELIEF ≠ DECISION
DECISION ≠ AUTHORIZATION
AUTHORIZATION ≠ SAFETY
ACTION ≠ COMPLETION
```

The audit treats these as architecture-wide invariants rather than local recommendations.

## 3. Research Cross-Validation

The audit was cross-checked against current work on long-horizon agent memory, memory evaluation, temporal correctness, provenance and memory security.

### 3.1 Long-term memory evaluation

LongMemEval evaluates information extraction, multi-session reasoning, knowledge updates, temporal reasoning and abstention, demonstrating that long-term memory evaluation cannot be reduced to simple recall. citeturn0search2

Recent longitudinal benchmark work further emphasizes update fidelity, interference resistance, temporal decay, delayed retrieval and abstention as separate dimensions. citeturn0search0

### 3.2 Stateful agent evaluation

STATE-Bench evaluates whether memory improves reliability on realistic stateful tasks rather than merely improving answer recall. This supports evaluating memory through downstream task outcomes as well as retrieval metrics. citeturn0search14

### 3.3 Memory security

Recent research shows that persistent memory creates a security surface distinct from ordinary prompt injection. Poisoned memories can persist across sessions and influence later behavior. citeturn0academia37turn0academia38

Sleeper-memory research further demonstrates delayed attacks in which malicious memories remain dormant before later influencing behavior. citeturn0academia39

OWASP independently treats memory/context poisoning as a distinct agentic security concern, reinforcing the requirement for write-time controls, integrity protection, policy enforcement and recovery. citeturn0search1turn0search4

### 3.4 Provenance

The architecture's provenance emphasis is also consistent with current agent-memory work that treats source lineage as necessary for debugging, source-scoped retrieval and compliance. citeturn0search15

### 3.5 Cross-validation conclusion

The research supports the architecture's decision to treat memory as a **stateful, temporal, governed and security-sensitive process**, rather than as a vector index alone.

However, research also shows that benchmarks and implementations remain heterogeneous. Therefore research findings are used as constraints and evidence, not as permission to claim that one memory architecture is universally optimal.

## 4. Foundational Document Traceability

The repository already contains foundational documents including:

```text
00 High-Level Memory Architecture
01 Memory Taxonomy
02 Memory Lifecycle
03 Memory Write and Admission Policy
04 Memory Consolidation and Forgetting
05 Memory Retrieval and Ranking
06 Memory Provenance and Trust
07 Memory Schema and Storage
08 Memory Indexing and Embeddings
09 Memory Knowledge Graph and Relationships
10 Memory Schema Evolution and Dynamic Data
```

These establish the original architecture's Memory Manager, active/durable memory separation, admission policy, retrieval, storage and provenance foundations.

The later 70–95 sequence expands these concepts into a more rigorous epistemic, security, governance and evaluation architecture.

### Audit conclusion

The foundational documents remain valuable and should not be discarded. They should be treated as earlier specifications that must converge with the normative semantics established by 95.

## 5. Architecture Traceability Matrix

| Domain | Existing foundation | 70–95 coverage | 95 requirement | Audit state | Priority |
|---|---|---|---|---|---|
| Memory taxonomy | 01 | 82–86 | Typed memory states | **Covered; formalize interfaces** | High |
| Lifecycle | 02, 76, 87 | 76, 87, 95 | Explicit lifecycle | **Covered; reconcile states** | Critical |
| Write/admission | 03 | 75, 88, 94, 95 | Governed memory write gate | **Covered; security hardening needed** | Critical |
| Consolidation | 04, 78, 89 | 78, 89 | Validated consolidation | **Covered; implementation contract needed** | Critical |
| Retrieval/ranking | 05, 80, 90 | 80, 90 | Governed retrieval | **Covered; benchmark integration needed** | Critical |
| Provenance/trust | 06, 74, 92 | 74, 92 | Traceable lineage | **Covered; schema contract needed** | Critical |
| Storage/schema | 07, 10 | 71, 95 | Stable typed objects | **Partial** | Critical |
| Indexing/embeddings | 08 | 79, 90, 92 | Derivative-aware retrieval | **Partial** | High |
| Knowledge graph | 09 | 73, 79, 92 | Relationship lineage | **Partial** | High |
| Schema evolution | 10 | 71, 92, 95 | Migration semantics | **Gap** | Critical |
| Distributed memory | — | 70–73 | Causal synchronization | **Partial** | Critical |
| Evidence quality | — | 75, 91 | Evidence ≠ belief | **Covered** | Critical |
| Belief revision | — | 77, 91 | Revision with provenance | **Covered; formal model needed** | Critical |
| Episodic memory | — | 82 | Experience records | **Covered** | High |
| Semantic memory | — | 83 | Generalized knowledge | **Covered** | High |
| Procedural memory | — | 84 | Skills with competence limits | **Partial** | Critical |
| Prospective memory | — | 85 | Intention lifecycle | **Covered; execution integration needed** | Critical |
| Metamemory | — | 86 | Memory self-knowledge | **Covered** | High |
| Forgetting/erasure | — | 87 | Propagated erasure | **Covered; implementation contract needed** | Critical |
| Privacy/governance | — | 88 | Purpose-limited access | **Covered; policy engine needed** | Critical |
| Consolidation engine | — | 89 | Controlled durable learning | **Covered; implementation contract needed** | Critical |
| Context assembly | — | 90 | Minimum sufficient context | **Covered** | Critical |
| Evidence arbitration | — | 91 | Conflict-aware fusion | **Covered; formal decision policy needed** | Critical |
| Provenance/lineage | — | 92 | Forward/backward traceability | **Covered; graph implementation needed** | Critical |
| Evaluation | — | 93 | Longitudinal validation | **Covered; harness needed** | Critical |
| Security | — | 94 | Memory threat model | **Covered; runtime controls needed** | Critical |
| Integration | — | 95 | Normative reference model | **Covered** | Critical |

## 6. Critical Architectural Gaps

The following gaps are not cosmetic. They affect the ability to implement the architecture safely.

### GAP-01 — Identity and Entity Resolution

**Problem:** Memories require stable identities for people, objects, devices, agents, places and concepts, including uncertain or changing identity.

**Why critical:** Without identity semantics, relationship memory, privacy boundaries, provenance, cross-session continuity and distributed synchronization can attach information to the wrong entity.

**Required next document:** dedicated identity/entity architecture.

### GAP-02 — Temporal Reasoning

**Problem:** Timestamps alone are insufficient for validity intervals, event ordering, recurrence, temporal uncertainty, revisions and "true at time" semantics.

**Why critical:** Long-term memory benchmarks specifically expose failures around updates and temporal reasoning. citeturn0search2turn0search0

**Required next document:** temporal memory and reasoning model.

### GAP-03 — Spatial Memory

**Problem:** Novi's physical-world operation requires uncertainty-aware places, landmarks, regions, routes and changing spatial relationships.

**Why critical:** Historical location memory must not be confused with current localization or current navigability.

**Required next document:** spatial memory architecture.

### GAP-04 — Causal World Modeling

**Problem:** Provenance tells Novi where information came from, but provenance is not a causal model.

**Why critical:** Temporal sequence and correlation must not be promoted into causal claims.

**Required next document:** causal reasoning/world-model architecture.

### GAP-05 — Cross-Modal Memory

**Problem:** Text, images, audio, video and sensor streams need common identity, time, provenance, uncertainty and derivative semantics.

**Why critical:** Novi is intended to operate in a physical environment; a memory architecture restricted to text is insufficient.

**Required next document:** cross-modal memory model.

### GAP-06 — Procedural Competence Verification

**Problem:** A successful execution does not prove general skill competence.

**Why critical:** Procedural memory can otherwise become an unsafe source of overconfident autonomous behavior.

**Required next document:** skill/competence verification architecture.

### GAP-07 — Memory Schema Evolution and Migration

**Problem:** The foundational schema-evolution document exists, but the integrated 95 model requires migration semantics for provenance, deletion, security, replicas and derived indexes.

**Why critical:** A migration that preserves values but loses provenance or deletion semantics is architecturally invalid.

**Required next document:** memory migration and compatibility architecture.

### GAP-08 — Model/Memory Co-Evolution

**Problem:** Changes to foundation models, embedding models, rerankers or extraction models can change interpretation and retrieval behavior without changing stored memory.

**Why critical:** A model upgrade can therefore alter the effective meaning and behavior of an existing memory corpus.

**Required next document:** model/memory compatibility and co-evolution architecture.

### GAP-09 — Machine-Verifiable Governance

**Problem:** Privacy, retention, access, deletion and safety policies currently exist primarily as architectural requirements.

**Why critical:** High-impact policy cannot depend only on application conventions or model instructions.

**Required next document:** formal policy engine and enforcement architecture.

### GAP-10 — Human Oversight and Escalation

**Problem:** Ambiguous ownership, high-impact corrections, disputed deletion, security incidents and unresolved evidence conflicts require escalation paths.

**Why critical:** Some decisions cannot be safely automated.

**Required next document:** human oversight and escalation architecture.

## 7. Secondary Gaps

These should follow the critical gaps or be integrated where appropriate:

- memory replication protocol;
- cross-agent memory contracts;
- offline synchronization;
- audit-log architecture;
- privacy-preserving observability;
- memory backup/restore semantics;
- cross-memory transaction semantics;
- memory cost/resource governance;
- benchmark dataset governance;
- reproducible memory interchange format;
- simulation/test-world memory generation.

## 8. Duplicate Responsibility Audit

The architecture contains areas where earlier and later documents overlap.

### Consolidation

```text
04 Consolidation and Forgetting
78 Consolidation / Abstraction
89 Consolidation / Reconsolidation Engine
```

**Resolution:** 04 remains foundational behavior; 78 defines conceptual consolidation; 89 defines the integrated engine. New implementation work should treat 89 as the execution-level contract while preserving 04's foundational requirements.

### Retrieval

```text
05 Retrieval and Ranking
80 Retrieval / Contextual Recall
90 Retrieval / Ranking / Context Assembly
```

**Resolution:** 05 remains foundational retrieval policy; 80 defines memory-recall behavior; 90 is the integrated retrieval/context engine.

### Provenance

```text
06 Provenance and Trust
74 Provenance / Evidence Graph
92 Provenance / Lineage / Traceability
```

**Resolution:** 06 defines foundational trust/provenance requirements; 74 defines evidence-graph semantics; 92 defines executable lineage/traceability.

### Lifecycle / Forgetting

```text
02 Lifecycle
76 Retention / Promotion / Demotion
87 Decay / Forgetting / Erasure
```

**Resolution:** 02 remains the base lifecycle; 76 controls retention state; 87 governs decay and erasure. These must eventually share one canonical lifecycle state machine.

## 9. Canonicalization Requirement

The next implementation phase must avoid maintaining parallel, contradictory state machines.

Create canonical definitions for:

```text
MemoryIdentity
MemoryLifecycleState
EvidenceStatus
EpistemicStatus
AccessDecision
RetentionClass
DeletionState
ProvenanceRecord
ConflictState
RetrievalResult
ContextPackage
SkillConfidence
IntentionState
EvaluationResult
SecurityState
```

Every document and implementation component should reference these canonical definitions rather than inventing local alternatives.

## 10. Research-to-Architecture Rules

Future architecture decisions should distinguish:

```text
EMPIRICAL FINDING
THEORETICAL MODEL
ENGINEERING DESIGN CHOICE
SECURITY REQUIREMENT
PRODUCT POLICY
```

They must not be presented as interchangeable evidence.

For example, a benchmark demonstrating better update fidelity does not establish universal superiority of an architecture, and a security attack demonstrating feasibility does not establish its prevalence in every deployment.

## 11. Evaluation Requirements for Future Documents

Every future memory component must define at least:

```text
WHAT IT IS SUPPOSED TO DO
WHAT CAN GO WRONG
HOW IT IS MEASURED
WHAT COUNTS AS FAILURE
WHAT HAPPENS AFTER FAILURE
HOW IT INTERACTS WITH 95
```

Where applicable, tests should include:

- clean behavior;
- stale information;
- contradictory information;
- missing information;
- adversarial input;
- privacy boundary violations;
- deletion;
- distributed operation;
- model changes;
- longitudinal accumulation.

## 12. Security Requirements for Future Documents

Any component that can read, write, transform or route memory must address:

```text
AUTHENTICITY
INTEGRITY
AUTHORIZATION
PROVENANCE
POISONING
EXFILTRATION
REPLAY
ROLLBACK
DELETION
CROSS-USER ISOLATION
```

Persistent memory must be treated as a security-sensitive state layer, consistent with current memory-poisoning research and OWASP's agentic memory threat model. citeturn0academia38turn0search1

## 13. Privacy Requirements for Future Documents

Any component handling memory must define:

- data ownership;
- access scope;
- purpose limitation;
- retention;
- deletion;
- derived-data treatment;
- cross-user isolation;
- audit requirements;
- emergency access behavior.

## 14. Failure and Degradation Requirements

Every component must define explicit states for at least the subset relevant to it:

```text
UNKNOWN
UNAVAILABLE
STALE
CONFLICTED
QUARANTINED
BLOCKED
DEGRADED
PENDING
FAILED
```

A component must not silently convert an unavailable or uncertain state into a confident result.

## 15. Implementation Readiness Gate

A memory subsystem should not move to implementation until it can answer:

```text
1. What data does it own?
2. What data does it consume?
3. What data does it produce?
4. What is authoritative?
5. What is derived?
6. What is the provenance chain?
7. What are the access controls?
8. What are the retention/deletion rules?
9. What are the failure states?
10. What are the security threats?
11. What are the evaluation metrics?
12. What current-state information can override historical memory?
13. How does it interact with 95?
```

## 16. Priority Order for Documents 97+

The audit produces the following dependency order.

### P0 — Required before serious implementation

```text
97  Identity / Entity Resolution
98  Temporal Reasoning and Temporal Memory
99  Spatial Memory and Spatial State
100 Causal World Modeling and Causal Memory
101 Cross-Modal Memory
102 Procedural Skill / Competence Verification
103 Memory Schema Migration / Compatibility
104 Model / Memory Co-Evolution
105 Machine-Verifiable Memory Governance / Policy Engine
106 Human Oversight / Escalation
```

### P1 — Required for production hardening

```text
107 Distributed Memory Replication and Synchronization
108 Cross-Agent Memory Exchange Contracts
109 Offline Memory Synchronization and Recovery
110 Memory Backup / Restore / Disaster Recovery
111 Privacy-Preserving Audit and Observability
112 Memory Transaction and Atomicity Semantics
113 Resource / Cost Governance for Memory
```

### P2 — Advanced capability / research

```text
114 Cross-Modal Retrieval and Fusion Optimization
115 Memory Simulation and Synthetic Evaluation Environments
116 Reproducible Memory Interchange Format
117 Formal Verification of Memory Policies
118 Memory Self-Diagnostics and Autonomous Repair
119 Adaptive Memory Architecture Selection
```

The sequence is provisional: each future document must be re-evaluated against newly discovered dependencies and research.

## 17. Immediate Next Step

The next document should be **97 — Identity and Entity Resolution Architecture**.

This is the correct next dependency because identity affects:

```text
PRIVACY
PROVENANCE
RELATIONSHIPS
EPISODES
SEMANTIC FACTS
SKILLS
INTENTIONS
DISTRIBUTED MEMORY
CROSS-MODAL MEMORY
DELETION
```

Without a stable identity model, later spatial, temporal, causal and cross-modal memory layers risk attaching facts to the wrong entity.

## 18. Architecture Governance Rule

Document 95 remains the normative integration point.

Document 96 becomes the **audit and sequencing point**.

Therefore:

```text
95 = WHAT THE INTEGRATED ARCHITECTURE MUST MEAN
96 = WHAT IS MISSING / INCONSISTENT / NEXT
97+ = RESOLUTION OF THE IDENTIFIED GAPS
```

Any future document that discovers a new architectural contradiction must update 96's gap register or explicitly supersede the affected finding.

## 19. Final Principle

> **Novi should not grow its memory architecture by accumulation alone. It should grow through controlled specification: establish the invariant, trace the dependency, validate the research, identify the gap, define the interface, test the failure modes, and only then add the next capability.**

Document 96 is therefore the quality gate between the first major memory architecture cycle and the next generation of Novi's memory system.