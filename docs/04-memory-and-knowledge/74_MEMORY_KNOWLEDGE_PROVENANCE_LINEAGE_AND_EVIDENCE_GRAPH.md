# 74 — Memory Knowledge Provenance, Lineage and Evidence Graph

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the provenance and evidence graph that allows Novi to trace information from its origin through observation, ingestion, transformation, inference, memory, knowledge, decisions, and actions.

## Core Principle

> **Every important belief should be traceable to the evidence and transformations that produced it, with uncertainty and provenance preserved throughout the chain.**

Novi must not merely remember *what* it believes. It must be able to determine, where policy and retained evidence permit, *why* it believes it.

## 1. Evidence Graph

Conceptually:

```text
SOURCE
  ↓
OBSERVATION
  ↓
EVENT
  ↓
EXTRACTION / TRANSFORMATION
  ↓
CLAIM
  ↓
VALIDATION
  ↓
INFERENCE
  ↓
MEMORY
  ↓
KNOWLEDGE
  ↓
DECISION
  ↓
ACTION
  ↓
OUTCOME
```

Each edge should identify the relationship rather than implying all nodes have the same evidentiary status.

## 2. Provenance vs Truth

Provenance answers:

> Where did this information come from and how was it transformed?

It does not automatically answer:

> Is the information true?

A perfectly traceable claim can still be false.

## 3. Evidence Classes

The graph should distinguish at minimum:

```text
DIRECT_SENSOR_OBSERVATION
USER_STATEMENT
DOCUMENT_CONTENT
EXTERNAL_SOURCE
REMOTE_AGENT_OBSERVATION
DERIVED_MEASUREMENT
MODEL_INFERENCE
MEMORY_RECALL
KNOWLEDGE_PROJECTION
DECISION
ACTION_OUTCOME
```

## 4. Entity Types

Evidence-graph entities may include:

- source;
- sensor;
- file/document;
- observation;
- event;
- claim;
- memory;
- knowledge object;
- model output;
- decision;
- action;
- outcome;
- agent;
- user;
- location;
- map artifact;
- transformation;
- validation result.

## 5. Activities

Transformations should be represented as activities such as:

```text
INGEST
PARSE
OCR
TRANSCRIBE
DETECT
CLASSIFY
FUSE
SUMMARIZE
RETRIEVE
INFER
VALIDATE
PROMOTE
MERGE
REVISE
DELETE
```

## 6. Agents

The graph should identify the agent responsible for a meaningful activity where appropriate:

- Novi subsystem;
- model;
- sensor;
- user;
- remote agent;
- external service.

## 7. Relationship Types

Useful relationships include:

```text
DERIVED_FROM
OBSERVED_BY
GENERATED_BY
EXTRACTED_FROM
SUPPORTED_BY
CONTRADICTS
SUPERSEDES
VALIDATED_BY
REJECTED_BY
CAUSED_BY
RESULTED_IN
LOCATED_AT
TEMPORALLY_PRECEDES
```

The relationship vocabulary should remain explicit and versioned.

## 8. Source Identity

A source node should retain sufficient identity to distinguish:

```text
which sensor
which document
which URL/service
which agent
which user
which model
```

Source identity is not necessarily source authority.

## 9. Sensor Provenance

For sensor observations, preserve where practical:

- sensor type;
- sensor identifier;
- calibration version;
- timestamp;
- pose/location;
- measurement uncertainty;
- firmware/software version;
- processing pipeline.

## 10. Document Provenance

For documents, preserve:

- document identity;
- version;
- source location;
- page/section/cell/timecode where applicable;
- parser/OCR/transcription version;
- extraction method.

## 11. External Source Provenance

External information should retain:

- source identity;
- retrieval time;
- publication/update time where available;
- retrieval method;
- source version or digest where practical;
- relevant validation information.

## 12. Remote Agent Provenance

Agent-provided information must preserve:

```text
agent identity
agent event ID
agent observation time
agent model/software context
agent source evidence where shared
```

## 13. Transformation Lineage

Every material transformation should be traceable:

```text
raw image
 ↓ OCR v4
text
 ↓ summarizer v2
summary
 ↓ extraction
claim
```

The claim does not replace the underlying evidence.

## 14. Lossy Transformations

Summaries, compression, aggregation and other lossy transformations must be marked as derived.

They should not be treated as equivalent to the original evidence.

## 15. Evidence Preservation

For important claims, Novi should retain or reference the supporting evidence required to verify the claim, subject to privacy and retention constraints.

## 16. Evidence Availability States

A provenance reference may be:

```text
AVAILABLE
RESTRICTED
EXPIRED
DELETED
UNAVAILABLE
UNKNOWN
```

A claim whose supporting evidence was deleted must not falsely appear fully verifiable.

## 17. Provenance Degradation

When evidence is removed or becomes unavailable:

```text
knowledge
  ↓
supporting evidence unavailable
  ↓
provenance incomplete
  ↓
confidence/verification status updated where required
```

Deletion must not fabricate certainty.

## 18. Claim Nodes

A claim should represent a proposition separately from its evidence.

Example:

```text
Claim: "The room contains a chair"
```

may be supported by:

```text
camera observation
LiDAR observation
user statement
```

## 19. Multiple Evidence

Claims can have multiple supporting sources.

Support should retain source independence information where known.

## 20. Correlated Evidence

The graph should represent common upstream dependencies where practical.

```text
Source X
 ↙     ↘
A       B
 \     /
  Claim
```

A and B are not independent if both derive from X.

## 21. Contradictory Evidence

Contradictions are first-class graph relationships.

```text
Claim A
   ↕ CONTRADICTS
Claim B
```

The graph must not silently collapse them into one statement.

## 22. Confidence

Confidence should be associated with the relevant claim/inference rather than treated as a universal property of the source.

Confidence should consider:

- evidence quality;
- independence;
- uncertainty;
- recency;
- context;
- model reliability;
- validation method.

## 23. Uncertainty Propagation

Transformations should propagate relevant uncertainty.

```text
uncertain measurement
      ↓
uncertain interpretation
      ↓
uncertain inference
```

False precision is prohibited.

## 24. Temporal Context

Claims should retain temporal validity where relevant:

```text
observed_at
valid_from
valid_until
superseded_at
```

A historical claim must not silently become a current claim.

## 25. Spatial Context

Embodied observations may require:

- coordinate frame;
- location;
- pose;
- map version;
- spatial uncertainty.

This is critical for Novi's future spatial memory and exploration maps.

## 26. Knowledge Promotion

A claim becomes durable knowledge through an explicit promotion process:

```text
CLAIM
 ↓
EVIDENCE EVALUATION
 ↓
VALIDATION
 ↓
POLICY CHECK
 ↓
PROMOTION
```

The promotion activity remains part of lineage.

## 27. Knowledge Revision

When knowledge changes:

```text
Knowledge v1
    ↓
new evidence
    ↓
Knowledge v2
```

The graph should retain the relationship between versions where retention permits.

## 28. Supersession

Superseding a claim does not necessarily mean the previous claim was false.

It may mean:

- newer evidence;
- changed circumstances;
- narrower scope;
- corrected interpretation.

## 29. Decision Provenance

Important decisions should be traceable to:

```text
decision
 ↓
policy
 ↓
knowledge/evidence
 ↓
observations
```

This is especially important for safety-related decisions.

## 30. Action Provenance

Actions should retain causal links to the decision that authorized them.

```text
observation
 ↓
interpretation
 ↓
decision
 ↓
action
```

## 31. Outcome Feedback

Where safe and useful, outcomes can be connected back to the action:

```text
action
 ↓
outcome
 ↓
evaluation
 ↓
learning candidate
```

An outcome does not automatically prove the original decision was correct; confounding factors must be considered.

## 32. Learning Lineage

Learning derived from experience should retain:

- experiences;
- outcomes;
- validation;
- context;
- model/algorithm version;
- promotion decision.

## 33. Model Provenance

Model-generated information should retain, where required:

- model identity;
- model version;
- configuration;
- relevant tool context;
- retrieval context;
- generation time.

## 34. Tool Provenance

If an answer depends on a tool call:

```text
claim
 ↓
tool result
 ↓
tool invocation
 ↓
source
```

The tool result should not be represented as independent evidence from the source it retrieved.

## 35. Retrieval Provenance

A retrieved memory should preserve the distinction between:

```text
original evidence
retrieval event
model interpretation
```

Retrieval does not create new evidence.

## 36. Repeated Recall

Repeated retrieval of the same memory must not artificially increase confidence.

```text
same evidence × 100 recalls
 ≠
100 independent confirmations
```

## 37. User Statements

User-provided information should retain provenance as a user statement.

A user statement can be highly useful without being automatically treated as independently verified fact.

## 38. Identity-Sensitive Evidence

Evidence concerning identity, biometrics, location or other sensitive domains requires stronger authorization and conservative provenance handling.

A recognition result is not itself proof of identity unless the relevant identity architecture establishes sufficient confidence and authority.

## 39. Privacy Labels

Provenance objects inherit or carry privacy classification.

The evidence graph must not become a side channel exposing private source relationships.

## 40. Access-Controlled Lineage

Users/agents may have permission to access a claim but not the underlying evidence.

The graph therefore supports:

```text
CLAIM = visible
EVIDENCE = restricted
```

The system must accurately communicate that the claim is not directly inspectable by the requester.

## 41. Redaction

When evidence is redacted:

```text
claim
 ↓
supporting evidence
 ↓
redacted representation
```

The graph should retain appropriate provenance metadata without exposing restricted content.

## 42. Deletion

Deleting evidence follows document 63 and the lifecycle policies.

Dependent claims and knowledge must be evaluated for whether their support remains sufficient.

## 43. Evidence Revocation

If a source is later determined to be compromised or invalid:

```text
source revoked
 ↓
affected evidence identified
 ↓
affected claims identified
 ↓
knowledge re-evaluated
```

The system should support impact analysis.

## 44. Blast Radius Analysis

The evidence graph should make it possible to ask:

> Which knowledge depends on this source?

and:

> Which decisions/actions were influenced by this claim?

This is essential for security incidents and data-quality failures.

## 45. Quarantine

If evidence becomes suspicious:

```text
source/evidence
 ↓
QUARANTINED
 ↓
affected downstream knowledge marked for review
```

Quarantine should not silently erase provenance.

## 46. Evidence Weighting

Evidence weighting should remain domain-specific.

A high-quality local LiDAR observation may be more relevant to immediate obstacle state than an old web page, while an official historical document may be more authoritative for a historical fact.

## 47. Current vs Historical Evidence

The graph must support both:

```text
WHAT WAS TRUE THEN?
WHAT IS SUPPORTED NOW?
```

without collapsing them.

## 48. Evidence Graph Queries

Useful queries include:

```text
Why does Novi believe X?
What supports X?
What contradicts X?
Where did X originate?
Which transformations produced X?
When was X learned?
When was X valid?
Which sources support X?
Which sources are correlated?
What knowledge depends on source Y?
What decisions depended on X?
```

## 49. Explainability

Provenance should support concise explanations without exposing protected data.

Example:

```text
"I believe X because of two recent local observations."
```

If evidence is restricted:

```text
"I have supporting evidence that I cannot disclose under current access policy."
```

Never fabricate citations or evidence.

## 50. Evidence Graph and Memory Retrieval

Memory retrieval can use graph relationships alongside lexical/vector retrieval.

```text
semantic search
      +
provenance graph
      +
temporal constraints
      +
spatial constraints
      ↓
contextual result
```

## 51. Evidence Graph and Distributed State

When knowledge synchronizes across agents, provenance references must remain meaningful across namespaces/devices.

Remote identifiers should retain source-agent context.

## 52. Evidence Graph and Causality

The graph complements the event log:

```text
EVENT LOG
 = temporal history

EVIDENCE GRAPH
 = semantic lineage and support relationships
```

They should interoperate without becoming one indistinguishable structure.

## 53. Evidence Graph and Conflict Resolution

Conflict resolution should consume graph information such as:

- provenance;
- independence;
- causal ordering;
- source reliability;
- temporal validity;
- transformation history.

## 54. Evidence Graph Integrity

Important provenance records should have integrity protection appropriate to their threat model.

A broken lineage link should produce an explicit integrity/availability state rather than silently being repaired with guessed relationships.

## 55. Graph Cycles

The system must detect problematic cycles.

For example:

```text
Claim A supports Claim B
Claim B supports Claim A
```

may indicate circular reasoning rather than independent evidence.

## 56. Self-Support

Novi must prevent:

```text
model generates claim
 ↓
claim stored
 ↓
claim retrieved
 ↓
model cites claim
 ↓
claim appears validated
```

Persistence cannot create independent evidence.

## 57. Provenance Depth

The system should support bounded lineage traversal to prevent pathological graph growth while preserving the ability to trace critical claims deeply enough for audit.

## 58. Storage Strategy

The evidence graph can be implemented using appropriate relational, graph, document or hybrid storage.

The architecture does not require a particular database technology.

The logical provenance model must remain storage-independent.

## 59. Performance

Provenance queries must not block real-time safety or motor-control loops.

Critical cognition should use bounded, cached or precomputed provenance views where necessary.

## 60. Offline Operation

The evidence graph must remain usable locally without Wi-Fi or cloud services for locally available evidence.

Connectivity may add external lineage but cannot be required for local provenance.

## 61. Synchronization

Distributed provenance synchronization must preserve:

- source identity;
- event IDs;
- graph relationships;
- versions;
- privacy restrictions;
- deletion state.

## 62. Testing

Test:

- missing provenance;
- broken lineage;
- conflicting sources;
- correlated sources;
- circular reasoning;
- self-support;
- deleted evidence;
- revoked sources;
- restricted evidence;
- cross-device identifiers;
- event/graph mismatch;
- timestamp inconsistencies;
- transformation version mismatch;
- malicious provenance injection;
- graph explosion;
- performance under large lineage chains;
- offline synchronization;
- privacy side channels.

## 63. Architectural Invariants

1. Provenance does not equal truth.
2. Important claims remain traceable to supporting evidence where retained and authorized.
3. Transformations preserve lineage.
4. Lossy transformations are marked as derived.
5. Contradictory evidence is represented explicitly.
6. Correlated evidence is not counted as independent merely because it appears in multiple nodes.
7. Repeated retrieval does not increase evidentiary weight.
8. Model output cannot self-validate through memory persistence.
9. Evidence deletion can degrade verifiability and must be represented accurately.
10. Revoked sources trigger downstream impact evaluation.
11. Privacy restrictions apply to provenance itself.
12. Claims may be visible while supporting evidence remains restricted.
13. Event causality and evidence lineage remain related but distinct concepts.
14. Provenance must not introduce unsafe latency into real-time control.
15. Offline local provenance remains functional without connectivity.
16. Provenance integrity failures are explicit states, not silently repaired guesses.
17. Decisions and important actions retain causal links to their supporting information where policy permits.

## 64. Final Principle

> **Novi's knowledge should have a memory of its own origin.**

The evidence graph provides that origin story: where information came from, what transformed it, what supported or contradicted it, when it was valid, how it became knowledge, and which decisions depended on it. This makes Novi's memory auditable, revisable, privacy-aware, and resistant to false certainty.