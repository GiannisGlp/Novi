# 87 — Memory Knowledge Memory Decay Forgetting and Controlled Erasure

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi manages the natural and policy-driven reduction of memory accessibility, intentional forgetting, deletion, sanitization and controlled erasure while preserving safety, auditability and privacy requirements.

## Core Principle

> **Forgetting, decay and deletion are different operations. Novi must be able to reduce the accessibility of information without pretending it never existed, and must be able to permanently erase information when policy requires it.**

## 1. Memory Lifecycle

```text
CREATED
   ↓
ACTIVE
   ↓
DECAYING / DEMOTED
   ↓
ARCHIVED / RESTRICTED
   ↓
DELETED / SANITIZED
```

Not every memory follows every stage.

## 2. Decay vs Forgetting vs Deletion

```text
DECAY
→ lower retrieval priority / accessibility

FORGETTING
→ intentionally stop retaining or using a memory under defined policy

DELETION
→ remove the retained data from its authoritative storage

SANITIZATION
→ remove or transform sensitive remnants and derivatives as required
```

These operations must remain machine-distinguishable.

## 3. Decay Is Not Truth Reduction

A memory becoming harder to retrieve does not mean the underlying event became less true.

```text
LOW RETRIEVAL PRIORITY
      ≠
LOW HISTORICAL TRUTH
```

## 4. Decay Dimensions

Memory can decay along different dimensions:

- retrieval priority;
- working-memory eligibility;
- cache lifetime;
- contextual relevance;
- confidence due to staleness;
- storage tier;
- indexing priority.

Decay should not automatically modify the original evidence record.

## 5. Time-Based Decay

Some memory classes can use time-based decay:

```text
recent
 ↓
aging
 ↓
low-priority
 ↓
archive / delete according to policy
```

Time alone must not erase safety, legal, audit or explicitly retained records when policy requires retention.

## 6. Task-Based Decay

A memory may become irrelevant to a task while remaining valuable elsewhere.

```text
TASK A relevance ↓
        ≠
GLOBAL memory deletion
```

## 7. Contextual Decay

A memory can decay from active context while remaining retrievable from long-term storage.

This is normal working-memory lifecycle behavior.

## 8. Access Decay

Repeated non-use can reduce retrieval ranking without deleting the record.

Retrieval systems should make this policy explicit.

## 9. Importance-Based Retention

Retention can consider:

- explicit user request;
- safety relevance;
- learning value;
- future usefulness;
- provenance/audit requirements;
- legal/policy requirements;
- privacy requirements;
- storage cost.

No single factor should silently override higher-priority governance.

## 10. Explicit Forget Requests

A user may request that Novi forget something.

The request should identify the intended scope where ambiguity exists:

```text
forget from working memory
forget from retrieval
forget the stored record
forget related derivatives
forget all copies where permitted
```

## 11. Forgetting Scope

Forgetting should support scoped operations:

- single memory;
- episode;
- entity relationship;
- task context;
- user-specific memory;
- memory category;
- derived summaries;
- embeddings/index entries;
- distributed replicas.

## 12. Deletion vs Suppression

```text
SUPPRESSED
→ retained but unavailable to ordinary retrieval

DELETED
→ authoritative record removed
```

Suppression must not be represented as deletion.

## 13. Privacy-Driven Erasure

Sensitive information may require accelerated deletion or restricted retention.

Privacy policy takes precedence over convenience of future retrieval where applicable.

## 14. Derived Memory Problem

A source memory can produce:

```text
SOURCE
 ↓
SUMMARY
 ↓
EMBEDDING
 ↓
PATTERN
 ↓
WORLD-MODEL ASSERTION
```

Deleting only the source may leave sensitive information in derivatives.

## 15. Deletion Propagation

When a source is erased, the system should evaluate dependent derivatives:

```text
SOURCE DELETED
      ↓
DEPENDENCY GRAPH
      ↓
IDENTIFY DERIVATIVES
      ↓
DELETE / SANITIZE / RECOMPUTE
```

## 16. Derived Knowledge Classification

Every derived artifact should ideally retain dependency lineage sufficient to determine whether it contains information derived from an erased source.

## 17. Aggregated Knowledge

Aggregated patterns require special handling.

If an aggregate can still reveal the erased individual's sensitive information, it may require recomputation or removal.

## 18. Irreversible Transformations

Some transformations make exact dependency tracing difficult.

The architecture should prefer lineage-preserving transformations for sensitive memory classes.

## 19. Embeddings

Embeddings are not automatically safe after source deletion.

If an embedding encodes deleted information, deletion policy should determine whether it must be removed or regenerated.

## 20. Indexes and Caches

Deletion must consider:

- vector indexes;
- full-text indexes;
- relational indexes;
- caches;
- replicas;
- materialized views;
- search snapshots.

An index must not resurrect deleted content.

## 21. Working-Memory Erasure

Sensitive information in active context should be removed when its retention window ends or deletion policy requires it.

The system should also consider temporary buffers and intermediate representations.

## 22. Logs and Telemetry

Memory deletion policy must account for logs and telemetry that may contain copied content or sensitive metadata.

Telemetry should use minimized identifiers where possible.

## 23. Backups

Backups can complicate deletion guarantees.

The architecture should define:

- backup retention;
- encryption;
- deletion schedules;
- restore behavior;
- post-restore re-erasure requirements.

A deleted memory should not silently return after restore.

## 24. Offline Copies

Novi instances operating offline may retain replicas temporarily.

Deletion synchronization must define how replicas learn about erasure requests.

## 25. Distributed Erasure

```text
ERASURE REQUEST
      ↓
AUTHORITATIVE STORE
      ↓
REPLICAS
      ↓
INDEXES / CACHES
      ↓
DERIVATIVES
```

Each layer needs a verifiable erasure state.

## 26. Erasure Conflicts

If one node deletes information while another modifies it concurrently, the deletion request must not be accidentally undone by last-write-wins synchronization.

Use explicit tombstones or equivalent deletion markers where appropriate.

## 27. Tombstones

A tombstone can record:

```text
MEMORY ID
ERASURE STATE
REQUEST TIME
SCOPE
VERSION
```

Tombstones themselves must be privacy-minimized and retained only as required to enforce deletion.

## 28. Reappearance Prevention

After deletion, a memory should not reappear because of:

- stale cache;
- replica synchronization;
- backup restoration;
- derived index;
- model-generated reconstruction;
- old client state.

## 29. Model Training / Adaptation

If deleted information was used to adapt a model or learned policy, the system must define whether and how that dependency can be removed.

The memory layer should not assume model-level unlearning is automatically achieved by deleting the source record.

## 30. Generated Memory

Generated summaries and narratives should be treated as derivatives.

They must not become independent evidence merely because they were generated repeatedly.

## 31. Memory Reconstruction After Deletion

If remaining information is insufficient to reconstruct a deleted memory, Novi must not infer the deleted content from vague remnants.

## 32. Forgetting and Autobiographical Continuity

Novi may have gaps in its autobiographical timeline.

```text
EPISODE A
   ↓
[ERASED / UNAVAILABLE]
   ↓
EPISODE C
```

The gap should not be filled with fabricated narrative.

## 33. User-Facing Erasure Language

Novi should distinguish:

```text
"I no longer have access to that memory."
```

from:

```text
"That event did not happen."
```

Deletion changes availability, not historical reality.

## 34. Memory Recovery

If deletion was reversible only because a retention window has not ended, recovery must be governed by explicit policy and authorization.

Permanent deletion should not be recoverable through ordinary interfaces.

## 35. Legal / Governance Retention

Some records may require retention for legitimate governance, safety or audit reasons.

User-facing forgetting must not silently bypass higher-priority legal or safety obligations where applicable.

## 36. Safety-Critical Records

Safety-relevant records may require controlled retention even when ordinary memories decay.

Access must remain restricted and purpose-limited.

## 37. Audit Records

An audit trail can document that an erasure occurred without retaining the erased content itself.

Example:

```text
MEMORY X
 → erased at time T
 → scope S
```

## 38. Privacy-Preserving Audit

Erasure audit metadata should avoid unnecessary reproduction of the deleted content.

## 39. Retention Classes

Memory can be assigned policy classes such as:

```text
EPHEMERAL
SHORT_TERM
STANDARD
IMPORTANT
SAFETY
AUDIT
USER_PINNED
RESTRICTED
```

Retention semantics must be explicitly defined for each class.

## 40. User-Pinned Memory

Pinned memories should not become immortal.

They remain subject to deletion, privacy, safety and governance policies.

## 41. Expiration

Expiration can automatically transition a memory to:

```text
ARCHIVED
RESTRICTED
DELETED
```

according to its retention class.

## 42. Memory Compaction

Compaction may remove redundant representations while preserving required semantics and provenance.

Compaction is not equivalent to deletion.

## 43. Safe Compression

Compression must not create a surviving summary that defeats a required erasure operation.

## 44. Forgetting and Retrieval

After a memory is demoted, retrieval ranking may decrease.

However, explicit retrieval requests may still surface retained information if authorization permits.

## 45. Forgotten Memory and New Evidence

If new independent evidence re-establishes a previously forgotten fact, Novi may learn it again.

This is not resurrection of the deleted record unless the old record itself returns.

## 46. Relearning

Relearned information should receive new provenance:

```text
OLD MEMORY → DELETED
NEW OBSERVATION → NEW MEMORY
```

## 47. Privacy-Preserving Relearning

A deletion request should not be interpreted as permission to immediately recreate the same sensitive memory from easily available sources unless policy explicitly permits it.

## 48. Memory Poisoning and Deletion

Attackers must not be able to erase or suppress important memories without authorization.

Deletion itself is a privileged operation.

## 49. Authorization

Erasure permissions should consider:

- requester identity;
- ownership;
- memory classification;
- legal/governance constraints;
- shared ownership;
- safety implications.

## 50. Confirmation

High-impact bulk deletion should require explicit confirmation and clear scope.

## 51. Bulk Erasure

Bulk operations should support:

- category filters;
- date ranges;
- entity scope;
- user scope;
- location scope;
- dependency scope.

Dry-run evaluation can show the likely impact before irreversible deletion.

## 52. Erasure Verification

After deletion, verify:

```text
SOURCE GONE
INDEX GONE
CACHE GONE
DERIVATIVES HANDLED
REPLICAS UPDATED
BACKUP POLICY APPLIED
```

Verification should avoid exposing deleted content.

## 53. Erasure Failures

If complete deletion cannot yet be verified:

```text
ERASURE PENDING
```

must remain distinct from:

```text
ERASURE COMPLETE
```

## 54. Partial Erasure

If some replicas are unreachable:

```text
LOCAL ERASED
REMOTE PENDING
```

The system must not report global deletion as complete prematurely.

## 55. Observability

Track privacy-safe metrics such as:

- decay transitions;
- deletion requests;
- erasure completion latency;
- failed erasures;
- replica lag;
- derivative cleanup;
- stale-cache detections;
- reappearance incidents.

Telemetry must itself follow retention rules.

## 56. Testing

Test:

- time-based decay;
- task-based demotion;
- explicit forgetting;
- single-record deletion;
- bulk deletion;
- derivative cleanup;
- embedding deletion;
- cache invalidation;
- index cleanup;
- backup restoration;
- offline replicas;
- concurrent updates;
- tombstones;
- reappearance prevention;
- model adaptation dependencies;
- autobiographical gaps;
- user-facing erasure language;
- authorization failures;
- malicious deletion attempts;
- dry-run scope accuracy;
- erasure verification;
- partial erasure states;
- safety/audit retention.

## 57. Architectural Invariants

1. Decay, forgetting, deletion and sanitization are distinct operations.
2. Reduced retrieval priority does not reduce historical truth.
3. Task-level irrelevance does not imply global deletion.
4. Suppression is not deletion.
5. Explicit erasure has a defined scope.
6. Derived artifacts are included in deletion analysis.
7. Embeddings and indexes cannot silently retain deleted information when policy requires removal.
8. Caches and backups cannot resurrect deleted memory.
9. Distributed deletion cannot be defeated by last-write-wins synchronization.
10. Deletion state is itself access-controlled and privacy-minimized.
11. Erasure completion must be verified before being reported as complete.
12. Partial erasure remains explicitly partial.
13. Deleted memories cannot be reconstructed into the same record without new authorized provenance.
14. Relearned information is a new memory with new provenance.
15. User-requested forgetting does not automatically override higher-priority governance requirements.
16. Safety/audit records can have controlled retention.
17. Pinned memories remain subject to deletion and governance.
18. Compaction is not deletion.
19. Generated summaries cannot bypass erasure requirements.
20. Memory deletion must not become an uncontrolled attack surface.

## 58. Final Principle

> **Novi should forget deliberately, decay gracefully, delete decisively when required, and propagate erasure through every representation that could otherwise preserve the information—while never confusing the disappearance of a record with proof that the underlying event never happened.**

Controlled forgetting makes Novi's memory system useful, privacy-aware, secure and governable rather than an irreversible accumulation of everything it has ever encountered.