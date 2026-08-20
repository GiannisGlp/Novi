import tempfile
import unittest
from pathlib import Path

from brain.contracts import utc_now

from MAC_BRAIN.storage import DurableMemoryStore


def _admit(store: DurableMemoryStore, memory_type: str, content, entity_refs=()):
    return store.admit(
        memory_type=memory_type,
        content=content,
        confidence=0.8,
        verification_status="pending",
        privacy_class="private",
        provenance={"source": "test", "captured_at": utc_now()},
        entity_refs=entity_refs,
    )


class IndexedRetrievalTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = DurableMemoryStore(Path(self._tmp.name) / "mem.db")

    def tearDown(self):
        self.store.close()

    def _one(self, n: int):
        for i in range(n):
            _admit(self.store, "episode", f"alice moved to the lamp {i}", entity_refs=("alice", "lamp"))
        for i in range(n):
            _admit(self.store, "episode", f"bob watered the plant {i}", entity_refs=("bob", "plant"))

    def test_indexed_matches_scan_results(self):
        self._one(6)
        scan = self.store.retrieve("alice lamp", limit=5)
        indexed = self.store.retrieve_indexed("alice lamp", limit=5)
        self.assertEqual(len(scan), len(indexed))
        self.assertEqual([r.memory_id for r in scan], [r.memory_id for r in indexed])
        # content matches the query terms
        self.assertTrue(all("alice" in r.entity_refs or "lamp" in r.entity_refs for r in indexed))

    def test_indexed_entity_filter(self):
        self._one(4)
        got = self.store.retrieve_indexed("plant", entity="bob", limit=5)
        self.assertTrue(all("bob" in r.entity_refs and "plant" in r.entity_refs for r in got))

    def test_empty_query_falls_back_to_scan(self):
        self._one(3)
        got = self.store.retrieve_indexed("", limit=3)
        self.assertEqual(len(got), 3)  # no crash, returns some records

    def test_forget_removes_from_index(self):
        self._one(2)
        recs = self.store.retrieve_indexed("alice", limit=10)
        self.assertGreater(len(recs), 0)
        target = recs[0].memory_id
        self.assertTrue(self.store.forget(target))
        after = self.store.retrieve_indexed("alice", limit=10)
        self.assertNotIn(target, [r.memory_id for r in after])

    def test_index_survives_reopen(self):
        self._one(4)
        path = Path(self._tmp.name) / "mem.db"
        self.store.close()
        reopened = DurableMemoryStore(path)
        self.store = reopened
        got = reopened.retrieve_indexed("plant", limit=5)
        self.assertGreater(len(got), 0)


if __name__ == "__main__":
    unittest.main()
