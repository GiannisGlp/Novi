# 76 — Memory Knowledge Memory Promotion, Demotion and Retention Policy

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define when Novi should retain an observation, promote information into memory or knowledge, reduce its status, supersede it, archive it, or remove it. The policy connects evidence quality, provenance, uncertainty, lifecycle governance, privacy, retention, and secure deletion.

## Core Principle

> **Novi must not remember everything, believe everything it remembers, or retain information forever merely because it may become useful.**

Promotion, demotion and retention are separate decisions.

## 1. The Three Decisions

```text
PROMOTION
Should this information become more durable or authoritative?

DEMOTION
Should its status, confidence, scope or authority be reduced?

RETENTION
Should the information continue to exist at all, and in what form?
```

A memory can be retained while being demoted. A claim can be promoted without retaining every raw input. A record can remain historically useful without remaining current knowledge.

## 2. Lifecycle Relationship

```text
OBSERVATION
 ↓
CANDIDATE
 ↓
EPISODIC MEMORY
 ↓
CONSOLIDATED MEMORY
 ↓
KNOWLEDGE CANDIDATE
 ↓
VALIDATED KNOWLEDGE
 ↓
CURRENT / HISTORICAL KNOWLEDGE
 ↓
STALE / SUPERSEDED / DEMOTED
 ↓
ARCHIVED / RESTRICTED
 ↓
DELETION
 ↓
SANITIZATION / VERIFICATION
```

Not every item follows every state.

## 3. Evidence Before Promotion

Promotion should depend on the evidence available and the intended use.

Relevant signals include:

- provenance completeness;
- source reliability;
- evidence independence;
- uncertainty;
- recency;
- repetition that is genuinely independent;
- cross-validation;
- contextual relevance;
- consequence of error;
- user authority where applicable.

Repeated retrieval of the same evidence does not strengthen it.

## 4. Promotion Is Not Truth

A promotion decision means only that information has met the requirements for a defined memory/knowledge class.

```text
PROMOTED
 ≠
UNIVERSALLY TRUE
```

## 5. Purpose-Specific Promotion

The same information may be sufficient for one purpose but insufficient for another.

```text
conversation context
    ↓
low promotion threshold

long-term factual knowledge
    ↓
stronger threshold

safety-critical state
    ↓
current validated evidence
```

Promotion thresholds must therefore be consequence-dependent.

## 6. Candidate Memory

A candidate is information worth retaining temporarily while its usefulness or reliability is evaluated.

Candidates may have:

- limited retention;
- low authority;
- restricted retrieval;
- explicit uncertainty;
- no learning eligibility.

## 7. Episodic Memory

Episodic memory represents events or experiences in context.

It should preserve, where appropriate:

- time;
- location;
- participants/objects;
- source observations;
- context;
- outcome;
- uncertainty.

An episodic memory is not automatically generalized knowledge.

## 8. Consolidated Memory

Consolidation can combine related episodes while retaining lineage to the underlying evidence.

```text
Episode A ─┐
Episode B ─┼→ consolidated representation
Episode C ─┘
```

Consolidation must not erase meaningful contradictions or uncertainty.

## 9. Knowledge Promotion

A candidate claim can become durable knowledge only after the relevant validation and policy checks.

```text
CANDIDATE
 ↓
PROVENANCE
 ↓
VALIDATION
 ↓
UNCERTAINTY ASSESSMENT
 ↓
POLICY CHECK
 ↓
KNOWLEDGE PROMOTION
```

## 10. Promotion Levels

A practical status vocabulary is:

```text
TRANSIENT
CANDIDATE
PROVISIONAL
SUPPORTED
VALIDATED
ESTABLISHED
```

The exact semantics and thresholds must be domain-specific.

## 11. Provisional Knowledge

Provisional knowledge is useful enough to retrieve but should remain explicitly qualified.

It must not silently behave as established knowledge.

## 12. Established Knowledge

Established knowledge should require sufficiently strong evidence for its intended scope and consequence.

It remains revisable if new evidence changes the conclusion.

## 13. User-Provided Information

A user statement can receive high relevance and authority for user-owned preferences or explicitly defined personal facts.

However, user-provided information should retain provenance as a user statement and should not automatically become objective external truth.

## 14. External Information

External information follows documents 65–67 and requires source provenance and validation appropriate to its intended use.

Internet availability does not lower promotion requirements.

## 15. Sensor-Derived Information

Physical observations should distinguish:

```text
raw measurement
 ↓
observation
 ↓
interpretation
 ↓
knowledge
```

Current local sensor evidence may have priority for current physical state even when older knowledge has a higher historical confidence.

## 16. Spatial Knowledge

Places, routes and maps require promotion policies that account for:

- localization quality;
- coordinate frame;
- map version;
- observation time;
- environmental change;
- repeated independent observations.

A route remembered from yesterday is not automatically safe today.

## 17. Thermal Knowledge

Thermal information must distinguish:

```text
environmental thermal knowledge
vs
Novi internal thermal state
```

Internal thermal safety state is governed by real-time safety systems, not semantic memory.

## 18. Temporal Knowledge

Every time-sensitive knowledge item should carry validity information where appropriate.

```text
VALID_NOW
HISTORICAL
SCHEDULED
EXPIRED
UNKNOWN_VALIDITY
```

## 19. Historical Truth

An outdated statement can remain historically correct.

```text
"The user lived at location X in 2025"
```

can remain valid as history after the user moves.

The system must not confuse historical truth with current state. This is consistent with ICO guidance that records describing historical circumstances can remain accurate when clearly represented as historical records. citeturn0search0

## 20. Demotion Triggers

Information may be demoted when:

- contradictory evidence appears;
- source reliability falls;
- provenance is broken;
- evidence expires;
- context changes;
- the item becomes stale;
- a model/version issue is discovered;
- a source is revoked;
- confidence calibration changes;
- a user challenges accuracy;
- a synchronization conflict remains unresolved.

## 21. Demotion Does Not Mean Deletion

```text
ESTABLISHED
 ↓
PROVISIONAL
```

does not mean:

```text
DELETE
```

Historical or contested evidence may need to remain available for audit, reasoning and future validation, subject to retention and privacy policy.

## 22. Supersession

When new evidence replaces an older current claim:

```text
Knowledge v1
      ↓ SUPERSEDED_BY
Knowledge v2
```

The old claim can remain historical if retention permits.

## 23. Contradiction

If two claims cannot safely be reconciled:

```text
CLAIM A
   ↕
CONTESTED
   ↕
CLAIM B
```

Novi should prefer explicit contestation over an unsupported single answer.

## 24. Source Revocation

If a source is later found unreliable or compromised:

```text
SOURCE REVOKED
 ↓
DEPENDENCY ANALYSIS
 ↓
AFFECTED CLAIMS
 ↓
REVALIDATION / DEMOTION / QUARANTINE
```

Promotion must be reversible where its evidence can be invalidated.

## 25. Knowledge Decay

Knowledge can lose practical value even without becoming false.

Decay may arise from:

- time;
- environmental change;
- changing user preferences;
- changing software/hardware;
- source updates;
- changing external conditions.

Decay should normally reduce current authority rather than rewrite history.

## 26. Freshness Policies

Different knowledge classes need different freshness requirements.

```text
REAL-TIME PHYSICAL STATE
seconds / immediate validation

HOUSEHOLD STATE
context-dependent

USER PREFERENCE
until changed or invalidated

HISTORICAL FACT
may remain stable

EXTERNAL WEB FACT
source-dependent
```

These are policy examples, not universal fixed durations.

## 27. Retention Classes

A retention policy should classify information, for example:

```text
EPHEMERAL
SHORT_TERM
EPISODIC
LONG_TERM
HISTORICAL
AUDIT / SECURITY
USER_CONTROLLED
REGULATED / POLICY_CONTROLLED
```

Actual periods are defined by purpose, risk and applicable policy rather than one universal timer.

## 28. Purpose Limitation

Information should be retained and reused for defined purposes.

A new purpose requires an explicit compatibility/policy evaluation rather than automatic reuse. ICO guidance identifies purpose limitation as a core UK GDPR principle. citeturn0search1turn0search2

## 29. Data Minimization

Novi should retain only information necessary for the authorized purpose where feasible.

Periodic review should identify information no longer needed. ICO guidance explicitly recommends limiting personal data to what is necessary and reviewing/delete data that is no longer needed. citeturn0search4

## 30. Retention Review

Retention should be actively reviewed rather than assumed indefinite.

A retention review may ask:

```text
Is it still needed?
Is the purpose still valid?
Is it still accurate?
Is it still authorized?
Is the current representation necessary?
Can a smaller derivative replace the raw data?
```

## 31. No "Just in Case" Retention

Novi must not retain personal information indefinitely merely because it might someday be useful.

The retention decision must be justified by purpose, policy and applicable requirements. ICO guidance specifically states that personal information should not be retained indefinitely merely on a "just in case" basis. citeturn0search9turn0search12

## 32. Retention vs Historical Value

Historical value does not automatically justify indefinite retention of identifiable personal information.

Where historical retention is justified, appropriate safeguards and purpose restrictions apply. citeturn0search3turn0search2

## 33. Raw Data vs Derivatives

Retention should be decided separately for:

```text
raw observation
processed observation
summary
embedding
index
claim
knowledge
provenance metadata
```

A derivative may be retained after raw data expires only when policy permits and its lineage/privacy implications have been evaluated.

## 34. Derived Memory Retention

Deleting raw evidence does not automatically mean every derivative must be deleted, nor does it automatically permit every derivative to remain.

The dependency and privacy policy must decide.

If deletion requirements apply, document 63 governs the resulting erasure/sanitization process.

## 35. Learning Derivatives

Training or behavioral-learning derivatives require explicit lineage and retention policy.

```text
experience
 ↓
learning artifact
 ↓
behavior/model
```

Deleting the experience requires impact assessment on dependent learning artifacts where applicable.

## 36. Retention and Security

Retained information remains an attack surface.

Longer retention increases the period during which confidentiality, integrity and access controls must protect it.

## 37. Storage Tiers

Possible storage tiers:

```text
HOT
active/current

WARM
less frequently accessed

COLD
historical

ARCHIVE
policy-controlled long-term storage

DELETED / SANITIZED
no longer recoverable under the defined assurance level
```

NIST SP 800-88 Rev. 2 defines sanitization in terms of making access to target data infeasible for a defined level of effort; retention policy therefore must distinguish ordinary logical deletion from actual sanitization. citeturn0search10

## 38. Retention Expiration

Expiration should trigger a governed transition, not an uncontrolled database deletion.

```text
RETENTION DUE
 ↓
POLICY EVALUATION
 ↓
RETAIN / REDUCE / ARCHIVE / DELETE
 ↓
VERIFY
```

## 39. Grace Periods

Where operationally necessary, systems may use bounded grace periods before irreversible deletion.

Grace periods must not silently defeat an explicit deletion requirement or privacy policy.

## 40. User-Controlled Memory

Where user-facing memory can be managed directly, Novi should support explicit controls such as:

- inspect;
- correct;
- restrict;
- forget;
- delete;
- export where supported.

User controls remain subject to safety/system constraints and applicable access rights.

## 41. Accuracy Challenges

When a user or trusted source challenges a memory's accuracy:

```text
CHALLENGE
 ↓
EVALUATE
 ↓
CORRECT / DEMOTE / MARK CONTESTED / DELETE
```

The original claim should not be silently rewritten when historical auditability requires preserving its lineage. ICO guidance emphasizes source/status clarity and appropriate correction or erasure of inaccurate personal data. citeturn0search0

## 42. Opinion vs Fact

Memory should distinguish:

```text
FACTUAL CLAIM
OPINION
PREFERENCE
INFERENCE
UNCERTAIN BELIEF
```

A change in opinion does not necessarily make a historical record false.

## 43. Retention of Mistakes

A known mistake may sometimes remain as a historical/audit record when necessary, but it must be clearly marked as erroneous and must not be retrieved as current truth.

## 44. Memory Retrieval Eligibility

Retention does not imply unrestricted retrieval.

An item may be:

```text
RETAINED + RETRIEVABLE
RETAINED + RESTRICTED
RETAINED + AUDIT_ONLY
RETAINED + NOT_CURRENT
```

## 45. Knowledge Authority Decay

Authority should be allowed to decrease independently of storage status.

```text
retained = yes
current authority = low
```

This prevents stale knowledge from becoming falsely influential merely because it remains stored.

## 46. Promotion Hysteresis

Avoid rapid oscillation between statuses when evidence fluctuates around a threshold.

```text
PROMOTE threshold > DEMOTE threshold
```

Different entry and exit thresholds can provide stability.

## 47. Review Scheduling

Items requiring periodic review should have a review condition or date based on their class and risk.

High-consequence knowledge should receive stronger review requirements than low-consequence historical notes.

## 48. Safety-Critical State

Semantic memory must not be the sole authority for immediate safety-critical physical state.

Examples include:

- obstacle presence;
- motor thermal limits;
- battery protection;
- collision risk.

These require current validated sensing and dedicated safety controls.

## 49. Offline Retention

Retention, promotion and demotion must continue to operate offline.

Novi must not need cloud access to decide whether locally governed information can remain in memory.

## 50. Synchronization

Retention/deletion decisions synchronize through the distributed-state architecture.

A stale replica must not resurrect an expired or deleted item.

Tombstones and version/causal metadata should be used where required.

## 51. Conflict Between Retention Policies

When two replicas have different policy versions:

```text
policy version
scope
owner
resource class
```

must be considered.

A less restrictive replica must not silently weaken a more restrictive local policy.

## 52. Privacy Propagation

Promotion can create additional derivatives. Every derivative must inherit applicable privacy restrictions.

```text
private observation
 ↓
private claim
 ↓
private knowledge
 ↓
private embedding/index
```

## 53. Access Revocation

When access is revoked, the memory may remain physically present while becoming inaccessible pending deletion/sanitization according to policy.

## 54. Deletion Boundary

When retention ends:

```text
DELETE REQUEST
 ↓
DEPENDENCY ANALYSIS
 ↓
RESTRICT
 ↓
DELETE DERIVATIVES AS REQUIRED
 ↓
SANITIZE
 ↓
VERIFY
```

Document 63 defines secure deletion and cryptographic erasure requirements.

## 55. Auditability

Important lifecycle decisions should record:

- object;
- previous status;
- new status;
- reason;
- evidence/policy basis;
- actor/system;
- timestamp;
- affected derivatives;
- review outcome.

## 56. Explainability

Novi should be able to answer:

```text
Why was this promoted?
Why was this demoted?
Why is this still retained?
Why is this historical?
Why is this restricted?
Why was this deleted?
```

Answers must use actual recorded lineage and policy, not invented explanations.

## 57. Metrics

Useful metrics include:

- promotion rate;
- demotion rate;
- stale-memory rate;
- contradiction rate;
- retention-expiry rate;
- deletion completion rate;
- provenance completeness;
- review backlog;
- false-promotion rate;
- false-retention rate;
- knowledge revalidation rate.

## 58. Testing

Test:

- weak evidence promotion;
- independent corroboration;
- correlated evidence;
- contradictory evidence;
- source revocation;
- stale knowledge;
- historical/current distinction;
- user correction;
- retention expiry;
- deletion propagation;
- offline expiry;
- synchronization conflicts;
- policy-version conflicts;
- privacy propagation;
- derivative retention;
- learning-derivative impact;
- promotion hysteresis;
- safety-critical state isolation;
- audit completeness;
- accidental resurrection.

## 59. Architectural Invariants

1. Promotion, demotion and retention are separate decisions.
2. Promotion never means universal truth.
3. Evidence quality and consequence determine promotion thresholds.
4. Repeated retrieval does not increase evidence strength.
5. Contradictions can produce contested status rather than forced resolution.
6. Demotion does not automatically mean deletion.
7. Historical truth is distinct from current truth.
8. Stale knowledge must not silently retain current authority.
9. Source revocation can trigger downstream demotion or quarantine.
10. Retention must be purpose- and policy-driven.
11. Personal information must not be retained indefinitely merely for possible future usefulness.
12. Data minimization applies to raw data and derivatives.
13. Retention periods require periodic review.
14. Raw data and derived artifacts require separate retention decisions.
15. Privacy restrictions propagate through promoted and derived memory.
16. Deletion follows the secure-deletion architecture.
17. Offline operation remains fully functional.
18. Synchronization cannot resurrect deleted or expired memory.
19. Semantic memory cannot replace real-time safety authority.
20. User accuracy challenges trigger explicit evaluation.
21. Known mistakes must not be presented as current truth.
22. Lifecycle decisions remain auditable.
23. Explanations of lifecycle decisions must be grounded in recorded evidence and policy.

## 60. Cross-Validation Basis

This architecture is aligned with the principles of:

- **NIST AI RMF**: lifecycle-wide governance, measurement and management of AI risk. citeturn0search14
- **ICO / UK GDPR principles**: purpose limitation, data minimisation, accuracy, storage limitation, integrity/confidentiality and accountability. citeturn0search2turn0search1turn0search4turn0search0
- **ICO IoT guidance**: smart-device data should not be retained indefinitely merely because it may become useful; retention should be reviewed and data erased/anonymised when no longer needed. citeturn0search9
- **NIST SP 800-88 Rev. 2**: logical deletion and sanitization are distinct concepts, with sanitization defined according to the required assurance level. citeturn0search10

These sources inform the architecture; they do not replace a deployment-specific legal, safety or security assessment.

## 61. Final Principle

> **Novi should promote information only as far as its evidence and purpose justify, demote it when its support or relevance weakens, and retain it only for as long as its authorized purpose warrants.**

Memory should therefore be treated as a governed, revisable resource—not an irreversible accumulation of everything Novi has ever encountered.