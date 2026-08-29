"""Prompt-boundary caps: memory summaries must not bloat LLM prefill.

The sleep cycle consolidates memories into summaries that can run tens of
thousands of characters. When those were passed verbatim into prompts
(recall + chat grounding), every LLM call prefilled ~4K tokens (~10s).
These tests pin the caps at the prompt boundary.
"""

import unittest
from types import SimpleNamespace
from unittest import mock

from novi.brain.chat import ChatMixin


class _Record:
    def __init__(self, memory_type: str, content: str, memory_id: str = "m1",
                 confidence: float = 0.9, entity_refs: tuple = (),
                 created_at: str = "2026-08-29T00:00:00Z") -> None:
        self.memory_type = memory_type
        self.content = content
        self.memory_id = memory_id
        self.confidence = confidence
        self.entity_refs = entity_refs
        self.created_at = created_at


class _FakeMemory:
    def __init__(self, rows: list) -> None:
        self._rows = rows

    def active_rows(self) -> list:
        return [{"record": r} for r in self._rows]

    def retrieve_with_states(self, query: str, limit: int = 20) -> SimpleNamespace:
        return SimpleNamespace(
            records=self._rows[:limit], state="OK", candidates_examined=len(self._rows),
            conflicts=[], reason="",
        )


class PromptBoundTests(unittest.TestCase):
    def _brain(self, rows: list) -> ChatMixin:
        brain = ChatMixin.__new__(ChatMixin)
        brain.memory = _FakeMemory(rows)
        brain.governance = SimpleNamespace(store=None)
        brain._emit = mock.Mock()
        brain._cycle = 0
        return brain

    def test_memory_summaries_capped_at_400_chars(self) -> None:
        brain = self._brain([_Record("summary", "x" * 5000), _Record("summary", "y" * 5000)])
        out = brain._chat_memory_summaries()
        self.assertEqual(len(out), 2)
        self.assertTrue(all(len(s) <= 400 for s in out))

    def test_recall_content_capped_at_300_chars(self) -> None:
        brain = self._brain([_Record("summary", "z" * 5000)])
        out = brain._recall_context(SimpleNamespace(salient_entities=[]), [])
        self.assertEqual(len(out["memories"]), 1)
        self.assertLessEqual(len(out["memories"][0]["content"]), 300)

    def test_summary_prompt_is_bounded(self) -> None:
        from novi.brain.models.summarizer import _summary_prompt

        records = [_Record("perception", "r" * 1000) for _ in range(200)]
        prompt = _summary_prompt("room", records)
        # 20 records x 200 chars + instructions — must stay well under ~6K chars.
        self.assertLess(len(prompt), 6000)

    def test_deterministic_summary_is_bounded(self) -> None:
        from novi.brain.consolidation import SummaryConsolidator

        records = [_Record("perception", "q" * 2000) for _ in range(50)]
        out = SummaryConsolidator._summarize("room", records)
        self.assertLess(len(out), 4000)

    def test_narrator_is_cached_until_new_episodes(self) -> None:
        rows = [_Record("perception", "saw a cup", memory_id="m1", created_at="2026-08-29T00:00:01Z"),
                _Record("perception", "cup moved", memory_id="m2", created_at="2026-08-29T00:00:02Z")]
        brain = self._brain(rows)
        brain.narrator = mock.Mock(return_value="A cup appeared and moved.")
        first = brain._episodic_narrative()
        second = brain._episodic_narrative()
        self.assertEqual(first, second)
        self.assertEqual(brain.narrator.call_count, 1)
        # New episode -> narrator runs again.
        brain.memory._rows.append(_Record("perception", "cup gone", memory_id="m3", created_at="2026-08-29T00:00:03Z"))
        brain._episodic_narrative()
        self.assertEqual(brain.narrator.call_count, 2)


if __name__ == "__main__":
    unittest.main()
