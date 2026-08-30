"""Bounded working memory (plan 22, Phase 4).

Tasks:
- 4.1 structure — current_person / current_topic / active_references /
  current_scene / active_goal / unresolved_questions / recent_events /
  recent_utterances / current_hypotheses / active_plan / pending_commitments;
- 4.2 lifecycle — per cycle: update → score importance → expire stale →
  promote important entries to long-term memory;
- 4.3 boundedness — explicit limits on items, tokens, event age and
  unresolved references.

Acceptance (plan §8): a 30-minute interaction does not cause unbounded
prompt growth. This layer is the cognition-side buffer in front of durable
storage; it is *not* a second memory database (plan §2.4).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

DEFAULT_MAX_ITEMS = 64
DEFAULT_MAX_TOKENS = 1600
DEFAULT_MAX_EVENT_AGE_CYCLES = 200
DEFAULT_MAX_UNRESOLVED_REFERENCES = 8
PROMOTION_IMPORTANCE = 0.7


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (chars/4) for budget enforcement."""
    return max(1, len(str(text)) // 4)


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class WorkingMemory:
    """Bounded, importance-scored cognition buffer (plan §2.4 separation:
    this is *what is active now*, distinct from durable long-term memory)."""

    max_items: int = DEFAULT_MAX_ITEMS
    max_tokens: int = DEFAULT_MAX_TOKENS
    max_event_age_cycles: int = DEFAULT_MAX_EVENT_AGE_CYCLES
    max_unresolved_references: int = DEFAULT_MAX_UNRESOLVED_REFERENCES

    # ---- slots (Task 4.1) ----
    current_person: str = ""
    current_topic: str = ""
    active_references: list[str] = field(default_factory=list)
    current_scene: str = ""
    active_goal: str | None = None
    unresolved_questions: list[str] = field(default_factory=list)
    recent_events: deque[dict[str, Any]] = field(default_factory=deque)
    recent_utterances: deque[dict[str, Any]] = field(default_factory=deque)
    current_hypotheses: list[str] = field(default_factory=list)
    active_plan: str | None = None
    pending_commitments: list[dict[str, Any]] = field(default_factory=list)

    _cycle: int = 0
    _promoted: set[str] = field(default_factory=set, repr=False)

    # ---- updates (Task 4.2: load → update) ----

    def update(
        self,
        *,
        cycle: int | None = None,
        person: str | None = None,
        topic: str | None = None,
        scene: str | None = None,
        goal: str | None = None,
        question: str | None = None,
        hypothesis: str | None = None,
        plan: str | None = None,
        commitment: dict[str, Any] | None = None,
        event: dict[str, Any] | None = None,
        utterance: str | None = None,
        utterance_source: str = "",
        reference: str | None = None,
    ) -> None:
        if cycle is not None:
            self._cycle = max(self._cycle, int(cycle))
        if person:
            self.current_person = person
        if topic:
            self.current_topic = topic
        if scene:
            self.current_scene = scene
        if goal is not None:
            self.active_goal = goal
        if plan is not None:
            self.active_plan = plan
        if hypothesis:
            if hypothesis not in self.current_hypotheses:
                self.current_hypotheses.append(hypothesis)
            self.current_hypotheses = self.current_hypotheses[-4:]
        if question:
            if question not in self.unresolved_questions:
                self.unresolved_questions.append(question)
            self.unresolved_questions = self.unresolved_questions[-self.max_unresolved_references:]
        if reference:
            if reference not in self.active_references:
                self.active_references.append(reference)
            self.active_references = self.active_references[-self.max_unresolved_references:]
        if commitment:
            self.pending_commitments.append(commitment)
            self.pending_commitments = self.pending_commitments[-self.max_unresolved_references:]
        if event:
            self.recent_events.append(
                {"cycle": self._cycle, "at": utc_now_iso(), "importance": _clamp01(float(event.get("importance", 0.3))), **event}
            )
        if utterance is not None:
            self.recent_utterances.append(
                {"cycle": self._cycle, "at": utc_now_iso(), "source": utterance_source, "text": utterance}
            )
        self._enforce_bounds()

    def _enforce_bounds(self) -> None:
        """Task 4.3: hard caps on items and tokens; evict oldest first."""
        while len(self.recent_events) > self.max_items:
            self.recent_events.popleft()
        while len(self.recent_utterances) > self.max_items:
            self.recent_utterances.popleft()
        while self.token_estimate() > self.max_tokens:
            # evict the oldest utterance (chat is the biggest token consumer)
            if self.recent_utterances:
                self.recent_utterances.popleft()
            elif self.recent_events:
                self.recent_events.popleft()
            else:
                break

    # ---- lifecycle (Task 4.2: expire → promote) ----

    def expire(self, *, cycle: int | None = None) -> list[dict[str, Any]]:
        """Drop stale entries; returns the expired events/utterances."""
        cycle = cycle if cycle is not None else self._cycle
        expired: list[dict[str, Any]] = []
        while self.recent_events and cycle - self.recent_events[0]["cycle"] > self.max_event_age_cycles:
            expired.append(self.recent_events.popleft())
        while self.recent_utterances and cycle - self.recent_utterances[0]["cycle"] > self.max_event_age_cycles:
            expired.append(self.recent_utterances.popleft())
        return expired

    def promote_important(self, promoter: Callable[[dict[str, Any]], None]) -> list[dict[str, Any]]:
        """Promote important, not-yet-promoted entries to long-term memory via
        the injected ``promoter`` (Task 4.2). Returns the promoted entries.
        """
        promoted: list[dict[str, Any]] = []
        for entry in self.recent_events:
            key = entry.get("event_id") or f"{entry.get('cycle')}:{entry.get('kind', '')}:{entry.get('at')}"
            if entry.get("importance", 0.0) >= PROMOTION_IMPORTANCE and key not in self._promoted:
                promoter(entry)
                self._promoted.add(key)
                promoted.append(entry)
        return promoted

    # ---- queries ----

    def token_estimate(self) -> int:
        total = _estimate_tokens(self.current_topic) + _estimate_tokens(self.current_scene)
        total += sum(_estimate_tokens(u.get("text", "")) for u in self.recent_utterances)
        total += sum(_estimate_tokens(e.get("kind", "")) for e in self.recent_events)
        total += sum(_estimate_tokens(q) for q in self.unresolved_questions)
        total += sum(_estimate_tokens(h) for h in self.current_hypotheses)
        return total

    def snapshot(self) -> dict[str, Any]:
        return {
            "current_person": self.current_person,
            "current_topic": self.current_topic,
            "active_references": list(self.active_references),
            "current_scene": self.current_scene,
            "active_goal": self.active_goal,
            "unresolved_questions": list(self.unresolved_questions),
            "recent_events": [dict(e) for e in self.recent_events],
            "recent_utterances": [dict(u) for u in self.recent_utterances],
            "current_hypotheses": list(self.current_hypotheses),
            "active_plan": self.active_plan,
            "pending_commitments": list(self.pending_commitments),
            "cycle": self._cycle,
            "token_estimate": self.token_estimate(),
        }
