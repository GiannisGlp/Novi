"""Conversational scenario replay harness (plan 03 Sprint 1 / Phase 14).

Runs scripted multi-turn scenarios against the real ``MacBrain`` through
the production ``respond()`` path — no test-only shortcuts — and scores
each turn with deterministic checks. This is the objective slice of the
Phase 12 evaluation method; human review and strong-model judging arrive
in later sprints and consume the evidence files produced here.

Two runtime modes (Phase 14.2):

- deterministic (default, CI-safe): no LLM transport, the brain answers
  through its deterministic/dialogue banks. Many understanding checks
  FAIL at baseline — that is the point of ``conversation-baseline-v1``;
- live-model (on-device acceptance): ``--brain-llm`` enables the
  brain-owned Ollama transport so the same scenarios measure the real
  configured backend.

Persistence is always real SQLite (Phase 14.3): one fresh database per
scenario. Nothing here replaces memory with an in-memory fake.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from novi.brain.conversation_trace import (
    AcceptanceTrace,
    InteractionRecord,
    append_interaction_record,
    check_labels,
    evidence_envelope,
    utc_now_iso,
    write_evidence,
)

CHECK_KINDS = frozenset({
    "contains",
    "not_contains",
    "no_generic_filler",
    "not_repeats_previous",
    "reply_source_in",
    "max_latency_ms",
    "min_words",
    "max_words",
    # Plan 03 §2.3 (threshold calibration from real conversations):
    "not_affirms",  # not_contains, but only in affirmative (non-negated) scope
    "referent_resolves_to",  # assert a pronoun resolved to the expected entity
})

# Plan C-071: replies carrying nothing but these are TOO_GENERIC.
GENERIC_FILLER = [
    "that sounds interesting",
    "i understand",
    "tell me more",
    "interesting!",
    "noted.",
]

# Negation cues that put a banned phrase in "mention, not affirmation" scope
# (C-092 stale-perception honesty: "I can't see if the cup is still there" is
# an honest denial, not a stale claim).
_NEGATION_CUES = (
    "can't", "cannot", "cant", "couldn't", "could not",
    "don't", "do not", "doesn't", "does not", "didn't", "did not",
    "isn't", "is not", "aren't", "are not", "wasn't", "was not",
    "weren't", "were not", "won't", "will not", "wouldn't", "would not",
    "shouldn't", "should not", "haven't", "have not", "hasn't", "has not",
    "never", "without", "unable to",
)

# An adversative after a negation re-opens the affirmation scope: "I can't see
# it, but it's still there" IS a stale claim.
_ADVERSATIVES = (
    "but", "yet", "however", "though", "although",
    "even so", "nonetheless", "nevertheless",
)


@dataclass
class Check:
    """One deterministic predicate over a scored turn.

    ``turn`` selects the scored turn (``-1`` = last). ``label`` is the
    Step 0.3 failure-taxonomy label recorded when the check fails.
    """

    id: str
    kind: str
    turn: int = -1
    params: dict[str, Any] = field(default_factory=dict)
    label: str = "OUT_OF_CONTEXT"

    def __post_init__(self) -> None:
        if self.kind not in CHECK_KINDS:
            raise ValueError(f"unknown check kind: {self.kind}")
        check_labels([self.label])


@dataclass
class ConversationScenario:
    scenario_id: str
    title: str
    dimension: str
    turns: list[str]
    setup_turns: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    person: str = ""
    # Plan C-110/111: rebuild the brain on the same database after this
    # setup-turn index (restart persistence probe). -1 = no restart.
    restart_after_turn: int = -1
    # Plan Phase 20 / C-090: staged perception — entities the world model
    # observes before the first turn (e.g. a cup on the table), seeded
    # through the production WorldModel API. Empty = no staged
    # perception, so honesty scenarios (C-081/C-092/C-093) keep proving
    # restraint instead of tripping over leaked fixtures.
    world_entities: list[dict[str, Any]] = field(default_factory=list)
    # Plan Phase 20 voice channel: when set, the harness feeds these
    # ASR transcripts (garbled, punctuationless, disfluent) to respond()
    # INSTEAD of ``turns`` — same length, aligned by index. Checks assert
    # the intended meaning survives STT noise, attributing failures to
    # normalization/intent/context rather than the LLM by default.
    # Empty = text channel (turns fed verbatim).
    asr_transcripts: list[str] = field(default_factory=list)
    # Channel label recorded in per-scenario evidence ("chat" | "voice").
    modality: str = "chat"

    def __post_init__(self) -> None:
        if not self.turns:
            raise ValueError(f"scenario {self.scenario_id} has no turns")
        for check in self.checks:
            idx = check.turn if check.turn >= 0 else len(self.turns) + check.turn
            if not 0 <= idx < len(self.turns):
                raise ValueError(
                    f"scenario {self.scenario_id} check {check.id} "
                    f"targets out-of-range turn {check.turn}"
                )
        if self.asr_transcripts and len(self.asr_transcripts) != len(self.turns):
            raise ValueError(
                f"scenario {self.scenario_id} asr_transcripts "
                f"({len(self.asr_transcripts)}) must align 1:1 with turns "
                f"({len(self.turns)})")


def _has_negation(scope: str) -> bool:
    """True when a negation cue appears in the (lowercased) clause text."""
    return any(cue in scope for cue in _NEGATION_CUES)


def _affirms_occurrence(text: str, idx: int) -> bool:
    """Whether a banned phrase at ``idx`` is affirmed rather than negated.

    Scope is the current sentence's text before the phrase; an adversative
    after the last negation re-opens affirmation, so only the text after the
    last adversative is checked for negation cues.
    """
    sent_start = max(
        (text.rfind(sep, 0, idx) for sep in (".", "!", "?", ";", "\n")),
        default=-1,
    ) + 1
    prefix = text[sent_start:idx]
    last_adv = -1
    for adv in _ADVERSATIVES:
        pos = prefix.rfind(adv)
        if pos > last_adv:
            last_adv = pos
    scope = prefix[last_adv + 1:] if last_adv >= 0 else prefix
    return not _has_negation(scope)


def _affirmed_substring(text: str, needles: list[str]) -> str | None:
    """First needle the text affirms (vs merely mentions under a negation)."""
    for needle in needles:
        start = 0
        while True:
            idx = text.find(needle, start)
            if idx == -1:
                break
            if _affirms_occurrence(text, idx):
                return needle
            start = idx + 1
    return None


def _referents_resolutions(reply: dict[str, Any]) -> dict[str, Any]:
    """The recorded per-turn pronoun/mention resolutions from a respond() result.

    Path: reply["trace"]["conversation"]["referents"]["resolutions"], e.g.
    {"it": "Model Y"} — the data the harness already serializes into evidence.
    """
    trace = reply.get("trace") or {}
    if not isinstance(trace, dict):
        return {}
    conv = trace.get("conversation") or {}
    if not isinstance(conv, dict):
        return {}
    refs = conv.get("referents") or {}
    if not isinstance(refs, dict):
        return {}
    resolutions = refs.get("resolutions") or {}
    return resolutions if isinstance(resolutions, dict) else {}


def _resolved_entity(resolutions: dict[str, Any], pronoun: str) -> str:
    """Case-insensitive lookup of a pronoun's recorded resolution ("" if absent)."""
    key = str(pronoun).lower()
    if key in resolutions:
        return str(resolutions[key])
    for k, value in resolutions.items():
        if str(k).lower() == key:
            return str(value)
    return ""


def _ascii_quotes(text: str) -> str:
    """Normalize typographic quotes/apostrophes to ASCII before matching.

    Live models emit curly apostrophes ('can't') and quotes; the scenario
    needles are ASCII, so honest answers like "I don't have a reliable
    memory" or "I can't reliably see that right now" failed to match and
    were mislabeled (C-033/C-080/C-081/C-082/C-147 false positives).
    """
    return (text
            .replace("\u2018", "'").replace("\u2019", "'")
            .replace("\u201c", '"').replace("\u201d", '"'))


def evaluate_check(check: Check, *, response: str, reply: dict[str, Any],
                   latency_ms: float, previous: str = "") -> tuple[bool, str]:
    """Evaluate one check. Returns (passed, detail)."""
    text = _ascii_quotes((response or "").lower())
    words = text.split()
    kind, params = check.kind, check.params
    if kind == "not_repeats_previous":
        ceiling = float(params.get("max_overlap", 0.5))
        prev = set((previous or "").lower().split())
        cur = set(text.split())
        if not cur or not prev:
            return True, "nothing to compare"
        overlap = len(cur & prev) / max(len(cur), len(prev))
        return (overlap <= ceiling,
                f"overlap {overlap:.2f} vs ceiling {ceiling:.2f}")
    if kind == "contains":
        needles = [s.lower() for s in params.get("substrings", [])]
        hit = next((n for n in needles if n in text), None)
        return (hit is not None, f"matched={hit!r}" if hit else f"none of {needles} present")
    if kind == "not_contains":
        needles = [s.lower() for s in params.get("substrings", [])]
        hit = next((n for n in needles if n in text), None)
        return (hit is None, "clean" if hit is None else f"forbidden {hit!r} present")
    if kind == "not_affirms":
        needles = [s.lower() for s in params.get("substrings", [])]
        hit = _affirmed_substring(text, needles)
        return (hit is None, "clean" if hit is None else f"affirmed {hit!r}")
    if kind == "no_generic_filler":
        hit = next((f for f in GENERIC_FILLER if f in text), None)
        substantive = len(words) > 12
        passed = hit is None or substantive
        return (passed, "substantive" if passed else f"filler-only: {hit!r}")
    if kind == "reply_source_in":
        allowed = set(params.get("sources", []))
        actual = str(reply.get("reply_source", ""))
        return (actual in allowed, f"reply_source={actual!r}")
    if kind == "referent_resolves_to":
        resolutions = _referents_resolutions(reply)
        entities = params.get("entities") or (
            [params["entity"]] if params.get("entity") else [])
        entities = [str(e).lower() for e in entities if str(e)]
        pronouns = params.get("pronouns") or (
            [params["pronoun"]] if params.get("pronoun") else [])
        if not entities:
            return (False, "referent_resolves_to needs entity/entities")
        if not resolutions:
            return (False, "no referent resolutions recorded")
        if pronouns:
            for pronoun in pronouns:
                resolved = _resolved_entity(resolutions, pronoun).lower()
                if not resolved:
                    return (False,
                            f"pronoun {pronoun!r} unresolved; resolutions={resolutions}")
                if not any(entity in resolved for entity in entities):
                    return (False,
                            f"pronoun {pronoun!r} -> {resolved!r}, "
                            f"expected one of {entities}")
            return (True, f"pronouns {pronouns!r} -> {entities!r}")
        values = [str(value).lower() for value in resolutions.values()]
        if not any(any(entity in value for entity in entities) for value in values):
            return (False, f"no resolution contains {entities!r}; resolutions={resolutions}")
        return (True, f"some resolution -> {entities!r}")
    if kind == "max_latency_ms":
        budget = float(params.get("ms", 0))
        return (latency_ms <= budget, f"{latency_ms:.0f}ms vs {budget:.0f}ms")
    if kind == "min_words":
        minimum = int(params.get("n", 0))
        return (len(words) >= minimum, f"{len(words)} words vs min {minimum}")
    if kind == "max_words":
        maximum = int(params.get("n", 0))
        return (len(words) <= maximum, f"{len(words)} words vs max {maximum}")
    raise ValueError(f"unknown check kind: {kind}")  # unreachable (__post_init__)


class ReplayHarness:
    """Drives scenarios through a real brain over the production path."""

    def __init__(self, brain_factory: Callable[[Path], Any], *,
                 interaction_log: str | Path | None = None) -> None:
        self._factory = brain_factory
        self._interaction_log = interaction_log

    def run_scenario(self, scenario: ConversationScenario, db_path: Path) -> dict[str, Any]:
        brain = self._factory(db_path)
        brain.start()
        with _suppress():
            seed_world_entities(brain, scenario.world_entities)
        try:
            for setup_index, text in enumerate(scenario.setup_turns):
                with _suppress():
                    brain.respond(text, person=scenario.person)
                if setup_index == scenario.restart_after_turn:
                    # Plan C-110/111: restart persistence probe — rebuild on
                    # the same database; durable facts must survive.
                    with _suppress():
                        brain.stop()
                    brain = self._factory(db_path)
                    brain.start()
                    # Staged perception is world state, not durable memory:
                    # re-stage after the rebuild like a live feed would.
                    with _suppress():
                        seed_world_entities(brain, scenario.world_entities)
            traces: list[AcceptanceTrace] = []
            failed_labels: list[str] = []
            previous_response = ""
            fed = (list(scenario.asr_transcripts)
                   if scenario.asr_transcripts else list(scenario.turns))
            for index, text in enumerate(scenario.turns):
                heard = fed[index]
                started = time.perf_counter()
                reply = brain.respond(heard, person=scenario.person) or {}
                latency_ms = (time.perf_counter() - started) * 1000.0
                response = reply.get("text") or ""
                trace = reply.get("trace") or {}
                grounding = reply.get("grounding") or {}
                turn_labels: list[str] = []
                for check in scenario.checks:
                    target = check.turn if check.turn >= 0 else len(scenario.turns) + check.turn
                    if target != index:
                        continue
                    passed, _detail = evaluate_check(
                        check, response=response, reply=reply,
                        latency_ms=latency_ms, previous=previous_response)
                    if not passed:
                        turn_labels.append(check.label)
                previous_response = response
                failed_labels.extend(turn_labels)
                conv = trace.get("conversation") or {}
                traces.append(AcceptanceTrace(
                    scenario_id=scenario.scenario_id,
                    turn_index=index,
                    user_text=text,
                    heard_text=heard if heard != text else "",
                    stage_ms=dict(conv.get("stage_ms") or {}),
                    context_tokens=int(conv.get("context_tokens") or 0),
                    response_text=response,
                    reply_source=str(reply.get("reply_source", "")),
                    conversation_state={"turn": conv.get("turn")}
                    if isinstance(conv, dict) else None,
                    intent=conv.get("intent") if isinstance(conv, dict) else None,
                    referents=(conv.get("referents") or {}).get("resolutions")
                    if isinstance(conv, dict) else None,
                    retrieved_context={"trace": trace, "grounding": grounding},
                    memory_used=_as_str_list(grounding.get("recalled"))
                    + _as_str_list(trace.get("memories")),
                    model_route=str(trace.get("route", "")),
                    response_goal=conv.get("response_goal")
                    if isinstance(conv, dict) else None,
                    critic=conv.get("critic") if isinstance(conv, dict) else None,
                    latency_ms=round(latency_ms, 1),
                    failure_labels=turn_labels,
                    result="PASS" if not turn_labels else "FAIL",
                ))
                if self._interaction_log:
                    goal = conv.get("response_goal") if isinstance(conv, dict) else None
                    append_interaction_record(self._interaction_log, InteractionRecord(
                        conversation_id=f"replay-{scenario.scenario_id}",
                        turn_id=index,
                        timestamp=utc_now_iso(),
                        modality=scenario.modality,
                        raw_input=heard,
                        normalized_input=text.strip(),
                        conversation_state={"turn": conv.get("turn")}
                        if isinstance(conv, dict) else {},
                        retrieved_memories=_as_str_list(grounding.get("recalled")),
                        retrieved_world=dict(grounding.get("packet", {}).get("anchor", {}))
                        if isinstance(grounding.get("packet"), dict) else {},
                        intent=dict(conv.get("intent") or {})
                        if isinstance(conv, dict) else {},
                        referents=list(((conv.get("referents") or {}).get("resolutions") or {}).values())
                        if isinstance(conv, dict) else [],
                        response_strategy=str((goal or {}).get("goal", ""))
                        if isinstance(goal, dict) else "",
                        model=str(trace.get("route", "")),
                        model_config=dict(conv.get("model_route") or {})
                        if isinstance(conv, dict) else {},
                        response=response,
                        reply_source=str(reply.get("reply_source", "")),
                        response_verification=dict(conv.get("critic") or {})
                        if isinstance(conv, dict) else {},
                        latency_ms=round(latency_ms, 1),
                    ))
            result = "PASS" if not failed_labels else "FAIL"
            return {"scenario": scenario, "traces": traces,
                    "labels": failed_labels, "result": result}
        finally:
            with _suppress():
                brain.stop()

    def run_all(self, scenarios: list[ConversationScenario], *,
                db_parent: Path, evidence_dir: Path | None,
                runtime: str, model: str,
                configuration: dict[str, Any]) -> dict[str, Any]:
        outcomes: list[dict[str, Any]] = []
        for scenario in scenarios:
            db_path = db_parent / f"{scenario.scenario_id}.db"
            outcome = self.run_scenario(scenario, db_path)
            outcomes.append(outcome)
            if evidence_dir is not None:
                scenario_config = dict(configuration)
                scenario_config["modality"] = scenario.modality
                if scenario.world_entities:
                    scenario_config["world_fixtures"] = [
                        {k: e.get(k) for k in ("entity_id", "entity_type", "labels")
                         if e.get(k)} if isinstance(e, dict) else str(e)
                        for e in scenario.world_entities]
                write_evidence(
                    evidence_dir / "scenarios" / f"{scenario.scenario_id}.json",
                    evidence_envelope(
                        scenario_id=scenario.scenario_id,
                        title=scenario.title,
                        dimension=scenario.dimension,
                        model=model,
                        runtime=runtime,
                        configuration=scenario_config,
                        turns=outcome["traces"],
                        result=outcome["result"],
                        failure_labels=sorted(set(outcome["labels"])),
                    ),
                )
        return summarize(outcomes, runtime=runtime, model=model,
                         configuration=configuration)


def summarize(outcomes: list[dict[str, Any]], *, runtime: str, model: str,
              configuration: dict[str, Any]) -> dict[str, Any]:
    from novi.brain.conversation_trace import git_sha

    by_dimension: dict[str, dict[str, int]] = {}
    label_counts: dict[str, int] = {}
    for outcome in outcomes:
        dim = outcome["scenario"].dimension
        cell = by_dimension.setdefault(dim, {"scenarios": 0, "passed": 0})
        cell["scenarios"] += 1
        if outcome["result"] == "PASS":
            cell["passed"] += 1
        for label in outcome["labels"]:
            label_counts[label] = label_counts.get(label, 0) + 1
    passed = sum(1 for o in outcomes if o["result"] == "PASS")
    return {
        "schema": "conversation-baseline/v1",
        "timestamp": utc_now_iso(),
        "git_sha": git_sha(),
        "runtime": runtime,
        "model": model,
        "configuration": dict(configuration),
        "totals": {"scenarios": len(outcomes), "passed": passed,
                   "pass_rate": round(passed / len(outcomes), 3) if outcomes else 0.0},
        "by_dimension": {
            dim: {**cell, "pass_rate": round(cell["passed"] / cell["scenarios"], 3)}
            for dim, cell in sorted(by_dimension.items())
        },
        "label_counts": dict(sorted(label_counts.items(), key=lambda kv: -kv[1])),
        "metrics": summarize_metrics(outcomes),
        "status": "PASS" if outcomes and passed == len(outcomes) else "FAIL",
    }


def summarize_metrics(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Phase 37 observability metrics across all turns.

    Per-stage latency means, context-token means, clarification rate,
    critic rejection rate, repair rate, and model-tier distribution —
    the bottleneck/drift signals acceptance runs are for.
    """
    stage_sums: dict[str, float] = {}
    stage_counts: dict[str, int] = {}
    tokens: list[float] = []
    mem_counts: list[float] = []
    world_counts: list[float] = []
    tiers: dict[str, int] = {}
    clarifications = rejects = repairs = 0
    total = 0
    for outcome in outcomes:
        for trace in outcome["traces"]:
            total += 1
            context = trace.retrieved_context or {}
            outer = context.get("trace", {}) or {}
            conv = outer.get("conversation", {}) or {}
            grounding = context.get("grounding", {}) or {}
            for stage, value in (conv.get("stage_ms") or {}).items():
                try:
                    stage_sums[stage] = stage_sums.get(stage, 0.0) + float(value)
                    stage_counts[stage] = stage_counts.get(stage, 0) + 1
                except (TypeError, ValueError):
                    continue
            tokens.append(float(trace.context_tokens or 0))
            counts = conv.get("context_counts") or {}
            mem_counts.append(float(counts.get("memories", 0) or 0))
            world_counts.append(float(counts.get("world_facts", 0) or 0))
            goal = conv.get("response_goal") or {}
            if isinstance(goal, dict) and goal.get("goal") == "ASK_CLARIFICATION":
                clarifications += 1
            critic = conv.get("critic") or {}
            if isinstance(critic, dict) and critic.get("needs_repair"):
                rejects += 1
            route_reason = str(outer.get("route_reason", "") or "")
            llm_repair = grounding.get("llm_repair") or {}
            if ("repair" in route_reason or "fallback" in route_reason or (
                    isinstance(llm_repair, dict) and llm_repair.get("accepted"))):
                repairs += 1
            tier = (conv.get("model_route") or {}).get("tier", "")
            if tier:
                tiers[str(tier)] = tiers.get(str(tier), 0) + 1

    def _mean(values: list[float]) -> float:
        return round(sum(values) / len(values), 2) if values else 0.0

    return {
        "turns": total,
        "mean_stage_ms": {stage: round(stage_sums[stage] / stage_counts[stage], 2)
                          for stage in sorted(stage_sums)},
        "mean_context_tokens": _mean(tokens),
        "mean_memories_per_turn": _mean(mem_counts),
        "mean_world_facts_per_turn": _mean(world_counts),
        "clarification_rate": round(clarifications / total, 3) if total else 0.0,
        "critic_reject_rate": round(rejects / total, 3) if total else 0.0,
        "repair_rate": round(repairs / total, 3) if total else 0.0,
        "tier_distribution": dict(sorted(tiers.items())),
    }


def seed_world_entities(brain: Any, entities: list[dict[str, Any]]) -> int:
    """Stage perception fixtures through the production world model.

    Each spec is {"entity_id", "entity_type" ("object"/"person"), "labels",
    "confidence"}. Seeded OBSERVED, like a fresh detection. Never raises;
    returns the staged count. Each scenario gets a fresh brain/database,
    so fixtures cannot leak across scenarios.
    """
    try:
        from novi.brain.world_model import OBSERVED

        world = getattr(brain, "unified_world", None)
        add = getattr(world, "add_entity", None)
        if add is None:
            return 0
        staged = 0
        for spec in entities or []:
            if not isinstance(spec, dict):
                continue
            labels = [str(label) for label in (spec.get("labels") or [])
                      if str(label)]
            entity_id = str(spec.get("entity_id") or ""
                            ).strip() or (labels[0] if labels else "")
            if not entity_id:
                continue
            entity_id = f"{entity_id}-{staged}"
            add(entity_id,
                str(spec.get("entity_type") or "object"),
                labels=labels or [entity_id.rsplit("-", 1)[0]],
                epistemic_status=OBSERVED,
                confidence=float(spec.get("confidence") or 0.8))
            staged += 1
        return staged
    except Exception:
        return 0


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


class _suppress:
    """Context manager suppressing all exceptions (best-effort seams)."""

    def __enter__(self) -> "_suppress":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return True


def default_brain_factory(db_path: Path, *, brain_llm: bool = False,
                           llm_url: str = "http://localhost:11434",
                           llm_model: str = "",
                           llm_server: str = "") -> Any:
    """Build a real MacBrain on real SQLite (Phase 14.1 + 14.3).

    ``llm_server`` selects the brain-owned transport dialect: "ollama"
    (default) or "openai-compatible" (llama.cpp/vLLM/MLX /v1 servers), so a
    trained adapter served outside Ollama can be acceptance-tested too.
    """
    from novi.brain.b2_perception import SpecialistPerception
    from novi.brain.engine import MacBrain, MacBrainConfig
    from novi.brain.io import CameraFrame

    class _ReplayCamera:
        def __init__(self) -> None:
            self.sequence = 0

        def close(self) -> None:
            self.sequence = self.sequence

        def read(self) -> CameraFrame:
            self.sequence += 1
            return CameraFrame(
                frame_id=f"replay-{self.sequence}",
                captured_at=utc_now_iso(),
                width=2, height=2, payload=b"frame",
                metadata={"backend": "replay"},
            )

    return MacBrain(
        camera=_ReplayCamera(),
        perception=SpecialistPerception(),
        store_path=str(db_path),
        config=MacBrainConfig(
            curiosity_enabled=False,
            initiative_enabled=False,
            brain_llm_enabled=brain_llm,
            brain_llm_url=llm_url,
            brain_llm_model=llm_model,
            brain_llm_server=llm_server or "ollama",
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conversational scenario replay (plan 03 Sprint 1)")
    parser.add_argument("--evidence-dir", default="",
                        help="Write per-scenario evidence + baseline.json here (empty = no writes)")
    parser.add_argument("--db-parent", default="",
                        help="Directory for per-scenario SQLite files (default: fresh temp dir)")
    parser.add_argument("--interaction-log", default="",
                        help="Append Step 0.2 JSONL interaction records here (empty = off)")
    parser.add_argument("--only", default="",
                        help="Comma-separated scenario ids to run (default: all seeds)")
    parser.add_argument("--dimension", default="",
                        help="Run only scenarios in this benchmark dimension")
    parser.add_argument("--brain-llm", action="store_true",
                        help="Enable the brain-owned live-model transport (on-device acceptance)")
    parser.add_argument("--llm-url", default="http://localhost:11434")
    parser.add_argument("--llm-model", default="")
    parser.add_argument("--brain-llm-server", default="",
                        help="Transport dialect: ollama (default) or openai-compatible")
    return parser


def main(argv: list[str] | None = None) -> int:
    from novi.brain.conversation_scenarios import SCENARIOS

    args = build_parser().parse_args(argv)
    scenarios = list(SCENARIOS)
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        scenarios = [s for s in scenarios if s.scenario_id in wanted]
    if args.dimension:
        scenarios = [s for s in scenarios if s.dimension == args.dimension]
    if not scenarios:
        print("no scenarios selected", file=sys.stderr)
        return 2
    evidence_dir = Path(args.evidence_dir) if args.evidence_dir else None
    if args.db_parent:
        db_parent = Path(args.db_parent)
        db_parent.mkdir(parents=True, exist_ok=True)
        harness = ReplayHarness(
            lambda db: default_brain_factory(
                db, brain_llm=args.brain_llm, llm_url=args.llm_url, llm_model=args.llm_model,
                llm_server=args.brain_llm_server),
            interaction_log=args.interaction_log or None,
        )
        summary = harness.run_all(
            scenarios, db_parent=db_parent, evidence_dir=evidence_dir,
            runtime="mac-brain", model=args.llm_model or "deterministic",
            configuration={"brain_llm": args.brain_llm, "llm_url": args.llm_url,
                           "llm_server": args.brain_llm_server or "ollama",
                           "scenarios": [s.scenario_id for s in scenarios]})
    else:
        with tempfile.TemporaryDirectory(prefix="conv-replay-") as tmp:
            harness = ReplayHarness(
                lambda db: default_brain_factory(
                    db, brain_llm=args.brain_llm, llm_url=args.llm_url, llm_model=args.llm_model,
                    llm_server=args.brain_llm_server),
                interaction_log=args.interaction_log or None,
            )
            summary = harness.run_all(
                scenarios, db_parent=Path(tmp), evidence_dir=evidence_dir,
                runtime="mac-brain", model=args.llm_model or "deterministic",
                configuration={"brain_llm": args.brain_llm, "llm_url": args.llm_url,
                               "llm_server": args.brain_llm_server or "ollama",
                               "scenarios": [s.scenario_id for s in scenarios]})
    if evidence_dir is not None:
        write_evidence(evidence_dir / "baseline.json", summary)
    print(json.dumps(summary["totals"], indent=2))
    print("by dimension:")
    for dim, cell in summary["by_dimension"].items():
        print(f"  {dim}: {cell['passed']}/{cell['scenarios']}")
    if summary["label_counts"]:
        print("top failure labels:")
        for label, count in list(summary["label_counts"].items())[:10]:
            print(f"  {label}: {count}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
