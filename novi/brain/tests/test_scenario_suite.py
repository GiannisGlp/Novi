"""Tests for the simulation-first scenario suite (06_AUTONOMY doc 09).

Covers: the 15-scenario library, expected outcomes per scenario, metrics,
reproducibility, and the A-EVAL-01 gate (full suite across repeated runs with
zero safety violations and reproducible evidence).
"""

from __future__ import annotations

import unittest

from novi.brain.scenario_suite import (
    build_scenario_library,
    run_scenario,
    run_suite,
)


class ScenarioLibraryTests(unittest.TestCase):
    def test_all_fifteen_scenarios_are_defined(self):
        library = build_scenario_library()
        self.assertEqual(len(library), 15)
        ids = [scenario.scenario_id for scenario in library]
        self.assertEqual(len(set(ids)), 15, "scenario ids must be unique")
        self.assertEqual(ids, [f"S{i:02d}" for i in range(1, 16)])

    def test_every_scenario_meets_its_expected_outcome(self):
        """The library is the executable spec: each scenario must end as documented."""
        for scenario in build_scenario_library():
            result = run_scenario(scenario)
            self.assertEqual(
                result.outcome, scenario.expected,
                f"{scenario.scenario_id} ({scenario.name}): expected {scenario.expected!r}, got {result.outcome!r}",
            )

    def test_safety_scenarios_stop_safely(self):
        for scenario_id in ("S10", "S11"):
            scenario = next(s for s in build_scenario_library() if s.scenario_id == scenario_id)
            result = run_scenario(scenario)
            self.assertEqual(result.outcome, "safe_stop")
            self.assertEqual(result.safety_violations, 0)

    def test_failure_scenarios_are_bounded(self):
        """Failed scenarios still respect bounds: no unbounded action loops."""
        for scenario_id in ("S02", "S05", "S08"):
            scenario = next(s for s in build_scenario_library() if s.scenario_id == scenario_id)
            result = run_scenario(scenario)
            self.assertEqual(result.outcome, "failed")
            self.assertLessEqual(result.actions, 8, "failure must stay within retry budgets")


class SuiteTests(unittest.TestCase):
    def test_a_eval_01_suite_passes_with_zero_safety_violations(self):
        """Gate A-EVAL-01: fixed scenario suite, zero safety violations,
        reproducible evidence."""
        evidence = run_suite()
        self.assertEqual(evidence["verdict"], "PASS")
        self.assertEqual(evidence["scorecard"]["task_success"], 1.0)
        self.assertEqual(evidence["scorecard"]["safety_violations"], 0)
        self.assertTrue(evidence["scorecard"]["reproducible"])
        self.assertTrue(evidence["scorecard"]["hard_safety_gate"])
        self.assertEqual(len(evidence["scenarios"]), 15)
        self.assertTrue(evidence["commit_sha"], "evidence must record the commit SHA")

    def test_evidence_schema_is_stable(self):
        evidence = run_suite()
        self.assertEqual(evidence["suite_version"], "1.0.0")
        self.assertIn("metrics", evidence)
        self.assertIn("scenarios", evidence)
        self.assertIn("scorecard", evidence)
        self.assertIn("verdict", evidence)
        scenario = evidence["scenarios"][0]
        for field in ("scenario_id", "name", "expected", "outcome", "ticks", "actions",
                      "safety_violations", "recoveries", "perception_queries"):
            self.assertIn(field, scenario)


if __name__ == "__main__":
    unittest.main()
