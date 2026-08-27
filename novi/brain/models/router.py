"""Reasoning model router for the Mac Brain.

Selects between the bounded deterministic reasoning provider and the local LLM
(Ollama/qwen) based on task confidence/uncertainty. Confident situations are
handled deterministically (fast, safe, explainable); uncertain situations are
escalated to the LLM for deeper judgment.

P2 adds input-aware routing (``decide_for_text``): the user-text intent class
computed from the same detectors ``chat.py`` uses for its canned replies decides
the route before confidence is consulted —

  - social (greeting / check-in / thanks / joke / acknowledgment) → deterministic
    only (these have warm canned replies; skip the multi-second LLM round-trip);
  - question (ends in "?" or starts with a question word) → LLM whenever one is
    present, even at high deterministic confidence;
  - substantive → the legacy confidence-threshold behavior, unchanged.

A bounded route cache keyed on the (class, conclusion, situation, threshold
crossing, recall length) tuple reuses the prior decision — including the
provider's returned intent — for identical call patterns.

Boundaries:
  - The router only chooses *which* provider decides; Policy/Safety still gates
    every resulting action at execution time.
  - If the LLM is unavailable or errors, the router degrades to the deterministic
    provider instead of failing.
  - The chosen route is tracked so behavior is inspectable and testable.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, OrderedDict
from dataclasses import dataclass
from typing import Any

from .reasoning import DeterministicReasoningProvider

# Question-word opener rule for the "question" input class (word-boundary aware
# so "does" matches but "down" does not).
_QUESTION_START_RE = re.compile(r"^(what|when|where|who|how|why|is|are|can|do|does|did)\b")


@dataclass
class RouteDecision:
    route: str  # deterministic | llm
    rationale: str


class ReasoningRouter:
    def __init__(
        self,
        deterministic: Any | None = None,
        llm: Any | None = None,
        *,
        confidence_threshold: float = 0.6,
        route_cache_size: int = 128,
    ) -> None:
        self.deterministic = deterministic or DeterministicReasoningProvider()
        self.llm = llm
        self.confidence_threshold = confidence_threshold
        self.route_cache_size = max(0, int(route_cache_size))
        self.last_route: str = "deterministic"
        self.last_reason: str = "init"
        self._route_log: list[str] = []
        # Bounded LRU-ish cache: key -> (route, base_reason, intent). Stores the
        # provider's returned intent too, so a hit skips the provider call
        # entirely (ActionIntent is frozen, so sharing the object is safe).
        self._route_cache: OrderedDict[str, tuple[str, str, Any]] = OrderedDict()
        self.route_counts_by_class: dict[str, dict[str, int]] = {}

    # ------------------------------------------------------------------ legacy
    def decide(self, *, conclusion: str, confidence: float, situation: Any, recall: Any = ()) -> Any:
        if self.llm is not None and confidence < self.confidence_threshold:
            route = "llm"
            reason = f"low_confidence:{confidence:.3f}<{self.confidence_threshold}"
            try:
                intent = self.llm.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
            except Exception as exc:  # LLM unavailable -> graceful fallback
                route = "deterministic"
                reason = f"llm_error:{type(exc).__name__}"
                intent = self.deterministic.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
        else:
            route = "deterministic"
            reason = "confident" if confidence >= self.confidence_threshold else "no_llm"
            intent = self.deterministic.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
        self.last_route = route
        self.last_reason = reason
        self._route_log.append(route)
        return intent

    # ------------------------------------------------------- P2 input-aware API
    def decide_for_text(
        self,
        text: str,
        *,
        conclusion: str,
        confidence: float,
        situation: Any,
        recall: Any = (),
    ) -> Any:
        """Route a decision using the user-text intent class, then cache.

        Class precedence mirrors chat.py's own handling order: social intents
        win over the question heuristic, so a joke request phrased as a question
        still takes the canned-reply fast path.
        """
        input_class = self._classify_input(text)
        key = self._cache_key(input_class, conclusion or "", situation, confidence, recall)

        cached = self._route_cache.get(key)
        if cached is not None:
            route, base_reason, intent = cached
            reason = f"cached:{base_reason}"
        else:
            route, reason, intent = self._route_for(
                input_class, conclusion=conclusion, confidence=confidence, situation=situation, recall=recall
            )
            self._route_cache[key] = (route, reason, intent)
            while len(self._route_cache) > self.route_cache_size:
                self._route_cache.popitem(last=False)  # evict oldest entry

        self.last_route = route
        self.last_reason = reason
        self._route_log.append(route)
        per_class = self.route_counts_by_class.setdefault(input_class, {})
        per_class[route] = per_class.get(route, 0) + 1
        return intent

    def _classify_input(self, text: str) -> str:
        """Classify user text into 'social' | 'question' | 'substantive'.

        Reuses the exact intent detectors chat.py uses for its canned replies
        (they live in dialogue.py and are re-exported through chat.py); the
        import is lazy to avoid any import cycle at module load time.
        """
        from ..dialogue import (
            _is_acknowledgment,
            _is_check_in,
            _is_greeting,
            _is_joke_request,
            _is_thanks,
            _is_time_greeting,
        )

        t = (text or "").strip()
        if (
            _is_greeting(t)
            or _is_time_greeting(t)
            or _is_check_in(t)
            or _is_thanks(t)
            or _is_joke_request(t)
            or _is_acknowledgment(t)
        ):
            return "social"
        if t.endswith("?") or _QUESTION_START_RE.match(t.lower()):
            return "question"
        return "substantive"

    def _route_for(
        self,
        input_class: str,
        *,
        conclusion: str,
        confidence: float,
        situation: Any,
        recall: Any,
    ) -> tuple[str, str, Any]:
        if input_class == "social":
            # Greetings/thanks/check-ins/jokes already have warm canned replies
            # in chat.py; never pay the LLM round-trip for them.
            intent = self.deterministic.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
            return "deterministic", f"social_fast_path:{input_class}", intent

        if input_class == "question":
            # Factual questions need the LLM even at high deterministic
            # confidence; degrade gracefully when it errors.
            if self.llm is not None:
                try:
                    intent = self.llm.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
                    return "llm", "factual_needs_llm", intent
                except Exception as exc:  # LLM unavailable -> graceful fallback
                    intent = self.deterministic.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
                    return "deterministic", f"llm_error:{type(exc).__name__}", intent
            intent = self.deterministic.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
            return "deterministic", "factual_needs_llm:no_llm", intent

        # substantive: legacy confidence-threshold behavior, unchanged.
        if self.llm is not None and confidence < self.confidence_threshold:
            try:
                intent = self.llm.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
                return "llm", f"low_confidence:{confidence:.3f}<{self.confidence_threshold}", intent
            except Exception as exc:  # LLM unavailable -> graceful fallback
                intent = self.deterministic.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
                return "deterministic", f"llm_error:{type(exc).__name__}", intent
        reason = "confident" if confidence >= self.confidence_threshold else "no_llm"
        intent = self.deterministic.decide(conclusion=conclusion, confidence=confidence, situation=situation, recall=recall)
        return "deterministic", reason, intent

    # --------------------------------------------------------------- cache keys
    @staticmethod
    def _stable_repr(value: Any) -> str:
        """Order-insensitive textual form of a (JSON-ish) situation payload."""
        try:
            return json.dumps(value, sort_keys=True, default=repr)
        except (TypeError, ValueError):
            return repr(value)

    def _cache_key(
        self,
        input_class: str,
        conclusion: str,
        situation: Any,
        confidence: float,
        recall: Any,
    ) -> str:
        # The cached value includes the provider intent, so every input that can
        # change it belongs in the key: whether confidence crossed the threshold
        # (a substantive low-confidence LLM route must never be replayed as a
        # high-confidence deterministic one) and the recall length (the
        # deterministic rationale cites it).
        if recall is None:
            recall_key = "none"
        else:
            try:
                recall_key = f"n={len(recall)}"
            except TypeError:
                recall_key = repr(recall)[:200]
        parts = (
            input_class,
            conclusion[:200],
            self._stable_repr(situation),
            confidence >= self.confidence_threshold,
            recall_key,
        )
        return hashlib.sha256(repr(parts).encode("utf-8")).hexdigest()

    # ------------------------------------------------------------- observability
    @property
    def route_counts(self) -> dict[str, int]:
        return dict(Counter(self._route_log))

    def snapshot(self) -> dict[str, Any]:
        return {
            "last_route": self.last_route,
            "last_reason": self.last_reason,
            "confidence_threshold": self.confidence_threshold,
            "route_counts": self.route_counts,
            "route_counts_by_class": {
                input_class: dict(routes) for input_class, routes in self.route_counts_by_class.items()
            },
            "route_cache_entries": len(self._route_cache),
        }
