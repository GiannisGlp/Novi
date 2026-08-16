# 03 — Attention and Social Behavior

## Status

**DESIGN** — detailed behavioral specification.

## Purpose

Novi must continuously observe its environment without continuously interrupting people. Attention is the gate between perception and external behavior.

## Attention Is Not Conversation

Seeing or hearing an event does not imply that Novi should speak.

```text
Perception
   ↓
Salience
   ↓
Attention
   ↓
Interaction decision
   ↓
Possible response
```

The default behavior for low-value events is observation and internal state update.

## Attention Factors

Attention scoring may consider:

- safety relevance
- explicit user request
- direct address / wake signal
- novelty
- familiarity
- relationship
- emotional/social significance
- persistence
- recurrence
- current goal relevance
- spatial proximity
- confidence
- interruption cost
- whether Novi recently responded
- whether a similar event was already acknowledged

The implementation should use explainable feature contributions and policy gates rather than an opaque single number for consequential decisions.

## Interaction Modes

Novi may enter:

- `PASSIVE`
- `AWARE`
- `SOCIAL`
- `CONVERSATION`
- `TASK_FOCUSED`
- `EMERGENCY`

Mode changes must be observable and reversible.

## Non-Interruption

Novi should normally avoid speaking when:

- people are having an unrelated private conversation;
- the event has no meaningful relevance to Novi's goals;
- confidence is low and no clarification is useful;
- Novi has already acknowledged the event;
- the interruption cost is greater than the expected benefit;
- social policy indicates silence.

It may still update internal state or use subtle nonverbal signals if configured.

## Nonverbal Interaction

Before speech, Novi may use:

- screen expression
- eye/head orientation
- lighting
- small animation
- body posture
- subtle audio cue

These actions also require policy checks and should not become distracting.

## Social Context

The interaction decision uses relationship state:

```text
unknown person
visitor
acquaintance
friend
household member
family
trusted user
```

Relationship labels are not assumed solely from face recognition. They are evidence-backed state maintained by the identity/relationship subsystem.

## Personality Integration

Personality influences style after the system decides that interaction is appropriate. Personality must not override safety, privacy, consent, or explicit user preferences.

Example:

```text
Attention says: SPEAK
Relationship says: family
Personality says: playful
Current affect says: energetic

→ generate a playful family-appropriate response
```

## Repeated Questions

Novi may recognize that a person previously asked the same or similar question. It should use memory to adapt the response, but must avoid humiliating or falsely claiming memory when confidence is insufficient.

Example behavior:

> “You asked me something very similar a few days ago — want the answer again?”

The exact phrasing remains model-generated within the interaction policy.

## Tone and Expression

Perceived tone, facial expression, body posture, and conversational context can become evidence for an internal emotion hypothesis. These are probabilistic observations and must not be represented as certain facts about a person's mental state.

Use:

```text
possible_state = tired
confidence = 0.62
source = multimodal_observation
```

not:

```text
person_is_tired = true
```

unless independently verified.

## Social Response Selection

The response policy considers:

1. Is interaction warranted?
2. Who is the person?
3. What is the relationship?
4. What is happening?
5. What has recently happened?
6. What does the person appear to be doing?
7. What personality style is appropriate?
8. Is the information sufficiently certain?
9. Is the response safe and privacy-preserving?
10. Should the response be verbal, visual, physical, or silent?

## Attention Decay

Attention should decay when:

- an event is acknowledged;
- the event stops changing;
- no useful action remains;
- the person moves away;
- the goal is completed;
- evidence becomes stale.

Persistent events may refresh attention only when a meaningful change occurs.

## Attention Budget

Novi must avoid becoming socially exhausting. A configurable attention budget can limit proactive interactions per time window while allowing safety and direct user requests to bypass ordinary social limits.

## Curiosity Interaction

Curiosity can create internal goals, but curiosity alone should not justify interrupting people repeatedly. Novi should batch questions where practical and select appropriate moments.

## Acceptance Criteria

The system should demonstrate:

- high-frequency observation with low conversational interruption;
- correct direct-address detection;
- different interaction styles for different relationship classes;
- use of recent memory without fabricated memories;
- multimodal social-context hypotheses with confidence;
- nonverbal reactions without speech when appropriate;
- attention decay and duplicate suppression;
- safety and privacy constraints overriding social behavior.
