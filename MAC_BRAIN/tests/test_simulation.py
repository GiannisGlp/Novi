"""Tests for `MAC_BRAIN/simulation.py` (simpy skill).

Covers deterministic edge cases, conservation, seed reproducibility, the
expected throughput/latency tradeoff, and replication-level estimates.
"""

import unittest

from MAC_BRAIN.simulation import STAGES, ClosedLoopSimulation, replicate


class ClosedLoopSimulationTest(unittest.TestCase):
    def test_zero_service_completes_all_admitted(self) -> None:
        # Zero service time: every admitted entity completes instantly.
        s = ClosedLoopSimulation(horizon=100.0, entity_cap=1000, mean_arrival=1.0, mean_service=0.0, seed=1)
        r = s.run()
        self.assertEqual(r["completed"], r["admitted"])
        self.assertEqual(r["unfinished"], 0)
        self.assertEqual(r["mean_latency"], 0.0)
        self.assertEqual(r["max_latency"], 0.0)

    def test_conservation(self) -> None:
        s = ClosedLoopSimulation(horizon=200.0, entity_cap=5000, mean_arrival=2.0, mean_service=1.0, seed=7)
        r = s.run()
        self.assertEqual(r["completed"] + r["unfinished"], r["admitted"])

    def test_deterministic_reproducibility(self) -> None:
        a = ClosedLoopSimulation(seed=42).run()
        b = ClosedLoopSimulation(seed=42).run()
        self.assertEqual(a, b)

    def test_throughput_drops_as_service_increases(self) -> None:
        light = ClosedLoopSimulation(horizon=200.0, entity_cap=5000, mean_arrival=1.0, mean_service=0.5, seed=3).run()
        heavy = ClosedLoopSimulation(horizon=200.0, entity_cap=5000, mean_arrival=1.0, mean_service=3.0, seed=3).run()
        self.assertGreater(light["throughput_per_time"], heavy["throughput_per_time"])

    def test_latency_increases_with_load(self) -> None:
        low = ClosedLoopSimulation(horizon=200.0, entity_cap=5000, mean_arrival=5.0, mean_service=1.0, seed=5).run()
        high = ClosedLoopSimulation(horizon=200.0, entity_cap=5000, mean_arrival=0.5, mean_service=1.0, seed=5).run()
        self.assertLess(low["mean_latency"], high["mean_latency"])

    def test_stages_match_runtime_loop(self) -> None:
        # The model's stage order mirrors the runtime loop's first/last stages.
        self.assertEqual(STAGES[0], "perception")
        self.assertEqual(STAGES[-1], "social")
        self.assertEqual(len(STAGES), 11)


class ReplicateTest(unittest.TestCase):
    def test_replicate_returns_means(self) -> None:
        r = replicate(replications=3, horizon=100.0, entity_cap=1000, mean_arrival=2.0, mean_service=1.0, base_seed=11)
        self.assertEqual(r["replications"], 3)
        self.assertIn("mean_completed", r)
        self.assertIn("mean_throughput_per_time", r)

    def test_replicate_refuses_single_replication(self) -> None:
        with self.assertRaises(ValueError):
            replicate(replications=1)


if __name__ == "__main__":
    unittest.main()
