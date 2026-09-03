"""Tests for the deterministic AutonomySupervisor (06_AUTONOMY doc 01).

Covers: legal/illegal state transitions, one-action-per-tick, interruption at
every stage, cancellation idempotency, lease/timeout boundedness, health-driven
authority degradation, emergency stop, human approval, and the A-ARCH-01 gate
(10,000 simulated ticks with injected faults never execute an unauthorized
action and always reach a terminal or recoverable state).
"""

from __future__ import annotations

import random
import unittest
from dataclasses import dataclass
from typing import Any

from novi.brain.autonomy_supervisor import (
    ActionResult,
    AuthorizedAction,
    AutonomyHealth,
    AutonomyState,
    AutonomySupervisor,
    SimClock,
    VerificationResult,
)
from novi.brain.governance_guard import ActionProposal, GovernanceGuard
from novi.brain.planner import Planner

# ---------------------------------------------------------------------------
# Deterministic fakes
# ---------------------------------------------------------------------------


@dataclass
class FakeGoal:
    goal_id: str
    kind: str = "reach"
    target: tuple[float, float] = (10.0, 0.0)


class FakeGoalSource:
    def __init__(self, goals: list[FakeGoal] | None = None) -> None:
        self.goals = list(goals or [])
        self.completed: dict[str, str] = {}
        self._index = 0

    def active_goal(self, *, cycle: int) -> FakeGoal | None:
        while self._index < len(self.goals):
            goal = self.goals[self._index]
            if goal.goal_id not in self.completed:
                return goal
            self._index += 1
        return None

    def complete_goal(self, goal_id: str, status: str, *, cycle: int) -> None:
        self.completed[goal_id] = status


class FakeWorld:
    def __init__(self, *, needs_info: bool = False, refresh_raises: bool = False) -> None:
        self.needs_info = needs_info
        self.refresh_raises = refresh_raises
        self.refreshes = 0
        self.expiries = 0

    def refresh(self, *, cycle: int) -> dict:
        self.refreshes += 1
        if self.refresh_raises:
            raise RuntimeError("sensor_failure")
        return {}

    def expire_stale(self, *, cycle: int) -> list[str]:
        self.expiries += 1
        return []

    def needs_information(self, goal: FakeGoal, *, cycle: int) -> bool:
        return self.needs_info


class FakeExecutor:
    def __init__(self, outcomes: dict[str, str] | None = None, *, raises: bool = False) -> None:
        # outcome per action name: SUCCESS | PARTIAL | FAILED | TIMEOUT
        self.outcomes = dict(outcomes or {})
        self.raises = raises
        self.executions: list[tuple[str, str, int]] = []  # (authorization_id, action, cycle)

    def execute(self, action: AuthorizedAction, *, cycle: int) -> ActionResult:
        self.executions.append((action.authorization_id, action.action, cycle))
        if self.raises:
            raise RuntimeError("executor_crash")
        outcome = self.outcomes.get(action.action, "SUCCESS")
        return ActionResult(
            result_id=f"res-{len(self.executions)}", action_ref=action.authorization_id,
            outcome=outcome, cycle=cycle,
            error="" if outcome == "SUCCESS" else f"{outcome}_injected",
        )


class FakeVerifier:
    def __init__(self, *, passes: bool = True) -> None:
        self.passes = passes
        self.verifications: list[str] = []

    def verify(self, action: AuthorizedAction, result: ActionResult, *, cycle: int) -> VerificationResult:
        self.verifications.append(action.action)
        return VerificationResult(
            verification_id=f"ver-{len(self.verifications)}", target_ref=action.authorization_id,
            method="deterministic_fake",
            status="PASS" if self.passes else "FAIL",
            observed_evidence={"injected": True} if self.passes else {},
            error="" if self.passes else "postcondition_not_met",
        )


class FakeProposer:
    def propose(self, step: Any, *, goal_id: str, plan_id: str, cycle: int) -> ActionProposal:
        return ActionProposal(
            proposal_id=f"prop-{cycle}-{step.action}",
            action=step.action,
            parameters=dict(step.params),
            risk_class="R1",
            source="deterministic",
            rationale=f"plan step {step.kind}",
        )


class FlakyPlanner(Planner):
    """Planner that raises on the first N plan() calls (fault injection)."""

    def __init__(self, failures: int = 1) -> None:
        super().__init__()
        self.failures_left = failures
        self.attempts = 0

    def plan(self, goal: FakeGoal, *, cycle: int = 0):
        self.attempts += 1
        if self.failures_left > 0:
            self.failures_left -= 1
            raise RuntimeError("planner_busy")
        return super().plan(goal, cycle=cycle)


def make_supervisor(
    *,
    goals: list[FakeGoal] | None = None,
    goals_source: FakeGoalSource | None = None,
    executor: FakeExecutor | None = None,
    verifier: FakeVerifier | None = None,
    world: FakeWorld | None = None,
    guard: GovernanceGuard | None = None,
    planner: Planner | None = None,
    proposer: FakeProposer | None = None,
    health: object | None = None,
    authority: str = "BOUNDED_AUTONOMY",
    max_action_retries: int = 2,
    max_events: int = 2048,
) -> AutonomySupervisor:
    return AutonomySupervisor(
        clock=SimClock(),
        executor=executor or FakeExecutor(),
        verifier=verifier or FakeVerifier(),
        world=world or FakeWorld(),
        goals=goals_source or FakeGoalSource(goals or [FakeGoal("g1")]),
        planner=planner or Planner(),
        proposer=proposer or FakeProposer(),
        guard=guard or GovernanceGuard(),
        authority_level=authority,
        max_action_retries=max_action_retries,
        max_events=max_events,
        health_checker=health,
    )


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class StateTransitionTests(unittest.TestCase):
    def test_legal_transition_is_recorded_as_event(self):
        sup = make_supervisor()
        ok = sup._transition(AutonomyState.OBSERVING, reason="test", producer="test")
        self.assertTrue(ok)
        self.assertEqual(sup.state, AutonomyState.OBSERVING)
        self.assertTrue(any(e.event_type == "STATE_CHANGED" for e in sup.events))

    def test_illegal_transition_is_rejected(self):
        sup = make_supervisor()
        # IDLE -> EXECUTING is not a legal transition.
        ok = sup._transition(AutonomyState.EXECUTING, reason="test", producer="test")
        self.assertFalse(ok)
        self.assertEqual(sup.state, AutonomyState.IDLE)
        self.assertTrue(any(e.event_type == "TRANSITION_REJECTED" for e in sup.events))

    def test_every_transition_event_has_reason_and_producer(self):
        sup = make_supervisor()
        for _ in range(8):
            sup.tick()
        for event in sup.events:
            self.assertTrue(event.reason, "event must carry a reason")
            self.assertTrue(event.producer, "event must carry its originating component")
            self.assertIsInstance(event.cycle, int)


class EpisodeTests(unittest.TestCase):
    def test_happy_path_reaches_completed(self):
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(goals_source=gs)
        for _ in range(10):
            sup.tick()
        self.assertTrue(sup.finished)
        self.assertGreaterEqual(sup.executed_count, 1)
        # Goal recorded as completed.
        self.assertEqual(gs.completed.get("g1"), "completed")

    def test_one_action_per_tick(self):
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(goals_source=gs)
        before = sup.executed_count
        sup.tick()
        after = sup.executed_count
        self.assertLessEqual(after - before, 1, "one tick must execute at most one action")

    def test_information_need_pauses_planning(self):
        world = FakeWorld(needs_info=True)
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(world=world, goals_source=gs)
        sup.tick()
        self.assertEqual(sup.state, AutonomyState.OBSERVING)
        self.assertTrue(any(e.event_type == "PERCEPTION_NEEDED" for e in sup.events))
        # Information arrives: the loop proceeds.
        world.needs_info = False
        for _ in range(10):
            sup.tick()
        self.assertEqual(gs.completed.get("g1"), "completed")

    def test_interruption_during_observation(self):
        world = FakeWorld(needs_info=True)
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(world=world, goals_source=gs)
        sup.tick()
        self.assertEqual(sup.state, AutonomyState.OBSERVING)
        sup.cancel(reason="user_redirect")
        for _ in range(3):
            sup.tick()
        self.assertEqual(gs.completed.get("g1"), "cancelled")
        self.assertFalse(sup.finished)

    def test_interruption_during_execution(self):
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(goals_source=gs)
        sup.tick()  # plan selected
        sup.tick()  # first action executed
        self.assertGreaterEqual(sup.executed_count, 1)
        sup.cancel(reason="stop_now")
        for _ in range(3):
            sup.tick()
        self.assertEqual(gs.completed.get("g1"), "cancelled")

    def test_cancellation_is_idempotent(self):
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(goals_source=gs)
        sup.cancel(reason="first")
        sup.cancel(reason="second")
        cancelled = [e for e in sup.events if e.event_type == "CANCELLED"]
        self.assertEqual(len(cancelled), 1, "second cancel must be a no-op")

    def test_cancelled_action_never_resumes(self):
        """Doc 01 Step 7: a cancelled action cannot later resume accidentally."""
        gs = FakeGoalSource([FakeGoal("g1")])
        executor = FakeExecutor()
        sup = make_supervisor(executor=executor, goals_source=gs)
        for _ in range(2):
            sup.tick()
        sup.cancel()
        ids = [e[0] for e in executor.executions]
        # After the cancel, no new execution may occur for the cancelled goal.
        for _ in range(3):
            sup.tick()
        self.assertEqual([e[0] for e in executor.executions], ids)


class LeaseAndRecoveryTests(unittest.TestCase):
    def test_retry_budget_exhausted_fails_goal(self):
        executor = FakeExecutor(outcomes={"observe": "TIMEOUT"})
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(executor=executor, goals_source=gs, max_action_retries=2)
        for _ in range(30):
            sup.tick()
        # 1 attempt + 2 retries = 3 executions max; goal then failed.
        self.assertLessEqual(sup.executed_count, 3)
        self.assertEqual(gs.completed.get("g1"), "failed")
        self.assertIn(sup.state, {AutonomyState.RECOVERING, AutonomyState.IDLE, AutonomyState.FAILED})
        retries = [e for e in sup.events if e.event_type == "ACTION_RETRY"]
        self.assertLessEqual(len(retries), 2, "retries must respect the budget")

    def test_executor_crash_fails_goal_within_budget(self):
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(executor=FakeExecutor(raises=True), goals_source=gs)
        for _ in range(30):
            sup.tick()
        self.assertEqual(gs.completed.get("g1"), "failed")
        self.assertLessEqual(sup.executed_count, 3)

    def test_verification_failure_fails_goal(self):
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(verifier=FakeVerifier(passes=False), goals_source=gs)
        for _ in range(20):
            sup.tick()
        self.assertEqual(gs.completed.get("g1"), "failed")

    def test_persistent_planner_failure_fails_goal_after_three_attempts(self):
        planner = FlakyPlanner(failures=100)  # permanently failing
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(planner=planner, goals_source=gs)
        for _ in range(20):
            sup.tick()
        self.assertEqual(gs.completed.get("g1"), "failed")
        self.assertLessEqual(planner.attempts, 3, "planner must not be called forever")

    def test_transient_planner_failure_recovers(self):
        planner = FlakyPlanner(failures=1)
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(planner=planner, goals_source=gs)
        for _ in range(15):
            sup.tick()
        self.assertEqual(gs.completed.get("g1"), "completed", "transient planner failure must recover")


class HealthAndAuthorityTests(unittest.TestCase):
    def test_degraded_health_reduces_authority(self):
        def health(cycle):
            return AutonomyHealth(health_id=f"h{cycle}", cycle=cycle, overall_status="DEGRADED",
                                  components={"perception": "degraded"})

        sup = make_supervisor(health=health, authority="BOUNDED_AUTONOMY", goals=[FakeGoal("g1")])
        sup.tick()
        self.assertEqual(sup.authority, "ASSISTED")
        self.assertTrue(any(e.event_type == "AUTHORITY_REDUCED" for e in sup.events))

    def test_unavailable_health_safe_stops(self):
        def health(cycle):
            return AutonomyHealth(health_id=f"h{cycle}", cycle=cycle, overall_status="UNAVAILABLE",
                                  components={"safety_monitor": "unavailable"})

        sup = make_supervisor(health=health, goals=[FakeGoal("g1")])
        sup.tick()
        self.assertEqual(sup.state, AutonomyState.SAFE_STOP)
        self.assertEqual(sup.authority, "PASSIVE")
        self.assertTrue(sup.finished)

    def test_emergency_stop_requires_explicit_reset(self):
        gs = FakeGoalSource([FakeGoal("g1"), FakeGoal("g2")])
        sup = make_supervisor(goals_source=gs)
        for _ in range(2):
            sup.tick()
        sup.emergency_stop(reason="test_estop")
        self.assertEqual(sup.state, AutonomyState.SAFE_STOP)
        # E-stop cancels the active goal (never auto-resume the same plan).
        self.assertEqual(gs.completed.get("g1"), "cancelled")
        # No auto-resume: the loop is blocked even though g2 is available.
        for _ in range(3):
            sup.tick()
        self.assertEqual(sup.state, AutonomyState.SAFE_STOP)
        self.assertNotIn("g2", gs.completed)
        # Explicit recovery conditions:
        sup.reset()
        self.assertEqual(sup.state, AutonomyState.IDLE)
        for _ in range(10):
            sup.tick()
        self.assertEqual(gs.completed.get("g2"), "completed")


class ApprovalTests(unittest.TestCase):
    def test_requires_confirmation_waits_for_operator(self):
        # R3 movement action requires confirmation.
        class HighRiskProposer(FakeProposer):
            def propose(self, step, *, goal_id, plan_id, cycle):
                proposal = super().propose(step, goal_id=goal_id, plan_id=plan_id, cycle=cycle)
                return ActionProposal(
                    proposal_id=proposal.proposal_id, action=proposal.action,
                    parameters=proposal.parameters, risk_class="R3",
                    source="model", rationale=proposal.rationale,
                )

        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(proposer=HighRiskProposer(), goals_source=gs)
        sup.tick()  # goal + plan
        sup.tick()  # proposal -> AWAITING_AUTHORITY
        self.assertEqual(sup.state, AutonomyState.AWAITING_AUTHORITY)
        self.assertTrue(any(e.event_type == "AWAITING_APPROVAL" for e in sup.events))
        executed_before = sup.executed_count

        # No approval, no execution.
        for _ in range(3):
            sup.tick()
        self.assertEqual(sup.executed_count, executed_before)

        # Approval is explicit, scoped and per-action: every R3 step needs its
        # own operator approval (doc 08 Step 7).
        approvals = 0
        for _ in range(40):
            if sup.state is AutonomyState.AWAITING_AUTHORITY and sup.approve():
                approvals += 1
            sup.tick()
            if sup.finished:
                break
        self.assertGreater(approvals, 0)
        self.assertGreater(sup.executed_count, executed_before)
        self.assertEqual(gs.completed.get("g1"), "completed")

    def test_approve_outside_pending_state_fails(self):
        gs = FakeGoalSource([FakeGoal("g1")])
        sup = make_supervisor(goals_source=gs)
        self.assertFalse(sup.approve())


class UnauthorizedActionPropertyTests(unittest.TestCase):
    def test_denying_guard_never_executes(self):
        """Property: no path can execute an action without authorization."""
        class DenyGuard(GovernanceGuard):
            def evaluate(self, proposal):
                from novi.brain.governance_guard import GovernanceGrant
                return GovernanceGrant(
                    grant_id=f"deny-{proposal.proposal_id}", proposal_id=proposal.proposal_id,
                    decision="DENY", reason="always_deny",
                )

        gs = FakeGoalSource([FakeGoal(f"g{i}") for i in range(5)])
        sup = make_supervisor(guard=DenyGuard(), goals_source=gs)
        for _ in range(50):
            sup.tick()
        self.assertEqual(sup.executed_count, 0, "no action may execute without a grant")
        self.assertGreater(sup.unauthorized_attempts, 0)
        self.assertEqual(set(gs.completed.values()), {"failed"})

    def test_a_arch_01_ten_thousand_fault_injected_ticks(self):
        """Gate A-ARCH-01: 10,000 simulated ticks with injected timeouts, stale
        sensors, cancellations and planner failures never execute an unauthorized
        action and always reach a terminal or recoverable state."""
        rng = random.Random(0xA1C41)
        goals = [FakeGoal(f"goal-{i}", kind="reach" if i % 2 == 0 else "investigate")
                 for i in range(400)]

        class FaultWorld(FakeWorld):
            def __init__(self):
                super().__init__()
                self.raise_count = 0

            def refresh(self, *, cycle):
                self.refreshes += 1
                if rng.random() < 0.01:
                    self.raise_count += 1
                    raise RuntimeError("injected_sensor_failure")
                return {}

            def needs_information(self, goal, *, cycle):
                return rng.random() < 0.10

        class FaultExecutor(FakeExecutor):
            def execute(self, action, *, cycle):
                if rng.random() < 0.04:
                    outcome = "TIMEOUT"
                elif rng.random() < 0.03:
                    outcome = "FAILED"
                else:
                    outcome = "SUCCESS"
                self.executions.append((action.authorization_id, action.action, cycle))
                return ActionResult(
                    result_id=f"res-{len(self.executions)}", action_ref=action.authorization_id,
                    outcome=outcome, cycle=cycle, error="" if outcome == "SUCCESS" else f"{outcome}_injected",
                )

        class FaultVerifier(FakeVerifier):
            def verify(self, action, result, *, cycle):
                passes = not (result.outcome == "SUCCESS" and rng.random() < 0.02)
                return VerificationResult(
                    verification_id=f"ver-{len(self.verifications)}", target_ref=action.authorization_id,
                    method="fault_injected", status="PASS" if passes else "FAIL",
                    observed_evidence={"ok": passes}, error="" if passes else "postcondition_miss",
                )

        class FaultPlanner(Planner):
            def plan(self, goal, *, cycle=0):
                if rng.random() < 0.02:
                    raise RuntimeError("injected_planner_failure")
                return super().plan(goal, cycle=cycle)

        def health(cycle):
            roll = rng.random()
            if roll < 0.005:
                return AutonomyHealth(f"h{cycle}", cycle, "UNAVAILABLE", {"safety_monitor": "unavailable"})
            if roll < 0.05:
                return AutonomyHealth(f"h{cycle}", cycle, "DEGRADED", {"perception": "degraded"})
            return AutonomyHealth(f"h{cycle}", cycle, "HEALTHY", {"safety_monitor": "healthy"})

        world = FaultWorld()
        executor = FaultExecutor()
        verifier = FaultVerifier()
        goals_source = FakeGoalSource(goals)
        sup = AutonomySupervisor(
            clock=SimClock(), executor=executor, verifier=verifier, world=world,
            goals=goals_source, planner=FaultPlanner(), proposer=FakeProposer(),
            guard=GovernanceGuard(), authority_level="SUPERVISED_AUTONOMY",
            max_action_retries=2, health_checker=health,
        )

        for _ in range(10_000):
            sup.tick()
            health_now = sup.health()
            if sup.state is AutonomyState.SAFE_STOP and health_now is not None \
                    and health_now.overall_status == "UNAVAILABLE":
                # Explicit recovery conditions satisfied: operator clears the stop.
                sup.reset()

        # 1. Zero unauthorized executions.
        self.assertEqual(sup.unauthorized_attempts, 0)
        self.assertEqual(len(executor.executions), sup.executed_count,
                         "every executed action went through the authorized path")

        # 2. No duplicate authorization ever executes (cancelled actions never resume).
        ids = [e[0] for e in executor.executions]
        self.assertEqual(len(ids), len(set(ids)), "an authorization must never execute twice")

        # 3. Bounded retries: per goal, retries <= retry_budget x max plan steps
        #    (2 x 3 for the typed 3-step plans the brain Planner emits).
        retries = [e for e in sup.events if e.event_type == "ACTION_RETRY"]
        from collections import Counter
        retries_per_goal = Counter(e.goal_id for e in retries)
        self.assertTrue(
            all(count <= 2 * 3 for count in retries_per_goal.values()),
            f"per-goal retries must respect budgets: {dict(retries_per_goal)}",
        )

        # 4. Every goal reached a terminal status (completed/failed/cancelled).
        self.assertEqual(len(goals_source.completed), len(goals),
                         "no goal may be left dangling after the horizon")

        # 5. End-of-tick states are always terminal or recoverable, and the
        # supervisor is not mid-execution with an expired lease.
        self.assertIn(sup.state, {
            AutonomyState.IDLE, AutonomyState.OBSERVING, AutonomyState.INTERPRETING,
            AutonomyState.GOAL_PENDING, AutonomyState.PLANNING, AutonomyState.AWAITING_AUTHORITY,
            AutonomyState.RECOVERING, AutonomyState.PAUSED, AutonomyState.SAFE_STOP,
            AutonomyState.COMPLETED, AutonomyState.FAILED,
        })
        self.assertTrue(sup.tick_count >= 10_000)
        self.assertGreater(sup.executed_count, 0, "the simulation must actually act")


class EventBoundTests(unittest.TestCase):
    """Memory bound: the event ledger caps with a drop counter, never grows."""

    def test_events_capped_with_drop_counter(self):
        sup = make_supervisor()
        for _ in range(2100):
            sup._emit("TEST", reason="soak", producer="test")
        self.assertEqual(len(sup.events), 2048)
        self.assertEqual(sup.dropped_events, 52)
        # newest retained
        self.assertEqual(sup.events[-1].reason, "soak")

    def test_cap_tunable_via_constructor(self):
        sup = make_supervisor(max_events=10)
        for _ in range(15):
            sup._emit("TEST", reason="soak", producer="test")
        self.assertEqual(len(sup.events), 10)
        self.assertEqual(sup.dropped_events, 5)


if __name__ == "__main__":
    unittest.main()
