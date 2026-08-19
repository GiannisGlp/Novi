import unittest

from brain.b2_perception_evaluation import (
    DeterministicPerceptionBackend,
    PerceptionCase,
    PerceptionEvaluator,
)


class B2PerceptionEvaluationTests(unittest.TestCase):
    def test_expected_detection_passes(self) -> None:
        case = PerceptionCase(
            case_id="person-001",
            modality="rgb",
            expected_labels=("person",),
            minimum_confidence=0.8,
        )
        result = PerceptionEvaluator(DeterministicPerceptionBackend()).evaluate(case)
        self.assertTrue(result.passed)
        self.assertEqual(result.detected_labels, ("person",))
        self.assertGreaterEqual(result.confidence, 0.8)

    def test_missing_detection_fails(self) -> None:
        class EmptyBackend:
            def infer(self, case):
                return {"labels": [], "confidence": 0.99, "latency_ms": 2.0}

        result = PerceptionEvaluator(EmptyBackend()).evaluate(
            PerceptionCase("person-002", "rgb", ("person",))
        )
        self.assertFalse(result.passed)
        self.assertIn("missing_labels:person", result.failure_reasons)

    def test_low_confidence_fails(self) -> None:
        class LowConfidenceBackend:
            def infer(self, case):
                return {"labels": ["person"], "confidence": 0.4, "latency_ms": 2.0}

        result = PerceptionEvaluator(LowConfidenceBackend()).evaluate(
            PerceptionCase("person-003", "rgb", ("person",), minimum_confidence=0.8)
        )
        self.assertFalse(result.passed)
        self.assertIn("confidence_below_threshold", result.failure_reasons)

    def test_negative_latency_is_invalid(self) -> None:
        class InvalidBackend:
            def infer(self, case):
                return {"labels": [], "confidence": 1.0, "latency_ms": -1.0}

        result = PerceptionEvaluator(InvalidBackend()).evaluate(
            PerceptionCase("invalid-001", "rgb")
        )
        self.assertFalse(result.passed)
        self.assertIn("invalid_latency", result.failure_reasons)


if __name__ == "__main__":
    unittest.main()
