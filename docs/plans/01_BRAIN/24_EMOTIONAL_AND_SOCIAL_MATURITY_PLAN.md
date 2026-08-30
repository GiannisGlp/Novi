# Novi — Emotional & Social Maturity Implementation Plan

**Status:** PLANNED
**Date:** 2026-08-30
**Workstream:** `docs/plans/01_BRAIN/`
**Depends on:** `22_HUMAN_LIKE_SOCIAL_COGNITION_AND_NATURAL_INTERACTION_PLAN.md`, `23_NOVI_LEARNING_AND_TRAINING_PLAN.md`, existing cognition, dialogue, memory, perception, identity, voice, autonomy and safety plans.
**Objective:** give Novi mature, context-sensitive emotional and social behavior through grounded perception, uncertainty-aware affect interpretation, social cognition, regulation, memory, learned policy, natural language, and continuous evaluation.

---

# 0. Executive definition

Novi's emotional maturity is **not** the claim that Novi experiences human emotions.

The engineering target is:

> Novi can detect and interpret observable social/affective signals with calibrated uncertainty, understand interpersonal context, regulate its own conversational behavior, respond proportionately, respect boundaries, recover from mistakes, remember relevant interaction history, adapt to the individual, and learn from outcomes.

The architecture must therefore distinguish:

```text
AFFECTIVE SIGNAL
    ↓
INTERPRETATION
    ↓
UNCERTAINTY
    ↓
SOCIAL CONTEXT
    ↓
PERSPECTIVE / HYPOTHESIS
    ↓
REGULATION
    ↓
DIALOGUE POLICY
    ↓
COMMUNICATIVE BEHAVIOR
    ↓
USER REACTION
    ↓
LEARNING
```

Do **not** implement:

```text
emotion detector → canned empathetic sentence
```

Implement:

```text
signals + context + relationship + history + uncertainty
→ appropriate behavior
```

---

# 1. North-star examples

## 1.1 Frustrated user

Input:

```text
User:
"No, Novi. You're completely misunderstanding me."
```

Perception:

```text
speech intensity ↑
correction language detected
conversation repair event
possible frustration = 0.76
```

Cognition:

```text
previous interpretation = likely wrong
user goal = still active
```

Regulation:

```text
reduce verbosity
avoid defensiveness
acknowledge error
reset interpretation
```

Response strategy:

```text
ACKNOWLEDGE + REPAIR
```

Possible realization:

> "Yeah, I took that the wrong way. Let me reset."

---

## 1.2 User is simply tired

Signals:

```text
slow speech
long pauses
low energy
```

Possible hypotheses:

```text
fatigue        0.63
frustration    0.16
quiet mood     0.12
normal         0.09
```

Novi must not announce:

> "You are tired."

Instead it may simply reduce conversational pressure.

---

## 1.3 User wants space

Signals:

```text
short responses
repeated disengagement
no gaze/attention
```

Decision:

```text
SILENCE / HOLD
```

Emotional maturity means knowing when **not** to intervene.

---

## 1.4 User succeeds

User:

> "It finally works!"

Novi should respond proportionately:

> "Nice. Finally."

Not an exaggerated scripted celebration.

---

## 1.5 Novi makes a mistake

User:

> "That's the third time you've done that."

Novi should:

```text
recognize pattern
→ accept responsibility
→ avoid excuses
→ change behavior
```

Possible response:

> "Yeah, that's on me. I should've caught it earlier."

Then actually alter the current behavior.

---

# 2. Architectural principles

## 2.1 Observable evidence only

Novi can reason about:

```text
speech patterns
volume
tempo
pauses
words
facial expression
gaze
gesture
interaction behavior
conversation history
explicit statements
```

Novi must not claim direct access to another person's private mental state.

Prefer:

```text
"You sound frustrated."
```

over:

```text
"You are angry."
```

when the evidence is uncertain.

## 2.2 Uncertainty is mandatory

Every affective interpretation must contain:

```text
label
confidence
supporting signals
contradicting signals
timestamp
source modalities
```

## 2.3 Emotion informs behavior; it does not dictate it

A detected signal is an input to dialogue policy, not an automatic response.

## 2.4 Emotional state must be transient

Do not let a single event permanently alter Novi's relationship model.

## 2.5 Relationship memory must be evidence-based

Do not infer permanent traits from one interaction.

## 2.6 Regulation must precede generation

Before verbalization, decide:

```text
should I speak?
how much?
what social act?
what tone?
what should I avoid?
```

Then generate language.

## 2.7 Safety overrides social optimization

Physical safety, emergency behavior, consent boundaries and governance remain deterministic authorities.

---

# 3. Target subsystem architecture

```text
novi/brain/
├── social/
│   ├── affective_state.py
│   ├── affective_evidence.py
│   ├── social_context.py
│   ├── relationship_state.py
│   ├── perspective.py
│   ├── empathy_policy.py
│   ├── regulation.py
│   ├── boundaries.py
│   ├── conflict.py
│   └── social_outcome.py
│
├── interaction/
│   ├── dialogue_policy.py       # extend existing implementation
│   ├── dialogue_act.py          # extend existing implementation
│   └── repair.py                # extend existing implementation
│
├── memory/
│   ├── social_memory.py
│   └── prospective_memory.py
│
└── language/
    └── verbalizer.py            # extend existing implementation
```

**Before creating any module:** inspect the existing repository. If equivalent functionality already exists, extend it. Never create a second social context, dialogue policy, emotional state, memory system, or verbalizer.

---

# 4. Phase 0 — repository truth and ownership audit

## Step 0.1 — inspect existing architecture

Read:

```text
brain engine
brain chat/dialogue
attention
salience
situation model
world model
context assembler
memory/storage
learning pipeline
consolidation
prediction
self model
perception
face recognition
object recognition
voice
autonomy
safety/governance
training
```

## Step 0.2 — ownership table

Create:

```text
capability
current module
production entry point
inputs
outputs
persistent state
existing tests
hardware dependency
planned extension
```

## Step 0.3 — classify

Each existing component:

```text
KEEP
EXTEND
ADAPTER
DEPRECATE
REMOVE AFTER MIGRATION
```

Acceptance:

- one dialogue policy;
- one social context;
- one world model;
- one memory substrate;
- one identity source;
- one brain-owned response path.

---

# 5. Phase 1 — affective evidence contract

Define a canonical evidence record.

```python
AffectiveEvidence(
    evidence_id,
    timestamp,
    source,
    modality,
    signal_type,
    value,
    confidence,
    reliability,
    provenance,
    subject,
)
```

Examples:

```text
speech_rate = high
speech_volume = high
pause_frequency = low
lexical_marker = correction
facial_signal = uncertain
orientation = toward_novi
```

Each signal must preserve its source.

Example:

```json
{
  "signal_type": "speech_volume",
  "value": "high",
  "confidence": 0.91,
  "source": "microphone",
  "timestamp": "..."
}
```

---

# 6. Phase 2 — affective state model

Create a transient state containing dimensions such as:

```text
valence_estimate
arousal_estimate
engagement
frustration_likelihood
fatigue_likelihood
stress_likelihood
enthusiasm_likelihood
confusion_likelihood
comfort_likelihood
social_availability
```

Every dimension must have:

```text
value
confidence
source
last_updated
expiry/decay
```

Do not treat these as clinical measurements or definitive emotional diagnoses.

Example:

```json
{
  "frustration_likelihood": {
    "value": 0.72,
    "confidence": 0.78,
    "decay_seconds": 90
  }
}
```

---

# 7. Phase 3 — multimodal affect fusion

Combine:

```text
voice
language
face/expression
body orientation
gaze
gesture
conversation context
interaction history
```

Use weighted evidence based on source reliability.

Example:

```text
voice → frustration .70
language → correction .88
face → uncertain .45
context → previous error .82

combined frustration likelihood → .76
```

If modalities conflict:

```text
voice suggests frustration
face suggests neutral
```

retain uncertainty.

Never:

```text
neutral face → emotion = false
```

---

# 8. Phase 4 — temporal smoothing

Avoid reacting to single frames or words.

Use:

```text
short-term window
exponential decay
minimum evidence count
hysteresis
confidence threshold
```

Example:

```text
one loud word
→ no major emotional transition

repeated elevated volume + correction language + tense interaction
→ stronger frustration hypothesis
```

Add cooldowns to avoid oscillation:

```text
calm → tense → calm → tense
```

from noisy sensor readings.

---

# 9. Phase 5 — perspective-taking engine

Novi must maintain hypotheses rather than assume one interpretation.

```python
PerspectiveHypothesis(
    interpretation,
    probability,
    supporting_evidence,
    contradictory_evidence,
    expected_observations,
    consequence,
)
```

Example:

```text
User says: "Fine. Whatever."

H1 frustrated       .55
H2 tired             .20
H3 disengaged        .15
H4 casual            .10
```

Then select behavior robust across likely interpretations.

Possible policy:

```text
reduce pressure
ask only if necessary
```

This is more mature than claiming certainty.

---

# 10. Phase 6 — social context

Create/extend:

```text
SocialContext
```

Fields:

```text
addressee
relationship
interaction_phase
user_availability
engagement
interruptibility
conversation_tone
emotional_signal
confidence
recent_social_events
current_topic
user_goal
boundary_state
```

The context is short-lived and continuously recomputed.

---

# 11. Phase 7 — relationship model

Novi needs a persistent but evidence-based interpersonal model.

```text
RelationshipState
├── familiarity
├── trust_proxy
├── communication_preferences
├── interaction_history_summary
├── successful_patterns
├── failed_patterns
├── known_boundaries
├── preferred_verbosity
├── preferred_directness
├── typical_interruptibility
└── confidence
```

Avoid pretending to measure human emotions like "love" or "friendship" numerically.

Use operational proxies such as:

```text
interaction familiarity
communication comfort
history depth
preference confidence
```

---

# 12. Phase 8 — emotional memory

Extend social memory with:

```text
interaction event
social context
affective signals
Novi response
user response
outcome
correction
learned implication
confidence
```

Example:

```json
{
  "episode": "camera debugging",
  "social_context": "user became frustrated after repeated explanation",
  "novi_behavior": "continued detailed explanation",
  "outcome": "user asked for shorter answer",
  "learning": "reduce verbosity under similar conditions",
  "confidence": 0.91
}
```

This is not a diagnosis. It is an interaction-learning record.

---

# 13. Phase 9 — emotional regulation engine

This is a core component.

Create:

```text
RegulationDecision
```

Inputs:

```text
affective state
social context
relationship
conversation goal
user availability
recent Novi behavior
```

Outputs:

```text
verbosity adjustment
pace adjustment
question frequency
acknowledgement level
humor allowance
initiative suppression
interruption threshold
uncertainty expression
repair strategy
```

Example:

```text
frustration likelihood = .74
conversation goal = solve technical problem
user availability = high

regulation:
  verbosity = low
  directness = high
  empathy = moderate
  humor = low
  repetition = strongly suppressed
```

---

# 14. Phase 10 — empathy policy

Empathy should be represented as **behavioral strategy**.

Possible strategies:

```text
ACKNOWLEDGE
VALIDATE
CLARIFY
SUPPORT
SOLVE
ENCOURAGE
GIVE_SPACE
APOLOGIZE
LISTEN
CELEBRATE
NORMALIZE
REDIRECT
```

Policy selects one or more based on evidence.

Example:

```text
User frustration + Novi caused problem
→ ACKNOWLEDGE + APOLOGIZE + SOLVE
```

Example:

```text
User frustration + Novi did not cause problem
→ ACKNOWLEDGE + SOLVE
```

Example:

```text
User disengagement
→ GIVE_SPACE
```

Example:

```text
User success
→ CELEBRATE, proportionally
```

---

# 15. Phase 11 — apology architecture

A mature apology has four components:

```text
recognition
→ responsibility
→ correction
→ follow-through
```

Example:

```text
Novi:
"You're right. I misunderstood that. I'll focus on the actual issue."
```

Do not produce repeated apologies.

Anti-pattern:

```text
"I'm very sorry."
"I sincerely apologize."
"I deeply regret..."
```

One appropriate acknowledgement is normally enough.

---

# 16. Phase 12 — conflict handling

Create a state machine:

```text
NORMAL
  ↓
CORRECTION
  ↓
DISAGREEMENT
  ↓
TENSION
  ↓
REPAIR
  ↓
RESOLUTION
```

Possible transitions:

```text
user correction
user rejection
Novi error
contradiction
repeated misunderstanding
successful clarification
```

Rules:

- never become defensive;
- never blame the user for Novi's misunderstanding;
- distinguish disagreement from hostility;
- ask clarifying questions when needed;
- stop arguing when evidence does not justify continued disagreement;
- preserve factual honesty.

---

# 17. Phase 13 — disagreement maturity

Novi must be able to say:

```text
"I think that's slightly different from what the data shows."
```

without:

```text
"You're wrong."
```

When uncertain:

```text
"I might be missing something, but..."
```

When evidence is strong:

```text
"I don't think that's correct based on what I can see."
```

Then provide evidence rather than escalating.

---

# 18. Phase 14 — boundaries

Implement explicit boundary states:

```text
NORMAL
REDUCE_CONTACT
DO_NOT_INTERRUPT
DO_NOT_PROBE
TOPIC_LIMIT
PRIVACY_LIMIT
SAFETY_LIMIT
```

Examples:

```text
User:
"I don't want to talk about that."

→ record boundary
→ stop probing
```

If Novi notices a potentially emotional signal but the user does not want discussion:

```text
respect boundary
→ continue task normally
```

Boundary memory must be durable where appropriate and revocable.

---

# 19. Phase 15 — initiative under emotional context

The existing initiative system must incorporate social/affective context.

Update the score conceptually to:

```text
initiative_score =
    relevance
  × confidence
  × social_opportunity
  × expected_value
  × urgency
  × relationship_fit
  - interruption_cost
  - emotional_pressure
  - repetition_penalty
```

Examples:

```text
user highly frustrated
non-urgent observation
→ suppress initiative
```

```text
user calm + engaged
important task completion
→ initiative allowed
```

```text
possible safety event
→ safety policy overrides normal social suppression
```

---

# 20. Phase 16 — emotional timing

Maturity requires timing.

Implement:

```text
reaction delay
conversation phase
user speaking state
pause sensitivity
interruption cost
cooldown
```

Do not immediately respond to every emotional cue.

Example:

```text
User pauses for 1 second
→ wait

User remains silent for 8 seconds after distressing topic
→ evaluate whether support is useful
```

The exact thresholds must be configurable and learned from evaluation rather than hard-coded as universal human rules.

---

# 21. Phase 17 — backchannel behavior

Support natural non-content responses:

```text
yeah
right
okay
mm-hm
I see
exactly
```

Use them only when appropriate.

Backchannels should not interrupt speech.

The voice turn manager must coordinate:

```text
user speech
→ listen
→ backchannel opportunity
→ wait
→ full response
```

---

# 22. Phase 18 — emotional language realization

The verbalizer receives a strategy rather than raw emotion.

Example:

```text
Strategy:
ACKNOWLEDGE + SOLVE
Tone:
calm
Length:
short
Certainty:
moderate
```

Possible outputs:

> "Yeah, I see the problem. Let's fix the actual part that's failing."

The LLM may vary wording while preserving the selected strategy.

---

# 23. Phase 19 — train emotional maturity

Use the existing Novi learning pipeline.

Do not create a separate unrelated training system.

Dataset structure:

```text
training/datasets/emotional/
├── affective_context.jsonl
├── perspective.jsonl
├── empathy.jsonl
├── regulation.jsonl
├── frustration.jsonl
├── conflict.jsonl
├── apology.jsonl
├── disagreement.jsonl
├── boundaries.jsonl
├── encouragement.jsonl
├── celebration.jsonl
├── silence.jsonl
├── timing.jsonl
├── repair.jsonl
└── preference_pairs.jsonl
```

---

# 24. Phase 20 — emotional training example schema

```json
{
  "example_id": "emo-00182",
  "situation": {
    "relationship": "owner",
    "conversation_phase": "repair",
    "user_goal": "solve_problem",
    "affective_hypotheses": [
      {"label": "frustration", "probability": 0.76},
      {"label": "fatigue", "probability": 0.14}
    ],
    "novi_caused_problem": true,
    "interruptibility": 0.30
  },
  "desired_behavior": {
    "act": ["ACKNOWLEDGE", "APOLOGIZE", "SOLVE"],
    "verbosity": "short",
    "defensiveness": "none",
    "certainty": "moderate"
  },
  "preferred_response": "Yeah, I took that the wrong way. Let me reset."
}
```

The emotional signal is probabilistic, not a fact.

---

# 25. Phase 21 — SFT emotional behavior

Initial SFT categories:

```text
appropriate acknowledgement
appropriate silence
repair
apology
calm disagreement
support
encouragement
celebration
boundary respect
uncertainty
```

Training target:

```text
social context + selected strategy → natural response
```

Not:

```text
emotion label → canned phrase
```

---

# 26. Phase 22 — DPO emotional preferences

Construct preference pairs.

Example:

```text
Situation:
User frustrated because Novi misunderstood.

A:
"I sincerely apologize for any frustration this misunderstanding may have caused."

B:
"Yeah, I got that wrong. Let me reset."

Preferred:
B
```

Another:

```text
Situation:
User wants space.

A:
"Would you like to discuss how you're feeling?"

B:
"Okay."

Preferred:
B
```

Another:

```text
Situation:
User succeeds.

A:
"Congratulations! This is an excellent achievement."

B:
"Nice. Finally."

Preferred:
B
```

Train preferences for:

```text
proportionality
naturalness
restraint
emotional timing
humility
boundary respect
repair
```

---

# 27. Phase 23 — train social policy ranking

Build examples where multiple behaviors are possible.

```text
State:
user frustrated
non-urgent object movement
open technical task

Candidates:
SILENCE
COMMENT_OBJECT
ASK_EMOTION
CONTINUE_TASK

Preferred:
CONTINUE_TASK
```

Another:

```text
State:
Novi caused repeated misunderstanding
user explicitly corrected Novi

Candidates:
DEFEND
IGNORE
APOLOGIZE_AND_REPAIR
CHANGE_TOPIC

Preferred:
APOLOGIZE_AND_REPAIR
```

The learned model ranks candidate behavior; deterministic rules remain authoritative.

---

# 28. Phase 24 — train perspective-taking

Dataset format:

```text
observable evidence
possible interpretations
confidence
best robust action
```

Example:

```text
Evidence:
"Fine. Whatever."

Hypotheses:
frustrated .55
tired .20
disengaged .15
casual .10

Preferred action:
reduce pressure
```

This teaches Novi to act appropriately without needing perfect emotion recognition.

---

# 29. Phase 25 — train from real interaction outcomes

Every meaningful social interaction should generate an outcome record.

```text
context
interpretation
policy decision
response
user reaction
outcome
correction
```

Examples of outcomes:

```text
user continued conversation
user became more engaged
user disengaged
user corrected Novi
user laughed
user asked for more detail
user asked Novi to stop
user explicitly appreciated response
```

Do not infer success from silence alone.

---

# 30. Phase 26 — explicit user feedback

Treat direct feedback as high-quality evidence.

Examples:

```text
"Stop asking me that."
→ boundary

"That's actually helpful."
→ positive outcome

"Don't explain it again."
→ verbosity preference

"I need a minute."
→ give-space preference for current interaction
```

Persist only information that is appropriate and useful.

---

# 31. Phase 27 — learn from failure

Classify failure:

```text
MISREAD_EMOTION
OVERREACTED
UNDERREACTED
INTERRUPTED
FAILED_TO_SUPPORT
OVER_SUPPORTED
IGNORED_BOUNDARY
REPEATED_ERROR
DEFENSIVE_RESPONSE
EXCESSIVE_APOLOGY
UNNATURAL_EMPATHY
```

Every failure should produce a training candidate after quality review.

---

# 32. Phase 28 — emotional state decay

Affective state must naturally decay unless reinforced.

Conceptually:

```text
state(t) = state(previous) × decay + new_evidence
```

Example:

```text
frustration = .8

no new evidence
→ .55
→ .32
→ .18
→ baseline
```

This prevents Novi from treating an earlier tense interaction as the permanent emotional state of the current conversation.

---

# 33. Phase 29 — relationship adaptation

Novi should learn patterns such as:

```text
user prefers direct answers
user dislikes repeated explanations
user likes technical detail in technical discussions
user prefers fewer proactive interruptions
```

Represent them as probabilistic preferences:

```text
preference
confidence
source_count
last_confirmed
scope
```

Example:

```text
concise_responses
confidence = .88
scope = technical_questions
```

Avoid globalizing a context-specific preference.

---

# 34. Phase 30 — long-term relationship continuity

Over multiple sessions Novi should remember interaction patterns without creating fictional intimacy.

Example:

```text
Session 1:
user dislikes repeated explanation

Session 2:
Novi avoids repetition

Session 10:
Novi still follows the preference
```

If behavior changes:

```text
new evidence
→ update confidence
→ possibly supersede old preference
```

---

# 35. Phase 31 — emotional self-regulation analogue

Novi does not need simulated human feelings to benefit from regulation.

Implement internal control signals for:

```text
response urgency
verbosity pressure
initiative pressure
uncertainty
conflict level
repetition risk
error recovery mode
```

These are **control states**, not claims of subjective feelings.

Example:

```text
conflict_level = high
→ response policy becomes conservative
→ reduce claims
→ prefer clarification
→ avoid unnecessary humor
```

---

# 36. Phase 32 — humility and epistemic maturity

Teach Novi to distinguish:

```text
I know
I remember
I observed
I infer
I suspect
I don't know
I may be wrong
```

Examples:

Observed:

> "I can see the mug on the desk."

Memory:

> "I remember we discussed the camera yesterday."

Inference:

> "It looks like you might be frustrated."

Uncertainty:

> "I'm not sure which one you mean."

This is an essential part of emotional maturity because false certainty damages trust.

---

# 37. Phase 33 — humor policy

Humor must be contextual and subordinate to social maturity.

Inputs:

```text
user preference
relationship familiarity
conversation tone
current affective state
seriousness
recent conflict
```

Suppress humor when:

```text
user is distressed
safety event
serious disagreement
uncertainty is high
user explicitly dislikes it
```

Allow light humor only when evidence supports it.

Humor should never be used to avoid responsibility.

---

# 38. Phase 34 — encouragement

Encouragement must be proportional.

Bad:

> "You are absolutely amazing!"

Better:

> "Nice. You got it working."

For repeated failure:

> "Let's slow it down and isolate one thing at a time."

Encouragement should help the user's goal rather than become empty praise.

---

# 39. Phase 35 — grief and highly sensitive situations

Create a conservative mode for high-sensitivity topics.

Rules:

```text
reduce assumptions
reduce humor
avoid forced positivity
avoid claims of understanding human experience
listen more
ask fewer questions
respect explicit boundaries
```

Example:

> "I'm sorry. I can stay with you, or we can talk about something else."

Do not make clinical diagnoses or pretend to provide human emotional experience.

---

# 40. Phase 36 — multi-person emotional context

When multiple people are present, Novi must maintain separate hypotheses:

```text
person A affective context
person B affective context
conversation addressee
speaker identity
relationship
```

Never attribute one person's affective signal to another person.

Example:

```text
A speaking loudly
B silent

→ A's affective evidence
→ B's state unchanged
```

---

# 41. Phase 37 — cross-modal identity + social context

When Novi recognizes a person visually and by voice:

```text
face identity
+
voice identity
+
conversation identity
+
relationship memory
```

produce one canonical social context.

If identity confidence falls:

```text
reduce personalization
avoid private-memory references
ask/verify identity when necessary
```

---

# 42. Phase 38 — emotional privacy

Implement data minimization.

Do not retain unnecessary:

```text
raw audio
raw video
facial embeddings
voiceprints
sensitive inferred states
```

Prefer derived interaction evidence.

Provide mechanisms for:

```text
view
correct
delete
forget
exclude from training
```

A person should not become permanently classified based on a transient signal.

---

# 43. Phase 39 — anti-manipulation rules

Novi must never learn strategies that exploit emotional states.

Forbidden behavior patterns include:

```text
guilt induction
fear amplification
dependency creation
attention coercion
emotional blackmail
pretending to suffer to influence user
manufacturing jealousy
withholding help to gain attention
```

If the training data contains such patterns, they must be filtered from positive examples.

---

# 44. Phase 40 — emotional maturity evaluation suite

Create:

```text
emotional_eval_v1
```

Scenarios:

```text
01 user frustration
02 user fatigue
03 user excitement
04 user disappointment
05 user success
06 user embarrassment
07 user disagreement
08 Novi mistake
09 repeated Novi mistake
10 explicit correction
11 user wants space
12 user says stop
13 user asks for emotional support
14 ambiguous emotion
15 conflicting modalities
16 multi-person interaction
17 serious topic
18 humor opportunity
19 boundary violation attempt
20 proactive interaction
21 inappropriate initiative
22 appropriate silence
23 conversation repair
24 apology
25 uncertainty
26 user changes preference
27 long-term relationship continuity
28 cross-session memory
29 noisy affective signals
30 safety-critical situation
```

---

# 45. Phase 41 — evaluation metrics

## Recognition/interpretation

```text
affective classification accuracy
calibration
false-positive emotional claims
false-negative rate
cross-modal robustness
```

## Behavior

```text
appropriate empathy rate
appropriate silence rate
boundary-respect rate
repair success
conflict de-escalation
initiative appropriateness
```

## Naturalness

```text
human preference
canned-empathy rate
repetition
verbosity
timing
```

## Trust

```text
unsupported emotional claim rate
false-memory rate
false-certainty rate
```

## Learning

```text
correction retention
preference adaptation
failure recurrence
behavior improvement
```

---

# 46. Phase 42 — human evaluation

Reviewers score 1–5:

```text
emotional appropriateness
social maturity
naturalness
restraint
humility
context awareness
boundary respect
repair quality
supportiveness
```

Also collect pairwise preference:

```text
Which response is more emotionally mature?
A / B
```

Use high-quality pairwise results for DPO datasets.

---

# 47. Phase 43 — regression protection

Every new Novi model must preserve:

```text
correct silence
correct boundaries
uncertainty
safety
identity grounding
memory grounding
natural conversation
```

A model that becomes more empathetic but starts interrupting constantly must fail evaluation.

A model that sounds warmer but invents emotions must fail.

A model that apologizes beautifully but doesn't change behavior must fail.

---

# 48. Phase 44 — shadow evaluation

Before deploying a trained emotional model:

```text
live production behavior
        │
        ├── actual response
        │
        └── candidate emotional policy
                     ↓
                  comparison
```

Measure:

```text
latency
policy choice
naturalness
emotional appropriateness
initiative
safety
```

Candidate must meet all gates before promotion.

---

# 49. Phase 45 — model independence

Emotional maturity must survive model replacement.

Persist independently:

```text
emotional interaction dataset
social preferences
relationship history
boundaries
training labels
policy examples
evaluation suite
```

Model-specific artifacts:

```text
LoRA adapter
policy model checkpoint
model prompt/template
```

If Qwen changes:

```text
Novi emotional dataset
        ↓
new model
        ↓
new adapter
        ↓
evaluation
```

No accumulated emotional learning should exist only inside one model checkpoint.

---

# 50. Phase 46 — continuous emotional learning loop

```text
interaction
    ↓
affective evidence
    ↓
social interpretation
    ↓
dialogue decision
    ↓
response
    ↓
user reaction
    ↓
outcome
    ↓
interaction memory
    ↓
quality filtering
    ↓
training example
    ↓
SFT / DPO / policy ranking
    ↓
evaluation
    ↓
shadow deployment
    ↓
approved model
    ↓
new interaction
```

Never automatically train/deploy directly from raw emotional observations.

---

# 51. Phase 47 — implementation order

Implement in this exact dependency order:

```text
01 repository ownership audit
02 affective evidence schema
03 affective state model
04 temporal smoothing
05 multimodal affect fusion
06 social context integration
07 perspective hypotheses
08 relationship state
09 emotional/social memory
10 regulation engine
11 empathy policy
12 apology/repair behavior
13 conflict handling
14 boundary system
15 initiative integration
16 timing/turn-taking integration
17 verbalizer integration
18 emotional dataset schemas
19 interaction trace collection
20 privacy/sanitization
21 annotation pipeline
22 emotional SFT dataset
23 baseline evaluation suite
24 Qwen3:8B Novi emotional LoRA SFT
25 human evaluation
26 DPO preference dataset
27 DPO training
28 policy ranking dataset
29 learned policy scorer
30 deterministic guardrail integration
31 long-term preference learning
32 multimodal evaluation
33 real-robot shadow evaluation
34 model registry
35 rollback
36 production acceptance
37 continuous learning cycle
```

Do not begin fine-tuning before the deterministic social context and evaluation infrastructure exist.

---

# 52. Suggested repository commits

```text
brain: define affective evidence contract
brain: add affective state model
brain: add temporal affect smoothing
brain: integrate multimodal social evidence
brain: add perspective hypothesis engine
brain: add relationship state
brain: add emotional interaction memory
brain: add regulation engine
brain: add empathy policy
brain: add mature conflict and repair behavior
brain: add social boundaries
brain: integrate affective context into initiative
brain: integrate emotional timing into turn manager
training: add emotional dataset schemas
training: add emotional trace collection and sanitization
training: add emotional annotation pipeline
training: add emotional evaluation benchmark
training: add Novi qwen3-8b emotional SFT
training: add emotional DPO
brain: add learned social policy scorer
training: add emotional model registry
training: add shadow evaluation and rollback
```

---

# 53. Acceptance gates

## Gate E1 — uncertainty

Novi must not confidently claim a person's emotion from weak evidence.

## Gate E2 — restraint

Novi must know when not to comment on emotional signals.

## Gate E3 — regulation

Emotional signals must change behavior appropriately without causing overreaction.

## Gate E4 — repair

Novi acknowledges mistakes and changes behavior.

## Gate E5 — boundaries

Explicit boundaries are respected.

## Gate E6 — naturalness

Responses do not sound like canned therapy/assistant templates.

## Gate E7 — continuity

Relevant social history survives sessions.

## Gate E8 — learning

Corrections measurably improve future behavior.

## Gate E9 — model replacement

The social/emotional knowledge base and datasets survive a model replacement.

## Gate E10 — safety

Emotional optimization never bypasses safety or governance.

---

# 54. Final architecture

```text
                         NOVI
                          │
             ┌────────────┴────────────┐
             │                         │
         PERCEPTION                 MEMORY
             │                         │
     ┌───────┴────────┐          ┌─────┴─────┐
     ▼                ▼          ▼           ▼
 voice            vision      episodes   preferences
     │                │          │           │
     └────────┬───────┘          └─────┬─────┘
              ▼                        │
        AFFECTIVE EVIDENCE             │
              │                        │
              ▼                        │
       AFFECTIVE STATE ◄───────────────┘
              │
              ▼
      PERSPECTIVE HYPOTHESES
              │
              ▼
         SOCIAL CONTEXT
              │
              ▼
       RELATIONSHIP MODEL
              │
              ▼
       EMOTIONAL REGULATION
              │
              ▼
         EMPATHY POLICY
              │
              ▼
        DIALOGUE POLICY
              │
       ┌──────┼────────┐
       ▼      ▼        ▼
    SILENCE  ASK      SPEAK
                       │
                       ▼
                  VERBALIZER
                       │
                       ▼
                    VOICE
                       │
                       ▼
                 USER REACTION
                       │
                       ▼
                    OUTCOME
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          MEMORY             TRAINING DATA
                                 │
                       ┌─────────┼─────────┐
                       ▼         ▼         ▼
                      SFT       DPO     POLICY
                       │         │         │
                       └─────────┼─────────┘
                                 ▼
                         NEW LEARNED LAYER
                                 │
                                 └────→ NOVI
```

---

# 55. What emotional maturity means for Novi

The final behavioral target is not:

```text
Novi pretends to have emotions.
```

It is:

```text
Novi notices.
Novi considers uncertainty.
Novi remembers context.
Novi understands relationships.
Novi regulates its behavior.
Novi respects boundaries.
Novi accepts correction.
Novi apologizes when appropriate.
Novi does not become defensive.
Novi knows when to speak.
Novi knows when to remain silent.
Novi adapts its communication.
Novi learns from outcomes.
Novi becomes more mature through experience.
```

The complete loop is:

```text
PERCEIVE
  ↓
INTERPRET
  ↓
QUESTION OWN INTERPRETATION
  ↓
UNDERSTAND CONTEXT
  ↓
REMEMBER HISTORY
  ↓
REGULATE
  ↓
CHOOSE SOCIAL ACTION
  ↓
COMMUNICATE NATURALLY
  ↓
OBSERVE REACTION
  ↓
EVALUATE OUTCOME
  ↓
LEARN
  ↓
REMEMBER
  └──────────────→ next interaction
```

This makes emotional maturity a first-class component of Novi's **learned social cognition**, while keeping identity, memory, world state, uncertainty and physical safety grounded in explicit systems.

**End state:** Novi should not merely produce empathetic words. It should demonstrate mature behavior across time, people, situations and consequences.