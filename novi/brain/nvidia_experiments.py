"""NoviEpisode schema + adapters for the Mac Brain (PERFECTING_PLAN Step 5).

A unified episode dataset schema with provenance + adapters (LeRobot/IsaacLab/
ROSBag/NoviNative) so NVIDIA formats never become the semantic source of truth.

Canonical authority:
  - docs/NOVI_NVIDIA_ROBOT_LEARNING_COGNITION_AUTONOMY_RESEARCH.md (research 20)
  - PERFECTING_PLAN/09_GAP_ANALYSIS_NVIDIA_INTEGRATION.md

Evidence classes OBSERVED/INFERRED/PREDICTED/SIMULATED are pinned on every
episode so simulations never silently become facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

# Reuse evidence classes from memory_hardening for consistency.
from .memory_hardening import (
    OBSERVED,
    SIMULATED,
)

# ---------------------------------------------------------------------------
# EpisodeStep — one step in an episode
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EpisodeStep:
    """One step in a NoviEpisode: observation, action, outcome."""
    step_id: str
    step_index: int
    timestamp: str
    observation: dict[str, Any]  # sensor data, detections, world state
    action: dict[str, Any]        # action taken (skill, parameters, governance)
    outcome: dict[str, Any]       # result, success/failure, world change
    evidence_class: str = OBSERVED  # OBSERVED/INFERRED/PREDICTED/SIMULATED
    provenance: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_index": self.step_index,
            "timestamp": self.timestamp,
            "observation": dict(self.observation),
            "action": dict(self.action),
            "outcome": dict(self.outcome),
            "evidence_class": self.evidence_class,
            "provenance": dict(self.provenance),
        }


# ---------------------------------------------------------------------------
# NoviEpisode — a complete episode in the unified schema
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NoviEpisode:
    """A unified episode dataset record with provenance.

    Adapters convert this to/from LeRobot, IsaacLab, ROSBag, or NoviNative
    formats. The NoviEpisode is the semantic source of truth; external formats
    are transport only.
    """
    episode_id: str
    task_name: str
    description: str
    steps: tuple[EpisodeStep, ...]
    evidence_class: str = OBSERVED  # overall evidence class for the episode
    provenance: dict[str, Any] = field(default_factory=dict)
    # platform tuple: pinned platform for reproducibility
    platform: dict[str, str] = field(default_factory=dict)
    # metadata: task type, environment, actor, etc.
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "task_name": self.task_name,
            "description": self.description,
            "step_count": len(self.steps),
            "steps": [s.snapshot() for s in self.steps],
            "evidence_class": self.evidence_class,
            "provenance": dict(self.provenance),
            "platform": dict(self.platform),
            "metadata": dict(self.metadata),
        }

    def to_dict(self) -> dict[str, Any]:
        return self.snapshot()


# ---------------------------------------------------------------------------
# Episode builders — create demonstration episodes
# ---------------------------------------------------------------------------

def build_navigate_episode(*, simulated: bool = False) -> NoviEpisode:
    """Build a Navigate demonstration episode (deterministic/mock)."""
    evidence = SIMULATED if simulated else OBSERVED
    source = "isaac_sim" if simulated else "mac_brain"

    steps = (
        EpisodeStep(
            step_id=str(uuid4()), step_index=0, timestamp="2026-01-01T10:00:00Z",
            observation={"robot_position": [0.0, 0.0], "target": "kitchen", "heading": 0.0},
            action={"skill": "navigate", "parameters": {"target_location": "kitchen"}, "risk_class": "R3"},
            outcome={"status": "running", "distance_traveled": 0.0},
            evidence_class=evidence,
            provenance={"source": source, "capability": "navigate_skill"},
        ),
        EpisodeStep(
            step_id=str(uuid4()), step_index=1, timestamp="2026-01-01T10:00:05Z",
            observation={"robot_position": [1.0, 0.0], "target": "kitchen", "heading": 0.0},
            action={"skill": "navigate", "parameters": {"target_location": "kitchen"}, "risk_class": "R3"},
            outcome={"status": "running", "distance_traveled": 1.0},
            evidence_class=evidence,
            provenance={"source": source, "capability": "navigate_skill"},
        ),
        EpisodeStep(
            step_id=str(uuid4()), step_index=2, timestamp="2026-01-01T10:00:10Z",
            observation={"robot_position": [2.5, 0.0], "target": "kitchen", "heading": 0.0},
            action={"skill": "navigate", "parameters": {"target_location": "kitchen"}, "risk_class": "R3"},
            outcome={"status": "SUCCESS", "destination": "kitchen", "distance_traveled": 2.5},
            evidence_class=evidence,
            provenance={"source": source, "capability": "navigate_skill"},
        ),
    )
    return NoviEpisode(
        episode_id=f"episode-{uuid4().hex[:12]}",
        task_name="navigate_to_kitchen",
        description="Navigate from start position to the kitchen.",
        steps=steps,
        evidence_class=evidence,
        provenance={"source": source, "experiment": "nvidia_exp_2_skill_contract"},
        platform={"runtime": "mac_brain", "simulated": str(simulated)},
        metadata={"task_type": "navigation", "skill": "navigate"},
    )


def build_pick_cup_episode(*, simulated: bool = False) -> NoviEpisode:
    """Build a Pick cup demonstration episode (Bring me that cup scenario)."""
    evidence = SIMULATED if simulated else OBSERVED
    source = "isaac_sim" if simulated else "mac_brain"

    steps = (
        EpisodeStep(
            step_id=str(uuid4()), step_index=0, timestamp="2026-01-01T10:00:00Z",
            observation={"cup_location": "table", "robot_position": [2.5, 0.0]},
            action={"skill": "find_object", "parameters": {"object_description": "cup"}, "risk_class": "R1"},
            outcome={"status": "SUCCESS", "object": "cup", "location": "table"},
            evidence_class=evidence,
            provenance={"source": source},
        ),
        EpisodeStep(
            step_id=str(uuid4()), step_index=1, timestamp="2026-01-01T10:00:03Z",
            observation={"cup_location": "table", "robot_position": [2.5, 0.0], "cup_visible": True},
            action={"skill": "pick", "parameters": {"object_id": "cup_001"}, "risk_class": "R3"},
            outcome={"status": "SUCCESS", "object_grasped": True},
            evidence_class=evidence,
            provenance={"source": source},
        ),
    )
    return NoviEpisode(
        episode_id=f"episode-{uuid4().hex[:12]}",
        task_name="pick_cup",
        description="Find and pick up the cup from the table (Bring me that cup).",
        steps=steps,
        evidence_class=evidence,
        provenance={"source": source, "experiment": "nvidia_exp_1_reference_resolution"},
        platform={"runtime": "mac_brain", "simulated": str(simulated)},
        metadata={"task_type": "manipulation", "skill": "pick", "referent": "cup"},
    )


# ---------------------------------------------------------------------------
# Episode adapters (LeRobot/IsaacLab/ROSBag/NoviNative)
# ---------------------------------------------------------------------------

class EpisodeAdapter:
    """Base adapter for converting NoviEpisode to/from external formats.

    NVIDIA formats (LeRobot, IsaacLab, ROSBag) are transport only; the
    NoviEpisode is the semantic source of truth. Adapters never lose
    provenance or evidence class.
    """

    format_name: str = "base"

    def to_format(self, episode: NoviEpisode) -> dict[str, Any]:
        raise NotImplementedError

    def from_format(self, data: dict[str, Any]) -> NoviEpisode:
        raise NotImplementedError


class NoviNativeAdapter(EpisodeAdapter):
    """NoviNative format — the canonical serialization (no loss)."""

    format_name = "novi_native"

    def to_format(self, episode: NoviEpisode) -> dict[str, Any]:
        return episode.to_dict()

    def from_format(self, data: dict[str, Any]) -> NoviEpisode:
        steps = tuple(
            EpisodeStep(
                step_id=s["step_id"], step_index=s["step_index"], timestamp=s["timestamp"],
                observation=s["observation"], action=s["action"], outcome=s["outcome"],
                evidence_class=s["evidence_class"], provenance=s["provenance"],
            )
            for s in data["steps"]
        )
        return NoviEpisode(
            episode_id=data["episode_id"], task_name=data["task_name"],
            description=data["description"], steps=steps,
            evidence_class=data["evidence_class"], provenance=data["provenance"],
            platform=data["platform"], metadata=data["metadata"],
        )


class LeRobotAdapter(EpisodeAdapter):
    """LeRobot format adapter (NVIDIA HuggingFace robotics dataset format).

    Converts to/from the LeRobot episode structure while preserving provenance
    and evidence class. The LeRobot format is transport only.
    """

    format_name = "lerobot"

    def to_format(self, episode: NoviEpisode) -> dict[str, Any]:
        return {
            "episode_id": episode.episode_id,
            "task": episode.task_name,
            "frames": [
                {
                    "frame_index": s.step_index,
                    "timestamp": s.timestamp,
                    "observation": s.observation,
                    "action": s.action,
                    "reward": 1.0 if s.outcome.get("status") == "SUCCESS" else 0.0,
                    "done": s.outcome.get("status") == "SUCCESS",
                    # Provenance preserved as metadata (not a native LeRobot field).
                    "_novi_outcome": s.outcome,
                    "_novi_evidence_class": s.evidence_class,
                    "_novi_provenance": s.provenance,
                }
                for s in episode.steps
            ],
            "_novi_evidence_class": episode.evidence_class,
            "_novi_provenance": episode.provenance,
        }

    def from_format(self, data: dict[str, Any]) -> NoviEpisode:
        steps = tuple(
            EpisodeStep(
                step_id=str(uuid4()), step_index=f["frame_index"],
                timestamp=f["timestamp"],
                observation=f["observation"], action=f["action"],
                outcome=f.get("_novi_outcome")
                or {"status": "SUCCESS" if f.get("reward", 0) >= 1.0 else "RUNNING"},
                evidence_class=f.get("_novi_evidence_class", OBSERVED),
                provenance=f.get("_novi_provenance", {}),
            )
            for f in data["frames"]
        )
        return NoviEpisode(
            episode_id=data["episode_id"], task_name=data["task"],
            description="", steps=steps,
            evidence_class=data.get("_novi_evidence_class", OBSERVED),
            provenance=data.get("_novi_provenance", {}),
            platform={"format": "lerobot"},
        )


class IsaacLabAdapter(EpisodeAdapter):
    """IsaacLab format adapter (NVIDIA Isaac simulation episodes).

    Converts to/from IsaacLab episode structure. Evidence class SIMULATED is
    always preserved so simulated episodes never silently become facts.
    """

    format_name = "isaac_lab"

    def to_format(self, episode: NoviEpisode) -> dict[str, Any]:
        return {
            "episode_id": episode.episode_id,
            "task_name": episode.task_name,
            "num_steps": len(episode.steps),
            "steps": [
                {
                    "step": s.step_index,
                    "obs": s.observation,
                    "action": s.action,
                    "result": s.outcome,
                    "_novi_evidence_class": s.evidence_class,
                    "_novi_provenance": s.provenance,
                }
                for s in episode.steps
            ],
            "_novi_evidence_class": episode.evidence_class,
            "_novi_provenance": episode.provenance,
        }

    def from_format(self, data: dict[str, Any]) -> NoviEpisode:
        steps = tuple(
            EpisodeStep(
                step_id=str(uuid4()), step_index=s["step"],
                timestamp="", observation=s["obs"], action=s["action"],
                outcome=s["result"],
                evidence_class=s.get("_novi_evidence_class", SIMULATED),
                provenance=s.get("_novi_provenance", {}),
            )
            for s in data["steps"]
        )
        return NoviEpisode(
            episode_id=data["episode_id"], task_name=data["task_name"],
            description="", steps=steps,
            evidence_class=data.get("_novi_evidence_class", SIMULATED),
            provenance=data.get("_novi_provenance", {}),
            platform={"format": "isaac_lab"},
        )


class ROSBagAdapter(EpisodeAdapter):
    """ROSBag format adapter (ROS2 bag recordings).

    Converts to/from ROS2 bag message structure. Provenance is preserved in
    message metadata.
    """

    format_name = "rosbag"

    def to_format(self, episode: NoviEpisode) -> dict[str, Any]:
        return {
            "bag_id": episode.episode_id,
            "topic": f"/novi/episode/{episode.task_name}",
            "messages": [
                {
                    "timestamp": s.timestamp,
                    "topic": f"/novi/step/{s.step_index}",
                    "data": {"observation": s.observation, "action": s.action, "outcome": s.outcome},
                    "_novi_evidence_class": s.evidence_class,
                    "_novi_provenance": s.provenance,
                }
                for s in episode.steps
            ],
            "_novi_evidence_class": episode.evidence_class,
            "_novi_provenance": episode.provenance,
        }

    def from_format(self, data: dict[str, Any]) -> NoviEpisode:
        steps = tuple(
            EpisodeStep(
                step_id=str(uuid4()), step_index=i,
                timestamp=msg["timestamp"],
                observation=msg["data"]["observation"],
                action=msg["data"]["action"],
                outcome=msg["data"]["outcome"],
                evidence_class=msg.get("_novi_evidence_class", OBSERVED),
                provenance=msg.get("_novi_provenance", {}),
            )
            for i, msg in enumerate(data["messages"])
        )
        return NoviEpisode(
            episode_id=data["bag_id"], task_name=data["topic"],
            description="", steps=steps,
            evidence_class=data.get("_novi_evidence_class", OBSERVED),
            provenance=data.get("_novi_provenance", {}),
            platform={"format": "rosbag"},
        )


ALL_ADAPTERS: dict[str, EpisodeAdapter] = {
    "novi_native": NoviNativeAdapter(),
    "lerobot": LeRobotAdapter(),
    "isaac_lab": IsaacLabAdapter(),
    "rosbag": ROSBagAdapter(),
}


# ---------------------------------------------------------------------------
# Experiment harness — run all NVIDIA no-hardware experiments
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExperimentResult:
    """Result of one NVIDIA experiment."""
    experiment_id: str
    name: str
    passed: bool
    evidence_class: str
    evidence_file: dict[str, Any]
    reason: str = ""
    validation_class: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "passed": self.passed,
            "evidence_class": self.evidence_class,
            "validation_class": self.validation_class,
            "evidence_file": self.evidence_file,
            "reason": self.reason,
        }


# Validation evidence classes (E0-E5) per
# docs/01-system-architecture/10_ARCHITECTURE_VALIDATION_AND_TRACEABILITY.md:
#   E0 design intent · E1 authoritative vendor/standards docs · E2 reproducible
#   benchmark · E3 integration validation · E4 physical · E5 long-duration.
# All no-hardware Mac experiments are deterministic cross-component tests, so
# E2 (reproducible Novi-controlled test) applies; Exp 3 additionally exercises
# cross-component integration (schema -> 4 adapters), hence E3.
VALIDATION_CLASS_BY_EXPERIMENT: dict[str, str] = {
    "nvidia_exp_1": "E2",  # reproducible reference-resolution benchmark
    "nvidia_exp_2": "E2",  # reproducible skill-contract invocation test
    "nvidia_exp_3": "E3",  # cross-component integration: schema + adapters round-trip
}


def run_nvidia_experiments() -> tuple[ExperimentResult, ...]:
    """Run all NVIDIA no-hardware experiments on the Mac.

    Exp 1: context-aware reference resolution (uses ContextAssembler + WorldModel).
    Exp 2: skill-contract invocation independent of implementation.
    Exp 3: demonstration dataset in NoviEpisode schema with adapters.
    """
    from .context_assembler import ContextAssembler, ContextRequest
    from .skill_contract import SUCCESS, SkillExecutor
    from .world_model import OBJECT, OBSERVED, PERSON, WorldModel

    results: list[ExperimentResult] = []

    # ---- Experiment 1: context-aware reference resolution ----
    wm = WorldModel()
    wm.add_entity("alice_001", PERSON, labels=["Alice"], epistemic_status=OBSERVED, confidence=0.95)
    wm.add_entity("cup_001", OBJECT, labels=["cup"], epistemic_status=OBSERVED, confidence=0.85)
    wm.update_entity_state("cup_001", "location", "kitchen", epistemic_status=OBSERVED, confidence=0.85, source="camera")
    assembler = ContextAssembler()
    request = ContextRequest(
        speaker_label="Alice", location="kitchen",
        utterance="bring me that cup", referenced_labels=("cup",), token_budget=5000,
    )
    ref_result = assembler.resolve_reference(wm, request, "that cup")
    exp1_passed = ref_result["status"] == "RESOLVED" and ref_result["label"] == "cup"
    results.append(ExperimentResult(
        experiment_id="nvidia_exp_1", name="context_aware_reference_resolution",
        passed=exp1_passed, evidence_class=OBSERVED, validation_class=VALIDATION_CLASS_BY_EXPERIMENT["nvidia_exp_1"],
        evidence_file=ref_result,
        reason=f"reference resolved to {ref_result.get('label')} with status {ref_result['status']}",
    ))

    # ---- Experiment 2: skill-contract invocation independent of implementation ----
    executor = SkillExecutor()
    nav_result = executor.invoke("navigate", {"target_location": "kitchen", "speed": 0.3},
                                  context={"robot_localized": True, "target_location_known": True, "path_clear": True})
    exp2_passed = nav_result.status == SUCCESS
    results.append(ExperimentResult(
        experiment_id="nvidia_exp_2", name="skill_contract_invocation",
        passed=exp2_passed, evidence_class=OBSERVED, validation_class=VALIDATION_CLASS_BY_EXPERIMENT["nvidia_exp_2"],
        evidence_file=nav_result.snapshot(),
        reason=f"skill navigate invoked with status {nav_result.status}",
    ))

    # ---- Experiment 3: demonstration dataset in NoviEpisode schema ----
    nav_episode = build_navigate_episode(simulated=False)
    pick_episode = build_pick_cup_episode(simulated=False)
    # Test round-trip through all adapters.
    all_roundtrips_ok = True
    for _, adapter in ALL_ADAPTERS.items():
        for episode in (nav_episode, pick_episode):
            formatted = adapter.to_format(episode)
            restored = adapter.from_format(formatted)
            if restored.evidence_class != episode.evidence_class:
                all_roundtrips_ok = False
            if len(restored.steps) != len(episode.steps):
                all_roundtrips_ok = False
    # Also test simulated episode.
    sim_episode = build_navigate_episode(simulated=True)
    sim_roundtrip = NoviNativeAdapter().to_format(sim_episode)
    sim_restored = NoviNativeAdapter().from_format(sim_roundtrip)
    sim_evidence_preserved = sim_restored.evidence_class == SIMULATED
    exp3_passed = all_roundtrips_ok and sim_evidence_preserved
    results.append(ExperimentResult(
        experiment_id="nvidia_exp_3", name="demonstration_dataset_novi_episode",
        passed=exp3_passed, evidence_class=OBSERVED, validation_class=VALIDATION_CLASS_BY_EXPERIMENT["nvidia_exp_3"],
        evidence_file={
            "episodes": [nav_episode.snapshot(), pick_episode.snapshot()],
            "simulated_episode": sim_episode.snapshot(),
            "adapters_tested": list(ALL_ADAPTERS.keys()),
            "all_roundtrips_ok": all_roundtrips_ok,
            "sim_evidence_preserved": sim_evidence_preserved,
        },
        reason=f"{len(ALL_ADAPTERS)} adapters tested, roundtrips {'OK' if all_roundtrips_ok else 'FAILED'}",
    ))

    return tuple(results)


# ---------------------------------------------------------------------------
# EpisodeRecorder — record episodes from the Mac Brain runtime
# ---------------------------------------------------------------------------

class EpisodeRecorder:
    """Records NoviEpisode datasets from the Mac Brain runtime.

    Usage:
        recorder = EpisodeRecorder(task_name="navigate_to_kitchen")
        recorder.record_step(observation={...}, action={...}, outcome={...})
        episode = recorder.build_episode()

    The recorder collects steps from the runtime and assembles them into a
    NoviEpisode with proper provenance and evidence class.
    """

    def __init__(
        self,
        task_name: str,
        *,
        description: str = "",
        evidence_class: str = OBSERVED,
        source: str = "mac_brain",
        platform: dict[str, str] | None = None,
    ) -> None:
        self.task_name = task_name
        self.description = description
        self.evidence_class = evidence_class
        self.source = source
        self.platform = platform or {"runtime": "mac_brain"}
        self._steps: list[EpisodeStep] = []
        self._step_index: int = 0

    def record_step(
        self,
        *,
        observation: dict[str, Any],
        action: dict[str, Any],
        outcome: dict[str, Any],
        timestamp: str = "",
        provenance: dict[str, Any] | None = None,
    ) -> EpisodeStep:
        """Record one step in the episode."""
        step = EpisodeStep(
            step_id=str(uuid4()),
            step_index=self._step_index,
            timestamp=timestamp,
            observation=dict(observation),
            action=dict(action),
            outcome=dict(outcome),
            evidence_class=self.evidence_class,
            provenance=provenance or {"source": self.source},
        )
        self._steps.append(step)
        self._step_index += 1
        return step

    def record_runtime_step(self, brain: Any, *, cycle: int) -> EpisodeStep:
        """Record a step from a MacBrain runtime step result.

        Extracts observation (detections, world state), action (governance,
        body), and outcome (reflection, loop verify) from the brain's last step.
        """
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        # Observation: detections + unified world state.
        detections = [e for e in brain.events if e["event_type"] == "perception.completed"]
        det_data = detections[-1].get("payload", {}) if detections else {}
        world_snap = brain.unified_world.to_dict() if brain.unified_world.entities else {}

        # Action: governance + body.
        action_events = [e for e in brain.events if e["event_type"] == "action.completed"]
        action_data = action_events[-1].get("payload", {}) if action_events else {}
        gov_events = [e for e in brain.events if e["event_type"] == "governance.evaluated"]
        gov_data = gov_events[-1].get("payload", {}) if gov_events else {}

        # Outcome: loop verify + reflection.
        loop_events = [e for e in brain.events if e["event_type"] == "loop.verify"]
        loop_data = loop_events[-1].get("payload", {}) if loop_events else {}
        refl_events = [e for e in brain.events if e["event_type"] == "reasoning.reflection"]
        refl_data = refl_events[-1].get("payload", {}) if refl_events else {}

        return self.record_step(
            observation={
                "cycle": cycle,
                "detection_count": det_data.get("detection_count", 0),
                "world_entities": len(world_snap.get("entities", {})) if world_snap else 0,
                "world_version": world_snap.get("world_version", 0) if world_snap else 0,
            },
            action={
                "action": action_data.get("action", "unknown"),
                "authorized": action_data.get("authorized", False),
                "governance_decision": gov_data.get("decision", ""),
                "risk_class": gov_data.get("risk_class", ""),
            },
            outcome={
                "loop_phase": loop_data.get("phase", ""),
                "loop_outcome": loop_data.get("outcome", ""),
                "reflection_effective": refl_data.get("effective", False),
            },
            timestamp=now,
            provenance={"source": self.source, "cycle": cycle},
        )

    def build_episode(self) -> NoviEpisode:
        """Assemble the recorded steps into a NoviEpisode."""
        return NoviEpisode(
            episode_id=f"episode-{uuid4().hex[:12]}",
            task_name=self.task_name,
            description=self.description,
            steps=tuple(self._steps),
            evidence_class=self.evidence_class,
            provenance={"source": self.source, "step_count": len(self._steps)},
            platform=self.platform,
            metadata={"task_type": self.task_name},
        )

    @property
    def step_count(self) -> int:
        return len(self._steps)

    def reset(self) -> None:
        """Clear recorded steps for a new episode."""
        self._steps.clear()
        self._step_index = 0
