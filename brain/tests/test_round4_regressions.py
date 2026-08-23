"""Regression tests for round-4 brain bug fixes.

  - b2_nemotron: started_at was a hardcoded fabricated timestamp.
  - b1_memory: re-admitting a forgotten (tombstoned) record stayed deleted.
"""

from __future__ import annotations

import unittest

from brain.b1_memory import DeterministicMemoryManager
from brain.b2_model_runtime import ModelArtifact, ModelCapabilities, ModelDescriptor, ModelRuntime
from brain.b2_nemotron import DeterministicNemotronBackend, NemotronAdapter, NemotronInput


class RecordingRuntime(ModelRuntime):
    """Captures the ModelInvocationRequest handed to the runtime."""

    def __init__(self, backend) -> None:
        super().__init__(backend=backend)
        self.last_request = None

    def invoke(self, request):
        self.last_request = request
        return super().invoke(request)


class NemotronStartedAtTests(unittest.TestCase):
    def _runtime(self) -> RecordingRuntime:
        runtime = RecordingRuntime(backend=DeterministicNemotronBackend())
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

    def test_started_at_is_not_hardcoded(self) -> None:
        runtime = self._runtime()
        runtime.load("nvidia/nemotron-3-nano-omni-30b-a3b")
        adapter = NemotronAdapter(runtime, DeterministicNemotronBackend())
        adapter.invoke(
            invocation_id="inv-1",
            artifact_digest="sha256:nemotron-test",
            runtime_name="deterministic",
            runtime_version="1.0.0",
            hardware={"target": "ci"},
            input_data=NemotronInput(text="hi", metadata={}),
        )
        started = runtime.last_request.started_at
        # Must not be the old hardcoded fabricated value.
        self.assertNotEqual(started, "2026-08-19T00:00:00Z")
        # Must be a plausible current-time ISO timestamp.
        self.assertIn("T", started)
        self.assertIn("Z", started)


class MemoryReAdmitTests(unittest.TestCase):
    def _admit(self, manager: DeterministicMemoryManager, content: str = "Alice prefers the living room"):
        return manager.admit(
            memory_type="episode",
            content={"text": content},
            confidence=0.9,
            verification_status="verified",
            privacy_class="internal",
            provenance={"source": "test"},
            entity_refs=("alice",),
        )

    def test_re_admit_after_forget_makes_record_retrievable_again(self) -> None:
        manager = DeterministicMemoryManager()
        first = self._admit(manager)
        self.assertTrue(manager.forget(first.memory_id))
        self.assertIsNone(manager.get(first.memory_id))
        self.assertEqual(manager.active_count, 0)
        # Re-admitting identical content must restore a retrievable record.
        second = self._admit(manager)
        self.assertEqual(second.memory_id, first.memory_id)
        self.assertIsNotNone(manager.get(second.memory_id))
        self.assertEqual(manager.active_count, 1)
        self.assertEqual(manager.deleted_count, 0)


if __name__ == "__main__":
    unittest.main()
