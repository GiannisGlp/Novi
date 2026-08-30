"""Contract tests (plan 12, §6.1–6.4, §7)."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from novi.brain.inference.contracts import InferenceBackend, runtime_checkable
from novi.brain.inference.errors import (
    ERROR_BY_CODE,
    ERROR_TAXONOMY,
    InferenceError,
    classify_backend_exception,
)
from novi.brain.inference.request import InferenceRequest, RequestPriority
from novi.brain.inference.response import FinishReason, InferenceResponse


class InferenceRequestTests(unittest.TestCase):
    def test_defaults_are_valid(self) -> None:
        request = InferenceRequest()
        self.assertTrue(request.request_id)
        self.assertEqual(request.priority, RequestPriority.NORMAL)
        self.assertEqual(request.model_hint, "")
        self.assertIsInstance(request.created_at, datetime)

    def test_frozen_immutability(self) -> None:
        from dataclasses import FrozenInstanceError

        request = InferenceRequest()
        with self.assertRaises(FrozenInstanceError):
            request.purpose = "nope"  # type: ignore[misc]

    def test_priority_rank_order(self) -> None:
        self.assertGreater(RequestPriority.CRITICAL.rank, RequestPriority.HIGH.rank)
        self.assertGreater(RequestPriority.HIGH.rank, RequestPriority.NORMAL.rank)
        self.assertGreater(RequestPriority.NORMAL.rank, RequestPriority.LOW.rank)
        self.assertGreater(RequestPriority.LOW.rank, RequestPriority.BACKGROUND.rank)

    def test_deadline_expiry(self) -> None:
        past = datetime.now(timezone.utc) - timedelta(seconds=5)
        request = InferenceRequest(deadline=past)
        self.assertTrue(request.is_expired)
        future = datetime.now(timezone.utc) + timedelta(seconds=5)
        self.assertFalse(InferenceRequest(deadline=future).is_expired)

    def test_no_backend_specific_fields_in_public_contract(self) -> None:
        # Backend specifics must only travel via backend_options.
        request = InferenceRequest(backend_options={"airllm_top_k": 8})
        self.assertEqual(request.backend_options["airllm_top_k"], 8)


class InferenceResponseTests(unittest.TestCase):
    def test_ok_semantics(self) -> None:
        ok = InferenceResponse(
            request_id="r1", model_id="m", backend_id="b", text="hi", finish_reason=FinishReason.STOP
        )
        self.assertTrue(ok.ok)
        err = InferenceResponse(request_id="r1", model_id="m", backend_id="b", finish_reason=FinishReason.ERROR)
        self.assertFalse(err.ok)

    def test_as_dict_roundtrip(self) -> None:
        response = InferenceResponse(
            request_id="r1",
            model_id="m",
            backend_id="b",
            text="hello",
            input_tokens=10,
            output_tokens=20,
            latency_ms=3.0,
            trace_id="t",
        )
        data = response.as_dict()
        self.assertEqual(data["request_id"], "r1")
        self.assertEqual(data["output_tokens"], 20)


class ErrorTaxonomyTests(unittest.TestCase):
    def test_all_taxonomy_codes_have_classes(self) -> None:
        for code in ERROR_TAXONOMY:
            self.assertIn(code, ERROR_BY_CODE, f"missing class for {code}")

    def test_error_carries_code_and_context(self) -> None:
        err = InferenceError("boom", code="test_code", context={"a": 1})
        self.assertEqual(err.code, "test_code")
        self.assertEqual(err.context["a"], 1)
        self.assertEqual(err.as_dict()["error"], "test_code")

    def test_classify_backend_exception_wraps_unknown(self) -> None:
        raw = RuntimeError("airllm exploded")
        translated = classify_backend_exception(raw)
        self.assertIsInstance(translated, InferenceError)
        self.assertIn("airllm exploded", translated.message)
        self.assertEqual(translated.context["source_type"], "RuntimeError")

    def test_classify_passthrough(self) -> None:
        original = InferenceError("typed")
        self.assertIs(classify_backend_exception(original), original)


class BackendProtocolTests(unittest.TestCase):
    def test_inference_backend_is_runtime_checkable(self) -> None:
        self.assertTrue(runtime_checkable(InferenceBackend))

    def test_abstract_backend_rejects_instantiation(self) -> None:
        from novi.brain.inference.backends import AbstractInferenceBackend

        with self.assertRaises(TypeError):
            AbstractInferenceBackend()  # type: ignore[abstract]


if __name__ == "__main__":
    unittest.main()
