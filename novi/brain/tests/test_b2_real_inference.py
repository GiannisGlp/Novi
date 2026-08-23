import unittest

from novi.brain.b2_model_runtime import ModelInvocationRequest, ModelRuntime
from novi.brain.b2_real_inference import InferencePolicy, RealModelInvoker


class FakeRealBackend:
    def __init__(self, output=None, error=None, elapsed_marker=False):
        self.output = {"decision": "observe"} if output is None else output
        self.error = error
        self.elapsed_marker = elapsed_marker

    def health(self, model_id: str) -> str:
        return "READY"

    def invoke(self, request):
        if self.error:
            raise self.error
        return self.output


class B2RealInferenceTests(unittest.TestCase):
    def request(self):
        return ModelInvocationRequest(
            invocation_id="b2-3-test",
            model_id="nemotron-test",
            model_version="3.0.0",
            artifact_digest="sha256:test",
            runtime="test-real-backend",
            runtime_version="1.0.0",
            hardware={"target": "test"},
            input_schema_version="1.0.0",
            output_schema_version="1.0.0",
            started_at="2026-08-19T12:00:00Z",
            input_payload={"text": "observe the room"},
        )

    def test_health_is_exposed(self):
        invoker = RealModelInvoker(ModelRuntime(), FakeRealBackend())
        self.assertEqual(invoker.health("nemotron-test"), "READY")

    def test_real_backend_result_is_structured(self):
        invoker = RealModelInvoker(ModelRuntime(), FakeRealBackend())
        result = invoker.invoke(self.request())
        self.assertEqual(result.status, "completed_on_time")
        self.assertEqual(result.output["decision"], "observe")
        self.assertIn("backend", result.provenance)

    def test_non_structured_output_is_rejected(self):
        invoker = RealModelInvoker(ModelRuntime(), FakeRealBackend(output="free text"))
        result = invoker.invoke(self.request())
        self.assertEqual(result.status, "invalid_output")

    def test_backend_failure_is_contained(self):
        invoker = RealModelInvoker(ModelRuntime(), FakeRealBackend(error=RuntimeError("backend unavailable")))
        result = invoker.invoke(self.request())
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_class, "RuntimeError")

    def test_deadline_policy_is_explicit(self):
        policy = InferencePolicy(deadline_ms=5000)
        self.assertEqual(policy.deadline_ms, 5000)
        self.assertTrue(policy.require_structured_output)


if __name__ == "__main__":
    unittest.main()
