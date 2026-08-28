"""Phase 1 quick wins: model propagation, deliberation shrink, persistence, narrative cache.

Every test is deterministic — no Ollama, no network. The narrative-cache tests use a
temp-file store so ``active_rows`` is available and the narrator is reachable.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novi.web import server as server_mod
from novi.web.server import NoviWebServer


class ModelPropagationTests(unittest.TestCase):
    """switch_model must re-point every LLM component at the chosen model."""

    def _server(self, **kw) -> NoviWebServer:
        defaults = {"port": 0, "store_path": None, "auto_step": False, "chat_llm": False}
        defaults.update(kw)
        return NoviWebServer(**defaults)

    def test_default_model_is_qwen3_4b(self) -> None:
        s = self._server()
        try:
            self.assertEqual(s.llm_model, "qwen3:4b")
            self.assertEqual(s._reasoning_provider.llm.model, "qwen3:4b")
            self.assertEqual(s._narrator_inner.model, "qwen3:4b")
        finally:
            s.stop()

    def test_switch_model_propagates_to_all_components(self) -> None:
        s = self._server()
        try:
            s.switch_model("qwen3:8b")
            self.assertEqual(s.llm_model, "qwen3:8b")
            self.assertEqual(s._reasoning_provider.llm.model, "qwen3:8b")
            self.assertEqual(s._narrator_inner.model, "qwen3:8b")
            self.assertEqual(s._summarizer_inner.model, "qwen3:8b")
            self.assertEqual(s._conversation_summarizer_inner.model, "qwen3:8b")
        finally:
            s.stop()

    def test_switch_model_ollama_mode_propagates_direct_provider(self) -> None:
        s = self._server(reasoning="ollama")
        try:
            s.switch_model("qwen3:32b")
            self.assertEqual(s._reasoning_provider.model, "qwen3:32b")
        finally:
            s.stop()

    def test_unknown_model_still_rejected(self) -> None:
        s = self._server()
        try:
            with self.assertRaises(ValueError):
                s.switch_model("does-not-exist")
        finally:
            s.stop()


class DeliberationShrinkTests(unittest.TestCase):
    """The web path uses a single-round, bounded deliberation (fast replies)."""

    def _server(self, **kw) -> NoviWebServer:
        defaults = {"port": 0, "store_path": None, "auto_step": False, "chat_llm": False}
        defaults.update(kw)
        return NoviWebServer(**defaults)

    def test_default_deliberation_is_single_round_and_bounded(self) -> None:
        s = self._server()
        try:
            llm = s._reasoning_provider.llm
            self.assertEqual(s.deliberation_rounds, 1)
            self.assertEqual(llm.max_rounds, 1)
            self.assertEqual(llm.max_tokens, 300)
            self.assertEqual(llm.timeout, 30)
        finally:
            s.stop()

    def test_deliberation_rounds_configurable(self) -> None:
        s = self._server(deliberation_rounds=2)
        try:
            self.assertEqual(s._reasoning_provider.llm.max_rounds, 2)
        finally:
            s.stop()


class ModelPersistenceTests(unittest.TestCase):
    """The UI-selected model survives a server restart (opt-in via persist_model)."""

    def test_switch_model_persists_and_reloads(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "novi.db")
            s = NoviWebServer(port=0, store_path=store, auto_step=False, chat_llm=False, persist_model=True)
            try:
                s.switch_model("qwen3:8b")
            finally:
                s.stop()
            self.assertEqual(server_mod._load_model_choice(store), "qwen3:8b")
            s2 = NoviWebServer(port=0, store_path=store, auto_step=False, chat_llm=False, persist_model=True)
            try:
                self.assertEqual(s2.llm_model, "qwen3:8b")
            finally:
                s2.stop()

    def test_explicit_model_wins_over_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "novi.db")
            server_mod._save_model_choice(store, "nemotron-3.5-lightning")
            s = NoviWebServer(
                port=0, store_path=store, auto_step=False, chat_llm=False, persist_model=True, llm_model="qwen3:4b"
            )
            try:
                self.assertEqual(s.llm_model, "qwen3:4b")
            finally:
                s.stop()

    def test_no_persist_means_no_file_written(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "novi.db")
            s = NoviWebServer(port=0, store_path=store, auto_step=False, chat_llm=False)
            try:
                s.switch_model("qwen3:32b")
            finally:
                s.stop()
            self.assertIsNone(server_mod._load_model_choice(store))


class NarrativeCacheTests(unittest.TestCase):
    """/api/state must not trigger an LLM narrator call on every poll."""

    def _store_server(self) -> tuple[NoviWebServer, tempfile.TemporaryDirectory]:
        td = tempfile.TemporaryDirectory()
        store = str(Path(td.name) / "novi.db")
        s = NoviWebServer(port=0, store_path=store, auto_step=False, chat_llm=True)
        s._llm_available = True
        return s, td

    def test_cache_reused_when_no_new_episodic_memory(self) -> None:
        s, td = self._store_server()
        try:
            calls = {"n": 0}

            def fake_narrator(episodes):  # type: ignore[no-untyped-def]
                calls["n"] += 1
                return "narrated"

            s.brain.narrator = fake_narrator
            s.brain.memory.admit(
                memory_type="utterance",
                content="hello there",
                confidence=0.9,
                verification_status="unverified",
                privacy_class="public",
                provenance={"source": "test"},
            )
            s._cached_narrative()
            s._cached_narrative()
            self.assertEqual(calls["n"], 1, "second poll must reuse the cache")
        finally:
            s.stop()
            td.cleanup()

    def test_cache_invalidates_on_new_episodic_memory(self) -> None:
        s, td = self._store_server()
        try:
            calls = {"n": 0}

            def fake_narrator(episodes):  # type: ignore[no-untyped-def]
                calls["n"] += 1
                return "narrated"

            s.brain.narrator = fake_narrator
            s.brain.memory.admit(
                memory_type="utterance",
                content="hello there",
                confidence=0.9,
                verification_status="unverified",
                privacy_class="public",
                provenance={"source": "test"},
            )
            s._cached_narrative()
            self.assertEqual(calls["n"], 1)
            s._cached_narrative()
            self.assertEqual(calls["n"], 1, "no new memory -> cache hit")
            s.brain.memory.admit(
                memory_type="utterance",
                content="second thing",
                confidence=0.9,
                verification_status="unverified",
                privacy_class="public",
                provenance={"source": "test"},
            )
            s._cached_narrative()
            self.assertEqual(calls["n"], 2, "new memory invalidates the cache")
        finally:
            s.stop()
            td.cleanup()

    def test_non_episodic_memory_does_not_invalidate(self) -> None:
        s, td = self._store_server()
        try:
            calls = {"n": 0}

            def fake_narrator(episodes):  # type: ignore[no-untyped-def]
                calls["n"] += 1
                return "narrated"

            s.brain.narrator = fake_narrator
            s.brain.memory.admit(
                memory_type="utterance",
                content="hello there",
                confidence=0.9,
                verification_status="unverified",
                privacy_class="public",
                provenance={"source": "test"},
            )
            s._cached_narrative()
            self.assertEqual(calls["n"], 1)
            s.brain.memory.admit(
                memory_type="summary",
                content="a consolidation",
                confidence=0.8,
                verification_status="consolidated",
                privacy_class="public",
                provenance={"source": "test"},
            )
            s._cached_narrative()
            self.assertEqual(calls["n"], 1, "a summary memory is not episodic")
        finally:
            s.stop()
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
