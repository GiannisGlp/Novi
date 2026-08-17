# Novi Brain — Multimodal Fusion Architecture

**Status:** P0 critical architecture specification  
**Version:** 1.0  
**Date:** 2026-08-17  
**Authority:** `docs/02-novi-brain/`  
**Depends on:** 02 Cognitive Architecture, 03 Brain State Model, 05 Cognitive Cycle, 11 Perception Architecture, 12 Vision, 13 Audio & Hearing, 14 Speech Recognition, 15 Speech Synthesis, system canonical contracts

---

## 1. Purpose

Novi must not experience the world as independent streams of camera detections, audio transcripts, IMU measurements and memory records.

The multimodal fusion layer converts heterogeneous observations into a coherent, time-aware, spatially grounded set of **evidence and beliefs** that the cognitive architecture can reason over.

The fundamental rule is:

> **Fusion combines evidence; it does not manufacture certainty.**

A fused representation must retain provenance, timing, uncertainty and modality attribution.

---

## 2. Why multimodal fusion is central to Novi

Novi's intended behavior requires cross-modal understanding.

Examples:

- hear a voice and turn toward its source;
- see a person and determine whether they are the speaker;
- hear a crash and visually inspect the location;
- see an object fall and use audio to confirm the event;
- combine camera, depth, LiDAR and IMU information for spatial awareness;
- maintain awareness of a person while speaking to them;
- understand that an utterance is directed at Novi rather than another person;
- distinguish an observed event from an inferred explanation;
- detect disagreement between sensors and reduce confidence instead of selecting a convenient answer.

Multimodal fusion therefore sits between perception and cognition but participates in both directions through active perception requests.

---

## 3. Canonical pipeline

```text
                         WORLD
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       VISION            AUDIO         PROPRIOCEPTION
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                  ACQUISITION NORMALIZATION
                           ↓
                 TIME / CLOCK ALIGNMENT
                           ↓
                    FRAME ALIGNMENT
                           ↓
                  SENSOR HEALTH / QUALITY
                           ↓
                 MODALITY-SPECIFIC MODELS
                           ↓
                  TEMPORAL ASSOCIATION
                           ↓
                  SPATIAL ASSOCIATION
                           ↓
                   ENTITY ASSOCIATION
                           ↓
                 CROSS-MODAL CORRELATION
                           ↓
                 FUSED EVIDENCE OBJECTS
                           ↓
               TRACKS / EVENTS / SITUATIONS
                           ↓
                 UNCERTAINTY + CONFLICT
                           ↓
                     WORLD STATE UPDATE
                           ↓
                 ATTENTION / MEMORY / GOALS
                           ↓
              COGNITIVE INTERPRETATION
                           │
                    ACTIVE PERCEPTION
                           │
                           └──────→ sensors
```

---

## 4. Modalities

The first-class modalities are:

### 4.1 Vision

- RGB;
- stereo;
- depth;
- optical flow where available;
- object detections;
- segmentation;
- pose;
- tracking;
- scene semantics;
- visual events.

### 4.2 Audio

- raw/processed audio;
- voice activity;
- acoustic events;
- direction of arrival;
- speaker diarization;
- speaker identity hypotheses;
- ASR partial/final results;
- prosodic features.

### 4.3 Spatial/proprioceptive

- IMU;
- joint states;
- wheel/motor encoders;
- odometry;
- LiDAR;
- localization;
- robot pose;
- velocity;
- acceleration.

### 4.4 World/context

- durable memory;
- active goals;
- known entities;
- relationships;
- current task;
- environment state;
- previous observations;
- interaction state.

Context is **not a sensor**. It is a source of prior information that must remain distinguishable from current observation evidence.

---

## 5. Evidence hierarchy

Novi must preserve the following distinction:

```text
RAW OBSERVATION
      ↓
MODEL OUTPUT
      ↓
TEMPORALLY/SPATIALLY ASSOCIATED ESTIMATE
      ↓
FUSED EVIDENCE
      ↓
BELIEF / WORLD-STATE HYPOTHESIS
      ↓
COGNITIVE INTERPRETATION
      ↓
PREDICTION
```

These are not interchangeable.

Example:

```text
Camera: person detection
Audio: speech source at azimuth +32°
ASR: "Novi, come here"
Track: person #17 at +30°
Memory: person #17 is known as Alice

→ fused evidence: person #17 is probably the speech source
→ belief: Alice probably addressed Novi
→ intention hypothesis: request to approach
```

The final interpretation remains a hypothesis until sufficient evidence exists.

---

## 6. Temporal fusion

Every multimodal item must have explicit timing metadata.

At minimum:

- source timestamp;
- acquisition timestamp;
- processing timestamp;
- publication timestamp;
- clock domain;
- synchronization quality;
- sequence number where applicable;
- latency estimate.

Fusion must handle:

- asynchronous sensors;
- different update rates;
- delayed inference;
- out-of-order messages;
- dropped frames;
- stale observations;
- clock drift;
- simulation time;
- replay time.

A result must never be fused merely because it arrived at the same wall-clock time.

Fusion uses the **observation/event time model** defined by the system architecture.

---

## 7. Spatial fusion

All spatial observations must be associated with explicit coordinate frames.

The system must distinguish:

- sensor frame;
- robot/body frame;
- odometry frame;
- map/world frame;
- camera optical frame;
- audio-array frame;
- object/entity frame where available.

Spatial fusion requires validated calibration and transform availability.

If transform quality is unknown, the resulting spatial estimate must carry reduced confidence or be rejected.

---

## 8. Association

Association links observations believed to refer to the same underlying entity/event.

Association candidates may use:

- time proximity;
- spatial proximity;
- motion consistency;
- appearance;
- identity embeddings;
- voice characteristics;
- semantic compatibility;
- known relationships;
- task context.

Association must remain probabilistic unless independently verified.

The fusion layer must support one-to-many and many-to-one ambiguity rather than forcing a single match.

---

## 9. Cross-modal event detection

The fusion layer should detect events that are difficult to establish from one modality.

Examples:

### Person speaking

```text
speech detected
+
voice direction
+
person track
+
face/body orientation
+
ASR content
+
interaction context
```

### Object impact

```text
rapid visual motion
+
trajectory termination
+
impact sound
+
scene change
```

### Person approaching

```text
visual track
+
depth
+
velocity
+
spatial trajectory
+
possibly audio cues
```

### Possible danger

```text
anomalous sound
+
visual anomaly
+
robot proximity
+
rapid motion
```

These become **events/evidence**, not automatic commands.

---

## 10. Fusion strategies

Novi should support several levels of fusion.

### 10.1 Early fusion

Raw or lightly processed modalities are combined before a learned model.

Useful when a model explicitly supports multimodal input.

Risks:

- high compute;
- synchronization sensitivity;
- harder debugging;
- difficult modality substitution.

### 10.2 Intermediate fusion

Specialist encoders produce representations which are combined.

This is expected to be important for Novi because it preserves specialist perception while allowing joint reasoning.

### 10.3 Late fusion

Independent model outputs are combined by a deterministic/probabilistic fusion layer.

Advantages:

- modularity;
- explainability;
- graceful modality loss;
- independent validation.

### 10.4 Hybrid fusion

The default Novi architecture should support all three and choose per capability.

No single fusion mechanism is mandated globally.

---

## 11. Learned multimodal models

Multimodal foundation models may consume:

- images;
- video;
- text;
- audio;
- action/state information;
- temporal context.

NVIDIA's current Cosmos 3 is particularly relevant because NVIDIA describes it as an omnimodal physical-AI foundation model capable of processing and generating combinations of text, image, video, ambient sound and action. NVIDIA describes a reasoner tower that interprets multimodal observations and a generator tower for future observations/action sequences. citeturn0search0turn0search3

This makes Cosmos 3 a candidate for higher-level multimodal reasoning/world-model workflows, not a replacement for Novi's entire perception stack.

NVIDIA also documents Isaac ROS as a modular ROS 2 ecosystem with hardware-accelerated perception pipelines. citeturn0search8

Therefore Novi should maintain both:

```text
specialist perception
        +
multimodal foundation models
        +
deterministic fusion
```

rather than assuming one foundation model can safely replace every sensor-processing function.

---

## 12. Confidence and uncertainty

Every fused result should carry, where meaningful:

- confidence;
- uncertainty representation;
- supporting modalities;
- contradictory modalities;
- freshness;
- spatial quality;
- model version;
- calibration version;
- association confidence;
- provenance.

A confidence score must never be interpreted as probability unless the model producing it has been appropriately calibrated and the semantics are documented.

---

## 13. Conflict handling

Conflicting observations are first-class events.

Example:

```text
Camera → object at x=2.0m
LiDAR  → object at x=2.7m
Depth  → low confidence
```

The system must not silently average these values.

It should:

1. validate timestamps;
2. validate calibration;
3. validate sensor health;
4. determine whether observations correspond to the same object;
5. estimate uncertainty;
6. retain both evidence items;
7. produce a fused estimate only if justified;
8. record the conflict.

Persistent disagreement can become a sensor-health or world-model anomaly.

---

## 14. Active perception

Multimodal fusion is bidirectional with attention.

When uncertainty is high, Novi may request additional evidence.

Example:

```text
sound detected behind Novi
        ↓
uncertain source
        ↓
attention score rises
        ↓
request audio localization refinement
        ↓
rotate head/body if appropriate
        ↓
request visual observation
        ↓
identify event
```

This makes perception an active process rather than passive sensor ingestion.

The request must pass through the action/governance architecture before physical motion occurs.

---

## 15. Attention interaction

Fusion feeds attention with:

- novelty;
- urgency;
- relevance to current goals;
- uncertainty;
- social importance;
- safety significance;
- expected information gain;
- persistence;
- proximity.

Attention can then request:

- higher camera rate;
- region-of-interest processing;
- more audio analysis;
- another sensor;
- visual orientation;
- speech recognition;
- multimodal reasoning.

Resource limits remain authoritative.

---

## 16. Identity fusion

Identity must be treated as a hypothesis assembled from evidence.

Potential evidence:

- face appearance;
- voice;
- body appearance;
- gait;
- known location/context;
- interaction history;
- explicit self-identification.

The system must support:

- unknown person;
- known person;
- ambiguous identity;
- identity conflict;
- identity change;
- spoofing suspicion.

No single biometric signal should automatically authorize a high-impact action.

---

## 17. Interaction grounding

A central multimodal task is determining whether a person is interacting with Novi.

Inputs can include:

- speech content;
- direction of speech;
- speaker identity;
- face orientation;
- body orientation;
- gaze where reliably estimated;
- proximity;
- conversational state;
- wake/attention state;
- current task.

Example:

```text
Person A talks to Person B
while Novi is nearby.

Audio alone:
    speech detected

Fusion:
    speaker → A
    gaze/body orientation → B
    dialogue context → B

Result:
    likely not addressed to Novi
```

Novi should not interrupt unnecessarily.

Conversely, if multiple signals indicate direct address, Novi should be able to allocate attention quickly.

---

## 18. Continuous embodied awareness

The fusion layer must continue operating while Novi:

- moves;
- speaks;
- listens;
- reasons;
- navigates;
- performs a task;
- waits;
- learns;
- recovers from an interruption.

No high-level cognitive operation is allowed to imply that the robot becomes perceptually blind unless an explicit degraded mode is entered.

This is a core requirement for Novi's "always alive" behavior.

---

## 19. Interruptions

High-priority multimodal events may interrupt lower-priority cognition.

Examples:

- emergency proximity;
- collision risk;
- unexpected obstacle;
- human distress cue;
- direct user interruption;
- hardware anomaly;
- unexpected physical event.

The interruption system must preserve resumable state where safe.

A lower-priority reasoning task should not block a safety-critical or interaction-critical perception path.

---

## 20. Memory interaction

Fusion should produce memory candidates rather than automatically writing every observation to durable memory.

Candidate admission should consider:

- novelty;
- emotional/social significance where defined by the architecture;
- task relevance;
- future utility;
- repetition;
- confidence;
- explicit user instruction;
- privacy policy.

Raw sensor data, evidence, beliefs and memories remain separate artifacts.

---

## 21. Privacy

Multimodal fusion is privacy-sensitive because it can correlate:

- faces;
- voices;
- locations;
- conversations;
- behavior;
- relationships.

The architecture therefore requires:

- data minimization;
- local processing where feasible;
- explicit retention rules;
- access controls;
- audit logging;
- configurable deletion;
- separation of transient processing from durable memory;
- protection against unauthorized cross-person identity inference.

Privacy policy remains authoritative over convenience.

---

## 22. Degraded modes

Novi must continue operating when modalities disappear.

Examples:

```text
vision unavailable
 → hearing + proprioception + memory

hearing unavailable
 → vision + state + interaction fallback

LiDAR unavailable
 → vision/depth/localization fallback

network unavailable
 → local models + deterministic capabilities

large model unavailable
 → specialist models + deterministic behavior
```

The brain must know what evidence has become unavailable and reduce confidence accordingly.

---

## 23. Simulation and replay

Simulation must reproduce multimodal timing and correlation.

Required simulated modalities include:

- RGB;
- depth;
- LiDAR;
- IMU;
- joint state;
- audio where supported;
- semantic/instance information;
- robot pose.

NVIDIA Isaac Sim documents ROS 2 workflows covering cameras, LiDAR, transforms, timing, QoS, navigation and reinforcement-learning policies. citeturn0search14

Replay must preserve:

- original timestamps;
- sensor configuration;
- calibration;
- model versions;
- fusion configuration;
- world state;
- random seeds where applicable.

---

## 24. Performance architecture

Fusion must have explicit budgets for:

- sensor ingestion latency;
- synchronization latency;
- association latency;
- fusion latency;
- memory bandwidth;
- GPU utilization;
- CPU utilization;
- network/IPC overhead;
- output freshness.

The system should avoid unnecessary copying of large image/audio tensors.

NVIDIA Isaac ROS NITROS is a candidate optimization mechanism because NVIDIA describes it as providing ROS 2 type adaptation/negotiation and hardware-accelerated processing pipelines. citeturn0search8

NITROS adoption remains subject to compatibility and benchmark validation.

---

## 25. Failure isolation

A failure in one modality must not automatically corrupt the fused state.

Every modality has:

- health state;
- freshness state;
- calibration state;
- confidence state;
- availability state.

The fusion layer must support quarantine of corrupted streams.

---

## 26. Security

Threats include:

- sensor spoofing;
- replayed observations;
- malicious audio;
- adversarial visual input;
- identity spoofing;
- timestamp manipulation;
- calibration tampering;
- forged fusion messages;
- compromised model outputs.

Fusion must authenticate critical inter-process messages and retain provenance sufficient for incident reconstruction.

---

## 27. Model boundaries

A multimodal model may propose:

- scene interpretation;
- relationship hypotheses;
- event classification;
- intent hypotheses;
- predicted future states;
- action candidates.

It must not directly bypass:

```text
fusion
 → brain state
 → governance
 → safety
 → control
```

No foundation model receives unrestricted actuator authority.

---

## 28. NVIDIA technology candidates

Candidate technologies to evaluate include:

| Capability | Candidate |
|---|---|
| ROS 2 accelerated graph | Isaac ROS / NITROS |
| Camera perception | Isaac ROS / specialist models |
| Visual localization | Isaac ROS Visual SLAM |
| 3D reconstruction | nvblox |
| Multimodal physical reasoning | Cosmos 3 |
| Multimodal/world-model generation | Cosmos 3 |
| Inference serving | TensorRT / Triton / NIM where justified |
| Simulation | Isaac Sim |

These are candidates, not automatic architectural dependencies.

---

## 29. Validation matrix

Every fusion capability requires tests for:

### Temporal

- synchronized streams;
- delayed streams;
- out-of-order streams;
- stale observations;
- clock drift.

### Spatial

- correct transforms;
- calibration error;
- moving robot;
- moving objects;
- localization loss.

### Modality failure

- camera loss;
- audio loss;
- LiDAR loss;
- IMU loss;
- model failure.

### Conflict

- contradictory sensors;
- incorrect identity association;
- false correlation;
- ambiguous source.

### Interaction

- direct address;
- indirect conversation;
- interruption;
- multiple speakers;
- multiple people moving.

### Long duration

- memory growth;
- track persistence;
- sensor drift;
- synchronization drift;
- repeated false associations.

---

## 30. Acceptance criteria

The multimodal system is not complete until it can demonstrate:

- continuous multi-sensor ingestion;
- deterministic timestamp/frame semantics;
- traceable evidence;
- uncertainty preservation;
- cross-modal association;
- conflict handling;
- graceful modality loss;
- active perception;
- person/speech grounding;
- event correlation;
- replayability;
- measurable latency;
- model/version provenance;
- privacy enforcement;
- security controls;
- simulation validation;
- hardware validation.

---

## 31. Required future ADRs

At minimum:

- ADR: fusion architecture strategy;
- ADR: sensor timestamp/synchronization implementation;
- ADR: TF2/frame authority;
- ADR: Isaac ROS/NITROS adoption;
- ADR: nvblox adoption;
- ADR: multimodal foundation model selection;
- ADR: fusion confidence representation;
- ADR: identity association strategy;
- ADR: active perception control interface.

---

## 32. Final principle

Novi should not experience the world as a collection of disconnected sensors.

It should maintain a continuously updated, uncertainty-aware, spatially and temporally grounded representation of:

```text
WHO is here
WHAT is here
WHERE it is
WHAT is happening
WHEN it happened
WHO is interacting with whom
WHAT changed
WHAT Novi is doing
WHAT Novi expects next
WHAT Novi does not know
```

The multimodal fusion layer is the bridge between **sensing the world** and **experiencing the world as a coherent situation**.

That bridge must remain traceable, testable, privacy-aware, fault-tolerant and independent of any single foundation model.
