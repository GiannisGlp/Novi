"""Reasoning model router for the Mac Brain.

Selects between the bounded deterministic reasoning provider and the local LLM
(Ollama/qwen) based on task confidence/uncertainty. Confident situations are
handled deterministically (fast, safe, explainable); uncertain situations are
escalated to the LLM for deeper judgment.

Boundaries:
  - The router only chooses *which* provider decides; Policy/Safety still gates
    every resulting action at execution time.
  - If the LLM is unavailable or errors, the router degrades to the deterministic
    provider instead of failing.
  - The chosen route is tracked so behavior is inspectable and testable.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from .reasoning import ActionIntent, DeterministicReasoningProvider, ReasoningProvider


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
    ) -> None:
        self.deterministic = deterministic or DeterministicReasoningProvider()
        self.llm = llm
        self.confidence_threshold = confidence_threshold
        self.last_route: str = "deterministic"
        self.last_reason: str = "init"
        self._route_log: list[str] = []

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

    @property
    def route_counts(self) -> dict[str, int]:
        return dict(Counter(self._route_log))

    def snapshot(self) -> dict[str, Any]:
        return {
            "last_route": self.last_route,
            "last_reason": self.last_reason,
            "confidence_threshold": self.confidence_threshold,
            "route_counts": self.route_counts,
        }
