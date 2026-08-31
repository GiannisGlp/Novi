"""Tests for emotional-example sanitization (plan 24 §29-§30, §51 item 20).

The plan 23 sanitizer governs the canonical corpus; emotional examples carry
the same privacy obligations (person abstraction, PII redaction, biometric
separation) over their own fields: preferred_response, evidence, response_a/b,
and the situation strings.
"""

from __future__ import annotations

from training.collection.sanitizer import REDACTED, Sanitizer
from training.schemas import validate_example


def _emotional(**overrides) -> dict:
    ex = {
        "example_id": "emo-trace-1-emo",
        "task": "appropriate_acknowledgement",
        "situation": {
            "person": {"id": "person:vano", "name": "Vano"},
            "relationship": "owner",
            "conversation_phase": "tension",
            "user_goal": "solve_problem",
            "affective_hypotheses": [{"label": "frustration", "probability": 0.7}],
            "novi_caused_problem": True,
            "interruptibility": 0.2,
        },
        "desired_behavior": {"act": ["ACKNOWLEDGE"], "verbosity": "short",
                             "defensiveness": "none", "certainty": "moderate"},
        "preferred_response": "Yeah, I took that the wrong way. Let me reset.",
        "synthetic": False,
    }
    ex.update(overrides)
    return ex


class TestEmotionalSanitization:
    def test_redacts_preferred_response(self):
        s = Sanitizer()
        out, _ = s.sanitize(_emotional(preferred_response="Email vano@example.com about it."))
        assert "vano@example.com" not in out["preferred_response"]
        assert REDACTED in out["preferred_response"]

    def test_redacts_evidence(self):
        s = Sanitizer()
        ex = _emotional(task="perspective", evidence="Call +1 (555) 123-4567 later.",
                        interpretations=[{"label": "frustration", "probability": 1.0}],
                        robust_action="reduce pressure")
        out, _ = s.sanitize(ex)
        assert "555" not in out["evidence"]

    def test_redacts_preference_pair(self):
        s = Sanitizer()
        ex = _emotional(task="preference", category="naturalness",
                        response_a="Write to vano@example.com.", response_b="Yeah, got it.",
                        preferred="B")
        out, _ = s.sanitize(ex)
        assert "vano@example.com" not in out["response_a"]
        assert out["response_b"] == "Yeah, got it."

    def test_redacts_situation_strings(self):
        s = Sanitizer()
        out, _ = s.sanitize(_emotional(user_goal="contact vano@example.com"))
        assert "vano@example.com" not in out["situation"]["user_goal"]

    def test_abstracts_raw_person_id(self):
        s = Sanitizer()
        ex = _emotional()
        ex["situation"]["person"] = {"id": "vano", "name": "Vano"}
        out, _ = s.sanitize(ex)
        assert out["situation"]["person"]["id"] == "person:owner_001"
        assert out["situation"]["person"]["name"] == ""

    def test_already_abstract_id_kept(self):
        s = Sanitizer()
        out, _ = s.sanitize(_emotional())
        assert out["situation"]["person"]["id"] == "person:vano"

    def test_keeps_example_valid_after_sanitization(self):
        s = Sanitizer()
        out, _ = s.sanitize(_emotional())
        assert validate_example(out, kind="emotional") == []

    def test_biometric_content_drops_example(self):
        s = Sanitizer()
        out, report = s.sanitize(_emotional(preferred_response="face embedding matched at 0.9"))
        assert out is None
        assert report.dropped_biometric == 1

    def test_plain_response_untouched(self):
        s = Sanitizer()
        out, _ = s.sanitize(_emotional())
        assert out["preferred_response"] == "Yeah, I took that the wrong way. Let me reset."
