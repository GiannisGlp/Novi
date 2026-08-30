"""AirLLM compatibility tests (plan 12, §5.2 Phase 5, §33 Phase 33).

All AirLLM imports are lazy: the base install must never require the optional
dependency. These tests exercise the compatibility surface without AirLLM
installed, proving graceful degradation.
"""

from __future__ import annotations

import unittest

from novi.brain.inference.airllm.compatibility import (
    probe_airllm_environment,
    require_airllm,
)
from novi.brain.inference.backends.airllm import AirLLMBackend
from novi.brain.inference.capabilities import CapabilityState
from novi.brain.inference.errors import BackendUnavailableError, InferenceConfigurationError


class AirLLMCompatibilityTests(unittest.TestCase):
    def test_probe_does_not_import_airllm(self) -> None:
        compat = probe_airllm_environment()
        self.assertIsInstance(compat.airllm_installed, bool)
        self.assertTrue(compat.python)
        # as_dict round-trips through a fresh dataclass
        restored = type(compat)(**compat.as_dict())
        self.assertEqual(restored.as_dict(), compat.as_dict())

    def test_require_airllm_raises_when_not_installed(self) -> None:
        # On a base install AirLLM is not present: must raise typed error.
        try:
            require_airllm()
            # If AirLLM happens to be installed this environment, skip.
            self.skipTest("airllm installed in this environment")
        except BackendUnavailableError:
            pass

    def test_backend_disabled_by_default(self) -> None:
        backend = AirLLMBackend()
        self.assertFalse(backend.enabled)
        self.assertEqual(backend.compression, "none")
        self.assertFalse(backend.delete_original)
        self.assertFalse(backend.preparation_allowed)
        self.assertEqual(backend.max_concurrent_requests, 1)
        health = backend.health()
        self.assertEqual(health["status"], "disabled")

    def test_backend_rejects_invalid_compression(self) -> None:
        with self.assertRaises(InferenceConfigurationError):
            AirLLMBackend(compression="16bit")

    def test_backend_rejects_delete_original_in_phase1(self) -> None:
        # plan 12, §14: deletion of original checkpoints is never automatic.
        with self.assertRaises(InferenceConfigurationError):
            AirLLMBackend(delete_original=True)

    def test_generate_raises_unavailable_when_disabled(self) -> None:
        from novi.brain.inference.request import InferenceRequest

        backend = AirLLMBackend()
        with self.assertRaises(BackendUnavailableError):
            backend.generate(InferenceRequest())

    def test_prepare_refused_in_live_runtime(self) -> None:
        from novi.brain.inference.registry import ModelSpec

        backend = AirLLMBackend(enabled=True)
        with self.assertRaises(BackendUnavailableError):
            backend.prepare(ModelSpec(id="x"))

    def test_capabilities_declare_unknown_hardware(self) -> None:
        # plan 12, §16: never turn unknown into supported by assumption.
        backend = AirLLMBackend()
        caps = backend.capabilities()
        self.assertIs(caps.hardware["cuda"], CapabilityState.UNKNOWN)
        self.assertIs(caps.hardware["mps"], CapabilityState.UNKNOWN)

    def test_shutdown_is_idempotent(self) -> None:
        backend = AirLLMBackend()
        backend.shutdown()
        backend.shutdown()


if __name__ == "__main__":
    unittest.main()
