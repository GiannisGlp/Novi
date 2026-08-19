import unittest

from brain.b1_autonomy import ActionProposal
from brain.b1_execution import SimulatedCapabilityGateway


class B1ExecutionTests(unittest.TestCase):
    def proposal(self) -> ActionProposal:
        return ActionProposal(
            proposal_id="proposal-test",
            capability="observe.environment",
            semantic_intent="test",
            parameters={},
            constraints={"requires_safety_authorization": True, "no_direct_motor_control": True},
            expected_effects={},
            risks={},
            requester_id="test",
            authorization_context={},
            expires_at="2099-01-01T00:00:00Z",
            idempotency_key="proposal-test",
            provenance={},
        )

    def test_execution_requires_explicit_approval(self) -> None:
        with self.assertRaises(PermissionError):
            SimulatedCapabilityGateway().execute(
                self.proposal(), authorization_ref="auth-1", safety_ref="safety-1", allowed=False
            )

    def test_allowed_execution_creates_canonical_execution_record(self) -> None:
        execution = SimulatedCapabilityGateway().execute(
            self.proposal(), authorization_ref="auth-1", safety_ref="safety-1", allowed=True
        )
        self.assertEqual(execution.proposal_ref, "proposal-test")
        self.assertEqual(execution.authorization_ref, "auth-1")
        self.assertEqual(execution.safety_ref, "safety-1")
        self.assertEqual(execution.status, "SIMULATED_ACCEPTED")
        self.assertFalse(execution.provenance["direct_hardware_control"])

    def test_execution_identity_is_deterministic(self) -> None:
        gateway = SimulatedCapabilityGateway()
        first = gateway.execute(self.proposal(), authorization_ref="auth-1", safety_ref="safety-1", allowed=True)
        second = gateway.execute(self.proposal(), authorization_ref="auth-1", safety_ref="safety-1", allowed=True)
        self.assertEqual(first.execution_id, second.execution_id)
        self.assertEqual(first.operation_id, second.operation_id)

    def test_missing_safety_requirement_is_rejected(self) -> None:
        proposal = self.proposal()
        object.__setattr__(proposal, "constraints", {})
        with self.assertRaises(PermissionError):
            SimulatedCapabilityGateway().execute(
                proposal, authorization_ref="auth-1", safety_ref="safety-1", allowed=True
            )


if __name__ == "__main__":
    unittest.main()
