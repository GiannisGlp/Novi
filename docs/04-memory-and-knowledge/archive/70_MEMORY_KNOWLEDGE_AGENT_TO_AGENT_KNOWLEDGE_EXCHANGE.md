# 70 — Memory Knowledge Agent-to-Agent Knowledge Exchange

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi exchanges observations, memories, knowledge, capabilities, and synchronization information with other agents or Novi instances while preserving identity, provenance, authorization, privacy, integrity, uncertainty, conflict handling, and local autonomy.

## Core Principle

> **Information received from another agent is external evidence, never automatic truth, authority, or permission.**

A remote agent can provide useful evidence, but the receiving Novi remains responsible for validating, classifying, authorizing, and deciding whether to admit or promote that information.

---

## 1. Trust Boundary

```text
REMOTE AGENT
    ↓
IDENTITY
    ↓
AUTHENTICATION
    ↓
CHANNEL INTEGRITY
    ↓
PROVENANCE
    ↓
AUTHORIZATION
    ↓
PRIVACY
    ↓
SOURCE RELIABILITY
    ↓
VALIDATION / CORROBORATION
    ↓
LOCAL ADMISSION
```

Network connectivity never bypasses this boundary.

## 2. Agent Identity

Every participating agent should have a distinct cryptographically verifiable identity where the deployment requires authenticated exchange.

Identity metadata may include:

- agent identifier;
- device identifier;
- software/model version;
- authority domain;
- key/certificate information where applicable;
- capability declaration;
- provenance context.

An agent claiming an identity does not prove that the claim is authentic.

## 3. Authentication

Authentication answers:

> Which agent is communicating?

It does not answer:

> What is this agent allowed to send or request?

Authentication and authorization remain separate.

## 4. Authorization

A remote agent must have explicit permission for each protected operation or scoped capability.

Possible operations:

```text
READ
SEND
REQUEST
PUBLISH
SUBSCRIBE
SYNC
SHARE
DELETE_REQUEST
DELEGATE
ADMINISTER
```

A remote agent cannot obtain authority merely by being authenticated.

## 5. Local Sovereignty

The receiving Novi remains authoritative over its own:

- safety state;
- private memories;
- identity database;
- access policy;
- retention policy;
- deletion state;
- physical-world state;
- action authorization.

Remote knowledge cannot override these boundaries.

## 6. Exchange Object

An exchanged knowledge object should carry, where applicable:

```text
object_id
source_agent
source_event
creation_time
event_time
validity_interval
content_type
content
provenance
confidence
uncertainty
source_reliability
privacy_class
authorization_scope
schema_version
model/version metadata
integrity metadata
supersedes / conflicts-with references
```

## 7. Provenance

The receiver must be able to distinguish:

```text
remote observation
remote interpretation
remote inference
remote knowledge
remote recommendation
remote command request
```

These are not equivalent evidence classes.

## 8. Observation vs Knowledge

Example:

```text
Agent A observed: "object detected at coordinate X"
```

is different from:

```text
Agent A concluded: "object X is the user's toolbox"
```

The receiver should preserve that distinction.

## 9. Trust Is Not Transitive by Default

```text
Novi trusts Agent A
Agent A trusts Agent B
```

does not automatically imply:

```text
Novi trusts Agent B
```

Trust delegation requires explicit policy.

## 10. Corroboration

Two agents may provide corroborating evidence.

However:

```text
Agent A and Agent B
   ↓
obtained information from the same source
```

is not necessarily independent corroboration.

Shared upstream dependencies must be considered.

## 11. Agent Diversity

Independent sensors, models, implementations, operators, or data sources can increase evidence diversity.

But nominally different agents that share identical models, data, or network sources may have correlated failure modes.

## 12. Conflict Handling

If agents disagree:

```text
Agent A → X
Agent B → Y
```

preserve both claims and evaluate:

- provenance;
- source reliability;
- event time;
- currentness;
- independence;
- sensor quality;
- context;
- uncertainty;
- consequence of being wrong.

Never resolve a conflict solely by message arrival order.

## 13. Current Physical State

For embodied physical state, local current sensing may supersede remote historical or stale observations.

```text
remote: hallway clear 10 minutes ago
local LiDAR: obstacle present now
```

The current local observation has priority for current physical safety decisions, subject to sensor-health evaluation.

## 14. Remote Memory Is Not Local Memory

Receiving a memory does not automatically make it a local memory.

Suggested lifecycle:

```text
RECEIVED
 ↓
VALIDATED
 ↓
QUARANTINED / PROVISIONAL / ADMITTED
 ↓
OPTIONAL CONSOLIDATION
 ↓
LOCAL KNOWLEDGE PROMOTION
```

## 15. Privacy

Remote agents must not receive private local memories without explicit authorization.

Similarly, received private data must not automatically become visible to local users, agents, or tools.

Privacy classification travels with the exchanged data.

## 16. Purpose Limitation

A request such as:

> "Tell me where the user is."

must be evaluated for purpose and authorization.

Authenticated agent identity alone is insufficient.

## 17. Data Minimization

Exchange only the minimum information needed for the authorized purpose.

```text
full private memory
      ↓
minimal useful representation
```

## 18. Capability Exchange

Agents may exchange capability information, but capability declarations do not automatically grant permissions.

```text
Agent says: "I can navigate."
      ≠
Novi authorizes navigation.
```

## 19. Commands vs Knowledge

A remote message can be:

```text
INFORMATION
REQUEST
RECOMMENDATION
COMMAND
```

These must be represented separately.

A remote command is never automatically executable.

## 20. Action Authorization

If a remote agent requests an action:

```text
REMOTE REQUEST
    ↓
AUTHENTICATION
    ↓
AUTHORIZATION
    ↓
LOCAL POLICY
    ↓
SAFETY CHECK
    ↓
ACTION / DENY
```

Memory or knowledge exchange cannot bypass action safety.

## 21. Prompt Injection

Remote agents may send malicious text designed to manipulate Novi.

```text
remote content
   ≠
system instruction
```

Incoming content must remain data until explicitly interpreted through authorized policy.

## 22. Memory Poisoning

A malicious or compromised agent could attempt to inject false memories.

Controls include:

- source identity;
- provenance;
- admission policy;
- corroboration;
- anomaly detection;
- confidence limits;
- quarantine;
- rollback;
- auditability.

## 23. No Self-Validation

An agent cannot establish the truth of its own claim by:

```text
sending claim
 ↓
receiving its own claim back
 ↓
claim appears corroborated
```

Looped or mirrored evidence is not independent evidence.

## 24. Schema Validation

Incoming objects must be validated against an explicit schema/version.

Malformed or unknown objects should be rejected or quarantined rather than guessed into the local schema.

## 25. Version Compatibility

Agents should exchange protocol/schema versions and negotiate compatible representations.

Unknown fields should be handled according to explicit compatibility policy.

## 26. Replay Protection

Repeated old messages should not be mistaken for new observations.

Where applicable, use:

- unique event IDs;
- sequence numbers;
- timestamps;
- nonces;
- replay windows;
- idempotency keys.

## 27. Duplicate Messages

Retransmission must not create duplicate memories.

Deduplication should preserve genuinely distinct repeated observations.

## 28. Ordering

Message arrival order is not necessarily event order.

Maintain:

```text
event time
receipt time
logical sequence/version
```

## 29. Offline Operation

Novi must remain fully functional when Wi-Fi, Bluetooth, and external networks are unavailable.

Agent exchange is therefore an optional capability, not a prerequisite for core memory or cognition.

## 30. Reconnection

When connectivity returns:

```text
local state
   ↓
exchange pending changes
   ↓
validate
   ↓
resolve conflicts
   ↓
apply authorized updates
```

Remote synchronization must not silently overwrite newer local decisions.

## 31. Offline Queues

Pending outbound/inbound synchronization may use durable queues where appropriate.

Queued data remains subject to:

- expiration;
- privacy policy;
- deletion policy;
- authorization revocation;
- integrity checks.

## 32. Deletion Propagation

If a shared memory is deleted or access is revoked:

```text
local deletion/restriction
      ↓
propagation policy
      ↓
remote replicas
```

The architecture must define what can be recalled, restricted, or deleted remotely.

## 33. Tombstones

Deleted synchronized objects should use durable tombstone/version information where required to prevent stale replicas from resurrecting them.

## 34. Conflict Resolution

Conflict resolution should consider:

- authoritative source;
- event time;
- version;
- provenance;
- policy;
- confidence;
- physical locality;
- current sensor evidence;
- user-authorized preferences.

No universal last-write-wins policy should be assumed for all memory classes.

## 35. Knowledge Promotion

Remote knowledge should normally enter as provisional evidence before becoming authoritative local knowledge.

```text
REMOTE KNOWLEDGE
      ↓
LOCAL VALIDATION
      ↓
LOCAL POLICY
      ↓
PROMOTION / REJECTION
```

## 36. Shared Knowledge

Some knowledge can intentionally be shared among a group of agents.

Shared knowledge should have an explicit namespace and governance policy.

```text
agent/private
household/shared
mission/shared
system/protected
```

## 37. Namespace Isolation

One agent's private namespace must not become visible through generic shared-memory queries.

Cross-namespace access requires authorization.

## 38. Delegation

If an agent delegates a task, the delegated authority should be:

- explicit;
- scoped;
- purpose-bound;
- time-limited where appropriate;
- revocable;
- auditable.

Delegation must not create unrestricted privilege escalation.

## 39. Multi-Agent Learning

Experience shared between agents must preserve:

- source agent;
- context;
- task/environment;
- evidence quality;
- outcome;
- uncertainty;
- privacy classification.

A successful experience in one environment is not automatically universally valid.

## 40. Behavioral Transfer

```text
Agent A learned policy X
      ↓
Agent B receives X
```

does not prove X is safe or effective on Agent B's hardware, sensors, environment, or capabilities.

Local validation is required before safety-critical adoption.

## 41. Hardware Capability Mismatch

A remote agent may have sensors Novi does not have.

Example:

```text
Agent A has thermal + LiDAR
Novi has camera only
```

Novi must not assume it possesses evidence derived from unavailable hardware unless it is explicitly receiving and trusting the remote observation.

## 42. Model Capability Mismatch

Different models may have different failure characteristics.

Confidence values should not be blindly compared across incompatible models or calibration schemes.

## 43. Time and Context Transfer

Shared knowledge must preserve context such as:

- location;
- environment;
- task;
- hardware;
- software version;
- time;
- operating conditions.

## 44. Geospatial Exchange

Agents may exchange:

- positions;
- landmarks;
- maps;
- routes;
- observed obstacles;
- explored areas.

Location data is privacy-sensitive and must be explicitly authorized.

## 45. Map Merging

Maps from multiple agents may use different coordinate frames, calibration, timestamps, or uncertainty models.

Map fusion must validate coordinate-frame compatibility before merging.

## 46. Sensor Observation Exchange

Remote observations should include enough metadata to interpret them:

```text
sensor type
sensor ID
calibration/version
measurement time
location/pose
measurement uncertainty
processing model/version
```

## 47. Security of Transport

Where networking is used, communication should use appropriate authenticated and integrity-protected channels.

Transport security protects the channel; it does not establish factual truth of the payload.

## 48. Encryption

Sensitive exchanged data should use appropriate encryption in transit and at rest according to the security architecture.

Keys remain outside ordinary semantic memory.

## 49. Rate Limits

Agents must not be able to consume unlimited memory, bandwidth, CPU, GPU, storage, or indexing capacity.

Apply resource budgets and backpressure.

## 50. Malicious Agent Behavior

The architecture should tolerate agents that:

- send malformed data;
- flood messages;
- send contradictory claims;
- replay old data;
- attempt privilege escalation;
- inject instructions;
- attempt memory poisoning;
- impersonate another agent.

Such behavior should trigger isolation or revocation according to security policy.

## 51. Agent Revocation

If an agent becomes compromised or untrusted:

```text
REVOKE
 ↓
STOP AUTHORIZED EXCHANGE
 ↓
QUARANTINE RECEIVED DATA WHERE REQUIRED
 ↓
ASSESS DEPENDENCIES
 ↓
ROLL BACK / REVALIDATE AFFECTED KNOWLEDGE
```

## 52. Audit Trail

Record important exchange events:

- sender;
- receiver;
- object/event ID;
- operation;
- authorization decision;
- timestamp;
- protocol/version;
- validation result;
- admission decision;
- conflicts;
- failures.

Audit data is itself protected information.

## 53. Observability

Monitor:

- message rates;
- validation failures;
- duplicate rates;
- conflict rates;
- latency;
- queue growth;
- unauthorized requests;
- rejected agents;
- memory poisoning indicators;
- synchronization health.

## 54. Testing

Test at minimum:

- forged identity;
- revoked agent;
- replay attack;
- duplicate events;
- out-of-order events;
- malformed schemas;
- prompt injection;
- memory poisoning;
- shared-source false corroboration;
- conflicting agents;
- privacy leakage;
- namespace escape;
- capability escalation;
- confused deputy;
- stale remote state;
- offline queue recovery;
- deletion/tombstone propagation;
- network loss;
- corrupted messages;
- rate exhaustion;
- hardware/model mismatch;
- map-frame mismatch.

## 55. Architectural Invariants

1. Remote information is external evidence, not automatic truth.
2. Authentication and authorization remain separate.
3. Local Novi retains sovereignty over its safety and security policies.
4. Trust is not transitive by default.
5. Shared-source claims are not independent corroboration.
6. Remote commands are never automatically executable.
7. Memory exchange cannot bypass action safety.
8. Remote agents cannot grant themselves local privileges.
9. Received knowledge is locally validated before promotion.
10. Privacy restrictions travel with exchanged data.
11. Private namespaces remain isolated by default.
12. Replay and duplicate protection are mandatory.
13. Event time is distinct from receipt time.
14. Offline operation remains fully functional without agent connectivity.
15. Synchronization cannot silently resurrect deleted memory.
16. Last-write-wins is not a universal conflict policy.
17. Sensor/model/hardware context travels with important observations.
18. Behavioral learning does not transfer blindly between different embodiments.
19. Resource consumption by remote agents is bounded.
20. Compromised agents can be revoked and their derived influence investigated.
21. Audit trails are protected and privacy-aware.
22. Network security protects transport integrity but does not establish truth.
23. No remote agent can override local safety controls.

## 56. Final Principle

> **Agents may cooperate, but Novi remains responsible for what it believes, remembers, shares, learns, and does.**

Agent-to-agent exchange should increase Novi's capabilities without transferring authority blindly. Every exchanged object remains traceable, scoped, validated, privacy-aware, and subject to local policy. Connectivity is an enhancement—not a dependency—and cooperation must never compromise local autonomy, safety, truthfulness, or privacy.
