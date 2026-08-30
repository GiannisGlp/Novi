"""AirLLM Mac (MLX) path tests (plan 12, §16-17 Mac validation).

Verified against AirLLM 3.3.0 on macOS: ``AutoModel.from_pretrained`` routes
to ``AirLLMLlamaMlx``, whose ``generate(x, temperature, max_new_tokens)``
takes a token tensor (no ``top_k``) and whose ``__init__`` uses
``layer_shards_saving_path`` (not ``shard_dir``). These tests pin the adapter
and loader to the real Mac API with a fake MLX model.
"""

from __future__ import annotations

import sys
import types
import unittest
from unittest import mock

from novi.brain.inference.airllm.adapter import AirLLMAdapter
from novi.brain.inference.airllm.loader import AirLLMModelHandle, _default_device
from novi.brain.inference.request import InferenceRequest


def _install_fake_mlx() -> None:
    """The base venv has no mlx (Mac-only dep); install a stand-in so the
    adapter's token-array construction is testable off the Mac."""
    if "mlx" in sys.modules:
        return
    core = types.SimpleNamespace(array=lambda x: x)
    module = types.ModuleType("mlx")
    module.core = core
    sys.modules["mlx"] = module
    sys.modules["mlx.core"] = core


class FakeMlxTokenizer:
    def __call__(self, prompt: str) -> dict:
        return {"input_ids": [[1, 2, 3, 4]]}


class FakeMlxModel:
    """Mirrors the AirLLMLlamaMlx surface (model_generate + tokenizer)."""

    def __init__(self, output: str = "mlx answer") -> None:
        self.output = output
        self.tokenizer = FakeMlxTokenizer()
        self.calls: list[dict] = []

    def model_generate(self, x, temperature=0, max_new_tokens=None):
        yield None

    def generate(self, x, temperature=0, max_new_tokens=None, **kwargs):
        self.calls.append({"x": x, "temperature": temperature, "max_new_tokens": max_new_tokens, "kwargs": kwargs})
        return self.output


def _mlx_adapter(output: str = "mlx answer") -> AirLLMAdapter:
    handle = AirLLMModelHandle(
        model_id="qwen3-8b",
        revision="r",
        artifact_path="/models/qwen3-8b",
        shards_dir=None,  # type: ignore[arg-type]
    )
    return AirLLMAdapter(FakeMlxModel(output), handle)


class AirLLMMlxAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        _install_fake_mlx()

    def test_mlx_detection(self) -> None:
        self.assertTrue(AirLLMAdapter._is_mlx(FakeMlxModel()))
        from novi.brain.inference.tests.test_airllm_adapter import FakeAirLLMModel

        self.assertFalse(AirLLMAdapter._is_mlx(FakeAirLLMModel()))

    def test_mlx_generate_uses_token_input_and_temperature(self) -> None:
        model = FakeMlxModel("hello from mlx")
        adapter = _mlx_adapter()
        adapter.model = model
        request = InferenceRequest(messages=[{"role": "user", "content": "hi"}], temperature=0.3, max_output_tokens=16)
        response = adapter.generate(request)
        self.assertEqual(response.text, "hello from mlx")
        self.assertEqual(len(model.calls), 1)
        call = model.calls[0]
        # Token tensor input (not a prompt string), temperature forwarded,
        # no top_k kwarg (the MLX generate has no top_k parameter).
        self.assertEqual(call["temperature"], 0.3)
        self.assertEqual(call["max_new_tokens"], 16)
        self.assertNotIn("top_k", call["kwargs"])

    def test_mlx_error_translation(self) -> None:
        adapter = _mlx_adapter()

        class BrokenMlx(FakeMlxModel):
            def generate(self, x, temperature=0, max_new_tokens=None, **kwargs):
                raise RuntimeError("CUDA out of memory. Tried to allocate 1.00 GiB")

        adapter.model = BrokenMlx()
        from novi.brain.inference.errors import OutOfMemoryError

        with self.assertRaises(OutOfMemoryError):
            adapter.generate(InferenceRequest(messages=[{"role": "user", "content": "x"}]))


class LoaderDeviceTests(unittest.TestCase):
    def test_default_device_is_platform_aware(self) -> None:
        with mock.patch("platform.system", return_value="Darwin"):
            self.assertEqual(_default_device(), "mps")
        with mock.patch("platform.system", return_value="Linux"):
            self.assertEqual(_default_device(), "cuda")


if __name__ == "__main__":
    unittest.main()
