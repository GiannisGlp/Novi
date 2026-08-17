# 38 — Memory, Social Context and Human Interaction

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi perceives, represents, remembers and reasons about human interaction while keeping observation, identity, preference, relationship, trust and interpretation explicitly separate.

Novi is expected to interact naturally with people, use multiple microphones and cameras, determine where voices originate, recognize familiar people where authorized, remember interaction history, and adapt its behavior over time. This document establishes the memory boundaries required to do that safely and accurately.

## Core Principle

> **Novi may learn from repeated human interaction, but it must never turn an uncertain perception or social inference into an unverified fact about a person.**

---

## 1. Social Memory Layers

Social information should be separated into:

```text
SIGNAL
  what sensors detected

OBSERVATION
  interpreted evidence

IDENTITY HYPOTHESIS
  who Novi thinks may be present

CONFIRMED IDENTITY
  identity established by an authorized mechanism

INTERACTION
  what occurred between Novi and a person

PREFERENCE
  an explicitly confirmed or sufficiently supported preference

RELATIONSHIP MODEL
  learned interaction pattern

SOCIAL KNOWLEDGE
  evidence-backed generalization
```

These layers must not be collapsed.

---

## 2. Human Detection vs Identity

Detecting a human is not identifying a human.

```text
camera → person detected
microphone → voice detected
speaker localization → direction estimated

≠

"This is Alice."
```

Identity requires additional evidence and authorization.

---

## 3. Speaker Localization

Novi's microphone array should support estimating the direction of an acoustic source where hardware and environment permit.

Possible inputs include:

- microphone array signals;
- beamforming;
- direction-of-arrival estimation;
- acoustic event detection;
- camera confirmation;
- robot pose.

Speaker direction is an observation, not identity.

---

## 4. Multimodal Human Association

Where permitted, Novi may associate signals from multiple sensors:

```text
voice direction
      +
face/body observation
      +
robot pose
      +
time
      ↓
probabilistic person association
```

The association must retain uncertainty and provenance.

---

## 5. Identity Confidence

Person identity should have explicit confidence/verification status.

Example:

```text
person_42
identity hypothesis: Alice
confidence: 0.82
status: unconfirmed
```

Only authorized identity mechanisms may promote it to confirmed identity.

---

## 6. No Silent Biometric Enrollment

Novi must not silently create a permanent biometric identity profile from an incidental encounter.

Enrollment requires an explicit, authorized process and must follow privacy policy.

---

## 7. Interaction Episode

A social interaction should be represented as an episode with:

- participants;
- time interval;
- location;
- initiating event;
- conversational/action context;
- observations;
- actions taken by Novi;
- outcomes;
- relevant goals;
- confidence;
- privacy classification.

An interaction episode can reference many lower-level events.

---

## 8. Conversation Memory

Conversation memory should distinguish:

```text
raw audio
transcription
speaker attribution
semantic interpretation
explicit user statement
inferred intent
memory candidate
```

A transcription error must not automatically become a durable factual memory.

---

## 9. Explicit vs Inferred Information

This distinction is mandatory.

Example:

```text
EXPLICIT:
"I prefer tea."

INFERRED:
"This person seems to prefer tea."
```

Explicit statements can be stronger evidence, but still require identity/authorization context.

---

## 10. Preference Memory

Preferences should record:

- subject;
- preference;
- source;
- confidence;
- time validity;
- scope;
- confirmation status;
- last supporting interaction.

Preferences may change.

---

## 11. Preference Scope

A preference may be:

```text
personal
contextual
temporary
household
location-specific
activity-specific
```

Example:

> "I don't want music now"

must not automatically become:

> "I never like music."

---

## 12. Preference Contradictions

Contradictory preference evidence should remain visible.

```text
Monday:
"I don't like coffee."

Friday:
"I'd like a coffee."
```

Possible explanation:

```text
context-dependent preference
```

Novi should not force a permanent binary preference when evidence suggests context dependence.

---

## 13. Relationship Model

Novi may maintain a structured relationship model containing evidence-backed interaction patterns.

Examples:

- frequently interacts with Novi;
- often gives explicit instructions;
- frequently requests music;
- household member relationship if explicitly established;
- professional/visitor relationship if authorized.

The relationship model is not a substitute for legal or identity authority.

---

## 14. Relationship Is Not Identity

A relationship label such as:

```text
"household member"
```

must have an explicit source.

Repeated proximity alone should not grant permissions.

---

## 15. Trust Model

Trust should be represented separately from identity and relationship.

```text
identity confidence
relationship
trust/reliability evidence
authorization
```

These dimensions may differ.

A known person is not automatically authorized to perform every action.

---

## 16. Authorization

Social familiarity must never bypass authorization.

For example:

```text
recognized person
      ≠
owner
      ≠
authorized administrator
```

Security-sensitive actions must use explicit authorization mechanisms.

---

## 17. Interaction History

Novi may retain summaries of meaningful interactions.

Examples:

- important requests;
- commitments made by Novi;
- confirmed preferences;
- recurring tasks;
- significant experiences;
- corrections provided by a user.

Routine interactions should be compressed or allowed to expire according to retention policy.

---

## 18. Social Context

Context may include:

- who is present;
- current interaction;
- recent conversation;
- location;
- time;
- active task;
- household context;
- relevant user preferences;
- social norms encoded by policy.

Context should be bounded and task-specific.

---

## 19. Presence Model

Novi should distinguish:

```text
person detected
person nearby
person interacting
person addressing Novi
person identified
person authorized
```

These are separate states.

---

## 20. Address Detection

Novi should determine whether speech is likely directed at it using multiple cues where available:

- wake phrase;
- speech direction;
- visual orientation;
- conversational context;
- proximity;
- recent interaction;
- explicit user action.

This remains probabilistic unless explicit interaction is established.

---

## 21. Multi-Speaker Conversations

Novi should support multiple simultaneous or sequential speakers.

The architecture should preserve:

- speaker segments;
- timestamps;
- estimated source direction;
- identity hypothesis;
- confidence;
- transcript linkage.

Speaker attribution errors must remain recoverable.

---

## 22. Social Event Model

Useful event types include:

```text
social.person_detected
social.person_identified
social.speaker_localized
social.interaction_started
social.interaction_ended
social.statement_received
social.preference_confirmed
social.preference_corrected
social.permission_changed
social.relationship_confirmed
social.relationship_corrected
```

Schemas must remain versioned and auditable.

---

## 23. Memory Admission

Not every social event becomes memory.

Admission should consider:

- user value;
- future usefulness;
- explicit request to remember;
- recurrence;
- importance;
- confidence;
- privacy sensitivity;
- retention policy.

High-sensitivity information should require stronger admission rules.

---

## 24. "Remember This" Requests

When a user explicitly asks Novi to remember something, the request should create a high-priority memory candidate.

The system must still validate:

- speaker identity/authority where relevant;
- content interpretation;
- privacy class;
- retention rules.

Explicit requests should not be silently discarded because they are socially inferred.

---

## 25. Social Memory Provenance

Every durable social memory should identify its origin.

Example:

```text
memory:
"User prefers quiet mode after 22:00."

source:
explicit statement

source event:
...

identity authority:
...

confidence:
high

scope:
home

validity:
ongoing until corrected
```

---

## 26. Corrections

Users should be able to correct Novi's social memories.

Example:

```text
Novi:
"You prefer X."

User:
"No, I don't."

 ↓

preference.corrected
 ↓

old preference superseded
```

The correction should not require deleting unrelated interaction history.

---

## 27. Social Forgetting

Social memories are subject to the general privacy, retention and deletion architecture.

Deletion must propagate through:

- memory records;
- embeddings;
- knowledge graph relationships;
- summaries;
- cached context;
- derived social models;
- synchronized copies where applicable.

---

## 28. Sensitive Information

Social memory can expose highly sensitive information even without raw audio/video.

Examples include:

- exact routines;
- household occupancy;
- relationships;
- location history;
- behavioral patterns;
- private preferences;
- health-related statements;
- financial information.

Sensitivity must be classified before retention and synchronization.

---

## 29. Privacy by Default

Novi should prefer the minimum social information needed for the current function.

```text
interaction needed
   ↓
retain necessary context
   ↓
avoid unnecessary biometric/social history
```

Local processing should be preferred where practical.

---

## 30. Offline Social Operation

Core interaction must work without Wi-Fi or Bluetooth.

Novi should still be able to:

- detect speech;
- localize speakers;
- process local conversations;
- retrieve local social memory;
- respond locally;
- update local memory.

Network services may extend capabilities but must not be required for basic interaction.

---

## 31. Social Context and Current State

Current presence should outrank stale historical assumptions.

Example:

```text
Memory:
"Alice usually sits in the living room."

Current perception:
Alice is in the kitchen.

Current context:
kitchen
```

Historical patterns remain useful but do not override current observations.

---

## 32. Social Prediction

Novi may predict interaction outcomes based on repeated evidence.

Example:

```text
person approaches
 ↓
previous pattern suggests greeting
 ↓
Novi predicts greeting
 ↓
actual interaction differs
 ↓
prediction error
```

Predictions must not be treated as facts about the person's intentions.

---

## 33. Intent Inference

Human intent is inherently uncertain.

Novi should represent:

```text
observed words
possible intent A
possible intent B
confidence
request for clarification if needed
```

The language model must not convert ambiguous intent into certainty when the action is consequential.

---

## 34. Clarification

When social ambiguity materially affects action, Novi should ask.

Example:

> "Do you want me to remember that?"

or:

> "Are you asking me to turn the lights off?"

Clarification is preferable to confident misinterpretation when stakes justify it.

---

## 35. Social Memory and Personality

Personality may affect:

- greeting style;
- conversational tone;
- verbosity;
- humor;
- preferred interaction rhythm.

It must not override:

- privacy;
- authorization;
- safety;
- factual provenance;
- user corrections.

---

## 36. Emotional Context

Novi may model observable interaction context such as:

- apparent conversational urgency;
- tone characteristics;
- interaction difficulty;
- user-requested emotional preferences.

It must not represent inferred internal human emotions as facts without appropriate evidence.

Prefer:

```text
"speech appears urgent"
```

over:

```text
"the person is angry"
```

unless the latter is explicitly established and appropriately scoped.

---

## 37. Social Learning

Repeated interactions may produce learning candidates:

```text
repeated observations
      ↓
pattern
      ↓
learning candidate
      ↓
validation
      ↓
updated social model
```

A single unusual interaction should not automatically create a stable personality model of a person.

---

## 38. No Stereotyping Rule

Novi must not infer stable traits from weak evidence.

Examples of prohibited reasoning patterns:

```text
one action → permanent personality trait
one facial expression → character judgment
one conversation → broad social classification
```

Social models must remain evidence-bounded.

---

## 39. Human Identification Failure

If identity confidence falls:

```text
confirmed identity
      ↓
identity uncertain
      ↓
use generic interaction
```

Novi should not continue using private memories simply because the person resembles a known individual.

---

## 40. Identity Collision

If two people are incorrectly associated with one identity, the system must support correction and lineage repair.

Historical observations should remain traceable so erroneous associations can be separated where possible.

---

## 41. Unknown People

Unknown people should be represented as temporary entities where useful:

```text
person_observation_abc
```

rather than forcing a known identity.

Temporary identity should expire according to policy if there is no legitimate reason to retain it.

---

## 42. Household Model

If Novi operates primarily in a home, household context may include explicitly authorized information such as:

- household members;
- room associations;
- shared devices;
- approved routines;
- permissions.

Household membership must be explicitly configured or verified, not inferred solely from presence.

---

## 43. Visitors

Visitors should not automatically receive household-level permissions or persistent memory.

Novi should distinguish:

```text
visitor detected
visitor recognized
visitor authorized for action
```

---

## 44. Children and Vulnerable Persons

The social architecture must support stricter privacy and safety policies for children and other vulnerable persons.

The system should avoid unnecessary persistent profiling and should follow the governing privacy/safety policy for the deployment jurisdiction.

---

## 45. Social Permissions

Permissions should be represented independently of social memory.

```text
social memory:
"person frequently interacts with Novi"

permission:
"may control lights"
```

One must not imply the other.

---

## 46. Social Context in Cognitive Workspace

The workspace may include only socially relevant information:

```text
current speaker
interaction history relevant to task
confirmed preferences
authorized relationship facts
current social context
uncertainty
```

Unrelated personal history should not be injected into cognition.

---

## 47. Social Context and Retrieval

Retrieval should prioritize:

1. current interaction;
2. explicit user request;
3. relevant preferences;
4. recent related episodes;
5. established relationship context;
6. older relevant history.

Privacy and authorization filter the result before cognition receives it.

---

## 48. Social Context and Action

Before socially consequential actions, Novi should verify:

- who is being addressed;
- authorization;
- current context;
- privacy implications;
- action reversibility;
- relevant user preference.

The final decision remains subject to the general action-validation architecture.

---

## 49. Social Event Replay

Social events should support controlled replay for:

- speaker-attribution testing;
- memory admission testing;
- retrieval evaluation;
- identity-association testing;
- conversation regression testing.

Replay must protect private data and must not reproduce physical actions by default.

---

## 50. Social Model Drift

The system should detect stale social beliefs.

Example:

```text
historical preference:
quiet mode after 22:00

recent explicit correction:
"That schedule changed."

 ↓
old preference superseded
```

Social models must remain revisable.

---

## 51. Social Memory and Synchronization

Only authorized social data should synchronize between devices or backups.

Potentially synchronizable:

- confirmed preferences;
- selected autobiographical experiences;
- authorized household configuration.

Potentially local-only:

- raw audio;
- raw video;
- temporary speaker tracks;
- transient biometric features.

Exact policy is deployment-specific.

---

## 52. Local-First Requirement

Because Novi must remain fully functional offline, the canonical social-memory path should operate locally.

Cloud services, if ever introduced, are optional and must not become the sole source of social identity or memory.

---

## 53. Hardware Integration

The social architecture should integrate with Novi's planned hardware:

```text
multiple microphones
      ↓
speaker direction

multiple cameras
      ↓
face/body/scene perception

speaker array
      ↓
spatial audio output

displays
      ↓
visual interaction

RGB lighting
      ↓
non-verbal interaction cues
```

These signals should enter the semantic event system through documented interfaces.

---

## 54. NVIDIA Integration Boundary

NVIDIA Isaac ROS is a candidate acceleration layer for perception pipelines, not the owner of Novi's social memory semantics. Isaac ROS is built on ROS 2 and provides accelerated perception packages and GPU-aware pipelines; it can therefore support person/object perception while Novi's identity, privacy, memory and authorization layers remain vendor-neutral. citeturn0search0turn0search8

NVIDIA's published robotics material also demonstrates Jetson-based human pose estimation and social/spatial interaction pipelines, while ReMEmbR demonstrates combining spatial memory, speech and LLM reasoning on a robot. These are useful implementation references, not requirements that Novi adopt NVIDIA-only components. citeturn0search4turn0search6

---

## 55. Vendor-Neutral Rule

The social memory layer must expose vendor-neutral semantic interfaces.

```text
camera model
voice model
face model
ASR model
ROS package
NVIDIA accelerator
OpenCV pipeline
other open-source model
        ↓
standard Novi observation/event interface
        ↓
social memory
```

This preserves the project's rule of using existing open-source local solutions whenever they are suitable.

---

## 56. Failure Modes

The system must handle:

- false person detection;
- false identity;
- speaker attribution errors;
- multiple speakers;
- poor acoustics;
- occlusion;
- lighting changes;
- ASR errors;
- ambiguous commands;
- stale preferences;
- incorrect relationship inference;
- privacy-policy rejection;
- unauthorized requests;
- corrupted social memory;
- synchronization conflict;
- identity collision;
- biometric subsystem failure.

---

## 57. Testing Requirements

Test:

- person detection;
- speaker localization;
- multi-speaker attribution;
- identity confidence;
- explicit identity confirmation;
- unknown-person handling;
- preference admission;
- preference correction;
- relationship boundaries;
- authorization separation;
- conversation retrieval;
- context filtering;
- privacy filtering;
- deletion propagation;
- offline interaction;
- social-model drift;
- identity collision recovery;
- replay;
- synchronization;
- children/vulnerable-person safeguards;
- prompt injection attempting to reveal private social memory.

---

## 58. Architectural Invariants

1. Human detection is not human identification.
2. Speaker direction is not speaker identity.
3. Identity is not authorization.
4. Relationship is not authorization.
5. Trust is not identity.
6. Explicit information is distinct from inference.
7. Social predictions are not facts.
8. A single weak observation cannot establish a stable human trait.
9. Novi must not silently enroll biometric identities.
10. Social memory is subject to privacy and deletion policies.
11. Core social interaction works offline.
12. Current perception outranks stale historical assumptions for current context.
13. User corrections supersede incorrect social memories.
14. The LLM cannot become the authoritative owner of human identity or permissions.
15. Sensitive social information is minimized before entering the cognitive workspace.
16. Vendor-specific perception systems must terminate at vendor-neutral semantic interfaces.
17. Unknown people can remain unknown.
18. Novi must prefer uncertainty or clarification over confident social hallucination.

---

## 59. Final Principle

> **Novi should remember people because meaningful relationships and interactions are part of its embodied life, but it must always distinguish what it sensed, what it inferred, what a person explicitly told it, what was verified, and what it merely believes.**

That distinction is essential for a social robot that is intended to become more capable and personalized over time without becoming an uncontrolled profiler of the people around it.
