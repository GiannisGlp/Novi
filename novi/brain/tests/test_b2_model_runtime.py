import unittest

from novi.brain.b2_model_runtime import (
    ModelAdmissionError,
    ModelArtifact,
    ModelCapabilities,
    ModelDescriptor,
    ModelInvocationRequest,
    ModelRuntime,
)


class B2ModelRuntimeTests(unittest.TestCase):
    def descriptor(self) -> ModelDescriptor:
        return ModelDescriptor(
            artifact=ModelArtifact(
                model_id="test-model",
                model_version="1.0.0",
                artifact_digest="sha256:test-artifact",
                uri="local://test-model",
                backend="deterministic",
                runtime_version="1.0.0",
            ),
            capabilities=ModelCapabilities(
                input_schema_version="1.0.0",
                output_schema_version="1.0.0",
            ),
        )

    def request(self, **overrides) -> ModelInvocationRequest:
        values = dict(
            invocation_id="inv-1",
            model_id="test-model",
            model_version="1.0.0",
            artifact_digest="sha256:test-artifact",
            runtime="deterministic",
            runtime_version="1.0.0",
            hardware={"target": "test"},
            input_schema_version="1.0.0",
            output_schema_version="1.0.0",
            started_at="2026-08-19T10:00:00Z",
            input_payload={"value": 42},
        )
        values.update(overrides)
        return ModelInvocationRequest(**values)

    def runtime(self) -> ModelRuntime:
        runtime = ModelRuntime()
        runtime.register(self.descriptor())
        return runtime

    def test_register_and_load_model(self) -> None:
        runtime = self.runtime()
        self.assertEqual(runtime.load("test-model").status, "READY")

    def test_registration_rejects_invalid_digest(self) -> None:
        runtime = ModelRuntime()
        descriptor = self.descriptor()
        invalid = ModelDescriptor(
            artifact=ModelArtifact(
                model_id=descriptor.artifact.model_id,
                model_version=descriptor.artifact.model_version,
                artifact_digest="not-a-digest",
                uri=descriptor.artifact.uri,
                backend=descriptor.artifact.backend,
                runtime_version=descriptor.artifact.runtime_version,
            )
        )
        with self.assertRaises(ModelAdmissionError):
            runtime.register(invalid)

    def test_invoke_returns_structured_result(self) -> None:
        runtime = self.runtime()
        runtime.load("test-model")
        result = runtime.invoke(self.request())
        self.assertEqual(result.status, "completed_on_time")
        self.assertEqual(result.output, {"echo": {"value": 42}})
        self.assertEqual(result.provenance["artifact_digest"], "sha256:test-artifact")

    def test_digest_mismatch_is_rejected(self) -> None:
        runtime = self.runtime()
        with self.assertRaises(Exception):
            runtime.invoke(self.request(artifact_digest="sha256:wrong"))

    def test_version_mismatch_is_rejected(self) -> None:
        runtime = self.runtime()
        with self.assertRaises(Exception):
            runtime.invoke(self.request(model_version="2.0.0"))

    def test_schema_mismatch_is_rejected(self) -> None:
        runtime = self.runtime()
        with self.assertRaises(Exception):
            runtime.invoke(self.request(input_schema_version="2.0.0"))

    def test_unloaded_model_isolated_as_runtime_failure(self) -> None:
        runtime = self.runtime()
        result = runtime.invoke(self.request())
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_class, "ModelInvocationError")

    def test_unload_removes_runtime_readiness(self) -> None:
        runtime = self.runtime()
        runtime.load("test-model")
        self.assertEqual(runtime.unload("test-model").status, "UNLOADED")


if __name__ == "__main__":
    unittest.main()
