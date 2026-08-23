"""LLM-enhanced memory summaries (Memory 3.1).

Verifies the LLMSummarizer (semantic gist via Ollama) and that SummaryConsolidator
uses it when available, falling back to the deterministic concatenation otherwise.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from novi.brain.consolidation import SummaryConsolidator
from novi.brain.models.summarizer import LLMSummarizer, _extract_summary
from novi.brain.storage import DurableMemoryStore


class ExtractSummaryTests(unittest.TestCase):
    def test_parses_plain_json(self):
        self.assertEqual(_extract_summary('{"summary": "alice is active"}'), "alice is active")

    def test_parses_embedded_json(self):
        self.assertEqual(_extract_summary('prefix {"summary": "gist"} suffix'), "gist")

    def test_empty_returns_none(self):
        self.assertIsNone(_extract_summary(""))


class _FakeResp:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class LLMSummarizerTests(unittest.TestCase):
    def test_returns_semantic_summary(self):
        def _urlopen(request, timeout=60):
            return _FakeResp(json.dumps({"response": json.dumps({"summary": "alice is an active person who moved the door and likes jazz"})}).encode("utf-8"))

        with mock.patch("urllib.request.urlopen", _urlopen):
            s = LLMSummarizer()
            result = s("alice", [])
        self.assertEqual(result, "alice is an active person who moved the door and likes jazz")


class ConsolidatorSummarizerTests(unittest.TestCase):
    def _store(self, td):
        return DurableMemoryStore(str(Path(td) / "m.db"))

    def _admit(self, store, text, entity):
        return store.admit(
            memory_type="utterance", content=text, confidence=0.9, verification_status="verified",
            privacy_class="public", provenance={"source": "test"}, entity_refs=(entity,),
        )

    def test_uses_llm_summary_when_provided(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            self._admit(store, "alice moved the door", "alice")
            self._admit(store, "alice likes jazz", "alice")
            c = SummaryConsolidator(store, summarizer=lambda entity, records: "alice is an active person")
            c.consolidate()
            summaries = [r["record"] for r in store.active_rows() if r["record"].memory_type == "summary"]
            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0].content, "alice is an active person")

    def test_falls_back_to_deterministic_when_summarizer_fails(self):
        with tempfile.TemporaryDirectory() as td:
            store = self._store(td)
            self._admit(store, "alice moved the door", "alice")
            self._admit(store, "alice likes jazz", "alice")

            def _broken(entity, records):
                raise RuntimeError("llm down")

            c = SummaryConsolidator(store, summarizer=_broken)
            c.consolidate()
            summaries = [r["record"] for r in store.active_rows() if r["record"].memory_type == "summary"]
            self.assertEqual(len(summaries), 1)
            self.assertIn("alice moved the door", summaries[0].content)
            self.assertIn("alice likes jazz", summaries[0].content)


if __name__ == "__main__":
    unittest.main()
