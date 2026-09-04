"""Plan 03 conversation package (Phase 1 foundation + frozen contracts).

This package makes conversation a first-class cognitive process. Layout
follows the plan's recommended ``novi/brain/conversation/`` modules;
this file holds the shared state and the cross-module result types every
track codes against — treat these dataclasses as frozen contracts:

- ``ConversationState`` / ``ConversationAnchor`` / ``TopicTransition``
  (Phase 1, Steps 1.1–1.4);
- ``IntentResult`` (Phase 2), ``ReferentResult`` (Phase 3),
  ``ContextPacket`` + ``FactClass`` (Phase 4), ``ResponsePlan``
  (Phase 7), ``CriticVerdict`` (Phase 9).

Deterministic, socket-free, stdlib-only. The brain keeps one
``ConversationState`` per addressee (bounded); long-term persistence of
conversation state arrives with the store-backed pass, the snapshot dict
is already shaped for it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

MAX_RECENT_TURNS = 12
MAX_ACTIVE_ENTITIES = 8


class TopicTransition(str, Enum):
    CONTINUE_CURRENT_TOPIC = "CONTINUE_CURRENT_TOPIC"
    SUBTOPIC_CHANGE = "SUBTOPIC_CHANGE"
    NEW_TOPIC = "NEW_TOPIC"
    RETURN_TO_PREVIOUS_TOPIC = "RETURN_TO_PREVIOUS_TOPIC"
    AMBIGUOUS = "AMBIGUOUS"


class FactClass(str, Enum):
    OBSERVED_FACT = "OBSERVED_FACT"
    USER_STATED_FACT = "USER_STATED_FACT"
    MEMORY = "MEMORY"
    INFERENCE = "INFERENCE"
    HYPOTHESIS = "HYPOTHESIS"
    PREFERENCE = "PREFERENCE"
    CURRENT_STATE = "CURRENT_STATE"
    HISTORICAL_STATE = "HISTORICAL_STATE"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class ConversationAnchor:
    """Compact active anchor, refreshed every turn (Step 1.2)."""

    topic: str = ""
    active_entity: str = ""
    active_person: str = ""
    active_place: str = ""
    active_task: str = ""
    user_goal: str = ""
    open_question: str = ""
    unresolved_reference: str = ""
    recent_decision: str = ""
    recent_correction: str = ""
    emotional_context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntentResult:
    """Phase 2 output: what the user is trying to accomplish."""

    intent: str
    dialogue_act: str
    confidence: float
    reason: str = ""
    needs_clarification: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReferentResult:
    """Phase 3 output: what each referring expression resolves to."""

    resolutions: dict[str, str] = field(default_factory=dict)
    ambiguous: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContextPacket:
    """Phase 4 output: the smallest useful context set (Step 4.5)."""

    current_turn: str = ""
    intent: IntentResult | None = None
    resolved_entities: dict[str, str] = field(default_factory=dict)
    ambiguous_referents: list[str] = field(default_factory=list)
    anchor: ConversationAnchor = field(default_factory=ConversationAnchor)
    relevant_history: list[str] = field(default_factory=list)
    relevant_memories: list[dict[str, Any]] = field(default_factory=list)
    world_context: list[dict[str, Any]] = field(default_factory=list)
    identity_context: dict[str, Any] = field(default_factory=dict)
    social_context: dict[str, Any] = field(default_factory=dict)
    emotional_context: dict[str, Any] = field(default_factory=dict)
    active_goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    response_requirements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.intent is not None:
            data["intent"] = self.intent.to_dict()
        return data


@dataclass
class ResponsePlan:
    """Phase 7 output: what the response must accomplish (Steps 7.1–7.2)."""

    goal: str = "ACKNOWLEDGE"
    must_include: list[str] = field(default_factory=list)
    may_include: list[str] = field(default_factory=list)
    must_not_include: list[str] = field(default_factory=list)
    required_evidence: list[str] = field(default_factory=list)
    uncertainty_statement: str = ""
    emotional_style: str = ""
    desired_length: str = "short"
    question_allowed: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CriticVerdict:
    """Phase 9 output: structured draft scores (Step 9.2)."""

    scores: dict[str, float] = field(default_factory=dict)
    failed: list[str] = field(default_factory=list)
    repair_instruction: str = ""
    needs_repair: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConversationState:
    """First-class conversation state (Step 1.1)."""

    topic: str = ""
    subtopics: list[str] = field(default_factory=list)
    active_entities: list[str] = field(default_factory=list)
    active_people: list[str] = field(default_factory=list)
    active_locations: list[str] = field(default_factory=list)
    active_time_context: str = ""
    user_goal: str = ""
    current_intent: str = ""
    current_dialogue_act: str = ""
    open_questions: list[str] = field(default_factory=list)
    pending_clarifications: list[str] = field(default_factory=list)
    last_user_claim: str = ""
    last_novi_claim: str = ""
    last_novi_question: str = ""
    last_unresolved_item: str = ""
    conversation_phase: str = "opening"
    recent_turns: list[dict[str, str]] = field(default_factory=list)
    conversation_summary: str = ""
    confidence: float = 0.0
    anchor: ConversationAnchor = field(default_factory=ConversationAnchor)
    turn_count: int = 0

    def record_turn(self, *, user_text: str, novi_text: str = "",
                    intent: str = "", dialogue_act: str = "",
                    entities: list[str] | None = None,
                    question_asked: str = "") -> None:
        """Fold one completed turn into the state (bounded)."""
        self.turn_count += 1
        self.recent_turns.append({"user": user_text[:300],
                                  "novi": (novi_text or "")[:300]})
        del self.recent_turns[:-MAX_RECENT_TURNS]
        if user_text.strip():
            self.last_user_claim = user_text.strip()[:300]
        if novi_text.strip():
            self.last_novi_claim = novi_text.strip()[:300]
            if "?" in novi_text:
                self.last_novi_question = novi_text.strip()[:300]
        if intent:
            self.current_intent = intent
        if dialogue_act:
            self.current_dialogue_act = dialogue_act
        for entity in entities or []:
            name = entity.strip()
            if name and name.lower() not in {e.lower() for e in self.active_entities}:
                self.active_entities.append(name)
        del self.active_entities[:-MAX_ACTIVE_ENTITIES]
        if question_asked:
            self.open_questions.append(question_asked[:200])
            del self.open_questions[:-4]
        self.conversation_phase = (
            "opening" if self.turn_count <= 2
            else "ongoing" if self.turn_count <= 20 else "long")
        self._refresh_anchor(user_text, entities or [])

    def answer_open_question(self, user_text: str) -> str:
        """Step 1.5: close an open slot when the user answers it."""
        if not self.open_questions:
            return ""
        text = user_text.strip().lower()
        if len(text.split()) <= 12 and text:
            return self.open_questions.pop()
        return ""

    def _refresh_anchor(self, user_text: str, entities: list[str]) -> None:
        anchor = self.anchor
        if entities:
            anchor.active_entity = entities[-1][:120]
        if self.topic:
            anchor.topic = self.topic[:120]
        if self.user_goal:
            anchor.user_goal = self.user_goal[:200]
        if self.open_questions:
            anchor.open_question = self.open_questions[-1]
        if self.last_unresolved_item:
            anchor.unresolved_reference = self.last_unresolved_item[:200]
        if user_text.strip():
            anchor.recent_decision = ""

    def set_topic(self, topic: str, *, transition: TopicTransition) -> None:
        """Step 1.3: topic update without resetting the conversation."""
        topic = topic.strip()[:120]
        if not self.topic:
            self.topic = topic
            self.anchor.topic = self.topic
            return
        if transition == TopicTransition.NEW_TOPIC:
            if self.topic and self.topic != topic:
                self.subtopics.append(self.topic)
                del self.subtopics[:-6]
            self.topic = topic
        elif transition == TopicTransition.SUBTOPIC_CHANGE:
            if topic and topic != self.topic:
                self.subtopics.append(topic)
                del self.subtopics[:-6]
        elif transition == TopicTransition.RETURN_TO_PREVIOUS_TOPIC:
            if topic in self.subtopics:
                self.subtopics.remove(topic)
            if self.topic:
                self.subtopics.append(self.topic)
                del self.subtopics[:-6]
            self.topic = topic
        self.anchor.topic = self.topic

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["anchor"] = self.anchor.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationState":
        anchor = data.get("anchor") or {}
        kwargs = {k: v for k, v in data.items() if k != "anchor"}
        state = cls(**{k: v for k, v in kwargs.items()
                       if k in cls.__dataclass_fields__})
        if isinstance(anchor, dict):
            state.anchor = ConversationAnchor(**{
                k: v for k, v in anchor.items()
                if k in ConversationAnchor.__dataclass_fields__})
        return state


# Mention extraction stoplist: sentence machinery, never entities.
_MENTION_STOP = frozenset({
    "i", "tell", "show", "give", "what", "which", "who", "when", "where",
    "how", "is", "are", "was", "do", "does", "did", "can", "novi", "hey",
    "hi", "hello", "please", "thanks", "yes", "no", "the", "a", "an",
    "any", "and", "but", "so", "then", "also", "however", "therefore",
    "meanwhile", "later", "today", "yesterday", "now", "just", "really",
    "very", "much", "more", "most", "such", "own", "same", "other",
    "another", "each", "every", "some", "many", "few", "several", "both",
    "either", "neither", "none", "all", "your", "their", "our", "its",
    "this", "that", "these", "those", "there", "here", "will", "would",
    "could", "should",
})

# Leading articles stripped from mentions ("The Tesla" -> "Tesla").
_ARTICLE_RE = "^(?:the|a|an)\\s+"

# Leading discourse markers stripped before entity check ("Actually the
# Model 3" -> "Model 3"; a bare marker never becomes an entity).
_MARKER_RE = ("^(?:actually|well|so|now|okay|ok|hmm|ah|oh|right|look|listen|"
              "honestly|basically|frankly|no|yes)\\s+")

# Negators that detach an entity mention ("not the Model Y").
_NEGATORS = frozenset({"not", "n't", "never", "no", "forget", "ignore",
                       "instead", "rather"})


def mention_candidates(text: str) -> list[str]:
    """Deterministic proper-noun mention extraction.

    Captures multi-word capitalized phrases ("Model Y") and mid-sentence
    single capitalized words ("Tesla", "BMW"). Sentence-initial single
    words ("Tell", "What") are skipped. Bounded, oldest-first,
    de-duplicated.
    """
    import re

    found: list[str] = []
    for match in re.finditer(r"\b([A-Z][\w\-]*(?:\s+[A-Z0-9][\w\-]*)*)", text or ""):
        phrase = match.group(1).strip()
        phrase = re.sub(_MARKER_RE, "", phrase, flags=re.IGNORECASE)
        phrase = re.sub(_ARTICLE_RE, "", phrase, flags=re.IGNORECASE)
        words = phrase.split()
        if not words:
            continue
        if len(words) > 1:
            candidate = phrase
        else:
            if match.start() == 0 or words[0].lower() in _MENTION_STOP:
                continue
            candidate = words[0]
        if candidate.lower() not in {f.lower() for f in found}:
            found.append(candidate)
        if len(found) >= 6:
            break
    return found


def preferred_correction_entity(mentions: list[str], text: str) -> str:
    """Pick the entity a correction points TO ("Model 3, not Model Y").

    Drops mentions negated in the turn, takes the last survivor; falls
    back to the last mention. Empty string when there are no mentions.
    """
    if not mentions:
        return ""
    lowered = f" {(text or '').lower()} "
    survivors = []
    for mention in mentions:
        idx = lowered.find(mention.lower())
        window = lowered[max(0, idx - 24):idx] if idx >= 0 else ""
        if any(neg in window.split() for neg in _NEGATORS):
            continue
        survivors.append(mention)
    return (survivors or mentions)[-1]


# Step 1.3 cue sets for the deterministic topic classifier.
_CONTINUE_CUES = ("what about", "and the", "and what", "how about",
                  "what if", "would that", "is that", "does that",
                  "it ", "its ", "they ", "them ", "those ")
_RETURN_CUES = ("back to", "returning to", "as i was saying",
                "earlier you", "you mentioned earlier", "we were talking")
_SWITCH_CUES = ("switch to", "switching to", "let's talk about",
                "lets talk about", "talk about ", "change the subject",
                "move on to", "moving on to", "new subject")


def classify_topic_transition(text: str, state: ConversationState) -> TopicTransition:
    """Deterministic topic-continuity signal (Step 1.3/1.4).

    Implicit continuations (pronouns, "what about X", "and Y") continue
    the current topic; explicit returns restore it; everything else is a
    new topic unless there is no topic yet (openingCONTINUE).
    """
    lowered = f" {(text or '').strip().lower()} "
    if any(cue in lowered for cue in _RETURN_CUES):
        return TopicTransition.RETURN_TO_PREVIOUS_TOPIC
    if any(cue in lowered for cue in _SWITCH_CUES):
        return TopicTransition.NEW_TOPIC
    if any(cue in lowered for cue in _CONTINUE_CUES):
        return TopicTransition.CONTINUE_CURRENT_TOPIC
    if not state.topic:
        return TopicTransition.CONTINUE_CURRENT_TOPIC
    if len(lowered.split()) <= 4:
        return TopicTransition.AMBIGUOUS
    return TopicTransition.NEW_TOPIC
