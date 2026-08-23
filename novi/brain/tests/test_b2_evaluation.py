import unittest

from novi.brain.b2_evaluation import EvaluationCase, InferenceEvaluationHarness


class FakeInvoker:
    def invoke(self, request):
        return type("Result", (), {
            "invocation_id": "inv-eval",
            "model_id": "nemotron-test",
            "model_version": "1.0.0",
            "status": "completed_on_time",
            "output": {"scene": "person", "confidence": 0.9},
            "latency_ms": 12.5,
            "provenance": {
                "artifact_digest": "sha256:test",
                "runtime": "test-runtime",
                "backend": "test-backend",
            },
        })()


class B2EvaluationTests(unittest.TestCase):
    def test_evaluation_records_provenance_and_checks(self):
        harness = InferenceEvaluationHarness(FakeInvoker())
        request = type("Request", (), {
            "input_schema_version": "1.0.0",
            "output_schema_version": "1.0.0",
        })()
        result = harness.evaluate(
            EvaluationCase("scene-1", "image", {"image": "fixture"}, ("scene",)),
            request,
        )
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.output_digest.startswith("sha256:"))
        self.assertEqual(result.provenance.backend, "test-backend")
        self.assertTrue(result.checks["expected:scene"])

    def test_missing_expected_property_fails(self):
        harness = InferenceEvaluationHarness(FakeInvoker())
        request = type("Request", (), {
            "input_schema_version": "1.0.0",
            "output_schema_version": "1.0.0",
        })()
        result = harness.evaluate(
            EvaluationCase("scene-2", "image", {"image": "fixture"}, ("missing",)),
            request,
        )
        self.assertEqual(result.status, "FAIL")
        self.assertFalse(result.checks["expected:missing"])

    def test_serialization_is_structured(self):
        harness = InferenceEvaluationHarness(FakeInvoker())
        request = type("Request", (), {
            "input_schema_version": "1.0.0",
            "output_schema_version": "1.0.0",
        })()
        result = harness.evaluate(EvaluationCase("scene-3", "image", None), request)
        serialized = harness.serialize(result)
        self.assertIn("provenance", serialized)
        self.assertIn("checks", serialized)
        self.assertIn("output_digest", serialized)

    def test_artifact_digest_and_runtime_read_from_request(self):
        """artifact_digest/runtime must come from the request object, not the
        free-form provenance dict (which only carries backend/deadline_ms)."""
        harness = InferenceEvaluationHarness(FakeInvoker())
        request = type("Request", (), {
            "input_schema_version": "1.0.0",
            "output_schema_version": "1.0.0",
            "artifact_digest": "sha256:request-digest",
            "runtime": "request-runtime",
        })()
        result = harness.evaluate(
            EvaluationCase("scene-4", "image", {"image": "fixture"}, ("scene",)),
            request,
        )
        self.assertEqual(result.provenance.artifact_digest, "sha256:request-digest")
        self.assertEqual(result.provenance.runtime, "request-runtime")
        self.assertEqual(result.provenance.backend, "test-backend")


if __name__ == "__main__":
    unittest.main()
