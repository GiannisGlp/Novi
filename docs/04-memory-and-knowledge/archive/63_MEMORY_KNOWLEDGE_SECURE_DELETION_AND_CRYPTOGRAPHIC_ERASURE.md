# 63 — Memory Knowledge Secure Deletion and Cryptographic Erasure

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi securely deletes or restricts memory and knowledge across authoritative records, indexes, embeddings, graph projections, caches, replicas, backups and other derived representations.

This document distinguishes ordinary logical deletion from security-oriented sanitization and cryptographic erasure. The implementation must use storage-specific mechanisms rather than assuming that deleting a file or database row makes underlying data unrecoverable.

## Research Basis

This architecture is informed by:

- **NIST SP 800-88 Rev. 2 (2025)**, which defines media sanitization as rendering target data infeasible to access for a defined level of effort and provides guidance for sanitization methods, including cryptographic erase. NIST Rev. 2 supersedes Rev. 1. citeturn0search8
- **UK ICO guidance on the right to erasure**, which states that erasure is not absolute, requires appropriate processes and methods, and addresses live systems, recipients and backups. The ICO specifically notes that backup data may remain temporarily where it is put "beyond use" and is not used for another purpose, subject to the applicable circumstances and retention schedule. citeturn1view1
- **ICO storage-limitation guidance**, which emphasizes defined retention periods, periodic review, and erasing or anonymising information when it is no longer needed. citeturn0search3

These sources provide guidance; legal applicability must be assessed for the final product, deployment and jurisdiction.

---

## 1. Core Principle

> **Deleting a pointer is not the same as securely erasing information. Novi must know which representations contain or can reconstruct the protected information and apply the appropriate deletion, restriction or sanitization method to each.**

---

## 2. Deletion Vocabulary

Novi must distinguish:

```text
LOGICAL DELETE
Record is removed from normal application retrieval.

RESTRICT
Record remains stored but cannot be processed for the restricted purpose.

TOMBSTONE
A durable marker records that a protected object must not be recreated or re-synchronized.

REDACTION
Specific content is removed while permitted surrounding structure remains.

ANONYMIZATION
Information is transformed so that the person is no longer identifiable under the applicable standard.

PURGE / SANITIZATION
Storage is processed so recovery of the target information is infeasible for the defined threat/effort level.

CRYPTOGRAPHIC ERASE
Data becomes inaccessible by securely destroying the cryptographic key(s) needed to decrypt it.
```

These terms must not be used interchangeably.

---

## 3. Deletion Intent

A deletion operation must identify its intent, for example:

```text
USER_REQUEST
RETENTION_EXPIRY
PRIVACY_POLICY
SECURITY_INCIDENT
ACCOUNT_DELETION
MEMORY_CORRECTION
RESOURCE_PRESSURE
DEVICE_DISPOSAL
MODEL_DATASET_PURGE
```

Different intents can require different scopes and assurance levels.

---

## 4. Delete the Logical Object First

The first safety boundary is removal from ordinary retrieval:

```text
DELETE REQUEST
   ↓
mark unavailable to normal cognition
   ↓
prevent new retrieval
   ↓
propagate deletion
```

This prevents a deletion operation from racing with normal cognition and exposing data that the user has already requested to remove.

---

## 5. Authoritative Record

Deletion must identify the authoritative record(s) representing the memory.

```text
memory_id
source_event_ids
provenance_ids
entity_ids
knowledge_dependencies
```

The system must not assume that one row or file represents the entire memory.

---

## 6. Dependency Graph

Before final deletion, Novi should determine relevant dependents:

```text
source
 ↓
observation
 ↓
memory
 ↓
consolidated memory
 ↓
knowledge
 ↓
embedding
 ↓
graph relationships
 ↓
cache
 ↓
replica / backup
```

The exact graph depends on the implementation.

---

## 7. Deletion Propagation

A deletion request should produce a propagation plan:

```text
TARGET
 ↓
AUTHORITATIVE STORE
 ↓
LEXICAL INDEX
 ↓
VECTOR INDEX
 ↓
GRAPH
 ↓
TEMPORAL/SPATIAL INDEXES
 ↓
CACHE
 ↓
REPLICAS
 ↓
BACKUPS
 ↓
DERIVED ARTIFACTS
```

Some components may use a tombstone rather than immediate physical deletion.

---

## 8. Tombstones

A tombstone prevents deleted objects from being recreated during synchronization or delayed processing.

Example:

```text
memory_123
status = DELETED
version = 7
```

A replica receiving version 6 must not resurrect the object.

Tombstones themselves should contain only the minimum information necessary to enforce deletion.

---

## 9. Delete-Wins Synchronization

For an explicitly authorized deletion, the synchronization layer must have a defined delete-wins policy or equivalent mechanism sufficient to prevent resurrection.

Concurrent legitimate changes require conflict policy rather than blind overwrite.

---

## 10. Idempotent Deletion

Repeating a deletion request should be safe.

```text
DELETE(memory_123)
DELETE(memory_123)
```

The second operation should not create an error that causes the overall deletion workflow to fail unnecessarily.

---

## 11. Deletion State Machine

Suggested states:

```text
REQUESTED
 ↓
AUTHORIZED
 ↓
BLOCKED_FROM_RETRIEVAL
 ↓
PROPAGATING
 ↓
DEPENDENCIES_PROCESSED
 ↓
SANITIZED / BEYOND_USE
 ↓
VERIFIED
 ↓
COMPLETED
```

Possible exception states:

```text
PARTIAL
DEFERRED
FAILED
REQUIRES_REVIEW
```

---

## 12. Race Conditions

Deletion must be safe against concurrent:

- reads;
- writes;
- consolidation;
- indexing;
- synchronization;
- backup creation;
- model training/export.

A deleted object must not re-enter active memory through a concurrent pipeline.

---

## 13. Stop New Derivatives

Once deletion is authorized, Novi should prevent new derived artifacts from being generated from the target while deletion is executing.

```text
DELETION LOCK / POLICY STATE
        ↓
no new embeddings
no new summaries
no new graph projections
no new learning artifacts
```

Where a global stop is too expensive, affected object IDs should be blocked.

---

## 14. Embeddings

Deleting a source memory requires identifying its embeddings.

```text
memory
 ↓
embedding(s)
```

Embeddings are derived representations and can themselves reveal information through similarity or reconstruction attacks; they therefore cannot automatically be considered harmless after the source text is deleted.

---

## 15. Vector Index Deletion

The system must remove or invalidate vector entries associated with deleted memories.

If immediate physical removal is not supported:

```text
vector entry
 ↓
logical exclusion
 ↓
background physical cleanup
```

Normal retrieval must not return the deleted entry.

---

## 16. Lexical Indexes

Search indexes may retain terms after the primary record is deleted.

They must be removed, invalidated or rebuilt as required by the storage implementation.

---

## 17. Knowledge Graph

Graph nodes and edges derived from deleted memory must be evaluated.

Possible outcomes:

```text
DELETE
RETRACT
RECOMPUTE
RETAIN WITH LEGAL/EXPLICIT BASIS
```

The system must not preserve a false relationship merely because its original source was deleted.

---

## 18. Consolidated Knowledge

Deleting one source memory may affect a consolidated knowledge item.

Example:

```text
memory A ─┐
memory B ─┼→ knowledge K
memory C ─┘
```

If A is deleted, Novi must determine whether K remains valid based on B/C and the applicable policy.

It must not automatically retain K without evaluation where K still contains protected information derived from A.

---

## 19. Learning Artifacts

Memory-derived learning artifacts require special treatment.

```text
memory
 ↓
training/learning candidate
 ↓
behavioral update
```

Deleting the source does not necessarily prove that the learned derivative has been removed.

The architecture must define whether the derivative:

- can be traced and removed;
- must be retrained/recomputed;
- can remain under a documented lawful/architectural basis;
- must be invalidated.

The default for privacy-sensitive learned derivatives should be conservative until this policy is explicitly established.

---

## 20. Caches

Caches must be invalidated as part of deletion propagation.

```text
DELETE
 ↓
cache invalidation
```

Sensitive data must not remain available through a stale cache after logical deletion.

---

## 21. Working Memory

If the target exists in active context or working memory:

```text
mark restricted
 ↓
remove from future context construction
 ↓
clear protected working representation
```

If an already-running operation has copied the information into another controlled buffer, that buffer becomes a dependency of the deletion policy.

---

## 22. Conversation Context

If a deleted memory has been inserted into an active model context, the system should prevent further reuse where technically possible and invalidate future context construction.

Deletion cannot retroactively erase information already generated outside Novi's controlled boundary, but controlled downstream storage must follow the applicable policy.

---

## 23. Backups

Backups require an explicit lifecycle.

The ICO notes that valid erasure can require action on backup systems, while acknowledging that immediate physical deletion from backups may not always be technically practical; data may instead need to be kept beyond use until scheduled replacement, depending on the circumstances. citeturn1view1

Novi should therefore maintain:

```text
backup retention schedule
backup deletion mechanism
backup restore filtering
backup tombstone propagation
verification process
```

---

## 24. Backup Restore Protection

A deleted object must not reappear when restoring an older backup.

```text
old backup
 ↓
restore
 ↓
apply deletion tombstones / deletion ledger
 ↓
validate
 ↓
usable state
```

This is mandatory for synchronized systems.

---

## 25. Replicas

All authorized replicas must receive deletion state.

If a replica is offline:

```text
local tombstone / deletion record
 ↓
replica reconnects
 ↓
deletion propagated
 ↓
verification
```

An offline replica must not be allowed to resurrect deleted memory.

---

## 26. External Recipients

If protected information has been intentionally shared with an external recipient, deletion policy must define whether and how a deletion instruction is propagated.

The ICO states that where personal data has been disclosed to others, there are circumstances requiring recipients to be informed of erasure. citeturn1view1

Novi should track disclosure provenance where required.

---

## 27. Logical Deletion vs Sanitization

Logical deletion means:

```text
application cannot normally retrieve it
```

Sanitization means a stronger property:

```text
recovery from the relevant storage is infeasible
for the defined threat/effort level
```

NIST SP 800-88 Rev. 2 explicitly frames sanitization in terms of making access infeasible for a defined level of effort. citeturn1view0

---

## 28. NIST Sanitization Classes

Novi's storage-disposal implementation should map its methods to the current NIST SP 800-88 Rev. 2 framework rather than inventing its own assurance vocabulary.

The implementation must select methods based on media type, information sensitivity, threat model and required assurance.

---

## 29. Cryptographic Erasure

Cryptographic erase can be used where the architecture has appropriate encryption and key-management properties.

Conceptually:

```text
encrypted data
      +
required key
      ↓
plaintext access

DESTROY KEY
      ↓
encrypted data remains
but becomes inaccessible
```

NIST includes cryptographic erase as a sanitization technique and emphasizes that its assurance depends on the underlying encryption/key-management implementation. citeturn0search36turn1view0

---

## 30. Key Hierarchy

For practical selective erasure, Novi should consider hierarchical encryption where appropriate:

```text
root/device key
   ↓
memory-domain key
   ↓
record/epoch key
   ↓
data
```

This is an architectural option, not a requirement for every storage implementation.

Selective cryptographic erasure is only meaningful if destroying a key actually makes all protected target data unrecoverable under the defined threat model.

---

## 31. Key Destruction

A key is not securely erased merely because an application object was removed.

Key destruction must be implemented through the selected key-management system and validated to the required assurance level.

Copies, backups, wrapped keys and recovery mechanisms must be considered.

---

## 32. Encryption Does Not Automatically Mean Secure Erasure

```text
encrypted database
      ≠
automatically securely erasable database
```

The architecture must establish where keys exist, who can access them, how they are backed up and how their destruction is verified.

---

## 33. Full-Device Erasure

When disposing of or repurposing Novi's storage/device, the target is not a single memory object.

Sanitization must cover applicable storage media and representations according to the device/media-specific procedure.

NIST SP 800-88 Rev. 2 is the reference point for this media-sanitization lifecycle. citeturn1view0

---

## 34. Flash Storage Caution

For SSD/eMMC/UFS/NVMe-like storage, filesystem overwrite assumptions can be unreliable because of wear leveling and device-managed storage behavior.

Novi must therefore use storage/device-specific sanitization capabilities validated for the actual hardware rather than assuming repeated application-level overwrites guarantee sanitization.

---

## 35. Memory Cards / Removable Media

If removable media is supported, its lifecycle requires explicit sanitization procedures.

A file delete or quick format must not be represented as equivalent to media sanitization.

---

## 36. Sensor Buffers

Cameras, microphones and other sensors may have local buffers or temporary files.

Deletion architecture must account for:

```text
sensor buffer
recording pipeline
encoder buffer
temporary file
processing buffer
cache
persistent memory
```

If a protected recording enters any durable representation, that representation becomes part of its lifecycle.

---

## 37. GPU / Accelerator Memory

Sensitive data can temporarily exist in accelerator memory during processing.

The implementation should define appropriate lifecycle clearing for sensitive buffers where feasible.

This is particularly relevant for multimodal inference and embeddings.

---

## 38. Swap / Paging / Crash Dumps

Sensitive memory can leak into:

- swap/page files;
- crash dumps;
- diagnostic snapshots;
- profiling captures;
- temporary debug files.

Production architecture should minimize such exposure and define clearing/retention behavior for protected data.

---

## 39. Logs

Logs must not become an undeclared memory store.

If logs contain identifiers, excerpts, paths or sensitive metadata related to deleted memories, deletion policy must determine whether those logs require redaction, expiration or protected retention.

---

## 40. Audit Records

The deletion audit should prove that a deletion workflow occurred without unnecessarily retaining the deleted content.

Prefer:

```text
memory_id
operation_id
policy/version
result
timestamps
component status
```

rather than copying the deleted memory into the audit log.

---

## 41. Verification

Deletion requires verification appropriate to the requested assurance level.

Possible checks:

```text
primary lookup → absent
lexical search → absent
vector retrieval → absent
graph query → absent/recomputed
cache → invalidated
replica → processed
backup state → compliant
provenance → appropriately restricted
```

For sanitization, storage-specific verification must follow the chosen sanitization method.

---

## 42. Negative Retrieval Tests

After deletion, automated tests should attempt to retrieve the target through all normal access paths.

```text
semantic query
lexical query
entity query
temporal query
spatial query
graph query
provenance query
cache lookup
```

A successful normal retrieval indicates deletion failure.

---

## 43. Re-Identification Tests

For sensitive personal data, verification should consider whether deleted information can still be reconstructed indirectly from remaining derivatives.

Example:

```text
deleted identity
      ↓
remaining embedding + metadata
      ↓
possible re-identification
```

This requires privacy/security evaluation rather than only checking for the original text string.

---

## 44. Deletion Completeness

A deletion should report scope explicitly:

```text
COMPLETE
PARTIAL
DEFERRED
BEYOND_USE
FAILED
UNKNOWN
```

Novi must not claim complete erasure when only the live database was modified.

---

## 45. Deletion Evidence

The system should maintain a deletion record containing enough evidence to demonstrate what was attempted and verified.

```text
request
 ↓
authorization
 ↓
affected objects
 ↓
propagation results
 ↓
verification
 ↓
final status
```

The deletion record itself must respect privacy and retention policy.

---

## 46. Failure Handling

If one component cannot be deleted:

```text
component failure
 ↓
block normal retrieval
 ↓
record incomplete deletion
 ↓
retry / repair
 ↓
verify
```

Do not silently report success.

---

## 47. Offline Deletion

Core deletion must work without:

- Wi-Fi;
- Bluetooth;
- cloud services.

Local deletion policy and local authorization are authoritative for local memory protection.

Synchronization occurs later.

---

## 48. Offline Replica Conflict

If an offline replica contains deleted data and later reconnects:

```text
local deletion tombstone
        ↓
replica receives deletion
        ↓
remove/restrict data
        ↓
verify
```

The old replica must not win merely because it has a newer local ingestion timestamp.

---

## 49. Restore Safety

After a disaster recovery restore, Novi must replay deletion state before allowing normal cognition to access restored memory.

```text
RESTORE
 ↓
DELETE LEDGER / TOMBSTONES
 ↓
INDEX REBUILD
 ↓
DELETION VERIFICATION
 ↓
COGNITION ENABLED
```

---

## 50. Deletion and Learning

Deletion must trigger evaluation of learning dependencies.

Possible response:

```text
source deleted
 ↓
identify learning dependency
 ↓
retrain / remove / invalidate / retain under approved policy
```

The system must not claim that deleting a source automatically removes all influence from a trained model.

---

## 51. Deletion and Knowledge Promotion

If a deleted memory supported a knowledge item:

```text
knowledge K
 ↓
source dependency removed
 ↓
re-evaluate K
```

K may:

- remain supported by independent evidence;
- become uncertain;
- become historical only;
- be retracted;
- require deletion/restriction.

---

## 52. Deletion and Provenance

After deletion, provenance should remain only to the extent permitted and necessary to enforce integrity, auditability and policy.

Do not retain unnecessary copies of deleted content merely to make the lineage graph look complete.

---

## 53. Privacy vs Auditability

These requirements can conflict.

The architecture should preserve:

```text
proof that deletion occurred
```

without preserving:

```text
unnecessary copy of deleted personal content
```

This is a data-minimization requirement.

---

## 54. Legal/Policy Exceptions

The technical architecture must support cases where deletion is restricted or not permitted because of an applicable legal or policy basis.

The ICO notes that UK GDPR erasure is not absolute and identifies circumstances where retention may be necessary, including legal obligations, certain public-interest/research purposes and legal claims. citeturn1view1

The system must represent such a decision explicitly rather than silently ignoring a deletion request.

---

## 55. Restriction Instead of Deletion

Where deletion cannot immediately occur but processing can be stopped, Novi may use a restricted state where permitted:

```text
stored
 ↓
NOT AVAILABLE FOR NORMAL PROCESSING
 ↓
awaiting authorized disposition
```

The ICO describes restriction as limiting future processing while retaining enough information to ensure the restriction is respected. citeturn0search4

---

## 56. Child Data

Where Novi processes children's personal data, deletion and privacy workflows require particular care and should follow applicable legal/product requirements.

The ICO specifically highlights enhanced attention to erasure requests concerning children's information. citeturn1view1

---

## 57. Security Incident Deletion

If deletion is triggered by suspected compromise, the workflow may need to preserve security evidence while preventing further use of the protected content.

```text
security evidence preservation
        +
protected-data restriction
        +
forensic policy
```

These goals must be coordinated rather than assuming ordinary deletion is always appropriate.

---

## 58. Device Disposal

Before Novi is transferred, sold, repaired outside the trusted boundary, or permanently retired:

```text
backup/replica assessment
 ↓
account removal
 ↓
key disposition
 ↓
media sanitization
 ↓
verification
 ↓
device release
```

The exact sanitization method must be selected according to the actual storage technology and assurance requirements.

---

## 59. No False Certificates

Novi must never claim:

> "Data has been securely erased."

unless the defined deletion/sanitization procedure completed and its verification requirements were satisfied.

A failed or incomplete workflow must be reported as such.

---

## 60. Testing Requirements

Test:

- logical deletion;
- repeated deletion;
- concurrent writes;
- concurrent reads;
- consolidation during deletion;
- indexing during deletion;
- vector deletion;
- lexical deletion;
- graph dependency removal;
- cache invalidation;
- working-memory clearing;
- replica synchronization;
- offline replica recovery;
- backup restore;
- tombstone enforcement;
- deleted-memory resurrection attempts;
- embedding re-identification risk;
- learning-derivative handling;
- model/context dependency handling;
- crash during deletion;
- power loss during deletion;
- storage failure;
- incomplete propagation;
- cryptographic key destruction;
- device sanitization;
- swap/crash-dump exposure;
- log leakage;
- authorization bypass;
- deletion audit integrity.

---

## 61. Architectural Invariants

1. Logical deletion and secure sanitization are distinct.
2. Deleting a pointer does not prove data destruction.
3. Every protected memory representation must have a defined deletion lifecycle.
4. Deleted memories cannot be returned through normal retrieval.
5. Tombstones prevent deleted data from being resurrected during synchronization.
6. Deletion is idempotent.
7. New derivatives must be prevented after authorized deletion begins.
8. Embeddings are treated as potentially sensitive derivatives.
9. Graph and consolidated knowledge dependencies are reevaluated.
10. Learning derivatives require explicit policy and cannot be assumed erased automatically.
11. Caches and working memory are included in deletion scope.
12. Backups have an explicit deletion/beyond-use lifecycle.
13. Restore operations replay deletion state before normal cognition resumes.
14. Offline replicas cannot resurrect deleted memory.
15. Cryptographic erasure is used only when its key-management and storage properties provide the required assurance.
16. Encryption alone does not guarantee secure erasure.
17. Storage-specific sanitization methods are required for device disposal.
18. Verification is required before claiming completion.
19. Partial deletion is reported honestly.
20. Audit records prove deletion without unnecessarily preserving deleted content.
21. Privacy restrictions apply to deletion logs and tombstones.
22. Deletion does not bypass legal/security evidence requirements.
23. Core deletion works without Wi-Fi, Bluetooth or cloud services.
24. Novi never fabricates deletion evidence.
25. Novi never claims complete erasure when the implementation has only achieved logical removal.

---

## 62. Final Principle

> **For Novi, forgetting is an engineered capability: authorized data must disappear from normal cognition immediately, propagate through every relevant derivative, resist resurrection, and reach the required sanitization assurance without creating a false claim about what was actually erased.**

Secure deletion is therefore part of memory architecture—not an afterthought added to the database layer.
