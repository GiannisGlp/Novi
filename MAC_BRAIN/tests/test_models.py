import unittest

from MAC_BRAIN.models import MacModelProvider, MacModelSpec


class MacModelProviderTests(unittest.TestCase):
    def test_local_callable_runs_through_existing_runtime(self) -> None:
        spec = MacModelSpec(
            capability="multimodal_reasoning",
            model_id="local-test-model",
            model_version="1.0.0",
            artifact_digest="sha256:local-test",
            runtime="test-local",
            runtime_version="1.0.0",
            modalities=("text", "image"),
        )
        provider = MacModelProvider(spec, lambda payload: {"decision": "observe", "keys": sorted(payload)})
        result = provider.invoke({"text": "look at the room"}, invocation_id="mac-model-test")
        self.assertEqual(provider.health(), "READY")
        self.assertEqual(result.status, "completed_on_time")
        self.assertEqual(result.output["decision"], "observe")
        self.assertEqual(result.provenance["backend"], "test-local")

    def test_model_backend_failure_is_contained(self) -> None:
        spec = MacModelSpec(
            capability="vision",
            model_id="failing-model",
            model_version="1.0.0",
            artifact_digest="sha256:failing",
            runtime="test-local",
            runtime_version="1.0.0",
        )
        provider = MacModelProvider(spec, lambda payload: (_ for _ in ()).throw(RuntimeError("boom")))
        result = provider.invoke({}, invocation_id="mac-model-failure")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_class, "RuntimeError")
