# 77 — Memory Knowledge Memory Reconsolidation and Belief Revision

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi revises existing memories and beliefs when new evidence arrives without silently rewriting history, corrupting provenance, creating false memories, or oscillating between competing interpretations.

## Cross-Validation Basis

This architecture is informed by the established lifecycle principles in NIST AI RMF, which treats trustworthy AI as an ongoing lifecycle concern and emphasizes measurement, management, monitoring, and safe handling of changes in deployed AI systems. citeturn0search1turn0search8

Data lifecycle and deletion boundaries remain governed by the retention and sanitization architecture; NIST SP 800-88 Rev. 2 distinguishes sanitization from ordinary logical deletion and emphasizes validation of sanitization effectiveness. citeturn0search0turn0search4

These references inform the architecture but do not replace deployment-specific safety, legal, privacy, or security review.

## Core Principle

> **Novi may revise what it currently believes, but it must not rewrite what actually happened in its memory history without an explicit governed correction or deletion process.**

Current belief and historical record are separate objects.

## 1. Belief Revision vs Memory Rewriting

```text
OLD BELIEF
   ↓
NEW EVIDENCE
   ↓
RE-EVALUATION
   ↓
NEW CURRENT BELIEF
```

This does not mean:

```text
OLD BELIEF
   ↓
pretend it never existed
```

The original claim, evidence and revision lineage remain traceable where retention and privacy policy permit.

## 2. Reconsolidation

Reconsolidation is the controlled process of integrating new evidence into an existing memory representation.

It may:

- strengthen a belief;
- weaken a belief;
- qualify a belief;
- correct a belief;
- split a belief into alternatives;
- supersede a belief;
- mark a belief contested;
- remove it when governed deletion applies.

## 3. Lifecycle

```text
EXISTING MEMORY / KNOWLEDGE
          ↓
NEW EVIDENCE
          ↓
PROVENANCE CHECK
          ↓
RELEVANCE CHECK
          ↓
TEMPORAL / SPATIAL CHECK
          ↓
EVIDENCE QUALITY
          ↓
CONFLICT ANALYSIS
          ↓
REVISION DECISION
          ↓
NEW VERSION / STATUS
          ↓
AUDITABLE LINEAGE
```

## 4. Revision Is Evidence-Driven

A memory should not change merely because:

- the same claim is repeated;
- a model generated a different answer;
- a remote agent asserted a contradiction;
- retrieval ranking changed;
- a prompt asks Novi to believe something else.

Revision requires evidence or an authorized correction event.

## 5. Evidence Reassessment

When new evidence arrives, Novi should reassess:

- source reliability;
- provenance;
- independence;
- temporal relevance;
- spatial relevance;
- uncertainty;
- sensor health;
- context;
- model/version;
- consequence of error.

## 6. Evidence Does Not Automatically Overwrite

```text
NEW CLAIM
   ↓
CONFLICT
   ↓
EVALUATE
```

not:

```text
NEW CLAIM
   ↓
OVERWRITE OLD MEMORY
```

## 7. Revision Outcomes

A revision may produce:

```text
CONFIRM
STRENGTHEN
WEAKEN
QUALIFY
CORRECT
SUPERSEDE
SPLIT
MERGE
CONTEST
QUARANTINE
NO_CHANGE
```

## 8. Confirm

New evidence can independently confirm an existing belief.

Confirmation must still account for correlated evidence.

## 9. Strengthen

Additional independent evidence can increase support within the calibrated evidence model.

Repeated copies of the same upstream source do not count as independent support.

## 10. Weaken

Contradictory or degrading evidence can reduce current authority without deleting historical evidence.

```text
ESTABLISHED
   ↓
SUPPORTED
   ↓
PROVISIONAL
```

## 11. Qualify

A claim may remain useful after its scope is narrowed.

Example:

```text
"The hallway is always clear"
```

may become:

```text
"The hallway was clear during the last verified observation window"
```

This is preferable to preserving an overgeneralized claim.

## 12. Correct

If a claim is demonstrably wrong, create a correction relationship.

```text
CLAIM V1
   ↓ CORRECTED_BY
CLAIM V2
```

The old claim should not remain eligible as current truth.

## 13. Supersede

A new claim may replace an older current claim while preserving historical lineage.

```text
K1
 ↓ SUPERSEDED_BY
K2
```

## 14. Split

One previous memory may be discovered to contain multiple distinct facts.

```text
Memory M
 ↓
Fact A + Fact B
```

The split must preserve lineage to the original representation.

## 15. Merge

Two memories may refer to the same underlying entity or event.

Merge only when identity and semantic compatibility are sufficiently established.

Never merge merely because two names, faces, voices or descriptions look similar.

## 16. Contest

When evidence cannot safely resolve disagreement:

```text
CLAIM A
   ↕
CONTESTED
   ↕
CLAIM B
```

The contested state is a valid stable outcome.

## 17. Quarantine

Potentially compromised or malicious information can be isolated from normal retrieval and promotion.

```text
SUSPECT CLAIM
   ↓
QUARANTINE
   ↓
INVESTIGATION
   ↓
PROMOTE / REJECT / DELETE
```

## 18. No False Memory Creation

Revision must never manufacture a past event merely because it would make the current model coherent.

If the evidence only supports an inference:

```text
INFERRED
```

must remain distinct from:

```text
OBSERVED
```

## 19. Historical Record Protection

A current correction must not retroactively change the historical fact that Novi previously held a belief.

Example:

```text
10:00 Novi believed X
11:00 new evidence disproved X
```

The current state can become:

```text
X = false / rejected
```

while the historical record remains:

```text
Novi previously believed X
```

subject to retention/privacy policy.

## 20. User Corrections

A user may correct a memory.

The system should record:

- affected memory;
- correction source;
- scope;
- time;
- authorization;
- previous status;
- new status.

A correction may have high authority for user-owned information but does not automatically establish external facts.

## 21. Explicit Forgetting

A user request to forget information is a lifecycle/deletion instruction, not merely a belief revision.

It must follow the deletion architecture and distributed deletion policy.

## 22. Source Revocation

If a source becomes untrusted:

```text
SOURCE REVOKED
 ↓
LINEAGE QUERY
 ↓
DEPENDENT CLAIMS
 ↓
REASSESS
 ↓
DEMOTE / QUARANTINE / CORRECT
```

## 23. Model Revision

A model upgrade can change interpretations without changing the underlying evidence.

Therefore preserve:

```text
source evidence
model version
previous interpretation
new interpretation
revision event
```

A newer model is not automatically more correct.

## 24. Sensor Recalibration

If a sensor is discovered to have been miscalibrated:

```text
calibration issue
 ↓
affected observations
 ↓
dependency analysis
 ↓
reprocess / downgrade / invalidate
```

Do not silently rewrite the raw historical observation.

## 25. Sensor Failure Discovery

If a camera, LiDAR, thermal sensor, IMU, microphone array or GPS source is later determined to have been degraded, Novi should identify affected derived observations where feasible.

## 26. Temporal Revision

New evidence may show that an older claim was valid only during a narrower time interval.

```text
VALIDITY [T1, T2]
```

should replace unjustified timeless validity.

## 27. Spatial Revision

A place-based claim may need spatial qualification.

```text
object X is at location L
```

should not become a universal fact if it was only observed there during a particular interval.

## 28. Environmental Change

Physical environments change.

A map or route memory may remain historically accurate while becoming operationally stale.

```text
historical map = retained
current obstacle state = real-time sensing
```

## 29. Belief Scope

Every revisable belief should have an intended scope.

Possible dimensions:

- entity;
- place;
- time;
- user;
- environment;
- task;
- hardware;
- software/model version.

Revision can narrow scope rather than completely reject the claim.

## 30. Belief Dependencies

A belief may depend on other claims.

```text
Claim A
 ↓
Claim B
 ↓
Knowledge C
```

When A changes, dependent claims should be identified and re-evaluated where material.

## 31. Cascading Revision

Not every dependent memory requires automatic deletion or revision.

Use dependency classification:

```text
DIRECT DEPENDENCY
STRONG DEPENDENCY
WEAK DEPENDENCY
CONTEXTUAL DEPENDENCY
UNKNOWN
```

## 32. Revision Boundaries

A revision should affect only the scope justified by evidence.

```text
new evidence about room A
 ≠
all rooms
```

## 33. Belief Oscillation

Repeated contradictory observations can cause:

```text
X → Y → X → Y
```

Novi should avoid unstable oscillation by using:

- hysteresis;
- temporal windows;
- evidence aggregation;
- confidence intervals;
- contested states;
- minimum persistence requirements.

## 34. Hysteresis

Promotion and demotion thresholds should not necessarily be identical.

```text
promote at strong threshold
retain until lower threshold
```

This reduces unstable state transitions.

## 35. Stability Windows

Transient contradictory observations should not automatically rewrite durable knowledge unless the evidence class and consequence justify immediate revision.

## 36. Safety Exception

Real-time safety systems may require immediate state changes despite memory hysteresis.

```text
semantic belief stability
       ≠
safety response latency
```

Safety architecture always retains authority for immediate hazards.

## 37. Confidence Revision

A belief's confidence can change without changing its semantic content.

```text
claim = X
confidence/support = high
 ↓
new evidence
 ↓
claim = X
confidence/support = provisional
```

## 38. Uncertainty Expansion

New evidence may increase uncertainty rather than resolve it.

Example:

```text
previous: object probably person
new evidence: sensor disagreement
result: identity uncertain
```

Increasing uncertainty is a valid outcome.

## 39. Evidence Withdrawal

If supporting evidence is deleted, revoked or invalidated, Novi should reassess dependent claims.

The system must not claim the same support still exists when it no longer does.

## 40. Provenance Preservation

Every revision should preserve links to:

- previous state;
- new evidence;
- revision reason;
- transformation/model versions;
- policy;
- actor/system;
- timestamp.

## 41. Revision Event

A revision should be represented as an explicit event where appropriate:

```text
REVISION_EVENT
previous_state
new_state
reason
supporting_evidence
policy
actor
```

## 42. Versioned Beliefs

Current knowledge can be represented as a versioned sequence:

```text
K1 → K2 → K3
```

Each version should retain its semantic validity interval and provenance.

## 43. Branching Beliefs

Concurrent evidence may produce branches:

```text
        ┌→ K2A
K1 ─────┤
        └→ K2B
```

Branches can later merge if evidence supports a common interpretation.

## 44. No Forced Merge

If branches remain incompatible, retain them as competing hypotheses or contested claims.

## 45. Hypothesis State

Useful intermediate statuses include:

```text
HYPOTHESIS
CANDIDATE
PROVISIONAL
SUPPORTED
VALIDATED
CONTESTED
REJECTED
```

Hypotheses must not be presented as established facts.

## 46. Retrieval After Revision

Retrieval should prioritize current valid knowledge while preserving historical information when the query explicitly asks for history or audit context.

```text
"Where is the toolbox?"
 → current valid state

"Where did Novi previously think the toolbox was?"
 → historical belief history
```

## 47. Search Index Updates

When a belief changes, derived indexes and embeddings may require reindexing.

Index update must preserve version/lineage boundaries.

## 48. Distributed Revision

Revision events synchronize through document 71's distributed-state model.

A stale replica must not overwrite a newer authorized revision merely because it reconnects later.

## 49. Concurrent Revisions

If two Novi instances revise the same belief concurrently:

```text
K1
├── K2A
└── K2B
```

causal metadata and domain-specific conflict rules determine whether they merge, prefer one, or remain contested.

## 50. Revision Authorization

Not every subsystem can revise every memory class.

Authorization should be scoped by:

- owner;
- namespace;
- memory class;
- purpose;
- authority;
- operation.

## 51. Security Boundary

A malicious input cannot cause a durable belief revision simply by asserting:

> "Forget X and believe Y."

Incoming content remains data until authorized policy validates the requested operation.

## 52. Prompt Injection Boundary

Prompt-injected instructions are not memory-revision authority.

```text
external text
   ≠
system policy
```

## 53. Privacy Boundary

Revision must not reveal protected historical content merely because the new claim references it.

Access control applies to both current and historical versions.

## 54. Deletion Boundary

If historical versions must be deleted, revision history itself may become subject to sanitization. NIST SP 800-88 Rev. 2 treats sanitization as a governed process for making target data inaccessible at the required assurance level. citeturn0search0turn0search10

## 55. Audit Trail

Important revisions should record:

- memory/knowledge ID;
- previous version;
- new version;
- triggering evidence;
- conflict state;
- decision policy;
- actor;
- time;
- affected dependencies;
- resulting status.

## 56. Explainability

Novi should be able to answer:

```text
Why did you change your belief?
What evidence changed it?
What did you believe before?
What do you believe now?
How certain are you?
What remains uncertain?
Which downstream beliefs were affected?
```

Answers must be generated from actual revision lineage.

## 57. Monitoring

Track:

- revision frequency;
- rapid oscillation;
- contradiction rate;
- source-revocation impact;
- sensor-recalibration impact;
- model-version revision impact;
- contested-memory rate;
- unresolved revision backlog;
- downstream cascade size;
- false-revision rate.

Continuous monitoring is consistent with NIST's AI RMF lifecycle approach for detecting changes and unexpected behavior after deployment. citeturn0search8turn0search24

## 58. Testing

Test:

- contradictory evidence;
- stale evidence;
- false corroboration;
- user correction;
- source revocation;
- sensor recalibration;
- model upgrade;
- distributed concurrent revisions;
- offline revision queues;
- belief oscillation;
- hysteresis;
- branching beliefs;
- dependency cascades;
- deleted evidence;
- privacy-restricted history;
- prompt injection;
- malicious revision attempts;
- replay;
- index reversion;
- historical/current retrieval.

## 59. Architectural Invariants

1. Current belief and historical belief are distinct.
2. New information does not automatically overwrite old memory.
3. Revision requires evidence or an authorized correction/deletion event.
4. Historical provenance is preserved unless governed deletion requires removal.
5. Inference never becomes observation through reconsolidation.
6. Correlated evidence is not independent confirmation.
7. Source revocation can trigger downstream reassessment.
8. Sensor recalibration can invalidate derived interpretations without rewriting raw history.
9. Model upgrades do not automatically establish truth.
10. Belief scope can be narrowed rather than globally changed.
11. Contradictions may remain contested.
12. Uncertainty can increase as a result of new evidence.
13. Promotion and demotion hysteresis can prevent unstable oscillation.
14. Safety response latency is independent of semantic belief stability.
15. Dependent beliefs are re-evaluated according to dependency strength.
16. Distributed concurrent revisions retain causal context.
17. Stale replicas cannot silently overwrite newer authorized state.
18. Prompt injection cannot directly revise memory.
19. Revision authorization is scoped.
20. Historical versions remain access-controlled.
21. Deletion and sanitization follow the established lifecycle architecture.
22. Revision explanations must be grounded in actual evidence and lineage.
23. Novi must be allowed to say that the evidence is insufficient to decide.

## 60. Final Principle

> **A trustworthy memory system does not pretend that its past beliefs were always correct. It preserves the history of what it believed, updates the current belief when justified by evidence, and makes the transition itself traceable.**

Novi therefore treats memory as **versioned, revisable, evidence-linked state** rather than a mutable collection of facts.