"""Plan 03 Phase 4 (context manager) + Phase 5 (memory selection) tests.

Socket-free, deterministic, real MacBrain on a tmp SQLite DB (the tiny
``default_brain_factory`` pattern from test_conversation_replay). LLM HTTP is
never touched: build_packet / memory selection are pure local composition over
the frozen conversation contracts plus the existing DurableMemoryStore.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.brain.conversation.context_manager import (
    MAX_HISTORY_ITEMS,
    MAX_MEMORIES,
    build_packet,
    context_score,
    label_fact,
)
from novi.brain.conversation.conversation_state import (
    ConversationState,
    FactClass,
    IntentResult,
    ReferentResult,
)
from novi.brain.conversation.memory_selector import (
    build_memory_query,
    cite_memory,
    missing_memory_verdict,
    reject_memory,
    select_memories,
)
from novi.brain.conversation_replay import default_brain_factory


def _brain(store_dir: str):
    return default_brain_factory(Path(store_dir) / "ctx.db")


def _admit(brain, content, *, entities=(), confidence=0.9,
           privacy_class="public", verification_status="observed",
           memory_type="utterance"):
    admission = brain.memory.admit(
        memory_type=memory_type,
        content=content,
        confidence=confidence,
        verification_status=verification_status,
        privacy_class=privacy_class,
        provenance={"source": "test.conversation_context"},
        entity_refs=tuple(entities),
    )
    assert admission.accepted, f"fixture admit rejected: {admission.reason}"
    return admission.memory_id


def _state_with_turns(*turns: str) -> ConversationState:
    state = ConversationState(topic="Tesla Model Y purchase")
    for i, turn in enumerate(turns):
        state.record_turn(user_text=turn, novi_text=f"noted ({i})",
                          entities=["Tesla Model Y"])
    return state


def _intent(intent="INFORMATION_REQUEST", confidence=0.9) -> IntentResult:
    return IntentResult(intent=intent, dialogue_act="QUESTION",
                       confidence=confidence, reason="test")


def _referents() -> ReferentResult:
    return ReferentResult(resolutions={"the range": "Tesla Model Y"},
                          ambiguous=[], confidence=0.9)


class ContextScoreTests(unittest.TestCase):
    def test_entity_match_outranks_no_match(self) -> None:
        high = context_score("model y range 330 miles",
                             query_entities=("Tesla Model Y",),
                             query_topic="Tesla Model Y purchase",
                             intent_match=1.0)
        low = context_score("unrelated gardening tip",
                            query_entities=("Tesla Model Y",),
                            query_topic="Tesla Model Y purchase",
                            intent_match=1.0)
        self.assertGreater(high, low)

    def test_contradiction_penalty_demotes(self) -> None:
        clean = context_score("model y range", query_entities=("Tesla Model Y",))
        contradicted = context_score("model y range",
                                     query_entities=("Tesla Model Y",),
                                     contradicted=True)
        self.assertGreater(clean, contradicted)

    def test_staleness_and_duplication_penalties(self) -> None:
        fresh = context_score("model y range")
        self.assertGreater(fresh, context_score("model y range", stale=True))
        self.assertGreater(fresh, context_score("model y range", duplicate=True))


class FactLabelTests(unittest.TestCase):
    def test_every_class_mappable(self) -> None:
        self.assertEqual(label_fact("memory", confidence=0.9), FactClass.MEMORY)
        self.assertEqual(label_fact("preference", confidence=0.9), FactClass.PREFERENCE)
        self.assertEqual(label_fact("user_turn", confidence=0.9), FactClass.USER_STATED_FACT)
        self.assertEqual(label_fact("observation", confidence=0.9), FactClass.OBSERVED_FACT)
        self.assertEqual(label_fact("world_state", confidence=0.9), FactClass.CURRENT_STATE)
        self.assertEqual(label_fact("inference", confidence=0.7), FactClass.INFERENCE)
        self.assertEqual(label_fact("hypothesis", confidence=0.5), FactClass.HYPOTHESIS)

    def test_low_confidence_is_uncertain(self) -> None:
        self.assertEqual(label_fact("memory", confidence=0.1), FactClass.UNCERTAIN)

    def test_superseded_is_historical(self) -> None:
        self.assertEqual(label_fact("memory", confidence=0.9, superseded=True),
                         FactClass.HISTORICAL_STATE)


class BudgetTests(unittest.TestCase):
    def test_memory_never_crowds_out_conversation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            for i in range(8):
                _admit(brain, f"Tesla Model Y range note number {i} about mileage",
                       entities=("Tesla Model Y",))
            state = _state_with_turns("Tell me about the Model Y.",
                                      "What about the range?",
                                      "And the price?")
            packet = build_packet("What about the range?", state,
                                   _intent(), _referents(), brain)
            # Conversation survives at full budget no matter how many memories match.
            self.assertEqual(len(packet.relevant_history), 3)
            self.assertLessEqual(len(packet.relevant_history), MAX_HISTORY_ITEMS)
            self.assertLessEqual(len(packet.relevant_memories), MAX_MEMORIES)
            self.assertLessEqual(len(packet.relevant_memories),
                                 len(packet.relevant_history))

    def test_budgets_hold_on_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            packet = build_packet("Hello.", ConversationState(),
                                   _intent("GREETING"), ReferentResult(), brain)
            self.assertLessEqual(len(packet.relevant_history), MAX_HISTORY_ITEMS)
            self.assertLessEqual(len(packet.relevant_memories), MAX_MEMORIES)
            self.assertEqual(packet.current_turn, "Hello.")


class PacketLabelTests(unittest.TestCase):
    def test_every_packet_fact_is_labeled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            _admit(brain, "Tesla Model Y long range is about 330 miles",
                   entities=("Tesla Model Y",))
            brain.preferences.learn("person", "verbosity", "short", explicit=True)
            state = _state_with_turns("Tell me about the Model Y.")
            packet = build_packet("What about the range?", state,
                                   _intent(), _referents(), brain)
            for mem in packet.relevant_memories:
                self.assertIn("fact_class", mem)
                FactClass(mem["fact_class"])
            for fact in packet.world_context:
                self.assertIn("fact_class", fact)
                FactClass(fact["fact_class"])
            memory_classes = {m["fact_class"] for m in packet.relevant_memories}
            self.assertTrue(memory_classes <= {"MEMORY", "UNCERTAIN"})


class NegativeCheckTests(unittest.TestCase):
    def test_wrong_entity_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            _admit(brain, "Tesla Model Y long range is about 330 miles",
                   entities=("Tesla Model Y",))
            _admit(brain, "BMW iX range is about 300 miles",
                   entities=("BMW iX",))
            state = _state_with_turns("Tell me about the Model Y.")
            packet = build_packet("What about the range?", state,
                                   _intent(), _referents(), brain)
            blob = " ".join(m.get("text", "") for m in packet.relevant_memories)
            self.assertIn("Tesla", blob)
            self.assertNotIn("BMW", blob)

    def test_superseded_memory_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            mid = _admit(brain, "Tesla Model Y range is 250 miles old estimate",
                         entities=("Tesla Model Y",))
            self.assertTrue(brain.memory.set_state(mid, "superseded"))
            state = _state_with_turns("Tell me about the Model Y.")
            packet = build_packet("What is the range?", state,
                                   _intent(), _referents(), brain)
            ids = [m.get("memory_id") for m in packet.relevant_memories]
            self.assertNotIn(mid, ids)

    def test_private_memory_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            _admit(brain, "Tesla Model Y range secret prototype detail",
                   entities=("Tesla Model Y",), privacy_class="private")
            state = _state_with_turns("Tell me about the Model Y.")
            packet = build_packet("What is the range?", state,
                                   _intent(), _referents(), brain)
            blob = " ".join(m.get("text", "") for m in packet.relevant_memories)
            self.assertNotIn("secret prototype", blob)

    def test_low_confidence_and_irrelevant_rejected_directly(self) -> None:
        low = {"memory_id": "m-low", "memory_type": "utterance",
               "content": "Tesla Model Y vague guess", "confidence": 0.1,
               "verification_status": "observed", "privacy_class": "public",
               "entity_refs": ("Tesla Model Y",)}
        self.assertEqual(reject_memory(low, query_entities=("Tesla Model Y",),
                                       query_text="tesla model y range"), "low_confidence")
        other = {"memory_id": "m-other", "memory_type": "utterance",
                 "content": "Gardening tips for roses in spring", "confidence": 0.9,
                 "verification_status": "observed", "privacy_class": "public",
                 "entity_refs": ()}
        self.assertEqual(reject_memory(other, query_entities=("Tesla Model Y",),
                                       query_text="tesla model y range"), "irrelevant")


class CitationTests(unittest.TestCase):
    def test_citation_shape(self) -> None:
        record = {"memory_id": "m-1", "memory_type": "utterance",
                  "content": "Tesla Model Y range 330 miles", "confidence": 0.9,
                  "verification_status": "observed", "privacy_class": "public",
                  "provenance": {"source": "test"}, "entity_refs": ("Tesla Model Y",)}
        citation = cite_memory(record, why_selected="entity_match+topic_match")
        for key in ("memory_id", "memory_type", "source", "confidence", "why_selected"):
            self.assertIn(key, citation)
        self.assertEqual(citation["memory_id"], "m-1")
        self.assertEqual(citation["source"], "test")

    def test_select_memories_returns_citations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            _admit(brain, "Tesla Model Y long range is about 330 miles",
                   entities=("Tesla Model Y",))
            state = _state_with_turns("Tell me about the Model Y.")
            query = build_memory_query("What about the range?", state, _intent())
            selected = select_memories(brain.memory, query)
            self.assertGreater(len(selected), 0)
            for citation in selected:
                for key in ("memory_id", "memory_type", "source",
                            "confidence", "why_selected"):
                    self.assertIn(key, citation)


class QueryBuilderTests(unittest.TestCase):
    def test_query_built_from_state_not_raw_sentence(self) -> None:
        state = _state_with_turns("Tell me about the Model Y.")
        query = build_memory_query("What about the range?", state, _intent())
        self.assertNotEqual(query.text, "What about the range?")
        self.assertIn("Tesla Model Y", query.text)
        self.assertIn("purchase", query.text)
        self.assertIn("INFORMATION_REQUEST", query.text)


class HonestyTests(unittest.TestCase):
    def test_missing_memory_honesty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            state = ConversationState(topic="zziqq-nonexistent-topic")
            query = build_memory_query("Do you remember what I told you about X last month?",
                                       state, _intent("MEMORY_QUERY"))
            selected = select_memories(brain.memory, query)
            self.assertEqual(selected, [])
            verdict = missing_memory_verdict(query.text, selected)
            self.assertFalse(verdict.found)
            self.assertIn("don't have", verdict.statement)

    def test_packet_never_fabricates_memories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            state = ConversationState(topic="zziqq-nonexistent-topic")
            packet = build_packet(
                "Do you remember what I told you about X last month?",
                state, _intent("MEMORY_QUERY"), ReferentResult(), brain)
            self.assertEqual(packet.relevant_memories, [])
            self.assertTrue(any("no reliable memory" in u.lower()
                                for u in packet.uncertainty))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
