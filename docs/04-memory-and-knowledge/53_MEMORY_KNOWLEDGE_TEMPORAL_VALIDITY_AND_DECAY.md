# 53 — Memory Knowledge Temporal Validity and Decay

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi represents the time-bounded validity of memories, beliefs, knowledge, preferences, environmental models, routes and learned behavior.

The architecture must prevent a common failure: treating an old observation as if it were the current state of the world. Historical truth must remain preserved while current-use validity is evaluated separately.

## Core Principle

> **Time changes the applicability of information, not necessarily the historical truth of the information. Novi must preserve what was true then while deciding independently whether it is safe and useful to treat it as true now.**

## 1. Temporal Dimensions

Important knowledge may need distinct temporal fields:

- `occurred_at` — when the underlying event happened;
- `observed_at` — when Novi observed it;
- `recorded_at` — when it was persisted;
- `valid_from` — beginning of the represented validity interval;
- `valid_until` — known or estimated end of validity;
- `last_verified_at` — most recent verification;
- `superseded_at` — when replaced by a newer representation;
- `expired_at` — when policy determined it should no longer be used as current.

These must not be collapsed into one generic timestamp.

## 2. Historical Truth vs Current Validity

Example:

```text
2027-03: "The sofa is in the living room."
2030-06: sofa moved

Historical claim → remains true for 2027-03
Current claim    → no longer valid
```

Novi preserves the historical record while updating the current world model.

## 3. Temporal Validity States

Use explicit states such as:

```text
CURRENT
CURRENT_UNVERIFIED
STALE
EXPIRED
SUPERSEDED
HISTORICAL
FUTURE
UNKNOWN_VALIDITY
CONFLICTED
```

`STALE` means evidence may still be true but has insufficient freshness for the intended use.

## 4. Freshness Is Not Truth

```text
freshness ≠ truth
truth ≠ freshness
```

Freshness is an input to applicability and verification, not a truth score.

## 5. Knowledge Classes Have Different Time Behavior

Examples:

```text
battery state          → seconds/minutes
robot pose             → milliseconds/seconds
room temperature       → minutes
route obstacle         → minutes/hours
user preference        → days/months or event-based
place layout           → days/months/years
historical event       → permanent historical record
scientific knowledge   → potentially long-lived but revisable
```

No universal TTL applies to all memory.

## 6. Validity Policy

Each memory/knowledge class should define:

- expected stability;
- verification method;
- maximum acceptable age by use case;
- invalidation triggers;
- decay model if applicable;
- revalidation requirements;
- retention policy.

## 7. Use-Case-Specific Freshness

The same memory can be fresh enough for one purpose and stale for another.

```text
"There is normally a chair here."

conversation       → potentially acceptable
collision avoidance → unacceptable without current sensing
```

Freshness is therefore evaluated at retrieval/use time.

## 8. Safety-Critical Freshness

Safety-critical state requires the strictest freshness rules, including:

- current pose;
- obstacle state;
- battery state;
- motor state;
- thermal state;
- emergency state.

Historical memory must never substitute for current safety sensing.

## 9. Current World State

Novi's current world model is a continuously updated estimate, not a permanent database of facts.

```text
historical knowledge
      ↓
current observations
      ↓
state estimation
      ↓
current world state
```

## 10. Invalidation Events

Information may become stale or invalid because of:

- contradictory observation;
- physical change;
- explicit user correction;
- hardware replacement;
- map update;
- policy change;
- model migration;
- source withdrawal;
- expiry policy;
- environment change.

## 11. Event-Driven Invalidation

Where reliable change events exist, use explicit invalidation instead of waiting for a timer.

```text
chair moved
   ↓
chair-location memory invalidated
```

## 12. TTL

TTL is a policy mechanism for dynamic information.

Expiration means:

```text
Do not assume current validity without revalidation.
```

It does **not** mean the historical claim was false.

## 13. Soft and Hard Expiration

Some knowledge can transition:

```text
CURRENT → STALE → EXPIRED
```

A stale item may remain useful as background context. A hard-expired item must not be used for its protected purpose without successful revalidation.

## 14. Verification

Revalidation should use the best available authoritative evidence:

- sensor observation;
- map matching;
- direct user confirmation;
- trusted system telemetry;
- repeated independent observation;
- approved external source.

Revalidation updates current belief; it does not rewrite history.

## 15. Confidence and Freshness

Represent them separately:

```text
confidence = strength of evidence
freshness  = temporal applicability
```

A highly reliable observation can be stale. A fresh observation can be low-confidence.

## 16. Decay Functions

Some information may use a validated decay model:

```text
weight(t) = w0 × decay(t)
```

Possible forms include exponential, linear, stepwise, domain-specific or no decay.

There must be no arbitrary universal exponential decay. Historical facts may have no decay as historical facts while their usefulness for current decisions decays rapidly.

## 17. Change-Rate-Aware Freshness

Dynamic entities generally require shorter verification intervals than stable structures.

```text
fast-changing object → short interval
stable structure     → longer interval
```

Intervals must be evidence- and risk-driven.

## 18. Surprise and Contradiction Driven Revalidation

Unexpected observations should accelerate revalidation.

```text
expected state
    ↓
unexpected observation
    ↓
change candidate
    ↓
verify
```

Contradictions should enter an explicit conflict/revalidation path rather than silently overwriting stored knowledge.

## 19. Recency Bias Protection

Newer information does not automatically outrank stronger evidence.

Resolution considers source quality, context, corroboration, uncertainty, temporal scope and authority.

## 20. Historical Memory

Historical memories retain their original temporal scope.

```text
"Novi visited the park on 2028-05-10."
```

This remains a historical fact even if the park is never visited again.

## 21. Temporal Scoping

Claims should support:

```text
point-in-time
interval
recurring pattern
open-ended current state
historical state
future plan
prediction
```

## 22. Recurring Knowledge

Patterns such as:

```text
"The user usually leaves at 08:00."
```

are temporal/probabilistic patterns, not guaranteed schedules. They should include observation window and confidence.

## 23. Future Information

Plans and predictions are not current facts.

```text
planned visit ≠ completed visit
```

Future information must have explicit status.

## 24. Temporal Contradictions

Many apparent contradictions are actually changes over time.

```text
A true in 2027
B true in 2029
```

First test whether validity intervals allow both claims to coexist before declaring an epistemic conflict.

## 25. Temporal Knowledge Graph

Relationships should be time-scoped where appropriate.

```text
object_42 located_in kitchen
valid: 2027-01 → 2028-04

object_42 located_in garage
valid: 2028-04 → current
```

Historical relationships remain distinct from current relationships.

## 26. Map and Environment Versions

Spatial knowledge must reference the map/world-model version relevant to the claim. A route valid against map A may be invalid against map B.

## 27. Model, Knowledge and Source Aging

Learned models can become stale because of:

- environmental distribution change;
- hardware changes;
- sensor recalibration;
- user behavior changes;
- software/dependency changes;
- changed model assumptions.

Knowledge can become stale even when the model is unchanged because the world changed. Sources themselves can change through firmware, APIs, documents, datasets or calibration.

## 28. Drift Monitoring

NIST's AI RMF emphasizes ongoing measurement and management, while NIST's 2026 work on deployed AI identifies performance degradation, distributional drift and determining when a model becomes stale as important monitoring challenges. Novi should therefore treat model and knowledge freshness as monitored properties rather than permanent assumptions.

## 29. Verification Windows

A verification policy should define:

```text
freshness threshold
warning threshold
hard invalidation threshold
verification action
```

Thresholds are information-class and risk dependent.

## 30. Retrieval-Time Validity

The memory retrieval layer must evaluate temporal applicability:

```text
query
 ↓
retrieve candidates
 ↓
check temporal scope
 ↓
check freshness
 ↓
check contradictions
 ↓
rank usable evidence
```

Staleness must remain visible to downstream reasoning.

## 31. Context Construction

Working memory should distinguish:

```text
CURRENT VERIFIED
CURRENT UNCERTAIN
RECENT
STALE CONTEXT
HISTORICAL
HYPOTHETICAL
```

Historical context must never masquerade as current verified state.

## 32. Decision Gate

Before consequential use:

```text
memory retrieved
   ↓
temporal validity check
   ↓
provenance check
   ↓
uncertainty check
   ↓
current-state verification if required
   ↓
policy/safety gate
   ↓
use or reject
```

## 33. Decay vs Forgetting

```text
DECAY
↓
less fresh / less applicable

FORGETTING
↓
retention/removal decision
```

A stale memory may remain valuable historical context.

## 34. Retention Interaction

Retention determines how long records remain stored. Validity determines how long they may be treated as current. These are independent policies.

## 35. Privacy Interaction

Privacy deletion can remove information even when it remains factually valid. Dependent knowledge may require redaction, reevaluation or removal according to the privacy architecture.

## 36. Preference Aging

Preferences may be:

```text
temporary
stable
expired
explicitly revoked
```

Explicit revocation takes precedence within its applicable scope.

## 37. Learning Interaction

Staleness is itself a learning signal.

```text
rule failure
 ↓
staleness candidate
 ↓
revalidation
 ↓
update / narrow scope / retire
```

A learned rule should not be kept indefinitely merely because it once worked.

## 38. Temporal Belief Revision

Prefer temporal qualification when it resolves an apparent contradiction:

```text
old belief valid until T1
new belief valid from T1
```

Only genuine overlap conflicts require epistemic conflict resolution.

## 39. Temporal Provenance

W3C PROV models entity lifetimes, generation/invalidation and event ordering, and deliberately avoids assuming perfectly synchronized clocks. Novi should likewise separate validity intervals and relative event ordering from raw timestamps.

## 40. Clock Uncertainty

Temporal reasoning must preserve:

- clock source;
- synchronization state;
- timestamp uncertainty;
- relative event ordering where available.

Novi must not invent precise ordering from uncertain clocks.

## 41. Offline Operation

Temporal validity must work without Wi-Fi, Bluetooth or cloud access.

Local monotonic clocks and event ordering can support operation when wall-clock synchronization is unavailable. Network time can improve absolute timestamps but must not be required for core autonomy.

## 42. Restart and Recovery

After restart, reconstruct:

```text
current time estimate
+ event history
+ validity intervals
+ last verification
+ active world state
```

Persisted state must not become current merely because it survived reboot.

## 43. Distributed Synchronization

Synchronization must preserve:

- original event time;
- source clock/domain;
- reception time;
- version;
- validity interval;
- supersession state.

A later synchronization time does not make an old observation fresh.

## 44. Conflicting Distributed State

If devices disagree:

```text
device A: state X at t1
device B: state Y at t2
```

resolve using temporal order, source quality, synchronization uncertainty, physical plausibility and the established conflict-resolution architecture.

## 45. Intermittent Connectivity

Novi should prefer an authoritative local current observation over an older synchronized remote state for the same fact.

## 46. Resource Awareness

Freshness checking must remain bounded. Useful indexes include:

- validity interval;
- last verified time;
- source;
- entity;
- knowledge class.

Background revalidation should prioritize high-risk and high-value knowledge.

## 47. Monitoring and Audit

Monitor:

- stale-memory rate;
- invalidation rate;
- revalidation success;
- contradiction rate;
- knowledge-age distribution;
- model drift;
- false-freshness incidents;
- expired knowledge used in decisions.

These metrics should feed observability and architecture audits.

## 48. Testing Requirements

Test:

- TTL expiration;
- soft and hard expiration;
- event-driven invalidation;
- historical/current separation;
- temporal contradictions;
- clock skew;
- offline timekeeping;
- restart recovery;
- distributed synchronization;
- stale remote data;
- sensor-driven revalidation;
- user correction;
- map/environment changes;
- model drift;
- preference decay;
- retention vs validity separation;
- safety-critical freshness gates;
- prevention of stale-data decisions.

## 49. Architectural Invariants

1. Historical truth and current validity are separate concepts.
2. No universal TTL applies to all memory.
3. Freshness is not truth.
4. Confidence is not freshness.
5. Safety-critical decisions require appropriately fresh evidence.
6. Historical memories retain their historical scope after current beliefs change.
7. Event-driven invalidation is preferred when reliable change events exist.
8. TTL expiration requires revalidation for applicable uses; it does not rewrite history.
9. Newer evidence does not automatically outrank stronger evidence.
10. Temporal scope can resolve apparent contradictions before belief conflict is declared.
11. Planned/future information is not evidence of completed events.
12. Stale qualifiers survive retrieval and context construction.
13. Retention and temporal validity are independent policies.
14. Offline operation cannot depend on network time or synchronization.
15. Distributed synchronization preserves original event and validity times.
16. Model and knowledge drift require monitoring.
17. A stale memory may remain valuable as historical context.
18. Revalidation can update current belief without rewriting historical evidence.
19. Privacy deletion can override temporal validity.
20. No stale memory may silently masquerade as current verified state.

## 50. Final Principle

> **Novi must remember the past without confusing it for the present.**

Temporal validity is therefore a first-class property of memory and knowledge. Novi preserves historical experiences, tracks when claims were valid, detects when information becomes stale, revalidates important knowledge against current evidence, and adapts its world model as the physical and informational environment changes.

## Research Basis

- W3C PROV Data Model / PROV Constraints — entity lifetimes, generation/invalidation and event ordering.
- NIST AI Risk Management Framework — ongoing measurement, monitoring and management of AI-system risks.
- NIST AI 800-4 (2026) — post-deployment monitoring, performance degradation, drift and model staleness.
