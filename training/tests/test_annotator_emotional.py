"""Tests for emotional annotation (plan 24 §31, §51 item 21).

Failures become training candidates only after quality review; the annotation
pipeline is that review. Emotional annotations score the emotional accuracy,
proportionality, boundary respect, and timing of a response (plan §31).
"""

from __future__ import annotations

import pytest

from training.collection.annotator import AnnotationWorkflow, annotate_example, consensus
from training.schemas import validate_annotation


def _example() -> dict:
    return {
        "example_id": "emo-trace-1-emo",
        "task": "appropriate_acknowledgement",
        "situation": {
            "person": {"id": "person:vano"},
            "relationship": "owner",
            "conversation_phase": "tension",
            "affective_hypotheses": [{"label": "frustration", "probability": 0.7}],
            "novi_caused_problem": True,
            "interruptibility": 0.2,
        },
        "desired_behavior": {"act": ["ACKNOWLEDGE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Yeah, I took that the wrong way. Let me reset.",
        "synthetic": False,
    }


def _annotation(**overrides) -> dict:
    a = {
        "annotation_id": "ann-1",
        "example_id": "emo-trace-1-emo",
        "reviewer_id": "reviewer-a",
        "emotional_accuracy": 4,
        "proportionality": 4,
        "boundary_respect": 5,
        "timing": 4,
        "naturalness": 4,
    }
    a.update(overrides)
    return a


class TestEmotionalAnnotationSchema:
    def test_emotional_annotation_valid(self):
        assert validate_annotation(_annotation()) == []

    def test_rejects_out_of_range_emotional_score(self):
        assert validate_annotation(_annotation(emotional_accuracy=7))
        assert validate_annotation(_annotation(proportionality=-1))

    def test_rejects_unknown_emotional_field_value(self):
        assert validate_annotation(_annotation(timing="late"))


class TestEmotionalAnnotate:
    def test_attaches_emotional_annotation(self):
        out = annotate_example(_example(), _annotation())
        assert out["annotations"][0]["emotional_accuracy"] == 4

    def test_mismatched_example_id_rejected(self):
        with pytest.raises(ValueError):
            annotate_example(_example(), _annotation(example_id="other"))

    def test_consensus_over_emotional_fields(self):
        a = _annotation(annotation_id="ann-1", reviewer_id="r1", emotional_accuracy=4, proportionality=4)
        b = _annotation(annotation_id="ann-2", reviewer_id="r2", emotional_accuracy=4, proportionality=5)
        c = _annotation(annotation_id="ann-3", reviewer_id="r3", emotional_accuracy=4, proportionality=4)
        c = consensus([a, b, c])
        assert c["fields"]["emotional_accuracy"] == 4
        assert c["fields"]["proportionality"] == 4

    def test_workflow_ready_after_quorum(self):
        wf = AnnotationWorkflow(min_reviewers=2)
        ex = wf.annotate(_example(), _annotation(annotation_id="ann-1", reviewer_id="r1"))
        assert wf.is_ready(ex) is False
        ex = wf.annotate(ex, _annotation(annotation_id="ann-2", reviewer_id="r2"))
        assert wf.is_ready(ex) is True
        assert "annotation_consensus" in ex
