"""Physical authority boundary (Phase 2c, P0 gap 3 of the 2026-08-29 plan).

The last deterministic gate in front of the actuator surface. Cognition
proposals — whatever produced them, deterministic or model — never command
the body directly: they are compiled into a bounded, expiring actuator
command, and only compiled commands survive:

  proposal -> policy (governance + safety) -> AUTHORITY -> actuator

with this module owning the AUTHORITY stage:

- allow-list: only actions the body surface documents (VirtualBody
  semantics) compile; anything else is UNKNOWN_ACTION;
- parameter bounds: per-action bounds enforce distance/degrees/text caps;
  oversize values are OUT_OF_BOUNDS (the model can never move the body
  farther or faster than the envelope);
- rate limit: at most ``max_commands_per_cycle`` commands per cycle
  (one-action-per-tick by default); over-budget compiles are RATE_LIMITED;
- expiry: every command carries a ttl (expires_cycle); ``is_live`` gates
  execution on the command not being expired, so an authorization that sat
  too long (e.g. held for confirmation) can never reach the actuator;
- watchdog: ``watch(cycle)`` expires stale issued commands and reports them
  for audit, so nothing lingers "authorized" invisibly.

Every refusal carries a typed rejection code for the audit trail. The
companion contract is ``novi.contracts://execution/actuator-command/1.0.0``
(schema validation for the serialized command snapshot).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

# Rejection codes (typed, audit-friendly).
UNKNOWN_ACTION = "UNKNOWN_ACTION"
OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
RATE_LIMITED = "RATE_LIMITED"
EXPIRED = "EXPIRED"

_VERSION = "actuator-boundary/1.0.0"

# Per-action parameter bounds (min, max). The speak bound is a text length
# cap (characters). Absent name-parameter pairs are not constrained here
# (the body ignores unknown parameters), but listed ones always enforce.
_ACTION_BOUNDS: dict[str, dict[str, tuple[float, float]]] = {
    "move_forward": {"distance_m": (0.0, 1.0)},
    "turn_left": {"degrees": (0.0, 360.0)},
    "turn_right": {"degrees": (0.0, 360.0)},
    "speak": {"text": (0.0, 2000.0)},
}

_LENGTH_ONLY: frozenset[str] = frozenset({"speak"})

_BODY_ACTIONS = frozenset({
    "inspect", "move_forward", "turn_left", "turn_right", "stop", "wait", "observe", "speak",
})


@dataclass(frozen=True)
class CompiledCommand:
    """One bounded, expiring authorization to actuate (contract-shaped)."""

    command_id: str
    action: str
    parameters: dict[str, Any]
    risk_class: str
    source: str
    issued_cycle: int
    expires_cycle: int
    correlation_id: str
    compiled_by: str

    def snapshot(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "action": self.action,
            "parameters": dict(self.parameters),
            "risk_class": self.risk_class,
            "source": self.source,
            "issued_cycle": self.issued_cycle,
            "expires_cycle": self.expires_cycle,
            "correlation_id": self.correlation_id,
            "compiled_by": self.compiled_by,
        }


@dataclass(frozen=True)
class CompileResult:
    """Fail-closed compile outcome: exactly one of command/rejection."""

    command: CompiledCommand | None
    rejection: str | None
    reason: str = ""


@dataclass
class WatchdogEntry:
    command_id: str
    action: str
    expired_at_cycle: int
    code: str = EXPIRED


class ActuatorBoundary:
    """Compile-and-authority gate between cognition and the actuator surface."""

    def __init__(
        self,
        *,
        allowed_actions: frozenset[str] | None = None,
        bounds: Mapping[str, Mapping[str, tuple[float, float]]] | None = None,
        max_commands_per_cycle: int = 1,
        command_ttl_cycles: int = 5,
        version: str = _VERSION,
    ) -> None:
        self.allowed_actions = frozenset(allowed_actions) if allowed_actions is not None else frozenset(_BODY_ACTIONS)
        self.bounds = dict(bounds) if bounds is not None else _ACTION_BOUNDS
        self.max_commands_per_cycle = max(1, int(max_commands_per_cycle))
        self.command_ttl_cycles = max(1, int(command_ttl_cycles))
        self.compiled_by = version
        self._issued_per_cycle: dict[int, int] = {}
        self._issued: dict[str, CompiledCommand] = {}
        self._expired: list[WatchdogEntry] = []

    # ----------------------------------------------------------------- compile

    def compile(
        self,
        *,
        action: str,
        parameters: Mapping[str, Any] | None = None,
        risk_class: str = "R1",
        source: str = "deterministic",
        cycle: int,
        correlation_id: str = "",
    ) -> CompileResult:
        """Compile a proposal into an actuator command — fail closed.

        Every refusal produces a typed rejection code: the caller can only
        actuate through a compiled command, never through the raw proposal.
        """
        params = dict(parameters or {})
        action = str(action)
        if action not in self.allowed_actions:
            return CompileResult(None, UNKNOWN_ACTION, f"action not on the actuator allow-list: {action!r}")
        if self._issued_per_cycle.get(cycle, 0) >= self.max_commands_per_cycle:
            return CompileResult(None, RATE_LIMITED, f"command budget for cycle {cycle} exhausted")
        for name, (low, high) in self.bounds.get(action, {}).items():
            value = params.get(name)
            if value is None:
                continue  # body supplies its default inside the bound
            if name in _LENGTH_ONLY:
                if not isinstance(value, str) or not (low <= len(value) <= high):
                    return CompileResult(None, OUT_OF_BOUNDS, f"{action}.{name} length outside [{low:g}, {high:g}]")
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return CompileResult(None, OUT_OF_BOUNDS, f"{action}.{name} not numeric: {value!r}")
            if not (low <= numeric <= high):
                return CompileResult(None, OUT_OF_BOUNDS, f"{action}.{name}={numeric:g} outside [{low:g}, {high:g}]")

        command = CompiledCommand(
            command_id=f"ac-{uuid4().hex[:12]}",
            action=action,
            parameters=dict(params or {}),
            risk_class=risk_class,
            source=source,
            issued_cycle=cycle,
            expires_cycle=cycle + self.command_ttl_cycles,
            correlation_id=correlation_id,
            compiled_by=self.compiled_by,
        )
        self._issued_per_cycle[cycle] = self._issued_per_cycle.get(cycle, 0) + 1
        self._issued[command.command_id] = command
        return CompileResult(command, None)

    # ------------------------------------------------------------------ expiry

    def is_live(self, command: CompiledCommand, *, cycle: int) -> bool:
        """True only while the command is inside its validity window."""
        if command is None:
            return False
        return command.issued_cycle <= cycle < command.expires_cycle

    def watch(self, *, cycle: int) -> list[dict[str, Any]]:
        """Watchdog pass: expire stale issued commands; report expirations."""
        expired = []
        for command_id in list(self._issued):
            command = self._issued[command_id]
            if not self.is_live(command, cycle=cycle):
                del self._issued[command_id]
                entry = WatchdogEntry(command_id=command_id, action=command.action, expired_at_cycle=cycle)
                self._expired.append(entry)
                expired.append({
                    "command_id": entry.command_id,
                    "action": entry.action,
                    "expired_at_cycle": entry.expired_at_cycle,
                    "code": entry.code,
                })
        return expired

    # -------------------------------------------------------------- introspect

    def snapshot(self) -> dict[str, Any]:
        return {
            "compiled_by": self.compiled_by,
            "allowed_actions": sorted(self.allowed_actions),
            "command_ttl_cycles": self.command_ttl_cycles,
            "max_commands_per_cycle": self.max_commands_per_cycle,
            "active_commands": len(self._issued),
            "expired_total": len(self._expired),
        }
