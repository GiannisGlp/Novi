"""Phase P1 tests: sleep cycle & memory maturation (deterministic, CI-safe)."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from novi.brain.b1_memory import utc_now
from novi.brain.consolidation import SummaryConsolidator
from novi.brain.engine import MacBrain
from novi.brain.sleep_cycle import SleepCycle
from novi.brain.storage import DurableMemoryStore
from novi.brain.tests.test_mac_brain import FakeCamera


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _old_created(hours_ago: float = 2.0) -> str:
    return _iso(datetime.now(timezone.utc) - timedelta(hours=hours_ago))


def _admit(store, content, *, memory_type="utterance", confidence=0.9, entity_refs=(), created_at=None):
    return store.admit(
        memory_type=memory_type,
        content=content,
        confidence=confidence,
        verification_status="verified",
        privacy_class="public",
        provenance={"source": "test"},
        entity_refs=tuple(entity_refs),
        created_at=created_at or utc_now(),
    )


def _cycle(store, **kwargs):
    kwargs.setdefault("consolidator", SummaryConsolidator(store))
    kwargs.setdefault("every_n_cycles", 5)
    return SleepCycle(store, **kwargs)


def _summaries(store):
    return [item["record"] for item in store.active_rows() if item["record"].memory_type == "summary"]


class CadenceTests(unittest.TestCase):
    def test_returns_none_on_non_multiple_and_zero_cycles(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            sc = _cycle(store)
            self.assertIsNone(sc.maybe_sleep(0))
            self.assertIsNone(sc.maybe_sleep(1))
            self.assertIsNone(sc.maybe_sleep(4))
            self.assertIsNone(sc.maybe_sleep(6))
            report = sc.maybe_sleep(5)
            self.assertIsNotNone(report)
            self.assertEqual(report["cycle"], 5)

    def test_report_has_contract_keys(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            report = _cycle(store).maybe_sleep(5)
            self.assertEqual(
                sorted(report.keys()),
                sorted(["cycle", "consolidated_groups", "new_summaries", "decayed", "strengthened", "duration_ms"]),
            )
            self.assertIsInstance(report["duration_ms"], float)


class ConsolidationPhaseTests(unittest.TestCase):
    def test_episodic_groups_become_summary_memories(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            for i in range(5):
                _admit(store, f"alice mentioned fact {i}", entity_refs=("alice",), created_at=_old_created())
            report = _cycle(store).maybe_sleep(5)
            self.assertGreaterEqual(report["consolidated_groups"], 1)
            self.assertGreaterEqual(report["new_summaries"], 1)
            summaries = _summaries(store)
            self.assertEqual(len(summaries), 1)
            self.assertIn("alice", summaries[0].entity_refs)
            # raw episodes remain active and untouched by consolidation
            self.assertGreaterEqual(store.active_count, 6)


class DecayPhaseTests(unittest.TestCase):
    def test_expired_memory_marked_decayed(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            admission = _admit(store, "fleeting perception", memory_type="perception", entity_refs=("spark",))
            past = _iso(datetime.now(timezone.utc) - timedelta(minutes=5))
            self.assertTrue(store.set_expiry(admission.memory_id, past))
            report = _cycle(store).maybe_sleep(5)
            self.assertEqual(report["decayed"], 1)
            self.assertEqual(store.get_state(admission.memory_id), "decayed")
            self.assertEqual(store.retrieve("fleeting"), ())  # hidden from retrieval


class StrengthenPhaseTests(unittest.TestCase):
    def test_recently_accessed_gets_exact_bump_capped(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            normal = _admit(store, "bob said hi once", confidence=0.50, entity_refs=("bob",))
            near_cap = _admit(store, "carol said hi twice", confidence=0.98, entity_refs=("carol",))
            untouched = _admit(store, "dave never called", confidence=0.90, entity_refs=("dave",))
            store.touch_accessed(normal.memory_id)
            store.touch_accessed(near_cap.memory_id)
            report = _cycle(store).maybe_sleep(5)
            self.assertEqual(report["strengthened"], 2)
            self.assertAlmostEqual(store.get(normal.memory_id).confidence, 0.52, places=9)
            self.assertAlmostEqual(store.get(near_cap.memory_id).confidence, 0.99, places=9)  # capped
            self.assertAlmostEqual(store.get(untouched.memory_id).confidence, 0.90, places=9)
            self.assertEqual(store.get_state(normal.memory_id), "active")  # state kept active

    def test_old_access_is_outside_phase_window(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            stale_recall = _admit(store, "erin long ago", confidence=0.60, entity_refs=("erin",))
            old = _iso(datetime.now(timezone.utc) - timedelta(minutes=10))
            store.touch_accessed(stale_recall.memory_id, when=old)
            report = _cycle(store, max_minutes_per_phase=1.0).maybe_sleep(5)
            self.assertEqual(report["strengthened"], 0)
            self.assertAlmostEqual(store.get(stale_recall.memory_id).confidence, 0.60, places=9)


class NarratorPhaseTests(unittest.TestCase):
    def test_broken_narrator_does_not_propagate_and_emits_error(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            _admit(store, "alice one", entity_refs=("alice",), created_at=_old_created())
            _admit(store, "alice two", entity_refs=("alice",), created_at=_old_created())
            events: list[tuple[str, dict]] = []

            def boom(episodes):
                raise RuntimeError("narrator exploded")

            report = _cycle(store, narrator=boom, emit=lambda t, p: events.append((t, p))).maybe_sleep(5)
            self.assertIsNotNone(report)
            self.assertGreaterEqual(report["new_summaries"], 1)  # earlier phases still ran
            errors = [p for t, p in events if t == "sleep.error"]
            self.assertEqual(len(errors), 1)
            self.assertIn("narrator exploded", errors[0]["error"])
            # broken narrator must not have rewritten the summary
            self.assertTrue(all("alice:" in s.content for s in _summaries(store)))

    def test_none_returning_narrator_leaves_summary_alone(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            _admit(store, "alice one", entity_refs=("alice",), created_at=_old_created())
            _admit(store, "alice two", entity_refs=("alice",), created_at=_old_created())
            self.assertIsNotNone(_cycle(store).maybe_sleep(5))  # create the summary deterministically
            original = _summaries(store)[0].content
            report = _cycle(store, narrator=lambda episodes: None).maybe_sleep(10)
            self.assertIsNotNone(report)
            self.assertEqual(len(_summaries(store)), 1)
            self.assertEqual(_summaries(store)[0].content, original)

    def test_narrator_refreshes_oldest_summary_content(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            early = _old_created(hours_ago=3.0)
            late = _old_created(hours_ago=1.0)
            first = _admit(store, "gist v1", memory_type="summary", entity_refs=("alice",), created_at=early)
            _admit(store, "gist v2", memory_type="summary", entity_refs=("carol",), created_at=late)
            report = _cycle(store, narrator=lambda episodes: f"refreshed: {episodes[0]['content']}").maybe_sleep(5)
            self.assertIsNotNone(report)
            contents = {r.content for r in _summaries(store)}
            self.assertIn("refreshed: gist v1", contents)  # oldest refreshed
            self.assertIn("gist v2", contents)  # newer left alone
            self.assertIsNotNone(store.get(first.memory_id))


class IdempotencyTests(unittest.TestCase):
    def test_second_run_does_not_duplicate_summaries(self):
        with tempfile.TemporaryDirectory() as td:
            store = DurableMemoryStore(Path(td) / "s.db")
            for i in range(3):
                _admit(store, f"alice event {i}", entity_refs=("alice",), created_at=_old_created())
                _admit(store, f"carol event {i}", entity_refs=("carol",), created_at=_old_created())
            sc = _cycle(store)
            first = sc.maybe_sleep(5)
            self.assertEqual(first["new_summaries"], 2)
            self.assertEqual(len(_summaries(store)), 2)
            second = sc.maybe_sleep(10)
            self.assertEqual(second["new_summaries"], 0)
            self.assertEqual(len(_summaries(store)), 2)  # no duplicates
            self.assertEqual(second["consolidated_groups"], 0)


class EngineHookTests(unittest.TestCase):
    def test_step_emits_sleep_phase_on_cadence_multiple(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "brain.db"
            brain = MacBrain(camera=FakeCamera(), store_path=str(db))
            brain._sleep_cycle = SleepCycle(
                brain.memory,
                consolidator=brain.summary_consolidator,
                every_n_cycles=2,
                emit=brain._emit,
            )
            brain.start()
            try:
                result1 = brain.step()
                result2 = brain.step()
            finally:
                brain.stop()
            self.assertNotIn("sleep", result1)
            events = [e for e in brain.events if e["event_type"] == "sleep.phase"]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["payload"]["cycle"], 2)
            self.assertEqual(result2["cycle"], 2)


if __name__ == "__main__":
    unittest.main()
