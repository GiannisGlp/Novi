"""Tests for NVIDIA no-hardware experiments (PERFECTING_PLAN Step 5).

Exp 1: context-aware reference resolution.
Exp 2: skill-contract invocation independent of implementation.
Exp 3: demonstration dataset in NoviEpisode schema with adapters.
"""

import unittest

from novi.brain.nvidia_experiments import (
    ALL_ADAPTERS,
    OBSERVED,
    SIMULATED,
    IsaacLabAdapter,
    LeRobotAdapter,
    NoviNativeAdapter,
    ROSBagAdapter,
    build_navigate_episode,
    build_pick_cup_episode,
    run_nvidia_experiments,
)


class NoviEpisodeSchemaTests(unittest.TestCase):
    def test_build_navigate_episode(self):
        ep = build_navigate_episode()
        self.assertEqual(ep.task_name, "navigate_to_kitchen")
        self.assertEqual(len(ep.steps), 3)
        self.assertEqual(ep.evidence_class, OBSERVED)

    def test_build_pick_cup_episode(self):
        ep = build_pick_cup_episode()
        self.assertEqual(ep.task_name, "pick_cup")
        self.assertEqual(len(ep.steps), 2)

    def test_episode_has_provenance(self):
        ep = build_navigate_episode()
        self.assertIn("source", ep.provenance)
        self.assertIn("experiment", ep.provenance)

    def test_episode_snapshot(self):
        ep = build_navigate_episode()
        snap = ep.snapshot()
        self.assertEqual(snap["step_count"], 3)
        self.assertEqual(len(snap["steps"]), 3)

    def test_simulated_episode_has_simulated_evidence_class(self):
        ep = build_navigate_episode(simulated=True)
        self.assertEqual(ep.evidence_class, SIMULATED)

    def test_episode_steps_have_evidence_class(self):
        ep = build_navigate_episode()
        for step in ep.steps:
            self.assertIn(step.evidence_class, {OBSERVED, SIMULATED, "INFERRED", "PREDICTED"})


class AdapterRoundTripTests(unittest.TestCase):
    def test_novi_native_roundtrip(self):
        ep = build_navigate_episode()
        adapter = NoviNativeAdapter()
        formatted = adapter.to_format(ep)
        restored = adapter.from_format(formatted)
        self.assertEqual(restored.episode_id, ep.episode_id)
        self.assertEqual(len(restored.steps), len(ep.steps))
        self.assertEqual(restored.evidence_class, ep.evidence_class)

    def test_lerobot_roundtrip(self):
        ep = build_pick_cup_episode()
        adapter = LeRobotAdapter()
        formatted = adapter.to_format(ep)
        restored = adapter.from_format(formatted)
        self.assertEqual(len(restored.steps), len(ep.steps))
        self.assertEqual(restored.evidence_class, ep.evidence_class)

    def test_isaac_lab_roundtrip(self):
        ep = build_navigate_episode()
        adapter = IsaacLabAdapter()
        formatted = adapter.to_format(ep)
        restored = adapter.from_format(formatted)
        self.assertEqual(len(restored.steps), len(ep.steps))
        self.assertEqual(restored.evidence_class, ep.evidence_class)

    def test_rosbag_roundtrip(self):
        ep = build_pick_cup_episode()
        adapter = ROSBagAdapter()
        formatted = adapter.to_format(ep)
        restored = adapter.from_format(formatted)
        self.assertEqual(len(restored.steps), len(ep.steps))
        self.assertEqual(restored.evidence_class, ep.evidence_class)

    def test_all_adapters_preserve_evidence_class(self):
        """Simulated episodes never silently become facts across all adapters."""
        ep = build_navigate_episode(simulated=True)
        for adapter_name, adapter in ALL_ADAPTERS.items():
            formatted = adapter.to_format(ep)
            restored = adapter.from_format(formatted)
            self.assertEqual(restored.evidence_class, SIMULATED,
                             f"{adapter_name} did not preserve SIMULATED evidence class")

    def test_all_adapters_preserve_observed_evidence_class(self):
        ep = build_navigate_episode(simulated=False)
        for adapter_name, adapter in ALL_ADAPTERS.items():
            formatted = adapter.to_format(ep)
            restored = adapter.from_format(formatted)
            self.assertEqual(restored.evidence_class, OBSERVED,
                             f"{adapter_name} did not preserve OBSERVED evidence class")

    def test_all_adapters_preserve_provenance(self):
        ep = build_navigate_episode()
        for adapter_name, adapter in ALL_ADAPTERS.items():
            formatted = adapter.to_format(ep)
            restored = adapter.from_format(formatted)
            self.assertTrue(restored.provenance, f"{adapter_name} lost provenance")

    def test_all_adapters_defined(self):
        self.assertEqual(len(ALL_ADAPTERS), 4)
        self.assertIn("novi_native", ALL_ADAPTERS)
        self.assertIn("lerobot", ALL_ADAPTERS)
        self.assertIn("isaac_lab", ALL_ADAPTERS)
        self.assertIn("rosbag", ALL_ADAPTERS)


class ExperimentRunnerTests(unittest.TestCase):
    def test_run_all_experiments(self):
        results = run_nvidia_experiments()
        self.assertEqual(len(results), 3)

    def test_experiment_1_reference_resolution(self):
        results = run_nvidia_experiments()
        exp1 = next(r for r in results if r.experiment_id == "nvidia_exp_1")
        self.assertTrue(exp1.passed)
        self.assertEqual(exp1.evidence_class, OBSERVED)

    def test_experiment_2_skill_contract(self):
        results = run_nvidia_experiments()
        exp2 = next(r for r in results if r.experiment_id == "nvidia_exp_2")
        self.assertTrue(exp2.passed)

    def test_experiment_3_demonstration_dataset(self):
        results = run_nvidia_experiments()
        exp3 = next(r for r in results if r.experiment_id == "nvidia_exp_3")
        self.assertTrue(exp3.passed)

    def test_experiments_carry_validation_evidence_class(self):
        """Each experiment is labelled E0-E5 (docs/01-system-architecture/10)."""
        results = run_nvidia_experiments()
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIn(r.validation_class, {"E0", "E1", "E2", "E3", "E4", "E5"})
            self.assertIn("validation_class", r.snapshot())

    def test_expected_validation_classes(self):
        results = {r.experiment_id: r for r in run_nvidia_experiments()}
        # Reproducible deterministic tests -> E2; adapter round-trip -> E3.
        self.assertEqual(results["nvidia_exp_1"].validation_class, "E2")
        self.assertEqual(results["nvidia_exp_2"].validation_class, "E2")
        self.assertEqual(results["nvidia_exp_3"].validation_class, "E3")

    def test_all_experiments_pass(self):
        """Done-bar: all NVIDIA experiments produce evidence files with evidence-class labels."""
        results = run_nvidia_experiments()
        for r in results:
            self.assertTrue(r.passed, f"{r.experiment_id} failed: {r.reason}")
            self.assertIn(r.evidence_class, {OBSERVED, SIMULATED, "INFERRED", "PREDICTED"})
            self.assertTrue(r.evidence_file, f"{r.experiment_id} has no evidence file")

    def test_experiment_result_snapshot(self):
        results = run_nvidia_experiments()
        for r in results:
            snap = r.snapshot()
            self.assertIn("experiment_id", snap)
            self.assertIn("passed", snap)
            self.assertIn("evidence_class", snap)


if __name__ == "__main__":
    unittest.main()
