"""Phase 4a (north-star gap analysis): retrieval ranks by time, provenance,
and confidence — never by vector similarity alone.

docs/audits/NOVI_NORTH_STAR_GAP_ANALYSIS_2026-08-29.md §4 Phase 4a:
"Add retrieve_ranked(query, *, min_confidence, provenance_scope,
recency_weight, importance_weight, trust_weight) fusing vector + recency +
importance + trust; apply to retrieve_semantic/retrieve_indexed."

Acceptance:
- a low-confidence/stale record and a high-confidence/recent record with
  equal term relevance -> the high-confidence/recent one returns first;
- retrieve_ranked honors min_confidence and provenance_scope filters;
- recency alone reorders ties honestly.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from novi.brain.importance import provenance_trust, rank_memory, recency_score
from novi.brain.storage import DurableMemoryStore


def _iso_days_ago(days: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")


class _Tmp:
    pass


class RankedRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.store = DurableMemoryStore(f"{self._tmp.name}/mem.db")

    def tearDown(self) -> None:
        self.store.close()
        self._tmp.cleanup()

    def _admit(self, *, memory_type: str, text: str, confidence: float, created_at: str, verification: str, source: str = "camera.front"):
        return self.store.admit(
            memory_type=memory_type,
            content={"text": text},
            confidence=confidence,
            verification_status=verification,
            privacy_class="unclassified",
            provenance={"source": source, "source_class": "DIRECT_SENSOR" if "sensor" in source or "camera" in source else "MODEL_INFERENCE"},
            entity_refs=("alice",),
            temporal_context={"captured_at": created_at},
            created_at=created_at,
        ).memory_id

    def test_low_conf_stale_loses_to_high_conf_fresh(self):
        self._admit(memory_type="observation", text="the alice lamp is on the desk",
                    confidence=0.2, created_at=_iso_days_ago(120),
                    verification="unverified", source="model-guess")
        self._admit(memory_type="observation", text="the alice lamp is on the desk",
                    confidence=0.9, created_at=_iso_days_ago(0),
                    verification="verified", source="camera.sensor")
        got = self.store.retrieve_indexed("alice lamp", limit=2)
        self.assertEqual(len(got), 2)
        self.assertEqual(got[0].confidence, 0.9, "the high-confidence/recent record must return first")
        ranked = self.store.retrieve_ranked("alice lamp", limit=2)
        self.assertEqual(ranked[0].confidence, 0.9)
        ranked_first = self.store.retrieve_ranked("alice lamp", limit=2, min_confidence=0.5)
        self.assertEqual(len(ranked_first), 1, "min_confidence filters the weak claim")
        self.assertEqual(ranked_first[0].confidence, 0.9)

    def test_provenance_scope_sensor_excludes_model_guesses(self):
        self._admit(memory_type="observation", text="key near the door",
                    confidence=0.95, created_at=_iso_days_ago(0), verification="unverified",
                    source="llm-inference")
        self._admit(memory_type="observation", text="key near the door",
                    confidence=0.5, created_at=_iso_days_ago(30), verification="unverified",
                    source="camera.sensor")
        scoped = self.store.retrieve_ranked("key door", limit=5, provenance_scope="sensor")
        self.assertEqual(len(scoped), 1)
        self.assertEqual(scoped[0].confidence, 0.5)
        unscoped = self.store.retrieve_ranked("key door", limit=5)
        self.assertEqual(len(unscoped), 2)

    def test_recency_reorders_equal_records(self):
        self._admit(memory_type="note", text="gardening tips for ferns",
                    confidence=0.7, created_at=_iso_days_ago(90), verification="verified",
                    source="manual-body")
        self._admit(memory_type="note", text="gardening tips for ferns (spring)",
                    confidence=0.7, created_at=_iso_days_ago(1), verification="verified",
                    source="manual-body")
        got = self.store.retrieve_indexed("gardening ferns", limit=2)
        self.assertEqual(len(got), 2)
        # Recency decay: the fresh one scores strictly higher.
        rank_first = rank_memory(got[0], similarity=1.0)
        rank_second = rank_memory(got[1], similarity=1.0)
        self.assertGreater(rank_first, rank_second)
        self.assertGreater(recency_score(got[0]), recency_score(got[1]))

    def test_no_confidence_bias_for_fresh_weak_claim(self):
        # Recency alone must not beat strong evidence: verified-but-old stays
        # ahead of an unverified toy claim with the same terms.
        self._admit(memory_type="observation", text="the boiler valve is closed",
                    confidence=0.3, created_at=_iso_days_ago(0),
                    verification="unverified", source="model-hint")
        self._admit(memory_type="observation", text="the boiler valve is closed",
                    confidence=0.95, created_at=_iso_days_ago(5),
                    verification="verified", source="camera.sensor")
        got = self.store.retrieve_indexed("boiler valve", limit=2)
        self.assertEqual(got[0].confidence, 0.95)


class ComponentTests(unittest.TestCase):
    def test_recency_neutral_for_missing_stamp(self):
        class NoStamp:
            created_at = ""

        self.assertAlmostEqual(recency_score(NoStamp()), 0.5)

    def test_recency_decays_with_age(self):
        class R:
            created_at = _iso_days_ago(0)

        class Old:
            created_at = _iso_days_ago(90)

        self.assertGreater(recency_score(R()), recency_score(Old()))
        self.assertAlmostEqual(recency_score(Old(), tau_days=10), 0.0, delta=0.05)

    def test_trust_prefers_verified_sensor_origin(self):
        class Verified:
            verification_status = "verified"
            provenance = {"source_class": "DIRECT_SENSOR"}

        class Guess:
            verification_status = "unverified"
            provenance = {"source_class": "MODEL_INFERENCE"}

        self.assertGreater(provenance_trust(Verified()), provenance_trust(Guess()))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
