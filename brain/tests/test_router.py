import unittest

from brain.models.reasoning import ActionIntent, LLMReasoningProvider
from brain.models.router import ReasoningRouter
from brain.models.validation import StructuredOutputValidator, action_output_spec

ALLOWED = frozenset({"inspect", "observe", "wait", "stop", "move_forward", "turn_left", "turn_right"})


class FakeProvider:
    def __init__(self, output, status="completed_on_time"):
        self.output = output
        self.status = status

    def invoke(self, payload, invocation_id=""):
        return type("R", (), {"output": self.output, "status": self.status})()


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def decide(self, **kw):
        self.calls += 1
        return ActionIntent(action="observe", parameters={}, rationale="llm-decided")


class ValidationTests(unittest.TestCase):
    def test_valid_action_output(self):
        v = StructuredOutputValidator(action_output_spec(ALLOWED))
        result = v.validate({"action": "inspect", "parameters": {"depth": "high"}, "rationale": "look"})
        self.assertTrue(result.valid)
        self.assertEqual(result.value["action"], "inspect")
        self.assertEqual(result.value["parameters"], {"depth": "high"})

    def test_json_string_parsed(self):
        v = StructuredOutputValidator(action_output_spec(ALLOWED))
        result = v.validate('{"action": "wait"}')
        self.assertTrue(result.valid)
        self.assertEqual(result.value["action"], "wait")

    def test_out_of_allowlist_rejected(self):
        v = StructuredOutputValidator(action_output_spec(ALLOWED))
        result = v.validate({"action": "hack"})
        self.assertFalse(result.valid)
        self.assertTrue(any("action" in e for e in result.errors))

    def test_missing_required_field(self):
        v = StructuredOutputValidator(action_output_spec(ALLOWED))
        result = v.validate({"parameters": {}})
        self.assertFalse(result.valid)
        self.assertTrue(any("required" in e for e in result.errors))

    def test_defaults_filled_for_optional(self):
        v = StructuredOutputValidator(action_output_spec(ALLOWED))
        result = v.validate({"action": "observe"})
        self.assertTrue(result.valid)
        self.assertEqual(result.value["parameters"], {})
        self.assertEqual(result.value["rationale"], "")

    def test_wrong_type_rejected(self):
        v = StructuredOutputValidator(action_output_spec(ALLOWED))
        result = v.validate({"action": "observe", "parameters": "not-a-dict"})
        self.assertFalse(result.valid)
        self.assertTrue(any("parameters" in e for e in result.errors))


class LLMValidationTests(unittest.TestCase):
    def test_invalid_llm_output_falls_back_to_default(self):
        llm = LLMReasoningProvider(FakeProvider({"action": "hack"}), allowed_actions=ALLOWED, default_action="wait")
        intent = llm.decide(conclusion="x", confidence=0.5, situation={})
        self.assertEqual(intent.action, "wait")
        self.assertFalse(llm.last_validation.valid)

    def test_valid_llm_output_accepted(self):
        llm = LLMReasoningProvider(FakeProvider({"action": "inspect", "parameters": {}}), allowed_actions=ALLOWED, default_action="wait")
        intent = llm.decide(conclusion="x", confidence=0.5, situation={})
        self.assertEqual(intent.action, "inspect")
        self.assertTrue(llm.last_validation.valid)


class RouterTests(unittest.TestCase):
    def test_confident_routes_to_deterministic(self):
        llm = FakeLLM()
        router = ReasoningRouter(llm=llm, confidence_threshold=0.6)
        intent = router.decide(conclusion="x", confidence=0.9, situation={})
        self.assertEqual(router.last_route, "deterministic")
        self.assertEqual(llm.calls, 0)
        self.assertEqual(intent.action, "observe")  # deterministic default

    def test_uncertain_routes_to_llm(self):
        llm = FakeLLM()
        router = ReasoningRouter(llm=llm, confidence_threshold=0.6)
        intent = router.decide(conclusion="x", confidence=0.4, situation={})
        self.assertEqual(router.last_route, "llm")
        self.assertEqual(llm.calls, 1)
        self.assertEqual(intent.action, "observe")

    def test_llm_error_degrades_to_deterministic(self):
        class BoomLLM:
            def decide(self, **kw):
                raise RuntimeError("ollama down")

        router = ReasoningRouter(llm=BoomLLM(), confidence_threshold=0.6)
        router.decide(conclusion="x", confidence=0.3, situation={})
        self.assertEqual(router.last_route, "deterministic")
        self.assertIn("llm_error", router.last_reason)

    def test_no_llm_always_deterministic(self):
        router = ReasoningRouter(confidence_threshold=0.6)
        router.decide(conclusion="x", confidence=0.1, situation={})
        self.assertEqual(router.last_route, "deterministic")
        self.assertEqual(router.last_reason, "no_llm")

    def test_route_counts_tracked(self):
        llm = FakeLLM()
        router = ReasoningRouter(llm=llm, confidence_threshold=0.6)
        router.decide(conclusion="a", confidence=0.9, situation={})
        router.decide(conclusion="b", confidence=0.3, situation={})
        router.decide(conclusion="c", confidence=0.8, situation={})
        self.assertEqual(router.route_counts, {"deterministic": 2, "llm": 1})


class BrainRouterTests(unittest.TestCase):
    def test_brain_uses_router_and_reports_route(self):
        from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
        from brain.engine import MacBrain, MacBrainConfig
        from brain.tests.test_mac_brain import FakeCamera

        class PersonBackend(DeterministicPerceptionBackend):
            def detect(self, frame):
                return (Detection("person", 0.8, (0, 0, 1, 1)),)

        llm = FakeLLM()
        router = ReasoningRouter(llm=llm, confidence_threshold=0.95)  # low -> escalate to llm
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(PersonBackend()),
            reasoning=router,
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        result = brain.step()
        brain.stop()
        self.assertIn("reasoning_route", result)
        self.assertEqual(result["reasoning_route"]["route"], "llm")
        self.assertIn("reasoning.route", [e["event_type"] for e in brain.events])
        self.assertIn("reasoning.completed", [e["event_type"] for e in brain.events])


if __name__ == "__main__":
    unittest.main()
