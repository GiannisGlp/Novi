"""Dedicated unit tests for `MAC_BRAIN/multi_speed_runtime.py`.

Fills the P7/gap-46 coverage hole: previously the multi-speed runtime was only
exercised indirectly via `test_skill_governance.py`. These tests cover tier
gating, resource modes, state transitions, interruption/resume, task
registration lifecycle, execution results, and the System-0 safety tier that
never waits on an LLM.
"""

import unittest

from MAC_BRAIN.multi_speed_runtime import (
    ALL_SYSTEM_TIERS,
    SYSTEM_0,
    SYSTEM_1,
    SYSTEM_2,
    SYSTEM_3,
    AutonomyState,
    MultiSpeedRuntime,
    ResourceMode,
    SystemTask,
)


def runtime_with_safety(safety: bool = True) -> MultiSpeedRuntime:
    rt = MultiSpeedRuntime()
    rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": safety})
    return rt


class SystemTaskTests(unittest.TestCase):
    def test_snapshot_excludes_handler_and_result(self):
        task = SystemTask(task_id="t1", tier=SYSTEM_1, name="x", priority=0.5, max_latency_ms=100)
        snap = task.snapshot()
        self.assertEqual(snap["task_id"], "t1")
        self.assertEqual(snap["tier"], SYSTEM_1)
        self.assertEqual(snap["priority"], 0.5)
        self.assertEqual(snap["max_latency_ms"], 100)
        self.assertTrue(snap["enabled"])
        self.assertNotIn("handler", snap)
        self.assertNotIn("last_result", snap)

    def test_defaults(self):
        task = SystemTask(task_id="t", tier=SYSTEM_0, name="n")
        self.assertIsNone(task.handler)
        self.assertEqual(task.last_run_cycle, -1)
        self.assertTrue(task.enabled)


class RegistrationTests(unittest.TestCase):
    def test_register_creates_task_and_stores_it(self):
        rt = MultiSpeedRuntime()
        task = rt.register(SYSTEM_1, "reactive", lambda ctx: {}, priority=0.3, max_latency_ms=50)
        self.assertEqual(task.task_id, f"task:{SYSTEM_1}:reactive")
        self.assertIs(rt.get_task(task.task_id), task)

    def test_register_rejects_unknown_tier(self):
        rt = MultiSpeedRuntime()
        with self.assertRaises(ValueError):
            rt.register("system_9", "bad")

    def test_register_without_handler(self):
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "noop")
        results = rt.step()
        self.assertEqual(results["system_0"]["task:system_0:noop"], {"executed": True})

    def test_register_replaces_same_task_id(self):
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_1, "dup", lambda ctx: {"v": 1})
        rt.register(SYSTEM_1, "dup", lambda ctx: {"v": 2})
        self.assertEqual(len(rt.all_tasks()), 1)

    def test_unregister(self):
        rt = MultiSpeedRuntime()
        task = rt.register(SYSTEM_1, "gone")
        self.assertTrue(rt.unregister(task.task_id))
        self.assertFalse(rt.unregister(task.task_id))
        self.assertIsNone(rt.get_task(task.task_id))

    def test_all_tiers_supported(self):
        self.assertEqual(ALL_SYSTEM_TIERS, frozenset({SYSTEM_0, SYSTEM_1, SYSTEM_2, SYSTEM_3}))


class TierExecutionTests(unittest.TestCase):
    def test_system0_runs_before_higher_tiers(self):
        order = []
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "safety", lambda ctx: order.append("s0") or {"safe": True})
        rt.register(SYSTEM_1, "reactive", lambda ctx: order.append("s1"))
        rt.step()
        self.assertEqual(order, ["s0", "s1"])

    def test_task_results_captured_and_cycles_tracked(self):
        rt = MultiSpeedRuntime()
        task = rt.register(SYSTEM_1, "reactive", lambda ctx: {"value": 42})
        results = rt.step()
        self.assertEqual(results["system_1"][task.task_id], {"value": 42})
        self.assertEqual(task.last_result, {"value": 42})
        self.assertEqual(task.last_run_cycle, rt.cycle)
        self.assertEqual(rt.cycle, 1)

    def test_handler_exception_reported_not_raised(self):
        rt = MultiSpeedRuntime()
        task = rt.register(SYSTEM_1, "boom", lambda ctx: (_ for _ in ()).throw(RuntimeError("fail")))
        results = rt.step()
        self.assertEqual(results["system_1"][task.task_id], {"error": "fail"})

    def test_disabled_task_does_not_run(self):
        rt = MultiSpeedRuntime()
        task = rt.register(SYSTEM_1, "disabled", lambda ctx: {"ran": True})
        task.enabled = False
        results = rt.step()
        self.assertNotIn(task.task_id, results.get("system_1", {}))

    def test_priority_ordering(self):
        order = []
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_1, "low", lambda ctx: order.append("low") or {}, priority=0.1)
        rt.register(SYSTEM_1, "high", lambda ctx: order.append("high") or {}, priority=0.9)
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
        rt.step()
        self.assertEqual(order, ["high", "low"])


class System0SafetyTests(unittest.TestCase):
    def test_unsafe_safety_gates_higher_tiers(self):
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": False})
        rt.register(SYSTEM_1, "reactive", lambda ctx: {"ran": True})
        rt.register(SYSTEM_3, "deep", lambda ctx: {"ran": True})
        results = rt.step()
        self.assertFalse(rt.system0_safety_clear)
        self.assertEqual(rt.state, AutonomyState.INTERRUPTED)
        self.assertEqual(results["system_1"], {"interrupted": True})
        self.assertEqual(results["system_2"], {"interrupted": True})
        self.assertEqual(results["system_3"], {"interrupted": True})

    def test_non_dict_system0_result_does_not_block(self):
        # A System-0 task may return a non-dict (e.g. bool); only dict results
        # with safe=False gate higher tiers.
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "reaction", lambda ctx: True)
        rt.register(SYSTEM_1, "reactive", lambda ctx: {"ran": True})
        results = rt.step()
        self.assertTrue(rt.system0_safety_clear)
        self.assertIn("system_1", results)

    def test_safe_system0_allows_tiers(self):
        rt = runtime_with_safety(safety=True)
        rt.register(SYSTEM_2, "deliberative", lambda ctx: {"thought": True})
        results = rt.step()
        self.assertTrue(rt.system0_safety_clear)
        self.assertIn("system_2", results)


class ResourceModeTests(unittest.TestCase):
    def test_full_runs_all_tiers(self):
        rt = runtime_with_safety()
        rt.register(SYSTEM_1, "s1", lambda ctx: {})
        rt.register(SYSTEM_2, "s2", lambda ctx: {})
        rt.register(SYSTEM_3, "s3", lambda ctx: {})
        results = rt.step()
        for tier in (SYSTEM_1, SYSTEM_2, SYSTEM_3):
            self.assertIn(tier, results)

    def test_reactive_only_runs_system0_and_1(self):
        rt = runtime_with_safety()
        rt.set_resource_mode(ResourceMode.REACTIVE_ONLY)
        rt.register(SYSTEM_1, "s1", lambda ctx: {})
        rt.register(SYSTEM_2, "s2", lambda ctx: {})
        results = rt.step()
        self.assertIn("system_1", results)
        self.assertNotIn("system_2", results)

    def test_safe_minimum_runs_system0_only(self):
        rt = runtime_with_safety()
        rt.set_resource_mode(ResourceMode.SAFE_MINIMUM)
        rt.register(SYSTEM_1, "s1", lambda ctx: {})
        results = rt.step()
        self.assertIn("system_0", results)
        self.assertNotIn("system_1", results)
        self.assertEqual(rt.state, AutonomyState.SAFE_MINIMUM)

    def test_degraded_mode_skips_system2_and_3(self):
        rt = runtime_with_safety()
        rt.set_resource_mode(ResourceMode.DEGRADED)
        rt.register(SYSTEM_1, "s1", lambda ctx: {})
        rt.register(SYSTEM_2, "s2", lambda ctx: {})
        results = rt.step()
        self.assertIn("system_1", results)
        self.assertNotIn("system_2", results)
        self.assertEqual(rt.state, AutonomyState.DEGRADED)

    def test_set_state_explicit(self):
        rt = MultiSpeedRuntime()
        rt.set_state(AutonomyState.ACTIVE)
        self.assertEqual(rt.state, AutonomyState.ACTIVE)


class InterruptResumeTests(unittest.TestCase):
    def test_interrupt_skips_non_system0_tasks(self):
        rt = runtime_with_safety()
        task = rt.register(SYSTEM_1, "reactive", lambda ctx: {"ran": True})
        rt.interrupt()
        self.assertEqual(rt.state, AutonomyState.INTERRUPTED)
        results = rt.step()
        self.assertEqual(results["system_1"][task.task_id], {"interrupted": True})

    def test_resume_returns_to_full(self):
        rt = runtime_with_safety()
        rt.register(SYSTEM_1, "reactive", lambda ctx: {"ran": True})
        rt.interrupt()
        rt.resume()
        self.assertEqual(rt.state, AutonomyState.ACTIVE)
        results = rt.step()
        self.assertIn("system_1", results)

    def test_resume_after_degraded_returns_degraded(self):
        rt = runtime_with_safety()
        rt.set_resource_mode(ResourceMode.DEGRADED)
        rt.interrupt()
        rt.resume()
        self.assertEqual(rt.state, AutonomyState.DEGRADED)

    def test_interrupt_never_touches_system0(self):
        rt = runtime_with_safety()
        s0 = rt.get_task("task:system_0:safety")
        rt.interrupt()
        self.assertNotIn(s0.task_id, rt.snapshot()["interrupted_tasks"])


class SnapshotTests(unittest.TestCase):
    def test_snapshot_shape(self):
        rt = runtime_with_safety()
        rt.register(SYSTEM_1, "reactive", lambda ctx: {})
        rt.step()
        snap = rt.snapshot()
        self.assertEqual(snap["cycle"], 1)
        self.assertEqual(snap["state"], AutonomyState.IDLE.value)
        self.assertEqual(snap["resource_mode"], ResourceMode.FULL.value)
        self.assertTrue(snap["system0_safety_clear"])
        self.assertEqual(len(snap["tasks"]), 2)
        self.assertEqual(snap["interrupted_tasks"], [])

    def test_tasks_by_tier(self):
        rt = runtime_with_safety()
        rt.register(SYSTEM_2, "a", lambda ctx: {})
        rt.register(SYSTEM_2, "b", lambda ctx: {})
        self.assertEqual(len(rt.tasks_by_tier(SYSTEM_2)), 2)
        self.assertEqual(len(rt.tasks_by_tier(SYSTEM_3)), 0)


if __name__ == "__main__":
    unittest.main()
