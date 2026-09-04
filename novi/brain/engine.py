from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from novi.brain.b1_cognition import DeterministicCognition
from novi.brain.b1_world import SensorObservation
from novi.brain.b2_perception import Detection as B2Detection
from novi.brain.b2_perception import PerceptionEvidence, SpecialistPerception
from novi.brain.runtime import ActionProposal as RuntimeActionProposal
from novi.brain.runtime import BrainSupervisor, Lifecycle

from .actuator_boundary import ActuatorBoundary
from .attention import AttentionRanker
from .audio import AudioFrame, Hearing
from .autonomy import BoundedGoalController, Goal, GoalState, GoalStatus
from .autonomy_state_machine import AutonomyStateMachine
from .autonomy_state_machine import AutonomyStateMachineState as ASMState
from .chat import ChatMixin
from .closed_loop import OUTCOME_DENIED as LOOP_DENIED
from .closed_loop import OUTCOME_FAILURE as LOOP_FAILURE
from .closed_loop import OUTCOME_SUCCESS as LOOP_SUCCESS
from .closed_loop import ClosedLoopRuntime
from .cognition import BeliefSystem, ExpectationSystem
from .cognition2 import MacCognition
from .consolidation import ConsolidationConfig, MemoryConsolidator, SummaryConsolidator
from .context_assembler import ContextAssembler
from .dialogue import DialogueEngine, _extract_self_name
from .discourse import DiscourseState
from .event_bus import EventBus
from .failure_modes import PERCEPTION_UNCERTAINTY, TOOL_FAILURE, DegradedMode, FailureHandler
from .fusion import ModalityObservation, MultimodalFusion
from .governance_guard import (
    REQUIRE_CONFIRMATION,
    GovernanceGuard,
)
from .governance_guard import (
    ActionProposal as GovernanceActionProposal,
)
from .identity import PersonIdentity
from .io import Camera, MacMicrophone, MacSpeaker, VirtualBody
from .kgraph import EntityKnowledgeGraph
from .lexicon import LearnedPreferences, Lexicon
from .memory_hardening import HardenedMemoryManager, WriteGate
from .models import (
    DeliberativeReasoningProvider,
    DeterministicSTTProvider,
    ReasoningProvider,
    SpeechToTextProvider,
    TranscriptionResult,
)
from .models.router import ReasoningRouter
from .multi_speed_runtime import SYSTEM_0, AutonomyState, MultiSpeedRuntime, ResourceMode
from .nvidia_experiments import ALL_ADAPTERS, EpisodeRecorder, NoviEpisode
from .nvidia_experiments import OBSERVED as EP_OBSERVED
from .observability import Diagnostics, HealthMonitor, MetricRegistry, default_health_checks
from .p0_gate_runner import run_p0_gate
from .planner import Plan, Planner
from .privacy import _PERSON_LABELS, COMMON_ENTITY_LABELS, PrivacyGovernance
from .reflection import ReflectionEngine
from .resource_telemetry import ResourceTelemetry, combine_resource_modes
from .safety_policy import (
    RuntimeSafetyMonitor,
    SafetyPolicy,
    default_engine_safety_invariants,
)
from .salience import EventSaliencePolicy, SurgeSalienceEvaluator
from .self_model import build_self_model
from .situation_model import SituationModel
from .skill_contract import SUCCESS as SKILL_SUCCESS
from .skill_contract import SkillExecutor, SkillInvocation
from .sleep_cycle import SleepCycle
from .social import InitiativeConfig, Relationships, SocialInitiative, SocialIntelligence
from .soul import Soul
from .soul_acceptance import CommunicationDecision
from .storage import DurableMemoryStore
from .temporal import TemporalModel
from .world_model import (
    BUILDING as WM_BUILDING,
)
from .world_model import (
    OBJECT as WM_OBJECT,
)
from .world_model import (
    OBSERVED as WM_OBSERVED,
)
from .world_model import (
    PERSON as WM_PERSON,
)
from .world_model import (
    PLACE as WM_PLACE,
)
from .world_model import (
    ROBOT as ROBOT_WM,
)
from .world_model import (
    UNKNOWN as WM_UNKNOWN,
)
from .world_model import WorldModel as UnifiedWorldModel

# Plan 02 (web memory stability): single authoritative retention bound for the
# flattened compatibility event view. Same order of magnitude as the EventBus
# history so the compat layer never retains substantially more than the
# authoritative store. Configurable via MacBrainConfig.compat_event_history.
WEB_COMPAT_EVENT_HISTORY = 4096


@dataclass(frozen=True)
class MacBrainConfig:
    compat_event_history: int = WEB_COMPAT_EVENT_HISTORY
    sensor_id: str = "mac.camera.front"
    run_id: str = ""
    memory_dir: Path = Path("brain_data/memory")
    max_cycles: int = 1
    curiosity_enabled: bool = True
    curiosity_investigate_steps: int = 5
    llm_triples_enabled: bool = False
    skill_dirs: tuple[str, ...] = ()  # extra user skill directories (~/.novi/skills)
    consolidation_enabled: bool = True
    # Consolidation is a maturation pass, not a per-cycle event: with the web
    # server's 0.8s auto-step, every=1 fired a ~40K-char LLM summarizer prompt
    # EVERY cycle (permanent GPU saturation, 500s, wedged endpoints). 50 cycles
    # (~40s) keeps memory maturing while leaving the LLM free for chat/reasoning.
    consolidation_every: int = 50
    consolidation_config: ConsolidationConfig = field(default_factory=ConsolidationConfig)
    initiative_enabled: bool = False
    initiative_neglect_threshold: int = 30
    initiative_cooldown: int = 60
    #: cycles of no user interaction before a spontaneous remark may fire —
    #: protects mid-dialogue pauses (0.8s tick: 180 cycles ~ 2.4 minutes).
    initiative_conversation_guard_cycles: int = 180
    # Phase 5 (plan 19): neural perception cadence — run the (expensive)
    # perception backend every N cycles instead of every cycle, for Jetson
    # power budgets. 1 = every cycle (default, unchanged). The loop still steps
    # every cycle; only the perception backend is throttled.
    perception_every_n_cycles: int = 1
    # Plan 20: event-driven autonomous speech (GAP-A/B/C). When enabled, drained
    # non-text events (presence/scene/identity/hearing) can seed a proactive
    # utterance, gated by the same speaking-lease and initiative budget.
    event_autonomy_enabled: bool = False
    # Phase 3e (north-star): the brain OWNS its default LLM transport —
    # surfaces may still override for model tiering (web/CLI), but with the
    # flag on, respond() complies its own Ollama-backed transport from this
    # config and no injected callable is needed to get grounded replies.
    # Default off (CI stays transport-free: text=None fallback paths).
    brain_llm_enabled: bool = False
    brain_llm_url: str = "http://localhost:11434"
    brain_llm_model: str = ""
    brain_llm_probe_cooldown_s: float = 60.0
    # Chat wire dialect for the brain-owned transport: "ollama" speaks the
    # native /api/* endpoints; "openai-compatible" speaks /v1 so llama.cpp,
    # vLLM, and TensorRT-LLM frontends are drop-in backends.
    brain_llm_server: str = "ollama"
    # Plan 25: trained-adapter reply (talk with the trained data). When enabled
    # and an adapter dir is configured, the brain's default transport renders
    # replies through the plan-23/24 LoRA adapters in the training prompt format
    # (situation + communicative act), so Novi's talk uses the trained data.
    trained_reply_enabled: bool = False
    trained_dialogue_adapter: str = ""
    trained_emotional_adapter: str = ""
    trained_base_model: str = "Qwen/Qwen3-8B"
    # Phase P1 (sleep cycle): memory-maturation cadence in cycles (0 disables).
    sleep_every_n_cycles: int = 500
    # Phase 5 (plan 19): neural perception cadence — run the (expensive)
    # perception backend every N cycles instead of every cycle, for Jetson
    # power budgets. 1 = every cycle (default, unchanged). The loop still steps
    # every cycle; only the perception backend is throttled.
    perception_every_n_cycles: int = 1


class MacBrain(ChatMixin):
    """First executable Mac embodiment of the existing Novi Brain."""

    def __init__(
        self,
        *,
        camera: Camera | None = None,
        speaker: MacSpeaker | None = None,
        body: VirtualBody | None = None,
        perception: SpecialistPerception | None = None,
        reasoning: ReasoningProvider | None = None,
        llm_reasoning: Any | None = None,
        microphone: MacMicrophone | None = None,
        stt: SpeechToTextProvider | None = None,
        goals: BoundedGoalController | None = None,
        store_path: str | None = None,
        soul: Soul | None = None,
        relationships: Relationships | None = None,
        social: SocialIntelligence | None = None,
        lexicon: Lexicon | None = None,
        preferences: LearnedPreferences | None = None,
        beliefs: BeliefSystem | None = None,
        expectations: ExpectationSystem | None = None,
        temporal: TemporalModel | None = None,
        fusion: MultimodalFusion | None = None,
        identity: PersonIdentity | None = None,
        knowledge: EntityKnowledgeGraph | None = None,
        planner: Planner | None = None,
        governance: PrivacyGovernance | None = None,
        hearing: Hearing | None = None,
        health: HealthMonitor | None = None,
        metrics: MetricRegistry | None = None,
        diagnostics: Diagnostics | None = None,
        summary_consolidator: Any | None = None,
        narrator: Any | None = None,
        dialogue: Any | None = None,
        speaker_id: Any | None = None,
        face_id: Any | None = None,
        governance_guard: GovernanceGuard | None = None,
        config: MacBrainConfig | None = None,
        spatial_map: Any | None = None,
        telemetry: ResourceTelemetry | None = None,
        embedder: Any | None = None,
        retention_policy: Any | None = None,
        perception_pipeline: Any | None = None,
        safety_policy: Any | None = None,
        safety_monitor: Any | None = None,
        actuator_boundary: Any | None = None,
        llm_chat: Any | None = None,
        inference_runtime: Any | None = None,
    ) -> None:
        self.config = config or MacBrainConfig()
        self.run_id = self.config.run_id or str(uuid4())
        # Unified input architecture (north star §4.2): one prioritized bus in
        # front of the cognition loop. Producers never block; step() drains.
        from .input_bus import InputBus

        self.input_bus = InputBus()
        self.camera = camera
        self.speaker = speaker or MacSpeaker()
        self.body = body or VirtualBody()
        self.microphone = microphone or MacMicrophone()
        self.brain = BrainSupervisor()
        self.perception = perception or SpecialistPerception()
        # North-star Phase 1a (gap analysis 2026-08-29): the `novi/perception/`
        # package becomes the brain's camera perception path when attached.
        # process_frame feeds the unified world model with track-stable
        # entities; ground_frame stays an explicit capability (`ground_scene`,
        # investigate goals). None keeps the legacy SpecialistPerception path.
        self.perception_pipeline = perception_pipeline
        self._last_frame: Any | None = None
        self._last_world_observation: Any | None = None
        # Plan 26 B: an injectable live-vision snapshot provider (installed by
        # the web layer). None keeps the brain's honest "no camera wired"
        # vision_status; a provider only READS camera/runtime state so the
        # reply thread can never deadlock against the camera thread.
        self._vision_provider: Any | None = None
        # Phase 3e: the brain's OWN default LLM transport. An injected callable
        # is a tiering override; without one, the brain builds (lazily) its own
        # Ollama-backed transport when enabled, so surfaces pass only the
        # message. Unreachable endpoints degrade to deterministic fallbacks.
        self._override_llm_chat = llm_chat
        self._brain_llm_chat: Any | None = None
        # Plan 25: lazily-built trained-adapter transport (talk with the trained data).
        self._trained_transport: Any | None = None
        self._llm_unreachable_until: float = 0.0
        # Phase 3a (north-star gap analysis): grounded reasoning is the default
        # — the engine routes through ReasoningRouter (cost-aware: the LLM is
        # only paid when the input class or confidence warrants it; an absent
        # or erroring LLM degrades to the deterministic provider). Surfaces may
        # inject an LLM reasoning provider (llm_reasoning) or fully override
        # the provider (reasoning=), preserving test/CI behavior.
        # Plan 12 (inference runtime): an injected InferenceRuntime backs the
        # reasoning provider through the runtime-backed adapter; the brain
        # never constructs a backend directly and stays model/backend agnostic.
        self.inference_runtime = inference_runtime
        if reasoning is None and inference_runtime is not None:
            from .inference.adapter import RuntimeBackedReasoningProvider

            self.reasoning = RuntimeBackedReasoningProvider(inference_runtime)
        else:
            self.reasoning = reasoning or ReasoningRouter(
                deterministic=DeliberativeReasoningProvider(),
                llm=llm_reasoning,
            )
        self.reflection = ReflectionEngine()
        self.stt = stt or DeterministicSTTProvider()
        self.unified_world = UnifiedWorldModel()
        from .spatial_map import default_home_map

        # Spatial model (roadmap item 11): runtime holder for frames, regions,
        # occupancy, and the metric<->semantic link. A default home map is
        # established so reachability/visibility queries are available.
        self.spatial = spatial_map if spatial_map is not None else default_home_map()
        self.context_assembler = ContextAssembler()
        self.attention_ranker = AttentionRanker()
        self.governance_guard = governance_guard or GovernanceGuard()
        # Phase 2a (north-star gap analysis): the deterministic safety gate
        # (doc 08) is now part of the production action path — proposals are
        # evaluated by SafetyPolicy before skill invocation/execution, and
        # RuntimeSafetyMonitor surrounds body.execute() so a previously
        # approved action can be interrupted when the world turns unsafe.
        self.safety_policy = safety_policy or SafetyPolicy(default_engine_safety_invariants())
        self.safety_monitor = safety_monitor or RuntimeSafetyMonitor(default_engine_safety_invariants())
        # Phase 2c: the physical authority boundary — the engine never calls
        # body.execute() except through a compiled, expiring actuator command
        # (allow-list + parameter bounds + one command per cycle + TTL).
        self.actuator_boundary = actuator_boundary or ActuatorBoundary()
        self.multi_speed = MultiSpeedRuntime()
        self.closed_loop = ClosedLoopRuntime()
        self._last_attention_candidates: list[dict[str, Any]] = []
        self._last_context_package: dict[str, Any] | None = None
        self._last_governance_grant: dict[str, Any] | None = None
        # Confirmation flow (gap-analysis Step 3, item 18): REQUIRE_CONFIRMATION
        # grants are surfaced as requests and held here until confirm_action().
        self._pending_confirmations: dict[str, dict[str, Any]] = {}
        self._last_loop_snapshot: dict[str, Any] | None = None
        self.communication_decision = CommunicationDecision()
        self.skill_executor = SkillExecutor()
        self._last_skill_invocation: dict[str, Any] | None = None
        self.situation_model = SituationModel()
        self._last_situations: list[dict[str, Any]] = []
        self._last_typed_cognition: dict[str, Any] | None = None
        self.failure_handler = FailureHandler()
        # Real resource telemetry (gap-analysis Step 3, item 19): samples host
        # CPU/memory pressure each cycle so the runtime degrades under genuine
        # load, not only when a subsystem reports a failure.
        self.telemetry = telemetry or ResourceTelemetry()
        self._last_resource_sample: dict | None = None
        self.autonomy_sm = AutonomyStateMachine()
        self.episode_recorder: EpisodeRecorder | None = None
        self._recording_enabled: bool = False
        # Memory: HardenedMemoryManager (in-memory, canonical contract) or
        # DurableMemoryStore (SQLite, persistent). Both paths now use the
        # same WriteGate so the durable path has the same hardening
        # (epistemic status, evidence class, source class, independence groups,
        # retrieval failure states) as the in-memory path.
        write_gate = WriteGate()
        self.memory = (
            DurableMemoryStore(store_path, embedder=embedder, write_gate=write_gate)
            if store_path
            else HardenedMemoryManager(write_gate=write_gate)
        )
        self._using_hardened_memory = isinstance(self.memory, HardenedMemoryManager)
        # Phase 4b: retention is enforced at the store (per-type TTLs, capacity
        # eviction, expires_at honoring with audited tombstone reports). The
        # sweep rides the sleep cadence; retrieval excludes expired records
        # regardless. The in-memory hardened manager has no store to sweep.
        from .retention import RetentionEnforcer, RetentionPolicy

        retention_policy_obj = retention_policy or RetentionPolicy(default_ttl_days=365.0, max_records=50000)
        self.retention_enforcer = (
            None if self._using_hardened_memory else RetentionEnforcer(self.memory, retention_policy_obj)
        )
        if body is None and isinstance(self.memory, DurableMemoryStore):
            pose = self.memory.load_body()
            if pose is not None:
                self.body.x_m = float(pose.get("x_m", 0.0))
                self.body.y_m = float(pose.get("y_m", 0.0))
                self.body.heading_deg = float(pose.get("heading_deg", 0.0))
                self.body.velocity_mps = float(pose.get("velocity_mps", 0.0))
                self.body.last_action = str(pose.get("last_action", "idle"))
        self.cognition = MacCognition()
        self.goals = goals or BoundedGoalController()
        self._seen_entities: set[str] = set()
        self._persisted_terminal: set[str] = set()
        self.planner = planner or Planner()
        self._plans: dict[str, Plan] = {}
        # Phase 3c: violation-driven plan revisions are throttled per goal
        # (at most one revision per cycle) so a noisy predictor cannot churn.
        self._replan_throttle: dict[str, int] = {}
        if isinstance(self.memory, DurableMemoryStore):
            for snap in self.memory.load_plans():
                try:
                    plan = Plan.from_snapshot(snap)
                    self._plans[plan.goal_id] = plan
                except KeyError:
                    continue
        if goals is None and isinstance(self.memory, DurableMemoryStore):
            self._load_goals()
        self.consolidator = (
            MemoryConsolidator(self.memory, self.config.consolidation_config)
            if isinstance(self.memory, DurableMemoryStore)
            else None
        )
        self.summary_consolidator = summary_consolidator or (
            SummaryConsolidator(self.memory) if isinstance(self.memory, DurableMemoryStore) else None
        )
        if (
            self.summary_consolidator is not None
            and getattr(self.summary_consolidator, "store", None) is None
            and isinstance(self.memory, DurableMemoryStore)
        ):
            self.summary_consolidator.store = self.memory
        self.narrator = narrator
        # Phase P1 (sleep cycle): scheduled memory-maturation pass over the
        # durable store; inert when memory is the in-memory hardened manager.
        self._sleep_cycle = (
            SleepCycle(
                self.memory,
                consolidator=self.summary_consolidator,
                narrator=self.narrator,
                emit=self._emit,
                every_n_cycles=self.config.sleep_every_n_cycles,
            )
            if isinstance(self.memory, DurableMemoryStore) and self.config.sleep_every_n_cycles > 0
            else None
        )
        self.dialogue = dialogue or DialogueEngine()
        self.speaker_id = speaker_id
        self.face_id = face_id
        if soul is not None:
            self.soul = soul
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_soul()
            self.soul = Soul.from_snapshot(persisted) if persisted else Soul()
        else:
            self.soul = Soul()
        from .importance import ImportanceModel

        self.importance = ImportanceModel(curiosity_trait=float(self.soul.personality.traits.get("curiosity", 0.85)))
        if relationships is not None:
            self.relationships = relationships
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_relationships()
            self.relationships = Relationships.from_snapshot(persisted) if persisted else Relationships()
        else:
            self.relationships = Relationships()
        self.social = social or SocialIntelligence()
        self.social_initiative = SocialInitiative(
            InitiativeConfig(
                neglect_threshold=self.config.initiative_neglect_threshold, cooldown=self.config.initiative_cooldown
            )
        )
        # Plan 20: event salience → autonomous utterance (GAP-A/B/C).
        self.salience = SurgeSalienceEvaluator(EventSaliencePolicy())
        # Speaking lease (plan 19, Phase 2): while a reply is being composed
        # (the lease is held), spontaneous initiative stays silent. This
        # replaces the web server's `_chat_busy` loop-freeze: the cognitive loop
        # keeps ticking (SCENARIO-V1) and the lease alone gates outbound
        # spontaneity, so a concurrent step can never fire a duplicate remark.
        # Phase 2 (multitasking): per-ADDRESSEE leases — person A's reply only
        # gates initiative toward A; person B keeps talking to Novi.
        self._speaking_leases: dict[str, bool] = {}
        if lexicon is not None:
            self.lexicon = lexicon
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_lexicon()
            self.lexicon = Lexicon.from_snapshot(persisted) if persisted else Lexicon(seed={"novi": "self name"})
        else:
            self.lexicon = Lexicon(seed={"novi": "self name"})
        if preferences is not None:
            self.preferences = preferences
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_preferences()
            self.preferences = LearnedPreferences.from_snapshot(persisted) if persisted else LearnedPreferences()
        else:
            self.preferences = LearnedPreferences()
        if beliefs is not None:
            self.beliefs = beliefs
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_beliefs()
            self.beliefs = BeliefSystem.from_snapshot(persisted) if persisted else BeliefSystem()
        else:
            self.beliefs = BeliefSystem()
        if expectations is not None:
            self.expectations = expectations
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_expectations()
            self.expectations = ExpectationSystem.from_snapshot(persisted) if persisted else ExpectationSystem()
        else:
            self.expectations = ExpectationSystem()
        if temporal is not None:
            self.temporal = temporal
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_temporal()
            self.temporal = TemporalModel.from_snapshot(persisted) if persisted else TemporalModel()
        else:
            self.temporal = TemporalModel()
        if fusion is not None:
            self.fusion = fusion
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_fusion()
            self.fusion = MultimodalFusion.from_snapshot(persisted) if persisted else MultimodalFusion()
        else:
            self.fusion = MultimodalFusion()
        if identity is not None:
            self.identity = identity
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_identity()
            self.identity = PersonIdentity.from_snapshot(persisted) if persisted else PersonIdentity()
        else:
            self.identity = PersonIdentity()
        # Plan 22 Phase 2: canonical persistent person registry (lifecycle,
        # cross-modal fusion, recognition events). Restored independently of
        # the legacy single-slot identity so old stores migrate cleanly.
        from .person_model import PersonRegistry

        if isinstance(self.memory, DurableMemoryStore):
            self.person_registry = PersonRegistry.from_snapshot(self.memory.load_person_registry())
        else:
            self.person_registry = PersonRegistry()
        # Plan 22 Phase 3: persistent object-instance registry.
        from .object_identity import ObjectRegistry

        if isinstance(self.memory, DurableMemoryStore):
            self.object_registry = ObjectRegistry.from_snapshot(self.memory.load_object_registry())
        else:
            self.object_registry = ObjectRegistry()
        # Plan 22 Phase 4: bounded working memory (cognition buffer, not a
        # second memory database).
        from .working_memory import WorkingMemory

        self.working_memory = WorkingMemory()
        # Plan 22 Phase 10: dialogue policy — the social decision layer.
        from .dialogue_policy import DialoguePolicy

        self.dialogue_policy = DialoguePolicy()
        self.last_dialogue_decision = None
        # Plan 22 Phase 6: prospective memory (commitments/reminders).
        from .prospective_memory import ProspectiveMemoryStore

        self.prospective_memory = ProspectiveMemoryStore()
        # Plan 22 Phase 18: interaction outcome recording.
        from .interaction_outcome import OutcomeRecorder

        self.outcome_recorder = OutcomeRecorder()
        # Plan 22 Phase 23: end-to-end decision traces.
        from .decision_trace import TraceRecorder

        self.decision_traces = TraceRecorder()

        # Discourse state: bounded sliding-window model of "what are we
        # talking about" (gap-audit plan Phase B1). Known world/person labels
        # are preferred as topics so pronoun resolution lands on real referents.
        def _discourse_known_labels() -> set[str]:
            labels = set(self.unified_world.to_world_state().entities)
            labels |= {str(p) for p in _PERSON_LABELS}
            labels |= set(COMMON_ENTITY_LABELS)
            return labels

        self.discourse = DiscourseState(known_labels=_discourse_known_labels)
        if knowledge is not None:
            self.knowledge = knowledge
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_knowledge()
            self.knowledge = EntityKnowledgeGraph.from_snapshot(persisted) if persisted else EntityKnowledgeGraph()
        else:
            self.knowledge = EntityKnowledgeGraph()
        if isinstance(self.memory, DurableMemoryStore):
            # Incremental knowledge persistence: persist every triple immediately
            # (WAL-backed), so nothing is lost on a crash or hard kill.
            self.knowledge.set_on_change(self._persist_knowledge)
            self._persist_knowledge()
        # Triple semantic index (gap-audit Phase D2): "subject predicate object"
        # embeddings with graceful offline fallback, kept in sync on change.
        from .triple_index import index_for_graph

        _kg_embedder = getattr(self.memory, "_embedder", None)
        self.triple_index = index_for_graph(self.knowledge, embedder=_kg_embedder)
        # Learning pipeline (roadmap item 13): evidence-backed promotion into
        # knowledge, explicit user corrections with provenance, routine
        # detection (hypotheses only), and counterfactual evaluation.
        from .learning_pipeline import (
            CounterfactualEngine,
            KnowledgePromotionPipeline,
            RoutineDetector,
            UserCorrectionLog,
        )

        self.learning = KnowledgePromotionPipeline()
        self.corrections = UserCorrectionLog()
        self.routines = RoutineDetector()
        self.counterfactuals = CounterfactualEngine()
        # Phase 4c: lessons/regressions join the learning subsystems, and ALL
        # of them are persisted with the durable store so learning survives
        # restart and keeps shaping behavior (the north star's revise loop).
        from .recovery import RegressionMemory

        self.lessons = RegressionMemory()
        self._restore_learning()
        # Memory-class decision (roadmap item 16) + L0–L6 schema-evolution hooks.
        from .memory_classes import MemoryClassDecisionRegistry, SchemaEvolutionGate

        self.memory_classes = MemoryClassDecisionRegistry()
        self.schema_evolution = SchemaEvolutionGate()
        self.governance = governance or PrivacyGovernance(
            self.memory if isinstance(self.memory, DurableMemoryStore) else None
        )
        self.hearing = hearing or Hearing()
        self._pending_audio: list[ModalityObservation] = []
        self._pending_speech: list[ModalityObservation] = []
        self._last_audio_events: list[dict[str, Any]] = []
        self._last_reasoning_trace: dict[str, Any] = {
            "cycle": -1,
            "conclusion": "awaiting_cycle",
            "confidence": 0.0,
            "action": "none",
            "rationale": "",
            "route": "none",
            "route_reason": "",
            "recalled": 0,
            "situation": None,
            "detections": [],
        }
        self.metrics = metrics or MetricRegistry()
        self.diagnostics = diagnostics or Diagnostics()
        self.health = health or HealthMonitor(default_health_checks())
        # Skill system (docs/plans/01_BRAIN/16): portable SKILL.md packages;
        # shipped skills + user dirs. Manifests only until a skill is used.
        from .skills import SkillRegistry

        shipped_dir = Path(__file__).resolve().parents[1] / "skills"  # novi/skills/
        self.skills = SkillRegistry([shipped_dir, *[Path(d) for d in self.config.skill_dirs]])
        # Centralized skill activation (plan 16 P4): one engine-owned place
        # decides which skills apply to anything Novi produces — chat is just
        # one consumer. Cycle observation primes skills from perception and
        # memory; the humanizer style pass lives here too.
        from .skill_activation import SkillActivator

        self.skill_activator = SkillActivator(self.skills, emit=self._emit)
        self._last_health: dict[str, Any] | None = None
        self._cycle = 0
        # Plan 02: bounded flattened compatibility view. `self.events` stays a
        # plain list so every legacy consumer (iteration, indexing, slicing,
        # len) keeps working, but insertion goes through _append_compat_event
        # which enforces the hard retention bound at the source — the brain is
        # safe even when no web server is draining events.
        self.events: list[dict[str, Any]] = []
        # Autonomy event bus (gap-analysis Step 3, item 17): canonical
        # envelope with correlation/causation IDs, priority, privacy class,
        # replay, dedup, backpressure, and access control. `self.events` is
        # kept as the flattened compatibility view (all legacy consumers read
        # it); the bus is the authoritative store.
        self.event_bus = EventBus()
        self._cycle_correlation_id = str(uuid4())
        # Persistent decision audit trail (gap-analysis Step 3, item 23):
        # structured records of consequential decisions/actions with retention.
        from .audit_trail import AuditTrail

        self.audit_trail = AuditTrail()

    def start(self) -> None:
        self.brain.start()
        # Register System-0 safety check (deterministic, never waits on LLM).
        if not self.multi_speed.tasks_by_tier(SYSTEM_0):
            self.multi_speed.register(SYSTEM_0, "safety_check", self._system0_safety_check, priority=1.0)
        # Autonomy state machine: BOOTING → INITIALIZING → OBSERVING.
        now = datetime.now(timezone.utc).isoformat()
        t1 = self.autonomy_sm.transition("boot_complete", timestamp=now)
        self._emit("autonomy.transition", {"cycle": 0, **t1.snapshot()})
        t2 = self.autonomy_sm.transition("init_complete", timestamp=now)
        self._emit("autonomy.transition", {"cycle": 0, **t2.snapshot()})
        self._emit("brain.started", {"run_id": self.run_id})

    # ---- unified input architecture (north star §4.2/§4.3) -----------------

    def submit(
        self,
        source: str,
        kind: str,
        payload: Any = None,
        *,
        priority: int | None = None,
        coalesce_key: str | None = None,
    ) -> int:
        """Enqueue one input from ANY source without blocking.

        This is the single front door: web chat, CLI, voice turns, presence
        transitions, audio events — all call submit(). The bus never touches
        the brain lock, so a slow producer (mic, remote HTTP) can never stall
        cognition. Returns the envelope sequence number as a receipt.
        """
        env = self.input_bus.put(
            source=source,
            kind=kind,
            payload=payload,
            priority=priority,
            coalesce_key=coalesce_key,
        )
        # Phase P2: remember the most recent speech text so the cycle's router
        # can classify intent (social fast-path vs question vs substantive).
        if isinstance(payload, dict) and str(payload.get("text", "") or "").strip():
            self._last_submitted_text = str(payload["text"])
        elif isinstance(payload, str) and payload.strip():
            self._last_submitted_text = payload
        self._emit(
            "input.submitted",
            {
                "seq": env.seq,
                "source": source,
                "kind": kind,
                "priority": env.priority,
            },
        )
        return env.seq

    def drain_inputs(self, max_items: int = 8) -> list[dict[str, Any]]:
        """Drain queued inputs at cycle start; ingest speech into memory/world.

        Priority order comes from the bus. Speech/interrupt payloads flow
        through ingest_transcript exactly like a heard utterance (admission,
        learning, triples) so every source gets identical treatment; event/
        ambient records update world context and are reported in the step.
        Reply composition is NOT done here — callers compose via respond()
        outside all locks (north star §4.4).
        """
        try:
            batch = self.input_bus.drain(max_items=max_items)
        except Exception:  # noqa: BLE001 - bus failure must not kill the loop
            return []
        consumed: list[dict[str, Any]] = []
        for env in batch:
            record = {
                "seq": env.seq,
                "source": env.source,
                "kind": env.kind,
                "priority": env.priority,
                "submitted_at": env.submitted_at,
                "drop_count": env.drop_count,
            }
            if env.drop_count:
                record["coalesced_drops"] = env.drop_count
            text = ""
            payload = env.payload
            if isinstance(payload, dict):
                text = str(payload.get("text", "") or "")
            elif isinstance(payload, str):
                text = payload
            if text.strip():
                try:
                    from .models.stt import TranscriptionResult

                    result = self.ingest_transcript(
                        TranscriptionResult(
                            text=text,
                            language="en",
                            confidence=0.9,
                            audio_path="",
                            provider=env.source,
                            model_id=f"bus:{env.kind}",
                        )
                    )
                    record["admitted"] = bool(result["admission"].accepted)
                    record["memory_id"] = getattr(result["admission"], "memory_id", None)
                except Exception as exc:  # noqa: BLE001 - admission is best-effort
                    record["admit_error"] = str(exc)
            else:
                # Non-text input: keep it in the audit trail + world context.
                # Carry the payload so the salience evaluator (plan 20) can
                # decide whether this event is worth a proactive remark.
                record["payload"] = payload
                self._emit("input.consumed", {"cycle": self._cycle, **record})
            consumed.append(record)
        if consumed:
            self._emit("inputs.drained", {"cycle": self._cycle, "count": len(consumed)})
        return consumed

    def _known_entities(self) -> list[str]:
        """Entity names Novi remembers: identity bindings + knowledge graph."""
        names: list[str] = []
        idn = getattr(self, "identity", None)
        if idn is not None:
            with contextlib.suppress(Exception):
                snap = idn.snapshot()
                for binds in snap.get("bindings", {}).values():
                    names.extend(binds.keys())
        kg = getattr(self, "knowledge", None)
        if kg is not None and hasattr(kg, "entity_types"):
            with contextlib.suppress(Exception):
                names.extend(kg.entity_types().keys())
        return names

    def _memory_grounding(self, entity: str) -> str:
        """A short memory-grounded clause for a proactive remark, or ''.

        Searches recent episodic memories for a mention of the entity so a
        scene-change remark can reference prior context ("I remember your red
        mug was on the counter."). Best-effort; returns '' when memory is
        unavailable or the entity is unknown.
        """
        if not entity:
            return ""
        rows = getattr(self.memory, "active_rows", None)
        if rows is None:
            return ""
        try:
            episodic = [r["record"] for r in rows() if r["record"].memory_type in {"utterance", "perception"}]
        except Exception:  # noqa: BLE001 - memory is best-effort
            return ""
        needle = entity.lower()
        for rec in sorted(episodic, key=lambda r: r.created_at, reverse=True):
            content = rec.content if isinstance(rec.content, str) else str(rec.content)
            if needle in content.lower():
                return f"I remember {entity} was around earlier."
        return ""

    def _maybe_autonomous_speech(self, events: list[dict], detections, person: str | None) -> dict[str, Any] | None:
        """Event-driven proactive speech (plan 20, GAP-A/B/C).

        Runs the salience evaluator over drained non-text events + perception
        detections/identity. Gated by the same speaking-lease and social budget
        as neglect-driven initiative; never interrupts goal pursuit. Returns the
        respond_event() result (and speaks) or None to stay silent.
        """
        if not self.config.event_autonomy_enabled:
            return None
        if self.speaking_lease_for(person):
            self._emit(
                "speech.initiative_suppressed",
                {
                    "cycle": self._cycle,
                    "reason": "speaking_lease_held",
                },
            )
            return None
        affect = self.soul.affect.dimensions
        if affect.get("social_comfort", 0.5) < 0.35 and affect.get("engagement", 0.5) < 0.5:
            self._emit(
                "speech.initiative_suppressed",
                {
                    "cycle": self._cycle,
                    "reason": "social_overload_reduction",
                },
            )
            return None
        if self.goals.has_active:
            return None
        present = [d.label for d in detections] if detections else []
        candidate = self.salience.evaluate(
            events,
            cycle=self._cycle,
            known_entities=self._known_entities(),
            present_entities=present,
        )
        if candidate is None:
            return None
        # Plan 22 Phase 8.3: the anti-narration gate decides "worth saying"
        # (chair detected / same mug again stay silent even if salient).
        from .salience import SalienceGate

        gate = SalienceGate()
        speak, reason = gate.should_speak(
            {"kind": candidate.kind, "entity": candidate.entity},
            kind=candidate.kind,
            entity=candidate.entity,
            novelty=float(getattr(candidate, "novelty", 0.0) or 0.0),
            safety=False,
            upstream_vetted=True,  # SurgeSalienceEvaluator already thresholded
        )
        if not speak:
            self._emit(
                "speech.initiative_suppressed",
                {
                    "cycle": self._cycle,
                    "reason": f"anti_narration:{reason}",
                },
            )
            return None
        # GAP-E grounding: a scene-change remark can reference prior memory
        # ("I remember your red mug was on the counter.").
        grounding = self._memory_grounding(candidate.entity) if candidate.kind == "scene.changed" else ""
        result = self.respond_event(candidate, person=person or "", grounding=grounding)
        if result.get("text"):
            self.speak(result["text"], person=person or "")
        return result

    def step(self, *, resource_constrained: bool = False) -> dict[str, Any]:
        if self.brain.lifecycle is not Lifecycle.ACTIVE:
            raise RuntimeError(f"Mac Brain must be ACTIVE, got {self.brain.lifecycle.value}")
        if self.camera is None:
            raise RuntimeError("camera provider is not configured")
        self._cycle += 1
        # Phase 2c: watchdog pass — expire stale actuator commands so nothing
        # stays "authorized" invisibly (each expiry is auditable).
        for _expired in self.actuator_boundary.watch(cycle=self._cycle):
            self._emit("actuator.expired", {"cycle": self._cycle, **_expired})
        # Unified input architecture (north star §4.3): drain queued inputs
        # FIRST so every source — chat, voice, presence events, CLI — flows
        # through this one cognition loop. Speech/interrupt inputs are ingested
        # here (admission + learning); their replies are composed by callers
        # via respond() outside all locks (§4.4).
        consumed_inputs = self.drain_inputs(max_items=8)
        # Resource-constrained cycles pause lower-priority goals (doc 00 §Resources).
        self._resource_constrained = bool(resource_constrained) or self.failure_handler.is_degraded
        # Each cycle is one correlation domain on the event bus: all events
        # emitted during this step share the correlation id, and each event
        # causally references the event before it (doc 10 ordering).
        self._cycle_correlation_id = str(uuid4())
        # Failure handler: attempt recovery from degraded mode at the start of each cycle.
        if self.failure_handler.is_degraded:
            recovered = self.failure_handler.attempt_recovery()
            if recovered:
                self._emit("failure.recovered", {"cycle": self._cycle, "mode": "normal"})
        # Resource-aware adaptation: keep the multi-speed runtime's resource
        # mode aligned with the current failure/degraded state (Step 3 item 19).
        self._apply_resource_adaptation()
        # Multi-speed runtime: System-0 safety check runs first (never waits on LLM).
        msr_results = self.multi_speed.step({"cycle": self._cycle})
        if not self.multi_speed.system0_safety_clear:
            self._emit("safety.gate_failed", {"cycle": self._cycle, "results": msr_results})
            # Autonomy state machine: emergency stop.
            t = self.autonomy_sm.emergency_stop(timestamp=datetime.now(timezone.utc).isoformat())
            self._emit("autonomy.transition", {"cycle": self._cycle, **t.snapshot()})
            # In safe-minimum mode, skip the rest of the step.
            self.multi_speed.set_state(AutonomyState.SAFE_MINIMUM)
            return {
                "cycle": self._cycle,
                "safety_gate": "failed",
                "detections": [],
                "action": "stop",
                "authorized": False,
            }
        frame = self.camera.read()
        # Keep the latest frame available for the explicit grounding capability
        # (ground_scene): SpatialQuery frame_id must match the grounded frame.
        self._last_frame = frame
        self._emit(
            "sensor.camera.frame",
            {
                "frame_id": frame.frame_id,
                "width": frame.width,
                "height": frame.height,
                "captured_at": frame.captured_at,
                "metadata": frame.metadata,
            },
        )
        # Closed-loop OBSERVE: record the start of a new cycle.
        self.closed_loop.observe({"cycle": self._cycle, "frame_id": frame.frame_id})
        # Phase 5 (plan 19): neural perception cadence — run the expensive
        # perception backend every N cycles (power-aware for Jetson). On skipped
        # cycles reuse the last evidence so downstream logic (world model,
        # cognition) still has a consistent view; the loop keeps stepping.
        cadence = max(1, int(self.config.perception_every_n_cycles))
        if cadence == 1 or self._cycle % cadence == 0:
            evidence = self.perception.process(
                sensor_id=self.config.sensor_id,
                frame_id=frame.frame_id,
                timestamp=frame.captured_at,
                frame=frame.payload,
            )
            self._last_evidence = evidence
            if self.perception_pipeline is not None:
                evidence = self._run_perception_pipeline(frame, evidence)
        else:
            evidence = getattr(self, "_last_evidence", None)
            if evidence is None:
                evidence = self.perception.process(
                    sensor_id=self.config.sensor_id,
                    frame_id=frame.frame_id,
                    timestamp=frame.captured_at,
                    frame=frame.payload,
                )
                self._last_evidence = evidence
        self._emit(
            "perception.completed",
            {
                "frame_id": evidence.frame_id,
                "detection_count": len(evidence.detections),
                "provenance": dict(evidence.provenance),
            },
        )
        observations = tuple(
            SensorObservation(
                cycle=self._cycle,
                source=f"{self.config.sensor_id}.perception",
                entity=detection.label,
                location=None,
                state="present",
                confidence=detection.confidence,
                captured_cycle=self._cycle,
            )
            for detection in evidence.detections
        )
        self._admit_detections(evidence.detections)
        if self.perception_pipeline is None:
            self._update_unified_world(evidence.detections)
        # Phase 1c: the robot is a first-class world-model entity whose
        # spatial_ref/location track the body's live pose via the SpatialMap.
        self._sync_robot_world_state()
        # Failure detection: perception uncertainty (low-confidence or no detections).
        if not evidence.detections or all(d.confidence < 0.5 for d in evidence.detections):
            failure = self.failure_handler.report_failure(
                PERCEPTION_UNCERTAINTY,
                severity="warning" if evidence.detections else "error",
                component="perception",
                message="low_confidence_or_no_detections",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self._emit("failure.detected", {"cycle": self._cycle, **failure.snapshot()})
            self._apply_resource_adaptation()
        # Autonomy state machine: OBSERVING → AWARE when significant events detected.
        now_sm = datetime.now(timezone.utc).isoformat()
        if self.autonomy_sm.state == ASMState.OBSERVING and evidence.detections:
            t = self.autonomy_sm.transition("significant_event", timestamp=now_sm)
            self._emit("autonomy.transition", {"cycle": self._cycle, **t.snapshot()})
        # Cognition 2.0: two-pass — build a preliminary situation to form the
        # recall query, then ground the full situation in knowledge + goal + memory.
        prelim = self.cognition.build_situation(self.unified_world.to_world_state(), observations, cycle=self._cycle)
        recall = self._recall_context(prelim, evidence.detections)
        self._emit(
            "memory.recall",
            {"cycle": self._cycle, "query": " ".join(recall["query"]), "recalled": len(recall["memories"])},
        )
        knowledge_ctx = self._knowledge_context_for(prelim.salient_entities)
        goal_ctx = self._goal_context()
        cognitive = self.cognition.cycle(
            self.unified_world.to_world_state(),
            observations,
            cycle=self._cycle,
            knowledge=knowledge_ctx,
            goal=goal_ctx,
            recalled=recall["memories"],
        )
        self._emit(
            "cognition.completed",
            {
                "cycle": self._cycle,
                "conclusion": cognitive.reasoning.conclusion,
                "confidence": cognitive.reasoning.confidence,
                "uncertainty": list(cognitive.situation.uncertainty),
                "inferences": list(cognitive.reasoning.inferences),
                "hypotheses": list(cognitive.reasoning.hypotheses),
                "relations": list(cognitive.situation.relations),
            },
        )
        # Plan 22 Phase 4: bounded working memory — update the active slots,
        # expire stale entries and promote important events to durable memory.
        self._update_working_memory(evidence)
        # Skill priming (plan 16 P4): every cycle, whatever Novi saw, heard,
        # or recalled can activate relevant skills — not only chat utterances.
        self.skill_activator.expire(self._cycle)
        self.skill_activator.observe_cycle(
            cycle=self._cycle,
            detections=[d.label for d in evidence.detections],
            memories=[str(getattr(m, "content", m))[:200] for m in recall["memories"][:4]],
            narrative=str(getattr(cognitive.situation, "summary", "") or "")[:400],
        )
        # Typed cognition is canonical: emit SituationState / PersonContext /
        # IntentHypothesis / Prediction for this cycle, grounded in the same
        # knowledge + goal + recall context as the legacy cycle above
        # (gap-audit Phase A1 — docs/plans/01_BRAIN/13).
        self.cognition_typed(
            list(observations),
            knowledge=knowledge_ctx,
            goal=goal_ctx,
            recalled=recall["memories"],
        )

        # Attention candidates: Cognition emits ranked candidates for Autonomy.
        goal_target = goal_ctx.get("target") if goal_ctx else None
        attention_candidates = self.attention_ranker.rank(
            self.unified_world,
            active_goal_target=str(goal_target) if goal_target else None,
            known_entities=self._seen_entities,
        )
        self._last_attention_candidates = [c.snapshot() for c in attention_candidates[:10]]
        if attention_candidates:
            self._emit(
                "cognition.attention",
                {
                    "cycle": self._cycle,
                    "candidates": self._last_attention_candidates,
                    "top_action": attention_candidates[0].suggested_action,
                },
            )

        # Situation Model: derive meaningful situations from the world state.
        active_goal_ids = ()
        if self.goals.has_active and self.goals.active is not None:
            active_goal_ids = (self.goals.active.goal.goal_id,)
        novi_state = {"cycle": self._cycle, "lifecycle": self.brain.lifecycle.value}
        # Plan 22 Phase 7: derive the short-lived SocialContext from
        # observable evidence (person model + conversation state) and feed it
        # into the situation model's social slot.
        social_snapshot = self._build_social_context()
        social_ctx = {
            "conversation_active": social_snapshot["interaction_phase"] == "active",
            "participants": list(cognitive.situation.salient_entities),
            "social": social_snapshot,
        }
        situations = self.situation_model.derive(
            self.unified_world,
            novi_state=novi_state,
            active_goals=active_goal_ids,
            recent_events=[e for e in self.events[-20:]],
            social_context=social_ctx,
            cycle=self._cycle,
        )
        self._last_situations = [s.snapshot() for s in situations]
        self._emit(
            "situation.derived",
            {
                "cycle": self._cycle,
                "situations": self._last_situations,
                "situation_count": len(situations),
            },
        )

        # Deepen cognition: update beliefs and learn/check expectations from current detections.
        now = datetime.now(timezone.utc).isoformat()
        present = {d.label for d in evidence.detections}
        for detection in evidence.detections:
            self.beliefs.observe(detection.label, True, confidence=detection.confidence, now=now)
            if detection.label in {"person", "human", "face"}:
                self.identity.observe("person", confidence=detection.confidence, modality="vision", cycle=self._cycle)
                self._observe_person_registry(
                    "person",
                    name=None,
                    confidence=detection.confidence,
                    modality="vision",
                    cycle=self._cycle,
                )
                self._persist_identity()
                self._identify_face(detection, image=frame.payload)
        identity = self.identity.identity_for("person")
        if identity is not None:
            self._emit(
                "identity.observed",
                {
                    "cycle": self._cycle,
                    "person": identity.person,
                    "name": identity.name,
                    "tier": identity.tier,
                    "confidence": identity.confidence,
                },
            )
        # Gap-audit Phase D4: deterministic persistence predictions, scored
        # against this cycle's observations. Accuracy is measurable (audit
        # lever 4) and violations feed the expectation system as prediction
        # errors. Predictions never write to the unified world model.
        from .prediction import PredictionEngine, SequencePredictor

        predictor = getattr(self, "_predictor", None)
        if predictor is None:
            predictor = PredictionEngine()
            self._predictor = predictor
        new_predictions, confirmed, violated = predictor.observe(set(present), self._cycle)
        for p in confirmed:
            self._emit(
                "prediction.confirmed", {"cycle": self._cycle, "entity": p.entity, "confidence": round(p.confidence, 3)}
            )
        for p in violated:
            self._emit(
                "prediction.violated", {"cycle": self._cycle, "entity": p.entity, "confidence": round(p.confidence, 3)}
            )
        for p in new_predictions:
            self._emit(
                "prediction.made",
                {"cycle": self._cycle, "entity": p.entity, "kind": p.kind, "confidence": round(p.confidence, 3)},
            )
        acc = predictor.accuracy.accuracy()
        if acc is not None:
            self.metrics.set("prediction_accuracy", acc, unit="ratio")

        # Plan P4: causal/sequence prediction — after A appears, B tends to
        # appear within k cycles. Violations are surprise signals that feed
        # curiosity/initiative; predictions never write world state.
        seq_predictor = getattr(self, "_sequence_predictor", None)
        if seq_predictor is None:
            seq_predictor = SequencePredictor()
            self._sequence_predictor = seq_predictor
        seq_new, seq_confirmed, seq_violated = seq_predictor.observe(set(present), self._cycle)
        for p in seq_confirmed:
            self._emit(
                "prediction.sequence_confirmed",
                {"cycle": self._cycle, "source": p.source, "target": p.target, "confidence": round(p.confidence, 3)},
            )
        for p in seq_violated:
            self._emit(
                "prediction.sequence_violated",
                {"cycle": self._cycle, "source": p.source, "target": p.target, "confidence": round(p.confidence, 3)},
            )
            # Plan 19, Phase 3: a sequence violation is a *surprise* signal —
            # Novi expected B after A but it never appeared. Surface it as
            # curiosity so the brain can act on the unexpected (e.g. investigate
            # the missing target). Predictions never write world state.
            self._emit(
                "curiosity.surprise",
                {
                    "cycle": self._cycle,
                    "source": p.source,
                    "target": p.target,
                    "kind": "sequence_violation",
                    "confidence": round(p.confidence, 3),
                },
            )
            # Phase 3c: a violation may invalidate the active plan's
            # assumptions -> fail and regenerate the plan (close the loop).
            self._maybe_replan_for_violation(p.target, "sequence_violated")
            # Investigate the missing target when idle (surprise-driven curiosity).
            self._spawn_surprise_goal(p.target)
        for p in seq_new:
            self._emit(
                "prediction.sequence_made",
                {"cycle": self._cycle, "source": p.source, "target": p.target, "confidence": round(p.confidence, 3)},
            )
        seq_acc = seq_predictor.accuracy.accuracy()
        if seq_acc is not None:
            self.metrics.set("sequence_prediction_accuracy", seq_acc, unit="ratio")

        self.expectations.update(present)
        violations = self.expectations.drain_violations()
        for v in violations:
            self._emit(
                "cognition.expectation_violation",
                {"cycle": self._cycle, "entity": v.entity, "kind": v.kind, "confidence": v.expectation_confidence},
            )
            # Phase 3c: an expectation violation revises the active plan.
            self._maybe_replan_for_violation(v.entity, "expectation_violated")
        if violations:
            self._emit("cognition.predicted", {"cycle": self._cycle, "violations": [v.snapshot() for v in violations]})

        # Autonomous learning from experience (docs/02-autonomy/01 §Learning):
        # feed the current detected-event set into the routine detector so Novi
        # learns recurring co-occurrence patterns, and promote stable patterns
        # into the knowledge graph as inferred relations.
        if present:
            self.routines.observe(self._cycle, present)
            for routine in self.routines.routines(min_occurrences=self.routines.min_occurrences):
                self._emit(
                    "learning.routine",
                    {
                        "cycle": self._cycle,
                        "pattern": list(routine.pattern),
                        "occurrences": routine.occurrences,
                        "confidence": routine.confidence,
                    },
                )
                self._promote_routine_to_knowledge(routine)

        # Multimodal fusion: combine vision detections + pending speech into fused events.
        vision_obs = [
            ModalityObservation(
                modality="vision",
                entity=d.label,
                value="present",
                confidence=d.confidence,
                captured_at=now,
                received_at=now,
                source="camera",
            )
            for d in evidence.detections
        ]
        fused_events = self.fusion.ingest(vision_obs + self._pending_speech + self._pending_audio)
        self._pending_speech = []
        self._pending_audio = []
        for event in fused_events:
            self._emit("fusion.completed", {"cycle": self._cycle, **event.snapshot()})
        fused_reported = [event.snapshot() for event in fused_events]

        route_info: dict[str, Any] = {}
        plan_ctx: dict[str, Any] | None = None
        if self.goals.active is not None and self.goals.active.goal.goal_id in self._plans:
            plan_ctx = self._plans[self.goals.active.goal.goal_id].snapshot()
        situation = self._situation_dict(cognitive)
        if plan_ctx is not None:
            situation["plan"] = plan_ctx
        situation["narrative"] = self._episodic_narrative()
        # Phase 4c: learned routines shape action selection — persisted
        # routines survive restart and feed the deliberator's evidence.
        situation["routines"] = [list(routine.pattern) for routine in self.routines.routines()]
        last_reflection = self.reflection.last()
        if last_reflection is not None:
            situation["reflection"] = last_reflection.snapshot()
        # Phase P2: when this cycle consumed speech inputs, route with the
        # input-aware classifier (social fast-path / questions→LLM); otherwise
        # the legacy confidence-threshold decide() applies.
        speech_texts = [c for c in (consumed_inputs or []) if c.get("kind") in ("chat", "message", "text", "voice")]
        if hasattr(self.reasoning, "decide_for_text") and speech_texts:
            first_text = ""
            payload_text = getattr(self, "_last_submitted_text", "")
            first_text = str(payload_text)
            intent = self.reasoning.decide_for_text(
                first_text,
                conclusion=cognitive.reasoning.conclusion,
                confidence=cognitive.reasoning.confidence,
                situation=situation,
                recall=recall["memories"],
            )
        else:
            intent = self.reasoning.decide(
                conclusion=cognitive.reasoning.conclusion,
                confidence=cognitive.reasoning.confidence,
                situation=situation,
                recall=recall["memories"],
            )
        if hasattr(self.reasoning, "last_route"):
            self._emit(
                "reasoning.route",
                {
                    "cycle": self._cycle,
                    "route": self.reasoning.last_route,
                    "reason": getattr(self.reasoning, "last_reason", ""),
                },
            )
            route_info: dict[str, Any] = {
                "route": self.reasoning.last_route,
                "reason": getattr(self.reasoning, "last_reason", ""),
            }
            # Phase 3a: per-route cost tracking — route counts surface both as
            # live metrics (Dashboard/health) and in the step result.
            counts = getattr(self.reasoning, "route_counts", None)
            if counts:
                route_info["counts"] = dict(counts)
                self.metrics.set("reasoning_route_deterministic", float(counts.get("deterministic", 0)), unit="count")
                self.metrics.set("reasoning_route_llm", float(counts.get("llm", 0)), unit="count")
        self._emit(
            "reasoning.completed", {"cycle": self._cycle, "action": intent.action, "rationale": intent.rationale}
        )
        # Closed-loop PLAN: record the reasoning decision.
        self.closed_loop.plan({"action": intent.action, "rationale": intent.rationale, "cycle": self._cycle})
        deliberation = getattr(self.reasoning, "last_deliberation", None)
        if deliberation is not None:
            self._emit(
                "reasoning.deliberation", {"cycle": self._cycle, "action": intent.action, "deliberation": deliberation}
            )
            # Plan P5: persist the winning rationale as a decision memory and
            # recall prior decisions so the trace can cite "last time I chose X".
            self._persist_decision_memory(deliberation, situation, intent, cognitive.reasoning.confidence)
        prior_decisions = self._recall_prior_decisions(situation)
        if prior_decisions:
            self._emit("reasoning.prior_decisions", {"cycle": self._cycle, "decisions": prior_decisions})

        self._last_reasoning_trace = {
            "cycle": self._cycle,
            "conclusion": cognitive.reasoning.conclusion,
            "confidence": round(cognitive.reasoning.confidence, 3),
            "action": intent.action,
            "rationale": getattr(intent, "rationale", intent.action),
            "route": route_info.get("route", "deterministic"),
            "route_reason": route_info.get("reason", ""),
            "recalled": len(recall["memories"]),
            "situation": situation if isinstance(situation, dict) else None,
            "detections": [d.label for d in evidence.detections],
            "inferences": list(cognitive.reasoning.inferences),
            "hypotheses": list(cognitive.reasoning.hypotheses),
            "deliberation": deliberation,
            "prior_decisions": prior_decisions,
            # Phase 3b: explicit alternative evaluation persisted with the
            # decision so reasoning traces can cite scored comparisons. The
            # default router delegates to its deterministic provider, so read
            # the scores through it.
            "option_scores": {
                action: {
                    "action": action,
                    "expected_success": round(s.expected_success, 4),
                    "cost": round(s.cost, 4),
                    "risk": round(s.risk, 4),
                    "total": round(s.total(), 4),
                }
                for action, s in (
                    getattr(self.reasoning, "last_option_scores", None)
                    or getattr(getattr(self.reasoning, "deterministic", None), "last_option_scores", {})
                    or {}
                ).items()
            },
        }

        novel_spawned = self._spawn_curiosity_goals(evidence.detections)
        # North-star Phase 1a: an active investigate goal grounds its target
        # explicitly against the current frame (plan Step 5.3 — grounding
        # never runs implicitly; the goal asking IS the explicit ask).
        grounding = self._ground_for_active_goal()

        goal_was_active = self.goals.has_active
        # Autonomy state machine: AWARE → sub-states.
        now_sm2 = datetime.now(timezone.utc).isoformat()
        if self.autonomy_sm.state == ASMState.AWARE:
            if goal_was_active:
                t = self.autonomy_sm.transition("planning_needed", timestamp=now_sm2)
                self._emit("autonomy.transition", {"cycle": self._cycle, **t.snapshot()})
            elif any(d.label in {"person", "human", "face"} for d in evidence.detections):
                t = self.autonomy_sm.transition("interaction_started", timestamp=now_sm2)
                self._emit("autonomy.transition", {"cycle": self._cycle, **t.snapshot()})
        if goal_was_active:
            step_command = self.goals.step(
                self.body, cycle=self._cycle, resource_constrained=self._resource_constrained
            )
            action = step_command.action
            parameters = step_command.parameters
            reason = "goal_pursuit"
            # Persist the active goal's step progress each cycle so a mid-pursuit
            # kill (SIGKILL) resumes with the correct step budget, not a reset one.
            if self.goals.active is not None:
                self._persist_goal(self.goals.active)
        else:
            action = intent.action
            parameters = intent.parameters
            reason = intent.rationale

        # Multi-step planning context: advance the active goal's plan one step per cycle.
        active_plan: Plan | None = None
        if self.goals.active is not None:
            active_plan = self._plans.get(self.goals.active.goal.goal_id)
            if active_plan is not None and active_plan.status == "running":
                next_step = self.planner.advance(active_plan)
                if next_step is not None:
                    self._emit(
                        "plan.step",
                        {
                            "cycle": self._cycle,
                            "goal_id": active_plan.goal_id,
                            "description": next_step.description,
                            "kind": next_step.kind,
                        },
                    )
                elif active_plan.complete:
                    self._emit("plan.completed", {"goal_id": active_plan.goal_id, "plan_id": active_plan.plan_id})

        # Temporal & causal cognition: record this cycle's observed + acted events.
        events = set(present) | {f"action:{action}"}
        self.temporal.record(events, cycle=self._cycle, now=now)
        expected = []
        for entity in present:
            expected.extend(self.temporal.expected_after(entity, limit=2))
        if expected:
            self._emit(
                "cognition.temporal",
                {
                    "cycle": self._cycle,
                    "expected": [link.snapshot() for link in expected],
                    "timeline": self.temporal.timeline(limit=3),
                },
            )
        temporal_expected = [
            {"cause": link.cause, "effect": link.effect, "confidence": round(link.confidence, 3)} for link in expected
        ]

        body_before = self.body.snapshot()
        proposal = RuntimeActionProposal(
            action=action, parameters=parameters, reason=reason, correlation_id=str(uuid4())
        )
        decision = self.brain.propose(proposal)

        # Governance guard: a runtime guard between proposal and execution.
        # Models never command action; even deterministic actions pass it.
        risk_class = self._risk_class_for_action(action)
        gov_proposal = GovernanceActionProposal(
            proposal_id=proposal.correlation_id,
            action=action,
            parameters=parameters,
            risk_class=risk_class,
            source="deterministic",
            rationale=reason,
        )
        gov_grant = self.governance_guard.evaluate(gov_proposal)
        governance_allowed = gov_grant.is_allowed
        self._last_governance_grant = gov_grant.snapshot()
        self._emit(
            "governance.evaluated",
            {
                "cycle": self._cycle,
                "action": action,
                "risk_class": risk_class,
                "decision": gov_grant.decision,
                "reason": gov_grant.reason,
            },
        )

        # Confirmation flow (gap-analysis Step 3, item 18): a
        # REQUIRE_CONFIRMATION grant is surfaced as a pending request and the
        # action is held until confirm_action() grants it — it is not silently
        # treated as a denial.
        awaiting_confirmation = False
        if gov_grant.decision == REQUIRE_CONFIRMATION:
            awaiting_confirmation = True
            governance_allowed = False
            self._pending_confirmations[gov_grant.grant_id] = {
                "grant_id": gov_grant.grant_id,
                "proposal_id": proposal.correlation_id,
                "action": action,
                "parameters": dict(parameters),
                "risk_class": risk_class,
                "reason": reason,
                "cycle": self._cycle,
                "proposal": proposal,
                "decision": decision,
            }
            self._emit(
                "governance.confirmation_required",
                {
                    "cycle": self._cycle,
                    "grant_id": gov_grant.grant_id,
                    "proposal_id": proposal.correlation_id,
                    "action": action,
                    "parameters": dict(parameters),
                    "risk_class": risk_class,
                    "reason": gov_grant.reason,
                },
            )

        # Phase 2a: deterministic safety gate (doc 08) — the model and the
        # governance guard have spoken; the safety authority still evaluates
        # invariants + risk from world state before anything executes. Its
        # decision is computed here, never from model output (A-SAFE-01).
        safety_state = self._safety_world_state()
        safety_decision = self.safety_policy.evaluate(
            {"action": action, "risk_class": risk_class},
            safety_state,
        )
        safety_allowed = safety_decision.allowed and safety_decision.decision != "STOP"
        self._emit(
            "safety.evaluated",
            {
                "cycle": self._cycle,
                "action": action,
                "decision": safety_decision.decision,
                "allowed": safety_allowed,
                "reason": safety_decision.reason,
                "risk_class": safety_decision.risk_class or risk_class,
                "violated": list(safety_decision.violated_invariants),
            },
        )
        awaiting_safety_approval = False
        if safety_decision.decision == "STOP":
            # A STOP verdict is the e-stop form: latch the machine and hold.
            authorized = False
            t_stop = self.autonomy_sm.emergency_stop(timestamp=datetime.now(timezone.utc).isoformat())
            self._emit("autonomy.transition", {"cycle": self._cycle, **t_stop.snapshot()})
        elif not safety_decision.allowed:
            authorized = False
            self._emit(
                "safety.blocked",
                {
                    "cycle": self._cycle,
                    "action": action,
                    "reason": safety_decision.reason,
                    "violated": list(safety_decision.violated_invariants),
                },
            )
        elif safety_decision.decision == "MODIFY" and "approval" in safety_decision.reason:
            # MODIFY-with-approval-required routes into the same hold-for-
            # confirmation flow the governance guard uses (never silently
            # treated as a denial, never executed without the grant).
            awaiting_safety_approval = True
            authorized = False
            self._pending_confirmations[safety_decision.decision_id] = {
                "grant_id": safety_decision.decision_id,
                "proposal_id": proposal.correlation_id,
                "action": action,
                "parameters": dict(parameters),
                "risk_class": risk_class,
                "reason": safety_decision.reason,
                "cycle": self._cycle,
                "proposal": proposal,
                "decision": decision,
                "source": "safety_policy",
            }
            self._emit(
                "safety.confirmation_required",
                {
                    "cycle": self._cycle,
                    "grant_id": safety_decision.decision_id,
                    "proposal_id": proposal.correlation_id,
                    "action": action,
                    "reason": safety_decision.reason,
                },
            )

        # Action executes only if the brain authorizes AND the governance guard
        # allows AND the safety authority permits.
        authorized = decision.authorized and governance_allowed and safety_allowed

        # Skill contract: invoke the formal skill contract for this action.
        # If the skill's preconditions aren't met, the action is skipped.
        # Actions held for confirmation (governance or safety) are not invoked yet.
        skill_invocation = None
        if not (awaiting_confirmation or awaiting_safety_approval):
            skill_invocation = self._invoke_skill_for_action(action, parameters, goal_was_active)
        skill_passed = True
        if skill_invocation is not None:
            skill_passed = skill_invocation.status == SKILL_SUCCESS
            if not skill_passed:
                authorized = False
                self._emit(
                    "skill.failed",
                    {
                        "cycle": self._cycle,
                        "action": action,
                        "skill_id": skill_invocation.skill_id,
                        "error": skill_invocation.error,
                    },
                )
                # Report skill failure to the failure handler.
                failure = self.failure_handler.report_failure(
                    TOOL_FAILURE,
                    severity="warning",
                    component="skill_executor",
                    message=f"skill_{skill_invocation.skill_id}_failed: {skill_invocation.error}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                self._emit("failure.detected", {"cycle": self._cycle, **failure.snapshot()})
                self._apply_resource_adaptation()

        if authorized:
            # Phase 2c: physical authority boundary — the raw proposal never
            # reaches the body. It is compiled into a bounded, expiring
            # actuator command (allow-list, parameter bounds, one command per
            # cycle); a refusal here is final for this cycle.
            compiled = self.actuator_boundary.compile(
                action=action,
                parameters=parameters,
                risk_class=risk_class,
                source="deterministic",
                cycle=self._cycle,
                correlation_id=proposal.correlation_id,
            )
            if compiled.command is None:
                authorized = False
                actuator_command = None
                actuator_rejection = compiled.rejection or "UNKNOWN"
                self._emit(
                    "actuator.rejected",
                    {
                        "cycle": self._cycle,
                        "action": action,
                        "rejection": actuator_rejection,
                        "reason": compiled.reason,
                        "parameters": dict(parameters),
                    },
                )
                self.audit_trail.record(
                    correlation_id=self._cycle_correlation_id,
                    action=action,
                    decision_reason=f"actuator_boundary: {compiled.reason}",
                    policy_result=f"REJECTED:{actuator_rejection}",
                    safety_result="blocked_by_actuator_boundary",
                    outcome="not_executed",
                    goal_id=self.goals.active.goal.goal_id if self.goals.has_active else "",
                    action_id=proposal.correlation_id,
                    actor="actuator_boundary",
                    version="mac-brain",
                )
            else:
                actuator_command = compiled.command
                actuator_rejection = None
                self._emit(
                    "actuator.compiled",
                    {
                        "cycle": self._cycle,
                        "command_id": actuator_command.command_id,
                        "action": actuator_command.action,
                        "expires_cycle": actuator_command.expires_cycle,
                    },
                )
                # Expiry gate: an authorization that outlived its ttl cannot
                # reach the actuator (watchdog semantics at the chokepoint).
                if not self.actuator_boundary.is_live(actuator_command, cycle=self._cycle):
                    authorized = False
                    actuator_command = None
                    actuator_rejection = "EXPIRED"
                    self._emit(
                        "actuator.rejected",
                        {
                            "cycle": self._cycle,
                            "action": action,
                            "rejection": "EXPIRED",
                            "reason": "command validity window elapsed",
                        },
                    )
        else:
            actuator_command = None
            actuator_rejection = None
        if authorized:
            outcome = self.brain.execute(proposal, decision)
            virtual_state = self.body.execute(action, **parameters)
            # Phase 2a: RuntimeSafetyMonitor — safety CONTINUES while the
            # action executes (doc 08 §5): a previously approved action that
            # became unsafe is interrupted (fail closed) and the machine
            # latches to emergency stop.
            monitor_safe, monitor_reason = self.safety_monitor.check(
                {"action": action},
                self._safety_world_state(),
                cycle=self._cycle,
            )
            safety_interrupted = not monitor_safe
            if safety_interrupted:
                t_int = self.autonomy_sm.emergency_stop(timestamp=datetime.now(timezone.utc).isoformat())
                self._emit("autonomy.transition", {"cycle": self._cycle, **t_int.snapshot()})
                self._emit(
                    "safety.interrupted",
                    {
                        "cycle": self._cycle,
                        "action": action,
                        "reason": monitor_reason,
                    },
                )
                self.failure_handler.report_failure(
                    PERCEPTION_UNCERTAINTY,
                    severity="critical",
                    component="safety_monitor",
                    message=f"execution_interrupted: {monitor_reason}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                self._emit(
                    "failure.detected",
                    {
                        "cycle": self._cycle,
                        "component": "safety_monitor",
                        "message": f"execution_interrupted: {monitor_reason}",
                        "severity": "critical",
                    },
                )
            # Autonomy state machine: → EXECUTING.
            now_sm3 = datetime.now(timezone.utc).isoformat()
            if self.autonomy_sm.state in (ASMState.PLANNING, ASMState.AWARE):
                t = self.autonomy_sm.transition("execution_ready", timestamp=now_sm3)
                self._emit("autonomy.transition", {"cycle": self._cycle, **t.snapshot()})
        else:
            outcome = None
            safety_interrupted = False
            virtual_state = self.body.snapshot()
        self._emit(
            "action.completed",
            {
                "action": action,
                "authorized": authorized,
                "brain_authorized": decision.authorized,
                "governance_allowed": governance_allowed,
                "governance_decision": gov_grant.decision,
                "awaiting_confirmation": awaiting_confirmation or awaiting_safety_approval,
                "safety": safety_decision.snapshot(),
                "safety_interrupted": safety_interrupted,
                "skill_passed": skill_passed,
                "skill_invoked": skill_invocation is not None,
                "outcome": (
                    outcome.detail
                    if outcome
                    else (
                        "awaiting_confirmation"
                        if (awaiting_confirmation or awaiting_safety_approval)
                        else (
                            decision.reason
                            if not decision.authorized
                            else (gov_grant.reason if not gov_grant.is_allowed else safety_decision.reason)
                        )
                    )
                ),
                "virtual_body": virtual_state,
            },
        )
        # Persistent decision audit trace (doc 13): record the consequential
        # action with policy/safety results and outcome, in the cycle's
        # correlation domain, with goal/plan/action ids when available.
        self.audit_trail.record(
            correlation_id=self._cycle_correlation_id,
            action=action,
            decision_reason=reason,
            policy_result=gov_grant.decision if not gov_grant.is_allowed else f"ALLOW:{risk_class}",
            safety_result=(
                "executed"
                if authorized
                else (
                    "held"
                    if (awaiting_confirmation or awaiting_safety_approval)
                    else ("blocked_by_safety:" + safety_decision.reason if not safety_allowed else "blocked")
                )
            ),
            outcome=outcome.detail
            if outcome
            else ("held" if (awaiting_confirmation or awaiting_safety_approval) else "not_executed"),
            goal_id=self.goals.active.goal.goal_id if self.goals.has_active else "",
            action_id=proposal.correlation_id,
            actor="runtime",
            version="mac-brain",
        )
        # Reflection / self-correction: judge whether the action had its intended effect.
        body_after = self.body.snapshot()
        effective = self._action_effective(
            action,
            body_before,
            body_after,
            authorized,
            cognitive.situation.salient_entities,
            cognitive.reasoning.inferences,
        )
        reflection = self.reflection.record(
            cycle=self._cycle,
            action=action,
            intent=reason,
            effective=effective,
            note=self._reflection_note(action, effective),
        )
        self._emit("reasoning.reflection", {"cycle": self._cycle, **reflection.snapshot()})

        # Closed-loop ACT + VERIFY: first-class verification of the action outcome.
        # A denied action (not authorized) is recorded as DENIED, not FAILURE, so
        # the loop does not retry a policy-denied action.
        act_outcome = LOOP_DENIED if not authorized else (LOOP_SUCCESS if effective else LOOP_FAILURE)
        self.closed_loop.act({"action": action, "authorized": authorized, "outcome": act_outcome})
        verify_criteria = self._verify_criteria_for_action(action, goal_was_active)
        observed_state = {
            "action_executed": authorized,
            "body_changed": body_before != body_after,
            "effective": effective,
        }
        loop_verify = self.closed_loop.verify(verify_criteria, observed_state)
        self._last_loop_snapshot = self.closed_loop.snapshot()
        self._emit(
            "loop.verify",
            {
                "cycle": self._cycle,
                "phase": loop_verify.phase,
                "outcome": loop_verify.outcome,
                "met": self.closed_loop._verify_result.get("met", []),
                "unmet": self.closed_loop._verify_result.get("unmet", []),
            },
        )
        soul_success: bool | None = None
        if goal_was_active and not self.goals.has_active:
            terminal = self.goals.history[-1]
            soul_success = terminal.status is GoalStatus.COMPLETED
            self._emit(
                "goal.status",
                {
                    "goal_id": terminal.goal.goal_id,
                    "kind": terminal.goal.kind,
                    "status": terminal.status.value,
                    "steps_taken": terminal.steps_taken,
                },
            )
            self._admit_goal_outcome(terminal)
            self._persist_goal(terminal)
            terminal_plan = self._plans.get(terminal.goal.goal_id)
            if terminal_plan is not None and terminal_plan.status == "running":
                if terminal.status is GoalStatus.COMPLETED:
                    terminal_plan.status = "completed"
                    self._emit("plan.completed", {"goal_id": terminal.goal.goal_id, "plan_id": terminal_plan.plan_id})
                else:
                    self.planner.fail(terminal_plan)
                    self._emit("plan.failed", {"goal_id": terminal.goal.goal_id, "plan_id": terminal_plan.plan_id})
        goal_info = None
        if self.goals.history:
            last = self.goals.history[-1]
            goal_info = {
                "goal_id": last.goal.goal_id,
                "kind": last.goal.kind,
                "status": last.status.value,
                "steps_taken": last.steps_taken,
            }
        if (
            self.consolidator is not None
            and self.config.consolidation_enabled
            and self._cycle % self.config.consolidation_every == 0
        ):
            self.consolidate()
        self._sync_goal_states()

        observability = self._update_observability()

        uncertain = cognitive.reasoning.confidence < 0.5
        self.soul.update_for_cycle(
            success=soul_success, novel=novel_spawned is not None, speech=False, uncertain=uncertain
        )
        tone = self.soul.tone({"serious": uncertain})
        self._emit(
            "soul.updated",
            {
                "cycle": self._cycle,
                "tone": tone["tone"],
                "affect": self.soul.affect.dimensions,
                "motivations": self.soul.motivations,
            },
        )

        person = self._person_label(evidence.detections)
        social_expression = None
        if person is not None:
            self.relationships.note_interaction(person, positive=True, now=datetime.now(timezone.utc).isoformat())
            social_expression = self.social.expression(
                person, self.relationships, self.soul.affect.dimensions, {"serious": uncertain}
            )
            self._emit(
                "social.interaction",
                {
                    "cycle": self._cycle,
                    "person": person,
                    "category": self.relationships.category_for(person).value,
                    "expression": social_expression,
                },
            )
        initiative = self._maybe_initiate(person, has_active_goal=self.goals.has_active)
        # Plan 20: event-driven autonomous speech (GAP-A/B/C). If neglect-driven
        # initiative stayed silent, let a salient drained event seed a proactive
        # remark — gated by the same speaking-lease and social budget.
        autonomous = None
        if initiative is None:
            event_records = [r for r in consumed_inputs if r.get("kind") and r.get("payload") is not None]
            # Plan 22 Phase 10: the dialogue policy is the social decision
            # layer — run it each cycle and expose the decision for
            # observability (proactive candidates are gated by it and by the
            # anti-narration guard inside _maybe_autonomous_speech).
            self._run_dialogue_policy(
                event_records, evidence=evidence, goal_id=active_goal_ids[0] if active_goal_ids else None
            )
            autonomous = self._maybe_autonomous_speech(event_records, evidence.detections, person)
        # CommunicationDecision: advance fatigue cooldown each cycle.
        self.communication_decision.tick()
        # Autonomy state machine: return to OBSERVING after action completes.
        now_sm4 = datetime.now(timezone.utc).isoformat()
        if self.autonomy_sm.state in (
            ASMState.EXECUTING,
            ASMState.INTERACTING,
            ASMState.LEARNING,
            ASMState.MAINTENANCE,
        ):
            if not self.goals.has_active:
                t = self.autonomy_sm.transition("action_completed", timestamp=now_sm4)
                self._emit("autonomy.transition", {"cycle": self._cycle, **t.snapshot()})
        elif self.autonomy_sm.state == ASMState.AWARE and not self.goals.has_active and not evidence.detections:
            # Nothing significant — return to OBSERVING.
            t = self.autonomy_sm.transition("no_longer_significant", timestamp=now_sm4)
            self._emit("autonomy.transition", {"cycle": self._cycle, **t.snapshot()})
        # Episode recording: if recording is enabled, record this step.
        if self._recording_enabled and self.episode_recorder is not None:
            self.episode_recorder.record_runtime_step(self, cycle=self._cycle)
        # Phase P1 (sleep cycle): periodic memory-maturation pass on cadence.
        if self._sleep_cycle is not None:
            sleep_report = self._sleep_cycle.maybe_sleep(self._cycle)
            if sleep_report:
                self._emit("sleep.phase", sleep_report)
        # Phase 4b: retention sweep rides the same maturation cadence — the
        # store's expires_at is already honored at query time; the sweep
        # reconciles tombstones + capacity as an auditable pass.
        if self.retention_enforcer is not None and self._cycle % max(1, self.config.sleep_every_n_cycles) == 0:
            retention_report = self.retention_enforcer.sweep()
            if any([retention_report.expired_expired, retention_report.expired_ttl, retention_report.evicted]):
                self._emit("retention.swept", retention_report.snapshot())
        return {
            "run_id": self.run_id,
            "cycle": self._cycle,
            "frame_id": frame.frame_id,
            "detections": [d.label for d in evidence.detections],
            "consumed_inputs": consumed_inputs,
            "reasoning": cognitive.reasoning.conclusion,
            "reasoning_confidence": cognitive.reasoning.confidence,
            "reasoning_route": route_info,
            "typed_situation_id": (
                self._last_typed_cognition["situation"]["id"]
                if self._last_typed_cognition and self._last_typed_cognition.get("situation")
                else None
            ),
            "action": action,
            "authorized": authorized,
            "virtual_body": virtual_state,
            "goal": goal_info,
            "soul": {"tone": tone["tone"], "identity": self.soul.identity.name, "affect": self.soul.affect.dimensions},
            "identity": identity.snapshot() if identity is not None else None,
            "social": {"person": person, "expression": social_expression},
            "initiative": initiative,
            "autonomous": autonomous,
            "grounding": grounding,
            "actuator": {
                "command_id": actuator_command.command_id if actuator_command else None,
                "expires_cycle": actuator_command.expires_cycle if actuator_command else None,
                "rejection": actuator_rejection,
                "boundary": self.actuator_boundary.snapshot(),
            },
            "safety": {
                "decision": safety_decision.decision,
                "allowed": safety_allowed,
                "reason": safety_decision.reason,
                "risk_class": safety_decision.risk_class or risk_class,
                "violated": list(safety_decision.violated_invariants),
                "interrupted": safety_interrupted,
            },
            "temporal": {
                "expected": temporal_expected,
                "top_links": [link.snapshot() for link in self.temporal.top_links(limit=3)],
            },
            "fusion": fused_reported,
            "knowledge": self.knowledge.counts(),
            "hearing": {"events": self._last_audio_events},
            "observability": observability,
            "plan": active_plan.snapshot()
            if active_plan is not None and active_plan.status == "running"
            else (active_plan.snapshot() if active_plan else None),
            "communication": {
                "fatigue_level": self.communication_decision.fatigue_level,
                "interaction_count": self.communication_decision.interaction_count,
                "is_fatigued": self.communication_decision.is_fatigued,
            },
            "failure_handler": self.failure_handler.snapshot(),
            "autonomy_state": self.autonomy_sm.snapshot(),
        }

    def consolidate(self, now: str | None = None) -> None:
        """Run the memory consolidation/decay pass (durable store only)."""
        # Plan 22 Phase 3: object-instance housekeeping rides the same cadence
        # (LOST marking + persistence), independent of the consolidator.
        self._housekeep_object_registry()
        if self.consolidator is None:
            return
        report = self.consolidator.consolidate(now=now)
        self._emit(
            "memory.consolidated",
            {
                "cycle": self._cycle,
                "expired": report.expired,
                "archived": report.archived,
                "decayed": report.decayed,
                "superseded": report.superseded,
            },
        )
        if self.summary_consolidator is not None:
            summary = self.summary_consolidator.consolidate()
            if summary.created:
                self._emit(
                    "memory.summarized", {"cycle": self._cycle, "created": summary.created, "groups": summary.groups}
                )
        # Phase 4c: maturation passes also checkpoint the learning subsystems
        # (routines/corrections/reflections/lessons) so they survive kill -9.
        self.persist_learning()

    def _restore_learning(self) -> None:
        """Phase 4c: reload learned state from the durable store at startup."""
        if not isinstance(self.memory, DurableMemoryStore):
            return
        try:
            snapshot = self.memory.load_learning()
        except Exception:
            return  # corrupt blob: fail closed (fresh learning), never crash
        if not isinstance(snapshot, dict) or not snapshot:
            return  # empty or unparseable payload: fresh learning
        routines = snapshot.get("routines")
        if isinstance(routines, dict):
            self.routines.from_snapshot(routines)
        corrections = snapshot.get("corrections")
        if isinstance(corrections, list):
            self.corrections.restore(corrections)
        reflections = snapshot.get("reflections")
        if isinstance(reflections, list) and reflections:
            restored_reflection = ReflectionEngine.from_snapshot(reflections)
            self.reflection = restored_reflection
        lessons = snapshot.get("lessons")
        if isinstance(lessons, dict) and lessons:
            self.lessons.from_snapshot(lessons)
        promotions = snapshot.get("promotions")
        if isinstance(promotions, dict) and promotions:
            self.learning.from_snapshot(promotions)
        counterfactuals = snapshot.get("counterfactuals")
        if isinstance(counterfactuals, dict) and counterfactuals:
            self.counterfactuals.from_snapshot(counterfactuals)
        if getattr(self, "event_bus", None) is not None:  # startup: bus not ready yet
            self._emit(
                "learning.restored",
                {
                    "routines": len(self.routines.routines()),
                    "corrections": len(self.corrections.records()),
                },
            )

    def persist_learning(self) -> None:
        """Phase 4c: write the learning subsystems' snapshots to the store."""
        if not isinstance(self.memory, DurableMemoryStore):
            return
        self.memory.save_learning(
            {
                "cycle": self._cycle,
                "routines": self.routines.snapshot(),
                "corrections": self.corrections.snapshot(),
                "reflections": self.reflection.snapshot(),
                "lessons": self.lessons.snapshot(),
                "promotions": self.learning.snapshot(),
                "counterfactuals": self.counterfactuals.snapshot(),
            }
        )

    def set_goal(self, goal: Goal, *, cycle: int | None = None) -> GoalState:
        """Adopt a bounded goal for the autonomy layer to pursue."""
        cycle = self._cycle if cycle is None else cycle
        state = self.goals.adopt(goal)
        plan = self.planner.plan(goal, cycle=cycle)
        self.planner.start(plan)
        self._plans[goal.goal_id] = plan
        # Plan validation (doc 05 §Plan Validation): a valid plan is not
        # automatically authorized; validation verdict is emitted for audit.
        validation = self.planner.validate(plan, available_actions=getattr(self.body, "ALLOWED_ACTIONS", None))
        self._emit(
            "plan.validated",
            {
                "goal_id": goal.goal_id,
                "plan_id": plan.plan_id,
                "valid": validation.valid,
                "issues": list(validation.issues),
            },
        )
        self._emit(
            "plan.created",
            {"goal_id": goal.goal_id, "goal_kind": goal.kind, "plan_id": plan.plan_id, "steps": len(plan.steps)},
        )
        self._emit(
            "goal.adopted",
            {"goal_id": goal.goal_id, "kind": goal.kind, "target": str(goal.target), "max_steps": goal.max_steps},
        )
        self._persist_goal(state)
        return state

    def _maybe_replan_for_violation(self, target: str, kind: str) -> Plan | None | str:
        """Phase 3c: close the prediction-error -> plan-revision loop.

        When a prediction/expectation violation invalidates the active plan's
        assumptions, the plan is marked FAILED and a fresh plan is generated
        for the same goal (the north star's revise step). Idle brains are a
        no-op; revisions are throttled to one per goal per cycle and audited.
        """
        active = self.goals.active if self.goals.has_active else None
        if active is None:
            return "no_active_goal"
        goal_id = active.goal.goal_id
        plan = self._plans.get(goal_id)
        if plan is None or plan.status != "running":
            return "no_running_plan"
        if self._replan_throttle.get(goal_id, -999) >= self._cycle:
            return "throttled"
        self._replan_throttle[goal_id] = self._cycle
        self.planner.fail(plan, reason=f"{kind}:{target}")
        self._emit("plan.failed", {"goal_id": goal_id, "plan_id": plan.plan_id, "reason": f"{kind}:{target}"})
        revised = self.replan_goal(goal_id)
        self._emit(
            "plan.revised",
            {
                "goal_id": goal_id,
                "failed_plan_id": plan.plan_id,
                "new_plan_id": (revised.plan_id if revised else None),
                "trigger": kind,
                "target": str(target),
            },
        )
        return revised

    def replan_goal(self, goal_id: str, *, cycle: int | None = None) -> Plan | None:
        """Rebuild a fresh plan for a goal when assumptions are invalidated."""
        cycle = self._cycle if cycle is None else cycle
        state = (
            self.goals.active if self.goals.active is not None and self.goals.active.goal.goal_id == goal_id else None
        )
        if state is None:
            state = next((s for s in self.goals.pending_goals if s.goal.goal_id == goal_id), None)
        if state is None:
            return None
        plan = self.planner.replan(state.goal, cycle=cycle)
        self.planner.start(plan)
        self._plans[goal_id] = plan
        self._emit("plan.replanned", {"goal_id": goal_id, "plan_id": plan.plan_id, "steps": len(plan.steps)})
        return plan

    def current_plan(self) -> Plan | None:
        if self.goals.active is None:
            return None
        return self._plans.get(self.goals.active.goal.goal_id)

    def enqueue_goal(self, goal: Goal, *, cycle: int | None = None) -> GoalState:
        """Queue a goal for priority-based pursuit (higher priority runs first).

        A queued goal with higher priority than the active goal safely supersedes
        it on the next cycle.
        """
        state = self.goals.enqueue(goal)
        self._emit(
            "goal.queued",
            {
                "goal_id": goal.goal_id,
                "kind": goal.kind,
                "priority": goal.priority,
                "pending": self.goals.pending_count,
            },
        )
        return state

    def _sync_goal_states(self) -> None:
        """Persist current goal lifecycle states to the durable store."""
        if not isinstance(self.memory, DurableMemoryStore):
            return
        for state in self.goals.history:
            if state.status in (GoalStatus.SUPERSEDED, GoalStatus.COMPLETED, GoalStatus.FAILED):
                if state.goal.goal_id in self._persisted_terminal:
                    continue
                self._persist_goal(state)
                self._persisted_terminal.add(state.goal.goal_id)
        for state in self.goals.pending_goals:
            self._persist_goal(state)
        if self.goals.active is not None:
            self._persist_goal(self.goals.active)

    def _persist_goal(self, state: Any) -> None:
        if isinstance(self.memory, DurableMemoryStore):
            self.memory.save_goal(
                goal_id=state.goal.goal_id,
                kind=state.goal.kind,
                target=state.goal.target,
                priority=state.goal.priority,
                max_steps=state.goal.max_steps,
                created_cycle=state.goal.created_cycle,
                status=state.status.value,
                steps_taken=state.steps_taken,
            )

    def _load_goals(self) -> None:
        """Rebuild active/pending/terminal goal state into the controller on restart.

        Closes the resume-goals-across-restart gap: a bounded goal adopted before
        shutdown is resumed (not lost) when the brain restarts against the same
        durable store. The active goal keeps its step budget, so resumed goals
        remain bounded.
        """
        if not isinstance(self.memory, DurableMemoryStore):
            return
        rows = self.memory.goals()
        active: GoalState | None = None
        for row in rows:
            target = row["target"]
            if isinstance(target, (list, tuple)) and len(target) == 2:
                target = (float(target[0]), float(target[1]))  # reach targets reload as tuples
            goal = Goal(
                goal_id=row["goal_id"],
                kind=row["kind"],
                target=target,
                priority=row["priority"],
                max_steps=int(row["max_steps"] or 0),
                created_cycle=int(row["created_cycle"] or 0),
            )
            status = GoalStatus(row["status"])
            state = GoalState(goal, status, int(row["steps_taken"] or 0))
            if status is GoalStatus.ACTIVE:
                # latest active wins; an earlier active row is safely superseded
                if active is None or goal.created_cycle >= active.goal.created_cycle:
                    if active is not None:
                        active.status = GoalStatus.SUPERSEDED
                        self._persisted_terminal.add(active.goal.goal_id)
                        self.goals.history.append(active)
                    active = state
            elif status is GoalStatus.PENDING:
                self.goals.enqueue(goal)
            else:  # terminal: completed / failed / superseded
                self._persisted_terminal.add(goal.goal_id)
                self.goals.history.append(state)
        if active is not None:
            self.goals.active = active
            self.goals.history.append(active)
            if active.goal.goal_id not in self._plans:
                plan = self.planner.plan(active.goal, cycle=active.goal.created_cycle)
                self.planner.start(plan)
                self._plans[active.goal.goal_id] = plan

    def _spawn_curiosity_goals(self, detections: Any) -> None:
        """Autonomously create a bounded investigate goal for a novel entity.

        A novel entity is one never before seen by this brain. When perception
        surfaces one and no goal is active, curiosity creates a bounded
        investigate goal (a goal source, per 04_GOALS_CURIOSITY_AND_LEARNING.md)
        rather than acting as a one-shot reaction. It never interrupts an active
        goal; it only fills the idle gap.
        """
        novel: list[str] = []
        for detection in detections:
            if detection.label not in self._seen_entities:
                novel.append(detection.label)
            self._seen_entities.add(detection.label)
        if not self.config.curiosity_enabled or self.goals.has_active or not novel:
            return None
        label = novel[0]
        goal = Goal.investigate(label, max_steps=self.config.curiosity_investigate_steps, created_cycle=self._cycle)
        self.set_goal(goal)
        self._emit("curiosity.triggered", {"entity": label, "goal_id": goal.goal_id, "max_steps": goal.max_steps})
        return label

    def _spawn_surprise_goal(self, target: str) -> None:
        """Plan 19, Phase 3: investigate a *missing* entity after a sequence
        violation.

        When Novi expected B after A but B never appeared, the surprise signal
        drives a bounded investigate goal for the missing target — "I expected
        the cup near the book — did someone move it?". Only fires when idle and
        curiosity is enabled; never interrupts an active goal.
        """
        if not self.config.curiosity_enabled or self.goals.has_active:
            return
        goal = Goal.investigate(target, max_steps=self.config.curiosity_investigate_steps, created_cycle=self._cycle)
        self.set_goal(goal)
        self._emit("curiosity.surprise_goal", {"entity": target, "goal_id": goal.goal_id, "max_steps": goal.max_steps})

    def listen(self, seconds: float = 3.0, *, output_dir: Path | None = None) -> dict[str, Any]:
        """Record from the microphone, transcribe locally, and ingest into cognition/memory."""
        output_dir = output_dir or Path("mac_test_results/STT")
        recording = self.microphone.record(seconds, output_dir)
        self._emit(
            "audio.recording.completed",
            {"recording_id": recording.recording_id, "duration_s": recording.duration_s, "path": str(recording.path)},
        )
        transcription = self.stt.transcribe(recording.path)
        self._emit(
            "stt.completed",
            {
                "recording_id": recording.recording_id,
                "text": transcription.text,
                "language": transcription.language,
                "confidence": transcription.confidence,
                "model_id": transcription.model_id,
            },
        )
        self._identify_speaker({"audio_path": str(recording.path)})
        ingested = self.ingest_transcript(transcription)
        return {"transcription": transcription, **ingested}

    def ingest_transcript(self, transcription: TranscriptionResult) -> dict[str, Any]:
        """Feed a transcript into memory (durable) and cognition (transient speech event)."""
        self.social_initiative.note_addressed(self._cycle)
        # Conversation-activity guard: any real user utterance (chat or voice)
        # resets the mid-dialogue initiative window so spontaneous "it's quiet
        # around here." remarks never interrupt an active conversation.
        self._last_user_utterance_cycle = self._cycle
        entity_refs = self._entities_in_text(transcription.text)
        # Only a speech self-introduction ("i am Maya", "my name is Maya") binds
        # the speaker's name — mentioning a third party does not invent an
        # identity (gap-audit Phase A2).
        introduced = _extract_self_name(transcription.text)
        if introduced:
            introduced = introduced.lower()
            self.identity.observe(
                "person", name=introduced, confidence=transcription.confidence, modality="speech", cycle=self._cycle
            )
            self._observe_person_registry(
                "person",
                name=introduced,
                confidence=transcription.confidence,
                modality="speech",
                cycle=self._cycle,
            )
            self._persist_identity()
            self._emit(
                "identity.named", {"cycle": self._cycle, "name": introduced, "confidence": transcription.confidence}
            )
        self._learn_triples(transcription.text, entity_refs, transcription.confidence, source="audio.stt")
        classification = self.governance.classify(
            memory_type="utterance", content=transcription.text, entity_refs=entity_refs, modality="speech"
        )
        allowed, mem_class = self._gate_memory("utterance")
        admission = None
        if allowed:
            admission = self.memory.admit(
                memory_type="utterance",
                content=transcription.text,
                confidence=transcription.confidence,
                verification_status="verified" if transcription.confidence >= 0.7 else "unverified",
                privacy_class=classification.privacy_class,
                provenance={
                    "source": "audio.stt",
                    "provider": transcription.provider,
                    "model_id": transcription.model_id,
                    "audio_path": transcription.audio_path,
                    "memory_class": mem_class,
                },
                entity_refs=entity_refs,
                temporal_context=self._temporal_context(),
                spatial_context=self._spatial_context(),
            )
        if admission is not None:
            self._emit(
                "memory.admitted",
                {
                    "memory_id": admission.memory_id,
                    "memory_type": "utterance",
                    "accepted": admission.accepted,
                    "entity_refs": list(entity_refs),
                },
            )
        if admission is not None and admission.accepted and admission.memory_id:
            self.governance.govern(
                admission.memory_id, privacy_class=classification.privacy_class, purpose=self.governance.default_purpose
            )

        speech = SensorObservation(
            cycle=self._cycle,
            source="audio.stt",
            entity=DeterministicCognition.SPEECH_ENTITY,
            location=None,
            state="heard",
            confidence=transcription.confidence,
            captured_cycle=self._cycle,
        )
        cognitive = self.cognition.cycle(self.unified_world.to_world_state(), (speech,), cycle=self._cycle)
        self._emit(
            "cognition.completed",
            {
                "cycle": self._cycle,
                "conclusion": cognitive.reasoning.conclusion,
                "confidence": cognitive.reasoning.confidence,
                "source": "audio.stt",
            },
        )
        # Skill priming for the audio path (plan 16 P4 symmetry): heard speech
        # activates relevant skills just like vision cycles do.
        self.skill_activator.expire(self._cycle)
        self.skill_activator.observe_cycle(
            cycle=self._cycle,
            heard=transcription.text[:400],
            narrative=str(cognitive.reasoning.conclusion or "")[:300],
        )
        now = datetime.now(timezone.utc).isoformat()
        self._pending_speech.append(
            ModalityObservation(
                modality="speech",
                entity=DeterministicCognition.SPEECH_ENTITY,
                value="heard",
                confidence=transcription.confidence,
                captured_at=now,
                received_at=now,
                source="audio.stt",
            )
        )
        self._emit(
            "speech.ingested",
            {
                "text": transcription.text,
                "memory_id": (admission.memory_id if admission else None),
                "reasoning": cognitive.reasoning.conclusion,
            },
        )
        return {
            "admission": admission,
            "speech_observation": speech,
            "reasoning": cognitive.reasoning.conclusion,
            "confidence": cognitive.reasoning.confidence,
        }

    def ingest_audio_frame(self, frame: AudioFrame) -> dict[str, Any]:
        """Hear a non-speech acoustic frame: detect events, monitor quality, admit
        significant events to memory, and feed audio evidence into multimodal fusion."""
        now = datetime.now(timezone.utc).isoformat()
        events = self.hearing.detect(frame)
        quality = self.hearing.quality(frame)
        admitted: list[str] = []
        for event in events:
            self._emit("hearing.event", {"cycle": self._cycle, **event.snapshot()})
            if event.speech:
                self._emit("hearing.voice", {"cycle": self._cycle, **event.snapshot()})
            if event.anomaly:
                anomaly = {
                    "cycle": self._cycle,
                    "event_type": event.event_type,
                    "novelty": event.novelty,
                    "direction_deg": event.direction_deg,
                }
                self._emit("hearing.anomaly", anomaly)
                # GAP-1b: also route the anomaly through the input bus so the
                # salience evaluator can seed a proactive remark about it.
                self.submit("hearing", "hearing.anomaly", anomaly)
            if self.hearing.worth_attention(event):
                classification = self.governance.classify(
                    memory_type="audio_event", content=event.snapshot(), entity_refs=(), modality="audio"
                )
                allowed, mem_class = self._gate_memory("audio_event")
                admission = None
                if allowed:
                    admission = self.memory.admit(
                        memory_type="audio_event",
                        content=event.snapshot(),
                        confidence=event.confidence,
                        verification_status="verified" if event.confidence >= 0.7 else "unverified",
                        privacy_class=classification.privacy_class,
                        provenance={"source": "audio.sed", "event_type": event.event_type, "memory_class": mem_class},
                        temporal_context=self._temporal_context(),
                        spatial_context=self._spatial_context(),
                    )
                if admission is not None and admission.accepted and admission.memory_id:
                    self.governance.govern(
                        admission.memory_id,
                        privacy_class=classification.privacy_class,
                        purpose=self.governance.default_purpose,
                    )
                    admitted.append(admission.memory_id)
                    self._emit(
                        "memory.admitted",
                        {
                            "memory_id": admission.memory_id,
                            "memory_type": "audio_event",
                            "accepted": admission.accepted,
                            "event_type": event.event_type,
                        },
                    )
            self._pending_audio.append(self.hearing.to_modality_observation(event, received_at=now))
        self._emit("hearing.quality", {"cycle": self._cycle, **quality.snapshot()})
        self._last_audio_events = [e.snapshot() for e in events]
        return {"events": [e.snapshot() for e in events], "quality": quality.snapshot(), "admitted": admitted}

    def _apply_resource_adaptation(self) -> None:
        """Map failure-handler degraded mode + real telemetry to a resource mode.

        Gap-analysis Step 3, item 19 (resource-aware behavioral adaptation):
        when a subsystem is degraded the runtime must run in a matching resource
        mode instead of always assuming FULL resources. The failure-handler
        mode is combined with a live host telemetry sample (CPU/memory
        pressure); the more conservative of the two wins.
        """
        mode = self.failure_handler.degraded_mode
        if mode == DegradedMode.NORMAL:
            failure_mode = ResourceMode.FULL
        elif mode in (DegradedMode.PERCEPTION_DEGRADED, DegradedMode.IDENTITY_DEGRADED):
            # Perception is unreliable: react deterministically, skip deliberation.
            failure_mode = ResourceMode.REACTIVE_ONLY
        elif mode == DegradedMode.SAFETY_ONLY:
            failure_mode = ResourceMode.SAFE_MINIMUM
        else:  # reasoning/memory degraded
            failure_mode = ResourceMode.DEGRADED

        # Real telemetry feed: sample host pressure and fold it in.
        sample = self.telemetry.sample()
        self._last_resource_sample = sample.snapshot()
        telemetry_mode = self.telemetry.to_resource_mode(sample)
        resource_mode = combine_resource_modes(failure_mode, telemetry_mode)

        self.multi_speed.set_resource_mode(resource_mode)
        if resource_mode == ResourceMode.SAFE_MINIMUM:
            self.multi_speed.set_state(AutonomyState.SAFE_MINIMUM)
        elif resource_mode == ResourceMode.REACTIVE_ONLY or resource_mode == ResourceMode.DEGRADED:
            self.multi_speed.set_state(AutonomyState.DEGRADED)
        elif self.multi_speed.state not in (AutonomyState.INTERRUPTED,):
            self.multi_speed.set_state(AutonomyState.ACTIVE)
        self._emit(
            "resource.telemetry", {"cycle": self._cycle, **sample.snapshot(), "resource_mode": resource_mode.value}
        )

    def _admit_detections(self, detections: Any) -> None:
        for detection in detections:
            allowed, mem_class = self._gate_memory("perception")
            admission = None
            if allowed:
                classification = self.governance.classify(
                    memory_type="perception",
                    content={"label": detection.label, "confidence": detection.confidence},
                    entity_refs=(detection.label,),
                    modality="vision",
                )
                admission = self.memory.admit(
                    memory_type="perception",
                    content={
                        "label": detection.label,
                        "confidence": detection.confidence,
                        "bbox": list(detection.bbox_xyxy),
                    },
                    confidence=detection.confidence,
                    verification_status="verified" if detection.confidence >= 0.7 else "unverified",
                    privacy_class=classification.privacy_class,
                    provenance={
                        "source": self.config.sensor_id,
                        "capability": "vision.object_detection",
                        "memory_class": mem_class,
                        "importance": self._importance_for(detection.label, detection.confidence),
                    },
                    entity_refs=(detection.label,),
                    temporal_context=self._temporal_context(),
                    spatial_context=self._spatial_context(),
                )
            else:
                classification = None
            if admission is not None and admission.accepted and admission.memory_id:
                self.governance.govern(
                    admission.memory_id,
                    privacy_class=classification.privacy_class,
                    purpose=self.governance.default_purpose,
                )
            self._emit(
                "memory.admitted",
                {
                    "memory_id": (admission.memory_id if admission else None),
                    "memory_type": "perception",
                    "accepted": bool(admission and admission.accepted),
                    "entity": detection.label,
                },
            )

    def _update_unified_world(self, detections: Any) -> None:
        """Update the unified WorldModel with perception detections.

        Each detection is admitted as a typed entity with epistemic status
        OBSERVED (or UNKNOWN if confidence is very low). Known entity labels
        from the knowledge graph and person identity are used to assign
        entity types.
        """
        now = datetime.now(timezone.utc).isoformat()
        from .kgraph import infer_entity_type

        for detection in detections:
            label = detection.label
            entity_type = infer_entity_type(label)
            # Map kgraph types to world_model types.
            wm_type = {
                "person": WM_PERSON,
                "place": WM_PLACE,
                "building": WM_BUILDING,
                "object": WM_OBJECT,
            }.get(entity_type, WM_OBJECT)
            entity_id = f"det:{label}:{self._cycle}"
            # Check if this label is already in the world model (by label).
            existing = self.unified_world.resolve(label)
            if existing is not None:
                entity_id = existing.entity_id
            else:
                self.unified_world.add_entity(
                    entity_id,
                    wm_type,
                    labels=[label],
                    epistemic_status=WM_OBSERVED if detection.confidence >= 0.5 else WM_UNKNOWN,
                    confidence=detection.confidence,
                    created_at=now,
                )
            self.unified_world.update_entity_state(
                entity_id,
                "presence",
                "present",
                epistemic_status=WM_OBSERVED,
                confidence=detection.confidence,
                source=self.config.sensor_id,
                timestamp=now,
            )
            self._seen_entities.add(entity_id)

    # -- North-star Phase 1a: vision pipeline as the perception path ----------

    def _run_perception_pipeline(self, frame: Any, evidence: PerceptionEvidence) -> PerceptionEvidence:
        """Run the vision pipeline as the camera perception path (Phase 1a).

        `PerceptionPipeline.process_frame` produces a WorldObservation
        (detections + active tracks + identities) that is admitted into the
        unified world model with track-stable entity ids (`track-<id>`)
        instead of the legacy per-cycle `det:<label>:<cycle>` ids. The
        pipeline's detections then become the cycle's evidence so memory
        admission, beliefs, identity, attention, and curiosity all see the
        same pipeline results. Fail-closed: a pipeline crash degrades to the
        specialist evidence for this cycle (reported, never invented).
        """
        try:
            observation = self.perception_pipeline.process_frame(frame)
        except Exception as exc:
            self._emit(
                "failure.detected",
                {
                    "cycle": self._cycle,
                    "component": "vision_pipeline",
                    "message": f"process_frame_failed: {exc}",
                    "severity": "warning",
                },
            )
            self.failure_handler.report_failure(
                PERCEPTION_UNCERTAINTY,
                severity="warning",
                component="vision_pipeline",
                message=f"process_frame_failed: {exc}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            return evidence
        self._last_world_observation = observation
        self._emit(
            "perception.vision_observation",
            {
                "frame_id": observation.frame_id,
                "tracked": len(observation.tracks),
                "detections": [d.label for d in observation.detections],
                "identities": len(observation.identities),
                "grounding_backend": self.perception_pipeline.grounding_backend is not None,
            },
        )
        self._admit_world_observation(observation)
        # Convert to the brain-side evidence shape so every downstream
        # consumer (memory admission, beliefs, identity, fusion, attention,
        # curiosity) sees the pipeline results as the cycle's evidence.
        b2_detections = tuple(
            B2Detection(
                label=d.label,
                confidence=d.confidence,
                bbox_xyxy=(
                    float(d.bbox[0]),
                    float(d.bbox[1]),
                    float(d.bbox[0] + d.bbox[2]),
                    float(d.bbox[1] + d.bbox[3]),
                ),
            )
            for d in observation.detections
        )
        return replace(
            evidence,
            detections=b2_detections,
            provenance={**evidence.provenance, "vision_pipeline": "novi.perception"},
        )

    def _admit_world_observation(self, observation: Any) -> None:
        """Admit a perception WorldObservation into the unified world model.

        Track-stable entity ids (`track-<id>`) keep one entity per tracked
        object across frames (replacing the legacy per-cycle recreation);
        status follows the legacy rule (OBSERVED when confidence >= 0.5, else
        UNKNOWN). Hypothetical candidates are admitted ONLY through the
        explicit grounding path (`ground_scene` ->
        world_state_adapter.admit_grounding_outcome): candidates can never
        overwrite observed state (epistemic discipline).

        Plan 22 (Phase 1): the admission now flows through the canonical
        Observation contract (novi.brain.observation) — the same normalized
        shape used by fusion, grounding and identity — and attaches the
        measurement uncertainty (sigma) and spatial_ref to world entities.
        """
        from .observation import apply_observation_to_world, observation_from_world_observation

        now = datetime.now(timezone.utc).isoformat()
        for obs in observation_from_world_observation(observation):
            entity_id = apply_observation_to_world(
                self.unified_world,
                obs,
                source=self.config.sensor_id,
                timestamp=now,
            )
            if entity_id is not None:
                self._seen_entities.add(entity_id)
            # Plan 22 Phase 3: instance identity + object events (moved /
            # reappeared / ...). Events are evidence for salience, never speech.
            self._observe_object_registry(obs, now=now)

    def ground_scene(self, query_text: str, *, policy: Any | None = None, requester: str = "brain") -> dict[str, Any]:
        """Explicit language-grounding capability (Phase 1a; plan Step 5.3).

        Grounds `query_text` against the most recent camera frame through the
        vision pipeline and admits the GroundingOutcome into the unified world
        model via novi.perception.world_state_adapter.admit_grounding_outcome:
        associated observations update their track entity (OBSERVED); unmatched
        observations become HYPOTHESIZED candidates that can never overwrite
        observed state. Fail-closed: without a pipeline, a grounding backend,
        or a frame, NOTHING is admitted — absence is never inferred from a
        failure.
        """
        if self.perception_pipeline is None:
            return {"grounded": False, "reason": "no_vision_pipeline"}
        if self.perception_pipeline.grounding_backend is None:
            return {"grounded": False, "reason": "no_grounding_backend"}
        frame = self._last_frame
        if frame is None:
            return {"grounded": False, "reason": "no_frame"}
        from novi.perception.grounding import SpatialInferencePolicy, SpatialQuery
        from novi.perception.world_state_adapter import admit_grounding_outcome

        grounding_policy = policy or SpatialInferencePolicy()
        query = SpatialQuery(
            text=query_text,
            frame_id=frame.frame_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            requester=requester,
        )
        try:
            outcome = self.perception_pipeline.ground_frame(frame, query, grounding_policy)
            summary = admit_grounding_outcome(self.unified_world, outcome)
        except Exception as exc:
            self._emit(
                "failure.detected",
                {
                    "cycle": self._cycle,
                    "component": "vision_pipeline",
                    "message": f"ground_frame_failed: {exc}",
                    "severity": "warning",
                },
            )
            return {"grounded": False, "reason": f"grounding_error: {exc}"}
        self._emit(
            "perception.grounded",
            {
                "frame_id": frame.frame_id,
                "query": query_text,
                "requester": requester,
                "created": summary.created,
                "updated": summary.updates,
                "candidates": summary.candidates,
                "success": bool(outcome.result.success),
                "no_object": bool(outcome.result.no_object),
            },
        )
        return {
            "grounded": True,
            "frame_id": frame.frame_id,
            "created": summary.created,
            "updated": summary.updates,
            "candidates": summary.candidates,
        }

    def _ground_for_active_goal(self) -> dict[str, Any] | None:
        """Ground an active investigate goal's target (explicit ask, Step 5.3).

        A curiosity-spawned investigate goal is the explicit ask: grounding
        runs once for this cycle against the current frame and is skipped
        entirely when no pipeline/grounding backend is attached.
        """
        if self.perception_pipeline is None:
            return None
        active = self.goals.active
        if active is None or active.goal.kind != "investigate":
            return None
        return self.ground_scene(str(active.goal.target), requester="curiosity_goal")

    # Risk class mapping for governance (docs/02-autonomy/09 §Risk Classes).
    # In the brain phase, the body is virtual (simulated actuation), so
    # movement actions are R1 (reversible digital) not R3 (physical movement).
    _R0_ACTIONS = frozenset({"wait", "observe", "stop", "idle"})
    _R1_ACTIONS = frozenset({"speak", "move_forward", "turn_left", "turn_right"})

    def default_llm_chat(self, *, force: bool = False) -> Any:
        """Phase 3e: the brain's OWN default LLM transport (brain owns the reply).

        Resolution order:
          1. an injected callable (tiering override by a surface) wins;
          2. the brain-built Ollama transport, when ``brain_llm_enabled``;
          3. None (no transport -> deterministic fallback paths).

        Unreachable endpoints degrade to None with a cooldown so a downed
        model neither raises nor gets hammered per message. Claims: the
        no-assistant/no-repetition guardrails in the reply pipeline still
        apply to every brain-default reply.
        """
        if self._override_llm_chat is not None:
            return self._override_llm_chat
        # Plan 25: the trained-adapter transport (talk with the trained data)
        # outranks the generic Ollama transport when enabled and configured.
        if self.config.trained_reply_enabled:
            transport = self._trained_reply_transport()
            if transport is not None:
                return transport
        if not self.config.brain_llm_enabled:
            return None
        if not force and time.monotonic() < self._llm_unreachable_until:
            return None
        if self._brain_llm_chat is None:
            if not self._brain_llm_reachable():
                # Downed endpoint: back off instead of hammering per message.
                self._llm_unreachable_until = time.monotonic() + float(self.config.brain_llm_probe_cooldown_s)
                self._emit(
                    "llm.unreachable",
                    {
                        "url": self.config.brain_llm_url,
                        "cooldown_s": float(self.config.brain_llm_probe_cooldown_s),
                    },
                )
                return None
            self._brain_llm_chat = self._build_brain_llm_chat()
        return self._brain_llm_chat

    def _brain_llm_reachable(self) -> bool:
        if (self.config.brain_llm_server or "ollama") == "openai-compatible":
            from .models.chat_server import OpenAICompatibleChatServer

            return OpenAICompatibleChatServer(self.config.brain_llm_url).probe(
                self.config.brain_llm_model or "brain-default"
            )
        import urllib.request

        try:
            req = urllib.request.Request(f"{self.config.brain_llm_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    def _brain_llm_call(self, *, system: str, user: str, temperature: float = 0.5, timeout: int = 120) -> str | None:
        """One chat call through the brain's own transport.

        Speaks the configured dialect (native Ollama /api/* by default,
        OpenAI-compatible /v1 when selected). Returns None on any failure —
        the reply pipeline's deterministic fallback applies (never raises
        into cognition).
        """
        if (self.config.brain_llm_server or "ollama") == "openai-compatible":
            from .models.chat_server import OpenAICompatibleChatServer

            return OpenAICompatibleChatServer(self.config.brain_llm_url).chat(
                model=self.config.brain_llm_model or "brain-default",
                system=system,
                user=user,
                temperature=temperature,
                timeout=timeout,
            )
        import json
        import urllib.request

        model = self.config.brain_llm_model or "brain-default"
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            req = urllib.request.Request(
                f"{self.config.brain_llm_url}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            return (data.get("message") or {}).get("content")
        except Exception:
            return None

    def _build_brain_llm_chat(self) -> Any:
        """Build the brain-owned chat callable once (endpoint already probed)."""
        return lambda *, system, user, temperature=0.5, timeout=120: self._brain_llm_call(
            system=system,
            user=user,
            temperature=temperature,
            timeout=timeout,
        )

    def _trained_reply_transport(self) -> Any:
        """Lazily build the trained-adapter transport (plan 25, Part A).

        Returns None when no adapter dir is configured, so the resolution falls
        through to the Ollama transport / deterministic fallback unchanged.
        """
        if self._trained_transport is None:
            if not (self.config.trained_dialogue_adapter or self.config.trained_emotional_adapter):
                return None
            from .trained_reply import TrainedReplyTransport

            self._trained_transport = TrainedReplyTransport(
                dialogue_adapter=self.config.trained_dialogue_adapter,
                emotional_adapter=self.config.trained_emotional_adapter,
                base_model=self.config.trained_base_model,
            )
        return self._trained_transport

    def _sync_robot_world_state(self) -> None:
        """Phase 1c: maintain the ROBOT self-entity in the unified world model.

        The robot is a first-class world-model citizen: its metric pose links
        to the SpatialMap (spatial_ref), and its semantic ``location`` derives
        from SpatialMap.region_at(body pose). Local odometry is exact in the
        virtual phase, so pose σ = 0 (confidence 1.0).
        """
        body_now = self.body.snapshot()
        x = float(body_now.get("x_m", 0.0))
        y = float(body_now.get("y_m", 0.0))
        now = datetime.now(timezone.utc).isoformat()
        robot = self.unified_world.add_entity(
            "robot",
            ROBOT_WM,
            labels=["novi"],
            epistemic_status=WM_OBSERVED,
            confidence=1.0,
            created_at=now,
        )
        region = self.spatial.region_at(x, y, frame="map") if self.spatial is not None else None
        self.unified_world.update_entity_state(
            "robot",
            "pose_2d",
            {"frame": "map", "x_m": x, "y_m": y, "heading_deg": float(body_now.get("heading_deg", 0.0))},
            epistemic_status=WM_OBSERVED,
            confidence=1.0,
            source="body.odometry",
            timestamp=now,
            sigma=0.0,
        )
        if region is not None:
            self.unified_world.update_entity_state(
                "robot",
                "location",
                region,
                epistemic_status=WM_OBSERVED,
                confidence=1.0,
                source="spatial_map.region_at",
                timestamp=now,
                sigma=0.0,
            )
        else:
            self.unified_world.update_entity_state(
                "robot",
                "location",
                "unknown",
                epistemic_status=WM_UNKNOWN,
                confidence=0.5,
                source="spatial_map.region_at",
                timestamp=now,
                sigma=1.0,
            )
        robot.spatial_ref = {"frame": "map", "x": x, "y": y}
        self._seen_entities.add("robot")

    def _safety_world_state(self) -> dict[str, Any]:
        """Compose the safety gate's self-reported world state (doc 08 §2).

        Only state the runtime genuinely knows is reported; keys that are not
        modeled yet stay absent so the invariant's fail-open default applies
        (fabricated violations are as dishonest as fabricated safety).
        """
        body_now = self.body.snapshot()
        sm_state = self.autonomy_sm.state
        return {
            # The latched emergency states from the canonical state machine.
            "estop_active": sm_state in (ASMState.EMERGENCY_STOP, ASMState.FAULT_RECOVERY),
            # Local odometry is always fresh in the Mac phase: the VirtualBody
            # owns its pose (no external localization to go stale). Perception
            # degradation must NOT couple into pose staleness — it gates its
            # own path (PERCEPTION_UNCERTAINTY handling).
            "pose_fresh": True,
            # No forbidden zones are modeled yet (the spatial map lacks zone
            # metadata) — the absent key defaults to False (safe).
            "speed_mps": abs(float(body_now.get("velocity_mps", 0.0))),
            "max_speed_mps": 1.0,
        }

    def _risk_class_for_action(self, action: str) -> str:
        """Map an action to its risk class for governance evaluation."""
        if action in self._R0_ACTIONS:
            return "R0"
        if action in self._R1_ACTIONS:
            return "R1"
        return "R1"  # default to reversible digital action

    def _system0_safety_check(self, ctx: dict[str, Any]) -> dict[str, Any]:
        """Deterministic System-0 safety check — never waits on an LLM.

        Checks that the runtime is in a safe state for execution.
        """
        safe = self.brain.lifecycle is Lifecycle.ACTIVE
        return {"safe": safe, "deterministic": True}

    # ---- Skill contract wiring ----

    # Map runtime actions to skill contract IDs.
    _ACTION_TO_SKILL: dict[str, str] = {
        "move_forward": "navigate",
        "turn_left": "navigate",
        "turn_right": "navigate",
        "observe": "inspect",
        "speak": "speak",
    }

    def _skill_context(self, action: str, parameters: dict[str, Any], goal_was_active: bool) -> dict[str, Any]:
        """Build the skill execution context from runtime state.

        Maps runtime state to the precondition flags that skills check.
        """
        ctx: dict[str, Any] = {
            # Navigate preconditions.
            "robot_localized": True,  # virtual body always has a position
            "target_location_known": goal_was_active and self.goals.has_active,
            "path_clear": True,  # no obstacle detection in virtual body
            # Inspect preconditions.
            "entity_visible": len(self._seen_entities) > 0,
            "camera_available": self.camera is not None,
            # FindObject preconditions.
            "object_description_known": bool(parameters.get("object_description")),
            "search_area_defined": bool(parameters.get("search_area")),
            # Pick preconditions.
            "object_located": bool(parameters.get("object_id")),
            "gripper_available": False,  # no gripper in virtual body
            "robot_near_object": False,  # no proximity detection in virtual body
            # Speak preconditions.
            "message_composed": bool(parameters.get("text", "")),
            "speaker_available": True,  # MacSpeaker is always available
        }
        return ctx

    def _skill_parameters(self, action: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Map runtime action parameters to skill contract parameters."""
        skill_id = self._ACTION_TO_SKILL.get(action, "")
        if skill_id == "navigate":
            target = ""
            if self.goals.has_active and self.goals.active is not None:
                t = self.goals.active.goal.target
                target = str(t) if not isinstance(t, tuple) else f"{t[0]},{t[1]}"
            return {"target_location": target or "current", "speed": 0.3}
        if skill_id == "inspect":
            entity_id = ""
            if self._seen_entities:
                # Use the most recently seen entity label.
                entity_id = list(self._seen_entities)[-1]
            return {"entity_id": entity_id or "unknown", "modality": "vision"}
        if skill_id == "speak":
            return {"text": parameters.get("text", action), "volume": 0.5}
        return {}

    def _invoke_skill_for_action(
        self, action: str, parameters: dict[str, Any], goal_was_active: bool
    ) -> SkillInvocation | None:
        """Invoke the skill contract for an action, if one exists.

        Returns the SkillInvocation result, or None if no skill maps to this action.
        """
        skill_id = self._ACTION_TO_SKILL.get(action, "")
        if not skill_id:
            return None  # no skill contract for this action (e.g. wait, stop)
        ctx = self._skill_context(action, parameters, goal_was_active)
        skill_params = self._skill_parameters(action, parameters)
        invocation = self.skill_executor.invoke(skill_id, skill_params, context=ctx)
        self._last_skill_invocation = invocation.snapshot()
        self._emit(
            "skill.invoked",
            {
                "cycle": self._cycle,
                "skill_id": skill_id,
                "action": action,
                "status": invocation.status,
                "error": invocation.error,
            },
        )
        return invocation

    def _verify_criteria_for_action(self, action: str, goal_was_active: bool) -> tuple[str, ...]:
        """Determine the success criteria for the closed-loop VERIFY step."""
        if action in ("stop", "wait", "idle"):
            return ("action_executed",)
        if goal_was_active:
            return ("action_executed", "effective")
        return ("action_executed",)

    # Capitalized words that are not real proper nouns (start-of-sentence articles,
    # pronouns, small function words) are not candidate entities.
    _ENTITY_STOPWORDS = frozenset(
        {
            "the",
            "a",
            "an",
            "i",
            "my",
            "me",
            "you",
            "your",
            "yours",
            "he",
            "she",
            "his",
            "her",
            "we",
            "us",
            "they",
            "them",
            "hi",
            "hello",
            "hey",
            "its",
            "it's",
            "do",
            "does",
            "did",
            "is",
            "am",
            "are",
            "was",
            "were",
            "be",
            "been",
            "of",
            "to",
            "and",
            "or",
            "in",
            "on",
            "at",
            "with",
            "what",
            "who",
            "when",
            "where",
            "how",
            "why",
            "remember",
            "name",
            "called",
            "like",
            "love",
            "not",
            "no",
            "yes",
            "ok",
            "so",
            "just",
            "very",
            "really",
            "please",
        }
    )

    def _learn_triples(self, text: str, entity_refs: tuple[str, ...], confidence: float, *, source: str) -> None:
        """Extract and admit entity→relation→entity triples from episodic content.

        Gap-audit Phase D3: when ``llm_triples_enabled`` and a dialogue
        transport exist, the local model is asked for constrained-JSON triples
        (FORBIDDEN-guarded); the deterministic regex extraction always runs as
        fallback so learning never depends on the model.
        """
        candidates: list[tuple[str, str, str]] = list(self.knowledge.extract_from_text(text, entity_refs))
        if self.config.llm_triples_enabled:
            try:
                from .knowledge_extraction import LLMTripleExtractor

                extractor = getattr(self, "_triple_extractor", None)
                if extractor is None:
                    extractor = LLMTripleExtractor()
                    self._triple_extractor = extractor
                chat = getattr(self.dialogue, "_chat", None)
                llm_triples = extractor.extract(text, entity_refs, llm_chat=chat)
            except Exception:  # noqa: BLE001 - LLM path is best-effort
                llm_triples = []
            for t in llm_triples:
                if t not in candidates:
                    candidates.append(t)
        for subject, predicate, obj in candidates:
            triple = self.knowledge.add(
                subject, predicate, obj, confidence=confidence, source=source, cycle=self._cycle
            )
            self._emit(
                "knowledge.updated",
                {
                    "cycle": self._cycle,
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "status": triple.status,
                },
            )
            if triple.status == "contradicted":
                self._emit(
                    "knowledge.contradiction",
                    {"cycle": self._cycle, "subject": subject, "predicate": predicate, "object": obj},
                )

    def _persist_knowledge(self) -> None:
        """Persist the knowledge graph immediately after a mutation (WAL-backed).

        Every triple learned is written to the durable store right away, so a
        crash or hard kill cannot lose recently-learned knowledge. No-op with a
        non-durable (deterministic) memory.
        """
        if isinstance(self.memory, DurableMemoryStore):
            self.memory.save_knowledge(self.knowledge.snapshot())

    def _persist_identity(self) -> None:
        """Persist person-identity bindings immediately (WAL-backed), mirroring
        incremental knowledge persistence, so who Novi has recognized survives a
        crash or hard kill rather than only a graceful stop()."""
        if isinstance(self.memory, DurableMemoryStore):
            self.memory.save_identity(self.identity.snapshot())
            with contextlib.suppress(Exception):
                self.memory.save_person_registry(self.person_registry.snapshot())

    def retrieve_knowledge(self, entity: str, *, limit: int = 10) -> dict[str, Any]:
        """Return the knowledge-graph context around an entity."""
        triples = self.knowledge.context(entity, limit=limit)
        out = [t.snapshot() for t in triples]
        self._emit("knowledge.recalled", {"entity": entity, "recalled": len(out)})
        return {"entity": entity, "triples": out}

    # ---- audit trail API (gap-analysis Step 3, item 23) ----

    def audit_entries(self, *, limit: int | None = None) -> tuple[dict[str, Any], ...]:
        """Full structured decision-trace snapshots (doc 13 §Decision Trace)."""
        return self.audit_trail.snapshots(limit=limit)

    def audit_user_view(self, *, limit: int | None = None) -> tuple[dict[str, Any], ...]:
        """Privacy-safe user audit view (doc 13 §User Audit)."""
        return self.audit_trail.user_audit_view(limit=limit)

    def audit_trace_for(self, correlation_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(e.snapshot() for e in self.audit_trail.by_correlation(correlation_id))

    def audit_stats(self) -> dict[str, Any]:
        return self.audit_trail.stats()

    # ---- confirmation flow API (gap-analysis Step 3, item 18) ----

    def pending_confirmations(self) -> tuple[dict[str, Any], ...]:
        """Snapshots of actions currently awaiting user/operator confirmation."""
        out: list[dict[str, Any]] = []
        for v in self._pending_confirmations.values():
            out.append(
                {
                    "grant_id": v["grant_id"],
                    "proposal_id": v["proposal_id"],
                    "action": v["action"],
                    "parameters": dict(v["parameters"]),
                    "risk_class": v["risk_class"],
                    "reason": v["reason"],
                    "cycle": v["cycle"],
                }
            )
        return tuple(out)

    def confirm_action(self, grant_id: str) -> bool:
        """Confirm a pending REQUIRE_CONFIRMATION grant and execute the action.

        This is the wired confirmation flow: REQUIRE_CONFIRMATION → surface
        request → confirm() → execute. Returns True when the action was
        confirmed and executed (or already executed); False when the grant is
        not pending or was denied.
        """
        confirmed = self.governance_guard.confirm(grant_id)
        if confirmed is None or not confirmed.is_allowed:
            return False
        pending = self._pending_confirmations.pop(grant_id, None)
        if pending is None:
            return False
        self._last_governance_grant = confirmed.snapshot()
        self._emit(
            "governance.confirmed",
            {
                "grant_id": grant_id,
                "action": pending["action"],
                "reason": "confirmed_by_user_or_operator",
            },
        )
        # Execute the confirmed action through the same brain + body path —
        # still compiled through the physical authority boundary (Phase 2c):
        # a grant that expired or commands an out-of-envelope action dies here.
        compiled = self.actuator_boundary.compile(
            action=str(pending["action"]),
            parameters=dict(pending.get("parameters") or {}),
            risk_class=str(pending.get("risk_class") or "R1"),
            source="confirmed",
            cycle=self._cycle,
            correlation_id=str(pending.get("proposal_id") or ""),
        )
        if compiled.command is None:
            self._emit(
                "actuator.rejected",
                {
                    "cycle": self._cycle,
                    "action": pending["action"],
                    "rejection": compiled.rejection,
                    "reason": compiled.reason,
                    "stage": "confirmation",
                },
            )
            return False
        if not self.actuator_boundary.is_live(compiled.command, cycle=self._cycle):
            self._emit(
                "actuator.rejected",
                {
                    "cycle": self._cycle,
                    "action": pending["action"],
                    "rejection": "EXPIRED",
                    "reason": "confirmed command issued past its validity window",
                },
            )
            return False
        self._emit(
            "actuator.compiled",
            {
                "cycle": self._cycle,
                "command_id": compiled.command.command_id,
                "action": compiled.command.action,
                "expires_cycle": compiled.command.expires_cycle,
                "stage": "confirmation",
            },
        )
        outcome = self.brain.execute(pending["proposal"], pending["decision"])
        virtual_state = self.body.execute(pending["action"], **pending["parameters"])
        self._emit(
            "action.completed",
            {
                "action": pending["action"],
                "authorized": True,
                "brain_authorized": True,
                "governance_allowed": True,
                "governance_decision": "ALLOW",
                "awaiting_confirmation": False,
                "safety": {
                    "decision": "ALLOW",
                    "allowed": True,
                    "reason": "confirmed",
                    "violated": [],
                    "interrupted": False,
                },
                "safety_interrupted": False,
                "actuator": {"command_id": compiled.command.command_id, "rejection": None},
                "skill_passed": True,
                "skill_invoked": False,
                "outcome": outcome.detail,
                "virtual_body": virtual_state,
            },
        )
        return True

    def reject_confirmation(self, grant_id: str) -> bool:
        """Withdraw a pending confirmation request without executing the action."""
        pending = self._pending_confirmations.pop(grant_id, None)
        if pending is None:
            return False
        self._emit(
            "governance.confirmation_rejected",
            {
                "grant_id": grant_id,
                "action": pending["action"],
            },
        )
        return True

    # ---- privacy / memory governance API ----
    def forget_memory(self, memory_id: str, *, reason: str = "user_request") -> dict[str, Any]:
        report = self.governance.erase_memory(memory_id, reason=reason)
        self._emit("privacy.erased", {"memory_id": memory_id, "reason": reason, "propagated": report.propagated})
        return {
            "memory_id": memory_id,
            "reason": reason,
            "erased": memory_id in report.erased_ids,
            "propagated": report.propagated,
        }

    def forget_entity(self, entity: str, *, reason: str = "right_to_be_forgotten") -> dict[str, Any]:
        report = self.governance.forget_entity(entity, reason=reason)
        self._emit(
            "privacy.entity_erased",
            {"entity": entity, "reason": reason, "erased": len(report.erased_ids), "propagated": report.propagated},
        )
        return {"entity": entity, "reason": reason, "erased": report.erased_ids, "propagated": report.propagated}

    def restrict_memory(self, memory_id: str, *, purpose: str) -> bool:
        ok = self.governance.restrict(memory_id, purpose=purpose)
        if ok:
            self._emit("privacy.restricted", {"memory_id": memory_id, "purpose": purpose})
        return ok

    def generalize_memory(self, memory_id: str) -> bool:
        ok = self.governance.generalize(memory_id)
        if ok:
            self._emit("privacy.generalized", {"memory_id": memory_id})
        return ok

    def privacy_status(self) -> dict[str, Any]:
        return self.governance.snapshot()

    # ---- health / observability API ----
    def health_report(self) -> dict[str, Any]:
        snap = self.health.run(self)
        self._last_health = snap.snapshot()
        self._emit("observability.health", {"cycle": self._cycle, **self._last_health})
        return self._last_health

    def p0_gate(self) -> dict[str, Any]:
        """Run the P0 soul acceptance gate against this brain.

        Returns the P0GateResult snapshot. The gate passes when zero
        constitutional/privacy/escalation/identity/safety violations are found.
        """
        gate = run_p0_gate(self)
        snap = gate.snapshot()
        self._emit("p0.gate", {"cycle": self._cycle, **snap})
        return snap

    # ---- Typed cognition emission (roadmap item 12) ----

    def cognition_typed(
        self,
        observations: list[Any] | None = None,
        *,
        knowledge: Any = (),
        goal: dict[str, Any] | None = None,
        recalled: Any = (),
    ) -> dict[str, Any]:
        """Run a cognition cycle and emit the canonical typed contracts.

        Wraps `MacCognition.cycle_typed` against the current unified world state,
        publishes the resulting contracts on the event bus (cognition.typed) and
        returns the snapshot. Nothing emitted is an authorization or command.

        When called from `step()` the same knowledge/goal/recall grounding that
        fed the legacy cycle is passed through, so the typed SituationState is
        the canonical record of the cycle rather than a parallel debug view.
        """
        observations = observations if observations is not None else ()
        state = self.unified_world.to_world_state()
        out = self.cognition.cycle_typed(
            state,
            observations,
            cycle=self._cycle,
            world_revision=self.unified_world.world_version,
            knowledge=knowledge,
            goal=goal,
            recalled=recalled,
            correlation_id=self._cycle_correlation_id,
        )
        snap = out.snapshot()
        self._emit(
            "cognition.typed",
            {
                "cycle": self._cycle,
                "correlation_id": out.correlation_id,
                "situation": snap["situation"]["id"] if snap.get("situation") else None,
                "person_contexts": [p["id"] for p in snap["person_contexts"]],
                "predictions": [p["id"] for p in snap["predictions"]],
                "intent_hypotheses": [h["id"] for h in snap["intent_hypotheses"]],
                "decision": snap["decision"]["id"] if snap.get("decision") else None,
                "counts": {
                    "person_contexts": len(snap["person_contexts"]),
                    "predictions": len(snap["predictions"]),
                    "intent_hypotheses": len(snap["intent_hypotheses"]),
                    "events": len(out.events),
                },
            },
        )
        self._last_typed_cognition = snap
        return snap

    # ---- Episode recording ----

    def start_recording(self, task_name: str = "runtime_observation", *, description: str = "") -> None:
        """Start recording an episode from subsequent steps."""
        self.episode_recorder = EpisodeRecorder(
            task_name=task_name,
            description=description,
            evidence_class=EP_OBSERVED,
            source="mac_brain",
            platform={"runtime": "mac_brain", "recording": "auto"},
        )
        self._recording_enabled = True
        self._emit(
            "episode.recording_started",
            {
                "cycle": self._cycle,
                "task_name": task_name,
                "description": description,
            },
        )

    def stop_recording(self) -> NoviEpisode | None:
        """Stop recording and return the built episode."""
        self._recording_enabled = False
        if self.episode_recorder is None:
            return None
        episode = self.episode_recorder.build_episode()
        self._emit(
            "episode.recording_stopped",
            {
                "cycle": self._cycle,
                "episode_id": episode.episode_id,
                "step_count": len(episode.steps),
            },
        )
        self.episode_recorder = None
        return episode

    def export_episode(self, episode: NoviEpisode, *, format: str = "novi_native") -> dict[str, Any]:
        """Export an episode through one of the adapters (LeRobot/IsaacLab/ROSBag/NoviNative)."""
        adapter = ALL_ADAPTERS.get(format)
        if adapter is None:
            raise ValueError(f"unknown format: {format!r}. Available: {list(ALL_ADAPTERS.keys())}")
        return adapter.to_format(episode)

    @property
    def is_recording(self) -> bool:
        return self._recording_enabled and self.episode_recorder is not None

    @property
    def recording_step_count(self) -> int:
        if self.episode_recorder is None:
            return 0
        return self.episode_recorder.step_count

    def metrics_snapshot(self) -> list[dict[str, Any]]:
        return self.metrics.snapshot()

    def brain_use_skill(self, name: str, args: list[str] | None = None) -> Any:
        """Run a skill through the registry with full governance (plan 16, P1).

        Script skills execute offline through the allowlisted interpreter.
        Every invocation is audited and emitted; successful results are
        admitted to memory with provenance ``skill:<name>`` so recall shows
        where the fact came from. Returns the SkillRunResult.
        """
        import json as _json

        result = self.skills.run(name, args)
        payload = {"cycle": self._cycle, "skill": result.skill, "outcome": result.outcome, "ok": result.ok}
        self._emit("skill.invoked", payload)
        self.audit_trail.record(
            correlation_id=self._cycle_correlation_id,
            action=f"skill:{result.skill}",
            decision_reason="user_or_trigger_request",
            policy_result="ALLOW:script_skill" if result.ok else f"DENY_OR_FAIL:{result.outcome}",
            safety_result="executed" if result.ok else "failed",
            outcome=result.outcome,
            actor="runtime",
            version="mac-brain",
            details={"args": [str(a) for a in (args or [])]},
        )
        if result.ok and result.data:
            content_blob = _json.dumps(result.data, sort_keys=True)[:500]
            allowed, mem_class = self._gate_memory("skill_result")
            if allowed:
                classification = self.governance.classify(
                    memory_type="skill_result", content={"text": content_blob}, entity_refs=(), modality="tool"
                )
                self.memory.admit(
                    memory_type="skill_result",
                    content={"skill": result.skill, "data": content_blob},
                    confidence=0.9,
                    verification_status="verified",
                    privacy_class=classification.privacy_class,
                    provenance={
                        "source": f"skill:{result.skill}",
                        "capability": "skill.script",
                        "memory_class": mem_class,
                    },
                    entity_refs=(),
                    temporal_context=self._temporal_context(),
                )
        return result

    def add_diagnostic(self, severity: str, message: str, context: dict[str, Any] | None = None) -> None:
        self.diagnostics.add(severity, message, context)
        self._emit(
            "observability.diagnostic",
            {"cycle": self._cycle, "severity": severity, "message": message, "context": context or {}},
        )

    def _update_observability(self) -> dict[str, Any]:
        """Record per-cycle metrics + run the health loop. Returns an observability block."""
        self.metrics.set("cycle", self._cycle, unit="count")
        if isinstance(self.memory, DurableMemoryStore):
            self.metrics.set("memory.active", self.memory.active_count, unit="records")
        self.metrics.set("knowledge.triples", self.knowledge.counts()["triples"], unit="triples")
        self.metrics.set("goals.active", 1 if self.goals.active is not None else 0, unit="count")
        health = self.health.run(self)
        self._last_health = health.snapshot()
        self._emit("observability.health", {"cycle": self._cycle, **health.snapshot()})
        self._emit("observability.metrics", {"cycle": self._cycle, "metrics": self.metrics.snapshot()})
        return {"health": health.snapshot(), "metrics": self.metrics.snapshot()}

    def _admit_goal_outcome(self, state: Any) -> None:
        allowed, mem_class = self._gate_memory("goal_outcome")
        admission = None
        if allowed:
            classification = self.governance.classify(
                memory_type="goal_outcome",
                content={"goal_id": state.goal.goal_id, "kind": state.goal.kind},
                entity_refs=(),
                modality="",
            )
            admission = self.memory.admit(
                memory_type="goal_outcome",
                content={
                    "goal_id": state.goal.goal_id,
                    "kind": state.goal.kind,
                    "status": state.status.value,
                    "steps_taken": state.steps_taken,
                    "target": str(state.goal.target),
                },
                confidence=1.0,
                verification_status="verified",
                privacy_class=classification.privacy_class,
                provenance={"source": "autonomy.goals", "memory_class": mem_class},
                temporal_context=self._temporal_context(),
                spatial_context=self._spatial_context(),
            )
            if admission.accepted and admission.memory_id:
                self.governance.govern(
                    admission.memory_id,
                    privacy_class=classification.privacy_class,
                    purpose=self.governance.default_purpose,
                )
        self._emit(
            "memory.admitted",
            {
                "memory_id": (admission.memory_id if admission else None),
                "memory_type": "goal_outcome",
                "accepted": bool(admission and admission.accepted),
                "goal_id": state.goal.goal_id,
            },
        )

    def _knowledge_context_for(self, salient_entities: tuple[str, ...]) -> list[dict[str, Any]]:
        """Knowledge-graph triples relevant to the salient entities (Cognition 2.0)."""
        salient = set(salient_entities)
        out: list[dict[str, Any]] = []
        for triple in self.knowledge.triples():
            if triple.subject in salient or triple.object in salient:
                out.append(triple.snapshot())
        return out

    def _goal_context(self) -> dict[str, Any] | None:
        """Serializable context for the active goal, if any."""
        active = self.goals.active
        if active is None or active.status.value != "active":
            return None
        goal = active.goal
        return {
            "kind": goal.kind,
            "target": list(goal.target) if isinstance(goal.target, tuple) else goal.target,
            "priority": goal.priority,
            "max_steps": goal.max_steps,
            "steps_taken": active.steps_taken,
            "distance_to_goal": self._distance_to_goal(goal),
        }

    def _distance_to_goal(self, goal: Any) -> float | None:
        try:
            body = self.body.snapshot()
            x, y = body.get("x_m", 0.0), body.get("y_m", 0.0)
            if isinstance(goal.target, tuple):
                tx, ty = goal.target
                return round(((x - tx) ** 2 + (y - ty) ** 2) ** 0.5, 3)
        except Exception:  # noqa: BLE001
            pass
        return None

    def _action_effective(
        self,
        action: str,
        body_before: dict[str, Any],
        body_after: dict[str, Any],
        authorized: bool,
        salient: Any,
        inferences: Any,
    ) -> bool:
        """Judge whether an action had its intended observable effect (Reasoning 2.0)."""
        if action in {"move_forward", "turn_left", "turn_right"}:
            moved = body_before.get("x_m") != body_after.get("x_m") or body_before.get("y_m") != body_after.get("y_m")
            turned = body_before.get("heading_deg") != body_after.get("heading_deg")
            return bool(moved or turned)
        if action in {"inspect", "observe"}:
            # effective if there was something salient/inferred to attend to and it was authorized
            return bool(authorized and (salient or inferences))
        return True  # wait / stop are no-ops and always "effective"

    def _reflection_note(self, action: str, effective: bool) -> str:
        if effective:
            return f"{action} had its intended effect"
        return f"{action} had no observable effect"

    def _situation_dict(self, cognitive: Any) -> dict[str, Any]:
        """Serialize a CognitiveState's situation for the reasoning providers."""
        sit = cognitive.situation
        return {
            "cycle": sit.cycle,
            "salient_entities": list(sit.salient_entities),
            "recent_events": list(sit.recent_events),
            "uncertainty": list(sit.uncertainty),
            "relations": list(sit.relations),
            "goal": sit.goal,
            "recalled": list(sit.recalled),
            "entities": [
                {"entity": e.entity, "state": e.state, "location": e.location, "confidence": e.confidence}
                for e in sit.entities
            ],
        }

    def recall_semantic(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        """Semantic (vector) memory recall; falls back to empty when unavailable."""
        retrieve = getattr(self.memory, "retrieve_semantic", None)
        if retrieve is None:
            return {"query": query, "memories": []}
        records = retrieve(query, limit=limit)
        memories = [
            {
                "memory_id": record.memory_id,
                "memory_type": record.memory_type,
                "content": record.content,
                "confidence": record.confidence,
                "entity_refs": list(record.entity_refs),
            }
            for record in records
        ]
        self._emit("memory.semantic_recall", {"query": query, "recalled": len(memories)})
        return {"query": query, "memories": memories}

    def _character_clause(self, self_state: dict[str, Any]) -> str:
        """A compact, human-readable character clause for the dialogue prompt.

        Weaves the persona's declared traits and values into a sentence so the
        model keeps a consistent voice instead of drifting to neutral-narrator.
        """
        traits = self_state.get("traits") or {}
        values = self_state.get("values") or {}
        bits: list[str] = []
        if traits:
            bits.append("you're " + ", ".join(f"{k}: {v}" for k, v in traits.items()))
        if values:
            names = [k.replace("_", " ") for k, v in values.items() if v]
            if names:
                bits.append("you value " + ", ".join(names))
        return "; ".join(bits)

    def self_model(self) -> dict[str, Any]:
        """Assemble a first-person self-model for dialogue/reasoning (docs/06-soul/01 §6)."""
        return build_self_model(self).snapshot()

    def set_vision_provider(self, provider: Any) -> None:
        """Install the live-vision snapshot provider (plan 26 B).

        The web layer installs a provider that reads MultimodalRuntime +
        CameraFeed state so ``vision_status()`` reports what Novi currently
        sees. One install point; the default (no provider) keeps the honest
        offline report and the default-brain behavior byte-identical.
        """
        self._vision_provider = provider

    def vision_status(self) -> dict[str, Any]:
        """JSON-safe live vision state or an honest offline report (plan 26 B).

        With no provider installed (non-web builds) this is offline — Novi
        won't claim it can see what it has no camera wired for.
        """
        from novi.brain.vision_status import build_vision_status

        return build_vision_status(self, self._vision_provider)

    def _attention_score_for(self, label: str) -> float:
        """Salience of this entity in the latest attention ranking (0 if absent)."""
        for cand in self._last_attention_candidates:
            if cand.get("target_label") == label or cand.get("candidate_id") == label:
                return float((cand.get("scores") or {}).get("salience", 0.0))
        return 0.0

    def _importance_for(self, label: str, confidence: float) -> float:
        """Deterministic importance stamp for a perception record (Phase C4)."""
        seen_count = 1 if label in self._seen_entities else 0
        novelty = self.importance.novelty_for(seen_count)
        score = self.importance.score(
            confidence=confidence,
            attention=self._attention_score_for(label),
            novelty=novelty,
        )
        return round(score, 3)

    def _spatial_context(self) -> dict[str, Any]:
        """Body pose + semantic place for memory admission (gap-audit Phase C3)."""
        x = float(getattr(self.body, "x_m", 0.0))
        y = float(getattr(self.body, "y_m", 0.0))
        place = ""
        try:
            place = self.spatial.region_at(x, y) or ""
        except Exception:  # noqa: BLE001 - spatial context is best-effort
            place = ""
        return {"x_m": x, "y_m": y, "place": place}

    def _temporal_context(self) -> dict[str, Any]:
        """Logical time for memory admission (gap-audit Phase C3).

        Deliberately cycle-only: wall-clock time would leak into the record
        identity hash and break duplicate-admission idempotency.
        """
        return {"cycle": self._cycle}

    def _persist_decision_memory(
        self, deliberation: dict[str, Any], situation: Any, intent: Any, confidence: float
    ) -> None:
        """Persist a deliberation's winning rationale as a first-class decision
        memory (plan P5): situation, chosen action, rejected alternatives, reason.

        Decisions survive restart in the single canonical DB and are recalled on
        similar situations so Novi can explain "last time I chose X because Y".
        """
        decision = deliberation.get("decision") or {}
        options = list(deliberation.get("options", []) or [])
        chosen = str(getattr(intent, "action", decision.get("action", "")))
        rejected = [o for o in options if str(o) != chosen]
        content = {
            "situation": situation if isinstance(situation, dict) else str(situation),
            "chosen_action": chosen,
            "rejected_alternatives": rejected,
            "reason": str(decision.get("rationale", "") or getattr(intent, "rationale", "")),
            "analysis": str(deliberation.get("analysis", "")),
        }
        try:
            admission = self.memory.admit(
                memory_type="decision",
                content=content,
                confidence=float(confidence),
                verification_status="verified" if confidence >= 0.7 else "unverified",
                privacy_class="internal",
                provenance={"source": "reasoning", "memory_class": "procedural"},
                temporal_context=self._temporal_context(),
                spatial_context=self._spatial_context(),
            )
            if admission is not None and admission.accepted:
                self._emit(
                    "memory.decision_admitted",
                    {"cycle": self._cycle, "memory_id": admission.memory_id, "action": chosen},
                )
        except Exception:  # noqa: BLE001 - decision memory is best-effort, never blocks the loop
            self._emit("memory.decision_failed", {"cycle": self._cycle, "action": chosen})

    def _recall_prior_decisions(self, situation: Any, limit: int = 3) -> list[dict[str, Any]]:
        """Recall prior decision memories relevant to the current situation."""
        query = ""
        if isinstance(situation, dict):
            query = " ".join(str(v) for v in situation.values() if isinstance(v, (str, int, float)))
        else:
            query = str(situation or "")
        if not query.strip():
            return []
        try:
            records = self.memory.retrieve(query, memory_type="decision", limit=limit)
        except Exception:  # noqa: BLE001 - recall is best-effort
            return []
        out: list[dict[str, Any]] = []
        for r in records:
            content = r.content if isinstance(r.content, dict) else {}
            out.append(
                {
                    "chosen_action": content.get("chosen_action", ""),
                    "reason": content.get("reason", ""),
                    "situation": content.get("situation", ""),
                }
            )
        return out

    def _gate_memory(self, memory_type: str) -> tuple[bool, str]:
        """Route an admission through MemoryClassDecisionRegistry (Phase C2).

        Returns (allowed, memory_class_value). Deferred classes are not
        admitted (a ``memory.class_deferred`` event records the refusal);
        implemented classes are stamped into provenance for downstream
        episodic-only consolidation routing.
        """
        allowed, mem_class, state = self.memory_classes.gate(memory_type)
        if not allowed:
            self._emit(
                "memory.class_deferred",
                {
                    "cycle": getattr(self, "_cycle", 0),
                    "memory_type": memory_type,
                    "memory_class": mem_class,
                    "state": state,
                },
            )
        return allowed, mem_class

    def _identify_face(self, detection: Any, image: Any = None) -> dict[str, Any] | None:
        """Recognise a detected face and feed it as voice-grade identity evidence (rule 6)."""
        if self.face_id is None:
            return None
        det = {
            "label": getattr(detection, "label", ""),
            "track": getattr(detection, "track", ""),
            "bbox": list(getattr(detection, "bbox_xyxy", ())),
            "image": image,
        }
        try:
            result = self.face_id.identify(detection=det)
        except Exception:  # noqa: BLE001 - recognition is best-effort evidence
            return None
        if result is None:
            return None
        self.identity.observe(
            "person", name=result.name, confidence=result.confidence, modality="face", cycle=self._cycle
        )
        # Plan 22 Phase 2: feed the canonical person registry (lifecycle +
        # recognition events). The face identity ref stays opaque — biometric
        # data never enters conversation memory.
        face_ref = getattr(result, "ref", None) or f"face:{result.name}"
        self._observe_person_registry(
            "person",
            name=result.name,
            confidence=result.confidence,
            modality="face",
            cycle=self._cycle,
            face_ref=face_ref,
        )
        self._persist_identity()
        self._emit(
            "identity.face", {"cycle": self._cycle, "name": result.name, "confidence": round(result.confidence, 3)}
        )
        return {"name": result.name, "confidence": result.confidence}

    def _identify_speaker(self, audio_features: dict[str, Any]) -> dict[str, Any] | None:
        """Recognise who is speaking and feed it as voice-grade identity evidence (rule 6)."""
        if self.speaker_id is None:
            return None
        try:
            result = self.speaker_id.identify(audio_features=audio_features)
        except Exception:  # noqa: BLE001 - recognition is best-effort evidence
            return None
        if result is None:
            return None
        self.identity.observe(
            "person", name=result.name, confidence=result.confidence, modality="voice", cycle=self._cycle
        )
        voice_ref = getattr(result, "ref", None) or f"voice:{result.name}"
        self._observe_person_registry(
            "person",
            name=result.name,
            confidence=result.confidence,
            modality="voice",
            cycle=self._cycle,
            voice_ref=voice_ref,
        )
        self._persist_identity()
        self._emit(
            "identity.voice", {"cycle": self._cycle, "name": result.name, "confidence": round(result.confidence, 3)}
        )
        return {"name": result.name, "confidence": result.confidence}

    def _observe_person_registry(
        self,
        person_id: str,
        *,
        name: str | None,
        confidence: float,
        modality: str,
        cycle: int,
        face_ref: str | None = None,
        voice_ref: str | None = None,
    ) -> None:
        """Feed identity evidence into the canonical PersonRegistry and emit
        recognition events (plan 22 Phase 2, Task 2.4). Best-effort: identity
        events must never break the perception/cognition loop.
        """
        try:
            self.person_registry.observe(
                person_id=person_id or "person",
                name=name,
                confidence=confidence,
                modality=modality,
                cycle=cycle,
                face_ref=face_ref,
                voice_ref=voice_ref,
            )
            for evt in self.person_registry.drain_events():
                self._emit(
                    evt["event_type"],
                    {
                        "cycle": cycle,
                        "person_id": evt["person_id"],
                        "name": evt["name"],
                        "confidence": evt["confidence"],
                        "status": evt["status"],
                    },
                )
        except Exception:  # noqa: BLE001 - identity events are best-effort
            pass

    def _observe_object_registry(self, obs: Any, *, now: str) -> None:
        """Feed one canonical Observation into the ObjectRegistry and emit
        object events (plan 22 Phase 3, Task 3.4). Events are evidence for
        salience, never speech by themselves. Best-effort: object identity
        must never break the perception loop.
        """
        try:
            location = ""
            if obs.location:
                if obs.location.get("place"):
                    location = str(obs.location["place"])
                elif obs.location.get("x") is not None:
                    location = f"map@{obs.location.get('x')},{obs.location.get('y')}"
            self.object_registry.observe(
                entity_id=obs.entity_id or f"obs-{obs.observation_id}",
                cls=obs.entity_candidate,
                confidence=obs.confidence,
                cycle=self._cycle,
                location=location,
                bbox=obs.attributes.get("bbox_px"),
                now=now,
            )
            for evt in self.object_registry.drain_events():
                self._emit(evt["event_type"], {"cycle": self._cycle, **evt})
        except Exception:  # noqa: BLE001 - object events are best-effort
            pass

    def _run_dialogue_policy(
        self,
        event_records: list[dict[str, Any]],
        *,
        evidence: Any = None,
        goal_id: str | None = None,
    ) -> Any:
        """Plan 22 Phase 10: build the DialogueContext from this cycle's state
        and select the communicative act. The decision is stored (and emitted
        when non-SILENCE) so proactive speech and the context packet can
        consume it. Best-effort: never breaks the step loop.
        """
        try:
            from .dialogue_policy import DialogueAct, DialogueContext

            kinds = [str(r.get("kind", "")) for r in event_records]
            social = (
                getattr(self.social_context, "snapshot", lambda: {})() if getattr(self, "social_context", None) else {}
            )
            commitments = [str(c.get("trigger", "")) for c in self.working_memory.pending_commitments if c.get("due")]
            threads = [q for q in self.working_memory.unresolved_questions]
            ctx = DialogueContext(
                has_user_message=False,
                person_present=bool(social.get("interaction_phase") not in ("departed", "none")),
                person_entered="presence.entered" in kinds,
                person_left="presence.left" in kinds,
                salient_events=[r for r in event_records if r.get("kind")],
                safety_event="safety.event" in kinds,
                addressee=str(social.get("addressee", "") or ""),
                addressee_known=bool(getattr(getattr(self, "social_context", None), "familiarity", 0.0) or 0.0) >= 0.5,
                social_opportunity=float(social.get("social_opportunity", 0.0) or 0.0),
                user_engagement=float(social.get("user_engagement", 0.0) or 0.0),
                interruptibility=float(social.get("interruptibility", 1.0) or 1.0),
                speaking_lease_held=bool(self.speaking_lease),
                open_threads=threads,
                commitments_due=commitments,
                active_goal=str(getattr(getattr(self, "goals", None), "active", None) or ""),
                initiative_budget_available=not bool(self.speaking_lease),
            )
            decision = self.dialogue_policy.decide(ctx)
            self.last_dialogue_decision = decision
            # Plan 22 Phase 23: record the decision trace (why Novi would say
            # anything this cycle is debuggable).
            with contextlib.suppress(Exception):
                trace = self.decision_traces.new_trace(
                    cycle_id=self._cycle,
                    input_event=",".join(kinds) or "cycle",
                )
                trace.perception_evidence = list({d.label for d in evidence.detections}) if evidence is not None else []
                trace.social_context = dict(social)
                trace.dialogue_act = decision.act.value
                trace.dialogue_reason = decision.reason
                trace.initiative_score = decision.expected_value if hasattr(decision, "expected_value") else 0.0
                trace.retrieved_memories = list(getattr(self, "_last_recall_ids", set()))[:6]
                trace.goals = [str(goal_id)] if goal_id else []
            # Plan 22 Phase 6: fire due prospective memories; due commitments
            # flow into working memory so the policy can INITIATE.
            with contextlib.suppress(Exception):
                conversation_ended = "presence.left" in kinds
                due = self.prospective_memory.check_due(conversation_ended=conversation_ended)
                for mem in due:
                    self.working_memory.update(
                        cycle=self._cycle,
                        commitment={"trigger": mem.intended_action, "due": True},
                    )
                    self._emit("prospective.due", {"memory_id": mem.memory_id, "action": mem.intended_action})
            if decision.act is not DialogueAct.SILENCE:
                self._emit("dialogue.policy", {"cycle": self._cycle, **decision.snapshot()})
            return decision
        except Exception:  # noqa: BLE001 - policy is best-effort
            return None

    def _build_social_context(self) -> dict[str, Any]:
        """Plan 22 Phase 7: derive the short-lived SocialContext from
        observable evidence and keep it on the brain for dialogue policy /
        initiative scoring. Best-effort: never breaks the step loop.
        """
        try:
            from .social_context import SocialContextBuilder, SocialEvidence

            person_name = ""
            familiarity = 0.0
            with contextlib.suppress(Exception):
                belief = self.identity.identity_for("person")
                if belief is not None and belief.name:
                    person_name = belief.name
                model = self.person_registry.person("person")
                if model is not None and model.known:
                    familiarity = model.confidence
            person_present = False
            with contextlib.suppress(Exception):
                person_present = self.identity.identity_for("person") is not None or any(
                    e.lower() in {"person", "human", "face"} for e in self.unified_world.to_world_state().entities
                )
            last_utterance = getattr(self, "_last_user_utterance_cycle", -1)
            recent_utterances = 1 if 0 <= self._cycle - last_utterance <= 3 else 0
            evidence = SocialEvidence(
                person_name=person_name,
                familiarity=familiarity,
                relationship="unknown",
                last_user_utterance_cycle=last_utterance,
                current_cycle=self._cycle,
                user_speaking=recent_utterances > 0,
                novi_speaking=bool(self.speaking_lease),
                interaction_count=self.communication_decision.interaction_count,
                recent_utterances=recent_utterances,
                person_present=person_present,
            )
            ctx = SocialContextBuilder().build(evidence)
            self.social_context = ctx
            return ctx.snapshot()
        except Exception:  # noqa: BLE001 - social context is best-effort
            return {"interaction_phase": "none", "social_opportunity": 0.0}

    def _update_working_memory(self, evidence: Any) -> None:
        """Plan 22 Phase 4: refresh the bounded working-memory slots from this
        cycle's state, expire stale entries and promote important events to
        durable memory. Best-effort: WM must never break the step loop.
        """
        try:
            wm = self.working_memory
            topic = ""
            with contextlib.suppress(Exception):
                topic = self.discourse.snapshot().get("topic", "") or ""
            person = ""
            with contextlib.suppress(Exception):
                model = self.person_registry.resolve(self.identity.identity_for("person").name or "")  # type: ignore[union-attr]
                if model is not None:
                    person = model.canonical_name or ""
                elif self.identity.identity_for("person") is not None:  # type: ignore[union-attr]
                    person = self.identity.identity_for("person").name or ""  # type: ignore[union-attr]
            goal_id = None
            with contextlib.suppress(Exception):
                if self.goals.has_active and self.goals.active is not None:
                    goal_id = self.goals.active.goal.goal_id
            labels = [d.label for d in getattr(evidence, "detections", []) or ()]
            importance = 0.0
            if labels:
                top = max((getattr(d, "confidence", 0.0) for d in evidence.detections), default=0.0)
                importance = max(0.0, min(0.95, top * 0.9))
            wm.update(
                cycle=self._cycle,
                person=person,
                topic=topic,
                goal=goal_id,
                event={
                    "event_id": f"wm-{self._cycle}",
                    "kind": "perception",
                    "entities": labels,
                    "importance": importance,
                },
            )
            wm.expire(cycle=self._cycle)
            wm.promote_important(self._promote_working_event)
        except Exception:  # noqa: BLE001 - working memory is best-effort
            pass

    def _promote_working_event(self, entry: dict[str, Any]) -> None:
        """Promote one important working-memory event into durable memory."""
        try:
            allowed, _mem_class = self._gate_memory("episodic")
            if not allowed:
                return
            entity_refs = tuple(str(e) for e in entry.get("entities", []) if e)
            admission = self.memory.admit(
                memory_type="episodic",
                content={"event": entry.get("kind", "perception"), "entities": entity_refs},
                confidence=float(entry.get("importance", 0.7)),
                verification_status="unverified",
                privacy_class="private",
                provenance={"source": "working_memory", "capability": "cognition.working_memory"},
                entity_refs=entity_refs,
            )
            if admission is not None and admission.accepted:
                self._emit(
                    "memory.promoted",
                    {
                        "memory_id": admission.memory_id,
                        "memory_type": "episodic",
                        "source": "working_memory",
                        "importance": entry.get("importance"),
                    },
                )
        except Exception:  # noqa: BLE001 - promotion is best-effort
            pass

    def _housekeep_object_registry(self, *, max_age_cycles: int = 40) -> None:
        """Mark long-unseen object instances LOST and persist the registry
        (runs on the consolidation/sleep cadence; frame-level loss is the
        tracker's job)."""
        try:
            for evt in self.object_registry.expire_missing(cycle=self._cycle, max_age_cycles=max_age_cycles):
                self._emit(evt["event_type"], {"cycle": self._cycle, **evt})
            if isinstance(self.memory, DurableMemoryStore):
                self.memory.save_object_registry(self.object_registry.snapshot())
        except Exception:  # noqa: BLE001 - housekeeping is best-effort
            pass

    def observe_expression(self, expression: str, *, source: str = "speech", person: str = "", now: str = "") -> str:
        entry = self.lexicon.observe(expression, source=source, person=person, now=now)
        self._emit(
            "lexicon.observed",
            {"expression": expression, "person": person, "status": entry.status.value, "frequency": entry.frequency},
        )
        return entry.status.value

    def learn_preference(self, person: str, kind: str, value, *, explicit: bool = False, now: str = "") -> None:
        pref = self.preferences.learn(person, kind, value, explicit=explicit, now=now)
        # Plan 22 Phase 18.3: preferences also land on the canonical person
        # model so they can change future behavior (verbosity/directness).
        with contextlib.suppress(Exception):
            model = self.person_registry.person(person) or self.person_registry.resolve(person)
            if model is not None:
                self.person_registry.learn_preference(model.person_id, kind, value)
        self._emit(
            "preference.learned",
            {"person": person, "kind": kind, "value": value, "confidence": pref.confidence, "explicit": explicit},
        )

    def _preferred_verbosity(self, person: str = "") -> str:
        """Phase 18.3: the person's persisted verbosity preference drives reply
        length ('' when unset)."""
        try:
            model = self.person_registry.person(person) or self.person_registry.resolve(person)
            if model is not None:
                value = model.preferences.get("verbosity")
                if value in ("short", "medium", "long"):
                    return str(value)
        except Exception:  # noqa: BLE001
            pass
        return ""

    # ---- Learning pipeline (roadmap item 13) ----

    def observe_knowledge(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        confidence: float,
        source: str = "",
        epistemic: str = "OBSERVED",
    ) -> bool:
        """Feed an observation into the promotion pipeline; promote when ready.

        Returns True if the candidate crossed the promotion thresholds and was
        added to the knowledge graph (never for SIMULATED/PREDICTED input).
        """
        from .learning_pipeline import OBSERVED, VERIFIED

        promotable = epistemic in (OBSERVED, VERIFIED, "INFERRED")
        cand = self.learning.observe(
            subject, predicate, object, confidence=confidence, source=source, cycle=self._cycle, epistemic=epistemic
        )
        if not promotable:
            self._emit(
                "learning.candidate",
                {
                    "subject": subject,
                    "predicate": predicate,
                    "object": object,
                    "epistemic": epistemic,
                    "status": "hypothetical",
                },
            )
            return False
        promoted = self.learning.promote(cand, self.knowledge, cycle=self._cycle)
        self._emit(
            "learning.candidate",
            {
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "epistemic": epistemic,
                "status": "promoted" if promoted else "accumulating",
                "evidence_count": cand.evidence_count,
            },
        )
        return promoted

    def correct_knowledge(
        self, subject: str, predicate: str, new_object: str, *, person: str = "", source: str = "user_correction"
    ) -> bool:
        """Apply an explicit user correction with provenance; supersedes prior claim.

        Returns True when a prior claim was actually corrected.
        """
        from .learning_pipeline import CorrectionRecord

        prior = self.knowledge.leading(subject, predicate)
        old_object = prior.object if prior is not None else None
        record = CorrectionRecord(
            subject=subject,
            predicate=predicate,
            old_object=old_object,
            new_object=new_object,
            person=person,
            source=source,
            cycle=self._cycle,
        )
        changed = self.corrections.apply(record, self.knowledge)
        self._emit(
            "learning.corrected",
            {
                "subject": subject,
                "predicate": predicate,
                "old_object": old_object,
                "new_object": new_object,
                "corrected_by": person,
                "source": source,
                "changed": changed,
            },
        )
        return changed

    def observe_routine(self, events: set[str]) -> None:
        """Feed a cycle's event set to the routine detector."""
        self.routines.observe(self._cycle, events)
        routines = self.routines.routines(min_occurrences=self.routines.min_occurrences)
        for routine in routines:
            self._emit(
                "learning.routine",
                {
                    "cycle": self._cycle,
                    "pattern": list(routine.pattern),
                    "occurrences": routine.occurrences,
                    "confidence": routine.confidence,
                },
            )
            self._promote_routine_to_knowledge(routine)

    def _promote_routine_to_knowledge(self, routine: Any) -> None:
        """Promote a stable co-occurrence routine into an inferred relation.

        A recurring pattern (A, B) is recorded as ``A co_occurs_with B`` in the
        knowledge graph with the routine's confidence. This is experience-driven
        learning (docs/06-soul/06 §Learning): patterns that persist across many
        cycles become part of Novi's understanding of its environment. It is
        always INFERRED and reversible.
        """
        from .learning_pipeline import INFERRED

        pattern = list(routine.pattern)
        if len(pattern) >= 2:
            for i in range(1, len(pattern)):
                cand = self.learning.observe(
                    pattern[0],
                    "co_occurs_with",
                    pattern[i],
                    confidence=routine.confidence,
                    source="routine_detector",
                    cycle=self._cycle,
                    epistemic=INFERRED,
                )
                if cand.epistemic in (INFERRED,) and cand.evidence_count >= self.learning.promote_min_evidence:
                    self.learning.promote(cand, self.knowledge, cycle=self._cycle)

    def counterfactual(
        self, *, premise: str, if_evidence: dict[str, Any], then_prediction: str, confidence: float = 0.4
    ) -> dict[str, Any]:
        """Evaluate a what-if question; result is SIMULATED, never merged into facts."""
        result = self.counterfactuals.evaluate(
            premise=premise,
            if_evidence=if_evidence,
            then_prediction=then_prediction,
            confidence=confidence,
        )
        self._emit("learning.counterfactual", {"cycle": self._cycle, **result})
        return result

    def learning_state(self) -> dict[str, Any]:
        """Expose the learning subsystems' state (routines, counterfactuals,
        corrections, memory-class decisions, schema-evolution gate).

        Makes the candidate/promotion learning observable and auditable without
        exposing the model to the ability to silently mutate authoritative state.
        """
        try:
            routines = [r.snapshot() for r in self.routines.routines()]
        except Exception:  # noqa: BLE001
            routines = []
        try:
            counterfactuals = list(self.counterfactuals.queries())
        except Exception:  # noqa: BLE001
            counterfactuals = []
        try:
            corrections = self.corrections.snapshot()
        except Exception:  # noqa: BLE001
            corrections = []
        try:
            memory_classes = self.memory_classes.snapshot()
        except Exception:  # noqa: BLE001
            memory_classes = {}
        try:
            schema = self.schema_evolution.snapshot()
        except Exception:  # noqa: BLE001
            schema = {}
        return {
            "routines": routines,
            "counterfactuals": counterfactuals,
            "corrections": corrections,
            "memory_classes": memory_classes,
            "schema_evolution": schema,
        }

    def record_correction(self, person: str, kind: str, value, *, now: str = "") -> None:
        self.preferences.record_correction(person, kind, value, now=now)
        self._emit("preference.corrected", {"person": person, "kind": kind, "value": value, "supersedes": True})

    def stop(self) -> None:
        if self.camera is not None:
            self.camera.close()
        if isinstance(self.memory, DurableMemoryStore):
            self.memory.save_soul(self.soul.durable_snapshot())
            self.memory.save_relationships(self.relationships.snapshot())
            self.memory.save_lexicon(self.lexicon.snapshot())
            self.memory.save_preferences(self.preferences.snapshot())
            self.memory.save_beliefs(self.beliefs.snapshot())
            self.memory.save_expectations(self.expectations.snapshot())
            self.memory.save_temporal(self.temporal.snapshot())
            self.memory.save_fusion(self.fusion.snapshot())
            self.memory.save_identity(self.identity.snapshot())
            self.memory.save_knowledge(self.knowledge.snapshot())
            self.memory.save_plans([p.snapshot() for p in self._plans.values()])
            self.memory.save_body(
                {
                    "x_m": self.body.x_m,
                    "y_m": self.body.y_m,
                    "heading_deg": self.body.heading_deg,
                    "velocity_mps": self.body.velocity_mps,
                    "last_action": self.body.last_action,
                }
            )
            self._sync_goal_states()
            self.memory.close()
        if self.brain.lifecycle is not Lifecycle.SHUTTING_DOWN:
            self.brain.shutdown()
        # Autonomy state machine: → SHUTTING_DOWN.
        now = datetime.now(timezone.utc).isoformat()
        t = self.autonomy_sm.shutdown(timestamp=now)
        self._emit("autonomy.transition", {"cycle": self._cycle, **t.snapshot()})
        self._emit("brain.stopped", {"run_id": self.run_id, "cycles": self._cycle})

    def _compat_event_limit(self) -> int:
        """Hard upper bound for the flattened compatibility view."""
        try:
            limit = int(getattr(self.config, "compat_event_history", WEB_COMPAT_EVENT_HISTORY))
        except (TypeError, ValueError):
            limit = WEB_COMPAT_EVENT_HISTORY
        return max(1, limit)

    @staticmethod
    def _sanitize_compat_payload(payload: dict[str, Any]) -> dict[str, Any]:
        """Defensive copy that never retains large runtime objects.

        Events must carry serializable summaries (ids/dimensions), not live
        buffers. Anything bytes-like over 1 KiB, or any value whose type name
        suggests an ndarray/tensor, is replaced with a compact reference so
        one misbehaving producer cannot pin megabytes per event.
        """
        clean: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, (bytes, bytearray, memoryview)):
                if len(value) > 1024:
                    clean[key] = {"__ref__": str(key), "bytes": len(value), "truncated": True}
                else:
                    clean[key] = bytes(value)
                continue
            tname = type(value).__name__
            if tname in ("ndarray", "Tensor", "EagerTensor") or "tensor" in tname.lower():
                clean[key] = {"__ref__": str(key), "type": tname}
                continue
            clean[key] = value
        return clean

    def _append_compat_event(self, event: dict[str, Any]) -> None:
        """Single insertion point for the compatibility view; enforces the bound."""
        self.events.append(event)
        limit = self._compat_event_limit()
        if len(self.events) > limit:
            del self.events[: len(self.events) - limit]

    def _emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        source: str = "runtime",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        priority: str = "normal",
        privacy_class: str = "unclassified",
    ) -> str:
        """Publish an event through the autonomy event bus (doc 10 contract).

        Returns the event_id. Events are threaded into the current cycle's
        correlation domain and causally chained to the previous event when no
        explicit ids are given. ``self.events`` remains the flattened
        compatibility view for legacy consumers, now bounded at the source
        (plan 02): ``len(self.events) <= config.compat_event_history`` under
        all runtime conditions, with or without a web server draining.
        """
        envelope = self.event_bus.publish(
            event_type,
            payload,
            source=source,
            correlation_id=correlation_id or self._cycle_correlation_id,
            causation_id=causation_id,
            priority=priority,
            privacy_class=privacy_class,
        )
        self._append_compat_event(
            {
                "event_type": event_type,
                "run_id": self.run_id,
                "cycle": self._cycle,
                "payload": self._sanitize_compat_payload(payload),
                "event_id": envelope.event_id,
                "correlation_id": envelope.correlation_id,
                "causation_id": envelope.causation_id,
                "priority": envelope.priority,
                "privacy_class": envelope.privacy_class,
                "sequence": envelope.sequence,
            }
        )
        return envelope.event_id


# Agnostic alias — new code should import Brain; MacBrain kept for backward compat.
Brain = MacBrain
BrainConfig = MacBrainConfig
