"""Natural-language verbalizer (plan 22, Phase 15).

The final language-realization layer: input DialogueDecision + grounded
context, output NaturalLanguageResponse. Controls length, sentence
complexity, contractions, acknowledgements, hedging, questions, follow-up,
repetition and tone — the phrasing always comes from the current
communicative intent and evidence, never canned personality text (plan §19).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

VERBOSITY_WORDS = {"short": 40, "medium": 90, "long": 200}

_HEDGE_PREFIXES = ("i think", "maybe", "possibly", "it seems", "i believe")
_ACK_PREFIXES = ("yeah,", "sure,", "right,", "got it", "okay,", "makes sense")


@dataclass
class NaturalLanguageResponse:
    text: str
    verbosity: str = "short"
    tone: str = "conversational"
    controls: list[str] = field(default_factory=list)  # what was applied

    def snapshot(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "verbosity": self.verbosity,
            "tone": self.tone,
            "controls": list(self.controls),
        }


class Verbalizer:
    """Deterministic style controls over the LLM's realized text."""

    def verbalize(
        self,
        text: str,
        *,
        act: str = "RESPOND",
        confidence: float = 1.0,
        verbosity: str = "short",
        tone: str = "conversational",
        question: bool = False,
        strategy: list[str] | None = None,
        certainty: str = "moderate",
    ) -> NaturalLanguageResponse:
        text = (text or "").strip()
        controls: list[str] = []
        strategy = list(strategy or [])
        if not text:
            return NaturalLanguageResponse("", verbosity=verbosity, tone=tone, controls=["empty"])

        # 1. Length control — the decision's verbosity is the budget.
        limit = VERBOSITY_WORDS.get(verbosity, VERBOSITY_WORDS["short"])
        words = text.split()
        if len(words) > limit:
            text = " ".join(words[:limit]).rstrip(" ,;:") + "."
            controls.append(f"truncated_to_{verbosity}")

        # 2. Hedging — only when evidence is genuinely uncertain (§19) or the
        # strategy asks for low certainty (plan 24 §22).
        if (confidence < 0.6 or certainty == "low") and not text.lower().startswith(_HEDGE_PREFIXES):
            text = f"I think {text[0].lower()}{text[1:]}"
            controls.append("hedged_low_confidence")

        # 3. Question acts end with a question mark (never mangled twice).
        if question and not text.rstrip().endswith("?"):
            text = text.rstrip(".") + "?"
            controls.append("question_form")

        # 4. Strategy-based realization (plan 24 §22): the verbalizer receives
        # a strategy rather than raw emotion. Phrasing varies while preserving
        # the selected strategy.
        if "APOLOGIZE" in strategy:
            text = f"You're right. {text[0].lower()}{text[1:]}"
            controls.append("APOLOGIZE")
        elif "ACKNOWLEDGE" in strategy:
            text = f"Yeah, I see the problem. {text[0].lower()}{text[1:]}"
            controls.append("ACKNOWLEDGE")
        if "GIVE_SPACE" in strategy:
            controls.append("GIVE_SPACE")

        # 5. Tone: conversational acknowledgements stay natural, but we never
        # inject canned personality — only trim robotic double-acknowledgement.
        text = re.sub(r"\b(okay|alright),?\s+(okay|alright),?\s+", "okay, ", text, flags=re.IGNORECASE)
        return NaturalLanguageResponse(text, verbosity=verbosity, tone=tone, controls=controls)

    @staticmethod
    def prefer_natural(example_robotic: str, natural: str) -> str:
        """Documented preference rule (plan §19): replace assistant-style
        boilerplate with the natural phrasing."""
        return natural if example_robotic and natural else example_robotic
