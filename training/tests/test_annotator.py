"""Tests for the annotation workflow (plan 23 §9)."""

from __future__ import annotations

import pytest

from training.collection.annotator import (
    AnnotationWorkflow,
    annotate_example,
    consensus,
    inter_annotator_agreement,
)


def _ex(example_id: str = "dlg-0001") -> dict:
    return {
        "example_id": example_id,
        "task": "clarification",
        "situation": {
            "person": {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.98},
            "world": {}, "conversation": {}, "memory": [], "social": {},
        },
        "decision": {"dialogue_act": "CLARIFY", "reason": "", "verbosity": "short"},
        "response": "The blue one?",
    }


def _ann(example_id: str, reviewer: str, **overrides) -> dict:
    ann = {
        "annotation_id": f"ann-{reviewer}-{example_id}",
        "example_id": example_id,
        "reviewer_id": reviewer,
        "dialogue_act": "CLARIFY",
        "memory_relevance": 0.9,
        "initiative_appropriate": True,
        "grounding_correct": True,
        "naturalness": 5,
        "verbosity": 4,
        "certainty": 4,
        "user_intent": "clarify_reference",
        "outcome_quality": 5,
    }
    ann.update(overrides)
    return ann


class TestAnnotate:
    def test_annotation_attached_to_example(self):
        ex = annotate_example(_ex(), _ann("dlg-0001", "r1"))
        assert ex["annotations"] == [_ann("dlg-0001", "r1")]

    def test_multiple_annotations_collected(self):
        ex = _ex()
        ex = annotate_example(ex, _ann("dlg-0001", "r1"))
        ex = annotate_example(ex, _ann("dlg-0001", "r2", naturalness=4))
        assert len(ex["annotations"]) == 2

    def test_annotation_for_wrong_example_rejected(self):
        with pytest.raises(ValueError):
            annotate_example(_ex("dlg-0001"), _ann("dlg-9999", "r1"))


class TestAgreement:
    def test_full_agreement(self):
        anns = [_ann("e1", "r1"), _ann("e1", "r2"), _ann("e1", "r3")]
        agg = consensus(anns)
        assert agg["fields"]["naturalness"] == 5
        assert agg["agreement_rate"] == pytest.approx(1.0)

    def test_majority_wins(self):
        anns = [
            _ann("e1", "r1", naturalness=5),
            _ann("e1", "r2", naturalness=5),
            _ann("e1", "r3", naturalness=2),
        ]
        agg = consensus(anns)
        assert agg["fields"]["naturalness"] == 5
        assert agg["agreement_rate"] < 1.0

    def test_disagreement_rate_reported(self):
        anns = [_ann("e1", "r1", naturalness=5), _ann("e1", "r2", naturalness=1)]
        agg = consensus(anns)
        assert 0.0 < agg["agreement_rate"] < 1.0

    def test_inter_annotator_agreement(self):
        pair_a = [_ann("e1", "r1"), _ann("e1", "r2")]
        pair_b = [_ann("e1", "r1", naturalness=1), _ann("e1", "r2", naturalness=5)]
        agree_a = inter_annotator_agreement(pair_a)
        agree_b = inter_annotator_agreement(pair_b)
        assert agree_a > agree_b
        assert 0.0 <= agree_a <= 1.0


class TestWorkflow:
    def test_workflow_requires_quorum(self):
        wf = AnnotationWorkflow(min_reviewers=2)
        ex = wf.annotate(_ex(), _ann("dlg-0001", "r1"))
        assert wf.is_ready(ex) is False
        ex = wf.annotate(ex, _ann("dlg-0001", "r2"))
        assert wf.is_ready(ex) is True

    def test_ready_annotation_gets_consensus(self):
        wf = AnnotationWorkflow(min_reviewers=2)
        ex = wf.annotate(_ex(), _ann("dlg-0001", "r1"))
        ex = wf.annotate(ex, _ann("dlg-0001", "r2"))
        assert "annotation_consensus" in ex
        assert ex["annotation_consensus"]["agreement_rate"] == pytest.approx(1.0)
