"""LLM-enhanced episodic narrative (Memory 3.3).

Verifies the LLMNarrator (natural "what happened" recap via Ollama) and that the
runtime uses it when available, falling back to the deterministic list otherwise.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from brain.models.narrator import LLMNarrator, _extract_narrative
from brain.models.stt import TranscriptionResult
from brain.engine import MacBrain, MacBrainConfig
from brain.tests.test_mac_brain import FakeCamera


class ExtractNarrativeTests(unittest.TestCase):
    def test_parses_plain_json(self):
        self.assertEqual(_extract_narrative('{"narrative": "alice moved the door"}'), "alice moved the door")

    def test_parses_embedded_json(self):
        self.assertEqual(_extract_narrative('prefix {"narrative": "gist"} suffix'), "gist")

    def test_empty_returns_none(self):
        self.assertIsNone(_extract_narrative(""))


class _FakeResp:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class LLMNarratorTests(unittest.TestCase):
    def test_returns_natural_narrative(self):
        def _urlopen(request, timeout=60):
            return _FakeResp(json.dumps({"response": json.dumps({"narrative": "Alice moved the door, then said hello."})}).encode("utf-8"))

        with mock.patch("urllib.request.urlopen", _urlopen):
            n = LLMNarrator()
            result = n([{"memory_type": "utterance", "content": "alice moved the door"}])
        self.assertEqual(result, "Alice moved the door, then said hello.")


class NarratorRuntimeTests(unittest.TestCase):
    def _brain(self, store_path, narrator=None):
        return MacBrain(camera=FakeCamera(), store_path=store_path, narrator=narrator, config=MacBrainConfig())

    def _hear(self, brain, text):
        return brain.ingest_transcript(TranscriptionResult(text=text, language="en", confidence=0.9, audio_path="", provider="web", model_id="web"))

    def test_uses_llm_narrative_when_provided(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "m.db")
            brain = self._brain(db, narrator=lambda episodes: "Alice moved the door, then said hello.")
            brain.start()
            try:
                self._hear(brain, "alice moved the door")
                self._hear(brain, "alice said hello")
                narrative = brain._episodic_narrative()
                self.assertEqual(narrative, ["Alice moved the door, then said hello."])
            finally:
                brain.stop()

    def test_falls_back_to_deterministic_when_narrator_fails(self):
        with tempfile.TemporaryDirectory() as td:
            db = str(Path(td) / "m.db")

            def _broken(episodes):
                raise RuntimeError("llm down")

            brain = self._brain(db, narrator=_broken)
            brain.start()
            try:
                self._hear(brain, "alice moved the door")
                narrative = brain._episodic_narrative()
                self.assertTrue(any("alice moved the door" in n for n in narrative), narrative)
            finally:
                brain.stop()


if __name__ == "__main__":
    unittest.main()
