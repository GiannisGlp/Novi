# 75 — Memory Knowledge Evidence Quality, Confidence and Uncertainty

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi represents evidence quality, uncertainty, confidence, reliability, freshness, calibration, and epistemic limitations without reducing all knowledge to a misleading single score.

## Core Principle

> **Novi must represent what it knows, how well it knows it, what it does not know, and why uncertainty exists.**

Confidence is contextual. It is not truth, authority, or permission.

## 1. Evidence Quality vs Confidence

These are different concepts.

```text
Evidence quality
= properties of the evidence

Confidence
= belief in a specific claim given available evidence
```

High-quality evidence can support a low-confidence claim if the interpretation is ambiguous.

## 2. Uncertainty Classes

Novi should distinguish, where meaningful:

```text
MEASUREMENT UNCERTAINTY
MODEL / EPISTEMIC UNCERTAINTY
ALEATORIC / ENVIRONMENTAL VARIABILITY
SOURCE UNCERTAINTY
TEMPORAL UNCERTAINTY
SPATIAL UNCERTAINTY
IDENTITY UNCERTAINTY
CAUSAL UNCERTAINTY
PROVENANCE UNCERTAINTY
```

The implementation may use a smaller operational vocabulary while retaining these semantics.

## 3. Unknown Is a Valid State

```text
UNKNOWN
```

must be a first-class state.

Novi must not convert missing information into a negative fact.

```text
not observed
≠
observed absent
```

## 4. Confidence Is Not Probability by Default

A value such as `0.82` must not automatically be interpreted as an 82% probability unless the system explicitly defines and validates that calibration.

Confidence semantics must be documented by subsystem.

## 5. Calibration

If a subsystem exposes probabilistic confidence, it should be evaluated for calibration against appropriate validation data.

A model can be accurate yet poorly calibrated, or well calibrated but inaccurate for a particular environment.

## 6. Context Dependence

Confidence depends on context such as:

- environment;
- sensor conditions;
- distance;
- lighting;
- temperature;
- motion;
- hardware configuration;
- model version;
- task;
- time;
- location.

A confidence value must not be transferred blindly between contexts.

## 7. Source Reliability

Reliability belongs to a source in a defined context, not universally.

```text
sensor S
reliable for temperature
≠
reliable for object identity
```

## 8. Reliability Is Not Authority

An accurate sensor does not gain permission to control Novi merely because it is reliable.

```text
reliability
≠
authority
```

## 9. Evidence Quality Dimensions

Evidence quality may include:

- accuracy;
- precision;
- completeness;
- resolution;
- freshness;
- provenance quality;
- independence;
- consistency;
- calibration status;
- environmental suitability;
- integrity.

## 10. Accuracy vs Precision

These must remain distinct.

```text
precision
= repeatability / resolution characteristics

accuracy
= closeness to the relevant true/reference value
```

High precision does not guarantee high accuracy.

## 11. Sensor Health

Sensor-derived confidence should consider sensor health.

Potential states:

```text
HEALTHY
DEGRADED
UNKNOWN
FAILED
UNAVAILABLE
```

A failed sensor must not continue producing apparently normal evidence.

## 12. Calibration State

Evidence quality should account for calibration state:

```text
CALIBRATED
CALIBRATION_STALE
CALIBRATION_UNKNOWN
CALIBRATION_INVALID
```

## 13. Measurement Uncertainty

Measurements should retain appropriate uncertainty representations such as:

- intervals;
- covariance;
- variance;
- error bounds;
- confidence intervals where statistically justified;
- qualitative uncertainty classes.

The representation depends on the sensor and domain.

## 14. Avoid False Precision

If the sensor supports only approximate location, Novi must not report unnecessary decimal precision as though it were meaningful.

```text
uncertain 5 m
≠
5.000000 m exact
```

## 15. Temporal Uncertainty

When event timing is uncertain:

```text
T ≈ [t1, t2]
```

may be more accurate than inventing a single timestamp.

## 16. Spatial Uncertainty

Positions should represent uncertainty where relevant.

For Novi this applies to:

- GPS/GNSS;
- visual localization;
- LiDAR localization;
- map alignment;
- object positions;
- remembered places.

## 17. Thermal Uncertainty

Thermal measurements depend on sensor characteristics and environment.

Novi should distinguish:

```text
measured temperature
estimated surface temperature
inferred environmental condition
```

and retain uncertainty where available.

## 18. Audio Uncertainty

Microphone-array direction-of-arrival estimates can be affected by:

- reverberation;
- noise;
- multiple speakers;
- occlusion;
- microphone calibration;
- room geometry.

Voice direction should therefore retain confidence/uncertainty and should not automatically establish speaker identity.

## 19. Vision Uncertainty

Object recognition confidence should consider:

- image quality;
- occlusion;
- lighting;
- motion blur;
- camera calibration;
- model version;
- domain shift.

Recognition remains an inference.

## 20. LiDAR Uncertainty

LiDAR-derived state can be affected by:

- reflective/absorptive surfaces;
- transparent objects;
- range limits;
- environmental conditions;
- calibration;
- occlusion;
- synchronization.

These limitations must inform downstream confidence.

## 21. Sensor Fusion

Fusion should not simply average confidence values.

It should consider:

```text
measurement uncertainty
sensor reliability
correlation
calibration
time alignment
spatial alignment
environment
```

## 22. Correlated Evidence

If two observations share a common failure source, treating them as independent can produce unjustifiably high confidence.

```text
same camera
 → two models
 → same visual error
```

is not independent corroboration.

## 23. Evidence Independence

Independence should be represented explicitly where known or estimated.

Unknown independence must not be treated as full independence.

## 24. Confidence Aggregation

Any aggregation method must be domain-specific and validated.

Avoid generic formulas such as:

```text
confidence = average(all_confidences)
```

unless the underlying assumptions are explicitly justified.

## 25. Claim Confidence

A claim's confidence should be derived from the relevant evidence and inference process.

It should retain links to:

- evidence;
- inference method;
- model/version;
- validation;
- uncertainty;
- context.

## 26. Confidence Decomposition

Where practical, expose why confidence is limited:

```text
GOOD SENSOR QUALITY
BUT
LOW VISIBILITY
AND
AMBIGUOUS OBJECT
```

This is more useful than a single opaque number.

## 27. Confidence Bands

For user-facing communication, qualitative bands may be preferable:

```text
HIGH
MODERATE
LOW
UNKNOWN
CONTESTED
```

Exact numerical values should be exposed only when their semantics are meaningful.

## 28. Confidence Thresholds

Thresholds must be task-specific.

The threshold appropriate for:

```text
showing a visual suggestion
```

is not necessarily appropriate for:

```text
moving a physical actuator
```

## 29. Safety-Critical Decisions

Safety decisions should not rely on a single generic confidence threshold.

They should consider:

- hazard severity;
- uncertainty;
- sensor redundancy;
- fail-safe behavior;
- current sensor health;
- conservative bounds.

## 30. Conservative Uncertainty

When uncertainty materially affects physical safety, Novi should prefer a conservative response over unjustified certainty.

Example:

```text
obstacle status uncertain
→ slow / stop / obtain more evidence
```

according to the safety architecture.

## 31. Confidence vs Action Authorization

Even extremely high confidence does not authorize an action.

```text
confidence
   ↓
perception/decision evidence
   ↓
authorization
   ↓
safety validation
   ↓
action
```

## 32. Freshness

Evidence quality includes temporal freshness when the fact can change.

```text
high-confidence old observation
```

may be less useful than a

```text
moderate-confidence recent observation
```

for current physical state.

## 33. Freshness Decay

Some knowledge classes may require explicit freshness functions or expiry policies.

Freshness decay must be domain-specific rather than universally exponential or time-based.

## 34. Stability

Some facts change slowly; others change rapidly.

Examples:

```text
birth date
→ stable

room occupancy
→ rapidly changing
```

Confidence/freshness policies must reflect this difference.

## 35. Temporal Validity

A claim may be:

```text
VALID_NOW
VALID_HISTORICALLY
EXPIRED
FUTURE_VALID
UNKNOWN_VALIDITY
```

Temporal validity is separate from confidence.

## 36. Contradiction

If reliable evidence conflicts:

```text
CONTESTED
```

may be more correct than choosing one claim without sufficient basis.

## 37. Confidence Under Contradiction

Conflicting evidence should generally reduce certainty in the affected proposition until resolved.

The system should preserve both evidence paths.

## 38. Provenance Completeness

Confidence should account for provenance completeness where traceability matters.

```text
unknown source
```

should not be treated like

```text
verified source with complete lineage
```

## 39. External Source Confidence

External information should consider:

- source authority for the topic;
- publication date;
- update status;
- corroboration;
- provenance;
- possible conflicts;
- retrieval integrity.

## 40. User Statements

A user's direct statement can be authoritative for some personal preferences or intentions while remaining unverified for external facts.

Authority is therefore **claim-type dependent**.

## 41. Personal Preference Confidence

Novi may model preferences with:

- explicitness;
- recency;
- repeated consistent statements;
- scope;
- user identity.

Repeated memory retrieval must not itself count as independent confirmation.

## 42. Identity Confidence

Identity inference requires conservative handling.

Similarity alone should not automatically establish identity.

Relevant evidence may include:

- authorized biometric systems;
- explicit user confirmation;
- context;
- temporal continuity;
- sensor quality.

## 43. Map Confidence

Spatial memories should retain confidence related to:

- localization quality;
- sensor observations;
- map alignment;
- revisit consistency;
- environment changes.

A remembered location should not be treated as exact merely because it is represented by a coordinate.

## 44. Learned Knowledge Confidence

Learned behavior/knowledge should distinguish:

```text
observed repeatedly

from

validated across independent contexts
```

Generalization requires evidence beyond repetition in one environment.

## 45. Model Shift

Confidence can degrade when deployment conditions differ from validation conditions.

Novi should track relevant distribution/domain shifts where feasible.

## 46. Model Versioning

Confidence semantics must be tied to model/version metadata.

A score from model V1 cannot automatically be compared numerically with a score from V2 without validation.

## 47. Calibration Monitoring

Where numerical probabilities are used, monitor calibration over time and across important operating environments.

Calibration degradation should be observable.

## 48. Confidence Drift

Confidence distributions may change because of:

- sensor aging;
- environmental change;
- model changes;
- calibration drift;
- hardware replacement;
- software updates.

These changes should be monitored.

## 49. Evidence Quality State

A useful normalized representation can include:

```text
quality_status
confidence
uncertainty
freshness
source_reliability
provenance_completeness
calibration_status
context_validity
```

Not every field must be numeric.

## 50. Missingness

Missing evidence should be explicitly represented.

```text
MISSING
NOT_APPLICABLE
NOT_OBSERVED
UNAVAILABLE
UNKNOWN
```

These states must not be collapsed.

## 51. Degraded Mode

If evidence quality falls below a safe operational level:

```text
NORMAL
 ↓
DEGRADED
 ↓
LIMITED CAPABILITY
 ↓
SAFE FALLBACK
```

The exact behavior belongs to the relevant safety/capability architecture.

## 52. Graceful Uncertainty

Novi should be able to say internally and externally, where appropriate:

```text
I don't know.

I have incomplete evidence.

The evidence conflicts.

The information is stale.

The source is unknown.
```

These are correct system states, not failures of reasoning.

## 53. User-Facing Communication

When uncertainty matters, Novi should communicate it clearly without unnecessary numerical complexity.

Prefer:

> "I'm not certain; two sensors disagree."

over:

> "Confidence: 63.284%."

unless the number has validated meaning and is useful for the user.

## 54. Explainability of Uncertainty

Novi should be able to identify major uncertainty contributors:

```text
LOW CONFIDENCE
because:
- low lighting
- partial occlusion
- stale map
```

The explanation must be generated from actual system state, not invented after the fact.

## 55. Uncertainty Propagation

Downstream systems should not silently discard relevant uncertainty.

```text
uncertain observation
 ↓
uncertain perception
 ↓
uncertain world state
 ↓
uncertain decision input
```

The exact mathematical propagation depends on the domain.

## 56. Bounds vs Estimates

Where safety matters, retain conservative bounds where appropriate rather than only point estimates.

```text
estimated distance = 2.0 m
possible range = [1.7, 2.4] m
```

The representation must match actual sensor/model assumptions.

## 57. Bayesian Methods

Bayesian reasoning may be used where its assumptions and probability semantics are appropriate.

It is not mandatory for every subsystem.

## 58. Statistical Methods

Frequentist intervals, hypothesis tests, calibration curves and other statistical tools may be appropriate for validation.

No single statistical framework is required universally.

## 59. Qualitative Uncertainty

Some knowledge cannot reasonably receive a precise numerical uncertainty.

Use explicit qualitative states instead of fabricated numbers.

## 60. Evidence Quality and Distributed Agents

Remote evidence retains its source context and uncertainty.

Novi must not normalize heterogeneous confidence values into a common scale without validated calibration.

## 61. Evidence Quality and Documents

Document claims should consider:

- source authority;
- provenance;
- document age;
- version;
- extraction quality;
- corroboration;
- context.

Parsing quality and factual truth remain separate dimensions.

## 62. Evidence Quality and Sensor Fusion

Fusion algorithms must expose assumptions about:

- sensor independence;
- covariance/error models;
- timing;
- calibration;
- coordinate frames;
- failure modes.

A fusion result should not appear more certain merely because more sensors were included.

## 63. Evidence Quality and Memory Promotion

Memory admission should consider evidence quality and retention policy.

Low-confidence observations can remain useful episodic evidence without becoming durable factual knowledge.

## 64. Evidence Quality and Knowledge Revision

When new evidence changes confidence:

```text
existing claim
 ↓
new evidence
 ↓
confidence/validity update
 ↓
knowledge revision or contested state
```

The original evidence remains traceable where retained.

## 65. Confidence Auditing

Important confidence-producing systems should be auditable for:

- calibration;
- threshold selection;
- false positives;
- false negatives;
- environmental performance;
- sensor failures;
- drift;
- subgroup/context differences where relevant.

## 66. Testing

Test:

- missing data;
- contradictory sensors;
- correlated sensors;
- stale observations;
- clock uncertainty;
- spatial uncertainty;
- sensor degradation;
- calibration drift;
- model version changes;
- domain shift;
- false confidence;
- overconfident unknowns;
- confidence calibration;
- uncertainty propagation;
- distributed confidence mismatch;
- document extraction uncertainty;
- identity ambiguity;
- map uncertainty;
- thermal measurement uncertainty;
- audio localization uncertainty;
- vision uncertainty;
- safety behavior under uncertainty.

## 67. Architectural Invariants

1. Confidence is not truth.
2. Confidence is not authorization.
3. Confidence is not universally probabilistic.
4. Unknown is a first-class state.
5. Missing evidence is not evidence of absence.
6. Evidence quality and claim confidence are distinct.
7. Accuracy and precision are distinct.
8. Source reliability is contextual.
9. Correlated evidence is not independent evidence.
10. Confidence values from incompatible systems must not be blindly compared.
11. Uncertainty should be propagated when materially relevant.
12. False precision is prohibited.
13. Freshness is distinct from confidence.
14. Historical validity is distinct from current confidence.
15. Conflicting evidence may produce a contested state.
16. Safety-critical decisions require more than a generic confidence threshold.
17. High confidence never bypasses authorization or safety controls.
18. Sensor health and calibration affect evidence quality.
19. Model/version changes can invalidate prior confidence assumptions.
20. User-facing uncertainty must reflect actual system state.
21. Novi must be able to represent "I don't know."
22. Repeated retrieval of the same evidence does not create independent corroboration.
23. Numerical confidence requires explicit semantics and validation.
24. Evidence-quality degradation must be observable.
25. Uncertainty handling must not disable core offline operation.

## 68. Final Principle

> **A trustworthy Novi is not one that is always confident; it is one that knows when confidence is justified, when uncertainty is material, and when the correct answer is simply that it does not know.**

Confidence and uncertainty therefore become first-class properties of Novi's memory and knowledge architecture, connected to provenance, sensor health, temporal/spatial context, model calibration, distributed evidence, safety policy, and knowledge promotion.