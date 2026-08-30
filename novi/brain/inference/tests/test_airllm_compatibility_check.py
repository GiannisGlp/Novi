"""Per-platform AirLLM compatibility pre-check (user directive 2026-08-30:
AirLLM is a GENERIC resource-optimization backend used everywhere, including
Mac). The pre-check lets the router select AirLLM for ANY approved compatible
model; answers are evidence-backed and ``unknown`` is never promoted to
``supported`` (plan 12 §16/§32).
"""

from __future__ import annotations

import unittest

from novi.brain.inference.airllm.compatibility import architecture_compatibility
from novi.brain.inference.backends.airllm import AirLLMBackend
from novi.brain.inference.capabilities import CapabilityState
from novi.brain.inference.errors import ModelCompatibilityError
from novi.brain.inference.registry import ModelRegistry


class ArchitectureCompatibilityTests(unittest.TestCase):
    def test_mac_mlx_verified_llama(self) -> None:
        # Execution-verified: TinyLlama (LlamaForCausalLM) full pipeline on Mac.
        self.assertIs(
            architecture_compatibility("LlamaForCausalLM", "mps"),
            CapabilityState.SUPPORTED,
        )

    def test_mac_mlx_rejects_qwen3_qk_norm(self) -> None:
        # Execution-verified: Qwen3 (QK-norm) fails at generation on the MLX path.
        self.assertIs(
            architecture_compatibility("Qwen3ForCausalLM", "mps"),
            CapabilityState.UNSUPPORTED,
        )

    def test_mac_mlx_rejects_qwen35_nested_layout(self) -> None:
        self.assertIs(
            architecture_compatibility("Qwen3_5ForConditionalGeneration", "mps"),
            CapabilityState.UNSUPPORTED,
        )

    def test_mac_mlx_unknown_is_never_promoted(self) -> None:
        # Unverified architectures stay unknown (e.g. Mistral on MLX: plausible
        # but not executed -> unknown, never assumed supported).
        self.assertIs(architecture_compatibility("MistralForCausalLM", "mps"), CapabilityState.UNKNOWN)
        self.assertIs(architecture_compatibility("", "mps"), CapabilityState.UNKNOWN)

    def test_cuda_known_and_generic_causal_lm(self) -> None:
        self.assertIs(
            architecture_compatibility("Qwen3_5ForConditionalGeneration", "cuda"),
            CapabilityState.SUPPORTED,
        )
        self.assertIs(architecture_compatibility("SomeNewForCausalLM", "cuda"), CapabilityState.SUPPORTED)

    def test_unknown_backend_is_unknown(self) -> None:
        self.assertIs(architecture_compatibility("LlamaForCausalLM", "unknown"), CapabilityState.UNKNOWN)


class AirLLMBackendCompatTests(unittest.TestCase):
    def test_backend_compat_check_and_validate(self) -> None:
        from novi.brain.inference.airllm.compatibility import AirLLMCompatibility

        backend = AirLLMBackend(enabled=True, compat=AirLLMCompatibility(airllm_installed=True, gpu_backend="mps"))
        registry = ModelRegistry()
        tiny = registry.get("tinyllama-1.1b")
        self.assertIs(backend.check_model_compatibility(tiny), CapabilityState.SUPPORTED)
        backend.validate_model(tiny)  # must not raise

    def test_backend_rejects_qwen3_on_mac(self) -> None:
        from novi.brain.inference.airllm.compatibility import AirLLMCompatibility
        from novi.brain.inference.registry import ModelSpec

        backend = AirLLMBackend(enabled=True, compat=AirLLMCompatibility(airllm_installed=True, gpu_backend="mps"))
        spec = ModelSpec(
            id="qwen3-8b",
            backend_artifacts={"airllm": {"source_id": "Qwen/Qwen3-8B", "architecture": "Qwen3ForCausalLM"}},
            resolved={"architecture": "Qwen3ForCausalLM", "parameter_count": "8b"},
        )
        self.assertIs(backend.check_model_compatibility(spec), CapabilityState.UNSUPPORTED)
        with self.assertRaises(ModelCompatibilityError):
            backend.validate_model(spec)


if __name__ == "__main__":
    unittest.main()
