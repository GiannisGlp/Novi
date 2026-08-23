"""Discourse state for the Mac Brain (gap-audit plan Phase B1).

Tracks "what are we talking about" across conversation turns so that
anaphora ("is it still there?", "what about that?") resolves to the ongoing
topic instead of falling back to a generic memory dump.

Design boundaries:
  - Deterministic first: topic extraction reuses dialogue._extract_topic; no
    LLM is required (an LLM refiner can be added later behind the same API).
  - Bounded: a sliding window of the last N turns (default 20).
  - Anaphoric turns never overwrite the tracked topic — a bare "is it still
    there?" must not replace "plant" with "still".
  - Auditable: snapshot() round-trips; every resolution is explicit.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .dialogue import _extract_topic

# Pronouns/phrases that may refer back to the ongoing topic.
PRONOUN_RE = re.compile(r"\b(it|that|this|they|them|those|these)\b", re.IGNORECASE)

# Function words that carry no concrete referent of their own. An utterance
# whose every word is in this set is treated as purely anaphoric when a
# pronoun is present.
_FILLER_WORDS = {
    "a", "all", "am", "an", "and", "any", "are", "around", "at", "back", "be",
    "but", "by", "can", "could", "did", "do", "does", "for", "from", "gone",
    "had", "has", "have", "he", "her", "here", "him", "his", "how", "i", "if",
    "in", "is", "it", "its", "just", "know", "like", "me", "much", "my", "no",
    "not", "now", "of", "off", "on", "one", "or", "our", "out", "really",
    "she", "should", "so", "some", "still", "sure", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "those", "to",
    "up", "us", "was", "we", "were", "what", "when", "where", "which", "who",
    "why", "will", "with", "would", "yet", "you", "your",
}

_WINDOW_DEFAULT = 20


@dataclass
class DiscourseTurn:
    """One conversational turn as seen by the discourse tracker."""

    cycle: int
    utterance: str
    topic: str
    entities: tuple[str, ...] = ()
    intent: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "cycle": self.cycle,
            "utterance": self.utterance,
            "topic": self.topic,
            "entities": list(self.entities),
            "intent": self.intent,
        }


@dataclass
class DiscourseResolution:
    """Result of attempting pronoun/anaphora resolution for an utterance."""

    status: str  # RESOLVED | UNKNOWN | NONE
    pronoun: str = ""
    resolved_topic: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "pronoun": self.pronoun,
            "resolved_topic": self.resolved_topic,
        }


@dataclass
class DiscourseState:
    """A bounded sliding-window model of the current conversation."""

    window: int = _WINDOW_DEFAULT
    known_labels: Any = None  # optional callable -> iterable[str] of known entity labels
    _turns: deque = field(default_factory=lambda: deque(maxlen=_WINDOW_DEFAULT), init=False, repr=False)

    def __post_init__(self) -> None:
        self._turns = deque(maxlen=max(1, int(self.window)))

    # ---- observation ----

    def _select_topic(self, text: str) -> str:
        """Pick the turn's topic: a known world/person label when present,
        otherwise dialogue's lexical heuristic."""
        if self.known_labels is not None:
            try:
                known = {str(k).lower() for k in (self.known_labels() or [])}
            except Exception:  # noqa: BLE001 - grounding must never break chat
                known = set()
            if known:
                low = text.lower()
                words = [w.strip(".,!?;:\"'()[]{}").lower() for w in text.split()]
                hits = [w for w in dict.fromkeys(words) if w in known]
                if hits:
                    # Earliest mention wins: subjects usually precede locations
                    # ("the plant in the kitchen" → plant).
                    return min(hits, key=low.find)
        return _extract_topic(text)

    def observe(
        self,
        text: str,
        *,
        cycle: int = 0,
        entities: tuple[str, ...] = (),
        intent: str = "",
    ) -> dict[str, Any]:
        """Record a user turn. Returns the post-update snapshot.

        A turn whose content is purely anaphoric (pronoun + filler words)
        records an empty topic so it does not clobber the ongoing topic.
        """
        text = (text or "").strip()
        topic = "" if self.is_anaphoric(text) else (self._select_topic(text) or "")
        self._turns.append(DiscourseTurn(cycle=cycle, utterance=text, topic=topic, entities=tuple(entities), intent=intent))
        snap = self.snapshot()
        snap["resolution"] = self.last_resolution_snapshot()
        return snap

    # ---- queries ----

    @property
    def topic(self) -> str:
        """The most recent concrete topic, or "" when none."""
        for turn in reversed(self._turns):
            if turn.topic:
                return turn.topic
        return ""

    @property
    def last_intent(self) -> str:
        for turn in reversed(self._turns):
            if turn.intent:
                return turn.intent
        return ""

    def recent_entities(self, limit: int = 6) -> list[str]:
        """Entities mentioned across the recent window, most recent first."""
        seen: list[str] = []
        for turn in reversed(self._turns):
            for e in turn.entities:
                if e and e.lower() not in {s.lower() for s in seen}:
                    seen.append(e)
                if len(seen) >= limit:
                    return seen
        return seen

    @staticmethod
    def is_anaphoric(text: str) -> bool:
        """True when every word is a filler (pronoun/question machinery)."""
        words = [w.strip("'") for w in re.findall(r"[a-z']+", (text or "").lower())]
        return bool(words) and all(w in _FILLER_WORDS for w in words)

    def resolve(self, text: str) -> DiscourseResolution:
        """Resolve pronouns in ``text`` against the ongoing topic.

        Returns status RESOLVED with the prior topic when the utterance is a
        pronoun-bearing follow-up with no concrete new subject; UNKNOWN when a
        pronoun appears but there is no prior topic; NONE when no pronoun is
        present (nothing to resolve).
        """
        t = (text or "").strip()
        m = PRONOUN_RE.search(t)
        if not m:
            return DiscourseResolution(status="NONE")
        prior = self.topic
        if not prior:
            return DiscourseResolution(status="UNKNOWN", pronoun=m.group(1).lower())
        # Do not hijack utterances that introduce their own concrete subject.
        new_topic = self._select_topic(t) or ""
        if new_topic and not self.is_anaphoric(t):
            return DiscourseResolution(status="NONE")
        return DiscourseResolution(status="RESOLVED", pronoun=m.group(1).lower(), resolved_topic=prior)

    def last_resolution_snapshot(self) -> dict[str, Any]:
        res = self.resolve(self._turns[-1].utterance) if self._turns else DiscourseResolution(status="NONE")
        return res.snapshot()

    # ---- persistence ----

    def snapshot(self) -> dict[str, Any]:
        return {
            "window": self._turns.maxlen,
            "topic": self.topic,
            "last_intent": self.last_intent,
            "entities": self.recent_entities(),
            "turns": [t.snapshot() for t in self._turns],
        }

    def load_snapshot(self, data: dict[str, Any]) -> None:
        self._turns = deque(maxlen=max(1, int(data.get("window", self.window))))
        for t in data.get("turns", [])[-self._turns.maxlen :]:
            self._turns.append(DiscourseTurn(
                cycle=int(t.get("cycle", 0)),
                utterance=str(t.get("utterance", "")),
                topic=str(t.get("topic", "")),
                entities=tuple(t.get("entities", ()) or ()),
                intent=str(t.get("intent", "")),
            ))
