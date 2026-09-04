"""Tests for the OpenAI-compatible chat server adapter.

The brain's LLM wire clients must not be locked to Ollama's native API:
this adapter speaks ``/v1`` (chat completions + model list), which Ollama,
llama.cpp, vLLM, and TensorRT-LLM frontends all serve. HTTP is mocked at
the urlopen boundary so these run anywhere (no server, no sockets).
"""

from __future__ import annotations

import io
import json
import unittest
from unittest import mock

from novi.brain.models.chat_server import OpenAICompatibleChatServer


def _response(payload: object) -> mock.MagicMock:
    resp = mock.MagicMock()
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    resp.__enter__.return_value = resp
    return resp


class ChatServerProbeTests(unittest.TestCase):
    def _server(self) -> OpenAICompatibleChatServer:
        return OpenAICompatibleChatServer("http://localhost:11434")

    def test_probe_true_when_model_listed(self) -> None:
        with mock.patch(
            "urllib.request.urlopen",
            return_value=_response({"data": [{"id": "qwen3:8b"}, {"id": "other"}]}),
        ) as opened:
            self.assertTrue(self._server().probe("qwen3:8b"))
        url = opened.call_args.args[0].full_url
        self.assertTrue(url.endswith("/v1/models"))

    def test_probe_false_when_model_missing(self) -> None:
        with mock.patch(
            "urllib.request.urlopen",
            return_value=_response({"data": [{"id": "other"}]}),
        ):
            self.assertFalse(self._server().probe("qwen3:8b"))

    def test_probe_false_when_server_down(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=OSError("refused")):
            self.assertFalse(self._server().probe("qwen3:8b"))


class ChatServerChatTests(unittest.TestCase):
    def _server(self) -> OpenAICompatibleChatServer:
        return OpenAICompatibleChatServer("http://localhost:11434")

    def test_chat_returns_message_content(self) -> None:
        with mock.patch(
            "urllib.request.urlopen",
            return_value=_response({"choices": [{"message": {"content": "hello there"}}]}),
        ) as opened:
            reply = self._server().chat(model="qwen3:8b", system="sys", user="hi")
        self.assertEqual(reply, "hello there")
        req = opened.call_args.args[0]
        self.assertTrue(req.full_url.endswith("/v1/chat/completions"))
        body = json.loads(opened.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(body["model"], "qwen3:8b")
        self.assertEqual(
            body["messages"],
            [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
        )
        self.assertFalse(body["stream"])

    def test_chat_json_mode_requests_json_object(self) -> None:
        with mock.patch(
            "urllib.request.urlopen",
            return_value=_response({"choices": [{"message": {"content": "{}"}}]}),
        ) as opened:
            self._server().chat(model="m", system="s", user="u", json_mode=True)
        body = json.loads(opened.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(body.get("response_format"), {"type": "json_object"})

    def test_chat_none_on_empty_choices(self) -> None:
        with mock.patch(
            "urllib.request.urlopen", return_value=_response({"choices": []})
        ):
            self.assertIsNone(self._server().chat(model="m", system="s", user="u"))

    def test_chat_none_when_server_down(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=OSError("refused")):
            self.assertIsNone(self._server().chat(model="m", system="s", user="u"))


class ChatServerStreamTests(unittest.TestCase):
    def _sse(self, contents: list[str]) -> mock.MagicMock:
        lines = "".join(
            f'data: {json.dumps({"choices": [{"delta": {"content": c}}]})}\n\n'
            for c in contents
        )
        stream = io.BytesIO((lines + "data: [DONE]\n\n").encode("utf-8"))

        resp = mock.MagicMock()
        resp.read.side_effect = lambda n=-1: stream.read(n)
        resp.__enter__.return_value = resp
        return resp

    def test_stream_yields_content_deltas(self) -> None:
        with mock.patch(
            "urllib.request.urlopen", return_value=self._sse(["hel", "lo"])
        ) as opened:
            deltas = list(
                OpenAICompatibleChatServer("http://x").chat_stream(
                    model="m", system="s", user="u"
                )
            )
        self.assertEqual(deltas, ["hel", "lo"])
        body = json.loads(opened.call_args.args[0].data.decode("utf-8"))
        self.assertTrue(body["stream"])

    def test_stream_ignores_malformed_lines(self) -> None:
        resp = mock.MagicMock()
        raw = b'data: not-json\n\ndata: {"choices": [{"delta": {"content": "ok"}}]}\n\ndata: [DONE]\n\n'
        stream = io.BytesIO(raw)
        resp.read.side_effect = lambda n=-1: stream.read(n)
        resp.__enter__.return_value = resp
        with mock.patch("urllib.request.urlopen", return_value=resp):
            deltas = list(
                OpenAICompatibleChatServer("http://x").chat_stream(
                    model="m", system="s", user="u"
                )
            )
        self.assertEqual(deltas, ["ok"])


if __name__ == "__main__":
    unittest.main()
