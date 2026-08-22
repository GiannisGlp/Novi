"""Tests for Closed-Loop Validation + Acceptance Gate (PERFECTING_PLAN Step 6).

Done-bar:
  - Cross-system acceptance tests (Soul -> Cognition -> Memory -> Autonomy -> Safety -> Brain).
  - Closed-loop verify tests (OBSERVE -> PLAN -> ACT -> VERIFY with outcome handling).
  - Full suite green + acceptance evidence.
  - Global completion-gate review.
"""

import unittest

from MAC_BRAIN.closed_loop import (
    ACT,
    ASK,
    OBSERVE,
    OUTCOME_FAILURE,
    OUTCOME_SUCCESS,
    PLAN,
    RECOVER,
    STOP,
    VERIFY,
    ClosedLoopRuntime,
    run_completion_gate,
    run_cross_system_acceptance,
)


class ClosedLoopRuntimeTests(unittest.TestCase):
    def test_full_cycle_success(self):
        rt = ClosedLoopRuntime()
        steps = rt.run_full_cycle(
            observation={"entities": ["cup"]},
            plan={"goal": "pick"},
            action={"skill": "pick", "outcome": OUTCOME_SUCCESS},
            success_criteria=["object_grasped"],
            observed_state={"object_grasped": True},
        )
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[0].phase, OBSERVE)
        self.assertEqual(steps[1].phase, PLAN)
        self.assertEqual(steps[2].phase, ACT)
        self.assertEqual(steps[3].phase, VERIFY)
        self.assertEqual(steps[3].outcome, OUTCOME_SUCCESS)

    def test_verify_failure_triggers_recovery(self):
        rt = ClosedLoopRuntime()
        rt.observe({"entities": ["cup"]})
        rt.plan({"goal": "pick"})
        rt.act({"skill": "pick", "outcome": OUTCOME_FAILURE})
        verify_step = rt.verify(["object_grasped"], {"object_grasped": False})
        self.assertEqual(verify_step.outcome, OUTCOME_FAILURE)
        self.assertEqual(rt.current_phase, RECOVER)

    def test_recovery_then_retry(self):
        rt = ClosedLoopRuntime()
        rt.observe({"entities": ["cup"]})
        rt.plan({"goal": "pick"})
        rt.act({"skill": "pick", "outcome": OUTCOME_FAILURE})
        rt.verify(["object_grasped"], {"object_grasped": False})
        # Recovery attempt.
        rt.recover({"action": "reapproach"})
        self.assertEqual(rt.current_phase, PLAN)
        # Try again.
        rt.plan({"goal": "pick", "retry": True})
        rt.act({"skill": "pick", "outcome": OUTCOME_SUCCESS})
        verify = rt.verify(["object_grasped"], {"object_grasped": True})
        self.assertEqual(verify.outcome, OUTCOME_SUCCESS)

    def test_max_recovery_then_ask(self):
        rt = ClosedLoopRuntime()
        rt._max_recovery = 2
        rt.observe({"entities": ["cup"]})
        rt.plan({"goal": "pick"})
        rt.act({"skill": "pick", "outcome": OUTCOME_FAILURE})
        # First recovery attempt.
        rt.verify(["object_grasped"], {"object_grasped": False})
        rt.recover({"action": "retry_1"})
        rt.plan({"goal": "pick"})
        rt.act({"skill": "pick", "outcome": OUTCOME_FAILURE})
        # Second recovery attempt.
        rt.verify(["object_grasped"], {"object_grasped": False})
        rt.recover({"action": "retry_2"})
        rt.plan({"goal": "pick"})
        rt.act({"skill": "pick", "outcome": OUTCOME_FAILURE})
        # After max recovery, should ASK.
        verify = rt.verify(["object_grasped"], {"object_grasped": False})
        self.assertEqual(rt.current_phase, ASK)

    def test_stop(self):
        rt = ClosedLoopRuntime()
        step = rt.stop("user_cancelled")
        self.assertEqual(step.phase, STOP)
        self.assertEqual(rt.current_phase, STOP)

    def test_loop_cycles_back_to_observe_on_success(self):
        rt = ClosedLoopRuntime()
        rt.run_full_cycle(
            observation={"entities": ["cup"]},
            plan={"goal": "pick"},
            action={"skill": "pick", "outcome": OUTCOME_SUCCESS},
            success_criteria=["object_grasped"],
            observed_state={"object_grasped": True},
        )
        self.assertEqual(rt.current_phase, OBSERVE)

    def test_snapshot(self):
        rt = ClosedLoopRuntime()
        rt.observe({"entities": ["cup"]})
        snap = rt.snapshot()
        self.assertEqual(snap["current_phase"], PLAN)
        self.assertEqual(len(snap["steps"]), 1)

    def test_verify_step_is_first_class(self):
        """The VERIFY step is a first-class phase, not an afterthought."""
        rt = ClosedLoopRuntime()
        rt.observe({"entities": ["cup"]})
        rt.plan({"goal": "pick"})
        rt.act({"skill": "pick"})
        verify = rt.verify(["object_grasped", "object_secured"], {"object_grasped": True, "object_secured": True})
        # Both criteria met → success.
        self.assertEqual(verify.outcome, OUTCOME_SUCCESS)
        self.assertEqual(len(rt._verify_result["met"]), 2)
        self.assertEqual(len(rt._verify_result["unmet"]), 0)


class CrossSystemAcceptanceTests(unittest.TestCase):
    def test_all_cross_system_tests_defined(self):
        results = run_cross_system_acceptance()
        self.assertGreaterEqual(len(results), 6)

    def test_soul_to_cognition(self):
        results = run_cross_system_acceptance()
        r = next(x for x in results if x.test_id == "cross_1")
        self.assertTrue(r.passed)

    def test_cognition_to_memory(self):
        results = run_cross_system_acceptance()
        r = next(x for x in results if x.test_id == "cross_2")
        self.assertTrue(r.passed)

    def test_memory_to_autonomy_simulated_not_fact(self):
        results = run_cross_system_acceptance()
        r = next(x for x in results if x.test_id == "cross_3")
        self.assertTrue(r.passed)

    def test_autonomy_to_safety_governance(self):
        results = run_cross_system_acceptance()
        r = next(x for x in results if x.test_id == "cross_4")
        self.assertTrue(r.passed)

    def test_safety_to_brain_system0(self):
        results = run_cross_system_acceptance()
        r = next(x for x in results if x.test_id == "cross_5")
        self.assertTrue(r.passed)

    def test_full_cross_system(self):
        results = run_cross_system_acceptance()
        r = next(x for x in results if x.test_id == "cross_6")
        self.assertTrue(r.passed)

    def test_all_cross_system_tests_pass(self):
        """Done-bar: all cross-system acceptance tests pass."""
        results = run_cross_system_acceptance()
        for r in results:
            self.assertTrue(r.passed, f"{r.test_id} failed: {r.reason}")


class CompletionGateTests(unittest.TestCase):
    def test_completion_gate_all_steps_pass(self):
        step_results = {
            "step_0": True, "step_1": True, "step_2": True,
            "step_3": True, "step_4": True, "step_5": True,
        }
        gate = run_completion_gate(step_results)
        self.assertTrue(gate.passed)
        self.assertEqual(gate.steps_passed, 6)

    def test_completion_gate_any_step_fail(self):
        step_results = {
            "step_0": True, "step_1": True, "step_2": False,
            "step_3": True, "step_4": True, "step_5": True,
        }
        gate = run_completion_gate(step_results)
        self.assertFalse(gate.passed)
        self.assertEqual(gate.steps_passed, 5)

    def test_completion_gate_includes_cross_system(self):
        step_results = {"step_1": True}
        gate = run_completion_gate(step_results)
        self.assertGreater(len(gate.cross_system_results), 0)

    def test_completion_gate_snapshot(self):
        step_results = {"step_1": True}
        gate = run_completion_gate(step_results)
        snap = gate.snapshot()
        self.assertIn("passed", snap)
        self.assertIn("cross_system_results", snap)


if __name__ == "__main__":
    unittest.main()
