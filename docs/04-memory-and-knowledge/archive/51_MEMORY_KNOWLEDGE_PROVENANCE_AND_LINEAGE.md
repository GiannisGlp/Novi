# 51 — Memory Knowledge Provenance and Lineage

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi records the origin, evidence, transformations, dependencies, versions and history of important observations, memories, beliefs, knowledge, decisions and learned behavior.

The objective is that important claims remain auditable from their current representation back to the evidence that produced them.

## Core Principle

> **Every important derived claim must have a traceable lineage to its supporting evidence, and every transformation in that lineage must remain distinguishable from the original observation.**

---

## 1. Provenance vs Lineage

```text
PROVENANCE
Where did this item come from?

LINEAGE
How did evidence become this item over time?
```

Provenance may identify a source. Lineage describes the complete transformation chain.

---

## 2. Canonical Evidence Chain

```text
SOURCE
  ↓
MEASUREMENT / ASSERTION
  ↓
OBSERVATION
  ↓
INTERPRETATION
  ↓
MEMORY CANDIDATE
  ↓
MEMORY
  ↓
BELIEF / KNOWLEDGE CANDIDATE
  ↓
KNOWLEDGE
  ↓
PREDICTION / DECISION
  ↓
ACTION
  ↓
OUTCOME
```

Not every item passes through every stage.

---

## 3. Source Types

Potential sources include:

- camera;
- LiDAR;
- microphone;
- IMU;
- GNSS;
- thermal sensor;
- BMS;
- system telemetry;
- software event;
- user statement;
- explicit instruction;
- external document;
- local database;
- learned model;
- simulation;
- controlled experiment.

Source identity and reliability should be preserved.

---

## 4. Source Identity

Important source metadata may include:

- source ID;
- device/component ID;
- sensor/model version;
- calibration version;
- software version;
- timestamp;
- coordinate frame where relevant;
- acquisition mode;
- simulation/real-world status.

---

## 5. Observation Provenance

An observation should answer:

```text
What was observed?
When?
Where?
By which source?
Under what conditions?
With what uncertainty?
```

Raw sensor data may be stored separately and referenced by immutable IDs.

---

## 6. Human Assertions

User statements are provenance-bearing assertions.

Example:

```text
source = user
statement = "The mug belongs in the kitchen."
```

This does not automatically make the statement objective world knowledge.

---

## 7. Derived Observations

Perception systems may transform raw measurements into observations.

```text
RGB frames
 ↓
object detector
 ↓
object observation
```

The derived observation must retain references to the source frames/model/version.

---

## 8. Interpretation

Interpretation adds semantic meaning.

```text
observation:
object detected at position X

interpretation:
possible mug
```

Interpretation must retain its uncertainty and supporting observations.

---

## 9. Memory Candidate Lineage

A memory candidate should record:

- source events;
- observations;
- interpretation;
- reason for admission;
- confidence;
- timestamp;
- context;
- policy version.

---

## 10. Memory Lineage

A durable memory should retain its parent evidence references.

```text
memory_123
 ├── event_456
 ├── observation_789
 └── interpretation_321
```

Deleting or superseding a parent may require reevaluating the memory.

---

## 11. Knowledge Lineage

Knowledge promoted from memory should identify its supporting memories.

```text
knowledge_55
 ↓
memory_123
memory_125
memory_201
 ↓
events / observations
```

---

## 12. Multiple Supporting Sources

Important claims should be able to cite multiple independent sources.

Example:

```text
camera evidence
+
LiDAR evidence
+
repeated observations
 ↓
stronger spatial claim
```

Source independence must be considered when evaluating confidence.

---

## 13. Transformation Records

Every important transformation should record:

- input IDs;
- output ID;
- transformation type;
- component/model;
- version;
- timestamp;
- parameters where necessary;
- confidence/result metadata.

---

## 14. Model Provenance

ML-derived outputs should record:

- model identity;
- model version/hash where available;
- inference configuration;
- preprocessing version;
- postprocessing version;
- hardware/runtime where relevant.

This supports reproducibility and audit.

---

## 15. Prompt/Reasoning Provenance

Where an LLM materially contributes to a consequential derived claim, the system should retain sufficient structured provenance to identify:

- model/version;
- task type;
- input evidence references;
- retrieved memory references;
- policy/context version;
- output identifier.

The goal is evidence traceability, not storing unrestricted private chain-of-thought.

---

## 16. No Synthetic Evidence

An LLM-generated statement must never be presented as sensor evidence, user testimony or historical observation unless such evidence actually exists.

```text
model output
 ≠
sensor observation
```

---

## 17. Simulation Provenance

Simulation-derived evidence must be explicitly labeled.

```text
REAL
SIMULATED
HYPOTHETICAL
COUNTERFACTUAL
```

These categories must never silently merge.

---

## 18. External Knowledge Provenance

If Novi imports knowledge from a document or approved external source, provenance should include:

- source identifier;
- source version/date where available;
- acquisition time;
- extraction method;
- relevant section/page/span where practical;
- trust/evaluation status.

---

## 19. Knowledge Freshness

Provenance should support freshness evaluation.

Examples:

```text
current hardware state → highly time-sensitive
route knowledge → time-sensitive
historical event → immutable historical fact
stable scientific knowledge → slower-changing
```

Freshness does not automatically determine truth.

---

## 20. Versioning

Important derived objects should be versioned.

```text
belief_v1
 ↓
new evidence
 ↓
belief_v2
```

Historical versions remain auditable.

---

## 21. Supersession

A new belief can supersede an older belief without deleting it.

```text
old belief
status = superseded
reason = new evidence
replacement = new belief
```

---

## 22. Correction Lineage

Corrections should preserve:

- original claim;
- correction evidence;
- corrected claim;
- time of correction;
- reason;
- actor/process responsible.

This prevents historical revisionism inside memory.

---

## 23. Conflict Lineage

When evidence conflicts, the conflict should reference all relevant sources.

```text
conflict_42
 ├── claim_A
 │    └── source_1
 └── claim_B
      └── source_2
```

Resolution must not hide the existence of the original conflict.

---

## 24. Causal Lineage

Causal claims should link to:

```text
cause evidence
 ↓
causal hypothesis
 ↓
validation
 ↓
causal knowledge
```

This complements document 47.

---

## 25. Learning Lineage

A learned behavioral change should identify:

```text
behavior update
 ↓
learning candidate
 ↓
evaluation
 ↓
experiences
 ↓
outcomes
```

This allows Novi to answer why a behavior changed.

---

## 26. Decision Lineage

Important decisions should retain enough context to reconstruct their basis:

- goal;
- current state;
- relevant observations;
- memories;
- knowledge;
- policy version;
- model/version;
- decision proposal;
- validation result.

---

## 27. Action Lineage

Actions should connect:

```text
goal
 ↓
plan
 ↓
decision
 ↓
validated command
 ↓
execution
 ↓
outcome
```

This enables post-action diagnosis.

---

## 28. Memory-to-Action Trace

For consequential behavior Novi should be able to trace:

```text
action
 ↓
decision
 ↓
workspace
 ↓
retrieved memory
 ↓
knowledge
 ↓
source evidence
```

Not every action requires a full human-readable trace, but the system should retain appropriate machine-auditable references.

---

## 29. Why-Belief Queries

Novi should support queries such as:

```text
Why do you believe X?
What evidence supports X?
When did you learn X?
Who told you X?
Which sensors support X?
Has X ever been contradicted?
What changed your belief about X?
```

Responses should be generated from provenance records.

---

## 30. Evidence Quality

Provenance records should support evidence quality dimensions such as:

- reliability;
- independence;
- recency;
- directness;
- calibration quality;
- context match;
- corroboration;
- contradiction.

These dimensions are inputs to evaluation, not a universal single score.

---

## 31. Confidence Decomposition

Avoid one opaque confidence value where possible.

Represent relevant components such as:

```text
source reliability
observation confidence
identity confidence
semantic confidence
causal confidence
freshness
corroboration
```

This makes uncertainty more interpretable.

---

## 32. Provenance and Uncertainty

Uncertainty must travel with derived information.

```text
uncertain measurement
 ↓
uncertain observation
 ↓
qualified memory
 ↓
qualified knowledge
```

A transformation must not silently convert uncertainty into certainty.

---

## 33. Provenance and Memory Consolidation

Consolidation should merge compatible memories while retaining supporting lineage.

```text
memory A
memory B
memory C
 ↓
consolidated knowledge
 ↓
references A/B/C
```

---

## 34. Provenance and Forgetting

When raw data is deleted, derived objects must preserve only the lineage permitted by retention/privacy policy.

Possible states:

```text
source retained
source deleted
source redacted
source inaccessible
lineage incomplete
```

A knowledge item with incomplete lineage must not falsely claim complete evidence.

---

## 35. Privacy-Aware Lineage

Provenance itself can contain sensitive information.

Examples:

- location history;
- identity information;
- conversations;
- biometric references;
- private documents.

Access to lineage must follow the same or stronger authorization as the underlying information.

---

## 36. Deletion Propagation

Deletion policy should identify dependent objects.

```text
source deleted
 ↓
dependent memory
 ↓
dependent knowledge
 ↓
reevaluate / delete / redact
```

The exact behavior depends on legal, privacy and product policy.

---

## 37. Security and Integrity

Provenance must be protected from unauthorized mutation.

Important records should support:

- integrity checks;
- access control;
- append-only history where appropriate;
- versioning;
- audit events.

---

## 38. Tamper Detection

If provenance is altered unexpectedly, Novi should be able to detect:

```text
missing parent
changed source
invalid version
broken reference
unexpected deletion
```

Integrity failure should reduce trust in the affected derived information.

---

## 39. Storage Independence

Provenance semantics must not depend on one storage technology.

Possible implementations include:

- SQLite;
- relational databases;
- append-only event stores;
- local files;
- graph indexes;
- object storage where available.

The semantic lineage model remains canonical.

---

## 40. Distributed Lineage

When multiple processes or devices produce data, lineage records need:

- globally unique IDs;
- source identity;
- event time;
- logical ordering where needed;
- version/conflict information.

Network synchronization is optional; local operation remains authoritative for core functionality.

---

## 41. Merge Conflicts

If two stores independently modify a derived belief:

```text
store A → belief v2
store B → belief v3
```

The merge process must preserve both lineages until the conflict is resolved.

---

## 42. Provenance Graph

A graph representation may be useful:

```text
source
  ↓
observation
  ↓
interpretation
  ↓
memory
  ↓
belief
  ↓
knowledge
  ↓
decision
  ↓
action
  ↓
outcome
```

Graph storage is optional; the relationships are mandatory for important records.

---

## 43. DAG vs Cycles

Lineage transformations should normally form a directed acyclic graph.

Operational event/causal graphs may contain feedback loops, but provenance of a derived artifact must remain reconstructable without circular dependency.

---

## 44. Garbage Collection

Unused lineage can be compacted under retention policy.

Compaction must not break required auditability or create false claims about evidence.

---

## 45. Provenance Caching

Frequently requested lineage may be cached, but caches are derived data and must not become authoritative evidence.

---

## 46. Audit Events

Important provenance operations should themselves be auditable:

- creation;
- correction;
- supersession;
- deletion;
- redaction;
- merge;
- rollback;
- policy-driven migration.

---

## 47. Reproducibility

Where practical, Novi should be able to reproduce a derived result from retained inputs and component versions.

Exact bit-for-bit reproducibility is not always possible; the system should record limitations.

---

## 48. Determinism

Deterministic components should record deterministic version/configuration information.

Probabilistic model outputs should retain model/version and relevant inference metadata.

---

## 49. Model Migration

When changing models:

```text
model A
 ↓
old derived outputs

model B
 ↓
new derived outputs
```

Historical outputs should retain the provenance of the model that generated them.

Migration must not rewrite history without explicit versioned transformation.

---

## 50. Provenance and Testing

Tests should verify:

- source-to-memory tracing;
- memory-to-knowledge tracing;
- decision tracing;
- action tracing;
- conflict tracing;
- correction tracing;
- deletion propagation;
- versioning;
- distributed merges;
- tamper detection;
- model migration;
- simulation/real separation;
- uncertainty propagation;
- offline operation;
- crash recovery.

---

## 51. Provenance Failure Modes

The architecture should handle:

```text
MISSING_SOURCE
BROKEN_LINEAGE
UNKNOWN_SOURCE
CONFLICTING_SOURCE
STALE_SOURCE
DELETED_SOURCE
UNTRUSTED_SOURCE
MODEL_VERSION_UNKNOWN
INTEGRITY_FAILURE
```

These states must not be silently converted into confidence.

---

## 52. Graceful Degradation

If lineage is incomplete:

```text
complete provenance
 → high auditability

partial provenance
 → qualified claim

missing provenance
 → limited trust / possible rejection
```

---

## 53. Offline Operation

Core provenance recording must work without Wi-Fi, Bluetooth or cloud access.

Synchronization can occur later without changing the original event times or source identities.

---

## 54. Resource Awareness

Detailed lineage can become large.

Use:

- immutable IDs;
- references instead of duplication;
- compression;
- tiered retention;
- summaries;
- background compaction.

Important provenance must remain protected from aggressive cleanup.

---

## 55. Authority Boundary

Provenance explains where information came from. It does not itself grant authority.

```text
provenance
 ≠
authorization
```

A highly trusted source still cannot bypass safety policy.

---

## 56. Human-Readable Explanations

When Novi explains a belief or decision, it should use concise evidence-backed summaries.

Example:

> "I believe the hallway is blocked because LiDAR detected an obstacle there twice within the last minute, and the current map also shows the same obstruction."

The explanation must be traceable to actual records.

---

## 57. No Fabricated Explanations

If provenance does not contain enough evidence, Novi must say so.

```text
"I don't have enough evidence to explain why I believed that."
```

is preferable to a plausible invented explanation.

---

## 58. Architectural Invariants

1. Important derived claims retain traceable lineage.
2. Source evidence is distinct from interpretation.
3. Model output is distinct from physical observation.
4. User assertions retain their source identity.
5. Simulation and real-world evidence remain separate.
6. Historical versions are not silently rewritten.
7. Corrections preserve original lineage.
8. Conflicting evidence remains visible.
9. Uncertainty propagates through transformations.
10. Provenance does not grant authority.
11. Privacy applies to provenance itself.
12. Deletion may require reevaluation of dependent knowledge.
13. Important lineage is integrity-protected.
14. Offline provenance recording remains functional.
15. Storage technology is not the semantic authority.
16. Model migrations preserve historical provenance.
17. Missing provenance reduces trust rather than increasing certainty.
18. Consequential decisions can be traced to relevant evidence.
19. Human-readable explanations derive from provenance rather than fabricated narratives.
20. No LLM may manufacture evidence or provenance.

---

## 59. Final Principle

> **If Novi cannot explain where an important belief came from, how it changed, and what evidence supports it, that belief should not be treated as fully trustworthy.**

Provenance and lineage therefore form the audit spine of Novi's memory and knowledge system: observations remain distinguishable from interpretations, memories from knowledge, hypotheses from facts, and current beliefs from their historical predecessors.
