import tempfile
import unittest
from pathlib import Path

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from brain.observability import (
    FAIL,
    INFO,
    PASS,
    UNKNOWN,
    WARN,
    Diagnostics,
    HealthCheck,
    HealthMonitor,
    MetricRegistry,
    aggregate_health,
)
from brain.engine import MacBrain, MacBrainConfig
from brain.tests.test_mac_brain import FakeCamera


class AggregationTests(unittest.TestCase):
    def test_pass_when_healthy(self):
        self.assertEqual(aggregate_health([PASS, PASS]), PASS)

    def test_warn_surfaces_when_no_fail(self):
        self.assertEqual(aggregate_health([PASS, WARN, UNKNOWN]), WARN)

    def test_fail_dominates(self):
        self.assertEqual(aggregate_health([PASS, WARN, FAIL, UNKNOWN]), FAIL)

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_health([PASS, "BOGUS"])


class MetricRegistryTests(unittest.TestCase):
    def test_deterministic_ordering_and_labels(self):
        m = MetricRegistry()
        m.set("b", 2, unit="s")
        m.set("a", 1, unit="count", labels={"who": "alice"})
        m.inc("a", 3, unit="count", labels={"who": "alice"})
        snap = m.snapshot()
        self.assertEqual([s["name"] for s in snap], ["a", "b"])  # sorted by name
        self.assertEqual(snap[0]["value"], 4.0)  # 1 + 3
        self.assertEqual(snap[0]["labels"], {"who": "alice"})

    def test_labels_normalized_to_str(self):
        m = MetricRegistry()
        m.set("x", 1, labels={"n": 5})
        self.assertEqual(m.snapshot()[0]["labels"], {"n": "5"})


class DiagnosticsTests(unittest.TestCase):
    def test_structured_record(self):
        d = Diagnostics(capacity=10)
        d.add(WARN, "low battery", {"level": 0.1})
        snap = d.snapshot()
        self.assertEqual(snap[0]["severity"], WARN)
        self.assertEqual(snap[0]["message"], "low battery")
        self.assertEqual(snap[0]["context"], {"level": 0.1})
        self.assertIn("wallclock", snap[0])
        self.assertIn("monotonic", snap[0])

    def test_invalid_severity_coerced(self):
        d = Diagnostics()
        d.add("BOGUS", "x")
        self.assertEqual(d.snapshot()[0]["severity"], INFO)


class HealthMonitorTests(unittest.TestCase):
    def test_aggregate_pass(self):
        m = HealthMonitor([HealthCheck("a", "a", lambda b: (PASS, "ok")), HealthCheck("b", "b", lambda b: (PASS, "ok"))])
        snap = m.run(object())
        self.assertEqual(snap.status, PASS)
        self.assertEqual(len(snap.checks), 2)
        self.assertIn("wallclock", snap.snapshot())
        self.assertIn("monotonic", snap.snapshot())

    def test_check_error_becomes_fail(self):
        m = HealthMonitor([HealthCheck("bad", "bad", lambda b: (_ for _ in ()).throw(RuntimeError("boom")))])
        snap = m.run(object())
        self.assertEqual(snap.status, FAIL)
        self.assertIn("check_error", snap.checks[0]["detail"])


class BrainObservabilityTests(unittest.TestCase):
    class PersonBackend(DeterministicPerceptionBackend):
        def detect(self, frame):
            return (Detection("person", 0.8, (0, 0, 1, 1)),)

    def _brain(self, db=None):
        return MacBrain(camera=FakeCamera(), perception=SpecialistPerception(self.PersonBackend()), store_path=db, config=MacBrainConfig(curiosity_enabled=False))

    def test_step_reports_health_and_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            b = self._brain(str(Path(td) / "b.db"))
            b.start()
            result = b.step()
            b.stop()
            self.assertIn("observability", result)
            self.assertEqual(result["observability"]["health"]["status"], PASS)
            self.assertIn("metrics", result["observability"])
            self.assertIn("observability.health", [e["event_type"] for e in b.events])

    def test_health_report_pass_with_durable_store(self):
        with tempfile.TemporaryDirectory() as td:
            b = self._brain(str(Path(td) / "b.db"))
            b.start()
            report = b.health_report()
            b.stop()
            self.assertEqual(report["status"], PASS)
            self.assertIn("observability.health", [e["event_type"] for e in b.events])

    def test_warn_when_governance_disabled(self):
        b = self._brain()  # non-durable memory -> governance disabled -> WARN
        b.start()
        result = b.step()
        b.stop()
        self.assertEqual(result["observability"]["health"]["status"], WARN)

    def test_diagnostic_emits(self):
        b = self._brain()
        b.start()
        b.add_diagnostic("WARN", "temp high", {"t": 45})
        b.stop()
        self.assertIn("observability.diagnostic", [e["event_type"] for e in b.events])


if __name__ == "__main__":
    unittest.main()
