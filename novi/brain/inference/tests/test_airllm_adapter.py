"""AirLLM adapter tests (plan 12, §11 Phase 6, §26 Phase 26).

Exercise the adapter's request/response translation and error translation with
a fake model — no AirLLM dependency required. Raw AirLLM exceptions must never
leak through the adapter (plan 12, §6.4).
"""

from __future__ import annotations

import unittest

from novi.brain.inference.airllm.adapter import AirLLMAdapter
from novi.brain.inference.airllm.loader import AirLLMModelHandle
from novi.brain.inference.errors import (
    ContextLimitError,
    GenerationError,
    OutOfMemoryError,
    TokenizationError,
)
from novi.brain.inference.request import InferenceRequest
from novi.brain.inference.response import FinishReason


class FakeAirLLMModel:
    def __init__(self, output="fake answer", error: Exception | None = None) -> None:
        self.output = output
        self.error = error

    def generate(self, prompt: str, max_new_tokens: int = 128, top_k: int = 1) -> object:
        if self.error is not None:
            raise self.error
        return self.output


def _adapter(
    output="fake answer", error: Exception | None = None, *, context_limit: int | None = None
) -> AirLLMAdapter:
    handle = AirLLMModelHandle(
        model_id="qwen3.8-27b",
        revision="rev-1",
        artifact_path="/models/qwen3.8-27b",
        shards_dir=None,  # type: ignore[arg-type]
    )
    return AirLLMAdapter(FakeAirLLMModel(output, error), handle, context_limit=context_limit)


class AirLLMAdapterTests(unittest.TestCase):
    def test_generate_translates_success(self) -> None:
        request = InferenceRequest(messages=[{"role": "user", "content": "hello"}])
        response = _adapter("hi there").generate(request)
        self.assertEqual(response.model_id, "qwen3.8-27b")
        self.assertEqual(response.backend_id, "airllm")
        self.assertEqual(response.text, "hi there")
        self.assertEqual(response.finish_reason, FinishReason.STOP)
        self.assertGreater(response.output_tokens, 0)
        self.assertTrue(response.provider_metadata["airllm"])

    def test_empty_request_raises_generation_error(self) -> None:
        request = InferenceRequest()
        with self.assertRaises(GenerationError):
            _adapter().generate(request)

    def test_oom_error_translation(self) -> None:
        request = InferenceRequest(messages=[{"role": "user", "content": "x"}])
        oom = RuntimeError("CUDA out of memory. Tried to allocate 4.00 GiB")
        with self.assertRaises(OutOfMemoryError):
            _adapter(error=oom).generate(request)

    def test_context_limit_raised_before_generation(self) -> None:
        request = InferenceRequest(messages=[{"role": "user", "content": "x" * 500_000}])
        with self.assertRaises(ContextLimitError):
            _adapter(context_limit=1000).generate(request)

    def test_dict_output_decoding(self) -> None:
        request = InferenceRequest(messages=[{"role": "user", "content": "q"}])
        adapter = _adapter({"generated_text": "structured answer"})
        response = adapter.generate(request)
        self.assertEqual(response.text, "structured answer")

    def test_unexpected_output_shape_is_protocol_error(self) -> None:
        from novi.brain.inference.errors import BackendProtocolError

        request = InferenceRequest(messages=[{"role": "user", "content": "q"}])
        adapter = _adapter({"unexpected": "shape"})
        with self.assertRaises(BackendProtocolError):
            adapter.generate(request)

    def test_generic_exception_never_leaks_raw(self) -> None:
        request = InferenceRequest(messages=[{"role": "user", "content": "q"}])
        adapter = _adapter(error=ValueError("tokenizer exploded"))
        with self.assertRaises(TokenizationError):
            adapter.generate(request)

    def test_streaming_unsupported_raises_protocol_error(self) -> None:
        from novi.brain.inference.errors import BackendProtocolError

        request = InferenceRequest(messages=[{"role": "user", "content": "q"}])
        with self.assertRaises(BackendProtocolError):
            adapter = _adapter()
            adapter.stream(request)  # raises synchronously before iteration


if __name__ == "__main__":
    unittest.main()
