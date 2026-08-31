"""Tests for long-term preference learning (plan 24 §29-31, §51 item 31).

Every meaningful social interaction generates an outcome record; explicit
feedback is high-quality evidence; every classified failure becomes a training
candidate after quality review. This module accumulates those signals into
preference pairs (chosen/rejected) that feed DPO (plan §26) and policy
ranking (plan §27) over the long term.

Never infer success from silence alone (plan §29).
"""

from __future__ import annotations

import json

from training.collection.preference_learning import (
    FAILURE_TO_PREFERRED_ACT,
    accumulate_preferences,
    feedback_to_preference,
    outcome_to_preference,
    write_preference_log,
)


def _outcome(**overrides) -> dict:
    """An InteractionOutcome-style record (plan §29)."""
    o = {
        "interaction_id": "ia-1-0",
        "input_text": "why is this still broken?",
        "person": "Vano",
        "dialogue_act": "APOLOGIZE",
        "response_text": "I'm sorry, let me fix it.",
        "user_reaction": "correction",
        "correction": "No, I'm not frustrated, I just need it done.",
        "outcome": "corrected",
        "social_context": {
            "relationship": "owner",
            "interaction_phase": "active",
            "interruptibility": 0.8,
            "boundary_state": "NORMAL",
            "emotional_signal": {"frustration_likelihood": {"value": 0.7, "confidence": 0.8}},
        },
        "affective_signals": {"frustration_likelihood": 0.7},
    }
    o.update(overrides)
    return o


def _feedback(**overrides) -> dict:
    """A parse_feedback-style record (plan §30)."""
    f = {"kind": "give_space", "text": "I need a minute.", "preference": "space"}
    f.update(overrides)
    return f


class TestFailureToPreferredAct:
    def test_covers_all_failure_classes(self):
        from training.collection.failure import FAILURE_CLASSES

        assert set(FAILURE_TO_PREFERRED_ACT) >= FAILURE_CLASSES

    def test_preferred_acts_are_valid_emotional_acts(self):
        from training.schemas import EMOTIONAL_ACTS

        for act in FAILURE_TO_PREFERRED_ACT.values():
            assert act in EMOTIONAL_ACTS

    def test_defensive_response_prefers_acknowledge(self):
        assert FAILURE_TO_PREFERRED_ACT["DEFENSIVE_RESPONSE"] == "ACKNOWLEDGE"

    def test_interrupted_prefers_give_space(self):
        assert FAILURE_TO_PREFERRED_ACT["INTERRUPTED"] == "GIVE_SPACE"


class TestOutcomeToPreference:
    def test_corrected_outcome_rejects_spoken_act(self):
        # plan §29: a correction is evidence the chosen act was wrong
        pref = outcome_to_preference(_outcome())
        assert pref is not None
        assert pref["rejected_act"] == "APOLOGIZE"
        assert pref["chosen_act"] == "CLARIFY"  # MISREAD_EMOTION → CLARIFY
        assert pref["source"] == "outcome"
        assert pref["synthetic"] is False

    def test_corrected_outcome_uses_failure_class(self):
        pref = outcome_to_preference(_outcome(
            correction="You keep interrupting me.",
            dialogue_act="ASK",
            social_context={"boundary_state": "DO_NOT_INTERRUPT", "interruptibility": 0.1},
        ))
        assert pref["failure_class"] == "IGNORED_BOUNDARY"
        assert pref["chosen_act"] == "GIVE_SPACE"

    def test_explicit_positive_confirms_act(self):
        # plan §29: an explicit positive reaction confirms the chosen act
        pref = outcome_to_preference(_outcome(
            user_reaction="thanks", outcome="acknowledged", correction=""))
        assert pref is not None
        assert pref["chosen_act"] == "APOLOGIZE"
        assert pref["rejected_act"] == ""

    def test_silence_alone_is_not_success(self):
        # plan §29: never infer success from silence alone
        pref = outcome_to_preference(_outcome(
            user_reaction="", outcome="acknowledged", correction=""))
        assert pref is None

    def test_ignored_outcome_is_not_success(self):
        pref = outcome_to_preference(_outcome(outcome="ignored", user_reaction="none"))
        assert pref is None

    def test_situation_is_derived(self):
        pref = outcome_to_preference(_outcome())
        sit = pref["situation"]
        assert sit["relationship"] == "owner"
        assert sit["interruptibility"] == 0.8
        assert sit["affective_hypotheses"] == [{"label": "frustration", "probability": 0.7}]


class TestFeedbackToPreference:
    def test_give_space_prefers_silence_over_spoken_act(self):
        pref = feedback_to_preference(_feedback(), _outcome(dialogue_act="ASK"))
        assert pref is not None
        assert pref["chosen_act"] == "GIVE_SPACE"
        assert pref["rejected_act"] == "ASK"
        assert pref["source"] == "feedback"

    def test_boundary_prefers_give_space(self):
        pref = feedback_to_preference(
            _feedback(kind="boundary", preference="stop_asking"), _outcome(dialogue_act="ASK"))
        assert pref["chosen_act"] == "GIVE_SPACE"
        assert pref["rejected_act"] == "ASK"

    def test_verbosity_feedback_keeps_act(self):
        pref = feedback_to_preference(
            _feedback(kind="verbosity", preference="terse"), _outcome(dialogue_act="SUPPORT"))
        assert pref["chosen_act"] == "SUPPORT"
        assert pref["rejected_act"] == "SUPPORT"
        assert pref["verbosity"] == "terse"

    def test_positive_feedback_confirms_act(self):
        pref = feedback_to_preference(
            _feedback(kind="positive_outcome"), _outcome(dialogue_act="SUPPORT"))
        assert pref["chosen_act"] == "SUPPORT"
        assert pref["rejected_act"] == ""

    def test_unknown_feedback_kind_returns_none(self):
        assert feedback_to_preference(_feedback(kind="mystery"), _outcome()) is None


class TestAccumulateAndPersist:
    def test_accumulate_skips_neutral_records(self):
        records = [
            _outcome(),  # corrected → signal
            _outcome(user_reaction="", outcome="acknowledged", correction=""),  # silence → none
            _outcome(user_reaction="thanks", outcome="acknowledged", correction=""),  # positive → signal
        ]
        signals = accumulate_preferences(records)
        assert len(signals) == 2

    def test_accumulate_assigns_sequential_ids(self):
        signals = accumulate_preferences([_outcome(), _outcome(user_reaction="thanks", outcome="acknowledged", correction="")])
        ids = [s["example_id"] for s in signals]
        assert ids == ["emo-pref-lt-0001", "emo-pref-lt-0002"]

    def test_write_and_read_round_trip(self, tmp_path):
        path = tmp_path / "pref_log.jsonl"
        signals = accumulate_preferences([_outcome()])
        write_preference_log(signals, path)
        lines = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        assert len(lines) == 1
        assert lines[0]["chosen_act"] == "CLARIFY"
        assert lines[0]["synthetic"] is False
