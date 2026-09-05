"""Plan 03 Phase 3 — deterministic referent/entity resolution.

``resolve_referents(text, state)`` maps every referring expression in the
current turn to the entity it denotes, reading only
``state.active_entities`` + ``state.recent_turns`` + ``state.anchor``:

- Step 3.1 — pronouns (``it``/``that``/``this``/``they``/``he``/``she``/
  ``there``/``one``/``another``/``the other one``/``both`` ...). The base
  pronoun pattern is reused from :mod:`novi.brain.discourse` (``PRONOUN_RE``),
  extended here with the Phase 3 remainder.
- Step 3.2 — noun phrases (``the car``, ``the larger model``,
  ``the one we discussed``) matched against active entities by token overlap,
  falling back to anaphoric/generic handling.
- Step 3.3 — implicit subjects: a subject-less follow-up
  (``What's the range?``) inherits ``anchor.active_entity``.
- Step 3.4 — ambiguity: two equally-plausible entities land in
  ``ambiguous`` and are never guessed.

Cue order for singular reference (first hit wins, deterministic):

1. same-turn explicit mention of exactly one active entity (0.9);
2. exactly one active entity mentioned in the most recent turn (0.7);
3. ``anchor.active_entity`` names an active entity (0.65);
4. a single active entity with no competing cue (0.8);
5. otherwise the expression is ambiguous (never guessed).

Plural pronouns (``they``/``them``/``those``/...) skip cues 2–3: binding a
plural to one of several candidates would be a guess, so they resolve only
on an explicit same-turn mention, a sole candidate, or ``both``.

Deterministic, socket-free, stdlib-only.
"""

from __future__ import annotations

import re
from typing import Any

from novi.brain.conversation.conversation_state import ReferentResult
from novi.brain.discourse import PRONOUN_RE

__all__ = [
    "class_noun_mismatches",
    "entity_kind",
    "resolve_referents",
    "turn_mismatches_anchor_kind",
]

# Phase 3 pronouns beyond discourse.PRONOUN_RE (it/that/this/they/them/
# those/these). "then" is temporal, not an entity referent: ignored.
_EXTRA_PRONOUN_RE = re.compile(
    r"\b(its|it's|he|she|him|her|his|hers|one|another(?:\s+one)?|both|there|here)\b",
    re.IGNORECASE,
)
_THE_OTHER_ONE_RE = re.compile(r"\bthe other one\b", re.IGNORECASE)
_THE_ONE_RE = re.compile(
    r"\bthe one(?:\s+we\s+discussed|\s+you\s+mentioned|\s+i\s+mentioned"
    r"|\s+we\s+talked\s+about|\s+we\s+looked\s+at)?\b",
    re.IGNORECASE,
)
_NP_RE = re.compile(
    r"\b(my|the|that|this|those|these)\s+([a-z][a-z'\-]*(?:\s+[a-z][a-z'\-]*){0,2})\b",
    re.IGNORECASE,
)
_ENTITY_BOUNDARY = re.compile(r"\s+")

_PLURAL = frozenset({"they", "them", "their", "theirs", "those", "these"})
_LOCATIVE = frozenset({"there", "here"})

# Generic head nouns that can stand in for an active entity
# ("the car" -> Model Y). Attribute nouns ("range", "price") are absent by
# design so "What's the range?" stays an implicit subject, not a referent.
_CLASS_NOUNS = frozenset({
    "one", "car", "vehicle", "model", "restaurant", "place", "thing",
    "person", "man", "woman", "wife", "husband", "guy", "driver",
})

# Class-noun semantic kinds. A class noun only binds an entity of a compatible
# kind: "the car" must not resolve to a city, "the place" must not resolve to a
# person (C-032: "the car" after "my sister lives in Porto" is a vehicle, not
# Porto). "one"/"thing" are unrestricted generic stand-ins.
_VEHICLE_NOUNS = frozenset({"car", "vehicle", "model"})
_PLACE_NOUNS = frozenset({"restaurant", "place"})
_PERSON_NOUNS = frozenset({"person", "man", "woman", "wife", "husband",
                           "guy", "driver"})

def entity_kind(entity: str, state: Any) -> str:
    """Infer a coarse kind for an entity from how it was introduced recently.

    Returns "place" when the entity is named as a location in a recent user
    turn ("My sister lives in Porto."), else "" (unknown). Deterministic and
    read-only; never mutates state.
    """
    name = (entity or "").strip()
    if not name:
        return ""
    pattern = re.compile(
        r"\b(?:lives?|live|lived|moves?|moved|visits?|visited|travels?|"
        r"travel(?:l)?ed|flies|flew|goes|went|stays?|stayed|arrives?|arrived|"
        r"comes?|came)\s+(?:in|to|at|from)\s+" + re.escape(name) + r"\b",
        re.IGNORECASE)
    for turn in (getattr(state, "recent_turns", []) or []):
        text = str(turn.get("user", "") if isinstance(turn, dict) else turn)
        if pattern.search(text):
            return "place"
    return ""


def _class_noun_kind(head: str) -> str:
    head = (head or "").lower()
    if head in _VEHICLE_NOUNS:
        return "vehicle"
    if head in _PLACE_NOUNS:
        return "place"
    if head in _PERSON_NOUNS:
        return "person"
    return "any"


def class_noun_mismatches(head: str, entity: str, state: Any) -> bool:
    """True when a class noun cannot denote the candidate entity's kind."""
    kind = _class_noun_kind(head)
    ekind = entity_kind(entity, state)
    if kind == "vehicle" and ekind == "place":
        return True
    if kind == "place" and ekind == "person":
        return True
    if kind == "person" and ekind == "place":
        return True
    return False


def turn_mismatches_anchor_kind(text: str, state: Any) -> bool:
    """True when the turn's class-noun reference denotes a kind the current
    anchor cannot be — e.g. "the car" while the anchor is a place (Porto).

    Used by the turn pipeline to clear a stale anchor when the user moved to a
    different kind of subject, without touching anchors that a short reply
    ("yes") or a bare question legitimately continues.
    """
    anchor = (getattr(getattr(state, "anchor", None), "active_entity", "")
              or "").strip()
    if not anchor:
        return False
    for match in _NP_RE.finditer(text or ""):
        words = match.group(2).split()
        for width in range(len(words), 0, -1):
            head = words[width - 1].lower()
            if head in _CLASS_NOUNS:
                return class_noun_mismatches(head, anchor, state)
    return False

_STOPWORDS = frozenset(
    "a an the and or but of at by for with about into through during before after "
    "to from in on is are was were be been being it its this that these those "
    "i you he she we they me him her us them my your his our their what which "
    "who whom how when where why do does did can could should would there here "
    "so as no yes not just very really we discussed discussed".split()
)

_CONF_EXPLICIT = 0.9
_CONF_SOLE = 0.8
_CONF_TOKEN_MATCH = 0.7
_CONF_RECENT_MENTION = 0.7
_CONF_BOTH = 0.7
_CONF_ANCHOR = 0.65
_CONF_CONTRAST = 0.6
_CONF_PLACE = 0.6
_CONF_IMPLICIT = 0.55
_CONF_AMBIGUOUS_ONLY = 0.35


def _content_tokens(text: str) -> set[str]:
    return {t for t in _ENTITY_BOUNDARY.split(
        "".join(c.lower() if c.isalnum() else " " for c in text)) if t and t not in _STOPWORDS}


def _entity_tokens(entity: str) -> set[str]:
    return _content_tokens(entity)


def _mentioned(haystack: str, candidates: list[str]) -> list[str]:
    """Active entities named in ``haystack`` (longest names first)."""
    found: list[str] = []
    lowered = haystack.lower()
    for entity in sorted(candidates, key=len, reverse=True):
        name = entity.strip()
        if not name:
            continue
        if re.search(r"\b" + re.escape(name.lower()) + r"\b", lowered):
            if name.lower() not in {f.lower() for f in found}:
                found.append(name)
    # Return in candidate order for determinism.
    order = {e.lower(): i for i, e in enumerate(candidates)}
    return sorted(found, key=lambda e: order.get(e.lower(), 0))


def _anchor_entity(state: Any) -> str:
    anchor = getattr(state, "anchor", None)
    return (getattr(anchor, "active_entity", "") or "").strip()


def _candidates(state: Any) -> list[str]:
    entities = getattr(state, "active_entities", []) or []
    return [e.strip() for e in entities if e and e.strip()]


def _recent_turn_texts(state: Any) -> list[str]:
    # User turns only: Novi's own echoes ("About Tesla: ...", "Do you mean
    # BMW or Tesla?") must not contaminate the recency cue — the user's
    # mentions drive discourse focus. Without this, an explicit switch
    # ("forget that, what about BMW?") followed by "its" stays ambiguous
    # because Novi's echo re-mentions the abandoned entity.
    turns = getattr(state, "recent_turns", []) or []
    texts: list[str] = []
    for turn in turns:
        if isinstance(turn, dict):
            texts.append(str(turn.get("user", "")))
        else:
            texts.append(str(turn))
    return texts


def _normalize_pronoun_key(raw: str) -> str:
    key = raw.lower()
    if key == "it's":
        return "it"
    return key


def _cue_target(*, explicit: list[str], recent_hit: str | None,
                anchor: str, candidates: list[str],
                allow_cues: bool = True) -> tuple[str | None, float, bool]:
    """Apply the cue order. Returns (target, confidence, contested).

    ``contested`` is True when several entities are equally plausible and
    the caller must record ambiguity instead of guessing.
    """
    if len(explicit) == 1:
        return explicit[0], _CONF_EXPLICIT, False
    if len(explicit) > 1:
        return None, 0.0, True
    if allow_cues and recent_hit is not None:
        return recent_hit, _CONF_RECENT_MENTION, False
    lowered = {c.lower(): c for c in candidates}
    if allow_cues and anchor and anchor.lower() in lowered:
        # A lone anchor resolves; with several live candidates and no
        # disambiguating cue the anchor is a guess — flag ambiguity
        # instead (plan Step 3.4: never guess between equals).
        if len(candidates) == 1:
            return lowered[anchor.lower()], _CONF_ANCHOR, False
        return None, 0.0, True
    if len(candidates) == 1:
        return candidates[0], _CONF_SOLE, False
    if candidates:
        return None, 0.0, True
    return None, 0.0, False


def resolve_referents(text: str, state: Any) -> ReferentResult:
    """Resolve referring expressions in ``text`` against conversation state."""
    resolutions: dict[str, str] = {}
    confidences: dict[str, float] = {}
    ambiguous: list[str] = []

    cleaned = (text or "").strip()
    if not cleaned:
        return ReferentResult(resolutions={}, ambiguous=[], confidence=0.0)

    candidates = _candidates(state)
    anchor = _anchor_entity(state)
    explicit = _mentioned(cleaned, candidates)
    recent_texts = _recent_turn_texts(state)
    recent_hit: str | None = None
    if recent_texts:
        last_mentioned = _mentioned(recent_texts[-1], candidates)
        if len(last_mentioned) == 1:
            recent_hit = last_mentioned[0]

    def _record(key: str, target: str | None, confidence: float,
                contested: bool) -> None:
        if target is not None:
            if key not in resolutions:
                resolutions[key] = target
                confidences[key] = confidence
        elif contested:
            if key not in ambiguous:
                ambiguous.append(key)

    # A class noun that could not bind any entity of a compatible kind
    # ("the car" vs a place like Porto) must not fall through to the implicit
    # subject, which would otherwise bind the stale anchor.
    mismatched_class_noun = False

    # Longest multi-word phrases first so generic patterns cannot claim a
    # sub-span ("the other one" beats the "the ..." noun-phrase matcher).
    claimed: list[tuple[int, int]] = []

    def _overlaps(start: int, end: int) -> bool:
        return any(start < claimed_end and end > claimed_start
                   for claimed_start, claimed_end in claimed)

    for match in _THE_OTHER_ONE_RE.finditer(cleaned):
        if _overlaps(*match.span()):
            continue
        claimed.append(match.span())
        key = match.group(0).lower()
        target: str | None = None
        confidence = _CONF_CONTRAST
        if candidates:
            fresher = [c for c in reversed(candidates)
                       if c.lower() != anchor.lower()] if anchor else []
            target = (fresher[0] if fresher else candidates[-1])
        if target is None:
            continue
        _record(key, target, confidence, False)

    for match in _THE_ONE_RE.finditer(cleaned):
        if _overlaps(*match.span()):
            continue
        claimed.append(match.span())
        key = match.group(0).lower()
        target, confidence, contested = _cue_target(
            explicit=explicit, recent_hit=recent_hit, anchor=anchor,
            candidates=candidates)
        _record(key, target, confidence, contested)

    for match in _NP_RE.finditer(cleaned):
        start, _ = match.span()
        if _overlaps(start, start + 1):
            continue
        determiner = match.group(1).lower()
        words = match.group(2).split()
        # Longest prefix first: "the car cost" backs off to "the car"
        # (attribute/trailing words are not part of the referent).
        for width in range(len(words), 0, -1):
            phrase = f"{determiner} {' '.join(words[:width]).lower()}"
            end = start + len(phrase)
            if _overlaps(start, end):
                continue
            head = words[width - 1].lower()
            phrase_tokens = _content_tokens(phrase)
            # A full-name mention ("the Model Y") names its entity even
            # when a head token is shared ("model" also matches Model 3):
            # exact beats overlap, per cue-order rule 1.
            bare = " ".join(words[:width]).lower()
            exact = next((c for c in candidates if c.lower() == bare), None)
            if exact is not None:
                claimed.append((start, end))
                _record(phrase, exact, _CONF_EXPLICIT, False)
                break
            overlapping = [c for c in candidates
                           if phrase_tokens & _entity_tokens(c)]
            if len(overlapping) == 1:
                claimed.append((start, end))
                _record(phrase, overlapping[0], _CONF_TOKEN_MATCH, False)
                break
            if len(overlapping) > 1:
                claimed.append((start, end))
                _record(phrase, None, 0.0, True)
                break
            if head in _CLASS_NOUNS:
                target, confidence, contested = _cue_target(
                    explicit=explicit, recent_hit=recent_hit, anchor=anchor,
                    candidates=candidates)
                if target is not None and class_noun_mismatches(head, target, state):
                    # The only live entity is a kind this class noun cannot
                    # denote (e.g. "the car" when the active entity is a
                    # city): leave the reference generic rather than bind a
                    # place as a vehicle (C-032).
                    mismatched_class_noun = True
                    target = None
                if target is not None or contested:
                    claimed.append((start, end))
                    _record(phrase, target, confidence, contested)
                    break
        # Else: attribute noun ("the range") — not a referent; unclaimed so
        # a pronoun inside ("that is fine") still resolves below.

    pronoun_matches = sorted(
        list(PRONOUN_RE.finditer(cleaned)) + list(_EXTRA_PRONOUN_RE.finditer(cleaned)),
        key=lambda m: m.span())
    for match in pronoun_matches:
        if _overlaps(*match.span()):
            continue
        raw = match.group(0)
        key = _normalize_pronoun_key(raw)
        claimed.append(match.span())
        word = key
        if word in _LOCATIVE:
            place = (getattr(getattr(state, "anchor", None), "active_place", "") or "").strip()
            if place:
                _record(key, place, _CONF_PLACE, False)
            continue
        if word == "both":
            if len(candidates) >= 2:
                _record(key, f"{candidates[-2]} + {candidates[-1]}", _CONF_BOTH, False)
            elif len(candidates) == 1:
                _record(key, candidates[0], _CONF_BOTH, False)
            continue
        if word in ("another", "another one"):
            if candidates:
                fresher = [c for c in reversed(candidates)
                           if c.lower() != anchor.lower()] if anchor else []
                _record(key, fresher[0] if fresher else candidates[-1], _CONF_CONTRAST, False)
            continue
        plural = word in _PLURAL
        target, confidence, contested = _cue_target(
            explicit=explicit, recent_hit=recent_hit, anchor=anchor,
            candidates=candidates, allow_cues=not plural)
        if plural and contested and len(explicit) == 0 and len(candidates) == 1:
            target, confidence, contested = candidates[0], _CONF_SOLE, False
        _record(key, target, confidence, contested)

    if not resolutions and not ambiguous and not explicit and not mismatched_class_noun:
        subject = _implicit_subject(cleaned, anchor)
        if subject is not None:
            resolutions["(implicit subject)"] = subject
            confidences["(implicit subject)"] = _CONF_IMPLICIT

    if resolutions:
        confidence = round(max(confidences.values()), 4)
    elif ambiguous:
        confidence = _CONF_AMBIGUOUS_ONLY
    else:
        confidence = 0.0
    return ReferentResult(resolutions=resolutions, ambiguous=ambiguous,
                          confidence=confidence)


def _implicit_subject(cleaned: str, anchor: str) -> str | None:
    """Step 3.3: a subject-less follow-up inherits the anchor entity."""
    if not anchor:
        return None
    words = cleaned.split()
    if len(words) > 12:
        return None
    lowered = cleaned.lower()
    if lowered.endswith("?") or lowered.startswith(
            ("and ", "also ", "what about", "how about")):
        return anchor
    return None
