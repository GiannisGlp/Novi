# 25 — Memory Security and Integrity

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi protects memory, knowledge, provenance, indexes, synchronization state and learning artifacts against unauthorized access, unauthorized modification, corruption, poisoning, replay, rollback and unsafe self-modification.

This document establishes security boundaries. Detailed cryptographic algorithms, key-management implementation, operating-system hardening and penetration-test procedures will be specified in dedicated engineering documents.

## Core Principle

> **Novi's ability to learn and evolve must never imply unrestricted authority to modify its own security boundaries, safety policies, provenance or trusted memory.**

Memory is a high-value cognitive asset. It must be protected as both data and an input to future decisions.

---

## 1. Security Objectives

The memory architecture must protect:

- confidentiality;
- integrity;
- authenticity;
- availability;
- provenance;
- deletion correctness;
- authorization boundaries;
- version integrity;
- recovery integrity;
- synchronization integrity;
- learning integrity;
- evaluation integrity.

Security decisions must also preserve offline operation.

---

## 2. Threat Model

Novi should assume that threats can originate from:

- accidental software bugs;
- corrupted storage;
- malformed sensor input;
- compromised peripherals;
- compromised processes;
- unauthorized local users;
- unauthorized network peers;
- malicious synchronized data;
- replayed commands;
- stale backups;
- compromised update packages;
- prompt/content injection through the environment;
- memory poisoning;
- compromised models or model artifacts;
- physical access to the robot;
- supply-chain compromise.

The exact threat model will be refined through security assessment.

---

## 3. Trust Boundaries

Novi must distinguish at least:

```text
HARDWARE / SAFETY
       │
       ▼
SYSTEM / OS
       │
       ▼
MEMORY MANAGER
       │
       ├── canonical memory
       ├── provenance
       └── policy
       │
       ▼
COGNITION / MODELS
       │
       ▼
APPLICATIONS / AGENTS
       │
       ▼
EXTERNAL DEVICES / NETWORK
```

Crossing a boundary must require explicit validation.

---

## 4. Canonical Memory Authority

The Memory Manager is the authoritative gate for semantic memory mutation.

Other components must not directly modify canonical memory tables/files outside approved interfaces.

```text
Agent ───────┐
Cognition ───┤
Autonomy ────┤
Control App ─┤ → Memory API → Policy → Canonical Store
Sync Peer ───┘
```

This prevents individual agents or models from bypassing security and provenance rules.

---

## 5. Least Privilege

Every process, agent and integration should receive only the permissions it requires.

Examples:

```text
Perception:
  create observations
  read required sensor configuration

Memory retrieval:
  read permitted memories

Learning:
  propose knowledge changes
  cannot directly alter policy

Synchronization:
  submit authenticated changes
  cannot bypass admission

Safety:
  independent protected authority
```

Privileges should be explicit and auditable.

---

## 6. Memory Classification

Memory should be classified by sensitivity and impact.

Potential classes:

- public/non-sensitive;
- ordinary personal;
- private personal;
- location history;
- identity information;
- biometric-derived information;
- security-sensitive;
- system/security policy;
- safety-critical state;
- cryptographic/key material.

The exact taxonomy must align with the privacy architecture.

---

## 7. Integrity of Canonical Data

Canonical memory records must be protected against silent modification.

Controls may include:

- transactional writes;
- version numbers;
- append-only event records where appropriate;
- integrity metadata;
- checksums/hashes;
- authenticated records for security-sensitive data;
- filesystem/storage integrity mechanisms.

Hashing alone does not establish authenticity unless the integrity metadata itself is protected.

---

## 8. Provenance Integrity

A memory claim must not be allowed to alter its own provenance after creation without an auditable operation.

For example:

```text
original source = camera_01
```

must not silently become:

```text
original source = user_confirmed
```

A new user confirmation creates new evidence and may change the state according to policy; it does not rewrite historical provenance.

---

## 9. Append-Only Evidence

Evidence that represents historical events should generally be immutable after acceptance.

Corrections should be represented as new events/claims that supersede or annotate prior evidence.

This protects the audit trail and makes learning/replay safer.

Exceptions require explicit policy.

---

## 10. Mutable Projections

Current-state tables, indexes and caches may be mutable.

They must be reconstructible from trusted canonical evidence where practical.

```text
trusted events / memories
        ↓
current state
        ↓
FTS / embeddings / graph / caches
```

Derived state must not silently become the only surviving representation of a semantic fact.

---

## 11. Embedding and Index Integrity

Embeddings, vector indexes, FTS indexes and graph projections are derived artifacts.

Security requirements:

- associate derived data with source memory version;
- record model/version used to create embeddings;
- detect stale indexes;
- rebuild from canonical memory after corruption;
- prevent an index from introducing records not present in authorized canonical state.

An attacker who can alter an index must not be able to create a new canonical memory merely by changing search results.

---

## 12. Memory Poisoning

Memory poisoning occurs when incorrect or malicious information is deliberately or accidentally admitted and later influences cognition.

Potential sources include:

- malicious users;
- compromised devices;
- manipulated sensors;
- adversarial visual/audio content;
- malicious synchronized replicas;
- incorrect model-generated claims;
- repeated low-quality observations.

Protection requires provenance, admission policy, corroboration, confidence handling and monitoring.

Repetition alone must not make an untrusted claim authoritative.

---

## 13. Environmental Prompt Injection

Novi's physical environment may contain adversarial instructions:

```text
sign
screen
voice
QR code
printed message
web content
```

Perception of text or speech does not automatically grant authority to execute the instruction.

The system must distinguish:

```text
observed instruction
       ≠
authorized command
```

Commands must pass the appropriate identity, authorization, safety and policy checks.

---

## 14. User-Generated Memory

User statements are valuable but must retain source identity and verification state.

Example:

```text
user statement
   ↓
user-authenticated evidence
   ↓
memory candidate
```

A statement from an unknown speaker should not automatically receive the authority of an authenticated user.

---

## 15. Agent Permissions

Autonomous agents should have explicit capabilities.

An agent may be allowed to:

- create candidate memories;
- retrieve specific classes of memory;
- propose knowledge changes;
- request verification;
- initiate maintenance.

It should not automatically be allowed to:

- disable security;
- alter safety policies;
- erase audit trails;
- rewrite provenance;
- change authorization rules;
- install arbitrary models;
- grant itself permissions.

---

## 16. Self-Modification Boundary

Novi is intended to continuously evolve, but self-improvement must have protected boundaries.

The adaptive system may modify approved:

- learned parameters;
- knowledge;
- memory organization;
- non-critical preferences;
- approved models/configuration within controlled procedures.

It must not autonomously redefine:

- safety constraints;
- security policy;
- authentication trust roots;
- authorization boundaries;
- audit requirements;
- deletion guarantees;
- evaluation gates;
- protected hardware controls.

Changes to these areas require a higher-trust administrative or engineering path.

---

## 17. Policy Immutability / Protected Policy

Critical policies should have stronger protection than ordinary memories.

Examples:

```text
Safety policy
Security policy
Privacy policy
Authorization policy
Evaluation gates
```

These should not be editable through ordinary memory-learning mechanisms.

---

## 18. Authentication

Any external actor capable of changing memory must be authenticated.

Potential actors:

- local control application;
- maintenance workstation;
- authorized phone;
- synchronization peer;
- update system.

Authentication must be separate from semantic trust.

A successfully authenticated device is not automatically authorized to modify every memory class.

---

## 19. Authorization

Authorization should evaluate:

- actor identity;
- capability;
- memory classification;
- requested operation;
- context;
- user authorization;
- safety state;
- device trust;
- offline/online state.

The authorization decision must occur before canonical mutation.

---

## 20. Synchronization Security

Incoming synchronized data must be treated as untrusted input until validated.

Required checks include:

- peer authentication;
- authorization;
- schema compatibility;
- message integrity;
- freshness;
- replay protection;
- provenance;
- deletion state;
- conflict resolution;
- privacy policy.

Cryptographic authenticity proves who sent data; it does not prove the semantic claim is true.

---

## 21. Replay Protection

Previously accepted commands/events must not be accepted again as new mutations.

Use appropriate combinations of:

- unique change IDs;
- monotonic sequence/cursor state;
- nonce/session mechanisms;
- authenticated timestamps where appropriate;
- idempotency records.

Replay protection must work offline and after restart.

---

## 22. Rollback Protection

A stale but authentic backup or replica must not silently roll canonical memory backwards.

Example:

```text
canonical version = 900
backup version = 700
```

Restoring version 700 requires an explicit recovery decision and reconciliation process.

It must never happen simply because the backup is cryptographically valid.

---

## 23. Deletion Integrity

Deletion is a security and privacy operation.

A deleted memory must not be resurrected by:

- stale replicas;
- stale backups;
- old indexes;
- embeddings;
- caches;
- graph projections;
- replayed events.

Restoration of deliberately deleted data requires explicit authorization and must respect the applicable deletion policy.

---

## 24. Encryption at Rest

Sensitive memory and credentials should be protected using appropriate encryption at rest.

The exact implementation should consider:

- device-bound keys;
- OS secure storage;
- encrypted volumes/databases;
- key rotation;
- recovery keys;
- backup encryption.

Encryption does not replace authorization or integrity controls.

---

## 25. Encryption in Transit

External synchronization and administrative connections should use authenticated encrypted channels.

This applies to:

- Wi-Fi;
- Ethernet;
- Bluetooth where applicable;
- remote maintenance;
- optional cloud synchronization.

Local offline cognition must not require a network connection.

---

## 26. Key Management

Cryptographic keys must not be stored as ordinary unprotected memory.

The architecture should eventually define:

- device identity keys;
- transport keys;
- storage-encryption keys;
- backup keys;
- signing keys;
- recovery keys;
- rotation;
- revocation;
- secure provisioning;
- lost-device recovery.

Key compromise must have a defined response.

---

## 27. Physical Access

A physical attacker may have access to:

- storage;
- USB;
- debug interfaces;
- cameras;
- microphones;
- network interfaces;
- maintenance ports.

The final security architecture should consider:

- secure boot;
- disabled production debug interfaces;
- authenticated maintenance mode;
- encrypted storage;
- tamper detection where justified;
- hardware root of trust where practical.

Exact controls depend on the selected hardware.

---

## 28. Secure Boot and Trusted Software

Where supported by the selected platform, Novi should use a verified boot chain so that unauthorized system software cannot silently become trusted.

The boot trust chain should cover, as appropriate:

```text
hardware root of trust
        ↓
bootloader
        ↓
OS
        ↓
driver/runtime
        ↓
Novi services
```

NVIDIA platform security capabilities should be evaluated during detailed Jetson engineering rather than assumed.

---

## 29. Model Integrity

Models are part of Novi's trusted computational environment.

The system should verify:

- model identity;
- model version;
- artifact integrity;
- source/provenance;
- compatibility;
- evaluation status.

An unverified model must not automatically become part of the trusted cognition path.

---

## 30. Model Update Boundary

Model updates should pass through controlled lifecycle stages:

```text
candidate model
      ↓
integrity verification
      ↓
compatibility checks
      ↓
benchmark evaluation
      ↓
safety/privacy checks
      ↓
staged deployment
      ↓
health monitoring
      ↓
approval / rollback
```

A model should not update itself simply because it believes a new model is better.

---

## 31. Learning Integrity

Continuous learning creates a security challenge because learning changes future behavior.

Learning inputs should therefore be classified:

```text
trusted
verified
unverified
rejected
```

High-impact learned changes should require stronger evidence and evaluation than low-impact personalization.

---

## 32. Security of Evaluation

Novi must not be able to modify the criteria used to determine whether its own changes are safe without passing through the protected evaluation governance path.

Otherwise:

```text
Novi changes itself
      ↓
Novi changes benchmark
      ↓
Novi declares success
```

would be possible.

Evaluation baselines and gates therefore require stronger authority than ordinary learning state.

---

## 33. Audit Integrity

Security-relevant audit records should be protected from ordinary mutation.

Where appropriate, use:

- append-only records;
- integrity chaining;
- authenticated logs;
- restricted deletion;
- secure time sources where available.

Audit data remains subject to privacy and retention policies.

---

## 34. Privacy vs Security

Security controls must not accidentally violate privacy principles.

For example, recording every raw microphone stream forever to make debugging easier is not an acceptable default.

The architecture should favor:

```text
minimum necessary data
        ↓
appropriate retention
        ↓
protected access
```

rather than unlimited surveillance data.

---

## 35. Offline Security

Security must remain effective without Internet access.

Offline Novi must still enforce:

- local authentication;
- authorization;
- memory protection;
- integrity validation;
- deletion rules;
- safety boundaries;
- secure storage;
- audit controls.

Network services may improve synchronization and remote management but cannot be the sole security mechanism.

---

## 36. Resource Exhaustion

Security must also protect memory services from resource exhaustion.

Examples:

- enormous memory write requests;
- unbounded embeddings;
- oversized events;
- synchronization floods;
- repeated conflict generation;
- malicious media;
- excessive logging.

Controls should include:

- quotas;
- rate limits;
- queue limits;
- size limits;
- backpressure;
- admission policies;
- circuit breakers.

---

## 37. Sensor Trust

Sensors are not automatically truthful because they are physically connected.

Novi should monitor:

- calibration;
- health;
- unexpected values;
- impossible transitions;
- disagreement with independent sensors;
- firmware identity;
- timing anomalies.

A compromised sensor should be able to lose trust without compromising the entire memory system.

---

## 38. Hardware Safety Separation

Memory security must never override independent safety controls.

For example:

```text
AI memory:
"motor should continue"

Safety controller:
"over-temperature — stop"

Safety controller wins.
```

The memory architecture cannot authorize unsafe physical behavior.

---

## 39. Incident Response

Security incidents should have defined handling states:

```text
suspected
   ↓
contained
   ↓
validated
   ↓
recovered
   ↓
verified
   ↓
returned to service
```

Potential actions include:

- isolate peer;
- disable synchronization;
- revoke credentials;
- switch to safe mode;
- preserve evidence;
- restore trusted state;
- rebuild derived indexes;
- re-evaluate models;
- require administrator intervention.

---

## 40. Compromised Memory

If a memory store is suspected of compromise, Novi must not blindly restore every record.

Recovery should consider:

- last known trusted checkpoint;
- event integrity;
- audit records;
- synchronized copies;
- deletion history;
- model versions;
- evaluation results.

A trusted recovery point must be established before returning to normal operation.

---

## 41. Security State as First-Class State

Novi should maintain an internal security posture such as:

```text
NORMAL
DEGRADED
SUSPECTED_COMPROMISE
ISOLATED
RECOVERY
SAFE_MODE
```

Security state can restrict capabilities.

For example:

```text
SUSPECTED_COMPROMISE
        ↓
stop external synchronization
        ↓
retain local safety/autonomy
        ↓
protect memory
        ↓
request authorized recovery
```

---

## 42. Observability

Security telemetry should include:

- denied memory mutations;
- authorization failures;
- rejected sync changes;
- replay attempts;
- integrity failures;
- model verification failures;
- unexpected privilege use;
- unusual memory-write rates;
- poisoning indicators;
- sensor trust changes;
- security-state transitions.

Security telemetry must itself be protected and privacy-aware.

---

## 43. Testing

Security validation should include:

- unauthorized memory writes;
- privilege escalation attempts;
- malformed memory records;
- corrupted SQLite/index data;
- tampered provenance;
- replayed events;
- stale backups;
- stale replicas;
- deletion resurrection;
- malicious synchronized data;
- prompt injection through vision/audio;
- model tampering;
- unauthorized model updates;
- sensor spoofing scenarios;
- resource exhaustion;
- offline attacks;
- physical-access scenarios;
- key compromise/revocation;
- recovery after compromise.

Penetration testing and threat modeling should be performed against the actual prototype.

---

## 44. Security Invariants

1. No model or agent may bypass the Memory Manager for canonical semantic writes.
2. Authentication does not imply universal semantic authority.
3. Provenance cannot be silently rewritten.
4. Historical evidence must remain auditable.
5. Deletions cannot be silently resurrected.
6. Stale backups cannot silently roll back canonical state.
7. Derived indexes cannot create authoritative memories.
8. Synchronization input is untrusted until validated.
9. Replay protection survives restart and offline operation.
10. Critical security and safety policies cannot be modified through ordinary learning.
11. Novi cannot redefine its own security boundaries as part of ordinary self-improvement.
12. Evaluation criteria protecting self-modification cannot be weakened by the adaptive system itself.
13. Safety hardware remains authoritative over cognition.
14. Security must remain functional without network access.
15. Sensitive data remains subject to privacy and retention controls.
16. Security failures must produce observable, auditable state changes.

---

## 45. Final Principle

> **Novi may learn from the world, but the world must never be allowed to silently rewrite what Novi trusts.**

Continuous evolution requires a protected foundation. Memory, knowledge, models and learned behavior can change; the mechanisms that establish trust, safety, provenance, authorization, privacy and evaluation must remain outside uncontrolled self-modification.

This separation is essential for an autonomous robot that is expected to become more capable over time without becoming progressively less governable.
