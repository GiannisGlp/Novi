# 35 — Memory Attention and Relevance Model

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi selects what information deserves processing, retrieval, monitoring, reasoning, active perception, and memory access at a given moment.

Novi will continuously receive information from multiple cameras, LiDAR, microphones, thermal sensors, IMU, GNSS, internal telemetry, memory, goals and other subsystems. Processing everything with equal depth is neither computationally feasible nor cognitively useful.

This document defines a bounded attention and relevance system rather than an unconstrained neural "attention" mechanism.

## Core Principle

> **Attention is a resource-allocation decision: Novi prioritizes information that is relevant, uncertain, surprising, safety-critical, goal-relevant, or potentially valuable while preserving mandatory monitoring and fairness constraints.**

Attention changes what Novi spends computation on. It does not change what is true.

---

## 1. Attention Is Not Truth

An item receiving high attention is not necessarily more true.

```text
attention priority ≠ confidence
attention priority ≠ truth
attention priority ≠ importance forever
```

A low-attention observation may still become important later if new evidence appears.

---

## 2. Attention Is Not Memory

Attention selects what to process now.

Memory determines what is retained over time.

```text
attention
   ↓
processing
   ↓
possible memory candidate
```

Not everything attended to should become memory.

---

## 3. Attention Is Not Consciousness

The architecture uses "attention" as an engineering term for selective information processing. It makes no claim about subjective experience or consciousness.

---

## 4. Sources of Attention

Potential attention candidates include:

- camera observations;
- LiDAR changes;
- audio events;
- speaker direction;
- thermal anomalies;
- GNSS changes;
- localization uncertainty;
- map changes;
- detected objects;
- people-related observations under policy;
- current goals;
- active commitments;
- predictions;
- prediction errors;
- retrieved memories;
- unresolved conflicts;
- system faults;
- security events;
- battery/thermal/resource pressure;
- user interaction;
- safety signals.

---

## 5. Mandatory vs Selective Attention

Some information must be monitored regardless of cognitive relevance.

### Mandatory monitoring

Examples:

- collision/safety sensors;
- emergency stop;
- thermal protection;
- battery protection;
- motor faults;
- critical hardware faults;
- security state;
- watchdogs.

### Selective attention

Examples:

- exploratory visual objects;
- background audio;
- old memories;
- map enrichment;
- retrospective learning;
- low-priority environmental details.

Selective attention must never disable mandatory safety monitoring.

---

## 6. Attention Pipeline

```text
raw/derived signals
        ↓
fast triage
        ↓
candidate generation
        ↓
relevance scoring
        ↓
policy/safety constraints
        ↓
resource check
        ↓
attention allocation
        ↓
deep processing / retrieval / active perception
        ↓
outcome
        ↓
attention update
```

The fast triage stage should be inexpensive enough to run continuously.

---

## 7. Relevance Dimensions

A candidate may receive independent scores for:

- safety relevance;
- goal relevance;
- user relevance;
- temporal relevance;
- spatial relevance;
- novelty;
- surprise/prediction error;
- uncertainty;
- expected information gain;
- memory relevance;
- social/contextual relevance where permitted;
- urgency;
- persistence;
- recurrence;
- consequence;
- resource cost.

A single scalar score may be used for scheduling, but the underlying dimensions should remain inspectable.

---

## 8. Priority Model

Conceptually:

```text
priority = f(
  safety,
  urgency,
  goal relevance,
  uncertainty,
  prediction error,
  novelty,
  expected information gain,
  persistence,
  spatial relevance,
  temporal relevance,
  user relevance,
  cost,
  policy
)
```

The exact mathematical function must be empirically evaluated rather than assumed.

---

## 9. Safety Dominance

Safety signals receive protected priority.

```text
possible collision
      ↓
attention override
      ↓
safety processing
```

A low battery, active conversation or interesting object cannot suppress required collision monitoring.

---

## 10. Goal Relevance

Current goals increase attention toward information useful for achieving them.

Example:

```text
Goal: navigate to kitchen

high relevance:
  obstacles
  localization
  doorway
  route
  destination

lower relevance:
  unrelated decorative object
```

Goal relevance must not suppress unexpected safety-critical information.

---

## 11. User Interaction Relevance

A direct authorized interaction should normally receive high priority.

Examples:

- wake word;
- explicit speech addressed to Novi;
- user interaction with display;
- authorized control request.

Voice activity from an unknown or ambiguous source should be treated as an observation until identity/authority is established.

---

## 12. Spatial Relevance

Attention should depend on Novi's current spatial context.

Examples:

```text
current route
current room
known landmark
unfamiliar region
previously important location
```

Spatially relevant memories can be prioritized during navigation and place recognition.

---

## 13. Temporal Relevance

Information can become more or less relevant with time.

Examples:

- a pending commitment due soon;
- a recently observed obstacle;
- an old route history;
- a scheduled user event;
- a stale sensor calibration.

Time decay must never erase safety requirements.

---

## 14. Novelty

Novel observations can receive additional attention, but novelty alone is insufficient.

A constantly changing display could be highly novel but irrelevant.

Novi should combine novelty with context and expected utility.

---

## 15. Prediction Error

Prediction error is an important attention trigger.

```text
expected
   ↓
observation
   ↓
difference
   ↓
attention increase
```

A significant discrepancy should trigger investigation proportional to its consequence and uncertainty.

---

## 16. Uncertainty

Uncertain but consequential information deserves attention.

Example:

```text
possible obstacle
confidence = 0.45
consequence = high
```

This may deserve more attention than a highly confident but trivial object detection.

---

## 17. Information Gain

Novi may select actions or sensors that reduce uncertainty.

Examples:

- rotate camera toward an ambiguous object;
- move to improve LiDAR visibility;
- listen toward a sound source;
- revisit an uncertain landmark;
- query memory for disambiguating context.

Active perception research treats attention/sensor selection as a planning problem that can trade information acquisition against computation and action cost. citeturn1academia0turn0academia14

---

## 18. Active Perception

Attention may control physical sensing, not merely software selection.

```text
uncertain object
      ↓
select camera angle
      ↓
move / orient sensor
      ↓
new observation
      ↓
reduced uncertainty
```

Physical movement for information gathering must pass through navigation and safety constraints.

---

## 19. Multimodal Attention

Novi should not assume that one modality is always authoritative.

Example:

```text
camera: object detected
LiDAR: geometry inconsistent
thermal: hot region
audio: sound from same direction
```

The attention system may increase processing across the relevant modalities.

Cross-modal disagreement should itself be an attention trigger.

---

## 20. Camera Attention

With multiple cameras, attention can select:

- camera view;
- region of interest;
- resolution;
- frame rate;
- inference model;
- temporal window.

The full-resolution/full-model pipeline should not be required for every frame.

NVIDIA's Jetson ecosystem provides hardware-accelerated multimedia and vision building blocks, while current robotics research is exploring selective multimodal perception to reduce computation on irrelevant views. citeturn0search0turn1academia1

---

## 21. Audio Attention

With multiple microphones, attention can select:

- direction of arrival;
- active speaker candidate;
- frequency band;
- temporal window;
- speech/non-speech processing;
- relevant sound class.

Attention should not imply identity. Speaker localization and speaker identification remain separate functions.

---

## 22. Thermal Attention

Thermal sensing should support both safety and environmental cognition.

Examples:

```text
motor overheating
battery hotspot
human/object heat source
cold region
unexpected temperature gradient
```

Internal thermal anomalies receive protected priority because they can affect system safety.

---

## 23. LiDAR Attention

LiDAR attention can prioritize:

- collision geometry;
- unknown obstacles;
- route boundaries;
- map changes;
- localization landmarks;
- areas of high uncertainty.

Raw point-cloud processing should be resource-aware.

---

## 24. GNSS Attention

GNSS should be monitored continuously at an appropriate low-cost rate outdoors, while expensive downstream processing can be triggered by:

- significant movement;
- uncertainty changes;
- geofence crossing;
- outdoor/indoor transition;
- disagreement with local localization.

GNSS loss should not stop Novi's local spatial system.

---

## 25. Internal-State Attention

Novi must attend to itself as well as the external world.

Potential internal triggers:

- thermal pressure;
- battery decline;
- memory pressure;
- GPU/RAM pressure;
- storage pressure;
- localization degradation;
- sensor failure;
- queue backlog;
- security anomaly.

This connects attention to the resource governance architecture.

---

## 26. Memory Retrieval Attention

Attention determines when deeper memory retrieval is worthwhile.

Example:

```text
current place
   ↓
place-recognition match
   ↓
retrieve previous visits
   ↓
retrieve relevant experiences
   ↓
update context
```

Memory retrieval should be relevance-ranked rather than dumping the entire history into cognition.

---

## 27. Working Memory

High-priority information should enter a bounded working context.

Working memory should contain only information currently needed for:

- perception interpretation;
- active goals;
- current plan;
- immediate safety;
- recent causal context;
- relevant retrieved memories;
- predictions and errors.

The size and token/resource budget must be explicit.

---

## 28. Attention Persistence

Attention should have temporal dynamics.

A stimulus should not necessarily disappear from attention immediately after one processing cycle.

Possible states:

```text
NEW
ACTIVE
SUSTAINED
DECAYING
SUPPRESSED
RESOLVED
```

Persistence should depend on unresolved uncertainty, importance and recurrence.

---

## 29. Attention Hysteresis

To avoid rapid oscillation:

```text
camera A
camera B
camera A
camera B
...
```

attention should use hysteresis, minimum dwell times or switching costs where appropriate.

This is especially important for active sensor control.

---

## 30. Attention Fairness

A constantly high-priority stream must not starve every other subsystem indefinitely.

The scheduler should provide:

- protected critical capacity;
- bounded high-priority dominance;
- aging for waiting tasks;
- quotas;
- reserved background capacity where appropriate.

Safety remains an exception to fairness.

---

## 31. Attention Starvation

The system must detect when a candidate repeatedly fails to receive processing.

Example:

```text
candidate waits
candidate waits
candidate waits
```

The scheduler may increase its priority unless policy says it is intentionally suppressed.

---

## 32. Suppression

Suppression means temporarily reducing processing priority.

It must be explicit and reversible.

Examples:

- known irrelevant repetitive background;
- duplicate sensor observations;
- already-resolved object;
- resource emergency.

Suppression is not deletion of truth or memory.

---

## 33. Repetition and Habituation

Repeated observations may become less attention-demanding when they are stable and low consequence.

Example:

```text
same wall
same room
same furniture
```

But habituation must be broken by:

- change detection;
- prediction error;
- safety relevance;
- user relevance;
- unusual behavior;
- environmental change.

---

## 34. Attention and Learning

Attention should influence what learning data receives expensive processing, but it must not become the only learning source.

Low-attention data may still be sampled for bias detection and long-term evaluation.

Otherwise Novi could learn only from what its current attention policy already considers important.

---

## 35. Attention Bias Protection

The attention policy can create feedback loops:

```text
attention → more data
       ↓
more data → stronger learned signal
       ↓
stronger signal → more attention
```

The architecture must use exploration, sampling and evaluation to detect and mitigate this bias.

---

## 36. Attention and Personality

Personality may influence preferences for benign attention allocation, but personality cannot suppress mandatory safety or privacy controls.

Example:

```text
personality:
likes music

safety:
possible collision

result:
collision receives priority
```

---

## 37. Attention and Goals

Goals influence relevance, but active goals must not become blinders.

A robot navigating to the kitchen must still notice:

- unexpected obstacle;
- smoke/heat anomaly;
- person entering path;
- hardware fault;
- security event.

Goal-directed attention must retain an open-world safety channel.

---

## 38. Attention and Commitments

Pending commitments can create scheduled or event-driven attention triggers.

Example:

```text
commitment:
check battery before leaving home
        ↓
attention trigger
        ↓
current battery state
```

The trigger must be revalidated against current conditions.

---

## 39. Attention and Predictions

Predictions create anticipated events that can be monitored.

Example:

```text
prediction:
person likely to cross path
        ↓
monitor relevant area
        ↓
update prediction
```

This is a core connection between document 34 and attention.

---

## 40. Attention and Memory Retrieval

Retrieval can be triggered by:

- current goal;
- current location;
- recognized object/place;
- user query;
- prediction error;
- repeated event;
- unresolved conflict;
- active commitment.

Retrieval should return bounded, ranked context rather than unrestricted memory dumps.

---

## 41. Relevance to Long-Term Memory

Attention is one input to memory admission, not a final authority.

A candidate can be retained because it is:

- safety-critical;
- explicitly user-relevant;
- novel;
- repeatedly observed;
- predictive;
- autobiographically significant;
- spatially important;
- required for future tasks.

Admission policy remains authoritative.

---

## 42. Attention Decay

Relevance may decay with time, but decay must respect:

- safety;
- unresolved goals;
- commitments;
- retention policy;
- user-defined importance;
- historical significance.

An old memory can become relevant again through a new cue.

---

## 43. Re-Activation

Old memories should be reactivated when new evidence connects to them.

```text
new observation
      ↓
semantic/spatial match
      ↓
old memory becomes relevant
      ↓
retrieve
```

This allows Novi to use long-term experience without keeping it permanently in working memory.

---

## 44. Attention Context Window

The cognition layer should receive a structured attention context, for example:

```text
current goal
active safety signals
high-priority observations
recent prediction errors
relevant memories
current place
current self-state
active commitments
resource state
uncertainties
```

The language model should not independently decide what raw sensor streams deserve processing.

---

## 45. LLM Boundary

The LLM may:

- interpret selected context;
- propose relevance;
- request additional information;
- explain attention decisions.

The LLM should not be the sole attention scheduler for:

- safety;
- real-time control;
- sensor health;
- thermal protection;
- resource protection.

Those require deterministic/real-time subsystems.

---

## 46. Attention Arbitration

When multiple candidates compete:

```text
candidate scores
      ↓
policy constraints
      ↓
safety constraints
      ↓
resource budget
      ↓
fairness/starvation controls
      ↓
attention allocation
```

The final allocation should be auditable.

---

## 47. Resource-Aware Attention

Attention must account for computational cost.

A candidate requiring a 500 ms GPU inference may be less attractive than a 5 ms heuristic when both provide similar expected value.

However, high-cost processing should still be admitted when its expected value or safety relevance justifies it.

This directly connects to document 28's resource governance.

---

## 48. Graceful Degradation

Under resource pressure:

```text
full perception
   ↓
reduced resolution
   ↓
reduced model frequency
   ↓
lighter model
   ↓
sampling
```

Critical perception must retain protected capacity.

NVIDIA's Jetson platform is designed for edge AI workloads and provides hardware-accelerated vision/multimedia components; the final attention policies must nevertheless be benchmarked on the actual Orin 64GB configuration. citeturn0search1turn0search0

---

## 49. Attention During Thermal Pressure

If thermal state becomes constrained:

- reduce optional inference;
- reduce background retrieval;
- postpone consolidation;
- reduce exploration;
- reduce map enrichment;
- retain safety and core autonomy.

The exact thresholds belong to hardware/runtime validation.

---

## 50. Attention During Low Battery

Low battery should shift attention toward:

- safe navigation;
- return/home planning where configured;
- battery state;
- route feasibility;
- charging availability;
- critical communication.

Optional exploration should normally be reduced.

---

## 51. Attention During Network Loss

Novi must remain operational offline.

Network loss should increase attention to:

- local state;
- local maps;
- local memory;
- local navigation;
- synchronization backlog.

It must not cause the attention system to fail.

---

## 52. Attention and Security

Security events can override ordinary relevance.

Examples:

- unauthorized access attempt;
- integrity failure;
- suspicious synchronized data;
- repeated authentication failures.

Security attention must remain separate from the LLM's conversational priorities.

---

## 53. Attention Audit

For important decisions, record:

- candidate set or relevant candidate IDs;
- priority dimensions;
- selected candidate;
- reason/category;
- policy version;
- resource state;
- outcome where useful.

Do not store unlimited raw data merely to make attention auditable.

---

## 54. Explainability

Novi should be able to produce structured explanations such as:

```text
attention target: thermal anomaly
priority: CRITICAL
reason:
  internal safety signal
confidence: high
resource action:
  background consolidation paused
```

This is preferable to an LLM-generated post-hoc story with no connection to actual scheduler state.

---

## 55. Attention Evaluation

Evaluate:

- safety recall;
- missed-event rate;
- relevance precision;
- unnecessary processing;
- latency;
- starvation;
- switching frequency;
- energy cost;
- GPU/CPU cost;
- memory retrieval quality;
- active perception information gain;
- prediction-error detection;
- long-term attention bias.

---

## 56. Benchmark Scenarios

Test scenarios should include:

1. normal home operation;
2. multiple simultaneous conversations;
3. unfamiliar room;
4. outdoor transition;
5. obstacle during navigation;
6. thermal anomaly;
7. low battery;
8. high GPU pressure;
9. network loss;
10. conflicting sensor evidence;
11. novel object;
12. repeated irrelevant stimulus;
13. sudden user interaction;
14. map change;
15. prediction failure;
16. security event.

---

## 57. Failure Modes

The system must detect:

- attention starvation;
- attention oscillation;
- safety suppression;
- goal fixation;
- novelty fixation;
- prediction-error fixation;
- repetitive stimulus fixation;
- modality starvation;
- memory retrieval flooding;
- resource exhaustion;
- LLM attention override attempts;
- feedback-loop bias;
- stale relevance scores.

---

## 58. Architectural Invariants

1. Attention is resource allocation, not truth.
2. Attention is not memory.
3. Safety monitoring cannot be suppressed by ordinary attention policy.
4. The LLM is not the sole real-time attention scheduler.
5. Goal relevance cannot create safety blinders.
6. Novelty alone does not justify indefinite attention.
7. Prediction error can trigger attention but does not prove an explanation.
8. Uncertainty and consequence must be considered together.
9. Active perception must obey safety and resource constraints.
10. High-priority streams cannot starve the entire system indefinitely except where safety requires it.
11. Attention suppression must be explicit and reversible.
12. Low-attention information remains eligible for sampling/evaluation.
13. Attention policies must be evaluated for feedback bias.
14. Attention decisions must be observable without retaining unlimited raw data.
15. Offline operation must preserve core attention functionality.
16. Resource pressure may reduce optional attention but cannot remove protected safety functions.
17. Attention cannot grant authorization to act.
18. Attention cannot rewrite canonical memory or knowledge.

---

## 59. Implementation Direction

The initial implementation should favor a hybrid architecture:

```text
FAST DETERMINISTIC LAYER
  safety
  hardware health
  resource pressure
  basic salience
        ↓
ATTENTION ARBITRATOR
  relevance
  goals
  uncertainty
  novelty
  prediction error
  cost
        ↓
ACTIVE PERCEPTION / RETRIEVAL
        ↓
COGNITION
  LLM/VLM reasoning
        ↓
LEARNING / EVALUATION
```

A lightweight scoring/ranking system should be established before introducing learned attention policies. Learned attention can be added when benchmarks demonstrate measurable improvement.

---

## 60. Final Principle

> **Novi cannot deeply process everything. It must decide what deserves its limited attention—but that decision must be bounded by safety, goals, uncertainty, evidence, resource limits, fairness and explicit policy.**

Attention is therefore not merely a feature of cognition. It is a cross-cutting control layer connecting perception, memory, prediction, autonomy, active sensing and resource governance.
