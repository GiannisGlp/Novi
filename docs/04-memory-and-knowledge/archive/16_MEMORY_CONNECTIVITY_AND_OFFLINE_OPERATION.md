# 16 — Memory Connectivity and Offline Operation

## Status

**DESIGN — V1**

## Purpose

Define how Novi's Memory and Knowledge subsystem behaves when Wi-Fi, Bluetooth, and external network connectivity are available, unavailable, intermittent, degraded, or restored.

This document operationalizes the system-level rule:

> **Novi must be fully operational without Wi-Fi, Bluetooth, or external network access.**

Connectivity is a capability extension, never a prerequisite for core memory, knowledge, cognition, autonomy, safety, personality, diagnostics, or local interaction.

---

## 1. Core Principle

```text
                         NOVI CORE
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
    Cognition             Memory              Autonomy
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    Local storage/indexes
                            │
                 ┌──────────┴──────────┐
                 │                     │
               Wi-Fi              Bluetooth
             OPTIONAL             OPTIONAL
```

Removing connectivity must not remove the core memory system.

The robot must continue to:

- store local memories;
- retrieve local knowledge;
- learn locally;
- consolidate locally;
- use local embeddings/indexes where configured;
- update the local world model;
- retain provenance;
- process deletion requests;
- run diagnostics;
- serve local cognition and autonomy.

---

## 2. Connectivity States

The memory subsystem recognizes at least four states:

### ONLINE

Required configured network capabilities are reachable.

### PARTIALLY CONNECTED

Some connectivity is available but one or more transports/services are unavailable.

Examples:

- Wi-Fi available, Bluetooth unavailable;
- Bluetooth available, Wi-Fi unavailable;
- local LAN available, Internet unavailable.

### OFFLINE

No external network transport is available.

### DEGRADED

A transport exists but has high latency, packet loss, intermittent failure, low bandwidth, authentication failure, or service unavailability.

Connectivity state must be observable by the capability layer but must not be treated as a global cognition failure.

---

## 3. Memory Operation Classification

Every connectivity-sensitive operation must declare whether it is:

### LOCAL-REQUIRED

Must work without connectivity.

Examples:

- memory read;
- memory write;
- local retrieval;
- deletion;
- local knowledge update;
- audit record creation.

### LOCAL-PREFERRED

Works locally and may use network resources when available.

Examples:

- document enrichment;
- optional external knowledge lookup;
- model download/update.

### CONNECTIVITY-OPTIONAL

Useful but not required for normal local operation.

Examples:

- remote monitoring;
- remote control;
- synchronization;
- external information retrieval.

### CONNECTIVITY-DEPENDENT

Cannot function without a remote resource.

These capabilities must have an explicit degraded/offline behavior where practical and must never be silently inserted into critical autonomous loops.

---

## 4. Offline Memory Path

The offline path is first-class:

```text
Sensor / User / Cognition
          ↓
      Local Event
          ↓
    Memory Manager
          ↓
       SQLite
          ↓
  Local FTS / Vector / Graph
          ↓
       Retrieval
          ↓
      Cognition
```

No network request is required anywhere in this path.

---

## 5. Bluetooth Is Not a Memory Dependency

Bluetooth may connect peripherals, phones, sensors, controllers, or other local devices.

Bluetooth loss must not prevent Novi from accessing its own canonical memory.

If a Bluetooth sensor disappears:

```text
sensor unavailable
      ↓
capability degraded
      ↓
world-state uncertainty updated
      ↓
memory records sensor absence
      ↓
other local sensors continue
```

Novi must not fabricate sensor values to hide the loss.

---

## 6. Wi-Fi Is Not a Memory Dependency

Wi-Fi may provide:

- remote control;
- external information;
- software updates;
- synchronization;
- optional cloud services;
- development monitoring.

Loss of Wi-Fi must not stop local memory or cognition.

For example:

```text
Wi-Fi lost
   ↓
external lookup unavailable
   ↓
local knowledge still available
   ↓
Novi can answer from local evidence
   ↓
if insufficient → state uncertainty / ask / defer
```

Novi must never turn network failure into fabricated knowledge.

---

## 7. Synchronization Architecture

If future deployments use another authorized device or server, synchronization is an explicit subsystem.

```text
                  LOCAL NOVI
                     │
                Sync Outbox
                     │
              connectivity
                     │
                     ▼
              Remote Endpoint
                     │
                Sync Inbound
                     │
                     ▼
              Conflict Resolver
                     │
                Memory Manager
```

Synchronization must not directly mutate SQLite outside the Memory Manager.

---

## 8. Outbox

Connectivity-dependent outbound operations may be represented by a durable outbox.

Each item should contain:

- operation ID;
- source entity/version;
- destination/capability;
- data classification;
- privacy policy reference;
- authorization context;
- provenance;
- creation time;
- expiration time if applicable;
- retry count;
- status.

The outbox must be subject to the same deletion and privacy rules as memory.

---

## 9. Do Not Queue Everything

Offline mode must not automatically mean:

> store everything now and upload everything later.

Before an outbound item enters the outbox, Novi evaluates:

- purpose;
- privacy classification;
- retention;
- user consent/authorization where required;
- destination trust;
- data minimization;
- expiration;
- whether the operation is still useful after reconnection.

Some events should remain permanently local.

---

## 10. Reconnection

When connectivity returns:

```text
connection restored
        ↓
capability verification
        ↓
authentication
        ↓
policy evaluation
        ↓
outbox selection
        ↓
bounded synchronization
        ↓
conflict detection
        ↓
validated commit
```

Reconnection must not trigger an unrestricted synchronization storm.

---

## 11. Conflict Resolution

Local and remote data may diverge while disconnected.

Never assume:

```text
remote wins
```

or:

```text
latest timestamp wins
```

for all memory types.

Conflict policy depends on semantic type.

Examples:

- current device state → newest trustworthy observation may win;
- historical episode → preserve both events;
- user-confirmed fact → requires explicit authority handling;
- deletion → deletion must not be undone by stale remote state;
- schema version → compatibility/migration policy required.

---

## 12. Deletion During Offline Operation

Deletion must work completely offline.

If a user deletes a memory while disconnected:

```text
local deletion
   ↓
tombstone / deletion record
   ↓
derived indexes invalidated
   ↓
local memory unavailable
   ↓
future synchronization carries deletion state
```

A later synchronization must not resurrect the deleted memory from a remote copy or stale outbox item.

---

## 13. Privacy During Synchronization

A memory that is permitted locally is not automatically permitted to leave the robot.

Outbound policy evaluates:

```text
local retention permission
        ≠
external transmission permission
```

The default for sensitive data should be **do not transmit unless explicitly authorized and required**.

---

## 14. Local Retrieval During Connectivity Failure

Retrieval must expose source availability.

Example result:

```text
local_memory:
  available = true

remote_knowledge:
  available = false
```

Cognition can then distinguish:

> “I don't know.”

from:

> “I cannot currently access the external source that might know.”

That distinction must remain explicit.

---

## 15. Connectivity and Learning

Offline Novi continues learning from local experience.

```text
offline experience
       ↓
local memory
       ↓
local consolidation
       ↓
local knowledge
```

If a future online service could improve a learning candidate, the candidate may be queued for optional enrichment, but local learning must not depend on it.

---

## 16. Connectivity and Embeddings

Local embedding generation is preferred for durable local memory.

If a preferred embedding service is unavailable:

- use an approved local embedding model;
- defer embedding generation;
- maintain lexical/structured retrieval;
- mark semantic index as incomplete;
- rebuild later.

A missing vector embedding must not make a canonical memory disappear.

---

## 17. Connectivity and External Knowledge

When Novi lacks knowledge, it should distinguish:

```text
unknown locally
       ↓
Can local reasoning answer safely?
       ↓
Can an approved external source be queried?
       ↓
Is transmission allowed?
       ↓
If yes → query
If no  → ask / defer / state uncertainty
```

External answers are evidence from an external source, not automatically verified truth.

They must enter the normal provenance and knowledge-promotion pipeline.

---

## 18. Remote Control Safety

Remote commands are not inherently trusted because they arrived over Wi-Fi or Bluetooth.

They must pass:

```text
transport authentication
        ↓
identity
        ↓
authorization
        ↓
command validation
        ↓
safety policy
        ↓
execution
```

Loss or restoration of connectivity must not bypass local safety controls.

---

## 19. Offline Diagnostics

Hardware diagnostics must remain available locally.

The control application may display richer diagnostics remotely when connected, but the robot itself must retain enough local diagnostic capability to identify:

- sensor failures;
- storage failures;
- memory corruption;
- thermal issues;
- battery/power issues;
- connectivity state;
- actuator errors;
- model/runtime failures.

---

## 20. Time and Offline Operation

Connectivity may be unavailable long enough for wall-clock synchronization to become unreliable.

Novi should distinguish:

- monotonic runtime time;
- local wall-clock time;
- externally synchronized time;
- event observation time;
- event receipt time.

Memory ordering must not rely exclusively on network-synchronized timestamps.

---

## 21. Resource Protection

Synchronization and network-dependent work must be background work unless explicitly required by a capability contract.

When CPU, GPU, memory, thermal, storage, or bandwidth resources are constrained:

```text
live cognition/autonomy
        ↓
local memory
        ↓
safety
        ↓
local interaction
        ↓
synchronization
        ↓
bulk external work
```

The exact priority is policy-controlled, but connectivity work must not starve core operation.

---

## 22. Failure Modes

The subsystem must handle:

- Wi-Fi unavailable;
- Wi-Fi authentication failure;
- Internet unavailable while LAN works;
- Bluetooth unavailable;
- intermittent connectivity;
- captive portals;
- DNS failure;
- remote service unavailable;
- authentication expiry;
- partial synchronization;
- duplicate synchronization;
- stale remote data;
- conflicting local/remote data;
- deletion while offline;
- remote deletion;
- clock skew;
- outbox corruption;
- repeated reconnection cycles.

The expected behavior is graceful degradation rather than core-system failure.

---

## 23. Testing Requirements

Offline mode must be tested deliberately.

### Mandatory tests

- boot with Wi-Fi disabled;
- boot with Bluetooth disabled;
- boot with both disabled;
- run normal cognition offline;
- run memory writes offline;
- retrieve memory offline;
- consolidate memory offline;
- perform deletion offline;
- restart offline;
- simulate intermittent Wi-Fi;
- disconnect during synchronization;
- reconnect after deletion;
- duplicate synchronization messages;
- conflicting local/remote updates;
- remote service unavailable;
- high outbox volume;
- resource pressure during synchronization.

### Acceptance criterion

A loss of Wi-Fi, Bluetooth, or Internet connectivity must not cause failure of core Novi operation.

---

## 24. Architectural Invariants

1. **Canonical memory remains local.**
2. **Connectivity is optional.**
3. **Offline operation is a supported runtime profile.**
4. **No network dependency may be hidden inside a core capability.**
5. **External data is untrusted until evaluated by normal provenance/knowledge rules.**
6. **Remote transport does not grant authorization.**
7. **Deletion propagates and cannot be undone by stale synchronization.**
8. **Synchronization cannot bypass the Memory Manager.**
9. **Sensitive local data is not automatically transmitted.**
10. **Background connectivity work cannot starve core cognition/autonomy.**

## 25. Final Principle

> **Connectivity is an enhancement to Novi, not an organ Novi needs in order to think.**

Novi must remain a capable local autonomous system when completely isolated. Wi-Fi and Bluetooth may allow Novi to communicate, synchronize, obtain optional external information, connect peripherals, receive updates, and expose remote interfaces, but the robot's fundamental memory and learning loop must remain local, deterministic where appropriate, observable, auditable, privacy-aware, and operational without them.
