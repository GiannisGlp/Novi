# 02 — Architectural Principles

These principles are mandatory constraints for Novi. When implementation pressure conflicts with a principle, the conflict must be documented as an Architecture Decision Record rather than silently bypassing the rule.

## 1. Autonomous, Not Prompt-Driven

Novi continuously processes environmental events. A user prompt is one input to the system, not the system's primary lifecycle trigger.

## 2. Intelligence Is Layered

General reasoning, perception, memory, world modelling, attention, policy, and robotics are separate responsibilities.

## 3. One Primary General-Purpose LLM Initially

NVIDIA Nemotron 3 Nano 30B-A3B is the initial primary reasoning candidate. Additional general-purpose models are introduced only when measurements show a real requirement.

## 4. Specialized AI Remains Specialized

Object detection, face recognition, speech recognition, embeddings, navigation, and low-level control use specialized systems where that is more efficient or reliable.

## 5. Models Are Replaceable

No core subsystem may depend on a specific model's internal API or output quirks without an adapter.

## 6. Vendor-Neutral Cognitive Core

NVIDIA is the reference hardware/software platform. Core cognitive contracts must remain independent of NVIDIA-specific implementations.

## 7. Evidence Before Knowledge

Observations are not automatically facts. All durable knowledge should have provenance and confidence appropriate to its source.

## 8. Memory Is Structured

Memory is not a single vector index. Structured facts, relationships, temporal events, spatial state, episodes, embeddings, and media have distinct representations.

## 9. Context Is Retrieved, Not Dumped

The complete memory/database is never inserted into every model context. Retrieval selects relevant information.

## 10. Attention Controls Interaction

Novi may observe without speaking. The decision to interact is independent of whether something was detected.

## 11. Personality Is Persistent

Personality is represented as stable traits plus dynamic state and relationship context. It must not depend solely on a prompt template.

## 12. Relationships Matter

Interaction behavior may vary according to identity, familiarity, relationship, history, and current social state.

## 13. Curiosity Is Controlled

Unknown concepts can become questions or learning candidates. Curiosity cannot bypass privacy, safety, authorization, or resource limits.

## 14. Learning Is Not Self-Modifying Code

Continuous evolution primarily changes managed data, memory, knowledge, preferences, learned routines, and approved model/configuration versions. It does not grant the AI unrestricted ability to rewrite source code or safety controls.

## 15. Schema Evolution Is Governed

Novi may create new data structures when existing structures are insufficient, but schema proposals pass through validation, policy, migration, and audit.

## 16. Safety Is Outside the Model

No LLM output is trusted as a safety decision. Physical action requires policy and safety validation.

## 17. Fail Closed for Unsafe Ambiguity

When safety state, authorization, hardware state, or action validity is uncertain, the system should refuse or safely degrade rather than guess.

## 18. Hardware Abstraction

The same logical capability should work against Mac, simulation, and Jetson implementations.

## 19. Simulation Before Physical Risk

New robotics behaviors should be validated in simulation before physical deployment whenever practical.

## 20. Observability Is a Feature

Every significant autonomous decision must be explainable through traceable events and audit records without requiring hidden model reasoning.

## 21. Data Minimization

Only the data required for a defined purpose should be retained. Sensitive data needs explicit retention, access, and deletion policies.

## 22. Local-First Operation

Core autonomy, memory, personality, and safety should function without mandatory cloud connectivity.

## 23. Deterministic Foundations

Safety, storage integrity, lifecycle management, hardware limits, and other foundational controls should be deterministic wherever possible.

## 24. Small Changes

Implementation changes should be incremental, testable, reviewable, and reversible.

## 25. Documentation Is Part of the System

Every significant subsystem must have a high-level document, detailed specification, interface definition, implementation plan, and validation strategy.

## 26. Connectivity Independence — Mandatory

**Novi must be fully operational without Wi-Fi, Bluetooth, or external network access.** Connectivity may extend Novi's capabilities but must never be a mandatory dependency for core perception, cognition, autonomy, memory, personality, safety, local interaction, diagnostics, or physical operation.

Wi-Fi and Bluetooth are optional capability providers. Connectivity state may change which optional functions are available, but it must never determine whether the core system is alive or able to perform its fundamental local functions.

Offline operation must be a supported and tested runtime profile, not merely a theoretical fallback.

Network-dependent operations must define one of the following behaviors when connectivity is unavailable:

- continue locally;
- queue for later;
- retry with bounded backoff;
- expire safely;
- degrade to a local implementation;
- explicitly report unavailable capability.

When connectivity returns, synchronization must remain subject to privacy, authorization, provenance, deletion, conflict-resolution, and safety policies. Reconnection must never automatically upload all local data or overwrite newer local state.

No subsystem may introduce an implicit network dependency into the offline-capable core.

---

## Principle Enforcement

These principles are architecture constraints. A proposed implementation that violates one must either be redesigned or documented through an explicit Architecture Decision Record with the reason, scope, alternatives considered, risks, migration plan, and approval status.
