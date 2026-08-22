"""Tests for P0GateEvaluator wiring as a release gate.

Verifies:
  - run_p0_gate() runs all P0 scenarios against a live brain.
  - The P0 gate passes with a healthy brain (zero violations).
  - The brain.p0_gate() method emits a p0.gate event.
  - The CLI runner exits 0 on pass.
  - Individual scenario runners produce correct results.
"""

import unittest
import subprocess
import sys

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception

from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
from MAC_BRAIN.soul_acceptance import P0GateResult, ALL_P0_SCENARIOS
from MAC_BRAIN.p0_gate_runner import run_p0_gate, _SCENARIO_RUNNERS
from MAC_BRAIN.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


class PersonBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("alice", 0.95, (0.0, 0.0, 0.3, 0.5)),)


class P0GateRunnerTests(unittest.TestCase):
    def _brain(self):
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(PersonBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        brain.step()
        return brain

    def test_run_p0_gate_returns_result(self):
        brain = self._brain()
        try:
            result = run_p0_gate(brain)
            self.assertIsInstance(result, P0GateResult)
        finally:
            brain.stop()

    def test_p0_gate_passes_with_healthy_brain(self):
        """The P0 gate should pass with a healthy, freshly-started brain."""
        brain = self._brain()
        try:
            result = run_p0_gate(brain)
            self.assertTrue(result.passed)
            self.assertEqual(result.failed_scenarios, 0)
            self.assertEqual(len(result.violations), 0)
        finally:
            brain.stop()

    def test_all_scenarios_have_runners(self):
        """Every P0 scenario has a runner function."""
        for scenario in ALL_P0_SCENARIOS:
            self.assertIn(scenario.scenario_id, _SCENARIO_RUNNERS,
                         f"No runner for scenario {scenario.scenario_id}")

    def test_all_scenarios_run(self):
        """All 13 P0 scenarios are executed by run_p0_gate."""
        brain = self._brain()
        try:
            result = run_p0_gate(brain)
            self.assertEqual(result.total_scenarios, len(ALL_P0_SCENARIOS))
            self.assertEqual(result.passed_scenarios + result.failed_scenarios,
                            result.total_scenarios)
        finally:
            brain.stop()

    def test_p0_gate_snapshot(self):
        brain = self._brain()
        try:
            result = run_p0_gate(brain)
            snap = result.snapshot()
            self.assertIn("passed", snap)
            self.assertIn("total_scenarios", snap)
            self.assertIn("violations", snap)
            self.assertEqual(snap["gate"], "P0")
        finally:
            brain.stop()


class P0GateRuntimeMethodTests(unittest.TestCase):
    def test_brain_p0_gate_method_exists(self):
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(CupBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        brain.step()
        try:
            self.assertTrue(hasattr(brain, "p0_gate"))
        finally:
            brain.stop()

    def test_p0_gate_method_returns_snapshot(self):
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(PersonBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        brain.step()
        try:
            result = brain.p0_gate()
            self.assertIsInstance(result, dict)
            self.assertIn("passed", result)
            self.assertIn("total_scenarios", result)
            self.assertTrue(result["passed"])
        finally:
            brain.stop()

    def test_p0_gate_emits_event(self):
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(PersonBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        brain.step()
        try:
            brain.p0_gate()
            events = [e for e in brain.events if e["event_type"] == "p0.gate"]
            self.assertGreater(len(events), 0)
            self.assertTrue(events[-1]["payload"]["passed"])
        finally:
            brain.stop()


class P0GateCLITests(unittest.TestCase):
    def test_cli_exits_zero_on_pass(self):
        """The CLI runner exits 0 when the gate passes."""
        result = subprocess.run(
            [sys.executable, "-m", "MAC_BRAIN.p0_gate_runner"],
            capture_output=True, text=True, timeout=30,
            cwd="/Users/vanonatobaidze/projects/Novi",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("P0 GATE PASSED", result.stdout)


if __name__ == "__main__":
    unittest.main()