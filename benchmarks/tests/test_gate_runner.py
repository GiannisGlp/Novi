"""Tests: gate runner — evaluates B1–B5 exit-contract gates (doc 14).

- runs the full deterministic test suite as the regression wall;
- evaluates each gate's machine-checkable evidence requirements;
- writes gate evidence JSON in the doc-14 format;
- OPEN/CLOSED status derived, never hand-written.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


class TestGateRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import tempfile

        from benchmarks.gate_runner import GateRunner

        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        cls.runner = GateRunner(repo_root=REPO_ROOT(), evidence_dir=cls.tmp)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_b3_context_gate_runs_scenarios(self) -> None:
        res = self.runner.run_gate("B3")
        self.assertIn(res.status, ("OPEN", "CLOSED"))
        # B3 requires context-resolution scenarios to exist and pass
        self.assertIn("scenarios", res.evidence)
        self.assertTrue(res.evidence["scenarios"]["total"] >= 3)
        for name in ("anaphora", "addressee", "spatial_recall"):
            self.assertIn(name, res.evidence["scenarios"]["by_name"])

    def test_b2_learning_benchmark_before_after(self) -> None:
        res = self.runner.run_gate("B2")
        self.assertIn("baseline", res.evidence)
        self.assertIn("after", res.evidence)

    def test_b1_autonomy_requires_uptime_evidence(self) -> None:
        res = self.runner.run_gate("B1")
        # No 24h soak has run yet -> must be OPEN with explicit missing evidence
        self.assertEqual(res.status, "OPEN")
        self.assertTrue(res.missing)

    def test_b4_soul_checks(self) -> None:
        res = self.runner.run_gate("B4")
        self.assertIn("identity_persistence", res.evidence)

    def test_b5_soak_requires_hours(self) -> None:
        res = self.runner.run_gate("B5")
        self.assertEqual(res.status, "OPEN")  # no soak archive yet
        self.assertIn("hours_observed", res.evidence)

    def test_evidence_json_written_in_doc14_format(self) -> None:
        res = self.runner.run_gate("B3")
        path = self.tmp / "gate_B3.json"
        data = json.loads(path.read_text())
        self.assertEqual(data["gate"], "B3")
        self.assertIn(data["status"], ("OPEN", "CLOSED"))
        self.assertIn("evidence", data)
        self.assertIn("timestamp", data)


def REPO_ROOT() -> Path:
    return Path(__file__).resolve().parents[1]


def tempfile_TmpDir():
    import tempfile

    return tempfile.TemporaryDirectory()


if __name__ == "__main__":
    unittest.main()
