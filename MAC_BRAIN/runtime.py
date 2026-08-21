from __future__ import annotations

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
from .consolidation import ConsolidationConfig, MemoryConsolidator
from .cognition import BeliefSystem, ExpectationSystem
from .cognition2 import MacCognition
from .fusion import ModalityObservation, MultimodalFusion
from .identity import PersonIdentity
from .io import Camera, MacMicrophone, MacSpeaker, VirtualBody
from .kgraph import EntityKnowledgeGraph
from .planner import Plan, Planner
from .privacy import PrivacyGovernance
from .audio import AudioEvent, AudioFrame, Hearing
from .observability import Diagnostics, HealthMonitor, MetricRegistry, default_health_checks
from .lexicon import LearnedPreferences, Lexicon
from .social import Relationships, SocialIntelligence
from .soul import Soul
from .storage import DurableMemoryStore
from .temporal import TemporalModel
from .models import (
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
        self.reasoning = reasoning or DeterministicReasoningProvider()
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
        }

        novel_spawned = self._spawn_curiosity_goals(evidence.detections)

        goal_was_active = self.goals.has_active
        if goal_was_active:
            step_command = self.goals.step(self.body, cycle=self._cycle)
            action = step_command.action
            parameters = step_command.parameters
            reason = "goal_pursuit"
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

        proposal = RuntimeActionProposal(action=action, parameters=parameters, reason=reason, correlation_id=str(uuid4()))
        decision = self.brain.propose(proposal)
        if decision.authorized:
            outcome = self.brain.execute(proposal, decision)
            virtual_state = self.body.execute(action, **parameters)
        else:
            outcome = None
            virtual_state = self.body.snapshot()
        self._emit("action.completed", {"action": action, "authorized": decision.authorized, "outcome": outcome.detail if outcome else decision.reason, "virtual_body": virtual_state})
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
        ingested = self.ingest_transcript(transcription)
        return {"transcription": transcription, **ingested}

    def ingest_transcript(self, transcription: TranscriptionResult) -> dict[str, Any]:
        """Feed a transcript into memory (durable) and cognition (transient speech event)."""
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
        """Retrieve relevant memories (salient entities + detections) for reasoning."""
        entities: list[str] = []
        for entity in situation.salient_entities:
            if entity not in entities:
                entities.append(entity)
        for detection in detections:
            if detection.label not in entities:
                entities.append(detection.label)
        query = " ".join(entities) if entities else "memory"
        retrieve = getattr(self.memory, "retrieve_indexed", self.memory.retrieve)
        records = list(retrieve(query, limit=5))
        if self.governance.store is not None:
            candidates = len(records)
            allowed = set(self.governance.authorize_ids([r.memory_id for r in records], requested_purpose=self.governance.default_purpose))
            records = [r for r in records if r.memory_id in allowed]
            self._emit("privacy.gate", {"query": query, "candidates": candidates, "allowed": len(records), "denied": candidates - len(records)})
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
