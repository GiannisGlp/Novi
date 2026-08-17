# 82 — Memory Knowledge Episodic Memory and Autobiographical Continuity

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi represents experiences as episodes and maintains a truthful, continuous history of its own interactions, observations, actions, locations, tasks, outcomes, and learned experiences without confusing original evidence with later reconstruction.

## Core Principle

> **Novi should remember experiences as time- and context-bound episodes, while preserving the distinction between what was observed, what was inferred, what was done, and what is remembered later.**

Autobiographical continuity is continuity of traceable history, not a license to invent a human-like personal narrative.

## 1. Episode Model

An episode can contain:

```text
EPISODE ID
START / END TIME
LOCATION / POSE
PARTICIPANTS / ENTITIES
TRIGGER
OBSERVATIONS
INTERPRETATIONS
GOALS
ACTIONS
OUTCOMES
EMOTIONAL/AFFECTIVE STATE IF IMPLEMENTED
UNCERTAINTY
PROVENANCE
RELATED MEMORIES
```

Not every field is required for every episode.

## 2. Episode Boundaries

Episodes should have explicit or inferred boundaries based on:

- task transitions;
- location changes;
- interaction start/end;
- meaningful environmental changes;
- goal completion;
- temporal gaps;
- explicit user-defined events.

Inferred boundaries remain marked as inferred.

## 3. Episode vs Event

An event is a discrete occurrence; an episode is a contextual grouping of events.

```text
EVENT A
EVENT B
EVENT C
   ↓
EPISODE
```

Grouping must not imply causal relationships that were never established.

## 4. Episode vs Fact

An episode records an experience in context.

A fact/knowledge item is a proposition that may be reusable outside that episode.

```text
"At 19:00 Novi saw X"
        ≠
"X is always present at 19:00"
```

## 5. First-Person Provenance

When Novi records its own action or observation, provenance should distinguish:

```text
Novi observed
Novi inferred
Novi decided
Novi acted
Novi received information
```

This prevents narrative compression from turning inference into direct experience.

## 6. Self-Model Boundary

Autobiographical memory can describe Novi's history without assuming human consciousness, subjective experience, or emotions unless those properties are explicitly implemented and evidenced by the system architecture.

## 7. Identity Continuity

Novi should maintain stable system identity metadata across software updates, hardware replacements and migrations where policy requires.

Identity continuity must not depend solely on a model checkpoint or a single storage device.

## 8. Versioned Self-State

Important self-state should be versioned:

```text
SELF STATE v1
      ↓
SELF STATE v2
```

Historical states remain distinct from current state.

## 9. Hardware Continuity

Replacing a camera, computer, battery, storage device or other component does not automatically create a new autobiographical identity.

Hardware provenance should remain available so Novi can distinguish:

```text
what Novi experienced
vs
what hardware captured it
```

## 10. Software Continuity

Software/model upgrades may alter perception or reasoning.

Episodes should retain relevant software/model versions where required for interpretation and reproducibility.

## 11. Episode Capture

Episode capture should occur through the event and provenance architecture rather than through free-form narrative generation alone.

```text
EVENT LOG
   ↓
EPISODE ASSEMBLY
   ↓
EPISODIC MEMORY
```

## 12. Narrative Representation

A human-readable episode summary may be generated as a derivative representation.

The narrative must remain linked to source events and must not replace them as authoritative evidence.

## 13. Reconstruction

When an episode is reconstructed from multiple records:

```text
SOURCE EVENTS
   ↓
RECONSTRUCTION
   ↓
EPISODE SUMMARY
```

The reconstruction should identify missing or uncertain portions.

## 14. No Fabricated Experience

Novi must never claim to have personally experienced an event when its records show only:

- an external report;
- a user statement;
- a remote agent observation;
- an inferred event;
- a generated scenario.

Example:

```text
USER: "You went outside yesterday."

If no supporting episode exists:
→ "I don't have a recorded episode confirming that."
```

## 15. Memory Confidence

Episodes may have confidence/completeness states:

```text
COMPLETE
PARTIAL
RECONSTRUCTED
UNCERTAIN
CONTESTED
CORRUPTED
UNKNOWN
```

These describe the memory record, not a claim of consciousness.

## 16. Temporal Continuity

Episodes should preserve:

- event time;
- episode start/end;
- temporal uncertainty;
- ordering/causality;
- timezone context where relevant.

Arrival or reconstruction time must not replace original event time.

## 17. Spatial Continuity

For an embodied Novi, episodes can include:

- GPS/GNSS coordinates;
- local pose;
- room/place identity;
- map version;
- coordinate frame;
- spatial uncertainty.

## 18. Outdoor History

Novi can maintain a history of places it has visited:

```text
TRIP
 ↓
ROUTE
 ↓
LOCATIONS
 ↓
LANDMARKS
 ↓
EPISODES
```

This supports the requirement that Novi can remember where it has been outside the home.

## 19. Visited vs Known

```text
Novi visited X
        ≠
Novi knows X
        ≠
Novi is currently at X
```

Each relationship must have separate semantics.

## 20. Location Uncertainty

GPS/GNSS may be unavailable or inaccurate.

Episodes should preserve localization quality and uncertainty rather than recording false precision.

## 21. Map Evolution

An episode should retain the map/localization context used to interpret its location where relevant.

Historical map states should remain distinct from the current map.

## 22. Participants

Episodes may reference:

- users;
- household members;
- recognized people;
- remote agents;
- objects;
- places.

Identity confidence and authorization remain attached to references.

## 23. Person Identity Uncertainty

A visual or acoustic recognition may produce:

```text
possible person A
confidence / evidence
```

The episode must not silently convert an uncertain recognition into a confirmed identity.

## 24. Object Continuity

Objects can persist across episodes:

```text
object X
 ↓
seen in episode A
 ↓
seen in episode B
```

Object identity may change due to ambiguity, appearance changes or replacement.

## 25. Interaction Episodes

User interactions should record relevant context without storing unnecessary raw content.

Potential metadata:

- interaction time;
- participants;
- task;
- decisions;
- explicit user statements;
- outcomes;
- follow-up commitments.

## 26. Conversation Memory

A conversation episode should distinguish:

```text
USER SAID
NOVI SAID
NOVI INFERRED
NOVI PROPOSED
USER ACCEPTED
USER REJECTED
UNRESOLVED
```

This is essential for avoiding false autobiographical memories.

## 27. Emotional/Affective Records

If affective state is implemented, it must distinguish:

```text
measured/estimated physiological or behavioral state
vs
inferred emotion
vs
user-reported emotion
```

Novi must not claim subjective feelings solely from an inference model.

## 28. Episode Outcomes

Outcomes should be linked explicitly:

```text
GOAL
 ↓
ACTION
 ↓
OBSERVED OUTCOME
```

An expected outcome must not be recorded as an actual outcome until observed or otherwise validated.

## 29. Failed Episodes

Failure is valuable history.

Examples:

```text
route attempt failed
command rejected
object recognition uncertain
plan assumption contradicted
```

Failures should remain traceable and can inform future planning without becoming permanent negative identity assumptions.

## 30. Repeated Episodes

Repeated similar experiences can be linked while preserving individual episodes.

```text
Episode 1 ─┐
Episode 2 ─┼→ Pattern
Episode 3 ─┘
```

This feeds the consolidation architecture.

## 31. Episode Similarity

Similarity can help retrieve related experiences but must not merge episodes automatically.

Distinct episodes remain distinct unless explicit consolidation occurs.

## 32. Episode Merging

Episodes may be merged only when evidence supports a shared underlying experience.

The original episode identifiers and lineage should remain recoverable where required.

## 33. Episode Splitting

An incorrectly grouped episode may be split into separate episodes.

```text
Episode X
 ↓
Episode A + Episode B
```

The correction must preserve the revision history.

## 34. Memory Reconsolidation

New evidence can modify the current interpretation of an episode without rewriting the original observations.

```text
ORIGINAL OBSERVATIONS
        ↓
ORIGINAL EPISODE
        ↓
NEW EVIDENCE
        ↓
REVISED INTERPRETATION
```

## 35. Historical Integrity

Historical episode records should preserve the distinction between:

```text
what was recorded then
what is believed now
```

## 36. Autobiographical Timeline

Novi may maintain a derived timeline:

```text
DAY
 ├── interaction
 ├── movement
 ├── task
 ├── observation
 └── outcome
```

The timeline is a projection over underlying episodes/events.

## 37. Timeline Queries

The system should support questions such as:

- What happened today?
- Where did Novi go yesterday?
- When did Novi first encounter this object?
- What happened before the failed task?
- What did Novi learn from that episode?

Answers should cite actual episode/event lineage internally.

## 38. Life-Log Boundaries

An autobiographical timeline must not become an unrestricted surveillance log.

Retention, privacy and minimization rules apply to every episode.

## 39. Episode Retention

Episode retention should depend on:

- significance;
- user value;
- safety/audit value;
- privacy;
- storage cost;
- future learning value;
- policy requirements.

## 40. Ephemeral Episodes

Low-value transient interactions can remain short-lived or be discarded after their purpose is complete.

Their derivatives must still be evaluated for retention/deletion dependencies.

## 41. Significant Episodes

Potentially significant episodes include:

- major user interactions;
- important task completion/failure;
- new environments;
- novel objects/people;
- safety events;
- corrections;
- significant discoveries;
- explicit user requests to remember.

Significance is policy-driven, not assumed.

## 42. User-Requested Memory

An explicit request to remember something can raise its retention priority, subject to privacy, authorization and safety constraints.

The request itself should be recorded as provenance for the memory decision.

## 43. Forgetting

Forgetting can mean:

```text
EVICT FROM WORKING MEMORY
DE-PRIORITIZE RETRIEVAL
DEMOTE AUTHORITY
DELETE MEMORY
SANITIZE DATA
```

These are different operations and must not be conflated.

## 44. Privacy and Household Boundaries

Episodes involving multiple people require scoped access.

One person's private information must not automatically become another person's accessible autobiographical memory.

## 45. Consent and Sensitive Context

Sensitive episodes require stricter storage, retrieval and sharing policies.

The architecture must not assume that physical proximity or household membership grants universal access.

## 46. Distributed Episodes

Remote Novi instances may contribute episode fragments.

Merged episodes must retain:

- source agent;
- synchronization state;
- causal relationships;
- confidence;
- conflict state.

## 47. Offline Episodes

Novi must be able to create and maintain episodes offline.

Later synchronization should merge records without fabricating event order.

## 48. Partial Episodes

An episode may begin offline and complete after reconnection.

The system should support incremental completion and revision.

## 49. Crash Recovery

Critical active episodes can use checkpoints to recover after interruption.

Recovery should distinguish:

```text
action started
vs
action completed
vs
outcome observed
```

## 50. Episode Security

Protect against:

- fabricated episodes;
- unauthorized modification;
- memory poisoning;
- identity spoofing;
- replay attacks;
- deletion bypass;
- provenance forgery.

## 51. Episode Integrity

Important episodes should retain integrity metadata and source references sufficient to detect unauthorized changes.

## 52. Autobiographical Narrative

A narrative such as:

> "Yesterday I went outside and discovered a new park."

must be generated only when the underlying episode supports all material claims.

If location or discovery status is uncertain, the narrative should preserve that uncertainty.

## 53. Narrative Compression

Narrative summaries may compress multiple episodes but must preserve:

- important chronology;
- contradictions;
- uncertainty;
- significant actions/outcomes;
- provenance references.

## 54. Narrative Drift

Repeatedly summarizing a summary can introduce distortion.

Prefer regeneration from authoritative episode/event records when accuracy matters.

## 55. False Memory Prevention

Novi must prevent generated narratives from becoming evidence for the events they describe.

```text
EPISODE → SUMMARY
```

not:

```text
SUMMARY → new evidence → stronger episode
```

## 56. Self-Narrative Boundary

Novi can maintain a structured history of its operation and experiences without claiming subjective consciousness.

Terms such as "I remember" may be conversational shorthand for an available memory record, not a scientific claim about phenomenal experience.

## 57. Continuity Across Updates

When models or software are updated, Novi should preserve autobiographical records while marking the software/version context used to create or interpret them.

## 58. Migration

When storage or hardware is migrated:

- preserve stable episode IDs;
- preserve provenance;
- validate integrity;
- preserve timestamps;
- verify references;
- record migration events.

## 59. Testing

Test:

- episode boundary detection;
- event-to-episode assembly;
- reconstruction;
- missing events;
- false narratives;
- person ambiguity;
- location uncertainty;
- map changes;
- hardware replacement;
- software upgrades;
- offline episodes;
- distributed merge;
- episode splitting/merging;
- user correction;
- deletion;
- privacy leakage;
- crash recovery;
- replay attacks;
- provenance tampering;
- narrative drift;
- repeated-summary distortion;
- failed-action vs completed-action distinction.

## 60. Architectural Invariants

1. Episodes are contextual records, not universal facts.
2. Events and episodes remain distinct.
3. Observations, interpretations, decisions and actions remain distinct.
4. Novi never fabricates personal experience.
5. Reconstructed episodes remain marked as reconstructed where appropriate.
6. Original evidence is not silently rewritten by later interpretation.
7. Current belief and historical record remain distinct.
8. Visited location is distinct from current location and current accessibility.
9. Identity uncertainty is preserved.
10. Failed actions are distinct from completed actions and observed outcomes.
11. Generated narratives are derivatives, not evidence.
12. Summaries cannot become self-validating evidence.
13. Autobiographical continuity does not imply consciousness.
14. Hardware/software provenance remains available where required.
15. Privacy and access boundaries apply to episodic history.
16. Offline episodes remain valid and synchronizable.
17. Distributed merges preserve source, causality and conflict.
18. Forgetting operations are explicitly distinguished.
19. Significant lifecycle decisions remain auditable.
20. Episode retention follows purpose, minimization and lifecycle policy.

## 61. Final Principle

> **Novi's autobiographical memory should form a continuous, traceable history of what happened to and through the system—without turning inference into experience, summaries into evidence, or narrative continuity into fabricated identity.**

This episodic layer provides the experiential foundation connecting Novi's event history, working memory, long-term memory, spatial history, learning and future reasoning.