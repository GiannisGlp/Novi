# 61 — Memory Knowledge Privacy and Personal Data Boundaries

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define the privacy boundaries for Novi's memory and knowledge systems: what personal information may be observed, processed, remembered, inferred, retrieved, shared, retained, learned from, or deleted.

This document is an architectural specification, not legal advice. Novi must be designed to support applicable law and policy; legal basis, controller/processor roles, notices, DPIAs, consent and retention schedules must be determined for the actual deployment and jurisdiction.

For a UK deployment, the architecture should be designed around the UK GDPR/data-protection principles and current ICO guidance. The ICO identifies purpose limitation, data minimisation, accuracy, storage limitation, integrity/confidentiality and accountability as core principles, and requires data protection by design and default throughout the lifecycle. citeturn0search2turn2search0

## Core Principle

> **Novi must remember only what it is permitted and justified to remember, for a defined purpose, for no longer than necessary, with the minimum identity linkage required to perform that purpose.**

---

## 1. Privacy Is an Architectural Property

Privacy is not a UI setting added after implementation.

```text
sensor design
 ↓
memory admission
 ↓
storage
 ↓
retrieval
 ↓
learning
 ↓
synchronization
 ↓
delete / export / audit
```

Privacy controls must exist throughout this lifecycle.

The ICO explicitly recommends integrating data protection from design through the full lifecycle and limiting, by default, the amount, extent, duration and accessibility of personal information. citeturn2search0

---

## 2. Personal Data Boundary

For architecture purposes, treat information as personal when it relates to an identified or identifiable person, directly or indirectly.

Potential Novi examples include:

- names;
- contact details;
- voice recordings;
- voice characteristics;
- face images;
- face embeddings;
- body appearance;
- location history;
- movement patterns;
- household routines;
- conversations;
- preferences;
- relationships;
- device identifiers;
- account identifiers;
- inferred attributes;
- behavioural profiles;
- health-related information;
- biometric information;
- private documents.

---

## 3. Observed vs Stored

Observation does not imply retention.

```text
camera frame
   ↓
transient perception
   ↓
object/person detection
   ↓
retain only what the task requires
```

Novi should prefer transient processing when durable storage is unnecessary.

ICO guidance notes that even transient processing of personal information remains processing, but transient handling can support data minimisation, storage limitation and privacy by design. citeturn0search6

---

## 4. Memory Admission Is a Privacy Gate

Before personal information becomes durable memory, evaluate:

```text
purpose
necessity
sensitivity
authorization
retention
access scope
future use
risk
```

If durable memory is not justified, do not admit it.

---

## 5. Purpose Limitation

Every durable personal-memory class must have a defined purpose.

```text
purpose
 ↓
permitted processing
 ↓
permitted memory
```

A later feature must not silently repurpose old personal memories.

The ICO states that purposes should be specified from the outset and that reuse for a new purpose requires compatibility assessment and an appropriate lawful basis where required. citeturn0search0

---

## 6. No “Collect Just in Case”

Novi must not retain personal information merely because it might become useful someday.

```text
possible future usefulness
        ≠
justified retention
```

ICO guidance specifically says personal data should not be collected or retained merely on the chance that it may be useful in the future. citeturn0search1

---

## 7. Data Minimisation

Store the smallest representation that satisfies the purpose.

Example:

```text
Need:
"Someone is present."

Do not automatically retain:
full video
face image
voice recording
identity
location history
```

Only the information necessary for the defined function should cross the durable-memory boundary.

---

## 8. Representation Minimisation

When possible prefer:

```text
raw recording
   ↓
structured event
   ↓
minimal memory
```

Example:

```text
"Guest detected in kitchen at 19:42"
```

may be sufficient for a particular operational purpose without retaining the complete audiovisual recording.

---

## 9. Identity Minimisation

Do not identify people when identity is unnecessary.

```text
person detected
    ≠
person identified
```

Use anonymous/ephemeral identifiers where possible.

This aligns with NIST's disassociability objective: process information or events without association to individuals or devices beyond operational requirements. citeturn1search21turn1search7

---

## 10. Identity Tiers

Potential identity states:

```text
UNKNOWN_PERSON
TEMPORARY_PERSON_ID
KNOWN_PERSON
VERIFIED_IDENTITY
PRIVILEGED_IDENTITY
```

Promotion between states requires appropriate evidence and authorization.

---

## 11. Guests and Unknown People

Novi must not assume that everyone observed in the home is a household member.

Unknown people should normally remain unidentified unless identification is necessary, permitted and appropriately authorized.

Guest information should have separate retention and access policies.

---

## 12. Household Members

Household membership does not grant unlimited access to another person's memories.

```text
household membership
      ≠
universal memory access
```

Memory access remains purpose- and authorization-scoped.

---

## 13. Private Conversations

Audio processing should distinguish:

```text
wake/interaction audio
transient speech processing
conversation memory
long-term transcript
```

These are separate retention classes.

A conversation should not become permanent memory merely because Novi heard it.

---

## 14. Voice Data

Voice can be personal information and, depending on processing and purpose, may have additional sensitivity.

Default policy should favor:

```text
local transient processing
 ↓
minimal structured memory
```

rather than indefinite raw-audio retention.

---

## 15. Facial Recognition

Face images and derived representations require special care.

Under UK GDPR guidance, biometric data processed for the purpose of uniquely identifying a natural person is special category data. citeturn0search3turn0search4

Therefore Novi must not treat face recognition as an ordinary memory feature.

If biometric recognition is used, the deployment must establish the appropriate lawful basis and separate special-category condition before processing; the ICO also recommends data protection by design and a DPIA for biometric recognition systems. citeturn0search5turn0search11

---

## 16. Face Embeddings

A face embedding is not automatically “anonymous” merely because it is not a photograph.

If it can be used to identify or distinguish a person, treat it as sensitive personal information according to the applicable legal and risk classification.

Do not expose embeddings to the language model unnecessarily.

---

## 17. Children

Children require heightened protection.

Novi should default to:

- minimal collection;
- minimal retention;
- restricted identity processing;
- no unnecessary profiling;
- no autonomous inference of sensitive attributes;
- explicit policy for child-related data.

For UK deployments, current ICO guidance states that data protection by design/default must take children's higher protection matters into account for relevant online services. citeturn2search0

---

## 18. Health Information

Novi may encounter health-related information through conversations, documents, sensors or user requests.

Health information should be treated as highly sensitive.

It should not become general-purpose long-term memory merely because Novi encountered it.

---

## 19. Inferred Personal Information

Novi must distinguish:

```text
OBSERVED
USER-STATED
INFERRED
PREDICTED
HYPOTHETICAL
```

Inference must never be represented as a directly observed fact.

---

## 20. Sensitive Inference Boundary

Novi should not silently create durable sensitive profiles from weak evidence.

Examples include inferred:

- health conditions;
- political opinions;
- religious beliefs;
- sexual orientation;
- ethnicity;
- financial vulnerability;
- psychological characteristics.

Any such processing requires explicit architectural justification and applicable legal/risk review.

UK GDPR special-category protections cover several of these categories, including health, racial/ethnic origin, religious/philosophical beliefs, political opinions, sexual orientation and biometric identification data. citeturn0search10

---

## 21. Location Privacy

Novi's GPS and mapping capabilities introduce persistent location history risks.

Location should be represented at the minimum precision necessary.

Example:

```text
Need: "Novi has been to the park."

Do not automatically retain:
continuous high-precision GPS trace
```

Fine-grained location should require a specific purpose.

---

## 22. Home Mapping Privacy

Novi may create spatial maps of the home.

These can reveal:

- room layout;
- entrances;
- sleeping areas;
- routines;
- occupancy;
- valuables;
- security weaknesses.

Home maps are therefore sensitive even when they do not contain names.

---

## 23. Environmental Privacy

Sensors can indirectly reveal human activity:

- thermal patterns;
- occupancy;
- motion;
- acoustic activity;
- appliance usage;
- sleep/wake patterns;
- presence/absence.

Derived activity information should receive a privacy classification even if no individual is explicitly named.

---

## 24. Presence Memory

Prefer:

```text
presence event
```

over continuous surveillance history when the latter is unnecessary.

Example:

```text
"Person detected in kitchen"
```

may be sufficient instead of retaining every frame that produced the observation.

---

## 25. Relationship Memory

Relationships are personal information.

Examples:

```text
person A is user's partner
person B is a colleague
person C is a frequent visitor
```

Such relationships must have purpose, provenance and access boundaries.

---

## 26. Preference Memory

User preferences may be useful long-term memory, but should be scoped.

```text
preference
 ↓
purpose
 ↓
context
 ↓
retention
```

A preference should not silently become a broad behavioural profile.

---

## 27. Personalization vs Profiling

```text
"User prefers lower lighting in the evening"
```

may be a bounded preference.

```text
"User has personality trait X because of repeated behaviour Y"
```

is a broader inference and requires a different risk assessment.

Novi should prefer the narrowest useful representation.

---

## 28. Memory Access Control

Access should be determined by:

```text
requester
purpose
memory sensitivity
relationship
authorization
context
```

Not merely by whether the requester can query the memory database.

---

## 29. Least Privilege

Subsystems should receive only the data required for their function.

```text
navigation
 → location state

voice interaction
 → current speech context

lighting
 → lighting-relevant preferences
```

No subsystem should receive the entire memory store by default.

---

## 30. LLM Data Boundary

The language model should receive the minimum relevant personal context required to answer or reason.

```text
memory store
 ↓
privacy filter
 ↓
authorization filter
 ↓
relevance filter
 ↓
LLM context
```

Never dump the full personal-memory database into a model context.

---

## 31. External Model Boundary

Personal information should not be sent to external inference providers unless the deployment explicitly authorizes it and the applicable privacy/security requirements are satisfied.

Local-first operation is the default architecture.

---

## 32. Network Independence

Core privacy controls must work when:

```text
Wi-Fi OFF
Bluetooth OFF
Cloud OFF
```

Novi must still be able to:

- restrict access;
- process local deletion;
- enforce retention;
- protect stored memory;
- operate local privacy policies.

---

## 33. Synchronization Privacy

Synchronization must not bypass local privacy policy.

```text
local memory
 ↓
privacy policy
 ↓
eligible for sync?
 ↓
encrypted transfer
```

A replica should not receive information merely because it is technically reachable.

---

## 34. Cross-Device Copies

Novi may eventually use multiple processors/devices.

Every replica must have a known data scope.

```text
device A
 └── permitted subset

device B
 └── permitted subset
```

The existence of a replica must be discoverable for deletion and audit purposes.

---

## 35. Backups

Backups are copies of personal information and remain subject to privacy policy.

Deleting information from the live system does not automatically make the backup irrelevant.

The backup architecture must define deletion/expiry handling.

ICO guidance notes that where personal data is deleted from a live system, appropriate deletion from backups should also be considered. citeturn0search12

---

## 36. Secure Deletion

Deletion must address:

```text
primary record
indexes
embeddings
knowledge graph
caches
replicas
exports
backups
learned derivatives
```

A deletion request must trigger dependency analysis rather than deleting only the visible record.

---

## 37. Derived Memory Deletion

If a deleted personal record contributed to:

```text
consolidated memory
knowledge
profile
embedding
learned behavior
```

the system must determine whether the derivative remains personal information and whether it must be deleted, corrected, retrained, or otherwise neutralized.

---

## 38. Restriction of Processing

The architecture should support a state where information is retained but cannot be used for normal processing.

```text
RESTRICTED
 ↓
stored
 ↓
not available for ordinary retrieval/learning
```

This is distinct from deletion.

The ICO describes restriction as limiting future processing while permitting storage in appropriate circumstances. citeturn2search10

---

## 39. Correction

Personal information that is inaccurate must support correction without silently rewriting historical provenance.

```text
old record
 ↓
correction evidence
 ↓
corrected current representation
```

Historical versions remain auditable where lawful and necessary.

---

## 40. User Controls

A user-facing privacy interface should eventually support granular controls such as:

```text
What may Novi remember?
What should Novi forget?
What may Novi learn from?
Which people may be identified?
Which sensors may retain data?
Which memories may leave the device?
```

Controls should be understandable and not hidden behind technical settings.

NIST's privacy engineering model emphasizes predictability and manageability, including granular alteration, deletion and selective disclosure. citeturn1search21

---

## 41. Privacy Modes

Potential modes:

```text
NORMAL
PRIVATE
GUEST
DO_NOT_REMEMBER
SENSITIVE
OFFLINE_PRIVATE
```

Mode semantics must be explicit and testable.

---

## 42. Do-Not-Remember

A user should be able to explicitly request:

> "Don't remember this."

The request should prevent durable admission where technically and legally appropriate.

Already stored information should be handled through the deletion/restriction pipeline.

---

## 43. Guest Mode

Guest mode should reduce persistent identification and personalization.

Example:

```text
guest detected
 ↓
transient interaction
 ↓
no durable identity profile by default
```

Any exception requires explicit policy.

---

## 44. Private Zones

The architecture should support physical/privacy zones.

Example:

```text
private room
 ↓
sensor processing restricted
 ↓
no durable recording
```

Zone policies should apply before memory admission.

---

## 45. Physical Privacy Controls

Hardware should support explicit indicators or controls where appropriate.

Examples:

- camera privacy shutter;
- microphone mute indicator/control;
- recording indicator;
- physical privacy switch;
- clearly visible processing state.

Software-only indicators should not be the only option for high-risk capture where hardware controls are feasible.

---

## 46. Transparency

People should be able to understand, in practical language:

- what Novi is sensing;
- what it stores;
- why it stores it;
- how long it keeps it;
- who can access it;
- whether it leaves the device;
- how to delete it.

---

## 47. Auditability

Privacy-sensitive operations should be auditable:

```text
collection
admission
access
export
sharing
learning use
sync
correction
restriction
deletion
```

Audit logs themselves must be privacy-protected.

---

## 48. Privacy Audit vs Memory Audit

A memory audit asks:

```text
Where did this memory come from?
```

A privacy audit additionally asks:

```text
Why was it retained?
Who can access it?
Was it permitted?
When should it disappear?
```

Both audit dimensions are required.

---

## 49. Privacy Risk Assessment

Before introducing a new sensitive-memory capability, evaluate:

```text
purpose
necessity
people affected
sensitivity
likelihood of misuse
impact if exposed
retention
sharing
inference risk
security controls
user control
```

For high-risk processing, the deployment should perform the appropriate DPIA/risk assessment before implementation.

The ICO describes DPIAs as a tool for identifying and reducing privacy risks and recommends them particularly where processing is likely to create high risk. citeturn2search0turn0search11

---

## 50. Function Creep Protection

New features must not silently reuse old memories for unrelated purposes.

```text
existing memory
 ↓
new feature request
 ↓
purpose compatibility check
 ↓
privacy review
 ↓
allowed / rejected
```

This is a core protection against gradual expansion of surveillance capability.

---

## 51. Learning Boundary

Novi's learning system must respect privacy policy.

```text
personal experience
 ↓
learning candidate
 ↓
privacy evaluation
 ↓
allowed learning / restricted / rejected
```

A private conversation must not automatically become a generalized behavioral rule.

---

## 52. Personal Data in Model Training

Novi should not automatically use personal memories to fine-tune or otherwise permanently modify models.

Model training/adaptation is a separate processing purpose and requires explicit architecture, governance and privacy review.

---

## 53. Memory-to-Model Leakage

A learned model may encode information derived from personal data.

Therefore deletion must consider whether the learned artifact can reproduce, identify or materially encode deleted personal information.

Where appropriate, model retraining, adapter removal or other mitigation must be considered.

---

## 54. Privacy and Retrieval Ranking

Sensitive memories should not become more visible merely because they are semantically similar.

Ranking must apply privacy/access filters before final ranking or presentation.

```text
candidate retrieval
 ↓
privacy filter
 ↓
authorization
 ↓
relevance ranking
```

---

## 55. Privacy and Search

A user should not be able to bypass access controls through clever query wording.

```text
"Tell me everything you know about X"
```

must not bypass sensitivity or authorization boundaries.

---

## 56. Privacy and Explanations

Explanations themselves can leak private information.

For example, refusing a query should not reveal that a hidden memory exists.

Prefer:

```text
"I can't provide that information."
```

over:

```text
"I have a private memory saying X about that person."
```

---

## 57. Privacy and Error Messages

Errors must not expose:

- hidden memory contents;
- identifiers;
- locations;
- credentials;
- private file names;
- other users' information.

Operational telemetry must be privacy-aware.

---

## 58. Privacy-Preserving Telemetry

Observability should prefer:

```text
aggregate metrics
pseudonymous identifiers
coarse context
redacted payloads
```

over raw personal content.

---

## 59. Third-Party Data

Information about a person who is not the primary user remains personal information.

The primary user's ownership of the device does not automatically mean unlimited rights to process every third party's information.

Guest and bystander protections are therefore mandatory architectural considerations.

---

## 60. Bystander Privacy

Novi's cameras and microphones may capture people who never intentionally interacted with it.

Default architecture should therefore favor:

```text
detect what is operationally necessary
 ↓
minimize identity
 ↓
avoid durable retention unless justified
```

---

## 61. Privacy and External Knowledge

External information about individuals should not automatically become personal memory about that person.

Source provenance, purpose, accuracy and authorization must be evaluated before admission.

---

## 62. Privacy and Security Relationship

Privacy and security are complementary:

```text
privacy policy
 ↓
what may be processed

security controls
 ↓
how permitted information is protected
```

Security cannot make an unjustified collection purpose acceptable.

NIST's framework explicitly treats privacy engineering objectives alongside confidentiality, integrity and availability. citeturn1search21turn1search13

---

## 63. Privacy and Availability

Privacy controls must not accidentally disable essential safety functions.

Example:

```text
private mode
 ↓
no long-term video retention

but
 ↓
real-time obstacle avoidance remains active
```

The distinction between transient processing and durable memory is essential.

---

## 64. Emergency Boundaries

Emergency behavior must have separately defined rules.

Privacy policy must not be used as an informal justification for arbitrary disclosure.

Any emergency exception must be explicit, narrow, logged and subject to applicable law/policy.

---

## 65. Offline-First Privacy

Because Novi must remain fully functional without Wi-Fi or Bluetooth, privacy enforcement must be local.

```text
LOCAL POLICY ENGINE
      ↓
collection
admission
retrieval
learning
sync
retention
```

Cloud services cannot be the authority for basic privacy enforcement.

---

## 66. Privacy Policy Versioning

Every important memory-policy decision should identify the policy version that permitted it.

```text
memory_123
policy = privacy_policy_v7
```

This supports auditability and future policy migration.

---

## 67. Policy Changes

Changing a privacy policy should trigger evaluation of existing memories.

```text
policy v7
 ↓
policy v8
 ↓
existing memories re-evaluated
```

New policy should not silently expand historical permissions.

---

## 68. Deletion Verification

Deletion should produce a verifiable result:

```text
REQUESTED
 ↓
LOCATED
 ↓
DEPENDENCIES IDENTIFIED
 ↓
DELETED / RESTRICTED
 ↓
INDEXES UPDATED
 ↓
REPLICAS UPDATED
 ↓
BACKUP POLICY APPLIED
 ↓
VERIFIED
```

---

## 69. Deletion Does Not Mean Historical Fabrication

If a memory is deleted, Novi should not reconstruct the deleted personal content from other traces merely to answer a query.

Deletion must be meaningful.

---

## 70. Retention Classes

Every personal-memory class should have a retention policy such as:

```text
TRANSIENT
SHORT
TASK-LIFETIME
SESSION
MEDIUM
LONG-TERM
USER-DIRECTED
LEGAL/POLICY-BOUND
```

Exact durations must be defined by deployment policy and justified by purpose.

---

## 71. No Universal Retention Period

Different information has different requirements.

```text
raw microphone buffer → seconds/minutes
navigation observation → short operational window
user preference → potentially long-term
historical event → purpose-dependent
biometric reference → high-sensitivity, tightly controlled
```

A universal TTL is inappropriate.

---

## 72. Privacy-Preserving Consolidation

Memory consolidation must not accidentally increase privacy exposure.

Example:

```text
100 transient events
 ↓
consolidation
```

The result should contain only the minimum useful information, not a permanent detailed profile merely because many events existed.

---

## 73. Privacy-Preserving Knowledge Promotion

Before promoting personal experiences to durable knowledge:

```text
candidate knowledge
 ↓
purpose check
 ↓
sensitivity check
 ↓
identity minimization
 ↓
retention policy
 ↓
promotion
```

---

## 74. Privacy-Preserving Multi-Agent Operation

Agents/processes must receive the minimum personal context required for their task.

```text
agent A
 → authorized subset

agent B
 → different authorized subset
```

A shared memory bus must not imply universal access.

---

## 75. Privacy and Concurrency

Concurrent requests must not bypass privacy controls through race conditions.

Authorization and privacy checks must be enforced at the actual data-access boundary.

---

## 76. Privacy and Recovery

Recovery procedures must preserve privacy policy.

Corrupted data cannot simply be restored into active memory without reapplying:

- access controls;
- retention policy;
- deletion state;
- restrictions;
- encryption/key policy.

---

## 77. Privacy and Backups During Recovery

A backup may contain memories that were later restricted or deleted.

Restore processes must reconcile backup state against current deletion/restriction state before reintroducing data.

---

## 78. Privacy Incident Handling

Potential privacy incidents include:

- unauthorized memory access;
- unexpected recording;
- excessive retention;
- unauthorized synchronization;
- accidental identity disclosure;
- cross-user memory leakage;
- deletion failure;
- inference leakage;
- malicious memory extraction.

Incident handling should preserve evidence while minimizing further exposure.

---

## 79. Testing Requirements

Privacy tests must include:

- guest isolation;
- bystander minimization;
- identity minimization;
- private-zone enforcement;
- do-not-remember behavior;
- deletion propagation;
- restricted processing;
- backup reconciliation;
- cross-device deletion;
- unauthorized retrieval;
- query-based access-control bypass;
- prompt injection through memories;
- malicious memory writes;
- sensitive inference prevention;
- face/voice handling;
- child-related data safeguards;
- external-provider isolation;
- offline privacy enforcement;
- concurrency/race conditions;
- recovery privacy checks.

---

## 80. Architectural Invariants

1. Privacy is enforced throughout the memory lifecycle.
2. Observation does not imply durable retention.
3. Every durable personal-memory class has a defined purpose.
4. Novi does not retain personal information merely because it might be useful later.
5. Store the minimum representation necessary for the purpose.
6. Do not identify people when identity is unnecessary.
7. Unknown people are not automatically converted into persistent identities.
8. Household membership does not grant universal memory access.
9. Personal conversations do not automatically become long-term memory.
10. Biometric identification receives heightened protection and deployment-specific legal review.
11. Sensitive inference is not silently promoted to fact.
12. Location and home maps are treated as sensitive information.
13. Personal data is access-controlled by purpose and authorization.
14. The LLM receives only the minimum relevant personal context.
15. External model providers do not receive personal data by default.
16. Wi-Fi/Bluetooth/cloud are not required for core privacy enforcement.
17. Synchronization cannot bypass local privacy policy.
18. Backups remain within the privacy lifecycle.
19. Deletion propagates to relevant derived representations.
20. Restriction is distinct from deletion.
21. Privacy policy changes are versioned and can trigger reevaluation.
22. Privacy checks cannot be bypassed through query wording.
23. Explanations and errors must not leak protected information.
24. Telemetry must minimize personal content.
25. Learning cannot bypass privacy policy.
26. Model adaptation from personal data requires separate governance.
27. Recovery cannot resurrect deleted/restricted information without policy authorization.
28. Privacy controls must not disable safety-critical sensing without an explicit, separately governed rule.
29. Privacy incidents are detectable and auditable.
30. No subsystem has universal access to memory by default.

---

## 81. Final Principle

> **Novi should be capable of remembering deeply without becoming a surveillance system.**

Its intelligence must come from useful, justified memory—not from indiscriminate collection.

The architecture therefore favors transient processing, purpose limitation, data minimisation, identity minimisation, local processing, granular authorization, explicit retention, meaningful deletion, disassociated processing, and transparent user control.

For UK deployments, these architectural rules should be mapped to the current legal and regulatory requirements before production. The ICO's current guidance emphasizes purpose limitation, minimisation, storage limitation, security, accountability and privacy by design/default; biometric recognition may trigger additional special-category requirements. citeturn0search0turn0search2turn2search0turn0search5

NIST's privacy engineering objectives provide a useful complementary design framework: **predictability, manageability and disassociability**, alongside confidentiality, integrity and availability. citeturn1search21
