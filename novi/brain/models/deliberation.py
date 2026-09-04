"""Multi-step LLM deliberation (Reasoning 3.0).

Replaces the single-shot conclusion→action LLM call with a bounded, structured
deliberation: the model explicitly reasons through ANALYSIS → OPTIONS → DECISION
before committing to one action. The deliberation trace is captured for
inspection, and the chosen action is re-validated against the allowlist so the
LLM can never authorize an unbounded action.

Boundaries:
  - Deliberation is bounded to a single structured call (no unbounded thinking).
  - The decision is validated against the fixed allowlist; an invalid or missing
    decision falls back to the safe default action.
  - Policy/Safety still gates every resulting action at execution time.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Sequence

from .reasoning import ActionIntent

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "nemotron-3.5-lightning"
DEFAULT_ALLOWED = frozenset({"inspect", "observe", "wait", "stop", "move_forward", "turn_left", "turn_right"})

# Documented fixed decision weights for the deliberative path (shared by the
# deterministic and LLM providers): maximize expected success, punish cost and
# risk. Module constants so traces can cite them; changing them is a deliberate
# auditable act, not a per-call tweak.
SUCCESS_WEIGHT = 0.5
COST_WEIGHT = 0.25
RISK_WEIGHT = 0.25

# Canonical per-action cost/risk budgets (0..1), shared with
# DeliberativeReasoningProvider as its base tables (that provider additionally
# applies user-correction bias on top; see correction_action_bias).
BASE_ACTION_COST = {
    "observe": 0.1,
    "wait": 0.05,
    "inspect": 0.15,
    "move_forward": 0.35,
    "turn_left": 0.25,
    "turn_right": 0.25,
}
BASE_ACTION_RISK = {
    "observe": 0.05,
    "wait": 0.02,
    "inspect": 0.1,
    "move_forward": 0.3,
    "turn_left": 0.2,
    "turn_right": 0.2,
}
DEFAULT_ACTION_COST = 0.2
DEFAULT_ACTION_RISK = 0.1


@dataclass(frozen=True)
class OptionScore:
    """Phase 3b: explicit alternative evaluation on three dimensions.

    - expected_success: probability (0..1) the option achieves its intent;
    - cost: resource/time budget (0..1);
    - risk: expected risk exposure (0..1).

    ``total`` is the weighted decision rule: maximize success, punish cost
    and risk. Deterministic and explainable.
    """

    action: str
    expected_success: float
    cost: float
    risk: float

    @staticmethod
    def _c(v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    def total(
        self,
        *,
        success_weight: float = SUCCESS_WEIGHT,
        cost_weight: float = COST_WEIGHT,
        risk_weight: float = RISK_WEIGHT,
    ) -> float:
        raw = (
            self._c(self.expected_success) * success_weight
            - self._c(self.cost) * cost_weight
            - self._c(self.risk) * risk_weight
        )
        return max(0.0, min(1.0, (raw + cost_weight + risk_weight) / (success_weight + cost_weight + risk_weight)))


class AlternativeEvaluator:
    """Phase 3b: explicit expected-success/cost/risk scoring of options.

    One evaluator per provider keeps weights fixed and auditable; ``select``
    returns ``(best_action, scores)`` with typed evidence for persistence.
    """

    def __init__(
        self,
        *,
        success_weight: float = SUCCESS_WEIGHT,
        cost_weight: float = COST_WEIGHT,
        risk_weight: float = RISK_WEIGHT,
    ) -> None:
        self.success_weight = float(success_weight)
        self.cost_weight = float(cost_weight)
        self.risk_weight = float(risk_weight)

    def select(self, options: Sequence[str], scores: dict[str, OptionScore], *, fallback: str = "observe") -> tuple[str, dict[str, OptionScore]]:
        """Argmax over weighted totals; deterministic tie-break on action name."""
        if not options:
            return fallback, dict(scores)
        known = {a: scores[a] for a in options if a in scores}
        if not known:
            return fallback, dict(scores)
        best = max(
            sorted(known),
            key=lambda a: (known[a].total(success_weight=self.success_weight, cost_weight=self.cost_weight, risk_weight=self.risk_weight), a),
        )
        return best, {a: known[a] for a in sorted(known)}


def deterministic_option_scores(
    success: dict[str, float],
    confidence: float,
    situation: dict[str, Any] | None,
) -> dict[str, OptionScore]:
    """Turn per-action success evidence into explicit success/cost/risk triples.

    Base scorer shared by the deterministic and LLM deliberative paths (same
    tables, same SUCCESS_WEIGHT/COST_WEIGHT/RISK_WEIGHT; the deterministic
    provider layers user-correction bias on top):

    - expected_success: accumulated evidence, gated by cognitive confidence
      (an uncertain world caps every option);
    - cost: declared per-action budget; repeating a just-FAILED action costs
      more (self-correction), and looking around is cheap;
    - risk: base exposure per action class, scaled up by uncertainty.
    """
    situation = situation or {}
    reflection = situation.get("reflection")
    c = max(0.0, min(1.0, float(confidence)))
    # Phase 4c (behavior link): a LEARNED routine whose pattern overlaps the
    # current situation raises the success evidence of the attention options.
    salient = {str(e).lower() for e in (situation.get("salient_entities") or [])}
    routine_boost = 0.0
    for pattern in situation.get("routines") or []:
        members = {str(m).lower() for m in (pattern or [])}
        if members & salient:
            routine_boost = max(routine_boost, 0.4)
    scored: dict[str, OptionScore] = {}
    for action, evidence in success.items():
        expected_success = max(0.0, min(1.0, evidence * (0.6 + 0.4 * c)))
        cost = BASE_ACTION_COST.get(action, DEFAULT_ACTION_COST)
        risk = min(1.0, BASE_ACTION_RISK.get(action, DEFAULT_ACTION_RISK) + (1.0 - c) * 0.2)
        if reflection and not reflection.get("effective", True) and str(reflection.get("action", "")) == action:
            # Repeating a just-failed action is expensive.
            cost = min(1.0, cost + 0.5)
            expected_success = max(0.0, expected_success - 0.2)
        if routine_boost and action in ("observe", "inspect"):
            expected_success = min(1.0, expected_success + routine_boost)
        scored[action] = OptionScore(action=action, expected_success=expected_success, cost=cost, risk=risk)
    return scored


def _deliberation_prompt(situation: dict[str, Any], recall: Any, allowed: frozenset[str]) -> str:
    allowed_list = ", ".join(sorted(allowed))
    return (
        "You are Novi's deliberative reasoner. Reason through multiple steps before choosing ONE action.\n"
        "Allowed actions: " + allowed_list + ".\n"
        "Situation: " + json.dumps(situation, sort_keys=True) + "\n"
        "Recalled memories: " + json.dumps(list(recall), sort_keys=True) + "\n"
        "Steps:\n"
        "1. ANALYSIS: briefly explain what is happening and what matters.\n"
        "2. OPTIONS: list 2-4 candidate actions from the allowed set with pros/cons.\n"
        "3. DECISION: choose the single best action.\n"
        'Respond ONLY with JSON: {"analysis": "...", "options": [{"action": "...", "pros": "...", "cons": "..."}], '
        '"decision": {"action": "...", "parameters": {"<key>": "<value>"}, "rationale": "..."}}'
    )


def _extract_json(text: str) -> dict[str, Any]:
    """Best-effort parse of the first JSON object in a model response."""
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    depth = 0
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


class DeliberativeLLMReasoningProvider:
    """Local LLM that deliberates (analysis → options → decision) before acting.

    Drop-in for ``OllamaReasoningProvider``: same ``decide`` signature, but the
    model is prompted to reason through multiple steps and the structured
    deliberation is captured on ``last_deliberation`` for the reasoning trace.

    Multi-round (Reasoning 3.2): after the initial decision the model critiques
    its own choice and either confirms it or revises it, up to ``max_rounds``
    total rounds. The loop is bounded and the final decision is re-validated
    against the allowlist.

    Explicit scoring: the model's pick is evidence, not the verdict. Every
    allowlisted candidate (options listed across rounds plus the final pick)
    is scored deterministically on expected-success/cost/risk under
    SUCCESS_WEIGHT/COST_WEIGHT/RISK_WEIGHT, the winner is the score argmax,
    and the scores persist on ``last_deliberation`` (and ``last_option_scores``)
    for the reasoning trace.
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        allowed_actions: frozenset[str] = DEFAULT_ALLOWED,
        default_action: str = "observe",
        max_rounds: int = 2,
        max_tokens: int = 600,
        timeout: float = 60,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.allowed_actions = allowed_actions
        self.default_action = default_action
        self.max_rounds = max(1, int(max_rounds))
        self.max_tokens = max(1, int(max_tokens))
        self.timeout = max(1.0, float(timeout))
        self.evaluator = AlternativeEvaluator(
            success_weight=SUCCESS_WEIGHT, cost_weight=COST_WEIGHT, risk_weight=RISK_WEIGHT
        )
        self.last_option_scores: dict[str, OptionScore] = {}
        self.last_deliberation: dict[str, Any] | None = None

    def decide(self, *, conclusion: str, confidence: float, situation: Any, recall: Any = ()) -> ActionIntent:
        situation = situation if isinstance(situation, dict) else {}
        raw = self._invoke(_deliberation_prompt(situation, recall, self.allowed_actions))
        deliberation = _extract_json(raw)
        decision = deliberation.get("decision") or {}
        rounds: list[dict[str, Any]] = [
            {
                "round": 1,
                "analysis": str(deliberation.get("analysis", "")),
                "options": list(deliberation.get("options", []) or []),
                "decision": decision,
            }
        ]
        # Self-critique rounds: the model evaluates its own decision and either
        # confirms it or revises it. Bounded by max_rounds.
        for r in range(2, self.max_rounds + 1):
            critique_raw = self._invoke(_critique_prompt(decision, situation, recall, self.allowed_actions))
            critique = _extract_json(critique_raw)
            confirmed = bool(critique.get("confirm", False))
            revised = critique.get("decision") or {}
            rounds.append(
                {
                    "round": r,
                    "evaluation": str(critique.get("evaluation", "")),
                    "confirm": confirmed,
                    "decision": revised,
                }
            )
            if confirmed:
                break
            if revised.get("action"):
                decision = revised

        llm_action = str(decision.get("action", ""))
        # Explicit option scoring on expected-success/cost/risk: every
        # allowlisted candidate the model listed (across rounds) plus its final
        # pick is scored deterministically; the winner is the score argmax, so
        # a riskier LLM pick loses to a safer-best alternative. An invalid or
        # missing decision falls back to the safe default action.
        candidates: list[str] = []
        for rnd in rounds:
            for opt in rnd.get("options", []) or []:
                if not isinstance(opt, dict):
                    continue
                name = str(opt.get("action", ""))
                if name in self.allowed_actions and name not in candidates:
                    candidates.append(name)
        if llm_action in self.allowed_actions and llm_action not in candidates:
            candidates.append(llm_action)
        # The model's endorsement is evidence (final pick 1.0, listed option
        # 0.7), gated by confidence; cost/risk tables and the just-failed
        # reflection penalty can still overturn it.
        evidence = {name: 0.7 for name in candidates}
        if llm_action in evidence:
            evidence[llm_action] = 1.0
        scored = deterministic_option_scores(evidence, confidence, situation) if candidates else {}
        if scored:
            action, self.last_option_scores = self.evaluator.select(
                sorted(scored), scored, fallback=self.default_action
            )
        else:
            action = self.default_action
            self.last_option_scores = {}
        if action == llm_action:
            parameters: dict[str, Any] = dict(decision.get("parameters", {}) or {})
        else:
            # Never apply parameters meant for a different (overruled) action.
            parameters = {}
        llm_rationale = str(decision.get("rationale", ""))
        self.last_deliberation = {
            "analysis": str(deliberation.get("analysis", "")),
            "options": list(deliberation.get("options", []) or []),
            "decision": {"action": action, "parameters": parameters, "rationale": llm_rationale},
            "rounds": rounds,
            "scores": {
                name: {
                    "action": name,
                    "expected_success": round(s.expected_success, 4),
                    "cost": round(s.cost, 4),
                    "risk": round(s.risk, 4),
                    "total": round(
                        s.total(
                            success_weight=self.evaluator.success_weight,
                            cost_weight=self.evaluator.cost_weight,
                            risk_weight=self.evaluator.risk_weight,
                        ),
                        4,
                    ),
                }
                for name, s in sorted(self.last_option_scores.items())
            },
            "weights": {
                "success": self.evaluator.success_weight,
                "cost": self.evaluator.cost_weight,
                "risk": self.evaluator.risk_weight,
            },
            "selected_by": "explicit_score:expected_success/cost/risk",
        }
        rationale = f"deliberated:{conclusion} -> {action} ({len(rounds)} rounds)"
        if llm_rationale:
            rationale += f" ({llm_rationale})"
        if action != llm_action and llm_action:
            rationale += f" [score_override:{llm_action}]"
        return ActionIntent(action=action, parameters=parameters, rationale=rationale)

    def _invoke(self, user_prompt: str) -> str:
        from novi.brain.models.ollama_reasoning import num_predict_for

        system = "You are Novi's bounded deliberative reasoner. Respond ONLY with the requested JSON."
        body: dict[str, Any] = {
            "model": self.model,
            "system": system,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {"num_predict": num_predict_for(self.model, self.max_tokens)},
        }
        # Deliberation is a structured JSON decision — always think:false (the
        # heavy-thinking tier would otherwise blow the 30s cap mid-thought).
        body["think"] = False
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        raw = data.get("response", "")
        if not (raw or "").strip():
            raw = data.get("thinking", "")
        return raw


def _critique_prompt(decision: dict[str, Any], situation: dict[str, Any], recall: Any, allowed: frozenset[str]) -> str:
    allowed_list = ", ".join(sorted(allowed))
    return (
        "You are Novi's deliberative reasoner. You proposed this decision:\n"
        + json.dumps(decision, sort_keys=True) + "\n"
        "Critically evaluate it against the situation. If it is sound, confirm it. "
        "If a better action from the allowed set exists, revise it.\n"
        "Allowed actions: " + allowed_list + ".\n"
        "Situation: " + json.dumps(situation, sort_keys=True) + "\n"
        'Respond ONLY with JSON: {"evaluation": "...", "confirm": true/false, '
        '"decision": {"action": "...", "parameters": {"<key>": "<value>"}, "rationale": "..."}}'
    )
