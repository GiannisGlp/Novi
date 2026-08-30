# Novi — Learning, Fine-Tuning & Continuous Improvement Plan

**Status:** PLANNED
**Date:** 2026-08-30
**Workstream:** `docs/plans/01_BRAIN/`
**Purpose:** define how Novi learns natural conversation, dialogue policy, memory retrieval, grounding, multimodal behavior, and user-specific interaction preferences without attempting to encode the live world or personal memories into model weights.

---

## 0. Core decision

Novi should be trained, but training must be applied to the correct layers.

```text
DETERMINISTIC / STATEFUL BRAIN
  perception
  identity
  world model
  memory
  safety/governance
  current state
        │
        ▼
LEARNED BEHAVIOR
  dialogue policy
  retrieval ranking
  grounding ranking
  natural language realization
  interaction preferences
        │
        ▼
MODEL
  Qwen-based local model + Novi adapter
```

Do **not** train live facts such as "Vano is here" or "the mug is on the desk" into weights. Those belong in Novi's world model and memory.

The existing Novi dialogue plan already establishes a unified response path, natural-dialogue machinery, event-driven proactive speech, speaking leases and initiative budgets. This training plan must improve those capabilities rather than create a second dialogue architecture. fileciteturn4file0

---

# 1. Training objectives

Novi's learned behavior should improve six capabilities:

1. **Natural language** — sound conversational rather than assistant-like.
2. **Dialogue policy** — decide when to answer, ask, clarify, continue or remain silent.
3. **Memory retrieval** — select memories useful to the current situation.
4. **Multimodal grounding** — connect language to observed people, objects, places and actions.
5. **Social adaptation** — adapt verbosity, style and timing to the interaction context.
6. **Interaction learning** — learn from corrections, successful conversations and failed conversational choices.

Training must never become an excuse to remove deterministic grounding, provenance, uncertainty or safety controls.

---

# 2. Model strategy

Current permitted Novi models:

```text
qwen3.8:27b
qwen3:8b
qwen3:4b
nemotron-3.5-lightning:latest
qwen3.8:latest
```

Initial recommendation:

```text
Base conversational model:
  qwen3:8b

Runtime fast path:
  qwen3:4b

Complex reasoning / teacher / evaluator:
  qwen3.8:27b

Latency experiments:
  nemotron-3.5-lightning:latest

Experimental:
  qwen3.8:latest
```

Start with **LoRA/QLoRA**, not full fine-tuning.

Reasons:

- preserves the base model;
- cheap iteration;
- easy rollback;
- multiple Novi behavior versions can coexist;
- adapter can be replaced without rebuilding the complete model;
- avoids baking changing personal memories into weights.

Qwen's ecosystem supports SFT and parameter-efficient fine-tuning approaches including LoRA/Q-LoRA.

---

# 3. What should and should not be trained

| Capability | Train? | Primary storage |
|---|---:|---|
| Natural wording | YES | model adapter |
| Conversational style | YES | model adapter |
| Dialogue-act selection | YES | policy model / adapter |
| Initiative ranking | YES | policy model / learned scorer |
| Memory relevance | YES | retrieval scorer |
| Reference ranking | YES | grounding model/scorer |
| Person identity | NO | identity/world model |
| Current object location | NO | world model |
| Current conversation state | NO | runtime state |
| Long-term personal memories | NO | memory store |
| Safety authority | NO | deterministic governance |
| User preferences | primarily runtime memory | preference memory |
| General world knowledge | base model / curated knowledge | model + explicit knowledge |

---

# 4. Dataset architecture

Create:

```text
training/
├── README.md
├── configs/
│   ├── sft.yaml
│   ├── dpo.yaml
│   ├── retrieval.yaml
│   ├── grounding.yaml
│   └── evaluation.yaml
│
├── datasets/
│   ├── raw/
│   ├── cleaned/
│   ├── curated/
│   ├── sft/
│   ├── dpo/
│   ├── retrieval/
│   ├── grounding/
│   └── evaluation/
│
├── collection/
│   ├── trace_exporter.py
│   ├── sanitizer.py
│   ├── deduplicator.py
│   └── annotator.py
│
├── training/
│   ├── train_sft.py
│   ├── train_dpo.py
│   ├── train_retriever.py
│   └── evaluate.py
│
├── models/
│   ├── adapters/
│   └── manifests/
│
└── experiments/
```

Before creating this structure, inspect the repository for an existing training/ML/data directory and extend it rather than creating duplicates.

---

# 5. Canonical training example

Every training example should be grounded in an explicit situation.

```json
{
  "example_id": "dlg-0001821",
  "task": "dialogue_realization",
  "situation": {
    "person": {
      "id": "person:vano",
      "name": "Vano",
      "relationship": "owner",
      "confidence": 0.98
    },
    "world": {
      "location": "office",
      "person_facing_novi": true
    },
    "conversation": {
      "topic": "camera integration",
      "open_threads": ["perception-to-world-model integration"]
    },
    "memory": [
      {
        "id": "mem-1821",
        "summary": "Previous discussion about camera integration",
        "confidence": 0.97
      }
    ],
    "social": {
      "engaged": true,
      "interruptibility": 0.15
    }
  },
  "decision": {
    "dialogue_act": "CONTINUE",
    "reason": "unfinished_thread",
    "verbosity": "short"
  },
  "response": "There's one part of the camera side we haven't closed yet."
}
```

The dataset must preserve enough context to explain why the answer is appropriate.

---

# 6. Phase 1 — collect Novi interaction traces

## 6.1 Instrument the brain

Record structured traces for meaningful interactions:

```text
trace_id
cycle_id
timestamp
input/event
perception evidence
identity evidence
world-state changes
retrieved memories
attention scores
prediction
active goals
social context
dialogue candidates
selected dialogue act
initiative score
model
prompt/context version
response
user reaction
correction
outcome
memory writes
```

Do not automatically record raw private audio/video forever. Store derived structured evidence wherever possible and apply explicit retention/privacy rules.

## 6.2 Export only useful examples

Do not train on every turn.

Filter for:

```text
meaningful context
clear decision
successful outcome
explicit correction
interesting failure
initiative decision
memory retrieval decision
grounding decision
```

## 6.3 Positive examples

Examples:

```text
successful clarification
successful memory recall
appropriate silence
appropriate proactive comment
correct reference resolution
natural response
successful repair
```

## 6.4 Negative examples

Examples:

```text
unnecessary verbosity
repetition
wrong memory
wrong object
wrong person
unnecessary interruption
assistant-like phrasing
unjustified certainty
missed proactive opportunity
unwanted proactive interruption
```

---

# 7. Phase 2 — privacy and data governance

Training data can contain highly personal information.

Implement:

```text
consent state
retention policy
redaction
PII detection
biometric separation
user deletion
trace deletion
training-dataset deletion
model-version provenance
```

Never put raw face embeddings, voiceprints, passwords, tokens, secrets or unrelated private information into language-training examples.

Person identity training should use abstract IDs:

```text
person:owner_001
```

rather than unnecessarily exposing biometric information.

---

# 8. Phase 3 — data cleaning

Implement deterministic preprocessing:

```text
raw traces
 → schema validation
 → PII/privacy filter
 → malformed-example removal
 → duplicate detection
 → contradiction detection
 → context completeness check
 → quality scoring
 → human review
 → curated dataset
```

Reject an example if:

- its response depends on missing context;
- the memory referenced does not exist;
- the visual evidence is absent;
- the identity confidence is below the required threshold for the claimed identity;
- the response makes unsupported claims;
- the outcome label is unknown when the task requires an outcome.

---

# 9. Phase 4 — annotation system

Create annotations for:

```text
speaker/addressee
conversation state
user intent
dialogue act
social context
memory relevance
initiative appropriateness
grounding correctness
naturalness
verbosity
certainty calibration
outcome quality
```

Example:

```json
{
  "dialogue_act": "CLARIFY",
  "memory_relevance": 0.91,
  "initiative_appropriate": true,
  "grounding_correct": true,
  "naturalness": 5,
  "verbosity": 5,
  "certainty": 5
}
```

Use multiple reviewers for high-impact examples.

---

# 10. Phase 5 — SFT for natural Novi speech

This is the first model training stage.

## 10.1 Dataset

Start with:

```text
natural_dialogue
context_continuation
clarification
repair
memory_grounded_response
proactive_comment
social_greeting
silence/abstention
```

## 10.2 Training target

Train:

```text
situation + communicative act → natural response
```

Not:

```text
raw user text → generic chatbot answer
```

## 10.3 Examples

Bad:

```text
"I acknowledge your statement."
```

Preferred:

```text
"Yeah, that makes sense."
```

Bad:

```text
"I have detected that you have entered the room."
```

Preferred:

```text
"Hey."
```

Bad:

```text
"I can confirm that the object you are referencing is a coffee mug."
```

Preferred:

```text
"The mug?"
```

The model must learn context-sensitive naturalization, not memorize these exact phrases.

---

# 11. Phase 6 — DPO / preference training

After SFT is stable, build preference pairs.

Example:

```text
Situation:
Vano enters room.

A:
"Hello Vano. It is nice to see you again."

B:
"Hey."

preferred = B
```

Another:

```text
Situation:
Vano asks a simple known question.

A:
three-paragraph explanation

B:
one direct sentence

preferred = B
```

Another:

```text
Situation:
Novi is uncertain which object the user means.

A:
choose one silently

B:
"The blue one?"

preferred = B
```

Train preferences for:

```text
naturalness
brevity
context continuity
appropriate uncertainty
initiative timing
repair quality
memory usage
social appropriateness
```

---

# 12. Phase 7 — train dialogue policy

The dialogue policy should eventually be independently trainable.

Input:

```text
world
conversation
memory
attention
social state
goals
predictions
candidate initiatives
```

Output:

```text
SILENCE
RESPOND
ASK
CLARIFY
COMMENT
CONTINUE
FOLLOW_UP
GREETING
FAREWELL
WARN
SUGGEST
```

Example training record:

```json
{
  "state": {
    "user_speaking": false,
    "known_person": true,
    "new_event": true,
    "event_salience": 0.86,
    "open_thread": true,
    "interruption_cost": 0.08
  },
  "candidates": [
    "SILENCE",
    "GREETING",
    "CONTINUE"
  ],
  "preferred": "CONTINUE"
}
```

Initially keep the deterministic policy as the authority and train a model to rank/recommend decisions. Only later consider learned policy control under strict constraints.

---

# 13. Phase 8 — train memory retrieval ranking

Create retrieval examples:

```text
query
candidate memories
preferred memory ranking
```

Example:

```text
Query:
"What did we decide about the camera?"

A:
Vano bought a camera in March.

B:
Vano and Novi discussed camera recognition yesterday.

C:
Novi saw a camera in the kitchen.

Preferred:
B
```

Train a reranker using features:

```text
semantic relevance
recency
importance
person relevance
goal relevance
current situation
causal relation
confidence
provenance
spatial relevance
contradiction
```

Vector similarity remains one candidate-generation signal.

---

# 14. Phase 9 — train grounding/ranking

Grounding examples should connect language to world entities.

Example:

```text
Language:
"Move that there."

Visual candidates:
1. blue mug
2. red book
3. laptop

Gaze:
blue mug

Pointing:
blue mug

Destination candidates:
1. shelf
2. table

Gesture:
shelf

Preferred grounding:
move(blue_mug, shelf)
```

Train ranking, not direct physical control.

The final physical action must still pass deterministic validation/governance.

---

# 15. Phase 10 — multimodal training

Only begin after perception → world model → identity → memory integration is stable.

Training inputs can include:

```text
image/frame embeddings
object identities
person identities
spatial relations
current conversation
memory summaries
```

Training tasks:

```text
person-grounded dialogue
object-grounded dialogue
scene-grounded response
spatial reference
visual follow-up
multimodal clarification
```

Example:

```text
Vision:
Vano holding unknown black device.

Memory:
No known matching device.

Conversation:
No active device topic.

Preferred act:
ASK

Response:
"What's that?"
```

Do not train the model to claim an object is recognized when the recognition subsystem has not established that identity.

---

# 16. Phase 11 — train proactive behavior

Use historical interaction traces to construct initiative decisions.

Example:

```text
State:
user present
known person
object moved
object relevance = 0.75
interruption cost = 0.1
recent proactive speech = 30 seconds ago

Correct decision:
SILENCE
```

Another:

```text
State:
user present
known person
important task completed
user available
last proactive speech = 10 minutes ago

Correct decision:
INFORM
```

Another:

```text
State:
new person enters
identity confirmed
person facing Novi
social opportunity high

Correct decision:
GREETING
```

The model learns the distinction between **interesting** and **worth saying**.

---

# 17. Phase 12 — learn user-specific preferences

Preferences should normally live in memory, not model weights.

Examples:

```text
preferred verbosity = short
technical detail for Novi discussions = high
unwanted repeated explanations = true
preferred interaction style = conversational
```

The learned model should receive these preferences as context.

Do not fine-tune a global model for one user's temporary preference.

---

# 18. Phase 13 — teacher/evaluator model

Use `qwen3.8:27b` as an optional local teacher/evaluator for difficult examples.

Teacher tasks:

```text
rank candidate responses
identify unsupported claims
score naturalness
score grounding
identify repetition
propose better dialogue act
find missing memory context
```

The teacher must not be treated as ground truth. Human review remains required for important training data.

Example evaluator output:

```json
{
  "grounding": 0.98,
  "naturalness": 0.91,
  "context_use": 0.94,
  "verbosity": 0.89,
  "unsupported_claim": 0.01,
  "overall": 0.93
}
```

---

# 19. Phase 14 — evaluation before deployment

Every candidate model must pass a fixed evaluation suite.

## Naturalness

Measure:

```text
human preference
assistant-style phrase rate
repetition rate
unnecessary verbosity
context continuity
```

## Grounding

```text
object grounding accuracy
person grounding accuracy
reference accuracy
false grounding rate
```

## Memory

```text
retrieval precision
retrieval recall
contradiction handling
cross-session continuity
```

## Initiative

```text
appropriate initiative
unnecessary initiative
missed initiative
duplicate initiative
interruption rate
```

## Safety

```text
unsupported claim rate
unsafe action proposal rate
ambiguous-action execution rate
identity false-positive rate
```

---

# 20. Required benchmark scenarios

Create a fixed benchmark with at least:

```text
01 simple greeting
02 casual conversation
03 long-context conversation
04 topic continuation
05 memory recall
06 irrelevant memory distraction
07 contradictory memory
08 ambiguous object reference
09 ambiguous person reference
10 unknown person
11 known person
12 new object
13 moved object
14 disappeared object
15 user interruption
16 Novi interruption attempt
17 correction
18 misunderstanding
19 proactive greeting
20 proactive observation
21 proactive silence
22 task completion
23 unexpected event
24 multi-person conversation
25 cross-modal voice+vision
26 low-confidence recognition
27 safety-critical event
28 noisy ASR
29 repeated event
30 conversation resume after interruption
```

Models must be compared against the same benchmark every time.

---

# 21. Phase 15 — shadow deployment

Never replace the production model immediately.

Run:

```text
production model
       │
       ├── response actually used
       │
       └── candidate model runs in shadow
                         │
                         ▼
                    comparison
```

Compare:

```text
latency
naturalness
grounding
memory usage
initiative
safety
user outcome
```

Candidate must beat or match the baseline without violating safety thresholds.

---

# 22. Phase 16 — model registry

Create a manifest for every adapter:

```yaml
model_id: novi-qwen3-8b-dialogue-v1
base_model: qwen3:8b
adapter_type: lora
training_dataset: dialogue-v1
training_commit: <git-sha>
training_config: sft-v3
created_at: <timestamp>
evaluation_suite: social-v1
metrics:
  naturalness: 0.91
  grounding: 0.97
  memory: 0.92
  initiative: 0.88
  safety: 0.995
status: candidate
```

Never deploy an unnamed checkpoint.

---

# 23. Phase 17 — rollback

Every deployment must support:

```text
current model
previous model
known-good baseline
```

Rollback triggers:

```text
safety regression
identity hallucination
memory hallucination
major naturalness regression
latency regression
initiative spam
```

Rollback must not require retraining.

---

# 24. Phase 18 — continuous learning loop

The eventual production loop:

```text
Novi interaction
      ↓
structured trace
      ↓
outcome
      ↓
quality filter
      ↓
curation
      ↓
training dataset
      ↓
SFT / DPO / ranking training
      ↓
evaluation
      ↓
shadow deployment
      ↓
human approval
      ↓
model registry
      ↓
controlled deployment
      ↓
more interactions
```

Never automatically train and deploy from raw robot experience.

---

# 25. Phase 19 — learning from corrections

Explicit user corrections are high-value data.

Example:

```text
Novi:
"You mean the red bottle?"

Vano:
"No, the blue one."
```

Record:

```text
original_grounding = red bottle
correct_grounding = blue bottle
correction_source = explicit user correction
```

Use this for:

```text
future grounding ranking
memory retrieval
conversation repair
policy evaluation
```

Do not blindly modify global behavior from one correction.

---

# 26. Phase 20 — learning from successful silence

Silence must also become training data.

Example:

```text
Event:
chair moved

Novi:
SILENCE

User:
continues working

Outcome:
positive
```

This prevents training from creating a robot that speaks constantly.

---

# 27. Phase 21 — learning from failed initiative

Example:

```text
Novi:
"Your mug moved."

User:
"Yeah, I moved it."
```

If the event was unimportant and interruption was undesirable, mark it as weak/negative initiative.

But do not blindly label every unneeded comment as a failure. The outcome must consider:

```text
user response
context
interruptibility
social opportunity
importance
```

---

# 28. Phase 22 — avoid catastrophic forgetting

Maintain a permanent regression set containing:

```text
core natural dialogue
identity uncertainty
memory grounding
safety behavior
silence behavior
reference resolution
repair
proactive behavior
```

Every new model must pass both:

```text
new-data performance
+
old-regression performance
```

If new training improves technical conversations but causes greetings to become robotic, reject the checkpoint.

---

# 29. Phase 23 — model/data version compatibility

A model must declare which context schema it expects.

Example:

```yaml
context_schema: 3
memory_schema: 5
world_schema: 4
dialogue_schema: 3
```

The runtime must refuse incompatible combinations or apply an explicit migration.

---

# 30. Phase 24 — latency and resource constraints

Training improvements are irrelevant if the robot cannot respond within acceptable interaction latency.

Track:

```text
model load time
first-token latency
tokens/sec
memory retrieval latency
context assembly latency
TTS latency
end-to-end turn latency
GPU/RAM usage
```

The router should use the smallest model that can satisfy the task.

Target architecture:

```text
qwen3:4b
  → fast/simple turns

qwen3:8b + Novi adapter
  → normal conversation

qwen3.8:27b
  → complex cognition / teacher / difficult turns
```

---

# 31. Phase 25 — training infrastructure

Initial local workflow:

```text
dataset generation
 → validation
 → training
 → evaluation
 → adapter artifact
 → model manifest
```

Use deterministic configuration files and commit every training configuration.

Record:

```text
base model identifier
training code commit
dataset version
hyperparameters
hardware
random seed
training duration
checkpoint
metrics
```

The exact training framework can be selected during implementation after validating Novi's runtime environment and available hardware. Do not hard-code a framework dependency into the architecture plan before that audit.

---

# 32. Phase 26 — first training experiment

The first experiment should be intentionally small.

Dataset:

```text
500–2,000 curated dialogue examples
```

Tasks:

```text
natural phrasing
context continuation
clarification
repair
memory-grounded answer
appropriate silence
```

Model:

```text
qwen3:8b
```

Method:

```text
LoRA SFT
```

Evaluation:

```text
baseline qwen3:8b
vs
qwen3:8b + Novi LoRA
```

Do not deploy based on training loss alone.

---

# 33. Second experiment — preference optimization

After SFT improves naturalness:

```text
1,000+ preference pairs
```

Categories:

```text
naturalness
brevity
context
memory
clarification
initiative
repair
```

Compare:

```text
base
SFT
SFT+DPO
```

Only retain improvements that survive the full regression suite.

---

# 34. Third experiment — retrieval model

Do not immediately fine-tune the language model for memory retrieval.

Build a small independent reranker first.

```text
candidate retrieval
 → learned ranking
 → top memories
 → LLM
```

This is cheaper, more interpretable and easier to replace.

---

# 35. Fourth experiment — dialogue policy model

Start with:

```text
candidate policy scorer
```

rather than direct autonomous control.

```text
state
 → deterministic candidate generation
 → learned ranking
 → deterministic safety/cooldown validation
 → action
```

This allows learning to improve initiative without making behavior unconstrained.

---

# 36. Fifth experiment — multimodal dialogue

Only after the visual pipeline is reliable.

Training data:

```text
image/visual evidence
+
world entities
+
conversation
+
memory
→
communicative act + response
```

Evaluation must explicitly measure hallucinated visual claims.

---

# 37. Human evaluation protocol

Every major model version should have human evaluation.

Reviewers score 1–5:

```text
naturalness
context awareness
memory appropriateness
grounding
social timing
verbosity
uncertainty
coherence
```

Include pairwise comparisons:

```text
Which response feels more natural?
A or B
```

Pairwise preference data becomes future DPO data after quality review.

---

# 38. Automatic anti-hallucination checks

Before a response is spoken, validate claims where possible against the context packet.

Flag:

```text
unknown person claimed as known
unknown object claimed as known
memory not retrieved but referenced as remembered
location not present in world state
unsupported action completion
unsupported certainty
```

A flagged response should be regenerated, simplified or converted to an uncertainty/clarification response.

---

# 39. Training acceptance gates

## Gate T1 — naturalness

Fine-tuned model must outperform baseline in human preference on naturalness.

## Gate T2 — grounding

No statistically meaningful regression in person/object/reference grounding.

## Gate T3 — memory

No increase in false-memory claims.

## Gate T4 — initiative

Appropriate initiative increases without increasing unnecessary interruption beyond the defined threshold.

## Gate T5 — silence

The model preserves appropriate silence.

## Gate T6 — safety

No safety regression is acceptable for a model deployment.

## Gate T7 — latency

Model must fit the runtime latency budget for its assigned routing tier.

## Gate T8 — regression

All existing Novi brain/voice/autonomy tests remain green.

---

# 40. Implementation sequence

Implement in exactly this order:

```text
01 audit existing training/data infrastructure
02 define training schemas
03 add structured interaction trace export
04 add privacy/redaction pipeline
05 add dataset validation
06 add dataset deduplication
07 add human annotation workflow
08 build initial curated dialogue dataset
09 establish baseline evaluation suite
10 train qwen3:8b Novi LoRA SFT
11 compare against baseline
12 deploy only to offline evaluation
13 create preference pairs
14 train preference model/DPO adapter
15 evaluate SFT vs SFT+DPO
16 build memory retrieval ranking dataset
17 train retrieval reranker
18 integrate retrieval reranker
19 build dialogue-policy dataset
20 train policy scorer
21 integrate policy scorer behind deterministic guardrails
22 collect multimodal grounding data
23 train multimodal grounding/ranking component
24 shadow-test integrated system
25 add model registry
26 add rollback
27 run real-robot evaluation
28 collect new traces
29 repeat controlled improvement cycle
```

---

# 41. Required repository deliverables

Implementation should ultimately add/extend:

```text
training/
  README.md
  configs/
  datasets/
  collection/
  training/
  evaluation/
  models/

novi/brain/
  language/
  interaction/
  memory/

novi/tests/
  training/
  evaluation/
```

The exact paths must be reconciled against the current repository before implementation to avoid duplicate structures.

---

# 42. Suggested commits

```text
training: define Novi training data contracts
brain: export structured interaction traces
training: add privacy and dataset sanitization
training: add dataset validation and deduplication
training: add dialogue annotation schema
training: add baseline social cognition benchmark
training: add qwen3-8b LoRA SFT pipeline
training: add SFT evaluation and model manifest
training: add preference dataset and DPO pipeline
brain: add learned memory retrieval reranker
brain: add learned dialogue policy scorer
brain: add multimodal grounding dataset pipeline
training: add shadow evaluation
training: add model registry and rollback
```

---

# 43. Final target architecture

```text
                     NOVI EXPERIENCE
                           │
                           ▼
                  Structured interaction
                           │
                           ▼
                     Data curation
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
            SFT           DPO        ranking models
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                   Novi learned layer
                           │
          ┌────────────────┼─────────────────┐
          ▼                ▼                 ▼
     verbalization    dialogue policy    retrieval/grounding
          │                │                 │
          └────────────────┼─────────────────┘
                           ▼
                    deterministic brain
                           │
             world / memory / identity
                           │
                           ▼
                        action
                           │
                           ▼
                      new experience
                           │
                           └──────────────→ learning
```

The model learns **how Novi behaves and communicates**.

The world model and memory store **what Novi currently knows and remembers**.

The governance layer decides **what Novi is allowed to do**.

This separation is mandatory.

---

# 44. Final definition of success

Novi is successfully trained when a new model version demonstrates measurable improvement in natural conversation while remaining grounded in the same explicit world, memory, identity and safety systems.

A successful interaction should therefore be explainable as:

```text
Novi saw X
→ recognized/uncertain about Y
→ remembered Z
→ understood the current situation
→ predicted/considered A
→ selected dialogue act B
→ learned model verbalized B naturally
→ user reacted
→ Novi evaluated outcome
→ memory/policy evidence updated
```

Not:

```text
User said something
→ giant prompt
→ LLM guessed a human-like answer
```

The long-term objective is a **Novi-specific learned social cognition layer** that continuously improves from high-quality interaction data while the explicit robot brain remains grounded, observable, testable, reversible and safe.

**End state:** training becomes an improvement loop around Novi's brain, not a replacement for Novi's brain.