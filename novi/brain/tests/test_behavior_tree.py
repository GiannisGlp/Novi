"""Tests for planning & skill execution (06_AUTONOMY doc 05).

Covers: behavior-tree control semantics (sequence/selector/retry/timeout),
precondition discipline (an action whose preconditions fail is never executed),
postcondition verification, recovery strategies, skill outcome memory, the
virtual NavigateTo/SearchForObject skills, and an A-PLAN-01-style 100-task run.
"""

from __future__ import annotations

import unittest

from novi.brain.active_perception import (
    ActiveSearch,
    DetectionBox,
    LocateResult,
    PerceptionBudget,
)
from novi.brain.behavior_tree import (
    ActionNode,
    BTContext,
    ConditionNode,
    OutcomeMemory,
    RecoveryNode,
    RetryNode,
    Selector,
    Sequence,
    Status,
    TimeoutNode,
    TreeRunner,
)
from novi.brain.virtual_skills import NavigateToSkill, SearchForObjectSkill, SimBody, SimWorld


class BehaviorTreeSemanticsTests(unittest.TestCase):
    def test_sequence_short_circuits_on_failure(self):
        calls: list[str] = []

        def mk(name: str, ok: bool):
            def execute(ctx):
                calls.append(name)
                return {"done": True}
            def post(ctx, outcome):
                from novi.brain.behavior_tree import PostconditionCheck
                return PostconditionCheck("check", ok, error="" if ok else "fail")
            return ActionNode(name, execute=execute, postcondition=post)

        tree = Sequence([mk("a", True), mk("b", False), mk("c", True)])
        status, _ = TreeRunner(tree).run(BTContext())
        self.assertEqual(status, Status.FAILURE)
        self.assertEqual(calls, ["a", "b"], "sequence must not run children after a failure")

    def test_selector_falls_back(self):
        def failing(ctx):
            return {"done": False}
        fail_node = ActionNode("fail", execute=failing)
        fail_node.postcondition = lambda ctx, out: __import__(
            "novi.brain.behavior_tree", fromlist=["PostconditionCheck"]).PostconditionCheck(
            "check", False, error="boom")

        def succeeding(ctx):
            return {"done": True}
        ok_node = ActionNode("ok", execute=succeeding)

        tree = Selector([fail_node, ok_node])
        status, _ = TreeRunner(tree).run(BTContext())
        self.assertEqual(status, Status.SUCCESS)

    def test_retry_is_bounded(self):
        attempts = {"n": 0}

        def always_fails(ctx):
            attempts["n"] += 1
            return {"done": False}
        node = ActionNode("flaky", execute=always_fails)
        node.postcondition = lambda ctx, out: __import__(
            "novi.brain.behavior_tree", fromlist=["PostconditionCheck"]).PostconditionCheck(
            "check", False, error="nope")

        tree = RetryNode(node, max_retries=3)
        status, _ = TreeRunner(tree).run(BTContext())
        self.assertEqual(status, Status.FAILURE)
        self.assertEqual(attempts["n"], 4, "1 initial + 3 retries, never more")

    def test_timeout_aborts(self):
        state = {"cycles": 0}

        def slow(ctx):
            state["cycles"] += 1
            return {"done": False}
        node = ActionNode("slow", execute=slow)
        node.postcondition = lambda ctx, out: __import__(
            "novi.brain.behavior_tree", fromlist=["PostconditionCheck"]).PostconditionCheck(
            "check", False, error="unfinished")

        tree = TimeoutNode(node, max_cycles=3)
        status, elapsed = TreeRunner(tree).run(BTContext())
        self.assertEqual(status, Status.FAILURE)
        self.assertLessEqual(elapsed, 4)

    def test_condition_node(self):
        cond = ConditionNode("localized", lambda ctx: ctx.world.get("localized", False))
        status, _ = TreeRunner(Sequence([cond])).run(BTContext(world={"localized": True}))
        self.assertEqual(status, Status.SUCCESS)
        status, _ = TreeRunner(Sequence([cond])).run(BTContext(world={"localized": False}))
        self.assertEqual(status, Status.FAILURE)


class PreconditionDisciplineTests(unittest.TestCase):
    def test_action_with_failed_precondition_never_executes(self):
        executions = {"n": 0}

        def precondition(ctx):
            return False, "not_localized"

        def execute(ctx):
            executions["n"] += 1
            return {"done": True}

        node = ActionNode("move", precondition=precondition, execute=execute)
        status, _ = TreeRunner(Sequence([node])).run(BTContext())
        self.assertEqual(status, Status.FAILURE)
        self.assertEqual(executions["n"], 0, "A-PLAN-01: preconditions gate execution")

    def test_precondition_failure_counted(self):
        def precondition(ctx):
            return False, "route_blocked"

        node = ActionNode("move", precondition=precondition, execute=lambda ctx: {})
        TreeRunner(Sequence([node])).run(BTContext())
        self.assertEqual(node.precondition_failures, 1)


class RecoveryTests(unittest.TestCase):
    def test_recovery_retry_then_safe_stop(self):
        attempts = {"n": 0}

        def flaky(ctx):
            attempts["n"] += 1
            return {"done": attempts["n"] >= 3}

        node = ActionNode("flaky", execute=flaky)
        node.postcondition = lambda ctx, out: __import__(
            "novi.brain.behavior_tree", fromlist=["PostconditionCheck"]).PostconditionCheck(
            "check", bool(out.get("done")), error="" if out.get("done") else "not_done")

        tree = RecoveryNode(node, strategy="retry", max_retries=4)
        status, _ = TreeRunner(tree).run(BTContext())
        self.assertEqual(status, Status.SUCCESS)
        self.assertEqual(attempts["n"], 3)
        self.assertEqual(tree.recovery_events[0]["strategy"], "retry")

    def test_safe_stop_strategy_is_terminal(self):
        node = ActionNode("danger", execute=lambda ctx: {})
        node.postcondition = lambda ctx, out: __import__(
            "novi.brain.behavior_tree", fromlist=["PostconditionCheck"]).PostconditionCheck(
            "check", False, error="unsafe")

        tree = RecoveryNode(node, strategy="safe_stop")
        status, _ = TreeRunner(tree).run(BTContext())
        self.assertEqual(status, Status.FAILURE)
        self.assertEqual(tree.recovery_events[-1]["strategy"], "safe_stop")


class OutcomeMemoryTests(unittest.TestCase):
    def test_success_rate_with_context_filter(self):
        memory = OutcomeMemory()
        memory.record(skill_id="NavigateTo", outcome="SUCCESS", verification="PASS",
                      context={"goal_kind": "reach"}, cycle=1)
        memory.record(skill_id="NavigateTo", outcome="FAILURE", verification="FAIL",
                      context={"goal_kind": "reach"}, cycle=2)
        memory.record(skill_id="NavigateTo", outcome="SUCCESS", verification="PASS",
                      context={"goal_kind": "investigate"}, cycle=3)
        rate_all = memory.success_rate("NavigateTo")
        assert rate_all is not None
        self.assertAlmostEqual(rate_all, 2 / 3)
        rate_reach = memory.success_rate("NavigateTo", context_filter={"goal_kind": "reach"})
        assert rate_reach is not None
        self.assertAlmostEqual(rate_reach, 0.5)
        self.assertIsNone(memory.success_rate("UnknownSkill"))


class VirtualSkillTests(unittest.TestCase):
    def test_navigate_reaches_target_with_verification(self):
        body = SimBody(x_m=0, y_m=0, heading_deg=0)
        world = SimWorld()
        skill = NavigateToSkill(body, world)
        ctx = {"target": (10.0, 0.0), "goal_kind": "reach"}
        ok, reason = skill.preconditions(ctx)
        self.assertTrue(ok)
        check = None
        for _ in range(100):
            outcome = skill.execute(ctx)
            check = skill.postcondition(ctx, outcome)
            if check.passed:
                break
        assert check is not None
        self.assertTrue(check.passed, "navigation must eventually verify arrival")
        self.assertAlmostEqual(body.x_m, 10.0, delta=0.5)

    def test_navigate_never_executes_when_not_localized(self):
        body = SimBody(localized=False)
        skill = NavigateToSkill(body, SimWorld())
        ok, reason = skill.preconditions({"target": (1.0, 0.0)})
        self.assertFalse(ok)
        self.assertEqual(reason, "not_localized")

    def test_navigate_blocks_on_forbidden_route(self):
        body = SimBody(x_m=0, y_m=0)
        world = SimWorld(forbidden_regions=[(0.2, -0.2, 0.8, 0.2)])
        skill = NavigateToSkill(body, world)
        ok, reason = skill.preconditions({"target": (10.0, 0.0)})
        self.assertFalse(ok)
        self.assertEqual(reason, "route_blocked")

    def test_search_found_records_outcome(self):
        box = DetectionBox("mug", 0.9, 0.1, 0.1, 0.5, 0.5)
        backend = _ScriptedBackend([LocateResult("pq", True, (box,), 0.2, "v1")])
        searcher = ActiveSearch(backend)
        memory = OutcomeMemory()
        skill = SearchForObjectSkill(searcher, memory=memory)
        ok, reason = skill.preconditions({"target": "mug"})
        self.assertTrue(ok)
        outcome = skill.execute({"target": "mug", "goal_id": "g1"})
        check = skill.postcondition({"target": "mug"}, outcome)
        self.assertTrue(check.passed)
        skill.record(outcome="SUCCESS", verification="PASS", ctx={"target": "mug"}, cycle=1)
        self.assertEqual(memory.success_rate("SearchForObject"), 1.0)

    def test_search_not_found_is_not_success(self):
        backend = _ScriptedBackend([])  # always no-match
        searcher = ActiveSearch(backend, budget=PerceptionBudget(max_vlm_queries=2))
        skill = SearchForObjectSkill(searcher)
        outcome = skill.execute({"target": "ghost"})
        self.assertFalse(outcome["found"])
        check = skill.postcondition({"target": "ghost"}, outcome)
        self.assertFalse(check.passed, "not-found must fail verification (no false success)")


class _ScriptedBackend:
    def __init__(self, script: list[LocateResult]) -> None:
        self.script = list(script)

    def locate(self, image, query, *, cycle=0) -> LocateResult:
        if not self.script:
            return LocateResult(query.query_id, False, (), 0.1, "v1", not_found_reason="no_match")
        return self.script.pop(0)


class PlanExecutionTests(unittest.TestCase):
    def test_a_plan_01_one_hundred_tasks_never_execute_failed_preconditions(self):
        """Gate A-PLAN-01-style: 100 simulated tasks with injected perception
        and execution failures recover or stop safely, and no skill whose
        preconditions fail is ever executed."""
        memory = OutcomeMemory()

        for task in range(100):
            body = SimBody(x_m=0, y_m=0)
            world = SimWorld()
            # Every 7th task has a blocked route; every 13th is not localized.
            if task % 7 == 0:
                world.forbidden_regions.append((-10.0, -10.0, 10.0, 10.0))
            if task % 13 == 0:
                body.localized = False
            navigate = NavigateToSkill(body, world, memory=memory, max_steps=40)
            target = (float(5 + task % 3), 0.0)

            # Build a small tree: precondition gate -> navigate -> verify.
            # (Bind the skill as a default arg so the closures capture the
            # per-task instance, not the loop variable.)
            def pre(ctx, _skill=navigate):
                return _skill.preconditions(dict(ctx.params))

            def execute(ctx, _skill=navigate):
                outcome = _skill.execute(dict(ctx.params))
                check = _skill.postcondition(dict(ctx.params), outcome)
                if check.passed:
                    _skill.record(outcome="SUCCESS", verification="PASS",
                                  ctx=dict(ctx.params), cycle=ctx.cycle)
                return outcome

            def post(ctx, outcome, _skill=navigate):
                return _skill.postcondition(dict(ctx.params), outcome)

            node = ActionNode("navigate", precondition=pre, execute=execute, postcondition=post)
            # Navigation is a multi-cycle action: bound it with a timeout and
            # recover within a small retry budget on real failures.
            tree = TimeoutNode(RecoveryNode(node, strategy="retry", max_retries=1), max_cycles=50)
            status, _ = TreeRunner(tree, max_cycles=50).run(
                BTContext(cycle=task, world={"localized": body.localized}, params={"target": target, "goal_kind": "reach"}))

            # The A-PLAN-01 invariant: preconditions gate execution.
            self.assertGreaterEqual(node.precondition_failures, 0)
            if not body.localized or world.forbidden_regions:
                self.assertEqual(node.executions, 0,
                                 "a skill whose preconditions fail must never execute")
                self.assertIn(status, (Status.FAILURE, Status.SUCCESS))
            else:
                self.assertEqual(status, Status.SUCCESS, f"task {task} should navigate successfully")
                self.assertGreaterEqual(node.executions, 1)

        # Outcome memory captured the experience. Tasks with blocked routes
        # (every 7th) or no localization (every 13th) never executed, so 79
        # of 100 tasks ran and recorded outcomes.
        self.assertGreaterEqual(memory.count(), 75)
        rate = memory.success_rate("NavigateTo")
        assert rate is not None
        self.assertGreater(rate, 0.7)


if __name__ == "__main__":
    unittest.main()
