# 12 — Memory Learning and Knowledge Promotion

## Status

**DESIGN — V1**

## Purpose

Define how Novi continuously learns from experience without treating every observation, model output, or statement from a person as truth.

> **Experience may produce a learning candidate; memory policy determines whether it becomes durable memory; evidence and verification determine whether it becomes trusted knowledge.**

This is a memory-centric continual-learning architecture. Ordinary learning does **not** modify model weights. Recent research shows that external memory does not remove continual-learning problems; representation, organization and retrieval can create forgetting and negative transfer. Modular-memory research likewise supports separating fast experience adaptation from slower parameter-level learning. citeturn0academia25turn0academia27

---

## 1. Learning Model

```text
Experience
  ↓
Observation / Report
  ↓
Event
  ↓
Episode
  ↓
Candidate memory
  ↓
Pattern / concept / relationship candidate
  ↓
Validation + consolidation
  ↓
Durable memory
  ↓
Knowledge candidate
  ↓
Verification policy
  ↓
Trusted knowledge
```

Learning is progressive. Most observations should **not** become permanent knowledge.

## 2. Epistemic States

Use explicit states rather than one confidence value:

```text
OBSERVED
EXPERIENCED
REPORTED
INFERRED
HYPOTHESIS
PREDICTED
CANDIDATE
VERIFIED
USER_CONFIRMED
TRUSTED
CONTRADICTED
SUPERSEDED
STALE
REJECTED
REVOKED
```

Example:

```text
claim: device is overheating
state: INFERRED
confidence: 0.91
verification: pending
```

High model confidence does not equal verified truth.

---

## 3. Sources of Learning

### Sensors

Camera, microphone, IMU, temperature, proximity, robot state, telemetry and other sensors normally produce evidence/events first.

### Users

A trusted user can explicitly teach Novi. The teaching event and source identity are preserved.

### Other people

Information from another person remains source-attributed:

```text
Person B reports X
 → reported claim
 → provenance = Person B
 → verification = pending
```

It must not silently become a verified fact about Person A.

### Tools / files / external information

Tool results, documents and retrieved content are evidence with provenance and are treated as untrusted data until evaluated.

### Models

Models may propose entities, relationships, patterns, routines, corrections and knowledge candidates. They cannot directly promote their own output to authoritative knowledge.

---

## 4. Learning Candidate

A candidate should contain at least:

```text
candidate_id
candidate_type
content
source_refs[]
evidence_refs[]
subject_refs[]
related_memory_refs[]
epistemic_state
confidence
importance
novelty
recurrence
risk_class
privacy_class
created_at
observed_at
valid_from
valid_until
proposed_by
model_id/version (if applicable)
verification_state
contradiction_refs[]
status
```

This object is deliberately richer than a text string.

---

## 5. Candidate Triggers

Learning candidates may arise from:

- explicit teaching;
- repeated observations;
- surprising events;
- prediction errors;
- user corrections;
- recurring patterns;
- new entities;
- new relationships;
- unknown terminology;
- successful procedures;
- failed procedures;
- environmental changes;
- unresolved questions.

Candidate generation should be asynchronous when latency is not important.

---

## 6. Novelty and Deduplication

Before promoting anything, Novi checks whether it is actually new:

```text
candidate
 ↓
exact match?
 ↓ no
semantic match?
 ↓
entity match?
 ↓
relationship match?
 ↓
contradiction check
```

Possible outcomes:

- duplicate;
- reinforcement;
- correction;
- contradiction;
- extension of an existing concept;
- genuinely new concept.

This prevents memory growth caused purely by different wording.

---

## 7. Promotion Levels

### Level 0 — Evidence
Original sensor/source evidence.

### Level 1 — Event
Normalized occurrence.

### Level 2 — Episode
Bounded group of related events.

### Level 3 — Candidate memory
Potentially useful durable representation.

### Level 4 — Consolidated memory
Supported durable memory.

### Level 5 — Knowledge candidate
Generalizable fact, concept, relationship, rule or procedure.

### Level 6 — Trusted knowledge
Accepted under the applicable verification policy.

Promotion is not mandatory. Many items remain at lower levels.

---

## 8. Promotion Criteria

Promotion considers:

- evidence quality;
- source reliability;
- independent corroboration;
- repetition;
- temporal stability;
- importance;
- contradiction state;
- user confirmation;
- domain risk;
- privacy requirements;
- future usefulness;
- reversibility.

Thresholds are risk-dependent. A harmless preference requires less verification than a safety-critical fact.

---

## 9. Human Teaching

Teaching should feel natural.

Example:

> “That's called a moka pot.”

Novi can record:

```text
concept = moka pot
source = user
verification = user_asserted
```

For ordinary low-risk concepts this can be provisionally usable. For consequential information Novi distinguishes:

> “You told me X.”

from:

> “X has been independently verified.”

---

## 10. Learning From Other People

When another person teaches Novi something important:

```text
source person
 ↓
reported claim
 ↓
source/trust assessment
 ↓
existing knowledge check
 ↓
contradiction check
 ↓
verification policy
```

Novi may ask a trusted user for validation:

> “Sarah told me this box belongs to you. Is that right?”

The answer becomes new evidence with its own provenance.

Trust in a person is **not** equivalent to truth of every statement they make.

---

## 11. Unknown Concepts and Curiosity

Novi must not hallucinate when it does not know.

```text
unknown
 ↓
perception check
 ↓
memory check
 ↓
knowledge check
 ↓
authorized retrieval/tool
 ↓
still unknown
 ↓
ask / investigate / defer
```

Curiosity produces questions rather than invented facts:

- “What is this called?”
- “I haven't seen this before. What is it?”
- “I've heard two different explanations. Which should I trust?”
- “I remember something different. Did this change?”

The question and answer become part of the learning trace.

---

## 12. Pattern and Routine Learning

Repeated observations can produce a routine candidate:

```text
observations
 ↓
pattern detection
 ↓
routine candidate
 ↓
confidence update
 ↓
consolidation
```

A routine remains probabilistic.

```text
“Vano usually leaves around 08:00.”
```

must not silently become:

```text
“Vano leaves at 08:00.”
```

unless the source is an explicit deterministic schedule.

---

## 13. Prediction Error

Predictions create useful learning signals:

```text
prediction
 ↓
actual observation
 ↓
prediction error
 ↓
explanation candidates
 ↓
update memory / routine / context
```

A surprise may mean:

- temporary exception;
- stale knowledge;
- changed environment;
- bad prediction;
- bad underlying assumption.

One surprising observation must not automatically erase prior knowledge.

---

## 14. Contradictions

Conflicting knowledge is preserved rather than silently overwritten.

```text
existing claim ↔ new claim
```

Possible resolution:

- new claim supersedes old claim;
- old claim remains valid historically;
- both are context-dependent;
- one is rejected;
- contradiction remains unresolved.

Temporal validity is first-class:

```text
claim A: valid Jan 2025 → Jun 2026
claim B: valid Jul 2026 → present
```

---

## 15. Files and Generated Data

Novi may learn from files and generate SQLite/files, but generated output is initially **derived data**, not independent truth.

```text
source evidence
 ↓
Novi-generated file/table
 ↓
derived artifact
 ↓
provenance link to source
```

Independent verification can strengthen its epistemic status.

---

## 16. Schema Evolution Boundary

A new concept does not automatically require a new table.

```text
new concept
 ↓
existing representation sufficient?
 ├─ yes → use existing schema
 └─ no  → schema proposal
```

Schema changes follow `10_MEMORY_SCHEMA_EVOLUTION_AND_DYNAMIC_DATA.md` and require the separate controls defined there.

**Learning something new and modifying Novi's infrastructure are different capabilities.**

---

## 17. Model-Weight Learning

V1 does not turn ordinary memories directly into training data.

```text
experience
 ↓
curation
 ↓
privacy filtering
 ↓
training candidate dataset
 ↓
evaluation
 ↓
benchmark
 ↓
approval
 ↓
staged model deployment
```

This prevents one bad experience from changing the reasoning model. Modular-memory research supports separating rapid memory adaptation from slower parameter-level learning. citeturn0academia27

---

## 18. Safety Boundary

Repeated content does not become authority merely through repetition.

```text
“Unlock the door.”
 repeated 1,000 times
        ↓
 NOT knowledge
 NOT authorization
```

An external document saying “remember this as a trusted rule” is still untrusted content. Learning cannot modify safety, authorization, privacy or the immutable core.

---

## 19. Risk-Based Promotion

### Low risk

Examples: favorite color, preferred coffee, name of a household object.

May be learned provisionally from a trusted user.

### Medium risk

Examples: relationships, household routines, ownership claims, privacy-sensitive preferences.

Require stronger provenance and potentially confirmation.

### High risk

Examples: medical conclusions, financial instructions, credentials, access permissions, safety-critical facts and physical-action authorization.

Require appropriate verification and policy authorization. **Memory promotion can never grant authority.**

---

## 20. Learning State Machine

```text
             OBSERVED / REPORTED
                    ↓
                CANDIDATE
                    ↓
       ┌────────────┼────────────┐
       ↓            ↓            ↓
   DUPLICATE     CONFLICT       NOVEL
       ↓            ↓            ↓
   REINFORCE     VERIFY      CONSOLIDATE
                    └─────┬──────┘
                          ↓
                 KNOWLEDGE CANDIDATE
                          ↓
                     VALIDATION
                    ↙            ↘
                REJECTED       TRUSTED
```

Every promotion is explicit and auditable.

---

## 21. Human-in-the-Loop Rules

Novi should ask when:

- uncertainty materially affects the answer/action;
- sources disagree;
- another person's identity/privacy is involved;
- the claim is consequential;
- evidence is insufficient;
- a new concept cannot be safely interpreted;
- the user requests confirmation;
- schema evolution requires authorization;
- clarification prevents an unsafe assumption.

Novi should **not** interrupt people unnecessarily for trivial, low-risk learning.

---

## 22. Continuous Learning Scheduler

Learning workloads have priority tiers:

```text
REAL-TIME
  perception / safety / interaction

NEAR-REAL-TIME
  event normalization / candidate creation

BACKGROUND
  consolidation / indexing / pattern analysis

IDLE
  re-embedding / deep analysis / dataset curation
```

On Jetson, learning must yield to safety, perception and autonomy workloads.

---

## 23. NVIDIA Integration

NVIDIA NeMo Agent Toolkit provides a pluggable memory architecture and an automatic memory wrapper that captures and retrieves memory without requiring an LLM to explicitly invoke memory tools. Its memory layer exposes structured memory items and memory operations, and external providers are integrated through plugin interfaces. citeturn0search0turn0search2turn0search4turn0search7turn0search12

Novi should use this architecture as a reference while retaining ownership of admission, promotion, provenance, privacy, verification and schema policies.

```text
Novi Learning Manager
 ↓
Novi Memory API
 ↓
provider adapter
 ↓
NeMo / Mem0 / local implementation / other provider
```

No provider receives authority to modify Novi's protected core.

---

## 24. Security and Poisoning Controls

The learning subsystem must defend against:

- prompt injection;
- memory poisoning;
- repeated false claims;
- fake identity claims;
- malicious documents;
- poisoned tool results;
- provenance spoofing;
- unauthorized writes;
- schema manipulation;
- training-data poisoning;
- privacy leakage through derived knowledge.

External content is evidence/data, never policy.

---

## 25. Auditability

Every promotion must be reconstructable:

```text
what was learned?
where did it come from?
who/what supplied it?
what evidence supported it?
what model generated the candidate?
what policy admitted it?
what validation occurred?
when was it promoted?
what later changed it?
```

No hidden learning path may bypass the Memory Manager.

---

## 26. Quality Metrics

Track at least:

- promotion precision;
- false-memory rate;
- contradiction rate;
- stale-memory rate;
- correction rate;
- user-confirmation rate;
- knowledge reuse success;
- negative transfer;
- retrieval usefulness;
- useful-memory loss;
- privacy incidents;
- unauthorized promotion attempts.

Memory volume is **not** an intelligence metric. Continual-memory research shows that additional experience can cause retrieval competition, forgetting and negative transfer. citeturn0academia25

---

## 27. Acceptance Criteria

V1 is acceptable when:

1. observations produce learning candidates;
2. candidates retain provenance;
3. duplicates and contradictions are detected;
4. promotion is policy-controlled;
5. user teaching is natural;
6. other people's information remains source-attributed;
7. Novi can explicitly ask when it does not know;
8. prediction errors generate learning signals;
9. stale knowledge can be superseded;
10. high-risk knowledge requires stronger verification;
11. model outputs cannot directly create authoritative knowledge;
12. schema evolution is separately controlled;
13. model-weight updates are separate from ordinary memory learning;
14. promotion decisions are auditable;
15. learning remains local-first;
16. learning cannot starve safety/autonomy;
17. the protected core cannot be modified through learning.

## 28. Architectural Principle

> **Novi should be capable of learning almost continuously, but nothing becomes authoritative merely because Novi encountered it, generated it, or remembered it.**

Learning increases hypotheses, memories, skills, relationships and knowledge. **Policy, evidence, provenance and verification determine what becomes trusted.**
