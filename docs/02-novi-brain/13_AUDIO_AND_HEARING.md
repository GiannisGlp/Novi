# Novi Brain — Audio & Hearing Architecture

**Status:** P0 Critical Architecture Specification  
**Version:** 1.0  
**Date:** 2026-08-17  
**Authority:** `docs/02-novi-brain/`  
**Depends on:** `11_PERCEPTION_ARCHITECTURE.md`, `04_BRAIN_ORCHESTRATOR.md`, `05_COGNITIVE_CYCLE.md`, `08_MODEL_ROUTING_AND_SELECTION.md`, `10_MODEL_RUNTIME.md`

---

## 1. Purpose

This document defines how Novi hears and understands the acoustic environment continuously.

Hearing is not synonymous with speech recognition. Novi must be able to detect and reason about sound even when nobody is speaking to it.

The audio subsystem therefore covers:

- microphone hardware;
- microphone arrays;
- acoustic capture;
- clocking and timestamps;
- calibration;
- audio quality monitoring;
- beamforming;
- acoustic echo cancellation;
- noise suppression;
- dereverberation;
- voice activity detection;
- sound-event detection;
- direction-of-arrival estimation;
- speaker separation;
- speaker diarization;
- speaker identity evidence;
- speech/non-speech classification;
- streaming ASR integration;
- acoustic context;
- audio attention;
- multimodal audio-visual fusion;
- audio memory and provenance;
- degraded operation;
- privacy/security;
- simulation, replay and validation.

The goal is for Novi to maintain a continuous acoustic relationship with its environment rather than activating hearing only after a wake word.

---

# 2. Behavioral objective

Novi should behave as though hearing is one of its continuously available senses.

Examples:

```text
Someone enters the room
        ↓
footsteps / door / motion sound
        ↓
acoustic event
        ↓
attention increases
        ↓
visual confirmation
        ↓
world model update
```

```text
Novi is speaking
        ↓
someone starts speaking
        ↓
voice activity detected
        ↓
barge-in / interruption candidate
        ↓
speech extraction
        ↓
Novi decides whether to stop speaking
```

```text
Unknown loud impact
        ↓
acoustic anomaly
        ↓
direction estimate
        ↓
visual attention request
        ↓
scene inspection
        ↓
contextual interpretation
```

The audio subsystem must therefore produce useful evidence even when ASR produces no transcript.

---

# 3. Architectural principle

```text
RAW AUDIO
   ≠
SPEECH
   ≠
TRANSCRIPT
   ≠
MEANING
   ≠
IDENTITY
   ≠
TRUTH
```

An acoustic observation must retain provenance and uncertainty.

For example:

```text
microphone evidence
      ↓
voice activity
      ↓
speech segment
      ↓
speaker hypothesis
      ↓
ASR transcript
      ↓
language/context interpretation
      ↓
world-model belief
```

A transcript is evidence, not ground truth.

---

# 4. High-level pipeline

```text
MICROPHONES
     ↓
CAPTURE / DRIVER
     ↓
CLOCK + TIMESTAMP
     ↓
CHANNEL HEALTH
     ↓
CALIBRATION
     ↓
PREPROCESSING
     ├── gain normalization
     ├── filtering
     ├── echo cancellation
     ├── noise suppression
     └── dereverberation
     ↓
ACOUSTIC ANALYSIS
     ├── VAD
     ├── sound-event detection
     ├── direction of arrival
     ├── beamforming
     └── speaker separation
     ↓
SPEAKER / EVENT REPRESENTATION
     ├── diarization
     ├── speaker embedding
     └── acoustic event identity
     ↓
STREAMING ASR
     ↓
AUDIO EVIDENCE
     ↓
MULTIMODAL FUSION
     ↓
ATTENTION / WORLD MODEL / MEMORY
```

The pipeline must support branches operating at different rates. A lightweight VAD/event detector can remain active while expensive ASR is invoked only when warranted.

---

# 5. Audio hardware architecture

## 5.1 Microphone array

The preferred Novi configuration is a multi-microphone array rather than a single microphone.

A final array must be selected using measured requirements for:

- number of microphones;
- spatial arrangement;
- inter-microphone spacing;
- frequency response;
- self-noise;
- dynamic range;
- sample rate;
- bit depth;
- synchronization;
- ADC characteristics;
- USB/I2S/other interface;
- latency;
- power;
- enclosure effects;
- speaker/motor noise coupling.

The array geometry must be treated as a calibration artifact and versioned.

## 5.2 Placement

Microphone placement must account for:

- robot body occlusion;
- motors and fans;
- speakers;
- airflow;
- structural vibration;
- reverberant surfaces;
- camera/visual field relationship;
- human speaking height;
- expected room geometry.

Placement must be validated physically rather than selected only from CAD assumptions.

## 5.3 Hardware synchronization

All channels required for beamforming and localization must be synchronously sampled or have a measured synchronization relationship.

Independent unsynchronized microphone clocks are not acceptable for high-quality direction estimation without explicit compensation and validation.

---

# 6. Sampling and representation

The implementation must define and benchmark:

- sample rate;
- bit depth;
- PCM representation;
- channel count;
- frame size;
- hop size;
- buffering strategy;
- end-to-end capture latency;
- timestamp semantics.

Speech processing should normally use a representation appropriate to the selected ASR model, but the capture layer must not be coupled directly to a specific ASR model.

The audio contract must support both short frames and longer retained segments.

---

# 7. Time synchronization

Audio timestamps must use the same system time model defined by `17_TIME_SYNCHRONIZATION_AND_CLOCK_SEMANTICS.md`.

Every audio segment must be attributable to:

- source device;
- channel;
- capture start time;
- capture end time;
- sample count;
- sampling rate;
- clock domain;
- calibration version;
- preprocessing version.

Cross-modal synchronization with cameras, IMU and other sensors is mandatory for reliable multimodal reasoning.

---

# 8. Audio quality monitoring

Novi must continuously estimate audio quality.

Required quality indicators include:

- clipping;
- saturation;
- silence;
- excessive noise;
- channel failure;
- dropped frames;
- timestamp discontinuity;
- sample-rate mismatch;
- excessive reverberation;
- motor/fan interference;
- speaker feedback;
- signal-to-noise estimate where measurable.

A degraded channel must not silently enter the fusion pipeline as trustworthy evidence.

---

# 9. Preprocessing

Preprocessing may include:

1. DC offset removal;
2. filtering;
3. gain normalization;
4. automatic gain control where appropriate;
5. acoustic echo cancellation;
6. noise suppression;
7. dereverberation;
8. beamforming;
9. resampling;
10. channel selection.

Preprocessing must preserve enough metadata to reproduce or explain the transformed signal.

Processing that destroys information required for another subsystem must not be applied globally without an explicit contract.

---

# 10. Voice Activity Detection

VAD is an always-on candidate for the low-latency hearing path.

Its purpose is to determine whether speech-like activity is present, not to understand the speech.

VAD output should include:

- speech start;
- speech continuation;
- speech end;
- confidence;
- source channels;
- timestamps;
- quality indicators.

NVIDIA Riva currently documents neural VAD using Silero VAD and supports using VAD for improved noise robustness and endpointing. citeturn0search0

Novi should benchmark VAD against:

- quiet rooms;
- television/radio;
- multiple simultaneous speakers;
- robot motor noise;
- fans;
- music;
- echoes;
- distant speech;
- whispered speech;
- overlapping speech.

VAD must not be treated as proof that a human is addressing Novi.

---

# 11. Acoustic event detection

Novi must hear non-speech events.

Candidate event classes include:

- door opening/closing;
- footsteps;
- knocks;
- impacts;
- objects falling;
- glass breaking;
- alarms;
- appliances;
- machinery;
- vehicles;
- animals;
- laughter;
- crying;
- coughing;
- sneezing;
- clapping;
- environmental changes;
- unusual/unknown sounds.

The taxonomy must remain extensible.

Unknown sounds should produce an anomaly/novelty representation rather than being forced into a known class.

---

# 12. Direction of arrival

A microphone array should support acoustic localization where hardware and environment permit.

Required outputs:

- azimuth;
- elevation where supported;
- confidence;
- estimated source count where supported;
- temporal stability;
- microphone channels contributing to the estimate.

Direction estimates must be treated as uncertain measurements.

Audio direction should be fused with visual observations rather than independently asserted as exact world coordinates.

Example:

```text
Audio: sound from approximately 42° ± 8°
            ↓
Vision: moving object near 39°
            ↓
Fusion: likely common source
```

---

# 13. Beamforming and source separation

Beamforming should be used when it improves downstream performance measurably.

Potential uses:

- isolate the current speaker;
- suppress robot speakers;
- suppress motor noise;
- improve ASR;
- estimate source direction;
- improve interaction range.

Source separation must preserve uncertainty and must not create an artificial transcript from overlapping voices without confidence attribution.

---

# 14. Speaker diarization

Diarization answers:

> Who spoke when?

It is different from speaker identification.

Required output:

```text
speaker_cluster
start_time
end_time
confidence
channel/source evidence
```

NVIDIA Riva currently supports streaming speaker diarization through Sortformer and documents a maximum of four speakers for that component. citeturn0search0

This should be treated as a current NVIDIA capability constraint, not a permanent Novi limitation.

Novi must not assume that four speakers is sufficient for every deployment.

---

# 15. Speaker identification

Speaker identification answers:

> Which known person, if any, is associated with this voice evidence?

The architecture must distinguish:

- unknown speaker;
- known speaker hypothesis;
- verified speaker;
- conflicting identity evidence.

Voice identity must never be treated as infallible authentication.

High-risk operations must use stronger authorization mechanisms defined by the security architecture.

Voice embeddings and identity information are sensitive personal data and must have explicit retention, access and deletion policies.

---

# 16. Automatic speech recognition

ASR is a downstream capability of hearing, not the hearing subsystem itself.

Novi should support:

- streaming ASR;
- partial transcripts;
- final transcripts;
- timestamps;
- word confidence;
- language identification where supported;
- endpointing;
- speaker attribution;
- cancellation;
- barge-in.

NVIDIA Riva documents both streaming and offline ASR, with streaming producing intermediate transcripts while audio is being captured. citeturn0search1

For Novi's interactive brain, streaming ASR is the default architectural path because waiting for an entire utterance increases interaction latency.

Riva's current documentation also supports streaming diarization and neural VAD in the ASR pipeline. citeturn0search0turn0search2

---

# 17. Endpointing

Speech endpointing must be separate from conversational interpretation.

Novi must distinguish:

- person started speaking;
- person is still speaking;
- person paused;
- person finished speaking;
- person was interrupted;
- ASR timed out;
- speech was too uncertain.

A short pause must not automatically terminate the conversational turn.

NVIDIA Riva documents configurable beginning/end-of-utterance detection and VAD-assisted endpointing. citeturn0search0

---

# 18. Barge-in and interruption

This is mandatory for human-like interaction.

When Novi is speaking:

```text
Novi TTS active
      ↓
continuous audio monitoring
      ↓
possible speech
      ↓
VAD
      ↓
likely human interruption
      ↓
reduce/stop TTS
      ↓
listen
```

Barge-in must not depend on a wake word.

The decision may use:

- VAD;
- speaker direction;
- speaker identity hypothesis;
- transcript partials;
- visual mouth/activity cues;
- dialogue state;
- interaction distance.

---

# 19. Audio-visual fusion

Audio and vision must cooperate.

Examples:

### Person speaking

```text
audio direction
      +
visual person track
      ↓
common-source hypothesis
```

### Unknown impact

```text
impact detected
      ↓
audio direction
      ↓
visual attention request
      ↓
inspect location
```

### Multiple people

```text
multiple faces
      +
multiple voices
      +
diarization
      +
visual mouth/activity
      ↓
active-speaker hypothesis
```

The fusion layer must preserve confidence and conflicting evidence.

---

# 20. Active hearing

Hearing should be capable of influencing Novi's physical orientation.

For example:

```text
sound source detected behind Novi
       ↓
attention score rises
       ↓
request visual inspection
       ↓
head/body orientation candidate
       ↓
safety/governance
       ↓
turn toward source
       ↓
visual confirmation
```

This creates an embodied perception loop:

```text
HEAR → ORIENT → SEE → UNDERSTAND → ACT
```

The audio subsystem must therefore expose requests for active perception, not directly command motors.

---

# 21. Audio attention model

Each audio event should contribute to an attention score based on:

- urgency;
- novelty;
- proximity;
- direction;
- persistence;
- confidence;
- relevance to current goal;
- relevance to current interaction;
- identity/context;
- multimodal corroboration.

A sound should not automatically interrupt cognition merely because it is loud.

Example:

```text
loud known appliance
→ low novelty
→ low relevance

quiet unfamiliar sound behind Novi
→ high novelty
→ moderate uncertainty
→ visual inspection candidate
```

---

# 22. Memory integration

Significant audio events may become:

- episodic memories;
- social memories;
- environmental memories;
- acoustic signatures;
- learned associations;
- anomaly records.

Routine audio should not be retained indefinitely.

Memory admission must follow the memory architecture's provenance, privacy and retention policies.

---

# 23. Personality and social behavior

Audio is a major social input.

Novi may infer interaction context such as:

- someone addressing Novi;
- someone speaking to another person;
- group conversation;
- emotional/prosodic cues;
- urgency;
- interruption;
- silence after a question.

These are hypotheses, not guaranteed internal states of another person.

Novi must avoid claiming certainty about emotions or intentions from voice alone.

---

# 24. Always-on hearing and privacy

Always-on does not mean unrestricted retention.

The default architecture should favor:

```text
continuous local processing
        ↓
minimal event metadata
        ↓
retain raw audio only when justified
```

Raw audio retention requires explicit policy.

The system must document:

- when recording begins;
- when it stops;
- whether a local ring buffer exists;
- retention duration;
- encryption;
- access controls;
- deletion;
- export;
- audit logging;
- user-visible controls.

Remote/cloud audio processing should be opt-in or explicitly governed by deployment policy.

---

# 25. Offline-first behavior

Novi's basic hearing must remain useful without network connectivity.

Minimum offline capabilities should include:

- VAD;
- basic sound-event detection;
- local direction estimation where supported;
- local ASR candidate;
- local interruption detection;
- local audio quality monitoring.

Cloud processing may improve capability but must not be a prerequisite for basic embodied awareness.

---

# 26. Failure and degraded operation

Required failure states include:

| Failure | Expected behavior |
|---|---|
| one microphone fails | degrade array, continue if safe |
| array synchronization fails | disable localization-dependent functions |
| excessive noise | reduce confidence, adapt processing |
| ASR unavailable | retain non-speech/audio-event awareness |
| diarization unavailable | continue ASR without identity attribution |
| TTS feedback | strengthen echo cancellation / reduce output |
| GPU unavailable | use validated CPU/fallback path where available |
| timestamps invalid | prevent unsafe cross-modal fusion |
| storage unavailable | continue with bounded transient state |
| network unavailable | continue local hearing |

A failed ASR model must never make Novi effectively deaf.

---

# 27. NVIDIA technology mapping

NVIDIA capabilities are candidates behind explicit Novi interfaces.

| Capability | NVIDIA candidate | Novi role | Adoption status |
|---|---|---|---|
| ASR | Riva | streaming speech recognition | candidate |
| VAD | Riva/Silero | speech activity | candidate |
| diarization | Riva/Sortformer | who-spoke-when | candidate |
| speech pipeline | Riva | speech processing | candidate |
| inference | TensorRT | optimized model execution | platform candidate |
| orchestration | Novi runtime | model scheduling | Novi-owned |
| memory | Novi memory | retention/retrieval | Novi-owned |
| attention | Novi brain | relevance/arbitration | Novi-owned |
| identity policy | Novi security | authorization | Novi-owned |

NVIDIA Riva's current ASR documentation provides direct evidence for streaming ASR, VAD, endpointing and Sortformer streaming diarization. citeturn0search0turn0search1

No NVIDIA component becomes a semantic dependency of Novi merely because it exists.

---

# 28. Hardware-to-software contract

The final hardware design must specify:

- microphone model;
- array geometry;
- audio interface;
- channel count;
- sampling configuration;
- synchronization;
- physical mounting;
- speaker placement;
- vibration isolation;
- acoustic enclosure;
- calibration process.

The software stack must expose the hardware characteristics as versioned configuration.

Changing the microphone array is therefore a configuration/model compatibility event, not an invisible hardware substitution.

---

# 29. Simulation and replay

The audio architecture must support recorded and simulated audio.

Replay must preserve:

- sample data;
- timestamps;
- channel identity;
- device metadata;
- environment metadata;
- calibration;
- ground truth where available.

Simulation should eventually include:

- room impulse responses;
- reverberation;
- multiple speakers;
- moving speakers;
- robot self-noise;
- motor noise;
- background conversations;
- environmental events;
- different microphone geometries.

Real recordings remain necessary because simulated acoustic environments do not fully reproduce deployment conditions.

---

# 30. Benchmark suite

The audio benchmark must include at minimum:

### Speech

- near-field speech;
- far-field speech;
- quiet speech;
- noisy speech;
- reverberant speech;
- accented speech;
- multiple speakers;
- overlapping speech;
- interrupted speech;
- speech while robot moves.

### Non-speech

- impacts;
- doors;
- footsteps;
- alarms;
- appliances;
- music;
- animals;
- unknown sounds.

### Robot self-noise

- idle;
- wheels moving;
- motors accelerating;
- fans;
- speakers playing;
- simultaneous motion and speech.

### Metrics

- VAD precision/recall;
- false activation rate;
- ASR word error rate;
- streaming latency;
- first-token/partial-transcript latency;
- endpointing latency;
- diarization error rate;
- speaker-attribution accuracy;
- direction error;
- event classification precision/recall;
- CPU/GPU utilization;
- memory;
- power;
- thermal behavior;
- failure recovery time.

---

# 31. Validation gates

## A0 — capture

All channels capture stable synchronized audio.

## A1 — quality

Clipping, dropout, synchronization and noise faults are detected.

## A2 — always-on hearing

VAD and acoustic events operate continuously within the latency budget.

## A3 — speech

Streaming ASR meets the Novi interaction benchmark.

## A4 — spatial hearing

Direction estimation and active-perception requests meet the spatial benchmark.

## A5 — social hearing

Speaker attribution and interruption behavior meet the interaction benchmark.

## A6 — multimodal hearing

Audio and vision fuse correctly under controlled scenarios.

## A7 — embodied hearing

Novi can orient toward relevant sound sources through the normal governance/control path.

## A8 — resilience

Hearing degrades safely under sensor/model/runtime failures.

## A9 — long-duration

The subsystem remains stable during extended continuous operation.

---

# 32. Acceptance scenarios

The following scenarios are mandatory before claiming that Novi can hear naturally.

### Scenario 1 — someone enters

Novi detects acoustic evidence of entry, correlates it with visual evidence, updates the world model and decides whether attention is warranted.

### Scenario 2 — person speaks from behind

Novi detects speech, estimates direction, orients appropriately through the governed action path, visually identifies the speaker if possible and responds according to interaction state.

### Scenario 3 — interruption

A human interrupts Novi while Novi is speaking. Novi detects the interruption, stops or reduces speech appropriately, listens and continues the interaction.

### Scenario 4 — ambiguous sound

Novi hears an unfamiliar sound, cannot classify it confidently, retains uncertainty and uses active perception rather than inventing an explanation.

### Scenario 5 — loud background

Novi maintains useful speech/event detection despite music, television or mechanical noise.

### Scenario 6 — multiple speakers

Novi distinguishes overlapping speakers as far as the validated system permits and preserves uncertainty when it cannot.

### Scenario 7 — robot motion

Novi continues hearing while wheels, motors, fans and speakers are active.

### Scenario 8 — ASR failure

Novi remains acoustically aware even if the ASR model crashes or becomes unavailable.

---

# 33. Security requirements

The audio subsystem must defend against:

- replayed voice commands;
- spoofed voices;
- adversarial audio;
- malicious ultrasonic/inaudible signals where relevant;
- microphone injection;
- unauthorized recording;
- unauthorized voice-identity access;
- compromised audio devices;
- model extraction through audio interfaces.

Voice commands must not be treated as sufficient authorization for high-impact actions.

---

# 34. Required ADRs

The following decisions require explicit ADRs before implementation freeze:

- `ADR-AUDIO-001` microphone-array hardware;
- `ADR-AUDIO-002` audio interface and synchronization;
- `ADR-AUDIO-003` VAD implementation;
- `ADR-AUDIO-004` ASR implementation;
- `ADR-AUDIO-005` speaker diarization;
- `ADR-AUDIO-006` speaker identity policy;
- `ADR-AUDIO-007` audio preprocessing stack;
- `ADR-AUDIO-008` offline/cloud boundary;
- `ADR-AUDIO-009` audio retention/privacy;
- `ADR-AUDIO-010` audio simulation/replay strategy.

No candidate is considered adopted until benchmark evidence and compatibility evidence exist.

---

# 35. Definition of done

This document is implementation-ready only when:

- [ ] microphone hardware requirements are measurable;
- [ ] array geometry is specified;
- [ ] clock/synchronization strategy is validated;
- [ ] capture contract is frozen;
- [ ] VAD benchmark exists;
- [ ] sound-event benchmark exists;
- [ ] ASR benchmark exists;
- [ ] diarization benchmark exists;
- [ ] spatial-audio benchmark exists;
- [ ] audio-visual fusion scenarios exist;
- [ ] privacy policy exists;
- [ ] offline behavior exists;
- [ ] failure behavior is tested;
- [ ] NVIDIA compatibility tuple is validated where NVIDIA components are used;
- [ ] all adopted technologies have ADRs;
- [ ] raw audio retention is explicitly governed;
- [ ] embodied-hearing scenario passes.

---

# 36. Source policy

NVIDIA-specific claims must be validated against current NVIDIA documentation before implementation decisions are made.

Primary references used for this specification:

- NVIDIA Riva ASR Pipeline Configuration: https://docs.nvidia.com/deeplearning/riva/user-guide/docs/public/asr/asr-pipeline-configuration.html
- NVIDIA Riva ASR Overview: https://docs.nvidia.com/deeplearning/riva/archives/2-17-0/asr/asr-overview.html
- NVIDIA Riva CLI: https://docs.nvidia.com/deeplearning/riva/user-guide/docs/public/apis/cli.html
- NVIDIA Speech NIM pipeline configuration: https://docs.nvidia.com/nim/speech/26.05.0/asr/customization/pipeline-configuration.html

External claims must use authoritative primary sources or peer-reviewed research where appropriate.

---

# 37. Final principle

> **Novi must hear continuously, but it must not listen blindly.**
>
> Hearing means maintaining a low-latency, uncertain, multimodal acoustic relationship with the world: detecting speech, people, events, direction, novelty and change; deciding what deserves attention; and using that evidence to orient, interact, remember and act safely.

Novi's hearing must remain a sense even when speech recognition is unavailable.
