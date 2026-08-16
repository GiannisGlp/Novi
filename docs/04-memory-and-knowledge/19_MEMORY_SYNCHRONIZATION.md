# 19 — Memory Synchronization

## Status

**DESIGN — V1**

## Purpose

Define how Novi synchronizes memory-related state between local subsystems, local processes, removable/replacement storage, optional companion devices, and future remote systems without making connectivity a dependency of the robot.

The central rule is:

> **Novi has one authoritative local cognitive state. Synchronization distributes changes; it does not redefine truth.**

Connectivity is an optional transport capability. Local cognition, autonomy, memory, safety and learning must continue when all external connectivity is unavailable.

---

## 1. What Synchronization Means

Synchronization is the controlled exchange of state or events between independently operating replicas or derived systems.

It is not:

- blind database copying;
- last-write-wins for all data;
- automatic uploading of all memory;
- automatic merging of conflicting beliefs;
- granting remote systems authority over Novi;
- a prerequisite for local operation.

Novi must distinguish:

```text
LOCAL AUTHORITATIVE STATE
        ↓
changes/events
        ↓
SYNC OUTBOX
        ↓
policy + privacy + authorization
        ↓
transport
        ↓
REMOTE / COMPANION TARGET
        ↓
validation
        ↓
ACK / CONFLICT / REJECT
        ↓
SYNC STATE
```

---

## 2. Local Authority

The local Novi Memory Manager remains authoritative for the robot's live cognitive memory.

Remote systems may include:

- development workstation;
- maintenance computer;
- phone/tablet control application;
- optional home server;
- backup target;
- future second Novi;
- optional cloud service.

None automatically becomes authoritative merely because it has a newer timestamp.

Authority must be explicitly defined per data domain.

---

## 3. Synchronization Domains

Novi should synchronize by domain rather than treating the entire database as one object.

Possible domains:

```text
configuration
hardware inventory
calibration metadata
user-approved preferences
memory records
knowledge claims
relationships
world-model snapshots
learning artifacts
model metadata
logs/telemetry
media
```

Each domain has its own:

- retention policy;
- privacy class;
- synchronization eligibility;
- conflict policy;
- durability requirement;
- bandwidth policy.

---

## 4. Local-First Principle

When disconnected:

```text
Novi continues operating
        ↓
local state changes
        ↓
changes remain local
        ↓
outbox records eligible changes
        ↓
connectivity returns
        ↓
sync policy evaluates them
```

No subsystem should block critical operation waiting for synchronization.

If synchronization is unavailable for hours, days or permanently, the robot must continue functioning subject to local storage limits and retention policies.

---

## 5. Synchronization Must Use Events / Change Records

The preferred V1 mechanism is a durable change/outbox record rather than repeatedly copying the entire memory database.

Example:

```text
memory mutation
      ↓
authoritative transaction
      ↓
change record/outbox entry
      ↓
commit
```

The outbox entry and authoritative mutation must be committed atomically when the operation is synchronization-eligible.

This prevents:

```text
memory changed
but
sync record lost
```

or:

```text
sync record exists
but
memory mutation never committed
```

---

## 6. Outbox

The local outbox should record enough information to safely synchronize a change.

Suggested fields:

- change ID;
- source robot ID;
- source database/domain;
- entity ID;
- entity version;
- operation type;
- event/claim IDs;
- creation time;
- ordering metadata;
- privacy classification;
- synchronization policy;
- payload reference;
- payload hash;
- retry count;
- delivery state;
- last attempt;
- target ID;
- error code.

Large media should normally be referenced rather than embedded directly in every change record.

---

## 7. Delivery States

A synchronization record can move through states such as:

```text
LOCAL
  ↓
ELIGIBLE
  ↓
QUEUED
  ↓
SENDING
  ↓
ACKNOWLEDGED
```

Alternative terminal/temporary states:

```text
RETRY
CONFLICT
REJECTED
EXPIRED
CANCELLED
DELETED
QUARANTINED
```

The state machine must be durable and recoverable after restart.

---

## 8. Idempotent Delivery

Every synchronization change requires a stable globally unique change ID within the synchronization namespace.

A receiver must safely handle duplicate delivery.

Example:

```text
change C123
→ received
→ committed
→ ACK lost
→ sender retries C123
→ receiver recognizes C123
→ returns existing result
```

The receiver must not create duplicate memory or knowledge records.

---

## 9. Ordering

Synchronization must preserve ordering where semantics require it.

A simple timestamp order is insufficient because clocks can differ.

The change record should support:

- monotonic local sequence;
- entity version;
- source event ID;
- causal parent IDs where applicable;
- acquisition/creation timestamp;
- synchronization timestamp.

The receiver should apply changes according to domain-specific consistency rules rather than assuming all changes form one global total order.

---

## 10. Versioning

Synchronizable mutable entities should have explicit versions.

Example:

```text
Memory M
local version 17
```

A change declares:

```text
base_version = 17
new_version = 18
```

If the receiver is already at version 19, it must not blindly apply version 18.

It should determine whether the change is:

- already represented;
- mergeable;
- superseded;
- conflicting;
- requiring human confirmation.

---

## 11. Synchronization vs Conflict Resolution

Synchronization answers:

> **How do we transport and reconcile changes?**

Conflict resolution answers:

> **What should Novi believe when valid changes disagree?**

These must remain separate architectural layers.

```text
transport
   ↓
validation
   ↓
version detection
   ↓
conflict detection
   ↓
conflict policy
   ↓
Memory Manager
```

Detailed conflict policy is defined in the next architecture document.

---

## 12. Domain-Specific Conflict Policy

Different data requires different policies.

### Append-only events

Usually merge by preserving both events.

### Historical memories

Usually preserve both observations with provenance.

### Current world state

May prefer the most recent valid observation, subject to timestamp quality and source health.

### User preferences

May require explicit user authority or deterministic source precedence.

### Knowledge claims

Should not be resolved solely by last-write-wins.

### Deletions

Must have strong precedence and durable tombstone semantics where required.

### Configuration

Requires explicit version and authorization rules.

---

## 13. Deletion Synchronization

Deletion must synchronize as a semantic operation, not merely as absence of a record.

Example:

```text
DELETE memory M
      ↓
durable deletion/tombstone
      ↓
sync deletion instruction
      ↓
remote deletion
      ↓
remote derived-data invalidation
      ↓
acknowledgment
```

If the original record is simply omitted from a future snapshot, an old replica may incorrectly reintroduce it.

Tombstone retention duration must therefore be long enough to prevent stale replicas from resurrecting deleted information, subject to the privacy/deletion policy.

---

## 14. Privacy Gate

No change enters the synchronization pipeline merely because it exists locally.

Before transmission:

```text
change
 ↓
privacy classification
 ↓
recipient authorization
 ↓
user policy
 ↓
data-minimization check
 ↓
redaction/filtering
 ↓
encryption
 ↓
transport
```

Examples of data that may require special treatment:

- audio;
- video;
- face/voice representations;
- location history;
- private conversations;
- household member information;
- sensitive memories;
- raw sensor data.

The default should be **do not synchronize unless explicitly eligible** for sensitive domains.

---

## 15. Derived Data Synchronization

Embeddings, FTS indexes and graph projections should generally be treated as derived data.

Preferred strategy:

```text
canonical memory/claim
        ↓
synchronize canonical data
        ↓
rebuild/recompute derived index locally
```

This avoids synchronizing implementation-specific indexes when they can be deterministically regenerated.

Exceptions may be allowed when rebuilding is prohibitively expensive and the derived artifact is version-compatible and safe.

---

## 16. Embeddings

If embeddings are synchronized, the record must identify:

- source memory version;
- embedding model ID/version;
- embedding dimensions;
- preprocessing version;
- vector format;
- creation time.

An embedding must never silently become attached to a newer memory version.

Model changes should support re-embedding from canonical source data.

---

## 17. Knowledge Graph Synchronization

Graph relationships should synchronize as semantic claims/edges with provenance, not merely as opaque graph database pages.

Example:

```text
entity A
   │
relationship R
   │
entity B
```

The synchronized representation should retain:

- relationship ID;
- subject/object IDs;
- predicate/type;
- evidence;
- provenance;
- confidence;
- validity interval;
- source version;
- supersession/deletion state.

The receiving system can rebuild its graph projection from canonical claims.

---

## 18. Media Synchronization

Large media should use a separate content-addressed or object-transfer mechanism rather than inflating the memory transaction stream.

Preferred model:

```text
memory/event metadata
        ↓
content reference + hash
        ↓
media transfer
        ↓
integrity verification
        ↓
activation
```

A metadata record must not become active as if media were available until the referenced content has passed integrity checks, unless the domain explicitly allows degraded operation.

---

## 19. Offline Queue Limits

Offline operation creates a finite-storage problem.

Novi must define per-domain queue policies:

```text
critical memory
→ retain until durable

ordinary events
→ retention policy

telemetry
→ aggregate/sample/expire

raw media
→ bounded storage policy
```

When storage approaches its limit, Novi must not randomly delete important memory merely to preserve low-value telemetry.

Priority-aware retention is required.

---

## 20. Connectivity Types

The architecture supports multiple transports.

### Wi-Fi

Preferred for high-bandwidth local synchronization and maintenance.

### Bluetooth

Useful for low-bandwidth local control/configuration and companion-device interactions.

### Ethernet / USB / local wired connection

Useful for development, recovery, diagnostics and bulk transfer.

### Internet/cloud

Optional and exceptional. It must pass the same policy, privacy and authorization controls.

No transport is part of the cognitive critical path.

---

## 21. Security

Synchronization must provide:

- authenticated peers;
- authorization;
- encrypted transport;
- replay protection;
- message integrity;
- sequence validation;
- device identity;
- credential rotation;
- revocation;
- audit records.

A physically nearby Bluetooth device must not automatically become a trusted Novi peer.

Likewise, Wi-Fi LAN presence must not imply authorization.

---

## 22. Trust Model

Every synchronization peer has an identity and trust relationship.

Example:

```text
Novi
 ├── owner phone
 ├── maintenance workstation
 ├── backup server
 └── untrusted device
```

Each peer receives only the capabilities required for its role.

Trust should be revocable without deleting Novi's local memory.

---

## 23. Companion Application

A control application should normally receive a filtered projection rather than unrestricted access to the cognitive database.

For example:

```text
Control App
   ↓
Novi API
   ↓
authorization
   ↓
privacy filter
   ↓
read projection
```

Administrative functions such as memory deletion, backup restore or policy modification require privileged operations.

---

## 24. Remote Commands

Synchronization and remote control must be separate concepts.

A device receiving synchronized state does not automatically gain action authority.

```text
sync data
    ≠
action permission
```

Remote commands must pass the autonomy/security/control pipeline independently.

This prevents a malicious or compromised synchronization peer from turning a harmless data channel into a robot-control channel.

---

## 25. Cloud Synchronization

Cloud synchronization is not part of V1's required operation.

If introduced later, it must be treated as an optional external peer with stricter controls.

Before upload:

- classify data;
- minimize data;
- apply privacy policy;
- authenticate destination;
- encrypt transport;
- maintain local copy/authority;
- record audit trail;
- support revocation/deletion where contractually possible.

Novi must remain fully operational if cloud services disappear.

---

## 26. Synchronization During Active Cognition

Synchronization must not block cognition or autonomy.

Example:

```text
Novi is navigating
        ↓
Wi-Fi reconnects
        ↓
sync begins
        ↓
resource manager limits sync
        ↓
navigation continues
```

Large transfers may be throttled or paused during high-priority physical activity.

---

## 27. Synchronization During Memory Consolidation

If consolidation is creating a new knowledge candidate while synchronization is active:

```text
consolidation proposal
       ↓
current source versions checked
       ↓
authoritative commit
       ↓
sync change generated
```

The system must never synchronize an intermediate uncommitted cognitive state.

---

## 28. Synchronization During Deletion

Deletion must outrank ordinary synchronization.

If:

```text
T1: memory M queued for upload
T2: user deletes M
T3: deletion commits
T4: upload worker wakes
```

the upload must be cancelled or rejected by a final authorization/version check.

Previously uploaded copies must follow the deletion protocol.

---

## 29. Reconnection Algorithm

A generic V1 reconnection flow:

```text
connectivity detected
        ↓
peer authentication
        ↓
capability negotiation
        ↓
protocol/version negotiation
        ↓
exchange high-level sync cursors
        ↓
identify missing changes
        ↓
privacy/authorization filtering
        ↓
transfer batches
        ↓
verify integrity
        ↓
apply idempotently
        ↓
detect conflicts
        ↓
acknowledge/reject
        ↓
advance durable cursors
        ↓
checkpoint/cleanup
```

The synchronization cursor must advance only after the relevant change has been durably accepted.

---

## 30. Batch Synchronization

Changes should normally be transferred in bounded batches.

Benefits:

- lower overhead;
- controlled memory usage;
- resumability;
- easier retry;
- bandwidth control;
- thermal/power control.

Batch boundaries must not compromise atomicity of individual semantic mutations.

---

## 31. Integrity Verification

Every transferred batch should provide integrity information.

Possible mechanisms include:

- cryptographic hash;
- authenticated transport;
- content hash;
- per-record checksum where appropriate;
- sequence/cursor verification.

A corrupted transfer must be rejected and retried without partially activating invalid data.

---

## 32. Crash Recovery

The synchronizer must survive crashes at every point:

```text
before send
mid-send
receiver accepted
ACK lost
after local ACK
before cursor update
```

The design must make retries safe.

A cursor should only move forward after durable confirmation of the corresponding operation.

---

## 33. Database Boundary

The authoritative SQLite database remains local to Novi's host.

SQLite WAL is appropriate for the local multi-process workload because readers and the writer can operate concurrently, while writes remain serialized. SQLite explicitly notes that WAL is designed for processes on the same host and is not a network-filesystem synchronization mechanism. citeturn0search0turn0search2

Therefore:

> **Never place Novi's live SQLite WAL database on a network share as a synchronization strategy.**

Synchronization occurs through the Memory/Sync APIs and change records, not by copying a live database over Wi-Fi.

SQLite also requires the `-wal` and `-shm` state to be handled correctly when copying/backup of a live WAL database is involved. citeturn0search0turn0search4

---

## 34. Backup vs Synchronization

Backup and synchronization are different.

### Backup

Goal:

> Recover Novi's state after failure.

### Synchronization

Goal:

> Reconcile changes between authorized replicas/peers.

A backup target should not automatically become a second authority.

A backup restore is an explicit administrative operation and must have a recovery procedure.

---

## 35. Database Snapshots

For large maintenance transfers, a consistent SQLite backup/snapshot may be appropriate instead of replaying millions of individual changes.

However, the snapshot must be created through a safe SQLite mechanism and must account for WAL state. SQLite documents its backup tooling and live-database copy mechanisms separately from ordinary file copying. citeturn0search1

Snapshots are especially useful for:

- initial provisioning;
- disaster recovery;
- development copies;
- full replica creation.

They do not replace normal incremental synchronization.

---

## 36. Version and Protocol Compatibility

Every synchronization peer should advertise:

- protocol version;
- schema version;
- supported domains;
- supported capabilities;
- supported compression;
- supported cryptographic algorithms;
- model/index compatibility where relevant.

Unknown fields should be handled according to forward-compatibility rules rather than silently discarded.

A peer must refuse operations it cannot safely interpret.

---

## 37. Resource Management

Synchronization competes with cognition, perception and autonomy for:

- CPU;
- GPU;
- memory;
- storage I/O;
- network bandwidth;
- power;
- thermal headroom.

The resource manager should be able to:

- throttle;
- pause;
- resume;
- prioritize;
- cancel low-value transfers.

A synchronization task must never starve safety-critical workloads.

---

## 38. Synchronization Metrics

Novi should measure:

- outbox depth;
- oldest unsynchronized change;
- bytes queued;
- bytes transferred;
- transfer latency;
- retry rate;
- conflict rate;
- rejection rate;
- deletion propagation delay;
- peer availability;
- synchronization CPU/GPU cost;
- storage pressure;
- network bandwidth;
- authentication failures;
- protocol mismatches.

These metrics belong in diagnostics/observability, not in user-facing cognitive memory by default.

---

## 39. Testing Requirements

The synchronization system must be tested under:

- no connectivity;
- intermittent Wi-Fi;
- intermittent Bluetooth;
- repeated reconnects;
- high latency;
- packet loss;
- duplicate delivery;
- reordered delivery;
- corrupted payload;
- peer restart;
- Novi restart;
- ACK loss;
- simultaneous edits;
- stale versions;
- deletion during transfer;
- privacy-policy changes while queued;
- revoked peer authorization;
- storage exhaustion;
- thermal throttling;
- power interruption;
- protocol mismatch;
- schema mismatch;
- corrupted local outbox.

Tests must verify that no synchronization failure prevents local operation.

---

## 40. Security Tests

Security validation must include:

- unauthorized peer connection;
- replayed synchronization messages;
- forged change IDs;
- altered payloads;
- privilege escalation;
- unauthorized memory domains;
- unauthorized deletion;
- malicious oversized batches;
- malformed records;
- compromised companion device;
- revoked credentials;
- network isolation.

Synchronization input is untrusted input until authenticated, authorized and validated.

---

## 41. Recommended V1 Architecture

```text
                 NOVI LOCAL STATE
                       │
                Memory Manager
                       │
             ┌─────────┴─────────┐
             │                   │
       Canonical SQLite      Sync Outbox
             │                   │
             │             Policy / Auth
             │                   │
             │             Sync Scheduler
             │                   │
             │          ┌────────┴────────┐
             │          │                 │
             │        Wi-Fi           Bluetooth
             │          │                 │
             │          └────────┬────────┘
             │                   ▼
             │              Authorized Peer
             │                   │
             └─────────────── ACK/Conflict
```

The Sync Manager is a **consumer of authoritative changes**, not a second memory authority.

---

## 42. V1 Non-Goals

V1 does not require:

- distributed consensus;
- multi-master arbitrary database writes;
- cloud-first memory;
- real-time remote mirroring of every sensor frame;
- synchronizing SQLite WAL files over a network;
- automatic conflict resolution for all knowledge;
- remote control through the synchronization channel;
- synchronization of all raw audio/video by default.

These can be evaluated later when real requirements justify them.

---

## 43. Architectural Invariants

1. Novi remains fully functional without synchronization.
2. Local authoritative state remains local.
3. Synchronization never bypasses the Memory Manager.
4. Every synchronized mutation is authenticated and authorized.
5. Every synchronized mutation is idempotent.
6. Deletion cannot be undone by a stale replica.
7. Sensitive data is not synchronized by default.
8. Remote synchronization does not grant action authority.
9. Derived indexes can normally be rebuilt from canonical data.
10. Synchronization never blocks safety-critical autonomy.
11. Live SQLite WAL files are never used as the network synchronization protocol.
12. Conflict detection is separate from transport.
13. Conflict resolution is domain-specific.
14. Failed synchronization cannot corrupt local authoritative memory.
15. Synchronization state itself is durable and recoverable.
16. Offline changes remain usable locally until normal retention/deletion rules apply.

---

## 44. Relationship to Other Memory Documents

```text
17 Event Log & Sensor Ingestion
             ↓
18 Sensor Grounding & Measurement Provenance
             ↓
Memory Manager / Canonical State
             ↓
19 Synchronization
             ↓
20 Conflict Resolution & Distributed State
             ↓
21 Backup / Recovery / Migration
```

The synchronization architecture depends on the event identity, provenance, versioning, privacy and deletion systems defined earlier.

---

## 45. Research Basis

The design is cross-validated against current SQLite documentation and NVIDIA robotics architecture.

SQLite WAL provides concurrent readers and a single writer, but is explicitly a same-host mechanism rather than a network synchronization protocol. SQLite also documents checkpointing, WAL recovery and the need to retain the WAL state when making a live copy. citeturn0search0turn0search2turn0search4

SQLite's current documentation also distinguishes consistency from durability under different `synchronous` settings; final Novi configuration must choose durability appropriate to the robot's power-loss requirements rather than assuming a performance-oriented default is sufficient. citeturn0search3

NVIDIA Isaac ROS provides the robotics-side foundation for synchronized sensor processing on Jetson-class systems, reinforcing the broader architecture of explicit sensor timing and hardware-aware processing rather than treating physical data as an undifferentiated stream. citeturn0search6turn0search9

---

## 46. Final Principle

> **Synchronization must make Novi more connected, not more dependent.**

Novi's local memory remains the foundation. Connectivity merely provides a controlled mechanism for moving eligible information between trusted systems. The robot must remain capable, coherent, private and safe whether synchronization is continuously available, intermittent, degraded, or completely absent.
