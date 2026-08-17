# 55 — Memory Knowledge Contextual Truth and Fact Model

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define what Novi means by a **fact**, how facts are scoped by time, place, entity, observer, source and situation, and how Novi distinguishes objective observations from contextual truths, personal preferences, hypotheses, disputed claims and model-generated statements.

The objective is to prevent Novi from turning context-dependent information into universal truth, while still allowing it to reason effectively about a dynamic physical and social world.

## Research Basis

The design is informed by established work on contextual knowledge representation, temporal knowledge bases, temporal knowledge graphs, robot context models and epistemic contextualism. Research shows that real-world knowledge frequently requires explicit temporal, spatial and contextual qualification, and that temporal knowledge bases must be able to represent changing and conflicting facts rather than assuming a single timeless value. citeturn0search0turn0search2turn0search4turn0search8

## Core Principle

> **A fact is not merely a sentence that sounds true. It is a claim whose subject, predicate, scope, time, context, provenance and evidentiary status are sufficiently defined for the intended use.**

---

## 1. Fact vs Claim

A **claim** is an assertion that can be evaluated.

A **fact** is a claim that has met the applicable evidence and validation requirements for its defined scope.

```text
CLAIM
  ↓
evaluation
  ↓
FACT within defined scope
```

Not every claim becomes a fact.

---

## 2. No Universal Fact Assumption

Novi must not assume that every fact is:

```text
universal
permanent
context-free
observer-independent
```

Many facts are inherently scoped.

Examples:

```text
The door is open.
→ current physical state

The door was open at 14:00.
→ historical state

This room is cold for Alice.
→ subjective/contextual statement

The robot is in the kitchen.
→ spatial state
```

---

## 3. Fact Dimensions

Important facts should support explicit dimensions such as:

```text
subject
predicate
object/value
valid_time
observation_time
location
context
source
provenance
confidence/uncertainty
scope
status
```

Not every fact needs every field, but the semantic model must support them.

---

## 4. Fact Classes

Novi should distinguish at least:

```text
OBSERVATIONAL_FACT
PHYSICAL_FACT
TEMPORAL_FACT
SPATIAL_FACT
RELATIONAL_FACT
USER_FACT
PREFERENCE
SOCIAL_ASSERTION
SCIENTIFIC_KNOWLEDGE
INFERRED_FACT
CAUSAL_FACT
HYPOTHESIS
DISPUTED_CLAIM
COUNTERFACTUAL
SIMULATION_RESULT
UNKNOWN
```

---

## 5. Observational Fact

An observational fact describes what a trusted observation established within its measurement limits.

Example:

```text
At 10:03:12, LiDAR detected an obstacle at position X.
```

This does not necessarily establish what the obstacle is.

---

## 6. Physical Fact

A physical fact describes a validated state of the physical world.

Example:

```text
The robot battery was at 42% at time T.
```

The fact remains historical even after the battery changes.

---

## 7. Temporal Fact

A temporal fact explicitly represents validity in time.

```text
fact:
Novi was in Room A
valid_from = T1
valid_until = T2
```

Temporal representation is required for dynamic entities.

---

## 8. Spatial Fact

Spatial facts should include the relevant frame/reference where needed.

```text
object_42
located_in
kitchen
at time T
```

A spatial fact is not automatically current merely because it was once true.

---

## 9. Relational Fact

Relations can describe:

- ownership;
- containment;
- proximity;
- association;
- identity;
- interaction;
- dependency;
- causal relationship.

Relationships may themselves have temporal validity.

---

## 10. User-Specific Fact

Some information is true specifically about a user or household context.

Example:

```text
User prefers the bedroom cooler than the living room.
```

This should not become a universal statement about ideal temperature.

---

## 11. Preference Is Not Fact

Preferences should normally be represented separately from objective physical facts.

```text
"The room is 21°C."
→ physical measurement

"I like the room at 21°C."
→ preference
```

Both may be valid, but they have different semantics.

---

## 12. Subjective Facts

Some statements describe an individual's experience or report.

Example:

```text
User reports feeling cold.
```

This can be a valid fact about the user's report without establishing an objective environmental temperature.

---

## 13. Objective vs Subjective

Novi should preserve the distinction:

```text
OBJECTIVE CLAIM
What is true about the measured/validated world?

SUBJECTIVE CLAIM
What does a person report, prefer or experience?
```

Subjective information must not be downgraded merely because it is subjective; it simply answers a different question.

---

## 14. Observer-Relative Facts

Some facts depend on an observer or reference frame.

Examples:

```text
visible_to(camera_A)
heard_by(microphone_B)
known_by(user_A)
perceived_as(object_type_X)
```

Observer-relative information must retain its observer/source.

---

## 15. Perspective

Different agents can possess different information about the same world state.

```text
Novi believes X
User believes Y
Sensor evidence supports Z
```

Novi should represent the perspectives rather than forcing them into one unsupported universal claim.

---

## 16. Knowledge vs Belief

```text
BELIEF
a proposition Novi currently accepts to some degree

KNOWLEDGE
a sufficiently supported proposition under defined scope
```

Knowledge requires stronger evidence and provenance than a temporary belief.

---

## 17. Fact vs Model Prediction

```text
Fact:
The door was open at 14:00.

Prediction:
The door will probably be open at 14:05.
```

Predictions must never be stored as historical facts before verification.

---

## 18. Fact vs Hypothesis

```text
Observation:
object detected

Hypothesis:
it may be a person

Fact:
validated person identity within required confidence/scope
```

The system must retain the distinction throughout the pipeline.

---

## 19. Fact vs Counterfactual

```text
Fact:
Novi used route A.

Counterfactual:
Route B might have been faster.
```

Counterfactual reasoning must never create a historical fact.

---

## 20. Fact vs Simulation

```text
REAL FACT
physical world observation

SIMULATION RESULT
result within a simulated environment
```

Simulation can support planning and learning but cannot silently become physical history.

---

## 21. Fact vs Narrative

A generated narrative may summarize multiple facts.

```text
facts
 ↓
summary
```

The narrative is not itself the primary evidence.

Every consequential statement should be traceable to underlying facts/evidence.

---

## 22. Context Object

A context may include:

```text
who
what
where
when
under_which_conditions
from_which_perspective
for_which_task
```

Context qualifies interpretation without necessarily changing the underlying physical event.

---

## 23. Context Hierarchy

Contexts may be nested.

```text
world
 └── country
      └── city
           └── building
                └── room
                     └── current task
```

Context inheritance must be explicit rather than assumed.

---

## 24. Contextual Truth

A statement can be true within one context and false outside it.

Example:

```text
"The robot is indoors."
```

can be true for a given time interval and false later.

Similarly:

```text
"The route is safe."
```

may be true only under specific environmental conditions.

---

## 25. Scope

Every contextual fact should define its applicable scope where relevant.

Possible scopes:

```text
GLOBAL
HOUSEHOLD
ROOM
LOCATION
TASK
PERSON
DEVICE
TIME_INTERVAL
ENVIRONMENT
MODEL_VERSION
```

---

## 26. Scope Must Not Be Over-Generalized

A fact established in one scope must not automatically propagate to a broader scope.

```text
works in kitchen
 ≠
works everywhere
```

```text
user prefers X today
 ≠
user always prefers X
```

---

## 27. Temporal Validity

Facts should support:

```text
valid_from
valid_until
observed_at
recorded_at
```

These times can differ.

Example:

```text
world state occurred at T1
Novi observed it at T2
Novi stored it at T3
```

---

## 28. Event Time vs Ingestion Time

Event time describes when the world event occurred.

Ingestion time describes when Novi received the information.

They must not be conflated.

---

## 29. Historical Truth

A fact can remain historically true after becoming currently false.

```text
Tuesday:
chair was in Room A

Thursday:
chair is in Room B
```

Both facts can coexist with different validity intervals.

---

## 30. Current Truth

Current-state queries require current validity evaluation.

```text
historical fact
 ↓
validity check
 ↓
current observation if necessary
 ↓
current state
```

Memory retrieval alone does not establish current physical state for safety-critical use.

---

## 31. Reverification

Reverification should be required when:

- the fact is highly time-sensitive;
- the environment may have changed;
- the fact is safety-relevant;
- source reliability degraded;
- contradictory evidence exists;
- the cost of being wrong is high.

---

## 32. Fact Status

Useful statuses include:

```text
PROVISIONAL
SUPPORTED
VERIFIED
CURRENT
HISTORICAL
STALE
SUPERSEDED
DISPUTED
RETRACTED
UNKNOWN
```

Status is distinct from truth itself.

---

## 33. Disputed Facts

When credible sources disagree:

```text
claim A
claim B
     ↓
DISPUTED
```

Novi should preserve both claims and their provenance until resolution.

---

## 34. Retraction

If a previously accepted claim is shown to be false:

```text
fact
 ↓
new evidence
 ↓
RETRACTED
```

The historical record should preserve that the claim existed and why it was retracted, subject to privacy/retention policy.

---

## 35. Identity Context

Identity facts require especially careful scoping.

```text
person_17
possibly = person_A
```

must not become:

```text
person_17 = person_A
```

until the identity policy is satisfied.

---

## 36. Ownership Context

Ownership can be temporal and contextual.

```text
object_42
owned_by person_A
valid T1–T2
```

A historical ownership fact does not necessarily describe current ownership.

---

## 37. Location Context

Locations may use multiple representations:

- room;
- address;
- GPS coordinates;
- map frame;
- semantic region;
- route segment.

The coordinate/reference frame must be preserved where precision matters.

---

## 38. Environmental Context

Facts may depend on:

- temperature;
- lighting;
- weather;
- noise;
- occupancy;
- battery state;
- robot operating mode.

Example:

```text
camera detection reliability = high
when lighting > threshold
```

This is a contextual capability fact, not a universal property of the camera.

---

## 39. Task Context

A statement can be relevant to one task and irrelevant to another.

Example:

```text
"Chair usually sits beside desk."
```

may help object retrieval but should not be used as a collision-avoidance guarantee.

---

## 40. Scientific / General Knowledge

General knowledge should retain:

- source;
- scope;
- date/version;
- domain;
- uncertainty;
- applicability conditions.

Scientific claims can also be revised when evidence changes.

---

## 41. World Model vs Language Model

The language model must not be treated as the authoritative world database.

```text
LLM
 ↓
reasoning / language

canonical world knowledge
 ↓
structured memory / knowledge system
```

The LLM can query and reason over the canonical system.

---

## 42. Fact Promotion

A claim may progress through:

```text
ASSERTION
 ↓
OBSERVATION
 ↓
SUPPORTED CLAIM
 ↓
VERIFIED FACT
 ↓
KNOWLEDGE
```

Promotion requirements depend on claim type and consequence.

---

## 43. No Universal Verification Threshold

A harmless conversational fact and a safety-critical physical fact should not require identical validation.

```text
low consequence
 → lower validation burden

high consequence
 → stronger evidence / current verification
```

The safety architecture controls final action requirements.

---

## 44. Contextual Querying

Queries should support context.

Examples:

```text
Where is the chair now?
Where was the chair yesterday?
Where does the chair usually stay?
Where did Novi last observe the chair?
Is the chair currently safe to navigate around?
```

These are different queries over related knowledge.

---

## 45. Query-Time Truth Evaluation

Retrieval should evaluate:

```text
scope
 ↓
time
 ↓
context
 ↓
source
 ↓
validity
 ↓
conflict
 ↓
uncertainty
```

Only then should the result be used as current knowledge.

---

## 46. Contradictory but Contextually Valid Facts

Two facts can both be valid when contexts differ.

```text
Room A: 20°C
Room B: 24°C
```

No contradiction exists if the location context is represented.

Likewise:

```text
Tuesday: object in Room A
Thursday: object in Room B
```

is not contradictory if time is represented.

---

## 47. Genuine Contradiction

A genuine contradiction occurs when two claims assert incompatible values over materially overlapping scope and validity intervals.

```text
same entity
same property
same context
overlapping time
value A ≠ value B
```

This should enter conflict resolution rather than being silently merged.

---

## 48. Open-World Assumption

Absence of evidence should normally mean:

```text
UNKNOWN
```

not:

```text
FALSE
```

Example:

```text
No memory says object X is in Room B.
```

does not prove:

```text
Object X is not in Room B.
```

unless a closed-world rule explicitly applies.

---

## 49. Closed-World Contexts

Some controlled subsystems may use closed-world assumptions.

Example:

```text
hardware inventory
```

may define a complete authoritative set.

The closed-world assumption must be explicit and scoped.

---

## 50. Negative Facts

Negative facts require provenance too.

```text
No object detected in region X at time T.
```

is different from:

```text
Object X does not exist.
```

Detection limits must be considered.

---

## 51. Unknown as First-Class State

Novi should support:

```text
TRUE
FALSE
UNKNOWN
DISPUTED
NOT_APPLICABLE
```

Unknown is not an error condition.

---

## 52. Fact Confidence

Fact status must be combined with the uncertainty architecture.

```text
VERIFIED
 +
low measurement uncertainty
 +
strong provenance
```

supports stronger use than:

```text
PROVISIONAL
 +
weak source
```

---

## 53. Fact Reliability and Source Reliability

Source reliability is evidence about the source.

Fact confidence evaluates the specific claim.

A highly reliable source can still produce an uncertain claim under difficult conditions.

---

## 54. Fact Lineage

Every important fact should retain lineage to:

```text
source
 ↓
observation/assertion
 ↓
processing
 ↓
validation
 ↓
fact
```

This follows document 51.

---

## 55. Fact Revision

When new evidence changes a fact:

```text
fact v1
 ↓
new evidence
 ↓
fact v2
```

The historical version remains auditable.

---

## 56. Fact Merging

Compatible facts may be merged into a stronger representation only when their contexts are compatible.

```text
observation A
observation B
 ↓
consolidated fact
```

Original lineage must remain available.

---

## 57. Fact Splitting

If a previously broad fact is discovered to contain multiple contexts, it may be split.

Example:

```text
"User prefers low light"
```

may become:

```text
bedroom → low light at night
living room → normal light during day
```

The narrower representation should not erase the original evidence.

---

## 58. Context Learning

Novi may learn contextual rules from repeated evidence:

```text
context
 ↓
repeated observations
 ↓
pattern
 ↓
contextual knowledge
```

The learned rule remains scoped unless evidence supports generalization.

---

## 59. Context Drift

Contexts can change.

Examples:

- furniture rearrangement;
- household routine change;
- new hardware;
- new occupant;
- seasonal environment;
- changed user preference.

Contextual knowledge should therefore support staleness and revalidation.

---

## 60. Context Conflict

If context itself is uncertain:

```text
unknown location
unknown time
uncertain identity
```

facts depending on that context must carry corresponding uncertainty.

---

## 61. Multi-Agent Context

Different processes/agents may have different observations.

```text
agent A observed X
agent B observed Y
```

The canonical memory system should retain source identity and merge only through defined synchronization/conflict rules.

---

## 62. Privacy

Context can be highly sensitive.

Examples:

- location;
- household routines;
- identity;
- private conversations;
- personal preferences.

Context must inherit applicable privacy and access controls.

---

## 63. Security

Context manipulation can change the meaning of a fact.

An attacker who changes:

```text
location
identity
user
permission context
```

may effectively change the interpretation of an otherwise valid statement.

Context integrity is therefore security-sensitive.

---

## 64. Offline Operation

Fact evaluation and contextual reasoning must work locally without Wi-Fi or Bluetooth.

External synchronization may add knowledge but must not be required to determine local physical context.

---

## 65. Hardware Context

Physical facts may depend on hardware state.

Examples:

```text
camera operational
LiDAR operational
GPS unavailable indoors
thermal sensor degraded
battery low
```

The world model should distinguish environmental facts from sensor-capability facts.

---

## 66. Sensor Perspective

A sensor's inability to observe something is not proof that the thing does not exist.

```text
camera cannot see object
```

means:

```text
object not observed by camera
```

not:

```text
object does not exist
```

---

## 67. Fact Use Policy

Before using a fact, Novi should consider:

```text
Is it relevant?
Is it within scope?
Is it temporally valid?
Is the source trustworthy?
Is it contradicted?
Is uncertainty acceptable for this task?
Is current verification required?
```

---

## 68. Safety-Critical Fact Use

For safety-critical decisions:

```text
historical/contextual fact
 ↓
current verification where required
 ↓
safety validation
 ↓
action authorization
```

A memory cannot override real-time safety sensing.

---

## 69. Explanation

Novi should be able to explain context:

> "That was true yesterday in the kitchen, but I don't have evidence that it is still true now."

This is preferable to incorrectly presenting historical knowledge as current fact.

---

## 70. Fact Audit Questions

For an important fact Novi should be able to answer:

```text
What is the claim?
Who/what is it about?
When was it valid?
Where was it valid?
Who/what observed or asserted it?
What evidence supports it?
What context applies?
Has it been contradicted?
Is it still current?
What would cause it to become invalid?
```

---

## 71. Testing Requirements

Test:

- temporal facts;
- spatial facts;
- user-specific facts;
- subjective reports;
- preferences;
- observer-relative facts;
- conflicting facts;
- context inheritance;
- context changes;
- historical/current queries;
- stale knowledge;
- negative facts;
- open-world behavior;
- explicit closed-world contexts;
- identity uncertainty;
- source uncertainty;
- simulation/real separation;
- distributed contexts;
- privacy filtering;
- context tampering;
- offline operation;
- safety-critical reverification.

---

## 72. Architectural Invariants

1. A claim is not automatically a fact.
2. Facts have scope appropriate to their meaning.
3. Time is explicit for changing facts.
4. Historical truth is not automatically current truth.
5. Spatial context is explicit where relevant.
6. Observer-relative claims retain their observer/source.
7. Preferences are distinct from objective facts.
8. Subjective reports are facts about the report, not automatically about objective reality.
9. Predictions and counterfactuals are not historical facts.
10. Simulation results remain distinct from physical facts.
11. Context must not be silently generalized.
12. Absence of evidence normally means UNKNOWN, not FALSE.
13. Closed-world assumptions must be explicit and scoped.
14. Contradictory claims retain provenance and context.
15. Context uncertainty propagates to dependent claims.
16. Important facts retain lineage.
17. Fact status is distinct from truth and confidence.
18. Safety-critical use may require current verification.
19. Context integrity is security-sensitive.
20. Core contextual fact reasoning works offline.
21. The LLM is not the canonical world database.
22. No generated narrative may manufacture a fact.

---

## 73. Final Principle

> **Novi must represent truth with enough context to know what is true, for whom, where, when, under which conditions, according to what evidence, and for what purpose—rather than treating every true statement as a timeless universal fact.**

This makes contextual truth a first-class component of Novi's world model and connects factual memory with temporal validity, provenance, uncertainty, source reliability, belief revision and safe decision-making.
