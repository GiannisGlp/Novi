# 101 — Memory Knowledge Cross-Modal Memory Architecture

## Status

**NORMATIVE ARCHITECTURE — CRITICAL / V1**

## Purpose

Define how Novi stores, aligns, links, retrieves, evaluates and reasons over memories originating from different modalities without collapsing their distinct evidential properties.

The architecture covers text, images, audio, video, structured records, telemetry, sensor streams, documents, spatial observations and future modalities.

It builds on:

- 95 — Integration / Reference Model;
- 96 — Architecture Audit / Gap Register;
- 97 — Identity / Entity Resolution;
- 98 — Temporal Reasoning;
- 99 — Spatial Memory;
- 100 — Causal World Modeling.

## 1. Core Principle

> **Novi must integrate modalities at the level of shared entities, events, time, space, semantics and provenance while preserving the original modality-specific evidence and uncertainty.**

Multimodal systems benefit from combining complementary information, but alignment, noise, representation mismatch, missing inputs and robustness remain fundamental challenges. citeturn0academia12turn0academia13

## 2. Cross-Modal Memory Is Not One Embedding

```text
TEXT
IMAGE
AUDIO
VIDEO
SENSOR
STRUCTURED DATA
       ↓
COMMON MEMORY GRAPH
       ↕
MODALITY-SPECIFIC EVIDENCE
```

A shared embedding can support retrieval, but it must not replace provenance, modality identity or the original evidence.

## 3. Modalities

V1 should support at least:

```text
TEXT
IMAGE
AUDIO
VIDEO
DOCUMENT
TABULAR / STRUCTURED DATA
TELEMETRY
LOCATION
TIME SERIES
SENSOR EVENT
```

The architecture must remain extensible to future modalities.

## 4. Observation vs Interpretation

Every modality produces observations that may later receive interpretation.

```text
IMAGE
 ↓
VISUAL OBSERVATION
 ↓
OBJECT HYPOTHESIS
 ↓
ENTITY LINK
```

The interpretation must not overwrite the original image evidence.

## 5. Modality-Specific Evidence

Each evidence item retains:

- modality;
- source;
- acquisition time;
- ingestion time;
- device/sensor;
- preprocessing history;
- transformations;
- quality;
- confidence;
- privacy classification;
- integrity metadata.

## 6. Shared Event Representation

Different modalities may describe the same event:

```text
CAMERA FRAME ─┐
AUDIO CLIP ───┼→ EVENT X
TEXT NOTE ────┤
GPS TRACE ────┘
```

The event is the shared semantic object; the modality records remain separate evidence.

## 7. Cross-Modal Alignment

Alignment determines which observations correspond across modalities.

```text
IMAGE @ T1
AUDIO @ T1+Δ
TEXT @ T1
      ↓
POSSIBLE SAME EVENT
```

Alignment must carry uncertainty.

## 8. Temporal Alignment

Streams rarely have identical timestamps.

Support:

```text
EXACT ALIGNMENT
WINDOW ALIGNMENT
OFFSET ALIGNMENT
UNKNOWN OFFSET
DRIFTING CLOCK
```

Temporal alignment must use document 98 semantics rather than assuming synchronized clocks.

## 9. Clock Uncertainty

Different devices can have:

- clock offsets;
- clock drift;
- missing timestamps;
- inconsistent time zones;
- delayed ingestion.

These must not silently create false event ordering.

## 10. Spatial Alignment

Modalities can be aligned using spatial context:

```text
CAMERA LOCATION
MICROPHONE LOCATION
GPS LOCATION
MAP REGION
ROOM
```

Spatial consistency is evidence for correspondence, not identity proof.

## 11. Spatial Coordinate Frames

Every spatial observation should identify its frame where relevant:

```text
GLOBAL
BUILDING
ROOM
DEVICE
CAMERA
ROBOT
MAP
```

Coordinate transformations must be explicit and versioned.

## 12. Identity Alignment

Modalities can reference entities from document 97:

```text
IMAGE
 ↓
PERSON CANDIDATE
 ↓
ENTITY_123
```

The identity link retains confidence and provenance.

## 13. Identity Does Not Equal Cross-Modal Correspondence

```text
SAME PERSON
 ≠
SAME EVENT
```

A person can appear in many unrelated observations.

## 14. Event Identity

Multiple modalities may refer to one event while one modality may contain many events.

Therefore event segmentation must remain explicit.

## 15. Segmentation

For continuous media:

```text
VIDEO STREAM
 ↓
SEGMENTS
 ↓
EVENT CANDIDATES
 ↓
MEMORY UNITS
```

Segmentation decisions retain provenance.

## 16. Granularity

Memory may exist at multiple levels:

```text
FRAME
CLIP
EPISODE
EVENT
DAY
LOCATION VISIT
LONG-TERM SUMMARY
```

A summary must remain linked to the underlying evidence.

## 17. Cross-Modal Memory Graph

A conceptual graph:

```text
ENTITY
  ↓
EVENT
 ↙ ↓ ↘
TEXT IMAGE AUDIO
  ↓
SPATIAL / TEMPORAL CONTEXT
  ↓
CAUSAL MODEL
```

## 18. Evidence Bundles

A cross-modal memory should be represented as an evidence bundle rather than a flattened blob:

```text
MEMORY M
 ├─ text evidence
 ├─ image evidence
 ├─ audio evidence
 ├─ sensor evidence
 ├─ spatial context
 ├─ temporal context
 └─ derived interpretations
```

## 19. Raw Evidence Preservation

Where retention policy permits, raw evidence remains independently addressable.

Derived representations cannot replace the original source without explicit policy.

## 20. Derived Representations

Examples:

```text
IMAGE → embedding
IMAGE → caption
AUDIO → transcript
VIDEO → summary
SENSOR → anomaly
```

Every derived representation must point back to its source.

## 21. Transformation Provenance

The provenance chain should support:

```text
RAW
 ↓
PREPROCESS
 ↓
ENCODE
 ↓
MODEL
 ↓
DERIVED OUTPUT
```

## 22. Correlated Evidence

The same source can produce multiple apparent modalities:

```text
VIDEO
 ↓
FRAME
 ↓
CAPTION
 ↓
TEXT SUMMARY
```

These are not independent confirmations.

## 23. Evidence Independence

Cross-modal fusion must track dependency between evidence sources.

```text
INDEPENDENT SOURCES
→ potentially complementary evidence

COMMON SOURCE
→ correlated evidence
```

This is essential for correct arbitration.

## 24. Modality Reliability

Reliability is task-specific.

```text
CAMERA
→ strong visual evidence
→ weak evidence in darkness

MICROPHONE
→ strong acoustic evidence
→ weak for visual identity
```

No modality receives a universal reliability rank.

## 25. Quality-Aware Fusion

Fusion should account for:

- signal quality;
- missingness;
- corruption;
- temporal alignment;
- spatial alignment;
- source reliability;
- model confidence;
- task relevance.

## 26. Missing Modalities

A memory may be incomplete:

```text
TEXT ✓
IMAGE ✗
AUDIO ✓
```

Missing evidence must not be interpreted as negative evidence unless the collection process guarantees that interpretation.

## 27. Modality Failure

When one modality fails:

```text
VISION FAILURE
      ↓
AUDIO / TEXT / SENSOR
      ↓
PARTIAL MEMORY
```

The resulting memory must retain the missingness state.

## 28. Asynchronous Streams

Different modalities may observe the same process at different rates:

```text
VIDEO 30 FPS
AUDIO 48 kHz
GPS 1 Hz
TEXT EVENT-DRIVEN
```

Cross-modal memory therefore requires temporal indexing rather than naive row-wise joining.

## 29. Cross-Modal Event Matching

Candidate correspondence should consider:

- temporal overlap;
- spatial compatibility;
- entity compatibility;
- semantic compatibility;
- causal compatibility;
- source provenance.

## 30. Cross-Modal Similarity

Similarity scores are evidence for correspondence, not proof.

```text
HIGH SIMILARITY
      ↓
CANDIDATE LINK
      ↓
ARBITRATION
```

## 31. Shared Latent Representations

Shared representations can improve retrieval and reasoning, but latent alignment must remain interpretable enough to preserve source provenance and uncertainty.

## 32. Modality-Specific Representations

Novi should preserve specialized representations where they contain information that a shared representation loses.

```text
SHARED REPRESENTATION
+
MODALITY-SPECIFIC REPRESENTATION
```

## 33. Early Fusion

Raw or low-level features may be combined before high-level reasoning.

Advantages can include direct cross-modal interaction.

Risks include:

- dimensionality;
- synchronization requirements;
- missing modality sensitivity;
- modality dominance.

## 34. Intermediate Fusion

Representations are aligned before fusion.

This can provide a useful balance between modality-specific processing and shared reasoning.

## 35. Late Fusion

Independent modality models produce outputs that are combined later.

Advantages include modularity and graceful degradation.

Risks include lost low-level cross-modal interactions.

## 36. Hybrid Fusion

Novi should allow hybrid architectures:

```text
MODALITY ENCODERS
      ↓
LOCAL PROCESSING
      ↓
CROSS-MODAL FUSION
      ↓
SHARED MEMORY
      ↓
MODALITY-SPECIFIC RETRIEVAL
```

Research surveys identify alignment and fusion as separate but interconnected design problems, with tradeoffs involving representation mismatch, noise and scalability. citeturn0academia12turn0academia13

## 37. Cross-Modal Retrieval

Queries should be able to cross modality boundaries:

```text
TEXT QUERY
 ↓
IMAGE / AUDIO / VIDEO / SENSOR MEMORY
```

and:

```text
IMAGE QUERY
 ↓
TEXT / EVENT / ENTITY MEMORY
```

## 38. Retrieval Must Preserve Modality

A retrieval result must identify whether it is:

```text
OBSERVED IMAGE
TRANSCRIPT
MODEL CAPTION
DERIVED SUMMARY
CAUSAL INFERENCE
```

## 39. Cross-Modal Ranking

Ranking should consider:

```text
SEMANTIC RELEVANCE
TEMPORAL RELEVANCE
SPATIAL RELEVANCE
ENTITY RELEVANCE
CAUSAL RELEVANCE
SOURCE QUALITY
```

## 40. Retrieval Does Not Equal Evidence Validation

A highly ranked memory is not automatically reliable.

```text
RELEVANCE
 ≠
TRUTH
```

## 41. Cross-Modal Contradictions

Different modalities can disagree:

```text
VISION: door closed
SENSOR: door open
TEXT: door was opened
```

The system must retain the conflict and use temporal context to resolve or preserve uncertainty.

## 42. Conflict Arbitration

Cross-modal conflicts should be evaluated using document 91's evidence arbitration principles:

- source reliability;
- acquisition conditions;
- temporal proximity;
- spatial compatibility;
- provenance;
- independence;
- task relevance.

## 43. No Majority-Vote Truth

Three derived outputs from one model do not automatically outweigh one independent authoritative sensor.

Evidence quantity is not the same as evidence independence.

## 44. Cross-Modal Confidence

Confidence must be decomposable:

```text
SOURCE QUALITY
×
ALIGNMENT CONFIDENCE
×
INTERPRETATION CONFIDENCE
×
ENTITY LINK CONFIDENCE
```

The exact mathematical combination is implementation-dependent.

## 45. Calibration

Confidence values must be calibrated for their intended task before being treated probabilistically.

## 46. Modality Bias

Multimodal models can rely excessively on one modality.

Research explicitly identifies unimodal biases in multimodal LLMs, including language and vision dominance. citeturn0search8

Novi should therefore test whether a decision remains supported when one modality is removed or corrupted.

## 47. Modality Ablation

Evaluation should include:

```text
ALL MODALITIES
TEXT ONLY
VISION ONLY
AUDIO ONLY
WITHOUT MOST RELIABLE MODALITY
CORRUPTED MODALITY
```

This helps identify hidden dependence.

## 48. Cross-Modal Grounding

Language concepts should link to observable entities, events and sensor evidence where possible.

```text
"red door"
   ↓
ENTITY / OBJECT
   ↓
IMAGE REGION
   ↓
SPATIAL LOCATION
```

## 49. Grounding Is Not Guaranteed

A language description may be hallucinated or inferred without direct evidence.

The memory layer must distinguish:

```text
DIRECTLY OBSERVED
MODEL-INFERRED
LANGUAGE-ASSERTED
EXTERNALLY SOURCED
```

## 50. Vision-Language Alignment

Modern multimodal LLMs demonstrate increasingly sophisticated text-image integration, but architecture and alignment choices vary substantially across systems. citeturn0search0turn0search1

Novi therefore defines interfaces and semantics rather than requiring one specific multimodal model.

## 51. Audio-Language Alignment

Audio memories may contain:

```text
SPEECH
ENVIRONMENTAL SOUND
MUSIC
ACOUSTIC EVENTS
VOICE FEATURES
```

Transcripts must not be treated as equivalent to the original acoustic evidence.

## 52. Video Memory

Video should preserve:

```text
FRAME RANGE
TEMPORAL ORDER
CAMERA ID
SPATIAL CONTEXT
TRACKS
EVENT SEGMENTS
DERIVED DESCRIPTIONS
```

A video summary is not a substitute for the temporal sequence when sequence matters.

## 53. Sensor Memory

Sensors may provide structured observations:

```text
TEMPERATURE
PRESSURE
MOTION
BATTERY
POSITION
DOOR STATE
```

Sensor semantics, calibration and hardware identity must remain attached.

## 54. Document Memory

Documents may contain text, images, tables and layout.

The architecture should preserve relationships between these elements rather than flattening a document into plain text only.

## 55. Tables and Structured Data

Structured values retain schema:

```text
VALUE
COLUMN
ROW
UNIT
TIMESTAMP
SOURCE
```

Flattening structured data into prose can destroy important semantics.

## 56. Units and Physical Meaning

Numeric sensor evidence must retain units and calibration context.

```text
5
```

is not meaningful without knowing whether it means:

```text
5 °C
5 m
5 V
5 kg
```

## 57. Cross-Modal Causal Evidence

Document 100 requires causal claims to preserve evidence provenance.

Cross-modal evidence can support causal hypotheses:

```text
VIDEO: action occurred
SENSOR: state changed
TEXT: operator reports action
      ↓
CAUSAL HYPOTHESIS
```

But correlated derived descriptions must not be counted as independent evidence.

## 58. Cross-Modal Temporal Reasoning

Cross-modal events must inherit temporal semantics from 98.

For example:

```text
AUDIO EVENT @ T1
ACTION VIDEO @ T1+0.2s
SENSOR CHANGE @ T1+0.4s
```

This can support event ordering without asserting causality automatically.

## 59. Cross-Modal Spatial Reasoning

Cross-modal observations inherit spatial semantics from 99.

```text
CAMERA A → ROOM 1
MIC B → ROOM 1
DEVICE C → ROOM 1
```

This provides context for event correspondence but not automatic entity identity.

## 60. Cross-Modal Identity Resolution

Document 97's entity resolution must remain authoritative for identity claims.

Cross-modal evidence can contribute to identity assessment but cannot bypass identity governance.

## 61. Memory Consolidation

Cross-modal memories can be consolidated:

```text
RAW OBSERVATIONS
 ↓
ALIGNED EVENTS
 ↓
EPISODE
 ↓
SEMANTIC MEMORY
 ↓
CAUSAL / PROCEDURAL DERIVATIVES
```

The provenance graph remains intact.

## 62. Summarization

Summaries must retain:

- source references;
- modality coverage;
- omissions;
- uncertainty;
- temporal scope;
- entity scope.

## 63. Compression

Compression may remove detail but must not silently change meaning.

Critical evidence should remain recoverable according to retention policy.

## 64. Memory Distillation

A distilled memory can be represented as:

```text
DISTILLED MEMORY
      ↓
SOURCE EVIDENCE SET
```

Distillation is a transformation, not a new observation.

## 65. Cross-Modal Memory Lifecycle

```text
INGEST
 ↓
NORMALIZE
 ↓
ALIGN
 ↓
SEGMENT
 ↓
LINK
 ↓
ARBITRATE
 ↓
STORE
 ↓
RETRIEVE
 ↓
CONSOLIDATE
 ↓
REVISE / EXPIRE / DELETE
```

## 66. Streaming Memory

For continuous sensors and media, the system should support incremental alignment rather than requiring full historical recomputation.

## 67. Late Arrivals

A late-arriving observation may change an earlier event interpretation.

```text
EVENT E
 ↓
NEW AUDIO ARRIVES
 ↓
REASSESS E
```

Historical provenance must record the revision.

## 68. Out-of-Order Events

Streams may arrive out of order.

Storage order must not be confused with event order.

## 69. Duplicate Observations

The same evidence may be ingested multiple times.

Deduplication should preserve source lineage and avoid double-counting evidence.

## 70. Cross-Modal Deduplication

Two different representations may describe the same underlying observation.

The system should distinguish:

```text
DUPLICATE SOURCE
DERIVED REPRESENTATION
INDEPENDENT OBSERVATION
```

## 71. Cross-Modal Entity Graph

A canonical entity may connect to modality-specific evidence:

```text
ENTITY X
 ├─ image observations
 ├─ voice observations
 ├─ text references
 ├─ sensor observations
 └─ video tracks
```

## 72. Cross-Modal Event Graph

```text
EVENT X
 ├─ video segment
 ├─ audio segment
 ├─ text report
 ├─ sensor transition
 └─ spatial trajectory
```

## 73. Memory Provenance Graph

Every derived memory should remain traceable:

```text
RAW EVIDENCE
 ↓
DERIVATION
 ↓
MEMORY
 ↓
SUMMARY
 ↓
REASONING
 ↓
DECISION
```

## 74. Security

Threats include:

- adversarial images;
- audio injection;
- malicious text;
- sensor spoofing;
- cross-modal poisoning;
- modality impersonation;
- timestamp manipulation;
- metadata forgery;
- malicious derived summaries.

## 75. Cross-Modal Poisoning

An attacker may use one modality to manipulate interpretation of another:

```text
MALICIOUS TEXT
 ↓
BIAS VISUAL INTERPRETATION
 ↓
FALSE MEMORY
```

or:

```text
SPOOFED SENSOR
 ↓
FALSE CAUSAL MODEL
```

Cross-modal integrity checks are therefore required.

## 76. Source Authentication

Where possible, modality evidence should include authenticated source identity and integrity metadata.

## 77. Provenance Cannot Be Assumed From Metadata Alone

A forged timestamp or device label is not authoritative merely because it exists in a record.

Trusted provenance must be distinguishable from self-asserted metadata.

## 78. Privacy

Different modalities carry different privacy risks:

```text
VOICE → biometric characteristics
IMAGE → identity / environment
LOCATION → movement patterns
TEXT → private content
VIDEO → people + environment
```

Privacy policy must apply to raw and derived representations.

## 79. Derived Sensitive Information

A harmless-looking embedding, transcript or summary can reveal sensitive information.

Privacy classification therefore propagates to derived memories.

## 80. Cross-User Isolation

Cross-modal evidence from one user's environment must not be silently linked into another user's private entity graph.

## 81. Deletion

Deletion must propagate through:

```text
RAW MEDIA
 ↓
DERIVATIVES
 ↓
ALIGNMENT LINKS
 ↓
SUMMARIES
 ↓
EMBEDDINGS
 ↓
CAUSAL / SEMANTIC DERIVATIVES
```

subject to policy and legally/technically valid retention constraints.

## 82. Retention Tiers

Different modalities may require different retention:

```text
RAW
HIGH-RESOLUTION DERIVED
FEATURE
SUMMARY
ABSTRACT SEMANTIC MEMORY
```

Retention must preserve enough provenance to interpret retained derivatives.

## 83. Cross-Modal Retrieval Security

A query should only retrieve evidence the requesting principal is authorized to see.

Authorization precedes sensitive cross-modal expansion.

## 84. Model Selection

Novi should not hard-code one multimodal model.

Models may specialize in:

```text
VISION
AUDIO
TEXT
VIDEO
SENSOR
CROSS-MODAL FUSION
```

A model registry should record capabilities, versions, limitations and evaluation status.

## 85. Model Composition

Modality-specific models can be composed when joint retraining is impractical.

Research has explored composing existing multimodal models to extend modality capabilities while addressing parameter interference and mismatch. citeturn0search7

## 86. Model Versioning

Every derived multimodal representation should record:

```text
MODEL ID
MODEL VERSION
PROMPT / CONFIGURATION
PREPROCESSING VERSION
EMBEDDING VERSION
```

## 87. Reproducibility

A derived interpretation should be reproducible or at least auditable where technically possible.

## 88. Evaluation

Evaluate cross-modal memory on:

- alignment accuracy;
- event matching;
- entity linking;
- retrieval precision/recall;
- temporal consistency;
- spatial consistency;
- contradiction handling;
- missing modality robustness;
- corruption robustness;
- calibration;
- provenance preservation;
- privacy leakage;
- latency;
- storage cost.

## 89. Multi-Image / Long-Context Evaluation

Realistic memory often requires reasoning over multiple images or observations rather than one isolated input. Benchmarks such as MIBench explicitly target multimodal models over multiple images, highlighting an important evaluation gap in single-image-centric evaluation. citeturn0search6

## 90. Ablation Evaluation

Test:

```text
ALL MODALITIES
REMOVE ONE
REMOVE TWO
NOISY MODALITY
MISALIGNED MODALITY
CONFLICTING MODALITY
```

## 91. Longitudinal Evaluation

Test whether cross-modal memory remains coherent over:

```text
HOURS
DAYS
MONTHS
YEARS
```

and whether new observations correctly revise rather than corrupt historical memory.

## 92. Causal Evaluation

Evaluate whether multimodal fusion improves causal reasoning without introducing spurious correlations or unimodal bias.

## 93. Cross-Modal Memory Invariants

1. Raw evidence and derived interpretation are distinct.
2. Every derived representation retains source provenance.
3. A shared embedding does not replace modality-specific evidence.
4. Alignment is uncertain unless independently established.
5. Time alignment is not storage order.
6. Spatial consistency is not identity proof.
7. Identity is not event correspondence.
8. Correlated derivatives are not independent evidence.
9. Missing evidence is not negative evidence by default.
10. Modality reliability is task-specific.
11. Confidence must be calibrated for its intended meaning.
12. Cross-modal relevance is not truth.
13. Summaries cannot silently erase provenance.
14. Contradictory modalities remain explicit until resolved.
15. One modality cannot automatically override another without evidence.
16. Cross-modal fusion must account for source dependency.
17. Model-generated content is not equivalent to direct observation.
18. Derived sensitive information inherits privacy controls.
19. Deletion propagates through dependent derivatives.
20. Model versions are part of memory provenance.
21. Cross-modal memory cannot bypass identity governance.
22. Cross-modal memory cannot bypass temporal governance.
23. Cross-modal memory cannot bypass spatial governance.
24. Cross-modal causal claims cannot bypass causal governance.
25. Current authoritative evidence can supersede stale derived memory for consequential decisions.
26. Multimodal models are tools, not sources of unquestionable truth.
27. Missing or corrupted modalities must be represented explicitly.
28. Cross-modal memory must support graceful degradation.
29. Cross-modal memory must be auditable.
30. Cross-modal memory must preserve the distinction between evidence and inference.

## 94. Integration With 95

```text
MULTIMODAL OBSERVATIONS
       ↓
EVIDENCE
       ↓
IDENTITY / TIME / SPACE
       ↓
CROSS-MODAL ALIGNMENT
       ↓
ARBITRATION
       ↓
MEMORY
       ↓
CAUSAL / SEMANTIC / PROCEDURAL DERIVATIVES
       ↓
REASONING
       ↓
AUTHORIZATION
       ↓
ACTION
```

## 95. Integration With 97

Identity links remain probabilistic/evidence-backed and reversible.

Cross-modal evidence contributes to identity resolution but never silently promotes an uncertain identity to fact.

## 96. Integration With 98

Temporal alignment uses event time, observation time, ingestion time and validity semantics.

Late-arriving evidence can revise interpretation without rewriting original observations.

## 97. Integration With 99

Spatial alignment uses explicit coordinate frames, places, regions and spatial uncertainty.

## 98. Integration With 100

Causal models consume cross-modal evidence but must preserve the dependency graph between evidence sources.

```text
VIDEO
 ↓
CAPTION
 ↓
CAUSAL CLAIM
```

must not be treated as three independent causal observations.

## 99. Research Cross-Validation

The architecture is supported by converging research directions:

### Multimodal model architecture and alignment
Caffagni et al. survey visual MLLMs and explicitly examine architectural choices, multimodal alignment, training, grounding, benchmarks and computational requirements. citeturn0search0

### Multimodal model taxonomy
Zhang et al. survey 126 MM-LLMs and identify recurring architectural and training patterns, supporting a model-agnostic interface rather than coupling Novi's memory architecture to one model family. citeturn0search1

### Alignment and fusion
Recent survey work categorizes multimodal alignment and fusion methods and identifies alignment, noise resilience and representation disparities as continuing challenges. citeturn0academia12

### Multimodal grounding and reasoning
Research tutorials describe multimodal systems as integrating language, visual, auditory and sensory information for understanding, reasoning and planning, while highlighting efficiency and reasoning as active challenges. citeturn0search4

### Unimodal bias
Research on multimodal LLMs shows that unimodal biases can cause incorrect multimodal answers, motivating explicit modality-ablation and conflict testing in Novi. citeturn0search8

## 100. Final Principle

> **Novi should remember the world as a structured network of observations and derived memories across modalities—not as a single fused representation. Every modality must retain its identity, provenance, timing, spatial context, uncertainty and failure modes, while shared entities and events provide the semantic bridges that allow multimodal reasoning without destroying evidential independence.**

Cross-modal memory is therefore the bridge between Novi's perception systems and its unified memory architecture: it enables integration without pretending that different sensors, representations or models are equivalent sources of truth.