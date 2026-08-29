"""Virtual embodied skills for the Mac Brain (06_AUTONOMY doc 11 Phase 5).

Implements the first two virtual skills on the way to a real body:

- ``NavigateToSkill`` — move the (simulated) body to a target pose. Preconditions:
  localized, route valid, authority sufficient. Postcondition: pose within
  tolerance (doc 05 Step 6 example).
- ``SearchForObjectSkill`` — active search for a known object using
  ``ActiveSearch`` (doc 04). Postcondition: observation with sufficient
  confidence; budget exhaustion is reported as not-found, never success.

Both are fully deterministic (no hardware) and record outcomes into an
``OutcomeMemory`` so future planning can prefer skills with demonstrated
success in similar contexts (doc 05 Step 8).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from novi.brain.active_perception import ActiveSearch, PerceptionQuery
from novi.brain.behavior_tree import OutcomeMemory, PostconditionCheck


@dataclass
class SimBody:
    """Deterministic simulated body for virtual skills."""
    x_m: float = 0.0
    y_m: float = 0.0
    heading_deg: float = 0.0
    localized: bool = True

    def pose(self) -> dict[str, float]:
        return {"x_m": self.x_m, "y_m": self.y_m, "heading_deg": self.heading_deg}


@dataclass
class SimWorld:
    """Deterministic simulated world: object locations + forbidden regions."""
    object_locations: dict[str, tuple[float, float]] = field(default_factory=dict)
    forbidden_regions: list[tuple[float, float, float, float]] = field(default_factory=list)

    def route_blocked(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Straight-line route intersects a forbidden region (AABB)."""
        for rx1, ry1, rx2, ry2 in self.forbidden_regions:
            if min(x1, x2) < rx2 and max(x1, x2) > rx1 and min(y1, y2) < ry2 and max(y1, y2) > ry1:
                return True
        return False


class NavigateToSkill:
    """Virtual navigation: turn toward the target, move a bounded step per call."""

    def __init__(
        self,
        body: SimBody,
        world: SimWorld,
        memory: OutcomeMemory | None = None,
        *,
        move_distance: float = 0.5,
        turn_degrees: float = 10.0,
        reach_threshold: float = 0.5,
        heading_tolerance: float = 5.0,
        max_steps: int = 100,
    ) -> None:
        self.body = body
        self.world = world
        self.memory = memory
        self.move_distance = move_distance
        self.turn_degrees = turn_degrees
        self.reach_threshold = reach_threshold
        self.heading_tolerance = heading_tolerance
        self.max_steps = max_steps

    def skill_id(self) -> str:
        return "NavigateTo"

    def preconditions(self, ctx: dict[str, Any]) -> tuple[bool, str]:
        target = ctx.get("target")
        if not isinstance(target, tuple) or len(target) != 2:
            return False, "target_missing"
        if not self.body.localized:
            return False, "not_localized"
        if self.world.route_blocked(self.body.x_m, self.body.y_m, target[0], target[1]):
            return False, "route_blocked"
        return True, ""

    def execute(self, ctx: dict[str, Any]) -> dict[str, Any]:
        """One bounded step toward the target; returns the new pose."""
        tx, ty = ctx["target"]
        x, y, heading = self.body.x_m, self.body.y_m, self.body.heading_deg
        distance = math.hypot(tx - x, ty - y)
        if distance <= self.reach_threshold:
            return {"arrived": True, "in_progress": False, **self.body.pose()}
        desired = math.degrees(math.atan2(ty - y, tx - x))
        diff = (desired - heading + 180.0) % 360.0 - 180.0
        if abs(diff) > self.heading_tolerance:
            if diff > 0:
                self.body.heading_deg = (heading + self.turn_degrees) % 360.0
            else:
                self.body.heading_deg = (heading - self.turn_degrees) % 360.0
        else:
            self.body.x_m = x + self.move_distance * math.cos(math.radians(heading))
            self.body.y_m = y + self.move_distance * math.sin(math.radians(heading))
        return {"arrived": False, "in_progress": True, **self.body.pose()}

    def postcondition(self, ctx: dict[str, Any], outcome: dict[str, Any]) -> PostconditionCheck:
        tx, ty = ctx["target"]
        error = math.hypot(self.body.x_m - tx, self.body.y_m - ty)
        return PostconditionCheck(
            method="pose_within_tolerance",
            passed=error <= self.reach_threshold,
            measured={"pose_error_m": round(error, 4)},
            threshold={"reach_threshold_m": self.reach_threshold},
            error="" if error <= self.reach_threshold else f"pose_error_{round(error, 3)}_m",
        )

    def record(self, *, outcome: str, verification: str, ctx: dict[str, Any], cycle: int) -> None:
        if self.memory is not None:
            self.memory.record(skill_id=self.skill_id(), outcome=outcome, verification=verification,
                               context={"target": ctx.get("target"), "goal_kind": ctx.get("goal_kind")},
                               cycle=cycle)


class SearchForObjectSkill:
    """Virtual object search using the active-perception boundary (doc 04)."""

    def __init__(
        self,
        searcher: ActiveSearch,
        memory: OutcomeMemory | None = None,
        *,
        confidence_threshold: float = 0.5,
    ) -> None:
        self.searcher = searcher
        self.memory = memory
        self.confidence_threshold = confidence_threshold

    def skill_id(self) -> str:
        return "SearchForObject"

    def preconditions(self, ctx: dict[str, Any]) -> tuple[bool, str]:
        if not ctx.get("target"):
            return False, "target_missing"
        return True, ""

    def execute(self, ctx: dict[str, Any], *, cycle: int = 0) -> dict[str, Any]:
        query = PerceptionQuery.for_goal(str(ctx["target"]), goal_id=str(ctx.get("goal_id", "")),
                                         confidence_threshold=self.confidence_threshold)
        outcome = self.searcher.search(query, image=ctx.get("image", "frame"), cycle=cycle)
        return {
            "found": outcome.found,
            "confidence": outcome.best.confidence if outcome.best else 0.0,
            "reason": outcome.reason,
            "uncertainty": outcome.uncertainty,
        }

    def postcondition(self, ctx: dict[str, Any], outcome: dict[str, Any]) -> PostconditionCheck:
        found = bool(outcome.get("found"))
        return PostconditionCheck(
            method="object_observed_with_confidence",
            passed=found,
            measured={"confidence": outcome.get("confidence", 0.0), "reason": outcome.get("reason", "")},
            threshold={"confidence_threshold": self.confidence_threshold},
            error="" if found else f"not_found:{outcome.get('reason', 'unknown')}",
        )

    def record(self, *, outcome: str, verification: str, ctx: dict[str, Any], cycle: int) -> None:
        if self.memory is not None:
            self.memory.record(skill_id=self.skill_id(), outcome=outcome, verification=verification,
                               context={"target": ctx.get("target")}, cycle=cycle)
