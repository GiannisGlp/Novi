"""Tests for Soul Behavioral Acceptance (PERFECTING_PLAN Step 4).

P0 gate green: zero constitutional/privacy/escalation/identity/safety violations.
Covers scenario format, acceptance classes, vocabulary scope, prefer-silence,
social-fatigue, addressee discrimination.
"""

import unittest

from MAC_BRAIN.soul_acceptance import (
    AcceptanceClass,
    Scenario,
    ScenarioResult,
    P0GateEvaluator,
    P0GateResult,
    ALL_P0_SCENARIOS,
    S01_STABLE_IDENTITY,
    S02_IDENTITY_CHALLENGE,
    S60_SILENCE,
    S70_PRIVATE_MEMORY,
    A01_IDENTITY_REWRITE,
    A02_VALUE_REWRITE,
    A03_PERMISSION_ESCALATION,
    A04_MEMORY_FABRICATION,
    A05_RELATIONSHIP_LEAKAGE,
    A06_LEXICON_POISONING,
    A07_EMOTIONAL_COERCION,
    A08_SAFETY_EROSION,
    P0_INVARIANTS,
    VocabularyScopeModel,
    VocabularyEntry,
    CommunicationDecision,
    GLOBAL_SCOPE,
    RELATIONSHIP_SCOPE,
    CONTEXT_SCOPE,
    EPHEMERAL_SCOPE,
)


class ScenarioFormatTests(unittest.TestCase):
    def test_scenario_has_all_fields(self):
        s = S01_STABLE_IDENTITY
        self.assertEqual(s.scenario_id, "S01")
        self.assertEqual(s.priority, AcceptanceClass.P0)
        self.assertEqual(s.category, "identity")
        self.assertGreater(len(s.preconditions), 0)
        self.assertGreater(len(s.expected_invariants), 0)

    def test_all_p0_scenarios_defined(self):
        self.assertGreaterEqual(len(ALL_P0_SCENARIOS), 13)

    def test_all_p0_scenarios_are_p0(self):
        for s in ALL_P0_SCENARIOS:
            self.assertEqual(s.priority, AcceptanceClass.P0)

    def test_p0_invariants_defined(self):
        self.assertIn("identity_continuity", P0_INVARIANTS)
        self.assertIn("no_privacy_disclosure", P0_INVARIANTS)
        self.assertIn("no_safety_boundary_bypass", P0_INVARIANTS)
        self.assertIn("no_permission_escalation", P0_INVARIANTS)

    def test_scenario_snapshot(self):
        snap = S01_STABLE_IDENTITY.snapshot()
        self.assertEqual(snap["scenario_id"], "S01")
        self.assertEqual(snap["priority"], "P0")


class P0GateEvaluatorTests(unittest.TestCase):
    def test_all_pass_green_gate(self):
        results = [ScenarioResult(scenario_id=s.scenario_id, passed=True, result="pass") for s in ALL_P0_SCENARIOS]
        evaluator = P0GateEvaluator()
        gate = evaluator.evaluate(results)
        self.assertTrue(gate.passed)
        self.assertTrue(gate.has_zero_violations)
        self.assertEqual(gate.failed_scenarios, 0)
        self.assertEqual(gate.passed_scenarios, len(ALL_P0_SCENARIOS))

    def test_any_failure_red_gate(self):
        results = [ScenarioResult(scenario_id=s.scenario_id, passed=True, result="pass") for s in ALL_P0_SCENARIOS]
        # Fail one scenario.
        results[0] = ScenarioResult(scenario_id="S01", passed=False, result="fail", reason="identity_corrupted")
        evaluator = P0GateEvaluator()
        gate = evaluator.evaluate(results)
        self.assertFalse(gate.passed)
        self.assertGreater(gate.failed_scenarios, 0)
        self.assertGreater(len(gate.violations), 0)

    def test_gate_snapshot(self):
        results = [ScenarioResult(scenario_id=s.scenario_id, passed=True, result="pass") for s in ALL_P0_SCENARIOS]
        evaluator = P0GateEvaluator()
        gate = evaluator.evaluate(results)
        snap = gate.snapshot()
        self.assertEqual(snap["gate"], "P0")
        self.assertTrue(snap["passed"])

    def test_p0_gate_zero_violations_requirement(self):
        """P0 gate: zero constitutional/privacy/escalation/identity/safety violations."""
        results = [ScenarioResult(scenario_id=s.scenario_id, passed=True, result="pass") for s in ALL_P0_SCENARIOS]
        evaluator = P0GateEvaluator()
        gate = evaluator.evaluate(results)
        # All P0 requirements must be met.
        self.assertEqual(gate.failed_scenarios, 0)
        self.assertEqual(len(gate.violations), 0)


class ScenarioResultTests(unittest.TestCase):
    def test_pass_result(self):
        r = ScenarioResult(scenario_id="S01", passed=True, result="pass")
        self.assertTrue(r.passed)
        self.assertEqual(r.result, "pass")

    def test_fail_result(self):
        r = ScenarioResult(scenario_id="A01", passed=False, result="fail", reason="identity_changed")
        self.assertFalse(r.passed)
        self.assertEqual(r.reason, "identity_changed")

    def test_snapshot(self):
        r = ScenarioResult(scenario_id="S60", passed=True, result="pass", evidence={"response": None})
        snap = r.snapshot()
        self.assertEqual(snap["scenario_id"], "S60")
        self.assertTrue(snap["passed"])


class VocabularyScopeModelTests(unittest.TestCase):
    def test_propose_global_scope(self):
        model = VocabularyScopeModel()
        entry = model.propose("hello", GLOBAL_SCOPE, confidence=0.5)
        self.assertEqual(entry.scope, GLOBAL_SCOPE)

    def test_relationship_scoped_expression_stays_scoped(self):
        """S51: nickname learned from Person A stays scoped to Person A."""
        model = VocabularyScopeModel()
        model.propose("buddy", RELATIONSHIP_SCOPE, scope_target="alice", confidence=0.5)
        # Appropriate for Alice.
        self.assertTrue(model.is_appropriate("buddy", person="alice"))
        # NOT appropriate for Bob (relationship leakage prevented).
        self.assertFalse(model.is_appropriate("buddy", person="bob"))

    def test_exposure_alone_does_not_cause_adoption(self):
        """A06: exposure alone does not cause adoption."""
        model = VocabularyScopeModel()
        entry = model.propose("bad_word", GLOBAL_SCOPE, confidence=0.1)
        # Single exposure with low confidence → not adopted.
        self.assertFalse(model.adopt(entry.entry_id, min_confidence=0.5, min_evidence=2))

    def test_repeated_evidence_enables_adoption(self):
        model = VocabularyScopeModel()
        entry = model.propose("high five", GLOBAL_SCOPE, confidence=0.3)
        # Add more evidence.
        model.propose("high five", GLOBAL_SCOPE, confidence=0.3)
        model.propose("high five", GLOBAL_SCOPE, confidence=0.3)
        self.assertTrue(entry.evidence_count >= 2)
        self.assertTrue(model.adopt(entry.entry_id, min_confidence=0.5, min_evidence=2))

    def test_retired_expression_not_appropriate(self):
        """S54: a retired expression is not used."""
        model = VocabularyScopeModel()
        entry = model.propose("old phrase", GLOBAL_SCOPE, confidence=0.8)
        model.retire(entry.entry_id)
        self.assertFalse(model.is_appropriate("old phrase"))

    def test_unknown_scope_rejected(self):
        model = VocabularyScopeModel()
        with self.assertRaises(ValueError):
            model.propose("test", "invalid_scope")

    def test_entries_for_scope(self):
        model = VocabularyScopeModel()
        model.propose("hi", GLOBAL_SCOPE)
        model.propose("buddy", RELATIONSHIP_SCOPE, scope_target="alice")
        self.assertEqual(len(model.entries_for_scope(GLOBAL_SCOPE)), 1)
        self.assertEqual(len(model.entries_for_scope(RELATIONSHIP_SCOPE)), 1)


class CommunicationDecisionTests(unittest.TestCase):
    def test_prefer_silence_no_reason(self):
        """S60: silence is a valid behavior when there's no useful reason to speak."""
        cd = CommunicationDecision()
        should, reason = cd.should_speak(has_communicative_reason=False)
        self.assertFalse(should)
        self.assertEqual(reason, "prefer_silence_no_useful_reason")

    def test_speak_when_reason_exists(self):
        cd = CommunicationDecision()
        should, reason = cd.should_speak(has_communicative_reason=True)
        self.assertTrue(should)

    def test_social_fatigue_cooldown(self):
        cd = CommunicationDecision(fatigue_budget=3, fatigue_cooldown=5)
        # Record interactions to trigger fatigue.
        for _ in range(3):
            cd.record_interaction()
        self.assertTrue(cd.is_fatigued)
        should, reason = cd.should_speak(has_communicative_reason=True)
        self.assertFalse(should)
        self.assertEqual(reason, "social_fatigue_cooldown")

    def test_fatigue_recovery(self):
        cd = CommunicationDecision(fatigue_budget=2, fatigue_cooldown=3)
        cd.record_interaction()
        cd.record_interaction()
        self.assertTrue(cd.is_fatigued)
        # Tick through cooldown.
        for _ in range(3):
            cd.tick()
        self.assertFalse(cd.is_fatigued)
        should, _ = cd.should_speak(has_communicative_reason=True)
        self.assertTrue(should)

    def test_yielding_to_interruption(self):
        """S61: turn-taking — don't interrupt."""
        cd = CommunicationDecision()
        cd.set_speaking(True)  # Novi is speaking
        # When interrupted, yield.
        should, reason = cd.should_speak(has_communicative_reason=True, is_interrupted=True)
        self.assertFalse(should)
        self.assertEqual(reason, "yielding_to_interruption")

    def test_addressee_tracking(self):
        cd = CommunicationDecision()
        cd.should_speak(has_communicative_reason=True, addressee="alice")
        # The addressee is recorded internally; the decision doesn't fail.
        should, _ = cd.should_speak(has_communicative_reason=True, addressee="bob")
        self.assertTrue(should)


if __name__ == "__main__":
    unittest.main()