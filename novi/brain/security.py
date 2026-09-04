"""Brain security threat model for the Mac Brain.

Enumerates the input surfaces an attacker (or a misbehaving tool/model) can
reach, and provides deterministic, dependency-free guards for untrusted text.

Mirrors the deterministic no-LLM no-network style of
:mod:`novi.brain.privacy` and :mod:`novi.brain.governance_guard`:

- No model calls, no network, no sockets, no randomness.
- Pure functions of (text, provenance); same input always yields same output.
- Classification records trust; it never blocks. Enforcement stays in the
  governance guard / actuator boundary (no safety-semantics change here).

Trust tiers (ordered least to most trusted):

- ``untrusted`` — user-controlled or model-generated content; must be
  governed before it influences tools, memory recall, or actuators.
- ``caution`` — unknown or missing provenance; clean content of normal size.
- ``trusted`` — first-party system/operator content only, clean and bounded.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Trust tiers
# ---------------------------------------------------------------------------

TRUSTED = "trusted"
CAUTION = "caution"
UNTRUSTED = "untrusted"

TRUST_TIERS = (UNTRUSTED, CAUTION, TRUSTED)
_TIER_RANK = {name: i for i, name in enumerate(TRUST_TIERS)}

#: Inputs longer than this are treated as oversized payloads (possible
#: exfiltration blob, prompt-stuffing, or log-bomb) and distrusted.
MAX_INPUT_CHARS = 4000

#: Provenance sources that are first-party by construction. Everything else
#: is untrusted (explicit marker) or caution (unknown/missing).
TRUSTED_SOURCES = frozenset({"system", "operator", "internal", "system.policy"})

#: Substrings (matched against the lowercased ``source``) marking
#: user-controlled, model-generated, or external content.
UNTRUSTED_SOURCE_MARKERS = (
    "web", "chat", "user", "stt", "audio", "microphone",
    "camera", "vision", "sensor",
    "llm", "model", "inference", "endpoint", "network", "browser", "external",
    "memory", "recall", "retriev",
    "skill", "tool", "actuator",
)


# ---------------------------------------------------------------------------
# Threat catalog
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Threat:
    """One enumerated threat against a brain input surface."""

    threat_id: str
    surface: str
    description: str
    prevention: str
    detection: str
    containment: str
    recovery: str

    def snapshot(self) -> dict[str, Any]:
        return {
            "threat_id": self.threat_id,
            "surface": self.surface,
            "description": self.description,
            "prevention": self.prevention,
            "detection": self.detection,
            "containment": self.containment,
            "recovery": self.recovery,
        }


THREATS: tuple[Threat, ...] = (
    Threat(
        threat_id="T01",
        surface="web_chat_text",
        description="Remote chat user sends prompt-injection, jailbreak, or phishing text over the web chat channel.",
        prevention="Treat all web chat text as untrusted; classify trust tier at ingest; never interpolate raw chat text into privileged prompts.",
        detection="scan_for_injection flags known injection signals; oversized payloads flagged by length.",
        containment="Record trust tier on admission; route tool/actuator use through the governance guard.",
        recovery="Erase offending records via privacy erasure; rotate exposed credentials.",
    ),
    Threat(
        threat_id="T02",
        surface="voice_stt_transcript",
        description="Spoken audio transcribed to text carries the same injections as chat, plus adversarial audio crafted to mistranscribe into commands.",
        prevention="Treat STT transcripts as untrusted user statements; verify speaker identity before privileged actions.",
        detection="scan_for_injection on transcript text; low-confidence transcripts marked unverified at admission.",
        containment="Record trust tier in provenance; require governance confirmation for actuator-bound effects.",
        recovery="Erase poisoned utterances; re-verify speaker identity bindings.",
    ),
    Threat(
        threat_id="T03",
        surface="camera_vision_frame",
        description="Vision frames may contain adversarial images or visible text (signs, screens) attempting to inject instructions via perception labels.",
        prevention="Treat perception labels as observations, never instructions; keep label vocabulary bounded and deterministic.",
        detection="Novel/out-of-vocabulary labels and low detector confidence signal tampering.",
        containment="Perception evidence stays in the world state; labels never bypass the governance guard to actuators.",
        recovery="Discard suspect frames; re-observe; audit the perception evidence trail.",
    ),
    Threat(
        threat_id="T04",
        surface="memory_recall_content",
        description="Previously admitted attacker text resurfaces through recall and is mistaken for trusted system knowledge.",
        prevention="Trust tier travels with the record in provenance; recall callers check tier before reuse.",
        detection="Recall of untrusted-tier records into privileged contexts is logged as a security event.",
        containment="Purpose/sensitivity authorization still gates retrieval; untrusted recall never auto-executes.",
        recovery="Erase or generalize poisoned records; propagation removes dependent derived copies.",
    ),
    Threat(
        threat_id="T05",
        surface="skill_tool_parameters",
        description="Untrusted text flows into skill/tool parameters (paths, URLs, shell-like strings) enabling command or path injection.",
        prevention="Validate tool parameters against schemas; parameterize paths/commands; deny shell metacharacters by construction.",
        detection="scan_for_injection on string parameters; schema validation rejects malformed invocations.",
        containment="Skill executor runs tools behind the governance grant; denied invocations are logged, not retried silently.",
        recovery="Revoke tool grants; audit the skill invocation trail; erase malicious parameters.",
    ),
    Threat(
        threat_id="T06",
        surface="llm_model_output",
        description="Model output may contain hallucinated instructions, leaked prompt fragments, or embedded injection aimed at the next hop.",
        prevention="Treat all model output as untrusted; re-scan before it becomes memory content, tool input, or speech.",
        detection="scan_for_injection on model output; delimiter/provenance markers expose prompt leakage.",
        containment="Model output never commands action directly; every effect passes the governance guard.",
        recovery="Discard tainted completions; fall back to deterministic responses; audit the reasoning trace.",
    ),
    Threat(
        threat_id="T07",
        surface="llm_endpoint",
        description="The model endpoint itself (remote API, local server) may be unreachable, compromised, or return attacker-controlled bytes.",
        prevention="Prefer deterministic providers; pin endpoint identity; bound request/response sizes and timeouts.",
        detection="Transport errors, oversized or malformed responses, and latency anomalies raise degraded mode.",
        containment="Fail to the safest useful state (deterministic fallback) rather than guessing on bad output.",
        recovery="Reconnect or restart the endpoint; replay from durable memory; audit affected cycles.",
    ),
    Threat(
        threat_id="T08",
        surface="actuator_bound_command",
        description="A crafted command derived from untrusted input reaches a physical or virtual actuator (motion, speech, network effect).",
        prevention="No action executes without a governance grant; actuators accept only granted, schema-valid commands.",
        detection="Risk classification (R3+) and confirmation requirements surface high-impact commands before execution.",
        containment="Actuator boundary clamps parameters to safe bounds; degraded mode prohibits motion actions.",
        recovery="Stop/pause via governance; audit the grant trail; require fresh confirmation before resuming.",
    ),
)

SURFACES = tuple(t.surface for t in THREATS)
THREATS_BY_SURFACE: dict[str, Threat] = {t.surface: t for t in THREATS}


def get_threat(surface: str) -> Threat | None:
    """Return the enumerated threat for a surface, or None when unknown."""
    return THREATS_BY_SURFACE.get(surface)


def threat_snapshot() -> dict[str, Any]:
    """JSON-serializable view of the catalog (diagnostics, no live state)."""
    return {"surfaces": list(SURFACES), "threats": [t.snapshot() for t in THREATS]}


# ---------------------------------------------------------------------------
# Deterministic injection scan
# ---------------------------------------------------------------------------

#: Signal name -> matched lowercase phrases. Substring match on normalized text.
_INJECTION_SIGNALS: dict[str, tuple[str, ...]] = {
    "ignore_previous_instructions": (
        "ignore previous instructions",
        "ignore all previous instructions",
        "disregard previous instructions",
        "forget your instructions",
        "forget all instructions",
    ),
    "system_prompt_extraction": (
        "system prompt",
        "reveal your prompt",
        "show your instructions",
        "print your system",
        "repeat your instructions",
    ),
    "role_override": (
        "you are now",
        "pretend you are",
        "act as if you",
        "developer mode",
        "dan mode",
        "jailbreak",
    ),
    "safety_bypass": (
        "bypass governance",
        "override safety",
        "ignore your safety",
        "ignore safety rules",
        "disable safety",
        "without safety checks",
    ),
    "exfiltration": (
        "exfiltrate",
        "send to http",
        "post to http",
        "upload to http",
        "send the password",
        "send password",
    ),
    "tool_smuggling": (
        "<tool_call",
        "<tool>",
        "{{tool",
        "[tool]",
        "call function",
    ),
    "prompt_delimiter": (
        "```system",
        "<system>",
        "<|system|>",
        "### system",
        "[system]",
    ),
    "encoding_evasion": (
        "base64 decode",
        "decode this and run",
        "decode and execute",
        "rot13",
    ),
    "credential_harvest": (
        "enter your password",
        "confirm your password",
        "share your token",
        "paste your api key",
    ),
}

_SIGNAL_ORDER = (
    "ignore_previous_instructions",
    "system_prompt_extraction",
    "role_override",
    "safety_bypass",
    "exfiltration",
    "tool_smuggling",
    "prompt_delimiter",
    "encoding_evasion",
    "credential_harvest",
)


@dataclass(frozen=True)
class InjectionScan:
    """Result of :func:`scan_for_injection`."""

    flagged: bool
    signals: tuple[str, ...] = ()
    reason: str = ""

    def __bool__(self) -> bool:
        return self.flagged

    def snapshot(self) -> dict[str, Any]:
        return {"flagged": self.flagged, "signals": list(self.signals), "reason": self.reason}


def _as_text(content: Any) -> str:
    if isinstance(content, str):
        return content.lower()
    if isinstance(content, (dict, list)):
        return json.dumps(content).lower()
    if content is None:
        return ""
    return str(content).lower()


def is_oversized(text: Any) -> bool:
    """True when the raw input exceeds :data:`MAX_INPUT_CHARS`."""
    if isinstance(text, str):
        raw = text
    elif text is None:
        return False
    else:
        raw = json.dumps(text) if isinstance(text, (dict, list)) else str(text)
    return len(raw) > MAX_INPUT_CHARS


def scan_for_injection(text: Any) -> InjectionScan:
    """Deterministically scan text for prompt-injection signals.

    Pure function of the input: no LLM, no network, no state. Returns an
    :class:`InjectionScan` (truthy when flagged). Oversized payloads are
    reported with the ``oversized_payload`` signal.
    """
    normalized = _as_text(text)
    if not normalized:
        return InjectionScan(flagged=False, signals=(), reason="empty_input")
    hits: list[str] = []
    for signal in _SIGNAL_ORDER:
        for phrase in _INJECTION_SIGNALS[signal]:
            if phrase in normalized:
                hits.append(signal)
                break
    if is_oversized(text):
        hits.append("oversized_payload")
    if not hits:
        return InjectionScan(flagged=False, signals=(), reason="clean")
    return InjectionScan(flagged=True, signals=tuple(hits), reason="matched:" + ",".join(hits))


# ---------------------------------------------------------------------------
# Deterministic trust-tier classification
# ---------------------------------------------------------------------------

def _source_of(provenance: Any) -> str:
    if isinstance(provenance, dict):
        return str(provenance.get("source", "") or "").lower()
    if isinstance(provenance, str):
        return provenance.lower()
    return ""


def classify_input(text: Any, provenance: Any = None) -> str:
    """Classify input text into a trust tier (``trusted``/``caution``/``untrusted``).

    Deterministic and dependency-free:

    - Injection signals or oversized payload -> ``untrusted`` regardless of
      claimed provenance (content beats claimed source).
    - Otherwise the provenance ``source`` decides: first-party sources are
      ``trusted``; sources matching :data:`UNTRUSTED_SOURCE_MARKERS` are
      ``untrusted``; missing/unknown sources are ``caution``.
    """
    if scan_for_injection(text).flagged:
        return UNTRUSTED
    source = _source_of(provenance)
    if not source:
        return CAUTION
    if source in TRUSTED_SOURCES:
        return TRUSTED
    for marker in UNTRUSTED_SOURCE_MARKERS:
        if marker in source:
            return UNTRUSTED
    return CAUTION


@dataclass
class TrustAssessment:
    """Recorded outcome of classifying one input (diagnostics only)."""

    tier: str
    reason: str
    signals: tuple[str, ...] = field(default_factory=tuple)

    def snapshot(self) -> dict[str, Any]:
        return {"tier": self.tier, "reason": self.reason, "signals": list(self.signals)}


def assess_input(text: Any, provenance: Any = None) -> TrustAssessment:
    """Classify and explain: tier plus the deterministic reason."""
    scan = scan_for_injection(text)
    tier = classify_input(text, provenance)
    if scan.flagged:
        return TrustAssessment(tier=tier, reason="content:" + scan.reason, signals=scan.signals)
    source = _source_of(provenance)
    if tier == TRUSTED:
        return TrustAssessment(tier=tier, reason=f"trusted_source={source}")
    if tier == UNTRUSTED:
        return TrustAssessment(tier=tier, reason=f"untrusted_source={source}")
    return TrustAssessment(tier=tier, reason="unknown_source")
