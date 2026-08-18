# 21 — Cognition Implementation Specification

**Status:** IN PROGRESS — P0 / critical
**Authority:** `docs/03-cognition/`
**Depends on:** System Architecture, Brain Implementation Blueprint, Soul Constitution, Cognition Architecture, Cognitive APIs & Contracts, World Model, Model Routing
**Implementation target:** Mac-first; later simulation and NVIDIA edge targets

---

## 1. Purpose

This document converts the existing Cognition domain from a conceptual architecture into an implementation-ready specification.

It does not replace the existing Cognition documents. It is the implementation-layer authority that connects them to executable components, contracts, state, runtime behavior, resource budgets, failure modes and validation.

The goal is that the Mac Brain can instantiate Cognition without inventing missing semantics.

The implementation must preserve the established ownership boundary:

```text
Soul
  → identity, personality, values, motivations, affect semantics, social disposition

Cognition
  → interpretation, understanding, world model, situation model,
    reasoning, prediction, uncertainty and social understanding

Memory
  → durable experience and knowledge

Autonomy
  → goals, priorities, planning and action selection

Brain
  → runtime orchestration and execution

Policy / Safety
  → authorization of consequential actions
```

---

## 2. Implementation principles

### 2.1 Cognition is not one neural network

Novi Cognition is a coordinated system containing deterministic state, structured representations, learned models and reasoning components.

```text
Sensors / external events
        ↓
Evidence
        ↓
Multimodal interpretation
        ↓
World Model
        ↓
Situation Model
        ↓
Attention/context
        ↓
Reasoning / prediction
        ↓
Cognitive state
        ↓
Soul / Memory / Autonomy interfaces
```

Neural models are used where learned representation or inference provides material value. They do not become the sole source of truth for identity, permissions, safety or durable state.

### 2.2 Structured state is authoritative where determinism matters

Use explicit schemas and deterministic logic for:

- timestamps;
- entity identifiers;
- confidence values;
- provenance;
- permissions;
- relationship evidence;
- state transitions;
- lifecycle state;
- action requests;
- safety-relevant facts;
- configuration;
- versioning.

### 2.3 Learned outputs are evidence, not unquestioned truth

Model outputs must carry:

- source/model identifier;
- model version;
- timestamp;
- confidence or uncertainty where available;
- input references;
- provenance;
- validity interval;
- processing stage.

### 2.4 Cognition must degrade gracefully

Missing or degraded perception, speech, memory or model services must result in explicit uncertainty or reduced capability rather than fabricated certainty.

### 2.5 Vendor neutrality at the semantic layer

NVIDIA technologies may be used as optimized implementations, but Cognition contracts must not require a specific vendor runtime.

The architecture must remain portable across Mac development, simulation and future edge deployment.

---

## 3. Runtime component model

The initial Cognition runtime should be decomposed into these logical components:

```text
                    COGNITION RUNTIME
                           │
       ┌───────────────────┼───────────────────┐
       ↓                   ↓                   ↓
 Evidence Intake     Context Builder      Model Router
       │                   │                   │
       ↓                   ↓                   ↓
 Multimodal Fusion    Situation Model     Reasoning Engine
       │                   │                   │
       └──────────────┬────┴───────────────────┘
                      ↓
                  World Model
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
       Predictive   Social      Uncertainty
       Inference  Understanding   Engine
          │           │           │
          └───────────┼───────────┘
                      ↓
              Cognitive State
                 /    |    \
                ↓     ↓     ↓
             Soul  Memory  Autonomy
```

These are logical boundaries. They may initially run in one process on the Mac and later become separate processes or services if profiling justifies it.

---

## 4. Evidence intake

### Responsibility

Convert raw or preprocessed external observations into canonical cognitive evidence.

### Inputs

Potential sources include:

- camera observations;
- depth observations;
- LiDAR observations;
- microphone/audio events;
- speech transcripts;
- speaker hypotheses;
- face/person hypotheses;
- pose/gesture hypotheses;
- object detections;
- robot state;
- navigation state;
- application events;
- user interaction;
- memory retrieval results;
- Brain/runtime events.

### Evidence contract

Every evidence object should contain at minimum:

```text
id
source
source_type
event_time
ingest_time
valid_from
valid_until
payload
confidence
provenance
model_reference
schema_version
correlation_id
```

Raw sensor data and interpreted evidence must remain distinguishable.

---

## 5. Multimodal evidence fusion

Fusion combines independent observations into coherent hypotheses.

Example:

```text
voice: “Novi”
        +
gaze toward Novi
        +
head orientation toward Novi
        +
speaker identity = Alice
        ↓
High-confidence address hypothesis
```

Fusion must preserve uncertainty when signals conflict.

Example:

```text
voice says “Novi”
        +
visual attention points elsewhere
        ↓
ambiguous address
```

Cognition should not force a binary decision when the evidence does not support one.

### Initial implementation

The Mac implementation should begin with deterministic evidence fusion and explicit weighted/confidence rules. Learned fusion models may be introduced only after a measurable benchmark demonstrates value.

---

## 6. World Model implementation

The World Model is the current structured representation of relevant entities and their state.

Core entity classes:

```text
Person
Object
Place
Robot
Event
Conversation
Action
Relationship
Goal-relevant state
Environment state
```

Each entity should support:

- stable identifier;
- attributes;
- observations;
- confidence;
- provenance;
- temporal validity;
- spatial information where applicable;
- relationships;
- last-seen/last-updated state;
- uncertainty;
- source references.

### World-state lifecycle

```text
observation
  ↓
interpretation
  ↓
entity resolution
  ↓
state update proposal
  ↓
consistency checks
  ↓
world-state commit
  ↓
new cognitive context
```

World Model state must not silently overwrite contradictory evidence. Conflicting observations remain traceable.

---

## 7. Situation Model

The Situation Model is a derived, task/context-specific view of the World Model.

Example:

```text
World Model:
Alice, Bob, Carol, kitchen, table, cups, conversation...

Situation Model:
Three people are talking to one another.
Novi is not currently addressed.
Alice is preparing coffee.
No urgent event is detected.
```

The Situation Model should contain:

- current context;
- active participants;
- likely addressee;
- ongoing activities;
- relevant recent events;
- salient objects;
- active uncertainty;
- temporal context;
- social context;
- current constraints;
- task-relevant hypotheses.

It should be derived rather than becoming an independent uncontrolled database.

---

## 8. Attention inputs

Cognition supplies evidence and context to Autonomy's attention system.

Relevant cognitive signals include:

- salience;
- novelty;
- relevance;
- urgency;
- confidence;
- social invitation probability;
- safety relevance;
- task relevance;
- unresolved uncertainty;
- relationship relevance.

Cognition does **not** make the final decision to interrupt or act. Autonomy owns that decision.

---

## 9. Social understanding

Cognition interprets social evidence such as:

- speaker identity;
- likely addressee;
- conversation membership;
- gaze/visual attention where available;
- body orientation;
- gestures;
- speech content;
- tone/prosody evidence;
- relationship evidence;
- group context;
- conversational turn state.

Output should be probabilistic where necessary:

```text
likely_addressee = Novi
confidence = 0.92
reason = name + gaze + turn-taking evidence
```

Cognition must not claim direct access to another person's private thoughts or subjective emotional state.

---

## 10. Identity and relationship interpretation

Soul owns Novi's identity and relationship behavior. Cognition owns interpretation of evidence about identity and relationships.

Examples:

```text
Cognition:
“Voice and face evidence are consistent with Alice.”

Cognition:
“Alice appears familiar based on stored relationship evidence.”

Soul:
“Familiar people receive different social behavior.”

Autonomy:
“Given the current context, do not interrupt.”
```

Identity hypotheses must carry confidence and provenance.

A low-confidence person match must not silently become a permanent identity fact.

---

## 11. Temporal reasoning

Cognition must represent:

- event order;
- duration;
- recency;
- intervals;
- temporal relationships;
- scheduled/future events;
- change over time;
- stale observations.

All temporal reasoning must use the canonical Novi time semantics defined by System Architecture.

Cognition must distinguish:

```text
event time
ingest time
processing time
memory time
wall-clock time
monotonic runtime time
simulation time
```

---

## 12. Causal reasoning

Causal claims require stronger evidence than correlation.

Cognition should distinguish:

```text
observed
inferred
hypothesized
causally supported
unknown
```

The system must not convert a model-generated explanation into a durable causal fact without the appropriate validation/provenance pathway.

---

## 13. Prediction

Prediction is used to anticipate likely future states, not to fabricate certainty.

Predictions must include:

- prediction target;
- horizon;
- confidence/uncertainty;
- source/model;
- timestamp;
- assumptions;
- expiration.

Expired predictions must not remain authoritative indefinitely.

---

## 14. Uncertainty model

Uncertainty is a first-class cognitive state.

The implementation must distinguish at least:

```text
known
probable
possible
ambiguous
unknown
contradictory
stale
unavailable
```

Confidence values must not be interpreted as universal probabilities unless the underlying model is calibrated accordingly.

The system should preserve both:

```text
belief
+
evidence supporting belief
```

This is required for correction and learning.

---

## 15. Provenance propagation

Cognitive outputs must retain provenance across transformations.

```text
sensor evidence
  ↓
model inference
  ↓
fusion
  ↓
world-state hypothesis
  ↓
situation model
  ↓
reasoning result
```

A downstream result must be traceable to the evidence and model versions that produced it.

This is essential for debugging hallucinations, incorrect identity recognition, social mistakes and model regressions.

---

## 16. Reasoning architecture

The initial reasoning stack should be hybrid:

```text
Deterministic / structured reasoning
            +
Symbolic/state operations
            +
Statistical models
            +
LLM/VLM reasoning where beneficial
```

Use structured reasoning for:

- state transitions;
- schema validation;
- temporal calculations;
- deterministic comparisons;
- permission facts;
- confidence propagation;
- consistency checks;
- routing constraints.

Use learned models for:

- semantic interpretation;
- language understanding;
- ambiguous multimodal interpretation;
- open-ended reasoning;
- summarization where appropriate;
- flexible hypothesis generation.

The LLM must not be the authoritative database, scheduler, safety controller or identity store.

---

## 17. Model router

Cognition already contains a model-selection concept; the implementation layer must make it executable.

The router should consider:

- task type;
- modality;
- latency budget;
- resource budget;
- confidence requirement;
- model availability;
- privacy constraints;
- context size;
- quality requirements;
- degraded-mode policy.

The router returns a model invocation plan rather than directly modifying cognitive state.

Every invocation should record:

```text
model_id
model_version
runtime
request_type
latency
resource_usage
success/failure
output_schema
confidence if available
```

---

## 18. Structured output boundary

Learned models must return validated structured outputs when they affect cognitive state.

Conceptual flow:

```text
model
 ↓
raw output
 ↓
parser
 ↓
schema validation
 ↓
semantic validation
 ↓
provenance attachment
 ↓
cognitive state proposal
 ↓
state commit
```

Malformed output must fail closed into an explicit uncertainty/error state rather than corrupting the World Model.

---

## 19. Cognitive cycle

The initial continuous loop is:

```text
1. Receive evidence
2. Normalize timestamps
3. Validate schemas
4. Fuse evidence
5. Update World Model
6. Build Situation Model
7. Retrieve relevant memory/context
8. Update uncertainty
9. Run required reasoning/prediction
10. Produce Cognitive State
11. Publish domain events
12. Accept feedback/outcomes
13. Repeat
```

The cycle must be interruptible and bounded by runtime budgets.

Not every component needs to execute at every cycle. Components should operate at explicit rates or event triggers.

---

## 20. Update-rate policy

Initial Mac implementation should classify cognitive work as:

### Event-driven

- speech transcript arrival;
- person detected;
- object detected;
- explicit user interaction;
- important memory result;
- safety-relevant evidence.

### Periodic

- world-state reconciliation;
- stale-state cleanup;
- prediction refresh;
- social-context refresh;
- health-aware cognitive housekeeping.

### On-demand

- deep reasoning;
- long-context retrieval;
- complex planning context preparation;
- expensive multimodal inference.

Exact frequencies are implementation benchmarks, not assumptions. They must be measured on the Mac before being frozen.

---

## 21. Interface to Soul

Cognition consumes Soul state and publishes evidence relevant to Soul.

Cognition may provide:

- current social context;
- interaction evidence;
- uncertainty;
- relevant observations;
- current situation;
- capability facts.

Cognition must not redefine:

- personality;
- identity;
- values;
- motivations;
- social character.

Soul remains authoritative.

---

## 22. Interface to Memory

Cognition requests and produces memory interactions through explicit contracts.

Cognition may request:

- relevant memories;
- relationship history;
- semantic knowledge;
- autobiographical context;
- prior observations;
- learned preferences.

Cognition may propose new memory candidates based on experience, but Memory owns durable persistence, provenance, retention and erasure.

---

## 23. Interface to Autonomy

Cognition provides:

- Situation Model;
- salient entities;
- social context;
- uncertainty;
- predictions;
- relevant memories/context;
- capability observations;
- cognitive recommendations/hypotheses.

Autonomy decides:

- whether to attend;
- whether to wait;
- whether to speak;
- whether to investigate;
- whether to plan;
- whether to act.

Cognition must not directly command physical actions.

---

## 24. Interface to Brain

Brain owns orchestration.

Brain provides Cognition with:

- lifecycle events;
- resource budgets;
- runtime configuration;
- model endpoints/adapters;
- health state;
- clock services;
- shutdown/recovery signals.

Cognition reports:

- health;
- queue depth;
- latency;
- model failures;
- uncertainty/degraded states;
- cognitive cycle metrics.

---

## 25. Resource budgets

The Mac implementation must measure:

- CPU utilization;
- GPU utilization where applicable;
- unified memory usage;
- model memory footprint;
- inference latency;
- queue latency;
- throughput;
- storage I/O;
- network use;
- temperature/resource pressure where observable.

No hard production budget should be invented before baseline measurements.

However, every expensive operation must have an explicit budget category before implementation.

---

## 26. Degraded modes

Cognition must define behavior for:

### LLM unavailable

Use structured/deterministic cognition and report reduced reasoning capability.

### Vision unavailable

Do not assert visual facts. Continue with audio/context where available.

### Speech unavailable

Use non-speech interaction where available.

### Memory unavailable

Do not invent memories. Operate with reduced continuity and explicit uncertainty.

### Model timeout

Cancel/replace according to router policy.

### Conflicting evidence

Preserve ambiguity and avoid forced certainty.

### High resource pressure

Reduce expensive inference, lower update frequency or enter degraded cognition mode according to Brain resource governance.

---

## 27. Failure recovery

Every cognitive operation should have:

```text
normal
 ↓
slow/degraded
 ↓
failed
 ↓
recovery attempt
 ↓
restored OR degraded continuation
```

Recovery must not silently duplicate events or corrupt cognitive state.

Idempotency and causal ordering follow the System Architecture durable-state and execution semantics.

---

## 28. Security and privacy boundaries

Cognition must treat external observations and model-generated content as untrusted input.

Threats include:

- prompt injection through speech/text;
- malicious visual content;
- poisoned memory results;
- spoofed identity evidence;
- adversarial sensor input;
- malicious tool outputs;
- model output manipulation.

Security controls are owned by the system security/policy architecture, but Cognition must expose provenance and trust metadata required by those controls.

---

## 29. Initial Mac implementation phases

### C0 — Semantic kernel

Implement without cameras or robot hardware:

- cognitive schemas;
- evidence objects;
- World Model;
- Situation Model;
- uncertainty;
- provenance;
- deterministic temporal utilities;
- model router interface;
- structured output validation;
- test harness.

### C1 — Local language cognition

Add:

- local/selected LLM adapter;
- context construction;
- reasoning adapter;
- model routing;
- structured reasoning outputs;
- memory read/write contracts.

### C2 — Audio cognition

Add:

- microphone input;
- speech recognition;
- speaker hypotheses;
- conversational evidence;
- social-context updates.

### C3 — Visual cognition

Add:

- camera input;
- person/object evidence;
- tracking;
- visual attention evidence;
- multimodal fusion.

### C4 — Continuous cognition

Combine:

```text
vision
+
audio
+
language
+
memory
+
soul
+
world model
+
situation model
```

and demonstrate stable continuous cognitive state updates.

### C5 — Simulation

Connect Cognition to simulated embodiment and evaluate temporal, spatial and social scenarios.

### C6 — Edge optimization

Only after Mac behavior is validated, benchmark NVIDIA-specific runtimes and deployment options.

---

## 30. Neural-network placement policy

Neural networks are appropriate where the problem is fundamentally learned or probabilistic, including:

- speech recognition;
- speech/voice features;
- visual recognition;
- multimodal semantic interpretation;
- language understanding;
- open-ended reasoning;
- learned prediction where benchmarked.

Neural networks should not be the sole implementation for:

- identity persistence;
- permission state;
- durable memory;
- event ordering;
- safety authorization;
- deterministic lifecycle;
- canonical timestamps;
- configuration;
- deployment state.

This is the core hybrid architecture decision.

---

## 31. Testing strategy

Testing must operate at multiple levels:

### Unit

- schema validation;
- temporal reasoning;
- uncertainty operations;
- fusion functions;
- state transitions;
- model router policies.

### Component

- World Model;
- Situation Model;
- reasoning engine;
- model adapter;
- evidence fusion.

### Integration

- Cognition ↔ Soul;
- Cognition ↔ Memory;
- Cognition ↔ Autonomy;
- Cognition ↔ Brain.

### Scenario

- five-person conversation;
- direct address;
- ambiguous address;
- person recognition uncertainty;
- conflicting sensor evidence;
- missing memory;
- LLM failure;
- vision failure;
- repeated interaction;
- changing world state.

### Longitudinal

- world-state consistency over hours;
- memory continuity;
- repeated person encounters;
- model replacement;
- restart/recovery.

---

## 32. Evaluation metrics

The Cognition implementation must measure at least:

### Correctness

- entity resolution accuracy;
- addressee accuracy;
- world-state accuracy;
- temporal reasoning accuracy;
- prediction quality;
- reasoning correctness.

### Uncertainty

- calibration where measurable;
- false-confidence rate;
- ambiguity preservation.

### Performance

- evidence-to-state latency;
- reasoning latency;
- end-to-end cognitive cycle latency;
- throughput;
- resource utilization.

### Reliability

- recovery rate;
- malformed-output rate;
- state corruption rate;
- duplicate-event rate;
- degraded-mode correctness.

Agent/system evaluation should measure trajectories and intermediate behavior rather than only final answers. NVIDIA's current NeMo evaluation stack explicitly supports task-driven agent evaluation, trajectory-aware scoring, local execution and reproducible evaluation artifacts. citeturn0search0turn0search2turn0search5

---

## 33. Research and technology validation

Technology choices must remain separate from the semantic Cognition specification.

NVIDIA NeMo Agent Toolkit provides current capabilities for workflow execution, memory providers and evaluation, including local evaluation and custom evaluators. These are candidates for implementation support, not automatic architecture decisions. citeturn0search0turn0search9

For Novi, any NVIDIA technology must pass:

```text
Novi requirement
 ↓
Candidate
 ↓
Primary-source validation
 ↓
Mac compatibility
 ↓
Benchmark
 ↓
Architecture fit
 ↓
Security/license review
 ↓
ADR
 ↓
Adoption
```

NVIDIA-specific optimization remains downstream of a working vendor-neutral Cognition contract.

---

## 34. Required implementation artifacts

Before Cognition is marked `VALIDATED`, the repository must contain or reference:

1. canonical evidence schema;
2. World Model schema;
3. Situation Model schema;
4. uncertainty/provenance schema;
5. cognitive state schema;
6. model invocation contract;
7. model router contract;
8. Soul/Cognition contract;
9. Cognition/Memory contract;
10. Cognition/Autonomy contract;
11. Brain/Cognition runtime contract;
12. degraded-mode matrix;
13. failure/recovery matrix;
14. resource budget specification;
15. test fixture strategy;
16. evaluation dataset/scenario strategy;
17. implementation ADRs for material technology choices.

---

## 35. Completion gate

Cognition may move from `IN PROGRESS` to `VALIDATED` only when:

- all implementation components have explicit ownership;
- all P0 contracts exist;
- World Model and Situation Model are executable in principle;
- uncertainty and provenance are explicit;
- neural and structured responsibilities are separated;
- model routing is replaceable;
- Mac runtime dependencies are identified;
- failure/degraded behavior is specified;
- security/privacy boundaries are documented;
- resource measurement is defined;
- acceptance scenarios exist;
- implementation artifacts are traceable to requirements;
- research sources are recorded for material technology/scientific claims.

Cognition may move to `COMPLETE` for the Mac implementation phase only after the first implementation passes the defined validation suite with evidence.

---

## 36. Non-goals

This document does not define:

- Soul personality or identity;
- durable memory implementation details;
- autonomous action selection;
- physical motor control;
- safety authorization logic;
- final hardware BOM;
- final model selection;
- final NVIDIA platform adoption.

Those remain authoritative in their respective domains.

---

## 37. Traceability

```text
North Star
   ↓
System Architecture
   ↓
Cognition Architecture
   ↓
Cognition Implementation Specification  ← this document
   ├── Evidence
   ├── World Model
   ├── Situation Model
   ├── Reasoning
   ├── Uncertainty
   ├── Prediction
   ├── Social Understanding
   └── Model Routing
          ↓
Brain Runtime
   ↓
Soul / Memory / Autonomy
   ↓
Validation
   ↓
Mac implementation
   ↓
Simulation
   ↓
Edge/physical deployment
```

---

## 38. Normative implementation rule

> **Cognition must turn evidence into a traceable, uncertainty-aware understanding of the world and current situation. It may use neural networks, structured algorithms or both, but it must never make an opaque model the sole authority for durable identity, memory, permissions, safety or runtime control.**
