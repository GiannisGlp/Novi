"""P2 input-aware routing tests: social fast-path, question->LLM, route cache.

Fake providers are plain classes with ``decide(**kwargs)`` matching the
ReasoningProvider protocol (see test_router.py for the established style).
"""

import unittest

from novi.brain.models.reasoning import ActionIntent
from novi.brain.models.router import ReasoningRouter


class CountingDeterministic:
    def __init__(self):
        self.calls = 0

    def decide(self, **kw):
        self.calls += 1
        return ActionIntent(action="observe", parameters={}, rationale="det")


class CountingLLM:
    def __init__(self):
        self.calls = 0

    def decide(self, **kw):
        self.calls += 1
        return ActionIntent(action="inspect", parameters={}, rationale="llm")


class BoomLLM:
    def decide(self, **kw):
        raise RuntimeError("ollama down")


def make_router(det=None, llm=None, **kwargs) -> ReasoningRouter:
    return ReasoningRouter(
        deterministic=det if det is not None else CountingDeterministic(),
        llm=llm,
        **kwargs,
    )


class SocialFastPathTests(unittest.TestCase):
    def test_social_text_routes_deterministic_despite_llm(self):
        for text in ("hello", "thanks!", "good morning"):
            with self.subTest(text=text):
                det, llm = CountingDeterministic(), CountingLLM()
                router = make_router(det=det, llm=llm)
                intent = router.decide_for_text(text, conclusion="x", confidence=0.95, situation={})
                # The LLM stub would succeed but must never be invoked.
                self.assertEqual(llm.calls, 0)
                self.assertEqual(det.calls, 1)
                self.assertEqual(router.last_route, "deterministic")
                self.assertTrue(router.last_reason.startswith("social_fast_path:"), router.last_reason)
                self.assertEqual(intent.action, "observe")

    def test_input_classes(self):
        router = make_router(llm=CountingLLM())
        cases = {
            "hello": "social",
            "how are you doing?": "social",  # check-in beats question heuristic
            "tell me a joke?": "social",  # social precedence over '?' rule
            "ok": "social",
            "what time is it?": "question",
            "who is alice": "question",
            "is the door open": "question",  # question word, no '?'
            "alice moved the door": "substantive",
            "the door is heavy": "substantive",  # 'is' not at start
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(router._classify_input(text), expected)


class QuestionRoutingTests(unittest.TestCase):
    def test_question_routes_to_llm_even_at_high_confidence(self):
        for text in ("what time is it?", "who is alice"):
            with self.subTest(text=text):
                det, llm = CountingDeterministic(), CountingLLM()
                router = make_router(det=det, llm=llm)
                intent = router.decide_for_text(text, conclusion="x", confidence=0.95, situation={})
                self.assertEqual(router.last_route, "llm")
                self.assertEqual(router.last_reason, "factual_needs_llm")
                self.assertEqual(llm.calls, 1)
                self.assertEqual(det.calls, 0)
                self.assertEqual(intent.action, "inspect")

    def test_question_without_llm_stays_deterministic(self):
        det = CountingDeterministic()
        router = make_router(det=det, llm=None)
        router.decide_for_text("what time is it?", conclusion="x", confidence=0.95, situation={})
        self.assertEqual(router.last_route, "deterministic")
        self.assertIn("no_llm", router.last_reason)
        self.assertEqual(det.calls, 1)


class SubstantiveLegacyTests(unittest.TestCase):
    def test_low_confidence_substantive_routes_llm(self):
        det, llm = CountingDeterministic(), CountingLLM()
        router = make_router(det=det, llm=llm)
        router.decide_for_text("alice moved the door", conclusion="x", confidence=0.3, situation={})
        self.assertEqual(router.last_route, "llm")
        self.assertTrue(router.last_reason.startswith("low_confidence:"), router.last_reason)
        self.assertEqual(llm.calls, 1)

    def test_high_confidence_substantive_routes_deterministic(self):
        det, llm = CountingDeterministic(), CountingLLM()
        router = make_router(det=det, llm=llm)
        router.decide_for_text("alice moved the door", conclusion="x", confidence=0.9, situation={})
        self.assertEqual(router.last_route, "deterministic")
        self.assertEqual(router.last_reason, "confident")
        self.assertEqual(llm.calls, 0)
        self.assertEqual(det.calls, 1)


class FallbackTests(unittest.TestCase):
    def test_llm_exception_on_question_falls_back_deterministic(self):
        det = CountingDeterministic()
        router = make_router(det=det, llm=BoomLLM())
        intent = router.decide_for_text("what time is it?", conclusion="x", confidence=0.95, situation={})
        self.assertEqual(router.last_route, "deterministic")
        self.assertIn("llm_error", router.last_reason)
        self.assertIn("RuntimeError", router.last_reason)
        self.assertEqual(intent.action, "observe")
        self.assertEqual(det.calls, 1)


class RouteCacheTests(unittest.TestCase):
    def test_same_inputs_reuse_cached_decision_without_second_provider_call(self):
        det, llm = CountingDeterministic(), CountingLLM()
        router = make_router(det=det, llm=llm)
        situation = {"entities": ["alice"], "place": "kitchen"}
        first = router.decide_for_text(
            "what time is it?", conclusion="time_query", confidence=0.95, situation=situation, recall=("m1",)
        )
        second = router.decide_for_text(
            "what time is it?", conclusion="time_query", confidence=0.95, situation=situation, recall=("m1",)
        )
        self.assertEqual(first.action, second.action)
        self.assertEqual(first.rationale, second.rationale)
        # Providers: LLM decided once, deterministic never involved on the
        # llm route; the second decision came from the cache.
        self.assertEqual(llm.calls, 1)
        self.assertEqual(det.calls, 0)
        self.assertTrue(router.last_reason.startswith("cached:"), router.last_reason)
        self.assertIn("factual_needs_llm", router.last_reason)

    def test_cache_does_not_cross_confidence_thresholds(self):
        det, llm = CountingDeterministic(), CountingLLM()
        router = make_router(det=det, llm=llm)
        router.decide_for_text("alice moved the door", conclusion="x", confidence=0.3, situation={"s": 1})
        router.decide_for_text("alice moved the door", conclusion="x", confidence=0.9, situation={"s": 1})
        # Same conclusion/situation but the threshold crossing differs, so the
        # low-confidence LLM route must not be replayed as a confident one.
        self.assertEqual(router.last_route, "deterministic")
        self.assertEqual(router.last_reason, "confident")
        self.assertEqual(llm.calls, 1)
        self.assertEqual(det.calls, 1)

    def test_cache_respects_size_bound(self):
        det, llm = CountingDeterministic(), CountingLLM()
        router = make_router(det=det, llm=llm, route_cache_size=2)
        for n in range(4):  # 4 distinct keys; a size-2 cache evicts before reuse
            router.decide_for_text("what is it?", conclusion=f"query_{n}", confidence=0.95, situation={})
        snap = router.snapshot()
        self.assertLessEqual(snap["route_cache_entries"], 2)
        self.assertEqual(llm.calls, 4)  # every key missed -> every call hit the provider


class ObservabilityTests(unittest.TestCase):
    def test_snapshot_includes_route_counts_by_class(self):
        det, llm = CountingDeterministic(), CountingLLM()
        router = make_router(det=det, llm=llm)
        router.decide_for_text("hello", conclusion="x", confidence=0.95, situation={})
        router.decide_for_text("what time is it?", conclusion="x", confidence=0.95, situation={})
        router.decide_for_text("alice moved the door", conclusion="x", confidence=0.3, situation={})
        snap = router.snapshot()
        self.assertEqual(
            snap["route_counts_by_class"],
            {"social": {"deterministic": 1}, "question": {"llm": 1}, "substantive": {"llm": 1}},
        )
        # Legacy observability fields still present and consistent.
        self.assertEqual(snap["route_counts"], {"deterministic": 1, "llm": 2})
        self.assertEqual(len(router._route_log), 3)

    def test_legacy_decide_untouched_by_new_state(self):
        det, llm = CountingDeterministic(), CountingLLM()
        router = make_router(det=det, llm=llm)
        router.decide(conclusion="x", confidence=0.4, situation={})  # legacy path
        snap = router.snapshot()
        self.assertEqual(router.last_route, "llm")
        self.assertEqual(snap["route_counts_by_class"], {})  # decide() does not feed class counts
        self.assertEqual(snap["route_cache_entries"], 0)  # decide() bypasses the cache


if __name__ == "__main__":
    unittest.main()
