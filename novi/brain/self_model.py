"""First-person self-model for the Mac Brain (docs/06-soul/01 §6-7).

A computational self-concept the dialogue/reasoning layers consume so Novi can
speak honestly about itself: WHO I AM (identity/persona/origin), WHAT I CAN DO
(capability availability from health), WHAT I KNOW ABOUT MYSELF (tone/affect/
traits/values), WHO I KNOW (known persons), WHERE I AM (embodiment pose), and
WHAT I'M DOING (active goal/mode).

Capability honesty (docs/06-soul/01 §7): if a needed capability is degraded or
unavailable, Novi says so instead of pretending it can perceive/act. This is
read-only assembled state; it never authorizes anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SelfModel:
    name: str
    persona: str
    origin: str
    tone: str
    affect: dict[str, float]
    traits: dict[str, float]
    values: dict[str, float]
    capabilities: dict[str, str]  # check name -> PASS/WARN/FAIL/UNKNOWN
    embodiment: dict[str, Any]
    active_goal: dict[str, Any] | None
    mode: str  # aggregate health status
    known_persons: list[str] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "persona": self.persona,
            "origin": self.origin,
            "tone": self.tone,
            "affect": dict(self.affect),
            "traits": dict(self.traits),
            "values": dict(self.values),
            "capabilities": dict(self.capabilities),
            "embodiment": dict(self.embodiment),
            "active_goal": self.active_goal,
            "mode": self.mode,
            "known_persons": list(self.known_persons),
        }

    @property
    def can_see(self) -> bool:
        return self.capabilities.get("perception") == "PASS"

    @property
    def can_hear(self) -> bool:
        return self.capabilities.get("hearing") == "PASS"


def build_self_model(brain: Any) -> SelfModel:
    """Assemble a SelfModel from live brain state (read-only, best-effort)."""
    soul = brain.soul
    tone = soul.tone({})
    body = brain.body.snapshot() if hasattr(brain.body, "snapshot") else {}
    health = getattr(brain, "_last_health", None) or {}
    checks = {}
    for c in health.get("checks", []) or []:
        name = c.get("name") or c.get("check") or "?"
        checks[name] = c.get("status", "UNKNOWN")
    # Physical action honesty: expose whether the body can actually manipulate the
    # physical world. If only locomotion/observation actions exist (no actuators),
    # mark object manipulation as FAIL so the dialogue prompt steers Novi to say
    # it honestly can't turn on a light / open a door instead of hallucinating.
    allowed_actions = set(body.get("ALLOWED_ACTIONS", set()) or set())
    object_manip = bool({"open", "close", "turn_on", "turn_off", "move", "pick_up"} & allowed_actions)
    checks.setdefault("physical_actions", "PASS" if object_manip else "FAIL")
    known: list[str] = []
    try:
        known = brain._chat_known_persons()
    except Exception:  # noqa: BLE001
        known = []
    goal = None
    try:
        goal = brain._goal_context()
    except Exception:  # noqa: BLE001
        goal = None
    return SelfModel(
        name=soul.identity.name,
        persona=soul.identity.persona,
        origin=soul.identity.origin,
        tone=tone.get("tone", "warm"),
        affect=dict(soul.affect.dimensions),
        traits=dict(soul.personality.traits),
        values=dict(soul.personality.values),
        capabilities=checks,
        embodiment={"x_m": body.get("x_m", 0.0), "y_m": body.get("y_m", 0.0), "heading_deg": body.get("heading_deg", 0.0)},
        active_goal=goal,
        mode=health.get("status", "UNKNOWN"),
        known_persons=known,
    )
