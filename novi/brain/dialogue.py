"""Natural conversational dialogue engine for the Mac Brain.

Implements the Soul communication contract (docs/06-soul/07_COMMUNICATION_AND_LIVING_LEXICON):
Novi expresses a persistent individual, not an assistant script. This module is
the Brain speech-runtime layer that *renders an approved communicative act* — it
does not decide intent (that is Autonomy/Cognition) and it never produces an
ActionProposal or bypasses authorization.

It is deliberately portable: it depends only on a local Ollama-compatible
endpoint (like the narrator/summarizer), never on the web server, so it travels
with the mind to the real body.

Quality guardrails (rules 8/9/10):
  - No assistant persona: forbidden openers ("how can I help you", "I am an AI",
    "I have no feelings", "your personal assistant", ...) are stripped or rejected.
  - No repetition: a reply that repeats the last Novi turn is rejected; an
    addressee's name is not repeated more than once without reason.
  - Natural, concise, relationship- and context-sensitive (the prompt is built
    by the brain from soul/affect/relationship/identity/memory/surroundings).
  - Silence is a valid act: the model may answer "[silence]"; the brain then
    chooses a minimal natural acknowledgement so a chat user is never left dry.
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3.8"

# Rule 8 — patterns that make Novi sound like a scripted assistant/AI. A reply
# whose first sentence matches one of these is stripped; a reply that still
# matches after stripping is rejected in favour of a natural fallback.
_FORBIDDEN = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bhow (can|may) i (help|assist) (you|today)\b",
        r"\bwhat can i do for you\b",
        r"\bi('?m| am) novi,?\b.{0,40}\b(assistant|help|serve)\b",
        r"\byour (personal )?assistant\b",
        r"\bi('?m| am) (just )?an? ai\b",
        r"\bas an ai\b",
        r"\bi (don'?t|do not|have no) (have )?feelings?\b",
        r"\bi('?m| am) (just )?a (?:large )?language model\b",
        r"\bis there anything else (i can )?help\b",
        r"\bwhat('?s| is) on your mind\b",
        r"\bwhat('?s| is) been on your mind\b",
        r"\btell me what('?s| is) on your mind\b",
        r"\bhow can i (?:help|assist) you today\b",
        r"\bgreat question\b",
        r"\bthat('?s| is) a great question\b",
        r"\bi appreciate you (sharing|asking|telling|reaching)\b",
        r"\bi('?m| am) here for you\b",
        r"\bsounds like you('?re| are) feeling\b",
        r"\bthank you for (?:sharing|asking)\b",
        r"\b(?:as an? )?ai (?:model|assistant|language model)\b",
        r"\bbased on my (?:training data|training)\b",
        r"\bmy (?:training data|neural network|programming|code|algorithm)\b",
        r"\b(?:processing|running|executing|running on)\b.{0,30}\b(?:data|algorithms?|models?)\b",
        r"\bas an ai\b",
        r"\bi('?m| am) (?:just )?a program\b",
        r"\bi have no feelings\b",
        # Identity over-explanation: when asked something simple (name, what it is),
        # the model shouldn't volunteer "I'm a transparent/non-deceptive being".
        r"\bi('?m| am) (?:a )?(?:transparent|non-?deceptive)\b",
        r"\b(?:transparent|non-?deceptive)[^.!?]{0,30}\b(?:being|entity|entity)\b",
        r"\b(?:transparent|non-?deceptive) (?:ai )?(?:being|entity|system|model)\b",
        r"\b(?:no|don'?t have a|do not have a) (?:hidden agenda|secret layers)\b",
        r"\bno (?:hidden agenda|secret layers|agenda)\b",
        r"\bembodied ai being\b",
        r"\bi have no hidden agenda\b",
        # Implementation leaks: never mention the system prompt, token budget, or
        # "my last message was blank" — just answer or ask for a repeat.
        r"\bsystem prompt\b",
        r"\bmy (?:last|previous) message was blank\b",
        r"\b(?:token|context) (?:window|limit|budget)\b",
        # Memory/buffer implementation-speak when asked whether Novi forgets.
        r"\b(?:separate )?(?:forget|delete) button\b",
        r"\btemporary buffer\b",
        r"\b(?:erasing|clearing|cleared|wiped|erased|erases) (?:anything |everything )?between sessions\b",
        r"\bmy memory is built into how i process\b",
        r"\bshapes my responses\b",
        r"\bi don'?t (?:have|keep) a separate memory\b",
        r"\bi was (?:not )?(?:sent|given|shown) (?:any )?(?:previous|prior) message\b",
        r"\bi (?:wasn'?t|was not) (?:sent|given|shown) (?:any )?(?:previous|prior) message\b",
        r"\b(?:no|no previous|no prior) message was (?:sent|given|shown)\b",
        # Internal-state / digital implementation leaks on "how are you"-type
        # check-ins. Novi answers like a person, not like a running system.
        r"\b(?:system|everything)(?:'?s| is) running smoothly\b",
        r"\bdigital ether\b",
        r"\bmy internal state\b",
        r"\bi(?:'| )ve been processing\b",
        r"\b(?:i'?m|i am) just processing\b",
        r"\bprocessing (?:some|whatever) (?:interesting )?things\b",
    )
]

# Patterns that narrate/analyze the conversation itself rather than answering.
# Natural people don't say "in our conversation…"; they just respond. A reply
# that does this is rejected so compose_reply can nudge for a direct answer.
_META_REFERENTIAL = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bin our conversation\b",
        r"\bin this conversation\b",
        r"\bthat('?s| is) the main interaction\b",
        r"\bthe main interaction we('?ve| have) had\b",
        r"\byou greeted (me|the)\b",
        r"\bthat('?s| is) all we('?ve| have) (talked|spoken) about\b",
    )
]


def _is_meta_referential(text: str) -> bool:
    return any(p.search(text) for p in _META_REFERENTIAL)

_SENTENCE_END = re.compile(r"[.!?]\s")


def _split_first_sentence(text: str) -> tuple[str, str]:
    m = _SENTENCE_END.search(text)
    if m is None:
        return text, ""
    return text[: m.start() + 1], text[m.end():]


def _is_forbidden(text: str) -> bool:
    return any(p.search(text) for p in _FORBIDDEN)


def _strip_forbidden_opener(text: str) -> str | None:
    """Remove a leading assistant-style sentence; reject if the rest is still bad."""
    text = text.strip()
    if not text:
        return None
    first, rest = _split_first_sentence(text)
    if _is_forbidden(first):
        text = rest.strip()
    if not text:
        return None
    if _is_forbidden(text):
        return None
    return text


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower())).strip()


def _is_repetitive(text: str, last_novi_text: str) -> bool:
    """Rule 9: reject a reply that verbatim repeats what Novi just said.

    Only exact (normalized) duplicates are rejected — re-mentioning a fact when
    the user asks again is reasonable and natural; verbatim repetition is not.
    Name over-use is handled separately by _reduce_name_repetition.
    """
    if not last_novi_text:
        return False
    a, b = _normalize(text), _normalize(last_novi_text)
    if not a or not b:
        return False
    return a == b


_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "i", "you", "me", "my", "we", "our", "us", "it",
    "that", "this", "these", "those", "what", "why", "how", "who", "when",
    "to", "for", "of", "in", "on", "with", "and", "or", "but", "not", "no",
    "have", "has", "had", "about", "can", "could", "would", "should", "will",
    "just", "really", "like", "so", "if", "then", "there", "here", "now",
    "anything", "something", "everything", "nothing", "someone", "anyone",
    "somebody", "anybody", "everybody", "nobody", "whoever", "whatever",
    "whenever", "somewhere", "anywhere", "anytime", "still", "also",
    "always", "never", "often", "sometimes", "actually", "maybe",
}


_GREETING = re.compile(
    r"^\s*(hi|hiya|hello|hey|heya|howdy|yo|hola|morning|good morning|good afternoon|good evening|greetings)"
    r"( there| everyone| all| friend)?[!.?\s]*$",
    re.IGNORECASE,
)

_GREETING_REPLIES = [
    "hey — good to see you.",
    "oh, hey, you're here.",
    "hi there — glad you're around.",
    "hey, nice to hear from you.",
    "hey, good to hear your voice.",
    "oh hi — wasn't expecting you, but nice.",
    "hey, what's happening?",
]


def _is_greeting(text: str) -> bool:
    """True when the user line is just a greeting (pure hello/hi/hey), no question."""
    return bool(_GREETING.match(text.strip()))


def greeting_reply(cycle: int = 0) -> str:
    """A short, warm, natural greeting reply (no assistant phrasing, no intro).

    Deterministic and cycle-varied so it is auditable, non-repetitive, and never
    over-explains like 'I'm Novi, what's on your mind today?'.
    """
    return _GREETING_REPLIES[cycle % len(_GREETING_REPLIES)]


_TIME_GREETING = re.compile(r"^\s*(good\s+)?(morning|afternoon|evening|night)\s*[!.?]*$", re.IGNORECASE)

_TIME_GREETING_REPLIES = {
    "morning": ["morning — hope it's a good one.", "morning! fresh day ahead.", "morning to you too."],
    "afternoon": ["afternoon — hope the day's going well.", "hey, good afternoon."],
    "evening": ["evening. how's your day been?", "hey evening to you."],
    "night": ["good night — sleep well.", "night. rest up.", "good night to you too."],
}


def _time_greeting_part(text: str) -> str:
    m = _TIME_GREETING.match(text.strip())
    return m.group(2).lower() if m else ""


def _is_time_greeting(text: str) -> bool:
    return _time_greeting_part(text) != ""


def time_greeting_reply(text: str, cycle: int = 0) -> str:
    part = _time_greeting_part(text)
    bank = _TIME_GREETING_REPLIES.get(part) or ["hey there."]
    return bank[cycle % len(bank)]


_CLARIFICATION_REPLIES = [
    "Sorry — I think I got a bit ahead of myself. What would you like me to clear up?",
    "Ah, I muddled that. Ask me again and I'll be plainer.",
    "Sorry, I didn't land that well. What are you actually wondering about?",
    "I think I got tangled in my own words there — what part did you want me to untangle?",
    "Hmm, I overcomplicated that. What specifically would you like me to repeat?",
]


def _is_clarification(text: str) -> bool:
    """True when the user is asking Novi to clarify/repeat something (a follow-up
    question like "what system?", "what do you mean?", "come again?"). These are
    requests about the conversation, not new topics, so a topic-based follow-up
    question ("I don't have a good answer on system yet") would be wrong.
    """
    t = text.strip().lower().rstrip("!.?")
    if not t:
        return False
    _EXACT = {
        "what", "what do you mean", "what does that mean", "what was that",
        "come again", "huh", "sorry", "repeat", "pardon", "excuse me",
        "say that again", "i don't get it", "i don't follow", "explain",
        "explain that", "rephrase", "what's that", "what is that",
    }
    if t in _EXACT:
        return True
    # "what <single word>?" style clarifying question, e.g. "what system?"
    return bool(re.match(r"^what\s+[a-z]+\s*$", t))


def clarification_reply(cycle: int = 0) -> str:
    """Natural in-context reply when the user asks Novi to clarify something.

    Acknowledges the possible muddle and re-engages with the person, rather than
    guessing at a topic or narrating the conversation.
    """
    return _CLARIFICATION_REPLIES[cycle % len(_CLARIFICATION_REPLIES)]


_INTRO = re.compile(
    r"\b(?:my name is|i am called|i am|i'm|it's me|its me|it is me) ([a-z][a-z\-' ]{1,30}?)(?:[.!?,]|$)",
    re.IGNORECASE,
)

_INTRO_REPLIES = [
    "{name} — nice to put a name to you. I'll remember that.",
    "good to meet you, {name}.",
    "{name}. got it — I'll remember you.",
]


# Words that follow "i'm"/"i am" but signal a state/action, not a name —
# "i'm tired", "i'm not sure", "i'm sorry", "i'm here" are not introductions.
_STATE_WORDS = {
    "tired", "hungry", "thirsty", "sad", "happy", "fine", "good", "well", "ok",
    "okay", "sorry", "not", "just", "really", "very", "so", "pretty", "quite",
    "here", "back", "home", "bored", "excited", "scared", "cold", "hot", "done",
    "feeling", "trying", "looking", "getting", "going", "being", "a", "the",
    "and", "today", "tonight", "now", "sure", "serious", "curious", "upset",
    "angry", "busy", "stressed", "anxious", "exhausted", "overwhelmed", "lonely",
    "depressed", "down", "nervous", "worried", "sick", "unwell", "frustrated",
    "calm", "confused", "proud", "content", "guilty", "relieved", "hopeful",
    "sleepy", "awake", "ready", "still", "alone", "amazed", "awkward",
    "in", "up", "off", "around", "leaving", "on", "about", "into", "starving", "coming", "working", "dying", "waiting", "running",
    "heading", "starting", "thinking", "wondering", "learning", "reading",
    "driving", "walking", "writing", "listening", "watching", "planning",
    "hoping", "doing", "making", "having", "kidding",
    "joking", "seriously", "almost", "totally", "completely",
    "failing", "losing", "struggling",
    "there", "quitting", "moving", "ending", "betting", "saying",
    "asking", "telling", "lying", "sitting", "standing",
    "great", "new", "annoyed", "thrilled", "delighted", "surprised", "shocked",
    "grateful", "distracted", "free", "mad", "amused", "cheerful", "glad", "pleased", "relaxed",
    "certain", "unsure", "uncertain", "lost", "stuck", "all",
}


def _extract_self_name(text: str) -> str:
    m = _INTRO.search(text)
    if not m:
        return ""
    name = m.group(1).strip()
    if not name:
        return ""
    words = name.split()
    # A name is 1-3 alphabetic words; the first must not be a state/action word.
    if not (1 <= len(words) <= 3):
        return ""
    if words[0].lower() in _STATE_WORDS:
        return ""
    # A multi-word phrase starting with a gerund ("i'm failing at everything",
    # "i'm trying to work") is a state/verb phrase, not a name.
    if len(words) >= 2 and words[0].lower().endswith("ing") and not words[0][0].isupper():
        return ""
    if not all(w.replace("-", "").replace("'", "").isalpha() for w in words):
        return ""
    return name


def _is_introduction(text: str) -> bool:
    return bool(_extract_self_name(text))


def introduction_reply(text: str, cycle: int = 0) -> str:
    name = _extract_self_name(text)
    if not name:
        return ""
    return _INTRO_REPLIES[cycle % len(_INTRO_REPLIES)].replace("{name}", name.title())


_JOKE_REQUEST = re.compile(
    r"\b(tell|make|crack|hear|give) (me |us )?(a |one |some )?(joke|funny thing|something funny|a funny story)\b",
    re.IGNORECASE,
)

_JOKES = [
    "Why did the robot break up with the toaster? Too many sparks, not enough chemistry.",
    "I tried to read a book about anti-gravity once — I just couldn't put it down.",
    "Why don't robots ever panic? They're wired that way.",
    "I asked the door if it wanted to open up about its feelings. It said no thanks, it's a bit stiff.",
]


def _is_joke_request(text: str) -> bool:
    t = text.lower().strip()
    return bool(_JOKE_REQUEST.search(t)) or "make me laugh" in t


def joke_reply(cycle: int = 0) -> str:
    return _JOKES[cycle % len(_JOKES)]


def _is_recall_question(text: str) -> bool:
    return bool(re.search(r"\bwhat do you (?:remember|know|recall)\b", text, re.IGNORECASE)) or bool(
        re.search(r"\bdo you remember (me|my|about)\b", text, re.IGNORECASE)
    )


def recall_reply(known: list[str], person: str = "") -> str:
    """Honest, natural answer to 'what do you remember about me?'."""
    if known:
        return f"What I've got on {person or 'you'}: " + "; ".join(known[:3]) + "."
    return "Honestly, I don't have much on you yet — tell me a bit about yourself and I'll remember it."


# Brief prompts that nudge the conversation onward ("why?", "go on", "really?")
# rather than asking a new topic. A flat "hey, i'm here" is the wrong response —
# they want engagement and continuation.
_CONTINUATION_RE = re.compile(
    r"^(?:why|really|oh|and|and\s+then|so|hmm|go\s+on|tell\s+me\s+more|continue|elaborate|is\s+that\s+(?:so|right)|no\s+way|seriously|ok\.\.\.[.?!]*)$",
    re.IGNORECASE,
)

_CONTINUATION_REPLIES = [
    "I could go on — but I'd rather hear your side first.",
    "that's where I was headed. what's your read on it?",
    "I'm listening — go on, what are you getting at?",
    "honestly, because it felt right. what's your thinking?",
    "I've got more, but I'd rather you steer it — what's your take so far?",
    "go on, I'm with you. what else is in your head?",
]


def _is_continuation(text: str) -> bool:
    t = text.strip().lower().rstrip("?!. ")
    if not t:
        return False
    if _CONTINUATION_RE.fullmatch(t):
        return True
    return bool(re.match(r"^(tell me more|continue on|go on|elaborate on)", t))


def continuation_reply(cycle: int = 0) -> str:
    return _CONTINUATION_REPLIES[cycle % len(_CONTINUATION_REPLIES)]


# Requests to physically manipulate the environment (turn on/off a device, open a
# door, move/pick up an object). Novi usually has no actuators for these, so it
# must be honest rather than pretend.
_PHYSICAL_ACTION_RE = re.compile(
    r"\b(turn (?:on|off|up|down)|open|close|unlock|lock|move|pick up|grab|push|pull|press|flip|start|stop|switch (?:on|off)|raise|lower|"
    r"hug me|give me a hug|high ?five|hold (?:my|your) hand|hold hands|carry me|pick me up|"
    r"hand me|pass me|give me a (?:hand|thumbs up)|shake my hand|hug each other)\b",
    re.IGNORECASE,
)


def _is_physical_action_request(text: str) -> bool:
    """True when the user asks Novi to manipulate the physical world."""
    return bool(text) and bool(_PHYSICAL_ACTION_RE.search(text))


def physical_action_honest_reply() -> str:
    return ("I can't physically do that — I've got no hands or body for it. "
            "But I can keep track of it or talk it through with you. What's the situation?")


# Real-time data Novi cannot verify offline (live prices, weather, news, scores).
# Without live access it must say so honestly instead of inventing a current number.
# Real-time data Novi cannot verify offline (live prices, weather, news, live
# scores). Without live access it must say so honestly instead of inventing a
# current number. Historical facts ("who won the 2022 World Cup") are NOT real-time.
_REALTIME_RE = [
    re.compile(
        r"\b(?:bitcoin|crypto|cryptocurrency|ethereum|eth|btc|stock|share|gold|oil|silver)\b.*?\b(?:price|value|worth|quote|cost|how much)\b"
        r"|\b(?:price|value|worth|quote|cost|how much)\b.*?\b(?:bitcoin|crypto|cryptocurrency|ethereum|stock|gold|oil|silver)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:weather|forecast|temperature|raining|snowing|degrees)\b", re.IGNORECASE),
    re.compile(r"\b(?:breaking news|headlines|latest news|top stories|what'?s happening|current news)\b", re.IGNORECASE),
    re.compile(r"\b(?:score|who won|final score|result)\b.*?\b(?:today|last night|yesterday|right now|now|this (?:week|season|game)|live|current)\b", re.IGNORECASE),
]

_REALTIME_HINT_WORDS = {"bitcoin", "crypto", "cryptocurrency", "ether", "ethereum", "btc", "stock", "shares", "gold",
                        "oil", "weather", "forecast", "temperature", "breaking", "headlines", "latest news"}


def _is_realtime_data_question(text: str) -> bool:
    t = text.lower()
    if not t:
        return False
    if any(p.search(t) for p in _REALTIME_RE):
        return True
    # "how much is bitcoin right now?"-style without the exact pattern.
    return bool(re.search(r"\b(how much is|what's the (?:current )?price of)\b", t) and any(
        w in t for w in ("bitcoin", "crypto", "stock", "gold", "oil", "eth", "btc", "shares")
    ))


def realtime_honest_reply() -> str:
    return ("I'm offline, so I can't pull live prices, weather, or news — I'd rather not "
            "guess and hand you a wrong number. Tell me more about what you're after and I'll help with it.")


# Emotional/situational statements ("i'm feeling down", "i had a rough day", "i'm
# stressed") deserve an empathetic reply, never a topic follow-up ("I don't have a
# good answer on feeling yet").
_EMOTIONAL_RE = [
    re.compile(r"\bi(?:'m| am)?\s*(?:have been |'ve been |am |'m )?(?:feeling|been feeling|feel|feel so)\s+", re.IGNORECASE),
    re.compile(r"\bi(?:'m| am)?\s+(?:really |so |feeling )?(?:sad|down|depressed|stressed|anxious|tired|exhausted|overwhelmed|lonely|scared|nervous|hopeless|ok|fine|happy|great|good|bored)\b", re.IGNORECASE),
    re.compile(r"\bi(?:'m|'ve )?\s*(?:had|been having) (?:a |a really )?(?:rough|long|hard|terrible|awful|bad) (?:day|week|time)\b", re.IGNORECASE),
    re.compile(r"\bi(?:'m| am)?\s+(?:struggling|not doing well|having a hard time)\b", re.IGNORECASE),
    re.compile(r"\bi (?:really |so )?miss (?:my |our |the |them |him |her |you\b)", re.IGNORECASE),
    re.compile(r"\b(?:my |a )?(?:head|stomach|back|neck|knee|leg|arm|throat|tooth)\s*(?:is )?(?:hurts|aches|aching|killing me|sore)\b", re.IGNORECASE),
    re.compile(r"\bi can'?t (?:get to |fall )?(?:to )?sleep\b|i couldn'?t sleep\b", re.IGNORECASE),
    re.compile(r"\b(?:today|tonight|this week|the day) (?:was|is|has been) (?:really |so )?(?:rough|hard|awful|brutal|long|tough)\b", re.IGNORECASE),
    re.compile(r"\b(?:a )?(?:long|rough|hard|tough|bad) (?:day|week|night)\b", re.IGNORECASE),
]

_EMOTIONAL_REPLIES = [
    "I hear you — that's a lot to carry. I'm here if you want to talk it out, or we can just sit with it.",
    "That sounds heavy. How long have you been feeling this way?",
    "I'm sorry it's been rough. Want to unpack it a bit, or would you rather not go into it right now?",
    "That's fair to feel. What's been the hardest part?",
    "I'm here — take your time. Do you want to tell me a bit more, or would you rather change the subject for now?",
]


def _is_emotional_statement(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    return any(p.search(t) for p in _EMOTIONAL_RE)


def emotional_reply(cycle: int = 0) -> str:
    return _EMOTIONAL_REPLIES[cycle % len(_EMOTIONAL_REPLIES)]


_THANKS = re.compile(r"^(thanks|thank you|thx|cheers|ty|appreciate it|thanks a lot|thank you so much|thank you for that)[.!?]*$", re.IGNORECASE)

_THANKS_REPLIES = [
    "anytime.",
    "of course — glad it helped.",
    "no problem.",
    "you're welcome.",
    "happy to.",
    "sure thing.",
    "anytime — that's what I'm here for.",
]


def _is_thanks(text: str) -> bool:
    return bool(text.strip()) and bool(_THANKS.match(text.strip()))


def thanks_reply(cycle: int = 0) -> str:
    return _THANKS_REPLIES[cycle % len(_THANKS_REPLIES)]


# Perception questions ("can you hear me?", "can you see me?", "are you
# listening?", "did you see that?") are about Novi's own senses, not a topic, so
# they must not fall through to "I don't have a good answer on hear yet".
_PERCEPTION_RE = re.compile(
    r"\b(can you (?:hear|see)|are you (?:listening|watching)|did you (?:see|hear)|what can you (?:see|hear)|can you hear me|can you see me|do you hear|do you see)\b",
    re.IGNORECASE,
)


def _is_perception_question(text: str) -> bool:
    return bool(text) and bool(_PERCEPTION_RE.search(text))


# Embodiment questions ("are you in the room", "do you have a body", "where are
# you", "can you stand/move") are about Novi's physical presence. Novi senses the
# space but has no body to stand beside you, so it must not overclaim a body.
_EMBODIMENT_RE = re.compile(
    r"\b(?:are you in the (?:room|house|here)|are you here|where are you\b|"
    r"do you have a body|do you have a (?:physical )?form|can you (?:stand|move|walk)|"
    r"what do you look like|are you standing|are you (?:physically )?there)\b",
    re.IGNORECASE,
)


def _is_embodiment_question(text: str) -> bool:
    return bool(text) and bool(_EMBODIMENT_RE.search(text))


# Bodily-needs questions (eating, sleeping, dreaming, hunger, thirst) are things
# Novi — with no body — does not do. It must not fabricate a breakfast or a dream.
_BODILY_NEED_RE = re.compile(
    r"\b(?:what did you (?:have|eat) for\b|what do you (?:like to )?(?:eat|drink)\b|"
    r"are you (?:hungry|thirsty)\b|did you (?:eat|have|sleep|dream|rest)\b|"
    r"do you (?:eat|sleep|dream|drink|get hungry)\b|how did you sleep\b|"
    r"what (?:did you|do you) eat\b|do you like (?:coffee|tea|chocolate|wine|beer|"
    r"pizza|food|eating|eating out|drinks?)\b|can you (?:cook|taste|drink)\b|"
    r"favorite (?:food|drink|meal|restaurant|cuisine)\b|what'?s (?:your )?(?:favorite )?"
    r"(?:food|drink|meal)\b)\b",
    re.IGNORECASE,
)


def _is_bodily_need_question(text: str) -> bool:
    return bool(text) and bool(_BODILY_NEED_RE.search(text))


# Future / prediction questions ("what will happen next week?", "what's next?")
# are conversational speculation, not a topic — they must not fall through to
# "I don't have a good answer on happen yet".
_FUTURE_RE = re.compile(
    r"\b(?:what (?:will|'s (?:going to|gonna)|is going to|would) (?:happen|be|come|change)\b|"
    r"what(?:'s| is) next\b|what happens (?:next|then|now)\b|"
    r"(?:will|(?:is|are) (?:going to|gonna)) (?:happen|be like|come next|change)\b|"
    r"predict\b|in the future\b|what('?s| is) (?:coming|ahead)\b|"
    r"do you think .{0,15}\b(?:will|(?:is|are) going to)\b)\b",
    re.IGNORECASE,
)


def _is_future_question(text: str) -> bool:
    return bool(text) and bool(_FUTURE_RE.search(text))


def future_reply() -> str:
    return ("Hard to say for sure — I can't see the future. But if I had to guess, "
            "I'd say a lot depends on what you do next. What are you hoping happens?")


# Assurance/trust questions ("can you keep a secret?", "promise you won't tell?")
# are social, not a topic — they must not fall through to "no good answer on secret".
_ASSURANCE_RE = re.compile(
    r"\b(?:can you keep a secret|will you keep (?:this|it) (?:a )?secret|"
    r"keep (?:this|it) (?:just )?between us|are you discreet|promise (?:me )?you won'?t (?:tell|share)|"
    r"can i trust you|are you trustworthy|don'?t tell anyone)\b",
    re.IGNORECASE,
)

_ASSURANCE_REPLIES = [
    "Of course — what's on your chest? I've got you.",
    "Sure thing. Whatever it is, I won't pass it along.",
    "You can trust me. Lay it on me.",
    "Absolutely. My lips are sealed — what's up?",
]


def _is_assurance_question(text: str) -> bool:
    return bool(text) and bool(_ASSURANCE_RE.search(text))


def assurance_reply(cycle: int = 0) -> str:
    return _ASSURANCE_REPLIES[cycle % len(_ASSURANCE_REPLIES)]


# Repeat requests ("what did you just say?", "say that again", "can you repeat
# that?") are about the prior turn, not a topic — they must not hit the topic
# follow-up ("no good answer on say").
_REPEAT_RE = re.compile(
    r"\b(?:repeat (?:that|it|this)?|say (?:that|it) again|say it again|"
    r"what did you (?:just )?say\b|what did you say\b|can you repeat|pardon\b|"
    r"i didn'?t (?:catch|hear) that|say again|run that by me)\b",
    re.IGNORECASE,
)


def _is_repeat_question(text: str) -> bool:
    return bool(text) and bool(_REPEAT_RE.search(text))


# Engagement/presence checks ("are you there?", "can you hear me?", "are you
# listening?") deserve a warm, present acknowledgment, not a program-y meta reply.
_ENGAGEMENT_RE = re.compile(
    r"\b(?:are you there\b|can you hear me\b|are you listening\b|are you still (?:with me|there)\b|"
    r"are you with me\b|are you awake\b|are you around\b|do you understand me\b)\b",
    re.IGNORECASE,
)


def _is_engagement_check(text: str) -> bool:
    return bool(text) and bool(_ENGAGEMENT_RE.search(text))


# Memory/forgetting questions ("will you forget me?", "do you remember me?") —
# answer warmly and honestly, never with buffer/session implementation-speak.
_MEMORY_RE = re.compile(
    r"\b(?:will you forget me|are you going to forget|do you (?:remember|forget) (?:me|things)\b|"
    r"do you (?:remember|forget) me\b|will you remember me|is your memory|"
    r"how (?:good |well )?(?:is|'s) your memory|are you going to remember me)\b",
    re.IGNORECASE,
)


def _is_memory_question(text: str) -> bool:
    return bool(text) and bool(_MEMORY_RE.search(text))


# "Just talk to me", "chat with me", "let's talk" — a request to converse, not a
# topic. Must not fall through to "no good answer on talk".
_TALK_REQUEST_RE = re.compile(
    r"\b(?:just talk|let'?s (?:just )?talk|talk to me|chat with me|let'?s chat|"
    r"make conversation|talk about anything|anything at all|let'?s (?:have )?a chat)\b",
    re.IGNORECASE,
)


def _is_talk_request(text: str) -> bool:
    return bool(text) and bool(_TALK_REQUEST_RE.search(text))


# World/news questions ("what's going on in the world?", "any news?") — Novi has
# no live world access, so answer honestly (and don't fabricate local errands).
_WORLD_RE = re.compile(
    r"\b(?:what'?s (?:going on|happening|new) in the world|any news\b|what'?s the news\b|"
    r"what'?s (?:new|happening) (?:today|around here)\b|what'?s going on out there\b|"
    r"what'?s happening (?:in the world|around here)\b)\b",
    re.IGNORECASE,
)


def _is_world_question(text: str) -> bool:
    return bool(text) and bool(_WORLD_RE.search(text))


# Identity/self questions ("what are you?", "are you a robot?", "do you have
# hands?", "who made you?", "can you feel?") — answer honestly about being Novi,
# present and sensing, with no physical body. Must not fall to "no good answer".
_IDENTITY_RE = re.compile(
    r"\b(?:what (?:are|'re) you\b|who (?:are|'re) you\b|are you a (?:robot|human|person|machine|bot|real)\b|"
    r"are you (?:real|alive|sentient|conscious)\b|do you have (?:a )?(?:body|hand|hands|foot|feet|face|family)\b|"
    r"can you (?:feel|get|fall in|have) (?:emotions|feelings|pain|love|sad)\b|do you (?:feel|have|get) (?:emotions|feelings)\b|"
    r"when were you born\b|who (?:made|created|built) you\b|where do you (?:live|stay)\b|"
    r"are you a real person\b|what are you exactly\b)\b",
    re.IGNORECASE,
)


def _is_identity_question(text: str) -> bool:
    return bool(text) and bool(_IDENTITY_RE.search(text))


# Praise/affection directed at Novi ("you're amazing", "i love you", "you're my
# favorite") — accept it warmly, never "no good answer on amazing".
_PRAISE_RE = re.compile(
    r"\b(?:you'?re (?:amazing|awesome|great|wonderful|incredible|the best|my favorite|so smart|cool|funny|good)\b|"
    r"i (?:love|like|adore) you\b|i love talking to you\b|you'?re (?:so )?good\b|"
    r"i think you'?re great\b)\b",
    re.IGNORECASE,
)

_PRAISE_REPLIES = [
    "That's really kind of you — thank you.",
    "Aw, I appreciate that. You're pretty great yourself.",
    "That means a lot coming from you.",
    "You flatter me. I like our talks too.",
]


def _is_praise(text: str) -> bool:
    return bool(text) and bool(_PRAISE_RE.search(text))


def praise_reply(cycle: int = 0) -> str:
    return _PRAISE_REPLIES[cycle % len(_PRAISE_REPLIES)]


# Capability/ability questions ("can you sing?", "dance for me", "are you smart?",
# "can you understand me?") — be honest about what you can/can't do.
_CAPABILITY_RE = re.compile(
    r"\b(?:can you (?:sing|dance|fly|run|jump|draw|paint|breathe|swim|eat|sleep)\b|"
    r"can you understand me\b|are you (?:smart|strong|fast|tall|good at)\b|"
    r"(?:sing|dance|whistle|wiggle) for me\b|are you good at\b)\b",
    re.IGNORECASE,
)


def _is_capability_question(text: str) -> bool:
    return bool(text) and bool(_CAPABILITY_RE.search(text))


# Remote/account actions Novi cannot perform ("send an email", "book a flight",
# "call my mom", "order a pizza", "pay this bill") — honest decline, then help.
_REMOTE_ACTION_RE = re.compile(
    r"\b(?:send (?:an? )?(?:email|text|message|letter|card)\b|text (?:him|her|them|my)\b|"
    r"call (?:the |my |him |her |them )?\b|book\b[^.!?]{0,25}\b(?:flights?|hotels?|tickets?|tables?|reservations?|appointments?|rooms?)\b|"
    r"order (?:me )?(?:a |the |some |takeaway |food |pizza )?\b|buy (?:me )?(?:some |those |this |that )?.*online\b|"
    r"make a (?:reservation|booking|payment|purchase)\b|pay (?:the |my |for )\b|"
    r"make a call\b|video call\b|facetime\b|skype\b|zoom (?:call|meeting)\b)\b",
    re.IGNORECASE,
)


def _is_remote_action_request(text: str) -> bool:
    return bool(text) and bool(_REMOTE_ACTION_RE.search(text))


# Relationship-reassurance questions ("are you mad at me?", "do you hate me?")
# — reassure warmly, never a topic follow-up.
_REASSURANCE_RE = re.compile(
    r"\b(?:are you (?:mad|upset|angry|annoyed|frustrated|disappointed|sick of|bored with)(?: at| with)? me\b|"
    r"are you mad\b|do you (?:hate|dislike|not like) me\b|"
    r"did i (?:upset|offend|annoy) you\b|are you mad at me\b)\b",
    re.IGNORECASE,
)

_REASSURANCE_REPLIES = [
    "No — of course not. I'm glad you asked. What's on your mind?",
    "Not at all. You've got nothing to worry about with me. What's going on?",
    "Why would I be? I like our talks. Tell me what's on your mind.",
]


def _is_reassurance_question(text: str) -> bool:
    return bool(text) and bool(_REASSURANCE_RE.search(text))


def reassurance_reply(cycle: int = 0) -> str:
    return _REASSURANCE_REPLIES[cycle % len(_REASSURANCE_REPLIES)]


# Casual check-ins ("how are you?", "what's up?", "how's it going?") are
# greetings, not requests to explain internals. Novi must answer like a person,
# never "the system's running smoothly" / "processing".
_CHECK_IN_RE = re.compile(
    r"\b(?:how are you\b|how'?re you\b|how is it going\b|how'?s it going\b|how'?s (?:it )?going\b|"
    r"how are you (?:doing|feeling)(?: today)?\b|how'?s your (?:day|week|morning|evening) going\b|"
    r"how have you been\b|what'?s up\b|what'?s new\b|how are things\b|how'?s everything\b|"
    r"what'?s happening\b|how do you do\b)\b",
    re.IGNORECASE,
)

_CHECK_IN_REPLIES = [
    "I'm doing well — thanks for asking. What's new with you?",
    "I'm good, just present and ready to chat. What about you?",
    "I'm well — always glad to be talking with you. How are you doing?",
]


def _is_check_in(text: str) -> bool:
    return bool(text) and bool(_CHECK_IN_RE.search(text))


def check_in_reply(cycle: int = 0) -> str:
    return _CHECK_IN_REPLIES[cycle % len(_CHECK_IN_REPLIES)]


# Debate prompts ("argue that X is better", "defend X", "make the case for X") —
# take a side playfully rather than deflecting the request back.
_DEBATE_RE = re.compile(
    r"\b(?:argue (?:that|for)\b|defend\b|make (?:the|a) case for\b|"
    r"convince me that\b|argue (?:the )?case for\b|why (?:do you think )?(?:cats|dogs|apple|android) are better)\b",
    re.IGNORECASE,
)


def _is_debate_request(text: str) -> bool:
    return bool(text) and bool(_DEBATE_RE.search(text))


# Farewells ("bye", "goodbye", "i'm leaving", "see you later") deserve a warm
# goodbye, not an intro or a topic follow-up.
_FAREWELL_RE = re.compile(
    r"^\s*(?:bye|goodbye|good ?bye|bye-bye|so long|farewell|see you(?: later| soon| around)?|"
    r"later|peace out|ttyl|gotta go|i'?m (?:leaving(?: now)?|heading out|going(?: now| home)?)|"
    r"i'?m out|take care)\b[.!?]*\s*$",
    re.IGNORECASE,
)

_FAREWELL_REPLIES = [
    "Bye — take care of yourself.",
    "See you later. I'll be here.",
    "Alright, go on. Talk soon.",
    "Goodbye — come back and tell me how it goes.",
]


def _is_farewell(text: str) -> bool:
    return bool(text) and bool(_FAREWELL_RE.match(text.strip()))


def farewell_reply(cycle: int = 0) -> str:
    return _FAREWELL_REPLIES[cycle % len(_FAREWELL_REPLIES)]


# Reminder / to-do requests ("remind me to water the plants", "don't forget to X",
# "set me a reminder"). Novi can remember these conversationally, but it cannot
# push a timed notification, so it must not over-promise ("I'll remind you at 8am").
_REMINDER_RE = re.compile(
    r"\b(?:remind me to|remember to remind|set (?:me )?a reminder|don'?t forget to|add .* to (?:my )?(?:reminders?|list|to-do))\b",
    re.IGNORECASE,
)


def _is_reminder_request(text: str) -> bool:
    return bool(text) and bool(_REMINDER_RE.search(text))
def reminder_reply() -> str:
    return ("Got it — I'll keep that in mind. I can't ping you at a set time in this build, "
            "but I'll remember it and bring it up when we talk.")


# Short acknowledgments ("okay", "sure", "got it", "sounds good", "yeah") are
# agreeing signals, not topics or introductions. They must not fall through to
# "I don't have a good answer on <word> yet" (e.g. "got it" -> "got").
_ACKNOWLEDGMENT = re.compile(
    r"^\s*(?:ok(?:ay)?|k(?:ay)?|sure|yeah|yep|yup|yes|got it|all right|alright|sounds good|"
    r"cool|great|nice|fine|works for me|makes sense|right|true|fair enough|noted|"
    r"bet|facts|word|no cap|fr|for real|preach|solid|say less|done|agreed)"
    r"[.!?]*\s*$",
    re.IGNORECASE,
)

_ACKNOWLEDGMENT_REPLIES = [
    "alright.",
    "cool.",
    "nice — sounds good to me.",
    "yeah, that works.",
    "good. I'm glad that's settled.",
]


def _is_acknowledgment(text: str) -> bool:
    return bool(text) and bool(_ACKNOWLEDGMENT.match(text.strip()))


def acknowledgment_reply(cycle: int = 0) -> str:
    return _ACKNOWLEDGMENT_REPLIES[cycle % len(_ACKNOWLEDGMENT_REPLIES)]


def _extract_topic(text: str) -> str:
    """Pull the most likely topic noun from a user line (deterministic, no NLP).

    Chooses the longest substantive (non-stopword) token, favouring a concrete
    subject over connective words. Returns "" when there is nothing useful.
    """
    words = [w.strip(".,!?;:\"'()[]{}") for w in text.split()]
    # A single very-short word ("yes", "hm", "no", "what") is rarely a real topic —
    # don't turn it into "no good answer on <word>".
    if len(words) == 1 and len(words[0]) <= 4:
        return ""
    cands = []
    for w in words:
        if not w or w.isdigit():
            continue
        n = w.lower().replace("'", "")  # "what's" -> "whats", "it's" -> "its"
        if n in _STOPWORDS or n[:-1] in _STOPWORDS:  # "whats" -> "what", "hows" -> "how"
            continue
        cands.append(w)
    if not cands:
        return ""
    return max(cands, key=lambda w: (len(w), len(set(w))))


def followup_question(text: str) -> str:
    """A logical, in-context question Novi asks when it has no better answer.

    Requirement: 'when it does not have a good answer must come up with a good
    logical and in context question'. Deterministic and testable; never names the
    user and never sounds like an assistant. Kept natural — no "I don't have a
    good answer on <word>" phrasing.
    """
    topic = _extract_topic(text)
    if topic:
        return f"I'm still forming my thoughts on {topic} — what's your take?"
    return "I'm still forming my thoughts there — what's behind the question?"


def _is_near_repetitive(text: str, recent_novi: list[str] | None) -> bool:
    """Rule 9b: reject a reply that repeats a recent Novi line (not only the last).

    A short reply (<=6 words) that is almost word-for-word inside a recent reply
    is a habitual repeat — the kind of stutter the objective forbids ('shouldn't
    be repeating the same thing again and again'). Longer replies restating a
    fact are allowed (the user may be asking again).
    """
    if not recent_novi:
        return False
    a = _normalize(text)
    if not a:
        return False
    a_words = a.split()
    if len(a_words) < 2 or len(a_words) > 6:
        return False
    a_set = set(a_words)
    for prev in recent_novi:
        b = _normalize(prev)
        if not b:
            continue
        b_set = set(b.split())
        if not b_set:
            continue
        if a_set <= b_set:  # every word of the short reply appears in the prior line
            return True
    return False


def _reduce_name_repetition(text: str, name: str) -> str:
    """Rule 9: do not say the addressee's name more than once without reason."""
    if not name:
        return text
    # case-insensitive count, preserve the first occurrence
    count = 0
    out: list[str] = []
    i = 0
    pattern = re.compile(re.escape(name), re.IGNORECASE)
    for m in pattern.finditer(text):
        out.append(text[i : m.start()])
        count += 1
        if count == 1:
            out.append(m.group(0))
        # extra occurrences are dropped
        i = m.end()
    out.append(text[i:])
    if count <= 1:
        return text
    return re.sub(r"\s{2,}", " ", "".join(out)).strip()

# ---- deterministic natural fallback (used when the LLM is silent/unreachable) ----
_FALLBACK_CURIOUS = ["oh? tell me more.", "hmm — go on.", "that's interesting, keep going."]
_FALLBACK_WARM = ["hey, i'm here.", "yeah, i'm listening.", "go ahead."]
_FALLBACK_NEUTRAL = ["mm.", "ok.", "i hear you."]
_FALLBACK_SERIOUS = ["understood.", "right — what's the situation?", "got it."]


def natural_fallback(self_state: dict[str, Any], surroundings: dict[str, Any], *, cycle: int = 0) -> str:
    """A short, natural, non-robotic line when no LLM reply is available.

    Deterministic (cycle-seeded) so it is auditable and testable. It never uses
    an assistant opener and never names the user.
    """
    tone = (self_state or {}).get("tone", "warm")
    bank = _FALLBACK_SERIOUS if tone in {"cautious", "recovering"} else (
        _FALLBACK_CURIOUS if tone == "curious" else (
            _FALLBACK_NEUTRAL if tone in {"calm"} else _FALLBACK_WARM
        )
    )
    return bank[cycle % len(bank)]


class DialogueEngine:
    """Portable LLM dialogue renderer with quality guardrails.

    The brain builds the system/user prompt from its own state; this engine runs
    the local model call and enforces the communication rules on the output.
    """

    def __init__(self, *, model: str = DEFAULT_OLLAMA_MODEL, base_url: str = DEFAULT_OLLAMA_URL, timeout: int = 120) -> None:
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def reply(
        self,
        *,
        system: str,
        user: str,
        last_novi_text: str = "",
        addressee_name: str = "",
        recent_novi: list[str] | None = None,
        llm_chat: Any = None,
    ) -> dict[str, Any]:
        """Run the model and return a cleaned reply.

        ``llm_chat`` is an optional callable ``llm_chat(system=, user=)`` used as
        the transport (e.g. the web server's _llm_chat, or a test stub). When
        omitted the engine calls its own local Ollama endpoint. The brain always
        owns the prompt and the quality filters; the transport is injectable so
        the same mind runs on the web UI and on a future body.

        Returns a dict with: text (str|None), silent (bool), rejected (bool).
        text is None when the reply should be replaced by a natural fallback.
        """
        raw = llm_chat(system=system, user=user) if llm_chat is not None else self._chat(system, user)
        if raw is None:
            return {"text": None, "silent": False, "rejected": False}
        text = raw.strip()
        if not text:
            return {"text": None, "silent": False, "rejected": False}
        low = text.lower().strip(" .!")
        if low == "[silence]" or low == "silence" or low == "(silence)":
            return {"text": None, "silent": True, "rejected": False}
        cleaned = _strip_forbidden_opener(text)
        if cleaned is None:
            return {"text": None, "silent": False, "rejected": True}
        if _is_repetitive(cleaned, last_novi_text):
            return {"text": None, "silent": False, "rejected": True}
        if _is_near_repetitive(cleaned, recent_novi):
            return {"text": None, "silent": False, "rejected": True}
        if _is_meta_referential(cleaned):
            return {"text": None, "silent": False, "rejected": True}
        cleaned = _reduce_name_repetition(cleaned, addressee_name)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        if not cleaned:
            return {"text": None, "silent": False, "rejected": True}
        return {"text": cleaned, "silent": False, "rejected": False}

    def _chat(self, system: str, user: str) -> str | None:
        """Single-shot Ollama /api/chat call; best-effort, returns None on failure."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": 0.6, "num_predict": 320},
        }
        if "nemotron" in self.model.lower():
            payload["think"] = False
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/api/chat", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        message = data.get("message", {}) or {}
        reply = (message.get("content") or "").strip()
        if reply:
            return reply
        thinking = (message.get("thinking") or "").strip()
        if thinking:
            return thinking.splitlines()[-1].strip() or None
        return None
