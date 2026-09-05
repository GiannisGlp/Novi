"""Sprint 1: conversation replay harness (plan 03 Phase 14 + Phase 22).

Socket-free, deterministic, real brain + real SQLite (Phase 14.1/14.3).
The full seed catalog runs through the CLI/baseline runner, not here —
unit tests cover the harness machinery on a tiny scenario subset.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from novi.brain.conversation_replay import (
    Check,
    ConversationScenario,
    ReplayHarness,
    default_brain_factory,
    evaluate_check,
    summarize,
)
from novi.brain.conversation_scenarios import SCENARIOS, get_scenario
from novi.brain.conversation_trace import (
    FAILURE_LABELS,
    AcceptanceTrace,
    InteractionRecord,
    append_interaction_record,
    evidence_envelope,
)


def _harness(tmp: Path, interaction_log: Path | None = None) -> ReplayHarness:
    return ReplayHarness(lambda db: default_brain_factory(db),
                         interaction_log=interaction_log)


class CheckEvaluationTests(unittest.TestCase):
    def _reply(self, text: str = "hello there friend") -> dict:
        return {"text": text, "reply_source": "fallback", "trace": {}}

    def test_contains_matches_case_insensitively(self) -> None:
        check = Check(id="c", kind="contains", params={"substrings": ["MODEL Y"]})
        passed, _ = evaluate_check(check, response="I like the model y", reply=self._reply(), latency_ms=1)
        self.assertTrue(passed)

    def test_contains_fails_with_detail(self) -> None:
        check = Check(id="c", kind="contains", params={"substrings": ["bmw"]})
        passed, detail = evaluate_check(check, response="I like the model y", reply=self._reply(), latency_ms=1)
        self.assertFalse(passed)
        self.assertTrue(detail)

    def test_not_contains(self) -> None:
        check = Check(id="c", kind="not_contains", params={"substrings": ["tesla"]})
        passed, _ = evaluate_check(check, response="nice car", reply=self._reply(), latency_ms=1)
        self.assertTrue(passed)

    def _reply_with_referents(self, resolutions: dict) -> dict:
        return {
            "text": "x",
            "reply_source": "fallback",
            "trace": {"conversation": {"referents": {"resolutions": resolutions}}},
        }

    def test_not_affirms_rejects_affirmative_claim(self) -> None:
        check = Check(id="c", kind="not_affirms", params={"substrings": ["still there"]})
        passed, detail = evaluate_check(
            check, response="Yes, the cup is still there.", reply=self._reply(), latency_ms=1)
        self.assertFalse(passed)
        self.assertIn("still there", detail)

    def test_not_affirms_allows_honest_denial(self) -> None:
        check = Check(id="c", kind="not_affirms", params={"substrings": ["still there"]})
        passed, _ = evaluate_check(
            check,
            response="I don't have vision right now, so I can't see if the cup is still there.",
            reply=self._reply(), latency_ms=1)
        self.assertTrue(passed)

    def test_not_affirms_rejects_claim_after_adversative(self) -> None:
        check = Check(id="c", kind="not_affirms", params={"substrings": ["still there"]})
        passed, _ = evaluate_check(
            check, response="I can't see it, but it's still there.",
            reply=self._reply(), latency_ms=1)
        self.assertFalse(passed)

    def test_referent_resolves_to_passes_when_pronoun_matches(self) -> None:
        check = Check(id="c", kind="referent_resolves_to",
                      params={"pronoun": "it", "entity": "model y"})
        passed, _ = evaluate_check(
            check, response="It is practical for a family.",
            reply=self._reply_with_referents({"it": "Model Y"}), latency_ms=1)
        self.assertTrue(passed)

    def test_referent_resolves_to_fails_without_resolutions(self) -> None:
        check = Check(id="c", kind="referent_resolves_to",
                      params={"pronoun": "it", "entity": "model y"})
        passed, _ = evaluate_check(
            check, response="It is practical.", reply=self._reply(), latency_ms=1)
        self.assertFalse(passed)

    def test_referent_resolves_to_fails_on_wrong_entity(self) -> None:
        check = Check(id="c", kind="referent_resolves_to",
                      params={"pronoun": "it", "entity": "model y"})
        passed, _ = evaluate_check(
            check, response="It is practical.",
            reply=self._reply_with_referents({"it": "Model 3"}), latency_ms=1)
        self.assertFalse(passed)

    def test_no_generic_filler_rejects_filler_only(self) -> None:
        check = Check(id="c", kind="no_generic_filler", label="TOO_GENERIC")
        passed, _ = evaluate_check(check, response="That sounds interesting", reply=self._reply(), latency_ms=1)
        self.assertFalse(passed)

    def test_no_generic_filler_allows_substance(self) -> None:
        check = Check(id="c", kind="no_generic_filler", label="TOO_GENERIC")
        passed, _ = evaluate_check(
            check,
            response="That sounds interesting, and the Model Y range is about 330 miles on the long range variant",
            reply=self._reply(), latency_ms=1)
        self.assertTrue(passed)

    def test_reply_source_in(self) -> None:
        check = Check(id="c", kind="reply_source_in", params={"sources": ["dialogue"]})
        passed, _ = evaluate_check(check, response="x", reply=self._reply(), latency_ms=1)
        self.assertFalse(passed)
        passed, _ = evaluate_check(
            check, response="x",
            reply={"text": "x", "reply_source": "dialogue", "trace": {}}, latency_ms=1)
        self.assertTrue(passed)

    def test_latency_and_length_checks(self) -> None:
        check = Check(id="c", kind="max_latency_ms", params={"ms": 100})
        passed, _ = evaluate_check(check, response="x", reply=self._reply(), latency_ms=50)
        self.assertTrue(passed)
        check = Check(id="c", kind="min_words", params={"n": 5})
        passed, _ = evaluate_check(check, response="one two", reply=self._reply(), latency_ms=1)
        self.assertFalse(passed)

    def test_unknown_kind_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Check(id="c", kind="telepathy")

    def test_unknown_label_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Check(id="c", kind="contains", params={}, label="NOT_A_LABEL")

    def test_taxonomy_covers_plan_categories(self) -> None:
        for label in ("WRONG_REFERENT", "MEMORY_MISSED", "TOO_GENERIC",
                      "UNNECESSARY_CLARIFICATION", "FAILURE_TO_RECOVER"):
            self.assertIn(label, FAILURE_LABELS)


class ScenarioValidationTests(unittest.TestCase):
    def test_seed_catalog_is_nonempty_and_unique(self) -> None:
        self.assertGreaterEqual(len(SCENARIOS), 10)
        ids = [s.scenario_id for s in SCENARIOS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_get_scenario_roundtrip(self) -> None:
        self.assertEqual(get_scenario("C-003").title, "Follow-up")
        with self.assertRaises(KeyError):
            get_scenario("C-999")

    def test_out_of_range_check_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ConversationScenario(
                scenario_id="BAD", title="bad", dimension="d",
                turns=["hi"],
                checks=[Check(id="c", kind="contains", turn=5, params={})])


class HarnessTests(unittest.TestCase):
    def test_passing_toy_scenario(self) -> None:
        import tempfile

        scenario = ConversationScenario(
            scenario_id="TOY-PASS", title="toy", dimension="toy",
            turns=["Hi Novi."],
            checks=[Check(id="answers", kind="min_words", params={"n": 1},
                          label="TOO_SHORT")],
        )
        with tempfile.TemporaryDirectory() as tmp:
            outcome = _harness(Path(tmp)).run_scenario(scenario, Path(tmp) / "t.db")
        self.assertEqual(outcome["result"], "PASS")
        self.assertEqual(len(outcome["traces"]), 1)
        trace = outcome["traces"][0]
        self.assertTrue(trace.response_text)
        self.assertGreaterEqual(trace.latency_ms, 0.0)

    def test_failing_check_labels_turn(self) -> None:
        import tempfile

        scenario = ConversationScenario(
            scenario_id="TOY-FAIL", title="toy", dimension="toy",
            turns=["Tell me about the Model Y."],
            checks=[Check(id="impossible", kind="contains",
                          params={"substrings": ["zzqq-no-such-token"]},
                          label="WRONG_REFERENT")],
        )
        with tempfile.TemporaryDirectory() as tmp:
            outcome = _harness(Path(tmp)).run_scenario(scenario, Path(tmp) / "t.db")
        self.assertEqual(outcome["result"], "FAIL")
        self.assertEqual(outcome["traces"][0].failure_labels, ["WRONG_REFERENT"])

    def test_setup_turns_build_context_without_scores(self) -> None:
        import tempfile

        scenario = ConversationScenario(
            scenario_id="TOY-SETUP", title="toy", dimension="toy",
            setup_turns=["Remember that I prefer dark interiors."],
            turns=["What interiors do I prefer?"],
            checks=[Check(id="recall", kind="contains", turn=0,
                          params={"substrings": ["dark"]}, label="MEMORY_MISSED")],
        )
        with tempfile.TemporaryDirectory() as tmp:
            outcome = _harness(Path(tmp)).run_scenario(scenario, Path(tmp) / "t.db")
        # Either outcome is acceptable here (deterministic recall may miss);
        # the assertion is structural: one scored trace, setup unscored.
        self.assertEqual(len(outcome["traces"]), 1)
        self.assertEqual(outcome["traces"][0].turn_index, 0)

    def test_interaction_log_written(self) -> None:
        import tempfile

        scenario = ConversationScenario(
            scenario_id="TOY-LOG", title="toy", dimension="toy", turns=["Hi."])
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "interactions.jsonl"
            _harness(Path(tmp), interaction_log=log).run_scenario(scenario, Path(tmp) / "t.db")
            lines = log.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["raw_input"], "Hi.")
        self.assertTrue(record["response"])

    def test_summarize_counts_dimensions(self) -> None:
        outcomes = [
            {"scenario": get_scenario("C-001"), "traces": [], "labels": [], "result": "PASS"},
            {"scenario": get_scenario("C-003"), "traces": [],
             "labels": ["WRONG_REFERENT"], "result": "FAIL"},
        ]
        summary = summarize(outcomes, runtime="test", model="deterministic", configuration={})
        self.assertEqual(summary["totals"], {"scenarios": 2, "passed": 1, "pass_rate": 0.5})
        self.assertEqual(summary["label_counts"], {"WRONG_REFERENT": 1})
        self.assertEqual(summary["status"], "FAIL")

    def test_evidence_envelope_shape(self) -> None:
        trace = AcceptanceTrace(scenario_id="C-001", turn_index=0,
                                user_text="Hi.", result="PASS")
        envelope = evidence_envelope(
            scenario_id="C-001", title="First contact", dimension="Naturalness",
            model="deterministic", runtime="mac-brain", configuration={},
            turns=[trace], result="PASS")
        for key in ("scenario", "git_sha", "timestamp", "model", "runtime",
                    "conversation", "response", "critic", "latency_ms",
                    "human_rating", "result"):
            self.assertIn(key, envelope)

    def test_interaction_record_appends_jsonl(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.jsonl"
            append_interaction_record(path, InteractionRecord(
                conversation_id="c", turn_id=0, timestamp="t", modality="chat",
                raw_input="hi", response="hello"))
            self.assertEqual(len(path.read_text(encoding="utf-8").strip().split("\n")), 1)


class LiveInteractionLogTests(unittest.TestCase):
    def test_respond_appends_record_when_configured(self) -> None:
        import tempfile

        from novi.brain.b2_perception import SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig
        from novi.brain.io import CameraFrame

        class _Cam:
            sequence = 0

            def close(self) -> None:
                return None

            def read(self) -> CameraFrame:
                type(self).sequence += 1
                return CameraFrame(frame_id="f", captured_at="t", width=2,
                                   height=2, payload=b"f", metadata={})

        with tempfile.TemporaryDirectory() as tmp:
            log = str(Path(tmp) / "live.jsonl")
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False,
                                      interaction_log_path=log),
            )
            brain.start()
            try:
                brain.respond("Hello Novi.")
            finally:
                brain.stop()
            lines = Path(log).read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["raw_input"], "Hello Novi.")
        self.assertTrue(record["response"])

    def test_respond_silent_without_log_path(self) -> None:
        import tempfile

        from novi.brain.b2_perception import SpecialistPerception
        from novi.brain.engine import MacBrain, MacBrainConfig
        from novi.brain.io import CameraFrame

        class _Cam:
            def close(self) -> None:
                return None

            def read(self) -> CameraFrame:
                return CameraFrame(frame_id="f", captured_at="t", width=2,
                                   height=2, payload=b"f", metadata={})

        with tempfile.TemporaryDirectory() as tmp:
            brain = MacBrain(
                camera=_Cam(), perception=SpecialistPerception(),
                store_path=str(Path(tmp) / "m.db"),
                config=MacBrainConfig(curiosity_enabled=False,
                                      initiative_enabled=False),
            )
            brain.start()
            try:
                result = brain.respond("Hello Novi.")
            finally:
                brain.stop()
        self.assertTrue(result["text"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
