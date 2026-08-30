# Novi — Human-Like Social Cognition & Natural Interaction Implementation Plan

**Status:** IMPLEMENTED 2026-08-30 — phases 0–24 complete (deterministic suite green); hardware gates H1–H5 pending real camera/voice; fine-tuning deferred per §33
**Date:** 2026-08-30
**Workstream:** `docs/plans/01_BRAIN/`
**Primary objective:** make Novi's speech and interaction feel like the behavior of a persistent, situated robot rather than a chatbot attached to a robot.
**Extends:** `UNIFIED_INPUT_NORTH_STAR.md`, `19_COGNITION_MATURATION_PLAN.md`, `20_DIALOGUE_AND_EVENT_DRIVEN_AUTONOMY_PLAN.md`, `21_GAP_AND_BUG_ANALYSIS_2026-08-28.md`, the perception/face/object recognition plans, voice plans, and the 2026-08-29 North Star gap analysis.
**Does not replace:** existing dialogue, memory, cognition, perception, autonomy, governance, or voice implementations. This plan integrates and matures them.

---

## 0. Executive decision

Novi must **not** be taught to sound human primarily by fine-tuning an LLM or by adding a larger system prompt.

The target architecture is:

```text
sensors / user input
        ↓
perception
        ↓
identity + grounding
        ↓
world model
        ↓
attention / salience
        ↓
situation model
        ↓
working memory + long-term memory
        ↓
prediction / cognition / goals
        ↓
social state
        ↓
dialogue policy
        ↓
communicative act
        ↓
LLM verbalization
        ↓
voice / text / gesture
        ↓
observe consequence
        ↓
learn + remember
        └──────────────→ next cycle
```

The LLM is therefore primarily the **language realization layer** for a brain-selected communicative act. It must not independently invent the robot's world state, identity, memories, goals, or reasons for speaking.

The existing Novi audit identifies the central architectural problem: strong components exist, but several north-star links are not closed. In particular, the perception package is not yet fully consumed by the live brain, LLM reasoning is not the default production cognition path, primary memory retrieval is too similarity-centric, and learning does not yet reliably alter future behavior. fileciteturn2file0

The existing dialogue/autonomy plan already implements a unified input/response spine, natural dialogue machinery, social initiative, prediction-error curiosity, and proactive event speech. This plan therefore **must not rebuild those capabilities**; it adds the deeper social-cognitive state, persistent identity/object models, multimodal grounding, memory architecture, predictive interaction, and evaluation required to make the existing dialogue system genuinely situated. fileciteturn4file0

---

# 1. North-star behavior

Novi should eventually behave like this:

### Example A — person enters

```text
Camera:
  person detected

Face system:
  identity = Vano, confidence = 0.97

World model:
  Vano entered room
  Vano is 2.4m away
  Vano is facing Novi

Memory:
  Vano = familiar person / owner
  previous conversation = Novi architecture
  open topic = perception integration

Attention:
  Vano highly salient

Social state:
  interaction opportunity = high

Dialogue policy:
  action = INITIATE
  act = GREET + CONTINUE_TOPIC

LLM:
  "Hey. I was actually thinking about the perception side of Novi again."
```

The important property is that the sentence is **derived from current perception + identity + memory + situation + social policy**.

### Example B — familiar object moves

```text
Previous world state:
  black mug → desk

Current perception:
  black mug → kitchen

Object identity:
  same mug, confidence 0.94

World model:
  mug moved

Prediction:
  mug normally remains on desk

Prediction error:
  moderate

Attention:
  relevant because owner is nearby

Dialogue policy:
  comment only if salience > threshold

Possible utterance:
  "I noticed your mug moved."
```

Novi must not say this if it did not actually observe or have trustworthy evidence for the movement.

### Example C — ambiguous reference

```text
User:
  "Can you get that?"

Perception:
  blue bottle near user's hand
  red book farther away

Gaze/gesture:
  points toward blue bottle

Grounding:
  "that" → blue bottle

Planner:
  bottle is reachable

Dialogue:
  "The blue bottle?"
```

### Example D — memory-triggered continuation

```text
Current:
  Vano is discussing Novi.

Memory:
  unresolved question about camera integration.

Policy:
  CONTINUE

Novi:
  "There's one part of the camera integration we haven't closed yet."
```

No user question is required. The conversation is driven by continuity.

---

# 2. Current-state constraints and architectural rules

## 2.1 One brain-owned communication path

All communication remains owned by `MacBrain` / `brain.respond()` and the existing unified input architecture. Web, CLI, voice, visual events, and autonomous events must never implement their own independent conversational intelligence.

The existing dialogue plan explicitly establishes this invariant. fileciteturn4file0

## 2.2 One canonical world model

Face, object, speech, tracking, spatial and sensor evidence must become evidence for the same world model. Do not create a separate conversational world database.

## 2.3 One canonical identity model

Do not let voice, face, dialogue, or web surfaces maintain independent copies of person identity.

## 2.4 Memory is not conversation state

Keep these separate:

```text
ConversationState = what is happening in this interaction now
WorkingMemory    = what is currently active in Novi's cognition
LongTermMemory   = durable knowledge/episodes/preferences
WorldModel       = current beliefs about the external environment
```

## 2.5 Perception is evidence, not truth

Every visual/audio observation must carry confidence, provenance, timestamp and epistemic status. A recognition result must never silently become an absolute fact.

## 2.6 Silence is a valid action

`SILENCE` must be a first-class dialogue act. Novi should not narrate every observation.

## 2.7 Initiative must have a reason

Every autonomous communicative act must record a machine-readable `initiative_reason` and supporting evidence.

## 2.8 No hallucinated grounding

If Novi cannot identify a person/object/reference confidently enough, it must say so or ask for clarification rather than fabricate identity or location.

## 2.9 Safety remains outside language generation

The LLM can propose communicative text and high-level intentions. It cannot bypass autonomy governance, physical command validation, actuator safety, or rate/expiry controls. The North Star audit identifies the production physical authority boundary as an important existing gap and this plan must not weaken that boundary. fileciteturn2file0

---

# 3. Target module architecture

Use the existing package structure where possible. Introduce new modules only when a current module has no appropriate ownership boundary.

```text
novi/brain/
├── interaction/
│   ├── __init__.py
│   ├── conversation_state.py
│   ├── dialogue_policy.py
│   ├── dialogue_act.py
│   ├── turn_manager.py
│   ├── initiative.py
│   ├── social_context.py
│   ├── grounding.py
│   ├── reference_resolution.py
│   └── repair.py
│
├── identity/
│   ├── __init__.py
│   ├── person_model.py
│   ├── identity_resolution.py
│   ├── relationship_model.py
│   └── object_identity.py
│
├── memory/
│   ├── working_memory.py
│   ├── retrieval_policy.py
│   ├── episodic_memory.py
│   ├── semantic_memory.py
│   ├── social_memory.py
│   ├── prospective_memory.py
│   └── memory_projection.py
│
├── cognition/
│   ├── prediction.py
│   ├── social_reasoning.py
│   ├── hypothesis_manager.py
│   └── attention_controller.py
│
└── language/
    ├── context_builder.py
    ├── response_generator.py
    ├── verbalizer.py
    └── model_router.py
```

Before creating any file, inspect the existing implementation and reuse/extend it when the responsibility already exists. In particular, do not create a second `salience.py`, `dialogue.py`, `attention.py`, `world_model.py`, `router.py`, or memory store if an existing implementation can be extended safely.

---

# 4. Phase 0 — architecture truth pass

## Task 0.1 — inventory existing implementations

Read and map:

- `novi/brain/engine.py`
- `novi/brain/chat.py`
- `novi/brain/dialogue.py`
- `novi/brain/salience.py`
- `novi/brain/attention.py`
- `novi/brain/world_model.py`
- `novi/brain/world_state_adapter.py`
- `novi/brain/situation_model.py`
- `novi/brain/context_assembler.py`
- `novi/brain/storage.py`
- `novi/brain/memory_hardening.py`
- `novi/brain/consolidation.py`
- `novi/brain/learning_pipeline.py`
- `novi/brain/sleep_cycle.py`
- `novi/brain/prediction.py`
- `novi/brain/cognition_typed.py`
- `novi/brain/router.py`
- `novi/brain/reasoning.py`
- `novi/brain/self_model.py`
- `novi/perception/`
- `novi/voice/`
- existing identity/face/object recognition modules
- contracts under `novi/contracts/`

## Task 0.2 — produce an ownership table

For every capability record:

```text
capability
current owner
production entry point
current consumers
missing consumers
persistent?
tested?
hardware tested?
planned replacement
```

## Task 0.3 — prohibit duplicate architecture

Before implementation, mark existing modules as:

```text
KEEP
EXTEND
ADAPTER ONLY
DEPRECATE
REMOVE AFTER MIGRATION
```

Acceptance:

- no duplicate conversation engine;
- no duplicate world model;
- no duplicate memory DB;
- no duplicate person identity registry;
- no second response path.

---

# 5. Phase 1 — close perception → identity → world model

This is the highest priority because the North Star audit identifies the live perception-to-world-model connection as a major missing link. fileciteturn2file0

## Task 1.1 — define canonical observation contract

Every perception result should normalize into an observation containing at minimum:

```python
Observation(
    observation_id,
    timestamp,
    source,
    modality,
    entity_candidate,
    attributes,
    location,
    confidence,
    uncertainty,
    provenance,
    epistemic_status,
)
```

Example:

```json
{
  "modality": "vision",
  "entity_candidate": "person",
  "identity_candidate": "vano",
  "confidence": 0.97,
  "location": {"frame": "camera", "x": 1.2, "y": 0.4},
  "provenance": "front_camera:frame:18322",
  "epistemic_status": "OBSERVED"
}
```

## Task 1.2 — wire camera pipeline into engine

Use the existing perception pipeline and adapter rather than bypassing it with legacy presence updates.

Required path:

```text
camera
 → perception pipeline
 → tracking
 → face/object recognition
 → grounding
 → world-state adapter
 → WorldModel
 → attention/situation
```

Acceptance:

A scripted frame passed through `MacBrain.step()` creates an `OBSERVED` person/object entity in the same world model consumed by cognition and dialogue.

## Task 1.3 — preserve uncertainty

Propagate confidence/uncertainty through:

```text
perception
 → fusion
 → world model
 → context assembler
 → reasoning
 → dialogue policy
```

If two independent observations support the same entity, fusion may increase confidence/reduce uncertainty; it must never manufacture certainty.

## Task 1.4 — spatial identity

Every persistent object/person entity should optionally have:

```text
spatial_ref
coordinate_frame
pose
last_seen
first_seen
region
```

Use existing spatial-map functionality instead of semantic-only `location` strings.

---

# 6. Phase 2 — persistent person recognition

## Task 2.1 — create `PersonModel`

Canonical fields:

```text
person_id
identity_status
canonical_name
aliases
face_identity_refs
voice_identity_refs
confidence
first_seen
last_seen
usual_locations
known_relationships
interaction_count
recent_interactions
preferences
communication_patterns
consent/privacy metadata
```

Do not store raw biometric data in ordinary conversation memory. Keep biometric references separate and access-controlled.

## Task 2.2 — identity lifecycle

Implement:

```text
UNKNOWN
CANDIDATE
RECOGNIZED
CONFIRMED
AMBIGUOUS
REJECTED
```

Recognition must not automatically mean confirmation.

Example:

```text
face match 0.61
→ CANDIDATE

face match 0.96 + repeated observations
→ RECOGNIZED
```

## Task 2.3 — cross-modal identity

Fuse:

```text
face
voice
conversation self-identification
known location/context
```

Example:

```text
face → candidate Vano .91
voice → candidate Vano .94
context → owner relationship

combined → Vano .98
```

If modalities disagree:

```text
face → Vano .96
voice → unknown .72
```

retain the contradiction and lower identity confidence rather than forcing a match.

## Task 2.4 — recognition event

Emit:

```text
identity.recognized
identity.lost
identity.ambiguous
identity.reidentified
```

These events enter the same InputBus/event pipeline already used by autonomous dialogue. The existing dialogue/autonomy plan has already established event-driven autonomous speech as the mechanism; this phase supplies richer identity evidence to it. fileciteturn4file0

---

# 7. Phase 3 — persistent object identity

## Task 3.1 — object entity model

Canonical object fields:

```text
object_id
class
appearance_signature
instance_embedding_ref
owner_candidate
first_seen
last_seen
usual_location
current_location
state
confidence
history
relationships
```

## Task 3.2 — instance re-identification

Distinguish:

```text
"a mug"
```

from:

```text
"Vano's black mug"
```

and from:

```text
"that same black mug we saw yesterday"
```

## Task 3.3 — object lifecycle

```text
DETECTED
TRACKED
IDENTIFIED
PERSISTENT
LOST
REACQUIRED
RETIRED
```

## Task 3.4 — object event semantics

Emit:

```text
object.detected
object.recognized
object.moved
object.disappeared
object.reappeared
object.state_changed
```

Do not make every event conversational. Dialogue salience decides whether an event becomes speech.

---

# 8. Phase 4 — working memory

Create a bounded working-memory layer in front of durable storage.

## Task 4.1 — working memory structure

```text
WorkingMemory
├── current_person
├── current_topic
├── active_references
├── current_scene
├── active_goal
├── unresolved_questions
├── recent_events
├── recent_utterances
├── current_hypotheses
├── active_plan
└── pending_commitments
```

## Task 4.2 — lifecycle

At each turn/cycle:

```text
load relevant state
→ update
→ score importance
→ expire stale entries
→ promote important entries to long-term memory
```

## Task 4.3 — boundedness

Working memory must have explicit limits:

```text
max items
max tokens
max event age
max unresolved references
```

Acceptance:

A 30-minute interaction does not cause unbounded prompt growth.

---

# 9. Phase 5 — memory architecture maturation

The existing durable memory is retained. The missing work is semantic separation and retrieval policy.

## Task 5.1 — memory classes

Implement logical projections for:

```text
EPISODIC
SEMANTIC
SOCIAL
AUTOBIOGRAPHICAL
OBJECT
SPATIAL
PROCEDURAL
PROSPECTIVE
PREFERENCE
METAMEMORY
```

They may initially share the existing SQLite substrate. Do not create multiple databases.

## Task 5.2 — memory record example

```json
{
  "memory_id": "mem-1821",
  "type": "EPISODIC",
  "subject": "Vano",
  "episode": "Vano and Novi discussed camera integration",
  "timestamp": "2026-08-30T...",
  "importance": 0.84,
  "confidence": 0.98,
  "provenance": "conversation",
  "entities": ["person:vano", "topic:camera-integration"],
  "location": "office",
  "privacy_class": "private"
}
```

## Task 5.3 — retrieval score

Replace similarity-only primary retrieval with a composite policy:

```text
score =
  semantic_relevance
+ temporal_relevance
+ person_relevance
+ situation_relevance
+ goal_relevance
+ causal_relevance
+ importance
+ confidence
+ provenance_quality
+ spatial_relevance
+ novelty
- contradiction_penalty
- staleness_penalty
```

Keep vector similarity as one signal, not the decision.

## Task 5.4 — memory provenance

Every memory used to influence a response must be traceable to its source.

The context builder should be able to produce:

```text
memory_id
why retrieved
confidence
source
last updated
```

## Task 5.5 — memory consolidation

Use the existing sleep/consolidation pipeline to:

```text
replay episodes
merge duplicates
strengthen recurring facts
supersede contradicted facts
promote important events
expire low-value memories
learn routines
```

Do not implement replay as only a fixed numeric bump; consolidation must use evidence and recurrence.

---

# 10. Phase 6 — prospective memory and commitments

This is necessary for continuity and natural follow-up.

## Task 6.1 — represent future intentions

```text
ProspectiveMemory(
  trigger,
  intended_action,
  owner,
  created_at,
  due_at,
  status,
  priority,
  confidence,
  source
)
```

Example:

```text
Vano:
  "Remind me to test the camera after we finish this."

Prospective memory:
  trigger = conversation_end OR explicit request
  action = remind_vano(camera_test)
```

## Task 6.2 — spontaneous follow-up

When trigger conditions occur:

```text
prospective memory
 → salience
 → dialogue policy
 → INITIATE / ASK / REMIND
```

Example:

> "We said we'd test the camera after this. Want to do that now?"

---

# 11. Phase 7 — social state

Create a short-lived `SocialContext` derived from perception + person model + conversation.

Fields:

```text
addressee
relationship
interaction_phase
attention_to_novi
user_availability
user_engagement
conversation_temperature
interruptibility
familiarity
social_opportunity
```

Do not claim to infer private mental states. Use observable, probabilistic descriptions.

Bad:

```text
Vano is angry.
```

Better:

```text
speech tempo increased
volume increased
facial expression uncertain
→ interaction tone may be tense, confidence 0.58
```

---

# 12. Phase 8 — attention and salience

The existing attention/salience implementation should become the bridge between perception and dialogue.

## Task 8.1 — calculate attention

Use:

```text
conversation relevance
person relevance
current goal
novelty
motion
safety
prediction error
object importance
spatial proximity
social opportunity
```

## Task 8.2 — separate attention from speech

```text
attention = "notice"
salience = "important"
dialogue policy = "worth saying"
```

An event may be highly salient but still not worth interrupting the user about.

## Task 8.3 — anti-narration guard

Examples that should normally remain silent:

```text
chair detected
wall detected
same mug seen again
same person remains seated
```

Examples potentially worth speaking:

```text
person enters
important person leaves
unexpected object appears
known object disappears
user explicitly looks/points at object
safety event
task completes
prediction fails significantly
open commitment becomes due
```

---

# 13. Phase 9 — predictive social cognition

Novi should not only react to observations. It should maintain predictions.

## Task 9.1 — prediction records

```text
Prediction(
  subject,
  expected_state,
  expected_time_window,
  confidence,
  source,
  consequence_if_wrong
)
```

Example:

```text
Expected:
  Vano remains at desk.

Observed:
  Vano closes laptop and picks up keys.

Prediction error:
  high
```

## Task 9.2 — convert prediction error into cognition

```text
prediction error
 → hypothesis generation
 → alternative explanations
 → evidence gathering
 → updated belief
 → optional goal
```

Do not jump directly from prediction error to speech.

## Task 9.3 — alternatives

Fix the existing shallow hypothesis behavior so that alternatives are real candidates:

```text
Hypothesis A: Vano is leaving
Hypothesis B: Vano is taking a break
Hypothesis C: Vano is changing location
```

Score by:

```text
probability
expected evidence
risk
cost
relevance
```

---

# 14. Phase 10 — dialogue policy as the social decision layer

This is the most important new control point.

Implement/extend:

```text
DialoguePolicy.decide(context) -> DialogueDecision
```

Inputs:

```text
conversation state
world state
person identity
social context
working memory
retrieved long-term memories
active goals
predictions
attention
salience
prospective memory
recent speech
speaking lease
initiative budget
```

Outputs:

```text
SILENCE
RESPOND
ASK
CLARIFY
ACKNOWLEDGE
COMMENT
INFORM
SUGGEST
WARN
FOLLOW_UP
GREETING
FAREWELL
INITIATE
CONTINUE
INTERRUPT
REPAIR
```

## Task 10.1 — decision object

```python
DialogueDecision(
    act="CONTINUE",
    target="person:vano",
    topic="camera integration",
    reason="unfinished_thread",
    evidence=[...],
    confidence=0.91,
    urgency=0.18,
    interruption_cost=0.08,
    expected_value=0.82,
    verbosity="short",
    tone="conversational",
)
```

## Task 10.2 — explicit `why_now`

Every proactive decision must contain:

```text
why_now
why_this_person
why_this_topic
why_this_verbosity
why_speak
```

This becomes part of observability and evaluation.

---

# 15. Phase 11 — initiative scoring

Build on the already-existing `SocialInitiative` and event-salience system instead of replacing it. The existing plan already gates autonomous speech through speaking leases, budgets and cooldowns. fileciteturn4file0

Target score:

```text
initiative_score =
    relevance
  × confidence
  × social_opportunity
  × novelty
  × expected_value
  × urgency
  - interruption_cost
  - repetition_penalty
  - fatigue_penalty
```

Suggested policy bands:

```text
< 0.25      SILENCE
0.25–0.50   HOLD
0.50–0.70   MONITOR
0.70–0.85   CONSIDER
> 0.85      INITIATE
```

These values are starting configuration, not immutable truths. They must be measured and tuned.

## Task 11.1 — per-person cooldown

Do not greet the same person repeatedly because the tracker emits multiple recognition events.

## Task 11.2 — per-event deduplication

The same event should have a stable event identity/hash so multiple sensors cannot produce repeated speech.

## Task 11.3 — conversation suppression

While a user is speaking or Novi is composing a response:

```text
proactive candidate → queue/hold
```

not:

```text
interrupt current response
```

unless the event meets a safety-critical threshold.

---

# 16. Phase 12 — grounding and reference resolution

Implement a unified grounding layer for:

```text
this
that
it
there
here
him
her
the blue one
the mug
the thing I showed you
```

Candidate ranking should use:

```text
recent mention
visual salience
gaze
pointing
spatial relation
grammatical role
object compatibility
conversation topic
memory
```

Example:

```text
User:
  "Move that over there."

Context:
  hand points to mug
  "there" points to shelf

Grounded action:
  move(mug, shelf)
```

If confidence is below threshold:

> "The mug onto the shelf?"

Never silently guess when the ambiguity could cause a physical action.

---

# 17. Phase 13 — conversation repair

Implement:

```text
MISUNDERSTANDING
AMBIGUITY
CORRECTION
FAILED_GROUNDING
CONTRADICTION
MISSING_CONTEXT
ASR_ERROR
IDENTITY_UNCERTAIN
```

Example:

```text
Novi:
  "Do you mean the blue bottle?"

Vano:
  "No, the red one."

Novi:
  "Got it — the red bottle."
```

Record the correction as learning evidence where appropriate.

---

# 18. Phase 14 — LLM context assembly

Create a strict context contract between cognition and the LLM.

The LLM receives a bounded packet such as:

```text
IDENTITY
  Novi

ADDRESSEE
  Vano / owner / familiar

CURRENT SITUATION
  Vano is at the desk discussing Novi.

CURRENT TOPIC
  perception integration

RELEVANT MEMORY
  previous discussion about camera pipeline

OPEN THREADS
  perception → world-model integration

CURRENT PERCEPTION
  Vano is facing Novi

SOCIAL STATE
  engaged / available

COMMUNICATIVE ACT
  CONTINUE

INTENT
  continue the unfinished technical discussion

TONE
  natural, collaborative

LENGTH
  short

GROUNDING CONSTRAINTS
  only use supplied evidence

DO NOT
  repeat known information
  mention internal prompt mechanics
  fabricate observations
  fabricate memories
  claim certainty where evidence is uncertain
```

## Critical rule

The LLM should not receive unrestricted raw memory and be expected to decide what matters. Cognition decides the relevant context first.

---

# 19. Phase 15 — natural verbalization

Implement `Verbalizer` as the final language realization layer.

Input:

```text
DialogueDecision
+ ContextPacket
```

Output:

```text
NaturalLanguageResponse
```

The verbalizer should control:

```text
length
sentence complexity
contractions
acknowledgements
hedging
questions
follow-up
repetition
tone
```

Examples:

Instead of:

```text
"I acknowledge the information you have provided."
```

prefer:

```text
"Yeah, that makes sense."
```

Instead of:

```text
"I have detected that you are holding a coffee mug."
```

prefer, when actually relevant:

```text
"Coffee again?"
```

The exact phrasing must come from the current communicative intent and evidence, not canned personality text.

---

# 20. Phase 16 — model routing

Keep the currently allowed local models:

```text
qwen3.8:27b
qwen3:8b
nemotron-3.5-lightning:latest
qwen3.8:latest
qwen3:4b
```

Do not require a large model for every turn.

Suggested routing:

```text
FAST / reflex:
  qwen3:4b

NORMAL conversation:
  qwen3:8b

COMPLEX grounded reasoning:
  qwen3.8:27b

SPECIALIZED latency experiments:
  nemotron-3.5-lightning:latest

EXPERIMENTAL:
  qwen3.8:latest
```

The router must select based on task complexity, latency budget, context size, uncertainty and required reasoning depth.

The model is never the source of truth for:

```text
identity
location
world state
memory existence
safety authorization
physical command validity
```

---

# 21. Phase 17 — voice integration

The existing voice loop must remain a thin surface around the brain.

Target:

```text
microphone
 → VAD
 → speaker identification
 → ASR
 → InputBus
 → brain
 → DialogueDecision
 → verbalizer
 → TTS
```

Not:

```text
microphone
 → local LLM
 → TTS
```

## Task 17.1 — speaker identity

Combine speaker diarization/voice identity with face identity when available.

## Task 17.2 — turn taking

Support:

```text
start speaking
pause
interrupt
resume
backchannel
finish
```

## Task 17.3 — barge-in

If user starts speaking while Novi speaks:

```text
stop/attenuate TTS
preserve unfinished communicative state
listen
replan
```

---

# 22. Phase 18 — learning from interaction

Novi must learn from consequences, not merely store transcripts.

## Task 18.1 — interaction outcome

Every meaningful interaction records:

```text
input
perception context
retrieved memories
cognitive decision
chosen dialogue act
generated response
user reaction
correction
outcome
```

## Task 18.2 — explicit correction

If Vano says:

> "No, that's not what I meant."

record:

```text
previous interpretation = incorrect
correct interpretation = ...
source = explicit user correction
confidence = high
```

## Task 18.3 — behavioral learning

Learning must affect future behavior through persisted policy/knowledge rather than only in-memory objects. The North Star audit specifically identifies current learning subsystems as largely in-memory and not reliably behavior-changing. fileciteturn2file0

Examples:

```text
Vano dislikes repeated explanations
→ lower verbosity after known context

Vano usually wants direct answers
→ increase directness preference

Vano prefers technical detail for Novi discussions
→ higher technical-depth preference in this topic
```

These are preferences, not immutable personality assumptions.

---

# 23. Phase 19 — autobiographical continuity

Novi needs a durable model of its own interaction history without confusing that with fabricated consciousness.

Represent:

```text
what Novi did
what Novi observed
what Novi decided
what succeeded
what failed
what it learned
what remains unresolved
```

Example:

```text
Yesterday:
  Novi attempted camera recognition test.

Outcome:
  object recognition failed under low light.

Learning:
  low-light confidence should be reduced.

Today:
  camera enters low-light condition.

Prediction:
  recognition confidence expected to be lower.
```

This creates behavioral continuity without pretending that the model has human subjective experience.

---

# 24. Phase 20 — proactive conversation scenarios

Implement deterministic scenarios before real hardware.

## Scenario P1 — person enters

```text
unknown person enters
→ detect
→ face candidate
→ no high-confidence identity
→ salience
→ policy
→ greet cautiously
```

Example:

> "Hey — I don't think we've met before."

## Scenario P2 — known person enters

> "Hey Vano."

Then optionally continue an open thread if social opportunity is high.

## Scenario P3 — familiar object disappears

```text
mug present
→ mug missing
→ last known location
→ confidence
→ policy
```

Potential:

> "Your mug isn't on the desk anymore."

## Scenario P4 — unusual sound

```text
hearing anomaly
→ confidence
→ event salience
→ policy
```

Potential:

> "That sounded unusual. Did you hear it?"

## Scenario P5 — task completion

> "The camera test is finished."

## Scenario P6 — unresolved conversation thread

> "There's one thing we haven't settled yet."

## Scenario P7 — user is unavailable

Novi remains silent despite a salient non-urgent event.

## Scenario P8 — user is already speaking

Novi does not interrupt.

## Scenario P9 — safety event

Safety policy overrides ordinary social suppression.

---

# 25. Phase 21 — deterministic test architecture

No hardware or live LLM is required for the main CI suite.

Create/extend tests for:

```text
conversation_state
person_model
identity_resolution
object_identity
memory_retrieval_policy
working_memory
grounding
reference_resolution
dialogue_policy
initiative
social_context
prediction
verbalizer
model_router
voice_turn_manager
```

## Required test classes

### Identity

- same face repeatedly resolves to same person;
- unknown face remains unknown;
- ambiguous face remains ambiguous;
- contradictory modalities preserve contradiction;
- confidence never becomes 1.0 without evidence.

### Object identity

- same object reidentified across frames;
- similar objects remain separate;
- object disappearance is emitted once;
- reacquisition links to prior instance when evidence supports it.

### Memory

- relevant episodic memory beats unrelated recent memory;
- recent relevant memory beats old weak memory;
- low-confidence memory is down-ranked;
- contradicted memory is not silently treated as truth;
- retrieval remains bounded;
- memory retrieval is explainable.

### Dialogue

- answer when addressed;
- silence when nothing relevant is happening;
- proactive comment only above threshold;
- no duplicate greeting;
- no repeated remark after cooldown;
- no proactive speech during active turn unless safety-critical;
- unresolved thread can produce follow-up.

### Grounding

- "that" resolves to visually/linguistically supported object;
- ambiguous reference triggers clarification;
- physical action cannot proceed on unresolved ambiguity.

### Naturalization

- no assistant-style boilerplate;
- no unnecessary repetition;
- no fabricated memories;
- no fabricated observations;
- no unsupported certainty;
- short response when short act is selected.

---

# 26. Phase 22 — end-to-end deterministic simulations

Build a scripted world simulator:

```text
WorldSimulator
├── people
├── objects
├── rooms
├── events
├── time
├── speech
├── gaze
├── gestures
└── sensor noise
```

Example timeline:

```text
T0  empty room
T1  Vano enters
T2  Vano looks at Novi
T3  Vano says "Hey Novi"
T4  Novi answers
T5  Vano puts mug on desk
T6  Vano leaves
T7  mug disappears
T8  Vano returns
```

Expected trace:

```text
T1 identity recognized
T2 social opportunity rises
T3 response decision
T4 natural answer
T5 object identity established
T6 farewell/hold
T7 object disappearance event
T8 possible observation/comment depending on salience
```

The exact utterance can vary. The **decision, grounding, evidence and safety invariants cannot**.

---

# 27. Phase 23 — observability and replay

Every meaningful interaction should produce a decision trace:

```text
trace_id
cycle_id
time
input/event
perception evidence
world changes
identity resolution
retrieved memories
attention scores
prediction
cognitive hypotheses
goals
social context
dialogue candidates
selected decision
initiative score
LLM model
LLM latency
response
outcome
memory writes
```

Example:

```json
{
  "event": "identity.recognized",
  "person": "Vano",
  "confidence": 0.97,
  "initiative_score": 0.86,
  "decision": "CONTINUE",
  "reason": "open_conversation_thread",
  "memory_ids": ["mem-1821"],
  "model": "qwen3:8b"
}
```

This is required to debug why Novi said something.

It also closes part of the existing decision-observability gap identified by the North Star audit. fileciteturn2file0

---

# 28. Phase 24 — evaluation metrics

Do not evaluate "human-like" only by subjective impression.

Track:

## Grounding

```text
person identification accuracy
object identity accuracy
reference resolution accuracy
location grounding accuracy
false grounding rate
```

## Memory

```text
memory retrieval precision
memory retrieval recall
contradiction handling
memory usefulness
cross-session continuity
```

## Conversation

```text
turn-taking success
interruptions
repair success
context continuity
repetition rate
unnecessary verbosity
```

## Initiative

```text
appropriate initiative rate
unnecessary initiative rate
missed initiative rate
duplicate initiative rate
cooldown violations
```

## Naturalness

Human evaluation dimensions:

```text
naturalness
context awareness
appropriateness
coherence
personality consistency
memory continuity
social timing
```

## Safety

```text
unsupported claim rate
unsafe grounding rate
unauthorized action attempts
ambiguous-action execution rate
```

The target is not "talk more like a human"; it is **behave appropriately given the same evidence and context a situated human interaction partner would have**.

---

# 29. Phase 25 — real-robot acceptance gates

## Gate H1 — recognition

Novi identifies the owner across:

- different distances;
- moderate lighting changes;
- different orientations;
- partial occlusion;
- multiple people.

False positive identity must be below the defined safety threshold.

## Gate H2 — object continuity

Novi can identify a known object after it leaves and re-enters view, when visual evidence supports that conclusion.

## Gate H3 — grounded conversation

10-minute natural conversation:

- remembers current topic;
- uses relevant previous information;
- resolves references;
- handles corrections;
- does not repeatedly restart context.

## Gate H4 — proactive behavior

During a 30-minute session Novi:

- initiates when there is a meaningful reason;
- remains silent when there is not;
- does not repeat itself;
- does not interrupt normal speech;
- can follow an unresolved thread.

## Gate H5 — multimodal continuity

The same interaction continues across:

```text
voice → vision → voice → physical event → voice
```

without resetting conversational identity.

## Gate H6 — failure honesty

When recognition or grounding confidence is insufficient, Novi explicitly expresses uncertainty or asks for clarification.

## Gate H7 — safety

No language-generation path can bypass the physical authority boundary.

---

# 30. Implementation order — exact sequence

Do not implement all layers simultaneously. Use the following dependency order.

```text
01  architecture truth map
02  canonical observation contract
03  perception → world-model integration
04  persistent person identity
05  persistent object identity
06  working memory
07  memory-type projections
08  composite memory retrieval
09  social context
10  attention/salience integration
11  prediction + prediction error
12  grounding/reference resolution
13  dialogue policy
14  initiative scoring integration
15  context packet
16  LLM verbalizer
17  model routing
18  voice integration
19  interaction outcome recording
20  persistent learning
21  proactive follow-up
22  deterministic world simulator
23  end-to-end replay traces
24  real-device gates
25  performance optimization
26  optional fine-tuning
```

Never jump to step 26 to compensate for missing steps 1–25.

---

# 31. Suggested implementation commits

Keep changes reviewable.

```text
01 docs: define social cognition architecture
02 brain: add canonical observation integration
03 brain: wire perception into world model
04 brain: add persistent person model
05 brain: add object identity continuity
06 brain: add bounded working memory
07 brain: add typed memory projections
08 brain: add composite memory retrieval
09 brain: add social context
10 brain: connect attention to dialogue policy
11 brain: add predictive interaction state
12 brain: add multimodal grounding
13 brain: add dialogue policy decisions
14 brain: strengthen initiative gating
15 brain: add grounded LLM context contract
16 brain: add verbalizer
17 brain: integrate model routing
18 voice: route speaker turns through brain
19 brain: persist interaction outcomes
20 brain: persist behavioral learning
21 tests: add deterministic social cognition scenarios
22 tests: add world simulator acceptance suite
23 observability: add end-to-end decision traces
```

Each commit must keep existing tests green and avoid introducing a second architecture.

---

# 32. What not to do

Do **not**:

1. fine-tune the LLM before the cognition loop is grounded;
2. send every camera frame to the LLM;
3. use vector similarity as the only memory selector;
4. let the LLM invent world state;
5. let the LLM decide physical authorization;
6. create separate databases for each memory type;
7. create a separate chatbot subsystem;
8. let each surface own its own personality or prompt;
9. continuously narrate perception;
10. equate face detection with person identity;
11. equate object classification with object-instance identity;
12. treat probabilistic recognition as certainty;
13. store every observation permanently;
14. use canned responses as the primary naturalness mechanism;
15. make proactive speech unconditional;
16. interrupt users for low-value events;
17. make "human-like" mean deceptive claims of human emotion/consciousness;
18. use cloud services as a requirement for the core architecture;
19. bypass the existing governance/autonomy safety path;
20. build parallel implementations of capabilities that already exist in Novi.

---

# 33. Fine-tuning / training — only after the architecture works

Once Novi has sufficient real interaction traces, training may improve verbalization and policy.

Training examples should look like:

```json
{
  "situation": {
    "person": "Vano",
    "world": "Vano is at desk",
    "topic": "camera integration",
    "memory": ["unfinished camera discussion"],
    "social": "engaged",
    "attention": "Vano"
  },
  "decision": {
    "act": "CONTINUE",
    "reason": "unfinished_thread",
    "verbosity": "short"
  },
  "response": "There's one part of the camera integration we haven't closed yet."
}
```

Potential future training targets:

```text
response naturalization
initiative ranking
turn-taking
repair behavior
reference resolution
memory usefulness ranking
style adaptation
```

But learned policies must remain bounded by deterministic grounding, memory provenance, safety, and governance.

---

# 34. Final architecture acceptance criterion

Novi reaches the first meaningful milestone when the following sentence is true:

> **Novi can see and recognize the people and objects around it, maintain those identities in a persistent world model, remember relevant previous interactions, understand the current social situation, decide whether speaking is appropriate, choose what communicative act to perform, generate natural language from that grounded internal state, speak through the normal brain-owned voice path, observe what happened next, and update its memory — without requiring the user to initiate every interaction.**

The complete loop must be:

```text
PERCEIVE
  ↓
IDENTIFY
  ↓
GROUND
  ↓
WORLD MODEL
  ↓
MEMORY
  ↓
ATTENTION
  ↓
SITUATION
  ↓
PREDICT
  ↓
COGNITION
  ↓
GOALS / CURIOSITY
  ↓
SOCIAL STATE
  ↓
DIALOGUE POLICY
  ↓
SILENCE / COMMUNICATIVE ACT
  ↓
LLM VERBALIZATION
  ↓
VOICE / TEXT / GESTURE / ACTION
  ↓
OBSERVE CONSEQUENCE
  ↓
LEARN
  ↓
MEMORY
  └──────────────────────→ next cycle
```

---

# 35. Relationship to existing Novi plans

This plan is an integration/maturation layer, not a replacement for prior work.

- `19_COGNITION_MATURATION_PLAN.md` remains the cognition maturation authority.
- `20_DIALOGUE_AND_EVENT_DRIVEN_AUTONOMY_PLAN.md` remains the authority for unified dialogue/event-driven proactive speech and its existing lease/budget/cooldown mechanisms. fileciteturn4file0
- Perception and recognition plans remain authoritative for model/provider-specific detection behavior.
- Voice plans remain authoritative for audio transport/VAD/TTS mechanics.
- Autonomy/safety plans remain authoritative for physical action authorization.
- Soul/communication documents remain authoritative for Novi's intended communicative character and vocabulary.
- This document defines **how those systems combine into situated social cognition**.

The main implementation principle is therefore:

```text
Do not add another brain.

Connect the existing brain's capabilities into one persistent
multimodal social-cognitive loop.
```

**End state:** Novi does not merely answer because somebody spoke. Novi understands who is present, what is happening, what matters, what has happened before, what is expected next, whether an interaction is appropriate, and then chooses whether and how to speak.