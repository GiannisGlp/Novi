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
            s.switch_model("qwen3.8:27b")
            self.assertEqual(s._reasoning_provider.model, "qwen3.8:27b")
        finally:
            s.stop()

    def test_unknown_model_still_rejected(self) -> None:
        s = self._server()
        try:
            with self.assertRaises(ValueError):
                s.switch_model("does-not-exist")
        finally:
            s.stop()

    def test_apply_model_prefers_set_model_capability(self) -> None:
        """A provider exposing both .model and set_model must be switched via set_model (H3)."""
        s = self._server()
        try:
            calls = {"set_model": 0}

            class _Fake:
                model = "qwen3:4b"

                def set_model(self, name: str) -> None:
                    calls["set_model"] += 1
                    self.model = name

            s._reasoning_provider = _Fake()
            s._apply_model_to_components()
            self.assertEqual(calls["set_model"], 1, "set_model must be preferred over .model assignment")
        finally:
            s.stop()

    def test_ollama_provider_switch_rebuilds_backend(self) -> None:
        """OllamaReasoningProvider.set_model rebuilds the closure; a bare .model
        assignment would leave the captured model stale (H3)."""
        from novi.brain.models.ollama_reasoning import OllamaReasoningProvider

        s = self._server()
        try:
            provider = OllamaReasoningProvider(model="qwen3:4b")
            old_llm = provider._llm
            s._reasoning_provider = provider
            s._apply_model_to_components()
            self.assertIsNot(provider._llm, old_llm, "set_model must rebuild the backend")
            self.assertEqual(provider.model, "qwen3:4b")
        finally:
            s.stop()

    def test_switch_model_holds_the_lock(self) -> None:
        """switch_model mutates shared state under the server lock (M1)."""
        s = self._server()
        try:
            held = {"v": False}
            orig = s._apply_model_to_components

            def wrapped() -> None:
                held["v"] = s._lock._is_owned()
                orig()

            s._apply_model_to_components = wrapped
            s.switch_model("qwen3:8b")
            self.assertTrue(held["v"], "switch_model must hold the lock while mutating state")
        finally:
            s.stop()


class ModelAvailabilityTests(unittest.TestCase):
    """_llm_up must only claim availability when the CURRENT model is pulled (M2)."""

    def _server(self, **kw) -> NoviWebServer:
        defaults = {"port": 0, "store_path": None, "auto_step": False, "chat_llm": False}
        defaults.update(kw)
        return NoviWebServer(**defaults)

    def _stub_tags(self, names: list[str]):
        import json as _json
        from unittest import mock

        resp = mock.MagicMock()
        resp.read.return_value = _json.dumps({"models": [{"name": n} for n in names]}).encode("utf-8")
        resp.__enter__.return_value = resp  # `with urlopen(...) as response` yields resp itself
        return mock.patch("urllib.request.urlopen", return_value=resp)

    def test_llm_up_false_when_current_model_not_pulled(self) -> None:
        s = self._server()
        try:
            s.llm_model = "qwen3:4b"
            s._llm_available = None
            s._llm_probed_at = 0.0
            with self._stub_tags(["qwen3:8b"]):
                self.assertFalse(s._llm_up())
        finally:
            s.stop()

    def test_llm_up_true_when_current_model_pulled(self) -> None:
        s = self._server()
        try:
            s.llm_model = "qwen3:4b"
            s._llm_available = None
            s._llm_probed_at = 0.0
            with self._stub_tags(["qwen3:4b", "qwen3:8b"]):
                self.assertTrue(s._llm_up())
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
            # 300 tokens with thinking disabled on fast tiers: the
            # analysis/options/decision JSON fits in ~220 tokens; 600 let the
            # model ramble at ~30 tok/s (~20s per chat turn).
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
                s.switch_model("qwen3.8:27b")
            finally:
                s.stop()
            self.assertIsNone(server_mod._load_model_choice(store))


class FastWrapperRefreshTests(unittest.TestCase):
    """L3: the fast_* wrappers' .model must track switch_model."""

    def _server(self, **kw) -> NoviWebServer:
        defaults = {"port": 0, "store_path": None, "auto_step": False, "chat_llm": False}
        defaults.update(kw)
        return NoviWebServer(**defaults)

    def test_fast_wrappers_model_refreshed_on_switch(self) -> None:
        s = self._server()
        try:
            s.switch_model("qwen3:8b")
            self.assertEqual(s._fast_narrator.model, "qwen3:8b")
            self.assertEqual(s._fast_summarizer.model, "qwen3:8b")
            self.assertEqual(s._fast_conv_summarizer.model, "qwen3:8b")
        finally:
            s.stop()


class AtomicModelChoiceTests(unittest.TestCase):
    """L4: model.json writes must be atomic (temp file + os.replace)."""

    def test_failed_write_leaves_previous_choice_intact(self) -> None:
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "novi.db")
            server_mod._save_model_choice(store, "qwen3:4b")
            self.assertEqual(server_mod._load_model_choice(store), "qwen3:4b")
            with mock.patch("os.replace", side_effect=OSError("disk full")):
                server_mod._save_model_choice(store, "qwen3:8b")
            self.assertEqual(server_mod._load_model_choice(store), "qwen3:4b")

    def test_no_temp_file_left_behind(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = str(Path(td) / "novi.db")
            server_mod._save_model_choice(store, "qwen3:4b")
            leftovers = [p.name for p in Path(td).glob("*.tmp")]
            self.assertEqual(leftovers, [])


class LlmUrlPropagationTests(unittest.TestCase):
    """L5: every LLM provider must be built against self.llm_url."""

    def test_providers_receive_llm_url(self) -> None:
        s = NoviWebServer(
            port=0, store_path=None, auto_step=False, chat_llm=False, llm_url="http://127.0.0.1:11435"
        )
        try:
            self.assertEqual(s._reasoning_provider.llm.base_url, "http://127.0.0.1:11435")
            self.assertEqual(s._narrator_inner.base_url, "http://127.0.0.1:11435")
            self.assertEqual(s._summarizer_inner.base_url, "http://127.0.0.1:11435")
            self.assertEqual(s._conversation_summarizer_inner.base_url, "http://127.0.0.1:11435")
        finally:
            s.stop()


class NarrativeCacheTests(unittest.TestCase):
    """/api/state must not trigger an LLM narrator call on every poll."""

    def _store_server(self) -> tuple[NoviWebServer, tempfile.TemporaryDirectory]:
        td = tempfile.TemporaryDirectory()
        store = str(Path(td.name) / "novi.db")
        s = NoviWebServer(port=0, store_path=store, auto_step=False, chat_llm=True)
        s._llm_available = True
        return s, td

    def _wait_for_narrative(self, s: NoviWebServer, timeout: float = 2.0) -> None:
        """Block until the background regeneration thread finishes (M3)."""
        import time

        deadline = time.time() + timeout
        while s._narrative_regenerating and time.time() < deadline:
            time.sleep(0.01)

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
            self._wait_for_narrative(s)
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
            self._wait_for_narrative(s)
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
            self._wait_for_narrative(s)
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
            self._wait_for_narrative(s)
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

    def test_regeneration_runs_off_the_lock_and_does_not_double_run(self) -> None:
        """M3: a cache miss returns immediately and never double-runs the narrator."""
        import threading as _threading
        import time

        s, td = self._store_server()
        try:
            started = _threading.Event()
            release = _threading.Event()
            calls = {"n": 0}

            def slow_narrator(episodes):  # type: ignore[no-untyped-def]
                calls["n"] += 1
                started.set()
                release.wait(timeout=2.0)
                return "narrated"

            s.brain.narrator = slow_narrator
            s.brain.memory.admit(
                memory_type="utterance",
                content="hello there",
                confidence=0.9,
                verification_status="unverified",
                privacy_class="public",
                provenance={"source": "test"},
            )
            # first call spawns the background regeneration and returns at once
            self.assertEqual(s._cached_narrative(), [])
            self.assertTrue(started.wait(timeout=2.0), "narrator must run on a background thread")
            # a second poll while regenerating must NOT block or double-run
            self.assertEqual(s._cached_narrative(), [])
            self.assertEqual(calls["n"], 1)
            release.set()
            # once the thread completes, the fresh narrative is served
            deadline = time.time() + 2.0
            while s._narrative_regenerating and time.time() < deadline:
                time.sleep(0.01)
            self.assertEqual(s._cached_narrative(), ["narrated"])
        finally:
            release.set()
            s.stop()
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
