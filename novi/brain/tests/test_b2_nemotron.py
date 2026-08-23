import unittest

from novi.brain.b2_model_runtime import ModelArtifact, ModelCapabilities, ModelDescriptor, ModelRuntime
from novi.brain.b2_nemotron import DeterministicNemotronBackend, NemotronAdapter, NemotronInput


class B2NemotronAdapterTests(unittest.TestCase):
    def runtime(self) -> ModelRuntime:
        runtime = ModelRuntime(backend=DeterministicNemotronBackend())
        runtime.register(
            ModelDescriptor(
                artifact=ModelArtifact(
                    model_id="nvidia/nemotron-3-nano-omni-30b-a3b",
                    model_version="3.0",
                    artifact_digest="sha256:nemotron-test",
                    uri="local://nemotron-3-nano-omni",
                    backend="deterministic",
                    runtime_version="1.0.0",
                ),
                capabilities=ModelCapabilities(
                    modalities=("text", "image", "audio", "video"),
                    input_schema_version="1.0.0",
                    output_schema_version="1.0.0",
                ),
            )
        )
        return runtime

    def test_multimodal_input_is_normalized(self) -> None:
        runtime = self.runtime()
        runtime.load("nvidia/nemotron-3-nano-omni-30b-a3b")
        adapter = NemotronAdapter(runtime, DeterministicNemotronBackend())
        result = adapter.invoke(
            invocation_id="nemotron-inv-1",
            artifact_digest="sha256:nemotron-test",
            runtime_name="deterministic",
            runtime_version="1.0.0",
            hardware={"target": "ci"},
            input_data=NemotronInput(
                text="Describe the scene",
                images=("image-1",),
                audio=("audio-1",),
                video=("video-1",),
                metadata={"source": "integration-test"},
            ),
        )
        self.assertEqual(result.status, "completed_on_time")
        self.assertEqual(result.output["image_count"], 1)
        self.assertEqual(result.output["audio_count"], 1)
        self.assertEqual(result.output["video_count"], 1)

    def test_adapter_uses_canonical_model_identity(self) -> None:
        runtime = self.runtime()
        adapter = NemotronAdapter(runtime, DeterministicNemotronBackend())
        self.assertEqual(adapter.model_id, "nvidia/nemotron-3-nano-omni-30b-a3b")
        self.assertEqual(adapter.model_version, "3.0")


if __name__ == "__main__":
    unittest.main()
