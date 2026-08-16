# 21 — Memory Backup, Recovery and Restoration

## Status

**DESIGN — V1 / CRITICAL ARCHITECTURE**

## Purpose

Define how Novi protects, verifies, backs up, recovers and restores its accumulated memory, knowledge, provenance, event history and required supporting state after:

- power loss;
- abrupt shutdown;
- filesystem failure;
- SQLite corruption;
- storage-device failure;
- accidental deletion;
- software bugs;
- schema migration failure;
- hardware replacement;
- failed upgrades;
- synchronization errors;
- compromised replicas;
- malicious deletion or encryption;
- catastrophic loss of the primary storage device.

The objective is not merely to have copies of files. The objective is to guarantee that Novi can recover a **coherent, provenance-preserving cognitive state** without silently resurrecting deleted information or overwriting newer knowledge with stale backup data.

This document was cross-validated against SQLite's official durability, WAL, backup and corruption documentation, NVIDIA's Jetson storage documentation, and CISA/NIST recovery guidance. SQLite documents atomic transactions and crash recovery; its Backup API creates consistent snapshots of live databases; WAL files are part of persistent database state and must remain associated with the database; CISA recommends offline, encrypted and regularly tested backups; and NIST emphasizes backup currency, consistency, secure storage and recoverability as interdependent requirements. citeturn0search0turn0search2turn0search3turn1search0turn1search27

---

## 1. Core Principle

> **A backup is a recovery source, not an authority over current Novi state.**

Restoration must never silently replace newer canonical memory with an older backup.

```text
CURRENT CANONICAL STATE
        │
        ├──────────► Backup snapshots
        │
        ├──────────► Event/change history
        │
        └──────────► Recovery metadata

Backup
  │
  ▼
Recovery candidate
  │
  ▼
Validation
  │
  ▼
Reconciliation
  │
  ▼
Restored canonical state
```

---

## 2. What Must Be Protected

Novi's memory system is larger than one SQLite database.

The recovery set may include:

- canonical memory records;
- knowledge claims;
- memory provenance;
- event log/change history required for reconstruction;
- deletion/tombstone state;
- schema/version metadata;
- migration metadata;
- entity identity state;
- relationship/knowledge-graph data;
- memory indexes when they cannot be cheaply regenerated;
- embedding metadata and model identifiers;
- user-authorized persistent preferences;
- configuration required to interpret stored data;
- encryption metadata and key references where appropriate;
- synchronization cursors/state;
- recovery manifests;
- integrity metadata;
- hardware/calibration provenance required to interpret physical-world memories.

Derived caches should not automatically be treated as authoritative data.

---

## 3. Canonical vs Derived State

The recovery architecture distinguishes:

```text
CANONICAL
─────────
memories
knowledge
provenance
identity
semantic relationships
required event history
policy state

DERIVED
───────
FTS indexes
embeddings
vector indexes
cached summaries
materialized projections
runtime caches
```

When possible, derived state should be rebuilt from canonical state.

This reduces the number of things that must be trusted during restoration.

---

## 4. SQLite Is a Component, Not the Recovery Strategy

SQLite provides strong transactional and crash-recovery properties, but Novi must not assume that SQLite alone solves backup and disaster recovery.

SQLite documents atomic commit across crashes/power failures and extensive crash testing. It also documents failure modes outside SQLite's control, including broken filesystems, storage hardware failures and inappropriate external file manipulation. citeturn0search0turn0search6

Therefore:

```text
SQLite durability
        ≠
disaster recovery
```

Novi needs both.

---

## 5. Live Database Backup

A live SQLite database must not normally be copied with a naive filesystem copy while active.

SQLite's official Online Backup API exists specifically to create a consistent snapshot of a live database while allowing the source to remain usable. SQLite also documents `VACUUM INTO` and other supported techniques. citeturn0search2

Novi's backup service should therefore use a SQLite-aware snapshot mechanism rather than:

```text
cp novi.db backup.db
```

as the general live-backup implementation.

---

## 6. WAL Handling

If Novi uses SQLite WAL mode, the backup architecture must treat the WAL as part of persistent database state.

SQLite explicitly states that separating a WAL database from its WAL file can lose previously committed transactions or corrupt the database. citeturn0search3

Therefore:

> **Novi must never independently copy, delete, move or restore a WAL database file without following SQLite's documented consistency rules.**

Backup operations should produce a coherent database snapshot rather than manually assembling database and WAL files.

---

## 7. Crash Recovery

After an unexpected shutdown:

```text
boot
  ↓
detect previous unclean shutdown
  ↓
open storage safely
  ↓
SQLite recovery
  ↓
integrity checks
  ↓
validate event/memory invariants
  ↓
reconcile incomplete application operations
  ↓
resume
```

SQLite WAL recovery validates WAL frames and reconstructs the WAL index when the database is reopened. citeturn0search8

Novi must additionally validate its own semantic invariants after database-level recovery.

---

## 8. Transaction Durability Policy

The final SQLite `synchronous` and journal configuration must be selected based on measured Novi durability requirements.

SQLite documents an important trade-off: WAL with `synchronous=NORMAL` is consistent but can lose recently committed transactions after power loss, while `synchronous=FULL` provides stronger durability guarantees. SQLite's corruption guidance recommends the default `FULL` setting when maximum reliability is required. citeturn0search4turn0search6

For Novi, the policy should classify writes:

```text
CRITICAL MEMORY / SAFETY-RELEVANT STATE
        ↓
strong durability requirement

NORMAL EPISODIC MEMORY
        ↓
normal durable transaction policy

REGENERABLE CACHE
        ↓
lower durability requirement
```

The exact runtime configuration must be benchmarked on the actual storage hardware.

---

## 9. Memory Write Classification

Every persistent write should belong to a durability class.

Example:

| Class | Examples | Recovery priority |
|---|---|---|
| P0 | safety state, deletion records, identity/security state | immediate/highest |
| P1 | canonical memories, knowledge, provenance | highest |
| P2 | events required for reconstruction | high |
| P3 | synchronization metadata | high |
| P4 | indexes/embeddings | rebuildable |
| P5 | temporary cache | disposable |

A lower class must never be allowed to block recovery of higher-priority state.

---

## 10. Backup Layers

Novi should use multiple recovery layers.

```text
L0 — live canonical storage

L1 — local snapshots

L2 — removable/offline local backup

L3 — optional encrypted external backup

L4 — optional remote/cloud backup
```

Cloud is optional and must remain consistent with Novi's local-first principle.

---

## 11. Offline Backup

At least one recovery copy should be capable of being disconnected from Novi's normal network and runtime environment.

CISA recommends maintaining offline, encrypted backups and regularly testing their availability and integrity because connected backups may be accessible to destructive malware. citeturn1search0turn1search24

For Novi, this is particularly valuable because the robot's long-term memory is a high-value accumulated asset.

---

## 12. Multiple Copies and Media

Recovery should not depend on one storage device.

The architecture should support multiple copies across appropriately separated media.

CISA guidance recommends multiple copies, physically separate/segmented storage, offline protection and regular restoration exercises. citeturn1search0turn1search1

The exact number and media strategy will depend on the final deployment and threat model.

---

## 13. Backup Encryption

Backups containing sensitive memories should be encrypted.

Encryption must cover:

- backup contents;
- sensitive metadata where applicable;
- credentials/authorization information where stored;
- transport when backup is transferred.

Keys must not be stored in plaintext beside the only backup copy.

Key recovery must itself be documented and tested.

A perfectly encrypted backup that cannot be decrypted after hardware failure is not a successful recovery system.

---

## 14. Backup Integrity

Every backup should have integrity metadata sufficient to detect corruption or unexpected modification.

Possible mechanisms include:

- cryptographic hashes;
- authenticated encryption;
- signed manifests;
- database integrity checks;
- schema/version metadata;
- backup creation metadata;
- source state identifiers.

A backup should be classified as:

```text
created
verified
trusted-for-restore
suspect
invalid
expired
```

---

## 15. Backup Manifest

Each backup should have a manifest containing, at minimum:

```text
backup_id
source_robot_id
creation_time
source_state_version
schema_version
application_version
memory-format-version
event-log boundary
highest committed event/change ID
oldest retained event/change ID
covered deletion/tombstone state
database integrity result
file/object hashes
encryption metadata reference
hardware/storage context
backup software version
verification status
```

The manifest itself must be protected against accidental or malicious modification.

---

## 16. Snapshot Identity

Every backup is a snapshot of a defined logical state.

Example:

```text
backup B17
canonical state version = 8421
event boundary = 19,332
schema = 7
```

Restoration must use this identity rather than assuming that a filename such as `backup_latest.db` describes the state accurately.

---

## 17. Backup Consistency Boundary

A backup must represent a coherent semantic point in time.

It must not contain:

```text
memory written
but provenance missing
```

or:

```text
knowledge claim written
but required supporting state absent
```

The backup service must coordinate with the Memory Manager to establish a consistent snapshot boundary.

---

## 18. Event Log and Backup Interaction

The event log can reduce recovery cost.

Conceptually:

```text
snapshot S100
      +
events 10001–12000
      ↓
state S12000
```

This enables point-in-time reconstruction if the required event range is retained.

However, the event log must not be treated as a substitute for periodic validated snapshots.

---

## 19. Point-in-Time Recovery

Novi should eventually support restoration to a defined logical point when sufficient history exists.

```text
Snapshot A
   ↓
events
   ↓
Snapshot B
   ↓
events
   ↓
current
```

A recovery request may specify:

```text
restore before corruption
restore before accidental deletion
restore known-good state
```

The recovery engine must never silently choose a point in time.

---

## 20. Recovery Before Restoration

Restoration should first produce a **candidate state**.

```text
backup
 ↓
restore to isolated workspace
 ↓
validate
 ↓
inspect differences
 ↓
reconcile
 ↓
approve
 ↓
activate
```

The original canonical state should remain untouched until the candidate passes required validation.

---

## 21. Never Restore Directly Over Canonical State

Unsafe pattern:

```text
backup.db
   ↓
overwrite novi.db
```

Preferred:

```text
backup
  ↓
restore candidate
  ↓
validate
  ↓
compare with surviving state
  ↓
reconcile
  ↓
atomic activation
```

This protects against stale or corrupted backups.

---

## 22. Stale Backup Protection

Suppose:

```text
Current state = version 100
Backup = version 80
```

The system must not automatically replace version 100 with version 80.

If restoration is required, it must be an explicit recovery operation with a defined policy for what happens to versions 81–100.

Possible strategy:

```text
backup v80
   ↓
restore candidate
   ↓
extract valid changes 81–100 from surviving event/replica sources where possible
   ↓
reconcile
   ↓
activate
```

If newer state cannot be recovered, the operator must understand what will be lost before activation.

---

## 23. Deletion Preservation During Recovery

Deleted memories must not automatically return because a backup predates their deletion.

Example:

```text
10:00 memory created
11:00 memory deleted
12:00 backup created
```

If the backup is older than the deletion:

```text
restore
   ↓
apply deletion/tombstone history
   ↓
memory remains deleted
```

Deletion semantics must therefore survive recovery according to the retention/deletion policy.

---

## 24. Privacy-Aware Recovery

Restoration must respect the same privacy rules as normal operation.

A backup is not a loophole around deletion.

If a memory has been permanently deleted according to policy, recovery procedures must not casually resurrect it from an old backup.

This requires defined backup-retention and deletion semantics.

---

## 25. Recovery After Hardware Replacement

If the Jetson or primary storage device is replaced:

```text
new hardware
   ↓
install trusted base software
   ↓
verify hardware identity
   ↓
restore recovery candidate
   ↓
validate schema/models
   ↓
restore memory
   ↓
restore configuration
   ↓
rebuild derived indexes
   ↓
validate sensor/calibration provenance
   ↓
activate Novi
```

Hardware-specific state must not be blindly copied from the old machine.

---

## 26. Sensor and Calibration State During Recovery

Historical sensor provenance must remain attached to the original hardware instance.

After hardware replacement:

```text
old camera instance A
      ↓
new camera instance B
```

Historical memories remain attributed to A.

B begins a new hardware lineage and must undergo its own calibration/health validation.

---

## 27. Model Recovery

Memory restoration may depend on models that are no longer installed.

Therefore persistent knowledge should record model identity/version where relevant.

Recovery should distinguish:

```text
memory is valid
model needed to interpret/recompute it is unavailable
```

from:

```text
memory itself is corrupt
```

The system should preserve the memory rather than silently deleting it because a model is unavailable.

---

## 28. Derived-State Rebuild

After canonical restoration:

```text
canonical memory
      ↓
knowledge graph rebuild
      ↓
FTS rebuild
      ↓
embedding generation
      ↓
vector index rebuild
      ↓
caches
```

Derived state should be marked as:

```text
rebuilding
partial
ready
failed
```

Cognition must know whether retrieval infrastructure is fully ready.

---

## 29. Storage Failure

If the primary storage device is failing:

1. stop unnecessary writes;
2. preserve critical state;
3. capture a consistent recovery snapshot if possible;
4. verify the snapshot;
5. isolate failing storage;
6. replace storage;
7. restore candidate;
8. validate;
9. resume operation.

The exact sequence depends on the storage failure mode and hardware diagnostics.

---

## 30. Storage Health

Novi should monitor storage health where supported:

- available capacity;
- I/O errors;
- filesystem errors;
- device health indicators;
- temperature;
- write endurance where measurable;
- backup failures;
- database integrity failures.

NVIDIA's Jetson platform documentation also provides mechanisms for external storage provisioning, reinforcing that storage should be treated as an explicit subsystem rather than an invisible implementation detail. citeturn0search11

---

## 31. Low-Storage Behavior

Novi must not wait until storage reaches zero.

Example policy:

```text
healthy
  ↓
warning
  ↓
constrained
  ↓
critical
  ↓
protected mode
```

Actions may include:

- reduce temporary media retention;
- reduce cache retention;
- postpone expensive derived indexes;
- prioritize critical memory;
- trigger backup;
- request external storage/service;
- stop nonessential data generation.

Memory deletion must follow policy and must not be used as an uncontrolled emergency cleanup mechanism.

---

## 32. Power-Loss Strategy

Because Novi is a mobile embedded system, power loss is an expected failure mode rather than an exceptional server event.

The architecture should combine:

- battery telemetry;
- low-power detection;
- graceful shutdown;
- transactional storage;
- write prioritization;
- recovery on reboot;
- periodic verified snapshots.

Novi should attempt graceful shutdown when sufficient warning exists, but recovery must remain safe if power disappears without warning.

---

## 33. Backup Scheduling

Backup frequency should be driven by:

- rate of important memory creation;
- acceptable data-loss window;
- storage cost;
- power consumption;
- CPU/GPU impact;
- robot activity;
- available external storage;
- backup success history.

Do not choose a fixed interval solely for convenience.

The final policy should define separate schedules for:

```text
critical state
canonical memory
full snapshot
incremental/event backup
offline backup
```

---

## 34. Backup While Novi Is Active

Backups must not unnecessarily interfere with:

- navigation;
- safety;
- real-time perception;
- voice interaction;
- actuator control;
- thermal management.

The backup scheduler should coordinate with resource budgets.

Example:

```text
Novi navigating
+ CPU/GPU constrained
+ battery low
      ↓
postpone noncritical backup
```

But critical persistence must not be postponed indefinitely.

---

## 35. Backup Failure Handling

A failed backup must never replace the previous known-good backup.

```text
known-good backup A
        │
new backup attempt B
        ↓
B fails
        ↓
A remains valid
```

A backup becomes the preferred recovery source only after verification succeeds.

---

## 36. Backup Verification

Verification should happen at multiple levels.

### Level 1 — file integrity

- hashes;
- size;
- manifest validation.

### Level 2 — database integrity

- open database;
- SQLite integrity checks;
- schema checks;
- WAL/recovery consistency.

### Level 3 — semantic integrity

- memory invariants;
- provenance links;
- deletion state;
- relationship integrity;
- event boundaries.

### Level 4 — restoration test

Actually restore a candidate environment and exercise retrieval.

A backup that has never been successfully restored is not fully trusted.

---

## 37. Restore Drills

CISA explicitly recommends regularly testing backup availability and restoration. NIST similarly emphasizes that successful recovery depends on correct, current, secure and accessible backups rather than merely possessing copies. citeturn1search0turn1search27

Novi should periodically perform automated or controlled restore drills.

Example:

```text
backup selected
   ↓
isolated restore
   ↓
validation
   ↓
query known memories
   ↓
verify provenance
   ↓
verify deletion state
   ↓
verify schema
   ↓
verify derived-state rebuild
```

---

## 38. Known-Good Recovery Tests

The test corpus should contain known memories with:

- simple facts;
- temporal sequences;
- conflicting evidence;
- deleted memories;
- user-confirmed information;
- sensor provenance;
- knowledge-graph relationships;
- embeddings;
- schema migrations.

After restore, automated assertions must verify that semantic state matches expectations.

---

## 39. Recovery Manifest

A restore candidate should report:

```text
source backup
source state version
schema version
software compatibility
memory count
knowledge count
event range
deleted/tombstoned count
provenance integrity
corruption findings
missing dependencies
rebuild requirements
newer surviving state
expected data loss
```

The operator should be able to understand the consequences before activation.

---

## 40. Recovery Modes

Novi should support explicit modes.

### Normal startup

Use current canonical state.

### Crash recovery

Recover interrupted local transactions and resume.

### Storage replacement

Restore onto new storage.

### Point-in-time recovery

Recover to an explicit historical boundary.

### Disaster recovery

Rebuild Novi from trusted backup and software artifacts.

### Forensic recovery

Create an isolated copy for investigation without modifying canonical state.

---

## 41. Recovery Must Be Idempotent

Running the same recovery validation twice should not create additional semantic changes.

Repeated recovery attempts must not:

- duplicate memories;
- duplicate relationships;
- resurrect deleted records;
- create duplicate events;
- advance versions incorrectly.

---

## 42. Recovery and Synchronization

Recovery must integrate with the distributed-state architecture.

```text
restore local candidate
        ↓
identify last known canonical state
        ↓
compare with trusted peers/backups
        ↓
reconcile changes
        ↓
apply deletion semantics
        ↓
activate canonical state
```

A restored robot must not blindly push an old backup to every synchronized device.

---

## 43. Recovery and Conflict Resolution

If recovery sources disagree:

```text
backup A
backup B
surviving local state
peer state
      ↓
conflict resolver
```

The conflict-resolution rules in document `20` apply.

The oldest or newest source is not automatically correct.

---

## 44. Recovery and Privacy Deletion

The privacy/deletion architecture must define how deletion propagates into:

- active database;
- backups;
- replicas;
- archives;
- event logs;
- derived indexes.

The recovery system must not accidentally create an infinite deletion contradiction such as:

```text
delete
→ restore old backup
→ resurrect
→ delete
→ restore
```

Tombstones, retention windows and backup expiration must be designed together.

---

## 45. Security of Backups

Backups are sensitive assets.

Controls should include:

- least-privilege access;
- encryption;
- authenticated backup operations;
- isolated backup storage;
- immutable/write-protected copies where appropriate;
- audit logs;
- integrity verification;
- secure key handling;
- protection from automatic network access.

CISA recommends offline, encrypted and immutable backup strategies for resilience against destructive attacks. citeturn1search0turn1search4

---

## 46. Compromised Backup

A backup may be technically intact but semantically compromised.

Examples:

- malware modified memory before backup;
- unauthorized user changed preferences;
- malicious replica injected events;
- corruption occurred before backup creation.

Therefore:

```text
backup integrity
      ≠
backup trustworthiness
```

Trust requires provenance, creation context, validation and threat assessment.

---

## 47. Backup Selection

When multiple backups exist, selection should consider:

- integrity status;
- trust status;
- age;
- semantic completeness;
- schema compatibility;
- deletion coverage;
- known corruption;
- hardware compatibility;
- security state;
- ability to reconcile with surviving state.

Do not simply select the filename containing `latest`.

---

## 48. Golden Recovery Image

Novi should maintain a reproducible software baseline containing, where appropriate:

- trusted OS image;
- required drivers;
- hardware configuration;
- core application/runtime;
- model manifests;
- schema migration tools;
- recovery tools.

CISA recommends maintaining golden images of critical systems to accelerate rebuilding after destructive incidents. citeturn1search0

The exact image mechanism will be defined in the system/deployment architecture.

---

## 49. Recovery Without Internet

The core recovery procedure must work without Internet access.

Required local artifacts should therefore include, or be reproducibly obtainable from trusted local media:

- recovery software;
- compatible runtime;
- schema migration tools;
- critical model metadata;
- backup encryption/key recovery path;
- hardware configuration;
- recovery documentation.

Cloud services may accelerate recovery but must not be required for fundamental memory restoration.

---

## 50. Recovery After Total Robot Loss

A catastrophic scenario may involve loss of the entire robot.

The recovery plan should support:

```text
new Jetson
+ new storage
+ trusted software baseline
+ trusted memory backup
+ configuration
      ↓
reconstructed Novi
```

Physical-world memories must retain their original robot/sensor provenance even after reconstruction.

The new robot instance should have a distinct hardware identity.

---

## 51. Recovery of Identity

Robot identity must be handled carefully.

A replacement device may be:

```text
same logical Novi identity
new physical hardware identity
```

or, after cloning/testing:

```text
new Novi instance
```

The identity architecture must prevent accidental simultaneous operation of two devices claiming to be the same authoritative robot.

---

## 52. Recovery of Encryption Keys

Encrypted backups are useless if their keys are permanently lost.

The architecture must define:

- key generation;
- key storage;
- key rotation;
- backup-key protection;
- recovery authorization;
- emergency recovery procedure;
- key destruction policy.

Keys must not simply be stored in the same unprotected location as the only encrypted backup.

---

## 53. Failure Matrix

| Failure | Expected behavior |
|---|---|
| application crash | SQLite/app recovery, no semantic duplication |
| sudden power loss | database remains recoverable; latest non-durable writes may be lost according to policy |
| filesystem failure | detect, isolate, restore from validated backup |
| storage failure | migrate to replacement storage |
| corrupted backup | reject and use another trusted copy |
| stale backup | restore only through explicit reconciliation |
| deleted memory in newer state | deletion remains effective according to policy |
| missing model | preserve memory, mark interpretation dependency |
| schema mismatch | migrate or defer, never silently discard |
| compromised peer | reject/contain synchronization input |
| corrupted index | rebuild from canonical state |
| lost robot | reconstruct from trusted recovery set |
| network unavailable | local recovery remains functional |
| backup job interrupted | previous good backup remains authoritative recovery source |

---

## 54. Recovery Observability

The system should expose:

- last successful backup;
- last verified backup;
- backup age;
- backup size;
- backup integrity status;
- last restore drill;
- restore drill result;
- available recovery points;
- storage health;
- recovery warnings;
- pending backup;
- failed backup count;
- deletion-retention status;
- key availability.

A user should never discover during a disaster that backups have silently failed for months.

---

## 55. Testing Strategy

Recovery testing must include real failure simulation where practical.

### Database-level

- transaction interruption;
- process crash;
- power-loss simulation;
- WAL recovery;
- checkpoint interruption;
- corrupted pages;
- incomplete writes.

### Storage-level

- full disk;
- read-only filesystem;
- I/O errors;
- device disappearance;
- filesystem corruption;
- replacement drive.

### Application-level

- interrupted migration;
- interrupted backup;
- interrupted restore;
- duplicate recovery;
- stale backup;
- deletion resurrection attempt;
- incompatible schema.

### Distributed

- restore behind peer state;
- restore ahead of peer state;
- conflicting replicas;
- offline divergence;
- compromised replica.

SQLite itself emphasizes crash testing because subtle recovery defects can escape code inspection; Novi should adopt the same philosophy at the semantic recovery layer. citeturn0search0

---

## 56. Recovery Acceptance Criteria

A recovery implementation is not complete merely because the database opens.

A successful recovery must demonstrate:

1. database integrity;
2. schema integrity;
3. memory integrity;
4. provenance integrity;
5. event continuity where required;
6. deletion correctness;
7. knowledge-graph consistency;
8. synchronization-state correctness;
9. derived-index rebuildability;
10. privacy-policy compliance;
11. hardware-provenance preservation;
12. retrieval correctness;
13. autonomous operation after recovery;
14. no unauthorized resurrection of deleted information;
15. no silent loss beyond the declared recovery point.

---

## 57. Recovery RTO / RPO

The final deployment should define:

**RPO — Recovery Point Objective**

How much recent state Novi may lose after a catastrophic failure.

**RTO — Recovery Time Objective**

How long it may take to restore useful operation.

These should be defined separately for:

- safety state;
- canonical memory;
- knowledge;
- event history;
- derived indexes;
- full robot operation.

Example architecture:

```text
critical safety state → near-zero loss target
canonical memory → very low loss target
indexes → rebuildable
cache → no recovery guarantee
```

Exact numerical targets belong to the deployment requirements.

---

## 58. Backup Policy Must Be Versioned

Backup behavior itself is part of the architecture.

Changes to:

- retention;
- encryption;
- snapshot format;
- schema;
- deletion behavior;
- backup frequency;
- restore rules;

must be versioned and tested.

A future Novi version must know how to interpret older recovery artifacts.

---

## 59. Migration Safety

Before schema migration:

```text
current state
    ↓
validated backup
    ↓
migration candidate
    ↓
validation
    ↓
activate
```

If migration fails:

```text
restore previous state
```

The system must never perform an irreversible migration without a verified recovery path.

---

## 60. Recovery Audit Trail

Record significant recovery actions:

- who/what initiated recovery;
- reason;
- source backup;
- source state version;
- target state;
- validation results;
- data-loss estimate;
- conflicts;
- migrations;
- restored/deleted records;
- activation time;
- software version.

Recovery is a high-impact operation and must be auditable.

---

## 61. Architectural Invariants

1. Backups are recovery sources, not automatic authorities.
2. Live SQLite databases must be backed up using consistency-aware mechanisms.
3. WAL state must never be separated incorrectly from its database.
4. Canonical state must be distinguishable from derived state.
5. Failed backups must never replace known-good backups.
6. Backups must have explicit logical state/version boundaries.
7. Backup integrity must be verified.
8. Backup trustworthiness must be considered separately from file integrity.
9. Restoration must occur into a candidate state before activation.
10. Stale backups must never silently overwrite newer state.
11. Deletions must not be silently undone by restoration.
12. Recovery must preserve sensor and hardware provenance.
13. Derived indexes should be rebuildable where practical.
14. Recovery must remain possible without Internet access.
15. Encryption keys require an independent recovery strategy.
16. Restore procedures must be regularly tested.
17. Recovery must be idempotent.
18. Recovery must be auditable.
19. Critical memory must have a stronger durability policy than disposable caches.
20. The recovery system must preserve privacy and deletion policy.
21. The LLM must not control backup or restoration authority.
22. A database opening successfully is not sufficient evidence of successful cognitive recovery.

---

## 62. Final Principle

> **Novi's memory is an accumulated life history. Backup and recovery must therefore restore not merely bytes, but a coherent, trustworthy, provenance-preserving state of that history.**

The recovery system must assume that failures happen, that storage can fail, that power can disappear, that replicas can diverge, and that backups can become stale or compromised.

The desired result is not merely:

> "The database opened."

It is:

> **"Novi recovered a verified cognitive state, knows what was recovered, knows what could not be recovered, preserved its provenance and privacy rules, and can safely continue operating."**

---

## 63. Research Basis

This architecture was cross-validated against multiple primary/authoritative sources:

- **SQLite Atomic Commit** — transaction atomicity, crash/power-loss behavior, filesystem assumptions and crash testing. citeturn0search0
- **SQLite Online Backup API** — consistent snapshots of live databases and limitations of naive file copying. citeturn0search2turn0search9
- **SQLite WAL documentation** — WAL as part of persistent database state and recovery behavior. citeturn0search3turn0search8
- **SQLite PRAGMA / corruption guidance** — durability trade-offs, synchronization and safe database configuration. citeturn0search4turn0search6
- **NVIDIA Jetson Platform Services storage documentation** — explicit treatment of external storage as a Jetson subsystem. citeturn0search11
- **CISA #StopRansomware guidance** — offline, encrypted, separated and regularly tested backups; recovery exercises and immutable protection. citeturn1search0turn1search4
- **NIST SP 800-209** — recovery depends jointly on backup correctness, currency, retention, secure storage and accessibility. citeturn1search27

These sources establish the underlying reliability and recovery principles. Novi-specific policies remain architectural decisions that must later be validated against the actual Jetson hardware, storage subsystem, software stack and operational threat model.
