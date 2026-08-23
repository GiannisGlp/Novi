"""Phase B3 (gap-audit plan 13): one auditable ContextPackage grounds replies.

Pins:
  - respond()/compose_reply assemble the world-context package for THIS
    utterance before composing;
  - the reply's grounding dict reports package item counts (knowledge/memory
    layers) so "why did you say that" is answerable by inspecting one object;
  - the discourse topic hint is visible in the grounding record.
"""

import unittest

from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.tests.test_mac_brain import FakeCamera


class CupBackend(DeterministicPerceptionBackend):
    def detect(self, frame):
        return (Detection("cup", 0.85, (0.1, 0.1, 0.5, 0.5)),)


def _brain() -> MacBrain:
    brain = MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(CupBackend()),
        config=MacBrainConfig(curiosity_enabled=False),
    )
    brain.start()
    return brain


def _transport(*, system: str, user: str, temperature: float = 0.5, timeout: int = 120):
    import json
    data = json.loads(user)
    # Echo the facts count back so tests can assert grounding reached the prompt.
    return f"ok ({len(data.get('facts_i_know', []))} facts)"


class ReplyGroundingTests(unittest.TestCase):
    def test_grounding_reports_context_counts(self):
        brain = _brain()
        try:
            out = brain.respond("what about the cup on the table?", llm_chat=_transport)
            g = out.get("grounding", {})
            self.assertIn("context_items", g)
            self.assertIsInstance(g["context_items"], int)
            self.assertGreaterEqual(g["context_knowledge_items"], 0)
            self.assertGreaterEqual(g["context_memory_items"], 0)
        finally:
            brain.stop()

    def test_package_reflects_current_utterance(self):
        brain = _brain()
        try:
            brain.step()  # perception fills the unified world
            brain.respond("tell me about the cup please", llm_chat=_transport)
            pkg = brain._last_context_package
            self.assertIsNotNone(pkg)
            self.assertIn("items", pkg)
            self.assertGreater(len(pkg["items"]), 0)
            utterance_layers = {i.get("layer") for i in pkg["items"]}
            self.assertTrue(utterance_layers <= {"immediate", "situational", "memory", "knowledge",
                                                 "relationship", "long-horizon"})
        finally:
            brain.stop()

    def test_discourse_hint_visible_in_grounding(self):
        brain = _brain()
        try:
            brain.respond("let's discuss the plant in the kitchen")
            out = brain.respond("is it still there?", llm_chat=_transport)
            g = out.get("grounding", {})
            self.assertEqual(g.get("discourse_topic_hint"), "plant")
        finally:
            brain.stop()

    def test_facts_include_package_knowledge_triples(self):
        brain = _brain()
        try:
            brain.knowledge.add("cup", "located_in", "kitchen", confidence=0.9, cycle=1)
            seen = {}

            def transport(*, system, user, temperature=0.5, timeout=120):
                import json
                seen.update(json.loads(user))
                return "nice"

            brain.respond("where is my cup?", llm_chat=transport)
            self.assertTrue(any("cup" in f for f in seen.get("facts_i_know", [])))
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
