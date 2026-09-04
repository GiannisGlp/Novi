"""Plan 03 Phase 3 referent/entity resolution tests (scenarios C-010/011/012).

Deterministic, socket-free, stdlib-only unit tests over the frozen
conversation contracts. No LLM is touched: resolve_referents is pure local
composition over ConversationState (active_entities + recent_turns + anchor).
"""

from __future__ import annotations

import unittest

from novi.brain.conversation.conversation_state import (
    ConversationAnchor,
    ConversationState,
    ReferentResult,
)
from novi.brain.conversation.referent_resolution import resolve_referents


def _state(*, entities: list[str], anchor_entity: str = "",
           recent: list[str] | None = None) -> ConversationState:
    state = ConversationState()
    state.active_entities = list(entities)
    state.anchor = ConversationAnchor(active_entity=anchor_entity)
    for turn in recent or []:
        state.recent_turns.append({"user": turn, "novi": ""})
    return state


class PronounChainTests(unittest.TestCase):
    """C-010: pronoun chain stays on Model Y."""

    def test_it_resolves_to_single_entity(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        result = resolve_referents("I really like it.", state)
        self.assertIsInstance(result, ReferentResult)
        self.assertEqual(result.resolutions.get("it"), "Model Y")
        self.assertEqual(result.ambiguous, [])

    def test_chain_stays_model_y(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        first = resolve_referents("I really like it.", state)
        second = resolve_referents("Do you think it's practical?", state)
        self.assertEqual(first.resolutions.get("it"), "Model Y")
        self.assertEqual(second.resolutions.get("it"), "Model Y")


class AmbiguityTests(unittest.TestCase):
    """C-011: two equally-plausible entities -> ambiguous, never guess."""

    def test_it_with_tesla_and_bmw_is_ambiguous(self) -> None:
        state = _state(entities=["Tesla", "BMW"])
        result = resolve_referents("Would you choose it?", state)
        self.assertEqual(result.resolutions, {})
        self.assertEqual(result.ambiguous, ["it"])

    def test_recent_mention_disambiguates(self) -> None:
        state = _state(entities=["Tesla", "BMW"],
                       recent=["The Tesla is cheaper."])
        result = resolve_referents("Would you choose it?", state)
        self.assertEqual(result.resolutions.get("it"), "Tesla")
        self.assertEqual(result.ambiguous, [])

    def test_same_turn_mention_disambiguates(self) -> None:
        state = _state(entities=["Tesla", "BMW"], anchor_entity="BMW")
        result = resolve_referents("The Tesla is cheaper, would you choose it?", state)
        self.assertEqual(result.resolutions.get("it"), "Tesla")
        self.assertEqual(result.ambiguous, [])


class EntitySwitchTests(unittest.TestCase):
    """C-012: entity switch lands on BMW."""

    def test_its_refers_to_bmw_after_switch(self) -> None:
        state = ConversationState()
        state.record_turn(user_text="Tell me about Tesla.", entities=["Tesla"])
        state.record_turn(user_text="Now forget that. What about BMW?",
                          entities=["BMW"])
        result = resolve_referents("What is its range?", state)
        self.assertEqual(result.resolutions.get("its"), "BMW")
        self.assertEqual(result.ambiguous, [])


class NounPhraseTests(unittest.TestCase):
    """Step 3.2: noun phrases resolve against entities + recent mentions."""

    def test_the_car_resolves_to_model_y(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        result = resolve_referents("How much does the car cost?", state)
        self.assertEqual(result.resolutions.get("the car"), "Model Y")

    def test_the_larger_model_matches_entity_token(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        result = resolve_referents("Tell me about the larger model.", state)
        self.assertEqual(result.resolutions.get("the larger model"), "Model Y")

    def test_the_one_we_discussed_uses_anchor(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        result = resolve_referents("Is the one we discussed still available?", state)
        self.assertEqual(result.resolutions.get("the one we discussed"), "Model Y")

    def test_the_other_one_picks_non_anchor_entity(self) -> None:
        state = _state(entities=["Tesla", "BMW"], anchor_entity="Tesla")
        result = resolve_referents("What about the other one?", state)
        self.assertEqual(result.resolutions.get("the other one"), "BMW")

    def test_attribute_noun_is_not_a_referent(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        result = resolve_referents("What about the range?", state)
        self.assertNotIn("the range", result.resolutions)
        self.assertNotIn("the range", result.ambiguous)


class ImplicitSubjectTests(unittest.TestCase):
    """Step 3.3: subject-less follow-ups inherit the anchor entity."""

    def test_bare_follow_up_inherits_anchor(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y",
                       recent=["Tell me about Model Y."])
        result = resolve_referents("What's the range?", state)
        self.assertEqual(result.resolutions.get("(implicit subject)"), "Model Y")
        self.assertEqual(result.ambiguous, [])

    def test_no_anchor_no_implicit_subject(self) -> None:
        state = _state(entities=[])
        result = resolve_referents("What's the range?", state)
        self.assertEqual(result.resolutions, {})
        self.assertEqual(result.ambiguous, [])

    def test_explicit_turn_has_no_implicit_subject(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        result = resolve_referents("Tell me about Model Y.", state)
        self.assertNotIn("(implicit subject)", result.resolutions)


class ContractTests(unittest.TestCase):
    def test_empty_text_resolves_nothing(self) -> None:
        state = _state(entities=["Model Y"], anchor_entity="Model Y")
        result = resolve_referents("", state)
        self.assertEqual(result.resolutions, {})
        self.assertEqual(result.ambiguous, [])
        self.assertEqual(result.confidence, 0.0)

    def test_deterministic(self) -> None:
        state = _state(entities=["Tesla", "BMW"], anchor_entity="BMW")
        first = resolve_referents("Would you choose it?", state).to_dict()
        state2 = _state(entities=["Tesla", "BMW"], anchor_entity="BMW")
        second = resolve_referents("Would you choose it?", state2).to_dict()
        self.assertEqual(first, second)

    def test_does_not_mutate_state(self) -> None:
        state = _state(entities=["Tesla", "BMW"], anchor_entity="BMW")
        before = state.to_dict()
        resolve_referents("Would you choose it?", state)
        self.assertEqual(state.to_dict(), before)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
