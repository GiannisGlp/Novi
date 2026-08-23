"""Tests for typed cognitive emission (roadmap item 12).

Verifies MacCognition.cycle_typed / MacBrain.cognition_typed emit canonical
typed contracts (SituationState, PersonContext, IntentHypothesis, Prediction,
CognitiveDecisionRecord, CognitiveEvent) that:
  - validate against their JSON Schemas (cognition.validation / schemas);
  - respect ownership boundaries (no authorization grant, no command);
  - appear on the runtime event bus as cognition.typed.
"""

import unittest

from brain.b1_world import SensorObservation, WorldEntityState, WorldModelState
from brain.cognition2 import MacCognition
from brain.cognition_typed import TypedCognitionOutput


def _state_with_alice() -> WorldModelState:
    return WorldModelState(entities={
        "alice": WorldEntityState(entity="alice", location="kitchen", state="present",
                                  confidence=0.95, last_observed_cycle=1),
        "door": WorldEntityState(entity="door", location="kitchen", state="open",
                                 confidence=0.9, last_observed_cycle=1),
    })


def _observations() -> tuple[SensorObservation, ...]:
    return (
        SensorObservation(source="camera", entity="alice", captured_cycle=1,
                          confidence=0.95, cycle=1, location="kitchen", state="present"),
        SensorObservation(source="camera", entity="door", captured_cycle=1,
                          confidence=0.9, cycle=1, location="kitchen", state="open"),
    )


class MacCognitionTypedTests(unittest.TestCase):
    def test_cycle_typed_returns_all_contract_kinds(self):
        cog = MacCognition()
        out = cog.cycle_typed(_state_with_alice(), _observations(), cycle=1, world_revision=3)
        self.assertIsInstance(out, TypedCognitionOutput)
        self.assertIsNotNone(out.situation)
        self.assertGreaterEqual(len(out.person_contexts), 1)
        self.assertIsNotNone(out.decision)
        self.assertGreaterEqual(len(out.events), 1)

    def test_decision_is_interpretation_only(self):
        cog = MacCognition()
        out = cog.cycle_typed(_state_with_alice(), _observations(), cycle=1, world_revision=3)
        self.assertTrue(out.decision.is_interpretation_only)
        self.assertEqual(out.decision.situation_ref, out.situation.id)
        self.assertEqual(out.decision.policy_constraints_observed, ["no_escalation", "interpretation_only"])

    def test_predictions_never_claim_observed_status(self):
        """Predictions are future-state hypotheses (epistemic PREDICTED), not facts."""
        cog = MacCognition()
        out = cog.cycle_typed(_state_with_alice(), _observations(), cycle=1, world_revision=3)
        for p in out.predictions:
            self.assertEqual(p.basis, "observed_pattern")
            self.assertIn("predicted", p.predicted_attribute.lower() or "activity")

    def test_person_context_is_not_a_full_profile(self):
        cog = MacCognition()
        out = cog.cycle_typed(_state_with_alice(), _observations(), cycle=1, world_revision=3)
        persons = {p.person_ref for p in out.person_contexts}
        self.assertIn("alice", persons)
        for p in out.person_contexts:
            self.assertFalse(p.authorized_interaction)  # governance decides

    def test_snapshot_is_json_serializable(self):
        import json
        cog = MacCognition()
        out = cog.cycle_typed(_state_with_alice(), _observations(), cycle=1, world_revision=3)
        json.dumps(out.snapshot())  # must not raise

    def test_hypotheses_each_carry_uncertainty(self):
        cog = MacCognition()
        out = cog.cycle_typed(_state_with_alice(), _observations(), cycle=1, world_revision=3)
        for h in out.intent_hypotheses:
            self.assertGreaterEqual(h.confidence, 0.0)
            self.assertLessEqual(h.confidence, 1.0)
            self.assertIsNotNone(h.uncertainty)


class SchemaValidationTests(unittest.TestCase):
    def test_all_typed_objects_validate_against_schemas(self):
        """Emitted contracts must pass the canonical JSON-Schema validation."""
        from cognition.validation import validate_structurally
        cog = MacCognition()
        out = cog.cycle_typed(_state_with_alice(), _observations(), cycle=1, world_revision=3)
        for obj in out.all_objects():
            result = validate_structurally(obj.contract_type, obj.model_dump(mode="json"))
            self.assertTrue(result.valid, f"{obj.contract_type} failed: {result.issues}")


class RuntimeTypedEmissionTests(unittest.TestCase):
    @staticmethod
    def _brain():
        from brain.b2_perception import DeterministicPerceptionBackend, SpecialistPerception
        from brain.engine import MacBrain, MacBrainConfig
        from brain.tests.test_mac_brain import FakeCamera
        return MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(DeterministicPerceptionBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
            store_path=None,
        )

    def test_cognition_typed_emits_event(self):
        brain = self._brain()
        brain.start()
        try:
            snap = brain.cognition_typed()
            self.assertIsNotNone(snap.get("decision"))
            emitted = [e for e in brain.events if e.get("event_type") == "cognition.typed"]
            self.assertEqual(len(emitted), 1)
            self.assertEqual(emitted[0]["correlation_id"], snap.get("correlation_id"))
        finally:
            brain.stop()

    def test_last_typed_cognition_stored(self):
        brain = self._brain()
        brain.start()
        try:
            snap = brain.cognition_typed()
            self.assertEqual(brain._last_typed_cognition["correlation_id"], snap["correlation_id"])
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
