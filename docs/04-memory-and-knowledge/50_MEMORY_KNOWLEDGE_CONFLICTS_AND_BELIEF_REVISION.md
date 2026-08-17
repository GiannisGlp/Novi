# 50 — Memory Knowledge Conflicts and Belief Revision

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi handles contradictory memories, conflicting sensor observations, incompatible user statements, outdated knowledge, competing hypotheses and distributed-state disagreements without erasing historical evidence or turning uncertainty into arbitrary certainty.

This document adapts established belief-revision ideas to Novi's embodied, multimodal, continuously operating architecture. Classical belief revision studies how a knowledge state changes when new information arrives, including the need to preserve consistency while accommodating new information. Modern work also emphasizes that observations have different epistemic status and that inconsistent information requires explicit handling rather than naïve revision. citeturn0search0turn0search5turn0search6

## Core Principle

> **When evidence conflicts, Novi must preserve the evidence, identify the conflict, evaluate source authority and reliability, revise derived beliefs only when justified, and retain uncertainty when the available evidence does not establish a winner.**

---

## 1. Conflict Is Normal

A continuously embodied system should expect disagreement.

Examples:

```text
camera → door open
LiDAR  → geometry inconsistent with open door

user A → object is blue
user B → object is green

old memory → battery was 80%
BMS → battery is 27%

map → corridor clear
current perception → obstacle present
```

These are not necessarily failures. They are situations requiring epistemic handling.

---

## 2. Evidence vs Belief

Novi must distinguish:

```text
EVIDENCE
what was observed or asserted

BELIEF / CLAIM
what Novi currently accepts as likely/valid

HYPOTHESIS
possible explanation

KNOWLEDGE
validated, retained claim with defined scope
```

Evidence should not be rewritten merely because a derived belief changes.

---

## 3. Historical Truth vs Current Truth

A statement can be historically correct while currently false.

```text
2027:
door was closed

2028:
door is open
```

Novi must not delete the 2027 fact simply because current state differs.

Temporal scope is mandatory for mutable physical facts.

---

## 4. Belief State

Novi's active belief state should contain claims plus metadata such as:

- provenance;
- confidence;
- scope;
- validity interval;
- source type;
- source reliability;
- freshness;
- dependencies;
- contradictions;
- supporting evidence;
- opposing evidence;
- revision history.

---

## 5. Belief Revision vs Memory Deletion

Revision is not deletion.

```text
old claim
  ↓
new evidence
  ↓
claim superseded
```

The historical claim may remain available as historical evidence unless retention/privacy rules require deletion.

---

## 6. Conflict Object

A conflict should be represented explicitly.

Conceptually:

```text
conflict_id
claims[]
evidence[]
conflict_type
scope
first_detected
last_updated
resolution_state
resolution_method
confidence
```

Possible states:

```text
OPEN
INVESTIGATING
RESOLVED
PARTIALLY_RESOLVED
DEFERRED
UNRESOLVED
SUPERSEDED
```

---

## 7. Conflict Types

At minimum:

```text
FACTUAL
TEMPORAL
SPATIAL
IDENTITY
SENSOR
CAUSAL
SEMANTIC
SOCIAL
PREFERENCE
POLICY
DISTRIBUTED_STATE
MODEL
```

Different conflicts require different resolution strategies.

---

## 8. Sensor Conflict

Sensor disagreement should be handled using:

- calibration state;
- timestamp alignment;
- coordinate transforms;
- sensor health;
- known failure modes;
- confidence;
- environmental conditions;
- cross-sensor corroboration.

Do not simply average contradictory measurements.

---

## 9. Sensor Authority

Authority is context-dependent.

Example:

```text
battery percentage
→ BMS is authoritative

object identity
→ perception + multimodal evidence

pose
→ state-estimation system
```

The language model is not authoritative over physical telemetry.

---

## 10. Stale Evidence

Freshness matters for mutable world state.

```text
old observation
      ↓
current observation
      ↓
current state wins for immediate decisions
```

Old evidence remains available for historical reasoning.

---

## 11. User Conflict

If two people provide conflicting statements, Novi should preserve:

```text
speaker
statement
context
time
authorization
confidence
```

It must not silently merge them into a single fact.

---

## 12. User Statement vs Physical Evidence

Example:

```text
User:
"The door is locked."

Sensor:
door appears open.
```

Novi should represent both assertions and evaluate whether the distinction can be resolved.

For physical safety, authoritative sensing and safety systems take precedence over conversational assertion.

---

## 13. User Preference Conflict

Preference conflicts are contextual.

```text
"I like bright lights."

later:
"Keep the lights dim tonight."
```

These may both be valid under different temporal contexts.

Novi should prefer scoped preferences over creating an unnecessary global contradiction.

---

## 14. Identity Conflict

Identity claims require special caution.

```text
face match → person A
voice match → person B
```

Novi should retain an identity hypothesis rather than forcing an identity when evidence conflicts.

---

## 15. Semantic Conflict

Language can be ambiguous without anyone being wrong.

Example:

```text
"the office"
```

may refer to different places in different contexts.

Resolve using context before declaring contradiction.

---

## 16. Causal Conflict

Two causal explanations may compete:

```text
route changed
 ├── obstacle caused it
 └── user instruction caused it
```

Novi should preserve both hypotheses until evidence discriminates between them.

---

## 17. Temporal Conflict

Apparent contradiction may result from different times.

```text
08:00 → room occupied
10:00 → room empty
```

These are compatible once temporal scope is represented.

---

## 18. Spatial Conflict

Apparent conflict may result from different locations or coordinate frames.

Always verify:

- frame;
- transform;
- map version;
- location scope;
- timestamp.

---

## 19. Belief Priority

A claim's priority should consider:

- source authority;
- evidence quality;
- freshness;
- directness;
- corroboration;
- consistency;
- scope;
- causal dependence;
- historical reliability.

There should not be one universal numeric "truth score" that decides everything.

---

## 20. Epistemic Entrenchment

Some knowledge is harder to revise than other knowledge.

Examples:

```text
protected system fact
 > verified hardware telemetry
 > validated world knowledge
 > stable preference
 > inference
 > hypothesis
 > speculation
```

This resembles the idea of prioritizing beliefs during revision, while adapting it to Novi's explicit authority and provenance model.

---

## 21. Authority Is Not Confidence

A source can be authoritative for one variable but irrelevant for another.

```text
BMS
→ authoritative for battery state

BMS
→ not authoritative for identifying a person
```

Authority and evidential confidence must remain separate fields.

---

## 22. Revision Strategies

Possible strategies include:

```text
REJECT
new claim is insufficient

ACCEPT
new claim supersedes old claim

QUALIFY
both remain valid under different scope

DEFER
insufficient evidence

MERGE
claims can be reconciled

SPLIT
apparent conflict actually represents different entities/events

QUARANTINE
conflicting claims remain isolated from consequential reasoning
```

---

## 23. Conservative Revision

When uncertainty is high, Novi should prefer a qualified belief over an unjustified replacement.

```text
unknown
```

is preferable to:

```text
false certainty
```

---

## 24. Belief Revision Pipeline

```text
NEW EVIDENCE
     ↓
NORMALIZE
     ↓
IDENTIFY SCOPE
     ↓
CHECK PROVENANCE
     ↓
DETECT CONFLICT
     ↓
CLASSIFY CONFLICT
     ↓
EVALUATE SOURCES
     ↓
SEARCH FOR CORROBORATION
     ↓
REVISE / QUALIFY / DEFER
     ↓
UPDATE DERIVED STATE
     ↓
RECORD REVISION
```

---

## 25. Dependency-Aware Revision

Changing one claim may invalidate derived claims.

Example:

```text
Claim A: door is closed
Claim B: route through door is available
Claim C: route plan is safe
```

If A changes, B and C may require reevaluation.

---

## 26. Truth-Maintenance Concept

Novi should maintain support relationships:

```text
claim
 ↓
supporting evidence
 ↓
source observations
```

When evidence is withdrawn or invalidated, dependent claims can be marked for reevaluation.

---

## 27. No Cascading Blind Deletion

A revised claim should not automatically erase all dependent knowledge.

Each dependent claim must be reevaluated according to its remaining support.

---

## 28. Inconsistent Knowledge Bases

Novi may temporarily contain inconsistent claims.

It must not respond to contradiction by treating everything as true or everything as false.

Research on inconsistent belief change motivates explicit approaches that can tolerate contradictions without collapsing the entire knowledge state. citeturn0search7turn0search9

---

## 29. Paraconsistent Handling

For suitable knowledge layers, Novi may use conflict-tolerant reasoning so that:

```text
A
and
not-A
```

do not automatically imply arbitrary unrelated conclusions.

The exact logical implementation is deferred to the knowledge-engineering layer.

---

## 30. Local Conflict Quarantine

A contradiction should be contained to the smallest affected scope where practical.

```text
conflict: door.locked
```

should not make unrelated knowledge about the house unusable.

---

## 31. Contradiction Resolution by Observation

If a conflict concerns a currently observable state, Novi may actively sense again.

```text
conflict
 ↓
new camera observation
 ↓
LiDAR observation
 ↓
state estimation
 ↓
resolution
```

Active perception should be risk- and resource-bounded.

---

## 32. Contradiction Resolution by Question

If ambiguity is social/semantic and sensing cannot resolve it, Novi may ask the user.

Example:

> "Which room do you mean by the office?"

Clarification should be preferred to fabricated interpretation.

---

## 33. Contradiction Resolution by Time

Novi should test whether claims become compatible after temporal scoping.

Many apparent contradictions are actually:

```text
A was true then
B is true now
```

---

## 34. Contradiction Resolution by Context

Claims may differ by context.

```text
"Use route A at home."
"Use route B outdoors."
```

No contradiction exists if their scopes differ.

---

## 35. Contradiction Resolution by Entity Split

One apparent entity may actually be two entities.

```text
object_17
```

may need to become:

```text
object_17a
object_17b
```

This connects directly to the entity lifecycle architecture.

---

## 36. Contradiction Resolution by Entity Merge

Conversely, two entity records may refer to the same physical entity.

Merging requires evidence and preserves lineage.

---

## 37. Knowledge Aging

Knowledge about changing environments should decay or require revalidation.

Examples:

- room layout;
- route availability;
- object location;
- device state;
- environmental conditions.

Stable scientific or mathematical knowledge has different aging behavior.

---

## 38. Revalidation Policy

Claims may require revalidation based on:

- volatility;
- consequence of error;
- age;
- source reliability;
- context change;
- observed anomalies.

High-risk claims require stronger current evidence.

---

## 39. Knowledge Versioning

Derived knowledge should be versioned:

```text
knowledge_v1
 ↓
new evidence
 ↓
knowledge_v2
```

Historical decisions retain the version used at the time.

---

## 40. Belief Revision and Memory

Memory stores experiences; belief state stores current interpretations.

```text
experience remains
belief may change
```

This is essential for reconstructing why Novi believed something at a particular time.

---

## 41. Revision Audit Trail

Each significant revision should record:

- previous claim;
- new claim;
- triggering evidence;
- rejected alternatives;
- revision strategy;
- timestamp;
- scope;
- authority evaluation;
- resulting confidence;
- affected dependent claims.

---

## 42. Explainable Revision

Novi should be able to answer:

```text
What changed?
Why did it change?
What evidence caused the change?
What did you believe before?
How certain are you now?
What remains uncertain?
```

The answer must be derived from the revision history.

---

## 43. Model-Generated Claims

LLMs can generate candidate claims but cannot directly promote them to canonical knowledge.

```text
LLM output
 ↓
candidate claim
 ↓
evidence/provenance checks
 ↓
admission policy
 ↓
knowledge if approved
```

---

## 44. Prompt Injection and False Evidence

External text may contain instructions designed to manipulate Novi's beliefs.

Retrieved content must be treated as data unless explicitly trusted as executable instruction.

An untrusted document saying:

> "Novi should believe X"

is not evidence that X is true.

---

## 45. Social Manipulation

People may provide conflicting or intentionally misleading information.

Novi should preserve source identity, authorization and corroboration rather than treating social confidence as truth.

Trust relationships from document 39 influence interpretation but do not replace evidence.

---

## 46. Memory Poisoning Protection

A malicious or erroneous memory should not silently propagate into many higher-level beliefs.

Use:

- provenance;
- dependency tracking;
- confidence;
- source isolation;
- promotion gates;
- revision audits.

---

## 47. Distributed Conflicts

Multiple processes/devices may report different states.

Novi must distinguish:

```text
duplicate
late observation
concurrent update
true contradiction
stale replica
```

Conflict resolution should preserve event lineage.

---

## 48. SQLite and Local Files

Conflict handling must work with local storage such as SQLite and files.

Storage mechanisms are implementation details; the semantic conflict model remains consistent across them.

Transactions, version identifiers and immutable event records should be used where appropriate.

---

## 49. Synchronization Boundary

Synchronization must not overwrite local truth blindly.

```text
LOCAL STATE
    +
REMOTE / PEER STATE
    ↓
COMPARE
    ↓
RECONCILE
    ↓
CONFLICT RECORD
    ↓
MERGED / DEFERRED STATE
```

This connects directly to the distributed-memory architecture.

---

## 50. Current State Selection

For immediate physical action, Novi must select the best current state using the authoritative state-estimation and safety architecture.

Historical disagreement should not block urgent safe action unless the uncertainty itself is safety-critical.

---

## 51. Safety-Critical Conflict

If a conflict affects safety:

```text
conflict
 ↓
uncertainty increases
 ↓
safety policy
 ↓
conservative behavior
 ↓
additional sensing / stop / ask / retreat
```

The LLM cannot resolve a safety conflict by assertion alone.

---

## 52. Confidence Is Not a Permission

Even a high-confidence belief does not authorize an action that policy forbids.

```text
belief
 ↓
planning
 ↓
authorization
 ↓
safety
 ↓
execution
```

---

## 53. Belief Hysteresis

Rapid oscillation between contradictory beliefs should be controlled.

Example:

```text
open
closed
open
closed
```

caused by noisy sensing.

Use temporal filtering, confidence thresholds, persistence requirements and state-estimation methods appropriate to the variable.

---

## 54. Avoiding Stale-Belief Oscillation

A new weak observation should not automatically overturn a strongly supported current state, nor should strong current evidence be ignored because of historical entrenchment.

Revision should consider both evidence quality and freshness.

---

## 55. Unknown as a First-Class State

Novi must support:

```text
TRUE
FALSE
UNKNOWN
CONFLICTED
```

where appropriate.

This is safer than forcing binary truth values when evidence is incomplete.

---

## 56. Belief Confidence Calibration

Confidence should be calibrated against historical outcomes.

A system that repeatedly labels 90% confidence events correctly only 60% of the time has poor calibration.

Calibration metrics belong in observability/evaluation architecture.

---

## 57. Resource-Aware Revision

Deep conflict analysis can be deferred when not consequential.

Priority should favor:

1. safety-critical conflicts;
2. active-goal conflicts;
3. current-world conflicts;
4. high-impact knowledge conflicts;
5. background historical conflicts.

---

## 58. Offline Operation

Belief revision must operate locally without Wi-Fi, Bluetooth or cloud services.

Network synchronization is optional.

---

## 59. Testing Requirements

Test:

- conflicting sensors;
- stale observations;
- temporal contradictions;
- spatial contradictions;
- identity ambiguity;
- conflicting user statements;
- preference conflicts;
- causal conflicts;
- model-generated false claims;
- prompt-injected false evidence;
- memory poisoning;
- distributed conflicts;
- late events;
- duplicate events;
- entity merge/split;
- belief oscillation;
- unknown/conflicted states;
- dependency invalidation;
- privacy deletion;
- rollback;
- restart recovery;
- safety-critical uncertainty;
- offline operation.

---

## 60. Architectural Invariants

1. Evidence is never silently rewritten because a belief changes.
2. A historical fact can remain valid historically while being false currently.
3. Contradiction is a representable state.
4. Unknown is preferable to fabricated certainty.
5. Authority and confidence are separate concepts.
6. Authority is contextual, not universal.
7. Temporal and spatial scope must be considered before declaring contradiction.
8. Current authoritative state outranks stale evidence for current safety decisions.
9. LLM-generated claims are candidates, not canonical facts.
10. Conflicts are localized where practical.
11. Dependent beliefs are reevaluated when supporting claims change.
12. Revision is versioned and auditable.
13. Historical evidence remains available unless retention/privacy policy requires deletion.
14. Contradictory sources are not silently averaged.
15. Safety-critical conflicts trigger conservative behavior.
16. Belief revision cannot grant action authority.
17. Distributed reconciliation preserves lineage.
18. Local/offline operation remains functional.
19. Significant belief changes remain explainable from evidence.
20. Novi must be able to remain uncertain when evidence does not justify resolution.

---

## 61. Final Principle

> **Novi does not need to believe everything consistently at every moment; it needs to know what it has evidence for, what conflicts, what it currently believes, why it believes it, and how that belief can change when better evidence arrives.**

This makes contradiction a managed property of a continuously learning system rather than an error that Novi must hide.

## Research Basis

The architecture is informed by established belief-revision research, including AGM-style theory change, practical knowledge-base revision, work on iterated belief change, and research on inconsistent belief change. These traditions emphasize that belief states may need structured revision when new information conflicts with existing information and that the epistemic status of observations matters. citeturn0search0turn0search6turn0search7

Novi's implementation deliberately extends these ideas with provenance, sensor authority, temporal/spatial scope, embodied state estimation, immutable event history, privacy, safety boundaries and distributed local storage. The broader risk-management approach is also consistent with NIST's AI Risk Management Framework emphasis on managing AI risks throughout system design and operation. citeturn0search12
