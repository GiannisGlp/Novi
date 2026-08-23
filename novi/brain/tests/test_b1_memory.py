import unittest

from novi.brain.b1_memory import DeterministicMemoryManager


class B1MemoryTests(unittest.TestCase):
    def _admit(self, manager: DeterministicMemoryManager, content: str = "Alice prefers the living room"):
        return manager.admit(
            memory_type="episodic",
            content=content,
            confidence=0.9,
            verification_status="observed",
            privacy_class="normal",
            provenance={"source": "sim.camera", "cycle": 1},
            event_refs=("1:person_entered_room:alice",),
            entity_refs=("alice",),
        )

    def test_admission_uses_canonical_memory_contract(self) -> None:
        manager = DeterministicMemoryManager()
        result = self._admit(manager)
        self.assertTrue(result.accepted)
        self.assertEqual(result.decision, "STORE_EPISODE")
        record = manager.get(result.memory_id)
        self.assertIsNotNone(record)
        self.assertEqual(record.revision, 0)
        self.assertEqual(record.entity_refs, ("alice",))

    def test_duplicate_admission_is_idempotent(self) -> None:
        manager = DeterministicMemoryManager()
        first = self._admit(manager)
        second = self._admit(manager)
        self.assertEqual(first.memory_id, second.memory_id)
        self.assertEqual(second.decision, "KEEP_EXISTING")
        self.assertEqual(manager.active_count, 1)

    def test_missing_provenance_is_rejected(self) -> None:
        manager = DeterministicMemoryManager()
        result = manager.admit(
            memory_type="episodic",
            content="Alice was here",
            confidence=0.9,
            verification_status="observed",
            privacy_class="normal",
            provenance={},
            entity_refs=("alice",),
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "missing_provenance")

    def test_invalid_confidence_is_rejected(self) -> None:
        manager = DeterministicMemoryManager()
        result = manager.admit(
            memory_type="episodic",
            content="Alice was here",
            confidence=1.5,
            verification_status="observed",
            privacy_class="normal",
            provenance={"source": "test"},
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "confidence_out_of_range")

    def test_retrieval_is_deterministic_and_entity_scoped(self) -> None:
        manager = DeterministicMemoryManager()
        self._admit(manager, "Alice entered the living room")
        manager.admit(
            memory_type="episodic",
            content="Door opened in hallway",
            confidence=0.9,
            verification_status="observed",
            privacy_class="normal",
            provenance={"source": "sim.door", "cycle": 2},
            entity_refs=("door",),
        )
        results = manager.retrieve("living Alice", entity="alice")
        self.assertEqual(len(results), 1)
        self.assertIn("Alice", results[0].content)

    def test_forget_removes_record_from_retrieval_but_keeps_tombstone(self) -> None:
        manager = DeterministicMemoryManager()
        admitted = self._admit(manager)
        self.assertTrue(manager.forget(admitted.memory_id))
        self.assertIsNone(manager.get(admitted.memory_id))
        self.assertEqual(manager.active_count, 0)
        self.assertEqual(manager.deleted_count, 1)
        self.assertFalse(manager.forget(admitted.memory_id))


if __name__ == "__main__":
    unittest.main()
