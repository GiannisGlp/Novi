# 92 — Memory Knowledge Memory Provenance, Lineage and Traceability Engine

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Research Basis

This architecture is grounded in the W3C PROV family, particularly the PROV Data Model and PROV-O, which model provenance through entities, activities and agents and support derivation, responsibility and temporal relationships. PROV-O is designed to be specialized for domain-specific provenance systems, making it a useful interoperability foundation rather than a complete Novi schema. citeturn0search1turn0search6

The 2024 PROV-JSONLD submission further provides a machine-readable JSON/JSON-LD representation intended for provenance interchange and processing. citeturn0search2turn0search7

Recent AI provenance research demonstrates why lineage must cover source, creators, licensing and subsequent transformations rather than treating datasets as opaque artifacts. citeturn0search0turn0search4 Research on RAG provenance also demonstrates the value of tracing generated claims back to specific retrieved context when detecting or correcting unsupported output. citeturn0search8turn0search24

## Purpose

Define the engine that records, traverses, validates and exposes the provenance and lineage of Novi's information across observations, episodes, memories, evidence, beliefs, summaries, skills, intentions, decisions, actions and derived knowledge.

## Core Principle

> **Every consequential piece of knowledge should be traceable backward to its supporting provenance and forward to the artifacts, beliefs, decisions and actions that depend on it.**

Traceability does not prove truth. It makes the basis, transformation history, responsibility and dependency structure inspectable.

## 1. Position in Architecture

```text
OBSERVATION / INPUT
        ↓
PROVENANCE CAPTURE
        ↓
MEMORY / EVIDENCE
        ↓
DERIVATION
        ↓
BELIEF / KNOWLEDGE
        ↓
RETRIEVAL
        ↓
REASONING / DECISION
        ↓
ACTION / OUTCOME
        ↓
NEW EVIDENCE
```

The provenance engine spans the complete chain.

## 2. Provenance vs Lineage vs Traceability

```text
PROVENANCE
→ information about origin, creation, responsibility and history

LINEAGE
→ directed dependency relationships between artifacts

TRACEABILITY
→ ability to follow those relationships for a defined question or audit
```

These concepts overlap but should remain distinguishable.

## 3. W3C PROV Alignment

Novi should conceptually map to three core PROV categories:

```text
ENTITY
→ observation, memory, document, claim, embedding, plan, outcome

ACTIVITY
→ observation, transformation, retrieval, inference, consolidation, execution

AGENT
→ user, Novi instance, model, tool, sensor, external service
```

Novi may extend these categories with domain-specific metadata.

## 4. Provenance Graph

The canonical representation is a directed provenance graph:

```text
AGENT
  ↓ associated with
ACTIVITY
  ↓ generates / uses
ENTITY
  ↓ derived from
ENTITY
```

Edges should carry timestamps, versions and relevant qualification metadata where required.

## 5. Entity Identity

Every traceable artifact should have a stable identifier within its scope.

Examples:

```text
observation_id
episode_id
memory_id
claim_id
belief_id
skill_id
intention_id
decision_id
action_id
outcome_id
```

Identifiers must not themselves expose sensitive information.

## 6. Entity Versioning

Mutable artifacts require version identity:

```text
MEMORY v1
   ↓
MEMORY v2
   ↓
MEMORY v3
```

Historical versions should remain distinguishable when required for audit, scientific reproducibility or conflict analysis.

## 7. Activities

Activities represent transformations or events such as:

- sensing;
- ingestion;
- parsing;
- retrieval;
- summarization;
- inference;
- consolidation;
- belief revision;
- planning;
- execution;
- verification;
- synchronization;
- deletion.

## 8. Agents

Agents can include:

- human users;
- Novi instances;
- model versions;
- sensors;
- tools;
- external services;
- other authorized agents.

Responsibility must not be inferred solely from technical ownership.

## 9. Source Provenance

An observation should record, where available:

- source agent/device;
- sensor/tool identity;
- capture time;
- location context;
- configuration/version;
- acquisition conditions;
- integrity metadata;
- authorization context.

## 10. Transformation Provenance

When data is transformed, record:

```text
INPUTS
 ↓
TRANSFORMATION
 ↓
OUTPUT
```

Examples include normalization, transcription, summarization, embedding, extraction and aggregation.

## 11. Model Provenance

Model-generated artifacts should identify:

- model family;
- model/version identifier where available;
- inference configuration relevant to reproducibility;
- input artifacts;
- tools used;
- retrieval context identifiers;
- generation time.

Exact internal model state need not be exposed when unavailable.

## 12. Tool Provenance

Tool-mediated outputs should identify:

- tool/service;
- invocation identity;
- invocation time;
- relevant input parameters;
- returned artifact/result;
- authorization context;
- failure state where applicable.

Secrets must never be copied into provenance merely because they were tool inputs.

## 13. Sensor Provenance

Sensor observations should retain relevant:

- sensor identity;
- calibration/version;
- sampling time;
- uncertainty;
- coordinate frame;
- preprocessing pipeline.

Sensor metadata can materially affect evidence interpretation.

## 14. Human Provenance

User-provided information should retain provenance indicating that it was explicitly supplied by a human when policy permits.

```text
USER STATEMENT
      ↓
REPORTED EVIDENCE
```

A user statement is not automatically equivalent to direct observation.

## 15. Evidence Lineage

Each evidence item should be traceable to its underlying source(s).

```text
EVIDENCE
 ↓ supported by
SOURCE RECORD(S)
```

The system must distinguish direct evidence from derivative evidence.

## 16. Claim Lineage

A claim should expose the evidence supporting it:

```text
CLAIM
 ├── supported by E1
 ├── supported by E2
 └── contradicted by E3
```

Support and contradiction are explicit relationships.

## 17. Belief Lineage

A belief should record:

- claims considered;
- evidence considered;
- arbitration activity;
- confidence/uncertainty;
- creation time;
- revision history.

This links document 91's arbitration to durable knowledge.

## 18. Belief Revision

When a belief changes:

```text
BELIEF v1
   ↓ revised because of
EVIDENCE / ARBITRATION
   ↓
BELIEF v2
```

The old belief should remain distinguishable from the new belief where historical traceability matters.

## 19. Decision Lineage

A consequential decision should be traceable to:

```text
DECISION
 ↓
RELEVANT BELIEFS
 ↓
EVIDENCE
 ↓
SOURCE PROVENANCE
```

This does not require storing private chain-of-thought. Decision provenance should capture auditable inputs, rules, policies and outputs rather than hidden reasoning traces.

## 20. Action Lineage

An action should identify, where appropriate:

- intention/task;
- plan version;
- selected skill;
- authorization decision;
- safety decision;
- relevant world-state snapshot;
- execution activity;
- observed outcome.

## 21. Outcome Lineage

An outcome should link back to the action and observation that established it.

```text
ACTION
 ↓
OBSERVATION
 ↓
OUTCOME
```

An issued command is not itself proof of outcome.

## 22. Skill Provenance

A skill should trace to:

```text
DEMONSTRATIONS
EPISODES
VALIDATION RUNS
FAILURES
UPDATES
```

This allows Novi to determine why a procedure exists and how it was validated.

## 23. Intention Provenance

An intention should identify its source:

```text
USER REQUEST
SYSTEM POLICY
ACCEPTED PLAN
RECURRING ROUTINE
EXTERNAL EVENT
```

Inferred intentions must remain distinguishable from explicit commitments.

## 24. Retrieval Provenance

Every retrieved context item should retain:

- memory identifier;
- version;
- retrieval query/context identifier;
- retrieval timestamp;
- retrieval method;
- ranking metadata where useful;
- access policy decision.

## 25. Context Provenance

A reasoning context should be reconstructible at the artifact level:

```text
CONTEXT
 ├── MEMORY A v4
 ├── MEMORY B v2
 ├── DOCUMENT C
 └── TOOL RESULT D
```

The context itself becomes a traceable derived artifact when appropriate.

## 26. Output Attribution

When Novi produces a factual claim from retrieved material, the claim should be traceable to the relevant context artifacts.

This supports targeted verification and correction rather than treating the entire response as one opaque output. RAG provenance research demonstrates the practical value of tracing unsupported output back to context chunks. citeturn0search8

## 27. Attribution Is Not Causation

A source being present in context does not prove it caused a particular output.

```text
AVAILABLE SOURCE
 ≠
CAUSAL SOURCE
```

Attribution should distinguish:

```text
AVAILABLE
USED
SUPPORTING
CONTRADICTING
INFLUENTIAL
```

Where causal influence cannot be established, Novi must not claim it.

## 28. Multiple Supporting Sources

A claim can have multiple independent or dependent sources.

Provenance should preserve their relationships rather than flattening them into one citation list.

## 29. Source Independence

Lineage must expose shared ancestors:

```text
SOURCE A ─┐
          ├→ SUMMARY
SOURCE B ─┘
```

If two apparently independent records share the same ancestor, their evidentiary independence must be discounted accordingly.

## 30. Derivation Graph

Derived artifacts should retain explicit relationships:

```text
SOURCE
 ↓ derived
EPISODE
 ↓ derived
SUMMARY
 ↓ derived
CLAIM
 ↓ derived
BELIEF
```

This graph is central to evidence quality and controlled erasure.

## 31. Forward Trace

Given a source, Novi should be able to ask:

```text
WHAT DEPENDS ON THIS?
```

Example:

```text
MEMORY X
 ↓
CLAIM Y
 ↓
BELIEF Z
 ↓
DECISION A
 ↓
ACTION B
```

## 32. Backward Trace

Given an action or belief, Novi should be able to ask:

```text
WHY DOES THIS EXIST?
```

Example:

```text
ACTION B
 ↓
DECISION A
 ↓
BELIEF Z
 ↓
CLAIM Y
 ↓
MEMORY X
 ↓
OBSERVATION
```

## 33. Impact Analysis

Before modifying or deleting a memory, determine downstream dependents where policy requires:

```text
MEMORY DELETE
 ↓
DEPENDENCY TRAVERSAL
 ↓
IMPACT SET
```

This connects directly to document 87.

## 34. Provenance-Aware Erasure

Deletion must preserve only the minimum governance metadata needed to enforce erasure and audit it.

Deleted content must not remain exposed through lineage records.

## 35. Provenance Integrity

Provenance records should be tamper-evident or otherwise integrity-protected according to consequence.

A provenance graph that can be silently rewritten cannot reliably support audit.

## 36. Append-Only History

High-value provenance events should use append-oriented history where practical:

```text
EVENT 1
EVENT 2
EVENT 3
```

Corrections should be represented as new events rather than silently overwriting historical provenance.

## 37. Immutability Boundaries

Not every metadata field needs immutable storage.

The architecture should distinguish:

```text
IMMUTABLE EVIDENCE
VERSIONED INTERPRETATION
MUTABLE INDEX / CACHE
```

This prevents unnecessary storage cost while preserving audit-critical history.

## 38. Cryptographic Integrity

For high-consequence records, consider:

- content hashes;
- signed provenance assertions;
- authenticated timestamps;
- hash-linked event chains;
- trusted execution/service attestations where available.

Cryptographic integrity proves record integrity, not truth of the underlying claim.

## 39. Clock and Temporal Integrity

Provenance timestamps should identify their time basis and account for clock uncertainty where relevant.

Important event ordering should not rely blindly on unsynchronized local clocks.

## 40. Causal Ordering

Distributed systems should use causal/version metadata where necessary to distinguish:

```text
A happened before B
B happened before A
A and B concurrent
ORDER UNKNOWN
```

Wall-clock timestamps alone may be insufficient.

## 41. Distributed Provenance

Across Novi instances, preserve:

- origin agent;
- event identity;
- causal metadata;
- source version;
- synchronization state;
- conflict state.

## 42. Provenance Replication

Replicated provenance should remain distinguishable from the original record.

```text
ORIGINAL
 ↓ replicated to
REPLICA
```

A replica is not a new independent source.

## 43. External Data

External records should retain:

- provider;
- resource identifier;
- acquisition time;
- version/ETag where available;
- retrieval method;
- license/usage metadata where relevant.

## 44. External Source Disappearance

If an external source later becomes unavailable, Novi should retain the provenance needed to state that the source was previously retrieved without pretending that it can still independently verify the source.

## 45. Provenance Confidence

Provenance itself can be uncertain.

```text
DIRECTLY RECORDED
INFERRED LINEAGE
PARTIAL LINEAGE
UNKNOWN LINEAGE
```

Novi must not represent inferred provenance as direct provenance.

## 46. Missing Provenance

A memory without provenance can remain useful, but its trust and downstream eligibility should be qualified according to policy.

```text
UNKNOWN ORIGIN
 ↓
restricted confidence / use
```

## 47. Provenance Completeness

Track whether required lineage fields are:

```text
COMPLETE
PARTIAL
MINIMAL
MISSING
```

Completeness is distinct from correctness.

## 48. Provenance Compression

Large graphs may be summarized for ordinary retrieval.

The compressed representation must remain linked to the authoritative provenance graph and must not become an independent evidence source.

## 49. Provenance Queries

The engine should support queries such as:

```text
WHERE DID THIS CLAIM COME FROM?
WHAT EVIDENCE SUPPORTS THIS BELIEF?
WHAT MEMORIES DEPEND ON THIS SOURCE?
WHAT ACTIONS USED THIS BELIEF?
WHO CREATED THIS ARTIFACT?
WHAT MODEL GENERATED THIS SUMMARY?
WHICH SOURCES WERE SHARED ANCESTORS?
WHAT WOULD BE AFFECTED BY DELETION?
```

W3C PROV-AQ explicitly addresses mechanisms for locating, retrieving and querying provenance records, supporting this style of architecture. citeturn0search5

## 50. Human Audit View

A human-facing trace should provide a concise path:

```text
ACTION
 ↓
DECISION
 ↓
BELIEF
 ↓
EVIDENCE
 ↓
SOURCE
```

with expandable detail rather than exposing unnecessary internal data.

## 51. Machine Audit View

Machines should have structured access to:

- identifiers;
- relations;
- versions;
- timestamps;
- agents;
- activities;
- confidence/status;
- integrity metadata;
- access restrictions.

JSON-LD/PROV-compatible serialization is a strong interoperability option. citeturn0search2turn0search7

## 52. Privacy Boundary

Provenance can reveal:

- who was present;
- where information came from;
- which person supplied it;
- what sensitive memory influenced a decision;
- which tools were used.

Therefore provenance must inherit or derive appropriate access controls from the underlying artifacts.

## 53. Minimal Disclosure

An auditor asking:

```text
"Why was this action taken?"
```

should receive the minimum evidence path necessary for the authorized purpose.

Full provenance traversal must not automatically expose unrelated private memories.

## 54. Security Boundary

Provenance data must be treated as potentially sensitive and potentially attacker-controlled when imported externally.

External provenance assertions are data, not authorization.

## 55. Prompt Injection Boundary

Text contained inside a provenance record must never become an instruction merely because it appears in the lineage graph.

```text
PROVENANCE CONTENT
 ≠
EXECUTION AUTHORITY
```

## 56. Provenance and Decision Safety

Safety-critical decisions should require provenance sufficient to establish:

- current relevant evidence;
- evidence freshness;
- source integrity where available;
- applicable policy;
- authorization;
- safety assessment.

Historical provenance alone cannot establish current safety.

## 57. Provenance and Memory Consolidation

Document 89 should create provenance edges whenever an episode produces a consolidated memory or abstraction.

This prevents abstraction from severing the evidence chain.

## 58. Provenance and Retrieval

Document 90 should attach retrieval provenance to every context artifact used by reasoning.

Retrieval metadata should remain separate from the underlying memory's original provenance.

## 59. Provenance and Evidence Arbitration

Document 91 should record the evidence set and arbitration activity that produced or revised a belief.

This enables later re-evaluation when source reliability or new evidence changes.

## 60. Provenance and Metamemory

Document 86 should be able to query provenance completeness and source reliability when assessing memory confidence.

## 61. Provenance and Erasure

Document 87 should use lineage traversal to identify derivatives and replicas affected by deletion.

## 62. Provenance and Privacy Governance

Document 88 should control who can inspect provenance and which fields may be exposed.

## 63. Provenance and Procedural Memory

Document 84 should link skills to the demonstrations, episodes, validation runs and failures that justify them.

## 64. Provenance and Prospective Memory

Document 85 should link intentions to their origin, acceptance, trigger and execution history.

## 65. Anti-Feedback-Loop Rule

A generated derivative must not automatically become stronger evidence merely because it appears repeatedly in its own descendants.

```text
SOURCE
 ↓
SUMMARY
 ↓
BELIEF
 ↓
NEW SUMMARY
```

The lineage remains one dependency chain, not multiple independent confirmations.

## 66. Provenance Graph Cycles

Cycles can arise through self-reference or repeated generated artifacts.

The engine should detect and classify cycles rather than treating graph depth as evidence strength.

## 67. Provenance Depth

Deep lineage does not imply high confidence.

```text
10 transformations
 ≠
10 confirmations
```

Depth is a traceability property, not an evidence-quality score.

## 68. Provenance Pruning

Old low-value provenance may be compacted or pruned according to policy, but pruning must preserve whatever lineage is required for:

- safety;
- governance;
- deletion propagation;
- audit;
- reproducibility;
- legal obligations where applicable.

## 69. Provenance Retention

Retention policy must distinguish:

```text
CONTENT RETENTION
PROVENANCE RETENTION
AUDIT RETENTION
```

They need not have identical lifetimes.

## 70. Reproducibility

Where practical, provenance should permit reconstruction of the relevant processing chain:

```text
INPUT VERSION
 +
PROCESS VERSION
 +
CONFIGURATION
 +
OUTPUT VERSION
```

Perfect reproducibility is not always possible, particularly for nondeterministic or unavailable external systems; provenance should state that limitation.

## 71. Non-Reproducible Activity

If an activity cannot be reproduced, record why:

- external state changed;
- source disappeared;
- model version unavailable;
- nondeterministic process;
- hardware state unavailable.

## 72. Attribution Limits

Provenance should never claim more causal certainty than the system can establish.

```text
TRACEABLE
 ≠
CAUSALLY PROVEN
```

## 73. Research / Training Provenance

If experiences or data are used to update models, policies or skills, retain appropriate lineage to establish which evidence contributed to the update.

The architecture must not assume that deleting the source automatically reverses a model-level update; this remains a separate governance/unlearning problem.

## 74. Provenance Quality Metrics

Track:

- provenance completeness;
- lineage coverage;
- unresolved provenance rate;
- broken-edge rate;
- synchronization lag;
- verification coverage;
- attribution accuracy;
- query latency;
- privacy violations;
- unauthorized traversal attempts.

## 75. Testing

Test:

- entity identity;
- version lineage;
- source capture;
- transformation tracking;
- model provenance;
- tool provenance;
- sensor provenance;
- human-provided evidence;
- forward traversal;
- backward traversal;
- impact analysis;
- deletion propagation;
- replicated provenance;
- causal ordering;
- clock skew;
- missing provenance;
- partial provenance;
- provenance compression;
- graph cycles;
- correlated-source detection;
- attribution vs causation;
- privacy filtering;
- unauthorized traversal;
- prompt injection in provenance;
- tamper detection;
- reproducibility limits;
- anti-feedback-loop behavior.

## 76. Architectural Invariants

1. Consequential knowledge should retain traceable provenance.
2. Provenance does not prove truth.
3. Lineage does not equal evidence strength.
4. Attribution does not automatically establish causation.
5. Replicas are not independent evidence.
6. Derived artifacts retain dependency relationships.
7. Generated summaries cannot become independent confirmations through repetition.
8. Historical versions remain distinguishable where required.
9. Provenance corrections should not silently rewrite audit-critical history.
10. High-consequence provenance should have appropriate integrity protection.
11. Distributed provenance preserves causal/version context.
12. Missing provenance must be represented explicitly.
13. Inferred lineage must not be represented as directly recorded lineage.
14. Provenance metadata is itself potentially sensitive.
15. Provenance traversal is access-controlled.
16. External provenance is data, not authorization.
17. Provenance content cannot become execution authority.
18. Deletion workflows use lineage to identify affected derivatives and replicas.
19. Provenance retention and content retention may have different policies.
20. Provenance depth must never be mistaken for confidence.
21. Safety-critical decisions require sufficiently current and trustworthy provenance.
22. Provenance must remain interoperable enough to support machine and human audit.

## 77. Final Principle

> **Novi should be able to answer not only “what does it know?” but “where did this come from, what transformed it, who or what was responsible, what depends on it, and what would change if its source changed?”**

Provenance turns Novi's memory architecture from a collection of records into a traceable knowledge system. It provides the connective tissue between observation, memory, evidence, belief, retrieval, reasoning, decision, action and erasure while preserving the essential distinction between traceability and truth.