"""Tests for novi/brain/real_device_gates.py — plan 22 Phase 25 harness."""

from __future__ import annotations

import unittest

from novi.brain.real_device_gates import HardwareGateRunner


class HardwareGateTest(unittest.TestCase):
    def test_hardware_gates_pending_and_deterministic_gates_run(self) -> None:
        report = HardwareGateRunner().report()
        by_id = {g["gate_id"]: g for g in report["gates"]}
        self.assertEqual(len(by_id), 7)
        # H1–H5 honestly report PENDING (no hardware in CI)
        for gate_id in ("H1", "H2", "H3", "H4", "H5"):
            self.assertEqual(by_id[gate_id]["status"], "PENDING")
        # H6 failure honesty passes deterministically
        self.assertEqual(by_id["H6"]["status"], "PASS")
        self.assertIn("clarification", by_id["H6"]["detail"])
        # H7 safety boundary passes deterministically
        self.assertEqual(by_id["H7"]["status"], "PASS")
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["pending_hardware"], 5)
        self.assertEqual(report["failed"], 0)


if __name__ == "__main__":
    unittest.main()
