"""Phase D1 (gap-audit plan 13): knowledge-graph analytics.

Pins:
  - query(): BFS multi-hop traversal with predicate filtering, deterministic
    order, hop distances;
  - pagerank(): networkx when available, normalized weighted-degree fallback
    otherwise — both bounded and deterministic;
  - top_entities() ordering;
  - the graph extra is declared in pyproject (checked by reading pyproject).
"""

import unittest

from novi.brain.kgraph import EntityKnowledgeGraph


def _graph() -> EntityKnowledgeGraph:
    g = EntityKnowledgeGraph()
    g.add("cup", "on", "table", confidence=0.9)
    g.add("cup", "near", "plant", confidence=0.8)
    g.add("plant", "in", "kitchen", confidence=0.95)
    g.add("kitchen", "has", "window", confidence=0.7)
    return g


class QueryTests(unittest.TestCase):
    def test_one_hop_query(self):
        rows = _graph().query("cup")
        pairs = {(r["subject"], r["predicate"], r["object"]) for r in rows}
        self.assertIn(("cup", "on", "table"), pairs)
        self.assertIn(("cup", "near", "plant"), pairs)
        self.assertTrue(all(r["hops"] == 1 for r in rows))

    def test_two_hop_query_follows_chain(self):
        rows = _graph().query("cup", hops=2)
        two_hop = [r for r in rows if r["hops"] == 2]
        triples_at_2 = {(r["subject"], r["object"]) for r in two_hop}
        self.assertIn(("plant", "kitchen"), triples_at_2)

    def test_predicate_filter(self):
        rows = _graph().query("cup", predicate="on")
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["subject"], rows[0]["object"]), ("cup", "table"))

    def test_inward_edges_are_followed(self):
        # "table" is only an object; a 1-hop query must still find cup→table.
        rows = _graph().query("table", hops=1)
        pairs = {(r["subject"], r["object"]) for r in rows}
        self.assertIn(("cup", "table"), pairs)

    def test_deterministic_ordering_and_empty_inputs(self):
        g = _graph()
        rows_a = g.query("cup", hops=2)
        rows_b = g.query("cup", hops=2)
        self.assertEqual(rows_a, rows_b)
        self.assertEqual(g.query(""), [])
        self.assertEqual(g.query("cup", hops=0), [])


class PageRankTests(unittest.TestCase):
    def test_scores_bounded_and_deterministic(self):
        ranks = _graph().pagerank()
        self.assertTrue(ranks)
        for v in ranks.values():
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)
        self.assertEqual(ranks, _graph().pagerank())

    def test_hub_entity_ranks_high(self):
        g = EntityKnowledgeGraph()
        g.add("hub", "near", "a", confidence=0.9)
        g.add("hub", "near", "b", confidence=0.9)
        g.add("hub", "near", "c", confidence=0.9)
        g.add("a", "near", "b", confidence=0.5)
        top = g.top_entities(limit=4)
        self.assertEqual(top[0][0], "hub")

    def test_empty_graph(self):
        self.assertEqual(EntityKnowledgeGraph().pagerank(), {})
        self.assertEqual(EntityKnowledgeGraph().top_entities(), [])

    def test_networkx_extra_declared(self):
        import tomllib
        from pathlib import Path
        data = tomllib.loads(Path("pyproject.toml").read_text())
        extras = data["project"]["optional-dependencies"]
        self.assertIn("networkx>=3.0", extras["graph"])


if __name__ == "__main__":
    unittest.main()
