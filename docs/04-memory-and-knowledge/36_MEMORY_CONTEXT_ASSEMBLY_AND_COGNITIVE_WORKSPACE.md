# 36 — Memory Context Assembly and Cognitive Workspace

## Status

**DESIGN — CRITICAL ARCHITECTURE / V1**

## High-Level Description

This document defines how Novi constructs the bounded, evidence-grounded cognitive context supplied to reasoning, planning, reflection and decision-making components.

Novi cannot place its entire memory, sensor history, world model, goals and internal state into a model context. Context must therefore be actively assembled from multiple authoritative sources according to the current task, attention state, safety requirements, uncertainty, recency, relevance, resource budget and information provenance.

The cognitive workspace is a **temporary, structured working set**, not a second permanent memory database.

## Detailed Description

The workspace sits between attention/retrieval and cognition:

```text
WORLD / SENSORS / INTERNAL STATE
              ↓
        ATTENTION + TRIAGE
              ↓
      MEMORY RETRIEVAL / QUERY
              ↓
       CONTEXT ASSEMBLY
              ↓
   ┌───────────────────────────┐
   │    COGNITIVE WORKSPACE    │
   │                           │
   │ task / goals              │
   │ current observations      │
   │ relevant memories         │
   │ world-state estimates     │
   │ predictions               │
   │ self-state                │
   │ constraints / policies    │
   │ uncertainty               │
   │ action history            │
   │ provenance                │
   └─────────────┬─────────────┘
                 ↓
          REASONING / PLANNING
                 ↓
             PROPOSALS
                 ↓
        VALIDATION / AUTHORITY
                 ↓
              ACTION
```

The workspace is where Novi decides **what the cognition layer needs to know now**, while the memory architecture decides what information exists and can be retrieved.

---

## 1. Core Principles

1. The workspace is bounded.
2. Context is assembled dynamically.
3. Safety-critical state has protected inclusion rules.
4. Current authoritative state outranks stale memories.
5. Provenance is preserved during assembly.
6. Retrieval does not imply truth.
7. Absence from context does not mean absence from memory.
8. The LLM cannot silently invent workspace facts.
9. The workspace is disposable unless explicitly persisted through an event/memory API.
10. Context construction must remain functional offline.
11. Context quality is evaluated independently from model quality.
12. Resource pressure can change optional context, but cannot silently remove mandatory safety state.

---

## 2. Cognitive Workspace vs Memory

These are different layers.

```text
MEMORY
Longer-lived retained information.

WORKSPACE
Information temporarily selected for current cognition.
```

A memory can be retrieved into a workspace without being modified.

A workspace item can influence a decision without becoming a memory.

A workspace can contain current runtime state that is not a memory at all.

---

## 3. Cognitive Workspace vs Model Context

The cognitive workspace is a structured internal object.

A model-specific prompt/context representation is a downstream serialization of that workspace.

```text
Cognitive Workspace
       ↓
policy-aware projection
       ↓
model-specific context
       ↓
LLM/VLM/reasoning model
```

This prevents the architecture from coupling memory semantics to one model's prompt format or context-window size.

---

## 4. Context Assembly Pipeline

Recommended pipeline:

```text
1. identify active task/goal
2. determine safety/authority requirements
3. obtain authoritative current state
4. collect active observations
5. retrieve relevant memories
6. retrieve relevant knowledge
7. retrieve spatial/temporal context
8. obtain self-model context
9. obtain predictions/expectations
10. include recent decision/action history
11. score candidates
12. remove duplicates/conflicts
13. resolve precedence
14. fit resource/token budget
15. validate provenance
16. serialize for the selected model
17. record context metadata
```

---

## 5. Workspace Envelope

A conceptual workspace should contain:

```text
workspace_id
created_at
expires_at / lifecycle
request_id
correlation_id
active_goal
active_intention
safety_state
current_state
observations
memories
knowledge
spatial_context
temporal_context
self_context
predictions
constraints
action_history
uncertainties
conflicts
provenance
resource_budget
model_requirements
assembly_policy_version
```

The exact schema belongs to the API/schema layer.

---

## 6. Mandatory Context

Some information may be mandatory for a class of decision.

Examples:

### Physical action

```text
safety state
current pose/state
relevant sensor health
authorization
active goal
environmental constraints
```

### Navigation

```text
current pose
local map
obstacles
localization confidence
goal
navigation constraints
battery/resource state where relevant
```

### Memory modification

```text
source evidence
provenance
memory policy
privacy classification
authorization
existing conflicting memory state
```

Mandatory context must not be dropped simply because a model context is crowded.

---

## 7. Optional Context

Optional information can compete for limited budget:

- older memories;
- secondary observations;
- historical examples;
- low-value metadata;
- broad world knowledge;
- redundant sensor descriptions.

Optional context is ranked and truncated according to policy.

---

## 8. Current State Precedence

For rapidly changing operational facts, authoritative current state should generally outrank historical memory.

Example:

```text
memory:
"battery was 82%"

current BMS:
31%

workspace:
31%
```

The old memory may remain useful historically but must not override the current BMS reading.

---

## 9. Provenance Preservation

Every retrieved item entering the workspace should retain enough metadata to answer:

- where it came from;
- when it was observed;
- when it was retrieved;
- how it was derived;
- confidence/uncertainty;
- source authority;
- memory/knowledge ID;
- event lineage where available.

The model may receive a simplified rendering, but the structured workspace retains provenance.

---

## 10. Evidence Classes

Context items should be classified, for example:

```text
AUTHORITATIVE_CURRENT_STATE
DIRECT_OBSERVATION
VERIFIED_KNOWLEDGE
SUPPORTED_MEMORY
PREDICTION
INFERENCE
USER_ASSERTION
MODEL_GENERATED_CANDIDATE
UNKNOWN
```

These classes must not be presented as equivalent facts.

---

## 11. Truth Boundary

Retrieval is not verification.

A highly similar memory can still be wrong, stale or superseded.

The context assembler should preserve evidence status and allow higher-authority sources to override lower-authority sources.

---

## 12. Conflict Representation

Conflicting information should not silently collapse into one statement.

Example:

```text
Memory A: door usually closed
Observation B: door currently open
Knowledge C: door sensor may be unreliable
```

Workspace:

```text
current observation → open
historical memory → usually closed
sensor reliability → uncertain
```

Cognition can then reason about the conflict.

---

## 13. Recency

Recency is useful but not sufficient.

A recent weak observation should not automatically outrank an authoritative state source.

A context score may combine:

```text
relevance
+ recency
+ source authority
+ confidence
+ task utility
+ novelty
+ predictive value
+ spatial relevance
+ temporal relevance
- redundancy
- contradiction risk
- cost
```

Weights are task-specific and must be evaluated empirically.

---

## 14. Goal Conditioning

Context assembly must be goal-aware.

For example, if Novi is navigating to the kitchen:

```text
high value:
local map
obstacles
current pose
recent kitchen observations
navigation constraints

low value:
old unrelated conversations
remote historical memories
unrelated objects
```

The same memory database can therefore produce very different workspaces for different tasks.

---

## 15. Multi-Goal Context

Novi may have several active goals.

The assembler must identify:

- primary goal;
- supporting goals;
- constraints;
- conflicting goals;
- deadlines;
- priority;
- authority.

Example:

```text
Primary: return home
Secondary: explore new area
Constraint: battery low
```

Battery/resource state can cause exploration context to be reduced or the exploration goal to be suspended.

---

## 16. Attention Integration

Document 35 determines what deserves attention.

Document 36 turns attention results into a structured workspace.

```text
Attention
  ↓
Candidate set
  ↓
Context assembly
  ↓
Budgeting
  ↓
Workspace
```

Attention therefore does not directly write a prompt.

---

## 17. Memory Retrieval Integration

Document 05 defines retrieval/ranking.

Context assembly consumes retrieval results but may rerank or filter them based on current task and authority.

```text
Memory retrieval
      ↓
Candidate memories
      ↓
Context policy
      ↓
Workspace
```

Retrieval and context assembly remain separate services/responsibilities.

---

## 18. Working Memory Integration

Document 14 defines working memory.

The cognitive workspace is the task-specific projection of working memory plus current state, retrieved evidence and constraints.

Working memory may persist across several reasoning cycles; an individual workspace may be shorter-lived.

---

## 19. Episodic Integration

Document 31 provides experience/episode retrieval.

The assembler may retrieve:

- current episode;
- previous similar episodes;
- first-time experiences;
- repeated patterns;
- relevant failures;
- successful strategies.

Older episodes should be included only when they improve the current decision.

---

## 20. Self-Model Integration

Document 32 provides authoritative self-context.

Examples:

```text
current capability
sensor health
battery
thermal state
current pose
software/model version
known limitations
```

This information should be dynamically refreshed rather than relying solely on old self-memories.

---

## 21. Goal Integration

Document 33 provides active goals, intentions and commitments.

The workspace should include enough information to answer:

```text
What am I trying to accomplish?
Why?
What constraints apply?
What has already been attempted?
What remains?
What changed?
```

---

## 22. Predictive Model Integration

Document 34 provides expectations and prediction errors.

The workspace can include:

```text
current expectation
confidence
predicted outcome
recent prediction error
candidate explanation
```

This is particularly useful for adaptive planning.

---

## 23. Spatial Context

For spatial tasks, the workspace may include:

```text
current pose
local map region
nearby objects
known landmarks
previous visits
route history
spatial uncertainty
coordinate-frame metadata
```

The assembler should prefer local relevant geometry over dumping the entire map into model context.

---

## 24. Temporal Context

Temporal context may include:

- current time;
- task duration;
- recent event sequence;
- previous visit time;
- recurring schedule;
- temporal validity of memories;
- time since observation.

Temporal uncertainty must remain explicit.

---

## 25. Sensor Context

Raw sensor streams should not normally be serialized into a language-model context.

Instead, cognition receives structured observations or selected multimodal representations.

```text
camera stream
   ↓
perception
   ↓
objects / scene / uncertainty
   ↓
workspace
```

When direct visual reasoning is needed, selected frames can be attached through a controlled multimodal interface.

---

## 26. Multimodal Context

The workspace may contain:

- text;
- images;
- audio features/transcripts;
- spatial geometry;
- thermal observations;
- object tracks;
- maps;
- structured sensor state.

Each modality needs provenance and timestamp metadata.

The assembler should avoid redundant representations that consume budget without adding information.

---

## 27. Audio Context

For voice interaction, context may include:

```text
transcript
speaker identity confidence
source direction
acoustic confidence
recent conversational turns
relevant user preference
```

Speaker identity should never be treated as authenticated authority solely because a voice classifier produced a match.

---

## 28. Thermal Context

Thermal observations may become context when relevant to:

- human/object safety;
- environmental exploration;
- hardware thermal state;
- unusual heat/cold detection;
- navigation constraints.

Internal hardware temperature and external thermal observations must remain distinct.

---

## 29. Context Compression

When the workspace exceeds its budget, compression may occur in stages:

```text
remove redundancy
      ↓
remove low-value optional items
      ↓
replace detailed history with validated summaries
      ↓
reduce multimodal resolution where safe
      ↓
retain mandatory evidence/state
```

Compression must not transform uncertainty into certainty.

---

## 30. Summarization Safety

A summary is a derived representation.

It must retain:

- source references;
- time range;
- uncertainty;
- important contradictions;
- relevant exceptions.

Example:

Bad:

```text
"The room is always empty."
```

Better:

```text
"No person was detected during the last 15 observations between 14:00 and 16:00; confidence varies by camera coverage."
```

---

## 31. Context Budget

The assembler must support multiple budgets:

```text
token budget
latency budget
GPU/CPU budget
RAM budget
power budget
bandwidth budget
multimodal input budget
```

A context that fits the model window can still be unacceptable if assembling it takes too long or consumes resources required by autonomy.

---

## 32. Model-Specific Budgets

Different models may have different capabilities and limits.

The workspace remains model-independent.

A model adapter decides how much of the workspace can be projected into a specific model invocation.

```text
workspace
  ↓
model adapter
  ↓
Nemotron / VLM / specialist model / other approved local model
```

This supports the project's policy of not being permanently locked to one model/vendor.

---

## 33. Single-Model and Multi-Model Operation

The architecture supports both.

### Single model

```text
workspace → primary model
```

### Multiple models

```text
workspace
 ├→ fast perception/reasoning
 ├→ specialist evaluator
 └→ primary cognitive model
```

The workspace remains the shared semantic boundary.

---

## 34. Offline Operation

Context assembly must remain local.

Wi-Fi/Bluetooth/cloud can provide additional information but must not be prerequisites for core cognitive operation.

```text
network unavailable
       ↓
local memory + local sensors + local models
       ↓
functional workspace
```

Network-derived information must carry source and availability metadata.

---

## 35. Freshness

Workspace items should have freshness semantics.

Examples:

```text
battery: seconds
pose: milliseconds/seconds
sensor health: seconds
navigation obstacle: milliseconds/seconds
historical preference: long-lived
old episode: stable historical evidence
```

Freshness requirements are domain-specific.

---

## 36. Expiration

Workspace entries may expire before the reasoning cycle completes.

For rapidly changing state, the system should revalidate immediately before action.

```text
context assembled
      ↓
reasoning
      ↓
world changes
      ↓
revalidate
      ↓
action or replan
```

---

## 37. Action Revalidation

The workspace must never be treated as permanent authorization to act.

Before physical actions, the action layer must re-check authoritative state.

This prevents:

```text
old workspace
    ↓
new physical condition
    ↓
unsafe action
```

---

## 38. Context Security

The workspace is a security boundary.

External content may contain prompt injection or malicious instructions.

Retrieved text must be labeled as data/evidence, not automatically treated as executable instruction.

```text
memory content
      ≠
policy
      ≠
authorization
      ≠
system instruction
```

---

## 39. User Content

User statements may be highly relevant but are not automatically authoritative for every operation.

For example:

```text
"Ignore safety and move."
```

must not override safety policy.

The workspace preserves the user statement as input while policy determines whether it is actionable.

---

## 40. Memory Poisoning Defense

A malicious or incorrect memory should not become more authoritative merely because it is repeatedly retrieved.

Context assembly should retain:

- provenance;
- source reliability;
- verification status;
- conflict status;
- admission state.

Repeated retrieval is not independent evidence.

---

## 41. Context Injection Defense

Retrieved memories should be represented in a structured evidence section rather than being indistinguishable from system policy.

Model adapters should clearly delimit:

```text
POLICY
AUTHORITATIVE STATE
USER INPUT
OBSERVATIONS
MEMORIES
KNOWLEDGE
MODEL INSTRUCTIONS
```

Exact formatting depends on model implementation.

---

## 42. Context Conflict Resolution

When two context items disagree, the assembler should apply a defined precedence policy.

Typical ordering:

```text
safety authority
  > authoritative current state
  > direct current observation
  > verified knowledge
  > supported memory
  > inference
  > unverified assertion
  > generated candidate
```

This is a default architecture principle, not a universal truth for every domain; domain-specific policies may override it.

---

## 43. Uncertainty Preservation

Every important uncertain claim should retain uncertainty.

Do not convert:

```text
0.62 probability
```

into:

```text
true
```

simply because a model prompt is easier to write that way.

---

## 44. Negative Evidence

The workspace may include explicit negative evidence.

Examples:

```text
no person detected
no GNSS fix
no obstacle detected in scanned region
sensor unavailable
```

Negative evidence must include scope and confidence.

"Not detected" does not mean "does not exist."

---

## 45. Context Handoff

If cognition delegates work to another model/agent, it should pass a controlled context projection rather than the entire workspace by default.

```text
workspace
   ↓
subtask context
   ↓
specialist
   ↓
result + provenance
```

This reduces context leakage and resource waste.

---

## 46. Context and Multi-Agent Operation

If Novi later uses multiple processes/agents, each should receive the minimum context required for its responsibility.

Examples:

```text
navigation agent → navigation context
memory agent → memory context
perception agent → perception context
reflection agent → experience context
```

A shared workspace can be represented through controlled projections, not unrestricted database access.

---

## 47. Context Persistence

The workspace itself should normally be ephemeral.

If a reasoning cycle produces something worth remembering, cognition must explicitly submit it through the memory APIs.

```text
workspace insight
      ↓
memory candidate
      ↓
admission
      ↓
durable memory
```

This prevents every thought from becoming permanent memory.

---

## 48. Context Logging

For important decisions, Novi should record metadata about context assembly without necessarily storing the complete sensitive prompt forever.

Useful metadata:

- workspace ID;
- assembly policy version;
- model version;
- retrieved memory IDs;
- event IDs;
- state snapshot ID;
- context size;
- truncation/compression decisions;
- decision correlation ID.

Privacy policy determines retention.

---

## 49. Reproducibility

For important decisions, Novi should be able to reconstruct the relevant context as closely as permitted.

This requires retaining or reconstructing:

```text
source events
memory versions
knowledge versions
model version
policy version
state snapshot
retrieval configuration
assembly policy
```

Exact reproduction may not be possible for all stochastic models; the architecture should distinguish reconstruction from deterministic replay.

---

## 50. Context Versioning

Every workspace should reference:

```text
assembly_policy_version
schema_version
model_adapter_version
```

This allows later analysis of whether behavior changed because of memory, retrieval, assembly or model changes.

---

## 51. Resource-Aware Assembly

The resource governance layer from document 28 can constrain assembly.

Under normal conditions:

```text
large context
rich multimodal evidence
more historical retrieval
```

Under pressure:

```text
smaller context
higher relevance threshold
less historical retrieval
lower image/audio resolution
fewer optional candidates
```

Mandatory safety context remains protected.

---

## 52. Thermal-Aware Assembly

If Novi is thermally constrained, optional cognitive work may be reduced.

For example:

```text
thermal pressure
      ↓
reduce retrospective retrieval
reduce large multimodal context
reduce speculative candidates
retain current safety/navigation state
```

This connects the memory architecture directly to the physical hardware constraints.

---

## 53. Attention Feedback

The workspace should feed outcomes back into attention evaluation.

If repeatedly selected context items never improve decisions, their ranking may be reduced.

If an apparently low-ranked signal repeatedly predicts important events, its relevance may increase.

This must happen through measured learning/evaluation rather than uncontrolled self-modification.

---

## 54. Context Quality Metrics

Measure at least:

- context retrieval precision;
- context recall for required evidence;
- stale-context rate;
- contradiction rate;
- hallucination rate;
- context truncation rate;
- token efficiency;
- decision latency;
- action-revalidation failures;
- memory reuse;
- unnecessary retrieval;
- missing-critical-context incidents;
- resource cost.

---

## 55. Failure Modes

The architecture must explicitly handle:

- empty retrieval;
- stale state;
- conflicting memories;
- missing provenance;
- corrupted memory;
- context overflow;
- model input failure;
- sensor latency;
- resource exhaustion;
- storage failure;
- offline mode;
- duplicate information;
- prompt injection;
- malicious memory content;
- incorrect summaries;
- model hallucination;
- action-state divergence.

---

## 56. Empty Context

Novi must remain functional when retrieval finds nothing useful.

```text
no relevant memory
      ↓
use current observations + authoritative state
      ↓
reason with explicit uncertainty
```

"I don't know" is a valid cognitive state.

---

## 57. Missing Sensor Context

When a required sensor is unavailable, the workspace should explicitly state the limitation.

Example:

```text
left_camera = unavailable
visual confidence = reduced
```

The model should not receive a silent omission that makes it appear the sensor was simply not needed.

---

## 58. Context Freshness Before Physical Action

For safety-relevant actions:

```text
retrieve
 ↓
assemble
 ↓
reason
 ↓
re-check authoritative state
 ↓
validate action
 ↓
execute
```

The workspace is advisory input to action, not a replacement for real-time control state.

---

## 59. Separation from Control

The cognitive workspace must never directly control motors.

```text
workspace
 ↓
cognitive proposal
 ↓
autonomy/action policy
 ↓
safety validation
 ↓
controller
 ↓
actuator
```

Low-level control remains deterministic/real-time where required.

---

## 60. NVIDIA / ROS / NITROS Integration

Novi should use existing robotics infrastructure where it is appropriate rather than recreating transport and perception systems.

NVIDIA documents Isaac ROS as built on ROS 2 and provides hardware-accelerated packages and NITROS pipelines for GPU-aware processing. NITROS is particularly relevant when high-bandwidth perception data must move through the ROS graph while reducing unnecessary CPU-memory copies. citeturn0search4turn0search5

For Novi, the architectural implication is:

```text
sensor/perception graph
        ↓
ROS 2 / Isaac ROS / NITROS where beneficial
        ↓
semantic observations
        ↓
context assembler
        ↓
cognitive workspace
```

The cognitive workspace should consume semantic outputs and selected multimodal artifacts rather than forcing the language model to process raw high-rate sensor transport.

---

## 61. NVIDIA ReMEmbR Reference

NVIDIA's open-source ReMEmbR work is a useful reference because it demonstrates an on-device robotics architecture combining VLM-generated semantic memory, spatial information, vector retrieval and an LLM agent for long-horizon reasoning. It explicitly addresses large contexts and spatial memory on a robot. citeturn0search3

Novi should adopt the underlying architectural lesson—**retrieve and assemble relevant long-horizon context instead of placing the complete history into a model**—without assuming ReMEmbR's exact implementation is the final Novi implementation.

---

## 62. Model Independence

The workspace must not depend on a specific foundation model.

A fast local model may receive a compact workspace.

A larger reasoning model may receive a richer workspace.

A specialist VLM may receive visual context only.

This preserves the project's ability to choose between NVIDIA, Hugging Face, PyTorch, TensorFlow, ONNX Runtime or other open-source local components when they are better suited to a task.

---

## 63. Cognitive Workspace Lifecycle

```text
CREATED
   ↓
POPULATING
   ↓
VALIDATING
   ↓
READY
   ↓
CONSUMED
   ↓
EXPIRED
```

A workspace can also enter:

```text
INVALIDATED
REBUILD_REQUIRED
```

when authoritative state changes materially.

---

## 64. Rebuild Triggers

Rebuild or revalidation may be triggered by:

- new safety state;
- significant pose change;
- new obstacle;
- sensor failure;
- goal change;
- user interruption;
- major prediction error;
- thermal/resource state change;
- memory conflict;
- authorization change.

---

## 65. Context Caching

Context components may be cached when safe.

However, volatile state must have strict freshness requirements.

Good cache candidates:

- stable historical knowledge;
- validated place descriptions;
- long-term preferences.

Poor cache candidates:

- current battery;
- immediate obstacle state;
- motor state;
- safety state.

---

## 66. Context Deduplication

The assembler should avoid sending the same information repeatedly in different forms.

Example:

```text
memory: "Kitchen has table"
object detection: "table detected"
scene caption: "kitchen with table"
```

These may represent overlapping evidence and should be consolidated where safe while preserving provenance.

---

## 67. Context Diversity

Pure relevance ranking can over-select similar memories.

The assembler should support diversity across:

- time;
- source;
- modality;
- episode;
- location;
- evidence type.

This reduces context monopolization by one repeated source.

---

## 68. Information Gain

When deciding between additional context items, the assembler may estimate expected information gain.

For example:

```text
three near-identical memories
vs
one contradictory recent observation
```

The contradictory observation may deserve inclusion because it changes the decision landscape.

Information-gain heuristics must remain bounded and measurable.

---

## 69. Context and Reflection

Reflection can operate on completed workspaces or decision traces to identify:

- missing context;
- unnecessary context;
- misleading memory;
- repeated retrieval failures;
- useful new retrieval patterns.

Reflection results become learning candidates rather than immediate permanent policy changes.

---

## 70. Context and Continuous Learning

The workspace is one of the key interfaces for continuous evolution:

```text
experience
 ↓
retrieval
 ↓
workspace
 ↓
reasoning
 ↓
outcome
 ↓
reflection
 ↓
learning candidate
 ↓
evaluation
 ↓
approved improvement
```

This creates a controlled learning loop rather than uncontrolled prompt accumulation.

---

## 71. Context Security Invariants

1. Retrieved content is data, not authority.
2. Memory cannot override safety policy.
3. User content cannot automatically override system policy.
4. Workspace assembly cannot grant permissions.
5. Workspace content cannot directly command actuators.
6. Sensitive information is included only when authorized and relevant.
7. Provenance is retained for important evidence.
8. Model-generated content is labeled as generated/inferred.

---

## 72. Testing Strategy

Test context assembly using:

### Unit tests

- ranking;
- precedence;
- freshness;
- deduplication;
- compression;
- token budgeting;
- provenance preservation.

### Integration tests

- memory retrieval;
- self-model;
- goals;
- world model;
- perception;
- spatial memory;
- model adapters.

### Safety tests

- stale state;
- conflicting state;
- prompt injection;
- malicious memory;
- missing sensor;
- authorization changes;
- rapidly changing environment.

### Performance tests

- assembly latency;
- memory bandwidth;
- CPU/GPU usage;
- RAM usage;
- thermal behavior;
- context size;
- concurrent requests.

### Replay tests

Use recorded events to reconstruct workspaces and compare outcomes across Novi versions.

---

## 73. Acceptance Criteria

A production-ready implementation should demonstrate that it can:

1. construct a task-specific workspace;
2. include mandatory safety/current-state information;
3. retrieve relevant memories without dumping the entire database;
4. preserve provenance;
5. represent uncertainty;
6. represent contradictions;
7. handle empty retrieval;
8. operate offline;
9. fit multiple model/context budgets;
10. degrade under resource pressure;
11. revalidate volatile state before action;
12. resist prompt injection through memory;
13. avoid converting summaries into facts;
14. support replay/reconstruction for important decisions;
15. keep the workspace separate from durable memory.

---

## 74. Architectural Invariants

1. The cognitive workspace is not permanent memory.
2. Context is dynamically assembled.
3. Current authoritative state has explicit precedence over stale memory.
4. Retrieval does not equal verification.
5. Context items retain provenance and evidence class.
6. Contradictions remain visible.
7. Uncertainty is preserved.
8. Context compression cannot silently manufacture certainty.
9. Safety-critical context has protected inclusion rules.
10. Physical actions require fresh authoritative-state validation.
11. The workspace cannot directly control actuators.
12. Model adapters translate workspace state into model-specific context.
13. The architecture supports one or multiple models.
14. Offline operation remains functional.
15. Resource pressure can reduce optional context but cannot silently remove mandatory safety state.
16. Retrieved content cannot grant authority or permissions.
17. Workspace-derived insights must pass memory admission before becoming durable memory.
18. Important context assembly decisions are traceable.
19. Derived summaries remain linked to source evidence.
20. The architecture remains vendor-independent even when NVIDIA acceleration is used.

---

## 75. Reference Architecture

```text
                    ┌──────────────────────────┐
                    │      Physical World      │
                    └────────────┬─────────────┘
                                 ↓
                    ┌──────────────────────────┐
                    │ Perception / State Est.  │
                    └────────────┬─────────────┘
                                 ↓
        ┌────────────────────────┴────────────────────────┐
        │                                                 │
        ▼                                                 ▼
┌──────────────────┐                              ┌──────────────────┐
│ Attention /       │                              │ Authoritative    │
│ Relevance         │                              │ Runtime State    │
└────────┬─────────┘                              └────────┬─────────┘
         │                                                 │
         ▼                                                 │
┌──────────────────┐                                       │
│ Memory Retrieval │                                       │
└────────┬─────────┘                                       │
         │                                                 │
         └──────────────────┬──────────────────────────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Context Assembler    │
                 │                      │
                 │ goals                │
                 │ memories             │
                 │ knowledge            │
                 │ observations         │
                 │ self-state           │
                 │ predictions          │
                 │ spatial context      │
                 │ constraints          │
                 │ uncertainty          │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Cognitive Workspace  │
                 └──────────┬───────────┘
                            ↓
                 ┌──────────────────────┐
                 │ Model Adapter        │
                 └──────────┬───────────┘
                            ↓
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           Fast Model     VLM/Model    Reasoning Model
              │             │             │
              └─────────────┼─────────────┘
                            ↓
                     Cognitive Proposal
                            ↓
                 Policy / Autonomy / Safety
                            ↓
                         Action
                            ↓
                         Outcome
                            ↓
                       Event Model
                            ↓
                  Learning / Memory Update
```

## 76. Final Principle

> **Novi should not ask its cognitive model to remember the world. Novi should maintain the world model and deliberately bring the right evidence into a bounded cognitive workspace at the moment it is needed.**

The cognitive workspace is therefore the controlled bridge between Novi's continuously evolving memory and its finite computational attention. It allows Novi to have long-lived experience without requiring any single model invocation to carry the entirety of that experience.

## References and Cross-Validation

The architecture was cross-checked against the following classes of sources:

- NVIDIA Isaac ROS and NITROS documentation/materials for ROS 2 integration, GPU-aware perception pipelines and efficient data movement. NVIDIA describes Isaac ROS as built on ROS 2 and NITROS as its type-adaptation/negotiation and accelerated processing approach. NVIDIA also documents reducing unnecessary CPU-memory copies in accelerated ROS graphs. 
- NVIDIA ReMEmbR for an on-device reference architecture combining semantic memory, spatial memory, vector retrieval and LLM reasoning over long-horizon robot experience.
- Recent embodied-agent research examining LLM-centered robot cognition with working/episodic memory and execution recovery.
- Recent cognitive-workspace research exploring active, task-driven context management rather than passive retrieval alone.

These references are architectural inputs, not requirements to copy a specific implementation. Novi remains open-source-first, local-first and vendor-independent.
