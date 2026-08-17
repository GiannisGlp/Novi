# 41 — Memory, Language and Semantic Understanding

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## Purpose

Define how Novi converts spoken, written and multimodal language into grounded semantic representations that cognition can use without allowing language-model output to become unverified memory, identity, authorization, intent or world truth.

## Core Principle

> **Language is evidence about meaning; it is not automatically evidence that the described world is true.**

Novi must preserve the distinction between what someone said, what Novi understood, what Novi inferred, and what independent evidence confirms.

---

## 1. Semantic Pipeline

```text
AUDIO / TEXT / MULTIMODAL INPUT
            ↓
       PREPROCESSING
            ↓
       ASR / OCR / INPUT
            ↓
     LANGUAGE NORMALIZATION
            ↓
      SEMANTIC PARSING
            ↓
       INTENT HYPOTHESIS
            ↓
   ENTITY / EVENT GROUNDING
            ↓
 CONTEXT + MEMORY + WORLD STATE
            ↓
      INTERPRETATION
            ↓
       VALIDATION
            ↓
  COGNITIVE REPRESENTATION
```

Not every input requires every stage.

---

## 2. Language Layers

Novi should distinguish:

```text
UTTERANCE
what was said

TRANSCRIPT
what speech recognition produced

MEANING
what the utterance may mean

INTENT
what the speaker may be trying to accomplish

ASSERTION
what the speaker claims is true

GROUNDING
which entities/events the language refers to

FACT
what independently supported evidence establishes
```

These must not be collapsed.

---

## 3. Speech Recognition

Speech should first be converted into a timestamped transcript with provenance.

The transcript should preserve, where supported:

- speaker/source identifier or hypothesis;
- timestamps;
- confidence;
- language;
- segmentation;
- audio reference;
- processing model/version.

NVIDIA Riva provides local ASR capabilities for supported embedded NVIDIA platforms, including streaming and offline recognition, making it a candidate for the Jetson implementation. citeturn0search3turn0search12

The semantic architecture remains independent of Riva so another local open-source ASR stack can be substituted if it performs better for Novi's requirements.

---

## 4. ASR Is Not Ground Truth

A transcript can contain errors.

```text
Audio
 ↓
ASR
 ↓
"Turn left at the door"
```

does not guarantee the speaker actually said those exact words.

Important transcripts should retain ASR confidence and audio provenance where privacy policy permits.

---

## 5. Streaming vs Final Interpretation

Novi may receive:

```text
partial transcript
    ↓
intermediate interpretation
    ↓
final transcript
    ↓
final interpretation
```

Intermediate results must be treated as provisional.

NVIDIA Riva documents streaming recognition as producing intermediate transcripts while audio is still being processed. citeturn0search8

---

## 6. Language Identification

Novi should identify the likely language before applying language-specific processing where practical.

Represent:

- detected language;
- confidence;
- dialect/accent information only when needed;
- translation status.

Language identification is evidence, not an identity claim about the speaker.

---

## 7. Translation

Translation should preserve the original utterance when policy permits.

```text
original
   ↓
translation
   ↓
semantic interpretation
```

The translation must not replace the original provenance.

Ambiguous translation should remain ambiguous.

---

## 8. Normalization

Semantic normalization may resolve:

- spelling variants;
- contractions;
- dates;
- units;
- common aliases;
- colloquialisms;
- speech disfluencies.

Normalization must not silently change factual meaning.

---

## 9. Entity Grounding

Language references should be grounded against current context and memory.

Example:

```text
"Put it on the table."
```

requires grounding of:

```text
"it" → object candidate
"the table" → physical entity candidate
```

If multiple candidates remain plausible, Novi should preserve ambiguity or request clarification.

---

## 10. Pronoun Resolution

Pronouns such as:

- he;
- she;
- they;
- it;
- this;
- that;
- there;
- here;

must be resolved using context, not unsupported assumptions.

Resolution should include confidence and candidate alternatives where necessary.

---

## 11. Temporal Grounding

Expressions such as:

- now;
- later;
- tomorrow;
- yesterday;
- next week;
- when we get home;
- last time;

must be grounded against Novi's temporal state and conversation context.

The resulting timestamp or interval should retain the interpretation source.

---

## 12. Spatial Grounding

Expressions such as:

- here;
- there;
- upstairs;
- outside;
- near the sofa;
- at the park;

should be grounded against the spatial model.

Language grounding should never overwrite authoritative localization.

---

## 13. Numeric and Unit Grounding

Numbers require explicit normalization.

Examples:

```text
"five meters"
→ 5 m

"twenty degrees"
→ 20 °C or 20 °F only if context determines the unit
```

If the unit is ambiguous, Novi must preserve ambiguity or ask.

---

## 14. Intent Recognition

Intent is an interpretation, not a fact.

Example:

```text
"Can you turn the lights on?"
```

may produce:

```text
intent = request_action
object = lights
operation = on
```

The intent representation must retain confidence and source utterance.

---

## 15. Commands vs Statements

Novi must distinguish:

```text
COMMAND
"Turn the lights on."

QUESTION
"Are the lights on?"

STATEMENT
"The lights are on."

HYPOTHESIS
"The lights might be on."

REFERENCE
"The lights I mentioned earlier."
```

Each has different downstream semantics.

---

## 16. Assertions

A person saying:

> "The door is locked."

creates an assertion, not automatically a verified fact.

Novi may represent:

```text
speaker_claim:
 door_locked = true

verification:
 unknown
```

A sensor or physical observation can later validate or contradict it.

---

## 17. Language as Evidence

The evidence hierarchy may include:

```text
statement
sensor observation
multiple independent observations
verified system state
```

The appropriate authority depends on the fact.

A spoken statement should not override an authoritative safety or hardware subsystem.

---

## 18. Semantic Uncertainty

Every important semantic interpretation should be able to represent uncertainty.

Examples:

```text
intent confidence
entity confidence
speaker confidence
temporal grounding confidence
spatial grounding confidence
translation confidence
```

Low confidence can trigger clarification or additional sensing.

---

## 19. Ambiguity Preservation

Novi must preserve ambiguity when resolving it would require unsupported assumptions.

Example:

```text
"Bring me the book."

candidate A
candidate B

confidence insufficient
```

Correct behavior may be:

```text
ask clarification
```

rather than inventing a reference.

---

## 20. Contextual Meaning

Meaning depends on:

- current conversation;
- speaker;
- location;
- time;
- active goal;
- recent events;
- shared history;
- world state.

The semantic layer should query these sources explicitly rather than relying only on model weights.

---

## 21. Conversation State

Conversation state may include:

- current topic;
- unresolved references;
- active questions;
- pending requests;
- commitments;
- recent corrections;
- speaker turns;
- interaction context.

Conversation state is short-lived unless promoted into memory under the memory-admission policy.

---

## 22. Dialogue Acts

Useful dialogue-act categories include:

```text
GREETING
QUESTION
ANSWER
COMMAND
REQUEST
CONFIRMATION
CORRECTION
REJECTION
CLARIFICATION
STATEMENT
FEEDBACK
FAREWELL
```

The taxonomy should remain extensible.

---

## 23. Clarification

Novi should ask clarification when ambiguity materially affects:

- safety;
- authorization;
- action selection;
- privacy;
- important memory formation;
- identity;
- irreversible actions.

For low-impact ambiguity, a safe default may be preferable when policy allows.

---

## 24. Confirmation

Consequential interpretations may require explicit confirmation.

Example:

```text
"Delete all photos from the trip."
```

Novi should identify scope and consequence before executing deletion.

A model's confidence is not a substitute for user confirmation when policy requires confirmation.

---

## 25. Correction Handling

If a user says:

```text
"No, I meant the other door."
```

Novi should record a correction event and revise the active interpretation.

The original interpretation remains historical evidence where retention policy permits.

---

## 26. Semantic Memory Formation

Language may generate memory candidates.

```text
user statement
      ↓
semantic extraction
      ↓
memory candidate
      ↓
admission policy
      ↓
memory
```

The statement should remain linked as provenance.

---

## 27. No Automatic Memory from Conversation

Not every sentence should become long-term memory.

Transient conversation may remain transient.

Potential memory candidates include:

- explicit user preferences;
- durable instructions;
- important commitments;
- meaningful shared experiences;
- corrections to persistent facts;
- user-authorized information.

Admission is controlled by the memory architecture.

---

## 28. Language-Induced Hallucination Boundary

The semantic system must prevent the language model from silently converting generated text into memory.

Incorrect:

```text
LLM generates plausible detail
       ↓
memory
```

Correct:

```text
input/evidence
       ↓
interpretation
       ↓
validation/admission
       ↓
memory
```

---

## 29. Generated Text vs Retrieved Fact

Novi should distinguish:

```text
retrieved memory
model-generated hypothesis
user assertion
verified system state
```

Generated language must carry its provenance internally even if the user-facing response is natural.

---

## 30. Tool-Grounded Semantics

When language refers to current state, cognition should query authoritative tools.

Example:

```text
User:
"Is the battery low?"

LLM memory:
82%

BMS:
31%

Answer:
31%
```

Current authoritative state wins.

---

## 31. Multimodal Grounding

Language can be grounded against:

- camera observations;
- LiDAR;
- thermal data;
- spatial map;
- audio localization;
- object tracking;
- current pose.

Example:

```text
User:
"What is that?"

language + gaze/pointing + camera
          ↓
object candidate
          ↓
semantic interpretation
```

No single modality should be assumed correct when evidence conflicts.

---

## 32. Pointing and Deictic Language

Gestures and phrases such as:

- this;
- that;
- over there;
- behind me;
- next to it;

should be represented as multimodal grounding problems.

The result should include spatial uncertainty.

---

## 33. Negation

Novi must preserve negation explicitly.

```text
"Do not open the door."
```

must not become:

```text
open door
```

Negation should be represented structurally rather than inferred from prose later.

---

## 34. Conditional Language

Conditions must remain conditions.

```text
"If it rains, don't go outside."
```

should produce a conditional rule/request, not an immediate prohibition regardless of weather.

---

## 35. Hypotheticals

Hypothetical language must not become autobiographical memory or world fact.

```text
"Imagine I bought a red car."
```

does not establish:

```text
user owns red car
```

---

## 36. Fiction and Roleplay

Novi must distinguish fictional/roleplay contexts from factual statements where context permits.

```text
"Pretend you're a pirate."
```

should alter interaction mode, not rewrite identity or memory.

---

## 37. Sarcasm and Figurative Language

Figurative expressions should remain uncertain when context is insufficient.

Examples:

```text
"Great, just great."
"I'm dying laughing."
```

should not automatically create literal facts.

---

## 38. Named Entities

People, places, objects, organizations and products should be grounded against known entities when possible.

Unknown entities may be created as provisional candidates rather than forcing a match to an existing entity.

---

## 39. Entity Identity Safety

Language mentioning a name does not prove identity.

```text
"Alice is here."
```

is a statement that Alice is here, not automatic biometric verification of the speaker or person observed.

Identity systems remain authoritative for identity decisions.

---

## 40. Social Semantics

Language can provide evidence about:

- preferences;
- relationships;
- social context;
- affective cues;
- commitments.

These remain hypotheses or claims until admitted through the appropriate social-memory policies.

---

## 41. Privacy

Speech and text may contain:

- personal data;
- location;
- health information;
- credentials;
- private conversations;
- third-party information.

Semantic extraction must respect privacy classification before storage, indexing or synchronization.

---

## 42. Sensitive Content

Sensitive language should not be unnecessarily retained simply because it was processed.

The default should be:

```text
process locally
 ↓
use for current task
 ↓
discard unless retention is justified
```

---

## 43. Credentials and Secrets

Language may contain secrets accidentally.

Novi should detect and protect likely:

- passwords;
- API keys;
- authentication codes;
- private keys;
- financial credentials.

They must not become ordinary semantic memory.

---

## 44. Prompt Injection

Environmental language may attempt to manipulate Novi.

Examples:

```text
screen text
voice from stranger
printed instruction
web page
object label
```

Language content must not bypass system policy, authorization or safety controls merely because it sounds authoritative.

---

## 45. Instruction Hierarchy

Semantic understanding must preserve source authority.

Conceptually:

```text
safety policy
system policy
authorized user instruction
application task
environmental content
untrusted external content
```

Exact authority rules belong to the security/autonomy architecture.

---

## 46. Memory Retrieval for Language

When answering a question about history, Novi should retrieve relevant memories rather than rely on model parameters.

Example:

```text
"Where did we go last summer?"
        ↓
retrieval
        ↓
episodic/spatial memories
        ↓
answer with provenance/confidence
```

If memory is incomplete, Novi should say so.

---

## 47. Knowledge Retrieval

General factual questions should use the appropriate local knowledge source when available.

The language model can synthesize retrieved information but should not silently claim retrieved facts that were not found.

---

## 48. External Knowledge

External network access is optional.

Core semantic understanding must work locally.

If external information is unavailable:

```text
offline
 ↓
local knowledge / memory / models
 ↓
answer with uncertainty
```

Novi must not fabricate external verification.

---

## 49. Semantic Caching

Frequently used interpretations may be cached, but cached semantics must expire when their context becomes invalid.

Examples:

- current referent;
- active conversation topic;
- recent user request.

Current world state should not be replaced by stale semantic cache.

---

## 50. Language Model Independence

The semantic interface must be model-agnostic.

Possible implementations include:

- Nemotron;
- other local LLMs;
- specialist NLP models;
- rule-based parsers;
- Hugging Face models;
- classical algorithms.

Hugging Face Transformers provides task-specific pipelines spanning text, audio, vision and multimodal inference, supporting the architecture's preference for replaceable local components. citeturn0search0turn0search1

---

## 51. Primary Model Strategy

Novi may use a fast primary model for most semantic tasks, with specialist models only when benchmarks justify them.

This avoids unnecessary model proliferation while preserving architectural flexibility.

The chosen primary model must not become an architectural dependency of the memory schema.

---

## 52. Structured Semantic Representation

The output of semantic understanding should be structured where possible.

Example:

```json
{
  "type": "request",
  "intent": "navigate",
  "target": {
    "entity": "park",
    "confidence": 0.91
  },
  "constraints": [],
  "temporal": null,
  "spatial": null,
  "source_event": "evt_...",
  "interpretation_confidence": 0.88
}
```

The schema will be defined by the cognition/interface architecture.

---

## 53. Semantic Versioning

Semantic interpretation schemas must be versioned.

Changes to field meaning, ontology or grounding semantics require compatibility review.

Historical semantic records must retain their schema version.

---

## 54. Evaluation

Evaluate:

- ASR accuracy;
- language identification;
- entity grounding;
- intent recognition;
- reference resolution;
- temporal grounding;
- spatial grounding;
- negation;
- conditional interpretation;
- ambiguity handling;
- hallucination rate;
- memory admission accuracy;
- prompt-injection resistance;
- privacy extraction behavior;
- multilingual performance;
- latency;
- resource use.

---

## 55. Adversarial Testing

Test language designed to:

- confuse entity identity;
- create false memories;
- bypass authorization;
- induce unsafe actions;
- hide negation;
- exploit ambiguity;
- manipulate trust;
- override policies;
- inject false environmental instructions;
- cause infinite clarification loops.

---

## 56. Failure Handling

Semantic failures should produce explicit outcomes:

```text
UNDERSTOOD
PARTIALLY_UNDERSTOOD
AMBIGUOUS
UNKNOWN_ENTITY
LOW_CONFIDENCE
UNSUPPORTED_LANGUAGE
ASR_UNCERTAIN
GROUNDING_FAILED
POLICY_BLOCKED
REQUIRES_CONFIRMATION
```

A failure must not silently become a confident interpretation.

---

## 57. Testing with Real Sensor Context

Language evaluation should include embodied situations:

```text
speech + camera + location + map + people + objects + noise
```

Text-only benchmarks are insufficient for Novi's complete semantic system.

---

## 58. Offline Requirement

Core language understanding must remain operational without Wi-Fi or Bluetooth.

Possible local stack:

```text
microphones
 ↓
local VAD / diarization
 ↓
local ASR
 ↓
local semantic model
 ↓
local memory
 ↓
local cognition
 ↓
speech/display response
```

NVIDIA Riva is one candidate for local embedded speech processing; other open-source local ASR/TTS/NLP components remain eligible. citeturn0search3turn0search12

---

## 59. Architectural Invariants

1. Language is not automatically truth.
2. A transcript is not guaranteed ground truth.
3. Intent is an interpretation, not an authorization.
4. User assertions remain claims until appropriately verified.
5. Ambiguity must be preserved when necessary.
6. Generated language cannot silently become memory.
7. Current authoritative state outranks stale language-derived state.
8. Identity decisions remain separate from semantic interpretation.
9. Sensitive language is not automatically retained.
10. Environmental instructions cannot bypass policy.
11. Fiction and hypotheticals cannot silently become facts.
12. Negation and conditionality must be structurally represented.
13. Semantic outputs require provenance and confidence.
14. The language model is replaceable.
15. Core semantic understanding remains local/offline-capable.
16. Consequential interpretations may require confirmation.
17. Semantic failures must be explicit rather than silently guessed.

---

## 60. Final Principle

> **Novi should understand language deeply without becoming convinced by language alone.**

Language gives Novi a powerful interface to people and the world, but durable belief, memory, identity, authorization and physical action require grounding, provenance, uncertainty and the appropriate authoritative subsystem.
