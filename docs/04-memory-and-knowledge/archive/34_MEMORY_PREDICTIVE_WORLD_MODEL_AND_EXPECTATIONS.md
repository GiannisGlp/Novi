# 34 — Memory Predictive World Model and Expectations

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi represents expectations about what may happen next, compares predictions with observations, records prediction errors, and uses those errors to improve perception, world knowledge, planning and autonomy.

This document defines an architectural capability, not a claim that Novi possesses consciousness. A predictive world model is a computational model used to anticipate state transitions and improve decisions.

## Core Principle

> **Novi should maintain explicit, uncertainty-aware expectations about the world and itself, but an expectation must never be treated as an observation or fact merely because the model predicted it.**

## 1. Why a Predictive Model Exists

Reactive behavior only answers:

```text
What is happening now?
```

A predictive system can additionally ask:

```text
What is likely to happen next?
What should happen if I take this action?
What changed unexpectedly?
What should I verify?
```

Prediction therefore supports planning, anomaly detection, active perception and learning.

## 2. World Model Layers

Novi should distinguish several predictive layers:

```text
PHYSICAL STATE
   ↓
OBSERVED STATE
   ↓
ESTIMATED STATE
   ↓
PREDICTED STATE
   ↓
EXPECTED OUTCOME
```

The distinction between observed, estimated and predicted state is mandatory.

## 3. World State Representation

The model may represent:

- objects;
- people where authorized;
- places;
- surfaces;
- obstacles;
- robot pose;
- environmental conditions;
- temperature;
- illumination;
- audio context;
- routes;
- object states;
- active goals;
- relevant system state.

It should not attempt to model every physical variable when doing so provides no useful decision value.

## 4. Predictive State

A prediction should include at minimum:

```text
prediction_id
subject/entity
predicted variable
prediction time
prediction horizon
expected value/range
uncertainty
model/version
context references
created_at
valid_until
```

Predictions are time-bound and context-bound.

## 5. Point Predictions vs Distributions

Where practical, Novi should represent uncertainty as a distribution or interval rather than a single value.

Instead of:

```text
person will arrive at 18:00
```

prefer:

```text
arrival window: 17:50–18:15
confidence/calibration metadata: ...
```

The representation depends on the prediction task.

## 6. Prediction Confidence Is Not Truth

A high-confidence prediction is still a prediction.

```text
confidence = 0.95
        ≠
observed = true
```

When an observation contradicts a prediction, the observation and its provenance must remain distinct.

## 7. Temporal Horizons

Predictions should be classified by horizon:

```text
milliseconds → control
seconds       → reactive autonomy
minutes       → task planning
hours         → routines/context
months        → long-term learned patterns
```

Longer horizons generally require stronger uncertainty handling.

## 8. Spatial Prediction

For Novi's spatial memory, predictions may include:

- expected location;
- expected route;
- expected obstacle position;
- expected landmark visibility;
- expected map change;
- expected travel time;
- expected GNSS availability.

Spatial predictions must carry coordinate-frame and uncertainty information.

## 9. Self-Prediction

Novi may predict its own state:

```text
battery after planned trip
thermal state after workload
localization quality
motor state
sensor availability
storage usage
```

Self-predictions must use authoritative telemetry for validation.

## 10. Action-Conditioned Prediction

The most important predictive capability for autonomy is:

```text
If I perform action A,
what is likely to happen?
```

Example:

```text
Action: move forward 0.5 m
Expected: free-space motion
Observed: obstacle detected
```

The discrepancy becomes evidence for replanning and learning.

## 11. Prediction Context

A prediction must record the context on which it depended.

Relevant context can include:

- current world state;
- current goal;
- selected plan;
- retrieved memories;
- model version;
- policy version;
- sensor state;
- resource state.

This prevents later evaluation from pretending that the prediction was made under today's conditions.

## 12. Prediction Event

Predictions should generate structured events when they matter to memory, autonomy or evaluation.

Example:

```text
prediction.created
prediction.updated
prediction.invalidated
prediction.confirmed
prediction.contradicted
prediction.expired
```

Not every internal numerical prediction requires durable storage.

## 13. Prediction Error

Prediction error is the discrepancy between expected and observed outcomes.

Conceptually:

```text
prediction
    ↓
observation
    ↓
comparison
    ↓
prediction error
```

The comparison must account for uncertainty, timing and measurement quality.

## 14. Surprise

Surprise should be treated as a measurable model discrepancy, not automatically as an emotional state.

Potential causes include:

- unexpected object;
- unexpected movement;
- unexpected temperature;
- unexpected person behavior;
- map change;
- sensor failure;
- model failure;
- environmental transition.

## 15. Surprise Must Be Diagnosed

A large prediction error does not automatically mean the world changed.

It may indicate:

```text
world changed
OR
sensor failed
OR
localization failed
OR
model was wrong
OR
context was incomplete
```

Novi should evaluate competing explanations before promoting surprise into knowledge.

## 16. Prediction Error as Learning Signal

Repeated, well-grounded prediction errors can indicate that a model or expectation needs improvement.

```text
prediction error
      ↓
classification
      ↓
repeatability check
      ↓
root-cause analysis
      ↓
learning candidate
```

A single unexpected observation should not automatically retrain a model.

## 17. Prediction Error and Memory

Significant prediction errors may become episodic memories when they are relevant to future behavior.

Example:

```text
expected route clear
        ↓
unexpected obstacle
        ↓
action/replan
        ↓
experience
        ↓
possible future route knowledge
```

The memory should preserve what was expected and what actually occurred.

## 18. Prediction Error and Knowledge

Repeated evidence may produce semantic knowledge.

```text
many predictions
      ↓
consistent deviations
      ↓
pattern
      ↓
knowledge candidate
```

Example:

```text
Route normally takes 5 minutes
Observed repeatedly: 8–10 minutes
        ↓
updated travel-time estimate
```

The system must preserve uncertainty and supporting evidence.

## 19. Expectation Types

Initial expectation categories:

- physical;
- spatial;
- temporal;
- social/interactional where appropriate;
- task;
- sensory;
- system-health;
- resource;
- user-routine;
- goal outcome;
- action outcome.

Social predictions require particularly careful privacy and uncertainty controls.

## 20. Learned Expectations

Expectations may be learned from repeated observations.

Example:

```text
Repeated observation:
front door usually opens after user approaches

Learned expectation:
door may open after approach
```

The expectation remains probabilistic and context-dependent.

## 21. Routine Detection

Novi may detect recurring patterns such as:

- typical household activity;
- recurring routes;
- common object locations;
- recurring environmental changes.

Routine inference must not be treated as certainty and must respect privacy policy.

## 22. Expectations About People

Predictions about people should be conservative.

Novi should avoid converting behavioral patterns into unsupported conclusions about intent, emotion, health or identity.

Example:

```text
Observed:
user usually leaves at 08:00

Permitted expectation:
user may leave around 08:00

Not justified automatically:
user intends to leave today
```

## 23. Expectation Expiration

Predictions must expire.

A prediction becomes stale when:

- its time horizon passes;
- relevant context changes;
- the underlying entity changes;
- the model is invalidated;
- sensor quality falls below threshold.

Stale predictions must not influence current decisions as if fresh.

## 24. Model Versioning

Every persisted prediction must identify the model/configuration that produced it.

A model update should not silently rewrite historical predictions.

New model evaluation may generate new prediction records.

## 25. Prediction Calibration

Novi should measure whether confidence corresponds to actual outcomes.

For example:

```text
predictions labeled 90% confidence
        ↓
actual success rate
        ↓
calibration assessment
```

Poor calibration should reduce trust in confidence estimates even when raw accuracy appears acceptable.

## 26. Prediction Quality Metrics

Metrics may include:

- accuracy;
- precision/recall where applicable;
- calibration;
- mean absolute error;
- probabilistic scoring rules;
- false-alarm rate;
- missed-event rate;
- prediction latency;
- horizon-dependent performance;
- performance under distribution shift.

Metrics must match the prediction task.

## 27. World-Model Drift

Prediction performance can degrade when the environment changes.

Potential indicators:

```text
rising prediction error
rising uncertainty
systematic residuals
changed sensor distribution
changed route behavior
changed environment
```

Drift should trigger evaluation, not uncontrolled self-retraining.

## 28. Active Perception

Prediction can guide what Novi should observe next.

Example:

```text
uncertain object identity
        ↓
choose camera angle / sensor
        ↓
obtain observation
        ↓
reduce uncertainty
```

This creates a closed loop:

```text
predict → observe → compare → act → observe again
```

## 29. Information Gain

When multiple observations are possible, Novi may prioritize those expected to reduce important uncertainty.

The exact information-gain calculation is implementation-specific.

The system must still consider:

- safety;
- privacy;
- power;
- compute;
- time;
- sensor wear;
- user expectations.

## 30. Prediction and Planning

Planning should use predictions to estimate action outcomes.

```text
current state
   ↓
candidate actions
   ↓
predict outcomes
   ↓
evaluate risk/utility
   ↓
select plan
```

Prediction must not override independent safety constraints.

## 31. Prediction and Goals

A goal creates conditional expectations.

Example:

```text
Goal: reach kitchen

Plan: move through hallway

Prediction:
robot reaches kitchen within expected time/range
```

If the prediction fails, Novi should re-evaluate the goal and plan rather than treating failure as proof that the goal is invalid.

## 32. Counterfactuals

The architecture may support hypothetical predictions:

```text
What would likely happen if I chose route B?
```

Counterfactual predictions must be explicitly marked as hypothetical.

They must never be stored as observations.

## 33. Simulation

Simulation can generate training/evaluation predictions, but simulated evidence must be marked as simulated.

```text
source = simulation
```

must never be silently represented as:

```text
source = physical observation
```

## 34. Predictive Memory Retrieval

Memory retrieval may use predictions to select relevant history.

Example:

```text
prediction:
route may be blocked

retrieve:
previous observations of route obstruction
```

Prediction should guide retrieval without manufacturing evidence.

## 35. Predictive Spatial Memory

For places, Novi may store:

- expected landmarks;
- expected routes;
- expected occupancy patterns;
- expected environmental conditions;
- historical change rates.

This supports recognition of changes between visits.

## 36. Prediction and Map Change

If a known environment differs from expectation:

```text
expected map
      ↓
new observation
      ↓
difference
      ↓
map-change candidate
```

Map updates require appropriate validation to avoid corrupting persistent maps from transient sensor errors.

## 37. Prediction and Sensor Faults

Unexpected observations can be used to detect sensor problems.

Example:

```text
camera predicts visible landmark
LiDAR/GNSS disagree
camera repeatedly fails
        ↓
sensor-health candidate
```

Independent evidence should be preferred where available.

## 38. Prediction and Thermal State

Novi can predict thermal consequences of workloads:

```text
model inference workload
        ↓
predicted thermal rise
        ↓
resource governor
```

Thermal sensors remain authoritative for actual temperature.

Prediction cannot override thermal safety controls.

## 39. Prediction and Power

Similarly:

```text
planned activity
        ↓
expected energy consumption
        ↓
battery prediction
        ↓
planning decision
```

Actual BMS measurements remain authoritative.

## 40. Prediction and Network Availability

Novi may predict connectivity based on history, but network state must always be determined from current observation.

```text
expected Wi-Fi
      ≠
current Wi-Fi
```

This reinforces the offline-first architecture.

## 41. Prediction Storage

Persist only predictions that have cognitive, operational, evaluation or audit value.

Short-lived control predictions may remain in memory.

Long-lived expectations should enter the memory architecture with provenance and retention policy.

## 42. Prediction Lifecycle

A prediction may follow:

```text
CREATED
  ↓
ACTIVE
  ↓
CONFIRMED
```

or:

```text
CREATED
  ↓
CONTRADICTED
  ↓
ANALYZED
```

or:

```text
CREATED
  ↓
EXPIRED
```

Additional states may be introduced when implementation requires them.

## 43. Contradiction Handling

When a prediction fails, Novi should record:

- prediction;
- observation;
- time difference;
- uncertainty;
- sensor quality;
- context;
- model version;
- likely cause;
- resulting action.

This creates a learning-quality record rather than simply incrementing an error counter.

## 44. Prediction Poisoning

Malicious or incorrect data can distort learned expectations.

Protection should include:

- source provenance;
- trust weighting;
- corroboration;
- outlier handling;
- temporal decay where appropriate;
- anomaly detection;
- bounded learning rates;
- protected baseline models.

Repeated malicious observations must not automatically become trusted because of repetition alone.

## 45. Human/User Corrections

An authorized user may correct an expectation or resulting knowledge.

The correction should create explicit evidence:

```text
prediction/knowledge correction
      ↓
new authoritative event
```

Historical predictions remain auditable according to policy.

## 46. Safety Boundary

Predictions can inform planning but cannot override safety.

```text
world prediction
      ↓
planning
      ↓
safety validation
      ↓
action
```

Safety remains authoritative.

## 47. Security Boundary

Prediction models and their learned state are protected assets.

Unauthorized modification can change future behavior even without changing explicit rules.

Model updates therefore follow the model-integrity and learning-governance architecture.

## 48. Privacy Boundary

Predictive models can expose sensitive patterns even without storing raw data.

Examples:

- household routines;
- presence/absence patterns;
- location habits;
- movement patterns.

Predictive memory must therefore inherit privacy classification from its evidence and intended use.

## 49. No Unrestricted Self-Prediction

Novi may model its own future state, but self-prediction must not become self-authorizing logic.

Example:

```text
prediction:
"I will probably remain safe."
```

cannot substitute for a safety check.

## 50. Learning Loop

The complete learning loop is:

```text
observe
  ↓
estimate state
  ↓
predict
  ↓
act / wait
  ↓
observe outcome
  ↓
compare
  ↓
prediction error
  ↓
diagnose
  ↓
learn candidate
  ↓
evaluate
  ↓
approved update
  ↓
new predictions
```

The evaluation gate is essential.

## 51. Separation of Online and Offline Learning

Online adaptation may update bounded, approved parameters or short-term expectations.

More consequential model changes should normally be evaluated offline or in a controlled staging path before deployment.

The exact boundary depends on model class and safety impact.

## 52. Resource Governance

Prediction workloads must obey the resource budgets defined elsewhere.

Under pressure, Novi may reduce:

- prediction horizon;
- model complexity;
- prediction frequency;
- background forecasting;
- long-term expectation updates.

Core safety and autonomy workloads remain protected.

## 53. Failure Modes

The system must handle:

- stale predictions;
- overconfident predictions;
- systematic model bias;
- sensor failure mistaken for world change;
- world change mistaken for sensor failure;
- prediction poisoning;
- model drift;
- insufficient data;
- missing context;
- clock errors;
- synchronization delays;
- resource exhaustion;
- corrupted predictive state.

## 54. Testing Requirements

Test:

- prediction accuracy;
- calibration;
- uncertainty representation;
- temporal horizons;
- spatial predictions;
- action-conditioned predictions;
- prediction error detection;
- stale prediction rejection;
- sensor-fault discrimination;
- map-change detection;
- active perception;
- model drift;
- poisoning resistance;
- replay;
- offline operation;
- thermal/power adaptation;
- resource pressure;
- privacy controls;
- security boundaries.

## 55. Architectural Invariants

1. A prediction is never an observation.
2. Predicted, estimated and observed states remain distinguishable.
3. Predictions carry time horizon and uncertainty where applicable.
4. Predictions are context-bound.
5. Historical predictions retain model/configuration provenance.
6. Stale predictions cannot silently influence current decisions.
7. Prediction error does not automatically imply world change.
8. Prediction error does not automatically trigger model retraining.
9. Repeated evidence is required for consequential learned expectations.
10. Simulated predictions are never represented as physical observations.
11. Counterfactual predictions remain explicitly hypothetical.
12. Safety authority remains independent of prediction.
13. Predictive learning is subject to memory security and governance.
14. Predictive state is subject to privacy controls.
15. Predictive workloads obey resource governance.
16. Prediction systems must remain functional in degraded/offline operation where required.

## 56. Final Principle

> **Prediction gives Novi a model of what might happen next; observation determines what actually happened; learning improves the model only after the difference has been understood and evaluated.**

This separation allows Novi to become increasingly anticipatory and adaptive while preserving the distinction between expectation, evidence and fact.