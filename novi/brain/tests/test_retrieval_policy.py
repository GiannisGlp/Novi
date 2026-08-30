"""Tests for novi/brain/retrieval_policy.py — composite memory retrieval.

Plan 22 Phase 5 (Tasks 5.3–5.4) and the required memory test classes:
- relevant episodic memory beats unrelated recent memory;
- recent relevant memory beats old weak memory;
- low-confidence memory is down-ranked;
- contradicted memory is not silently treated as truth;
- retrieval remains bounded;
- memory retrieval is explainable (why retrieved / source traceable).
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from novi.brain.retrieval_policy import RetrievalContext, RetrievalScorer


def _record(
    memory_id,
    content="camera integration discussion",
    *,
    confidence=0.9,
    entity_refs=(),
    created_at=None,
    verification_status="verified",
    memory_type="episodic",
):
    class _R:
        memory_id: str
        content: str
        confidence: float
        entity_refs: tuple
        created_at: str
        verification_status: str
        memory_type: str

    r = _R()
    r.memory_id = memory_id
    r.content = content
    r.confidence = confidence
    r.entity_refs = entity_refs
    r.created_at = created_at or datetime.now(timezone.utc).isoformat()
    r.verification_status = verification_status
    r.memory_type = memory_type
    return r


class RetrievalScorerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scorer = RetrievalScorer()
        self.ctx = RetrievalContext()

    def test_relevant_episodic_beats_unrelated_recent(self) -> None:
        relevant = _record("mem-1", "camera integration with vano", entity_refs=("vano",), created_at=datetime.now(timezone.utc).isoformat())
        unrelated = _record("mem-2", "recipes for sourdough bread", created_at=datetime.now(timezone.utc).isoformat())
        ctx = RetrievalContext(person="vano", situation="conversation_occurring")
        s_relevant = self.scorer.score(relevant, relevance=0.9, context=ctx)
        s_unrelated = self.scorer.score(unrelated, relevance=0.9, context=ctx)
        self.assertGreater(s_relevant.score, s_unrelated.score)

    def test_recent_relevant_beats_old_weak(self) -> None:
        old = _record("mem-old", "camera integration", created_at=(datetime.now(timezone.utc) - timedelta(days=60)).isoformat())
        recent = _record("mem-new", "camera integration", created_at=datetime.now(timezone.utc).isoformat())
        s_old = self.scorer.score(old, relevance=0.5)
        s_new = self.scorer.score(recent, relevance=0.5)
        self.assertGreater(s_new.score, s_old.score)

    def test_low_confidence_memory_down_ranked(self) -> None:
        strong = _record("mem-strong", "same topic", confidence=0.95)
        weak = _record("mem-weak", "same topic", confidence=0.3)
        s_strong = self.scorer.score(strong, relevance=0.8)
        s_weak = self.scorer.score(weak, relevance=0.8)
        self.assertGreater(s_strong.score, s_weak.score)

    def test_contradicted_memory_not_treated_as_truth(self) -> None:
        normal = _record("mem-ok", "the mug is on the desk", verification_status="verified")
        contradicted = _record("mem-bad", "the mug is on the desk", verification_status="contradicted")
        s_ok = self.scorer.score(normal, relevance=0.9)
        s_bad = self.scorer.score(contradicted, relevance=0.9)
        self.assertGreater(s_ok.score, s_bad.score)
        self.assertIn("contradiction", s_bad.penalties)
        self.assertGreater(s_bad.penalties["contradiction"], 0.0)

    def test_hypothetical_evidence_down_ranked(self) -> None:
        observed = _record("mem-obs", "mug moved", verification_status="verified")
        predicted = _record("mem-pred", "mug moved", verification_status="unverified", memory_type="causal_link")
        s_obs = self.scorer.score(observed, relevance=0.9)
        s_pred = self.scorer.score(predicted, relevance=0.9)
        self.assertGreater(s_obs.score, s_pred.score)

    def test_retrieval_remains_bounded(self) -> None:
        records = [_record(f"mem-{i}", "topic") for i in range(200)]
        ranked = self.scorer.rank(records, relevance_for=lambda idx, r: 1.0 / (1 + idx), limit=8)
        self.assertLessEqual(len(ranked), 8)
        self.assertEqual(ranked[0].memory_id, "mem-0")  # best relevance wins ties

    def test_retrieval_is_explainable(self) -> None:
        record = _record("mem-42", "vano discussed camera integration at the office", entity_refs=("vano",), created_at=datetime.now(timezone.utc).isoformat())
        ctx = RetrievalContext(person="vano", situation="conversation_occurring", location="office")
        scored = self.scorer.score(record, relevance=0.9, context=ctx)
        snap = scored.snapshot()
        self.assertEqual(snap["memory_id"], "mem-42")
        self.assertGreater(snap["score"], 0.0)
        # contributions are per-signal and "why" names the winners
        self.assertIn("semantic", snap["contributions"])
        self.assertIn("person", snap["contributions"])
        self.assertTrue(snap["why"])
        self.assertLessEqual(len(snap["why"]), 5)

    def test_recently_retrieved_loses_novelty(self) -> None:
        record = _record("mem-1", "topic")
        ctx = RetrievalContext(recently_retrieved={"mem-1"})
        fresh = self.scorer.score(record, relevance=0.7)
        seen = self.scorer.score(record, relevance=0.7, context=ctx)
        self.assertGreater(fresh.score, seen.score)


if __name__ == "__main__":
    unittest.main()
