"""Semantic/vector memory primitives for the Mac Brain.

Provides a provider-neutral embedding boundary and a deterministic, offline
implementation so semantic recall works with zero external model dependency, plus
a seam (`EmbeddingProvider`) where a real local embedding model (e.g. a
sentence-transformers/all-MiniLM adapter on MPS) can be plugged in later.

Boundaries honored (docs/03-cognition 03, 04-memory-and-knowledge):
  - Embeddings are derived representations; raw memory stays the source of truth.
  - Retrieval ranks candidates; it never rewrites stored records.
  - The default provider is deterministic and local (no cloud, no weights download).
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

DEFAULT_DIM = 256
_TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...
    def dimension(self) -> int: ...


class HashingEmbedding:
    """Deterministic offline embedding: signed feature-hash over tokens, L2-normalized."""

    def __init__(self, dim: int = DEFAULT_DIM) -> None:
        self._dim = dim

    def dimension(self) -> int:
        return self._dim

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return _TOKEN_RE.findall(text.lower())

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in self._tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[idx] += sign
        return normalize(vec)


def normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    return sum(x * y for x, y in zip(a, b))


class EmbeddingIndex:
    """In-memory embedding index keyed by memory_id, persisted via the store."""

    def __init__(self, provider: EmbeddingProvider) -> None:
        self.provider = provider
        self._vectors: dict[str, list[float]] = {}
        self._text: dict[str, str] = {}

    def add(self, memory_id: str, text: str) -> None:
        self._vectors[memory_id] = self.provider.embed(text)
        self._text[memory_id] = text

    def remove(self, memory_id: str) -> None:
        self._vectors.pop(memory_id, None)
        self._text.pop(memory_id, None)

    def __contains__(self, memory_id: str) -> bool:
        return memory_id in self._vectors

    def search(self, query: str, *, limit: int = 5) -> list[tuple[str, float]]:
        qvec = self.provider.embed(query)
        scored = [(mid, cosine(qvec, v)) for mid, v in self._vectors.items()]
        scored.sort(key=lambda item: -item[1])
        return scored[:limit]

    def snapshot(self) -> list[dict[str, str]]:
        return [{"memory_id": mid, "text": self._text[mid]} for mid in self._text]

    @classmethod
    def from_snapshot(cls, provider: EmbeddingProvider, rows: list[dict[str, str]]) -> "EmbeddingIndex":
        index = cls(provider)
        for row in rows:
            index.add(row["memory_id"], row["text"])
        return index
