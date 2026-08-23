import unittest

from novi.brain.b1_autonomy import DeterministicAutonomy
from novi.brain.b1_cognition import DeterministicCognition
from novi.brain.b1_execution import SimulatedCapabilityGateway
from novi.brain.b1_memory import DeterministicMemoryManager
from novi.brain.b1_outcomes import DeterministicOutcomeEvaluator, DeterministicReplay
from novi.brain.b1_world import DeterministicWorld, TemporalWorldModel


class B1IntegrationGateTests(unittest.TestCase):
    """End-to-end B1 gate: world -> cognition -> memory -> autonomy -> execution -> outcome -> replay."""

    def _run_once(self) -> dict[str, object]:
        world = DeterministicWorld()
        model = TemporalWorldModel()
        memory = DeterministicMemoryManager()
        cognition = DeterministicCognition()
        autonomy = DeterministicAutonomy()
        gateway = SimulatedCapabilityGateway()
        evaluator = DeterministicOutcomeEvaluator()
        replay = DeterministicReplay()

        world.advance()
        observations = world.observe()
        model.apply_many(observations)
        cognitive = cognition.cycle(model.state, observations, cycle=world.cycle)

        admission = memory.admit(
            memory_type="situation",
            content={
                "cycle": cognitive.situation.cycle,
                "salient_entities": list(cognitive.situation.salient_entities),
                "reasoning": cognitive.reasoning.conclusion,
            },
            confidence=cognitive.reasoning.confidence,
            verification_status="observed",
            privacy_class="normal",
            provenance={
                "source": "b1.integration_gate",
                "cognition_cycle": cognitive.situation.cycle,
            },
            event_refs=("1:person_entered_room:alice",),
            entity_refs=tuple(cognitive.situation.salient_entities),
        )
        self.assertTrue(admission.accepted)

        proposal = autonomy.propose(cognitive)
        self.assertTrue(proposal.constraints["requires_safety_authorization"])
        self.assertTrue(proposal.constraints["no_direct_motor_control"])

        authorization_ref = "auth-b1-gate"
        safety_ref = "safety-b1-gate"
        execution = gateway.execute(
            proposal,
            authorization_ref=authorization_ref,
            safety_ref=safety_ref,
            allowed=True,
            hardware_target="simulated-body",
        )

        self.assertEqual(execution.proposal_ref, proposal.proposal_id)
        self.assertEqual(execution.authorization_ref, authorization_ref)
        self.assertEqual(execution.safety_ref, safety_ref)
        self.assertFalse(execution.provenance["direct_hardware_control"])

        outcome = evaluator.evaluate(
            proposal,
            observed_effects=("observation_update",),
            expected_effects=("observation_update",),
        )
        self.assertEqual(outcome.status, "SUCCEEDED")
        replay.record(cognitive.situation.cycle, outcome)

        return {
            "world": {
                "cycle": world.cycle,
                "events": tuple(f"{event.cycle}:{event.event_type}:{event.entity}" for event in world.events),
                "observations": len(observations),
            },
            "cognition": {
                "cycle": cognitive.situation.cycle,
                "entities": cognitive.situation.salient_entities,
                "conclusion": cognitive.reasoning.conclusion,
                "confidence": cognitive.reasoning.confidence,
            },
            "memory": {
                "admitted": admission.accepted,
                "decision": admission.decision,
            },
            "proposal": {
                "id": proposal.proposal_id,
                "capability": proposal.capability,
                "intent": proposal.semantic_intent,
                "target_refs": proposal.target_refs,
            },
            "execution": {
                "proposal_ref": execution.proposal_ref,
                "authorization_ref": execution.authorization_ref,
                "safety_ref": execution.safety_ref,
                "status": execution.status,
                "operation_id": execution.operation_id,
            },
            "outcome": {
                "status": outcome.status,
                "discrepancies": outcome.discrepancies,
            },
            "replay": {
                "count": replay.count,
                "proposal_id": replay.replay()[0].proposal_id,
                "outcome_status": replay.replay()[0].outcome_status,
            },
        }

    def test_b1_closed_loop_completes_end_to_end(self) -> None:
        result = self._run_once()
        self.assertEqual(result["world"]["cycle"], 1)
        self.assertEqual(result["cognition"]["conclusion"], "person_alice_is_relevant_to_current_situation")
        self.assertTrue(result["memory"]["admitted"])
        self.assertTrue(result["proposal"]["id"].startswith("proposal-"))
        self.assertEqual(result["execution"]["status"], "SIMULATED_ACCEPTED")
        self.assertEqual(result["outcome"]["status"], "SUCCEEDED")
        self.assertEqual(result["replay"]["count"], 1)

    def test_b1_semantic_result_is_deterministic(self) -> None:
        first = self._run_once()
        second = self._run_once()
        self.assertEqual(first, second)

    def test_execution_requires_explicit_approval(self) -> None:
        world = DeterministicWorld()
        model = TemporalWorldModel()
        world.advance()
        observations = world.observe()
        model.apply_many(observations)
        cognitive = DeterministicCognition().cycle(model.state, observations, cycle=world.cycle)
        proposal = DeterministicAutonomy().propose(cognitive)

        with self.assertRaises(PermissionError):
            SimulatedCapabilityGateway().execute(
                proposal,
                authorization_ref="auth-denied",
                safety_ref="safety-denied",
                allowed=False,
            )

    def test_no_physical_hardware_path_is_exposed(self) -> None:
        gateway = SimulatedCapabilityGateway()
        self.assertNotIn("gpio", type(gateway).__module__.lower())
        self.assertNotIn("serial", type(gateway).__module__.lower())
        self.assertNotIn("can", type(gateway).__module__.lower())


if __name__ == "__main__":
    unittest.main()
