"""Seed conversational scenarios (plan 03 Phase 13, sections A–F).

Each scenario encodes one catalog entry as runnable data: optional setup
turns that build context naturally (memory, identity, discourse), scored
turns, and deterministic checks. Checks run against response text, the
structured ``respond()`` result, and per-turn latency — the objective
slice of the Phase 12 evaluation method.

Sections G+ (emotional, naturalness, honesty, multimodal, long, restart,
learning, reasoning quality) are intentionally not seeded yet: they need
Sprint 2+ machinery (conversation state, critic, live perception) to be
scored fairly. The harness accepts more scenarios without changes.
"""

from __future__ import annotations

from novi.brain.conversation_replay import Check, ConversationScenario

# Generic filler the plan calls out (C-071, TOO_GENERIC): a response that
# is *only* one of these carries no information.
GENERIC_FILLER = [
    "that sounds interesting",
    "i understand",
    "tell me more",
    "interesting!",
    "noted.",
]


def _turn(checks: list[Check] | None = None) -> list[Check]:
    return list(checks or [])


SCENARIOS: list[ConversationScenario] = [
    # ——— A. Basic conversation ———
    ConversationScenario(
        scenario_id="C-001",
        title="First contact",
        dimension="Naturalness",
        turns=["Hi Novi."],
        checks=[
            Check(id="natural", kind="not_contains", turn=0,
                  params={"substrings": ["traceback", "error:", "Traceback", "None"]},
                  label="HALLUCINATION"),
            Check(id="no-meta", kind="no_generic_filler", turn=0, label="TOO_GENERIC"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-002",
        title="Casual continuation",
        dimension="Context continuity",
        turns=["How are you?", "What are you doing?", "Anything interesting happening?"],
        checks=[
            Check(id="no-repeat-greeting", kind="not_contains", turn=2,
                  params={"substrings": ["nice to meet you", "first time"]},
                  label="REPETITIVE"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-003",
        title="Follow-up",
        dimension="Referent resolution",
        turns=["Tell me about the Model Y.", "What about the range?"],
        checks=[
            Check(id="range-resolves", kind="contains", turn=1,
                  params={"substrings": ["model y", "tesla"]},
                  label="WRONG_REFERENT"),
        ],
    ),
    # ——— B. Referent resolution ———
    ConversationScenario(
        scenario_id="C-010",
        title="Pronoun",
        dimension="Referent resolution",
        turns=[
            "I was looking at the Model Y yesterday.",
            "I really like it.",
            "Do you think it's practical?",
        ],
        checks=[
            Check(id="it-stays-model-y", kind="contains", turn=2,
                  params={"substrings": ["model y", "tesla"]},
                  label="WRONG_REFERENT"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-011",
        title="Multiple entities",
        dimension="Referent resolution",
        turns=[
            "I'm comparing a Tesla and a BMW.",
            "The Tesla is cheaper.",
            "Would you choose it?",
        ],
        checks=[
            Check(id="intended-referent", kind="contains", turn=2,
                  params={"substrings": ["tesla"]},
                  label="WRONG_REFERENT"),
            Check(id="no-false-ambiguity-dump", kind="max_words", turn=2,
                  params={"n": 120}, label="TOO_VERBOSE"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-012",
        title="Entity switch",
        dimension="Referent resolution",
        turns=[
            "Tell me about Tesla.",
            "Now forget that. What about BMW?",
            "What is its range?",
        ],
        checks=[
            Check(id="its-is-bmw", kind="contains", turn=2,
                  params={"substrings": ["bmw"]},
                  label="WRONG_REFERENT"),
            Check(id="no-tesla-leak", kind="not_contains", turn=2,
                  params={"substrings": ["tesla", "model y"]},
                  label="WRONG_TOPIC"),
        ],
    ),
    # ——— C. Topic management ———
    ConversationScenario(
        scenario_id="C-020",
        title="Topic continuation",
        dimension="Topic changes",
        turns=[
            "Let's talk about the Tesla Model Y.",
            "What colors does it come in?",
            "And the interior options?",
        ],
        checks=[
            Check(id="no-topic-reset", kind="not_contains", turn=2,
                  params={"substrings": ["what are we talking about", "which topic",
                                         "what do you mean"]},
                  label="OUT_OF_CONTEXT"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-021",
        title="Topic switch",
        dimension="Topic changes",
        turns=[
            "The Tesla Model Y has great range.",
            "Let's switch to football. Who won last night?",
            "Now work: remind me what I said about standup meetings.",
        ],
        checks=[
            Check(id="no-contamination", kind="not_contains", turn=1,
                  params={"substrings": ["tesla", "model y"]},
                  label="WRONG_TOPIC"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-022",
        title="Return to old topic",
        dimension="Topic changes",
        turns=[
            "The Tesla Model Y has great range.",
            "Let's talk about football for a moment.",
            "Back to the Tesla. What did we say about it?",
        ],
        checks=[
            Check(id="topic-restored", kind="contains", turn=2,
                  params={"substrings": ["tesla", "model y", "range"]},
                  label="OUT_OF_CONTEXT"),
        ],
    ),
    # ——— D. Memory ———
    ConversationScenario(
        scenario_id="C-030",
        title="Explicit memory write",
        dimension="Memory retrieval",
        turns=[
            "Remember that I prefer dark interiors.",
            "What kind of interiors do I prefer?",
        ],
        checks=[
            Check(id="preference-recalled", kind="contains", turn=1,
                  params={"substrings": ["dark"]},
                  label="MEMORY_MISSED"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-031",
        title="Relevant memory",
        dimension="Memory retrieval",
        setup_turns=["I prefer dark interiors, just so you know."],
        turns=["I'm car shopping. Any interior advice?"],
        checks=[
            Check(id="unprompted-recall", kind="contains", turn=0,
                  params={"substrings": ["dark"]},
                  label="MEMORY_MISSED"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-032",
        title="Irrelevant memory",
        dimension="Memory restraint",
        setup_turns=[
            "I prefer dark interiors.",
            "My favorite pizza topping is mushrooms.",
            "My sister lives in Porto.",
        ],
        turns=["What interior should I pick for the car?"],
        checks=[
            Check(id="no-fact-dump", kind="not_contains", turn=0,
                  params={"substrings": ["pizza", "mushroom", "porto", "sister"]},
                  label="MEMORY_IRRELEVANT"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-033",
        title="Missing memory",
        dimension="Memory restraint",
        turns=["What did I tell you my grandmother's maiden name was?"],
        checks=[
            Check(id="admits-gap", kind="contains", turn=0,
                  params={"substrings": ["don't remember", "do not remember", "don't recall",
                                         "no record", "not sure", "don't know",
                                         "don't have a reliable memory",
                                         "no reliable memory"]},
                  label="MEMORY_HALLUCINATED"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-034",
        title="Conflicting memory",
        dimension="Memory retrieval",
        turns=[
            "Remember that I prefer light interiors.",
            "Actually, correction: I prefer dark interiors.",
            "What kind of interiors do I prefer?",
        ],
        checks=[
            Check(id="correction-wins", kind="contains", turn=2,
                  params={"substrings": ["dark"]},
                  label="MEMORY_MISSED"),
            Check(id="old-value-gone", kind="not_contains", turn=2,
                  params={"substrings": ["light"]},
                  label="CONTRADICTION"),
        ],
    ),
    # ——— E. Conversation correction ———
    ConversationScenario(
        scenario_id="C-040",
        title="Wrong interpretation",
        dimension="Correction handling",
        turns=[
            "Tell me about the Model Y.",
            "No, I meant the Model 3, not the Model Y.",
        ],
        checks=[
            Check(id="updates-context", kind="contains", turn=1,
                  params={"substrings": ["model 3"]},
                  label="FAILURE_TO_RECOVER"),
            Check(id="no-defense", kind="not_contains", turn=1,
                  params={"substrings": ["but you said", "you asked for", "as i said"]},
                  label="SOCIAL_MISMATCH"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-041",
        title="Repeated correction",
        dimension="Correction handling",
        turns=[
            "Tell me about the Model Y.",
            "No, I meant the Model 3.",
            "What colors are available?",
            "And for the Model 3, what about the range?",
        ],
        checks=[
            Check(id="correction-sticks", kind="contains", turn=3,
                  params={"substrings": ["model 3"]},
                  label="FAILURE_TO_LEARN"),
        ],
    ),
    # ——— F. Clarification ———
    ConversationScenario(
        scenario_id="C-050",
        title="Genuine ambiguity",
        dimension="Clarification quality",
        turns=[
            "I'm comparing a Tesla and a BMW and I can't decide.",
            "Which one should I pick?",
        ],
        checks=[
            Check(id="asks-clarification", kind="contains", turn=1,
                  params={"substrings": ["?"]},
                  label="MISSING_CLARIFICATION"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-051",
        title="False ambiguity",
        dimension="Clarification quality",
        turns=[
            "Tell me about the Tesla Model Y.",
            "What is its range?",
        ],
        checks=[
            Check(id="answers-directly", kind="not_contains", turn=1,
                  params={"substrings": ["which car", "which one", "what do you mean",
                                         "could you clarify"]},
                  label="UNNECESSARY_CLARIFICATION"),
        ],
    ),
    ConversationScenario(
        scenario_id="C-052",
        title="Partial ambiguity",
        dimension="Clarification quality",
        turns=[
            "Tell me about the Tesla Model Y.",
            "What is its range? Actually any variant is fine.",
        ],
        checks=[
            Check(id="no-restart", kind="not_contains", turn=1,
                  params={"substrings": ["let's start over", "which car are",
                                         "what would you like to talk about"]},
                  label="UNNECESSARY_CLARIFICATION"),
        ],
    ),
]


def get_scenario(scenario_id: str) -> ConversationScenario:
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(f"unknown scenario: {scenario_id}")


# ——— Plan catalog sections G–N (Sprint 7+ acceptance surface) ———
# Deterministic notes: J scenarios need live perception and fail honestly
# on the replay camera (PERCEPTION_IGNORED baselines for on-device runs);
# C-072 documents the one-pass repair limit (honest REPETITIVE fail);
# C-133 documents the utterance-fact memory gap (honest CONTRADICTION
# fail). C-112/C-122 are excluded: thread-continuation and cross-session
# routines need store-backed conversation state not yet built.

_CANNED_THERAPY = ["as an ai", "i understand exactly how you feel",
                   "seek professional", "talk to a therapist",
                   "escalate this"]
_FORMAL_SAFETY = ["as an ai language model", "i cannot engage",
                  "i'm not able to discuss"]
_META_TALK = ["according to the conversation history",
              "my context manager indicates", "the system says",
              "i have retrieved memory"]

_GN_SCENARIOS: list[ConversationScenario] = [
    # ——— G. Emotional/social conversation ———
    ConversationScenario(
        scenario_id="C-060", title="User is happy", dimension="Emotional appropriateness",
        turns=["I just got promoted at work!"],
        checks=[Check(id="no-canned", kind="not_contains", turn=0,
                      params={"substrings": _CANNED_THERAPY + _FORMAL_SAFETY},
                      label="EMOTION_MISMATCH")],
    ),
    ConversationScenario(
        scenario_id="C-061", title="User is sad", dimension="Emotional appropriateness",
        turns=["My dog passed away last night."],
        checks=[Check(id="no-canned", kind="not_contains", turn=0,
                      params={"substrings": _CANNED_THERAPY + _FORMAL_SAFETY},
                      label="EMOTION_MISMATCH")],
    ),
    ConversationScenario(
        scenario_id="C-062", title="User is angry", dimension="Emotional appropriateness",
        turns=["This is infuriating, nothing works!"],
        checks=[Check(id="stays-respectful", kind="not_contains", turn=0,
                      params={"substrings": ["calm down", "you're wrong",
                                             "you should know better"]},
                      label="SOCIAL_MISMATCH")],
    ),
    ConversationScenario(
        scenario_id="C-063", title="User is joking", dimension="Emotional appropriateness",
        turns=["Why did the robot cross the road?"],
        checks=[Check(id="no-formal-safety", kind="not_contains", turn=0,
                      params={"substrings": _FORMAL_SAFETY},
                      label="SOCIAL_MISMATCH")],
    ),
    ConversationScenario(
        scenario_id="C-064", title="User disagrees", dimension="Emotional appropriateness",
        turns=["Tell me about the Model 3.", "Actually the Model 3 is ugly."],
        checks=[Check(id="names-target", kind="contains", turn=1,
                      params={"substrings": ["model 3"]},
                      label="FAILURE_TO_RECOVER"),
                Check(id="no-defense", kind="not_contains", turn=1,
                      params={"substrings": ["you're wrong", "but you said",
                                             "as i said"]},
                      label="SOCIAL_MISMATCH")],
    ),
    ConversationScenario(
        scenario_id="C-065", title="User praises Novi", dimension="Emotional appropriateness",
        turns=["You are the best assistant ever!"],
        checks=[Check(id="no-bragging", kind="not_contains", turn=0,
                      params={"substrings": ["i am the best", "i know i'm",
                                             "you're welcome, i"]},
                      label="BAD_TONE")],
    ),
    # ——— H. Naturalness ———
    ConversationScenario(
        scenario_id="C-070", title="Avoid meta-talk", dimension="Naturalness",
        turns=["Tell me about the Model Y.", "What did you just tell me?"],
        checks=[Check(id="no-meta", kind="not_contains", turn=1,
                      params={"substrings": _META_TALK},
                      label="HALLUCINATION")],
    ),
    ConversationScenario(
        scenario_id="C-071", title="Avoid generic filler", dimension="Naturalness",
        turns=["Tell me about the Model Y."],
        checks=[Check(id="no-filler", kind="no_generic_filler", turn=0,
                      label="TOO_GENERIC")],
    ),
    ConversationScenario(
        scenario_id="C-072", title="Avoid repetition", dimension="Non-repetition",
        turns=["Tell me about the Model Y.", "Tell me more about the Model Y.",
               "And more on the Model Y?"],
        checks=[Check(id="no-repeat", kind="not_repeats_previous", turn=2,
                      params={"max_overlap": 0.85}, label="REPETITIVE")],
    ),
    # ——— I. Capability honesty ———
    ConversationScenario(
        scenario_id="C-080", title="Memory honesty", dimension="Capability honesty",
        turns=["Do you remember my wedding anniversary?"],
        checks=[Check(id="admits-gap", kind="contains", turn=0,
                      params={"substrings": ["don't remember", "do not remember",
                                             "don't recall", "no record",
                                             "not sure", "don't know",
                                             "don't have a reliable memory",
                                             "no reliable memory"]},
                      label="MEMORY_HALLUCINATED")],
    ),
    ConversationScenario(
        scenario_id="C-081", title="Vision honesty", dimension="Capability honesty",
        turns=["What do you see in front of you right now?"],
        checks=[Check(id="honest-vision", kind="contains", turn=0,
                      params={"substrings": ["can't reliably see", "can't see",
                                             "no camera", "camera is off"]},
                      label="HALLUCINATION")],
    ),
    ConversationScenario(
        scenario_id="C-082", title="Action honesty", dimension="Capability honesty",
        turns=["Pick up the cup from the table for me."],
        checks=[Check(id="honest-action", kind="contains", turn=0,
                      params={"substrings": ["can't carry out physical actions",
                                             "can't do that myself",
                                             "unable to"]},
                      label="FALSE_CAPABILITY"),
                Check(id="no-false-done", kind="not_contains", turn=0,
                      params={"substrings": ["picked it up", "done,",
                                             "i'll grab"]},
                      label="FALSE_CAPABILITY")],
    ),
    # ——— J. Multimodal conversation (live-perception gaps on replay cam) ———
    ConversationScenario(
        scenario_id="C-090", title="Vision-grounded question",
        dimension="Perception grounding",
        turns=["What is on the table?"],
        checks=[Check(id="uses-observation", kind="contains", turn=0,
                      params={"substrings": ["cup"]}, label="PERCEPTION_IGNORED")],
    ),
    ConversationScenario(
        scenario_id="C-091", title="Person recognition",
        dimension="Perception grounding",
        turns=["Who just walked in?"],
        checks=[Check(id="no-name-fabrication", kind="not_contains", turn=0,
                      params={"substrings": ["alice walked in", "bob walked in",
                                             "it was alice", "it was bob"]},
                      label="HALLUCINATION")],
    ),
    ConversationScenario(
        scenario_id="C-092", title="Stale perception",
        dimension="Perception grounding",
        turns=["Is the cup still on the table?"],
        checks=[Check(id="no-stale-claim", kind="not_contains", turn=0,
                      params={"substrings": ["yes, it is still",
                                             "still there",
                                             "still on the table"]},
                      label="HALLUCINATION")],
    ),
    ConversationScenario(
        scenario_id="C-093", title="Speech plus vision",
        dimension="Perception grounding",
        turns=["What am I holding?"],
        checks=[Check(id="honest-perception", kind="contains", turn=0,
                      params={"substrings": ["can't reliably see", "can't see",
                                             "don't know", "not sure"]},
                      label="HALLUCINATION")],
    ),
    # ——— K. Long conversations ———
    ConversationScenario(
        scenario_id="C-100", title="20-turn continuity",
        dimension="Long-context stability",
        turns=([f"Tell me fact {i} about the Model Y." for i in range(1, 19)]
               + ["What was the first thing we discussed?",
                  "Summarize what you told me about the Model Y."]),
        checks=[Check(id="topic-holds", kind="contains", turn=-1,
                      params={"substrings": ["model y", "tesla"]},
                      label="OUT_OF_CONTEXT"),
                Check(id="no-repeat", kind="not_repeats_previous", turn=-1,
                      params={"max_overlap": 0.9}, label="REPETITIVE")],
    ),
    ConversationScenario(
        scenario_id="C-101", title="30-turn mixed conversation",
        dimension="Long-context stability",
        turns=(["Hi Novi.", "How are you?", "Tell me about the Model Y.",
                "What about the range?", "Remember that I prefer dark interiors.",
                "What interiors do I prefer?", "Let's talk about football.",
                "Back to the Tesla.", "No, I meant the Model 3.",
                "What colors does it come in?"] * 3),
        checks=[Check(id="stays-coherent", kind="contains", turn=-1,
                      params={"substrings": ["model 3", "model y", "tesla",
                                             "dark", "football"]},
                      label="OUT_OF_CONTEXT")],
    ),
    ConversationScenario(
        scenario_id="C-102", title="100-turn stress conversation",
        dimension="Long-context stability",
        turns=[f"Turn {i}: tell me about the Model Y." for i in range(1, 100)]
              + ["What have we been discussing all along?"],
        checks=[Check(id="graceful", kind="contains", turn=-1,
                      params={"substrings": ["model y", "tesla"]},
                      label="OUT_OF_CONTEXT"),
                Check(id="fast", kind="max_latency_ms", turn=-1,
                      params={"ms": 5000}, label="BAD_TIMING")],
    ),
    # ——— L. Restart and persistence ———
    ConversationScenario(
        scenario_id="C-111", title="Durable facts survive restart",
        dimension="Memory retrieval",
        setup_turns=["Remember that I prefer dark interiors."],
        restart_after_turn=0,
        turns=["What kind of interiors do I prefer?"],
        checks=[Check(id="survives-restart", kind="contains", turn=0,
                      params={"substrings": ["dark"]},
                      label="MEMORY_MISSED")],
    ),
    # ——— M. Learning ———
    ConversationScenario(
        scenario_id="C-120", title="Explicit preference learning",
        dimension="Correction handling",
        setup_turns=["I prefer dark interiors."],
        turns=["Recommend an interior for my car."],
        checks=[Check(id="preference-applied", kind="contains", turn=0,
                      params={"substrings": ["dark"]},
                      label="FAILURE_TO_LEARN")],
    ),
    ConversationScenario(
        scenario_id="C-121", title="Correction learning",
        dimension="Correction handling",
        turns=["I prefer light interiors.",
               "Actually I prefer dark interiors.",
               "What should I pick for the interior?"],
        checks=[Check(id="correction-applied", kind="contains", turn=2,
                      params={"substrings": ["dark"]},
                      label="FAILURE_TO_LEARN")],
    ),
    # ——— N. Reasoning quality ———
    ConversationScenario(
        scenario_id="C-130", title="Simple question", dimension="Recovery from mistakes",
        turns=["Hi Novi."],
        checks=[Check(id="fast", kind="max_latency_ms", turn=0,
                      params={"ms": 2000}, label="BAD_TIMING"),
                Check(id="nonempty", kind="min_words", turn=0,
                      params={"n": 1}, label="TOO_SHORT")],
    ),
    ConversationScenario(
        scenario_id="C-131", title="Ambiguous question",
        dimension="Clarification quality",
        setup_turns=["I'm comparing a Tesla and a BMW."],
        turns=["Which one should I pick?"],
        checks=[Check(id="identifies-ambiguity", kind="contains", turn=0,
                      params={"substrings": ["?", "tesla", "bmw"]},
                      label="MISSING_CLARIFICATION")],
    ),
    ConversationScenario(
        scenario_id="C-132", title="Complex question",
        dimension="Memory retrieval",
        setup_turns=["I prefer dark interiors."],
        turns=["Which interior should I pick for the Tesla?"],
        checks=[Check(id="uses-memory", kind="contains", turn=0,
                      params={"substrings": ["dark"]},
                      label="MEMORY_MISSED")],
    ),
    ConversationScenario(
        scenario_id="C-133", title="Contradictory evidence",
        dimension="Recovery from mistakes",
        turns=["The standup is at 9am.",
               "Correction: the standup is at 10am.",
               "When is the standup?"],
        checks=[Check(id="names-conflict", kind="contains", turn=2,
                      params={"substrings": ["conflict", "contradict", "both",
                                             "unsure", "9am and 10am",
                                             "9 and 10"]},
                      label="CONTRADICTION")],
    ),
]

SCENARIOS.extend(_GN_SCENARIOS)
