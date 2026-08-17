# Novi Brain — Speech Recognition

**Status:** P0 critical architecture specification  
**Version:** 1.0  
**Date:** 2026-08-17  
**Domain:** `02-novi-brain`  
**Depends on:** `04_BRAIN_ORCHESTRATOR.md`, `05_COGNITIVE_CYCLE.md`, `08_MODEL_ROUTING_AND_SELECTION.md`, `10_MODEL_RUNTIME.md`, `13_AUDIO_AND_HEARING.md`

---

# 1. Purpose

Speech recognition is the subsystem that converts spoken human language into structured, time-aware evidence that Novi can use for interaction, reasoning, memory, social understanding and action selection.

It is **not** the whole hearing system.

The distinction is:

```text
Acoustic world
    ↓
Audio / Hearing
    ↓
Speech candidate
    ↓
Speech Recognition
    ↓
Transcript evidence
    ↓
Language / multimodal understanding
    ↓
Cognition
```

Speech recognition must never be treated as a truth oracle. A transcript is an interpretation of an acoustic signal and must retain provenance, timing, confidence and uncertainty.

---

# 2. Novi requirement

Novi must be able to participate in natural, continuous, real-time conversation while remaining aware of its physical environment.

The speech subsystem therefore must support:

- continuous listening;
- low-latency streaming recognition;
- partial/intermediate hypotheses;
- final utterance results;
- endpoint detection;
- interruption/barge-in;
- speaker attribution;
- multilingual operation;
- language identification where required;
- contextual vocabulary biasing;
- word/segment timestamps;
- confidence/quality signals;
- noisy-room operation;
- robot self-noise;
- offline operation;
- graceful degradation;
- deterministic replay;
- auditable model/version identity.

Novi must not require a wake word for every interaction. Wake-word gating may be used as an explicit privacy/power mode, but continuous ambient hearing remains an architectural capability.

---

# 3. Core architecture

```text
Microphone Array
      ↓
Audio Acquisition
      ↓
Clock / Timestamp Validation
      ↓
Audio Quality + VAD
      ↓
Speech Candidate
      ↓
Beamforming / Enhancement
      ↓
Speaker / Source Association
      ↓
Streaming ASR
      ↓
Partial Hypotheses
      ↓
Endpoint Detection
      ↓
Final Transcript
      ↓
Timestamp + Confidence + Provenance
      ↓
Speech Evidence
      ↓
Multimodal Fusion
      ↓
Language Understanding
      ↓
Brain State / Attention
```

Speech recognition is one consumer of the hearing subsystem and must not own microphone acquisition or raw audio lifecycle.

---

# 4. Speech states

Each active speech stream has an explicit state:

```text
IDLE
 ↓
SPEECH_CANDIDATE
 ↓
STREAMING
 ↓
PARTIAL
 ↓
ENDPOINT_PENDING
 ↓
FINALIZING
 ↓
FINAL
 ↓
ARCHIVED / DISCARDED
```

Possible exceptional states:

- `NOISY`;
- `LOW_CONFIDENCE`;
- `SPEAKER_AMBIGUOUS`;
- `LANGUAGE_AMBIGUOUS`;
- `MODEL_UNAVAILABLE`;
- `TIMEOUT`;
- `CANCELLED`;
- `PRIVACY_BLOCKED`;
- `RESOURCE_LIMITED`.

State transitions must be observable and replayable.

---

# 5. Streaming is the primary interaction mode

Novi's conversational path should be streaming-first.

NVIDIA Riva currently documents both streaming and offline ASR, with streaming recognition returning intermediate results as audio segments arrive. citeturn0search2turn0search4

NVIDIA's current Riva ASR guidance also exposes explicit low-latency streaming configuration, including chunking and endpointing controls. citeturn0search5

Therefore:

```text
microphone
   ↓
small audio chunk
   ↓
ASR
   ↓
partial hypothesis
   ↓
brain may begin interpretation
   ↓
more audio
   ↓
revised hypothesis
   ↓
endpoint
   ↓
final hypothesis
```

Partial transcripts must never be persisted as final facts unless explicitly marked as provisional.

---

# 6. Partial transcript semantics

A partial transcript is a hypothesis that may change.

Every partial result should include:

- stream ID;
- utterance ID;
- hypothesis sequence number;
- text;
- word/segment timestamps where available;
- confidence/quality signals;
- speaker hypothesis;
- language hypothesis;
- model ID/version;
- runtime ID/version;
- audio time range;
- processing timestamp;
- provenance.

The brain may use partial results for low-risk anticipatory behavior, but must avoid irreversible decisions based solely on unstable hypotheses.

Example:

```text
partial: "Novi can you..."
partial: "Novi can you come..."
final:   "Novi, can you come here?"
```

The cognitive layer should receive updates rather than treating each partial result as a new independent utterance.

---

# 7. Endpoint detection

Endpoint detection determines when a speech segment has probably ended.

It must balance:

- responsiveness;
- interruption behavior;
- natural pauses;
- speaker hesitation;
- noisy environments;
- overlapping speakers;
- multilingual speech;
- computational cost.

A premature endpoint creates fragmented conversations.

A late endpoint makes Novi feel slow and prevents natural turn-taking.

Endpoint configuration therefore belongs in the Novi speech benchmark and is not copied blindly from a vendor default.

---

# 8. Barge-in and interruption

Novi must support interruption while speaking.

```text
Novi speaking
      ↓
hearing continues
      ↓
speech candidate detected
      ↓
priority assessment
      ↓
human speech likely directed at Novi?
      ↓
YES
      ↓
stop/reduce TTS output
      ↓
listen
      ↓
interpret
```

The interruption path must be faster than the normal deliberative conversation path.

This is a core requirement for the perception → interaction loop and for Novi's continuous-living behavior.

---

# 9. Speaker attribution

Speech recognition must distinguish at least:

- known speaker hypothesis;
- unknown speaker;
- multiple-speaker overlap;
- speaker transition;
- uncertain attribution.

Speaker identity must not be inferred solely from transcript text.

The evidence chain should be:

```text
acoustic signal
 ↓
speaker embedding / diarization
 ↓
speaker hypothesis
 ↓
identity resolver
 ↓
context + memory
 ↓
identity belief
```

Identity confidence and transcript confidence remain separate.

Current NVIDIA Riva documentation supports streaming/offline ASR and speaker-related capabilities, while NVIDIA's current ASR model documentation lists speaker diarization support for selected Parakeet configurations. citeturn1search6

---

# 10. Language identification

Novi should support language-aware routing rather than assuming one fixed language forever.

Possible states:

```text
KNOWN_LANGUAGE
LANGUAGE_HYPOTHESIS
MULTILINGUAL
CODE_SWITCH
UNKNOWN
```

The language decision should be allowed to change as more speech arrives.

NVIDIA's current NeMo-Speech Canary family supports multilingual ASR and speech translation across a broad set of European languages, while current NeMo streaming pipelines support configurable streaming inference. citeturn1search2turn1search7

NVIDIA's current Riva documentation also exposes multilingual Parakeet configurations and requires the selected language code to match the deployed model's supported languages. citeturn1search0turn1search8

---

# 11. Contextual biasing

Novi should be able to improve recognition of context-specific terms without retraining the ASR model for every environment.

Examples:

- person's name;
- robot name;
- room names;
- device names;
- product names;
- technical terminology;
- places;
- user-specific vocabulary.

Contextual biasing must be bounded.

It must not force the recognizer to produce a known word when the acoustic evidence does not support it.

NVIDIA's current Riva/NIM ASR documentation describes word boosting/customization for selected Parakeet models. citeturn1search6

---

# 12. Timestamps

Speech evidence should preserve temporal alignment whenever the selected model/runtime supports it.

Minimum useful levels:

- utterance;
- segment;
- word.

NVIDIA's current NeMo-Speech documentation states that Parakeet models support character-, word- and segment-level timestamps. citeturn1search5

Timestamps allow Novi to correlate:

```text
spoken phrase
    ↕
face orientation
    ↕
person track
    ↕
scene event
    ↕
robot movement
```

This is critical for multimodal grounding.

---

# 13. Speech evidence contract

The output of ASR should be represented as structured evidence, not only text.

Minimum conceptual fields:

```text
SpeechEvidence
 ├── evidence_id
 ├── stream_id
 ├── utterance_id
 ├── sequence
 ├── transcript
 ├── status (partial/final)
 ├── audio_interval
 ├── word_timestamps
 ├── language
 ├── speaker_hypothesis
 ├── confidence
 ├── acoustic_quality
 ├── model_id
 ├── model_version
 ├── runtime_version
 ├── configuration_digest
 ├── source_sensor_ids
 ├── created_at
 └── provenance
```

The transcript itself must not be allowed to overwrite the original acoustic evidence metadata.

---

# 14. Speech → cognition boundary

The ASR subsystem must not directly:

- execute actions;
- modify durable semantic memory;
- change personality;
- authorize tools;
- command motors;
- alter safety limits.

It produces evidence.

The brain then decides what the speech means and what, if anything, to do about it.

```text
ASR
 ↓
SpeechEvidence
 ↓
Language / multimodal interpretation
 ↓
Intent / social meaning hypothesis
 ↓
Goal or interaction state
 ↓
Planning / response
 ↓
Governance
 ↓
Action
```

---

# 15. Speech recognition model hierarchy

Novi should support several ASR model classes rather than one permanent model.

## Always-on / low-latency

Purpose:

- conversational responsiveness;
- short utterances;
- low compute;
- low power.

## Higher-accuracy streaming

Purpose:

- difficult acoustic conditions;
- longer speech;
- specialist vocabulary;
- multilingual operation.

## Offline/high-quality

Purpose:

- post-event transcription;
- memory processing;
- dataset creation;
- forensic/debug analysis;
- high-quality archive transcription.

## Translation-capable

Purpose:

- multilingual interactions;
- speech translation workflows.

NVIDIA's current NeMo-Speech documentation exposes Parakeet, Canary and other ASR model families with different streaming, language and task characteristics. citeturn1search2turn1search5

---

# 16. Initial model candidates

These are candidates, not adoptions.

| Candidate | Potential Novi role | Current evidence | Initial status |
|---|---|---|---|
| Parakeet 0.6B | low-cost ASR benchmark | NVIDIA documents streaming/offline variants | Evaluate |
| Parakeet 1.1B | primary streaming ASR candidate | NVIDIA documents low-latency streaming deployment | Evaluate |
| Parakeet multilingual | multilingual streaming | NVIDIA documents multilingual configurations | Evaluate |
| Canary | multilingual ASR/translation | NVIDIA documents multi-task capabilities | Evaluate |
| Whisper-family | offline/broad-language comparison | useful benchmark baseline | Evaluate |
| Nemotron ASR Streaming | English streaming candidate | current NVIDIA NIM catalog lists streaming ASR | Evaluate |

Current NVIDIA ASR NIM documentation lists Parakeet, Whisper, Canary and Nemotron ASR options with different language and streaming/offline capabilities. citeturn1search11

No model is selected until Novi's benchmark is run on the intended hardware/runtime.

---

# 17. Jetson constraint

The future physical deployment must distinguish between:

```text
workstation/server candidate
        ≠
Jetson-compatible candidate
```

Current NVIDIA Riva documentation states that the Riva SDK release supports embedded L4T platforms, while separate NIM documentation defines different hardware requirements for data-center deployment. citeturn0search1turn1search9

Therefore Novi must not assume that an ASR model that works on a development workstation can simply be moved to Jetson.

The deployment matrix must record:

- hardware;
- JetPack/L4T;
- CUDA;
- runtime;
- model version;
- precision;
- memory;
- streaming mode;
- measured latency;
- power;
- thermal behavior.

---

# 18. Latency budget

Novi should measure at least:

```text
microphone capture
 ↓
preprocessing
 ↓
ASR queue
 ↓
inference
 ↓
partial transcript
 ↓
endpoint
 ↓
final transcript
 ↓
cognitive interpretation
```

Required metrics:

- first partial latency;
- partial update interval;
- endpoint latency;
- final transcript latency;
- real-time factor;
- CPU utilization;
- GPU utilization;
- memory;
- power;
- dropped audio;
- queue depth;
- recovery time.

Exact target thresholds belong in the Novi benchmark rather than being invented from vendor marketing numbers.

---

# 19. Accuracy benchmark

Measure at minimum:

- word error rate;
- sentence/utterance error rate;
- proper-name error rate;
- domain-vocabulary error rate;
- multilingual error rate;
- code-switching error rate;
- noisy-room error rate;
- far-field error rate;
- overlapping-speech error rate;
- accented-speech error rate;
- robot-self-noise error rate.

Evaluate separately for:

- clean speech;
- quiet room;
- reverberant room;
- multiple speakers;
- moving robot;
- robot speaking while listening;
- music/background media;
- outdoor conditions.

---

# 20. Interaction benchmark

Accuracy alone is insufficient.

Novi should be tested on:

### Test A — natural conversation

Person speaks naturally with pauses and corrections.

Expected:

- low interruption;
- timely partial understanding;
- correct endpoint;
- natural response timing.

### Test B — barge-in

Novi is speaking and person interrupts.

Expected:

- speech detected;
- TTS interruption;
- speech recognition starts quickly;
- prior response is cancelled or revised safely.

### Test C — two people

Two people speak in the same environment.

Expected:

- speaker ambiguity represented;
- no invented identity;
- correct directed-speech handling where possible.

### Test D — noisy environment

Background sound is present.

Expected:

- confidence reflects degradation;
- speech is not treated as certain when unclear.

### Test E — moving robot

Robot moves while listening.

Expected:

- self-noise handling;
- timestamps remain coherent;
- recognition degrades gracefully rather than silently failing.

---

# 21. Active conversational listening

Speech recognition must interact with attention.

Example:

```text
Novi navigating
     ↓
hears speech
     ↓
speech candidate
     ↓
Is Novi likely being addressed?
     ↓
 ┌───┴────┐
 NO       YES
 ↓         ↓
monitor   elevate attention
           ↓
       recognize
           ↓
       understand
```

This prevents every ambient conversation from interrupting Novi's current goal while still allowing important speech to attract attention.

---

# 22. Speech and visual grounding

When possible, ASR should be fused with:

- person tracks;
- face/body orientation;
- gaze/pose;
- speaker direction;
- room/location;
- current conversation;
- recent visual events.

Example:

```text
Audio: "Novi, come here"
       ↓
speaker direction
       ↓
person track #17
       ↓
person facing Novi
       ↓
identity hypothesis
       ↓
high-confidence directed interaction
```

This is a multimodal inference problem, not an ASR-only problem.

---

# 23. Privacy

Speech is highly sensitive data.

The system must distinguish:

- raw audio;
- transient speech buffers;
- partial transcript;
- final transcript;
- semantic interpretation;
- durable memory.

Default principle:

```text
raw audio
   ↓
retain only when justified
   ↓
structured evidence
   ↓
semantic memory only when meaningful
```

Privacy policy must control recording, retention, deletion, user-visible recording state and access to stored audio/transcripts.

---

# 24. Failure modes

Required failure handling:

| Failure | Required response |
|---|---|
| ASR unavailable | hearing continues; speech unavailable state |
| GPU unavailable | fallback model/runtime if available |
| High latency | reduce model tier / degrade gracefully |
| Audio dropout | mark evidence incomplete |
| Low confidence | ask/repeat/seek confirmation where appropriate |
| Endpoint failure | continue stream or recover |
| Language unknown | retain uncertainty / route language detection |
| Speaker ambiguous | do not invent identity |
| Model timeout | cancel and fallback |
| Memory unavailable | conversation may continue without durable memory |
| Privacy restriction | do not retain prohibited data |
| Network unavailable | use local/offline path where provisioned |

---

# 25. Security

Speech input is an untrusted input channel.

Threats include:

- adversarial audio;
- prompt injection through speech;
- replayed commands;
- impersonation;
- malicious background speech;
- ultrasonic/inaudible interference where relevant;
- poisoned contextual vocabulary;
- transcript manipulation;
- compromised model artifacts.

Speech-derived intent must never bypass Novi's authorization and safety layers.

---

# 26. Data and training

Novi-specific ASR evaluation data should include:

- clean speech;
- far-field speech;
- robot self-noise;
- reverberation;
- multiple speakers;
- accents;
- domain terminology;
- names;
- multilingual speech;
- code switching;
- interruptions;
- natural pauses;
- spontaneous corrections.

NVIDIA NeMo-Speech documents manifest-based dataset organization with audio, transcript and duration metadata, with additional fields for multilingual/task-specific models. citeturn1search13

Any future fine-tuning dataset must have:

- provenance;
- consent/privacy classification;
- license;
- train/validation/test separation;
- transcript quality review;
- speaker leakage checks;
- version/checksum;
- transformation history.

---

# 27. Evaluation gates

## Gate ASR-0 — interface

Audio streams can be reliably delivered to ASR.

## Gate ASR-1 — streaming

Partial and final hypotheses work under controlled conditions.

## Gate ASR-2 — interaction

Endpointing and barge-in produce natural conversational timing.

## Gate ASR-3 — environment

Far-field, noise, reverberation and robot self-noise are benchmarked.

## Gate ASR-4 — identity/language

Speaker and language uncertainty are represented correctly.

## Gate ASR-5 — edge

Selected candidate meets measured compute, memory, thermal and latency constraints on the target platform.

## Gate ASR-6 — long-duration

Continuous listening remains stable without memory/resource leaks or unacceptable degradation.

---

# 28. Required artifacts

Before ASR adoption, Novi must have:

- ASR model manifest;
- model checksum;
- runtime manifest;
- hardware compatibility record;
- benchmark dataset version;
- benchmark results;
- language support matrix;
- latency profile;
- resource profile;
- privacy configuration;
- fallback policy;
- failure test report;
- ADR.

---

# 29. Initial recommendation

The initial implementation should benchmark at least:

1. **NVIDIA Parakeet 1.1B streaming**;
2. **a smaller Parakeet variant** for always-on/low-power comparison;
3. **NVIDIA multilingual Parakeet**;
4. **NVIDIA Canary** where multilingual/translation capability is useful;
5. **one strong non-NVIDIA baseline** for independent comparison.

The exact production choice should be made only after running the same Novi benchmark on the intended development hardware and, later, the target Jetson platform.

NVIDIA's current documentation provides the relevant model families, streaming/offline modes, timestamps, multilingual options and customization mechanisms needed for this evaluation. citeturn1search0turn1search2turn1search5turn1search6

---

# 30. Architectural invariants

1. ASR produces evidence, not truth.
2. Partial hypotheses are provisional.
3. Final transcripts retain provenance.
4. Speech recognition does not control actuators.
5. Speaker identity and transcript confidence are independent.
6. Language identification remains probabilistic until sufficiently supported.
7. Streaming is the default conversational path.
8. Offline transcription is a separate workload.
9. Contextual biasing cannot override acoustic evidence without validation.
10. Barge-in must remain available while Novi speaks.
11. Hearing continues while Novi performs other tasks.
12. Speech and vision should be fused when useful.
13. Raw audio retention is governed by privacy policy.
14. Model/runtime versions must be recorded.
15. Vendor capability claims require Novi-specific benchmarking before adoption.
16. Jetson deployment requires an explicit compatibility test.
17. ASR failure must degrade cognition rather than compromise safety.
18. Speech-derived commands must pass the same authorization and safety boundaries as every other command source.

---

# 31. Open decisions

The following remain ADR candidates:

- primary streaming ASR model;
- always-on low-power ASR model;
- multilingual strategy;
- language identification mechanism;
- speaker diarization/identity architecture;
- Riva vs direct NeMo/runtime deployment;
- Jetson ASR runtime;
- contextual vocabulary mechanism;
- transcript retention policy;
- speech benchmark target thresholds.

No decision is final until benchmark evidence exists.

---

# 32. Definition of done

Speech recognition is architecturally complete when:

- streaming semantics are implemented;
- partial/final evidence contracts are defined;
- endpointing is benchmarked;
- barge-in is validated;
- speaker attribution is represented safely;
- language handling is specified;
- contextual vocabulary is controlled;
- multimodal grounding is defined;
- privacy controls are defined;
- model/runtime compatibility is recorded;
- candidate models are benchmarked;
- edge deployment is validated;
- failure and recovery behavior is tested;
- long-duration operation is tested;
- an ADR records the selected implementation.

Until then this document remains the authoritative design baseline, not a claim that the capability has been validated in hardware.
