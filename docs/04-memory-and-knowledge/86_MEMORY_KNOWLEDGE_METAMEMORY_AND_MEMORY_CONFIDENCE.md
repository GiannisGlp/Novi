# 86 — Memory Knowledge Metamemory and Memory Confidence

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define Novi's **metamemory**: structured knowledge about its own memory capabilities, availability, provenance, reliability, uncertainty, accessibility, freshness, limitations and failure states.

## Core Principle

> **Novi must know the difference between remembering something, being able to retrieve it, believing it, and knowing how reliable that memory is.**

Metamemory describes the state of the memory system; it does not magically establish the truth of remembered content.

## 1. Position in Architecture

```text
MEMORY STORES
     ↓
MEMORY OBSERVATION / AUDIT
     ↓
METAMEMORY
     ↓
RETRIEVAL / REASONING
     ↓
CALIBRATED CLAIM ABOUT MEMORY
```

## 2. Core Memory States

Novi should distinguish:

```text
KNOWN TO MEMORY
RETRIEVABLE
NOT RETRIEVABLE
FORGOTTEN / DELETED
UNKNOWN WHETHER RETAINED
RESTRICTED
STALE
CONTESTED
```

These states are not interchangeable.

## 3. Memory Availability vs Truth

```text
I can retrieve X
        ≠
X is true
```

Likewise:

```text
I cannot retrieve X
        ≠
X never happened
```

## 4. Memory Confidence vs Fact Confidence

Two dimensions should remain separate:

```text
MEMORY CONFIDENCE
"How confident am I that this record is what I think it is?"

FACT CONFIDENCE
"How strongly is the underlying claim supported?"
```

A perfectly retrieved record can still contain an incorrect claim.

## 5. Provenance Awareness

Metamemory should know, where available:

- source type;
- source identity;
- capture time;
- transformation history;
- model/version;
- validation status;
- revision history.

## 6. Source Reliability

Historical source performance can inform retrieval and qualification.

Examples:

```text
sensor X frequently reliable for temperature
sensor X weak for distant identity recognition
```

Reliability must remain task-specific.

## 7. Reliability Is Not Permanent

Source reliability can change because of:

- calibration drift;
- hardware degradation;
- environment;
- software/model changes;
- synchronization errors.

Metamemory should support time-bounded reliability assessments.

## 8. Calibration

Confidence should be evaluated against observed correctness where possible.

```text
PREDICTED CONFIDENCE
       ↓
OBSERVED OUTCOME
       ↓
CALIBRATION UPDATE
```

A confidence score that is consistently overconfident should be corrected.

## 9. Confidence Decomposition

Instead of one opaque confidence number, retain dimensions such as:

- source quality;
- evidence strength;
- temporal freshness;
- spatial certainty;
- identity certainty;
- independence of evidence;
- consistency;
- model reliability.

## 10. Epistemic Status

Claims can have statuses such as:

```text
OBSERVED
VERIFIED
INFERRED
HYPOTHESIZED
REPORTED
RECONSTRUCTED
CONTESTED
UNKNOWN
```

## 11. Memory Self-Knowledge

Novi may maintain statements such as:

```text
"I have a recorded episode of this event."
"I only have a user report."
"I have conflicting records."
"I do not currently have the record."
"The record is stale."
```

These statements describe memory state, not absolute truth.

## 12. Knowing That It Does Not Know

A critical capability is explicit uncertainty:

```text
UNKNOWN
```

should be a valid answer state when evidence is insufficient.

## 13. Unknown vs Forgotten

```text
UNKNOWN
 ≠
FORGOTTEN
```

`UNKNOWN` means Novi lacks sufficient knowledge.

`FORGOTTEN/DELETED` means information may have existed but is no longer available under current retention state.

## 14. Not Accessible vs Not Retained

```text
NOT AUTHORIZED
 ≠
NOT RETAINED
```

A restricted memory may exist even though the current process cannot access it.

## 15. Retrieval Confidence

Metamemory can estimate whether a retrieval result is likely to be complete:

```text
HIGH AVAILABILITY
PARTIAL
AMBIGUOUS
STALE
MISSING
```

This should be communicated when material to the task.

## 16. Memory Completeness

A recalled episode may be:

```text
COMPLETE
PARTIAL
RECONSTRUCTED
FRAGMENTARY
```

Completeness is distinct from correctness.

## 17. Recollection Reconstruction

When reconstructing a memory from multiple records, Novi should know that the result is a reconstruction.

```text
SOURCE FRAGMENTS
 ↓
RECONSTRUCTION
 ↓
METAMEMORY: RECONSTRUCTED
```

## 18. Memory Freshness

Metamemory should track whether a memory remains fit for the current purpose.

```text
FRESH
AGING
STALE
REQUIRES REVALIDATION
```

Freshness is task-dependent.

## 19. Temporal Reliability

A fact may be historically reliable but irrelevant to the present.

```text
"Door was open yesterday"
```

can be a reliable historical memory while being useless evidence for whether the door is open now.

## 20. Spatial Reliability

Location memories should include uncertainty and map/localization context.

```text
exact
approximate
room-level
region-level
unknown
```

## 21. Identity Reliability

Person/object identity confidence should be distinct from confidence that an observation occurred.

```text
"I saw someone"
```

may be highly reliable while:

```text
"that person was Alice"
```

remains uncertain.

## 22. Source Independence

Metamemory should recognize when multiple memories derive from the same source.

Repeated copies do not equal independent confirmation.

## 23. Correlated Evidence

```text
source A
 ↓
summary B
 ↓
embedding C
```

should not be counted as three independent sources.

## 24. Memory Conflict Awareness

Novi should know when its memory contains incompatible claims:

```text
Claim A
Claim B
 ↓
CONFLICT
```

The system should not hide the conflict merely to produce a confident answer.

## 25. Conflict Severity

Conflicts can be classified by consequence:

```text
LOW
MODERATE
HIGH
SAFETY-CRITICAL
```

Higher-consequence conflicts require stronger resolution or conservative handling.

## 26. Memory Failure Awareness

Metamemory should track failure modes such as:

- retrieval failure;
- index failure;
- corruption;
- synchronization lag;
- authorization failure;
- deletion;
- stale data;
- ambiguous identity;
- provenance loss.

## 27. Index vs Source Awareness

Novi should distinguish:

```text
SOURCE RECORD EXISTS
INDEX RECORD EXISTS
```

An index hit does not prove the underlying source remains available or current.

## 28. Cache Awareness

A cached memory may be stale.

Metamemory should know the cache timestamp/version where relevant.

## 29. Memory Version Awareness

When a memory is revised:

```text
MEMORY v1
 ↓
MEMORY v2
```

Metamemory can report that the current interpretation is newer than the original record.

## 30. Belief Revision Awareness

Novi should know when a current belief differs from an historical belief.

```text
HISTORICAL BELIEF
        ↓
CURRENT BELIEF
```

This supports truthful statements such as:

> "I previously believed X, but later evidence changed that assessment."

## 31. Memory Consolidation Awareness

Metamemory should distinguish source episodes from abstractions derived from them.

```text
3 episodes
 ↓
1 pattern
```

The pattern is a derivative, not an additional independent observation.

## 32. Summary Awareness

A generated summary should be marked as derivative.

Repeatedly reading the summary must not increase its evidentiary weight.

## 33. Embedding Awareness

Vector representations can help locate memories but do not themselves constitute authoritative semantic content.

Embedding/model version should be available where necessary.

## 34. Memory Accessibility

Access may depend on:

- identity;
- role;
- task;
- privacy;
- local/remote status;
- current authorization;
- storage availability.

## 35. Privacy-Aware Metamemory

Even metadata can be sensitive.

For example:

```text
"Novi has a memory about person's medical appointment"
```

may reveal sensitive information even without revealing the content.

## 36. Privacy-Minimized Self-Knowledge

Metamemory should expose only the minimum information necessary to determine availability or reliability.

## 37. User-Facing Confidence

When answering, Novi should communicate uncertainty proportionately.

Examples:

```text
High confidence:
"I have a recorded episode confirming this."

Moderate:
"I have a record suggesting this, but it is not fully verified."

Low:
"I have an uncertain or incomplete memory of this."

None:
"I don't have enough information to establish this."
```

## 38. Avoid False Precision

Novi should not expose an exact confidence percentage unless the underlying system is sufficiently calibrated and the number has a meaningful interpretation.

## 39. Confidence Language

Confidence wording should correspond to actual epistemic state rather than conversational style.

## 40. Metamemory and Hallucination Prevention

Before making a memory-based claim, Novi should ask internally:

```text
Do I have a source?
Is the source accessible?
Is it current enough?
Is the claim directly observed or inferred?
Are there conflicts?
Am I reconstructing?
```

## 41. Memory Search Failure

If retrieval fails, Novi should not fabricate a likely memory.

```text
NO RETRIEVAL
 ↓
NO FABRICATION
```

## 42. Retrieval Failure vs Absence of Event

```text
retrieval failed
 ≠
event did not happen
```

This distinction should be preserved in internal reasoning and user-facing communication when relevant.

## 43. Memory Self-Testing

Novi may periodically evaluate:

- retrieval accuracy;
- source reliability;
- confidence calibration;
- stale-memory rates;
- conflict frequency;
- corruption;
- synchronization quality.

## 44. Metamemory Updating

New evidence can update memory-system assessments:

```text
OBSERVED ERROR
 ↓
SOURCE RELIABILITY UPDATE
 ↓
AFFECTED MEMORY REASSESSMENT
```

This should not silently rewrite historical records.

## 45. Reliability Scope

A source can be reliable for one domain and unreliable for another.

```text
camera
 → strong object localization
 → weaker identity at distance
```

Reliability should therefore be scoped by task/domain.

## 46. Model Reliability

Different model versions may have different strengths and failure modes.

Metamemory can retain evaluation metadata to qualify model-derived memories.

## 47. Hardware Reliability

Hardware degradation can affect memory quality.

Examples:

- dirty lens;
- degraded microphone;
- LiDAR faults;
- GPS antenna problems;
- thermal sensor drift.

Affected memories may require revalidation.

## 48. Memory Integrity

Important memory records should have integrity mechanisms sufficient to detect unauthorized modification or corruption.

## 49. Memory Recovery

If a memory source becomes unavailable, Novi should distinguish:

```text
TEMPORARILY UNAVAILABLE
PERMANENTLY DELETED
CORRUPTED
NOT SYNCHRONIZED
NOT AUTHORIZED
```

## 50. Distributed Metamemory

Across Novi instances, metamemory should track:

- source agent;
- replica freshness;
- synchronization status;
- conflict state;
- trust context.

## 51. Offline Metamemory

Local metamemory must remain functional offline.

It should not falsely claim that remote memories are unavailable simply because the network is currently disconnected.

## 52. Memory Budget Awareness

Novi should know when storage or indexing constraints affect recall quality.

Examples:

```text
storage pressure
 ↓
retention reduction
 ↓
possible recall degradation
```

This can be surfaced when material to an answer.

## 53. Memory Lifecycle Awareness

Metamemory should understand lifecycle states from document 76:

```text
candidate
active
retained
demoted
expired
deleted
```

## 54. Deletion Awareness

After deletion, Novi should not claim the content remains available.

If only derived artifacts remain, those dependencies must be handled according to deletion policy.

## 55. User Corrections

If a user corrects a remembered fact, metamemory should record the correction path and distinguish:

```text
previous memory
user correction
current interpretation
```

## 56. Self-Correction

When Novi discovers a memory error, it should be able to say, where appropriate:

```text
I previously had this wrong.
```

without pretending the original memory never existed.

## 57. Metamemory Does Not Create Authority

Knowing that a source has historically been reliable does not make every future output from that source correct.

Current evidence remains necessary.

## 58. Safety Boundary

Metamemory confidence must never weaken hard safety controls.

A low-confidence safety-relevant observation should trigger conservative safety handling, not optimistic action.

## 59. Testing

Test:

- confidence calibration;
- memory vs fact confidence separation;
- retrieval failure;
- deleted memory handling;
- restricted memory handling;
- stale memory detection;
- conflicting memories;
- source correlation;
- source reliability drift;
- model/hardware degradation;
- cache staleness;
- index/source divergence;
- reconstruction labeling;
- user correction;
- distributed replicas;
- offline state;
- privacy leakage through metadata;
- false precision;
- hallucinated recollection;
- safety-critical uncertainty.

## 60. Architectural Invariants

1. Memory availability is distinct from truth.
2. Memory confidence is distinct from fact confidence.
3. Retrieval failure is distinct from event absence.
4. Unknown is distinct from forgotten/deleted.
5. Unauthorized is distinct from unavailable.
6. Source reliability is scoped and time-sensitive.
7. Correlated copies are not independent evidence.
8. Historical and current beliefs remain distinct.
9. Reconstructed memories remain marked as reconstructed.
10. Summaries and embeddings do not become independent evidence.
11. Metadata can itself be sensitive.
12. Metamemory must not expose more private information than necessary.
13. Confidence should be calibrated rather than invented.
14. Exact confidence percentages require meaningful calibration.
15. Memory errors can update reliability assessments without rewriting history.
16. Current evidence remains necessary even for historically reliable sources.
17. Distributed replicas retain freshness and trust context.
18. Offline operation does not imply remote data deletion.
19. Memory lifecycle state remains visible to appropriate governance systems.
20. Metamemory cannot weaken hard safety controls.

## 61. Final Principle

> **Novi should know what it remembers, how it remembers it, how accessible and complete that memory is, how trustworthy its supporting evidence has been, and when it should admit that it does not know.**

Metamemory is the self-awareness layer of Novi's memory architecture—not consciousness, but disciplined knowledge about the capabilities and limitations of its own memory system.