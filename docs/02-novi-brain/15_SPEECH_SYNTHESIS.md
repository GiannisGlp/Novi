# Novi Brain — Speech Synthesis

**Document:** 15_SPEECH_SYNTHESIS.md  
**Status:** Critical architecture specification  
**Scope:** Text-to-speech, expressive speech generation, voice identity, streaming output, turn-taking, interruption, audio output and integration with the Novi cognitive architecture.

---

## 1. Purpose

Novi must be able to communicate through natural speech as an embodied participant in the environment. Speech synthesis is therefore not a standalone text-to-audio utility. It is the final stage of a governed communication pipeline connecting cognition, interaction state, personality, language, prosody and the physical audio system.

The speech subsystem MUST NOT decide independently what Novi believes, intends, promises, or does. It receives an approved communicative act from the brain and renders that act into speech.

The core boundary is:

```text
Cognition
  ↓
Communicative intent
  ↓
Response content
  ↓
Interaction policy
  ↓
Voice/prosody plan
  ↓
Speech synthesis
  ↓
Audio validation
  ↓
Output arbitration
  ↓
Speaker / physical world
```

---

## 2. Behavioral objective

Novi's voice should feel like a persistent component of the same embodied individual rather than a generic API response.

Novi should support:

- natural conversational timing;
- low-latency responses;
- interruption and barge-in;
- intentional pauses;
- appropriate speaking rate;
- context-sensitive prosody;
- stable voice identity;
- multilingual operation where supported;
- controlled expressiveness;
- emotional expression without claiming unsupported internal states;
- pronunciation of names and domain-specific terms;
- concise or detailed speech depending on context;
- speaking while maintaining perception of the environment;
- stopping safely when interrupted or when speech is no longer appropriate;
- recovery after synthesis/output failure.

Novi MUST NOT generate speech merely to appear active. Speech must originate from an intentional communicative reason, while silence remains a valid and meaningful state.

---

## 3. NVIDIA technology evidence

NVIDIA Riva currently provides TTS with both streaming and offline inference. Streaming returns generated audio chunks as they become available and is intended to reduce time-to-first-audio for larger requests. Riva also documents SSML, custom pronunciation dictionaries, multilingual models and beta emotion-mixing capabilities. citeturn0search0turn0search1

Riva exposes streaming synthesis APIs and client tooling for receiving audio incrementally. citeturn0search3turn0search13

NVIDIA NeMo-Speech is the research/customization path. Current documentation describes pretrained TTS models, configurable model architectures, checkpoint loading, training/fine-tuning workflows and controllable prosody. MagpieTTS supports standard, long-form and streaming inference. citeturn0search2turn0search8turn0search10

**Architecture decision:** Riva and NeMo are candidate implementations, not permanent Novi dependencies. Novi adopts a provider-neutral speech contract and selects a concrete backend only after benchmark, compatibility, privacy, licensing and quality validation.

---

## 4. Speech output contract

The brain MUST produce a structured communicative request rather than passing arbitrary model text directly to TTS.

Minimum conceptual fields:

```text
SpeechRequest
- request_id
- interaction_id
- source_turn_id
- semantic_content
- language
- voice_profile_id
- prosody_profile_id
- urgency
- priority
- interruptibility
- expected_duration
- pronunciation_context
- safety_class
- provenance
- created_at
- expires_at
```

The request represents **what Novi has decided to communicate**, not merely a string to synthesize.

---

## 5. Content/prosody separation

Content and delivery MUST be separate layers.

```text
WHAT NOVI SAYS
      ↓
LINGUISTIC PLAN
      ↓
HOW NOVI SAYS IT
      ↓
AUDIO
```

Content may include:

- words;
- numbers;
- names;
- structured references;
- pronunciation hints;
- language;
- SSML-equivalent controls.

Delivery may include:

- rate;
- pitch;
- volume;
- pause duration;
- emphasis;
- phrasing;
- speaking style;
- controlled emotional intensity;
- voice identity.

The prosody layer MUST NOT silently change the semantic meaning of the approved content.

---

## 6. Voice identity

Novi requires a stable canonical voice identity.

A voice profile SHOULD define:

- voice/model identifier;
- language coverage;
- speaker characteristics;
- default speaking rate;
- pitch range;
- supported emotional controls;
- pronunciation dictionary;
- fallback voice;
- model version;
- artifact digest;
- compatibility requirements.

Voice changes MUST be explicit and versioned. Accidental model changes must not silently change Novi's identity.

Voice cloning/custom voices are a separate capability and require explicit authorization, provenance, consent and security controls. A supplied voice sample MUST NOT automatically authorize impersonation of a real person.

---

## 7. Prosody architecture

Prosody should be generated from the interaction context rather than randomly varied.

Potential inputs:

- communicative intent;
- sentence structure;
- dialogue state;
- urgency;
- personality profile;
- current interaction mode;
- user preferences;
- environmental conditions;
- speaking history;
- interruption state.

Example:

```text
informative → neutral, clear
question → interrogative contour
urgent warning → concise, high salience
comfort → slower, calm delivery
excited discovery → increased expressive range
navigation instruction → short, unambiguous phrasing
```

Emotion must be treated as an **expressive control**, not evidence that Novi possesses a human emotional experience.

---

## 8. Streaming architecture

Interactive speech SHOULD use streaming synthesis when the selected backend supports it.

```text
approved response
      ↓
text segmentation
      ↓
TTS request
      ↓
first audio chunk
      ↓
audio buffer
      ↓
output device
      ↓
additional chunks
```

The system SHOULD begin synthesis before an unnecessarily long response has been fully materialized when doing so is semantically safe.

However, streaming MUST NOT cause Novi to speak content that has not passed the required cognitive/governance boundary.

---

## 9. Time-to-first-audio

Speech latency MUST be measured separately from total synthesis latency.

Required measurements:

- request-to-first-audio;
- request-to-first-audible-sample;
- first-audio-to-completion;
- total synthesis duration;
- real-time factor;
- audio underruns;
- output buffering latency;
- interruption detection-to-audio-stop latency.

The target values must be defined by benchmark rather than assumed from vendor marketing numbers.

---

## 10. Turn-taking

Speech synthesis participates in a broader conversational state machine:

```text
IDLE
 ↓
PREPARING
 ↓
SPEAKING
 ↓
LISTENING-IN-PARALLEL
 ↓
INTERRUPTED / COMPLETED
 ↓
RESUME / LISTEN / THINK
```

Novi MUST be able to listen while speaking where hardware and acoustic processing permit it.

This enables:

```text
Novi speaking
      ↓
person begins speaking
      ↓
hearing detects probable interruption
      ↓
speech output attenuates/stops
      ↓
ASR receives priority
      ↓
Novi listens
```

---

## 11. Barge-in and interruption

Interruption is a first-class control path.

An interruption MAY come from:

- human speech;
- emergency/safety event;
- navigation event;
- sensor event;
- higher-priority system message;
- user explicitly stopping Novi;
- loss of environmental suitability.

The audio subsystem MUST support immediate cancellation/attenuation of speech output without requiring the cognitive model to finish its current generation.

A cancelled utterance MUST be recorded as cancelled rather than completed.

---

## 12. Output arbitration

Only one authoritative speech output path should control the physical speaker at a time unless explicitly supporting multi-channel output.

Priority examples:

```text
P0 safety / emergency
P1 immediate physical-state warning
P2 direct interactive response
P3 navigation/task instruction
P4 background/status speech
P5 optional social behavior
```

Lower-priority speech MUST be cancellable or deferred when higher-priority communication occurs.

---

## 13. Environmental awareness

Speech output is part of physical behavior.

The system SHOULD account for:

- ambient noise;
- distance to listener;
- room acoustics;
- current robot movement;
- microphone/speaker feedback;
- privacy requirements;
- whether the intended listener is present;
- whether speech would interfere with perception.

If the environment makes speech unreliable, Novi may:

- repeat;
- increase clarity;
- change volume within safe limits;
- reposition toward the listener;
- use another interaction modality;
- wait for a better moment.

---

## 14. Embodied interaction

Speech should coordinate with movement and visual attention.

Example:

```text
hear person
 ↓
identify interaction opportunity
 ↓
orient head/body
 ↓
establish visual attention
 ↓
begin speaking
 ↓
monitor listener
 ↓
adapt / stop / continue
```

Speech generation MUST therefore expose timing events to the behavior system, including:

- speech-starting;
- speech-active;
- phrase boundary;
- speech-ending;
- cancelled;
- completed;
- output error.

These events can drive gaze, head movement, gestures and navigation behavior.

---

## 15. Personality integration

Personality affects expression, not truth.

```text
Personality
    ↓
communication style
    ↓
prosody / phrasing
    ↓
TTS
```

Personality MUST NOT:

- invent facts;
- override safety;
- fabricate memories;
- impersonate unauthorized people;
- change explicit user instructions;
- conceal uncertainty that should be communicated.

A personality profile SHOULD be persistent and versioned so that speech remains recognizably Novi across model updates.

---

## 16. Multilingual operation

The architecture SHOULD support multiple languages through explicit language selection.

Required metadata:

- language code;
- voice availability;
- pronunciation rules;
- text normalization rules;
- fallback language;
- model version.

Language switching should follow the dialogue/interaction policy rather than being inferred solely from an isolated sentence.

NVIDIA Riva currently documents multiple language/model options and regularly updated speech models. citeturn0search0

---

## 17. Pronunciation

Novi needs a pronunciation layer for:

- people's names;
- locations;
- technical terms;
- product names;
- uncommon words;
- user-defined vocabulary.

Riva currently supports custom pronunciation dictionaries and SSML controls for pronunciation/prosody. citeturn0search0

Pronunciation overrides MUST be versioned and associated with their source/context.

---

## 18. Speech safety

TTS is not an authority layer.

Before speech reaches the speaker:

```text
brain output
 ↓
content validation
 ↓
interaction policy
 ↓
privacy check
 ↓
voice policy
 ↓
TTS
 ↓
audio validation
 ↓
speaker
```

The system must prevent accidental disclosure through speech when the cognitive/security policy marks information as private or restricted.

High-risk or externally consequential statements may require stronger governance than ordinary conversational output.

---

## 19. Failure modes

Required failure handling:

| Failure | Expected behavior |
|---|---|
| TTS unavailable | use approved fallback or non-speech interaction |
| TTS timeout | cancel/retry according to policy |
| malformed audio | reject before output |
| output device unavailable | update interaction state; do not claim speech occurred |
| audio underrun | recover buffer or stop safely |
| model incompatibility | reject deployment |
| wrong language | use language fallback/policy |
| pronunciation failure | apply approved dictionary/fallback |
| barge-in | stop/deprioritize speech |
| emergency | immediately preempt ordinary speech |
| privacy restriction | suppress speech |
| model produces unsafe/invalid result | reject output |

---

## 20. Provenance and observability

Every synthesized utterance SHOULD be attributable to:

- brain decision/request ID;
- interaction ID;
- model ID/version;
- runtime version;
- voice profile;
- language;
- prosody profile;
- timestamps;
- latency measurements;
- output status;
- cancellation reason;
- fallback status.

Raw generated audio SHOULD NOT be retained by default merely for observability. Retention requires an explicit policy and purpose.

---

## 21. Simulation and testing

TTS must be testable independently of the physical robot.

Required levels:

1. unit tests for request validation;
2. model/backend tests;
3. deterministic fixture tests;
4. streaming tests;
5. interruption tests;
6. latency benchmarks;
7. language tests;
8. pronunciation tests;
9. audio quality tests;
10. simulated interaction tests;
11. hardware-in-the-loop audio tests;
12. physical acoustic tests;
13. long-duration tests.

NeMo's current documentation provides TTS tutorials, pretrained checkpoints and configurable training/evaluation workflows, which can support experimentation and later customization. citeturn0search2turn0search7

---

## 22. Benchmark suite

The Novi TTS benchmark MUST measure at minimum:

### Latency

- time-to-first-audio;
- end-to-end response latency;
- interruption latency.

### Quality

- intelligibility;
- pronunciation accuracy;
- naturalness;
- prosody;
- consistency;
- artifact rate.

### Interaction

- turn-taking success;
- barge-in success;
- resume behavior;
- cancellation accuracy.

### Identity

- voice consistency across versions;
- speaker identity preservation;
- multilingual consistency.

### Resource usage

- GPU;
- CPU;
- memory;
- VRAM;
- power;
- thermal behavior.

### Reliability

- failure rate;
- recovery time;
- streaming underruns;
- model-load failures;
- long-duration stability.

---

## 23. Candidate implementation path

Initial candidates:

1. NVIDIA Riva TTS for an optimized local/edge-oriented deployment path.
2. NVIDIA NeMo TTS for research, customization and model experimentation.
3. Other validated TTS providers/models may be evaluated through the same Novi speech contract.

The first implementation SHOULD use the simplest backend that satisfies the latency, quality, privacy and hardware requirements. A distributed inference stack is not required merely because it exists.

---

## 24. Acceptance criteria

Speech synthesis architecture is considered validated only when Novi can demonstrate:

- stable voice identity;
- low-latency interactive speech;
- streaming output;
- interruption/barge-in;
- correct turn-taking;
- controlled prosody;
- correct pronunciation of required vocabulary;
- multilingual behavior where required;
- speech while continuing environmental perception;
- physical coordination with gaze/movement;
- privacy enforcement;
- deterministic cancellation semantics;
- fallback behavior;
- complete provenance;
- repeatable benchmark results.

---

## 25. Architectural invariants

1. TTS never decides Novi's intentions.
2. TTS never bypasses governance.
3. Speech output is cancellable.
4. Silence is a valid state.
5. Voice identity is versioned.
6. Prosody cannot silently change semantics.
7. Private information cannot bypass output policy.
8. A cancelled utterance is never recorded as completed.
9. Novi must be able to listen while speaking where hardware permits.
10. Speech must remain attributable to the cognitive decision that caused it.
11. Model/provider changes require validation before promotion.
12. TTS failure must never cause unsafe physical behavior.
13. Emotional expression is an output control, not proof of human emotion.
14. Generated speech is part of embodied behavior and must expose lifecycle events to the behavior system.

---

## 26. Open decisions / ADRs

The following remain intentionally unresolved until benchmarked:

- canonical Novi voice;
- first TTS model;
- Riva versus direct NeMo runtime;
- local versus distributed speech service;
- supported languages for Stage 1;
- target time-to-first-audio;
- acoustic hardware;
- speaker placement;
- maximum safe output level;
- voice customization policy;
- emotion/prosody limits;
- audio retention policy.

These decisions MUST be captured in ADRs after evidence is collected.

---

## 27. North-star behavior

Novi should not sound like a chatbot attached to a robot.

It should sound like **the same embodied Novi who is perceiving, remembering, thinking and acting in the world**.

That means speech must remain temporally connected to perception and action:

```text
Novi notices
    ↓
Novi attends
    ↓
Novi decides communication is useful
    ↓
Novi looks/orients
    ↓
Novi speaks
    ↓
Novi listens while speaking
    ↓
Novi notices the listener's response
    ↓
Novi adapts
```

Speech is therefore not the brain. It is one of the brain's **physical communication organs**.
