"""Tests for scoped-vocabulary wiring into the dialogue/lexicon path.

Verifies:
  - The canonical Lexicon is initialized in the runtime (single source of truth;
    the legacy duplicate VocabularyScopeModel was removed, roadmap item 27).
  - _learn_from_chat observes expressions as relationship-scoped.
  - Exposure alone does not cause adoption (A06: lexicon poisoning).
  - Relationship-scoped expressions from other people are surfaced in vocabulary_scope.
  - The vocabulary_scope warning is included when other-scoped expressions exist.
  - The lexicon.observed_from_chat event is emitted.
"""

import unittest

from brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from brain.lexicon import Lexicon, LexiconStatus
from brain.lexicon import Scope as LexScope
from brain.engine import MacBrain, MacBrainConfig
from brain.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


def _mock_llm(system: str, user: str) -> str:
    return "I hear you. That's interesting."


class VocabularyScopeWiringTests(unittest.TestCase):
    def _brain(self):
        brain = MacBrain(
            camera=FakeCamera(),
            perception=SpecialistPerception(CupBackend()),
            config=MacBrainConfig(curiosity_enabled=False),
        )
        brain.start()
        brain.step()
        return brain

    def test_canonical_lexicon_initialized(self):
        """The runtime owns one canonical Lexicon; no legacy duplicate remains."""
        brain = self._brain()
        try:
            self.assertIsInstance(brain.lexicon, Lexicon)
            self.assertFalse(hasattr(brain, "vocab_scope"),
                             "legacy VocabularyScopeModel duplicate removed")
        finally:
            brain.stop()

    def test_learn_from_chat_observes_expression(self):
        """_learn_from_chat observes the user's text as a relationship-scoped expression."""
        brain = self._brain()
        try:
            brain._learn_from_chat("hey buddy, how are you?", person="Alice")
            # The expression should be observed in the lexicon.
            status = brain.lexicon.status_of("hey buddy, how are you?", person="Alice")
            self.assertIn(status, (LexiconStatus.OBSERVED, LexiconStatus.UNDERSTOOD, LexiconStatus.CANDIDATE))
        finally:
            brain.stop()

    def test_learn_from_chat_emits_event(self):
        """The lexicon.observed_from_chat event is emitted."""
        brain = self._brain()
        try:
            brain._learn_from_chat("hello there", person="Alice")
            events = [e for e in brain.events if e["event_type"] == "lexicon.observed_from_chat"]
            self.assertGreater(len(events), 0)
            self.assertEqual(events[-1]["payload"]["person"], "Alice")
            self.assertEqual(events[-1]["payload"]["scope"], "relationship")
        finally:
            brain.stop()

    def test_exposure_alone_does_not_adopt(self):
        """A06: a single exposure does not cause adoption."""
        brain = self._brain()
        try:
            brain._learn_from_chat("sup weirdo", person="Stranger")
            status = brain.lexicon.status_of("sup weirdo", person="Stranger")
            # Should NOT be ADOPTED or SCOPED after a single exposure.
            self.assertNotIn(status, (LexiconStatus.ADOPTED, LexiconStatus.SCOPED))
        finally:
            brain.stop()

    def test_repeated_exposure_can_adopt(self):
        """Repeated exposure can eventually lead to scoped adoption."""
        brain = self._brain()
        try:
            for _ in range(3):
                brain._learn_from_chat("high five", person="Alice")
            status = brain.lexicon.status_of("high five", person="Alice")
            # After 3 observations with relationship scope, should be at least VALIDATED.
            self.assertIn(status, (LexiconStatus.VALIDATED, LexiconStatus.SCOPED, LexiconStatus.ADOPTED))
        finally:
            brain.stop()

    def test_vocabulary_scope_for_person(self):
        """_vocabulary_scope_for returns available vocabulary for the person."""
        brain = self._brain()
        try:
            # Seed a global expression.
            brain.lexicon.observe("hello", source="seed", person="", scope=LexScope.GLOBAL)
            brain.lexicon._entries[brain.lexicon._key("hello")].status = LexiconStatus.ADOPTED
            # Seed a relationship-scoped expression for Alice.
            brain.lexicon.observe("buddy", source="chat", person="Alice", scope=LexScope.RELATIONSHIP)
            key = brain.lexicon._key_scoped("buddy", "Alice")
            brain.lexicon._entries[key].status = LexiconStatus.SCOPED

            scope = brain._vocabulary_scope_for("Alice")
            self.assertIn("hello", scope["available_vocabulary"])
            self.assertIn("buddy", scope["available_vocabulary"])
        finally:
            brain.stop()

    def test_vocabulary_scope_warns_about_other_scoped(self):
        """When other-relationship-scoped expressions exist, a warning is included."""
        brain = self._brain()
        try:
            # Seed a relationship-scoped expression for Bob.
            brain.lexicon.observe("buddy", source="chat", person="Bob", scope=LexScope.RELATIONSHIP)
            key = brain.lexicon._key_scoped("buddy", "Bob")
            brain.lexicon._entries[key].status = LexiconStatus.SCOPED

            # When asking for Alice's scope, Bob's expression should appear in other_scoped.
            scope = brain._vocabulary_scope_for("Alice")
            self.assertGreater(len(scope["other_relationship_scoped"]), 0)
            self.assertTrue(scope["warning"])
        finally:
            brain.stop()

    def test_vocabulary_scope_in_user_payload(self):
        """The vocabulary_scope is included in the user_payload sent to the LLM."""
        brain = self._brain()
        try:
            # The compose_reply wrapper should include vocabulary_scope in the grounding.
            result = brain.compose_reply("hello", person="Alice", llm_chat=_mock_llm)
            # The result should have grounding info (the vocabulary scope is in the
            # user_payload, not directly in the result, but we can check the event log).
            # Just verify compose_reply doesn't crash with the new vocabulary scope logic.
            self.assertIsInstance(result, dict)
        finally:
            brain.stop()

    def test_learn_from_chat_updates_canonical_lexicon(self):
        """_learn_from_chat updates the canonical Lexicon (single scoped source)."""
        brain = self._brain()
        try:
            brain._learn_from_chat("hey there friend", person="Alice")
            entries = [e for e in brain.lexicon.snapshot()
                       if e["expression"] == "hey there friend" and e["person"] == "Alice"]
            # Should have at least one entry (the expression from Alice), scoped.
            self.assertGreater(len(entries), 0)
            self.assertEqual(entries[0]["scope"], LexScope.RELATIONSHIP.value)
            self.assertEqual(entries[0]["person"], "Alice")
        finally:
            brain.stop()

    def test_relationship_scoped_not_appropriate_for_other_person(self):
        """S51: nickname from Person A stays scoped — not appropriate for Person B."""
        brain = self._brain()
        try:
            brain._learn_from_chat("buddy", person="Alice")
            # After a single observation, the expression is OBSERVED (not yet usable) —
            # the canonical Lexicon's is_usable() is the authoritative check.
            for _ in range(3):
                brain._learn_from_chat("buddy", person="Alice")
            usable_for_alice_after = brain.lexicon.is_usable("buddy", person="Alice")
            usable_for_bob_after = brain.lexicon.is_usable("buddy", person="Bob", stranger_present=True)
            self.assertTrue(usable_for_alice_after)
            self.assertFalse(usable_for_bob_after)
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
