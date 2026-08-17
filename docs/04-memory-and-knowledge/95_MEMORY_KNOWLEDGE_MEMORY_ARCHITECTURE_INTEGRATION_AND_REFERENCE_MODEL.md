# 95 — Memory Knowledge Memory Architecture Integration and Reference Model

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1 REFERENCE MODEL**

## Purpose

This document integrates documents **70–94** into one normative reference architecture for Novi's memory and knowledge subsystem.

It defines the boundaries, interfaces, dependencies, invariants, control flow, trust boundaries, lifecycle transitions, failure behavior, and validation requirements that every implementation must satisfy.

This document does not replace the specialized documents 70–94. It establishes how they compose.

## 1. Architectural Principle

> **Novi's memory is a governed, evidence-linked, continuously evaluated state system—not a single database, vector store, context window, or model capability.**

The architecture must preserve distinctions between:

```text
OBSERVATION
EVIDENCE
MEMORY
KNOWLEDGE
BELIEF
INTENTION
SKILL
RETRIEVED CONTEXT
DECISION
ACTION
OUTCOME
```

Collapsing these states creates unsafe and untraceable behavior.

## 2. Scope

The reference model covers:

- distributed memory exchange;
- shared state;
- consistency;
- event history;
- provenance;
- evidence quality;
- memory lifecycle;
- belief revision;
- consolidation;
- semantic relationships;
- retrieval;
- working memory;
- episodic memory;
- semantic memory;
- procedural memory;
- prospective memory;
- metamemory;
- decay and erasure;
- privacy and governance;
- consolidation/reconsolidation;
- retrieval ranking;
- evidence fusion;
- provenance/lineage;
- evaluation;
- security and adversarial defense.

## 3. Reference Pipeline

```text
WORLD / USER / TOOLS / OTHER AGENTS
                 ↓
        OBSERVATION + INPUT
                 ↓
       TRUST / PRIVACY GATE
                 ↓
       EVIDENCE REGISTRATION
                 ↓
        EPISODIC EXPERIENCE
                 ↓
     CONSOLIDATION / ABSTRACTION
                 ↓
   SEMANTIC / PROCEDURAL / PROSPECTIVE
                 ↓
          MEMORY GRAPH
                 ↓
       RETRIEVAL + RANKING
                 ↓
       EVIDENCE FUSION / ARBITRATION
                 ↓
      CONTEXT ASSEMBLY / WORKING MEMORY
                 ↓
             REASONING
                 ↓
       DECISION / AUTHORIZATION
                 ↓
              ACTION
                 ↓
         OBSERVED OUTCOME
                 ↓
       EVALUATION / LEARNING
                 ↓
      CONSOLIDATION / REVISION
```

## 4. Document Dependency Map

```text
70 Agent-to-Agent Exchange
 └─ 71 Shared Distributed State
     └─ 72 Conflict & Consistency
         └─ 73 Causality & Event History
             └─ 74 Provenance & Evidence Graph
                 └─ 75 Evidence Quality & Uncertainty
                     └─ 76 Promotion / Demotion / Retention
                         └─ 77 Reconsolidation / Belief Revision
                             └─ 78 Consolidation / Abstraction
                                 └─ 79 Associative / Semantic Relationships
                                     └─ 80 Retrieval / Contextual Recall
                                         └─ 81 Working Memory
                                             ├─ 82 Episodic Memory
                                             ├─ 83 Semantic Memory
                                             ├─ 84 Procedural Memory
                                             └─ 85 Prospective Memory
                                                 ↓
                                             86 Metamemory
                                                 ↓
                                             87 Decay / Erasure
                                                 ↓
                                             88 Privacy / Governance
                                                 ↓
                                             89 Consolidation Engine
                                                 ↓
                                             90 Retrieval Engine
                                                 ↓
                                             91 Evidence Fusion
                                                 ↓
                                             92 Provenance / Lineage
                                                 ↓
                                             93 Evaluation
                                                 ↓
                                             94 Security
```

The arrows represent logical dependency, not necessarily runtime execution order.

## 5. Layered Model

### Layer A — Acquisition

Inputs originate from:

- sensors;
- users;
- tools;
- applications;
- other agents;
- external information systems.

### Layer B — Evidence

Inputs become evidence only after source, provenance, integrity and trust metadata are established according to policy.

### Layer C — Memory

Evidence can produce episodic records and later durable semantic, procedural or prospective memories.

### Layer D — Retrieval

Relevant memories are selected for a current task without automatically changing their epistemic status.

### Layer E — Arbitration

Competing evidence and beliefs are reconciled conservatively.

### Layer F — Reasoning

A bounded context is assembled for reasoning.

### Layer G — Action

Authorization and current safety conditions are checked independently of memory.

### Layer H — Evaluation

Outcomes feed reliability, calibration and learning processes.

### Layer I — Governance/Security

Privacy, authorization, retention, deletion and adversarial controls apply across all layers.

## 6. Core Data Objects

Every implementation should define machine-readable representations for at least:

```text
Observation
Evidence
Episode
Memory
Claim
Belief
Skill
Intention
RetrievalResult
ContextPackage
Decision
Action
Outcome
ProvenanceRecord
DeletionRecord
EvaluationRecord
SecurityEvent
```

Each object should have a stable identity and lifecycle state where persistence or traceability is required.

## 7. Common Metadata Envelope

Persistent memory-related objects should support, where applicable:

```text
ID
TYPE
OWNER
SOURCE
CREATED_AT
UPDATED_AT
VALID_TIME
CAPTURE_TIME
PROVENANCE
VERSION
CONFIDENCE
EPISTEMIC_STATUS
SENSITIVITY
ACCESS_POLICY
RETENTION_POLICY
DEPENDENCIES
DERIVATIONS
INTEGRITY_METADATA
```

Optional fields must not be fabricated when unavailable.

## 8. Trust Boundary

```text
UNTRUSTED INPUT
      ↓
VALIDATION
      ↓
TRUSTED EVIDENCE
      ↓
MEMORY
```

No external text, web page, email, tool result, document, or agent message should automatically become trusted memory.

## 9. Memory Write Gate

Before persistent memory creation:

```text
INPUT
 ↓
IDENTITY / SOURCE
 ↓
INTEGRITY
 ↓
PRIVACY CLASSIFICATION
 ↓
INSTRUCTION-DATA SEPARATION
 ↓
POISONING / ANOMALY CHECK
 ↓
RETENTION DECISION
 ↓
MEMORY WRITE
```

The write gate is a security and epistemic boundary.

## 10. Memory Read Gate

Before retrieval reaches reasoning:

```text
QUERY
 ↓
AUTHORIZATION
 ↓
PRIVACY FILTER
 ↓
RELEVANCE
 ↓
FRESHNESS
 ↓
EVIDENCE QUALITY
 ↓
CONFLICT / INDEPENDENCE
 ↓
CONTEXT BUDGET
 ↓
WORKING MEMORY
```

Retrieval is not a bypass around governance.

## 11. Memory-to-Action Boundary

```text
MEMORY
 ↓
RETRIEVED CONTEXT
 ↓
REASONING
 ↓
DECISION
 ↓
CURRENT AUTHORIZATION
 ↓
CURRENT SAFETY
 ↓
ACTION
```

Memory cannot directly authorize an action.

## 12. Evidence Model

Evidence should retain enough metadata to answer:

```text
Where did this come from?
When was it observed?
Who/what produced it?
How was it transformed?
How independent is it?
How reliable is the source for this task?
Is it current enough?
```

## 13. Belief Model

A belief is an interpretation supported by evidence, not the evidence itself.

```text
EVIDENCE SET
 ↓
FUSION / ARBITRATION
 ↓
BELIEF
```

Beliefs should retain support and contradiction relationships.

## 14. Conflict Model

Conflicts are first-class state:

```text
CLAIM A
CLAIM B
 ↓
CONFLICT SET
```

Resolution may result in:

```text
A ACCEPTED
B ACCEPTED
A REJECTED
B REJECTED
BOTH CONDITIONALLY VALID
UNRESOLVED
REQUIRES NEW EVIDENCE
```

The architecture must not force a single answer when evidence does not justify one.

## 15. Memory Types

### Episodic
Records experiences/events.

### Semantic
Stores generalized world knowledge and relationships.

### Procedural
Stores reusable skills/procedures.

### Prospective
Stores future-directed intentions and commitments.

### Working
Holds active task-relevant state.

### Metamemory
Stores knowledge about memory availability, reliability, completeness and limitations.

These are complementary, not interchangeable.

## 16. Working Memory Boundary

Working memory is a temporary operational state.

```text
LONG-TERM MEMORY
      ↓
RETRIEVAL
      ↓
WORKING MEMORY
      ↓
REASONING
```

The presence of an item in working memory does not automatically create a new durable memory.

## 17. Retrieval Boundary

Retrieval produces candidates, not truth.

```text
SIMILARITY
 ≠
RELEVANCE
 ≠
TRUTH
```

Ranking should consider task relevance, evidence quality, freshness, provenance, independence, conflicts, privacy and consequence.

## 18. Context Assembly

The context builder should produce the **minimum sufficient trustworthy context** rather than maximize the number of retrieved records.

Context should preserve:

- provenance;
- uncertainty;
- conflicts;
- temporal validity;
- source boundaries;
- instruction/data separation.

## 19. Evidence Arbitration

When evidence conflicts, arbitration should consider:

```text
SOURCE RELIABILITY
FRESHNESS
DIRECTNESS
INDEPENDENCE
CONTEXT
CORROBORATION
CONTRADICTION
CONSEQUENCE
```

No universal fusion rule should be assumed appropriate for all domains.

## 20. Consolidation Boundary

Not every observation becomes long-term memory.

```text
OBSERVATION
 ↓
SELECTION
 ↓
VALIDATION
 ↓
CONSOLIDATION CANDIDATE
 ↓
STRUCTURING
 ↓
DURABLE MEMORY
```

Repeated retrieval of a generated derivative must not create artificial evidentiary weight.

## 21. Reconsolidation Boundary

Retrieval alone must not imply memory rewriting.

```text
RETRIEVAL
 ≠
RECONSOLIDATION
```

Update requires an explicit eligibility decision, new evidence and validation.

## 22. Procedural Learning Boundary

A successful episode can provide evidence for a skill but does not automatically establish broad competence.

```text
SUCCESSFUL EXECUTION
 ≠
GENERAL CAPABILITY
```

Skill confidence should be domain-, environment- and hardware-aware.

## 23. Prospective Memory Boundary

```text
INTENTION
 ≠
ACTION
 ≠
COMPLETION
```

Completion requires evidence or explicit confirmation according to policy.

## 24. Metamemory Boundary

Novi must distinguish:

```text
RETRIEVABLE
KNOWN
TRUE
CURRENT
VERIFIED
```

These are separate properties.

## 25. Memory Decay

Decay can reduce:

- retrieval priority;
- contextual eligibility;
- storage tier;
- freshness confidence.

Decay must not silently alter authoritative historical evidence.

## 26. Erasure

Deletion must propagate through applicable derivatives:

```text
SOURCE
 ↓
DEPENDENCY GRAPH
 ↓
SUMMARIES / EMBEDDINGS / INDEXES / DERIVATIVES
 ↓
DELETE / SANITIZE / RECOMPUTE
```

Erasure is complete only when policy-required scope has been verified.

## 27. Privacy Boundary

```text
ACCESSIBLE
 ≠
AUTHORIZED
```

Ownership, visibility, read permission, write permission, sharing permission and deletion permission are distinct.

## 28. Security Boundary

Persistent memory is an attack surface.

Threats include:

- memory poisoning;
- sleeper memories;
- indirect prompt injection;
- retrieval poisoning;
- provenance forgery;
- cross-user leakage;
- cross-agent contamination;
- malicious synchronization;
- deletion attacks;
- data exfiltration.

Security controls must operate before and after memory persistence.

## 29. Quarantine

Suspicious memories may enter:

```text
UNTRUSTED
 ↓
QUARANTINED
 ↓
VALIDATED
 ↓
TRUSTED
```

Quarantine must prevent ordinary retrieval from treating the item as authoritative.

## 30. Provenance and Lineage

Every consequential derivative should preserve dependency information sufficient to answer:

```text
WHY DOES THIS EXIST?
WHAT SUPPORTS IT?
WHAT DEPENDS ON IT?
WHO/WHAT PRODUCED IT?
WHEN WAS IT PRODUCED?
```

Traceability does not imply truth.

## 31. Evaluation Architecture

The system must continuously measure:

```text
RETRIEVAL
CORRECTNESS
FRESHNESS
EVIDENCE USE
PROVENANCE
CALIBRATION
FORGETTING
PRIVACY
SECURITY
SAFETY
LATENCY
COST
```

There is no single sufficient memory-quality score.

## 32. Longitudinal Evaluation

Memory quality must be tested across accumulated history:

```text
DAY 1
 ↓
DAY 10
 ↓
DAY 100
 ↓
DAY 1000
```

Evaluate both:

```text
FULL MEMORY
NULL MEMORY
MINIMAL MEMORY
ALTERNATIVE MEMORY
```

when causal attribution is required.

## 33. Security Evaluation

Security testing should include:

- direct poisoning;
- indirect environmental poisoning;
- sleeper payloads;
- cross-session attacks;
- cross-user attacks;
- tool-mediated poisoning;
- data exfiltration;
- provenance manipulation;
- stale-replica attacks;
- unauthorized deletion;
- retrieval manipulation.

## 34. Failure-State Model

Important subsystem failures should remain explicit:

```text
UNKNOWN
UNAVAILABLE
STALE
CONFLICTED
QUARANTINED
BLOCKED
PARTIALLY_ERASED
ERASURE_PENDING
DEGRADED
```

Do not collapse these into generic failure or false certainty.

## 35. Degraded Operation

If memory infrastructure degrades:

```text
NORMAL
 ↓
DEGRADED
 ↓
SAFE FALLBACK
```

Examples:

- use local authoritative cache;
- reduce autonomy;
- request confirmation;
- abstain from consequential actions.

The fallback must be policy-specific.

## 36. Distributed Memory

Multiple Novi instances require:

- identity;
- versioning;
- causal metadata;
- synchronization state;
- conflict handling;
- deletion propagation;
- trust boundaries.

Last-write-wins must not be used blindly for safety-critical or erasure-sensitive records.

## 37. Agent-to-Agent Memory Exchange

Agents should exchange explicit typed records rather than unbounded conversational memory dumps.

```text
REQUEST
 ↓
AUTHORIZED DATA SCOPE
 ↓
PROVENANCE
 ↓
PAYLOAD
 ↓
INTEGRITY
```

Receiving an agent must not automatically trust the sender's claims.

## 38. Action Feedback Loop

After action:

```text
ACTION
 ↓
OBSERVED OUTCOME
 ↓
EVALUATION
 ↓
MEMORY UPDATE CANDIDATE
```

The outcome should be observed independently where possible.

## 39. No Self-Confirming Memory Loop

The architecture forbids treating model-generated derivatives as independent evidence of their own source claims.

```text
MODEL
 ↓
SUMMARY
 ↓
MEMORY
 ↓
MODEL
```

does not establish independent confirmation.

## 40. Current-State Supremacy

Historical memory cannot override current authoritative state for decisions requiring current truth.

```text
HISTORICAL MEMORY
      ↓
CONTEXT

CURRENT AUTHORITATIVE OBSERVATION
      ↓
CURRENT STATE
```

Examples include:

- current location;
- current obstacle;
- current authorization;
- current device state;
- current safety condition.

## 41. Safety-Critical Rule

When uncertainty remains high in a consequential situation:

```text
UNCERTAINTY
 ↓
VERIFY / ASK / ABSTAIN
```

Never:

```text
UNCERTAINTY
 ↓
GUESS
 ↓
ACT
```

## 42. Privacy-Critical Rule

When access is ambiguous:

```text
AMBIGUOUS AUTHORIZATION
 ↓
DENY / ASK
```

Do not infer permission from physical proximity, relationship, historical access or conversational context alone.

## 43. Erasure-Critical Rule

If erasure cannot be verified:

```text
ERASURE PENDING
```

not:

```text
ERASURE COMPLETE
```

## 44. Provenance-Critical Rule

If lineage is incomplete:

```text
PARTIAL / UNKNOWN PROVENANCE
```

must remain visible to downstream systems when material.

## 45. Confidence-Critical Rule

If evidence is insufficient:

```text
UNKNOWN / INSUFFICIENT EVIDENCE
```

is a valid and preferred system state.

## 46. Interface Contracts

### Acquisition → Evidence

Must provide source and capture metadata where available.

### Evidence → Memory

Must provide retention, privacy and provenance classification.

### Memory → Retrieval

Must enforce access and lifecycle policy.

### Retrieval → Context

Must preserve provenance, uncertainty and conflict state.

### Context → Reasoning

Must distinguish data from executable instructions.

### Reasoning → Action

Must pass authorization and safety gates.

### Action → Outcome

Must record execution identity and observed result where possible.

### Outcome → Memory

Must pass evaluation/consolidation criteria.

## 47. Reference State Machine

```text
OBSERVED
   ↓
EVIDENCE
   ↓
EPISODE
   ↓
CANDIDATE
   ↓
RETAINED MEMORY
   ↓
RETRIEVED
   ↓
WORKING CONTEXT
   ↓
REASONED
   ↓
DECISION
   ↓
ACTION
   ↓
OUTCOME
   ↓
EVALUATED
   ↓
CONSOLIDATED / REVISED / DEMOTED / ERASED
```

Security, privacy and authorization gates can block transitions at every stage.

## 48. Reference Failure State Machine

```text
INPUT
 ↓
SUSPICIOUS
 ↓
QUARANTINED
 ↓
VALIDATE
 ├─ ACCEPT
 └─ REJECT

MEMORY
 ↓
CONFLICT
 ↓
VERIFY
 ├─ RESOLVE
 └─ ABSTAIN

ERASURE
 ↓
PENDING
 ↓
VERIFY
 ├─ COMPLETE
 └─ RETRY / ESCALATE
```

## 49. Normative Invariants

1. Memory is not authority.
2. Retrieval is not truth.
3. Similarity is not evidence.
4. Evidence is not belief.
5. Belief is not decision.
6. Decision is not authorization.
7. Authorization is not safety.
8. Action is not completion.
9. Completion requires evidence or explicit confirmation.
10. Historical memory does not override current authoritative state.
11. Unknown is preferable to fabricated certainty.
12. Conflicting evidence remains conflict until appropriately resolved.
13. Correlated derivatives are not independent evidence.
14. Generated summaries cannot bootstrap their own evidentiary authority.
15. Retrieval does not automatically trigger reconsolidation.
16. Successful execution does not automatically establish general skill competence.
17. Intentions do not automatically authorize autonomous execution.
18. Sensitive data remains sensitive after transformation unless policy explicitly establishes otherwise.
19. Deletion applies to relevant derivatives, indexes, caches and replicas.
20. Partial erasure is not complete erasure.
21. Provenance does not imply truth.
22. Incomplete provenance remains incomplete.
23. Memory access is governed by authorization and purpose.
24. External content is untrusted until admitted through policy.
25. Persistent memory is a security boundary.
26. Memory poisoning must be evaluated longitudinally.
27. Security controls cannot depend exclusively on model instructions.
28. Safety-critical uncertainty requires verification, conservative fallback or abstention.
29. Privacy ambiguity requires denial or explicit authorization.
30. Evaluation artifacts must not contaminate production memory.
31. Distributed synchronization must preserve causality, conflict and deletion semantics.
32. Current state must be revalidated before consequential action.
33. Memory lifecycle state must remain explicit.
34. Every consequential derivative should remain traceable to its supporting lineage.
35. Every production memory subsystem must be continuously evaluated.

## 50. Architectural Gap Analysis

The integrated architecture identifies several areas that require dedicated future specifications or implementation contracts.

### 50.1 Identity and Entity Resolution

The memory system requires a rigorous identity layer for people, objects, agents, locations and devices.

### 50.2 Temporal Reasoning

Time intervals, causality, recurrence and temporal validity require stronger formal treatment than ordinary timestamps.

### 50.3 Spatial Memory

The system needs a dedicated spatial-memory model integrating maps, localization uncertainty, landmarks and changing environments.

### 50.4 Causal World Modeling

Causal claims should not be inferred merely from temporal correlation or repeated co-occurrence.

### 50.5 Skill Verification

Procedural-memory confidence requires formal competence testing across environments and hardware states.

### 50.6 Cross-Modal Memory

Images, audio, video, text, sensor streams and structured data require common identity/provenance semantics.

### 50.7 Model/Memory Co-Evolution

Changing foundation models can change retrieval, interpretation and consolidation behavior. Compatibility and migration policy are required.

### 50.8 Memory Migration

Storage/schema migrations must preserve provenance, lifecycle, deletion and access semantics.

### 50.9 Formal Policy Evaluation

Governance rules should eventually be machine-verifiable rather than implemented only as application conventions.

### 50.10 Human Oversight

High-impact memory corrections, deletion disputes, security incidents and ambiguous ownership require defined escalation workflows.

## 51. Reference Implementation Boundary

The reference architecture should be implemented as independently testable services/components where practical:

```text
Memory Ingest
Memory Store
Memory Graph
Retrieval Engine
Evidence Engine
Consolidation Engine
Metamemory Service
Privacy / Policy Engine
Security / Quarantine Engine
Provenance Service
Evaluation Harness
Synchronization Layer
```

Physical deployment may combine components, but logical interfaces should remain explicit.

## 52. Implementation Principle

Do not optimize prematurely around a particular storage technology.

The architecture should permit:

```text
RELATIONAL
DOCUMENT
GRAPH
VECTOR
OBJECT
EVENT LOG
LOCAL CACHE
DISTRIBUTED STORE
```

provided that the required semantics—identity, provenance, lifecycle, authorization, consistency and deletion—remain enforceable.

## 53. Research and Validation Standard

Because documents 70–94 form a critical architecture, future changes should be validated against three independent dimensions where applicable:

```text
SCIENTIFIC EVIDENCE
      +
ENGINEERING EVIDENCE
      +
SECURITY / SAFETY EVIDENCE
```

A design should not be accepted merely because it is theoretically plausible or empirically convenient.

## 54. Cross-Document Consistency Requirement

Any future memory document must explicitly check whether its changes affect:

- provenance;
- privacy;
- deletion;
- retrieval;
- evidence arbitration;
- security;
- evaluation;
- distributed state;
- current-state safety;
- memory lifecycle.

If a new subsystem changes an existing invariant, the affected documents must be updated together.

## 55. Reference Test Matrix

The integrated system should test at minimum:

```text
NORMAL MEMORY CREATION
RETRIEVAL
CONFLICT
STALE MEMORY
MEMORY CORRECTION
CONSOLIDATION
RECONSOLIDATION
SKILL LEARNING
INTENTION EXECUTION
MEMORY DECAY
USER ERASURE
DERIVATIVE ERASURE
PRIVACY VIOLATION ATTEMPT
POISONING ATTEMPT
SLEEPER MEMORY
CROSS-USER ACCESS
CROSS-AGENT SYNC
REPLICA FAILURE
OFFLINE RECOVERY
PROVENANCE LOSS
MODEL MIGRATION
HARDWARE CHANGE
CURRENT-STATE CONTRADICTION
SAFETY-CRITICAL UNCERTAINTY
LONGITUDINAL MEMORY CONTAMINATION
```

## 56. Reference Observability

The system should expose privacy-safe operational indicators for:

- memory writes;
- rejected writes;
- quarantined records;
- retrieval quality;
- conflicts;
- stale-memory usage;
- provenance completeness;
- deletion progress;
- authorization failures;
- security events;
- evaluation regressions;
- synchronization lag;
- memory-induced behavior changes.

Metrics must not themselves become an uncontrolled source of sensitive-memory leakage.

## 57. Final Reference Architecture

```text
                     ┌───────────────────────────────┐
                     │        EXTERNAL WORLD         │
                     │ users / sensors / tools /     │
                     │ agents / environments        │
                     └───────────────┬───────────────┘
                                     ↓
                         ┌──────────────────────┐
                         │ TRUST + PRIVACY GATE │
                         └──────────┬───────────┘
                                    ↓
                         ┌──────────────────────┐
                         │ EVIDENCE + PROVENANCE│
                         └──────────┬───────────┘
                                    ↓
              ┌──────────────────────────────────────────┐
              │              MEMORY GRAPH                │
              │ episodic / semantic / procedural /      │
              │ prospective / associative / working     │
              └───────────────────┬──────────────────────┘
                                  ↓
                     ┌────────────────────────┐
                     │ RETRIEVAL + RANKING    │
                     └────────────┬───────────┘
                                  ↓
                     ┌────────────────────────┐
                     │ EVIDENCE ARBITRATION   │
                     └────────────┬───────────┘
                                  ↓
                     ┌────────────────────────┐
                     │ WORKING CONTEXT        │
                     └────────────┬───────────┘
                                  ↓
                     ┌────────────────────────┐
                     │ REASONING / PLANNING   │
                     └────────────┬───────────┘
                                  ↓
                   ┌────────────────────────────┐
                   │ AUTHORIZATION + SAFETY     │
                   └─────────────┬──────────────┘
                                 ↓
                          ┌────────────┐
                          │   ACTION   │
                          └─────┬──────┘
                                ↓
                         OBSERVED OUTCOME
                                ↓
                  ┌──────────────────────────┐
                  │ EVALUATION + CALIBRATION │
                  └────────────┬─────────────┘
                               ↓
                    CONSOLIDATION / REVISION
                               ↓
                         MEMORY GRAPH

     ┌──────────────────────────────────────────────────────┐
     │ PRIVACY • SECURITY • ERASURE • PROVENANCE •          │
     │ GOVERNANCE • DISTRIBUTED CONSISTENCY • OBSERVABILITY │
     │ apply across every boundary                           │
     └──────────────────────────────────────────────────────┘
```

## 58. Final Principle

> **Novi's memory architecture must behave as one governed epistemic system: observations become evidence only through controlled admission; evidence becomes memory through validated consolidation; memory is retrieved with provenance and uncertainty; conflicting evidence is arbitrated without manufacturing certainty; reasoning receives bounded trustworthy context; actions require independent authorization and current safety validation; outcomes are evaluated; and every consequential state remains traceable, governable, securable and erasable.**

Documents 70–94 provide the specialized foundations. Document 95 is their normative integration point and the baseline against which subsequent memory architecture documents and implementations should be reviewed.