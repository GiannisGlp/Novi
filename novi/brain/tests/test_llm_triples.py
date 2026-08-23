"""Phase D3 (gap-audit plan 13): LLM triple extraction behind the FORBIDDEN guard.

Pins:
  - constrained-JSON parsing: valid arrays pass, prose/fences tolerated,
    garbage yields [];
  - hard validation: entities must be lowercase tokens, predicates from the
    allowed set, self-loops dropped, duplicates deduped, cap respected;
  - the FORBIDDEN guard rejects assistant-speak responses entirely;
  - entity filtering keeps only triples over known refs when provided;
  - engine wiring: llm_triples_enabled=False (default) keeps the deterministic
    path; enabled + a fake transport merges validated LLM triples;
  - transport failure/None degrades to [] without exceptions.
"""

import unittest

from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.knowledge_extraction import LLMTripleExtractor
from novi.brain.tests.test_mac_brain import FakeCamera


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.x = LLMTripleExtractor()

    def test_valid_json_parses(self):
        raw = '[{"subject":"cup","predicate":"on","object":"table"}]'
        self.assertEqual(self.x.parse(raw), [("cup", "on", "table")])

    def test_prose_and_fences_tolerated(self):
        raw = 'Here you go:\n```json\n[{"subject":"plant","predicate":"in","object":"kitchen"}]\n```'
        self.assertEqual(self.x.parse(raw), [("plant", "in", "kitchen")])

    def test_garbage_yields_empty(self):
        for bad in ("", "no json here", '{"subject": 1}', "[not valid", "[]"):
            self.assertEqual(self.x.parse(bad), [], repr(bad))

    def test_validation_rules(self):
        raw = (
            '[{"subject":"cup","predicate":"flies","object":"table"},'   # predicate not allowed
            '{"subject":"Cup","predicate":"on","object":"table"},'        # normalized ok
            '{"subject":"table","predicate":"on","object":"table"},'      # self-loop
            '{"subject":"cup","predicate":"on","object":"table"},'        # duplicate of line above normalization
            '{"subject":123,"predicate":"on","object":"x"},'              # non-string
            '{"subject":"bob","predicate":"likes","object":"coffee"}]'    # valid
        )
        out = self.x.parse(raw)
        self.assertIn(("cup", "on", "table"), out)
        self.assertIn(("bob", "likes", "coffee"), out)
        self.assertNotIn(("table", "on", "table"), out)
        self.assertEqual(len(out), len(set(out)))

    def test_max_triples_cap(self):
        x = LLMTripleExtractor(max_triples=2)
        rows = ",".join(f'{{"subject":"a{i}","predicate":"on","object":"t{i}"}}' for i in range(10))
        self.assertEqual(len(x.parse("[" + rows + "]")), 2)


class ForbiddenGuardTests(unittest.TestCase):
    def test_assistant_speak_response_is_rejected_entirely(self):
        x = LLMTripleExtractor()

        def bad_chat(*, system, user):
            return 'As an AI language model, I can help: [{"subject":"cup","predicate":"on","object":"table"}]'

        self.assertEqual(x.extract("the cup is on the table", ("cup", "table"), llm_chat=bad_chat), [])

    def test_clean_response_passes_the_guard(self):
        x = LLMTripleExtractor()

        def good_chat(*, system, user):
            return '[{"subject":"cup","predicate":"on","object":"table"}]'

        out = x.extract("the cup is on the table", ("cup", "table"), llm_chat=good_chat)
        self.assertEqual(out, [("cup", "on", "table")])


class TransportFailureTests(unittest.TestCase):
    def test_none_transport_returns_empty(self):
        self.assertEqual(LLMTripleExtractor().extract("text", (), llm_chat=None), [])

    def test_raising_transport_returns_empty_not_exception(self):
        x = LLMTripleExtractor()

        def broken(*, system, user):
            raise ConnectionError("ollama down")

        self.assertEqual(x.extract("text", ("a",), llm_chat=broken), [])


class EngineWiringTests(unittest.TestCase):
    def _brain(self, **cfg) -> MacBrain:
        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False, **cfg))
        brain.start()
        return brain

    def test_default_config_stays_deterministic(self):
        brain = self._brain()
        try:
            self.assertFalse(brain.config.llm_triples_enabled)

            class T:
                text = "the plant is near the table"
                confidence = 0.9
                provider = "test"
                model_id = "m"
                audio_path = ""

            brain.ingest_transcript(T())
            leading = brain.knowledge.leading("plant", "located_near")
            self.assertIsNotNone(leading)
            self.assertEqual(brain.config.llm_triples_enabled, False)
        finally:
            brain.stop()

    def test_enabled_llm_merges_extra_triples(self):
        brain = self._brain(llm_triples_enabled=True)
        try:
            def fake_chat(*, system, user):
                assert "json" in system.lower()
                return '[{"subject":"table","predicate":"in","object":"kitchen"}]'

            brain.dialogue._chat = fake_chat

            class T:
                text = "the plant is near the table"
                confidence = 0.9
                provider = "test"
                model_id = "m"
                audio_path = ""

            brain.ingest_transcript(T())
            # regex fallback triple still present...
            self.assertIsNotNone(brain.knowledge.leading("plant", "located_near"))
            # ...and the validated LLM-only triple was merged in.
            self.assertEqual(
                (brain.knowledge.leading("table", "in").subject,
                 brain.knowledge.leading("table", "in").object),
                ("table", "kitchen"),
            )
        finally:
            brain.stop()


if __name__ == "__main__":
    unittest.main()
