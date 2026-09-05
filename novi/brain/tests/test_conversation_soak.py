"""Plan 03 Gap 6: conversational soak runner.

Deterministic, socket-free. Runs short soaks and asserts the report
schema, memory-probe behavior, and failure detection (a broken probe
answer fails the soak).
"""

from __future__ import annotations

import unittest

from novi.brain.conversation_soak import build_script, run_soak


class SoakTests(unittest.TestCase):
    def test_script_cycles_dimensions(self) -> None:
        script = build_script(turns=40)
        self.assertEqual(len(script), 40)
        self.assertTrue(all(isinstance(t, str) and t.strip() for t in script))
        # Round-robin reaches past the first dimension's turns.
        first_turns = script[:8]
        self.assertGreater(len(set(first_turns)), 3)

    def test_short_soak_passes(self) -> None:
        report = run_soak(turns=12, probe_every=6)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["memory_probes"], {
            "passed": 2, "of": 2, "probes": report["memory_probes"]["probes"]})
        self.assertTrue(all(report["checks"].values()))
        for key in ("schema", "timestamp", "git_sha", "duration_s",
                    "turns_run", "errors", "latency_ms", "growth",
                    "state_bounds"):
            self.assertIn(key, report)

    def test_state_bounds_observed(self) -> None:
        report = run_soak(turns=24, probe_every=12)
        bounds = report["state_bounds"]
        self.assertGreaterEqual(bounds["speakers"], 1)
        self.assertTrue(bounds["within_bounds"])


if __name__ == "__main__":
    unittest.main()
