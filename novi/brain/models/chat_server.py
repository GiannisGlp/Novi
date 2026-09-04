"""OpenAI-compatible chat server adapter (the portable LLM wire protocol).

Ollama, llama.cpp (``llama-server``), vLLM, and TensorRT-LLM frontends all
serve ``POST /v1/chat/completions`` and ``GET /v1/models`` — so a client
written against this surface works against every one of them with only the
base URL changing. This is the no-Ollama option for the robot body: point
it at ``llama-server`` and nothing upstream changes.

The native Ollama dialect (``/api/*`` with ``think``/``options`` controls)
remains the default where its tuned behavior matters; this adapter is the
swappable alternative, selected per surface (``llm_server`` /
``brain_llm_server``). Stdlib only, like the rest of the LLM wire code.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any


class OpenAICompatibleChatServer:
    """Minimal ``/v1`` chat client: probe, complete, stream."""

    def __init__(self, base_url: str, *, timeout: float = 2.0) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.timeout = timeout

    # -- probe ------------------------------------------------------------
    def probe(self, model: str) -> bool:
        """True when the server lists `model` (handles ``:latest`` suffixes)."""
        try:
            req = urllib.request.Request(f"{self.base_url}/v1/models", method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception:  # noqa: BLE001 - offline fallback
            return False
        want = (model or "").strip()
        for entry in data.get("data", []) or []:
            got = str((entry or {}).get("id", ""))
            if got == want or got.removesuffix(":latest") == want:
                return True
        return False

    # -- chat -------------------------------------------------------------
    def chat(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.5,
        max_tokens: int = 320,
        timeout: int = 120,
        json_mode: bool = False,
    ) -> str | None:
        """One full completion; None on any failure or empty content."""
        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            req = urllib.request.Request(
                f"{self.base_url}/v1/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception:  # noqa: BLE001 - offline fallback
            return None
        choices = data.get("choices", []) or []
        if not choices:
            return None
        content = ((choices[0] or {}).get("message") or {}).get("content") or ""
        return content.strip() or None

    # -- stream -----------------------------------------------------------
    def chat_stream(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.5,
        max_tokens: int = 320,
        timeout: int = 120,
    ):
        """Yield content deltas from the SSE event stream (``data:`` lines)."""
        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            buf = b""
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line.startswith(b"data:"):
                        continue
                    payload = line[len(b"data:"):].strip()
                    if payload == b"[DONE]":
                        return
                    try:
                        data = json.loads(payload.decode("utf-8"))
                    except Exception:  # noqa: BLE001 - skip malformed SSE lines
                        continue
                    for choice in data.get("choices", []) or []:
                        delta = ((choice or {}).get("delta") or {}).get("content") or ""
                        if delta:
                            yield delta
