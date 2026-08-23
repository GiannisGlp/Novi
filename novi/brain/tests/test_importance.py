"""Phase C4 (gap-audit plan 13): learned importance + weighted consolidation.

Pins:
  - ImportanceModel: bounded deterministic fusion of confidence, attention and
    novelty, modulated by the Soul's curiosity trait;
  - provenance_trust / record_importance accessors;
  - the Phase C4 recall formula ranks an importance-stamped record above an
    otherwise-identical unstamped one, and trust breaks remaining ties;
  - consolidation archives by ascending importance×recency and exempts
    protected (importance ≥ 0.8) records from automatic archival.
"""

import unittest
from datetime import datetime, timezone

from novi.brain.importance import (
    PROTECTED_IMPORTANCE,
    ImportanceModel,
    provenance_trust,
    record_importance,
)


class _Rec:
    def __init__(self, created_at, verification_status="verified", confidence=0.5, provenance=None, memory_type="perception"):
        self.created_at = created_at
        self.verification_status = verification_status
        self.confidence = confidence
        self.provenance = provenance or {}
        self.memory_type = memory_type


class ImportanceModelTests(unittest.TestCase):
    def test_score_is_bounded_and_deterministic(self):
        m = ImportanceModel()
        for c in (-1.0, 0.0, 0.5, 2.0):
            for a in (0.0, 1.0):
                s = m.score(confidence=c, attention=a, novelty=0.7)
                self.assertTrue(0.0 <= s <= 1.0)
        self.assertEqual(m.score(confidence=0.9), m.score(confidence=0.9))

    def test_novelty_decays_with_sightings(self):
        m = ImportanceModel()
        self.assertEqual(m.novelty_for(0), 1.0)
        self.assertGreater(m.novelty_for(1), m.novelty_for(5))
        self.assertGreaterEqual(m.novelty_for(100), m.novelty_floor)

    def test_curiosity_trait_amplifies_novelty_term(self):
        curious = ImportanceModel(curiosity_trait=1.0)
        indifferent = ImportanceModel(curiosity_trait=0.0)
        novel_high = curious.score(confidence=0.5, attention=0.0, novelty=1.0) - curious.score(confidence=0.5, attention=0.0, novelty=0.0)
        novel_low = indifferent.score(confidence=0.5, attention=0.0, novelty=1.0) - indifferent.score(confidence=0.5, attention=0.0, novelty=0.0)
        self.assertGreater(novel_high, novel_low)

    def test_trust_prefers_verified_sensor_records(self):
        now = datetime.now(timezone.utc).isoformat()
        trusted = _Rec(now, verification_status="verified", provenance={"source": "vision.sensor"})
        shaky = _Rec(now, verification_status="unverified", provenance={"source": "audio.stt"})
        unknown = _Rec(now, verification_status="weird")
        self.assertGreater(provenance_trust(trusted), provenance_trust(shaky))
        self.assertGreater(provenance_trust(shaky), 0.0)
        self.assertLess(provenance_trust(unknown), 1.0)

    def test_record_importance_falls_back_to_confidence(self):
        stamped = _Rec("2026-01-01T00:00:00Z", provenance={"importance": 0.77})
        plain = _Rec("2026-01-01T00:00:00Z", confidence=0.42)
        self.assertAlmostEqual(record_importance(stamped), 0.77)
        self.assertAlmostEqual(record_importance(plain), 0.42)


class RecallFormulaTests(unittest.TestCase):
    def test_importance_stamp_breaks_ties_in_memory_score(self):
        from novi.brain.chat import ChatMixin
        now = datetime.now(timezone.utc)
        stamped = _Rec(now.isoformat(), confidence=0.5, provenance={"importance": 0.95})
        plain = _Rec(now.isoformat(), confidence=0.5)
        s_stamped = ChatMixin._memory_score(stamped, 0, now)
        s_plain = ChatMixin._memory_score(plain, 0, now)
        self.assertGreater(s_stamped, s_plain)

    def test_formula_matches_plan_weights(self):
        from novi.brain.chat import ChatMixin
        now = datetime.now(timezone.utc)
        rec = _Rec(now.isoformat(), verification_status="verified", confidence=0.5, provenance={"importance": 0.5, "source": "camera"})
        expected = 0.4 * 1.0 + 0.25 * 1.0 + 0.2 * 0.5 + 0.15 * provenance_trust(rec)
        self.assertAlmostEqual(ChatMixin._memory_score(rec, 0, now), expected, places=6)


class ConsolidationPriorityTests(unittest.TestCase):
    def _store_and_records(self):
        from novi.brain.b1_memory import DeterministicMemoryManager
        return DeterministicMemoryManager()

    def test_protected_importance_exempts_from_archival(self):
        from novi.brain.consolidation import ConsolidationConfig, MemoryConsolidator

        class MiniStore:
            def __init__(self):
                self.rows = {}
                self.states = {}

            def active_rows(self):
                return [{"record": r} for r in self.rows.values()]

            def get_state(self, mid):
                return self.states.get(mid, "active")

            def set_state(self, mid, state):
                self.states[mid] = state.value

            def set_confidence(self, mid, conf):
                self.rows[mid].confidence = conf

            def admit_rec(self, rec):
                self.rows[rec.memory_id] = rec

        store = MiniStore()
        cherished = _Rec(
            "2026-08-01T00:00:00+00:00", verification_status="verified",
            confidence=0.9, provenance={"importance": PROTECTED_IMPORTANCE},
        )
        cherished.memory_id = "mem-cherished"
        mundane = _Rec(
            "2026-08-01T00:00:00+00:00", verification_status="unverified",
            confidence=0.35, provenance={"importance": 0.2},
        )
        mundane.memory_id = "mem-mundane"
        store.admit_rec(cherished)
        store.admit_rec(mundane)
        cfg = ConsolidationConfig(decay_start_seconds=0.0, decay_period_seconds=10.0,
                                  decay_factor=0.5, min_confidence=0.5, contradiction_types=())
        report = MemoryConsolidator(store, cfg).consolidate()
        # Both decayed below min; only the mundane one is archived.
        self.assertEqual(report.archived, 1)
        self.assertEqual(store.get_state("mem-mundane"), "archived")
        self.assertEqual(store.get_state("mem-cherished"), "active")

    def test_lowest_priority_archives_first(self):
        from novi.brain.consolidation import _priority, _recency_factor, _record_importance
        old_low = _Rec("2026-01-01T00:00:00Z", provenance={"importance": 0.1})
        new_higher = _Rec("2026-01-02T00:00:00Z", provenance={"importance": 0.6})
        p_old = _priority(old_low, age_s=7200)
        p_new = _priority(new_higher, age_s=60)
        self.assertLess(p_old, p_new)
        self.assertAlmostEqual(_recency_factor(0), 1.0)
        self.assertAlmostEqual(_recency_factor(3600), 0.5, places=6)
        self.assertAlmostEqual(_record_importance(old_low), 0.1)


if __name__ == "__main__":
    unittest.main()
