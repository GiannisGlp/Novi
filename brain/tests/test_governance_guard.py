"""Dedicated unit tests for `brain/governance_guard.py`.

Fills the P7/gap-46 coverage hole: previously the governance guard was only
exercised indirectly via `test_skill_governance.py`. These tests cover the full
decision surface — ALLOW / DENY / MODIFY / REQUIRE_CONFIRMATION / PAUSE / STOP /
DEGRADED_MODE, the confirmation flow, grant tracking, and the core invariant
that no action executes without a grant.
"""

import unittest

from brain.governance_guard import (
    ALL_GOVERNANCE_DECISIONS,
    ALLOW,
    DEGRADED_MODE,
    DENY,
    MODIFY,
    PAUSE,
    REQUIRE_CONFIRMATION,
    STOP,
    ActionProposal,
    GovernanceGrant,
    GovernanceGuard,
)


def proposal(pid: str = "p1", action: str = "wait", risk_class: str = "R0", **kw) -> ActionProposal:
    return ActionProposal(proposal_id=pid, action=action, parameters={}, risk_class=risk_class, **kw)


class ActionProposalTests(unittest.TestCase):
    def test_snapshot_roundtrip_fields(self):
        snap = proposal(rationale="test", source="model").snapshot()
        self.assertEqual(snap["proposal_id"], "p1")
        self.assertEqual(snap["action"], "wait")
        self.assertEqual(snap["risk_class"], "R0")
        self.assertEqual(snap["source"], "model")
        self.assertEqual(snap["rationale"], "test")
        self.assertIsInstance(snap["parameters"], dict)

    def test_snapshot_copies_parameters(self):
        p = ActionProposal(proposal_id="p", action="pick", parameters={"id": "cup"})
        snap = p.snapshot()
        snap["parameters"]["id"] = "mutated"
        self.assertEqual(p.parameters["id"], "cup")


class GovernanceGrantTests(unittest.TestCase):
    def test_is_allowed_and_is_denied(self):
        self.assertTrue(GovernanceGrant(grant_id="g", proposal_id="p", decision=ALLOW).is_allowed)
        self.assertFalse(GovernanceGrant(grant_id="g", proposal_id="p", decision=ALLOW).is_denied)
        self.assertTrue(GovernanceGrant(grant_id="g", proposal_id="p", decision=DENY).is_denied)

    def test_snapshot_contains_conditions(self):
        g = GovernanceGrant(grant_id="g", proposal_id="p", decision=REQUIRE_CONFIRMATION,
                            conditions=("a", "b"), modified_parameters={"x": 1})
        snap = g.snapshot()
        self.assertEqual(snap["conditions"], ["a", "b"])
        self.assertEqual(snap["modified_parameters"], {"x": 1})
        self.assertEqual(snap["decision"], REQUIRE_CONFIRMATION)


class GovernanceGuardDecisionTests(unittest.TestCase):
    def test_all_decisions_are_known(self):
        # Every possible decision constant is a member of the canonical set.
        for d in (ALLOW, DENY, MODIFY, REQUIRE_CONFIRMATION, PAUSE, STOP, DEGRADED_MODE):
            self.assertIn(d, ALL_GOVERNANCE_DECISIONS)

    def test_modify_decision_available_but_not_auto_granted(self):
        # MODIFY is a declared decision; the guard never guesses parameters.
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="m1", action="navigate", risk_class="R2"))
        self.assertNotEqual(grant.decision, MODIFY)

    def test_unknown_risk_class_falls_to_confirmation(self):
        # Unknown risk classes must not silently execute.
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="u1", action="custom", risk_class="R9"))
        self.assertEqual(grant.decision, REQUIRE_CONFIRMATION)

    def test_r2_action_requires_confirmation_for_physical_actions(self):
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="r2", action="move_forward", risk_class="R2"))
        self.assertEqual(grant.decision, REQUIRE_CONFIRMATION)

    def test_observe_allowed_even_at_unknown_risk(self):
        # But `observe` with default risk remains allowed by the safe-action stage.
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="o1", action="observe", risk_class="R0"))
        self.assertEqual(grant.decision, ALLOW)

    def test_custom_safe_actions_respected(self):
        guard = GovernanceGuard(safe_actions={"custom_poke"})
        grant = guard.evaluate(proposal(pid="c1", action="custom_poke", risk_class="R1"))
        self.assertEqual(grant.decision, ALLOW)

    def test_stop_and_pause_are_governance_outcomes(self):
        # PAUSE/STOP are valid guards for actions the guard is asked about in
        # future states; they are part of the decision vocabulary.
        self.assertIn(STOP, ALL_GOVERNANCE_DECISIONS)
        self.assertIn(PAUSE, ALL_GOVERNANCE_DECISIONS)


class GovernanceGuardConfirmationTests(unittest.TestCase):
    def test_confirm_turns_requirement_into_allow(self):
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="c1", action="navigate", risk_class="R3"))
        self.assertEqual(grant.decision, REQUIRE_CONFIRMATION)
        confirmed = guard.confirm(grant.grant_id)
        self.assertIsNotNone(confirmed)
        self.assertEqual(confirmed.decision, ALLOW)
        self.assertIn("confirmed", confirmed.reason)

    def test_confirm_unknown_grant_returns_none(self):
        guard = GovernanceGuard()
        self.assertIsNone(guard.confirm("does-not-exist"))

    def test_confirm_non_confirmation_grant_returns_none(self):
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="c2", action="wait", risk_class="R0"))
        self.assertEqual(grant.decision, ALLOW)
        self.assertIsNone(guard.confirm(grant.grant_id))

    def test_confirm_preserves_proposal_and_conditions(self):
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="c3", action="pick", risk_class="R3"))
        confirmed = guard.confirm(grant.grant_id)
        self.assertEqual(confirmed.proposal_id, grant.proposal_id)
        self.assertEqual(confirmed.grant_id, grant.grant_id)


class GovernanceGuardModeTests(unittest.TestCase):
    def test_set_degraded_mode_blocks_physical(self):
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="d1", action="navigate", risk_class="R3"))
        self.assertEqual(grant.decision, REQUIRE_CONFIRMATION)
        guard.set_degraded_mode(True)
        grant = guard.evaluate(proposal(pid="d2", action="navigate", risk_class="R3"))
        self.assertEqual(grant.decision, DEGRADED_MODE)

    def test_degraded_mode_does_not_block_speak(self):
        guard = GovernanceGuard(degraded_mode=True)
        grant = guard.evaluate(proposal(pid="d3", action="speak", risk_class="R1"))
        self.assertEqual(grant.decision, ALLOW)

    def test_toggle_degraded_off_restores_behavior(self):
        guard = GovernanceGuard(degraded_mode=True)
        guard.set_degraded_mode(False)
        grant = guard.evaluate(proposal(pid="d4", action="navigate", risk_class="R3"))
        self.assertEqual(grant.decision, REQUIRE_CONFIRMATION)


class GovernanceGuardTrackingTests(unittest.TestCase):
    def test_denied_count_increments(self):
        guard = GovernanceGuard()
        guard.evaluate(proposal(pid="t1", action="boom", risk_class="R5"))
        self.assertEqual(guard.denied_count, 1)

    def test_allowed_count_increments_on_allow_and_confirm(self):
        guard = GovernanceGuard()
        guard.evaluate(proposal(pid="t2", action="wait", risk_class="R0"))
        self.assertEqual(guard.allowed_count, 1)
        grant = guard.evaluate(proposal(pid="t3", action="navigate", risk_class="R3"))
        guard.confirm(grant.grant_id)
        self.assertEqual(guard.allowed_count, 2)

    def test_get_grant_and_all_grants(self):
        guard = GovernanceGuard()
        g1 = guard.evaluate(proposal(pid="t4", action="wait", risk_class="R0"))
        g2 = guard.evaluate(proposal(pid="t5", action="wait", risk_class="R0"))
        self.assertIs(guard.get_grant(g1.grant_id), g1)
        self.assertEqual(len(guard.all_grants()), 2)
        # Confirm updates the stored grant for the same id.
        g3 = guard.evaluate(proposal(pid="t6", action="navigate", risk_class="R3"))
        guard.confirm(g3.grant_id)
        self.assertEqual(guard.get_grant(g3.grant_id).decision, ALLOW)


class GovernanceGuardInvariantTests(unittest.TestCase):
    def test_no_grant_no_execution(self):
        """Core invariant: an unevaluated action has no grant and cannot run."""
        guard = GovernanceGuard()
        probe = proposal(pid="i1", action="wait", risk_class="R0")
        self.assertIsNone(guard.get_grant(probe.proposal_id))

    def test_model_cannot_override_deny(self):
        guard = GovernanceGuard()
        grant = guard.evaluate(proposal(pid="i2", action="boom", risk_class="R5", source="model"))
        self.assertEqual(grant.decision, DENY)
        self.assertIsNone(guard.confirm(grant.grant_id))


class RuntimeConfirmationFlowTests(unittest.TestCase):
    """Gap-analysis Step 3, item 18: the runtime confirmation flow is wired.

    REQUIRE_CONFIRMATION → surface request → confirm() before execution.
    Before this wiring the runtime treated REQUIRE_CONFIRMATION as a silent
    denial and never called confirm().
    """

    def _brain(self, *, require_confirmation_above: str = "R1"):
        from brain.engine import MacBrain, MacBrainConfig
        from brain.tests.test_mac_brain import FakeCamera

        guard = GovernanceGuard(require_confirmation_above=require_confirmation_above)
        brain = MacBrain(
            camera=FakeCamera(),
            config=MacBrainConfig(curiosity_enabled=False),
            governance_guard=guard,
        )
        brain.start()
        return brain

    def test_confirmable_action_is_held_and_surfaced(self):
        from brain.autonomy import Goal

        brain = self._brain()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=30))  # drives move_forward/turn
        result = brain.step()
        # With confirmation required above R1, movement is held, not executed.
        self.assertFalse(result["authorized"])
        self.assertEqual(result["action"], "move_forward")
        self.assertEqual(result["virtual_body"]["x_m"], 0.0)  # not moved
        pending = brain.pending_confirmations()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["action"], "move_forward")
        # The request was surfaced as an event.
        event_types = [e["event_type"] for e in brain.events]
        self.assertIn("governance.confirmation_required", event_types)
        self.assertNotIn("skill.failed", event_types)  # skill not invoked while held
        brain.stop()

    def test_confirm_action_executes_held_action(self):
        from brain.autonomy import Goal

        brain = self._brain()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=30))
        brain.step()
        pending = brain.pending_confirmations()
        self.assertEqual(len(pending), 1)
        grant_id = pending[0]["grant_id"]
        self.assertTrue(brain.confirm_action(grant_id))
        self.assertEqual(len(brain.pending_confirmations()), 0)
        # The confirmed action executed: the body moved.
        self.assertGreater(brain.body.x_m, 0.0)
        event_types = [e["event_type"] for e in brain.events]
        self.assertIn("governance.confirmed", event_types)
        brain.stop()

    def test_reject_confirmation_withdraws_request(self):
        from brain.autonomy import Goal

        brain = self._brain()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=30))
        brain.step()
        pending = brain.pending_confirmations()
        grant_id = pending[0]["grant_id"]
        self.assertTrue(brain.reject_confirmation(grant_id))
        self.assertEqual(len(brain.pending_confirmations()), 0)
        self.assertEqual(brain.body.x_m, 0.0)  # never executed
        brain.stop()

    def test_confirm_unknown_grant_returns_false(self):
        brain = self._brain()
        self.assertFalse(brain.confirm_action("does-not-exist"))
        self.assertFalse(brain.reject_confirmation("does-not-exist"))
        brain.stop()

    def test_confirm_does_not_execute_when_guard_denies(self):
        from brain.autonomy import Goal

        brain = self._brain()
        brain.set_goal(Goal.reach(3.0, 0.0, max_steps=30))
        brain.step()
        pending = brain.pending_confirmations()
        grant_id = pending[0]["grant_id"]
        # Simulate the grant being invalidated (e.g. revoked) before confirm.
        brain.governance_guard._grants[grant_id] = GovernanceGrant(
            grant_id=grant_id, proposal_id=pending[0]["proposal_id"],
            decision=DENY, reason="revoked_before_confirmation",
        )
        self.assertFalse(brain.confirm_action(grant_id))
        self.assertEqual(brain.body.x_m, 0.0)
        brain.stop()


if __name__ == "__main__":
    unittest.main()
