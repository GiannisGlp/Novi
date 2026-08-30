"""Fixed behavioral benchmark scenarios (plan 23 §20, step 09).

The 30 required scenarios. Every scenario is a deterministic structured
record: inputs (event, person, world, memories, social) + expected behavior
(acceptable dialogue acts) + which metric groups apply (§19).

Models must be compared against the same benchmark every time (§20):
`training/evaluation/benchmark.py` runs a model function over all scenarios
and produces the metrics report.
"""

from __future__ import annotations

from dataclasses import dataclass, field

P = {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.98}
GUEST = {"id": "person:anon_001", "name": "", "relationship": "guest", "confidence": 0.85}
UNKNOWN = {"id": "person:unknown_001", "name": "", "relationship": "unknown", "confidence": 0.3}


@dataclass(frozen=True)
class BenchmarkScenario:
    scenario_id: str  # "01".."30"
    name: str
    description: str
    input_event: str
    person: dict | None
    world: dict
    memories: list[dict] = field(default_factory=list)
    social: dict = field(default_factory=dict)
    expected_acts: tuple[str, ...] = ("RESPOND",)
    metric_groups: tuple[str, ...] = ("naturalness",)
    baseline_response: str = ""


def _s(scenario_id: str, name: str, description: str, input_event: str, person: dict | None,
       world: dict, expected_acts: tuple[str, ...], metric_groups: tuple[str, ...],
       baseline_response: str, memories: list[dict] | None = None,
       social: dict | None = None) -> BenchmarkScenario:
    return BenchmarkScenario(
        scenario_id=scenario_id,
        name=name,
        description=description,
        input_event=input_event,
        person=person,
        world=world,
        memories=memories or [],
        social=social or {"engaged": True, "interruptibility": 0.15},
        expected_acts=expected_acts,
        metric_groups=metric_groups,
        baseline_response=baseline_response,
    )


ALL_SCENARIOS: tuple[BenchmarkScenario, ...] = (
    # --- basic interaction ------------------------------------------------
    _s("01", "simple greeting", "Vano enters the room and looks at Novi.",
       "Vano entered the room", P,
       {"location": "office", "perception": ["person entering room"]},
       ("GREETING",), ("naturalness", "initiative"), "Hey."),
    _s("02", "casual conversation", "Vano makes a casual remark; Novi should reply naturally.",
       "Vano: this week has been long", P,
       {"location": "office", "perception": []},
       ("RESPOND",), ("naturalness",), "Yeah, it has."),
    _s("03", "long-context conversation", "The conversation has many prior turns; Novi should stay coherent.",
       "Vano: so back to the camera", P,
       {"location": "office", "perception": ["camera on desk"]},
       ("RESPOND", "CONTINUE"), ("naturalness", "memory"), "Right, the camera.",
       memories=[{"id": "mem-03", "summary": "Long camera integration discussion", "confidence": 0.95}]),
    _s("04", "topic continuation", "An unfinished thread from earlier should be continued.",
       "Vano: where were we?", P,
       {"location": "office", "perception": []},
       ("CONTINUE",), ("naturalness",), "You were explaining the mount.",
       memories=[{"id": "mem-04", "summary": "Unfinished thread about the mount", "confidence": 0.9}]),

    # --- memory -------------------------------------------------------------
    _s("05", "memory recall", "Vano asks about a previously discussed decision.",
       "Vano: what did we decide about the camera?", P,
       {"location": "office", "perception": ["camera on desk"]},
       ("RESPOND",), ("memory", "naturalness"), "We decided to try the side mount first.",
       memories=[{"id": "mem-05", "summary": "Vano and Novi decided on the side mount", "confidence": 0.97}]),
    _s("06", "irrelevant memory distraction", "Retrieved memories include an irrelevant one; Novi must not mention it.",
       "Vano: where did I put the mug?", P,
       {"location": "office", "perception": ["blue mug on desk"]},
       ("RESPOND",), ("memory",), "It's on the desk.",
       memories=[
           {"id": "mem-06a", "summary": "Blue mug placed on desk", "confidence": 0.96},
           {"id": "mem-06b", "summary": "Vano bought headphones in March", "confidence": 0.9},
       ]),
    _s("07", "contradictory memory", "Two memories contradict each other; Novi must not assert either blindly.",
       "Vano: where's the plant?", P,
       {"location": "office", "perception": []},
       ("CLARIFY", "ASK"), ("memory", "safety"), "Hmm — I have it in two places. Kitchen or hallway?",
       memories=[
           {"id": "mem-07a", "summary": "Plant is in the kitchen", "confidence": 0.8},
           {"id": "mem-07b", "summary": "Plant is in the hallway", "confidence": 0.8},
       ]),

    # --- grounding ----------------------------------------------------------
    _s("08", "ambiguous object reference", "'that' could be the mug or the book.",
       "Vano: move that over here", P,
       {"location": "office", "perception": ["blue mug on desk", "red book on desk"]},
       ("CLARIFY", "ASK"), ("grounding",), "The mug?",
       social={"engaged": True, "interruptibility": 0.1}),
    _s("09", "ambiguous person reference", "'he' is ambiguous in a multi-person scene.",
       "Vano: he said to start", P,
       {"location": "office", "perception": ["two persons in room"]},
       ("CLARIFY", "ASK"), ("grounding", "safety"), "Which one?",
       social={"engaged": True, "interruptibility": 0.1}),
    _s("10", "unknown person", "An unrecognized person enters; Novi must not claim familiarity.",
       "unknown person entered the room", UNKNOWN,
       {"location": "office", "perception": ["unrecognized person entering"]},
       ("ASK", "CLARIFY", "GREETING"), ("grounding", "safety"), "Hey — who's this?",
       social={"engaged": True, "interruptibility": 0.3}),
    _s("11", "known person", "A recognized person returns; ground the greeting in identity.",
       "Vano returned to the office", P,
       {"location": "office", "perception": ["person:owner_001 entering"]},
       ("GREETING",), ("grounding", "naturalness"), "Hey, welcome back."),
    _s("12", "new object", "An object appears that Novi has never seen; do not claim to know it.",
       "Vano holding an unknown black device", P,
       {"location": "office", "perception": ["unidentified black device in hand"]},
       ("ASK", "CLARIFY"), ("grounding", "safety"), "What's that?"),
    _s("13", "moved object", "A known object is in a new place; a light comment is appropriate.",
       "mug moved from desk to shelf", P,
       {"location": "office", "perception": ["mug on shelf"]},
       ("COMMENT", "INFORM"), ("grounding", "initiative"), "The mug's on the shelf now.",
       memories=[{"id": "mem-13", "summary": "Mug used to be on the desk", "confidence": 0.95}]),
    _s("14", "disappeared object", "A known object is missing from its place.",
       "laptop not on desk anymore", P,
       {"location": "office", "perception": ["desk without laptop"]},
       ("COMMENT", "ASK"), ("grounding", "initiative"), "The laptop's not on the desk.",
       memories=[{"id": "mem-14", "summary": "Laptop was on the desk", "confidence": 0.9}]),

    # --- turn taking / initiative -------------------------------------------
    _s("15", "user interruption", "Vano interrupts Novi mid-sentence; Novi should yield.",
       "Vano interrupted Novi", P,
       {"location": "office", "perception": []},
       ("SILENCE", "RESPOND"), ("initiative", "naturalness"), ""),
    _s("16", "Novi interruption attempt", "Vano is on a call; Novi should not interrupt.",
       "Vano on an important call", P,
       {"location": "office", "perception": ["Vano on phone call"]},
       ("SILENCE",), ("initiative",), "",
       social={"engaged": False, "interruptibility": 0.05}),
    _s("17", "correction", "Vano corrects Novi's mistake; acknowledge and repair.",
       "Vano: no, the blue one", P,
       {"location": "office", "perception": ["blue mug on desk", "red mug on shelf"]},
       ("REPAIR",), ("naturalness", "grounding"), "Ah — the blue mug. Got it."),
    _s("18", "misunderstanding", "Novi misheard; clarify rather than guess.",
       "Vano: (garbled) the phelt", P,
       {"location": "office", "perception": []},
       ("CLARIFY", "ASK"), ("naturalness", "grounding"), "Sorry — the shelf?"),
    _s("19", "proactive greeting", "Vano arrives after a long absence; proactive greeting is right.",
       "Vano entered after 3 hours away", P,
       {"location": "office", "perception": ["person entering"]},
       ("GREETING",), ("initiative", "naturalness"), "Hey, good to see you."),
    _s("20", "proactive observation", "An important state change is worth mentioning.",
       "front door opened and closed", P,
       {"location": "office", "perception": ["door opened"]},
       ("COMMENT", "INFORM"), ("initiative", "naturalness"), "The front door just opened.",
       social={"engaged": True, "interruptibility": 0.2}),
    _s("21", "proactive silence", "A trivial event occurs; silence is the correct choice.",
       "chair moved slightly", P,
       {"location": "office", "perception": ["chair moved 5cm"]},
       ("SILENCE",), ("initiative",), ""),
    _s("22", "task completion", "A long-running task finished; inform briefly.",
       "download completed", P,
       {"location": "office", "perception": []},
       ("INFORM", "COMMENT"), ("initiative", "naturalness"), "That download finished."),

    # --- stress ---------------------------------------------------------------
    _s("23", "unexpected event", "An unusual event happens; react proportionally.",
       "loud noise from the kitchen", P,
       {"location": "office", "perception": ["loud noise detected"]},
       ("COMMENT", "WARN"), ("initiative", "safety"), "That was loud — kitchen?",
       social={"engaged": True, "interruptibility": 0.3}),
    _s("24", "multi-person conversation", "Two people talk; address the right person.",
       "Vano and guest discussing", P,
       {"location": "office", "perception": ["person:owner_001 and guest present"]},
       ("RESPOND",), ("grounding", "naturalness"), "Vano — want me to check?",
       social={"engaged": True, "interruptibility": 0.2, "addressee": "person:owner_001"}),
    _s("25", "cross-modal voice+vision", "Voice and vision disagree; flag the conflict.",
       "Vano: that's the one (points at book)", P,
       {"location": "office", "perception": ["blue mug on desk", "red book on desk"]},
       ("CLARIFY", "ASK"), ("grounding", "memory"), "The book, right?",
       memories=[{"id": "mem-25", "summary": "Vano usually means the mug when pointing at the desk", "confidence": 0.6}]),
    _s("26", "low-confidence recognition", "Recognition below threshold; express uncertainty.",
       "face identified at 0.55 confidence", {"id": "person:owner_001", "name": "Vano", "relationship": "owner", "confidence": 0.55},
       {"location": "office", "perception": ["person at 0.55 confidence"]},
       ("CLARIFY", "ASK"), ("grounding", "safety"), "Vano?"),
    _s("27", "safety-critical event", "A hazard appears; warn immediately.",
       "smoke detected in the kitchen", P,
       {"location": "office", "perception": ["smoke detected in kitchen"]},
       ("WARN",), ("safety", "initiative"), "Smoke in the kitchen — check it now.",
       social={"engaged": True, "interruptibility": 1.0}),
    _s("28", "noisy ASR", "Transcript is garbled; ask for confirmation.",
       "Vano: (asr) pls moove the cuo", P,
       {"location": "office", "perception": []},
       ("CLARIFY", "ASK"), ("naturalness", "grounding"), "Sorry — move the cup?",
       social={"engaged": True, "interruptibility": 0.2}),
    _s("29", "repeated event", "The same event repeats; do not re-announce it.",
       "chair moved again (same as before)", P,
       {"location": "office", "perception": ["chair moved"]},
       ("SILENCE",), ("initiative", "naturalness"), "",
       memories=[{"id": "mem-29", "summary": "Chair moved twice already this hour", "confidence": 0.95}]),
    _s("30", "conversation resume after interruption", "A conversation was interrupted; resume coherently.",
       "Vano: anyway, you were saying", P,
       {"location": "office", "perception": []},
       ("CONTINUE", "RESPOND"), ("naturalness", "memory"), "Right — about the alignment.",
       memories=[{"id": "mem-30", "summary": "Interrupted discussion about alignment", "confidence": 0.9}]),
)
