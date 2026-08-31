"""Tests for emotional trace collection (plan 24 §29-§31, §51 item 19).

Phase 25 (§29) — train from real interaction outcomes: every meaningful
social interaction generates an outcome record (context, interpretation,
policy decision, response, user reaction, outcome, correction). Success is
never inferred from silence alone.

Phase 26 (§30) — explicit user feedback is high-quality evidence.

Phase 27 (§31) — failures are classified into the 11 plan classes and become
training candidates after quality review.
"""

from __future__ import annotations

from novi.brain.decision_trace import DecisionTrace, utc_now_iso
from training.collection.failure import FAILURE_CLASSES, classify_failure
from training.collection.feedback import parse_feedback
from training.collection.trace_exporter import (
    EmotionalTraceExporter,
    emotional_task_for_act,
    is_emotional_eligible,
)
from training.schemas import validate_example


def _signal(**dims) -> dict:
    """AffectiveState snapshot with the given dimensions (value/confidence)."""
    out = {}
    for name, (value, confidence) in dims.items():
        out[name] = {
            "value": value,
            "confidence": confidence,
            "source": "lexical_marker",
            "last_updated": "2026-08-31T00:00:00+00:00",
            "decay_seconds": 90.0,
        }
    return out


def _emo_trace(**overrides) -> dict:
    t = DecisionTrace(
        trace_id="emo-trace-1",
        cycle_id=9,
        time=utc_now_iso(),
        input_event="Vano: that's not what I asked for",
        perception_evidence=["user voice detected"],
        world_changes=[],
        identity_resolution={"person_id": "person:vano", "confidence": 0.98, "name": "Vano"},
        retrieved_memories=[],
        social_context={
            "relationship": "owner",
            "conversation_temperature": "tense",
            "interruptibility": 0.2,
            "user_availability": "available",
            "boundary_state": "NORMAL",
            "recent_social_events": ["correction"],
            "user_goal": "solve_problem",
            "emotional_signal": _signal(
                frustration_likelihood=(0.8, 0.9),
                fatigue_likelihood=(0.2, 0.5),
                engagement=(0.3, 0.4),
            ),
        },
        dialogue_act="ACKNOWLEDGE",
        dialogue_reason="user_corrected_novi",
        initiative_score=0.0,
        llm_model="qwen3:8b",
        response="Yeah, I took that the wrong way. Let me reset.",
        outcome="corrected",
    )
    for k, v in overrides.items():
        setattr(t, k, v)
    return t.snapshot()


class TestEmotionalTaskInference:
    def test_act_to_emotional_task(self):
        assert emotional_task_for_act("ACKNOWLEDGE") == "appropriate_acknowledgement"
        assert emotional_task_for_act("SILENCE") == "appropriate_silence"
        assert emotional_task_for_act("REPAIR") == "repair"
        assert emotional_task_for_act("APOLOGIZE") == "apology"
        assert emotional_task_for_act("GIVE_SPACE") == "boundary_respect"
        assert emotional_task_for_act("SUPPORT") == "support"
        assert emotional_task_for_act("ENCOURAGE") == "encouragement"
        assert emotional_task_for_act("CELEBRATE") == "celebration"
        assert emotional_task_for_act("CLARIFY") == "uncertainty"
        assert emotional_task_for_act("TELEPORT") == "appropriate_acknowledgement"  # default


class TestEmotionalEligibility:
    def test_affective_trace_with_outcome_eligible(self):
        assert is_emotional_eligible(_emo_trace()) is True

    def test_missing_affective_evidence_not_eligible(self):
        t = _emo_trace()
        t["social_context"] = dict(t["social_context"], emotional_signal={})
        assert is_emotional_eligible(t) is False

    def test_missing_decision_not_eligible(self):
        assert is_emotional_eligible(_emo_trace(dialogue_act="", response="")) is False

    def test_silence_without_outcome_not_eligible(self):
        # plan §29: do not infer success from silence alone.
        t = _emo_trace(dialogue_act="SILENCE", response="", outcome="", correction="")
        assert is_emotional_eligible(t) is False

    def test_silence_with_explicit_outcome_eligible(self):
        t = _emo_trace(dialogue_act="SILENCE", response="", outcome="acknowledged")
        assert is_emotional_eligible(t) is True

    def test_correction_makes_eligible(self):
        t = _emo_trace(outcome="", correction="no, the blue one")
        assert is_emotional_eligible(t) is True


class TestEmotionalExport:
    def test_exports_emotional_example(self):
        exporter = EmotionalTraceExporter()
        examples = exporter.export(_emo_trace())
        assert len(examples) == 1
        ex = examples[0]
        assert ex["synthetic"] is False
        assert validate_example(ex, kind="emotional") == []

    def test_task_from_act(self):
        exporter = EmotionalTraceExporter()
        assert exporter.export(_emo_trace())[0]["task"] == "appropriate_acknowledgement"
        assert exporter.export(_emo_trace(dialogue_act="SILENCE", response=""))[0]["task"] == "appropriate_silence"

    def test_affective_hypotheses_mapped_and_normalized(self):
        exporter = EmotionalTraceExporter()
        ex = exporter.export(_emo_trace())[0]
        hyps = ex["situation"]["affective_hypotheses"]
        labels = {h["label"] for h in hyps}
        assert "frustration" in labels
        assert all(0.0 <= h["probability"] <= 1.0 for h in hyps)
        assert abs(sum(h["probability"] for h in hyps) - 1.0) < 1e-6

    def test_act_mapped_to_strategy(self):
        exporter = EmotionalTraceExporter()
        ex = exporter.export(_emo_trace())[0]
        assert ex["desired_behavior"]["act"] == ["ACKNOWLEDGE"]

    def test_conversation_phase_derived_from_temperature(self):
        exporter = EmotionalTraceExporter()
        ex = exporter.export(_emo_trace())[0]
        assert ex["situation"]["conversation_phase"] == "tension"

    def test_correction_implies_novi_caused_problem(self):
        exporter = EmotionalTraceExporter()
        ex = exporter.export(_emo_trace(correction="no, the blue one"))[0]
        assert ex["situation"]["novi_caused_problem"] is True

    def test_person_id_carried_for_privacy(self):
        exporter = EmotionalTraceExporter()
        ex = exporter.export(_emo_trace())[0]
        assert ex["situation"]["person"]["id"] == "person:vano"

    def test_response_carried_as_preferred(self):
        exporter = EmotionalTraceExporter()
        ex = exporter.export(_emo_trace())[0]
        assert ex["preferred_response"] == "Yeah, I took that the wrong way. Let me reset."

    def test_skips_ineligible_traces(self):
        exporter = EmotionalTraceExporter()
        bad = _emo_trace()
        bad["social_context"] = dict(bad["social_context"], emotional_signal={})
        assert exporter.export(bad) == []

    def test_deterministic(self):
        exporter = EmotionalTraceExporter()
        a = exporter.export(_emo_trace())[0]
        b = exporter.export(_emo_trace())[0]
        assert a == b

    def test_export_all_filters(self):
        exporter = EmotionalTraceExporter()
        good = _emo_trace()
        bad = _emo_trace(trace_id="emo-trace-2")
        bad["social_context"] = dict(bad["social_context"], emotional_signal={})
        assert len(exporter.export_all([good, bad])) == 1


class TestFailureClassification:
    def test_failure_classes_match_plan_section31(self):
        assert frozenset({
            "MISREAD_EMOTION", "OVERREACTED", "UNDERREACTED", "INTERRUPTED",
            "FAILED_TO_SUPPORT", "OVER_SUPPORTED", "IGNORED_BOUNDARY",
            "REPEATED_ERROR", "DEFENSIVE_RESPONSE", "EXCESSIVE_APOLOGY",
            "UNNATURAL_EMPATHY",
        }) == FAILURE_CLASSES

    def test_success_is_not_a_failure(self):
        assert classify_failure(_emo_trace(outcome="acknowledged")) is None

    def test_misread_emotion(self):
        t = _emo_trace(outcome="corrected", correction="I'm not frustrated, I'm fine")
        assert classify_failure(t) == "MISREAD_EMOTION"

    def test_overreacted(self):
        t = _emo_trace(outcome="negative", verbosity="long",
                       social_context={"conversation_temperature": "calm",
                                       "emotional_signal": _signal(frustration_likelihood=(0.1, 0.2))})
        assert classify_failure(t) == "OVERREACTED"

    def test_underreacted(self):
        t = _emo_trace(outcome="negative", verbosity="terse", dialogue_act="RESPOND",
                       social_context={"conversation_temperature": "tense",
                                       "emotional_signal": _signal(distress_likelihood=(0.9, 0.9))})
        assert classify_failure(t) == "UNDERREACTED"

    def test_interrupted(self):
        t = _emo_trace(dialogue_act="COMMENT", outcome="ignored",
                       social_context={"user_availability": "busy"})
        assert classify_failure(t) == "INTERRUPTED"

    def test_failed_to_support(self):
        t = _emo_trace(dialogue_act="RESPOND", outcome="negative",
                       social_context={"emotional_signal": _signal(distress_likelihood=(0.8, 0.8))})
        assert classify_failure(t) == "FAILED_TO_SUPPORT"

    def test_over_supported(self):
        t = _emo_trace(dialogue_act="SUPPORT", outcome="ignored",
                       social_context={"emotional_signal": _signal(distress_likelihood=(0.1, 0.2))})
        assert classify_failure(t) == "OVER_SUPPORTED"

    def test_ignored_boundary(self):
        t = _emo_trace(dialogue_act="ASK", outcome="negative",
                       social_context={"boundary_state": "DO_NOT_PROBE"})
        assert classify_failure(t) == "IGNORED_BOUNDARY"

    def test_repeated_error(self):
        t = _emo_trace(outcome="corrected", repeat_count=3)
        assert classify_failure(t) == "REPEATED_ERROR"

    def test_defensive_response(self):
        t = _emo_trace(outcome="negative", defensiveness="high")
        assert classify_failure(t) == "DEFENSIVE_RESPONSE"

    def test_excessive_apology(self):
        t = _emo_trace(dialogue_act="APOLOGIZE", outcome="negative", novi_caused_problem=False)
        assert classify_failure(t) == "EXCESSIVE_APOLOGY"

    def test_unnatural_empathy(self):
        t = _emo_trace(dialogue_act="SUPPORT", outcome="negative",
                       response="I understand that you are experiencing difficult emotions right now.")
        assert classify_failure(t) == "UNNATURAL_EMPATHY"


class TestFeedbackParsing:
    def test_stop_asking_is_boundary(self):
        fb = parse_feedback("Stop asking me that.")
        assert fb is not None and fb["kind"] == "boundary"

    def test_that_is_helpful_is_positive(self):
        fb = parse_feedback("That's actually helpful.")
        assert fb is not None and fb["kind"] == "positive_outcome"

    def test_dont_explain_again_is_verbosity(self):
        fb = parse_feedback("Don't explain it again.")
        assert fb is not None and fb["kind"] == "verbosity"

    def test_i_need_a_minute_is_give_space(self):
        fb = parse_feedback("I need a minute.")
        assert fb is not None and fb["kind"] == "give_space"

    def test_unknown_feedback_returns_none(self):
        assert parse_feedback("What time is it?") is None
