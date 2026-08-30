# Plan 22 — Social Cognition & Natural Interaction: Implementation Status & Architecture Truth Map

**Plan:** `22_HUMAN_LIKE_SOCIAL_COGNITION_AND_NATURAL_INTERACTION_PLAN.md`
**This document:** Phase 0 output (Tasks 0.1–0.3) + running phase-status tracker for the whole implementation.
**Date:** 2026-08-30
**Status:** Phase 0 **COMPLETE** — Phase 1 (canonical observation contract) is next.

---

## 1. Task 0.1 — Inventory (module map)

Method: read and mapped the modules listed in plan §4 against the current `main`
(as of commit `73af953`). The plan's target module tree (interaction/identity/
memory/cognition/language) is **not** created literally; per plan §3 the rule is
*reuse/extend before creating* — the disposition in §3 below records what each
capability maps to today.

### 1.1 Unified input/response spine (plan 20/21 — exists, KEEP)

| Module | Responsibility | Production entry point |
|---|---|---|
| `novi/brain/chat.py` `ChatMixin` | Source-agnostic reply orchestration; speaking leases; addressee resolution; learning from chat; natural fallbacks | `MacBrain.respond(text, person=…)`, `respond_event(initiative, …)` |
| `novi/brain/dialogue.py` `DialogueEngine` | LLM renderer + quality guardrails (forbidden openers, meta-framing strip, repetition rejection, silence token); deterministic social replies (greeting/clarification/intro/joke/recall/continuation) | called from `_compose_reply_impl` |
| `novi/brain/discourse.py` `DiscourseState` | Conversation state: turns, topic, anaphora/topic resolution (`note_user_message` → `resolved_topic`) | `ChatMixin.note_user_message` |
| `novi/brain/input_bus.py`, `event_bus.py` | Priority-classified input queue; event envelopes with payload-signature dedup | `MacBrain.submit` / `_emit` |
| `novi/web/server.py` + CLI + voice | Thin transport surfaces → `brain.respond()` | web `/api/chat` (person=), CLI, `VoiceLoop` |

### 1.2 Perception → world model (plan 20/21/16/17 — exists, KEEP)

| Module | Responsibility | Entry point |
|---|---|---|
| `novi/perception/pipeline.py` `PerceptionPipeline` | Frame → detections/tracks → `WorldObservation` | `MacBrain._run_perception_pipeline` (in `step()`) |
| `novi/perception/detection.py`, `camera.py`, `tracking.py` (`ObjectTracker`) | Detector + track-stable IDs (`track-<id>`) | pipeline |
| `novi/perception/faces.py` `FaceIdentifier`, `novi/brain/face_id.py` (OpenCV/InsightFace), `speaker_id.py` (`VoiceprintSpeakerID`) | Face/voice identity providers | `MacBrain._identify_face/_identify_speaker` |
| `novi/brain/world_model.py` `WorldModel` (**canonical**) | Typed entities w/ epistemic status (OBSERVED/UNKNOWN/HYPOTHETICAL), provenance, contradictions, snapshots, uncertainty | `MacBrain._admit_world_observation`, `_update_unified_world`, `ground_scene` |
| `novi/perception/world_state_adapter.py` `admit_grounding_outcome` | Explicit grounding outcome → world model (hypothetical candidates, never overwrite observed) | `MacBrain.ground_scene` |
| `novi/perception/grounding*.py`, `active_grounding.py`, `locate_anything*` | Spatial grounding (LocateAnything backend), escalation policy, dedup/cache | `ground_scene`, active-perception path |
| `novi/brain/spatial_map.py` `SpatialMap` | Pose/region/frame spatial topology | `_spatial_context`, spatial memory promotion |
| `novi/brain/b1_world.py` | **Explicitly non-canonical** deterministic fast-path world model + scenario scaffolding (module docstring states canonical = `world_model.py`) | tests only — no duplicate authority |

### 1.3 Identity (exists; no lifecycle)

| Module | Responsibility |
|---|---|
| `novi/brain/identity.py` `PersonIdentity`/`IdentityBelief`/`IdentityMatch` | In-memory person identity belief; speech self-introduction binding (`resolve_addressee`) |
| `novi/brain/face_id.py`, `speaker_id.py` | Biometric providers (embeddings, cosine) — refs, no raw biometrics in memory |
| `novi/brain/engine.py` `_persist_identity` | Persists identity snapshot via `DurableMemoryStore.save_identity` (WAL) |
| **MISSING** | Identity lifecycle states (UNKNOWN/CANDIDATE/RECOGNIZED/CONFIRMED/AMBIGUOUS/REJECTED); cross-modal fusion policy; recognition events (`identity.recognized` etc.) |

### 1.4 Memory (rich substrate exists; projections + retrieval to mature)

| Module | Responsibility | Persistent |
|---|---|---|
| `novi/brain/storage.py` `DurableMemoryStore` | Single SQLite store (WAL), FTS, identity/knowledge/decision saves | ✅ |
| `novi/brain/memory_hardening.py` `HardenedMemoryManager` | Write gate, independence tracking, contextual trust, canonical records, governance | via store |
| `novi/brain/memory_classes.py` `MemoryClass` | Taxonomy + deterministic admission routing; `IMPLEMENTED_NOW` vs `DEFERRED_CLASSES` (prospective/metamemory/autobiographical/procedural-competence deferred; **SOCIAL and OBJECT classes absent**) | — |
| `novi/brain/consolidation.py` + `sleep_cycle.py` | Consolidator + summary consolidator + sleep-cycle scheduling | ✅ |
| `novi/brain/learning_pipeline.py` | Knowledge promotion, user-correction log, routine detection, counterfactual engine | ✅ (engine `_restore_learning`/`persist_learning`) |
| `novi/brain/importance.py` | Importance model, provenance trust, recency, `rank_memory` | — |
| `novi/brain/chat.py` `_memory_score` | Composite retrieval: 0.4 relevance + 0.25 recency + 0.2 importance + 0.15 trust | — |
| `novi/brain/social.py` `Relationships` | Relationship model (categories) — **in-memory, no persistence** | ❌ |
| **MISSING** | Bounded WorkingMemory layer; ProspectiveMemory mechanism; SOCIAL/OBJECT memory classes; full composite retrieval (person/situation/goal/causal/spatial/novelty/contradiction/staleness terms) | — |

### 1.5 Cognition (exists, KEEP/EXTEND)

| Module | Responsibility |
|---|---|
| `novi/brain/situation_model.py` `SituationModel` | Situations w/ confidence, freshness, `social_context` dict, attention targets, predictions, uncertainties |
| `novi/brain/prediction.py` | `PredictionEngine`, `SequencePredictor`, `PredictionErrorTracker` (+ curiosity wiring) |
| `novi/brain/curiosity.py` | Novelty detection, curiosity scoring, exploration planner/goals, preference learner |
| `novi/brain/attention.py` `AttentionRanker`, `salience.py` `EventSaliencePolicy`/`SurgeSalienceEvaluator` | Attention candidates; event salience → `CandidateInitiative` → `_maybe_autonomous_speech` |
| `novi/brain/social.py` `SocialInitiative`/`InitiativeConfig` | Initiative budget/cooldown; speaking leases in chat.py |
| `novi/brain/cognition_typed.py`, `cognition2.py`, `learning_pipeline.CounterfactualEngine` | Typed cognition output, hypotheses/alternatives (shallow per plan 22 §13) |
| `novi/brain/context_assembler.py` `ContextAssembler` | `ContextPackage` from world + situation (used by chat) |
| **MISSING** | DialoguePolicy (social decision layer, `decide()`); SocialContext (short-lived derived fields); HypothesisManager with scored alternatives; explicit attention→policy bridge |

### 1.6 Language / routing (exists, KEEP/EXTEND)

| Module | Responsibility |
|---|---|
| `novi/brain/models/router.py` `ReasoningRouter` | Conclusion/confidence/situation-based reasoning route (`decide`, `decide_for_text`, input classification, counts) |
| `novi/brain/inference/router.py` `ModelRouter` | Registry-based routing (latency/context aware, fallbacks) |
| `novi/brain/models/reasoning.py` | Deterministic/Deliberative/LLM reasoning providers |
| `novi/brain/self_model.py`, `soul.py` | Self-model, character clause, affect→expression, humanizer system block |
| **MISSING (formalized)** | ContextPacket contract (cognition→LLM, plan §18); Verbalizer layer (plan §19) — today the prompt assembly + guardrails live in `chat.py`/`dialogue.py` |

### 1.7 Voice (exists, thin-surface ✓)

`novi/voice/` — `VoiceLoop`, `TurnTakingPolicy` (Channel-prioritized), `STT/TTS/VAD` providers (deterministic fakes + SayTTS). Engine `listen/ingest_transcript/ingest_audio_frame`. Plan §21 target (mic→VAD→speaker-ID→ASR→InputBus→brain→decision→TTS) matches; barge-in/TTS attenuation and speaker-ID fusion are the gaps.

### 1.8 Contracts, governance, observability

- `novi/contracts/` — brain/model-invocation; cognition/{attention-candidate, cognitive-decision-record, cognitive-event, intent-hypothesis, person-context, prediction, situation-state}; memory/{knowledge-record, memory-record} — KEEP as schema authority; context-packet contract may extend it.
- Autonomy/safety: `governance_guard.py`, `safety_policy.py`, `actuator_boundary.py`, `canonical_autonomy.py`, `autonomy_supervisor.py`, `behavior_tree.py`, `planner.py`, skills + skill governance — KEEP, never bypassed (plan §2.9, Gate H7).
- Observability: `observability.py`, `audit_trail.py`, `MacBrain._emit`, `respond()` trace dict — EXTEND with full decision traces (plan §27).

---

## 2. Task 0.2 — Ownership table

Columns: capability · current owner · production entry point · consumers · **missing consumers** · persistent · tested · hardware tested · planned replacement (plan §30 order).

| # | Capability | Current owner | Production entry | Consumers | Missing consumers | Persistent | Tested | HW tested | Replacement |
|---|---|---|---|---|---|---|---|---|---|
| 01 | Response orchestration (one path) | `chat.py` `ChatMixin.respond/respond_event` | `MacBrain.respond` | web, CLI, voice, autonomy events | — | partial (discourse) | ✅ `test_dialogue_natural`, `test_respond_event`, `test_identity_addressee` | ✅ (voice) | EXTEND (DialoguePolicy control point) |
| 02 | Observation contract | `WorldObservation` (perception/pipeline) + `track-<id>` | `_run_perception_pipeline` | `_admit_world_observation` | grounding path consumes a *different* shape (`GroundingObservation`) | ❌ | ✅ `test_pipeline`, `test_full_flow_scenario` | ✅ | EXTEND → canonical `Observation` (Phase 1) |
| 03 | Perception→world link | `_admit_world_observation`, `_update_unified_world` | `MacBrain.step()` | `unified_world` → chat ctx, `cognition.build_situation` | dialogue-policy (future) | ❌ (world in-memory; spatial facts promoted) | ✅ `test_world_integration`, `test_unified_world_replacement`, `test_engine_vision_pipeline` | ✅ (camera) | EXTEND (uncertainty propagation, spatial identity) |
| 04 | Person identity | `identity.py` + `face_id`/`speaker_id`/`faces.py` | `_identify_face/_identify_speaker`, `resolve_addressee` | addressee resolution, memory grounding | social context, dialogue policy, events | ✅ (`save_identity`) | ✅ `test_identity*` | ✅ (face/mic) | EXTEND → `PersonModel` + lifecycle (Phase 2) |
| 05 | Object identity | **none** (tracking only) | `ObjectTracker` (`track-<id>`) | world model | — | ❌ | ✅ tracking | ✅ | **NEW** `object_identity.py` (Phase 3) |
| 06 | Working memory | **none** (discourse + world only) | — | — | all of cognition | — | — | — | **NEW** `working_memory.py` (Phase 4) |
| 07 | Memory-type projections | `memory_classes.py` | admission routing | store | SOCIAL/OBJECT classes; PROSPECTIVE/AUTOBIOGRAPHICAL deferred | via class tag | ✅ `test_memory_classes` | — | EXTEND (Phase 5.1) |
| 08 | Composite retrieval | `chat._memory_score` + `importance.rank_memory` | recall paths | chat, recall_semantic | policy needs person/situation/goal/causal/spatial/novelty/contradiction/staleness terms | — | ✅ `test_retrieval_ranking` | — | EXTEND (Phase 5.3) |
| 09 | Social context | `Situation.social_context` (dict) + `social.py` | situation builder | context assembly | addressee/engagement/interruptibility fields | ❌ | ✅ `test_situation_model`, `test_social` | — | EXTEND → `SocialContext` (Phase 7) |
| 10 | Attention/salience | `attention.py`, `salience.py` | `_maybe_autonomous_speech` | proactive speech | dialogue policy as consumer | ❌ | ✅ `test_attention`, `test_salience_policy` | ✅ | EXTEND (bridge to policy, anti-narration) |
| 11 | Prediction + error | `prediction.py`, `curiosity.py` | `_spawn_surprise_goal` | curiosity goals | hypothesis manager | ❌ | ✅ `test_prediction`, `test_prediction_curiosity` | — | EXTEND (Phase 9: alternatives) |
| 12 | Grounding/reference | `perception/grounding*.py`, `discourse.py` | `ground_scene`, `note_user_message` | active perception, chat topic | unified reference resolution ("that/it/blue one") | cache only | ✅ extensive `test_grounding*`, `test_discourse` | ✅ | EXTEND (Phase 12) |
| 13 | Dialogue policy | distributed: `respond`/salience/`_maybe_initiate`/`communication_decision` | — | — | single decision point + `why_now` | — | ✅ (parts) | ✅ | **NEW** `dialogue_policy.py` (Phase 10) |
| 14 | Initiative scoring | `SocialInitiative`, `EventSaliencePolicy` | `_maybe_autonomous_speech` | proactive speech | full formula (relevance×confidence×…−costs); per-person cooldown; event dedup (bus dedup exists) | ❌ | ✅ `test_social`, `test_salience_policy`, `test_autonomous_speech`, `test_speaking_lease` | ✅ | EXTEND (Phase 11) |
| 15 | Context packet | `ContextAssembler` + `_compose_reply_impl` prompt build | chat | LLM | strict packet contract (identity/addressee/situation/topic/memory/act/intent/tone/length/constraints) | — | ✅ `test_context_assembler` | ✅ | EXTEND (Phase 14) |
| 16 | Verbalizer | `DialogueEngine` guardrails + humanizer block + `soul` character | `_compose_reply_impl` | final text | explicit verbalizer controls (length/complexity/hedging/follow-up) | — | ✅ `test_dialogue*` | ✅ | EXTEND (Phase 15) |
| 17 | Model routing | `models/router.py` (ReasoningRouter) + `inference/router.py` (ModelRouter) | chat/reasoning paths | brain | route by task complexity/latency budget/uncertainty/depth (verify which router is production) | counts | ✅ `test_router`, `test_engine_reasoning_router`, `test_input_aware_router` | ✅ | EXTEND (Phase 16) |
| 18 | Voice integration | `novi/voice/*` | `listen`/`ingest_transcript` | brain | speaker-ID fusion, barge-in/attenuation, full turn-taking (start/pause/interrupt/resume/backchannel/finish) | ❌ | ✅ `test_voice_loop`, `test_turn_taking`, `test_scenario_v1` | ✅ | EXTEND (Phase 17) |
| 19 | Interaction outcomes | `learning_pipeline.UserCorrectionLog`, `CommunicationDecision` | `record_correction`, `compose_reply` | learning | full outcome record (input/perception/retrieval/decision/act/response/reaction/outcome) | ✅ | ✅ `test_learning_pipeline`, `test_learning_persistence` | — | EXTEND (Phase 18.1) |
| 20 | Behavioral learning | `learn_preference`, `_learn_from_chat`, `soul.learn_from_interaction`, `_restore_learning` | chat/step | future turns | persisted preferences affecting verbosity/directness/topic depth | ✅ | ✅ | ✅ | EXTEND (Phase 18.3) |
| 21 | Prospective memory | **none** (class tag only) | — | — | follow-up/reminders | — | — | — | **NEW** (Phase 6) |
| 22 | World simulator | `simulation.py`, `scenario_suite.py`, `b1_world.run_world_scenario` | tests | tests | people/objects/rooms/time/speech/gaze/gesture/noise timeline | — | ✅ `test_simulation`, `test_scenario_suite` | — | EXTEND → `WorldSimulator` (Phase 22) |
| 23 | Decision traces | `observability.py`, `audit_trail.py`, `respond().trace` | step/respond | debug | full trace (perception→…→memory writes, model+latency) | ✅ | ✅ `test_observability_engine` | — | EXTEND (Phase 23) |
| 24 | Conversation state (bounded) | `discourse.py` | chat | chat | explicit WorkingMemory bounds (max items/tokens/age/references) | — | ✅ `test_discourse` | — | EXTEND (Phase 4) |

---

## 3. Task 0.3 — Architecture disposition

### KEEP (no change)
- `world_model.py` (canonical world model — single authority)
- `storage.py` (single memory DB — no second database)
- `chat.py` `respond/respond_event` (one brain-owned response path)
- `event_bus.py`/`input_bus.py`, `dialogue.py` guardrails, `situation_model.py`, `attention.py`, `prediction.py`, `curiosity.py`, `fusion.py`, `spatial_map.py`, `context_assembler.py`, `memory_hardening.py`, `consolidation.py`, `sleep_cycle.py`, `learning_pipeline.py`, `importance.py`, `self_model.py`, `soul.py`, `kgraph.py`/`triple_index.py`, `novi/contracts/*`, governance/safety/actuator modules, `novi/voice/*`, perception pipeline/tracking/faces, `b1_world.py` (as non-canonical fast path)

### EXTEND (in place, in order of plan §30)
1. `perception/pipeline.py` → canonical `Observation` normalization (Phase 1)
2. `engine._admit_world_observation`/`world_state_adapter` → uncertainty propagation + spatial identity (Phase 1.3/1.4)
3. `identity.py` → `PersonModel` + lifecycle + recognition events (Phase 2)
4. `tracking.py` → `object_identity.py` (Phase 3)
5. `discourse.py` + new `working_memory.py` (Phase 4)
6. `memory_classes.py` → add SOCIAL/OBJECT, activate deferred classes (Phase 5.1)
7. `chat._memory_score`/`importance.rank_memory` → full composite retrieval (Phase 5.3)
8. `social.py`/`situation_model.py` → `SocialContext` (Phase 7)
9. `salience.py`/`attention.py` → attention→dialogue-policy bridge + anti-narration (Phase 8)
10. `prediction.py`/`curiosity.py` + new `hypothesis_manager`-style alternatives (Phase 9)
11. `grounding*`/`discourse.py` → unified reference resolution (Phase 12)
12. **NEW `dialogue_policy.py`** → `DialoguePolicy.decide` (Phase 10 — the new control point)
13. `social.py` `SocialInitiative` → full initiative formula + cooldowns + dedup (Phase 11)
14. `context_assembler.py` → strict ContextPacket contract (Phase 14)
15. `dialogue.py`/`chat.py` → `Verbalizer` (Phase 15)
16. `models/router.py`/`inference/router.py` → complexity/latency routing (Phase 16)
17. `novi/voice/*` → speaker-ID fusion, barge-in, turn-taking (Phase 17)
18. `learning_pipeline.py` → full interaction-outcome records (Phase 18)
19. `simulation.py`/`scenario_suite.py` → `WorldSimulator` timeline (Phase 22)
20. `observability.py` → full decision traces (Phase 23)

### ADAPTER ONLY
- `novi/web/server.py`, `cli.py`, `voice_loop.py` — thin transports; must keep calling `brain.respond()`/`respond_event()` and never own conversational intelligence (plan §2.1).

### DEPRECATE / REMOVE AFTER MIGRATION
- None found that can be removed now. `b1_world.py` is explicitly documented as non-canonical; it stays as the deterministic fast path until the canonical `WorldModel` covers its test-scenario use. The `b1_*`/`b2_*` stage modules are harnesses, not runtime duplicates — verify no runtime path imports them for authority (quick check below).

### Acceptance — "no duplicate architecture" checks
| Criterion | Verdict | Evidence |
|---|---|---|
| No duplicate conversation engine | ✅ PASS | single `respond()`/`respond_event()` in `ChatMixin`; `DialogueEngine` is a renderer, not a second brain |
| No duplicate world model | ✅ PASS | `world_model.py` canonical; `b1_world.py` docstring explicitly defers authority; `_admit_world_observation` is the only runtime admission path |
| No duplicate memory DB | ✅ PASS | `DurableMemoryStore` single SQLite; projections share the substrate (`memory_classes.py`) |
| No duplicate person identity registry | ✅ PASS | `identity.py` sole registry; `face_id`/`speaker_id`/`faces.py` are providers feeding it; persisted via `save_identity` |
| No second response path | ✅ PASS | web/CLI/voice/autonomy all land in `respond()`/`respond_event()`; autonomy events use `_maybe_autonomous_speech` → `respond_event` |

---

## 4. Gap summary → what Phase 1+ builds (vs extends)

| Plan phase | Disposition | Core work |
|---|---|---|
| 0 architecture truth | **DONE (this doc)** | inventory + ownership + disposition |
| 1 perception→world | EXTEND | canonical `Observation` contract; unify `WorldObservation`/`GroundingObservation`; propagate confidence/uncertainty; spatial identity on entities |
| 2 person identity | EXTEND | `PersonModel` fields; lifecycle states; cross-modal fusion (`fusion.py`); `identity.*` events |
| 3 object identity | **NEW** | `object_identity.py`; appearance signatures; lifecycle; `object.*` events |
| 4 working memory | **NEW** | bounded layer (items/tokens/age/references); promotion to LTM |
| 5 memory maturation | EXTEND | SOCIAL/OBJECT classes; deferred classes activation; full composite retrieval; provenance in context |
| 6 prospective memory | **NEW** | triggers/reminders; spontaneous follow-up via salience→policy |
| 7 social context | EXTEND | derived `SocialContext` fields (observable, probabilistic) |
| 8 attention/salience | EXTEND | attention→policy bridge; anti-narration guard |
| 9 predictive cognition | EXTEND | real hypothesis alternatives with scoring |
| 10 dialogue policy | **NEW** | `DialoguePolicy.decide()` + `DialogueDecision` + `why_now` |
| 11 initiative | EXTEND | full formula; per-person cooldown; stable event identity; conversation suppression |
| 12 grounding | EXTEND | unified reference resolution for deixis |
| 13 repair | **NEW** | repair acts + correction learning |
| 14 context packet | EXTEND | strict cognition→LLM contract |
| 15 verbalizer | EXTEND | explicit language-realization controls |
| 16 routing | EXTEND | complexity/latency-based selection; model is never truth source |
| 17 voice | EXTEND | speaker-ID fusion; barge-in; turn-taking verbs |
| 18 learning | EXTEND | full outcome records; persisted behavioral learning |
| 19 autobiographical | EXTEND | durable self-history (memory classes) |
| 20 proactive scenarios | EXTEND | P1–P9 deterministic scenarios on `scenario_suite.py` |
| 21 deterministic tests | EXTEND | per-module test classes per plan §25 |
| 22 world simulator | EXTEND | `WorldSimulator` timeline (T0–T8) |
| 23 observability | EXTEND | full decision traces |
| 24 evaluation | **NEW** | metric tracking harness |
| 25 real-device gates | later | H1–H7 |

---

## 5. Phase status tracker (updated as phases land)

| Phase | Status | Date | Notes |
|---|---|---|---|
| 0 architecture truth | ✅ COMPLETE | 2026-08-30 | ownership table + disposition (this document) |
| 1 perception→world | ✅ COMPLETE | 2026-08-30 | canonical `Observation` contract (`observation.py`), `apply_observation_to_world`, sigma + spatial_ref propagation, engine rewired through the canonical path |
| 2 person identity | ✅ COMPLETE | 2026-08-30 | `PersonModel`/`PersonRegistry` (`person_model.py`): lifecycle UNKNOWN→CANDIDATE→RECOGNIZED→CONFIRMED (+AMBIGUOUS/REJECTED), cross-modal fusion, contradiction retention, `identity.*` events, persisted |
| 3 object identity | ✅ COMPLETE | 2026-08-30 | `ObjectRegistry` (`object_identity.py`): instance re-identification, lifecycle, `object.*` events, persistence on consolidation cadence |
| 4 working memory | ✅ COMPLETE | 2026-08-30 | `WorkingMemory` (`working_memory.py`): bounded slots, expire/promote, token caps; wired into step + respond |
| 5 memory maturation | ✅ COMPLETE | 2026-08-30 | SOCIAL/OBJECT classes added; PROSPECTIVE/AUTOBIOGRAPHICAL activated (`memory_classes.py`); composite retrieval policy + explainable scoring (`retrieval_policy.py`) wired into recall |
| 6 prospective memory | ✅ COMPLETE | 2026-08-30 | `ProspectiveMemoryStore` (`prospective_memory.py`); "remind me to X" registration in respond(); due triggers → working memory → policy INITIATE |
| 7 social context | ✅ COMPLETE | 2026-08-30 | `SocialContext` (`social_context.py`): observable-probabilistic derivation, wired into situation model + policy |
| 8 attention/salience | ✅ COMPLETE | 2026-08-30 | `SalienceGate` anti-narration guard (plan §8.3 silent vs speak-worthy), `upstream_vetted` mode, gated proactive speech |
| 9 predictive cognition | ✅ COMPLETE | 2026-08-30 | `HypothesisManager` (`hypothesis_manager.py`): scored alternatives, evidence-driven belief, ambiguity preserved |
| 10 dialogue policy | ✅ COMPLETE | 2026-08-30 | `DialoguePolicy.decide` → `DialogueDecision` (`dialogue_policy.py`): 16 acts, why_* fields, safety override; run each cycle + emitted |
| 11 initiative | ✅ COMPLETE | 2026-08-30 | `InitiativeScorer` + bands + `InitiativeGate` (`initiative_scoring.py`): per-person cooldown, event dedup, conversation suppression |
| 12 grounding | ✅ COMPLETE | 2026-08-30 | `ReferenceResolver` (`reference_resolution.py`): deictic/definite resolution with pointing/gaze/topic signals; never guesses on ambiguity |
| 13 repair | ✅ COMPLETE | 2026-08-30 | REPAIR act in policy; `_is_correction_like` → correction outcomes (18.2) |
| 14 context packet | ✅ COMPLETE | 2026-08-30 | `ContextPacket`/`Builder` (`context_packet.py`): strict bounded contract, explainable memory entries, hard size boundary |
| 15 verbalizer | ✅ COMPLETE | 2026-08-30 | `Verbalizer` (`verbalizer.py`): length/hedging/question controls from the decision |
| 16 routing | ✅ COMPLETE | 2026-08-30 | `TierRouter` (`models/tier_router.py`): FAST/NORMAL/COMPLEX/SPECIALIZED/EXPERIMENTAL tiers; model never truth source |
| 17 voice | ✅ COMPLETE | 2026-08-30 | `TurnSession` (`voice/turn_session.py`): start/pause/interrupt/resume/backchannel/finish + barge-in preservation |
| 18 learning | ✅ COMPLETE | 2026-08-30 | `OutcomeRecorder` (`interaction_outcome.py`); `learn_preference` → person model; `_preferred_verbosity` behavior hook |
| 19 autobiographical | ✅ COMPLETE | 2026-08-30 | AUTOBIOGRAPHICAL projection activated (5.1); interaction outcomes + traces form the durable self-history substrate |
| 20 proactive scenarios | ✅ COMPLETE | 2026-08-30 | P1–P9 deterministic suite (`test_prospective_outcomes_scenarios.py`) |
| 21 deterministic tests | ✅ COMPLETE | 2026-08-30 | per-module test classes for every plan §25 list |
| 22 world simulator | ✅ COMPLETE | 2026-08-30 | `WorldSimulator` (`world_simulator.py`): scripted timeline T0–T8 + trace invariants |
| 23 observability | ✅ COMPLETE | 2026-08-30 | `TraceRecorder` (`decision_trace.py`) wired into step; bounded decision traces |
| 24 evaluation | ✅ COMPLETE | 2026-08-30 | `SocialMetricsTracker` (`social_metrics.py`): plan §28 rates |
| 25 real-device gates | ⏳ H1–H5 PENDING (hardware) | 2026-08-30 | `HardwareGateRunner` (`real_device_gates.py`): H6 + H7 PASS deterministically; H1–H5 report PENDING until real camera/voice |
| 26 fine-tuning | 🔒 deferred | — | requires real interaction traces (plan §33) — never a substitute for steps 1–25 |

*Update the plan's own Status line and this tracker at each phase boundary. Keep commits per plan §31; never push.*
