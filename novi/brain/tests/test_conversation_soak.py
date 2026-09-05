"""Plan 03 Gap 6: conversational soak runner.

Deterministic, socket-free. Runs short soaks and asserts the report
schema, memory-probe behavior, failure detection (a broken probe
answer fails the soak), and — since the 300-turn acceptance soak
silently degraded to the deterministic path and still reported PASS —
the live-LLM engagement gate (min_live_ratio).
"""

from __future__ import annotations

import unittest
from unittest import mock

from novi.brain.conversation_soak import (
    PROBE_ASK,
    build_script,
    run_soak,
)


class _FatigueClock:
    """CommunicationDecision stand-in that counts ticks (social-fatigue
    cooldown advance, normally driven by engine.step in real surfaces)."""

    def __init__(self) -> None:
        self.ticks = 0

    def tick(self) -> None:
        self.ticks += 1


class _FakeBrain:
    """Stub brain: replies as a live LLM (route=local_llm) or as the
    deterministic fallback (route=deterministic), per ``mode``."""

    def __init__(self, mode: str) -> None:
        self.mode = mode  # "live" | "fallback"
        self.communication_decision = _FatigueClock()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def respond(self, text: str, person: str = "") -> dict:
        if text == PROBE_ASK:
            return {"text": "you like ultraviolet linings", "reply_source": "fallback",
                    "trace": {"route": "deterministic"}}
        if self.mode == "live":
            # Only the true LLM path sets grounding.route="dialogue".
            return {"text": "ok", "reply_source": "dialogue",
                    "trace": {"route": "local_llm"},
                    "grounding": {"route": "dialogue",
                                  "model_route": {"tier": "FAST"}}}
        # Deterministic social fast paths keep grounding.route != "dialogue"
        # (check_in/greeting/skill) even in live mode — they never call the
        # model, so they must not count toward the live ratio.
        return {"text": "ok", "reply_source": "fallback",
                "trace": {"route": "local_llm"},
                "grounding": {"route": "check_in"}}


def _soak_with_fake(mode: str, **kw) -> dict:
    brains: list[_FakeBrain] = []

    def factory(db_path, **kwargs):
        brain = _FakeBrain(mode)
        brains.append(brain)
        return brain

    with mock.patch(
        "novi.brain.conversation_soak.default_brain_factory",
        side_effect=factory,
    ):
        report = run_soak(turns=10, probe_every=5, **kw)
    report["_brains"] = brains
    return report


class SoakTests(unittest.TestCase):
    def test_script_cycles_dimensions(self) -> None:
        script = build_script(turns=40)
        self.assertEqual(len(script), 40)
        self.assertTrue(all(isinstance(t, str) and t.strip() for t in script))
        # Round-robin reaches past the first dimension's turns.
        first_turns = script[:8]
        self.assertGreater(len(set(first_turns)), 3)

    def test_short_soak_passes(self) -> None:
        report = run_soak(turns=12, probe_every=6)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["memory_probes"], {
            "passed": 2, "of": 2, "probes": report["memory_probes"]["probes"]})
        self.assertTrue(all(report["checks"].values()))
        for key in ("schema", "timestamp", "git_sha", "duration_s",
                    "turns_run", "errors", "latency_ms", "growth",
                    "state_bounds", "live_engagement"):
            self.assertIn(key, report)

    def test_state_bounds_observed(self) -> None:
        report = run_soak(turns=24, probe_every=12)
        bounds = report["state_bounds"]
        self.assertGreaterEqual(bounds["speakers"], 1)
        self.assertTrue(bounds["within_bounds"])

    def test_live_soak_passes_engagement_gate(self) -> None:
        report = _soak_with_fake("live", brain_llm=True, min_live_ratio=0.5)
        self.assertEqual(report["live_engagement"]["ratio"], 1.0)
        self.assertTrue(report["checks"]["live_engaged"])
        self.assertEqual(report["status"], "PASS")

    def test_degraded_soak_fails_engagement_gate(self) -> None:
        # A backend that silently falls back to the deterministic path must
        # FAIL a live acceptance soak, not report a meaningless PASS.
        report = _soak_with_fake("fallback", brain_llm=True, min_live_ratio=0.5)
        self.assertEqual(report["live_engagement"]["ratio"], 0.0)
        self.assertFalse(report["checks"]["live_engaged"])
        self.assertEqual(report["status"], "FAIL")

    def test_engagement_unchecked_without_floor(self) -> None:
        report = _soak_with_fake("fallback", brain_llm=True, min_live_ratio=None)
        self.assertNotIn("live_engaged", report["checks"])
        self.assertEqual(report["status"], "PASS")

    def test_ticks_between_turns_advance_fatigue_clock(self) -> None:
        # Real surfaces step the engine between messages (draining the
        # social-fatigue cooldown); the soak must model that cadence or a
        # long run silently degrades after the 20-interaction fatigue wall.
        report = _soak_with_fake("live", brain_llm=True, min_live_ratio=0.5)
        brain = report["_brains"][0]
        self.assertGreaterEqual(brain.communication_decision.ticks, 30)


if __name__ == "__main__":
    unittest.main()
