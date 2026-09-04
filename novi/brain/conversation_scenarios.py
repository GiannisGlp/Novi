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
                                         "no record", "not sure", "don't know"]},
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
