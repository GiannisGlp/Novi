# 52 — Memory Knowledge Confidence and Uncertainty Model

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi represents, propagates, calibrates, communicates and acts upon uncertainty across sensing, perception, language, memory, knowledge, reasoning, planning and action.

This document deliberately separates **confidence**, **probability**, **measurement uncertainty**, **evidence quality**, **epistemic uncertainty**, and **decision risk**. They are related but are not interchangeable.

## Research Basis

The design is aligned with established uncertainty and calibration practice. The BIPM/JCGM Guide to the Expression of Uncertainty in Measurement provides an international framework for evaluating and expressing measurement uncertainty and explicitly connects uncertainty with measurement and decision processes. citeturn0search48turn0search3 NIST AI RMF recommends rigorous testing with associated uncertainty measures, realistic test sets, external validity and documented reporting. citeturn0search5turn0search49 Machine-learning probability outputs also require calibration: scikit-learn documents that model probabilities can be over- or under-confident and provides calibration methods and reliability diagrams. citeturn0search0turn0search2

These sources establish principles; Novi's final thresholds and fusion algorithms remain implementation-specific and must be empirically validated on Novi's actual hardware and environments.

---

## 1. Core Principle

> **Novi must represent what it knows, how strongly the evidence supports it, what remains uncertain, and how uncertainty affects the decision—without reducing all of those concepts to one arbitrary confidence number.**

---

## 2. Epistemic Layers

Novi should distinguish:

```text
MEASUREMENT
What did a sensor measure?

OBSERVATION
What was detected from measurements?

INTERPRETATION
What might the observation mean?

HYPOTHESIS
What explanation is currently plausible?

BELIEF
What proposition does Novi currently accept provisionally?

KNOWLEDGE
What has sufficient evidence and validation for durable use?

DECISION
What should Novi do given uncertainty and risk?
```

---

## 3. Confidence Is Not Probability

A model score such as `0.92` must not automatically be described as:

> "92% probability that this is true."

A probability has a defined probabilistic interpretation. A model confidence score may not.

The semantic meaning of every numerical score must be explicitly defined.

---

## 4. Measurement Uncertainty

Physical measurements should represent uncertainty appropriate to the sensor and measurement model.

Examples:

```text
temperature = 24.1 °C ± uncertainty
position = estimated pose + covariance/quality
range = estimated distance + measurement uncertainty
```

The representation must match the underlying sensor and estimator rather than inventing precision.

---

## 5. Measurement vs Classification Uncertainty

These are different.

```text
LiDAR range uncertainty
        ≠
object-class uncertainty
```

A precise measurement can support an uncertain classification, and an uncertain measurement can sometimes still strongly constrain a class.

---

## 6. Evidence Quality

Evidence quality should be represented separately from belief confidence.

Useful dimensions include:

- source reliability;
- calibration state;
- directness;
- freshness;
- independence;
- context match;
- corroboration;
- contradiction;
- completeness;
- provenance integrity.

---

## 7. Source Reliability

Reliability should be contextual.

Example:

```text
thermal sensor
 → strong for internal component temperature
 → irrelevant for identifying a person's name
```

A source is not globally reliable for every proposition.

---

## 8. Evidence Independence

Multiple observations are not necessarily independent.

```text
camera A
camera B
same lighting failure
        ↓
correlated evidence
```

Confidence must not be inflated simply by counting correlated observations as separate proof.

---

## 9. Corroboration

Independent sources can strengthen a claim.

```text
camera
+
LiDAR
+
repeated observation
        ↓
stronger evidence
```

Corroboration must remain traceable through provenance.

---

## 10. Epistemic vs Aleatoric Uncertainty

Where practical, distinguish:

```text
EPISTEMIC
uncertainty caused by lack of knowledge

ALEATORIC
irreducible variability/noise in the phenomenon or process
```

This distinction matters because epistemic uncertainty may sometimes be reduced with additional information, while aleatoric variability may not.

---

## 11. Unknown Is First-Class

Novi must support:

```text
KNOWN
UNKNOWN
UNCERTAIN
CONFLICTED
NOT_APPLICABLE
NOT_OBSERVED
```

Unknown is not equivalent to false.

---

## 12. Open-World Assumption

Absence of evidence should not automatically become evidence of absence.

```text
no person detected
    ≠
no person exists
```

The distinction is particularly important with occlusion, sensor limitations and incomplete exploration.

---

## 13. Negative Evidence

Negative evidence is meaningful only relative to sensor coverage, sensitivity and context.

Example:

```text
no obstacle detected
```

must be interpreted together with:

- sensor field of view;
- occlusion;
- range;
- sensor health;
- localization quality.

---

## 14. Confidence Decomposition

For important claims, use structured components rather than one opaque number:

```text
source_reliability
observation_quality
semantic_confidence
identity_confidence
temporal_confidence
spatial_confidence
causal_confidence
freshness
corroboration
contradiction
```

The exact fields depend on claim type.

---

## 15. Composite Confidence

A composite score may be computed for ranking, but it must never replace the underlying evidence dimensions.

```text
composite_score
     ↓
retrieval/ranking aid
```

It should not be treated as universal truth probability.

---

## 16. Calibration

Whenever a model output is interpreted probabilistically, Novi must evaluate whether the output is calibrated.

Calibration means that predicted probabilities should correspond appropriately to observed frequencies. Reliability diagrams and calibration metrics can be used for evaluation. citeturn0search0turn0search6

---

## 17. Calibration Data

Calibration must use data representative of intended operating conditions.

Examples:

```text
indoor
outdoor
low light
bright light
moving robot
stationary robot
thermal variation
camera contamination
```

A model calibrated only in a laboratory is not automatically calibrated for Novi's home environment.

---

## 18. Calibration Drift

Calibration can degrade after:

- model changes;
- sensor replacement;
- camera repositioning;
- environment changes;
- firmware changes;
- distribution shift;
- long-term wear.

Novi should monitor calibration health.

---

## 19. Calibration Methods

Depending on model and task, candidates include:

- sigmoid/Platt-style calibration;
- isotonic regression;
- temperature scaling;
- task-specific probabilistic calibration.

The method must be selected and validated for the actual model/task rather than assumed universally superior. scikit-learn documents sigmoid and isotonic calibration and notes their different data requirements and behavior. citeturn0search1turn0search9

---

## 20. Brier Score and Log Loss

For probabilistic predictions, proper scoring rules such as Brier score and log loss can evaluate predictive quality. Brier score should not be interpreted as a pure calibration metric because it combines calibration/reliability, resolution and uncertainty-related effects. citeturn0search0turn0search12

Novi should therefore use multiple complementary evaluation measures.

---

## 21. Decision Confidence vs Prediction Confidence

A prediction may be uncertain while the correct action is still obvious.

Example:

```text
object identity uncertain
        ↓
keep distance
```

Conversely, a highly confident prediction may still require a conservative action if the consequence of being wrong is severe.

---

## 22. Risk Is Not Uncertainty

```text
UNCERTAINTY
How unsure is Novi?

RISK
How bad could the consequence be?
```

A low-probability event can still justify caution when its consequence is catastrophic.

---

## 23. Risk-Aware Thresholds

Decision thresholds should depend on:

- uncertainty;
- consequence severity;
- reversibility;
- action cost;
- safety policy;
- available verification;
- user expectations.

There must not be one universal confidence threshold for all actions.

---

## 24. Safety-Critical Actions

Safety-critical actions should require stronger evidence and/or additional verification.

Examples:

```text
move near person
cross hazardous area
activate high-power actuator
modify safety configuration
```

The exact thresholds belong to the safety architecture.

---

## 25. Reversible vs Irreversible Actions

A lower-confidence reversible action may sometimes be acceptable.

An irreversible or high-impact action requires substantially stronger evidence and authorization.

---

## 26. Ask vs Act

When uncertainty materially affects a user-level decision, Novi should consider:

```text
ACT
ASK
VERIFY
WAIT
DEFER
REFUSE
```

The choice depends on risk, cost and available evidence.

---

## 27. Active Perception

Novi may reduce uncertainty by acquiring additional information.

```text
uncertainty high
      ↓
choose informative observation
      ↓
new evidence
      ↓
uncertainty update
```

Examples:

- rotate camera;
- approach only when safe;
- use LiDAR;
- use thermal sensor;
- ask the user;
- wait for occlusion to clear.

---

## 28. Value of Information

Additional sensing should be prioritized when the expected information gain is useful relative to:

- time;
- energy;
- compute;
- thermal cost;
- safety risk;
- user disruption.

Novi should not endlessly gather information when it cannot change the decision.

---

## 29. Confidence Decay

Some confidence should decay with time when the underlying world can change.

```text
current door state
 → fast decay

historical birth date
 → no automatic decay
```

Decay policy is claim-specific.

---

## 30. Freshness

Freshness is a separate evidence dimension.

A highly reliable observation can still be stale.

```text
reliability = high
freshness = low
```

The resulting claim may be unsuitable for current control.

---

## 31. Temporal Scope

Claims should support:

- valid_from;
- valid_until;
- observed_at;
- last_confirmed_at;
- expected_refresh_interval where appropriate.

---

## 32. Spatial Scope

Confidence may also depend on location.

A perception model may perform differently:

```text
home
vs
outdoors
vs
unknown environment
```

Spatial scope should remain explicit.

---

## 33. Contextual Confidence

Confidence should be conditioned on relevant context.

```text
identity confidence
 + lighting
 + viewpoint
 + motion
 + occlusion
```

A global confidence number can hide important context failures.

---

## 34. Distribution Shift

Confidence can become unreliable when operating conditions differ from evaluation data.

Novi should monitor for:

- unfamiliar environments;
- sensor degradation;
- novel objects;
- lighting shifts;
- weather changes;
- unusual motion;
- model input anomalies.

NIST emphasizes testing under realistic expected-use conditions and external validity rather than relying only on benchmark accuracy. citeturn0search49

---

## 35. Out-of-Distribution Awareness

Where supported, models should expose or derive signals indicating inputs outside their validated operating distribution.

OOD detection is itself uncertain and must not be treated as perfect.

---

## 36. Novelty

Unknown objects or situations should be representable as:

```text
novel_entity
unknown_class
unfamiliar_context
```

Novi must not force every novel observation into a familiar class merely to obtain a confident label.

---

## 37. Conflicting Evidence

If evidence conflicts:

```text
source A → claim X
source B → claim not-X
```

Novi should preserve the conflict and evaluate:

- source reliability;
- temporal alignment;
- calibration;
- spatial alignment;
- sensor health;
- occlusion;
- independence.

---

## 38. Confidence Under Conflict

Conflict should generally reduce confidence in the affected claim until resolved or better qualified.

It should not be resolved by arbitrary averaging.

---

## 39. Confidence Propagation

Derived confidence must account for uncertainty in parent evidence.

```text
uncertain observation
      ↓
uncertain interpretation
      ↓
qualified memory
      ↓
qualified knowledge
```

No transformation may silently increase certainty without new supporting evidence.

---

## 40. Independence-Aware Fusion

Sensor fusion should account for correlated errors.

```text
camera 1
camera 2
same calibration fault
      ↓
not independent
```

Fusion algorithms should use the appropriate statistical assumptions for the estimator.

---

## 41. Sensor Health

Sensor-health state should influence confidence.

Possible states:

```text
HEALTHY
DEGRADED
UNKNOWN
FAILED
```

A failed sensor's output must not retain normal confidence.

---

## 42. Calibration Health

Calibration status should be part of evidence quality.

Examples:

- camera intrinsics;
- extrinsics;
- IMU calibration;
- LiDAR-camera transform;
- microphone-array geometry;
- thermal sensor calibration.

---

## 43. Confidence of Localization

Localization should expose uncertainty suitable for downstream use.

Examples:

```text
pose estimate
covariance / quality
localization mode
source set
map version
```

Navigation should not treat all poses as equally reliable.

---

## 44. Confidence of Identity

Person/object identity should support multiple hypotheses where necessary.

```text
candidate A: 0.60
candidate B: 0.30
unknown: 0.10
```

The exact numerical interpretation must be calibrated if treated probabilistically.

---

## 45. Identity Is Not Authorization

Even a high-confidence identity does not grant permission.

```text
identity confidence
       ≠
authorization
```

Authorization is governed by security policy.

---

## 46. Confidence in Language Understanding

Language interpretations should preserve ambiguity.

```text
"Put it there."
```

may have multiple candidate referents.

Novi should ask or use grounded context rather than inventing certainty.

---

## 47. LLM Confidence

Token probabilities, verbal certainty and fluent explanations are not sufficient evidence of factual confidence.

LLMs may propose hypotheses, interpretations and candidate explanations, but those outputs must be grounded through the evidence/provenance architecture.

---

## 48. Memory Confidence

A memory should distinguish at least:

```text
source evidence quality
memory admission confidence
identity confidence
temporal confidence
spatial confidence
semantic confidence
```

A vivid or detailed memory is not necessarily a reliable memory.

---

## 49. Knowledge Confidence

Durable knowledge should include:

- supporting evidence;
- provenance;
- validation state;
- scope;
- freshness;
- contradictions;
- confidence components;
- last review/update.

---

## 50. Confidence and Promotion

Confidence is an input to memory/knowledge promotion, not the sole criterion.

Promotion also requires appropriate provenance, evidence quality, policy compliance and scope.

---

## 51. Confidence and Learning

Learning updates should evaluate whether observed outcomes are sufficiently reliable to justify behavioral change.

One noisy outcome should not automatically lower a well-established skill.

---

## 52. Confidence and Causal Reasoning

Causal confidence should be separate from outcome confidence.

```text
route failed
 → high confidence

obstacle caused failure
 → moderate confidence
```

The first can be well established while the second remains uncertain.

---

## 53. Confidence and Counterfactuals

Counterfactual confidence must remain separate from factual confidence.

```text
real event confidence
      ≠
counterfactual confidence
```

A highly plausible simulation does not become historical fact.

---

## 54. Confidence and Simulation

Simulation evidence should include:

- simulator version;
- scenario;
- model assumptions;
- parameterization;
- environment;
- domain-gap limitations.

Simulation confidence cannot automatically transfer unchanged to reality.

---

## 55. Confidence Communication

Novi should communicate uncertainty in human-understandable terms when relevant:

```text
certain / verified
high confidence
moderate confidence
low confidence
uncertain
unknown
```

Numerical probabilities should be used only when their interpretation is meaningful.

---

## 56. Avoid False Precision

Do not say:

> "I am 87.341% sure."

unless the number has a validated probabilistic interpretation and the precision is justified.

---

## 57. Decision Thresholds Are Policy

A confidence value does not independently authorize action.

```text
confidence
 + uncertainty
 + risk
 + authority
 + context
 + safety
        ↓
policy decision
```

---

## 58. Confidence Monitoring

Novi should monitor confidence quality over time.

Metrics may include:

- calibration error;
- reliability diagrams;
- Brier score;
- log loss;
- false-positive/negative rates;
- uncertainty coverage;
- abstention quality;
- performance by environment;
- performance by sensor condition.

Calibration and discrimination should be evaluated separately where appropriate. citeturn0search0turn0search1

---

## 59. Abstention

Novi should be able to abstain from classification or decision when evidence is insufficient.

```text
insufficient evidence
      ↓
abstain
      ↓
verify / ask / defer / safe fallback
```

Abstention is a capability, not a failure.

---

## 60. Uncertainty Reduction

Novi should distinguish:

```text
uncertainty can be reduced
uncertainty cannot currently be reduced
uncertainty is irrelevant to this decision
```

This prevents unnecessary sensing and computation.

---

## 61. Confidence Budget

Background uncertainty analysis must respect:

- compute;
- memory;
- energy;
- thermal limits;
- latency;
- current task priority.

Safety-critical uncertainty receives priority.

---

## 62. Offline Operation

The confidence and uncertainty framework must operate locally without Wi-Fi, Bluetooth or cloud access.

Cloud-based calibration or evaluation may be used only where a local solution is unavailable and the architecture explicitly permits it.

---

## 63. Vendor-Neutral Implementation

Potential implementation components include:

```text
NVIDIA Isaac / Isaac ROS
PyTorch
TensorFlow
OpenCV
ONNX Runtime
Hugging Face
ROS 2
custom estimators
```

No vendor's confidence representation becomes Novi's canonical uncertainty model.

---

## 64. Canonical Internal Representation

Novi should expose a vendor-neutral semantic representation such as:

```text
Claim
 ├── proposition
 ├── status
 ├── evidence_refs
 ├── source_quality
 ├── uncertainty
 ├── scope
 ├── temporal_validity
 ├── spatial_validity
 ├── calibration_state
 ├── contradiction_refs
 ├── provenance
 └── decision_relevance
```

The exact schema belongs to the implementation phase.

---

## 65. Testing Requirements

Test:

- sensor uncertainty;
- calibration;
- probability calibration;
- reliability diagrams;
- Brier/log loss;
- confidence under distribution shift;
- sensor degradation;
- correlated sensor errors;
- conflicting evidence;
- stale evidence;
- uncertainty propagation;
- localization confidence;
- object identity confidence;
- language ambiguity;
- LLM overconfidence;
- abstention;
- active perception;
- risk-aware decisions;
- simulation/real separation;
- model migration;
- long-term calibration drift;
- offline operation;
- low compute/thermal conditions;
- restart recovery.

---

## 66. Failure Modes

The architecture must explicitly handle:

```text
OVERCONFIDENT
UNDERCONFIDENT
UNCALIBRATED
UNKNOWN
CONFLICTED
STALE
CORRELATED_EVIDENCE
SENSOR_DEGRADED
OOD
MISSING_PROVENANCE
INVALID_UNCERTAINTY
FALSE_PRECISION
```

These states should be observable in diagnostics.

---

## 67. Architectural Invariants

1. Confidence is not automatically probability.
2. Measurement uncertainty is not classification confidence.
3. Evidence quality is not belief confidence.
4. Risk is not uncertainty.
5. Unknown is not false.
6. Absence of detection is not automatically absence.
7. Correlated evidence must not be counted as independent proof.
8. Confidence cannot override safety policy.
9. Identity confidence cannot grant authorization.
10. LLM fluency is not factual confidence.
11. Counterfactual confidence is not historical certainty.
12. Simulation confidence does not automatically transfer to reality.
13. Uncertainty must propagate through derived representations.
14. Important probabilities require calibration evidence.
15. Calibration must be evaluated under representative operating conditions.
16. Confidence should be contextual and claim-specific.
17. High-risk actions require stronger evidence than low-risk actions.
18. Novi can abstain, ask, verify or defer.
19. Confidence representations remain vendor-neutral.
20. Offline operation remains fully supported.
21. Important uncertainty and calibration state are auditable.
22. No single composite score may replace the underlying evidence dimensions.
23. False precision is prohibited.
24. New evidence may revise confidence without rewriting historical observations.

---

## 68. Final Principle

> **Novi should not merely know an answer; it should know how uncertain that answer is, why it believes it, what could make it wrong, and whether that uncertainty matters for the decision at hand.**

This creates the uncertainty layer required for Novi to evolve safely: evidence remains distinguishable from belief, probability from confidence, uncertainty from risk, and prediction from verified knowledge.
