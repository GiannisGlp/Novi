"""Offline operation tests (plan 12, §42 Phase 42, Step 29).

Offline requirement: after model preparation, Novi must execute inference
without Internet access. If a runtime unexpectedly attempts network access
during normal inference, classify this as an integration defect.

CI-safe verification at the runtime level: generation through the mock and
existing (local transport) backends must complete with zero network calls —
``urllib.request.urlopen`` is patched to fail loudly if anything reaches the
network.
"""

from __future__ import annotations

import unittest
from unittest import mock

from novi.brain.inference.backends.existing import ExistingBackend
from novi.brain.inference.backends.mock import MockBackend
from novi.brain.inference.registry import ModelRegistry, ModelSpec
from novi.brain.inference.request import InferenceRequest
from novi.brain.inference.runtime import InferenceRuntime


def _approve(registry: ModelRegistry, model_id: str, backend_preferences: tuple[str, ...]) -> None:
    spec = registry.get(model_id)
    registry.register(
        ModelSpec(
            id=spec.id,
            family=spec.family,
            role_candidates=spec.role_candidates,
            backend_preferences=backend_preferences,
            source_type=spec.source_type,
            source_id=spec.source_id,
            local_aliases=spec.local_aliases,
            status="approved",
        )
    )


class OfflineOperationTests(unittest.TestCase):
    def test_mock_backend_runs_offline(self) -> None:
        registry = ModelRegistry()
        _approve(registry, "qwen3-8b", ("mock",))
        runtime = InferenceRuntime(backends=[MockBackend()], registry=registry)
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network access attempted")) as net:
            response = runtime.generate(
                InferenceRequest(model_hint="qwen3-8b", messages=[{"role": "user", "content": "hi"}])
            )
            net.assert_not_called()
        self.assertTrue(response.ok)
        self.assertEqual(response.backend_id, "mock")

    def test_existing_backend_local_transport_runs_offline(self) -> None:
        registry = ModelRegistry()
        _approve(registry, "qwen3-8b", ("existing",))
        calls: list[object] = []

        def local_transport(payload: dict) -> str:
            calls.append(payload.get("prompt"))
            return "local deterministic answer"

        runtime = InferenceRuntime(
            backends=[ExistingBackend(transport=local_transport)],
            registry=registry,
        )
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network access attempted")) as net:
            response = runtime.generate(
                InferenceRequest(model_hint="qwen3-8b", messages=[{"role": "user", "content": "hi"}])
            )
            net.assert_not_called()
        self.assertEqual(response.text, "local deterministic answer")
        self.assertEqual(len(calls), 1)  # local transport invoked, no network

    def test_hardware_probe_makes_no_network_calls(self) -> None:
        from novi.brain.inference.capabilities import probe_hardware

        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network access attempted")):
            profile = probe_hardware("offline-test")
        self.assertTrue(profile.profile_id)


if __name__ == "__main__":
    unittest.main()
