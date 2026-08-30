"""AirLLM cache status and isolation (plan 12, §44 Phase 39).

Never reuse a cache across different models, incompatible tokenizer
revisions, different conversations, or different security/authority contexts.
Cache keys include model revision, backend, tokenizer revision,
conversation/session, context hash, and runtime configuration.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from ..request import InferenceRequest


@dataclass(frozen=True)
class CacheKey:
    model_revision: str
    backend: str
    tokenizer_revision: str
    conversation_id: str
    context_hash: str
    runtime_configuration: str

    def digest(self) -> str:
        payload = {
            "model_revision": self.model_revision,
            "backend": self.backend,
            "tokenizer_revision": self.tokenizer_revision,
            "conversation_id": self.conversation_id,
            "context_hash": self.context_hash,
            "runtime_configuration": self.runtime_configuration,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def context_hash(request: InferenceRequest) -> str:
    """Hash the bounded context package (never raw private content)."""
    payload = {
        "system": request.system,
        "messages": [{"role": m.get("role"), "content": m.get("content")} for m in request.messages],
        "max_input_tokens": request.max_input_tokens,
        "max_output_tokens": request.max_output_tokens,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=repr).encode("utf-8")).hexdigest()


def build_cache_key(
    *,
    model_revision: str,
    backend: str,
    tokenizer_revision: str,
    request: InferenceRequest,
    runtime_configuration: str = "default",
) -> CacheKey:
    return CacheKey(
        model_revision=model_revision,
        backend=backend,
        tokenizer_revision=tokenizer_revision,
        conversation_id=request.conversation_id or "no-conversation",
        context_hash=context_hash(request),
        runtime_configuration=runtime_configuration,
    )


class InferenceCache:
    """Bounded keyed cache of generation results (best-effort, non-authoritative).

    Cache status is reported on responses (none | cold | warm | hit); the
    cache is an optimization only and must never be treated as truth.
    """

    def __init__(self, *, capacity: int = 64) -> None:
        self._capacity = max(1, int(capacity))
        self._entries: dict[str, Any] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: CacheKey) -> Any | None:
        digest = key.digest()
        if digest in self._entries:
            self._hits += 1
            return self._entries[digest]
        self._misses += 1
        return None

    def put(self, key: CacheKey, value: Any) -> None:
        digest = key.digest()
        self._entries[digest] = value
        while len(self._entries) > self._capacity:
            # Drop the oldest insertion (dict preserves insertion order).
            self._entries.pop(next(iter(self._entries)))

    def stats(self) -> dict[str, Any]:
        return {"hits": self._hits, "misses": self._misses, "entries": len(self._entries), "capacity": self._capacity}
