# 91 — Memory Knowledge Evidence Fusion Conflict Resolution and Belief Arbitration

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi combines evidence from multiple memory records, sensors, agents, tools and external sources; detects and represents conflict; evaluates source independence and reliability; updates beliefs without rewriting historical evidence; and determines when the system must abstain rather than force a single conclusion.

## Core Principle

> **Novi must fuse evidence without manufacturing certainty. When evidence conflicts, the conflict itself is information and must remain representable.**

## 1. Research Boundary

This architecture is informed by evidence-fusion research, belief-updating research and retrieval-grounded reasoning. Evidence theory provides useful tools for representing uncertainty and combining imperfect sources, but highly conflicting evidence can produce counter-intuitive fusion results; therefore no single mathematical fusion rule is treated as universally correct. fileciteturn142file0

Recent work on belief updating also indicates that source reliability can materially affect how contradictory information is evaluated and revised. fileciteturn143file0

Recent multi-evidence RAG research further supports combining heterogeneous authoritative evidence and using disagreement/high-risk cases as signals requiring additional scrutiny rather than blindly trusting one retrieved source. fileciteturn144file0

## 2. Cross-Validation Rule

No fusion algorithm is authoritative merely because it produces a numerical answer.

Every fusion strategy must be evaluated against:

- source reliability;
- source independence;
- uncertainty;
- known correlations;
- temporal validity;
- spatial validity;
- provenance;
- domain constraints;
- adversarial failure modes;
- observed calibration;
- consequence of error.

## 3. Evidence Is Not Belief

```text
OBSERVATION
   ↓
EVIDENCE
   ↓
FUSION
   ↓
BELIEF / HYPOTHESIS
   ↓
DECISION
```

Evidence remains traceable even when the resulting belief changes.

## 4. Evidence Record

Each evidence item should retain, where available:

- evidence ID;
- source;
- source type;
- capture time;
- observation time;
- location/context;
- content/claim;
- modality;
- transformation lineage;
- reliability estimate;
- uncertainty;
- independence group;
- integrity status;
- access classification.

## 5. Evidence Classes

Novi should distinguish:

```text
DIRECT OBSERVATION
INSTRUMENT MEASUREMENT
USER REPORT
TOOL RESULT
EXTERNAL SOURCE
DERIVED MEMORY
MODEL INFERENCE
AGENT REPORT
HYPOTHESIS
```

These should not receive identical default evidentiary treatment.

## 6. Direct vs Derived Evidence

```text
DIRECT OBSERVATION
    ≠
MODEL SUMMARY
```

A derivative inherits provenance and uncertainty from its supporting evidence.

## 7. Evidence Lineage

```text
SOURCE A
 ├── observation
 ├── summary
 └── semantic assertion
```

The summary and assertion must not be counted as independent confirmations of Source A.

## 8. Independence Groups

Evidence should be grouped by common origin.

```text
same sensor
same user report
same API response
same generated summary
same upstream dataset
```

Evidence within one correlated group should not be naively multiplied as independent support.

## 9. Source Reliability

Reliability should be contextual:

```text
source × task × environment × time
```

A camera may be reliable for object presence but weak for identity at distance.

## 10. Reliability Is Evidence, Not Authority

A historically reliable source can still be wrong in a particular observation.

Current evidence must remain independently evaluated.

## 11. Reliability Updating

Observed source performance can update reliability estimates:

```text
PREDICTION
 ↓
OBSERVED OUTCOME
 ↓
CALIBRATION
 ↓
UPDATED RELIABILITY
```

Historical observations must remain intact.

## 12. Evidence Weighting

Candidate weighting can consider:

- source reliability;
- independence;
- freshness;
- precision;
- completeness;
- environmental fit;
- corroboration;
- contradiction history.

Weights are decision aids, not proof of truth.

## 13. Temporal Compatibility

Evidence must be evaluated relative to the question time.

```text
DOOR OPEN AT 10:00
        ≠
DOOR OPEN AT 14:00
```

Older evidence may remain historically valid while becoming irrelevant to current state.

## 14. Spatial Compatibility

Evidence must be evaluated relative to location uncertainty and map/version context.

```text
OBSERVED HERE
 ≠
OBSERVED THERE
```

For moving objects and outdoor navigation, spatial validity must include time.

## 15. Claim Normalization

Before fusion, claims should be normalized into comparable forms without destroying their original wording or provenance.

Example:

```text
"The door appears closed"
→
DOOR.STATE = CLOSED
```

The normalized claim remains linked to the original evidence.

## 16. Open-World Semantics

Absence of evidence should not automatically become evidence of absence.

```text
NOT OBSERVED
 ≠
ABSENT
```

This is especially important for partial sensor coverage.

## 17. Explicit Unknown

Fusion must support:

```text
UNKNOWN
INSUFFICIENT EVIDENCE
CONFLICTED
NOT APPLICABLE
NOT OBSERVABLE
```

A forced binary answer is not acceptable when the evidence does not support one.

## 18. Agreement

When independent evidence converges:

```text
A → X
B → X
C → X
```

confidence may increase, subject to independence and source-quality checks.

## 19. Correlated Agreement

```text
A → summary B
B → assertion C
```

should not be treated as three independent observations.

## 20. Direct Contradiction

Example:

```text
Sensor A: DOOR = OPEN
Sensor B: DOOR = CLOSED
```

The system should produce a conflict state rather than silently selecting whichever value was processed last.

## 21. Conflict Representation

Represent:

```text
CLAIM A
CLAIM B
CONFLICT TYPE
EVIDENCE SET A
EVIDENCE SET B
SEVERITY
RESOLUTION STATUS
```

## 22. Conflict Types

Possible types include:

- temporal conflict;
- spatial conflict;
- identity conflict;
- state conflict;
- causal conflict;
- source conflict;
- schema conflict;
- authorization conflict;
- provenance conflict;
- model disagreement.

## 23. Conflict Severity

```text
LOW
MODERATE
HIGH
SAFETY-CRITICAL
```

Severity depends on consequence, not merely numerical disagreement.

## 24. Conflict Is Information

A conflict can reveal:

- sensor degradation;
- environmental change;
- stale memory;
- source unreliability;
- identity ambiguity;
- synchronization lag;
- genuine uncertainty.

It should therefore feed diagnostics and metamemory.

## 25. Resolution States

```text
UNRESOLVED
PARTIALLY RESOLVED
RESOLVED
SUPERSEDED
EXPIRED
```

An unresolved conflict remains queryable.

## 26. Resolution Methods

Depending on context, Novi may:

- request another observation;
- use a more authoritative source;
- apply temporal ordering;
- apply spatial constraints;
- evaluate source reliability;
- seek independent corroboration;
- preserve both claims;
- defer the decision;
- abstain.

## 27. No Universal Conflict Rule

The system must not hard-code:

```text
newest always wins
majority always wins
sensor always wins
user always wins
model always wins
```

Authority is contextual and governed by policy.

## 28. Source Hierarchy

Where a domain defines authoritative sources, that hierarchy should be explicit and versioned.

Example:

```text
SAFETY SENSOR
 >
SEMANTIC MEMORY
```

But only for the state that the safety sensor is designed to measure.

## 29. Cross-Modal Fusion

Evidence may arrive from:

```text
CAMERA
LIDAR
AUDIO
IMU
GNSS
TACTILE
THERMAL
USER
SOFTWARE API
```

Fusion should preserve modality-specific uncertainty.

## 30. Sensor Fusion Boundary

Fusion should not erase raw disagreement:

```text
RAW EVIDENCE
 ↓
FUSED ESTIMATE
```

The fused estimate remains linked to contributing evidence and residual uncertainty.

## 31. Dynamic State Estimation

For changing physical state, fusion should account for:

- timestamp differences;
- sensor latency;
- measurement noise;
- motion;
- prediction horizon.

A stale measurement should not be treated as simultaneous with a fresh measurement.

## 32. Belief State

The current belief state can contain:

```text
BEST CURRENT HYPOTHESIS
ALTERNATIVE HYPOTHESES
CONFIDENCE / UNCERTAINTY
SUPPORTING EVIDENCE
CONFLICTS
LAST VALIDATION
```

## 33. Belief Revision

When new evidence arrives:

```text
CURRENT BELIEF
      +
NEW EVIDENCE
      ↓
REASSESS
      ↓
REVISE / RETAIN / SPLIT / ABSTAIN
```

Historical evidence remains traceable.

## 34. Belief Versioning

Store:

```text
BELIEF v1
BELIEF v2
CURRENT BELIEF
```

with reason and evidence lineage for transitions.

## 35. Belief Confidence

Belief confidence should reflect:

- evidence quality;
- independence;
- consistency;
- freshness;
- uncertainty;
- contradiction;
- model limitations.

It should not be a direct copy of retrieval score.

## 36. Belief vs Decision Confidence

```text
HIGH CONFIDENCE BELIEF
 ≠
PERMISSION TO ACT
```

Action requires independent authorization and safety checks.

## 37. Decision Thresholds

Different consequences require different evidence thresholds.

```text
LOW CONSEQUENCE
→ lower evidence threshold may be acceptable

HIGH CONSEQUENCE
→ stronger evidence / corroboration required
```

## 38. Safety-Critical Arbitration

For safety-critical state:

```text
CONFLICT
 ↓
CONSERVATIVE SAFETY STATE
 ↓
REQUEST / SEEK BETTER EVIDENCE
```

The exact safe state must be defined by the relevant safety subsystem.

## 39. Abstention

Abstention is a valid output:

```text
CANNOT RELIABLY DETERMINE STATE
```

It should be preferred over false certainty when the cost of error is high.

## 40. Active Evidence Acquisition

When uncertainty matters, Novi can seek additional evidence:

```text
CONFLICT
 ↓
IDENTIFY MOST INFORMATIVE OBSERVATION
 ↓
ACQUIRE EVIDENCE
 ↓
FUSE AGAIN
```

This creates a closed-loop evidence system.

## 41. Value of Information

Additional evidence should be prioritized when it can materially change the decision or reduce consequential uncertainty.

Do not acquire expensive evidence merely to improve an irrelevant confidence score.

## 42. Human Clarification

When ambiguity concerns user intent or private facts, asking the user can be more appropriate than inferring.

```text
AMBIGUOUS INTENT
 ↓
CLARIFY
 ↓
UPDATE BELIEF
```

## 43. External Source Verification

Important claims can be checked against authoritative external sources when permitted.

External evidence remains subject to provenance, freshness and trust evaluation.

## 44. Multi-Agent Evidence

Reports from other Novi instances should include:

- agent identity;
- observation time;
- source sensors;
- location;
- confidence;
- provenance;
- software/hardware version.

## 45. Agent Independence

Two agents are not independent merely because they have different IDs.

Shared sensors, shared upstream APIs or copied reports create correlation.

## 46. Adversarial Evidence

Evidence may be maliciously manipulated.

Fusion should consider:

- spoofed sensor data;
- poisoned memories;
- forged tool responses;
- compromised agents;
- prompt injection;
- malicious external documents.

Untrusted evidence must not automatically gain authority through repetition.

## 47. Evidence Poisoning

Repeated false evidence can create apparent consensus:

```text
FALSE SOURCE
 ↓
COPIES
 ↓
RETRIEVAL
 ↓
APPARENT CONSENSUS
```

Lineage and independence tracking are required to resist this.

## 48. Misinformation Updating

Source reliability should influence belief revision, while preserving the possibility that historically reliable sources can still be wrong. Recent belief-updating research specifically supports attention to source reliability in contradictory-information settings. fileciteturn143file0

## 49. Evidence Fusion Algorithms

Possible mathematical approaches include:

- Bayesian updating;
- likelihood-based fusion;
- Dempster-Shafer-style evidence theory;
- weighted voting;
- probabilistic graphical models;
- Kalman/particle filtering for appropriate dynamic state-estimation problems;
- rule-based arbitration.

No method should be selected solely because it produces a convenient scalar confidence.

## 50. Dempster-Shafer Boundary

Evidence theory can represent uncertainty beyond a single probability distribution, but research identifies counter-intuitive behavior under highly conflicting evidence and ongoing debate over uncertainty measures. fileciteturn142file0

Therefore Novi should treat Dempster-Shafer methods as one configurable family, not the universal arbitration mechanism.

## 51. Bayesian Boundary

Bayesian updating can be useful when priors, likelihoods and conditional assumptions are defensible.

Poor priors or incorrect independence assumptions can produce confidently wrong results.

## 52. Rule-Based Arbitration

Hard rules are appropriate for explicit safety or governance constraints.

They should not be disguised as statistical evidence.

## 53. Hybrid Arbitration

A practical architecture may combine:

```text
HARD POLICY RULES
      ↓
DOMAIN CONSTRAINTS
      ↓
STATISTICAL / EVIDENCE FUSION
      ↓
UNCERTAINTY ASSESSMENT
      ↓
DECISION THRESHOLD
```

## 54. Evidence Fusion Output

The fusion engine should return structured output:

```text
CLAIM
STATUS
CONFIDENCE / UNCERTAINTY
SUPPORTING EVIDENCE
CONTRADICTING EVIDENCE
INDEPENDENCE GROUPS
FRESHNESS
PROVENANCE
RESOLUTION STATE
RECOMMENDED NEXT EVIDENCE
```

## 55. Context Assembly Integration

Document 90 may retrieve evidence candidates; document 91 determines how competing evidence is reconciled before reasoning receives the result.

```text
90 RETRIEVAL
   ↓
91 FUSION / ARBITRATION
   ↓
CONTEXT ASSEMBLY
   ↓
REASONING
```

## 56. Consolidation Integration

If arbitration changes a belief, document 89 controls durable consolidation/reconsolidation.

Fusion must not directly rewrite durable memory.

## 57. Metamemory Integration

Conflicts and source errors should update document 86's memory-quality assessments.

```text
SOURCE ERROR
 ↓
METAMEMORY RELIABILITY UPDATE
```

## 58. World-Model Integration

The semantic world model receives current beliefs with uncertainty and provenance, not opaque "truth" values.

## 59. Prospective Memory Integration

A conflict in evidence may block a consequential intention:

```text
INTENTION
 ↓
REQUIRED STATE UNCERTAIN
 ↓
BLOCK / VERIFY
```

## 60. Procedural Integration

If a skill depends on uncertain state, execution should pause or choose a safer validated variant rather than assuming the preferred state is true.

## 61. Privacy Integration

Fusion must respect access controls before combining evidence.

Unauthorized evidence cannot become authorized merely by fusing it with permitted evidence.

## 62. Data Minimization

The fusion engine should retain only the evidence details necessary for the decision and required provenance.

## 63. Auditability

Important arbitration decisions should record:

- evidence set;
- algorithms/rules used;
- versions;
- source reliability inputs;
- conflicts;
- output;
- decision threshold;
- reason for abstention or selection.

## 64. Explainability

Novi should be able to answer:

```text
Why does it currently believe X?
What evidence supports X?
What evidence contradicts X?
Which sources were considered independent?
Why was source A weighted more than source B?
What would change the belief?
```

Explanations must be generated from recorded provenance and decision metadata.

## 65. Idempotency

Fusing the same unchanged evidence set repeatedly must not inflate confidence or create duplicate evidence.

## 66. Determinism

For a fixed evidence set, policy version and algorithm version, arbitration should be reproducible within defined numerical tolerances.

## 67. Uncertainty Calibration

Fusion confidence should be evaluated against later observed outcomes.

Track calibration separately by domain and consequence class.

## 68. Testing

Test:

- independent corroboration;
- correlated evidence;
- direct contradiction;
- stale evidence;
- temporal mismatch;
- spatial mismatch;
- identity ambiguity;
- unknown states;
- sensor disagreement;
- multi-agent disagreement;
- malicious evidence;
- duplicated summaries;
- poisoned retrieval;
- source reliability drift;
- Bayesian fusion;
- evidence-theory fusion;
- rule-based arbitration;
- hybrid arbitration;
- safety-critical conflicts;
- abstention;
- active evidence acquisition;
- user clarification;
- privacy filtering;
- deletion-aware provenance;
- calibration;
- reproducibility;
- audit trail;
- failure recovery.

## 69. Architectural Invariants

1. Evidence and belief are distinct.
2. Historical evidence remains traceable after belief revision.
3. Retrieval score is not evidence strength.
4. Repeated derivatives do not create independent evidence.
5. Source reliability is contextual and revisable.
6. Independence must be established, not assumed.
7. Temporal and spatial validity matter to evidence fusion.
8. Unknown and conflict are valid states.
9. Conflict must not be silently hidden.
10. No universal source hierarchy applies to every domain.
11. No universal fusion algorithm is assumed.
12. High-conflict evidence can require abstention or new observation.
13. High-consequence decisions require stronger evidence thresholds.
14. Belief confidence does not grant action authority.
15. Safety arbitration remains outside ordinary belief fusion.
16. Unauthorized evidence cannot become authorized through fusion.
17. Important arbitration decisions remain auditable.
18. Fusion is idempotent over unchanged evidence.
19. Confidence must be calibrated against outcomes where possible.
20. Fusion must preserve provenance and uncertainty.
21. Active evidence acquisition should target decision-relevant uncertainty.
22. Malicious repetition cannot manufacture consensus.
23. Current beliefs are revisable; historical evidence is not silently rewritten.
24. Fusion output is not automatically durable memory.
25. Consequential uncertainty should produce conservative handling or abstention.

## 70. Final Principle

> **Novi should not ask which source to believe; it should determine what each source actually establishes, how independent and reliable the evidence is, what conflicts remain, and what conclusion is justified by the total evidence. When the evidence is insufficient, Novi must preserve uncertainty rather than manufacture agreement.**

Evidence fusion is therefore the arbitration layer between retrieval and belief: it converts heterogeneous evidence into a calibrated, provenance-preserving belief state without turning disagreement into false certainty.