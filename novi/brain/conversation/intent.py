"""Plan 03 Phase 2: deterministic intent + dialogue-act classification.

Pure pattern/cue matching over the Step 2.1 taxonomy and the Step 2.2
dialogue acts — no LLM, no sockets, stdlib only. Imports the frozen
contracts from ``conversation_state`` exactly; nothing is redefined here.

Step 2.3 policy: confidence >= 0.85 proceeds normally, 0.60-0.84 proceeds
with cautious context handling, < 0.60 sets ``needs_clarification`` when
the ambiguity is material (competing cues, or no discriminating cue).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from novi.brain.conversation.conversation_state import (
    ConversationState,
    IntentResult,
)

CLARIFY_THRESHOLD = 0.60

# Dialogue acts (Step 2.2). Intent says what the user wants; the act says
# the conversational move used to express it.
QUESTION = "QUESTION"
ASSERTION = "ASSERTION"
REQUEST = "REQUEST"
CORRECTION = "CORRECTION"
GREETING = "GREETING"
FAREWELL = "FAREWELL"
EMPATHIC_TRIGGER = "EMPATHIC_TRIGGER"
CLARIFICATION_ANSWER = "CLARIFICATION_ANSWER"
CLARIFICATION_QUESTION = "CLARIFICATION_QUESTION"
CONFIRMATION = "CONFIRMATION"
DISCONFIRMATION = "DISCONFIRMATION"


@dataclass(frozen=True)
class _Rule:
    intent: str
    dialogue_act: str
    confidence: float
    cues: tuple[str, ...]
    reason: str


def _has(text: str, *cues: str) -> bool:
    return any(cue in text for cue in cues)


def _match_re(text: str, *patterns: str) -> bool:
    return any(re.search(p, text) for p in patterns)


def _match_start(text: str, *patterns: str) -> bool:
    """Match against the unpadded string so ``^`` anchors behave."""
    return any(re.match(p, text) for p in patterns)


def _candidate_rules(text: str, state: ConversationState) -> list[_Rule]:
    """All rules whose cues fire, in priority order (first = highest)."""
    stripped = text.strip()
    flat = stripped.lower()
    # Voice-channel/disfluency normalization (plan pipeline stage 1):
    # leading ASR fillers ("uh", "um") carry no intent and otherwise
    # depress cue confidence into spurious clarification ("uh what
    # interiors do I prefer" must read as the memory question it is).
    flat = re.sub(r"^(?:(?:uh|um|er|ah|hmm)[,\s]+)+", "", flat).strip()
    lowered = f" {flat} "
    words = lowered.split()
    is_question = stripped.endswith("?") or bool(
        re.match(r"^(who|what|when|where|which|how|is|are|was|were|does|do|did|"
                 r"can|could|will|would|has|have|had|should)\b", flat))
    rules: list[_Rule] = []

    # Explicit corrections win over everything (plan: 'no, I meant X').
    # Bare "no"/"nope" alone is disconfirmation, not a correction.
    # Bare "i said X" recalls content (memory question), it does not correct
    # unless a contrast marker is adjacent ("I said Tesla, not BMW").
    _contrast = _has(lowered, " not ", "n't ", " instead", " rather",
                     " wrong", " incorrect", " meant", " misspoke")
    if (len(words) > 2 or _has(lowered, "i meant", "actually", "wrong",
                               "incorrect", "mistake", "rephrase",
                               "misunderstood")) and (
            _has(lowered, "i meant", "i misspoke", "let me rephrase",
                 "you misunderstood", "that's not what i")
            or (_has(lowered, "i said ") and _contrast)
            or _match_re(lowered, r"\bactually\b", r"\bwrong\b",
                         r"\bincorrect\b", r"\bmy mistake\b")
            or _match_start(flat, r"no[,.]")):
        rules.append(_Rule("CORRECTION", CORRECTION, 0.90,
                           ("correction cue",),
                           "explicit correction cue"))
    # Bare confirmations / disconfirmations (short replies only).
    if len(words) <= 4 and _match_start(
            flat, r"(yes|yeah|yep|yup|sure|exactly|correct|right|affirmative)\b"):
        rules.append(_Rule("CONFIRMATION", CONFIRMATION, 0.90,
                           ("confirmation cue",), "bare confirmation reply"))
    if (len(words) <= 4 and _match_start(
            flat, r"(no|nope|nah|not really|negative)\b")
            and not _has(lowered, "i meant", "actually")):
        rules.append(_Rule("DISCONFIRMATION", DISCONFIRMATION, 0.90,
                           ("disconfirmation cue",),
                           "bare disconfirmation reply"))
    # Greeting / farewell only when the message is essentially just that;
    # "hi, what is X?" is a question, not a greeting.
    if len(words) <= 5 and _match_start(
            flat, r"(hi|hey|hello|yo|good ?(morning|afternoon|evening)|howdy|hiya)\b"):
        rules.append(_Rule("GREETING", GREETING, 0.95,
                           ("greeting cue",), "greeting with no other content"))
    if _match_re(lowered, r"\b(goodbye|bye+|see you|talk (to you )?later|gotta go|good ?night)\b"):
        rules.append(_Rule("FAREWELL", FAREWELL, 0.90,
                           ("farewell cue",), "farewell cue"))
    if _has(lowered, "tell me a joke", "make me laugh", "say something funny",
            "know any jokes", "another joke"):
        rules.append(_Rule("JOKE/HUMOR", REQUEST, 0.90,
                           ("humor cue",), "explicit joke request"))
    if _has(lowered, "cross the road", "knock knock", "knock, knock"):
        rules.append(_Rule("JOKE/HUMOR", REQUEST, 0.95,
                           ("joke frame",), "classic joke frame"))
    if _has(lowered, "who are you", "your name", "about yourself",
            "what are you", "who made you", "who created you"):
        rules.append(_Rule("IDENTITY_QUERY", QUESTION, 0.90,
                           ("identity cue",), "asks about Novi's identity"))
    if _has(lowered, "what do you see", "describe what you see",
            "what's in front", "what is in front", "do you see",
            "can you see", "what does it look like right now",
            "who is in front", "what am i holding",
            "on the table", "on the counter", "on the desk",
            "in the room", "in front of you", "around you",
            "walked in", "just arrived",
            "is there anyone", "is anyone here", "is anyone there",
            "who is here", "who's here",
            "what is on the table", "what's on the table"):
        rules.append(_Rule("OBSERVATION_QUERY", QUESTION, 0.90,
                           ("observation cue",), "asks about live observation"))
    if _has(lowered, "did you hear", "do you hear", "what was that sound",
            "what does that sound like", "who is speaking",
            "recognize that sound"):
        rules.append(_Rule("PERCEPTION_QUERY", QUESTION, 0.85,
                           ("perception cue",), "asks about live perception"))
    if _has(lowered, "do you remember", "you remember", "recall ",
            "what did i tell you", "what did i say", "what do you know about me",
            "have i told you", "what have i told you",
            "do i prefer", "do i like", "do i love", "do i hate",
            "what do i prefer", "what do i like", "what do i love") or (
            is_question and _has(lowered, "my trip", "yesterday")):
        rules.append(_Rule("MEMORY_QUERY", QUESTION, 0.85,
                           ("memory cue",), "asks about remembered content"))
    # Interrogative frames ("do I prefer?", "would I like?") ask about a
    # preference — they must not match the declarative "i prefer" cue.
    _asks_about_self = is_question and _has(
        lowered, "do i ", "do you ", "would i ", "should i ", "what ",
        "which ", "who ", "when ", "where ", "how ")
    if _has(lowered, "don't forget", "do not forget", "remember that",
            "note that", "save this", "write this down",
            "my birthday is", "i live in", "my name is",
            "my favorite", "my favourite", "i prefer", "i hate",
            "i love ", "i like ", "i dislike", "allergic to") \
            and not _asks_about_self:
        rules.append(_Rule("MEMORY_UPDATE", ASSERTION, 0.85,
                           ("memory-update cue",),
                           "states durable personal fact/preference"))
    if _has(lowered, "compare", " vs ", " versus ", "difference between",
            "which is better", "which one is better", "better choice"):
        rules.append(_Rule("COMPARISON", QUESTION, 0.85,
                           ("comparison cue",), "explicit comparison cue"))
    # Bare "best " collides with praise ("you are the best"), so the cue
    # set names recommendation frames explicitly instead.
    if _has(lowered, "recommend", "suggest", "should i buy", "should i get",
            "should i choose", "which one should i", "what should i buy",
            "what is the best", "what's the best", "which is the best",
            "best way", "best place", "best time", "best deal",
            "best price", "best option", "best choice", "best buy",
            "worth buying", "would you buy"):
        rules.append(_Rule("RECOMMENDATION", REQUEST, 0.85,
                           ("recommendation cue",),
                           "asks for a recommendation"))
    if _has(lowered, "what can you do", "your capabilit", "what are you able to",
            "are you able to", "do you support", "can you even"):
        rules.append(_Rule("CAPABILITY_QUERY", QUESTION, 0.90,
                           ("capability cue",),
                           "asks about Novi's capabilities"))
    if _has(lowered, "remind me", "set a ", "create a reminder",
            "book ", "order ", "send ", "schedule a", "add a calendar",
            "write ", "draft ", "summarize this", "summarise this",
            "translate", "please ", "pick up", "pick that up",
            "bring me", "fetch ", "hand me", "carry ", "place ",
            "put ", "move ", "open ", "close "):
        rules.append(_Rule("TASK_REQUEST", REQUEST, 0.80,
                           ("task cue",), "requests an action/task"))
    if _has(lowered, "summar"):
        rules.append(_Rule("SUMMARIZATION", REQUEST, 0.85,
                           ("summary cue",), "asks for a summary"))
    if _has(lowered, "plan ", "itinerary", "schedule for", "organize my",
            "organise my", "trip plan", "help me plan"):
        rules.append(_Rule("PLANNING", REQUEST, 0.80,
                           ("planning cue",), "planning cue"))
    if _has(lowered, "explain", "how does", "how do ",
            "what does", "what is meant by", "walk me through"):
        rules.append(_Rule("EXPLANATION_REQUEST", QUESTION, 0.85,
                           ("explanation cue",), "asks for an explanation"))
    # Bare "why" is a weak generic cue: it wins alone but never forces a
    # rival downgrade against a specific frame (joke, comparison, ...).
    if _has(lowered, "why "):
        rules.append(_Rule("EXPLANATION_REQUEST", QUESTION, 0.85,
                           ("explanation cue",), "generic wh-word question"))
    # Explicit tell-me-about requests are information requests, not social
    # chat (0.80 keeps the cautious band: confident, no clarification).
    if _match_start(flat, r"(tell me about|tell us about|describe|give me (an overview|a rundown) of)\b"):
        rules.append(_Rule("INFORMATION_REQUEST", QUESTION, 0.80,
                           ("about-cue",), "explicit tell-me-about request"))
    if _has(lowered, "what do you think", "your opinion", "do you think",
            "in your opinion", "point of view"):
        rules.append(_Rule("OPINION_REQUEST", QUESTION, 0.80,
                           ("opinion cue",), "asks for Novi's opinion"))
    if _has(lowered, "let's talk about", "lets talk about",
            "changing the subject", "change the subject", "new topic",
            "something else entirely", "speaking of something else",
            "switch to", "switching to", "move on to", "talk about "):
        rules.append(_Rule("TOPIC_CHANGE", ASSERTION, 0.85,
                           ("topic-change cue",), "explicit topic change"))
    if _has(lowered, "what do you mean", "clarify", "be more specific",
            "which one do you mean", "can you repeat", "say that again",
            "i don't understand", "i dont understand", "confused"):
        rules.append(_Rule("CLARIFICATION", CLARIFICATION_QUESTION, 0.85,
                           ("clarification cue",),
                           "asks for clarification"))
    # Short reply to Novi's open question closes the slot (Step 1.5).
    # Interrogative-shaped turns are questions, not answers — without this,
    # a punctuationless voice follow-up ("What is its range") after Novi's
    # own question gets swallowed as a slot answer and goes unanswered.
    if (state.open_questions or state.last_novi_question) and len(words) <= 12 \
            and not stripped.endswith("?") and not is_question:
        rules.append(_Rule("CLARIFICATION", CLARIFICATION_ANSWER, 0.75,
                           ("open-question answer",),
                           "short reply to Novi's open question"))
    if _has(lowered, "i agree", "you're right", "you are right",
            "exactly right", "couldn't agree more", "fair point"):
        rules.append(_Rule("AGREEMENT", CONFIRMATION, 0.85,
                           ("agreement cue",), "agreement cue"))
    if _has(lowered, "i disagree", "don't agree", "do not agree",
            "that's not true", "not true", "i see it differently"):
        rules.append(_Rule("DISAGREEMENT", DISCONFIRMATION, 0.80,
                           ("disagreement cue",), "disagreement cue"))
    if _has(lowered, "thank", "thanks", "great job", "well done",
            "that helps", "that helped", "good answer", "awesome",
            "terrible answer", "bad answer", "not helpful",
            "wrong answer"):
        rules.append(_Rule("FEEDBACK", ASSERTION, 0.85,
                           ("feedback cue",), "feedback on Novi's answer"))
    if _has(lowered, "you are the best", "you're the best",
            "you are amazing", "you're amazing", "you are awesome",
            "you're awesome", "i love you", "so helpful"):
        rules.append(_Rule("FEEDBACK", ASSERTION, 0.90,
                           ("praise cue",), "praise for Novi"))
    if _has(lowered, "everything will be", "going to be ok",
            "going to be fine", "going to be alright",
            "reassure", "don't worry", "calm me down",
            "am i going to be"):
        rules.append(_Rule("REASSURANCE", QUESTION, 0.80,
                           ("reassurance cue",),
                           "seeks reassurance"))
    if _has(lowered, "i feel ", "i'm feeling", "im feeling",
            "i am sad", "i'm sad", "im sad", "i'm stressed",
            "i'm anxious", "i'm upset", "i'm lonely", "i'm depressed",
            "i'm scared", "i'm angry", "i feel lonely",
            "my dog died", "broke up", "lost my", "passed away",
            "that sounds awful", "i'm going through",
            "cheer me up", "comfort me"):
        rules.append(_Rule("EMOTIONAL_SUPPORT", EMPATHIC_TRIGGER, 0.85,
                           ("emotional cue",),
                           "emotional content needing empathy"))
    if _has(lowered, "i've been thinking", "ive been thinking",
            "looking back", "i realize", "i realised",
            "life is", "makes me wonder", "been reflecting"):
        rules.append(_Rule("REFLECTION", ASSERTION, 0.70,
                           ("reflection cue",), "reflective statement"))
    if _has(lowered, "how are you", "how's it going", "what's up",
            "whats up", "how are things", "nice weather",
            "how was your day"):
        rules.append(_Rule("SOCIAL_CHAT", QUESTION, 0.80,
                           ("social cue",), "social small talk"))
    # Implicit continuation of the live topic (Steps 1.4/2.1).
    if state.topic and (
            _has(lowered, "what about", "how about", "would that",
                 "is that", "does that", "what if")
            or _match_start(flat, r"and (the|what|is|are|does|do)\b")):
        rules.append(_Rule("FOLLOW_UP", QUESTION, 0.70,
                           ("follow-up cue",),
                           "implicit continuation of current topic"))
    # Bare wh-word follow-up ("Why?", "How?", "Which?") continues the active
    # subject (C-154): with a live entity/topic, a lone wh-word is not generic
    # small-talk — it asks about the thing just discussed. Classify it as an
    # explanation/information request so the planner answers on the subject
    # instead of deflecting. Without an active subject it stays a generic
    # question (the fallback below).
    active_entity = (getattr(state.anchor, "active_entity", "") or "").strip()
    if state.topic or active_entity:
        bare_wh = re.match(r"^(why|how|what|which|when|where|who)\s*\??$",
                           flat, re.IGNORECASE)
        if bare_wh:
            word = bare_wh.group(1).lower()
            label = ("EXPLANATION_REQUEST" if word in ("why", "how")
                     else "INFORMATION_REQUEST")
            rules.append(_Rule(label, QUESTION, 0.80,
                               ("bare wh-continuation",),
                               "bare wh-follow-up continues the active topic"))
    # Generic question shape -> information request (cautious band).
    # This is a fallback, never a rival interpretation (see classify).
    if is_question:
        rules.append(_Rule("INFORMATION_REQUEST", QUESTION, 0.80,
                           ("question shape",), "generic question shape"))
    return rules


def classify_intent(text: str, state: ConversationState) -> IntentResult:
    """Classify ``text`` into (intent, dialogue act, confidence).

    Deterministic and total: every input yields an ``IntentResult``.
    ``needs_clarification`` is set only when confidence falls below
    ``CLARIFY_THRESHOLD`` (0.60) *and* the ambiguity is material —
    competing cues fired, or nothing discriminating fired.
    """
    stripped = (text or "").strip()
    if not stripped:
        return IntentResult(intent="CLARIFICATION",
                            dialogue_act=CLARIFICATION_QUESTION,
                            confidence=0.40,
                            reason="empty input carries no intent",
                            needs_clarification=True)

    rules = _candidate_rules(stripped, state)
    if not rules:
        words = stripped.split()
        if len(words) <= 2:
            return IntentResult(
                intent="CLARIFICATION", dialogue_act=CLARIFICATION_QUESTION,
                confidence=0.45,
                reason="too short with no discriminating cues",
                needs_clarification=True)
        # A bare assertion asks nothing: per plan Step 2.3 clarification is
        # only owed when ambiguity affects the answer. Asking "which do you
        # mean?" about a statement is UNNECESSARY_CLARIFICATION.
        return IntentResult(
            intent="SOCIAL_CHAT", dialogue_act=ASSERTION, confidence=0.55,
            reason="statement with no discriminating cues",
            needs_clarification=False)

    top = rules[0]
    # Material ambiguity: a rival cue set fires at near-equal strength.
    # Generic fallbacks (question shape, bare wh-words) are not rival
    # interpretations — specific frames win over them outright. The
    # open-question-answer cue is the same kind of weak fallback: after Novi
    # asks "what else is on your mind?", a follow-up like "Recommend an
    # interior" or "Tell me about the Model Y" is its own request, not a slot
    # answer, and must not be demoted below the clarification bar (C-120/C-161).
    rival = next((r for r in rules[1:]
                  if r.reason not in ("generic question shape",
                                       "generic wh-word question",
                                       "short reply to Novi's open question")
                  and abs(r.confidence - top.confidence) <= 0.10
                  and r.intent != top.intent), None)
    if rival is not None:
        return IntentResult(
            intent=top.intent, dialogue_act=top.dialogue_act,
            confidence=min(top.confidence, 0.55),
            reason=(f"ambiguous between {top.intent} ({top.reason}) and "
                    f"{rival.intent} ({rival.reason})"),
            needs_clarification=True)
    return IntentResult(intent=top.intent, dialogue_act=top.dialogue_act,
                        confidence=top.confidence, reason=top.reason,
                        needs_clarification=False)
