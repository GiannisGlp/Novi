import unittest

from novi.brain.observability import HealthRegistry, MetricsRegistry, RuntimeObservability


class ObservabilityTests(unittest.TestCase):
    def test_health_pass(self) -> None:
        health = HealthRegistry()
        health.set("scheduler", "PASS")
        health.set("contracts", "PASS")
        snapshot = health.snapshot()
        self.assertEqual(snapshot.status, "PASS")
        self.assertEqual(snapshot.checks["scheduler"], "PASS")

    def test_health_failure_has_priority(self) -> None:
        health = HealthRegistry()
        health.set("optional", "WARN")
        health.set("safety", "FAIL")
        self.assertEqual(health.snapshot().status, "FAIL")

    def test_invalid_health_status_rejected(self) -> None:
        health = HealthRegistry()
        with self.assertRaises(ValueError):
            health.set("test", "BROKEN")

    def test_metrics_are_deterministically_snapshot(self) -> None:
        metrics = MetricsRegistry()
        metrics.set("cycle.duration", 1.5, "ms", labels={"component": "brain"})
        snapshot = metrics.snapshot()
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(snapshot[0].value, 1.5)
        self.assertEqual(snapshot[0].labels["component"], "brain")

    def test_diagnostics_preserve_context(self) -> None:
        observability = RuntimeObservability()
        observability.record("ERROR", "component failed", context={"component": "model-runtime"})
        self.assertEqual(len(observability.diagnostics), 1)
        self.assertEqual(observability.diagnostics[0]["level"], "ERROR")
        self.assertEqual(observability.diagnostics[0]["context"]["component"], "model-runtime")


if __name__ == "__main__":
    unittest.main()
