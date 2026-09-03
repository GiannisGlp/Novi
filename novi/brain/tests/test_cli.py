"""Tests for the terminal CLI guards (novi/brain/cli.py)."""

from __future__ import annotations

import argparse
import io
import unittest

from novi.brain.cli import (
    _brain_config_from_args,
    _neural_without_image_source,
    run_chat_loop,
)


def _args(**kw) -> argparse.Namespace:
    base = {"neural": False, "live_camera": False, "neural_image": None}
    base.update(kw)
    return argparse.Namespace(**base)


class NeuralSourceGuardTests(unittest.TestCase):
    def test_neural_with_demo_camera_needs_image_source(self) -> None:
        self.assertTrue(_neural_without_image_source(_args(neural=True)))

    def test_neural_with_live_camera_is_fine(self) -> None:
        self.assertFalse(_neural_without_image_source(_args(neural=True, live_camera=True)))

    def test_neural_with_static_image_is_fine(self) -> None:
        self.assertFalse(_neural_without_image_source(_args(neural=True, neural_image="novi/assets/test-image.png")))

    def test_deterministic_demo_is_fine(self) -> None:
        self.assertFalse(_neural_without_image_source(_args()))


class _FakeChatBrain:
    """Minimal respond()/default_llm_chat() double for the REPL loop."""

    def __init__(self, replies=None) -> None:
        self.calls: list[dict] = []
        self._replies = list(replies or [])
        self.transport_calls = 0

    def default_llm_chat(self):
        self.transport_calls += 1
        return "transport-sentinel"

    def respond(self, text, **kw):
        self.calls.append({"text": text, **kw})
        reply = self._replies.pop(0) if self._replies else f"echo:{text}"
        return {"text": reply}


class _FakeSpeaker:
    def __init__(self) -> None:
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)


class ChatLoopTests(unittest.TestCase):
    def _run(self, brain, stdin_text, speaker=None):
        out = io.StringIO()
        code = run_chat_loop(brain, speaker=speaker, stdin=io.StringIO(stdin_text), stdout=out)
        return code, out.getvalue()

    def test_single_turn_uses_full_respond_path(self) -> None:
        brain = _FakeChatBrain()
        code, output = self._run(brain, "hello novi\nquit\n")
        self.assertEqual(code, 0)
        self.assertIn("novi: echo:hello novi", output)
        self.assertEqual(len(brain.calls), 1)
        call = brain.calls[0]
        self.assertEqual(call["text"], "hello novi")
        self.assertEqual(call["history"], [])
        self.assertEqual(call["llm_chat"], "transport-sentinel")
        self.assertTrue(call["learn"])

    def test_history_carries_across_turns_and_speaks(self) -> None:
        brain = _FakeChatBrain()
        speaker = _FakeSpeaker()
        code, output = self._run(brain, "first\nsecond\nquit\n", speaker=speaker)
        self.assertEqual(code, 0)
        self.assertEqual(len(brain.calls), 2)
        self.assertEqual(brain.calls[1]["history"], [
            {"role": "user", "text": "first"},
            {"role": "novi", "text": "echo:first"},
        ])
        self.assertEqual(speaker.spoken, ["echo:first", "echo:second"])

    def test_history_stays_bounded(self) -> None:
        from novi.brain.cli import CHAT_HISTORY_TURNS

        brain = _FakeChatBrain()
        lines = "".join(f"msg {i}\n" for i in range(CHAT_HISTORY_TURNS * 3)) + "quit\n"
        self._run(brain, lines)
        last_history = brain.calls[-1]["history"]
        self.assertLessEqual(len(last_history), 2 * CHAT_HISTORY_TURNS)

    def test_blank_lines_skipped_and_eof_exits_cleanly(self) -> None:
        brain = _FakeChatBrain()
        code, output = self._run(brain, "\n   \nhello\n")
        self.assertEqual(code, 0)
        self.assertEqual(len(brain.calls), 1)

    def test_reply_failure_prints_and_continues(self) -> None:
        class Flaky(_FakeChatBrain):
            def respond(self, text, **kw):
                self.calls.append({"text": text, **kw})
                if text == "boom":
                    raise RuntimeError("adapter hiccup")
                return {"text": f"echo:{text}"}

        brain = Flaky()
        code, output = self._run(brain, "boom\nhello\nquit\n")
        self.assertEqual(code, 0)
        self.assertIn("adapter hiccup", output)
        self.assertIn("novi: echo:hello", output)

    def test_config_helper_maps_trained_flags(self) -> None:
        args = argparse.Namespace(
            trained_reply=True,
            trained_dialogue_adapter="/adapters/dialogue",
            trained_emotional_adapter="/adapters/emotional",
            trained_base_model="Qwen/Qwen3-8B",
        )
        cfg = _brain_config_from_args(args)
        self.assertTrue(cfg.trained_reply_enabled)
        self.assertEqual(cfg.trained_dialogue_adapter, "/adapters/dialogue")
        self.assertEqual(cfg.trained_emotional_adapter, "/adapters/emotional")
        self.assertEqual(cfg.trained_base_model, "Qwen/Qwen3-8B")

    def test_config_helper_maps_brain_llm_flags(self) -> None:
        args = argparse.Namespace(
            brain_llm=True,
            brain_llm_url="http://localhost:11434",
            brain_llm_model="qwen3:8b",
        )
        cfg = _brain_config_from_args(args)
        self.assertTrue(cfg.brain_llm_enabled)
        self.assertEqual(cfg.brain_llm_url, "http://localhost:11434")
        self.assertEqual(cfg.brain_llm_model, "qwen3:8b")

    def test_config_helper_defaults_keep_ci_transport_free(self) -> None:
        cfg = _brain_config_from_args(argparse.Namespace())
        self.assertFalse(cfg.trained_reply_enabled)
        self.assertFalse(cfg.brain_llm_enabled)

    def test_config_helper_maps_brain_llm_server(self) -> None:
        cfg = _brain_config_from_args(argparse.Namespace(brain_llm_server="openai-compatible"))
        self.assertEqual(cfg.brain_llm_server, "openai-compatible")
        self.assertEqual(_brain_config_from_args(argparse.Namespace()).brain_llm_server, "ollama")


class AutoStepLoopTests(unittest.TestCase):
    def test_steps_until_stopped(self) -> None:
        import threading
        import time

        from novi.brain.cli import _auto_step_loop

        class FakeBrain:
            def __init__(self) -> None:
                self.steps = 0

            def step(self):
                self.steps += 1
                return {}

        brain, stop, stats = FakeBrain(), threading.Event(), {}
        worker = threading.Thread(
            target=_auto_step_loop,
            kwargs={"brain": brain, "interval_s": 0.01, "stop_event": stop, "stats": stats},
            daemon=True,
        )
        worker.start()
        time.sleep(0.12)
        stop.set()
        worker.join(timeout=5.0)
        self.assertFalse(worker.is_alive())
        self.assertGreaterEqual(brain.steps, 2)
        self.assertEqual(stats.get("errors"), 0)

    def test_step_errors_counted_never_fatal(self) -> None:
        import threading
        from unittest import mock

        import novi.brain.cli as cli_mod

        class ExplodingBrain:
            def step(self):
                raise RuntimeError("boom")

        stop, stats = threading.Event(), {}
        real_wait = stop.wait
        calls = {"n": 0}

        def _wait_twice(timeout):
            # let exactly two ticks through, then stop
            calls["n"] += 1
            if calls["n"] > 2:
                stop.set()
                return True
            return real_wait(0.001)

        with mock.patch.object(stop, "wait", side_effect=_wait_twice):
            cli_mod._auto_step_loop(
                ExplodingBrain(), interval_s=0.01, stop_event=stop, stats=stats
            )
        self.assertEqual(stats.get("errors"), 2)
        self.assertIn("boom", stats.get("first_error", ""))

    def test_chat_loop_passes_person_through(self) -> None:
        import io

        from novi.brain.cli import run_chat_loop

        brain = _FakeChatBrain()
        out = io.StringIO()
        code = run_chat_loop(
            brain, stdin=io.StringIO("hello\nquit\n"), stdout=out, person="alice"
        )
        self.assertEqual(code, 0)
        self.assertEqual(brain.calls[0].get("person"), "alice")

    def test_resolve_adapter_prefers_explicit_value(self) -> None:
        from novi.brain.cli import _resolve_adapter

        self.assertEqual(_resolve_adapter("/custom/adapter", "whatever-v1"), "/custom/adapter")

    def test_resolve_adapter_empty_and_missing_default(self) -> None:
        from novi.brain.cli import _resolve_adapter

        self.assertEqual(_resolve_adapter("", "no-such-adapter-v0"), "")

    def test_resolve_adapter_falls_back_to_bundled_dir(self) -> None:
        from unittest import mock

        from novi.brain.cli import _resolve_adapter

        with mock.patch(
            "novi.brain.cli._default_adapter_dir", return_value="/repo/training/models/adapters/x-v1"
        ):
            self.assertEqual(
                _resolve_adapter("", "x-v1"), "/repo/training/models/adapters/x-v1"
            )


if __name__ == "__main__":
    unittest.main()
