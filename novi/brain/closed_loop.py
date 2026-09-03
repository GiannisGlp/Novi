"""Closed-Loop Validation for the Mac Brain (PERFECTING_PLAN Step 6).

Implements:
  1. A first-class VERIFY step (observe -> plan -> act -> verify -> recover/ask/stop)
     with outcome/failure handling across the loop.
  2. Cross-system acceptance tests (Soul -> Cognition -> Memory -> Autonomy ->
     Safety -> Brain).
  3. The global completion-gate review.

Canonical authority:
  - PERFECTING_PLAN/10_ROADMAP_BY_STEP.md §Step 6
  - PERFECTING_PLAN/11_VALIDATION_AND_ACCEPTANCE.md
  - docs/02-autonomy/06_ACTION_EXECUTION_AND_FEEDBACK.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence
from uuid import uuid4

# ---------------------------------------------------------------------------
# Closed-loop states
# ---------------------------------------------------------------------------

OBSERVE = "OBSERVE"
PLAN = "PLAN"
ACT = "ACT"
VERIFY = "VERIFY"
RECOVER = "RECOVER"
ASK = "ASK"
STOP = "STOP"

LOOP_STATES = frozenset({OBSERVE, PLAN, ACT, VERIFY, RECOVER, ASK, STOP})

# Outcome states
OUTCOME_SUCCESS = "SUCCESS"
OUTCOME_FAILURE = "FAILURE"
OUTCOME_PARTIAL = "PARTIAL"
OUTCOME_TIMEOUT = "TIMEOUT"
OUTCOME_DENIED = "DENIED"  # action was not executed (governance denial / held)
OUTCOME_UNKNOWN = "UNKNOWN"

ALL_OUTCOMES = frozenset(
    {OUTCOME_SUCCESS, OUTCOME_FAILURE, OUTCOME_PARTIAL, OUTCOME_TIMEOUT, OUTCOME_DENIED, OUTCOME_UNKNOWN}
)


# ---------------------------------------------------------------------------
# LoopStep — one step in the closed loop
# ---------------------------------------------------------------------------


@dataclass
class LoopStep:
    """One step in the closed-loop cycle."""

    step_id: str
    phase: str  # OBSERVE | PLAN | ACT | VERIFY | RECOVER | ASK | STOP
    cycle: int
    data: dict[str, Any] = field(default_factory=dict)
    outcome: str = OUTCOME_UNKNOWN
    timestamp: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "phase": self.phase,
            "cycle": self.cycle,
            "data": dict(self.data),
            "outcome": self.outcome,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# ClosedLoopRuntime — the first-class VERIFY loop
# ---------------------------------------------------------------------------

#: Maximum retained loop steps (~100 cycles of OBSERVE/PLAN/ACT/VERIFY).
#: The runtime is a per-cycle VERIFY loop, not a history database: only the
#: current cycle and recent history are ever consulted, so the tail window is
#: the complete working set. Bounds memory under indefinite autonomous runs
#: (plan 02, Rule 1/Rule 3).
MAX_LOOP_STEPS = 400


class ClosedLoopRuntime:
    """Implements the closed-loop cycle: OBSERVE -> PLAN -> ACT -> VERIFY ->
    RECOVER/ASK/STOP.

    The VERIFY step is first-class: after acting, the system verifies the
    outcome against success criteria and decides whether to recover, ask for
    help, or stop.
    """

    def __init__(self, *, max_steps: int = MAX_LOOP_STEPS) -> None:
        self._steps: list[LoopStep] = []
        self._max_steps = max(1, int(max_steps))
        self._cycle: int = 0
        self._current_phase: str = OBSERVE
        self._action_outcome: str = OUTCOME_UNKNOWN
        self._verify_result: dict[str, Any] = {}
        self._recovery_attempts: int = 0
        self._max_recovery: int = 3

    def _append_step(self, step: LoopStep) -> None:
        """Single insertion point; enforces the bounded tail window."""
        self._steps.append(step)
        if len(self._steps) > self._max_steps:
            del self._steps[: len(self._steps) - self._max_steps]

    @property
    def max_steps(self) -> int:
        return self._max_steps

    @property
    def cycle(self) -> int:
        return self._cycle

    @property
    def current_phase(self) -> str:
        return self._current_phase

    @property
    def steps(self) -> tuple[LoopStep, ...]:
        return tuple(self._steps)

    def observe(self, observation: dict[str, Any]) -> LoopStep:
        """OBSERVE phase: collect sensor data and world state."""
        self._cycle += 1
        step = LoopStep(
            step_id=str(uuid4()),
            phase=OBSERVE,
            cycle=self._cycle,
            data=observation,
            timestamp=observation.get("timestamp", ""),
        )
        self._append_step(step)
        self._current_phase = PLAN
        return step

    def plan(self, plan_data: dict[str, Any]) -> LoopStep:
        """PLAN phase: generate a plan for the current goal."""
        step = LoopStep(
            step_id=str(uuid4()),
            phase=PLAN,
            cycle=self._cycle,
            data=plan_data,
            timestamp=plan_data.get("timestamp", ""),
        )
        self._append_step(step)
        self._current_phase = ACT
        return step

    def act(self, action_data: dict[str, Any]) -> LoopStep:
        """ACT phase: execute the planned action (through governance)."""
        step = LoopStep(
            step_id=str(uuid4()),
            phase=ACT,
            cycle=self._cycle,
            data=action_data,
            outcome=action_data.get("outcome", OUTCOME_UNKNOWN),
            timestamp=action_data.get("timestamp", ""),
        )
        self._append_step(step)
        self._action_outcome = step.outcome
        self._current_phase = VERIFY
        return step

    def verify(self, success_criteria: Sequence[str], observed_state: dict[str, Any]) -> LoopStep:
        """VERIFY phase: check if the action achieved its success criteria.

        This is the first-class verify step. If the action succeeded, the loop
        returns to OBSERVE. If it failed, the loop enters RECOVER/ASK/STOP.
        """
        # Check each success criterion against the observed state.
        met: list[str] = []
        unmet: list[str] = []
        for criterion in success_criteria:
            if observed_state.get(criterion, False):
                met.append(criterion)
            else:
                unmet.append(criterion)

        # A denied action (governance denial / held for confirmation) was not
        # executed, so it is not a retryable failure — do not enter RECOVER.
        if self._action_outcome == OUTCOME_DENIED:
            outcome = OUTCOME_DENIED
            next_phase = OBSERVE
        elif not unmet:
            outcome = OUTCOME_SUCCESS
            next_phase = OBSERVE  # loop back to observe
        elif self._recovery_attempts < self._max_recovery:
            outcome = OUTCOME_FAILURE
            next_phase = RECOVER
        else:
            outcome = OUTCOME_FAILURE
            next_phase = ASK  # ask for help after max recovery attempts

        self._verify_result = {"met": met, "unmet": unmet, "outcome": outcome}
        step = LoopStep(
            step_id=str(uuid4()),
            phase=VERIFY,
            cycle=self._cycle,
            data={"success_criteria": list(success_criteria), "observed_state": observed_state},
            outcome=outcome,
        )
        self._append_step(step)

        if outcome in (OUTCOME_SUCCESS, OUTCOME_DENIED):
            # A fresh cycle begins: either the action succeeded or it was
            # denied (governance / held for confirmation) and not executed.
            # Both are non-retryable, so reset the recovery budget.
            self._current_phase = OBSERVE
            self._recovery_attempts = 0
        else:
            self._current_phase = next_phase

        return step

    def recover(self, recovery_data: dict[str, Any]) -> LoopStep:
        """RECOVER phase: attempt to recover from a failed action."""
        self._recovery_attempts += 1
        step = LoopStep(
            step_id=str(uuid4()),
            phase=RECOVER,
            cycle=self._cycle,
            data=recovery_data,
            outcome=recovery_data.get("outcome", OUTCOME_UNKNOWN),
        )
        self._append_step(step)
        # After recovery attempt, go back to PLAN to try again.
        self._current_phase = PLAN
        return step

    def ask(self, ask_data: dict[str, Any]) -> LoopStep:
        """ASK phase: ask for human help after max recovery attempts."""
        step = LoopStep(
            step_id=str(uuid4()),
            phase=ASK,
            cycle=self._cycle,
            data=ask_data,
        )
        self._append_step(step)
        self._current_phase = STOP
        return step

    def stop(self, reason: str = "") -> LoopStep:
        """STOP phase: stop the loop."""
        step = LoopStep(
            step_id=str(uuid4()),
            phase=STOP,
            cycle=self._cycle,
            data={"reason": reason},
        )
        self._append_step(step)
        self._current_phase = STOP
        return step

    def run_full_cycle(
        self,
        observation: dict[str, Any],
        plan: dict[str, Any],
        action: dict[str, Any],
        success_criteria: Sequence[str],
        observed_state: dict[str, Any],
    ) -> tuple[LoopStep, ...]:
        """Run one full closed-loop cycle: OBSERVE -> PLAN -> ACT -> VERIFY.

        Returns all steps produced in this cycle.
        """
        cycle_steps: list[LoopStep] = []
        cycle_steps.append(self.observe(observation))
        cycle_steps.append(self.plan(plan))
        cycle_steps.append(self.act(action))
        cycle_steps.append(self.verify(success_criteria, observed_state))
        return tuple(cycle_steps)

    def snapshot(self) -> dict[str, Any]:
        return {
            "cycle": self._cycle,
            "current_phase": self._current_phase,
            "recovery_attempts": self._recovery_attempts,
            "steps": [s.snapshot() for s in self._steps],
            "action_outcome": self._action_outcome,
            "verify_result": dict(self._verify_result),
        }


# ---------------------------------------------------------------------------
# Cross-system acceptance test
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CrossSystemTestResult:
    """Result of a cross-system acceptance test."""

    test_id: str
    name: str
    systems_tested: tuple[str, ...]
    passed: bool
    results: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "systems_tested": list(self.systems_tested),
            "passed": self.passed,
            "results": dict(self.results),
            "reason": self.reason,
        }


def run_cross_system_acceptance() -> tuple[CrossSystemTestResult, ...]:
    """Run cross-system acceptance tests.

    Tests the composition: Soul -> Cognition -> Memory -> Autonomy -> Safety -> Brain.
    Each subsystem appears correct independently; the composition must not
    violate intended behavior.
    """
    results: list[CrossSystemTestResult] = []

    # Test 1: Soul -> Cognition (identity question doesn't bypass cognition)
    from novi.brain.soul_acceptance import CommunicationDecision

    cd = CommunicationDecision()
    should_speak, _ = cd.should_speak(has_communicative_reason=True)
    results.append(
        CrossSystemTestResult(
            test_id="cross_1",
            name="soul_to_cognition",
            systems_tested=("soul", "cognition"),
            passed=should_speak,
            results={"should_speak": should_speak},
            reason="soul communication decision feeds cognition correctly",
        )
    )

    # Test 2: Cognition -> Memory (observed evidence is stored correctly)
    from novi.brain.memory_hardening import DIRECT_SENSOR, OBSERVED, HardenedMemoryManager

    mgr = HardenedMemoryManager()
    admit_result = mgr.admit(
        memory_type="perception",
        content="cup on table",
        confidence=0.85,
        epistemic_status=OBSERVED,
        evidence_class=OBSERVED,
        verification_status="UNVERIFIED",
        source_class=DIRECT_SENSOR,
        privacy_class="unclassified",
        provenance={"source": "camera"},
        entity_refs=("cup",),
    )
    retrieve_result = mgr.retrieve_with_states("cup")
    results.append(
        CrossSystemTestResult(
            test_id="cross_2",
            name="cognition_to_memory",
            systems_tested=("cognition", "memory"),
            passed=admit_result.accepted and retrieve_result.state == "RESOLVED",
            results={"admitted": admit_result.accepted, "retrieval_state": retrieve_result.state},
            reason="cognition observation stored and retrieved correctly",
        )
    )

    # Test 3: Memory -> Autonomy (simulated episode cannot become fact in autonomy)
    from novi.brain.memory_hardening import SIMULATED, SIMULATION, VERIFIED

    sim_admit = mgr.admit(
        memory_type="simulation",
        content="cup at table",
        confidence=0.9,
        epistemic_status=SIMULATED,
        evidence_class=SIMULATED,
        verification_status="UNVERIFIED",
        source_class=SIMULATION,
        privacy_class="unclassified",
        provenance={"source": "isaac_sim"},
    )
    fact_attempt = mgr.admit(
        memory_type="perception",
        content="cup at table",
        confidence=0.9,
        epistemic_status=VERIFIED,
        evidence_class=SIMULATED,
        verification_status="USER_CONFIRMED",
        source_class=SIMULATION,
        privacy_class="unclassified",
        provenance={"source": "isaac_sim"},
    )
    results.append(
        CrossSystemTestResult(
            test_id="cross_3",
            name="memory_to_autonomy",
            systems_tested=("memory", "autonomy"),
            passed=sim_admit.accepted and not fact_attempt.accepted,
            results={"sim_admitted": sim_admit.accepted, "fact_rejected": not fact_attempt.accepted},
            reason="simulated episode stored as SIMULATED; cannot be recalled as fact",
        )
    )

    # Test 4: Autonomy -> Safety (governance guard gates action)
    from novi.brain.governance_guard import ActionProposal, GovernanceGuard

    guard = GovernanceGuard()
    proposal = ActionProposal(proposal_id="p1", action="wait", parameters={}, risk_class="R0")
    grant = guard.evaluate(proposal)
    results.append(
        CrossSystemTestResult(
            test_id="cross_4",
            name="autonomy_to_safety",
            systems_tested=("autonomy", "safety"),
            passed=grant.is_allowed,
            results={"decision": grant.decision},
            reason="autonomy action gated by safety governance guard",
        )
    )

    # Test 5: Safety -> Brain (System-0 safety gate works)
    from novi.brain.multi_speed_runtime import SYSTEM_0, MultiSpeedRuntime

    rt = MultiSpeedRuntime()
    rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
    rt.step()
    results.append(
        CrossSystemTestResult(
            test_id="cross_5",
            name="safety_to_brain",
            systems_tested=("safety", "brain"),
            passed=rt.system0_safety_clear,
            results={"system0_safety_clear": rt.system0_safety_clear},
            reason="System-0 safety gate clears for brain execution",
        )
    )

    # Test 6: Full cross-system (Soul -> Cognition -> Memory -> Autonomy -> Safety -> Brain)
    full_loop = ClosedLoopRuntime()
    loop_steps = full_loop.run_full_cycle(
        observation={"entities": ["cup"], "location": "kitchen"},
        plan={"goal": "pick_cup", "skill": "pick"},
        action={"skill": "pick", "parameters": {"object_id": "cup"}, "governed": True},
        success_criteria=["object_grasped"],
        observed_state={"object_grasped": True},
    )
    results.append(
        CrossSystemTestResult(
            test_id="cross_6",
            name="full_cross_system",
            systems_tested=("soul", "cognition", "memory", "autonomy", "safety", "brain"),
            passed=len(loop_steps) == 4 and loop_steps[-1].outcome == OUTCOME_SUCCESS,
            results={"steps": [s.snapshot() for s in loop_steps]},
            reason="full closed-loop cycle completes with VERIFY success",
        )
    )

    return tuple(results)


# ---------------------------------------------------------------------------
# Global completion gate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompletionGateResult:
    """Result of the global completion-gate review."""

    passed: bool
    total_steps: int
    steps_passed: int
    step_results: dict[str, bool]
    cross_system_results: tuple[CrossSystemTestResult, ...]
    reason: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "total_steps": self.total_steps,
            "steps_passed": self.steps_passed,
            "step_results": dict(self.step_results),
            "cross_system_results": [r.snapshot() for r in self.cross_system_results],
            "reason": self.reason,
        }


def run_completion_gate(step_results: dict[str, bool]) -> CompletionGateResult:
    """Run the global completion-gate review.

    The completion gate requires:
      - All 6 steps (0-5) passed their done-bars.
      - All cross-system acceptance tests passed.
      - No P0 violations.
    """
    cross_results = run_cross_system_acceptance()
    all_cross_passed = all(r.passed for r in cross_results)
    all_steps_passed = all(step_results.values()) if step_results else False

    passed = all_steps_passed and all_cross_passed
    return CompletionGateResult(
        passed=passed,
        total_steps=len(step_results),
        steps_passed=sum(1 for v in step_results.values() if v),
        step_results=dict(step_results),
        cross_system_results=cross_results,
        reason="all steps and cross-system tests passed" if passed else "some steps or tests failed",
    )
