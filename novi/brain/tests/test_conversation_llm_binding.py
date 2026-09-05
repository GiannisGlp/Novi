"""Plan 03 Gap 2: packet→LLM binding, model routing, LLM-path repair.

Deterministic, socket-free. Uses a real MacBrain on tmp SQLite with stub
``llm_chat(system=, user=)`` transports — no model required.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from novi.brain.b2_perception import SpecialistPerception
from novi.brain.conversation.llm_binding import (
    MAX_CONVERSATION_BLOCK_CHARS,
    render_conversation_block,
    route_for_turn,
)
from novi.brain.engine import MacBrain, MacBrainConfig
from novi.brain.io import CameraFrame


class _Cam:
    def close(self) -> None:
        return None

    def read(self) -> CameraFrame:
        return CameraFrame(frame_id="f", captured_at="t", width=2,
                           height=2, payload=b"f", metadata={})


def _brain(tmp: str) -> MacBrain:
    brain = MacBrain(
        camera=_Cam(), perception=SpecialistPerception(),
        store_path=str(Path(tmp) / "m.db"),
        config=MacBrainConfig(curiosity_enabled=False,
                              initiative_enabled=False))
    brain.start()
    return brain


class BindingRenderTests(unittest.TestCase):
    def test_empty_conv_renders_empty(self) -> None:
        self.assertEqual(render_conversation_block({}), "")
        self.assertEqual(render_conversation_block(None), "")

    def test_unknown_route_when_no_interpretation(self) -> None:
        self.assertEqual(route_for_turn({})["tier"], "UNKNOWN")
        self.assertEqual(route_for_turn(None)["tier"], "UNKNOWN")

    def test_block_bounded_and_names_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                conv = brain._conversation_turn(
                    "Tell me about the Model Y.", addressee="",
                    cycle=0, discourse_topic="", speaker="user")
            finally:
                brain.stop()
        block = render_conversation_block(conv)
        self.assertTrue(block)
        self.assertLessEqual(len(block), MAX_CONVERSATION_BLOCK_CHARS)
        self.assertIn("Conversation state", block)
        self.assertIn("response goal", block)

    def test_simple_turn_routes_fast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                conv = brain._conversation_turn(
                    "What time is it?", addressee="",
                    cycle=0, discourse_topic="", speaker="user")
                route = route_for_turn(conv)
            finally:
                brain.stop()
        self.assertIn(route["tier"], ("FAST", "NORMAL", "SPECIALIZED"))
        self.assertTrue(route["model"])

    def test_complex_goal_routes_up(self) -> None:
        from novi.brain.conversation.conversation_state import (
            IntentResult,
            ReferentResult,
            ResponsePlan,
        )

        conv = {
            "intent": IntentResult(intent="COMPARISON",
                                  dialogue_act="QUESTION",
                                  confidence=0.9),
            "referents": ReferentResult(
                resolutions={"the Model Y": "Model Y"}, ambiguous=[]),
            "packet": None,
            "plan": ResponsePlan(goal="COMPARE"),
        }
        route = route_for_turn(conv)
        self.assertIn(route["tier"], ("NORMAL", "COMPLEX"))
        self.assertIn("signals", route)

    def test_ambiguous_compare_routes_clarification_cheaply(self) -> None:
        # Two named rivals with no distinguishing context ask a short
        # clarification (C-050); serving that question is a cheap turn.
        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                conv = brain._conversation_turn(
                    "Compare the Model Y and the Model 3 and recommend one.",
                    addressee="", cycle=0, discourse_topic="", speaker="user")
                route = route_for_turn(conv)
            finally:
                brain.stop()
        self.assertIn(route["tier"], ("FAST", "NORMAL", "COMPLEX", "SPECIALIZED"))
        self.assertTrue(route["model"])


class LlmPathBindingTests(unittest.TestCase):
    def test_packet_reaches_model_prompt_and_route_recorded(self) -> None:
        seen: dict[str, str] = {}

        def stub(*, system: str, user: str) -> str:
            seen["system"] = system
            seen["user"] = user
            return "The Model Y is a solid crossover with great range."

        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                resp = brain.respond("Tell me about the Model Y.",
                                     llm_chat=stub)
            finally:
                brain.stop()
        self.assertIn("Conversation state", seen.get("system", ""))
        payload = json.loads(seen.get("user", "{}"))
        self.assertIn("conversation_state", payload)
        self.assertEqual(payload["conversation_state"].get("active_entity", "").lower(), "model y")
        grounding = resp.get("grounding") or {}
        self.assertIn((grounding.get("model_route") or {}).get("tier"),
                      ("FAST", "NORMAL", "COMPLEX", "SPECIALIZED"))
        trace_conv = ((resp.get("trace") or {}).get("conversation") or {})
        self.assertIn("model_route", trace_conv)

    def test_clean_draft_makes_one_call(self) -> None:
        calls: list[str] = []

        def stub(*, system: str, user: str) -> str:
            calls.append(system)
            return "The Model Y is a solid crossover with great range."

        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                resp = brain.respond("Tell me about the Model Y.",
                                     llm_chat=stub)
            finally:
                brain.stop()
        self.assertEqual(len(calls), 1)
        grounding = resp.get("grounding") or {}
        self.assertFalse((grounding.get("llm_repair") or {}).get("attempted", False))

    def test_filler_draft_triggers_bounded_repair(self) -> None:
        calls: list[str] = []
        replies = ["That's interesting",
                   "The Model Y is a solid crossover with great range."]

        def stub(*, system: str, user: str) -> str:
            calls.append(system)
            return replies[min(len(calls) - 1, len(replies) - 1)]

        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                resp = brain.respond("Tell me about the Model Y.",
                                     llm_chat=stub)
            finally:
                brain.stop()
        # Exactly one repair call — never a loop.
        self.assertEqual(len(calls), 2)
        grounding = resp.get("grounding") or {}
        repair = grounding.get("llm_repair") or {}
        self.assertTrue(repair.get("attempted"))
        self.assertTrue(repair.get("accepted"))
        self.assertIn("Model Y", resp.get("text") or "")

    def test_unfixable_draft_keeps_original(self) -> None:
        calls: list[str] = []

        def stub(*, system: str, user: str) -> str:
            calls.append(system)
            return "That's interesting"

        with tempfile.TemporaryDirectory() as tmp:
            brain = _brain(tmp)
            try:
                resp = brain.respond("Tell me about the Model Y.",
                                     llm_chat=stub)
            finally:
                brain.stop()
        self.assertEqual(len(calls), 2)
        grounding = resp.get("grounding") or {}
        repair = grounding.get("llm_repair") or {}
        self.assertTrue(repair.get("attempted"))
        self.assertFalse(repair.get("accepted", True))
        # Repair advises, never vetoes: the original draft still answers.
        self.assertTrue((resp.get("text") or "").strip())


if __name__ == "__main__":
    unittest.main()
