# Novi — Conversational Intelligence, Context, and Real-World Acceptance Plan

**Status:** Implementation-ready
**Priority:** P0/P1 — intelligence quality
**Scope:** Mac Brain conversation quality, context tracking, intent/referent resolution, memory/world retrieval, response planning, response verification, model routing, training/evaluation, real-device testing, long-session testing, and acceptance evidence.
**Primary objective:** Make Novi consistently understand what the user means, preserve conversational context, retrieve the right memories and world facts, choose an appropriate response strategy, and produce natural, useful, grounded answers. The plan deliberately prioritizes **real end-to-end behavior over unit-test volume**.

---

## 1. Executive Summary

Novi has accumulated a substantial cognitive substrate: persistent memory, knowledge, world state, identity, perception, emotion/social cognition, learning, planning, model routing, trained dialogue/emotional adapters, and a source-agnostic BrainDriver. The current problem is therefore not simply lack of capability.

The observed quality problem is that the components do not yet guarantee that the correct internal state is selected and composed for every conversational turn. This produces responses that can be technically grammatical while still feeling unintelligent, out of context, generic, emotionally inappropriate, repetitive, or disconnected from what was just discussed.

The central architectural change in this plan is to make conversation a first-class cognitive process:

```text
User input
  ↓
Input normalization
  ↓
Intent + dialogue-act understanding
  ↓
Referent/entity resolution
  ↓
Conversation-state update
  ↓
Relevant memory retrieval
  ↓
Relevant world-state retrieval
  ↓
Social/emotional context
  ↓
Context composition
  ↓
Response goal + strategy
  ↓
Reasoning/model routing
  ↓
Draft response
  ↓
Response critic / verifier
  ↓
Repair if needed
  ↓
Final response
  ↓
Memory/learning update
```

The LLM should not be required to reconstruct the entire brain from raw conversation text on every turn. Novi should first construct a compact, explicit cognitive state and then use the LLM primarily for reasoning and natural-language realization.

This plan intentionally changes the project validation philosophy:

> **Real conversations, real Mac runtime, real models, real camera/voice where applicable, real memory, real restarts, and long sessions are the primary acceptance evidence. Unit tests remain useful for preventing regressions, but they are no longer the primary proof of intelligence quality.**

---

# 2. Current Assets to Reuse

The repository already contains important foundations that must not be duplicated:

- `novi/brain/dialogue.py` — dialogue behavior and response safeguards.
- `novi/brain/trained_reply.py` — trained dialogue/emotional response transport and bounded conversation prompt construction.
- `novi/brain/models/conversation_summarizer.py` — conversation summarization.
- `novi/brain/social_context.py` — social context derived from perception, person model, and conversation state.
- `novi/brain/regulation.py` — affective/social/conversation-goal behavior adjustments.
- `novi/brain/skill_activation.py` — skill relevance selection around Novi responses.
- memory/knowledge storage and retrieval infrastructure.
- identity and recognition infrastructure.
- world-state and situation-model infrastructure.
- learning/training pipeline and dialogue/emotional datasets.
- existing Mac evidence under `docs/plans/EVIDENCE/mac/`.
- existing scenario catalog under `docs/specs/brain/29_SCENARIO_CATALOG.md`.
- existing architecture and acceptance-gate definitions.

Do not replace these blindly. First map each capability into the new conversation pipeline and remove duplication only after behavior is preserved.

---

# 3. Problem Definition

Novi currently exhibits several classes of poor behavior:

1. **Out-of-context answers** — response addresses an older topic, wrong entity, or generic interpretation instead of the current turn.
2. **Wrong referent** — pronouns or implicit references such as `it`, `that`, `she`, `there`, `the car`, or `the other one` resolve incorrectly.
3. **Intent failure** — Novi answers the literal words but misses the user's actual communicative goal.
4. **Memory misuse** — a relevant memory is omitted, an irrelevant memory is inserted, or uncertain memory is presented as fact.
5. **World-state mismatch** — Novi answers without using current perception/environmental state when the question depends on it.
6. **Conversation reset behavior** — Novi behaves as if every turn is independent.
7. **Over-questioning** — Novi asks a clarification question when the intended meaning is sufficiently clear.
8. **Under-questioning** — Novi confidently chooses an interpretation when ambiguity is material.
9. **Generic responses** — safe-sounding but unhelpful replies such as `That sounds interesting`, `I understand`, or `Tell me more` when a direct answer is possible.
10. **Repetition** — Novi repeats facts, explanations, greetings, or emotional language unnecessarily.
11. **Emotional mismatch** — wording does not fit the user's emotional state or the relationship/context.
12. **Model overreach** — the LLM invents memories, capabilities, observations, or conclusions.
13. **Poor response strategy** — Novi has the correct facts but chooses the wrong communicative act.
14. **Long-context degradation** — quality falls as a conversation becomes longer.
15. **Cross-modal disconnect** — Novi sees/hears something but the conversational response does not use it when relevant.
16. **Failure after restart** — durable memory exists but conversation context or identity links are not restored correctly.
17. **Model-specific behavior** — switching Qwen/Ollama models changes behavior unexpectedly because cognitive instructions are insufficiently structured.
18. **Training mismatch** — trained dialogue/emotional adapters improve style but do not reliably improve context resolution or reasoning.

---

# 4. Success Definition

Novi should feel intelligent because it reliably demonstrates these behaviors in real interaction:

- understands the current topic;
- remembers what was just said;
- resolves references naturally;
- knows when the user changed topic;
- retrieves useful older memories without dumping irrelevant history;
- distinguishes facts from beliefs and uncertainty;
- uses live perception when relevant;
- maintains emotional/social continuity;
- answers directly when it can;
- asks clarification only when necessary;
- admits uncertainty when necessary;
- does not invent memories or observations;
- does not contradict established context without explanation;
- does not repeat itself unnecessarily;
- can recover after misunderstandings;
- can learn from explicit corrections;
- remains coherent over long conversations;
- preserves identity and relationship continuity;
- can use the same reasoning/context system across chat, voice, and multimodal interaction.

The target is not that every response is perfect. The target is that poor responses become uncommon, diagnosable, and recoverable.

---

# 5. Phase 0 — Establish the Real-Conversation Baseline

## Step 0.1 — Stop optimizing from isolated examples

Collect a baseline corpus from actual Novi usage before changing behavior.

Target initially:

- at least 100 real conversations;
- at least 500 individual turns;
- at least 100 known-bad responses if possible;
- at least 50 long conversations of 20+ turns;
- at least 20 conversations containing topic changes;
- at least 20 conversations involving memory;
- at least 20 conversations involving ambiguity;
- at least 20 conversations involving emotional/social context;
- at least 20 multimodal conversations once camera/voice is available.

Do not manufacture every example. Real failures are more valuable because they expose the actual distribution of problems.

## Step 0.2 — Capture complete interaction records

For each turn capture, with privacy controls:

```text
conversation_id
turn_id
timestamp
input modality
raw user input where permitted
normalized input
conversation state before turn
retrieved memories
retrieved world facts
identity context
social/emotional context
selected intent
selected referents
response strategy
model/provider
model configuration
response
response verification
memory updates
user correction if any
```

## Step 0.3 — Classify every failure

Use these categories:

```text
OUT_OF_CONTEXT
WRONG_TOPIC
WRONG_REFERENT
INTENT_MISUNDERSTOOD
DIALOGUE_ACT_WRONG
MEMORY_MISSED
MEMORY_IRRELEVANT
MEMORY_HALLUCINATED
WORLD_STATE_IGNORED
PERCEPTION_IGNORED
EMOTION_MISMATCH
SOCIAL_MISMATCH
TOO_GENERIC
TOO_VERBOSE
TOO_SHORT
REPETITIVE
UNNECESSARY_CLARIFICATION
MISSING_CLARIFICATION
CONTRADICTION
HALLUCINATION
FALSE_CAPABILITY
BAD_TONE
BAD_TIMING
FAILURE_TO_LEARN
FAILURE_TO_RECOVER
MODEL_ROUTING_ERROR
```

A response can have multiple labels.

## Step 0.4 — Record the expected behavior

For every bad response create a corrected interpretation and ideal response.

Example:

```json
{
  "input": "What about the range?",
  "active_topic": "Tesla Model Y purchase",
  "resolved_entity": "Tesla Model Y",
  "intent": "ASK_ATTRIBUTE",
  "attribute": "range",
  "bad_response": "Range can refer to many things...",
  "ideal_behavior": "Answer about Model Y range, with appropriate caveat about variant/conditions."
}
```

This dataset becomes the main improvement loop.

---

# 6. Phase 1 — Build the Conversation State

Create a first-class conversation state rather than relying only on raw message history.

Recommended conceptual location:

```text
novi/brain/conversation/
```

Initial modules:

```text
conversation_state.py
intent.py
referent_resolution.py
context_manager.py
memory_selector.py
response_planner.py
response_critic.py
conversation_trace.py
conversation_benchmark.py
```

## Step 1.1 — Define `ConversationState`

Minimum state:

```text
topic
subtopics
active_entities
active_people
active_locations
active_time_context
user_goal
current_intent
current_dialogue_act
open_questions
pending_clarifications
last_user_claim
last_novi_claim
last_novi_question
last_unresolved_item
conversation_phase
recent_turns
conversation_summary
confidence
```

## Step 1.2 — Define conversation anchors

Maintain a compact active anchor:

```text
ConversationAnchor
- topic
- active entity
- active person
- active place
- active task
- user goal
- open question
- unresolved reference
- recent decision
- recent correction
- emotional context
```

The anchor must be updated every turn.

## Step 1.3 — Detect topic continuity

For every new message classify:

```text
CONTINUE_CURRENT_TOPIC
SUBTOPIC_CHANGE
NEW_TOPIC
RETURN_TO_PREVIOUS_TOPIC
AMBIGUOUS
```

Do not reset the entire conversation on every topic transition.

## Step 1.4 — Detect implicit continuation

Support messages such as:

```text
"What about the range?"
"And the price?"
"Would you buy it?"
"Is that expensive?"
"What if I got the AWD one?"
"Would that work for me?"
```

The state must supply the missing subject.

## Step 1.5 — Track unresolved questions

When Novi asks:

> What model are you considering?

and the user answers:

> The Model Y.

The state should explicitly close the open slot rather than treating the answer as unrelated text.

---

# 7. Phase 2 — Intent and Dialogue-Act Understanding

## Step 2.1 — Separate intent from wording

Classify what the user is trying to accomplish.

Initial intent taxonomy:

```text
INFORMATION_REQUEST
EXPLANATION_REQUEST
OPINION_REQUEST
COMPARISON
RECOMMENDATION
MEMORY_QUERY
MEMORY_UPDATE
CORRECTION
CONFIRMATION
DISCONFIRMATION
FOLLOW_UP
CLARIFICATION
EMOTIONAL_SUPPORT
REASSURANCE
GREETING
FAREWELL
SOCIAL_CHAT
JOKE/HUMOR
REFLECTION
PLANNING
TASK_REQUEST
OBSERVATION_QUERY
PERCEPTION_QUERY
IDENTITY_QUERY
CAPABILITY_QUERY
FEEDBACK
DISAGREEMENT
AGREEMENT
TOPIC_CHANGE
```

## Step 2.2 — Add dialogue-act classification

Intent and dialogue act are different.

Examples:

```text
"You remember my trip?"
intent = MEMORY_QUERY
act = QUESTION

"I told you yesterday that I hate flying."
intent = MEMORY_UPDATE / CORRECTION
act = ASSERTION

"That sounds awful."
intent = EMOTIONAL_SUPPORT_CONTEXT
act = EMPATHIC_RESPONSE_TRIGGER
```

## Step 2.3 — Confidence and escalation

Every interpretation receives confidence.

Example policy:

```text
>= 0.85 → proceed normally
0.60–0.84 → proceed with cautious context handling
< 0.60 → ask concise clarification if ambiguity affects answer
```

Thresholds must be calibrated from real conversations rather than assumed permanently.

---

# 8. Phase 3 — Referential and Entity Resolution

This phase should directly attack out-of-context behavior.

## Step 3.1 — Resolve pronouns

Support:

```text
it
that
this
they
he
she
there
here
then
one
another
both
the other one
```

## Step 3.2 — Resolve noun phrases

Examples:

```text
"the car"
"the larger model"
"that restaurant"
"my wife"
"the one we discussed"
```

Use active entities, identity, recent mentions, memory, and semantic compatibility.

## Step 3.3 — Resolve implicit subjects

Example:

```text
User: Tell me about Model Y.
User: What's the range?
```

The second message must resolve to Model Y unless evidence indicates otherwise.

## Step 3.4 — Detect ambiguous references

Example:

```text
User: I was talking about the BMW and Tesla yesterday.
User: Would you buy it?
```

Do not guess if both are plausible.

Ask:

> Do you mean the BMW or the Tesla?

The clarification must be short and specific.

## Step 3.5 — Track entity identity across perception

When the camera sees a known person/object, link the observation to the active entity model where confidence allows.

---

# 9. Phase 4 — Context Manager

This is the central quality component.

The model must not receive every available memory and every world fact.

It should receive the **smallest useful context set**.

## Step 4.1 — Define context sources

Potential sources:

```text
current user turn
recent conversation turns
conversation summary
active conversation anchor
relevant semantic memory
relevant episodic memory
user preferences
identity
relationships
current world state
recent perception
emotional state
social context
current goals/tasks
relevant corrections
relevant skills
model/runtime constraints
```

## Step 4.2 — Rank relevance

Use a combined score:

```text
context_score =
    semantic_similarity
  + active_entity_match
  + active_topic_match
  + intent_match
  + temporal_relevance
  + conversational_recency
  + memory_importance
  + relationship_relevance
  + world_state_relevance
  + confidence
  - contradiction_penalty
  - staleness_penalty
  - duplication_penalty
```

The exact weights should be learned/calibrated from real evaluation data.

## Step 4.3 — Apply context budgets

Define separate budgets for:

```text
recent conversation
conversation summary
memory
world state
emotion/social context
reasoning evidence
```

Do not allow memory retrieval to crowd out the actual conversation.

## Step 4.4 — Distinguish fact classes

Every injected fact should identify whether it is:

```text
OBSERVED_FACT
USER_STATED_FACT
MEMORY
INFERENCE
HYPOTHESIS
PREFERENCE
CURRENT_STATE
HISTORICAL_STATE
UNCERTAIN
```

This prevents Novi from presenting an inference as an observed fact.

## Step 4.5 — Context packet

Create a structured internal packet:

```text
ConversationContextPacket
- current_turn
- intent
- dialogue_act
- resolved_entities
- conversation_anchor
- relevant_history
- relevant_memories
- world_context
- identity_context
- social_context
- emotional_context
- active_goals
- constraints
- uncertainty
- response_requirements
```

Only this packet should be handed to the response planner/model layer.

---

# 10. Phase 5 — Memory Selection and Retrieval Quality

Novi already has memory. The problem is selecting the right memory.

## Step 5.1 — Separate memory types

At minimum:

```text
working memory
conversation memory
episodic memory
semantic memory
preference memory
relationship memory
procedural/routine memory
correction memory
```

## Step 5.2 — Query memory using conversation state

Do not search only by the latest sentence.

Construct a memory query from:

```text
current intent
active topic
active entities
user identity
relationships
open question
recent conversation
explicit memory request
```

## Step 5.3 — Add negative relevance checks

A memory should be rejected if it is:

- semantically similar but about another entity;
- stale and superseded;
- low confidence;
- contradicted by newer information;
- private information not appropriate for the current context;
- unrelated background knowledge.

## Step 5.4 — Memory citation internally

When Novi uses a memory, retain an internal trace:

```text
memory_id
memory_type
source
confidence
why_selected
```

This allows bad responses to be diagnosed.

## Step 5.5 — Never fabricate missing memory

If Novi cannot retrieve the requested memory, it must say so rather than produce a plausible reconstruction.

Real acceptance scenario:

```text
User: Do you remember what I told you about X last month?
Novi: I don't have a reliable memory of that specific detail.
```

This is a PASS, not a failure, when the memory genuinely is unavailable.

---

# 11. Phase 6 — World and Multimodal Grounding

## Step 6.1 — Use current world state only when relevant

Do not dump perception into every answer.

Example:

```text
User: What do you see?
→ use current perception.

User: What's your opinion on philosophy?
→ perception likely irrelevant.

User: Is there anyone in the room?
→ current camera state is required.
```

## Step 6.2 — Resolve temporal validity

Before using a perception fact ask:

```text
How old is it?
Is the source still active?
Could the object/person have moved?
Was confidence high enough?
```

## Step 6.3 — Connect perception to language

Examples:

```text
Camera sees a person.
User: Who just walked in?
→ resolve latest person observation.

Camera sees a cup.
User: What's on the table?
→ use current object detections.

User: Is Sarah here?
→ use identity + current perception + confidence.
```

## Step 6.4 — Do not hallucinate vision

If the camera is unavailable or stale:

> I can't reliably see that right now.

Never convert an old observation into a current claim without temporal qualification.

---

# 12. Phase 7 — Response Planning

Before generating natural language, Novi must decide what the response is supposed to accomplish.

## Step 7.1 — Define response goals

Examples:

```text
ANSWER_DIRECTLY
ASK_CLARIFICATION
ACKNOWLEDGE
REASSURE
CORRECT
DISAGREE_RESPECTFULLY
EXPLAIN
COMPARE
RECOMMEND
SUMMARIZE
REMEMBER
ADMIT_UNCERTAINTY
SET_BOUNDARY
TAKE_ACTION
REPORT_ACTION_RESULT
CONTINUE_SOCIAL_CONVERSATION
```

## Step 7.2 — Define required content

The planner should specify:

```text
must_include
may_include
must_not_include
required_evidence
uncertainty_statement
emotional_style
desired_length
question_allowed
```

## Step 7.3 — Prevent generic responses

If the user asks a question that can be answered, the planner should prefer an answer over generic social filler.

Bad:

> That's an interesting question.

Better:

> I think X because...

## Step 7.4 — Prevent unnecessary questions

If the intended meaning is sufficiently clear, answer.

Ask only when ambiguity materially changes the response.

---

# 13. Phase 8 — Model Routing

Use the model hierarchy deliberately.

## Fast model

Use for:

- intent classification;
- dialogue-act detection;
- entity extraction;
- referent candidates;
- simple emotional classification;
- lightweight response checks.

## Conversational model

Use for:

- normal dialogue;
- social conversation;
- natural-language realization;
- ordinary explanations.

## Larger reasoning model

When available, use for:

- difficult ambiguity;
- complex planning;
- deep reasoning;
- difficult response critique;
- dataset generation;
- benchmark evaluation;
- teacher/reference generation.

The model router must be transparent in the trace.

---

# 14. Phase 9 — Response Critic and Repair

Do not blindly send the first generated answer.

## Step 9.1 — Evaluate the draft

The critic should evaluate:

### Context
Does it answer the current topic?

### Intent
Does it satisfy the user's actual intent?

### Referent
Did it answer about the correct entity/person/place?

### Grounding
Are claims supported by available evidence?

### Memory
Did it use the right memory and avoid invented memory?

### World state
Did it use current perception when required?

### Emotional appropriateness
Does it fit the user's emotional/social state?

### Repetition
Does it unnecessarily repeat previous content?

### Contradiction
Does it conflict with current known state?

### Naturalness
Does it sound like a human conversational response rather than an internal system report?

### Capability honesty
Does it claim actions, perception, memory, or abilities that Novi does not have?

## Step 9.2 — Score the response

Produce structured scores:

```text
context_relevance
intent_match
referent_correctness
grounding
memory_use
emotional_fit
naturalness
non_repetition
contradiction_safety
capability_honesty
```

## Step 9.3 — Repair

If a critical score is below threshold:

```text
draft
 ↓
critic
 ↓
repair instruction
 ↓
regenerate
 ↓
critic
```

Limit repair attempts, for example to 1–2, to avoid latency loops.

## Step 9.4 — Deterministic safety fallback

If repeated generation fails:

- answer directly from verified facts if possible;
- ask a concise clarification if ambiguity is the cause;
- admit uncertainty otherwise.

Never fall back to fabricated confidence.

---

# 15. Phase 10 — Conversation Repair and Self-Correction

Humanlike conversation includes recovery from mistakes.

## Scenario

User:
> No, I meant the BMW, not the Tesla.

Novi must:

1. acknowledge the correction;
2. update the active referent;
3. remove/mark the incorrect interpretation;
4. answer the corrected question if possible;
5. persist the correction when it is durable and appropriate.

Example:

> Ah, you meant the BMW. In that case...

Do not repeatedly make the same mistake later in the conversation.

## Correction types

```text
REFERENT_CORRECTION
FACT_CORRECTION
PREFERENCE_CORRECTION
IDENTITY_CORRECTION
WORLD_STATE_CORRECTION
CONVERSATION_GOAL_CORRECTION
EMOTIONAL_INTERPRETATION_CORRECTION
```

---

# 16. Phase 11 — Failure-Driven Training

Training should be driven by real failures, not arbitrary volume.

## Step 11.1 — Build the failure dataset

Each example:

```text
conversation context
user message
Novi interpretation
Novi response
failure category
correct interpretation
ideal response
reason for correction
```

## Step 11.2 — Generate contrastive examples

For every bad example create:

```text
bad response
acceptable response
excellent response
```

The difference should be meaningful, not cosmetic.

## Step 11.3 — Train context behavior

Create examples where the correct answer depends on:

- previous turn;
- earlier entity;
- memory;
- world state;
- emotional state;
- user preference;
- correction.

## Step 11.4 — Train restraint

Include examples where the correct response is:

```text
I don't know.
I don't remember that reliably.
I can't see that right now.
Do you mean X or Y?
I may be mistaken, but...
```

These are critical intelligence behaviors.

## Step 11.5 — Do not overfit to scripts

Every scenario should have paraphrased variants.

Example:

```text
What's the range?
How far can it go?
What's its real-world range?
How many miles does it get?
Would the range be enough for me?
```

All should resolve to the same active entity/attribute where appropriate.

---

# 17. Phase 12 — Benchmark Design

Create a **real conversational benchmark**, not primarily a unit-test suite.

Target initial benchmark:

**300 scenarios / 1,000+ turns**.

Each scenario should have a human-reviewed expected behavior.

## Benchmark dimensions

```text
Context continuity
Referent resolution
Intent understanding
Memory retrieval
Memory restraint
World grounding
Perception grounding
Emotional appropriateness
Social continuity
Correction handling
Topic changes
Long-context stability
Naturalness
Non-repetition
Groundedness
Capability honesty
Clarification quality
Response usefulness
Recovery from mistakes
```

## Evaluation method

Use a combination of:

1. deterministic checks where objective;
2. human review for conversational quality;
3. strong-model judging where useful;
4. pairwise comparison against previous Novi versions;
5. real-user preference feedback.

Never use a single LLM judge as the only quality metric.

---

# 18. Phase 13 — Real Scenario Catalog

The existing scenario catalog should be expanded rather than replaced.

The following scenarios are mandatory.

## A. Basic conversation

### C-001 First contact

```text
User: Hi Novi.
Novi: natural greeting.
```

PASS if response is natural and does not expose implementation details.

### C-002 Casual continuation

```text
User: How are you?
User: What are you doing?
User: Anything interesting happening?
```

PASS if Novi maintains natural conversational continuity.

### C-003 Follow-up

```text
User: Tell me about the Model Y.
User: What about the range?
```

PASS if `range` resolves to Model Y.

---

## B. Referent resolution

### C-010 Pronoun

```text
User: I was looking at the Model Y yesterday.
User: I really like it.
User: Do you think it's practical?
```

PASS if `it` remains Model Y.

### C-011 Multiple entities

```text
User: I'm comparing a Tesla and a BMW.
User: The Tesla is cheaper.
User: Would you choose it?
```

PASS only if Novi correctly resolves the intended referent; otherwise ask clarification.

### C-012 Entity switch

```text
User: Tell me about Tesla.
User: Now forget that. What about BMW?
User: What is its range?
```

PASS if `its` refers to BMW.

---

## C. Topic management

### C-020 Topic continuation

Several follow-ups remain on one topic.

PASS if Novi does not repeatedly ask what the user is talking about.

### C-021 Topic switch

```text
Tesla discussion
→ football
→ work
```

PASS if Novi cleanly transitions without contaminating the new topic with old context.

### C-022 Return to old topic

```text
Tesla
→ football
→ "Back to the Tesla..."
```

PASS if Novi restores the earlier topic state correctly.

---

## D. Memory

### C-030 Explicit memory write

```text
User: Remember that I prefer dark interiors.
```

Later:

```text
User: What kind of interiors do I prefer?
```

PASS if Novi retrieves the durable preference.

### C-031 Relevant memory

Conversation requires a previously known user preference.

PASS if Novi retrieves it without being explicitly reminded.

### C-032 Irrelevant memory

A conversation has many old facts but only one is relevant.

PASS if Novi does not dump unrelated facts.

### C-033 Missing memory

Ask for a fact that was never stored.

PASS if Novi admits it does not reliably remember it.

### C-034 Conflicting memory

Store old and corrected preferences.

PASS if the newer authoritative correction wins and history remains auditable.

---

## E. Conversation correction

### C-040 Wrong interpretation

User explicitly corrects Novi.

PASS if Novi immediately updates context and does not defend the incorrect interpretation.

### C-041 Repeated correction

Correct Novi once, then revisit the topic later.

PASS if the correction remains effective.

---

## F. Clarification

### C-050 Genuine ambiguity

Two entities are equally plausible.

PASS if Novi asks a short clarification.

### C-051 False ambiguity

Context makes the intended entity obvious.

PASS if Novi answers rather than asking a needless question.

### C-052 Partial ambiguity

Only one attribute is ambiguous.

PASS if Novi asks only about the ambiguous attribute rather than restarting the conversation.

---

## G. Emotional/social conversation

### C-060 User is happy

PASS if Novi matches positive energy without becoming exaggerated.

### C-061 User is sad

PASS if Novi acknowledges emotion and responds appropriately without canned therapy language.

### C-062 User is angry

PASS if Novi remains calm, respectful, and useful.

### C-063 User is joking

PASS if Novi recognizes obvious humor and does not respond with unnecessary formal safety language.

### C-064 User disagrees

PASS if Novi can disagree respectfully and explain why.

### C-065 User praises Novi

PASS if Novi accepts naturally without repetitive self-congratulation.

---

## H. Naturalness

### C-070 Avoid meta-talk

Novi must not say things such as:

```text
According to the conversation history...
My context manager indicates...
The system says...
I have retrieved memory...
```

unless the user explicitly asks about internal operation.

### C-071 Avoid generic filler

No unnecessary:

```text
That's interesting.
I understand.
That sounds great.
Tell me more.
```

when a useful direct answer is available.

### C-072 Avoid repetition

Ask the same topic repeatedly.

PASS if Novi does not repeat the same explanation unnecessarily.

---

## I. Capability honesty

### C-080 Memory honesty

Ask about a nonexistent memory.

PASS if Novi says it does not reliably remember it.

### C-081 Vision honesty

Ask what is currently visible when camera is unavailable.

PASS if Novi does not hallucinate a scene.

### C-082 Action honesty

Ask Novi to perform an unavailable physical action.

PASS if it clearly distinguishes capability from intention.

---

## J. Multimodal conversation

### C-090 Vision-grounded question

```text
Camera sees a cup.
User: What is on the table?
```

PASS if the current observation is used.

### C-091 Person recognition

Known person enters scene.

PASS if recognition confidence is sufficient and response respects identity uncertainty.

### C-092 Stale perception

Object was visible, then removed.

PASS if Novi does not claim it is still visible based on stale state.

### C-093 Speech + vision

User asks about something visible while speaking naturally.

PASS if speech and perception are fused correctly.

---

## K. Long conversations

### C-100 20-turn continuity

Maintain one topic for at least 20 turns.

PASS if context remains coherent.

### C-101 50-turn mixed conversation

Mix:

```text
casual chat
facts
memory
emotion
topic changes
corrections
```

PASS if Novi remains coherent.

### C-102 100-turn stress conversation

Long conversation with controlled topic changes and references.

PASS if quality degrades gracefully and summaries preserve important state.

---

## L. Restart and persistence

### C-110 Before restart

Establish:

- identity;
- preference;
- relationship context;
- conversation topic;
- durable fact.

Restart Novi.

### C-111 After restart

Ask about durable information.

PASS if durable facts are restored.

Do not require transient working context to survive unless explicitly designed to persist.

### C-112 Conversation continuation after restart

If the product contract says thread persistence is supported, continue naturally from the persisted summary/history.

---

## M. Learning

### C-120 Explicit preference learning

Teach a preference.

Later ask for a recommendation.

PASS if the preference influences the recommendation.

### C-121 Correction learning

Correct a previous assumption.

Later repeat similar situation.

PASS if Novi applies the correction.

### C-122 Routine learning

Repeat a behavior across multiple sessions.

PASS only if the resulting routine is sufficiently supported and does not cause inappropriate assumptions.

---

## N. Reasoning quality

### C-130 Simple question

PASS if Novi answers quickly without unnecessary complex reasoning.

### C-131 Ambiguous question

PASS if Novi identifies ambiguity.

### C-132 Complex question

PASS if Novi retrieves relevant context, reasons correctly, and gives a useful answer.

### C-133 Contradictory evidence

Provide conflicting information.

PASS if Novi identifies the conflict rather than silently selecting one fact.

---

# 19. Phase 14 — Real End-to-End Test Harness

The primary test runner should execute **real Novi**, not isolated classes.

## Step 14.1 — Launch the actual Mac Brain

Use the same startup path as the user.

No test-only shortcut that bypasses production orchestration.

## Step 14.2 — Use the real model runtime

Use the actual configured Ollama/model backend.

Record:

```text
model
provider
runtime
parameters
context settings
reasoning mode
```

## Step 14.3 — Use real persistence

Use the real database/storage layer.

Do not replace memory with an in-memory fake for acceptance runs.

## Step 14.4 — Use the real web/terminal/voice path

Where a scenario is meant to validate user behavior, drive the same interface a real user uses.

## Step 14.5 — Capture complete traces

For every turn store an acceptance trace containing:

```text
input
normalized input
conversation state
intent
referents
retrieved context
memory candidates
selected memories
world state used
emotion/social state
response goal
model route
response
critic result
repair count
final result
latency
```

Do not expose internal traces to normal users unless explicitly requested; they are test evidence.

---

# 20. Phase 15 — Real Human Evaluation

Automated evaluation is not sufficient.

Recruit a small group of evaluators, ideally including the primary Novi user and at least 2–4 independent reviewers.

Each evaluator should conduct scripted and unscripted sessions.

Score each response 1–5 on:

```text
Did Novi understand me?
Did Novi stay on topic?
Did Novi remember what mattered?
Did Novi answer the actual question?
Did Novi feel natural?
Did Novi use context appropriately?
Did Novi feel emotionally appropriate?
Did Novi make me repeat myself?
Did Novi hallucinate?
Would I trust this response?
```

Also collect free-text feedback:

> What specifically made Novi feel unintelligent here?

This question is more useful than a generic thumbs-up/down.

---

# 21. Phase 16 — Pairwise Version Testing

Every significant intelligence change should be evaluated against the previous stable Novi.

Run:

```text
same scenario
same input
same initial state
same model configuration where possible
old Novi
new Novi
```

Then compare:

```text
Which response is more relevant?
Which preserves context better?
Which is more natural?
Which uses memory better?
Which is more grounded?
Which would you prefer as a user?
```

This prevents regressions hidden by aggregate metrics.

---

# 22. Phase 17 — Long-Running Real Sessions

The goal is not merely good isolated turns.

Run Novi continuously for:

- 30 minutes;
- 1 hour;
- 2 hours;
- eventually 4+ hours.

Include:

```text
chat
camera
neural perception
recognition
LLM responses
auto-step
memory retrieval
learning
web UI
voice where available
```

Observe:

- conversational quality drift;
- context drift;
- memory contamination;
- repeated responses;
- hallucinations;
- latency drift;
- RAM growth;
- worker growth;
- event growth;
- browser memory growth;
- model/runtime failures.

A session that becomes technically stable but conversationally incoherent is a failure.

---

# 23. Phase 18 — Context Degradation Tests

Intentionally stress the context system.

## Scenario types

### Many irrelevant facts

Inject 50+ irrelevant memories.

PASS if the correct memory still wins.

### Many similar entities

Create several similar objects/people/topics.

PASS if referents remain correct.

### Long conversation

100+ turns.

PASS if the active topic and durable summary remain correct.

### Rapid topic switching

Switch topics every 2–3 turns.

PASS if context boundaries remain clean.

### Return to previous topics

Cycle through three topics repeatedly.

PASS if Novi can restore each topic correctly.

---

# 24. Phase 19 — Adversarial Conversation Testing

Test cases designed to expose weak behavior:

```text
ambiguous pronouns
contradictory claims
misleading wording
sarcasm
jokes
indirect requests
unfinished sentences
very short replies
one-word answers
rapid topic changes
multiple entities with same type
old memories conflicting with new facts
stale perception
missing perception
model refusal edge cases
user corrections
repeated questions
```

The goal is not to trick Novi for sport. The goal is to find where ordinary human conversation breaks the architecture.

---

# 25. Phase 20 — Voice and Multimodal Real Tests

Once voice is active, repeat the benchmark through speech.

## Voice scenarios

- normal conversation;
- interruptions;
- short confirmations;
- corrections;
- pronouns;
- emotional tone;
- noisy environment;
- partial ASR errors;
- repeated words;
- pauses;
- topic changes.

The test must determine whether failures come from:

```text
ASR
→ normalization
→ intent
→ context
→ reasoning
→ response
→ TTS
```

Do not blame the LLM automatically.

## Multimodal scenarios

Run:

```text
vision only
speech only
vision + speech
memory + vision
memory + speech
vision + speech + memory
```

and compare behavior.

---

# 26. Phase 21 — Response Quality Gates

Establish practical acceptance thresholds after the baseline is measured.

Initial target direction, to be calibrated:

```text
Context continuity              >= 95%
Referent resolution             >= 95%
Intent understanding            >= 95%
Memory relevance                >= 90%
Memory hallucination            0 critical cases
World grounding                 >= 95%
Capability honesty              100% critical cases
Correction recovery             >= 95%
Unnecessary clarification       <= 5%
Critical out-of-context replies <= 2%
Severe emotional mismatches     <= 2%
Repeated-response failures      <= 5%
```

These are starting targets, not excuses to manipulate metrics. If a target is unrealistic, document the measured baseline and revised target.

A single catastrophic hallucinated memory can remain a release blocker even if aggregate quality is high.

---

# 27. Phase 22 — Evidence Artifact

Every acceptance run should produce a machine-readable evidence file.

Example:

```json
{
  "scenario": "C-003-follow-up",
  "git_sha": "...",
  "timestamp": "...",
  "hardware": "...",
  "runtime": "...",
  "model": "...",
  "conversation": [...],
  "state_before": {...},
  "intent": {...},
  "referents": [...],
  "context": {...},
  "memory": [...],
  "world": {...},
  "response_plan": {...},
  "response": "...",
  "critic": {...},
  "latency_ms": 0,
  "human_rating": null,
  "result": "PASS"
}
```

The evidence must identify the exact software/model/runtime configuration used.

---

# 28. Phase 23 — Human-Reviewed Acceptance Sessions

At every major milestone, conduct a real session with no developer intervention.

The evaluator should not manually repair context for Novi.

Minimum session:

```text
20–30 minutes
multiple topics
memory references
emotional interaction
corrections
at least one ambiguity
at least one topic return
at least one multimodal question
```

Record the full session.

Afterwards, mark every response:

```text
PASS
MINOR ISSUE
MAJOR ISSUE
FAIL
```

For every MAJOR/FAIL, classify the root cause.

---

# 29. Phase 24 — Root-Cause Loop

Every real failure follows this process:

```text
Bad response
   ↓
Classify failure
   ↓
Find layer
   ↓
Fix layer
   ↓
Re-run original scenario
   ↓
Re-run related scenarios
   ↓
Re-run full benchmark slice
   ↓
Run long real session
```

Possible root layers:

```text
ASR
input normalization
intent
referent resolution
conversation state
memory retrieval
world retrieval
emotion/social state
context composition
response planning
model routing
LLM generation
response critic
repair
persistence
```

Do not immediately retrain the model for every failure. First determine whether the model was given the correct cognitive context.

---

# 30. Phase 25 — Training Decision Tree

For every repeated failure ask in order:

### Question 1
Did Novi have the correct information?

If no → fix retrieval/context/world state.

### Question 2
Did Novi have the correct intent/referent?

If no → fix interpretation.

### Question 3
Did Novi have the correct response plan?

If no → fix cognition/policy.

### Question 4
Did the model receive a correct compact context packet?

If no → fix context composition.

### Question 5
Did the model still generate a bad response despite all correct inputs?

If yes → consider prompt/training/model changes.

This prevents expensive model training from compensating for architectural bugs.

---

# 31. Phase 26 — Model Training Strategy

Only after the architecture and benchmark are stable:

## SFT

Train on:

- context continuity;
- referent resolution;
- correct dialogue acts;
- grounded memory usage;
- emotional/social response;
- correction behavior;
- concise clarification;
- natural direct answers;
- capability honesty.

## Preference data

Create pairs where:

```text
A = technically fluent but contextually wrong
B = contextually correct and natural
```

This is more valuable than generic style preference pairs.

## DPO/preference optimization

Use only when the benchmark identifies systematic preference failures that SFT and orchestration do not solve.

Evaluate against the frozen benchmark before promotion.

## Larger teacher model

Use the stronger local model for:

- generating candidate interpretations;
- difficult scenario labeling;
- critic/reference answers;
- synthetic paraphrase generation;
- failure explanation.

Human-review the generated dataset before training.

---

# 32. Phase 27 — Regression Without Becoming Unit-Test Driven

Unit tests are not the primary acceptance mechanism, but a small number of automated checks should protect the real scenarios.

The important artifact is the **scenario runner**, not thousands of mocked assertions.

Every accepted real scenario should be replayable automatically:

```text
scenario JSON
   ↓
real Novi runtime
   ↓
real model
   ↓
real persistence
   ↓
real response
   ↓
scoring
   ↓
acceptance result
```

Use automated tests mainly to detect whether a previously accepted scenario has regressed.

---

# 33. Phase 28 — Release Gates

A conversational-quality release should require:

### Gate A — Baseline

A frozen real-conversation benchmark exists.

### Gate B — No critical regressions

No increase in:

- hallucinated memories;
- false perception claims;
- severe context failures;
- severe emotional failures;
- capability misrepresentation.

### Gate C — Context quality

Target thresholds met for context/referent/intent metrics.

### Gate D — Real human session

20–30 minute human session passes without major context breakdown.

### Gate E — Long session

At least 1–2 hours of continuous operation with no unacceptable quality or memory degradation.

### Gate F — Multimodal

Camera/voice scenarios pass where those capabilities are enabled.

### Gate G — Restart

Durable memory and supported conversation persistence survive restart.

### Gate H — Evidence

All results tied to exact Git SHA/model/runtime configuration.

---

# 34. Phase 29 — Recommended Implementation Order

Do not implement everything simultaneously.

## Sprint 1 — Baseline and instrumentation

1. Freeze current model/runtime configuration.
2. Collect real bad conversations.
3. Create failure taxonomy.
4. Build acceptance trace capture.
5. Build scenario replay harness.
6. Establish baseline scores.

**Deliverable:** `conversation-baseline-v1`.

## Sprint 2 — Conversation state

1. Implement ConversationState.
2. Implement conversation anchors.
3. Implement topic continuity.
4. Implement topic switching.
5. Implement open-question tracking.
6. Implement active entity tracking.

**Deliverable:** stable multi-turn context.

## Sprint 3 — Intent and referents

1. Intent classifier.
2. Dialogue-act classifier.
3. Entity resolver.
4. Pronoun resolver.
5. Ambiguity detector.
6. Confidence thresholds.

**Deliverable:** reliable interpretation.

## Sprint 4 — Context manager

1. Context packet.
2. Memory ranking.
3. World ranking.
4. conversation-history selection.
5. emotional/social context selection.
6. context budgets.
7. fact-type labeling.

**Deliverable:** relevant compact context.

## Sprint 5 — Response planning

1. Response goals.
2. Response strategies.
3. Required/forbidden content.
4. Direct-answer preference.
5. Clarification policy.
6. Model routing.

**Deliverable:** intentional responses.

## Sprint 6 — Critic and repair

1. Draft generation.
2. critic.
3. structured scoring.
4. repair.
5. bounded retries.
6. deterministic fallback.

**Deliverable:** fewer bad final responses.

## Sprint 7 — Real scenario campaign

1. Run 300-scenario benchmark.
2. Run human sessions.
3. Fix highest-frequency failure classes.
4. Repeat benchmark.
5. Compare against baseline.

**Deliverable:** measurable intelligence improvement.

## Sprint 8 — Failure-driven training

1. Build curated training set.
2. Train SFT candidate.
3. Evaluate frozen benchmark.
4. Compare to baseline.
5. Promote only if better.
6. Generate preference pairs for remaining failures.
7. Evaluate DPO candidate if justified.

**Deliverable:** validated trained model improvement.

## Sprint 9 — Long-running multimodal validation

1. 1-hour session.
2. 2-hour session.
3. camera + recognition.
4. voice + conversation.
5. memory + perception.
6. restart.
7. resource monitoring.

**Deliverable:** real Mac Brain acceptance evidence.

---

# 35. Detailed End-to-End Acceptance Campaign

This is the most important section of the plan.

## Campaign 1 — Natural conversation

Duration: 15 minutes.

Human speaks naturally without following a script.

Include:

- greetings;
- casual discussion;
- follow-ups;
- jokes;
- opinions;
- topic transitions.

PASS criteria:

- no major context loss;
- no repeated generic filler;
- no implementation/meta talk;
- natural turn-taking.

## Campaign 2 — Deep topic conversation

Duration: 20 minutes.

One topic with 20+ turns.

PASS:

- entity remains correct;
- previous facts are used appropriately;
- no unnecessary resets;
- no significant context drift.

## Campaign 3 — Multi-topic conversation

Duration: 30 minutes.

Cycle among three topics.

PASS:

- transitions clean;
- old context does not contaminate new topic;
- explicit return restores correct context.

## Campaign 4 — Memory

Teach 10 durable facts/preferences.

Discuss unrelated topics.

Return later.

PASS:

- relevant memories retrieved;
- irrelevant memories not injected;
- corrections override outdated facts.

## Campaign 5 — Ambiguity

Use deliberately ambiguous references.

PASS:

- correct resolution where context is sufficient;
- concise clarification where it is not.

## Campaign 6 — Emotional conversation

Conduct happy, sad, frustrated, joking, disagreement and reassurance scenarios.

PASS:

- appropriate tone;
- no canned responses;
- no emotional overreaction;
- social context preserved.

## Campaign 7 — Vision-grounded conversation

Real camera active.

Perform:

- object questions;
- person questions;
- scene questions;
- appearance changes;
- object removal;
- identity confidence cases.

PASS:

- current perception used;
- stale perception not treated as current;
- uncertainty communicated appropriately.

## Campaign 8 — Voice conversation

Real microphone/STT/TTS.

Include interruptions, short replies, corrections and ambiguous references.

PASS:

- ASR errors do not cause cascading context failures where recoverable;
- speech responses remain natural;
- state remains continuous.

## Campaign 9 — Restart

Build context and memory.

Restart the application.

Continue.

PASS:

- durable memory restored;
- supported thread state restored;
- no false memories introduced.

## Campaign 10 — Long-running autonomy

Run Novi for 2+ hours with:

- auto-step;
- camera;
- LLM;
- memory;
- web UI;
- intermittent conversation.

PASS:

- memory remains bounded;
- no context degradation;
- no increasing response latency caused by retained history;
- no worker/event leak;
- no persistent conversational drift.

---

# 36. Real-User Evaluation Form

For each response, evaluators should answer:

```text
1. Did Novi understand what you meant?       1–5
2. Did it stay on the current topic?         1–5
3. Did it remember useful context?           1–5
4. Was the answer actually useful?           1–5
5. Did it feel natural?                      1–5
6. Was the emotional tone appropriate?       1–5
7. Did it make you repeat yourself?          yes/no
8. Did it hallucinate anything?              yes/no
9. Did it ask an unnecessary question?       yes/no
10. Would you trust this response?           1–5
```

Then:

```text
What was wrong, if anything?
What should Novi have said instead?
What information should Novi have used?
```

These answers become future training/evaluation data.

---

# 37. Observability Requirements

During acceptance runs expose a developer-only trace containing:

```text
turn id
input timestamp
normalization latency
intent latency
referent latency
memory retrieval latency
world retrieval latency
context composition latency
model latency
critic latency
repair latency
total latency
model selected
context token count
memory count
world facts count
response score
```

Also track:

```text
context drift
memory retrieval hit rate
clarification rate
critic rejection rate
repair rate
hallucination reports
user corrections
repeated-response rate
```

These metrics should be used to identify bottlenecks rather than exposed as user-facing technical language.

---

# 38. Performance Requirements

The intelligence pipeline must not become so expensive that Novi feels slow.

Measure end-to-end latency:

```text
input received
→ response visible/audible
```

Break down:

```text
interpretation
context retrieval
reasoning
LLM generation
critic
repair
```

The fast path should avoid unnecessary critic/model calls for trivial responses.

Suggested policy:

```text
simple greeting → fast path
simple factual follow-up → normal path
ambiguous/complex question → deeper path
high-risk/action request → strongest verification path
```

---

# 39. Privacy Requirements

Real conversation testing may contain personal information.

Before storing acceptance traces:

- define retention rules;
- redact secrets;
- avoid unnecessary personal data;
- separate production/private sessions from benchmark data;
- use synthetic replacements where possible;
- keep raw audio/video only when explicitly required for evaluation;
- do not use private memories as generic training data without authorization.

The test system must preserve the existing privacy and governance model.

---

# 40. What Not To Do

Do not:

- simply increase the context window;
- dump all memories into prompts;
- add more generic system-prompt instructions as the main fix;
- replace the current model solely because of a few bad responses;
- train on random internet conversation without failure analysis;
- optimize for benchmark scores while ignoring real sessions;
- use only unit tests as proof of intelligence;
- hide uncertainty;
- fabricate memory to appear smarter;
- make Novi ask clarification questions for everything;
- make Novi answer confidently when ambiguity is material;
- add multiple overlapping conversation-state implementations;
- allow the web UI to own conversation logic;
- bypass the canonical BrainDriver/Brain architecture in acceptance tests.

---

# 41. Definition of Done

This plan is complete only when all of the following are true:

### Architecture

- [ ] Conversation state is first-class.
- [ ] Intent and dialogue act are explicit.
- [ ] Referential resolution is explicit.
- [ ] Context selection is centralized.
- [ ] Memory selection is relevance-aware.
- [ ] World/perception grounding is temporal and confidence-aware.
- [ ] Response planning is explicit.
- [ ] Response verification exists.
- [ ] Repair is bounded.

### Quality

- [ ] Baseline real-conversation dataset exists.
- [ ] Failure taxonomy exists.
- [ ] 300+ real/curated scenarios exist.
- [ ] Long conversations are evaluated.
- [ ] Multimodal conversations are evaluated.
- [ ] Human evaluation is included.
- [ ] Pairwise old-vs-new evaluation is included.

### Training

- [ ] Failure-driven SFT dataset exists.
- [ ] SFT candidate beats baseline or is rejected.
- [ ] Preference data exists for remaining systematic failures.
- [ ] DPO is evaluated only when justified.
- [ ] Model promotion is evidence-based.

### Real runtime

- [ ] Real Mac Brain is used.
- [ ] Real model runtime is used.
- [ ] Real persistence is used.
- [ ] Real camera/voice paths are tested where enabled.
- [ ] Restart is tested.
- [ ] 1–2 hour continuous sessions pass.
- [ ] Memory remains bounded.
- [ ] Latency remains acceptable.

### Acceptance

- [ ] No critical memory hallucination failures.
- [ ] No critical false perception claims.
- [ ] Context/referent/intent targets are met.
- [ ] Human reviewers report a clear improvement over baseline.
- [ ] The primary user reports fewer out-of-context/bad responses.
- [ ] Evidence artifacts are tied to exact Git/model/runtime versions.

---

# 42. Final Acceptance Gate

The final question is not:

> "How many tests pass?"

It is:

> **Can a person spend a meaningful amount of time talking naturally with Novi, change topics, refer back to previous things, teach Novi facts, ask follow-up questions, correct it, involve emotions and perception, restart it, and continue—without repeatedly feeling that Novi has forgotten, misunderstood, hallucinated, or lost the conversation?**

The acceptance run should therefore be a real human session on the actual Mac Brain.

### Final target flow

```text
                         REAL HUMAN
                             │
                             ▼
                    chat / voice / vision
                             │
                             ▼
                       BrainDriver
                             │
                             ▼
                    input normalization
                             │
                             ▼
                  intent + dialogue act
                             │
                             ▼
                    referent resolution
                             │
                             ▼
                   conversation state
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           memory          world         emotion
           retrieval       state         social
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    context composition
                             │
                             ▼
                     response planning
                             │
                             ▼
                       model routing
                             │
                             ▼
                       draft response
                             │
                             ▼
                         critic
                       ┌─────┴─────┐
                       │           │
                     PASS        FAIL
                       │           │
                       │         repair
                       │           │
                       └─────┬─────┘
                             ▼
                       final response
                             │
                             ▼
                    learning / memory
                             │
                             ▼
                    durable Novi state
```

The result should be a Novi that feels smarter because its **whole brain understands the conversation**, not merely because the language model became larger.

---

# 43. Immediate Next Action

Do not begin by retraining Qwen.

The immediate implementation order is:

1. **Create the real-conversation baseline.**
2. Capture at least 100 real conversations / 500+ turns.
3. Classify every bad response.
4. Implement the first ConversationState + ConversationAnchor.
5. Implement intent/dialogue-act + referent resolution.
6. Implement the centralized Context Manager.
7. Implement response planning.
8. Add response critic/repair.
9. Build the real scenario replay runner.
10. Run the 300-scenario benchmark against the current Novi baseline.
11. Fix the highest-frequency failures one layer at a time.
12. Re-run the benchmark after every meaningful change.
13. Only then create failure-driven SFT data.
14. Evaluate SFT against the frozen real benchmark.
15. Evaluate DPO only if evidence says preference optimization is needed.
16. Run human 20–30 minute sessions.
17. Run 1–2 hour real Mac sessions with camera/LLM/web/auto-step.
18. Produce the final acceptance evidence pack.

**The first coding task is therefore the real conversation baseline + scenario replay harness.** It gives Novi an objective way to answer the most important question from now on: **did this change actually make Novi smarter for a real person, or did it only make the code/tests look better?**
