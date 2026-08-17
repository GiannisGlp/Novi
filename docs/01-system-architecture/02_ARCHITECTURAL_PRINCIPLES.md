# 02 — Architectural Principles

**Status:** P0 normative architecture constraints

These principles are mandatory. If implementation pressure conflicts with a principle, the conflict requires an explicit ADR rather than a silent exception.

## 1. Autonomous, Not Prompt-Driven

Novi continuously processes environmental and internal events. User prompts are one event source, not the system lifecycle trigger.

## 2. Intelligence Is Layered

Perception, world modeling, memory, knowledge, attention, planning, policy, models and robotics have separate responsibilities.

## 3. Models Are Replaceable

No core subsystem may depend on a specific model's private API, hidden output quirks or weight format. Model access is through versioned capability interfaces.

## 4. Specialized AI Remains Specialized

Object detection, speech, embeddings, tracking, localization, navigation and low-level control use specialized systems where that provides better correctness, latency or resource behavior.

## 5. Vendor-Neutral Cognitive Core

NVIDIA is an important reference ecosystem, but Novi's semantic contracts must not depend on NVIDIA-specific APIs or product names.

## 6. Evidence Before Knowledge

Observations are not automatically facts. Durable knowledge requires provenance, confidence and verification appropriate to the claim.

## 7. Memory Is Structured

Memory is not a single vector index. Episodic, semantic, spatial, temporal, procedural, relational and media representations have distinct semantics.

## 8. Context Is Retrieved, Not Dumped

The complete memory store is never inserted into every model context. Retrieval is purpose-, authorization- and relevance-aware.

## 9. Attention Controls Interaction

Novi may observe without speaking. Detection does not imply interaction.

## 10. Personality Is Persistent

Personality is represented as governed state, not merely a prompt template.

## 11. Relationships Matter

Behavior may depend on identity, familiarity, relationship, history and current social state, subject to privacy and authorization.

## 12. Curiosity Is Controlled

Curiosity may create learning candidates, but cannot bypass safety, privacy, authorization or resource limits.

## 13. Learning Is Not Unrestricted Self-Modification

Learning changes governed data, memories, knowledge, routines, skills and approved model/configuration versions. It does not grant unrestricted source-code or safety-policy modification.

## 14. Schema Evolution Is Governed

New structures require validation, compatibility analysis, migration, authorization and audit.

## 15. Safety Is Outside the Model

No model output is trusted as a safety decision. Physical actions require deterministic policy/safety enforcement outside the model.

## 16. Fail Closed for Unsafe Ambiguity

When authorization, safety state, hardware state or action validity is uncertain, Novi refuses or safely degrades rather than guessing.

## 17. Hardware Abstraction

The same logical capability must be implementable across development, simulation, edge and physical runtimes.

## 18. Simulation Before Physical Risk

New robotics behaviors should be validated in simulation/HIL before physical deployment whenever practical.

## 19. Observability Is a Feature

Consequential autonomous decisions must be traceable through operational events and audit records without exposing hidden chain-of-thought.

## 20. Data Minimization

Only information required for a defined purpose should be retained. Privacy applies to source data and material derivatives.

## 21. Local-First Operation

Core perception, cognition, memory, personality, diagnostics and safety must remain functional without mandatory external network access.

## 22. Deterministic Foundations

Safety, storage integrity, authorization, lifecycle management and hardware limits must be deterministic wherever practical.

## 23. Small, Reversible Changes

Architecture and implementation changes should be incremental, testable, reviewable and reversible where possible.

## 24. Documentation Is Part of the System

Every significant subsystem requires:

- purpose;
- scope;
- responsibilities;
- inputs/outputs;
- interfaces;
- dependencies;
- state ownership;
- failure modes;
- security/privacy impact;
- performance/resource requirements;
- implementation candidates;
- validation strategy;
- acceptance criteria.

## 25. Connectivity Independence — Mandatory

**Novi must operate without Wi-Fi, Bluetooth or external network access.** Connectivity can extend capabilities but is never a mandatory dependency for core perception, cognition, autonomy, memory, personality, local interaction, diagnostics or safe physical operation.

Offline operation must be a tested runtime profile.

Network-dependent operations must explicitly define one of:

- continue locally;
- queue for later;
- retry with bounded backoff;
- expire safely;
- degrade to a local implementation;
- report unavailable capability.

When connectivity returns, synchronization remains subject to privacy, authorization, provenance, deletion, conflict and safety policies. Reconnection must never automatically upload all local data or overwrite newer local state.

## 26. Resource-Bounded Intelligence

Adaptive components must operate within explicit CPU/GPU/memory/storage/concurrency/context/action budgets. A model may be unavailable without making the entire robot unsafe.

## 27. Versioned Contracts

Cross-domain contracts must have explicit schema/API versions where compatibility can break. Implementations must declare the contract version they support.

## 28. Provenance Is End-to-End

When data is transformed from observation to evidence to memory, knowledge, decision or action, the provenance chain must remain addressable.

## 29. Authority Is Explicit

Identity, authentication, authorization, model identity, device identity and node identity are separate concepts. A model cannot manufacture authority through generated content.

## 30. No Silent Semantic Loss

Compression, summarization, indexing, caching, replication or migration must not silently turn authoritative state into an unverifiable approximation.

## 31. Recovery Is a First-Class Requirement

Every critical state transition must have defined crash, restart, replay, reconciliation and recovery semantics.

## 32. Privacy Survives Derivation

Deleting or restricting source data must trigger dependency analysis for memories, summaries, embeddings, indexes, replicas, backups and other material derivatives.

## 33. Technology Requires Evidence

No major technology becomes architecturally adopted because it is popular or vendor-recommended. Adoption requires:

```text
requirement
 ↓
authoritative documentation
 ↓
compatibility review
 ↓
benchmark / test
 ↓
security/license review
 ↓
ADR
```

For NVIDIA technologies, current NVIDIA documentation is the primary vendor source. For ROS 2, use official ROS documentation plus NVIDIA compatibility documentation where NVIDIA products are involved.

## 34. Principle Enforcement

A violation requires an ADR containing:

- violated principle;
- reason;
- scope;
- alternatives;
- risks;
- security/privacy impact;
- migration/reversal plan;
- validation evidence;
- approval.
