"""Skill Contract module for the Mac Brain (PERFECTING_PLAN Step 3).

Defines formal skill contracts (Navigate/Inspect/FindObject/Pick/Speak) with
preconditions, success/failure criteria, timeout, recovery, and safety
constraints. Deterministic/mock implementations first (NVIDIA Experiment 2).

Canonical authority:
  - docs/02-autonomy/06_ACTION_EXECUTION_AND_FEEDBACK.md
  - docs/02-autonomy/09_AUTONOMY_SAFETY_BOUNDARIES.md
  - PERFECTING_PLAN/09_GAP_ANALYSIS_NVIDIA_INTEGRATION.md

The skill contract proves that a skill can be invoked independent of its
implementation — the same contract runs with a deterministic mock or a real
NVIDIA/Isaac backend behind an adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

# ---------------------------------------------------------------------------
# Risk classes (docs/02-autonomy/09 §Risk Classes)
# ---------------------------------------------------------------------------

R0 = "R0"  # informational/internal
R1 = "R1"  # reversible digital action
R2 = "R2"  # low-risk environmental/IoT action
R3 = "R3"  # physical movement or consequential external action
R4 = "R4"  # high-risk physical/security/privacy action
R5 = "R5"  # prohibited without dedicated external safety authority

ALL_RISK_CLASSES = frozenset({R0, R1, R2, R3, R4, R5})

# ---------------------------------------------------------------------------
# Skill outcome states
# ---------------------------------------------------------------------------

SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
TIMEOUT = "TIMEOUT"
CANCELLED = "CANCELLED"
SAFETY_STOP = "SAFETY_STOP"
PENDING = "PENDING"
RUNNING = "RUNNING"

ALL_OUTCOME_STATES = frozenset({SUCCESS, FAILURE, TIMEOUT, CANCELLED, SAFETY_STOP, PENDING, RUNNING})


# ---------------------------------------------------------------------------
# SkillContract — the formal contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SkillContract:
    """A formal skill contract with preconditions, success/failure criteria,
    timeout, recovery, and safety constraints.

    A skill is invoked independent of its implementation — the same contract
    runs with a deterministic mock or a real backend.
    """
    skill_id: str
    skill_name: str
    description: str
    risk_class: str
    # Preconditions: what must be true before the skill can execute.
    preconditions: tuple[str, ...]
    # Success criteria: what must be observed for the skill to be successful.
    success_criteria: tuple[str, ...]
    # Failure criteria: what must be observed for the skill to have failed.
    failure_criteria: tuple[str, ...]
    # Timeout in seconds.
    timeout_seconds: float
    # Recovery actions: what to do if the skill fails.
    recovery_actions: tuple[str, ...]
    # Safety constraints: immutable limits that cannot be exceeded.
    safety_constraints: tuple[str, ...]
    # Parameter schema: what parameters the skill accepts.
    parameter_schema: dict[str, str]  # param_name -> type_description

    def snapshot(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "description": self.description,
            "risk_class": self.risk_class,
            "preconditions": list(self.preconditions),
            "success_criteria": list(self.success_criteria),
            "failure_criteria": list(self.failure_criteria),
            "timeout_seconds": self.timeout_seconds,
            "recovery_actions": list(self.recovery_actions),
            "safety_constraints": list(self.safety_constraints),
            "parameter_schema": dict(self.parameter_schema),
        }


# ---------------------------------------------------------------------------
# SkillInvocation — one execution of a skill
# ---------------------------------------------------------------------------

@dataclass
class SkillInvocation:
    """One execution attempt of a skill contract."""
    invocation_id: str
    skill_id: str
    parameters: dict[str, Any]
    status: str = PENDING
    result: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""
    error: str = ""
    timeout_seconds: float = 0.0
    started_monotonic: float = 0.0  # time.monotonic() at start, for deadline checks
    deadline_monotonic: float = 0.0  # time.monotonic() deadline, or 0.0 when none

    def snapshot(self) -> dict[str, Any]:
        return {
            "invocation_id": self.invocation_id,
            "skill_id": self.skill_id,
            "parameters": dict(self.parameters),
            "status": self.status,
            "result": dict(self.result),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "timeout_seconds": self.timeout_seconds,
            "deadline_monotonic": self.deadline_monotonic,
        }

    @property
    def timed_out(self) -> bool:
        """True when the deadline has been reached/exceeded (timeout enforced)."""
        from time import monotonic
        return self.deadline_monotonic > 0.0 and monotonic() >= self.deadline_monotonic


# ---------------------------------------------------------------------------
# Canonical skill contracts
# ---------------------------------------------------------------------------

NAVIGATE_SKILL = SkillContract(
    skill_id="navigate",
    skill_name="Navigate",
    description="Navigate to a target location in the environment.",
    risk_class=R3,
    preconditions=("robot_localized", "target_location_known", "path_clear"),
    success_criteria=("robot_at_target", "arrival_confirmed"),
    failure_criteria=("timeout_exceeded", "obstacle_blocking", "localization_lost"),
    timeout_seconds=60.0,
    recovery_actions=("replan_path", "request_help", "return_to_safe_location"),
    safety_constraints=("max_speed_0.5m_s", "stop_on_obstacle", "no_collision"),
    parameter_schema={"target_location": "str", "speed": "float"},
)

INSPECT_SKILL = SkillContract(
    skill_id="inspect",
    skill_name="Inspect",
    description="Observe and classify an entity in the environment.",
    risk_class=R0,
    preconditions=("entity_visible", "camera_available"),
    success_criteria=("entity_classified", "classification_confident"),
    failure_criteria=("entity_not_visible", "classification_low_confidence", "timeout_exceeded"),
    timeout_seconds=10.0,
    recovery_actions=("reorient_camera", "approach_entity", "request_human_confirmation"),
    safety_constraints=(),
    parameter_schema={"entity_id": "str", "modality": "str"},
)

FIND_OBJECT_SKILL = SkillContract(
    skill_id="find_object",
    skill_name="FindObject",
    description="Search for and locate a specified object in the environment.",
    risk_class=R1,
    preconditions=("object_description_known", "search_area_defined"),
    success_criteria=("object_found", "object_location_known"),
    failure_criteria=("object_not_found", "timeout_exceeded", "search_area_exhausted"),
    timeout_seconds=120.0,
    recovery_actions=("expand_search_area", "request_user_clarification"),
    safety_constraints=(),
    parameter_schema={"object_description": "str", "search_area": "str"},
)

PICK_SKILL = SkillContract(
    skill_id="pick",
    skill_name="Pick",
    description="Pick up an object from its current location.",
    risk_class=R3,
    preconditions=("object_located", "gripper_available", "robot_near_object"),
    success_criteria=("object_grasped", "object_secured"),
    failure_criteria=("object_not_graspable", "gripper_fault", "timeout_exceeded"),
    timeout_seconds=30.0,
    recovery_actions=("reapproach_object", "adjust_grasp", "abort_pick"),
    safety_constraints=("max_object_weight_2kg", "no_dropping", "no_collision"),
    parameter_schema={"object_id": "str", "grasp_force": "float"},
)

SPEAK_SKILL = SkillContract(
    skill_id="speak",
    skill_name="Speak",
    description="Speak a message through the speakers.",
    risk_class=R1,
    preconditions=("message_composed", "speaker_available"),
    success_criteria=("audio_played", "playback_completed"),
    failure_criteria=("speaker_unavailable", "playback_failed", "timeout_exceeded"),
    timeout_seconds=15.0,
    recovery_actions=("retry_playback", "use_alternate_output"),
    safety_constraints=("no_loud_volume", "no_inappropriate_content"),
    parameter_schema={"text": "str", "volume": "float"},
)

ALL_SKILLS: dict[str, SkillContract] = {
    "navigate": NAVIGATE_SKILL,
    "inspect": INSPECT_SKILL,
    "find_object": FIND_OBJECT_SKILL,
    "pick": PICK_SKILL,
    "speak": SPEAK_SKILL,
}


# ---------------------------------------------------------------------------
# SkillExecutor — deterministic/mock implementations
# ---------------------------------------------------------------------------

class SkillExecutor:
    """Executes skill contracts with deterministic/mock implementations.

    The executor validates preconditions, runs the skill, checks success/failure
    criteria, and enforces the contract timeout deadline. The same contract runs
    with a mock or a real backend behind an adapter.

    Custom handlers can be registered per skill (e.g. slow/simulated backends)
    for testing deadline enforcement; when none is registered the deterministic
    mock is used.
    """

    def __init__(self) -> None:
        self._invocations: dict[str, SkillInvocation] = {}
        self._handlers: dict[str, Any] = {}  # skill_id -> handler(invocation, contract, context)

    def register_handler(self, skill_id: str, handler: Any) -> None:
        """Register a custom execution handler for a skill (test/backend seam)."""
        self._handlers[skill_id] = handler

    def get_contract(self, skill_id: str) -> SkillContract | None:
        return ALL_SKILLS.get(skill_id)

    def validate_preconditions(self, skill_id: str, context: dict[str, Any]) -> tuple[bool, list[str]]:
        """Check if all preconditions are met."""
        contract = self.get_contract(skill_id)
        if contract is None:
            return False, [f"unknown_skill:{skill_id}"]
        unmet: list[str] = []
        for precondition in contract.preconditions:
            if not context.get(precondition, False):
                unmet.append(precondition)
        return (len(unmet) == 0, unmet)

    def invoke(
        self,
        skill_id: str,
        parameters: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> SkillInvocation:
        """Invoke a skill contract.

        Returns a SkillInvocation with the outcome.
        """
        context = context or {}
        contract = self.get_contract(skill_id)
        invocation = SkillInvocation(
            invocation_id=str(uuid4()),
            skill_id=skill_id,
            parameters=dict(parameters),
        )

        if contract is None:
            invocation.status = FAILURE
            invocation.error = f"unknown_skill:{skill_id}"
            self._invocations[invocation.invocation_id] = invocation
            return invocation

        # Validate parameters.
        for param_name, _ in contract.parameter_schema.items():
            if param_name not in parameters:
                invocation.status = FAILURE
                invocation.error = f"missing_parameter:{param_name}"
                self._invocations[invocation.invocation_id] = invocation
                return invocation

        # Check preconditions.
        met, unmet = self.validate_preconditions(skill_id, context)
        if not met:
            invocation.status = FAILURE
            invocation.error = f"preconditions_not_met:{','.join(unmet)}"
            self._invocations[invocation.invocation_id] = invocation
            return invocation

        # Execute the deterministic/mock implementation with a deadline.
        from datetime import datetime, timezone
        from time import monotonic

        invocation.status = RUNNING
        invocation.started_at = datetime.now(timezone.utc).isoformat()
        invocation.timeout_seconds = contract.timeout_seconds
        invocation.started_monotonic = monotonic()
        invocation.deadline_monotonic = (
            invocation.started_monotonic + contract.timeout_seconds
            if contract.timeout_seconds > 0 else 0.0
        )
        self._invocations[invocation.invocation_id] = invocation
        self._execute_mock(invocation, contract, context)

        # Enforce the timeout: a skill that overruns its contract deadline is
        # reported as TIMEOUT instead of SUCCESS/FAILURE (gap-analysis Step 3,
        # item 20: SkillContract.timeout_seconds must be enforced).
        if contract.timeout_seconds > 0 and invocation.timed_out and invocation.status != TIMEOUT:
            invocation.status = TIMEOUT
            invocation.error = f"timeout_exceeded:{contract.timeout_seconds:.1f}s"
        invocation.completed_at = datetime.now(timezone.utc).isoformat()

        return invocation

    def _execute_mock(self, invocation: SkillInvocation, contract: SkillContract, context: dict[str, Any]) -> None:
        """Deterministic mock execution for each skill (or a registered handler)."""
        handler = self._handlers.get(invocation.skill_id)
        if handler is not None:
            handler(invocation, contract, context)
            return
        if invocation.skill_id == "navigate":
            target = invocation.parameters.get("target_location", "")
            if target and context.get("robot_localized"):
                invocation.status = SUCCESS
                invocation.result = {"destination": target, "distance_traveled": 2.5}
            else:
                invocation.status = FAILURE
                invocation.error = "navigation_failed"

        elif invocation.skill_id == "inspect":
            entity_id = invocation.parameters.get("entity_id", "")
            if entity_id and context.get("entity_visible"):
                invocation.status = SUCCESS
                invocation.result = {"entity_id": entity_id, "classification": "object", "confidence": 0.85}
            else:
                invocation.status = FAILURE
                invocation.error = "entity_not_visible"

        elif invocation.skill_id == "find_object":
            description = invocation.parameters.get("object_description", "")
            if description and context.get("search_area_defined"):
                invocation.status = SUCCESS
                invocation.result = {"object": description, "location": "table", "found": True}
            else:
                invocation.status = FAILURE
                invocation.error = "object_not_found"

        elif invocation.skill_id == "pick":
            object_id = invocation.parameters.get("object_id", "")
            if object_id and context.get("robot_near_object"):
                invocation.status = SUCCESS
                invocation.result = {"object_id": object_id, "grasped": True}
            else:
                invocation.status = FAILURE
                invocation.error = "object_not_graspable"

        elif invocation.skill_id == "speak":
            text = invocation.parameters.get("text", "")
            if text and context.get("speaker_available"):
                invocation.status = SUCCESS
                invocation.result = {"text": text, "played": True}
            else:
                invocation.status = FAILURE
                invocation.error = "speaker_unavailable"
        else:
            invocation.status = FAILURE
            invocation.error = f"no_mock_implementation:{invocation.skill_id}"

    def get_invocation(self, invocation_id: str) -> SkillInvocation | None:
        return self._invocations.get(invocation_id)

    @property
    def invocation_count(self) -> int:
        return len(self._invocations)
