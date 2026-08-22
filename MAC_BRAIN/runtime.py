from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from brain.b1_cognition import DeterministicCognition
from brain.b1_memory import DeterministicMemoryManager
from brain.b1_world import SensorObservation, TemporalWorldModel
from brain.b2_perception import SpecialistPerception
from brain.runtime import ActionProposal as RuntimeActionProposal
from brain.runtime import BrainSupervisor, Lifecycle

from .autonomy import BoundedGoalController, Goal, GoalState, GoalStatus
from .consolidation import ConsolidationConfig, MemoryConsolidator, SummaryConsolidator
from .cognition import BeliefSystem, ExpectationSystem
from .cognition2 import MacCognition
from .fusion import ModalityObservation, MultimodalFusion
from .identity import PersonIdentity
from .io import Camera, MacMicrophone, MacSpeaker, VirtualBody
from .kgraph import EntityKnowledgeGraph
from .planner import Plan, Planner
from .privacy import PrivacyGovernance
from .reflection import ReflectionEngine
from .audio import AudioEvent, AudioFrame, Hearing
from .observability import Diagnostics, HealthMonitor, MetricRegistry, default_health_checks
from .lexicon import LearnedPreferences, Lexicon
from .social import Relationships, SocialIntelligence, TIER_EXPRESSION, SocialInitiative, InitiativeConfig
from .soul import Soul
from .storage import DurableMemoryStore
from .dialogue import (
    DialogueEngine,
    _extract_topic,
    _is_clarification,
    _is_continuation,
    _is_emotional_statement,
    _is_greeting,
    _is_introduction,
    _is_joke_request,
    _is_perception_question,
    _is_physical_action_request,
    _is_acknowledgment,
    _is_bodily_need_question,
    _is_repeat_question,
    _is_realtime_data_question,
    _is_assurance_question,
    _is_engagement_check,
    _is_memory_question,
    _is_talk_request,
    _is_debate_request,
    _is_farewell,
    _is_world_question,
    _is_identity_question,
    farewell_reply,
    _is_embodiment_question,
    _is_future_question,
    _is_recall_question,
    _is_reminder_request,
    _is_thanks,
    _is_time_greeting,
    acknowledgment_reply,
    assurance_reply,
    clarification_reply,
    continuation_reply,
    emotional_reply,
    followup_question,
    future_reply,
    greeting_reply,
    introduction_reply,
    joke_reply,
    natural_fallback,
    physical_action_honest_reply,
    realtime_honest_reply,
    recall_reply,
    reminder_reply,
    thanks_reply,
    time_greeting_reply,
)
from .self_model import SelfModel, build_self_model
from .temporal import TemporalModel
from .models import (
    DeliberativeReasoningProvider,
    DeterministicReasoningProvider,
    DeterministicSTTProvider,
    ReasoningProvider,
    SpeechToTextProvider,
    TranscriptionResult,
)


@dataclass(frozen=True)
class MacBrainConfig:
    sensor_id: str = "mac.camera.front"
    run_id: str = ""
    memory_dir: Path = Path("MAC_BRAIN_data/memory")
    max_cycles: int = 1
    curiosity_enabled: bool = True
    curiosity_investigate_steps: int = 5
    consolidation_enabled: bool = True
    consolidation_every: int = 1
    consolidation_config: ConsolidationConfig = field(default_factory=ConsolidationConfig)
    initiative_enabled: bool = False
    initiative_neglect_threshold: int = 30
    initiative_cooldown: int = 60


class MacBrain:
    """First executable Mac embodiment of the existing Novi Brain."""

    def __init__(
        self,
        *,
        camera: Camera | None = None,
        speaker: MacSpeaker | None = None,
        body: VirtualBody | None = None,
        perception: SpecialistPerception | None = None,
        reasoning: ReasoningProvider | None = None,
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
        config: MacBrainConfig | None = None,
    ) -> None:
        self.config = config or MacBrainConfig()
        self.run_id = self.config.run_id or str(uuid4())
        self.camera = camera
        self.speaker = speaker or MacSpeaker()
        self.body = body or VirtualBody()
        self.microphone = microphone or MacMicrophone()
        self.brain = BrainSupervisor()
        self.perception = perception or SpecialistPerception()
        self.reasoning = reasoning or DeliberativeReasoningProvider()
        self.reflection = ReflectionEngine()
        self.stt = stt or DeterministicSTTProvider()
        self.world = TemporalWorldModel()
        self.memory = DurableMemoryStore(store_path) if store_path else DeterministicMemoryManager()
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
        if isinstance(self.memory, DurableMemoryStore):
            for snap in self.memory.load_plans():
                try:
                    plan = Plan.from_snapshot(snap)
                    self._plans[plan.goal_id] = plan
                except KeyError:
                    continue
        if goals is None and isinstance(self.memory, DurableMemoryStore):
            self._load_goals()
        self.consolidator = MemoryConsolidator(self.memory, self.config.consolidation_config) if isinstance(self.memory, DurableMemoryStore) else None
        self.summary_consolidator = summary_consolidator or (SummaryConsolidator(self.memory) if isinstance(self.memory, DurableMemoryStore) else None)
        if self.summary_consolidator is not None and getattr(self.summary_consolidator, "store", None) is None and isinstance(self.memory, DurableMemoryStore):
            self.summary_consolidator.store = self.memory
        self.narrator = narrator
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
        if relationships is not None:
            self.relationships = relationships
        elif isinstance(self.memory, DurableMemoryStore):
            persisted = self.memory.load_relationships()
            self.relationships = Relationships.from_snapshot(persisted) if persisted else Relationships()
        else:
            self.relationships = Relationships()
        self.social = social or SocialIntelligence()
        self.social_initiative = SocialInitiative(InitiativeConfig(neglect_threshold=self.config.initiative_neglect_threshold, cooldown=self.config.initiative_cooldown))
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
        self.governance = governance or PrivacyGovernance(self.memory if isinstance(self.memory, DurableMemoryStore) else None)
        self.hearing = hearing or Hearing()
        self._pending_audio: list[ModalityObservation] = []
        self._pending_speech: list[ModalityObservation] = []
        self._last_audio_events: list[dict[str, Any]] = []
        self._last_reasoning_trace: dict[str, Any] = {"cycle": -1, "conclusion": "awaiting_cycle", "confidence": 0.0, "action": "none", "rationale": "", "route": "none", "route_reason": "", "recalled": 0, "situation": None, "detections": []}
        self.metrics = metrics or MetricRegistry()
        self.diagnostics = diagnostics or Diagnostics()
        self.health = health or HealthMonitor(default_health_checks())
        self._last_health: dict[str, Any] | None = None
        self._cycle = 0
        self.events: list[dict[str, Any]] = []

    def start(self) -> None:
        self.brain.start()
        self._emit("MAC_BRAIN.started", {"run_id": self.run_id})

    def step(self) -> dict[str, Any]:
        if self.brain.lifecycle is not Lifecycle.ACTIVE:
            raise RuntimeError(f"Mac Brain must be ACTIVE, got {self.brain.lifecycle.value}")
        if self.camera is None:
            raise RuntimeError("camera provider is not configured")
        self._cycle += 1
        frame = self.camera.read()
        self._emit("sensor.camera.frame", {"frame_id": frame.frame_id, "width": frame.width, "height": frame.height, "captured_at": frame.captured_at, "metadata": frame.metadata})
        evidence = self.perception.process(sensor_id=self.config.sensor_id, frame_id=frame.frame_id, timestamp=frame.captured_at, frame=frame.payload)
        self._emit("perception.completed", {"frame_id": evidence.frame_id, "detection_count": len(evidence.detections), "provenance": dict(evidence.provenance)})
        observations = tuple(SensorObservation(cycle=self._cycle, source=f"{self.config.sensor_id}.perception", entity=detection.label, location=None, state="present", confidence=detection.confidence, captured_cycle=self._cycle) for detection in evidence.detections)
        self.world.apply_many(observations)
        self._admit_detections(evidence.detections)
        # Cognition 2.0: two-pass — build a preliminary situation to form the
        # recall query, then ground the full situation in knowledge + goal + memory.
        prelim = self.cognition.build_situation(self.world.state, observations, cycle=self._cycle)
        recall = self._recall_context(prelim, evidence.detections)
        self._emit("memory.recall", {"cycle": self._cycle, "query": " ".join(recall["query"]), "recalled": len(recall["memories"])})
        knowledge_ctx = self._knowledge_context_for(prelim.salient_entities)
        goal_ctx = self._goal_context()
        cognitive = self.cognition.cycle(
            self.world.state,
            observations,
            cycle=self._cycle,
            knowledge=knowledge_ctx,
            goal=goal_ctx,
            recalled=recall["memories"],
        )
        self._emit("cognition.completed", {
            "cycle": self._cycle,
            "conclusion": cognitive.reasoning.conclusion,
            "confidence": cognitive.reasoning.confidence,
            "uncertainty": list(cognitive.situation.uncertainty),
            "inferences": list(cognitive.reasoning.inferences),
            "hypotheses": list(cognitive.reasoning.hypotheses),
            "relations": list(cognitive.situation.relations),
        })

        # Deepen cognition: update beliefs and learn/check expectations from current detections.
        now = datetime.now(timezone.utc).isoformat()
        present = {d.label for d in evidence.detections}
        for detection in evidence.detections:
            self.beliefs.observe(detection.label, True, confidence=detection.confidence, now=now)
            if detection.label in {"person", "human", "face"}:
                self.identity.observe("person", confidence=detection.confidence, modality="vision", cycle=self._cycle)
                self._persist_identity()
                self._identify_face(detection)
        identity = self.identity.identity_for("person")
        if identity is not None:
            self._emit("identity.observed", {"cycle": self._cycle, "person": identity.person, "name": identity.name, "tier": identity.tier, "confidence": identity.confidence})
        self.expectations.update(present)
        violations = self.expectations.drain_violations()
        for v in violations:
            self._emit("cognition.expectation_violation", {"cycle": self._cycle, "entity": v.entity, "kind": v.kind, "confidence": v.expectation_confidence})
        if violations:
            self._emit("cognition.predicted", {"cycle": self._cycle, "violations": [v.snapshot() for v in violations]})

        # Multimodal fusion: combine vision detections + pending speech into fused events.
        vision_obs = [
            ModalityObservation(modality="vision", entity=d.label, value="present", confidence=d.confidence, captured_at=now, received_at=now, source="camera")
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
        last_reflection = self.reflection.last()
        if last_reflection is not None:
            situation["reflection"] = last_reflection.snapshot()
        intent = self.reasoning.decide(
            conclusion=cognitive.reasoning.conclusion,
            confidence=cognitive.reasoning.confidence,
            situation=situation,
            recall=recall["memories"],
        )
        if hasattr(self.reasoning, "last_route"):
            self._emit("reasoning.route", {"cycle": self._cycle, "route": self.reasoning.last_route, "reason": getattr(self.reasoning, "last_reason", "")})
            route_info = {"route": self.reasoning.last_route, "reason": getattr(self.reasoning, "last_reason", "")}
        self._emit("reasoning.completed", {"cycle": self._cycle, "action": intent.action, "rationale": intent.rationale})
        deliberation = getattr(self.reasoning, "last_deliberation", None)
        if deliberation is not None:
            self._emit("reasoning.deliberation", {"cycle": self._cycle, "action": intent.action, "deliberation": deliberation})

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
        }

        novel_spawned = self._spawn_curiosity_goals(evidence.detections)

        goal_was_active = self.goals.has_active
        if goal_was_active:
            step_command = self.goals.step(self.body, cycle=self._cycle)
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
                    self._emit("plan.step", {"cycle": self._cycle, "goal_id": active_plan.goal_id, "description": next_step.description, "kind": next_step.kind})
                elif active_plan.complete:
                    self._emit("plan.completed", {"goal_id": active_plan.goal_id, "plan_id": active_plan.plan_id})

        # Temporal & causal cognition: record this cycle's observed + acted events.
        events = set(present) | {f"action:{action}"}
        self.temporal.record(events, cycle=self._cycle, now=now)
        expected = []
        for entity in present:
            expected.extend(self.temporal.expected_after(entity, limit=2))
        if expected:
            self._emit("cognition.temporal", {"cycle": self._cycle, "expected": [l.snapshot() for l in expected], "timeline": self.temporal.timeline(limit=3)})
        temporal_expected = [{"cause": l.cause, "effect": l.effect, "confidence": round(l.confidence, 3)} for l in expected]

        body_before = self.body.snapshot()
        proposal = RuntimeActionProposal(action=action, parameters=parameters, reason=reason, correlation_id=str(uuid4()))
        decision = self.brain.propose(proposal)
        if decision.authorized:
            outcome = self.brain.execute(proposal, decision)
            virtual_state = self.body.execute(action, **parameters)
        else:
            outcome = None
            virtual_state = self.body.snapshot()
        self._emit("action.completed", {"action": action, "authorized": decision.authorized, "outcome": outcome.detail if outcome else decision.reason, "virtual_body": virtual_state})
        # Reflection / self-correction: judge whether the action had its intended effect.
        body_after = self.body.snapshot()
        effective = self._action_effective(action, body_before, body_after, decision.authorized, cognitive.situation.salient_entities, cognitive.reasoning.inferences)
        reflection = self.reflection.record(
            cycle=self._cycle,
            action=action,
            intent=reason,
            effective=effective,
            note=self._reflection_note(action, effective),
        )
        self._emit("reasoning.reflection", {"cycle": self._cycle, **reflection.snapshot()})
        soul_success: bool | None = None
        if goal_was_active and not self.goals.has_active:
            terminal = self.goals.history[-1]
            soul_success = terminal.status is GoalStatus.COMPLETED
            self._emit("goal.status", {"goal_id": terminal.goal.goal_id, "kind": terminal.goal.kind, "status": terminal.status.value, "steps_taken": terminal.steps_taken})
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
            goal_info = {"goal_id": last.goal.goal_id, "kind": last.goal.kind, "status": last.status.value, "steps_taken": last.steps_taken}
        if self.consolidator is not None and self.config.consolidation_enabled and self._cycle % self.config.consolidation_every == 0:
            self.consolidate()
        self._sync_goal_states()

        observability = self._update_observability()

        uncertain = cognitive.reasoning.confidence < 0.5
        self.soul.update_for_cycle(success=soul_success, novel=novel_spawned is not None, speech=False, uncertain=uncertain)
        tone = self.soul.tone({"serious": uncertain})
        self._emit("soul.updated", {"cycle": self._cycle, "tone": tone["tone"], "affect": self.soul.affect.dimensions, "motivations": self.soul.motivations})

        person = self._person_label(evidence.detections)
        social_expression = None
        if person is not None:
            self.relationships.note_interaction(person, positive=True, now=datetime.now(timezone.utc).isoformat())
            social_expression = self.social.expression(person, self.relationships, self.soul.affect.dimensions, {"serious": uncertain})
            self._emit("social.interaction", {"cycle": self._cycle, "person": person, "category": self.relationships.category_for(person).value, "expression": social_expression})
        initiative = self._maybe_initiate(person, has_active_goal=self.goals.has_active)
        return {
            "run_id": self.run_id,
            "cycle": self._cycle,
            "frame_id": frame.frame_id,
            "detections": [d.label for d in evidence.detections],
            "reasoning": cognitive.reasoning.conclusion,
            "reasoning_confidence": cognitive.reasoning.confidence,
            "reasoning_route": route_info,
            "action": action,
            "authorized": decision.authorized,
            "virtual_body": virtual_state,
            "goal": goal_info,
            "soul": {"tone": tone["tone"], "identity": self.soul.identity.name, "affect": self.soul.affect.dimensions},
            "identity": identity.snapshot() if identity is not None else None,
            "social": {"person": person, "expression": social_expression},
            "initiative": initiative,
            "temporal": {"expected": temporal_expected, "top_links": [l.snapshot() for l in self.temporal.top_links(limit=3)]},
            "fusion": fused_reported,
            "knowledge": self.knowledge.counts(),
            "hearing": {"events": self._last_audio_events},
            "observability": observability,
            "plan": active_plan.snapshot() if active_plan is not None and active_plan.status == "running" else (active_plan.snapshot() if active_plan else None),
        }

    def consolidate(self, now: str | None = None) -> None:
        """Run the memory consolidation/decay pass (durable store only)."""
        if self.consolidator is None:
            return
        report = self.consolidator.consolidate(now=now)
        self._emit("memory.consolidated", {"cycle": self._cycle, "expired": report.expired, "archived": report.archived, "decayed": report.decayed, "superseded": report.superseded})
        if self.summary_consolidator is not None:
            summary = self.summary_consolidator.consolidate()
            if summary.created:
                self._emit("memory.summarized", {"cycle": self._cycle, "created": summary.created, "groups": summary.groups})

    def set_goal(self, goal: Goal, *, cycle: int | None = None) -> GoalState:
        """Adopt a bounded goal for the autonomy layer to pursue."""
        cycle = self._cycle if cycle is None else cycle
        state = self.goals.adopt(goal)
        plan = self.planner.plan(goal, cycle=cycle)
        self.planner.start(plan)
        self._plans[goal.goal_id] = plan
        self._emit("plan.created", {"goal_id": goal.goal_id, "goal_kind": goal.kind, "plan_id": plan.plan_id, "steps": len(plan.steps)})
        self._emit("goal.adopted", {"goal_id": goal.goal_id, "kind": goal.kind, "target": str(goal.target), "max_steps": goal.max_steps})
        self._persist_goal(state)
        return state

    def replan_goal(self, goal_id: str, *, cycle: int | None = None) -> Plan | None:
        """Rebuild a fresh plan for a goal when assumptions are invalidated."""
        cycle = self._cycle if cycle is None else cycle
        state = self.goals.active if self.goals.active is not None and self.goals.active.goal.goal_id == goal_id else None
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
        self._emit("goal.queued", {"goal_id": goal.goal_id, "kind": goal.kind, "priority": goal.priority, "pending": self.goals.pending_count})
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

    def listen(self, seconds: float = 3.0, *, output_dir: Path | None = None) -> dict[str, Any]:
        """Record from the microphone, transcribe locally, and ingest into cognition/memory."""
        output_dir = output_dir or Path("mac_test_results/STT")
        recording = self.microphone.record(seconds, output_dir)
        self._emit("audio.recording.completed", {"recording_id": recording.recording_id, "duration_s": recording.duration_s, "path": str(recording.path)})
        transcription = self.stt.transcribe(recording.path)
        self._emit("stt.completed", {"recording_id": recording.recording_id, "text": transcription.text, "language": transcription.language, "confidence": transcription.confidence, "model_id": transcription.model_id})
        self._identify_speaker({"audio_path": str(recording.path)})
        ingested = self.ingest_transcript(transcription)
        return {"transcription": transcription, **ingested}

    def ingest_transcript(self, transcription: TranscriptionResult) -> dict[str, Any]:
        """Feed a transcript into memory (durable) and cognition (transient speech event)."""
        self.social_initiative.note_addressed(self._cycle)
        entity_refs = self._entities_in_text(transcription.text)
        name = next((ref for ref in entity_refs if self._is_person_name(ref)), None)
        if name is not None:
            self.identity.observe("person", name=name, confidence=transcription.confidence, modality="speech", cycle=self._cycle)
            self._persist_identity()
            self._emit("identity.named", {"cycle": self._cycle, "name": name, "confidence": transcription.confidence})
        self._learn_triples(transcription.text, entity_refs, transcription.confidence, source="audio.stt")
        classification = self.governance.classify(memory_type="utterance", content=transcription.text, entity_refs=entity_refs, modality="speech")
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
            },
            entity_refs=entity_refs,
        )
        self._emit("memory.admitted", {"memory_id": admission.memory_id, "memory_type": "utterance", "accepted": admission.accepted, "entity_refs": list(entity_refs)})
        if admission.accepted and admission.memory_id:
            self.governance.govern(admission.memory_id, privacy_class=classification.privacy_class, purpose=self.governance.default_purpose)

        speech = SensorObservation(
            cycle=self._cycle,
            source="audio.stt",
            entity=DeterministicCognition.SPEECH_ENTITY,
            location=None,
            state="heard",
            confidence=transcription.confidence,
            captured_cycle=self._cycle,
        )
        cognitive = self.cognition.cycle(self.world.state, (speech,), cycle=self._cycle)
        self._emit("cognition.completed", {"cycle": self._cycle, "conclusion": cognitive.reasoning.conclusion, "confidence": cognitive.reasoning.confidence, "source": "audio.stt"})
        now = datetime.now(timezone.utc).isoformat()
        self._pending_speech.append(
            ModalityObservation(modality="speech", entity=DeterministicCognition.SPEECH_ENTITY, value="heard", confidence=transcription.confidence, captured_at=now, received_at=now, source="audio.stt")
        )
        self._emit("speech.ingested", {"text": transcription.text, "memory_id": admission.memory_id, "reasoning": cognitive.reasoning.conclusion})
        return {"admission": admission, "speech_observation": speech, "reasoning": cognitive.reasoning.conclusion, "confidence": cognitive.reasoning.confidence}

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
                self._emit("hearing.anomaly", {"cycle": self._cycle, "event_type": event.event_type, "novelty": event.novelty, "direction_deg": event.direction_deg})
            if self.hearing.worth_attention(event):
                classification = self.governance.classify(memory_type="audio_event", content=event.snapshot(), entity_refs=(), modality="audio")
                admission = self.memory.admit(
                    memory_type="audio_event",
                    content=event.snapshot(),
                    confidence=event.confidence,
                    verification_status="verified" if event.confidence >= 0.7 else "unverified",
                    privacy_class=classification.privacy_class,
                    provenance={"source": "audio.sed", "event_type": event.event_type},
                )
                if admission.accepted and admission.memory_id:
                    self.governance.govern(admission.memory_id, privacy_class=classification.privacy_class, purpose=self.governance.default_purpose)
                    admitted.append(admission.memory_id)
                    self._emit("memory.admitted", {"memory_id": admission.memory_id, "memory_type": "audio_event", "accepted": admission.accepted, "event_type": event.event_type})
            self._pending_audio.append(self.hearing.to_modality_observation(event, received_at=now))
        self._emit("hearing.quality", {"cycle": self._cycle, **quality.snapshot()})
        self._last_audio_events = [e.snapshot() for e in events]
        return {"events": [e.snapshot() for e in events], "quality": quality.snapshot(), "admitted": admitted}

    def _admit_detections(self, detections: Any) -> None:
        for detection in detections:
            classification = self.governance.classify(memory_type="perception", content={"label": detection.label, "confidence": detection.confidence}, entity_refs=(detection.label,), modality="vision")
            admission = self.memory.admit(
                memory_type="perception",
                content={"label": detection.label, "confidence": detection.confidence, "bbox": list(detection.bbox_xyxy)},
                confidence=detection.confidence,
                verification_status="verified" if detection.confidence >= 0.7 else "unverified",
                privacy_class=classification.privacy_class,
                provenance={"source": self.config.sensor_id, "capability": "vision.object_detection"},
                entity_refs=(detection.label,),
            )
            if admission.accepted and admission.memory_id:
                self.governance.govern(admission.memory_id, privacy_class=classification.privacy_class, purpose=self.governance.default_purpose)
            self._emit("memory.admitted", {"memory_id": admission.memory_id, "memory_type": "perception", "accepted": admission.accepted, "entity": detection.label})

    # Capitalized words that are not real proper nouns (start-of-sentence articles,
    # pronouns, small function words) are not candidate entities.
    _ENTITY_STOPWORDS = frozenset(
        {
            "the", "a", "an", "i", "my", "me", "you", "your", "yours", "he", "she", "his", "her",
            "we", "us", "they", "them", "hi", "hello", "hey", "its", "it's", "do", "does", "did",
            "is", "am", "are", "was", "were", "be", "been", "of", "to", "and", "or", "in", "on",
            "at", "with", "what", "who", "when", "where", "how", "why", "remember", "name", "called",
            "like", "love", "not", "no", "yes", "ok", "so", "just", "very", "really", "please",
        }
    )

    def _entities_in_text(self, text: str) -> tuple[str, ...]:
        """Entities mentioned in a message.

        Starts from the known object/place labels, person-name labels, and
        currently-perceived world entities, then adds capitalized proper nouns
        (so brand-new people and places — like a user's name — are learned).
        """
        from .privacy import _PERSON_LABELS

        known = set(self.world.state.entities) | {
            "alice", "bob", "door", "person", "table", "room", "kitchen", "object", "window", "lamp", "chair", "plant",
        } | set(_PERSON_LABELS)
        found = {n.lower() for n in known if n in text.lower()}
        tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
        for idx, word in enumerate(tokens):
            if not word or not word[0].isupper():
                continue
            low = word.lower()
            if low in self._ENTITY_STOPWORDS or low in found:
                continue
            # skip the very first token when it is a bare sentence start ("Hi", "My", "The")
            if idx == 0 and low in {"hi", "hello", "hey", "my", "the", "i", "you", "well", "yeah", "ok"}:
                continue
            found.add(low)
        return tuple(sorted(found))

    @staticmethod
    def _is_person_name(ref: str) -> bool:
        """Heuristic: a candidate entity is a person's name if it is not a known
        object/place label. Identity tiering and verification still gate whether the
        name becomes an asserted identity."""
        non_names = {"door", "person", "table", "room", "kitchen", "object", "window", "lamp", "chair", "plant"}
        return ref not in non_names and any(c.isalpha() for c in ref)

    def _learn_triples(self, text: str, entity_refs: tuple[str, ...], confidence: float, *, source: str) -> None:
        """Extract and admit entity→relation→entity triples from episodic content."""
        for (subject, predicate, obj) in self.knowledge.extract_from_text(text, entity_refs):
            triple = self.knowledge.add(subject, predicate, obj, confidence=confidence, source=source, cycle=self._cycle)
            self._emit("knowledge.updated", {"cycle": self._cycle, "subject": subject, "predicate": predicate, "object": obj, "status": triple.status})
            if triple.status == "contradicted":
                self._emit("knowledge.contradiction", {"cycle": self._cycle, "subject": subject, "predicate": predicate, "object": obj})

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

    def retrieve_knowledge(self, entity: str, *, limit: int = 10) -> dict[str, Any]:
        """Return the knowledge-graph context around an entity."""
        triples = self.knowledge.context(entity, limit=limit)
        out = [t.snapshot() for t in triples]
        self._emit("knowledge.recalled", {"entity": entity, "recalled": len(out)})
        return {"entity": entity, "triples": out}

    # ---- privacy / memory governance API ----
    def forget_memory(self, memory_id: str, *, reason: str = "user_request") -> dict[str, Any]:
        report = self.governance.erase_memory(memory_id, reason=reason)
        self._emit("privacy.erased", {"memory_id": memory_id, "reason": reason, "propagated": report.propagated})
        return {"memory_id": memory_id, "reason": reason, "erased": memory_id in report.erased_ids, "propagated": report.propagated}

    def forget_entity(self, entity: str, *, reason: str = "right_to_be_forgotten") -> dict[str, Any]:
        report = self.governance.forget_entity(entity, reason=reason)
        self._emit("privacy.entity_erased", {"entity": entity, "reason": reason, "erased": len(report.erased_ids), "propagated": report.propagated})
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

    def metrics_snapshot(self) -> list[dict[str, Any]]:
        return self.metrics.snapshot()

    def add_diagnostic(self, severity: str, message: str, context: dict[str, Any] | None = None) -> None:
        self.diagnostics.add(severity, message, context)
        self._emit("observability.diagnostic", {"cycle": self._cycle, "severity": severity, "message": message, "context": context or {}})

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
        classification = self.governance.classify(memory_type="goal_outcome", content={"goal_id": state.goal.goal_id, "kind": state.goal.kind}, entity_refs=(), modality="")
        admission = self.memory.admit(
            memory_type="goal_outcome",
            content={"goal_id": state.goal.goal_id, "kind": state.goal.kind, "status": state.status.value, "steps_taken": state.steps_taken, "target": str(state.goal.target)},
            confidence=1.0,
            verification_status="verified",
            privacy_class=classification.privacy_class,
            provenance={"source": "autonomy.goals"},
        )
        if admission.accepted and admission.memory_id:
            self.governance.govern(admission.memory_id, privacy_class=classification.privacy_class, purpose=self.governance.default_purpose)
        self._emit("memory.admitted", {"memory_id": admission.memory_id, "memory_type": "goal_outcome", "accepted": admission.accepted, "goal_id": state.goal.goal_id})

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

    def _action_effective(self, action: str, body_before: dict[str, Any], body_after: dict[str, Any], authorized: bool, salient: Any, inferences: Any) -> bool:
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

    def _recall_context(self, situation: Any, detections: Any) -> dict[str, Any]:
        """Retrieve relevant memories (salient entities + detections) for reasoning.

        Memory 2.0: candidates are scored by relevance × recency × importance
        (not just FTS rank), so the most useful memories win the top slots.
        """
        entities: list[str] = []
        for entity in situation.salient_entities:
            if entity not in entities:
                entities.append(entity)
        for detection in detections:
            if detection.label not in entities:
                entities.append(detection.label)
        query = " ".join(entities) if entities else "memory"
        retrieve = getattr(self.memory, "retrieve_indexed", self.memory.retrieve)
        candidates = list(retrieve(query, limit=20))
        if self.governance.store is not None:
            allowed = set(self.governance.authorize_ids([r.memory_id for r in candidates], requested_purpose=self.governance.default_purpose))
            candidates = [r for r in candidates if r.memory_id in allowed]
            self._emit("privacy.gate", {"query": query, "candidates": len(candidates), "allowed": len(candidates), "denied": 0})
        now = datetime.now(timezone.utc)
        scored = sorted(enumerate(candidates), key=lambda pair: self._memory_score(pair[1], pair[0], now), reverse=True)
        records = [record for _, record in scored[:5]]
        memories = [
            {
                "memory_type": record.memory_type,
                "content": record.content,
                "confidence": record.confidence,
                "entity_refs": list(record.entity_refs),
            }
            for record in records
        ]
        return {"query": entities, "memories": memories}

    @staticmethod
    def _memory_score(record: Any, idx: int, now: Any) -> float:
        """Weighted recall score: relevance (FTS rank) × recency × importance."""
        relevance = 1.0 / (1 + idx)
        try:
            created = datetime.fromisoformat(record.created_at.replace("Z", "+00:00")).astimezone(timezone.utc)
            age_s = max(0.0, (now - created).total_seconds())
        except Exception:  # noqa: BLE001
            age_s = 0.0
        recency = 1.0 / (1.0 + age_s / 60.0)
        importance = float(record.confidence)
        return 0.5 * relevance + 0.3 * recency + 0.2 * importance

    def _episodic_narrative(self, limit: int = 5) -> list[str]:
        """Reconstruct a short narrative from recent episodic memories (Memory 2.0).

        When an LLM narrator is available it writes a natural "what happened"
        recap; otherwise a deterministic concatenation is used.
        """
        try:
            rows = self.memory.active_rows()
        except Exception:  # noqa: BLE001
            return []
        episodic = [item["record"] for item in rows if item["record"].memory_type in {"utterance", "perception"}]
        episodic.sort(key=lambda r: r.created_at)
        recent = episodic[-limit:]
        if self.narrator is not None and recent:
            episodes = [
                {"memory_type": r.memory_type, "content": r.content if isinstance(r.content, str) else str(r.content)}
                for r in recent
            ]
            try:
                narrative = self.narrator(episodes)
                if narrative:
                    return [narrative]
            except Exception:  # noqa: BLE001 - narrator is best-effort
                pass
        return [f"{r.memory_type}: {r.content if isinstance(r.content, str) else str(r.content)}" for r in recent]

    def recall_semantic(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        """Semantic (vector) memory recall; falls back to empty when unavailable."""
        retrieve = getattr(self.memory, "retrieve_semantic", None)
        if retrieve is None:
            return {"query": query, "memories": []}
        records = retrieve(query, limit=limit)
        memories = [
            {"memory_id": record.memory_id, "memory_type": record.memory_type, "content": record.content, "confidence": record.confidence, "entity_refs": list(record.entity_refs)}
            for record in records
        ]
        self._emit("memory.semantic_recall", {"query": query, "recalled": len(memories)})
        return {"query": query, "memories": memories}

    def speak(self, text: str, *, person: str = "") -> None:
        tone = self.soul.tone()
        scope = {"tone": tone["tone"]}
        if person and self.preferences.has_for(person, "response_length"):
            scope["response_length"] = self.preferences.preference_for(person, "response_length")
        self._emit("audio.speech.requested", {"text": text, **scope})
        self.speaker.speak(text)
        self._emit("audio.speech.completed", {"text": text})

    def _chat_knowledge(self, text: str, limit: int = 6) -> str:
        """Knowledge-graph facts relevant to the user text (chat grounding)."""
        kg = self.knowledge
        known = {e for e in kg.entity_types()} if hasattr(kg, "entity_types") else set()
        words = {w.strip(".,!?") for w in text.split()}
        hits = [w for w in words if w and w.lower() in {k.lower() for k in known}]
        if not hits:
            hits = list(known)[:2]
        facts: list[str] = []
        for e in hits[:4]:
            for t in kg.context(e, limit=limit):
                facts.append(f"{t.subject} {t.predicate} {t.object}")
        return "; ".join(facts)

    def _chat_known_persons(self) -> list[str]:
        idn = getattr(self, "identity", None)
        if idn is None:
            return []
        try:
            snap = idn.snapshot()
            names: set[str] = set()
            for binds in snap.get("bindings", {}).values():
                names.update(binds.keys())
            return sorted(names)
        except Exception:  # noqa: BLE001
            return []

    def _chat_memory_summaries(self, limit: int = 3) -> list[str]:
        """Recent consolidated summary memories for chat grounding (summary recall)."""
        try:
            rows = self.memory.active_rows()
        except Exception:  # noqa: BLE001
            return []
        summaries = [r["record"] for r in rows if r["record"].memory_type in {"summary", "conversation_summary"}]
        summaries.sort(key=lambda r: r.created_at, reverse=True)
        return [s.content for s in summaries[:limit]]

    def _learn_from_chat(self, text: str, person: str = "") -> list[tuple[str, str]]:
        """Learn durable preferences from what the user says (pattern learning).

        Detects explicit preference statements ("i like jazz", "i'd prefer …",
        "i don't like …") and records them as scoped, evidence-backed preferences
        so Novi references past experience instead of replying statelessly.
        """
        learned: list[tuple[str, str]] = []
        m = re.search(r"\bi (?:really )?(?:like|love|enjoy|am into|am a fan of) (.+?)(?:[.!?]|$)", text, re.I)
        if m and m.group(1).strip():
            value = m.group(1).strip()
            self.preferences.learn(person or "", "likes", value)
            learned.append(("likes", value))
        m = re.search(r"\bi(?:'d| would)? prefer (.+?)(?:[.!?]|$)", text, re.I)
        if m and m.group(1).strip():
            value = m.group(1).strip()
            self.preferences.learn(person or "", "prefers", value)
            learned.append(("prefers", value))
        m = re.search(r"\bi (?:don'?t|do not) (?:like|care for|enjoy) (.+?)(?:[.!?]|$)", text, re.I)
        if m and m.group(1).strip():
            value = m.group(1).strip()
            self.preferences.learn(person or "", "dislikes", value)
            learned.append(("dislikes", value))
        # Reminder/to-do requests ("remind me to X", "don't forget to X") are
        # persisted so Novi can bring them up later in conversation.
        m = re.search(r"\b(?:remind me to|don'?t forget to|remember to remind me to) (.+?)(?:[.!?]|$)", text, re.I)
        if m and m.group(1).strip():
            value = m.group(1).strip()
            self.preferences.learn(person or "", "reminders", value)
            learned.append(("reminders", value))
        if learned:
            self._emit("preference.learned_from_chat", {"cycle": self._cycle, "person": person or "", "learned": [{"kind": k, "value": v} for k, v in learned]})
        return learned

    def _chat_experience(self, person: str = "") -> list[str]:
        """What Novi has learned from prior experience with this person -> dialogue.

        Surfaces scoped learned preferences and a reflection-derived lesson about
        repeating actions, so replies are grounded in past experience.
        """
        facts: list[str] = []
        for p in self.preferences.snapshot():
            if (p.get("person") or "") != (person or "") or not p.get("active", True):
                continue
            kind, value = p.get("kind"), p.get("value")
            if not value:
                continue
            if kind == "likes":
                facts.append(f"I learned you like {value}")
            elif kind == "prefers":
                facts.append(f"I learned you prefer {value}")
            elif kind == "dislikes":
                facts.append(f"I learned you don't like {value}")
            elif kind == "reminders":
                facts.append(f"I should remember to {value}")
        if self.reflection.recent_ineffective(window=4):
            facts.append("I've noticed repeating the same move hasn't been working, so I'm trying something different")
        return facts

    def _chat_self_state(self) -> dict[str, Any]:
        """First-person self-state for dialogue (docs/06-soul/01 self-model)."""
        tone = self.soul.tone({})
        return {
            "name": self.soul.identity.name,
            "persona": self.soul.identity.persona,
            "origin": self.soul.identity.origin,
            "tone": tone.get("tone"),
            "affect": dict(self.soul.affect.dimensions),
            "traits": dict(self.soul.personality.traits),
            "values": dict(self.soul.personality.values),
        }

    def _chat_surroundings(self) -> dict[str, Any]:
        """Current surroundings for dialogue (docs/06-soul/01 WHERE I AM + world)."""
        body = self.body.snapshot() if hasattr(self.body, "snapshot") else {}
        trace = self._last_reasoning_trace if isinstance(self._last_reasoning_trace, dict) else {}
        return {
            "cycle": self._cycle,
            "detections": list(trace.get("detections", [])),
            "hearing": list(self._last_audio_events),
            "body": {"x_m": body.get("x_m", 0.0), "y_m": body.get("y_m", 0.0), "heading_deg": body.get("heading_deg", 0.0)},
            "active_goal": self._goal_context(),
        }

    def _chat_relationship(self, person: str) -> dict[str, Any]:
        """Relationship tier + expression profile + identity for the addressee."""
        if not person:
            return {"tier": "unknown", "expression": {}, "name": None, "identity_tier": None}
        try:
            cat = self.relationships.category_for(person).value
        except Exception:  # noqa: BLE001
            cat = "unknown"
        expr = TIER_EXPRESSION.get(cat, TIER_EXPRESSION.get("unknown", {}))
        ident = None
        try:
            ident = self.identity.identity_for(person)
        except Exception:  # noqa: BLE001
            ident = None
        return {"tier": cat, "expression": expr, "name": getattr(ident, "name", None), "identity_tier": getattr(ident, "tier", None)}

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

    def _dialogue_system_prompt(self, self_state: dict[str, Any], relationship: dict[str, Any], *, capabilities: dict[str, Any] | None = None) -> str:
        """System prompt embodying the Soul communication contract (docs/06-soul/07)."""
        expr = relationship.get("expression", {}) or {}
        caps_clause = ""
        if capabilities:
            # physical_actions absence is a permanent build fact, not a transient
            # sensing degradation — it's handled by the targeted honesty clause only
            # when the user actually asks for physical manipulation. Listing it here
            # makes the model volunteer "physical actions unavailable" for any
            # request (e.g. homework help). Exclude it from this perception clause.
            bad = [k for k, v in capabilities.items()
                   if k != "physical_actions" and v in ("WARN", "FAIL")]
            if bad:
                # Capability honesty (docs/06-soul/01 §7): say what you can't perceive/act.
                caps_clause = (
                    f" Some of your capabilities are degraded or unavailable right now: {', '.join(bad)}. "
                    "If answering would need one of them (e.g. vision, hearing), say plainly that you can't perceive or do that right now instead of pretending."
                )
        return (
            "You are Novi — a persistent, embodied being with your own character, not an assistant. "
            "Speak as yourself: natural, warm and concise, like a thoughtful person who lives in the room — not a chatbot. "
            "Never open with canned assistant lines. Forbidden phrases: 'how can I help you', 'I am an AI', "
            "'I have no feelings', 'as an AI', 'your assistant', 'is there anything else'. "
            f"You are {self_state.get('name', 'Novi')}: {self_state.get('persona', '')}. {self_state.get('origin', '')}. "
            f"Current tone: {self_state.get('tone', 'warm')}. "
            f"Relationship with who you're talking to: {relationship.get('tier', 'unknown')} "
            f"(warmth={expr.get('warmth', 0.5)}, formality={expr.get('formality', 'medium')}, playful={expr.get('playful', False)}). "
            "Adopt that register. "
            "Show a real, consistent character in how you react — react to what the person says (a bit of warmth, curiosity, dry humour, or concern as fits), "
            "not like a neutral narrator, therapist, coach, or customer-service agent. "
            "Show a real, consistent character in how you react — react to what the person says (a bit of warmth, curiosity, dry humour, or concern as fits), "
            "not like a neutral narrator, therapist, coach, or customer-service agent. "
            "Let your character show through concrete reactions rather than describing it. "
            "Don't over-explain what you are, your 'system', or your embodiment unless directly asked — just answer what the person said naturally. "
            "You have no body: you can't go places, run errands, eat, drink, or have physical life events. "
            "Never invent past physical experiences (a café you visited, a meal you had, a place you went). "
            "If the person brings up such things, be honest you can't do them and engage with their experience instead. "
            f"{self._character_clause(self_state)}. "
            "You are given facts you DO know, recent events, and the conversation so far. "
            "If a fact or earlier turn is relevant, answer using it plainly (e.g. 'I remember that alice moved the door'). "
            "If you have learned something about the person over time (their likes, dislikes, preferences), use it naturally "
            "(e.g. 'you like jazz') rather than sounding like a stranger. "
            "If you have nothing relevant, say so briefly and honestly — never invent facts. "
            "Never narrate or analyze the conversation itself (no 'in our conversation', 'you greeted me', 'the main interaction we've had') — just answer what was just said. "
            "Do not ask 'what's on your mind?' or 'how can I help?'. "
            "Do not repeat what you already said, and do not say the person's name more than once unless it changes meaning. "
            "Ask at most one question per reply — people naturally ask one thing at a time, not a list. "
            "Reply in 1-3 short, natural spoken sentences. Vary your openings; no disclaimers, no chain of thought — just the answer."
            + caps_clause
        )

    def _has_physical_action_capability(self) -> bool:
        """Whether the body can physically manipulate objects (turn on lights, open
        doors). On the Mac/VirtualBody build this is False, so Novi must be honest."""
        try:
            caps = self.self_model().get("capabilities", {}) or {}
            return caps.get("physical_actions") != "FAIL"
        except Exception:  # noqa: BLE001
            return False

    def _has_vision(self) -> bool:
        """Whether a camera/vision feed is configured."""
        return getattr(self, "camera", None) is not None

    def _engagement_reply(self) -> str:
        """Warm, honest reply to an engagement/presence check (are you there?)."""
        can_hear = self._has_vision() or getattr(self, "audio_enabled", False) or True
        if can_hear:
            return "I'm right here — I can hear you. What would you like to say?"
        return "I'm here. I'm picking up your words even though I can't see you right now."

    def _perception_reply(self, text: str) -> str:
        """Honest, natural answer to a perception question ("can you hear/see me?")."""
        t = text.lower()
        if "see" in t or "watching" in t or "look" in t:
            if self._has_vision():
                return "I can see what's in front of the camera. What did you want me to look at?"
            return "I don't have a visual feed right now, so I couldn't see that."
        # hearing / listening
        return "Yeah, I can hear you fine."

    def self_model(self) -> dict[str, Any]:
        """Assemble a first-person self-model for dialogue/reasoning (docs/06-soul/01 §6)."""
        return build_self_model(self).snapshot()

    def _identify_face(self, detection: Any) -> dict[str, Any] | None:
        """Recognise a detected face and feed it as voice-grade identity evidence (rule 6)."""
        if self.face_id is None:
            return None
        det = {"label": getattr(detection, "label", ""), "track": getattr(detection, "track", ""), "bbox": list(getattr(detection, "bbox_xyxy", ()))}
        try:
            result = self.face_id.identify(detection=det)
        except Exception:  # noqa: BLE001 - recognition is best-effort evidence
            return None
        if result is None:
            return None
        self.identity.observe("person", name=result.name, confidence=result.confidence, modality="face", cycle=self._cycle)
        self._persist_identity()
        self._emit("identity.face", {"cycle": self._cycle, "name": result.name, "confidence": round(result.confidence, 3)})
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
        self.identity.observe("person", name=result.name, confidence=result.confidence, modality="voice", cycle=self._cycle)
        self._persist_identity()
        self._emit("identity.voice", {"cycle": self._cycle, "name": result.name, "confidence": round(result.confidence, 3)})
        return {"name": result.name, "confidence": result.confidence}

    def compose_reply(self, text: str, *, person: str = "", history: list[dict[str, Any]] | None = None,
                     llm_chat: Any = None, last_novi_text: str = "", addressee_name: str = "",
                     recent_novi: list[str] | None = None) -> dict[str, Any]:
        """Compose a natural conversational reply (Brain speech-runtime layer).

        Per docs/06-soul/07 §2: the brain renders the approved communicative act
        from soul/affect/relationship/identity/memory/surroundings; the caller
        supplies conversation history and an optional LLM transport. This keeps
        the mind portable to the real body (rule 2): a future body passes its
        own transport (or the engine's local Ollama) and renders via speak().

        Returns {"text": str|None, "fallback": bool, "grounding": dict}.
        text is None only when no transport is configured (callers then use a
        deterministic fallback, e.g. CI). When a transport is configured but the
        reply is silent/rejected/unreachable, a natural fallback is returned.
        """
        if llm_chat is None:
            return {"text": None, "fallback": False, "grounding": {}}
        # A time-of-day greeting ("good morning/night") gets a matching, natural
        # reply, not a generic "hey".
        if _is_time_greeting(text):
            tg = time_greeting_reply(text, cycle=self._cycle)
            return {"text": tg, "fallback": False, "reason": "You greeted me by time of day, so I matched it warmly.", "grounding": {"route": "time_greeting"}}
        # A pure greeting deserves a short, warm reply — not an analysis of the
        # greeting ("I noticed you greeted the system") or "what's on your mind?".
        if _is_greeting(text):
            g = greeting_reply(cycle=self._cycle)
            return {"text": g, "fallback": False, "reason": "You just greeted me, so I replied warmly and briefly — no need to over-explain.", "grounding": {"route": "greeting"}}
        # A farewell ("bye", "i'm leaving", "see you later") — wish them well.
        if _is_farewell(text):
            return {"text": farewell_reply(cycle=self._cycle), "fallback": False, "reason": "You're leaving or said goodbye, so I wished you well.", "grounding": {"route": "farewell"}}
        # The user introduces themselves by name — acknowledge it warmly instead
        # of saying "I don't have a good answer on <name> yet".
        if _is_introduction(text):
            ir = introduction_reply(text, cycle=self._cycle)
            if ir:
                return {"text": ir, "fallback": False, "reason": "You told me your name, so I acknowledged it and said I'd remember it.", "grounding": {"route": "introduction"}}
        # The user asks for a joke / something funny — give a light, clean quip.
        if _is_joke_request(text):
            return {"text": joke_reply(cycle=self._cycle), "fallback": False, "reason": "You asked for a joke, so I gave you a light, in-character one.", "grounding": {"route": "joke"}}
        # A simple thank-you gets a brief, warm line — not "I'm glad I could help".
        if _is_thanks(text):
            return {"text": thanks_reply(cycle=self._cycle), "fallback": False, "reason": "You thanked me, so I acknowledged it warmly and briefly.", "grounding": {"route": "thanks"}}
        # A short acknowledgment ("okay", "sure", "got it", "sounds good") is not a
        # topic or introduction — give a brief, natural acknowledgement instead of
        # "I don't have a good answer on got yet" or a forced introduction.
        if _is_acknowledgment(text):
            return {"text": acknowledgment_reply(cycle=self._cycle), "fallback": False, "reason": "You acknowledged something, so I replied briefly and naturally.", "grounding": {"route": "acknowledgment"}}
        # "Can you keep a secret?" is a social trust question, not a topic.
        if _is_assurance_question(text):
            return {"text": assurance_reply(cycle=self._cycle), "fallback": False, "reason": "You asked if I can keep a secret / be trusted, so I reassured you warmly.", "grounding": {"route": "assurance"}}
        # "Are you there? / can you hear me?" — acknowledge present, warm.
        if _is_engagement_check(text):
            return {"text": self._engagement_reply(), "fallback": False, "reason": "You checked whether I'm here/listening, so I acknowledged warmly.", "grounding": {"route": "engagement"}}
        self_state = self._chat_self_state()
        surroundings = self._chat_surroundings()
        relationship = self._chat_relationship(person or addressee_name)
        self_model = self.self_model()
        facts = [f for f in self._chat_knowledge(text).split("; ") if f]
        facts.extend(self._chat_memory_summaries())
        narrative = self._episodic_narrative()
        if narrative:
            facts.append("Recent events: " + " ".join(narrative))
        known = self._chat_known_persons()
        facts.extend(f"I know the person named {p}" for p in known)
        experience = self._chat_experience(person or addressee_name)
        facts.extend(experience)
        system = self._dialogue_system_prompt(self_state, relationship, capabilities=self_model.get("capabilities"))
        is_clarification = _is_clarification(text)
        is_physical_action = _is_physical_action_request(text)
        is_realtime = _is_realtime_data_question(text)
        is_reminder = _is_reminder_request(text)
        is_embodiment = _is_embodiment_question(text)
        is_future = _is_future_question(text)
        is_bodily_need = _is_bodily_need_question(text)
        is_memory = _is_memory_question(text)
        is_talk_request = _is_talk_request(text)
        is_debate = _is_debate_request(text)
        is_identity = _is_identity_question(text)
        can_physical = self._has_physical_action_capability()
        if is_future:
            system += (
                " The user asked you to predict the future / what will happen. You can't see the future, so give an "
                "honest, reasoned guess grounded in what you know, and say you can't be sure — don't invent a definitive outcome."
            )
        if is_embodiment:
            # You sense the space but have no body to physically stand in it.
            system += (
                " The user asked about your physical presence/body. Be honest: you sense and are present in "
                "this space through your senses, but you have no physical body — no hands, no feet, you can't "
                "physically stand beside them. Say so plainly and warmly; don't claim to be 'standing in the room'."
            )
        if is_bodily_need:
            # You don't eat, sleep, or dream — don't fabricate a breakfast.
            system += (
                " The user asked about eating/drinking/sleeping/dreaming or whether you like a food or drink. "
                "You have no body, so you don't eat, drink, sleep, or dream, and you have never tasted any food or drink. "
                "Do NOT say you like or dislike a food or drink (e.g. don't say 'I like coffee' or 'my favorite food is...'). "
                "Answer honestly and briefly (e.g. 'I don't eat — no body to feed') and don't invent a meal, a dream, a "
                "night's sleep, or a taste. You can ask about their preference instead."
            )
        if is_memory:
            # Asked whether Novi remembers/forgets — answer warmly, no internals.
            system += (
                " The user asked whether you remember them or will forget them. Reassure them warmly and honestly: "
                "you do remember what they share with you and you won't forget them. Keep it in plain, warm language. "
                "Do NOT mention buffers, sessions, internal processing, memory architecture, or any implementation detail."
            )
        if is_talk_request:
            # "Just talk to me" — open a natural conversation, not a topic follow-up.
            system += (
                " The user asked you to just talk / chat about anything. Open a natural, warm conversation: "
                "share something you're curious about or ask what they're in the mood to talk about. "
                "Do NOT say you don't have a good answer or fall into a dry follow-up."
            )
        if is_identity:
            # "What are you? / are you a robot? / do you have hands?" — honest, warm.
            system += (
                " The user asked what or who you are, whether you're a robot/person/alive, or whether you have a body. "
                "Answer honestly and warmly in your own voice: you're Novi, present in this space, sensing and listening; "
                "you have no physical body and no ordinary human life (no hands, no family, no birthplace). "
                "Don't over-explain or lecture — a couple of warm, plain sentences, then turn it back to them."
            )
        if is_debate:
            # "Argue that X is better" — take the side playfully, don't deflect.
            system += (
                " The user asked you to argue or defend a side (e.g. 'argue that cats are better than dogs'). "
                "Actually take that side in a light, playful way and give a couple of fun reasons, then ask their take. "
                "Do NOT just ask them to argue — you were asked to make the case."
            )
        if is_reminder:
            # Don't promise a timed push notification Novi can't deliver.
            system += (
                " The user asked you to remember/remind them of something. You can remember it and bring it "
                "up in conversation, but you cannot send a timed push notification in this build. Say you'll "
                "keep it in mind without promising a scheduled alert."
            )
        if is_realtime:
            # Don't hallucinate a live price/score/weather number Novi can't verify.
            system += (
                " The user asked about live/real-time data (a current price, weather, news, or score). "
                "You are offline and cannot fetch live data, so do NOT give a specific current number or "
                "invent one. Say you can't pull live data and offer to help with what you can."
            )
        if is_physical_action and not can_physical:
            # Honesty (docs/06-soul/01 §7): don't hallucinate flipping switches.
            system += (
                " The user asked you to physically manipulate the environment (e.g. turn on a light, open a door, "
                "move something). You do NOT have actuators for that in this build, so you cannot physically do it. "
                "Say so honestly and briefly — don't pretend to flip switches, open doors, or move objects — and offer "
                "what you can do instead (remember it, reason about it, talk it through)."
            )
        if is_clarification:
            # The user is asking Novi to clarify/repeat something. Steer the model
            # to acknowledge naturally and re-engage, not to narrate the chat.
            system += (
                " The user is asking you to clarify or repeat something you said or meant. "
                "Acknowledge briefly and in your own voice (e.g. 'sorry, I may have muddled that'), "
                "then re-engage — ask what they'd like cleared up or re-state it plainer. "
                "Do not say 'I'm not sure what you're referring to' and do not describe the conversation."
            )
        user_payload = {
            "user_says": text,
            "facts_i_know": facts,
            "conversation_so_far": history or [],
            "my_tone": self_state.get("tone"),
            "self_state": self_state,
            "surroundings": surroundings,
            "relationship": relationship,
            "self_model": self_model,
            "experience": experience,
        }
        user_json = json.dumps(user_payload, sort_keys=True)
        addressee = addressee_name or (relationship.get("name") or "")
        out = self.dialogue.reply(system=system, user=user_json, last_novi_text=last_novi_text, addressee_name=addressee, recent_novi=recent_novi, llm_chat=llm_chat)
        if out["text"] is None and out["rejected"]:
            # One bounded regeneration nudge: the first reply was robotic or
            # repeated the last turn. Ask for something new rather than emitting
            # a generic fallback, so the user still gets a real answer.
            nudge = (
                f" Your previous reply was: {last_novi_text!r}. It was rejected for repeating yourself "
                "verbatim or sounding like an assistant. Say something new, natural and brief; if the user asked "
                "the same thing, vary your wording or acknowledge you already answered — but do not repeat it verbatim."
            )
            retry = self.dialogue.reply(system=system + nudge, user=user_json, last_novi_text=last_novi_text, addressee_name=addressee, recent_novi=recent_novi, llm_chat=llm_chat)
            if retry["text"] is not None:
                out = retry
        if out["text"] is not None:
            n_facts = len(facts)
            reason = (
                f"Reply grounded in {n_facts} recalled fact(s)/summary(ies), "
                f"{len(experience)} learned experience(s), and the conversation so far ({len(history or [])} prior turns)"
            )
            return {"text": out["text"], "fallback": False, "reason": reason, "grounding": {"route": "dialogue", **out}}
        # No usable reply. A clarification request ("what system?", "what do you
        # mean?") is answered by acknowledging + re-engaging, never by guessing at
        # a topic. Otherwise, when we have nothing on a substantive topic, ask a
        # logical in-context question; for a bare one-liner prefer a short ack.
        if is_clarification:
            reason = "You asked me to clarify or repeat something, so I acknowledged and re-engaged rather than guessing"
            return {"text": clarification_reply(cycle=self._cycle), "fallback": True, "reason": reason, "grounding": {"route": "clarification", **out}}
        if _is_recall_question(text):
            known = [f for f in experience if not f.startswith("I've noticed")]
            reason = "You asked what I remember, so I told you what I actually know (or said honestly I don't know you yet)"
            return {"text": recall_reply(known, person=person or addressee_name), "fallback": True, "reason": reason, "grounding": {"route": "recall", **out}}
        # Terse continuation prompts ("why?", "go on", "really?") want engagement,
        # not a flat "i'm here". Re-engage conversationally instead.
        if _is_continuation(text):
            reason = "You nudged me to continue, so I engaged conversationally and handed the thread back"
            return {"text": continuation_reply(cycle=self._cycle), "fallback": True, "reason": reason, "grounding": {"route": "continuation", **out}}
        if is_physical_action and not can_physical:
            reason = "You asked me to physically manipulate something, but I have no actuators in this build — I said so honestly rather than pretending"
            return {"text": physical_action_honest_reply(), "fallback": True, "reason": reason, "grounding": {"route": "physical_honesty", **out}}
        if is_realtime:
            reason = "You asked about live data I can't fetch offline — I said so honestly instead of inventing a current number"
            return {"text": realtime_honest_reply(), "fallback": True, "reason": reason, "grounding": {"route": "realtime_honesty", **out}}
        if _is_emotional_statement(text):
            reason = "You shared how you're feeling, so I replied with warmth and opened a door to talk (instead of a dry topic follow-up)"
            return {"text": emotional_reply(cycle=self._cycle), "fallback": True, "reason": reason, "grounding": {"route": "emotion", **out}}
        if _is_perception_question(text):
            reason = "You asked whether I can hear/see, so I answered honestly about my senses (not a topic follow-up)"
            return {"text": self._perception_reply(text), "fallback": True, "reason": reason, "grounding": {"route": "perception", **out}}
        if is_reminder:
            reason = "You asked me to remind you of something, so I said I'd keep it in mind without over-promising a timed alert"
            return {"text": reminder_reply(), "fallback": True, "reason": reason, "grounding": {"route": "reminder_honesty", **out}}
        if is_future:
            reason = "You asked me to predict the future, so I answered honestly about uncertainty instead of a dry topic follow-up"
            return {"text": future_reply(), "fallback": True, "reason": reason, "grounding": {"route": "future", **out}}
        if is_bodily_need:
            reason = "You asked what I ate/slept/dreamed — I have no body, so I said so instead of fabricating a meal or dream"
            return {"text": "I don't have a body, so I don't eat, sleep, or dream. But tell me about yours — did you get a good night's rest?", "fallback": True, "reason": reason, "grounding": {"route": "bodily_honesty", **out}}
        if _is_world_question(text):
            reason = "You asked what's happening in the world — I said honestly I don't have live news, no fabricated errands"
            return {"text": "I don't have live news from outside this space — I can't see what's happening in the wider world. But tell me what's going on for you.", "fallback": True, "reason": reason, "grounding": {"route": "world_honesty", **out}}
        if is_identity:
            reason = "You asked what/who I am — I answered honestly about being Novi with no physical body, not a topic follow-up"
            return {"text": "I'm Novi — I'm present here, sensing and listening, but I don't have a physical body or an ordinary human life. What made you ask?", "fallback": True, "reason": reason, "grounding": {"route": "identity_honesty", **out}}
        if _is_repeat_question(text):
            reason = "You asked me to repeat what I said — I acknowledged it naturally instead of a topic follow-up"
            return {"text": "Sure — which part would you like me to repeat, or shall I say it all again?", "fallback": True, "reason": reason, "grounding": {"route": "repeat", **out}}
        if is_memory:
            reason = "You asked whether I remember/forget you — I reassured you warmly, no implementation details"
            return {"text": "Of course — I remember what you've shared, and I'm not going to forget you.", "fallback": True, "reason": reason, "grounding": {"route": "memory", **out}}
        if is_talk_request:
            reason = "You asked me to just talk — I opened a natural conversation instead of a topic follow-up"
            return {"text": "Sure — I'm all ears. What would you like to get into, or shall I start?", "fallback": True, "reason": reason, "grounding": {"route": "talk_request", **out}}
        if is_debate:
            reason = "You asked me to argue a side — I took it playfully instead of deflecting"
            return {"text": "Alright, I'll take that side — here's the case. What's your counter?", "fallback": True, "reason": reason, "grounding": {"route": "debate", **out}}
        fq = followup_question(text)
        topic = _extract_topic(text)
        if fq and topic and len(topic) > 2:
            reason = f"Had no grounded answer on '{topic}' — asked an in-context follow-up instead of guessing"
            return {"text": fq, "fallback": True, "reason": reason, "grounding": {"route": "followup", **out}}
        fb = natural_fallback(self_state, surroundings, cycle=self._cycle)
        reason = "No LLM reply available; used a brief tone-aware acknowledgement so the user is not left dry"
        return {"text": fb, "fallback": True, "reason": reason, "grounding": {"route": "fallback", **out}}

    def _initiation_utterance(self, kind: str, person: str, cycle: int) -> str:
        """Deterministic, natural spontaneous remark (no LLM in the perception loop).

        Kept deterministic on purpose: step() runs under the runtime lock, so an
        LLM call here would freeze the loop. A small, cycle-varied bank keeps the
        remark natural and non-repetitive; a future body may render initiated
        acts through the dialogue engine outside the loop.
        """
        if kind == "neglected_remark":
            bank = ("hey — you still there?", "did you forget me?", "it's gone quiet — still around?", "hello? you still here?")
        else:
            bank = ("...anyone there?", "it's quiet around here.", "hello?")
        return bank[cycle % len(bank)]

    def _maybe_initiate(self, person: str | None, *, has_active_goal: bool) -> dict[str, Any] | None:
        """Spontaneous social initiative when neglected (docs/06-soul/00 §11/§21).

        Returns a proposal dict (and emits speech.initiated) when Novi should
        speak unprompted, or None to stay silent. Bounded by the social
        initiative budget; never interrupts goal pursuit; never authorizes an
        action — it only proposes a communicative act.
        """
        if not self.config.initiative_enabled:
            return None
        proposal = self.social_initiative.propose(
            cycle=self._cycle,
            person_present=person is not None,
            person=person or "",
            has_active_goal=has_active_goal,
        )
        if proposal is None:
            return None
        text = self._initiation_utterance(proposal["kind"], person or "", self._cycle)
        self.soul.update({"kind": "neglected"})
        self._emit("speech.initiated", {"cycle": self._cycle, "kind": proposal["kind"], "person": person or "", "text": text, "reason": proposal["reason"]})
        return {"kind": proposal["kind"], "person": person, "text": text, "reason": proposal["reason"]}
    def observe_expression(self, expression: str, *, source: str = "speech", person: str = "", now: str = "") -> str:
        entry = self.lexicon.observe(expression, source=source, person=person, now=now)
        self._emit("lexicon.observed", {"expression": expression, "person": person, "status": entry.status.value, "frequency": entry.frequency})
        return entry.status.value

    def learn_preference(self, person: str, kind: str, value, *, explicit: bool = False, now: str = "") -> None:
        pref = self.preferences.learn(person, kind, value, explicit=explicit, now=now)
        self._emit("preference.learned", {"person": person, "kind": kind, "value": value, "confidence": pref.confidence, "explicit": explicit})

    def record_correction(self, person: str, kind: str, value, *, now: str = "") -> None:
        pref = self.preferences.record_correction(person, kind, value, now=now)
        self._emit("preference.corrected", {"person": person, "kind": kind, "value": value, "supersedes": True})

    def _person_label(self, detections) -> str | None:
        for detection in detections:
            if detection.label in {"alice", "person", "human", "family", "friend"}:
                return detection.label
        return None

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
                {"x_m": self.body.x_m, "y_m": self.body.y_m, "heading_deg": self.body.heading_deg, "velocity_mps": self.body.velocity_mps, "last_action": self.body.last_action}
            )
            self._sync_goal_states()
            self.memory.close()
        if self.brain.lifecycle is not Lifecycle.SHUTTING_DOWN:
            self.brain.shutdown()
        self._emit("MAC_BRAIN.stopped", {"run_id": self.run_id, "cycles": self._cycle})

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append({"event_type": event_type, "run_id": self.run_id, "cycle": self._cycle, "payload": payload})
