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
import logging
import math
import re
from typing import Protocol

DEFAULT_DIM = 256
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_LOG = logging.getLogger(__name__)


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


class MiniLMEmbedding:
    """Local semantic embedding via sentence-transformers/all-MiniLM-L6-v2 (384d, MPS).

    Loads lazily and falls back to HashingEmbedding when the optional dependency
    or the model weights are unavailable (offline/CI). The model runs on MPS when
    available, otherwise CPU, and is 80 MB — fully local, no cloud.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DIM = 384

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        self.model_name = model_name or self.MODEL_NAME
        self._device = device  # auto-detect if None
        self._model: object | None = None
        self._fallback = HashingEmbedding(dim=self.DIM)
        self._load_error: str | None = None
        self._tried_load = False

    def dimension(self) -> int:
        return self.DIM

    def _load(self) -> object | None:
        if self._tried_load:
            return self._model
        self._tried_load = True
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

            # Device: prefer MPS on Apple Silicon, fall back to CPU.
            device = self._device
            if device is None:
                try:
                    import torch  # type: ignore[import-not-found]

                    device = "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu"
                except Exception:
                    device = "cpu"
            self._model = SentenceTransformer(self.model_name, device=device)
            _LOG.info("MiniLMEmbedding loaded %s on %s", self.model_name, device)
        except Exception as exc:  # noqa: BLE001 - optional dep, fall back gracefully
            self._load_error = str(exc)
            _LOG.warning("MiniLMEmbedding unavailable (%s) — falling back to hashing", exc)
            self._model = None
        return self._model

    def embed(self, text: str) -> list[float]:
        model = self._load()
        if model is None:
            # Hashing fallback but at 384d so the index stays consistent.
            return self._fallback.embed(text)
        try:
            # SentenceTransformer.encode returns np.ndarray; normalize_embeddings=True gives L2-normalized.
            vec = model.encode(text, normalize_embeddings=True, show_progress_bar=False)  # type: ignore[union-attr]
            # vec may be np.ndarray or list
            if hasattr(vec, "tolist"):
                vec = vec.tolist()
            # Ensure list[float] and L2-normalized (encode already normalized, but be safe)
            if isinstance(vec, list) and vec and isinstance(vec[0], list):
                # Batched case — take first
                vec = vec[0]
            return [float(x) for x in vec]  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001 - embedding failure falls back
            _LOG.warning("MiniLM embed failed (%s) — using hashing fallback", exc)
            return self._fallback.embed(text)

    @property
    def is_available(self) -> bool:
        return self._load() is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error


def auto_embedding_provider(prefer: str = "auto") -> EmbeddingProvider:
    """Factory: 'auto' tries MiniLM then falls back to hashing; 'hash' forces hashing; 'minilm' forces MiniLM (falls back on failure)."""
    prefer = (prefer or "auto").lower()
    if prefer == "hash":
        return HashingEmbedding()
    if prefer in ("auto", "minilm"):
        m = MiniLMEmbedding()
        # Trigger load attempt now for 'minilm' so caller knows availability; for 'auto' we keep lazy.
        if prefer == "minilm":
            m._load()
            if m._model is None:
                _LOG.warning("MiniLM requested but unavailable (%s)", m.load_error)
        return m
    return HashingEmbedding()


def normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=False))


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
