"""Trained-adapter reply transport (plan 25, Part A — talk with the trained data).

Wires the plan-23/24 LoRA adapters (dialogue + emotional) into the brain's
reply path. The transport is ``llm_chat``-compatible — it can be passed to
``DialogueEngine.reply(llm_chat=...)`` and inherits the no-assistant /
no-repetition guardrails for free — but it renders the *training* prompt format
(situation + communicative act), not the system/user prompt, because that is
what the adapters were fine-tuned on.

The base model (Qwen3-8B) loads lazily once; each configured LoRA adapter
attaches via PEFT multi-adapter (``dialogue``, ``emotional``). Loading is
injectable so tests substitute a fake model. Any failure degrades to None so the
reply pipeline's deterministic fallback applies — the transport never raises
into cognition.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Callable

from .chat import _is_correction_like
from .dialogue import (
    _is_clarification,
    _is_continuation,
    _is_emotional_statement,
    _is_farewell,
    _is_greeting,
    _is_thanks,
)

_LOG = logging.getLogger(__name__)

# Emotional statement detectors (subset of the dialogue.py emotional bank).
_EMOTIONAL_DISTRESS = re.compile(
    r"\b(?:sad|down|depressed|stressed|anxious|overwhelmed|lonely|scared|nervous|"
    r"hopeless|exhausted|tired|upset|angry|frustrated|hurt|crying|miss|rough day|"
    r"hard time|struggling|not doing well)\b",
    re.IGNORECASE,
)
_EMOTIONAL_CELEBRATE = re.compile(
    r"\b(?:i got|i passed|i won|great news|good news|i did it|promoted|accepted|"
    r"engaged|pregnant|(?:i'?m|i am) (?:so happy|thrilled|excited|proud))\b",
    re.IGNORECASE,
)

# Qwen3 CoT blocks are line-delimited ("thinking\n...\n response\n") and appear
# at the start of the generated continuation, so the regex anchors "thinking" at
# the start of the text — it never over-matches prose like "I was thinking about
# your response".
_THINK_RE = re.compile(r"^\s*thinking\s*\n.*?\n\s*response", re.DOTALL)


def _strip_think(text: str) -> str:
    """Remove Qwen3 thinking CoT blocks (the adapters should not narrate).

    ``<think>`` tag blocks go first (shared helper); the legacy anchored
    ``thinking``/``response`` split below covers older verbose formats.
    """
    from .dialogue import _strip_think_blocks  # noqa: PLC0415 - keep module import light

    return _THINK_RE.sub("", _strip_think_blocks(text)).strip()


def derive_dialogue_act(user_says: str) -> str:
    """Map a user line to the plan-23 dialogue-act vocabulary.

    The dialogue adapter was fine-tuned on: CONTINUE, RESPOND, CLARIFY, REPAIR,
    COMMENT, INFORM, GREETING, SILENCE. Deterministic routing keeps the act
    explainable and testable. Farewells and thanks are outside the fine-tuned
    vocabulary, so they map to the nearest in-vocabulary acts (GREETING for a
    social close, RESPOND for an acknowledgment).
    """
    if _is_farewell(user_says):
        return "GREETING"
    if _is_greeting(user_says):
        return "GREETING"
    if _is_correction_like(user_says):
        return "REPAIR"
    if _is_clarification(user_says):
        return "CLARIFY"
    if _is_continuation(user_says):
        return "CONTINUE"
    if _is_thanks(user_says):
        return "RESPOND"
    return "RESPOND"


def derive_emotional_act(user_says: str) -> str:
    """Map a user line to the plan-24 emotional-act vocabulary.

    The emotional adapter was fine-tuned on: SILENCE, REPAIR, ACKNOWLEDGE,
    SUPPORT, GIVE_SPACE, APOLOGIZE, LISTEN, RESPOND, VALIDATE, CELEBRATE,
    CLARIFY, ENCOURAGE. A small deterministic subset covers the common cases.
    """
    if _is_correction_like(user_says):
        return "REPAIR"
    if _EMOTIONAL_CELEBRATE.search(user_says):
        return "CELEBRATE"
    if _EMOTIONAL_DISTRESS.search(user_says):
        return "SUPPORT"
    return "RESPOND"


def _affective_hypotheses(user_says: str) -> list[dict[str, Any]]:
    """Probabilistic affective hypotheses from the user line (plan 24 §25).

    The emotional signal is rendered as probabilistic context, not a fact —
    matching the training format.
    """
    if _EMOTIONAL_CELEBRATE.search(user_says):
        return [{"label": "positive_affect", "probability": 0.7}]
    if _EMOTIONAL_DISTRESS.search(user_says):
        return [{"label": "distress", "probability": 0.7}]
    return [{"label": "neutral", "probability": 0.5}]


def _compact_world(payload: dict[str, Any]) -> dict[str, Any]:
    """Compact world context for the training prompt (bounded, label-only)."""
    wc = payload.get("world_context") or {}
    if not isinstance(wc, dict):
        wc = {}
    entities = []
    for e in wc.get("visible_entities") or []:
        if isinstance(e, dict) and (e.get("label") or e.get("id")):
            entities.append(e.get("label") or e.get("id"))
    world: dict[str, Any] = {}
    if entities:
        world["perception"] = entities[:5]
    return world


def _compact_conversation(payload: dict[str, Any]) -> dict[str, Any]:
    """Recent conversation turns for the training prompt (bounded)."""
    history = payload.get("conversation_so_far") or []
    conv: dict[str, Any] = {}
    if history:
        conv["history"] = [
            str(h.get("content", ""))[:200]
            for h in history[-3:]
            if isinstance(h, dict) and h.get("content")
        ]
    return conv


def _conversation_phase(payload: dict[str, Any]) -> str:
    return "opening" if not (payload.get("conversation_so_far") or []) else "sustained"


def _user_goal(payload: dict[str, Any]) -> str:
    surroundings = payload.get("surroundings") or {}
    if not isinstance(surroundings, dict):
        surroundings = {}
    goal = surroundings.get("active_goal") or ""
    if goal:
        if isinstance(goal, dict):
            kind = goal.get("kind") or ""
            target = goal.get("target") or ""
            if isinstance(target, list):
                target = ", ".join(str(t) for t in target[:3])
            label = f"{kind}: {target}" if kind else str(target)
            return label[:80]
        return str(goal)[:80]
    user_says = payload.get("user_says") or ""
    if _EMOTIONAL_CELEBRATE.search(user_says):
        return "celebration"
    if _EMOTIONAL_DISTRESS.search(user_says):
        return "support"
    return ""


def build_dialogue_prompt(payload: dict[str, Any], act: str, system: str = "") -> str:
    """Build the plan-23 training prompt from the brain's user payload.

    Mirrors ``training.training.common.situation_to_prompt``: situation lines
    (person / world / conversation / memory / social) + ``Communicative act``.
    The brain's system guardrails are carried through as a bounded ``System``
    line so they are not silently discarded.
    """
    relationship = payload.get("relationship") or {}
    if not isinstance(relationship, dict):
        relationship = {}
    person = {
        "id": f"person:{relationship.get('name') or 'user'}",
        "relationship": relationship.get("tier", "unknown"),
    }
    world = _compact_world(payload)
    conversation = _compact_conversation(payload)
    memory = [{"summary": str(f)[:200]} for f in (payload.get("facts_i_know") or [])[:5]]
    social = {"engaged": True, "interruptibility": 1.0}
    parts = [f"Person: {person['id']} ({person['relationship']})"]
    if world:
        parts.append(f"World: {json.dumps(world, ensure_ascii=False)}")
    if conversation:
        parts.append(f"Conversation: {json.dumps(conversation, ensure_ascii=False)}")
    if memory:
        parts.append(f"Memory: {json.dumps(memory, ensure_ascii=False)}")
    parts.append(f"Social: {json.dumps(social, ensure_ascii=False)}")
    if system:
        parts.append(f"System: {system[:200]}")
    parts.append(f"Communicative act: {act}")
    return "\n".join(parts)


def build_emotional_prompt(payload: dict[str, Any], act: str, system: str = "") -> str:
    """Build the plan-24 training prompt from the brain's user payload.

    Mirrors ``training.training.common.emotional_situation_to_prompt``: social
    context lines + selected strategy as ``Communicative act``.
    """
    relationship = payload.get("relationship") or {}
    if not isinstance(relationship, dict):
        relationship = {}
    user_says = payload.get("user_says") or ""
    parts = [f"Relationship: {relationship.get('tier', 'unknown')}"]
    parts.append(f"Conversation phase: {_conversation_phase(payload)}")
    parts.append(f"User goal: {_user_goal(payload)}")
    parts.append(
        f"Affective hypotheses: {json.dumps(_affective_hypotheses(user_says), ensure_ascii=False)}"
    )
    parts.append(f"Novi caused problem: {str(_is_correction_like(user_says)).lower()}")
    parts.append("Interruptibility: 1.0")
    if system:
        parts.append(f"System: {system[:200]}")
    parts.append(f"Communicative act: {act}")
    return "\n".join(parts)


def _load_adapters(
    *,
    base_model: str,
    dialogue_adapter: str | None,
    emotional_adapter: str | None,
    device: str = "mps",
) -> tuple[Any, Any]:
    """Load the base model once and attach the configured LoRA adapters.

    Returns ``(model, tokenizer)``. Each configured adapter attaches under its
    own name (``dialogue`` / ``emotional``); the transport selects with
    ``set_adapter``. A single-adapter config attaches just that one.
    """
    from .third_party_quiet import quiet_third_party_startup_noise  # noqa: PLC0415

    quiet_third_party_startup_noise()
    import torch  # noqa: PLC0415
    from peft import PeftConfig, PeftModel  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

    # Validate the adapter ids FIRST: a typo'd path must fail here with the
    # path in the message — not after loading the multi-GB base model.
    for role, adapter in (("dialogue", dialogue_adapter), ("emotional", emotional_adapter)):
        if adapter:
            try:
                PeftConfig.from_pretrained(adapter)
            except Exception as exc:  # noqa: BLE001 - re-raised below with the path attached
                raise OSError(f"trained {role} adapter {adapter!r}: {exc}") from exc

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    try:
        # `dtype` is the supported spelling; `torch_dtype` warns on every
        # load in recent transformers.
        model = AutoModelForCausalLM.from_pretrained(base_model, dtype=torch.float16).to(device)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float16).to(device)
    if dialogue_adapter:
        model = PeftModel.from_pretrained(model, dialogue_adapter, adapter_name="dialogue")
    if emotional_adapter:
        if dialogue_adapter:
            model.load_adapter(emotional_adapter, adapter_name="emotional")
        else:
            model = PeftModel.from_pretrained(model, emotional_adapter, adapter_name="emotional")
    model.eval()
    return model, tokenizer


class TrainedReplyTransport:
    """``llm_chat``-compatible transport that renders replies via the trained adapters.

    Callable as ``transport(system=..., user=...)`` where ``user`` is the brain's
    JSON payload (``user_says``, ``facts_i_know``, ``conversation_so_far``,
    ``relationship``, ``world_context``, ...). Emotional statements route to the
    emotional adapter; everything else to the dialogue adapter. With only one
    adapter configured, all messages route to it.
    """

    def __init__(
        self,
        *,
        dialogue_adapter: str = "",
        emotional_adapter: str = "",
        base_model: str = "Qwen/Qwen3-8B",
        loader: Callable[..., Any] | None = None,
        device: str = "mps",
        max_new_tokens: int = 64,
        load_cooldown: float = 30.0,
    ) -> None:
        self.dialogue_adapter = dialogue_adapter
        self.emotional_adapter = emotional_adapter
        self.base_model = base_model
        self._loader = loader or _load_adapters
        self._device = device
        self.max_new_tokens = max_new_tokens
        self._model: Any | None = None
        self._tokenizer: Any | None = None
        self._load_error: str | None = None
        self._last_error: str | None = None
        self._load_attempted_at = 0.0
        self._load_cooldown = load_cooldown

    @property
    def load_error(self) -> str:
        return self._load_error or ""

    @property
    def last_error(self) -> str:
        return self._last_error or ""

    def _ensure_loaded(self) -> bool:
        if self._model is not None:
            return True
        now = time.time()
        # A failed load is expensive (full Qwen3-8B); back off rather than
        # retrying on every call while the model is unavailable.
        if self._load_error and now - self._load_attempted_at < self._load_cooldown:
            return False
        try:
            self._model, self._tokenizer = self._loader(
                base_model=self.base_model,
                dialogue_adapter=self.dialogue_adapter or None,
                emotional_adapter=self.emotional_adapter or None,
                device=self._device,
            )
            return True
        except Exception as exc:  # noqa: BLE001 - transport must never raise into cognition
            self._load_error = str(exc)
            self._load_attempted_at = now
            # LOUD failure: a broken adapter config otherwise degrades to the
            # deterministic fallbacks with no trace of why. Attempts are
            # already cooldown-throttled, so this cannot spam per message.
            _LOG.warning(
                "TrainedReplyTransport: model/adapter load failed "
                "(base=%s dialogue=%s emotional=%s): %s — "
                "replies fall back to deterministic until it loads",
                self.base_model,
                self.dialogue_adapter or "-",
                self.emotional_adapter or "-",
                exc,
            )
            return False

    def __call__(
        self, *, system: str, user: str, temperature: float = 0.5, timeout: int = 120
    ) -> str | None:
        if not self._ensure_loaded():
            return None
        try:
            payload = json.loads(user) if isinstance(user, str) else (user or {})
            if not isinstance(payload, dict):
                return None
            user_says = payload.get("user_says") or ""
            is_emotional = _is_emotional_statement(user_says) or bool(
                _EMOTIONAL_CELEBRATE.search(user_says)
            )
            use_emotional = bool(self.emotional_adapter) and (
                is_emotional or not self.dialogue_adapter
            )
            if use_emotional:
                act = derive_emotional_act(user_says)
                prompt = build_emotional_prompt(payload, act, system=system)
                adapter = "emotional"
            else:
                act = derive_dialogue_act(user_says)
                prompt = build_dialogue_prompt(payload, act, system=system)
                adapter = "dialogue"
        except Exception:  # noqa: BLE001 - malformed payloads degrade, never raise
            return None
        return self._generate(prompt, adapter, temperature)

    def _generate(self, prompt: str, adapter_name: str, temperature: float) -> str | None:
        """One generation pass through the selected adapter; None on any failure."""
        try:
            import torch  # noqa: PLC0415

            self._model.set_adapter(adapter_name)
            text = f"{prompt}\n<|im_start|>assistant\n"
            inp = self._tokenizer(text, return_tensors="pt")
            inp = {k: v.to(self._device) for k, v in inp.items()}
            with torch.no_grad():
                out = self._model.generate(
                    **inp,
                    max_new_tokens=self.max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id,
                )
            raw = self._tokenizer.decode(
                out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True
            ).strip()
            return _strip_think(raw) or None
        except Exception as exc:  # noqa: BLE001 - degrade to the deterministic fallback
            self._last_error = f"{adapter_name}: {exc}"
            _LOG.warning(
                "TrainedReplyTransport: generation via '%s' adapter failed: %s — falling back",
                adapter_name,
                exc,
            )
            return None
