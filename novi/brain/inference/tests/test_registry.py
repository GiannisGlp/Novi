"""Registry tests (plan 12, §8 Phase 3, §9 Phase 4, §9.5)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.inference.errors import InferenceConfigurationError, ModelNotFoundError
from novi.brain.inference.registry import ModelRegistry, ModelSpec


class ModelRegistryTests(unittest.TestCase):
    def test_contains_exactly_five_current_aliases(self) -> None:
        registry = ModelRegistry()
        self.assertEqual(
            set(registry.ids()),
            {"qwen3-4b", "qwen3-8b", "nemotron-3.5-lightning", "qwen3.8-27b", "qwen3.8-latest"},
        )
        aliases = {alias for spec in registry.all() for alias in spec.local_aliases}
        self.assertEqual(
            aliases,
            {"qwen3:4b", "qwen3:8b", "nemotron-3.5-lightning:latest", "qwen3.8:27b", "qwen3.8:latest"},
        )

    def test_alias_resolution(self) -> None:
        registry = ModelRegistry()
        spec = registry.get_by_alias("qwen3.8:27b")
        self.assertEqual(spec.id, "qwen3.8-27b")
        self.assertEqual(registry.resolve("qwen3.8:27b").id, "qwen3.8-27b")
        self.assertEqual(registry.resolve("qwen3.8-27b").id, "qwen3.8-27b")

    def test_unknown_alias_raises(self) -> None:
        registry = ModelRegistry()
        with self.assertRaises(ModelNotFoundError):
            registry.get_by_alias("no-such-model:latest")

    def test_no_unverified_model_is_routable(self) -> None:
        # Step 10: register the five aliases WITHOUT enabling new routing.
        registry = ModelRegistry()
        self.assertEqual(registry.routable(), ())

    def test_approved_model_routable_after_resolution(self) -> None:
        registry = ModelRegistry()
        spec = registry.get("qwen3-8b")
        approved = ModelSpec(
            id=spec.id,
            family=spec.family,
            role_candidates=spec.role_candidates,
            backend_preferences=spec.backend_preferences,
            source_type=spec.source_type,
            source_id=spec.source_id,
            local_aliases=spec.local_aliases,
            status="approved",
        )
        registry.register(approved)
        routable = [s.id for s in registry.routable()]
        self.assertIn("qwen3-8b", routable)

    def test_airllm_requires_resolved_identity(self) -> None:
        # §9.5: qwen3.8:27b is NOT AirLLM-eligible until exact artifact
        # identity (architecture/parameter count) is recorded (Step 17).
        registry = ModelRegistry()
        spec = registry.get("qwen3.8-27b")
        self.assertFalse(spec.is_airllm_eligible())
        with self.assertRaises(InferenceConfigurationError):
            spec.resolve_backend_artifact("airllm")

    def test_qwen38_latest_is_not_routable_until_resolved(self) -> None:
        registry = ModelRegistry()
        spec = registry.get("qwen3.8-latest")
        self.assertEqual(spec.resolved, {})
        self.assertNotIn("qwen3.8-latest", [s.id for s in registry.routable()])

    def test_json_roundtrip(self) -> None:
        registry = ModelRegistry()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            registry.to_json(path)
            restored = ModelRegistry.from_json(path)
        self.assertEqual(restored.ids(), registry.ids())
        self.assertEqual(
            restored.get_by_alias("nemotron-3.5-lightning:latest").id,
            "nemotron-3.5-lightning",
        )


class ModelSpecTests(unittest.TestCase):
    def test_backend_artifact_mapping_is_explicit(self) -> None:
        spec = ModelSpec(
            id="test-model",
            backend_artifacts={"airllm": {"path": "/models/test", "architecture": "qwen3.8", "revision": "abc"}},
            resolved={"architecture": "qwen3.8", "parameter_count": 27},
        )
        artifact = spec.resolve_backend_artifact("airllm")
        self.assertEqual(artifact["path"], "/models/test")
        self.assertTrue(spec.is_airllm_eligible())

    def test_never_silently_substitute_checkpoint(self) -> None:
        spec = ModelSpec(id="test-model")
        with self.assertRaises(InferenceConfigurationError):
            spec.resolve_backend_artifact("airllm")


if __name__ == "__main__":
    unittest.main()
