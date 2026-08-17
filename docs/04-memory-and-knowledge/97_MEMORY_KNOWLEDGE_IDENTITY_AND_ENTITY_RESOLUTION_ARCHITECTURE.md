# 97 — Memory Knowledge Identity and Entity Resolution Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi represents, identifies, resolves, merges, splits, tracks and governs real-world entities across memory, knowledge, perception, agents, devices, locations and time.

This document is the first implementation of the P0 identity gap identified by document 96 and must conform to document 95's reference model.

## Core Principle

> **Novi must never confuse similarity of records with identity of the underlying entity. Entity resolution is an uncertainty-bearing inference process whose results must remain traceable, reversible and governed.**

## 1. Why Identity Comes First

Nearly every memory operation depends on knowing what a record refers to.

```text
OBSERVATION
   ↓
ENTITY
   ↓
EPISODE
   ↓
MEMORY
   ↓
RELATIONSHIP
   ↓
BELIEF
```

If identity is wrong, downstream memory can be attached to the wrong person, object, device, place or agent.

Consequences can include:

- privacy violations;
- false autobiographical memories;
- incorrect relationships;
- provenance corruption;
- unsafe actions;
- incorrect skill attribution;
- incorrect deletion;
- cross-user leakage.

## 2. Entity vs Record

```text
RECORD
→ representation stored somewhere

ENTITY
→ real-world or conceptual thing the record refers to
```

Multiple records can refer to one entity.

One record must not automatically be treated as a unique entity.

## 3. Entity Resolution

Entity resolution determines whether two or more records refer to the same entity.

The research literature treats this as a longstanding, difficult problem involving probabilistic, statistical, database and machine-learning approaches. [1][2] fileciteturn161file0 fileciteturn163file0

## 4. Identity Is Not a Similarity Score

```text
SIMILARITY
   ↓
MATCH HYPOTHESIS
   ↓
IDENTITY ASSESSMENT
```

A high similarity score is evidence for a possible match, not proof of identity.

## 5. Entity Classes

Novi should support at least:

```text
PERSON
ANIMAL
OBJECT
DEVICE
VEHICLE
PLACE
ROOM / AREA
ORGANIZATION
AGENT
SOFTWARE ENTITY
DOCUMENT
EVENT
CONCEPT
ACCOUNT
IDENTIFIER
```

Entity types should be extensible.

## 6. Entity Identity Is Scoped

Identity must be interpreted in context.

```text
ENTITY
 ×
DOMAIN
 ×
TIME
 ×
ENVIRONMENT
```

An identifier may be unique within one system but ambiguous globally.

## 7. Stable Entity ID

Every canonical entity should have an internal stable identifier independent of mutable attributes.

```text
ENTITY_ID = stable internal identity
```

Names, labels, locations and device properties can change without changing the entity ID unless a formal merge/split operation occurs.

## 8. External Identifiers

External identifiers should be represented separately:

```text
ENTITY
 ├─ internal ID
 ├─ external ID A
 ├─ external ID B
 └─ local alias
```

External identifiers have issuer, namespace, validity interval and provenance.

## 9. Identity Claims

Identity should be represented as explicit claims:

```text
RECORD A
   ↓
MATCHES
   ↓
ENTITY X
```

Each identity claim should retain:

- evidence;
- method;
- confidence;
- time;
- source;
- reviewer where applicable;
- version;
- provenance.

## 10. Identity Confidence

Identity confidence must remain separate from observation confidence.

```text
"I observed a person"
        ≠
"The person was Alice"
```

This follows the metamemory and evidence-separation principles of documents 86 and 91.

## 11. Match States

Identity resolution should support:

```text
MATCH
NON-MATCH
POSSIBLE MATCH
UNKNOWN
CONFLICTED
REQUIRES REVIEW
```

Binary match/no-match is insufficient for safety-critical ambiguity.

## 12. Candidate Generation / Blocking

Large entity sets require candidate reduction before expensive matching.

```text
ALL RECORDS
    ↓
BLOCKING / FILTERING
    ↓
CANDIDATE PAIRS
```

Research shows blocking and matching are distinct components of entity resolution, and modern embedding-based approaches must be evaluated for both effectiveness and scalability. [3] fileciteturn165file0

## 13. Progressive Resolution

For online systems, resolution may proceed progressively:

```text
FILTER
 ↓
WEIGHT
 ↓
PRIORITIZE
 ↓
MATCH
```

This permits high-value candidate decisions without requiring complete batch processing.

## 14. Matching Evidence

Candidate matching can use:

- exact identifiers;
- names;
- aliases;
- temporal consistency;
- spatial consistency;
- relationships;
- visual features;
- voice features;
- device fingerprints;
- behavioral patterns;
- shared context;
- external authoritative identifiers.

No single signal is universally authoritative.

## 15. Source Reliability

Identity evidence must inherit source reliability from document 75 and 91.

```text
SOURCE × SIGNAL × TASK × TIME
```

A sensor may be reliable for presence but unreliable for identity.

## 16. Multimodal Identity

Identity can be supported by multiple modalities:

```text
IMAGE
AUDIO
TEXT
LOCATION
DEVICE
BEHAVIOR
RELATIONSHIP
```

These must not be treated as independent evidence when they share a common upstream source.

## 17. Correlated Evidence

```text
CAMERA
 ↓
VISION MODEL
 ↓
TEXT DESCRIPTION
```

The three representations do not constitute three independent identity confirmations.

## 18. Temporal Identity

Entity identity must be time-aware.

Attributes can change:

```text
PERSON
 ├─ address at T1
 ├─ address at T2
 └─ address at T3
```

A changed attribute does not necessarily imply a new entity.

## 19. Spatial Identity

Location is evidence, not identity proof.

```text
SAME LOCATION
 ≠
SAME PERSON
```

Spatial consistency can increase or decrease match probability but must remain contextual.

## 20. Relationship Evidence

Relationships can support identity:

```text
A works with B
A lives with B
A owns device C
```

But relationship evidence can itself be stale or incorrect and therefore requires provenance.

## 21. Entity Attributes

Attributes should be modeled separately from identity:

```text
ENTITY
 ↓
ATTRIBUTE
 ↓
VALUE
 ↓
VALIDITY INTERVAL
```

This prevents changing attributes from causing accidental identity replacement.

## 22. Attribute History

Novi should preserve important attribute changes where retention permits:

```text
ADDRESS A [T1–T2]
ADDRESS B [T2–T3]
```

This supports temporal reasoning and avoids overwriting historical truth.

## 23. Entity Aliases

Aliases include:

- names;
- nicknames;
- usernames;
- device labels;
- organizational identifiers;
- temporary labels.

Aliases must retain provenance and validity.

## 24. Ambiguous Names

```text
"John"
```

must not automatically resolve to one entity when multiple plausible candidates exist.

Novi should retain ambiguity until evidence sufficiently distinguishes candidates.

## 25. Entity Resolution and Privacy

Identity resolution is inherently privacy-sensitive.

The system must apply access controls before exposing identity evidence.

```text
IDENTITY QUERY
 ↓
AUTHORIZATION
 ↓
MINIMUM NECESSARY EVIDENCE
 ↓
RESOLUTION
```

## 26. Identity Inference Boundary

Novi must distinguish:

```text
KNOWN IDENTITY
INFERRED IDENTITY
POSSIBLE IDENTITY
UNKNOWN IDENTITY
```

An inferred identity must not be represented as directly observed identity.

## 27. Sensitive Identity

Some identities are intrinsically sensitive or become sensitive through association.

Examples include identity linked to:

- medical information;
- financial information;
- precise location;
- private communications;
- protected records.

Resolution results must inherit applicable sensitivity policies.

## 28. Cross-User Boundary

One user's identity evidence must not silently resolve or enrich another user's private entity graph.

Shared identity records require explicit governance.

## 29. Entity Graph

Entities form a graph:

```text
PERSON A
 ├── owns → DEVICE B
 ├── knows → PERSON C
 ├── visited → PLACE D
 └── participated-in → EVENT E
```

Relationships must carry provenance and validity.

## 30. Identity vs Relationship

```text
A MATCHES B
```

is fundamentally different from:

```text
A KNOWS B
```

The identity layer should not infer relationships merely from matching records.

## 31. Merge

When records are determined to refer to the same entity:

```text
RECORD A ─┐
          ├→ ENTITY X
RECORD B ─┘
```

Merge operations must preserve the source records and provenance where retention permits.

## 32. Merge Is Not Destruction

Merging two records must not silently erase their historical identities or provenance.

A canonical entity can replace duplicate operational representations while retaining lineage.

## 33. Split

If an entity was incorrectly merged:

```text
ENTITY X
  ↓
SPLIT
 ↙   ↘
X1   X2
```

The system must identify affected memories, relationships, beliefs and decisions.

## 34. Merge/Split Versioning

Identity graph changes should be versioned:

```text
GRAPH v1
 ↓
MERGE
 ↓
GRAPH v2
```

Historical records should retain the graph version needed to interpret their identity references.

## 35. Identity Lineage

Every resolution decision should be traceable:

```text
MATCH DECISION
 ↓
FEATURES / EVIDENCE
 ↓
SOURCE RECORDS
 ↓
ORIGINAL OBSERVATIONS
```

This directly integrates document 92.

## 36. Identity Revision

New evidence can change identity assessment.

```text
POSSIBLE MATCH
 ↓
NEW EVIDENCE
 ↓
MATCH
```

or:

```text
MATCH
 ↓
CONTRADICTORY EVIDENCE
 ↓
CONFLICT / SPLIT
```

## 37. Identity Confidence Calibration

Identity confidence should be evaluated against known outcomes where ground truth exists.

Where ground truth is unavailable, alternative quality estimation methods can be used, but must be labeled as estimates. Recent research specifically addresses unsupervised ER evaluation when complete ground truth is unavailable. [4] fileciteturn164file0

## 38. Thresholds Must Be Risk-Aware

```text
LOW-CONSEQUENCE MATCH
→ ordinary threshold

HIGH-CONSEQUENCE MATCH
→ stronger evidence

SAFETY / PRIVACY CRITICAL
→ conservative threshold / verification
```

A single global identity threshold is inappropriate for all decisions.

## 39. Abstention

Novi should be able to say:

```text
"I cannot reliably determine whether these records refer to the same entity."
```

Abstention is preferable to a confident false match when consequences are high.

## 40. Human Review

Human review may be required for:

- ambiguous identity;
- high-impact merge;
- high-impact split;
- sensitive identity;
- safety-critical identity;
- disputed identity;
- insufficient evidence.

Human decisions must retain provenance and authorization context.

## 41. No Automatic Identity from Conversation

A conversational statement such as:

```text
"I'm Alice"
```

is evidence about identity, not necessarily authoritative identity proof.

Authority depends on context and policy.

## 42. No Automatic Identity from Appearance

Visual resemblance is not sufficient to establish identity for consequential decisions.

Identity claims should combine appropriate evidence and uncertainty.

## 43. No Automatic Identity from Location

```text
DEVICE AT HOME
 ≠
PERSON IS OWNER
```

Location and proximity can support candidate generation but should not independently establish ownership or identity.

## 44. Device Identity

Devices should have distinct identity semantics:

```text
PHYSICAL DEVICE
DEVICE INSTANCE
SOFTWARE INSTALLATION
NETWORK IDENTITY
ACCOUNT
```

These must not be conflated.

## 45. Agent Identity

Novi instances and external agents require:

- stable agent identity;
- instance identity;
- capability identity;
- trust domain;
- authentication state;
- provenance.

## 46. Location Identity

Locations require identity separate from coordinates.

```text
COORDINATE
 ≠
PLACE ENTITY
```

A place can persist while its coordinates or boundaries change.

## 47. Event Identity

Repeated descriptions of an event may refer to one event:

```text
OBSERVATION A
OBSERVATION B
OBSERVATION C
      ↓
EVENT X
```

Event resolution must consider temporal, spatial and causal consistency.

## 48. Document Identity

Different copies or versions of a document should not automatically be treated as separate conceptual documents.

Track:

```text
DOCUMENT ENTITY
VERSION
COPY
SOURCE
HASH / INTEGRITY
```

## 49. Identity and Provenance

Identity resolution decisions are themselves derived entities and must be represented in provenance.

```text
RECORDS
 ↓
MATCH ACTIVITY
 ↓
IDENTITY CLAIM
```

## 50. Identity and Deletion

If an entity is deleted or privacy-erased, dependent identity mappings must be evaluated.

```text
ENTITY ERASURE
 ↓
ALIASES
IDENTIFIERS
RELATIONSHIPS
MEMORY REFERENCES
INDEXES
CACHES
DERIVATIVES
```

This integrates document 87.

## 51. Identity and Security

Identity resolution is an attack surface.

Threats include:

- identity spoofing;
- record poisoning;
- malicious alias creation;
- false merges;
- malicious splits;
- identity graph manipulation;
- cross-user identity leakage;
- compromised sensor identity;
- replayed identifiers.

## 52. Identity Provenance Forgery

An attacker must not be able to create a convincing identity claim by fabricating source metadata.

Integrity mechanisms and trusted provenance are required for high-impact identity decisions.

## 53. Sybil / Clone Awareness

Multiple records can represent one attacker, and one legitimate entity can be represented by multiple records.

Therefore:

```text
MANY RECORDS
 ≠
MANY ENTITIES
```

and:

```text
ONE RECORD
 ≠
ONE UNIQUE ENTITY
```

## 54. Transitive Matching Risk

```text
A matches B
B matches C
```

does not automatically mean:

```text
A matches C
```

unless the matching relation is known to be safely transitive under the applicable identity model.

## 55. Cluster Constraints

Entity clusters should obey explicit constraints appropriate to the entity type.

For example, two records may not both represent the same physical device if they have mutually exclusive serial identifiers during overlapping validity periods.

Constraints must be domain-specific, not universally assumed.

## 56. Contradiction Detection

Identity resolution should detect contradictions such as:

- impossible temporal overlap;
- mutually exclusive identifiers;
- incompatible physical locations;
- incompatible ownership;
- incompatible device state.

Contradictions should reduce confidence or trigger review rather than being silently ignored.

## 57. Identity Graph Consistency

The identity graph should be periodically checked for:

- duplicate canonical entities;
- impossible merges;
- orphaned identifiers;
- stale relationships;
- conflicting attributes;
- circular ownership assumptions;
- privacy boundary violations.

## 58. Entity Lifecycle

```text
CANDIDATE
 ↓
PROVISIONAL
 ↓
CONFIRMED
 ↓
ACTIVE
 ↓
INACTIVE / HISTORICAL
 ↓
MERGED / SPLIT / ERASED
```

Lifecycle state must be distinct from identity confidence.

## 59. Provisional Entities

Novi may create a provisional entity when immediate association is useful but certainty is insufficient.

Example:

```text
UNKNOWN_PERSON_17
```

This is preferable to incorrectly assigning the observation to a known person.

## 60. Entity Resolution and Memory Admission

A memory involving uncertain identity should retain the uncertainty:

```text
EPISODE
 ↓
SUBJECT = PROVISIONAL ENTITY
 ↓
IDENTITY CONFIDENCE
```

Later resolution can update the relationship without rewriting the original observation.

## 61. Identity and Working Memory

Working memory may temporarily maintain candidate identities:

```text
Candidate A: 0.62
Candidate B: 0.31
Unknown: 0.07
```

Such values are illustrative only; production confidence must be calibrated.

## 62. Avoid False Precision

Do not present numerical identity confidence unless calibration supports a meaningful interpretation.

Otherwise use qualitative states:

```text
HIGH
MODERATE
LOW
AMBIGUOUS
UNKNOWN
```

## 63. Identity and Retrieval

Retrieval should support queries by:

- canonical entity;
- alias;
- historical identifier;
- relationship;
- temporal identity;
- provisional identity.

Results must preserve identity uncertainty.

## 64. Identity and Evidence Fusion

Identity evidence can be fused using the arbitration mechanisms of document 91.

No single fusion algorithm is mandated globally.

## 65. Identity and Consolidation

Consolidated semantic knowledge should reference canonical entity IDs rather than mutable surface names where possible.

## 66. Identity and Skill Memory

Procedural skill attribution must distinguish:

```text
SKILL EXECUTED BY ENTITY X
```

from:

```text
OBSERVATION OCCURRED NEAR ENTITY X
```

Identity uncertainty must propagate into skill confidence.

## 67. Identity and Prospective Memory

Intentions must attach to an authorized entity or agent with explicit ownership.

```text
INTENTION OWNER
 ≠
CURRENT OBSERVER
```

## 68. Identity and Access Control

Authorization should resolve the requesting principal before sensitive memory access.

```text
REQUESTER IDENTITY
 ↓
AUTHORIZATION POLICY
 ↓
MEMORY ACCESS
```

An uncertain requester identity should produce conservative access behavior.

## 69. Identity and Agent-to-Agent Exchange

Agent messages should identify:

- sending agent;
- sending instance;
- trust domain;
- message provenance;
- authentication/integrity state.

Receiving agents must validate these claims.

## 70. Identity Migration

When entity IDs or schemas change, migration must preserve:

- historical references;
- provenance;
- privacy constraints;
- deletion semantics;
- merge/split history.

## 71. Evaluation Dataset Design

Identity evaluation should include:

- exact matches;
- near duplicates;
- aliases;
- missing attributes;
- noisy attributes;
- contradictory attributes;
- temporal changes;
- spatial changes;
- multimodal evidence;
- adversarial records;
- cross-user boundary cases;
- merge/split cases.

## 72. Evaluation Metrics

Where ground truth is available:

- precision;
- recall;
- F1;
- false-match rate;
- false-non-match rate;
- calibration;
- cluster quality;
- latency;
- resource cost.

Where ground truth is incomplete, estimates must be clearly labeled. Research demonstrates that ground-truth-free evaluation can be useful but is itself an estimation problem. [4] fileciteturn164file0

## 73. Safety Evaluation

Test identity errors by downstream consequence:

```text
FALSE MATCH
 ↓
WRONG MEMORY
 ↓
WRONG BELIEF
 ↓
WRONG DECISION
```

The most important metric is not merely matching accuracy; it is **harm-weighted downstream impact**.

## 74. Privacy Evaluation

Test:

- unauthorized identity inference;
- cross-user leakage;
- sensitive attribute linkage;
- identity graph traversal abuse;
- deleted-identity reappearance;
- alias leakage.

## 75. Security Evaluation

Test:

- spoofed identifiers;
- poisoned records;
- false merges;
- false splits;
- malicious clustering;
- compromised sensors;
- replay attacks;
- provenance forgery;
- cross-agent identity spoofing.

## 76. Longitudinal Evaluation

Identity state must be evaluated over time.

```text
T1
 ↓
T2
 ↓
T3
 ↓
T100
```

Test whether old identity errors persist, propagate or contaminate newly consolidated memories.

## 77. Human Correction

When a user corrects identity:

```text
OLD IDENTITY CLAIM
 ↓
CORRECTION
 ↓
NEW IDENTITY CLAIM
 ↓
DEPENDENCY ANALYSIS
```

Affected downstream memories should be identified through document 92 lineage.

## 78. Correction Does Not Rewrite Observation

If an observation was recorded as:

```text
UNKNOWN_PERSON_17
```

and later resolved to Alice, the original observation remains an observation of the provisional entity. The later mapping is a separate identity assertion.

## 79. Merge Correction

Incorrect merges require impact analysis:

```text
MERGED ENTITY
 ↓
DEPENDENT MEMORIES
 ↓
DEPENDENT RELATIONSHIPS
 ↓
DEPENDENT BELIEFS
 ↓
DEPENDENT ACTIONS
```

The system should not silently rewrite all history without provenance.

## 80. Split Correction

When an entity is split, all affected references must be evaluated for reassignment or ambiguity.

## 81. Identity Tombstones

Erased or retired entity IDs may require privacy-minimized tombstones to prevent accidental recreation or synchronization conflicts.

Tombstones must not unnecessarily expose the erased identity.

## 82. Entity Resolution Under Uncertainty

The system should preserve distributions or candidate sets internally where appropriate rather than prematurely collapsing to one identity.

## 83. Decision Policy

```text
IDENTITY CERTAINTY HIGH
→ proceed if authorized

IDENTITY UNCERTAIN
→ gather evidence / ask / restrict action

IDENTITY CONFLICTED
→ resolve or abstain

IDENTITY UNKNOWN
→ do not fabricate identity
```

## 84. Current-State Verification

Historical identity cannot override current authentication or authorization state.

```text
HISTORICAL IDENTITY MEMORY
        ≠
CURRENT AUTHENTICATION
```

Current security systems remain authoritative.

## 85. Implementation Components

Logical components should include:

```text
Entity Registry
Identifier Registry
Alias Registry
Candidate Generator
Entity Matcher
Identity Evidence Store
Identity Graph
Merge/Split Manager
Identity Policy Engine
Identity Provenance Service
Identity Evaluation Harness
```

## 86. Storage Independence

The architecture must not mandate one storage technology.

Possible implementations include:

- relational stores;
- graph stores;
- document stores;
- vector indexes;
- event logs;
- object stores.

Identity semantics must remain enforceable independent of storage.

## 87. Performance

Large-scale resolution should use staged processing:

```text
COARSE FILTER
 ↓
CANDIDATE GENERATION
 ↓
EXPENSIVE MATCH
 ↓
CONSTRAINT CHECK
 ↓
ARBITRATION
```

This follows the broad blocking/matching separation in the literature. [1][3] fileciteturn161file0 fileciteturn165file0

## 88. Embeddings Are a Tool, Not an Authority

Embedding similarity can support blocking and candidate ranking, but embedding choice introduces tradeoffs in quality, computational overhead and scalability. [3] fileciteturn165file0

Therefore:

```text
EMBEDDING MATCH
 ≠
IDENTITY CONFIRMATION
```

## 89. Heterogeneous Data

Real-world entity sources can differ in structure, representation and semantics.

The system must explicitly account for heterogeneous matching rather than assuming a common schema. Recent research identifies representation and semantic heterogeneity as persistent ER challenges and highlights multimodal and human-in-the-loop directions. [2] fileciteturn162file0

## 90. Cross-Modal Future Compatibility

The identity model must support future multimodal evidence without changing the canonical identity abstraction.

```text
TEXT
IMAGE
AUDIO
VIDEO
SENSOR
STRUCTURED DATA
       ↓
COMMON IDENTITY MODEL
```

## 91. Research Limitations

The literature does not establish a universally optimal entity-resolution method.

Therefore this architecture does not mandate:

- one matcher;
- one embedding model;
- one probabilistic model;
- one clustering algorithm;
- one confidence threshold.

Method selection must be evaluated against Novi's domain, consequence profile, privacy requirements and available evidence.

## 92. Architectural Invariants

1. Record identity is distinct from entity identity.
2. Similarity is not identity.
3. Identity claims are evidence-bearing inferences.
4. Identity uncertainty must remain explicit.
5. Observation confidence is distinct from identity confidence.
6. External identifiers are namespaced and time-aware.
7. Mutable attributes do not automatically create new entities.
8. Multiple records can refer to one entity.
9. One record can remain ambiguous between entities.
10. Location is evidence, not identity proof.
11. Appearance is evidence, not identity proof.
12. Relationships are evidence, not identity proof.
13. Correlated modalities are not independent confirmations.
14. Transitive matching is not universally safe.
15. Merge operations preserve lineage.
16. Split operations propagate impact analysis.
17. Provisional entities are preferable to false certainty.
18. Identity decisions must respect privacy boundaries.
19. Identity resolution cannot grant authorization by itself.
20. Current authentication overrides historical identity memory.
21. Identity mappings participate in deletion analysis.
22. Identity provenance must remain traceable.
23. Identity confidence must be evaluated and calibrated where possible.
24. High-consequence identity decisions require stronger evidence.
25. Abstention is a valid identity result.
26. Ground-truth-free evaluation remains an estimate.
27. Embeddings are candidate-generation/matching tools, not authority.
28. Identity errors must be evaluated by downstream harm, not matching score alone.
29. Identity graph changes must be versioned.
30. Identity is a foundational dependency of memory, privacy, provenance, retrieval and action.

## 93. Integration With Document 95

97 conforms to the reference model by enforcing:

```text
OBSERVATION
 ↓
EVIDENCE
 ↓
ENTITY CLAIM
 ↓
MEMORY
 ↓
RETRIEVAL
 ↓
ARBITRATION
 ↓
REASONING
 ↓
AUTHORIZATION
 ↓
ACTION
```

Identity is never allowed to bypass:

- provenance;
- evidence arbitration;
- privacy;
- security;
- authorization;
- current-state validation;
- evaluation.

## 94. Integration With Document 96

97 resolves the first P0 gap:

**Identity / Entity Resolution.**

It also establishes prerequisites for:

- 98 temporal reasoning;
- 99 spatial memory;
- 100 causal world modeling;
- 101 cross-modal memory;
- 102 skill verification;
- 103 schema migration;
- 104 model/memory co-evolution;
- 105 machine-verifiable governance;
- 106 human oversight.

## 95. Final Principle

> **Novi should maintain stable identities without pretending certainty it does not possess: every identity is a governed, evidence-backed, time-aware hypothesis whose provenance can be inspected, whose confidence can change, whose merge or split can be reversed, and whose consequences can be traced through the entire memory architecture.**

Identity resolution is therefore not a convenience feature. It is the foundational semantic layer that prevents Novi from attaching the right memories to the wrong entities.