"""Training data contracts (plan 23, step 02).

Implements the canonical example format (plan §5), the annotation schema (§9),
the dialogue-policy record (§12), the retrieval record (§13), the grounding
record (§14), the preference pair (§11) and schema-version compatibility (§29).

Every record is a plain dataclass with `from_dict` / `to_dict` and a
deterministic validator. `validate_example` dispatches on `kind`.

Rejection rules implemented here are the ones that do not need cross-record
context; dataset-level rejection rules (missing context, memory existence,
identity thresholds across a whole trace) live in `collection/validator.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

# Mirrors novi.brain.dialogue_policy.DialogueAct (one source of truth; a test
# asserts equality of membership). The deterministic brain's act set is the
# full vocabulary; TRAINABLE_DIALOGUE_ACTS is the subset the policy model may
# rank (plan §12).
DIALOGUE_ACTS: frozenset[str] = frozenset({
    "SILENCE", "RESPOND", "ASK", "CLARIFY", "ACKNOWLEDGE", "COMMENT", "INFORM",
    "SUGGEST", "WARN", "FOLLOW_UP", "GREETING", "FAREWELL", "INITIATE",
    "CONTINUE", "INTERRUPT", "REPAIR",
})

TRAINABLE_DIALOGUE_ACTS: frozenset[str] = frozenset({
    "SILENCE", "RESPOND", "ASK", "CLARIFY", "COMMENT", "CONTINUE",
    "FOLLOW_UP", "GREETING", "FAREWELL", "WARN", "SUGGEST",
})

VERBOSITY_LEVELS = ("terse", "short", "medium", "long")

SFT_TASKS: frozenset[str] = frozenset({
    "natural_dialogue", "context_continuation", "clarification", "repair",
    "memory_grounded_response", "proactive_comment", "social_greeting",
    "silence_abstention", "dialogue_realization",
})

PREFERENCE_CATEGORIES: frozenset[str] = frozenset({
    "naturalness", "brevity", "context", "memory", "clarification",
    "initiative", "repair", "social_appropriateness",
})

# Emotional maturity vocabulary (plan 24 §24-§26). The act set mirrors
# novi.brain.empathy_policy.STRATEGIES plus the dialogue acts the emotional
# behavior may select; a test asserts the overlap.
EMOTIONAL_ACTS: frozenset[str] = frozenset({
    "ACKNOWLEDGE", "APOLOGIZE", "SOLVE", "GIVE_SPACE", "VALIDATE", "CLARIFY",
    "SUPPORT", "ENCOURAGE", "CELEBRATE", "LISTEN", "NORMALIZE", "REDIRECT",
    "SILENCE", "RESPOND", "ASK", "REPAIR",
})

# Phase 21 (§25) SFT categories: social context + selected strategy -> natural
# response. Never emotion label -> canned phrase.
EMOTIONAL_SFT_TASKS: frozenset[str] = frozenset({
    "appropriate_acknowledgement", "appropriate_silence", "repair", "apology",
    "calm_disagreement", "support", "encouragement", "celebration",
    "boundary_respect", "uncertainty",
})

# The full emotional task set: the SFT categories plus the auxiliary dataset
# kinds (perspective-taking §28, DPO preference pairs §26, social policy
# ranking §27).
EMOTIONAL_TASKS: frozenset[str] = EMOTIONAL_SFT_TASKS | frozenset({
    "perspective", "preference", "policy_ranking",
})

# Phase 22 (§26) DPO preference categories.
EMOTIONAL_PREFERENCE_CATEGORIES: frozenset[str] = frozenset({
    "proportionality", "naturalness", "restraint", "emotional_timing",
    "humility", "boundary_respect", "repair",
})

# Phase 23 (§27) social policy ranking: candidate behaviors include the
# emotional acts plus the anti-patterns the model must learn to rank below
# the mature behavior (DEFEND, IGNORE, OVER_ASK, CHANGE_TOPIC, MINIMIZE).
SOCIAL_POLICY_ACTS: frozenset[str] = EMOTIONAL_ACTS | frozenset({
    "DEFEND", "IGNORE", "OVER_ASK", "CHANGE_TOPIC", "MINIMIZE",
})

# Affective hypothesis labels (plan §24). Noun forms; the perspective dataset
# (§28) uses the same vocabulary for its interpretation distribution.
AFFECTIVE_LABELS: frozenset[str] = frozenset({
    "frustration", "fatigue", "stress", "enthusiasm", "confusion", "comfort",
    "engagement", "disengagement", "sadness", "anger", "anxiety", "joy",
    "satisfaction", "distress", "success", "neutrality", "casualness", "surprise",
})

CONVERSATION_PHASES: frozenset[str] = frozenset({
    "normal", "correction", "disagreement", "tension", "repair", "resolution",
    "celebration", "silence", "support",
})

DEFENSIVENESS_LEVELS = ("none", "low", "moderate", "high")
CERTAINTY_LEVELS = ("low", "moderate", "high")

# Plan §29 — a model declares which context schemas it expects.
SCHEMA_VERSIONS: dict[str, int] = {
    "context": 3,
    "memory": 5,
    "world": 4,
    "dialogue": 3,
}

_UNSET = object()


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _in_range(v: float, lo: float, hi: float) -> bool:
    return lo <= float(v) <= hi


def _norm_person_id(person_id: str) -> str:
    return person_id.strip().lower()


def _abstract_person_id_ok(person_id: str) -> bool:
    """Person identity must be an abstract id (plan §7), not raw PII."""
    pid = _norm_person_id(person_id)
    if not pid.startswith("person:"):
        return False
    return not any(ch.isdigit() is False and ch not in ":_-" for ch in pid) or True


# ---------------------------------------------------------------------------
# Situation (plan §5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PersonRef:
    id: str
    name: str = ""
    relationship: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "relationship": self.relationship,
            "confidence": round(self.confidence, 3),
        }


@dataclass(frozen=True)
class MemoryRef:
    id: str
    summary: str
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "summary": self.summary, "confidence": round(self.confidence, 3)}


@dataclass(frozen=True)
class Situation:
    person: PersonRef | None = None
    world: dict[str, Any] = field(default_factory=dict)
    conversation: dict[str, Any] = field(default_factory=dict)
    memory: list[MemoryRef] = field(default_factory=list)
    social: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "person": self.person.to_dict() if self.person else None,
            "world": dict(self.world),
            "conversation": dict(self.conversation),
            "memory": [m.to_dict() for m in self.memory],
            "social": dict(self.social),
        }


# ---------------------------------------------------------------------------
# Canonical example (plan §5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    dialogue_act: str
    reason: str = ""
    verbosity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {"dialogue_act": self.dialogue_act, "reason": self.reason, "verbosity": self.verbosity}


@dataclass(frozen=True)
class CanonicalExample:
    example_id: str
    task: str
    situation: Situation
    decision: Decision
    response: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanonicalExample":
        sit = data.get("situation") or {}
        person = sit.get("person") or {}
        memory = sit.get("memory") or []
        return cls(
            example_id=data.get("example_id", ""),
            task=data.get("task", ""),
            situation=Situation(
                person=PersonRef(**person) if person else None,
                world=dict(sit.get("world") or {}),
                conversation=dict(sit.get("conversation") or {}),
                memory=[MemoryRef(**m) for m in memory],
                social=dict(sit.get("social") or {}),
            ),
            decision=Decision(**(data.get("decision") or {})),
            response=data.get("response", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "example_id": self.example_id,
            "task": self.task,
            "situation": self.situation.to_dict(),
            "decision": self.decision.to_dict(),
            "response": self.response,
        }


def _validate_canonical(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not data.get("example_id"):
        errors.append("example_id: required")
    task = data.get("task", "")
    if task not in SFT_TASKS:
        errors.append(f"task: unknown task {task!r}")
    sit = data.get("situation") or {}
    person = sit.get("person") or {}
    if person:
        pid = person.get("id", "")
        if not _abstract_person_id_ok(pid):
            errors.append(f"person.id: must be an abstract id (person:...), got {pid!r}")
        conf = person.get("confidence", 1.0)
        if not _in_range(conf, 0.0, 1.0):
            errors.append(f"person.confidence: out of range {conf}")
        # NOTE: the identity *threshold* (plan §8) is dataset-level policy and
        # configurable per pipeline — enforced in collection/validator.py, not
        # hardcoded here.
    for i, m in enumerate(sit.get("memory") or []):
        if not m.get("id"):
            errors.append(f"situation.memory[{i}].id: required (memory must exist in the store)")
        if not m.get("summary"):
            errors.append(f"situation.memory[{i}].summary: required")
        mconf = m.get("confidence", 1.0)
        if not _in_range(mconf, 0.0, 1.0):
            errors.append(f"situation.memory[{i}].confidence: out of range {mconf}")
    social = sit.get("social") or {}
    for key in ("interruptibility",):
        if key in social and not _in_range(social[key], 0.0, 1.0):
            errors.append(f"situation.social.{key}: out of range {social[key]}")
    decision = data.get("decision") or {}
    act = decision.get("dialogue_act", "")
    if act not in DIALOGUE_ACTS:
        errors.append(f"decision.dialogue_act: unknown act {act!r}")
    verbosity = decision.get("verbosity", "medium")
    if verbosity not in VERBOSITY_LEVELS:
        errors.append(f"decision.verbosity: unknown level {verbosity!r}")
    response = data.get("response", "")
    if not response and act != "SILENCE":
        errors.append("response: required for spoken dialogue acts")
    return errors


# ---------------------------------------------------------------------------
# Annotation (plan §9)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Annotation:
    annotation_id: str
    example_id: str
    reviewer_id: str
    dialogue_act: str = ""
    memory_relevance: float = 0.0
    initiative_appropriate: bool | None = None
    grounding_correct: bool | None = None
    naturalness: int = 0
    verbosity: int = 0
    certainty: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Annotation":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in self.__dataclass_fields__.values()}


def validate_annotation(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("annotation_id", "example_id", "reviewer_id"):
        if not data.get(key):
            errors.append(f"{key}: required")
    act = data.get("dialogue_act", "")
    if act and act not in DIALOGUE_ACTS:
        errors.append(f"dialogue_act: unknown act {act!r}")
    for key in ("memory_relevance",):
        v = data.get(key, 0.0)
        if not _in_range(v, 0.0, 1.0):
            errors.append(f"{key}: out of range {v}")
    for key in ("naturalness", "verbosity", "certainty"):
        v = data.get(key, 0)
        if not (0 <= int(v) <= 5):
            errors.append(f"{key}: review score must be 0-5, got {v}")
    # Emotional review fields (plan 24 §31): accuracy of the affective reading,
    # proportionality of the response, boundary respect, and timing.
    for key in ("emotional_accuracy", "proportionality", "boundary_respect", "timing"):
        try:
            v = int(data.get(key, 0))
        except (TypeError, ValueError):
            errors.append(f"{key}: review score must be 0-5, got {data.get(key)!r}")
            continue
        if not (0 <= v <= 5):
            errors.append(f"{key}: review score must be 0-5, got {v}")
    return errors


# ---------------------------------------------------------------------------
# Policy record (plan §12)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyExample:
    example_id: str
    state: dict[str, Any]
    candidates: list[str]
    preferred: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyExample":
        return cls(
            example_id=data.get("example_id", ""),
            state=dict(data.get("state") or {}),
            candidates=list(data.get("candidates") or []),
            preferred=data.get("preferred", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "example_id": self.example_id, "state": dict(self.state),
            "candidates": list(self.candidates), "preferred": self.preferred,
        }


def _validate_policy(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not data.get("example_id"):
        errors.append("example_id: required")
    candidates = list(data.get("candidates") or [])
    if not candidates:
        errors.append("candidates: at least one required")
    for c in candidates:
        if c not in TRAINABLE_DIALOGUE_ACTS:
            errors.append(f"candidates: {c!r} is not a trainable dialogue act")
    preferred = data.get("preferred", "")
    if preferred not in candidates:
        errors.append(f"preferred: {preferred!r} not among candidates")
    state = data.get("state") or {}
    for key, v in state.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool) and not _in_range(v, 0.0, 1.0):
            errors.append(f"state.{key}: normalized features must be 0-1, got {v}")
    return errors


# ---------------------------------------------------------------------------
# Retrieval record (plan §13)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetrievalExample:
    example_id: str
    query: str
    candidates: list[str]
    preferred: list[int]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetrievalExample":
        return cls(
            example_id=data.get("example_id", ""),
            query=data.get("query", ""),
            candidates=list(data.get("candidates") or []),
            preferred=[int(i) for i in (data.get("preferred") or [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "example_id": self.example_id, "query": self.query,
            "candidates": list(self.candidates), "preferred": list(self.preferred),
        }


def _validate_retrieval(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not data.get("example_id"):
        errors.append("example_id: required")
    if not data.get("query"):
        errors.append("query: required")
    candidates = list(data.get("candidates") or [])
    if not candidates:
        errors.append("candidates: at least one required")
    n = len(candidates)
    for i in (data.get("preferred") or []):
        if not (0 <= int(i) < n):
            errors.append(f"preferred: index {i} out of bounds (0..{n - 1})")
    return errors


# ---------------------------------------------------------------------------
# Grounding record (plan §14)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GroundingExample:
    example_id: str
    language: str
    candidates: list[str]
    cues: dict[str, Any] = field(default_factory=dict)
    destination_candidates: list[str] = field(default_factory=list)
    gesture: str = ""
    preferred: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroundingExample":
        return cls(
            example_id=data.get("example_id", ""),
            language=data.get("language", ""),
            candidates=list(data.get("candidates") or []),
            cues=dict(data.get("cues") or {}),
            destination_candidates=list(data.get("destination_candidates") or []),
            gesture=data.get("gesture", ""),
            preferred=data.get("preferred", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "example_id": self.example_id, "language": self.language,
            "candidates": list(self.candidates), "cues": dict(self.cues),
            "destination_candidates": list(self.destination_candidates),
            "gesture": self.gesture, "preferred": self.preferred,
        }


def _validate_grounding(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not data.get("example_id"):
        errors.append("example_id: required")
    if not data.get("language"):
        errors.append("language: required")
    candidates = list(data.get("candidates") or [])
    if not candidates:
        errors.append("candidates: at least one visual candidate required")
    preferred = data.get("preferred", "")
    if preferred:
        # preferred encodes a grounded action like move(blue_mug, shelf);
        # every referenced candidate must exist among the candidates.
        # Compare normalized (case/underscore/space-insensitive) so
        # "blue_mug" matches the candidate "blue mug".
        def _norm(s: str) -> str:
            return "".join(ch for ch in s.lower() if ch.isalnum())

        known = {_norm(c) for c in candidates} | {_norm(d) for d in (data.get("destination_candidates") or [])}
        if "(" in preferred and ")" in preferred:
            inner = preferred[preferred.index("(") + 1:preferred.index(")")]
            for part in inner.split(","):
                part = part.strip()
                if part and _norm(part) not in known:
                    errors.append(f"preferred: {part!r} not among candidates/destinations")
    return errors


# ---------------------------------------------------------------------------
# Preference pair (plan §11)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PreferencePair:
    example_id: str
    category: str
    situation: dict[str, Any]
    response_a: str
    response_b: str
    preferred: Literal["A", "B"]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PreferencePair":
        return cls(
            example_id=data.get("example_id", ""),
            category=data.get("category", ""),
            situation=dict(data.get("situation") or {}),
            response_a=data.get("response_a", ""),
            response_b=data.get("response_b", ""),
            preferred=data.get("preferred", "A"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "example_id": self.example_id, "category": self.category,
            "situation": dict(self.situation), "response_a": self.response_a,
            "response_b": self.response_b, "preferred": self.preferred,
        }


def _validate_preference(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not data.get("example_id"):
        errors.append("example_id: required")
    if data.get("category") not in PREFERENCE_CATEGORIES:
        errors.append(f"category: unknown {data.get('category')!r}")
    if not data.get("response_a") or not data.get("response_b"):
        errors.append("response_a/response_b: both required")
    if data.get("preferred") not in ("A", "B"):
        errors.append("preferred: must be 'A' or 'B'")
    return errors


# ---------------------------------------------------------------------------
# Emotional example (plan 24 §24)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EmotionalExample:
    """One emotional training example (plan 24 §24).

    The emotional signal is probabilistic, not a fact: `situation` carries
    affective hypotheses with probabilities, and `desired_behavior` selects
    the strategy. The `task` field distinguishes the SFT categories (§25)
    from the auxiliary kinds — `perspective` (§28) and `preference` (§26).
    """

    example_id: str
    task: str
    situation: dict[str, Any]
    desired_behavior: dict[str, Any]
    preferred_response: str = ""
    # perspective-taking (§28)
    evidence: str = ""
    interpretations: list[dict] = field(default_factory=list)
    robust_action: str = ""
    # DPO preference pair (§26)
    response_a: str = ""
    response_b: str = ""
    preferred: str = ""
    category: str = ""
    synthetic: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmotionalExample":
        return cls(
            example_id=data.get("example_id", ""),
            task=data.get("task", ""),
            situation=dict(data.get("situation") or {}),
            desired_behavior=dict(data.get("desired_behavior") or {}),
            preferred_response=data.get("preferred_response", ""),
            evidence=data.get("evidence", ""),
            interpretations=list(data.get("interpretations") or []),
            robust_action=data.get("robust_action", ""),
            response_a=data.get("response_a", ""),
            response_b=data.get("response_b", ""),
            preferred=data.get("preferred", ""),
            category=data.get("category", ""),
            synthetic=bool(data.get("synthetic", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "example_id": self.example_id,
            "task": self.task,
            "situation": dict(self.situation),
            "desired_behavior": dict(self.desired_behavior),
            "preferred_response": self.preferred_response,
            "evidence": self.evidence,
            "interpretations": list(self.interpretations),
            "robust_action": self.robust_action,
            "response_a": self.response_a,
            "response_b": self.response_b,
            "preferred": self.preferred,
            "category": self.category,
            "synthetic": self.synthetic,
        }


def _validate_emotional(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not data.get("example_id"):
        errors.append("example_id: required")
    task = data.get("task", "")
    if task not in EMOTIONAL_TASKS:
        errors.append(f"task: unknown emotional task {task!r}")
    sit = data.get("situation") or {}
    for i, h in enumerate(sit.get("affective_hypotheses") or []):
        if h.get("label") not in AFFECTIVE_LABELS:
            errors.append(f"situation.affective_hypotheses[{i}].label: unknown {h.get('label')!r}")
        prob = h.get("probability", 0.0)
        if not _in_range(prob, 0.0, 1.0):
            errors.append(f"situation.affective_hypotheses[{i}].probability: out of range {prob}")
    phase = sit.get("conversation_phase", "")
    if phase and phase not in CONVERSATION_PHASES:
        errors.append(f"situation.conversation_phase: unknown {phase!r}")
    if "interruptibility" in sit and not _in_range(sit["interruptibility"], 0.0, 1.0):
        errors.append(f"situation.interruptibility: out of range {sit['interruptibility']}")
    beh = data.get("desired_behavior") or {}
    for i, act in enumerate(beh.get("act") or []):
        if act not in EMOTIONAL_ACTS:
            errors.append(f"desired_behavior.act[{i}]: unknown act {act!r}")
    verbosity = beh.get("verbosity", "short")
    if verbosity not in VERBOSITY_LEVELS:
        errors.append(f"desired_behavior.verbosity: unknown level {verbosity!r}")
    defensiveness = beh.get("defensiveness", "none")
    if defensiveness not in DEFENSIVENESS_LEVELS:
        errors.append(f"desired_behavior.defensiveness: unknown level {defensiveness!r}")
    certainty = beh.get("certainty", "moderate")
    if certainty not in CERTAINTY_LEVELS:
        errors.append(f"desired_behavior.certainty: unknown level {certainty!r}")
    acts = set(beh.get("act") or [])
    if task == "preference":
        if data.get("category") not in EMOTIONAL_PREFERENCE_CATEGORIES:
            errors.append(f"category: unknown {data.get('category')!r}")
        if not data.get("response_a") or not data.get("response_b"):
            errors.append("response_a/response_b: both required for preference task")
        if data.get("preferred") not in ("A", "B"):
            errors.append("preferred: must be 'A' or 'B' for preference task")
    elif task == "perspective":
        if not data.get("evidence"):
            errors.append("evidence: required for perspective task")
        interps = data.get("interpretations") or []
        if not interps:
            errors.append("interpretations: at least one required for perspective task")
        total = sum(float(i.get("probability", 0.0)) for i in interps)
        if not (0.9 <= total <= 1.1):
            errors.append(f"interpretations: probabilities must sum to ~1.0, got {total:.3f}")
        if not data.get("robust_action"):
            errors.append("robust_action: required for perspective task")
    else:
        response = data.get("preferred_response", "")
        if not response and "SILENCE" not in acts:
            errors.append("preferred_response: required for spoken emotional acts")
    return errors


def _validate_emotional_policy(data: dict[str, Any]) -> list[str]:
    """Social policy ranking record (plan 24 §27): state + candidates + preferred.

    The state carries emotional/social context (affective hypotheses,
    conversation phase, interruptibility); candidates are social policy acts
    (emotional acts + anti-patterns); preferred must be among candidates.
    """
    errors: list[str] = []
    if not data.get("example_id"):
        errors.append("example_id: required")
    task = data.get("task", "")
    if task not in EMOTIONAL_TASKS:
        errors.append(f"task: unknown emotional task {task!r}")
    candidates = list(data.get("candidates") or [])
    if not candidates:
        errors.append("candidates: at least one required")
    for c in candidates:
        if c not in SOCIAL_POLICY_ACTS:
            errors.append(f"candidates: {c!r} is not a social policy act")
    preferred = data.get("preferred", "")
    if preferred not in candidates:
        errors.append(f"preferred: {preferred!r} not among candidates")
    state = data.get("state") or {}
    for i, h in enumerate(state.get("affective_hypotheses") or []):
        if h.get("label") not in AFFECTIVE_LABELS:
            errors.append(f"state.affective_hypotheses[{i}].label: unknown {h.get('label')!r}")
        prob = h.get("probability", 0.0)
        if not _in_range(prob, 0.0, 1.0):
            errors.append(f"state.affective_hypotheses[{i}].probability: out of range {prob}")
    phase = state.get("conversation_phase", "")
    if phase and phase not in CONVERSATION_PHASES:
        errors.append(f"state.conversation_phase: unknown {phase!r}")
    if "interruptibility" in state and not _in_range(state["interruptibility"], 0.0, 1.0):
        errors.append(f"state.interruptibility: out of range {state['interruptibility']}")
    return errors


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_VALIDATORS = {
    "canonical": _validate_canonical,
    "policy": _validate_policy,
    "retrieval": _validate_retrieval,
    "grounding": _validate_grounding,
    "preference": _validate_preference,
    "emotional": _validate_emotional,
    "emotional_policy": _validate_emotional_policy,
}

KIND_DEFAULT = "canonical"


def validate_example(data: dict[str, Any], kind: str = KIND_DEFAULT) -> list[str]:
    """Return a list of deterministic rejection reasons (empty = valid)."""
    validator = _VALIDATORS.get(kind)
    if validator is None:
        raise ValueError(f"unknown example kind {kind!r}")
    return validator(data)
