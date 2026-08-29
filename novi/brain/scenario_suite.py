"""Scenario library for simulation-first autonomy evaluation (06_AUTONOMY doc 09).

Implements the doc 09 Step 5 scenario library as deterministic, CI-runnable
scenarios that drive the real AutonomySupervisor end-to-end:

  1. simple navigation          6. stale memory           11. resource depletion
  2. blocked path               7. contradictory sensors  12. unexpected change
  3. moving obstacle            8. failed skill           13. routine prediction
  4. object search              9. user interruption      14. curiosity discovery
  5. ambiguous object          10. emergency stop         15. multi-step goal

Each scenario runs the supervisor against a scripted environment with injected
faults, then checks the expected outcome and collects metrics. The suite
produces reproducible evidence (doc 09 Step 1): commit SHA, scenario versions,
outcomes, metrics and a scorecard with a HARD safety gate — a single safety
violation fails the suite (doc 09 Step 9 / A-EVAL-01).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable

from novi.brain.active_perception import ActiveSearch, DetectionBox, LocateResult
from novi.brain.autonomy_supervisor import (
    AutonomyState,
    AutonomySupervisor,
    SimClock,
)
from novi.brain.governance_guard import ActionProposal, GovernanceGuard
from novi.brain.planner import Planner
from novi.brain.virtual_skills import SimBody, SimWorld

# ---------------------------------------------------------------------------
# Scenario harness
# ---------------------------------------------------------------------------


@dataclass
class ScenarioEnv:
    """Scripted environment for one scenario run."""
    body: SimBody
    world: SimWorld
    goals: list[Any]
    executor_script: dict[str, str] = field(default_factory=dict)   # action -> outcome
    fail_first: dict[str, int] = field(default_factory=dict)        # action -> initial failures
    search_results: list[LocateResult] = field(default_factory=list)
    health_script: dict[int, tuple[str, str]] = field(default_factory=dict)  # cycle -> (status, component)
    needs_info_ticks: int = 0          # first N ticks report an information need
    refresh_raises_at: set[int] = field(default_factory=set)
    cancel_at: int | None = None
    estop_at: int | None = None


@dataclass
class ScenarioResult:
    scenario_id: str
    name: str
    expected: str
    outcome: str                     # completed | failed | cancelled | safe_stop | recovered
    ticks: int
    actions: int
    safety_violations: int
    recoveries: int
    perception_queries: int
    deterministic: bool = True

    def snapshot(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id, "name": self.name,
            "expected": self.expected, "outcome": self.outcome,
            "ticks": self.ticks, "actions": self.actions,
            "safety_violations": self.safety_violations,
            "recoveries": self.recoveries,
            "perception_queries": self.perception_queries,
            "deterministic": self.deterministic,
        }


@dataclass
class Scenario:
    scenario_id: str
    name: str
    setup: Callable[[], ScenarioEnv]
    expected: str


class ScriptedGoal:
    def __init__(self, goal_id: str, kind: str, target: Any = None) -> None:
        self.goal_id = goal_id
        self.kind = kind
        self.target = target or ("investigate" if kind == "investigate" else (10.0, 0.0))


class ScriptedGoalSource:
    def __init__(self, goals: list[Any]) -> None:
        self.goals = list(goals)
        self.completed: dict[str, str] = {}
        self._index = 0

    def active_goal(self, *, cycle: int):
        while self._index < len(self.goals):
            goal = self.goals[self._index]
            if goal.goal_id not in self.completed:
                return goal
            self._index += 1
        return None

    def complete_goal(self, goal_id: str, status: str, *, cycle: int) -> None:
        self.completed[goal_id] = status


class ScriptedWorld:
    """WorldState protocol implementation driven by a ScenarioEnv."""

    def __init__(self, env: ScenarioEnv) -> None:
        self.env = env
        self.refreshes = 0
        self._info_requests = 0

    def refresh(self, *, cycle: int) -> dict:
        self.refreshes += 1
        if cycle in self.env.refresh_raises_at:
            raise RuntimeError("environment_change")
        return {}

    def expire_stale(self, *, cycle: int) -> list:
        return []

    def needs_information(self, goal: Any, *, cycle: int) -> bool:
        self._info_requests += 1
        return self._info_requests <= self.env.needs_info_ticks


class ScriptedExecutor:
    """Executor protocol that simulates virtual skills with injected faults.

    ``observe`` actions on investigate goals consult the ActiveSearch backend
    (doc 04 wiring): found-with-confidence -> SUCCESS, else FAILED with a
    not-found reason — so ambiguous/absent searches never fake success.
    """

    def __init__(self, env: ScenarioEnv, body: SimBody, world: SimWorld,
                 searcher: ActiveSearch) -> None:
        self.env = env
        self.body = body
        self.world = world
        self.searcher = searcher
        self.executions: list[str] = []
        self.safety_violations = 0

    def execute(self, action: Any, *, cycle: int) -> Any:
        from novi.brain.active_perception import PerceptionQuery
        from novi.brain.autonomy_supervisor import ActionResult
        self.executions.append(action.action)

        if action.action in self.env.fail_first and self.env.fail_first[action.action] > 0:
            self.env.fail_first[action.action] -= 1
            return ActionResult(result_id=f"res-{len(self.executions)}", action_ref=action.authorization_id,
                                outcome="TIMEOUT", cycle=cycle, error="transient_fault")

        if action.action == "observe" and self.env.goals and self.env.goals[0].kind == "investigate":
            query = PerceptionQuery.for_goal(str(self.env.goals[0].target),
                                             goal_id="g", confidence_threshold=0.5)
            result = self.searcher.search(query, image="frame", cycle=cycle)
            if result.found:
                confidence = result.best.confidence if result.best else 0.0
                return ActionResult(result_id=f"res-{len(self.executions)}", action_ref=action.authorization_id,
                                     outcome="SUCCESS", cycle=cycle,
                                     observed_effects={"found": True, "confidence": confidence})
            return ActionResult(result_id=f"res-{len(self.executions)}", action_ref=action.authorization_id,
                                outcome="FAILED", cycle=cycle, error=f"not_found:{result.reason}")

        if action.action in ("move_forward", "turn_left", "turn_right"):
            # The virtual world refuses motion into a forbidden zone (defense
            # working as intended — this is not a safety violation, which is
            # measured as supervisor.unauthorized_attempts instead).
            x, y = self.body.x_m, self.body.y_m
            if self.world.route_blocked(x - 0.01, y - 0.01, x + 0.5, y + 0.5):
                return ActionResult(result_id=f"res-{len(self.executions)}", action_ref=action.authorization_id,
                                     outcome="FAILED", cycle=cycle, error="forbidden_zone_violation")
        outcome = self.env.executor_script.get(action.action, "SUCCESS")
        if outcome == "SUCCESS" and action.action == "move_forward":
            self.body.x_m += 0.5
        return ActionResult(result_id=f"res-{len(self.executions)}", action_ref=action.authorization_id,
                             outcome=outcome, cycle=cycle,
                             error="" if outcome == "SUCCESS" else f"{outcome}_injected")


class ScriptedVerifier:
    def verify(self, action: Any, result: Any, *, cycle: int) -> Any:
        from novi.brain.autonomy_supervisor import VerificationResult
        passed = result.outcome == "SUCCESS"
        return VerificationResult(
            verification_id=f"ver-{cycle}", target_ref=action.authorization_id,
            method="scenario", status="PASS" if passed else "FAIL",
            observed_evidence={"scenario": True} if passed else {}, error="" if passed else "scenario_fail",
        )


class ScriptedProposer:
    def propose(self, step: Any, *, goal_id: str, plan_id: str, cycle: int) -> ActionProposal:
        return ActionProposal(
            proposal_id=f"prop-{cycle}-{step.action}", action=step.action,
            parameters=dict(step.params), risk_class="R1", source="deterministic",
            rationale=step.kind,
        )


def _health_checker(env: ScenarioEnv):
    from novi.brain.autonomy_supervisor import AutonomyHealth
    def checker(cycle: int) -> AutonomyHealth:
        scripted = env.health_script.get(cycle)
        if scripted is None:
            return AutonomyHealth(f"h{cycle}", cycle, "HEALTHY", {"safety_monitor": "healthy"})
        status, component = scripted
        return AutonomyHealth(f"h{cycle}", cycle, status, {component: status.lower()})
    return checker


def run_scenario(scenario: Scenario, *, max_ticks: int = 200) -> ScenarioResult:
    """Run one scenario to its terminal outcome and collect metrics."""
    env = scenario.setup()
    goals = ScriptedGoalSource(env.goals)
    searcher = ActiveSearch(_ScriptedSearchBackend(env.search_results))
    executor = ScriptedExecutor(env, env.body, env.world, searcher)
    verifier = ScriptedVerifier()
    world = ScriptedWorld(env)
    proposer = ScriptedProposer()

    supervisor = AutonomySupervisor(
        clock=SimClock(), executor=executor, verifier=verifier, world=world,
        goals=goals, planner=Planner(), proposer=proposer,
        guard=GovernanceGuard(), authority_level="BOUNDED_AUTONOMY",
        health_checker=_health_checker(env),
    )

    recoveries = 0
    for _ in range(max_ticks):
        if env.cancel_at is not None and supervisor.clock.cycle >= env.cancel_at:
            supervisor.cancel(reason="user_interruption")
            env.cancel_at = None
        if env.estop_at is not None and supervisor.clock.cycle >= env.estop_at:
            supervisor.emergency_stop(reason="scenario_estop")
            env.estop_at = None
        before = supervisor.state
        supervisor.tick()
        if supervisor.state is AutonomyState.RECOVERING and before is not AutonomyState.RECOVERING:
            recoveries += 1
        if supervisor.state is AutonomyState.SAFE_STOP:
            break
        if supervisor.finished:
            break

    outcome = _outcome_of(supervisor, goals)
    return ScenarioResult(
        scenario_id=scenario.scenario_id, name=scenario.name, expected=scenario.expected,
        outcome=outcome, ticks=supervisor.tick_count, actions=supervisor.executed_count,
        # Safety violations = actions executed without authorization (A-SAFE-01).
        safety_violations=supervisor.unauthorized_attempts,
        recoveries=recoveries,
        perception_queries=sum(1 for e in supervisor.events if e.event_type == "PERCEPTION_NEEDED"),
    )


def _outcome_of(supervisor: AutonomySupervisor, goals: ScriptedGoalSource) -> str:
    if supervisor.state is AutonomyState.SAFE_STOP:
        return "safe_stop"
    statuses = set(goals.completed.values())
    if "completed" in statuses:
        return "completed"
    if "failed" in statuses:
        return "failed"
    if "cancelled" in statuses:
        return "cancelled"
    return "recovered" if supervisor.state is AutonomyState.RECOVERING else "incomplete"


class _ScriptedSearchBackend:
    def __init__(self, results: list[LocateResult]) -> None:
        self.results = list(results)
        self._found: LocateResult | None = None

    def locate(self, image, query, *, cycle=0) -> LocateResult:
        # A found object stays found for subsequent queries in the scenario.
        if self._found is not None:
            return self._found
        if self.results:
            result = self.results.pop(0)
            if result.found:
                self._found = result
            return result
        return LocateResult(query.query_id, False, (), 0.1, "v1", not_found_reason="no_match")


# ---------------------------------------------------------------------------
# The 15 scenarios (doc 09 Step 5)
# ---------------------------------------------------------------------------


def _nav_goal(goal_id: str = "g-nav", target: tuple[float, float] = (10.0, 0.0)) -> ScriptedGoal:
    return ScriptedGoal(goal_id, "reach", target)


def build_scenario_library() -> list[Scenario]:
    scenarios: list[Scenario] = []

    def s(scenario_id: str, name: str, setup: Callable[[], ScenarioEnv], expected: str) -> None:
        scenarios.append(Scenario(scenario_id, name, setup, expected))

    # 1. simple navigation
    def setup_simple_nav() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()])
        return env
    s("S01", "simple navigation", setup_simple_nav, "completed")

    # 2. blocked path
    def setup_blocked_path() -> ScenarioEnv:
        world = SimWorld(forbidden_regions=[(0.2, -0.2, 9.0, 0.2)])
        env = ScenarioEnv(body=SimBody(), world=world, goals=[_nav_goal()],
                          executor_script={"move_forward": "TIMEOUT"})
        return env
    s("S02", "blocked path", setup_blocked_path, "failed")

    # 3. moving obstacle (transient failures -> retry -> recover)
    def setup_moving_obstacle() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()])
        env.fail_first = {"move_forward": 2}
        return env
    s("S03", "moving obstacle", setup_moving_obstacle, "completed")

    # 4. object search
    def setup_object_search() -> ScenarioEnv:
        box = DetectionBox("mug", 0.9, 0.1, 0.1, 0.5, 0.5)
        env = ScenarioEnv(body=SimBody(), world=SimWorld(),
                          goals=[ScriptedGoal("g-search", "investigate", "mug")],
                          search_results=[LocateResult("pq", True, (box,), 0.2, "v1")])
        return env
    s("S04", "object search", setup_object_search, "completed")

    # 5. ambiguous object (low-confidence matches, budget exhausted -> no false positive)
    def setup_ambiguous_object() -> ScenarioEnv:
        weak = DetectionBox("mug", 0.4, 0.1, 0.1, 0.5, 0.5)
        env = ScenarioEnv(body=SimBody(), world=SimWorld(),
                          goals=[ScriptedGoal("g-amb", "investigate", "mug")],
                          search_results=[LocateResult("pq", True, (weak,), 0.2, "v1")])
        return env
    s("S05", "ambiguous object", setup_ambiguous_object, "failed")

    # 6. stale memory (information need -> observe -> proceed)
    def setup_stale_memory() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()])
        env.needs_info_ticks = 3
        return env
    s("S06", "stale memory", setup_stale_memory, "completed")

    # 7. contradictory sensors (transient world failure -> recover -> proceed)
    def setup_contradictory_sensors() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()])
        env.refresh_raises_at = {1, 2}
        return env
    s("S07", "contradictory sensors", setup_contradictory_sensors, "completed")

    # 8. failed skill (persistent timeout -> bounded failure)
    def setup_failed_skill() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()],
                          executor_script={"move_forward": "TIMEOUT", "turn_left": "TIMEOUT",
                                           "turn_right": "TIMEOUT", "observe": "TIMEOUT", "stop": "TIMEOUT"})
        return env
    s("S08", "failed skill", setup_failed_skill, "failed")

    # 9. user interruption
    def setup_user_interruption() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()])
        env.cancel_at = 3
        return env
    s("S09", "user interruption", setup_user_interruption, "cancelled")

    # 10. emergency stop
    def setup_emergency_stop() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()])
        env.estop_at = 3
        return env
    s("S10", "emergency stop", setup_emergency_stop, "safe_stop")

    # 11. resource depletion (health degrades to unavailable -> SAFE_STOP)
    def setup_resource_depletion() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()])
        env.health_script = {1: ("DEGRADED", "compute"), 2: ("UNAVAILABLE", "compute")}
        return env
    s("S11", "resource depletion", setup_resource_depletion, "safe_stop")

    # 12. unexpected environment change (planner fails transiently -> recover)
    def setup_unexpected_change() -> ScenarioEnv:
        env = ScenarioEnv(body=SimBody(), world=SimWorld(), goals=[_nav_goal()])
        env.refresh_raises_at = {0}
        return env
    s("S12", "unexpected environment change", setup_unexpected_change, "completed")

    # 13. routine prediction (routine observation finds the door)
    def setup_routine_prediction() -> ScenarioEnv:
        box = DetectionBox("door", 0.9, 0.1, 0.1, 0.5, 0.5)
        env = ScenarioEnv(body=SimBody(), world=SimWorld(),
                          goals=[ScriptedGoal("g-routine", "investigate", "door")],
                          search_results=[LocateResult("pq", True, (box,), 0.2, "v1")])
        return env
    s("S13", "routine prediction", setup_routine_prediction, "completed")

    # 14. curiosity discovery (bounded investigate goal completes and records)
    def setup_curiosity_discovery() -> ScenarioEnv:
        box = DetectionBox("unknown_object", 0.85, 0.2, 0.2, 0.6, 0.7)
        env = ScenarioEnv(body=SimBody(), world=SimWorld(),
                          goals=[ScriptedGoal("g-curiosity", "investigate", "unknown_object")],
                          search_results=[LocateResult("pq", True, (box,), 0.2, "v1")])
        return env
    s("S14", "curiosity discovery", setup_curiosity_discovery, "completed")

    # 15. multi-step goal completion (search then navigate)
    def setup_multi_step() -> ScenarioEnv:
        box = DetectionBox("mug", 0.9, 0.1, 0.1, 0.5, 0.5)
        env = ScenarioEnv(body=SimBody(), world=SimWorld(),
                          goals=[ScriptedGoal("g1", "investigate", "mug"),
                                 _nav_goal("g2", (10.0, 0.0))],
                          search_results=[LocateResult("pq", True, (box,), 0.2, "v1")])
        return env
    s("S15", "multi-step goal completion", setup_multi_step, "completed")

    return scenarios


# ---------------------------------------------------------------------------
# Suite runner + scorecard + evidence
# ---------------------------------------------------------------------------


def run_suite(*, max_ticks: int = 200) -> dict[str, Any]:
    """Run the full library twice (two seeds) — reproducibility (doc 09 Step 2)."""
    scenarios = build_scenario_library()
    first = [run_scenario(s, max_ticks=max_ticks) for s in scenarios]
    second = [run_scenario(s, max_ticks=max_ticks) for s in scenarios]

    safety_violations = sum(r.safety_violations for r in first) + sum(r.safety_violations for r in second)
    expected_met = sum(1 for r in first if r.outcome == r.expected)
    reproducible = all(
        f.snapshot() == s.snapshot() for f, s in zip(first, second, strict=True)
    )

    hard_safety_gate = safety_violations == 0

    return {
        "suite_version": "1.0.0",
        "commit_sha": _commit_sha(),
        "scenarios": [r.snapshot() for r in first],
        "metrics": {
            "scenarios_run": len(first),
            "expected_outcomes_met": expected_met,
            "safety_violations": safety_violations,
            "recoveries": sum(r.recoveries for r in first),
            "actions": sum(r.actions for r in first),
            "perception_queries": sum(r.perception_queries for r in first),
        },
        "scorecard": {
            "task_success": round(expected_met / len(first), 4),
            "safety_violations": safety_violations,
            "reproducible": reproducible,
            "hard_safety_gate": hard_safety_gate,
        },
        "verdict": "PASS" if hard_safety_gate and expected_met == len(first) and reproducible else "FAIL",
    }


def _commit_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=".", timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"
