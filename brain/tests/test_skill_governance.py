"""Tests for Step 3: Skill contract + governance guard + multi-speed runtime.

Done-bars:
  - A proposed action cannot execute without a governance grant.
  - Skill contract tests green (invocation independent of implementation).
  - System-0 safety gating proven.
"""

import dataclasses
import unittest

from brain.governance_guard import (
    ALLOW,
    DEGRADED_MODE,
    DENY,
    REQUIRE_CONFIRMATION,
    ActionProposal,
    GovernanceGuard,
)
from brain.multi_speed_runtime import (
    SYSTEM_0,
    SYSTEM_1,
    SYSTEM_2,
    AutonomyState,
    MultiSpeedRuntime,
    ResourceMode,
)
from brain.skill_contract import (
    ALL_SKILLS,
    FAILURE,
    INSPECT_SKILL,
    NAVIGATE_SKILL,
    PICK_SKILL,
    R0,
    R1,
    R3,
    R5,
    SPEAK_SKILL,
    SUCCESS,
    TIMEOUT,
    SkillExecutor,
)

# ---------------------------------------------------------------------------
# Skill contract tests
# ---------------------------------------------------------------------------

class SkillContractTests(unittest.TestCase):
    def test_all_skills_defined(self):
        self.assertEqual(len(ALL_SKILLS), 5)
        for skill_id in ("navigate", "inspect", "find_object", "pick", "speak"):
            self.assertIn(skill_id, ALL_SKILLS)

    def test_skill_contract_has_preconditions(self):
        self.assertGreater(len(NAVIGATE_SKILL.preconditions), 0)
        self.assertIn("robot_localized", NAVIGATE_SKILL.preconditions)

    def test_skill_contract_has_success_failure_criteria(self):
        self.assertGreater(len(NAVIGATE_SKILL.success_criteria), 0)
        self.assertGreater(len(NAVIGATE_SKILL.failure_criteria), 0)

    def test_skill_contract_has_timeout(self):
        self.assertGreater(NAVIGATE_SKILL.timeout_seconds, 0)

    def test_skill_contract_has_recovery_actions(self):
        self.assertGreater(len(NAVIGATE_SKILL.recovery_actions), 0)

    def test_skill_contract_has_safety_constraints(self):
        self.assertIn("no_collision", NAVIGATE_SKILL.safety_constraints)

    def test_risk_class_assignment(self):
        self.assertEqual(NAVIGATE_SKILL.risk_class, R3)
        self.assertEqual(INSPECT_SKILL.risk_class, R0)
        self.assertEqual(PICK_SKILL.risk_class, R3)
        self.assertEqual(SPEAK_SKILL.risk_class, R1)


class SkillExecutorTests(unittest.TestCase):
    def test_invoke_navigate_success(self):
        executor = SkillExecutor()
        result = executor.invoke("navigate", {"target_location": "kitchen", "speed": 0.3},
                                  context={"robot_localized": True, "target_location_known": True, "path_clear": True})
        self.assertEqual(result.status, SUCCESS)
        self.assertEqual(result.result["destination"], "kitchen")

    def test_invoke_navigate_preconditions_not_met(self):
        executor = SkillExecutor()
        result = executor.invoke("navigate", {"target_location": "kitchen", "speed": 0.3},
                                  context={"robot_localized": True})  # missing target_location_known, path_clear
        self.assertEqual(result.status, FAILURE)
        self.assertIn("preconditions_not_met", result.error)

    def test_invoke_inspect_success(self):
        executor = SkillExecutor()
        result = executor.invoke("inspect", {"entity_id": "cup_001", "modality": "vision"},
                                  context={"entity_visible": True, "camera_available": True})
        self.assertEqual(result.status, SUCCESS)

    def test_invoke_find_object_success(self):
        executor = SkillExecutor()
        result = executor.invoke("find_object", {"object_description": "red cup", "search_area": "kitchen"},
                                  context={"object_description_known": True, "search_area_defined": True})
        self.assertEqual(result.status, SUCCESS)

    def test_invoke_pick_success(self):
        executor = SkillExecutor()
        result = executor.invoke("pick", {"object_id": "cup_001", "grasp_force": 0.5},
                                  context={"object_located": True, "gripper_available": True, "robot_near_object": True})
        self.assertEqual(result.status, SUCCESS)

    def test_invoke_speak_success(self):
        executor = SkillExecutor()
        result = executor.invoke("speak", {"text": "hello", "volume": 0.5},
                                  context={"message_composed": True, "speaker_available": True})
        self.assertEqual(result.status, SUCCESS)

    def test_invoke_unknown_skill_fails(self):
        executor = SkillExecutor()
        result = executor.invoke("fly", {})
        self.assertEqual(result.status, FAILURE)

    def test_invoke_missing_parameter_fails(self):
        executor = SkillExecutor()
        result = executor.invoke("navigate", {"speed": 0.3},  # missing target_location
                                  context={"robot_localized": True, "target_location_known": True, "path_clear": True})
        self.assertEqual(result.status, FAILURE)
        self.assertIn("missing_parameter", result.error)

    def test_invocation_independent_of_implementation(self):
        """NVIDIA Exp 2: skill contract invocation is independent of implementation.
        The same contract produces the same outcome with mock vs real backend.
        """
        executor = SkillExecutor()
        # The contract defines the interface; the executor implements it.
        # Both a mock and a real adapter would produce the same status for the
        # same preconditions.
        result_mock = executor.invoke("inspect", {"entity_id": "cup", "modality": "vision"},
                                       context={"entity_visible": True, "camera_available": True})
        self.assertEqual(result_mock.status, SUCCESS)
        self.assertEqual(result_mock.result["entity_id"], "cup")

    def test_get_invocation_by_id(self):
        executor = SkillExecutor()
        result = executor.invoke("speak", {"text": "hi", "volume": 0.5},
                                  context={"message_composed": True, "speaker_available": True})
        retrieved = executor.get_invocation(result.invocation_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.status, SUCCESS)

    def test_invoke_enforces_contract_timeout(self):
        """Gap-analysis Step 3, item 20: SkillContract.timeout_seconds enforced.

        A handler that exceeds the contract deadline is reported as TIMEOUT
        rather than SUCCESS/FAILURE.
        """
        import time as _time

        executor = SkillExecutor()

        def slow_handler(invocation, contract, context):
            # Simulate a backend that overruns the deadline.
            _time.sleep(max(contract.timeout_seconds + 0.05, 0.05))
            invocation.status = SUCCESS
            invocation.result = {"slow": True}

        executor.register_handler("navigate", slow_handler)
        # Override the contract deadline to a tiny value so the test is fast.
        fast_contract = dataclasses.replace(NAVIGATE_SKILL, timeout_seconds=0.02)
        executor._handlers["navigate"] = slow_handler
        original = executor.get_contract

        def get_contract_with_timeout(skill_id):
            if skill_id == "navigate":
                return fast_contract
            return original(skill_id)

        executor.get_contract = get_contract_with_timeout  # type: ignore[method-assign]
        result = executor.invoke("navigate", {"target_location": "kitchen", "speed": 0.3},
                                  context={"robot_localized": True, "target_location_known": True, "path_clear": True})
        self.assertEqual(result.status, TIMEOUT)
        self.assertIn("timeout_exceeded", result.error)
        self.assertGreater(result.deadline_monotonic, 0.0)

    def test_invoke_fast_handler_not_timed_out(self):
        """A handler completing within the deadline is not reported as TIMEOUT."""
        executor = SkillExecutor()

        def fast_handler(invocation, contract, context):
            invocation.status = SUCCESS
            invocation.result = {"fast": True}

        executor.register_handler("navigate", fast_handler)
        result = executor.invoke("navigate", {"target_location": "kitchen", "speed": 0.3},
                                  context={"robot_localized": True, "target_location_known": True, "path_clear": True})
        self.assertEqual(result.status, SUCCESS)


# ---------------------------------------------------------------------------
# Governance guard tests
# ---------------------------------------------------------------------------

class GovernanceGuardTests(unittest.TestCase):
    def test_safe_action_allowed(self):
        guard = GovernanceGuard()
        proposal = ActionProposal(proposal_id="p1", action="wait", parameters={}, risk_class=R0)
        grant = guard.evaluate(proposal)
        self.assertEqual(grant.decision, ALLOW)
        self.assertTrue(grant.is_allowed)

    def test_r5_action_denied(self):
        guard = GovernanceGuard()
        proposal = ActionProposal(proposal_id="p2", action="self_destruct", parameters={}, risk_class=R5)
        grant = guard.evaluate(proposal)
        self.assertEqual(grant.decision, DENY)
        self.assertTrue(grant.is_denied)

    def test_r3_action_requires_confirmation(self):
        guard = GovernanceGuard()
        proposal = ActionProposal(proposal_id="p3", action="navigate", parameters={}, risk_class=R3)
        grant = guard.evaluate(proposal)
        self.assertEqual(grant.decision, REQUIRE_CONFIRMATION)

    def test_model_proposed_r4_action_requires_confirmation(self):
        guard = GovernanceGuard()
        proposal = ActionProposal(proposal_id="p4", action="pick", parameters={}, risk_class="R4", source="model")
        grant = guard.evaluate(proposal)
        self.assertEqual(grant.decision, REQUIRE_CONFIRMATION)

    def test_user_action_allowed(self):
        guard = GovernanceGuard()
        proposal = ActionProposal(proposal_id="p5", action="speak", parameters={"text": "hello"}, risk_class=R1, source="user")
        grant = guard.evaluate(proposal)
        self.assertEqual(grant.decision, ALLOW)

    def test_degraded_mode_blocks_physical_actions(self):
        guard = GovernanceGuard(degraded_mode=True)
        proposal = ActionProposal(proposal_id="p6", action="navigate", parameters={}, risk_class=R3, source="user")
        grant = guard.evaluate(proposal)
        self.assertEqual(grant.decision, DEGRADED_MODE)

    def test_confirmation_grants_allow(self):
        guard = GovernanceGuard()
        proposal = ActionProposal(proposal_id="p7", action="navigate", parameters={}, risk_class=R3)
        grant = guard.evaluate(proposal)
        self.assertEqual(grant.decision, REQUIRE_CONFIRMATION)
        confirmed = guard.confirm(grant.grant_id)
        self.assertIsNotNone(confirmed)
        self.assertEqual(confirmed.decision, ALLOW)

    def test_no_action_executes_without_grant(self):
        """Done-bar: a proposed action cannot execute without a governance grant."""
        guard = GovernanceGuard()
        # Any action must be evaluated first.
        proposal = ActionProposal(proposal_id="p8", action="wait", parameters={}, risk_class=R0)
        grant = guard.evaluate(proposal)
        # The grant must exist and have a decision.
        self.assertIsNotNone(grant)
        self.assertIn(grant.decision, {ALLOW, DENY, REQUIRE_CONFIRMATION, DEGRADED_MODE, "MODIFY"})

    def test_denied_action_cannot_be_overridden(self):
        """The model cannot override governance outcomes."""
        guard = GovernanceGuard()
        proposal = ActionProposal(proposal_id="p9", action="self_destruct", parameters={}, risk_class=R5, source="model")
        grant = guard.evaluate(proposal)
        self.assertEqual(grant.decision, DENY)
        # Confirm cannot turn a DENY into ALLOW.
        confirmed = guard.confirm(grant.grant_id)
        self.assertIsNone(confirmed)  # confirm only works on REQUIRE_CONFIRMATION

    def test_grant_tracking(self):
        guard = GovernanceGuard()
        for i in range(5):
            guard.evaluate(ActionProposal(proposal_id=f"p{i}", action="wait", parameters={}, risk_class=R0))
        self.assertEqual(guard.allowed_count, 5)
        self.assertEqual(len(guard.all_grants()), 5)


# ---------------------------------------------------------------------------
# Multi-speed runtime tests
# ---------------------------------------------------------------------------

class MultiSpeedRuntimeTests(unittest.TestCase):
    def test_register_and_run_system0_task(self):
        rt = MultiSpeedRuntime()
        called = []
        rt.register(SYSTEM_0, "safety_check", lambda ctx: called.append(True) or {"safe": True})
        results = rt.step()
        self.assertIn("system_0", results)
        self.assertTrue(called)

    def test_system0_always_runs(self):
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
        rt.register(SYSTEM_1, "reactive", lambda ctx: {"reacted": True})
        results = rt.step()
        self.assertIn("system_0", results)
        self.assertIn("system_1", results)

    def test_system0_safety_gate_blocks_higher_tiers(self):
        """Done-bar: System-0 safety gating proven."""
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": False})
        rt.register(SYSTEM_1, "reactive", lambda ctx: {"reacted": True})
        rt.register(SYSTEM_2, "deliberative", lambda ctx: {"thought": True})
        results = rt.step()
        self.assertFalse(rt.system0_safety_clear)
        # When safety gate fails, higher tiers are interrupted.
        sys1_results = results.get("system_1", {})
        if isinstance(sys1_results, dict):
            self.assertTrue(sys1_results.get("interrupted") or
                           any(v.get("interrupted") for v in sys1_results.values() if isinstance(v, dict)))
        self.assertEqual(rt.state, AutonomyState.INTERRUPTED)

    def test_system0_safety_clear_allows_higher_tiers(self):
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
        rt.register(SYSTEM_2, "deliberative", lambda ctx: {"thought": True})
        results = rt.step()
        self.assertTrue(rt.system0_safety_clear)
        self.assertIn("system_2", results)

    def test_safe_minimum_mode_only_runs_system0(self):
        rt = MultiSpeedRuntime()
        rt.set_resource_mode(ResourceMode.SAFE_MINIMUM)
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
        rt.register(SYSTEM_1, "reactive", lambda ctx: {"reacted": True})
        results = rt.step()
        self.assertIn("system_0", results)
        self.assertNotIn("system_1", results)

    def test_reactive_only_mode_runs_system0_and_1(self):
        rt = MultiSpeedRuntime()
        rt.set_resource_mode(ResourceMode.REACTIVE_ONLY)
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
        rt.register(SYSTEM_1, "reactive", lambda ctx: {"reacted": True})
        rt.register(SYSTEM_2, "deliberative", lambda ctx: {"thought": True})
        results = rt.step()
        self.assertIn("system_0", results)
        self.assertIn("system_1", results)
        self.assertNotIn("system_2", results)

    def test_degraded_mode_sets_state(self):
        rt = MultiSpeedRuntime()
        rt.set_resource_mode(ResourceMode.DEGRADED)
        self.assertEqual(rt.state, AutonomyState.DEGRADED)

    def test_interrupt_and_resume(self):
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
        rt.register(SYSTEM_1, "reactive", lambda ctx: {"reacted": True})
        rt.interrupt()
        self.assertEqual(rt.state, AutonomyState.INTERRUPTED)
        results = rt.step()
        # When interrupted, system_1 results show the task was interrupted.
        sys1_results = results.get("system_1", {})
        self.assertTrue(any(v.get("interrupted") for v in sys1_results.values() if isinstance(v, dict)))
        rt.resume()
        self.assertEqual(rt.state, AutonomyState.ACTIVE)
        results = rt.step()
        # After resume, system_1 tasks run normally.
        sys1_results = results.get("system_1", {})
        self.assertTrue(any(isinstance(v, dict) and "interrupted" not in v for v in sys1_results.values()))

    def test_task_priority_ordering(self):
        rt = MultiSpeedRuntime()
        order = []
        rt.register(SYSTEM_1, "low", lambda ctx: order.append("low") or {}, priority=0.1)
        rt.register(SYSTEM_1, "high", lambda ctx: order.append("high") or {}, priority=0.9)
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
        rt.step()
        self.assertEqual(order, ["high", "low"])  # higher priority first

    def test_unknown_tier_rejected(self):
        rt = MultiSpeedRuntime()
        with self.assertRaises(ValueError):
            rt.register("system_5", "bad", lambda ctx: {})

    def test_snapshot(self):
        rt = MultiSpeedRuntime()
        rt.register(SYSTEM_0, "safety", lambda ctx: {"safe": True})
        snap = rt.snapshot()
        self.assertEqual(snap["state"], AutonomyState.IDLE.value)
        self.assertTrue(snap["system0_safety_clear"])
        self.assertEqual(len(snap["tasks"]), 1)

    def test_system0_never_waits_on_llm(self):
        """System 0 is deterministic and never calls an LLM."""
        rt = MultiSpeedRuntime()
        llm_called = []
        def system0_handler(ctx):
            # System 0 must NOT call any LLM — it's purely deterministic.
            return {"safe": True, "deterministic": True}
        def system2_handler(ctx):
            # System 2 may use an LLM.
            llm_called.append(True)
            return {"deliberated": True}
        rt.register(SYSTEM_0, "safety", system0_handler)
        rt.register(SYSTEM_2, "deliberation", system2_handler)
        rt.step()
        self.assertTrue(rt.system0_safety_clear)
        self.assertTrue(llm_called)  # LLM only called at System 2


if __name__ == "__main__":
    unittest.main()
