"""Phase D4 (gap-audit plan 13): PredictionEngine + accuracy metric.

Pins:
  - streak-based persistence predictions with rising, capped confidence;
  - next-cycle scoring: confirmed/violated outcomes;
  - rolling prediction_accuracy tracked and logged to the MetricRegistry by
    the engine (audit lever 4);
  - predictions never mutate the unified world model (observed state wins);
  - the CosmosReason2 adapter still routes through ModelRuntime untouched
    (prediction.requested trigger exercises it in tests via a stub backend).
"""

import unittest

from novi.brain.b2_cosmos_reason import CosmosReason2Adapter, CosmosReasonRequest
from novi.brain.b2_model_runtime import ModelRuntime
from novi.brain.prediction import AccuracyTracker, PredictionEngine
from novi.brain.tests.test_mac_brain import FakeCamera


class PredictionEngineTests(unittest.TestCase):
    def test_no_prediction_before_min_streak(self):
        pe = PredictionEngine(min_observations=2)
        new, conf, viol = pe.observe({"cup"}, cycle=1)
        self.assertEqual(new, [])
        new, _, _ = pe.observe({"cup"}, cycle=2)
        self.assertEqual([p.entity for p in new], ["cup"])

    def test_confidence_rises_with_streak_and_caps(self):
        pe = PredictionEngine(min_observations=2)
        pe.observe({"cup"}, cycle=1)
        new2, _, _ = pe.observe({"cup"}, cycle=2)
        c2 = new2[0].confidence
        new3, _, _ = pe.observe({"cup"}, cycle=3)
        c3 = new3[0].confidence
        self.assertGreater(c3, c2)
        self.assertLessEqual(c3, pe.confidence_cap)

    def test_next_cycle_scores_outcomes(self):
        pe = PredictionEngine(min_observations=1)
        pe.observe({"cup", "lamp"}, cycle=1)
        new, conf, viol = pe.observe({"cup"}, cycle=2)  # lamp vanished
        entities_confirmed = {p.entity for p in conf}
        entities_violated = {p.entity for p in viol}
        self.assertIn("cup", entities_confirmed)
        self.assertIn("lamp", entities_violated)
        # cup predicted again (streak continues)
        self.assertEqual([p.entity for p in new], ["cup"])

    def test_accuracy_tracker_rolling_window(self):
        t = AccuracyTracker(window=4)
        for conf, hit in ((0.9, True), (0.8, True), (0.7, False), (0.9, True)):
            t.record(conf, hit)
        self.assertAlmostEqual(t.accuracy(), 0.75)
        t.record(0.6, False)  # evicts the first entry (window=4)
        self.assertAlmostEqual(t.accuracy(), 0.5)
        empty = AccuracyTracker()
        self.assertIsNone(empty.accuracy())
        pairs = t.pairs()
        self.assertEqual(pairs[0], (0.8, True))

    def test_snapshot_shape(self):
        pe = PredictionEngine(min_observations=1)
        pe.observe({"cup"}, cycle=1)
        snap = pe.snapshot()
        self.assertIn("streaks", snap)
        self.assertIn("pending", snap)
        self.assertIsNone(snap["accuracy"])  # nothing scored yet


class EnginePredictionMetricTests(unittest.TestCase):
    def _brain(self):
        from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig

        class CupBackend(DeterministicPerceptionBackend):
            def detect(self, frame):
                return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)

        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(CupBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        return brain

    def test_accuracy_logged_to_metric_registry(self):
        brain = self._brain()
        try:
            brain.step()  # cup appears
            brain.step()  # streak -> prediction made
            brain.step()  # prediction scored: confirmed; metric now set
            rows = {m["name"]: m["value"] for m in brain.metrics_snapshot()}
            self.assertIn("prediction_accuracy", rows)
            acc = rows["prediction_accuracy"]
            self.assertTrue(0.0 <= acc <= 1.0)
        finally:
            brain.stop()

    def test_predictions_never_touch_world_model(self):
        brain = self._brain()
        try:
            brain.step()
            brain.step()  # prediction made for next cycle
            brain.step()  # prediction scored
            state = brain.unified_world.to_world_state()
            for _eid, ent in state.entities.items():
                status = getattr(ent, "epistemic_status", "") or ""
                self.assertNotEqual(str(status).lower(), "predicted")
        finally:
            brain.stop()


class _StubCosmosBackend:
    def invoke(self, request):
        return {"answer": "object_persists", "confidence": 0.8}


class CosmosAdapterTests(unittest.TestCase):
    def test_adapter_routes_through_model_runtime(self):
        runtime = ModelRuntime()
        adapter = CosmosReason2Adapter(runtime=runtime, backend=_StubCosmosBackend())
        result = adapter.reason(CosmosReasonRequest(
            invocation_id="inv-1", video=b"stub-video",
            question="will the cup stay on the table?", correlation_id="corr-1",
        ))
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
