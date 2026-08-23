import unittest

from novi.brain.models import (
    DeliberativeReasoningProvider,
    DeterministicReasoningProvider,
    LLMReasoningProvider,
    MacModelProvider,
    MacModelSpec,
)


class DeliberativeReasoningProviderTests(unittest.TestCase):
    def test_no_signal_falls_back_to_configured_default(self) -> None:
        # Regression: when no signal is present all scores are 0.0 and the
        # provider used to return the first action ("inspect") instead of the
        # configured safe default.
        provider = DeliberativeReasoningProvider(default_action="wait")
        intent = provider.decide(conclusion="unknown", confidence=0.0, situation={})
        self.assertEqual(intent.action, "wait")

    def test_signal_still_drives_action(self) -> None:
        provider = DeliberativeReasoningProvider(default_action="wait")
        intent = provider.decide(conclusion="causal_change_inferred", confidence=0.9, situation={})
        self.assertEqual(intent.action, "inspect")


class DeterministicReasoningProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = DeterministicReasoningProvider()

    def test_maps_person_to_observe(self) -> None:
        intent = self.provider.decide(conclusion="person_alice_is_relevant_to_current_situation", confidence=0.95, situation={})
        self.assertEqual(intent.action, "observe")

    def test_maps_environmental_change_to_inspect(self) -> None:
        intent = self.provider.decide(conclusion="environmental_change_is_relevant", confidence=0.8, situation={})
        self.assertEqual(intent.action, "inspect")

    def test_maps_no_salience_to_wait(self) -> None:
        intent = self.provider.decide(conclusion="no_high_salience_change_detected", confidence=0.7, situation={})
        self.assertEqual(intent.action, "wait")

    def test_unknown_conclusion_defaults_to_observe(self) -> None:
        intent = self.provider.decide(conclusion="some_other_conclusion", confidence=0.5, situation={})
        self.assertEqual(intent.action, "observe")

    def test_recall_informs_rationale(self) -> None:
        intent = self.provider.decide(
            conclusion="no_high_salience_change_detected",
            confidence=0.7,
            situation={},
            recall=[{"memory_type": "utterance", "content": "alice came by"}],
        )
        self.assertEqual(intent.action, "wait")
        self.assertIn("recalled 1 relevant memories", intent.rationale)


class LLMReasoningProviderTests(unittest.TestCase):
    def _provider(self, backend_fn, allowed_actions=None) -> LLMReasoningProvider:
        spec = MacModelSpec(
            capability="reasoning",
            model_id="llm-reasoner",
            model_version="1.0.0",
            artifact_digest="sha256:test",
            runtime="test-local",
            runtime_version="1.0.0",
            modalities=("text",),
        )
        model = MacModelProvider(spec, backend_fn)
        return LLMReasoningProvider(model, allowed_actions=allowed_actions or frozenset({"observe", "inspect", "wait"}))

    def test_uses_llm_action_within_allowlist(self) -> None:
        provider = self._provider(lambda payload: {"action": "observe", "parameters": {"target": "alice"}})
        intent = provider.decide(conclusion="person_alice_is_relevant_to_current_situation", confidence=0.9, situation={})
        self.assertEqual(intent.action, "observe")
        self.assertEqual(intent.parameters, {"target": "alice"})

    def test_rejects_action_outside_allowlist(self) -> None:
        provider = self._provider(lambda payload: {"action": "unbounded_action", "parameters": {}})
        intent = provider.decide(conclusion="x", confidence=0.9, situation={})
        self.assertEqual(intent.action, "observe")
        self.assertEqual(intent.parameters, {})


if __name__ == "__main__":
    unittest.main()
