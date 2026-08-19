import unittest

from brain.b2_cosmos_reason import CosmosReason2Adapter, CosmosReasonRequest
from brain.b2_model_runtime import ModelRuntime, ModelResult


class FakeCosmosBackend:
    def invoke(self, request):
        return {
            "answer": "wait because the moving object crosses the robot path",
            "objects": [{"label": "person", "position": [1.0, 2.0, 0.0]}],
            "confidence": 0.91,
        }


class FailingCosmosBackend:
    def invoke(self, request):
        raise TimeoutError("backend timeout")


class B2CosmosReasonTests(unittest.TestCase):
    def test_physical_reasoning_returns_evidence_without_action_authority(self):
        adapter = CosmosReason2Adapter(ModelRuntime(), FakeCosmosBackend())
        result = adapter.reason(
            CosmosReasonRequest(
                invocation_id="cosmos-test-1",
                video="simulated://crossing-person",
                question="What should the robot consider before moving?",
                timestamp_context=(0.0, 0.5, 1.0),
            )
        )
        self.assertEqual(result.status, "completed_on_time")
        evidence = adapter.to_evidence(result)
        self.assertEqual(evidence["kind"], "physical_reasoning")
        self.assertNotIn("action", evidence)
        self.assertNotIn("motor_command", evidence)
        self.assertEqual(evidence["payload"]["objects"][0]["label"], "person")

    def test_backend_failure_is_contained(self):
        adapter = CosmosReason2Adapter(ModelRuntime(), FailingCosmosBackend())
        result = adapter.reason(
            CosmosReasonRequest(
                invocation_id="cosmos-test-2",
                video="simulated://failure",
                question="Describe the physical situation",
            )
        )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_class, "TimeoutError")

    def test_failed_result_cannot_become_evidence(self):
        result = ModelResult(
            invocation_id="cosmos-test-3",
            model_id="cosmos-reason2",
            model_version="2.0",
            status="failed",
        )
        with self.assertRaises(ValueError):
            CosmosReason2Adapter.to_evidence(result)


if __name__ == "__main__":
    unittest.main()
