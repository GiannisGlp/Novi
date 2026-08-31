# Plan 24 — Emotional & Social Maturity: Implementation Status & Architecture Truth Map

**Plan:** `24_EMOTIONAL_AND_SOCIAL_MATURITY_PLAN.md`
**This document:** Phase 0 output (Steps 0.1–0.3) + running phase-status tracker for the whole implementation.
**Date:** 2026-08-31
**Status:** Phases 0–20 **COMPLETE** — Phase 21 (evaluation + DPO + policy ranking) in progress: §51 items 19–23 done (trace collection, sanitization, annotation, emotional SFT dataset, baseline evaluation suite).

---

## 1. Step 0.1 — Inventory (module map)

Method: read and mapped the modules listed in plan §4 against the current `main`
(as of commit `b0ee488`). The plan's target module tree (`social/`, `interaction/`,
`memory/`, `language/` subpackages) is **not** created literally; per plan §3 the
rule is *reuse/extend before creating* — the disposition in §3 below records what
each capability maps to today. Plan 22 (social cognition) is IMPLEMENTED and its
modules are the natural extension points.

### 1.1 Brain engine + response spine (exists, KEEP)

| Module | Responsibility | Production entry point |
|---|---|---|
| `novi/brain/engine.py` `MacBrain` | One input front door (`submit`), one step loop, one response path; wires perception → cognition → dialogue → voice | `MacBrain.submit` / `step` |
| `novi/brain/chat.py` `ChatMixin` | Source-agnostic reply orchestration; speaking leases; addressee resolution; learning from chat; natural fallbacks | `MacBrain.respond(text, person=…)`, `respond_event(initiative, …)` |
| `novi/brain/dialogue.py` `DialogueEngine` | LLM renderer + quality guardrails (forbidden openers, meta-framing strip, repetition rejection, silence token); deterministic social replies | called from `_compose_reply_impl` |
| `novi/brain/discourse.py` `DiscourseState` | Conversation state: turns, topic, anaphora/topic resolution | `ChatMixin.note_user_message` |
| `novi/brain/input_bus.py`, `event_bus.py` | Priority-classified input queue; event envelopes with dedup | `MacBrain.submit` / `_emit` |
| `novi/brain/context_packet.py`, `context_assembler.py` | Assembled context for the LLM; grounded context packet | `_compose_reply_impl` |
| `novi/brain/decision_trace.py` | Decision traces (why Novi would say anything) | `_decide_dialogue_act` |

### 1.2 Social cognition layer (plan 22 — exists, EXTEND)

| Module | Responsibility | Entry point |
|---|---|---|
| `novi/brain/social_context.py` `SocialContext`/`SocialContextBuilder`/`SocialEvidence` | Short-lived observable-probabilistic social context (addressee, phase, availability, engagement, temperature, interruptibility, social_opportunity, cues) | `MacBrain._build_social_context` |
| `novi/brain/dialogue_policy.py` `DialoguePolicy`/`DialogueContext`/`DialogueDecision` | Rule-based communicative-act selection (SILENCE/RESPOND/ASK/CLARIFY/ACKNOWLEDGE/COMMENT/INFORM/SUGGEST/WARN/FOLLOW_UP/GREETING/FAREWELL/INITIATE/CONTINUE/INTERRUPT/REPAIR) | `MacBrain._decide_dialogue_act` |
| `novi/brain/initiative_scoring.py` `InitiativeScorer`/`InitiativeGate` | Initiative score (relevance×confidence×social_opportunity×novelty×expected_value×urgency − interruption_cost − repetition_penalty − fatigue_penalty) + hard gates | `_decide_dialogue_act` / proactive path |
| `novi/brain/social.py` `Relationships`/`Relationship`/`SocialIntelligence`/`SocialInitiative` | Per-person relationship state (familiarity, trust, respect, shared_history, interaction_frequency/quality, preference/boundary knowledge, stability), tier expression, participation gate, initiative budget | `MacBrain` relationships registry |
| `novi/brain/person_model.py` `PersonRegistry`/`PersonModel` | Canonical persistent person identity with lifecycle (UNKNOWN→CANDIDATE→RECOGNIZED→CONFIRMED, AMBIGUOUS/REJECTED), cross-modal fusion, preferences, communication_patterns, consent | `MacBrain._observe_person_registry` |
| `novi/brain/identity.py`, `face_id.py`, `speaker_id.py` | Identity belief + biometric providers (refs only) | `_identify_face` / `_identify_speaker` |
| `novi/brain/hypothesis_manager.py` `HypothesisManager`/`Hypothesis` | Competing explanations of an observation, scored on probability/evidence/risk/cost/relevance; ambiguity preserved | prediction-failure path |
| `novi/brain/fusion.py` `MultimodalFusion`/`ModalityObservation`/`FusedEvent` | Confidence-weighted multimodal fusion with temporal alignment, conflict retention, uncertainty (σ) | `MacBrain` fusion slot |
| `novi/brain/interaction_outcome.py` `OutcomeRecorder`/`InteractionOutcome` | Every meaningful interaction records input, perception, decision, response, user reaction, correction, outcome | `MacBrain` outcome recorder |
| `novi/brain/prospective_memory.py` `ProspectiveMemoryStore` | Future intentions with triggers → INITIATE/ASK/REMIND | `_decide_dialogue_act` |
| `novi/brain/verbalizer.py` `Verbalizer` | Deterministic style controls over realized text (length, hedging, question form, tone) | `_compose_reply_impl` |
| `novi/brain/social_metrics.py` `SocialMetricsTracker` | Deterministic counters: grounding, retrieval, repetition, verbosity, initiative appropriateness, unsupported claims | evaluation path |

### 1.3 Cognition / world (exists, KEEP)

| Module | Responsibility |
|---|---|
| `novi/brain/world_model.py` `WorldModel` (**canonical**) | Typed entities w/ epistemic status, provenance, contradictions, snapshots, uncertainty |
| `novi/brain/situation_model.py` | Meaningful situations from world state + social slot |
| `novi/brain/attention.py`, `salience.py` | Attention candidates; salience policy |
| `novi/brain/self_model.py` | Self model |
| `novi/brain/prediction.py` | Prediction engine + accuracy |
| `novi/brain/curiosity.py`, `belief_revision.py` | Curiosity; belief revision |
| `novi/brain/working_memory.py` | Bounded working-memory slots |
| `novi/brain/planner.py`, `behavior_tree.py`, `skills.py` | Planning / execution / skills |

### 1.4 Memory / storage (exists, KEEP/EXTEND)

| Module | Responsibility | Persistent |
|---|---|---|
| `novi/brain/storage.py` `DurableMemoryStore` | Single SQLite store (WAL), FTS, identity/knowledge/decision saves | ✅ |
| `novi/brain/memory_hardening.py` `HardenedMemoryManager` | Write gate, independence tracking, contextual trust, canonical records, governance | via store |
| `novi/brain/memory_classes.py` `MemoryClass` | Taxonomy + admission routing; **SOCIAL class exists** (plan 22 Phase 5.1) | — |
| `novi/brain/consolidation.py` + `sleep_cycle.py` | Consolidator + summary consolidator + sleep-cycle scheduling | ✅ |
| `novi/brain/learning_pipeline.py` | Knowledge promotion, user-correction log, routine detection, counterfactual engine | ✅ |
| `novi/brain/importance.py`, `retention.py`, `retrieval_policy.py` | Importance, retention, composite retrieval scoring | — |
| `novi/brain/privacy.py` | Privacy classes, purpose binding, ERASE w/ propagation | — |

### 1.5 Perception / voice / autonomy / safety (exists, KEEP)

| Module | Responsibility |
|---|---|
| `novi/perception/pipeline.py`, `detection.py`, `camera.py`, `tracking.py` | Frame → detections/tracks → `WorldObservation` |
| `novi/perception/faces.py`, `novi/brain/face_id.py`, `speaker_id.py` | Face/voice identity providers |
| `novi/brain/audio.py`, `novi/voice/` | Audio capture, STT, TTS, turn manager |
| `novi/brain/autonomy.py`, `autonomy_state_machine.py`, `autonomy_supervisor.py` | Autonomy loop, state machine, supervisor |
| `novi/brain/safety_policy.py`, `governance_guard.py`, `actuator_boundary.py` | Safety, governance, actuator boundary |
| `novi/brain/object_identity.py`, `active_perception.py` | Object identity, active perception |

### 1.6 Training / learning workspace (exists, EXTEND)

| Module | Responsibility |
|---|---|
| `training/schemas.py` | Canonical example / policy / retrieval / grounding / preference-pair schemas + validation |
| `training/datasets/` | raw/ cleaned/ curated/ sft/ dpo/ retrieval/ grounding/ evaluation/ |
| `training/collection/` | trace_exporter, sanitizer, validator, deduplicator, annotator, teacher |
| `training/evaluation/` | benchmark, metrics, scenarios (30-scenario), shadow |
| `training/integration/` | claim_validator, policy_scorer, reranker |
| `training/models/` | registry, deploy, rollback, adapters, manifests |
| `training/training/` | train_sft / train_dpo / train_retriever / train_policy / evaluate |
| `novi/brain/learning_pipeline.py` | Deterministic in-brain learning (promotion, corrections, routines) |

---

## 2. Step 0.2 — Ownership table

| Capability | Current module | Production entry point | Inputs | Outputs | Persistent state | Existing tests | Hardware dep | Planned extension (plan 24) |
|---|---|---|---|---|---|---|---|---|
| Brain engine | `engine.py` `MacBrain` | `submit`/`step` | all inputs | response path | via store | `test_mac_brain.py` etc. | none | wire affective state into step loop |
| Chat/dialogue | `chat.py` `ChatMixin`, `dialogue.py` `DialogueEngine` | `respond` | text, person | reply | — | `test_dialogue*.py` | none | emotional strategy → verbalizer |
| Dialogue policy | `dialogue_policy.py` | `_decide_dialogue_act` | `DialogueContext` | `DialogueDecision` | — | `test_dialogue_policy.py` | none | empathy/regulation inputs; new acts |
| Social context | `social_context.py` | `_build_social_context` | `SocialEvidence` | `SocialContext` | — | `test_social_context.py` | none | affective state slot, boundary_state, current_topic, user_goal |
| Initiative | `initiative_scoring.py` | proactive path | relevance/confidence/… | `InitiativeScore` | — | `test_initiative_scoring.py` | none | emotional_pressure penalty, relationship_fit |
| Relationships | `social.py` | `MacBrain.relationships` | person, quality | `Relationship` | ✅ via store | `test_social.py` | none | communication_preferences, preferred_verbosity/directness, successful/failed patterns |
| Person identity | `person_model.py` | `_observe_person_registry` | modality observations | `PersonModel` | ✅ via store | `test_identity*.py` | face/voice providers | cross-modal identity + social context (Phase 37) |
| Hypothesis engine | `hypothesis_manager.py` | prediction-failure path | observation, alternatives | `Hypothesis` | — | `test_hypothesis_manager.py` | none | perspective hypotheses (Phase 5) |
| Multimodal fusion | `fusion.py` | `MacBrain.fusion` | `ModalityObservation` | `FusedEvent` | — | `test_fusion.py` | none | affect fusion (Phase 3) |
| Interaction outcomes | `interaction_outcome.py` | `MacBrain.outcome_recorder` | interaction | `InteractionOutcome` | — | `test_respond_event.py` | none | affective signals, learned implication (Phase 8) |
| Prospective memory | `prospective_memory.py` | `_decide_dialogue_act` | trigger | `ProspectiveMemory` | — | `test_prospective*.py` | none | — |
| Verbalizer | `verbalizer.py` | `_compose_reply_impl` | text, act, confidence, verbosity, tone | `NaturalLanguageResponse` | — | `test_verbalizer_router_voice.py` | none | strategy-driven realization (Phase 18) |
| Social metrics | `social_metrics.py` | evaluation path | interaction evidence | `MetricsReport` | — | `test_social*.py` | none | emotional metrics (Phase 41) |
| World model | `world_model.py` | `_admit_world_observation` | observations | world state | ✅ | `test_world_model.py` | none | — |
| Situation model | `situation_model.py` | `_derive_situations` | world, social | situations | — | `test_situation_model.py` | none | — |
| Memory substrate | `storage.py` | `DurableMemoryStore` | records | durable store | ✅ | `test_storage*.py` | none | social memory records (Phase 8) |
| Learning pipeline | `learning_pipeline.py` | `_restore_learning`/`persist_learning` | candidates | promotions | ✅ | `test_learning_pipeline.py` | none | emotional outcome learning (Phase 25) |
| Training workspace | `training/` | collection/training/eval | traces | datasets/models | ✅ | `training/tests/` | none | emotional datasets + SFT/DPO (Phases 19–31) |
| Safety/governance | `safety_policy.py`, `governance_guard.py` | step loop | events | decisions | — | `test_safety_policy.py` | none | safety overrides social optimization (Phase 14/40) |
| Privacy | `privacy.py` | memory admission | records | classification | — | `test_privacy.py` | none | emotional privacy (Phase 38) |

---

## 3. Step 0.3 — Classification

| Component | Class | Rationale |
|---|---|---|
| `engine.py` `MacBrain` | **KEEP** | One brain-owned response path; extend with affective state wiring |
| `chat.py` `ChatMixin` | **KEEP** | One response path; extend verbalizer integration |
| `dialogue.py` `DialogueEngine` | **KEEP** | LLM renderer + guardrails; extend with strategy-driven realization |
| `dialogue_policy.py` | **EXTEND** | One dialogue policy; add empathy/regulation inputs + new acts |
| `social_context.py` | **EXTEND** | One social context; add affective state, boundary_state, topic, goal |
| `initiative_scoring.py` | **EXTEND** | Add emotional_pressure penalty, relationship_fit component |
| `social.py` | **EXTEND** | Add communication_preferences, preferred_verbosity/directness, patterns |
| `person_model.py` | **EXTEND** | Cross-modal identity + social context (Phase 37) |
| `hypothesis_manager.py` | **EXTEND** | Perspective hypotheses (Phase 5) |
| `fusion.py` | **EXTEND** | Affect fusion (Phase 3) |
| `interaction_outcome.py` | **EXTEND** | Affective signals + learned implication (Phase 8) |
| `verbalizer.py` | **EXTEND** | Strategy-driven realization (Phase 18) |
| `social_metrics.py` | **EXTEND** | Emotional metrics (Phase 41) |
| `world_model.py` | **KEEP** | Canonical world model |
| `situation_model.py` | **KEEP** | Canonical situation model |
| `storage.py` | **KEEP** | One memory substrate |
| `memory_classes.py` | **EXTEND** | SOCIAL class already present; add emotional interaction records |
| `learning_pipeline.py` | **KEEP** | Deterministic in-brain learning |
| `training/` | **EXTEND** | Emotional datasets + SFT/DPO/policy |
| `safety_policy.py`/`governance_guard.py` | **KEEP** | Deterministic authorities; safety overrides social optimization |
| `privacy.py` | **EXTEND** | Emotional privacy (Phase 38) |
| `b1_world.py` | **KEEP (non-canonical)** | Explicitly non-canonical fast-path; tests only |

### New modules to create (no existing equivalent)

| Module | Plan phase | Purpose |
|---|---|---|
| `novi/brain/affective_evidence.py` | 1 | Canonical `AffectiveEvidence` record |
| `novi/brain/affective_state.py` | 2 | Transient affective state with decay |
| `novi/brain/affect_fusion.py` | 3 | Multimodal affect fusion (or extend `fusion.py`) |
| `novi/brain/affect_smoothing.py` | 4 | Temporal smoothing / hysteresis / cooldown |
| `novi/brain/perspective.py` | 5 | `PerspectiveHypothesis` engine |
| `novi/brain/relationship_state.py` | 7 | Evidence-based relationship preferences (or extend `social.py`) |
| `novi/brain/social_memory.py` | 8 | Emotional interaction memory (or extend `interaction_outcome.py`) |
| `novi/brain/regulation.py` | 9 | `RegulationDecision` engine |
| `novi/brain/empathy_policy.py` | 10 | Behavioral empathy strategies |
| `novi/brain/apology.py` | 11 | Apology architecture |
| `novi/brain/conflict.py` | 12 | Conflict state machine |
| `novi/brain/boundaries.py` | 14 | Boundary states + durable/revocable memory |
| `novi/brain/emotional_timing.py` | 16 | Timing / turn-taking integration |
| `novi/brain/backchannel.py` | 17 | Backchannel behavior |
| `novi/brain/humor_policy.py` | 33 | Humor policy |
| `novi/brain/encouragement.py` | 34 | Proportional encouragement |
| `novi/brain/sensitive_mode.py` | 35 | Grief / high-sensitivity conservative mode |
| `novi/brain/anti_manipulation.py` | 39 | Anti-manipulation rules |

---

## 4. Acceptance check (plan §4)

- **one dialogue policy** — `dialogue_policy.py` ✅
- **one social context** — `social_context.py` ✅
- **one world model** — `world_model.py` ✅
- **one memory substrate** — `storage.py` ✅
- **one identity source** — `person_model.py` `PersonRegistry` ✅
- **one brain-owned response path** — `chat.py` `ChatMixin` via `MacBrain.respond` ✅

---

## 5. Phase status tracker

| Phase | Status |
|---|---|
| 0 — repository truth and ownership audit | **COMPLETE** |
| 1 — affective evidence contract | **COMPLETE** |
| 2 — affective state model | **COMPLETE** |
| 3 — multimodal affect fusion | **COMPLETE** |
| 4 — temporal smoothing | **COMPLETE** |
| 5 — perspective-taking engine | **COMPLETE** |
| 6 — social context | **COMPLETE** |
| 7 — relationship model | **COMPLETE** |
| 8 — emotional memory | **COMPLETE** |
| 9 — emotional regulation engine | **COMPLETE** |
| 10 — empathy policy | **COMPLETE** |
| 11 — apology architecture | **COMPLETE** |
| 12 — conflict handling | **COMPLETE** |
| 13 — disagreement maturity | **COMPLETE** |
| 14 — boundaries | **COMPLETE** |
| 15 — initiative under emotional context | **COMPLETE** |
| 16 — emotional timing | **COMPLETE** |
| 17 — backchannel behavior | **COMPLETE** |
| 18 — emotional language realization | **COMPLETE** |
| 19–24 — emotional training datasets + SFT | **COMPLETE** (datasets + schema; SFT run is Phase 21 §29–§31) |
| 25–31 — evaluation + DPO + policy ranking | **IN PROGRESS** — §51 items 19–23 complete (trace collection, sanitization, annotation, emotional SFT dataset, baseline evaluation suite §44–§45); items 24–31 pending (SFT run, human eval, DPO, policy ranking) |
| 32–37 — multimodal eval, shadow eval, registry, rollback, acceptance, continuous learning | pending |
