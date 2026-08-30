"""Tests for plan 22 Phase 22–24: world simulator trace, decision traces,
and evaluation metrics."""

from __future__ import annotations

import unittest

from novi.brain.decision_trace import TraceRecorder
from novi.brain.dialogue_policy import DialogueContext, DialoguePolicy
from novi.brain.social_metrics import SocialMetricsTracker
from novi.brain.world_simulator import SimEvent, WorldSimulator


class WorldSimulatorTest(unittest.TestCase):
    def test_plan_example_timeline_trace(self) -> None:
        """Plan §26: T0–T8 with the expected trace invariants."""
        sim = WorldSimulator(WorldSimulator.plan_example_timeline(), seed=7)
        seen: dict[str, str] = {}
        identity_recognized = False
        social_opportunity_rose = False
        response_decided = False
        mug_identity = False
        mug_disappeared = False

        def observe(evt: SimEvent) -> None:
            nonlocal identity_recognized, social_opportunity_rose, response_decided, mug_identity, mug_disappeared
            seen[evt.at] = evt.kind
            if evt.kind == "person.entered" and evt.detail.get("identity_confidence", 0) >= 0.95:
                identity_recognized = True
            if evt.kind == "gaze" and evt.detail.get("at_novi"):
                social_opportunity_rose = True
            if evt.kind == "speech" and evt.entity == "vano":
                response_decided = True
            if evt.kind == "object.placed":
                mug_identity = True
            if evt.kind == "object.disappeared":
                mug_disappeared = True

        trace = sim.play(observe)
        self.assertEqual(len(trace), 9)
        # expected trace invariants (plan §26)
        self.assertTrue(identity_recognized, "T1 identity recognized")
        self.assertTrue(social_opportunity_rose, "T2 social opportunity rises")
        self.assertTrue(response_decided, "T3 response decision")
        self.assertTrue(mug_identity, "T5 object identity established")
        self.assertEqual(seen.get("T6"), "person.left")
        self.assertTrue(mug_disappeared, "T7 object disappearance event")
        self.assertEqual(seen.get("T8"), "person.entered")

    def test_deterministic_noise(self) -> None:
        a = WorldSimulator([], seed=1).noisy(0.5)
        b = WorldSimulator([], seed=1).noisy(0.5)
        c = WorldSimulator([], seed=2).noisy(0.5)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_policy_responds_to_simulated_entrance(self) -> None:
        """P2 through the simulator: known person enters → greeting."""
        policy = DialoguePolicy()
        sim = WorldSimulator([SimEvent("T1", "person.entered", "vano", {"identity_confidence": 0.97})])
        decisions = []

        def observe(evt: SimEvent) -> None:
            if evt.kind == "person.entered":
                dec = policy.decide(DialogueContext(
                    person_entered=True, addressee=evt.entity, addressee_known=True,
                    social_opportunity=0.7, interruptibility=1.0,
                ))
                decisions.append(dec.act.value)

        sim.play(observe)
        self.assertEqual(decisions, ["GREETING"])


class DecisionTraceTest(unittest.TestCase):
    def test_trace_captures_full_decision_context(self) -> None:
        rec = TraceRecorder()
        t = rec.new_trace(cycle_id=7, input_event="person.entered:vano")
        t.perception_evidence = ["vano@0.97"]
        t.identity_resolution = {"name": "vano", "status": "RECOGNIZED"}
        t.retrieved_memories = ["mem-1", "mem-2"]
        t.attention_scores = [{"entity": "vano", "score": 0.9}]
        t.social_context = {"interaction_phase": "active"}
        t.dialogue_act = "GREETING"
        t.dialogue_reason = "person_entered"
        t.initiative_score = 0.86
        t.llm_model = "qwen3:8b"
        t.llm_latency_s = 1.2
        t.response = "hey vano"
        t.memory_writes = ["mem-3"]
        snap = t.snapshot()
        self.assertEqual(snap["cycle_id"], 7)
        self.assertEqual(snap["dialogue_act"], "GREETING")
        self.assertEqual(snap["llm_model"], "qwen3:8b")
        self.assertIn("identity_resolution", snap)
        self.assertIn("initiative_score", snap)

    def test_bounded_and_findable(self) -> None:
        rec = TraceRecorder(max_traces=4)
        for i in range(10):
            rec.new_trace(cycle_id=i, input_event=f"evt-{i}")
        self.assertLessEqual(len(rec._traces), 4)
        latest = rec.latest()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.cycle_id, 9)  # type: ignore[union-attr]
        self.assertIsNotNone(rec.find(latest.trace_id))  # type: ignore[union-attr]


class SocialMetricsTest(unittest.TestCase):
    def test_rates_computed(self) -> None:
        m = SocialMetricsTracker()
        m.record_grounding(correct=True)
        m.record_grounding(correct=True)
        m.record_grounding(correct=False)
        m.record_initiative(appropriate=True)
        m.record_initiative(appropriate=False)
        m.record_initiative(appropriate=False, duplicate=True)
        m.record_utterance()
        m.record_repetition()
        m.record_cooldown_violation()
        m.record_claim()
        m.record_unsupported_claim()
        rep = m.report()
        self.assertAlmostEqual(rep.rates["grounding_accuracy"], 2 / 3)
        self.assertAlmostEqual(rep.rates["appropriate_initiative_rate"], 1 / 3)
        self.assertAlmostEqual(rep.rates["duplicate_initiative_rate"], 1 / 3)
        self.assertEqual(rep.rates["cooldown_violations"], 1.0)
        self.assertAlmostEqual(rep.rates["unsupported_claim_rate"], 0.5)
        self.assertAlmostEqual(rep.rates["repetition_rate"], 0.5)

    def test_no_division_by_zero(self) -> None:
        rep = SocialMetricsTracker().report()
        self.assertEqual(rep.rates["grounding_accuracy"], 0.0)

    def test_safety_metric_ambiguous_actions_blocked(self) -> None:
        m = SocialMetricsTracker()
        m.record_ambiguous_action_blocked()
        m.record_ambiguous_action_blocked()
        self.assertEqual(m.report().counters["ambiguous_actions_blocked"], 2)


if __name__ == "__main__":
    unittest.main()
