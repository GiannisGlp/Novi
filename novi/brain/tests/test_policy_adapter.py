"""Tests for the learned-policy adapter seam + Exp-4 simulation benchmark."""

import unittest

from novi.brain.policy_adapter import (
    OBSTACLE_BLOCKING,
    SIMULATED,
    TIMEOUT_EXCEEDED,
    DeterministicPolicyBackend,
    IsaacPolicyBackend,
    PolicySkillAdapter,
    RandomizationConfig,
    run_policy_benchmark,
)
from novi.brain.skill_contract import NAVIGATE_SKILL
from novi.brain.virtual_skills import SimBody, SimWorld


class DeterministicPolicyTests(unittest.TestCase):
    def test_policy_arrives_within_budget(self):
        policy = DeterministicPolicyBackend()
        body = SimBody(x_m=0.0, y_m=0.0)
        world = SimWorld()
        adapter = PolicySkillAdapter(policy, NAVIGATE_SKILL, max_iterations=100)
        execution = adapter.invoke(
            {"pose_x": 0.0, "pose_y": 0.0, "heading_deg": 0.0, "target": (5.0, 1.0)},
            body=body,
            world=world,
        )
        self.assertEqual(execution.status, "SUCCESS")
        self.assertIsNone(execution.failure_class)
        self.assertGreater(execution.iterations, 0)

    def test_obstacle_blocks_with_classification(self):
        policy = DeterministicPolicyBackend()
        body = SimBody(x_m=0.0, y_m=0.0)
        world = SimWorld(forbidden_regions=[(2.0, -0.5, 2.4, 0.5)])
        adapter = PolicySkillAdapter(policy, NAVIGATE_SKILL, max_iterations=100)
        execution = adapter.invoke(
            {"pose_x": 0.0, "pose_y": 0.0, "heading_deg": 0.0, "target": (5.0, 1.0)},
            body=body,
            world=world,
        )
        self.assertEqual(execution.status, "FAILURE")
        self.assertEqual(execution.failure_class, OBSTACLE_BLOCKING)

    def test_iteration_budget_yields_timeout(self):
        policy = DeterministicPolicyBackend(move_distance=0.01)
        body = SimBody(x_m=0.0, y_m=0.0)
        world = SimWorld()
        adapter = PolicySkillAdapter(policy, NAVIGATE_SKILL, max_iterations=10)
        execution = adapter.invoke(
            {"pose_x": 0.0, "pose_y": 0.0, "heading_deg": 0.0, "target": (5.0, 1.0)},
            body=body,
            world=world,
        )
        self.assertEqual(execution.status, "TIMEOUT")
        self.assertEqual(execution.failure_class, TIMEOUT_EXCEEDED)

    def test_localization_loss_classified(self):
        policy = DeterministicPolicyBackend()
        body = SimBody(x_m=0.0, y_m=0.0, localized=True)
        world = SimWorld()
        adapter = PolicySkillAdapter(policy, NAVIGATE_SKILL, max_iterations=100)
        body.localized = False  # simulator reports localization loss on first step
        execution = adapter.invoke(
            {"pose_x": 0.0, "pose_y": 0.0, "heading_deg": 0.0, "target": (5.0, 1.0)},
            body=body,
            world=world,
        )
        self.assertEqual(execution.status, "FAILURE")
        self.assertEqual(execution.failure_class, "localization_lost")

    def test_partial_simulator_provision_rejected(self):
        policy = DeterministicPolicyBackend()
        adapter = PolicySkillAdapter(policy, NAVIGATE_SKILL)
        with self.assertRaises(ValueError):
            adapter.invoke(
                {"pose_x": 0.0, "pose_y": 0.0, "heading_deg": 0.0, "target": (1.0, 0.0)},
                body=SimBody(x_m=0.0, y_m=0.0),
            )  # world omitted -> body/world must be provided together

    def test_open_loop_returns_running(self):
        policy = DeterministicPolicyBackend()
        adapter = PolicySkillAdapter(policy, NAVIGATE_SKILL)
        execution = adapter.invoke({"pose_x": 0.0, "pose_y": 0.0, "heading_deg": 0.0, "target": (1.0, 0.0)})
        self.assertEqual(execution.status, "RUNNING")


class IsaacBackendGatingTests(unittest.TestCase):
    def test_isaac_backend_fails_loudly_on_mac(self):
        policy = IsaacPolicyBackend()
        adapter = PolicySkillAdapter(policy, NAVIGATE_SKILL)
        execution = adapter.invoke({"target": (1.0, 0.0)})
        self.assertEqual(execution.status, "FAILURE")
        self.assertIn("Isaac", execution.error)

    def test_isaac_backend_accepts_injected_policy_fn(self):
        def policy_fn(_obs):
            return {"action": "arrive", "target": [1.0, 0.0]}

        policy = IsaacPolicyBackend(policy_fn=policy_fn)
        execution = PolicySkillAdapter(policy, NAVIGATE_SKILL).invoke({"target": (1.0, 0.0)})
        self.assertEqual(execution.status, "SUCCESS")


class PolicyBenchmarkTests(unittest.TestCase):
    def test_benchmark_reports_metrics(self):
        result = run_policy_benchmark(episodes_per_config=3, seed=7)
        self.assertEqual(result.evidence_class, SIMULATED)
        self.assertEqual(len(result.runs), 3 * 5)  # 5 default configs
        self.assertGreater(result.success_rate, 0.0)
        self.assertLessEqual(result.success_rate, 1.0)
        self.assertGreaterEqual(result.robustness, 0.0)
        self.assertLessEqual(result.robustness, 1.0)
        self.assertEqual(
            set(result.config_metrics.keys()), {"nominal", "start_jitter", "target_jitter", "sensor_noise", "obstacle"}
        )

    def test_obstacle_config_fails_with_classification(self):
        result = run_policy_benchmark(
            configs=[RandomizationConfig(name="obstacle", obstacle=(2.0, -1.5, 2.4, 1.5))],
            episodes_per_config=3,
            seed=11,
        )
        self.assertEqual(result.config_metrics["obstacle"]["success_rate"], 0.0)
        self.assertIn(OBSTACLE_BLOCKING, result.failure_classes())
        self.assertEqual(result.failure_classes()[OBSTACLE_BLOCKING], 3)

    def test_nominal_config_high_success(self):
        result = run_policy_benchmark(
            configs=[RandomizationConfig(name="nominal")],
            episodes_per_config=5,
            seed=3,
        )
        self.assertEqual(result.config_metrics["nominal"]["success_rate"], 1.0)

    def test_snapshot_serializable(self):
        result = run_policy_benchmark(episodes_per_config=2, seed=1)
        snap = result.snapshot()
        self.assertIn("success_rate", snap)
        self.assertIn("robustness", snap)
        self.assertIn("failure_classes", snap)
        self.assertIn("per_config", snap)
        self.assertIn("runs", snap)
        self.assertEqual(snap["evidence_class"], SIMULATED)

    def test_benchmark_is_deterministic(self):
        a = run_policy_benchmark(episodes_per_config=3, seed=7).snapshot()
        b = run_policy_benchmark(episodes_per_config=3, seed=7).snapshot()
        c = run_policy_benchmark(episodes_per_config=3, seed=8).snapshot()
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


if __name__ == "__main__":
    unittest.main()
