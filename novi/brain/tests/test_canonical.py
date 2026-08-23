import unittest

from novi.brain.canonical import (
    action_outcome_payload,
    action_proposal_payload,
    observation_payload,
    safety_decision_payload,
)
from novi.brain.contracts import utc_now


class CanonicalPayloadTests(unittest.TestCase):
    def test_observation_matches_canonical_schema(self) -> None:
        payload = observation_payload(
            source_type="synthetic",
            source_id="environment-1",
            modality="state",
            value={"entity": "test_object"},
            quality=1.0,
            uncertainty={"confidence": 1.0},
            provenance={"producer": "brain.tests"},
        )
        self.assertIn("observation_id", payload)

    def test_action_proposal_matches_canonical_schema(self) -> None:
        payload = action_proposal_payload(
            capability="inspect",
            semantic_intent="inspect observed entity",
            parameters={"entity": "test_object"},
            constraints={},
            expected_effects={"inspection": "completed"},
            risks=[],
            requester_id="brain-stage0",
            authorization_context={},
            expires_at=utc_now(),
            idempotency_key="test-idempotency-key",
            provenance={"producer": "brain.tests"},
        )
        self.assertIn("proposal_id", payload)

    def test_safety_decision_matches_canonical_schema(self) -> None:
        payload = safety_decision_payload(
            proposal_ref="proposal-1",
            policy_version="1.0.0",
            hardware_health_revision=0,
            environment_state_revision=0,
            decision="ALLOW",
            constraints={},
            reason_codes=["SAFE"],
            valid_until=utc_now(),
            audit_ref="audit-1",
        )
        self.assertEqual(payload["decision"], "ALLOW")

    def test_action_outcome_matches_canonical_schema(self) -> None:
        payload = action_outcome_payload(
            execution_ref="execution-1",
            status="SUCCEEDED",
            observed_effects={"inspection": "completed"},
            expected_effect_comparison={"matched": True},
            sensor_evidence_refs=[],
            recovery_state={"state": "NORMAL"},
            provenance={"producer": "brain.tests"},
        )
        self.assertEqual(payload["status"], "SUCCEEDED")


if __name__ == "__main__":
    unittest.main()
