"""Phase D2 (gap-audit plan 13): triple embeddings + semantic search.

Pins:
  - every triple indexes as "subject predicate object" text;
  - semantic_search ranks the matching triple above unrelated ones;
  - incremental sync adds new triples and drops removed ones;
  - attach_to_graph preserves the previous on_change callback (persistence);
  - deterministic ordering and empty-input safety.
"""

import unittest

from novi.brain.kgraph import EntityKnowledgeGraph
from novi.brain.triple_index import TripleSemanticIndex, index_for_graph, triple_text


class _HashEmbedder:
    """Deterministic offline embedder (token-hashing bag of words)."""

    def dimension(self) -> int:
        return 64

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension()
        for token in str(text).lower().replace("_", " ").split():
            vec[hash(token) % 64] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]


def _graph() -> EntityKnowledgeGraph:
    g = EntityKnowledgeGraph()
    g.add("cup", "on", "table", confidence=0.9)
    g.add("plant", "in", "kitchen", confidence=0.95)
    g.add("alice", "likes", "coffee", confidence=0.8)
    return g


class TripleIndexTests(unittest.TestCase):
    def test_triple_text_format(self):
        g = _graph()
        t = g.triples(subject="cup")[0]
        self.assertEqual(triple_text(t), "cup on table")

    def test_indexes_all_triples(self):
        idx = TripleSemanticIndex(embedder=_HashEmbedder())
        g = _graph()
        self.assertEqual(idx.rebuild(g), len(g.triples()))

    def test_semantic_search_ranks_relevant_triple_first(self):
        idx = TripleSemanticIndex(embedder=_HashEmbedder())
        g = _graph()
        idx.rebuild(g)
        hits = idx.semantic_search("the cup is on the table", limit=3)
        self.assertTrue(hits)
        top = hits[0][0]
        self.assertEqual((top.subject, top.predicate, top.object), ("cup", "on", "table"))
        scores = [s for _, s in hits]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_incremental_sync_adds_new_triples(self):
        g = _graph()
        idx = index_for_graph(g, embedder=_HashEmbedder())
        before = len(idx)
        self.assertEqual(before, len(g.triples()))
        g.add("bob", "owns", "mug", confidence=0.7)
        self.assertEqual(len(idx), before + 1)
        # The new triple is searchable immediately.
        hits = idx.semantic_search("bob owns a mug", limit=1)
        self.assertEqual((hits[0][0].subject, hits[0][0].object), ("bob", "mug"))

    def test_empty_query_returns_empty(self):
        idx = TripleSemanticIndex(embedder=_HashEmbedder())
        idx.rebuild(_graph())
        self.assertEqual(idx.semantic_search("", limit=5), [])
        self.assertEqual(idx.semantic_search("anything", limit=0), [])

    def test_attach_preserves_previous_callback(self):
        calls = []
        g = _graph()
        g.set_on_change(lambda: calls.append("persist"))
        idx = index_for_graph(g, embedder=_HashEmbedder())
        n = len(idx)
        g.add("dana", "near", "door", confidence=0.6)
        self.assertEqual(len(idx), n + 1)
        # persistence callback still fired after index sync
        self.assertEqual(calls, ["persist"])


if __name__ == "__main__":
    unittest.main()
