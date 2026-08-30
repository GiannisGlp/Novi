"""AirLLM lifecycle, shard storage, and integrity tests (plan 12, §8–10, §13, §18)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.inference.airllm.cache import InferenceCache, build_cache_key
from novi.brain.inference.airllm.shards import (
    ShardManifest,
    check_disk_capacity,
    model_dir,
    read_manifest,
    verify_shard_integrity,
    write_health,
    write_manifest,
)
from novi.brain.inference.errors import ShardIntegrityError, StorageCapacityError
from novi.brain.inference.lifecycle import (
    LifecycleTransitionError,
    ModelLifecycle,
    ModelResidency,
    new_model_lifecycle,
    new_residency,
)
from novi.brain.inference.request import InferenceRequest


class LifecycleMachineTests(unittest.TestCase):
    def test_valid_transition(self) -> None:
        machine = new_model_lifecycle()
        machine.transition(ModelLifecycle.REGISTERED)
        machine.transition(ModelLifecycle.VALIDATING)
        machine.transition(ModelLifecycle.READY)
        machine.transition(ModelLifecycle.LOADING)
        machine.transition(ModelLifecycle.LOADED)
        machine.transition(ModelLifecycle.RUNNING)
        self.assertEqual(machine.state, ModelLifecycle.RUNNING)

    def test_forbidden_transition_failed_to_running(self) -> None:
        # plan 12, §18: FAILED -> RUNNING is forbidden.
        machine = new_model_lifecycle()
        machine.transition(ModelLifecycle.REGISTERED)
        machine.transition(ModelLifecycle.VALIDATING)
        machine.transition(ModelLifecycle.FAILED)
        with self.assertRaises(LifecycleTransitionError):
            machine.transition(ModelLifecycle.RUNNING)

    def test_unloaded_can_reenter_registered(self) -> None:
        machine = new_model_lifecycle()
        machine.transition(ModelLifecycle.REGISTERED)
        machine.transition(ModelLifecycle.VALIDATING)
        machine.transition(ModelLifecycle.READY)
        machine.transition(ModelLifecycle.UNLOADED)
        machine.transition(ModelLifecycle.REGISTERED)
        self.assertEqual(machine.state, ModelLifecycle.REGISTERED)

    def test_residency_transitions(self) -> None:
        residency = new_residency()
        residency.transition(ModelResidency.PREPARED)
        residency.transition(ModelResidency.COLD)
        residency.transition(ModelResidency.WARM)
        residency.transition(ModelResidency.ACTIVE)
        residency.transition(ModelResidency.DRAINING)
        self.assertEqual(residency.state, ModelResidency.DRAINING)

    def test_snapshot_records_transitions(self) -> None:
        machine = new_model_lifecycle()
        machine.transition(ModelLifecycle.REGISTERED)
        snapshot = machine.snapshot()
        self.assertEqual(snapshot["state"], "REGISTERED")
        self.assertEqual(len(snapshot["transitions"]), 1)


class ShardStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.shards = self.root / "shards"
        self.shards.mkdir()
        (self.shards / "shard-0.bin").write_bytes(b"layer-0-data")
        (self.shards / "shard-1.bin").write_bytes(b"layer-1-data")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_manifest_roundtrip(self) -> None:
        manifest = ShardManifest(
            model_id="qwen3.8-27b",
            revision="abc123",
            architecture="qwen3.8",
            shard_count=2,
            shard_sizes=(11, 11),
            total_bytes=22,
        )
        path = self.root / "manifest.json"
        write_manifest(manifest, path)
        restored = read_manifest(path)
        self.assertEqual(restored.model_id, "qwen3.8-27b")
        self.assertEqual(restored.total_bytes, 22)
        self.assertEqual(restored.shard_sizes, (11, 11))

    def test_integrity_verification_passes_with_checksums(self) -> None:
        import hashlib

        manifest = ShardManifest(
            model_id="m",
            shard_count=2,
            checksums={
                "shard-0.bin": hashlib.sha256(b"layer-0-data").hexdigest(),
                "shard-1.bin": hashlib.sha256(b"layer-1-data").hexdigest(),
            },
        )
        verified = verify_shard_integrity(self.shards, manifest)
        self.assertEqual(verified.status, "prepared")

    def test_missing_shard_raises(self) -> None:
        manifest = ShardManifest(model_id="m", shard_count=3)
        with self.assertRaises(ShardIntegrityError):
            verify_shard_integrity(self.shards, manifest)

    def test_corrupt_shard_raises(self) -> None:
        import hashlib

        manifest = ShardManifest(
            model_id="m",
            shard_count=2,
            checksums={
                "shard-0.bin": hashlib.sha256(b"WRONG").hexdigest(),
                "shard-1.bin": hashlib.sha256(b"layer-1-data").hexdigest(),
            },
        )
        with self.assertRaises(ShardIntegrityError):
            verify_shard_integrity(self.shards, manifest)

    def test_integrity_verification_nested_layout(self) -> None:
        # The Mac/MLX path writes shards under splitted_model/ — discovery must
        # be recursive and checksum keys relative (plan 12 §15).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "splitted_model"
            nested.mkdir()
            (nested / "model.layers.0.mlx.npz").write_bytes(b"layer-0-data")
            (nested / "model.layers.1.mlx.npz").write_bytes(b"layer-1-data")
            import hashlib

            manifest = ShardManifest(
                model_id="m",
                shard_count=2,
                checksums={
                    "splitted_model/model.layers.0.mlx.npz": hashlib.sha256(b"layer-0-data").hexdigest(),
                    "splitted_model/model.layers.1.mlx.npz": hashlib.sha256(b"layer-1-data").hexdigest(),
                },
            )
            verified = verify_shard_integrity(root, manifest)
            self.assertEqual(verified.status, "prepared")

    def test_insufficient_disk_refuses_with_typed_error(self) -> None:
        # plan 12, §14: refuse preparation, emit diagnostic, delete nothing.
        with self.assertRaises(StorageCapacityError):
            check_disk_capacity(self.root, required_bytes=10**30)

    def test_model_dir_layout(self) -> None:
        path = model_dir(self.root, "qwen3.8-27b")
        self.assertEqual(path, self.root / "models" / "airllm" / "qwen3.8-27b")

    def test_health_written(self) -> None:
        manifest = ShardManifest(model_id="m")
        health_path = self.root / "health.json"
        write_health(manifest, health_path, healthy=True, note="ok")
        import json

        payload = json.loads(health_path.read_text(encoding="utf-8"))
        self.assertTrue(payload["healthy"])
        self.assertEqual(payload["model_id"], "m")


class CacheIsolationTests(unittest.TestCase):
    def test_cache_key_includes_identity(self) -> None:
        request = InferenceRequest(conversation_id="conv-1", messages=[{"role": "user", "content": "hi"}])
        key = build_cache_key(
            model_revision="rev-a",
            backend="airllm",
            tokenizer_revision="tok-a",
            request=request,
        )
        other = build_cache_key(
            model_revision="rev-b",
            backend="airllm",
            tokenizer_revision="tok-a",
            request=request,
        )
        self.assertNotEqual(key.digest(), other.digest())

    def test_conversation_isolation(self) -> None:
        a = InferenceRequest(conversation_id="conv-a", messages=[{"role": "user", "content": "x"}])
        b = InferenceRequest(conversation_id="conv-b", messages=[{"role": "user", "content": "x"}])
        # Same content, different session: cache key digests must differ.
        key_a = build_cache_key(model_revision="r", backend="b", tokenizer_revision="t", request=a)
        key_b = build_cache_key(model_revision="r", backend="b", tokenizer_revision="t", request=b)
        self.assertNotEqual(key_a.digest(), key_b.digest())

    def test_cache_hit_and_miss(self) -> None:
        cache = InferenceCache(capacity=4)
        request = InferenceRequest(conversation_id="c", messages=[{"role": "user", "content": "q"}])
        key = build_cache_key(model_revision="r", backend="b", tokenizer_revision="t", request=request)
        self.assertIsNone(cache.get(key))
        cache.put(key, {"text": "answer"})
        self.assertEqual(cache.get(key)["text"], "answer")
        stats = cache.stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)


if __name__ == "__main__":
    unittest.main()
