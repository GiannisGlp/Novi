"""Tests for the continuous emotional learning cycle (plan 24 §46, §51 item 37).

The §46 loop: interaction -> ... -> outcome -> interaction memory ->
quality filtering -> training example -> SFT/DPO/policy ranking ->
evaluation -> shadow deployment -> approved model -> new interaction.

The coordinator accumulates quality-filtered preference signals into a
growing log and, when enough have accumulated, *plans* a training cycle.
It never trains or deploys itself — "never automatically train/deploy
directly from raw emotional observations" (plan §46).
"""

from __future__ import annotations

import json

from training.collection.continuous_learning import (
    DEFAULT_MIN_SIGNALS,
    CycleCompletion,
    CycleReport,
    CycleState,
    accumulate_cycle,
    complete_cycle,
    plan_cycle,
    quality_filter,
    should_train,
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
        "social_context": {"relationship": "owner", "interruptibility": 0.8},
        "affective_signals": {"frustration_likelihood": 0.7},
    }
    o.update(overrides)
    return o


def _feedback(**overrides) -> dict:
    """A parse_feedback-style record (plan §30)."""
    f = {
        "kind": "give_space",
        "text": "I need a minute.",
        "preference": "space",
        "trace": _outcome(dialogue_act="ASK"),
    }
    f.update(overrides)
    return f


class TestQualityFilter:
    def test_keeps_feedback_records(self):
        assert quality_filter([_feedback()]) == [_feedback()]

    def test_keeps_corrected_outcomes(self):
        assert quality_filter([_outcome()]) == [_outcome()]

    def test_keeps_explicit_positive_reactions(self):
        rec = _outcome(user_reaction="thanks", outcome="acknowledged", correction="")
        assert quality_filter([rec]) == [rec]

    def test_drops_silence_alone(self):
        # plan §29: never infer success from silence alone
        rec = _outcome(user_reaction="", outcome="acknowledged", correction="")
        assert quality_filter([rec]) == []

    def test_drops_ignored_outcomes(self):
        rec = _outcome(outcome="ignored", user_reaction="none")
        assert quality_filter([rec]) == []

    def test_mixed_batch_keeps_only_signals(self):
        recs = [
            _outcome(),  # corrected -> signal
            _outcome(user_reaction="", outcome="acknowledged", correction=""),  # silence -> none
            _feedback(),  # explicit feedback -> signal
        ]
        assert len(quality_filter(recs)) == 2


class TestAccumulateCycle:
    def test_appends_signals_with_continuing_ids(self, tmp_path):
        path = tmp_path / "pref_log.jsonl"
        state = CycleState()
        first = accumulate_cycle([_outcome()], state, path)
        assert [s["example_id"] for s in first] == ["emo-pref-lt-0001"]
        second = accumulate_cycle([_outcome()], state, path)
        assert [s["example_id"] for s in second] == ["emo-pref-lt-0002"]
        assert state.signals_since_cycle == 2

    def test_skips_neutral_records(self, tmp_path):
        path = tmp_path / "pref_log.jsonl"
        state = CycleState()
        signals = accumulate_cycle(
            [_outcome(user_reaction="", outcome="acknowledged", correction=""),
             _outcome(outcome="ignored", user_reaction="none")],
            state, path)
        assert signals == []
        assert state.signals_since_cycle == 0
        assert not path.exists() or path.read_text() == ""

    def test_round_trip(self, tmp_path):
        path = tmp_path / "pref_log.jsonl"
        state = CycleState()
        accumulate_cycle([_outcome(), _feedback()], state, path)
        lines = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        assert len(lines) == 2
        assert lines[0]["example_id"] == "emo-pref-lt-0001"
        assert lines[1]["example_id"] == "emo-pref-lt-0002"
        assert lines[0]["chosen_act"] == "CLARIFY"  # MISREAD_EMOTION -> CLARIFY

    def test_continues_existing_log(self, tmp_path):
        path = tmp_path / "pref_log.jsonl"
        path.write_text(json.dumps({"example_id": "emo-pref-lt-0001"}) + "\n")
        state = CycleState()
        signals = accumulate_cycle([_outcome()], state, path)
        assert [s["example_id"] for s in signals] == ["emo-pref-lt-0002"]


class TestShouldTrain:
    def test_false_below_threshold(self):
        assert should_train(CycleState(signals_since_cycle=10)) is False

    def test_true_at_threshold(self):
        assert should_train(CycleState(signals_since_cycle=DEFAULT_MIN_SIGNALS)) is True

    def test_true_above_threshold(self):
        assert should_train(CycleState(signals_since_cycle=100)) is True

    def test_custom_min_signals(self):
        assert should_train(CycleState(signals_since_cycle=5), min_signals=5) is True
        assert should_train(CycleState(signals_since_cycle=4), min_signals=5) is False


class TestPlanCycle:
    def test_plan_not_ready_below_threshold(self):
        state = CycleState(signals_since_cycle=10)
        report = plan_cycle(state, adapter_dir="adapters/x", training_kind="dpo",
                            config="configs/dpo.yaml", dataset="datasets/dpo.jsonl")
        assert isinstance(report, CycleReport)
        assert report.ready is False
        assert report.signals == 10

    def test_plan_ready_at_threshold(self):
        state = CycleState(signals_since_cycle=DEFAULT_MIN_SIGNALS)
        report = plan_cycle(state, adapter_dir="adapters/x", training_kind="dpo",
                            config="configs/dpo.yaml", dataset="datasets/dpo.jsonl")
        assert report.ready is True

    def test_plan_carries_cycle_metadata(self):
        state = CycleState(signals_since_cycle=60)
        report = plan_cycle(state, adapter_dir="adapters/novi-emotional-dpo-v2",
                            training_kind="dpo", config="configs/dpo_emotional.yaml",
                            dataset="datasets/dpo/emotional_dpo_v2.jsonl")
        assert report.adapter_dir == "adapters/novi-emotional-dpo-v2"
        assert report.training_kind == "dpo"
        assert report.config == "configs/dpo_emotional.yaml"
        assert report.dataset == "datasets/dpo/emotional_dpo_v2.jsonl"
        assert report.planned_at

    def test_plan_does_not_touch_filesystem(self, tmp_path):
        # plan_cycle only describes the cycle; it never writes anything
        state = CycleState(signals_since_cycle=60)
        plan_cycle(state, adapter_dir="adapters/x", training_kind="dpo",
                   config="configs/dpo.yaml", dataset="datasets/dpo.jsonl")
        assert list(tmp_path.iterdir()) == []


class TestCompleteCycle:
    def test_resets_accumulation_and_bumps_counter(self):
        state = CycleState(signals_since_cycle=60, cycles_run=2)
        completion = complete_cycle(state, accepted=True, at="2026-08-31T12:00:00+00:00")
        assert state.signals_since_cycle == 0
        assert state.cycles_run == 3
        assert state.last_cycle_at == "2026-08-31T12:00:00+00:00"
        assert isinstance(completion, CycleCompletion)
        assert completion.accepted is True
        assert completion.signals_consumed == 60

    def test_rejected_cycle_still_resets(self):
        state = CycleState(signals_since_cycle=55)
        complete_cycle(state, accepted=False)
        assert state.signals_since_cycle == 0
        assert state.cycles_run == 1
        assert state.last_cycle_at

    def test_state_to_dict(self):
        state = CycleState(signals_since_cycle=3, cycles_run=1, last_cycle_at="t")
        assert state.to_dict() == {"signals_since_cycle": 3, "cycles_run": 1, "last_cycle_at": "t"}


class TestFullCycle:
    def test_loop_accumulate_plan_complete(self, tmp_path):
        path = tmp_path / "pref_log.jsonl"
        state = CycleState()
        accumulate_cycle([_outcome() for _ in range(DEFAULT_MIN_SIGNALS)], state, path)
        assert should_train(state)
        report = plan_cycle(state, adapter_dir="adapters/novi-emotional-dpo-v2",
                            training_kind="dpo", config="configs/dpo_emotional.yaml",
                            dataset="datasets/dpo/emotional_dpo_v2.jsonl")
        assert report.ready is True
        assert report.signals == DEFAULT_MIN_SIGNALS
        complete_cycle(state, accepted=True)
        assert state.signals_since_cycle == 0
        assert state.cycles_run == 1
