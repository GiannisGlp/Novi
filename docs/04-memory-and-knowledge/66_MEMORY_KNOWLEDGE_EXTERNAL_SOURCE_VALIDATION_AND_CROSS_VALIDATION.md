# 66 — Memory Knowledge External Source Validation and Cross-Validation

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi evaluates information obtained from external sources before that information can influence memory, knowledge, learning, planning, or consequential decisions.

This document covers source authenticity, provenance, corroboration, independence, conflict detection, ground truth, temporal validity, source-specific reliability, adversarial content, uncertainty, abstention, and revalidation.

It applies to information obtained from the Internet, APIs, documents, other agents, other Novi instances, removable media, connected devices, user-provided material, and any other source outside the immediately trusted local state.

## Research Basis

This design is informed and cross-validated against:

- **NIST AI RMF / Generative AI Profile** — emphasizes documenting data origin and content lineage, testing data/content flows, understanding upstream dependencies, and assessing accuracy, quality, reliability and authenticity against known ground truth and multiple evaluation methods. citeturn0search40
- **W3C PROV** — establishes provenance as information about entities, activities and agents involved in producing information and provides consistency/validity concepts for provenance records. citeturn0search0turn0search1
- **OWASP GenAI Security Project** — identifies external data as a significant poisoning risk and indirect prompt injection as a threat through websites, files and other external content; it recommends trust boundaries, least privilege and validation rather than treating retrieved content as trusted instructions. citeturn0search2turn0search3turn0search4

These sources inform the architecture; they do not by themselves define Novi's implementation or authority model.

---

## 1. Core Principle

> **External information is evidence with provenance, not truth by default.**

No external source may become authoritative merely because it is:

- online;
- popular;
- highly ranked by a search engine;
- returned by a trusted API;
- written confidently;
- produced by an AI system;
- repeated many times;
- supplied by another agent;
- stored in a document;
- accompanied by a citation.

---

## 2. Validation Is Multi-Dimensional

Novi should not reduce validation to a single score.

Evaluation may consider:

```text
identity
provenance
authenticity
integrity
reliability
independence
freshness
context match
specificity
completeness
corroboration
contradiction
known ground truth
uncertainty
security risk
privacy constraints
```

---

## 3. Validation vs Truth

Validation determines whether information is sufficiently supported for a particular purpose.

```text
VALIDATED FOR PURPOSE X
        ≠
UNIVERSALLY TRUE
```

A source may be sufficiently reliable for a low-risk task but insufficient for a safety-critical decision.

---

## 4. Source Identity

For each external source, Novi should capture where possible:

- source identifier;
- publisher/provider;
- endpoint/document URI or equivalent locator;
- source type;
- acquisition method;
- timestamp;
- version/revision;
- cryptographic digest where appropriate;
- transport/security metadata;
- claimed author/issuer;
- provenance chain.

Unknown source identity lowers trust and may prohibit promotion.

---

## 5. Authenticity

Authenticity asks:

> **Did this information actually originate from the claimed source?**

Where appropriate, Novi should use:

- authenticated transport;
- signatures;
- trusted certificates/keys;
- signed metadata;
- content hashes;
- verified provider identities;
- trusted local credentials.

Authenticity does not establish truth.

```text
AUTHENTIC SOURCE
      ≠
CORRECT CLAIM
```

---

## 6. Integrity

Integrity asks whether content changed unexpectedly between production and ingestion.

If integrity cannot be established where integrity matters, the item should be treated as unverified or rejected according to policy.

---

## 7. Provenance

Every external claim that enters durable memory should retain provenance sufficient to answer:

```text
Where did it come from?
When was it obtained?
Who/what produced it?
How was it transformed?
What validation was performed?
What evidence supported promotion?
```

W3C PROV explicitly treats provenance as useful for assessing information quality, reliability and trustworthiness. citeturn0search0

---

## 8. Acquisition Provenance

Novi should distinguish:

```text
SOURCE TIME
when source produced/published the information

ACQUISITION TIME
when Novi obtained it

PROCESSING TIME
when Novi transformed/evaluated it

USE TIME
when Novi relied on it
```

These timestamps must not be silently conflated.

---

## 9. Content Transformation

If external content is transformed:

```text
source document
 ↓
parser
 ↓
normalizer
 ↓
extractor
 ↓
summary
 ↓
claim
```

lineage must preserve the relationship between the derived claim and its upstream evidence.

---

## 10. Source Reliability

Source reliability is inherited from document 54 and should be evaluated specifically for:

- source type;
- topic/domain;
- operating conditions;
- historical performance;
- freshness;
- known failure modes.

A source should not receive a universal trust score.

---

## 11. Independence

Multiple sources are useful only to the extent that they provide independent evidence.

```text
Source A
Source B
Source C
```

does not automatically mean three confirmations.

If all reproduce the same upstream source, they may represent one evidence lineage.

---

## 12. Correlated Evidence

Novi should identify likely common dependencies:

```text
Article A → database X
Article B → database X
Article C → article A
```

These should not be counted as independent corroboration.

---

## 13. Corroboration

Corroboration should preferentially come from sources that are:

- independent;
- directly relevant;
- temporally aligned;
- contextually compatible;
- independently produced;
- themselves sufficiently trustworthy.

Corroboration increases support; it does not guarantee truth.

---

## 14. Direct vs Derived Evidence

Evidence should be classified as:

```text
DIRECT
source directly measured/reported X

DERIVED
X was inferred from source data

SECONDARY
source reports another source

TERTIARY
source summarizes multiple prior sources
```

Evidence depth affects validation requirements.

---

## 15. Ground Truth

Where known ground truth exists, Novi should prefer it for validation.

Examples include:

- calibrated sensor measurements;
- verified physical outcomes;
- authoritative system state;
- controlled experiments;
- independently verified records.

NIST specifically recommends evaluating accuracy, quality, reliability and authenticity against known ground truth where available. citeturn0search40

---

## 16. No Ground Truth

When ground truth is unavailable, Novi must represent uncertainty rather than manufacture certainty.

Possible result:

```text
SUPPORTED
PLAUSIBLE
CONTESTED
UNVERIFIED
UNKNOWN
```

---

## 17. Cross-Validation Is Purpose-Dependent

The required validation strength depends on consequence.

```text
LOW RISK
single credible source may be sufficient

MEDIUM RISK
corroboration often preferred

HIGH RISK
independent evidence / authoritative state / direct verification

SAFETY CRITICAL
current trusted sensing and safety systems take precedence
```

These are policy categories, not universal numerical thresholds.

---

## 18. Current Physical State

External information must not override current trusted physical sensing when the question concerns immediate physical safety or state.

Example:

```text
web page says bridge is open
        ↓
NOT sufficient for robot navigation
        ↓
current local perception/state required
```

---

## 19. Temporal Validation

A source may have been accurate when published but stale now.

Validation should evaluate:

- source timestamp;
- publication/update time;
- acquisition time;
- expected rate of change;
- current contradictions.

Temporal validity follows document 53.

---

## 20. Context Validation

A claim may be true in one context and false in another.

Novi should validate:

```text
who
what
where
when
under what conditions
```

before generalizing.

---

## 21. Scope Preservation

Never silently generalize:

```text
works in environment A
       ↓
works everywhere
```

or:

```text
true for person X
       ↓
true for everyone
```

The original scope must survive ingestion.

---

## 22. Contradiction Detection

If sources disagree:

```text
Source A → X
Source B → not-X
```

Novi should preserve both claims and evaluate:

- temporal differences;
- contextual differences;
- source reliability;
- independence;
- directness;
- provenance;
- possible source corruption.

---

## 23. Contradiction Is Not Automatically Error

Two statements may differ because:

- the world changed;
- the sources describe different contexts;
- one describes a forecast;
- one reports an observation;
- one is historical;
- one is erroneous.

Resolution requires context.

---

## 24. Source Ranking Is Not Validation

Search-engine ranking, popularity, engagement or retrieval rank may help select candidates but must not be interpreted as evidence of truth.

```text
HIGH SEARCH RANK
      ≠
HIGH EVIDENTIARY QUALITY
```

---

## 25. Citation Is Not Validation

A claim containing a citation is not automatically validated.

Novi must evaluate whether the cited source actually supports the claim.

---

## 26. AI-Generated Sources

AI-generated information should be classified as generated/derived content.

```text
LLM says X
    ↓
claim
    ↓
requires evidence appropriate to purpose
```

An AI model cannot independently validate its own unsupported assertion.

---

## 27. Self-Corroboration Prohibition

Novi must prevent:

```text
model generates X
 ↓
Novi stores X
 ↓
retrieves X later
 ↓
counts X as independent confirmation
```

A derived claim cannot become independent evidence merely by being persisted.

---

## 28. External Agent Claims

Claims from another AI agent or Novi instance should include:

- agent identity;
- model/version where relevant;
- source evidence;
- generation time;
- provenance;
- confidence/uncertainty;
- authority scope.

Agent identity alone does not establish truth.

---

## 29. User-Provided Information

User-provided information can be highly valuable but should retain its source class.

For example:

```text
USER REPORT
```

should not silently become:

```text
INDEPENDENT PHYSICAL OBSERVATION
```

The distinction matters for future reasoning.

---

## 30. Documents and Files

Documents may contain:

- authoritative facts;
- outdated information;
- opinions;
- instructions;
- malicious content;
- embedded metadata;
- hidden prompt injection.

They must pass the same source validation boundary before influencing durable knowledge.

OWASP identifies indirect prompt injection through external files and other content as a specific threat. citeturn0search3turn0search4

---

## 31. Web Content

Web content is inherently dynamic and heterogeneous.

Novi should preserve:

- URL/locator;
- retrieval timestamp;
- publication/update timestamp where available;
- page identity;
- extracted claim;
- relevant passage/structured evidence;
- source provenance.

A later retrieval may produce different content from the same locator.

---

## 32. APIs

API responses should record:

- provider;
- endpoint;
- request context where appropriate;
- response time;
- version;
- authentication context;
- response integrity;
- transformation pipeline.

A trusted transport does not make API content infallible.

---

## 33. Sensor Sources

Physical sensors should be validated using:

- calibration;
- health;
- environmental conditions;
- measurement uncertainty;
- cross-sensor agreement;
- known failure modes.

Document 54 governs source reliability; this document governs external-evidence validation across source boundaries.

---

## 34. Security Screening

Before external content reaches memory or an LLM context, evaluate for:

- malicious instructions;
- prompt injection;
- malformed data;
- unexpected file types;
- executable content;
- suspicious metadata;
- poisoning indicators;
- oversized/unbounded input;
- unauthorized content.

Security screening does not replace epistemic validation.

---

## 35. Data Poisoning

External information can deliberately manipulate future behavior or knowledge.

OWASP identifies data and model poisoning as an integrity threat and specifically notes elevated risk from external data sources. citeturn0search2

Novi should therefore separate:

```text
CONTENT ACCEPTANCE
      ≠
KNOWLEDGE PROMOTION
```

---

## 36. Prompt Injection Boundary

External content may contain text that looks like instructions.

```text
EXTERNAL CONTENT
      ↓
UNTRUSTED DATA
```

not:

```text
EXTERNAL CONTENT
      ↓
SYSTEM INSTRUCTION
```

OWASP explicitly identifies indirect prompt injection through external sources and recommends trust boundaries and least privilege. citeturn0search3turn0search4

---

## 37. Validation Pipeline

Conceptual pipeline:

```text
INGEST
  ↓
IDENTIFY SOURCE
  ↓
VERIFY INTEGRITY / AUTHENTICITY
  ↓
CAPTURE PROVENANCE
  ↓
CLASSIFY CONTENT
  ↓
SECURITY SCREEN
  ↓
CHECK SCOPE / TIME / CONTEXT
  ↓
ASSESS SOURCE RELIABILITY
  ↓
FIND INDEPENDENT EVIDENCE
  ↓
CHECK CONTRADICTIONS
  ↓
COMPARE TO GROUND TRUTH WHERE AVAILABLE
  ↓
CALCULATE/REPRESENT UNCERTAINTY
  ↓
DECIDE
```

---

## 38. Validation Outcomes

Use explicit outcomes:

```text
ACCEPTED
ACCEPTED_WITH_LIMITATIONS
PROVISIONAL
REQUIRES_CORROBORATION
REQUIRES_VERIFICATION
CONTESTED
REJECTED
QUARANTINED
```

Do not collapse these into a binary trusted/untrusted state.

---

## 39. Admission Thresholds

Validation outcome must be evaluated against the destination.

For example:

```text
conversation context
 → provisional may be sufficient

long-term knowledge
 → stronger evidence

safety-critical decision
 → authoritative/current evidence required
```

---

## 40. Knowledge Promotion

External information should normally progress through:

```text
EXTERNAL CLAIM
      ↓
EVIDENCE RECORD
      ↓
VALIDATION
      ↓
CANDIDATE MEMORY
      ↓
CORROBORATION / REVALIDATION
      ↓
KNOWLEDGE CANDIDATE
      ↓
PROMOTION POLICY
```

No direct external-source-to-authoritative-knowledge shortcut.

---

## 41. Confidence Propagation

When a derived claim depends on uncertain sources, uncertainty must propagate rather than disappear.

```text
uncertain source
      ↓
derivation
      ↓
uncertain claim
```

Document 52 governs the broader uncertainty model.

---

## 42. Provenance Graph

A validated claim should be traceable:

```text
knowledge
   ↓
claim
   ↓
evidence
   ↓
source
   ↓
acquisition
   ↓
transformation
```

W3C PROV's model supports representing entities, activities, agents and derivations for this purpose. citeturn0search11

---

## 43. Validation Reproducibility

Where practical, record enough information to reproduce the validation:

- source version/content digest;
- retrieval time;
- validation rules/version;
- corroborating sources;
- ground-truth reference;
- model/tool versions;
- decision outcome.

---

## 44. Revalidation

A previously validated source may require revalidation when:

- content changes;
- source identity changes;
- source reliability degrades;
- relevant environment changes;
- evidence becomes stale;
- contradictions emerge;
- validation policy changes;
- the claim becomes more consequential.

---

## 45. Validation Decay

Validation strength may become less useful over time when the underlying claim is time-sensitive.

```text
validated yesterday
      ↓
not necessarily validated today
```

Temporal policy follows document 53.

---

## 46. Negative Evidence

Novi should preserve evidence against a claim as well as supporting evidence.

```text
supporting evidence
       +
contradictory evidence
       ↓
current assessment
```

Removing inconvenient evidence would corrupt epistemic state.

---

## 47. Minority / Outlier Sources

A source that disagrees with many others should not automatically be discarded.

Evaluate:

- source independence;
- evidence quality;
- directness;
- recency;
- known source reliability;
- possibility of a genuine new event.

Consensus is evidence, not proof.

---

## 48. Authority Hierarchy

Where sources have different authority, authority must be explicitly defined for the relevant domain.

Examples may include:

```text
current safety controller
 > historical memory

verified device telemetry
 > inferred status

official system state
 > informal report
```

Authority is domain-specific and does not imply universal truth.

---

## 49. Cross-Validation Failure

If required independent validation cannot be obtained:

```text
NO CORROBORATION
      ↓
retain as provisional/unverified
      ↓
DO NOT overstate certainty
```

Failure to validate is not evidence that the claim is false.

---

## 50. Validation and Action

Validation status must be passed into decision-making.

```text
validated claim
      ↓
context
      ↓
uncertainty
      ↓
authorization
      ↓
safety
      ↓
action
```

A validated claim still does not authorize an action.

---

## 51. Validation and LLM Context

Before external content is placed into LLM context, Novi should preserve source boundaries and metadata.

Conceptually:

```text
SYSTEM / POLICY
      ↓
TRUSTED APPLICATION DATA
      ↓
UNTRUSTED EXTERNAL CONTENT
```

The LLM must not be relied upon as the sole enforcement mechanism separating these classes.

---

## 52. No Hidden Promotion Through Summarization

A summary of unverified external content remains unverified unless independently validated.

```text
unverified document
      ↓
LLM summary
      ↓
still unverified
```

Transformation does not create evidence.

---

## 53. No Trust Amplification by Persistence

Persisting a claim in Novi's memory does not increase its evidentiary quality.

```text
stored claim
 ≠
independent confirmation
```

---

## 54. No Trust Amplification by Frequency

Repeated retrieval of the same claim does not make it more true.

```text
same source × 100
 ≠
100 sources
```

Frequency may indicate persistence, not correctness.

---

## 55. Privacy and Validation

Validation must not create unnecessary copies of sensitive external data.

Where possible, use:

- minimized evidence;
- hashes/digests;
- scoped excerpts;
- derived validation metadata;
- redaction.

Privacy constraints from document 61 remain applicable throughout validation.

---

## 56. Authorization

Only authorized processes may submit external information for durable memory promotion.

Validation itself may require access to sensitive material and therefore remains subject to document 62.

---

## 57. Failure Handling

If validation infrastructure fails:

```text
validator unavailable
      ↓
DO NOT silently accept
      ↓
provisional / deferred / reject
```

The appropriate outcome depends on risk and policy.

---

## 58. Offline Operation

Core validation of locally available sources must work without:

- Wi-Fi;
- Bluetooth;
- cloud services.

When offline, external-network claims may be unavailable, but local evidence validation remains functional.

---

## 59. Network Reconnection

When connectivity returns, newly obtained information must pass through the same validation boundary.

Network availability must never bypass:

- provenance;
- security;
- privacy;
- authorization;
- uncertainty;
- admission policy.

---

## 60. Validation Telemetry

Record operational metrics such as:

- source validation success/failure;
- corroboration rate;
- contradiction rate;
- stale-source rate;
- provenance completeness;
- rejected/ quarantined content;
- poisoning indicators;
- false-validation discoveries;
- revalidation frequency;
- latency/resource cost.

These metrics belong under the observability/audit architecture defined elsewhere.

---

## 61. Evaluation and Benchmarking

Validation should be tested using datasets containing:

- correct sources;
- stale sources;
- contradictory sources;
- duplicated sources;
- correlated sources;
- malicious sources;
- AI-generated misinformation;
- incomplete provenance;
- forged identity;
- tampered content;
- prompt injection;
- poisoned data;
- valid minority viewpoints.

The system should measure both false acceptance and false rejection.

---

## 62. Safety-Critical Evaluation

For safety-critical information, validation tests should include adversarial and failure scenarios.

Examples:

```text
trusted-looking stale source
forged official source
compromised API
conflicting sensors
malicious document
false emergency information
```

The system should default to safe current state rather than trusting external claims when uncertainty is material.

---

## 63. Recovery and Rollback

If a source is later discovered to have been compromised:

```text
source compromise detected
      ↓
identify dependent claims
      ↓
trace provenance
      ↓
quarantine affected knowledge
      ↓
re-evaluate
      ↓
rollback / supersede / delete as required
```

Documents 51, 59 and 60 provide the lineage, recovery and integrity foundations.

---

## 64. Learning Boundary

External validation results may become learning signals only after their provenance and validation status are preserved.

```text
external event
      ↓
validated experience
      ↓
learning candidate
      ↓
learning policy
```

Learning must not erase the distinction between observation, source report and verified outcome.

---

## 65. Architectural Invariants

1. External information is evidence, not truth by default.
2. Source identity must be preserved where available.
3. Provenance is mandatory for durable external knowledge.
4. Authenticity and truth are separate properties.
5. Integrity and correctness are separate properties.
6. Source reliability is scoped to task, domain and conditions.
7. Multiple copies of the same source do not constitute independent corroboration.
8. Correlated sources must not be counted as independent evidence.
9. Search ranking and popularity are not validation.
10. Citations are not validation by themselves.
11. AI-generated claims require evidence appropriate to their intended use.
12. Novi must not validate its own unsupported output by persistence or repetition.
13. User reports retain their source class.
14. External content is untrusted data unless separately authorized.
15. External instructions never become system authority through ingestion.
16. Current trusted physical state takes precedence over stale external claims for immediate physical decisions.
17. Validation strength is proportional to consequence.
18. Unknown ground truth results in uncertainty, not fabricated certainty.
19. Contradictory evidence is preserved rather than silently discarded.
20. Minority evidence is evaluated rather than rejected solely because it is uncommon.
21. Validation status is separate from authorization.
22. Validation status is separate from action safety.
23. Summarization does not increase evidentiary quality.
24. Persistence does not increase evidentiary quality.
25. Repetition from one source does not increase independence.
26. Validation must respect privacy and access control.
27. Validation failures must produce explicit degraded/provisional states.
28. Core local validation works without network connectivity.
29. Network reconnection does not bypass validation controls.
30. Compromised sources must be traceable through provenance and eligible for rollback.
31. Validation decisions should be reproducible where practical.
32. External knowledge promotion requires an explicit admission/promotion policy.
33. Safety-critical decisions require stronger evidence than ordinary conversational use.
34. Novi must be able to abstain when evidence is insufficient.

---

## 66. Final Principle

> **Novi should not ask only “Does this source look trustworthy?” It should ask “What exactly is being claimed, where did it come from, can its origin and integrity be established, how independent is the evidence, what contradicts it, how fresh and contextually valid is it, and what level of consequence will depend on it?”**

External knowledge becomes useful to Novi through disciplined validation—not through blind trust, popularity, repetition, model confidence, or persistence. The result should be an auditable evidence chain that allows Novi to remain curious and continuously learning while preserving uncertainty, provenance, security, privacy and safe boundaries.