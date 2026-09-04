"""Plan 03 store-backed conversation threads + cross-session routines.

``ConversationState`` snapshots persist per speaker so a thread continues
naturally after a restart (C-112); repeated user behaviors observed across
brain runs promote to routines only with sufficient support, and a
supported routine annotates the matching reply instead of being assumed
silently (C-122).

Deterministic, socket-free, stdlib-only. Persistence rides the durable
store's conversation tables (immediate write per turn, kill -9 safe);
a "session" is one brain run (``run_id``). Everything fails closed:
corrupt rows read as absent, never raising into the reply path.
"""

from __future__ import annotations

import contextlib
import re
from datetime import datetime, timezone
from typing import Any

# A routine is "sufficiently supported" when the same behavior repeats
# across distinct sessions (minimal plural) with genuine repetition.
ROUTINE_MIN_SESSIONS = 2
ROUTINE_MIN_OCCURRENCES = 3

# Upper bounds: stored speakers, sessions remembered per routine.
MAX_STORED_THREADS = 20
MAX_ROUTINE_SESSIONS = 32
MAX_STORED_ROUTINES = 500

# Prefix voicing a supported routine ahead of a confident answer.
ROUTINE_PREFIX = "Your usual: "

# Dialogue acts that are conversational moves, not repeatable behaviors —
# ritualizing them would manufacture routines out of politeness.
_NON_ROUTINE_INTENTS = frozenset({
    "GREETING",
    "FAREWELL",
    "CONFIRMATION",
    "DISCONFIRMATION",
    "CORRECTION",
})

# Glue words that carry no behavior signal in a routine signature.
_SIGNATURE_STOP = frozenset({
    "about", "what", "which", "when", "where", "your", "with", "from",
    "that", "this", "have", "been", "they", "them", "then", "than",
    "there", "their", "would", "could", "should", "does", "like",
})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def salient_words(text: str, *, limit: int = 6) -> list[str]:
    """Stable content words for a routine signature (sorted, deduped)."""
    words = {w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
             if len(w) > 4 and w not in _SIGNATURE_STOP}
    return sorted(words)[:limit]


def routine_signature(intent: str, text: str) -> tuple[str, tuple[str, ...]] | None:
    """Normalized behavior signature, or None for non-behavioral turns.

    Greetings, farewells, bare confirmations, and corrections are moves,
    not behaviors — observing them would ritualize politeness and
    meta-talk. Empty or wordless turns carry no signal either.
    """
    name = (intent or "").strip().upper()
    if not name or name in _NON_ROUTINE_INTENTS:
        return None
    words = salient_words(text)
    if not words:
        return None
    return (name, tuple(words))


def routine_key(speaker: str, signature: tuple[str, tuple[str, ...]]) -> str:
    """Per-speaker routine key (S20: routines never cross speakers)."""
    name, words = signature
    return f"{speaker}\x00{name}\x00{'+'.join(words)}"


def _routine_label(signature: tuple[str, tuple[str, ...]]) -> str:
    return " ".join(signature[1][:4])


def observe_routine(store: Any, *, speaker: str, session_id: str,
                    intent: str, text: str) -> dict[str, Any]:
    """Record one behavior occurrence; immediate durable write.

    The current turn counts as evidence (observe-then-apply within the
    turn): a pattern completing its support threshold on this turn is
    supported for this turn. Returns the record ({} when unobservable).
    """
    try:
        speaker = (speaker or "").strip()
        session_id = (session_id or "").strip()
        signature = routine_signature(intent, text)
        if not speaker or not session_id or signature is None:
            return {}
        key = routine_key(speaker, signature)
        prior = store.load_conversation_routine(key)
        prior = prior if isinstance(prior, dict) else {}
        sessions = [s for s in (prior.get("sessions") or [])
                    if isinstance(s, str) and s]
        if session_id not in sessions:
            sessions.append(session_id)
        del sessions[:max(0, len(sessions) - MAX_ROUTINE_SESSIONS)]
        occurrences = int(prior.get("occurrences") or 0) + 1
        supported = (len(sessions) >= ROUTINE_MIN_SESSIONS
                     and occurrences >= ROUTINE_MIN_OCCURRENCES)
        record = {
            "speaker": speaker,
            "intent": signature[0],
            "words": list(signature[1]),
            "label": str(prior.get("label") or _routine_label(signature)),
            "occurrences": occurrences,
            "sessions": sessions,
            "supported": supported,
            "updated_at": _utc_now_iso(),
        }
        store.save_conversation_routine(key, record)
        return record
    except Exception:
        return {}


def matched_routine(store: Any, *, speaker: str, intent: str,
                    text: str) -> dict[str, Any]:
    """The supported routine matching this turn, else {} (never raises)."""
    try:
        signature = routine_signature(intent, text)
        if not (speaker or "").strip() or signature is None:
            return {}
        record = store.load_conversation_routine(
            routine_key(speaker.strip(), signature))
        if isinstance(record, dict) and record.get("supported"):
            return record
        return {}
    except Exception:
        return {}


def _valid_snapshot(data: Any) -> dict[str, Any]:
    """A restorable thread snapshot, else {} (fail closed, never raises)."""
    if not isinstance(data, dict):
        return {}
    if not isinstance(data.get("turn_count"), int):
        return {}
    recent = data.get("recent_turns", [])
    if not isinstance(recent, list):
        return {}
    return data


def save_thread(store: Any, speaker: str, snapshot: dict[str, Any]) -> None:
    """Persist one speaker's thread snapshot + bound stored speakers."""
    speaker = (speaker or "").strip()
    if not speaker or not isinstance(snapshot, dict):
        return
    store.save_conversation_thread(speaker, snapshot)
    with contextlib.suppress(Exception):
        store.trim_conversation_threads(MAX_STORED_THREADS)


def load_thread(store: Any, speaker: str) -> dict[str, Any]:
    """Load one speaker's snapshot, else {} (never raises)."""
    try:
        speaker = (speaker or "").strip()
        if not speaker:
            return {}
        return _valid_snapshot(store.load_conversation_thread(speaker))
    except Exception:
        return {}
