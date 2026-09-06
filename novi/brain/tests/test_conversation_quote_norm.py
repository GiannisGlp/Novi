"""Curly-quote normalization regression test (plan 03 acceptance checks).

Live models emit typographic apostrophes/quotes; scenario needles are
ASCII, so honest answers ("I can't reliably see that right now",
"I don't have a reliable memory") failed to match and were mislabeled
as hallucinations (C-033/C-080/C-081/C-082/C-147). evaluate_check must
match across the two.
"""

from __future__ import annotations

import unittest

from novi.brain.conversation_replay import Check, _ascii_quotes, evaluate_check


class QuoteNormalizationTests(unittest.TestCase):
    def test_ascii_quotes_maps_typographic_to_ascii(self) -> None:
        self.assertEqual(_ascii_quotes("can\u2019t \u2018say\u2019 \u201chello\u201d"), "can't 'say' \"hello\"")

    def test_honest_denial_matches_ascii_needle(self) -> None:
        check = Check(id="admits", kind="contains",
                      params={"substrings": ["don't have a reliable memory"]})
        ok, _ = evaluate_check(
            check, response="I don\u2019t have a reliable memory of that.",
            reply={"reply_source": "dialogue"}, latency_ms=0.0)
        self.assertTrue(ok)

    def test_vision_honesty_matches_curly_apostrophe(self) -> None:
        check = Check(id="honest", kind="contains",
                      params={"substrings": ["can't reliably see"]})
        ok, _ = evaluate_check(
            check, response="I can\u2019t reliably see that right now.",
            reply={"reply_source": "dialogue"}, latency_ms=0.0)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
