"""Triple semantic index for the knowledge graph (gap-audit plan Phase D2).

Embeds each knowledge triple as ``"subject predicate object"`` and answers
natural-language ``semantic_search(text)`` queries by cosine similarity over
the stored vectors. Uses the brain's standard embedder (MiniLM on MPS with a
deterministic hashing fallback), so it degrades gracefully offline.

Boundaries:
  - Purely additive retrieval; never mutates the graph.
  - Vectors are computed lazily on the first search, not at graph-mutation
    time: constructing a brain stays cheap and offline-safe, and the embedder
    is created at most once per process.
  - Deterministic ordering: score desc, then subject/predicate/object.
"""

from __future__ import annotations

import math
from typing import Any

from .kgraph import EntityKnowledgeGraph, KnowledgeTriple

_SHARED_EMBEDDER: Any | None = None


def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b, strict=False))
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (da * db)


def triple_text(triple: KnowledgeTriple) -> str:
    return f"{triple.subject} {triple.predicate} {triple.object}"


class TripleSemanticIndex:
    """Semantic search over knowledge triples."""

    def __init__(self, embedder: Any | None = None) -> None:
        self._embedder_ref: Any | None = embedder
        self._embedder_loaded = embedder is not None
        self._triples: dict[tuple[str, str, str], KnowledgeTriple] = {}
        self._vectors: dict[tuple[str, str, str], list[float]] = {}

    def __len__(self) -> int:
        return len(self._triples)

    @property
    def _embedder(self) -> Any:
        if not self._embedder_loaded:
            from .vector import MiniLMEmbedding
            global _SHARED_EMBEDDER
            if _SHARED_EMBEDDER is None:
                _SHARED_EMBEDDER = MiniLMEmbedding()
            self._embedder_ref = _SHARED_EMBEDDER
            self._embedder_loaded = True
        return self._embedder_ref

    # ---- indexing ----

    def add_triple(self, triple: KnowledgeTriple) -> bool:
        key = (triple.subject, triple.predicate, triple.object)
        is_new = key not in self._triples
        self._triples[key] = triple
        return is_new

    def remove_triple(self, subject: str, predicate: str, object_: str) -> bool:
        key = (subject, predicate, object_)
        had = key in self._triples
        self._triples.pop(key, None)
        self._vectors.pop(key, None)
        return had

    def rebuild(self, graph: EntityKnowledgeGraph) -> int:
        """Re-index every triple in the graph. Returns the index size."""
        self._triples.clear()
        self._vectors.clear()
        for t in graph.triples():
            self.add_triple(t)
        return len(self)

    def _ensure_vectors(self) -> None:
        """Embed triples that do not have a vector yet."""
        for key, t in list(self._triples.items()):
            if key in self._vectors:
                continue
            vec = self._embedder.embed(triple_text(t))
            if vec:
                self._vectors[key] = vec

    # ---- retrieval ----

    def semantic_search(self, text: str, *, limit: int = 5) -> list[tuple[KnowledgeTriple, float]]:
        """Top-``limit`` triples whose "s p o" text best matches ``text``."""
        text = (text or "").strip()
        if not text or limit <= 0 or not self._triples:
            return []
        qvec = self._embedder.embed(text)
        if not qvec:
            return []
        self._ensure_vectors()
        scored = [
            (_cosine(qvec, self._vectors[key]), t)
            for key, t in self._triples.items()
            if key in self._vectors
        ]
        scored.sort(key=lambda pair: (-pair[0], pair[1].subject, pair[1].predicate, pair[1].object))
        return [(t, round(score, 6)) for score, t in scored[:limit]]

    # ---- graph sync ----

    def attach_to_graph(self, graph: EntityKnowledgeGraph) -> None:
        """Keep the index in sync with graph mutations via on_change chaining.

        The previous callback (persistence) is preserved and invoked after the
        incremental update.
        """
        previous = graph._on_change

        def _sync() -> None:
            self.sync_with_graph(graph)
            if previous is not None:
                previous()

        graph.set_on_change(_sync)

    def sync_with_graph(self, graph: EntityKnowledgeGraph) -> None:
        """Incremental diff: add missing triples, drop removed ones."""
        live: dict[tuple[str, str, str], KnowledgeTriple] = {}
        for t in graph.triples():
            live[(t.subject, t.predicate, t.object)] = t
        for key in set(self._triples) - set(live):
            self.remove_triple(*key)
        for key, t in live.items():
            if key not in self._triples:
                self.add_triple(t)


def index_for_graph(graph: EntityKnowledgeGraph, *, embedder: Any | None = None) -> TripleSemanticIndex:
    """Build an index pre-populated from a graph and attached to its changes."""
    idx = TripleSemanticIndex(embedder=embedder)
    idx.rebuild(graph)
    idx.attach_to_graph(graph)
    return idx
