"""TeleOp Phase 1 — keyboard demonstration over the simulated embodiment.

NVIDIA research §17 (Isaac TeleOp) applied to the Mac phase: teleoperation is a
data-acquisition capability. Phase 1 is keyboard/gamepad demonstration: a human
drives the simulated body (``SimBody``/``SimWorld`` from virtual_skills) through
the environment, and every command is recorded as an episode step
(observation / action / outcome) into a ``NoviEpisode`` with pinned provenance
and evidence class.

Progression (research §17):
    Phase 1 keyboard/gamepad demonstration  -> THIS MODULE
    Phase 2 VR/spatial teleoperation        -> hardware phase
    Phase 3 assisted teleoperation          -> hardware phase
    Phase 4 policy-assisted demonstration   -> hardware phase
    Phase 5 human intervention only on failures -> hardware phase

The resulting episodes feed the NoviEpisode schema and can be exported to
LeRobot layout for a future GR00T fine-tune (lerobot_export.export_lerobot_dataset).
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from novi.brain.nvidia_experiments import EpisodeRecorder, NoviEpisode
from novi.brain.virtual_skills import SimBody, SimWorld

# ---------------------------------------------------------------------------
# TeleOp command vocabulary (Phase 1: keyboard/gamepad)
# ---------------------------------------------------------------------------

FORWARD = "forward"
BACKWARD = "backward"
TURN_LEFT = "turn_left"
TURN_RIGHT = "turn_right"
INTERACT = "interact"
SPEAK = "speak"
RESET = "reset"
END = "end"

ALL_COMMANDS = frozenset(
    {
        FORWARD,
        BACKWARD,
        TURN_LEFT,
        TURN_RIGHT,
        INTERACT,
        SPEAK,
        RESET,
        END,
    }
)

# Single-key mapping used by the interactive demo and documented for gamepads.
KEY_MAP: dict[str, str] = {
    "w": FORWARD,
    "W": FORWARD,
    "\x1b[A": FORWARD,  # up arrow
    "s": BACKWARD,
    "S": BACKWARD,
    "\x1b[B": BACKWARD,  # down arrow
    "a": TURN_LEFT,
    "A": TURN_LEFT,
    "\x1b[D": TURN_LEFT,  # left arrow
    "d": TURN_RIGHT,
    "D": TURN_RIGHT,
    "\x1b[C": TURN_RIGHT,  # right arrow
    " ": INTERACT,
    "f": INTERACT,
    "F": INTERACT,
    "t": SPEAK,
    "T": SPEAK,
    "r": RESET,
    "R": RESET,
    "q": END,
    "Q": END,
}


# ---------------------------------------------------------------------------
# Step result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TeleOpStepResult:
    """Outcome of one teleoperation command."""

    command: str
    step_index: int
    timestamp: str
    pose: dict[str, float]
    visible_objects: tuple[dict[str, Any], ...]
    outcome_status: str  # SUCCESS / FAILURE / RUNNING / ENDED
    outcome_detail: dict[str, Any]
    object_grasped: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "step_index": self.step_index,
            "timestamp": self.timestamp,
            "pose": dict(self.pose),
            "visible_objects": list(self.visible_objects),
            "outcome_status": self.outcome_status,
            "outcome_detail": dict(self.outcome_detail),
            "object_grasped": self.object_grasped,
        }


# ---------------------------------------------------------------------------
# TeleOpSession — drive the simulated body and record episodes
# ---------------------------------------------------------------------------


class TeleOpSession:
    """Keyboard demonstration session over a simulated embodiment.

    Each ``step(command)`` applies the command to the body, builds an
    observation (pose + visible objects with spatial relations), an action
    (skill ``teleop``, command, risk class), and an outcome, and records the
    triple into an ``EpisodeRecorder``. ``build_episode()`` assembles the
    recorded steps into a ``NoviEpisode`` with OBSERVED evidence class.

    Grasp semantics: ``INTERACT`` grasps the nearest object within
    ``reach_threshold``; the object is then held (removed from the world until
    a later ``INTERACT`` releases it).
    """

    def __init__(
        self,
        body: SimBody,
        world: SimWorld,
        *,
        recorder: EpisodeRecorder | None = None,
        task_name: str = "teleop_demonstration",
        description: str = "Keyboard teleoperation demonstration over the simulated embodiment.",
        move_distance: float = 0.5,
        turn_degrees: float = 15.0,
        reach_threshold: float = 0.6,
        visibility_radius: float = 3.0,
        evidence_class: str = "OBSERVED",
    ) -> None:
        self.body = body
        self.world = world
        self.move_distance = move_distance
        self.turn_degrees = turn_degrees
        self.reach_threshold = reach_threshold
        self.visibility_radius = visibility_radius
        self._held_object: str | None = None
        self._step_index = 0
        self._history: list[TeleOpStepResult] = []
        self.recorder = recorder or EpisodeRecorder(
            task_name=task_name,
            description=description,
            evidence_class=evidence_class,
            source="mac_brain_teleop",
            platform={"runtime": "mac_brain", "teleop_phase": "1_keyboard"},
        )

    # -- state helpers ------------------------------------------------------

    def visible_objects(self) -> tuple[dict[str, Any], ...]:
        """Objects within visibility radius, with distance/heading (spatial
        relations, research §13) and grasp-reach flag."""
        out: list[dict[str, Any]] = []
        for obj_id, (ox, oy) in self.world.object_locations.items():
            if obj_id == self._held_object:
                continue
            dx, dy = ox - self.body.x_m, oy - self.body.y_m
            dist = math.hypot(dx, dy)
            if dist > self.visibility_radius:
                continue
            bearing = math.degrees(math.atan2(dy, dx)) % 360.0
            out.append(
                {
                    "object_id": obj_id,
                    "distance_m": round(dist, 3),
                    "bearing_deg": round(bearing, 1),
                    "in_reach": dist <= self.reach_threshold,
                }
            )
        return tuple(sorted(out, key=lambda o: o["distance_m"]))

    def _nearest_reachable(self) -> tuple[str, float] | None:
        best: tuple[str, float] | None = None
        for obj_id, (ox, oy) in self.world.object_locations.items():
            if obj_id == self._held_object:
                continue
            dist = math.hypot(ox - self.body.x_m, oy - self.body.y_m)
            if dist <= self.reach_threshold and (best is None or dist < best[1]):
                best = (obj_id, dist)
        return best

    # -- command execution ---------------------------------------------------

    def step(self, command: str, *, text: str = "") -> TeleOpStepResult:
        """Apply one teleoperation command and record the episode step."""
        if command not in ALL_COMMANDS:
            raise ValueError(f"unknown teleop command: {command!r}")
        now = datetime.now(timezone.utc).isoformat()

        if command == END:
            status, detail, grasped = "ENDED", {"session": "ended"}, self._held_object
        elif command == RESET:
            self.body.x_m, self.body.y_m, self.body.heading_deg = 0.0, 0.0, 0.0
            status, detail, grasped = "RUNNING", {"reset": True}, self._held_object
        elif command == FORWARD:
            self.body.x_m += self.move_distance * math.cos(math.radians(self.body.heading_deg))
            self.body.y_m += self.move_distance * math.sin(math.radians(self.body.heading_deg))
            status, detail, grasped = "RUNNING", {"moved": "forward"}, self._held_object
        elif command == BACKWARD:
            self.body.x_m -= self.move_distance * math.cos(math.radians(self.body.heading_deg))
            self.body.y_m -= self.move_distance * math.sin(math.radians(self.body.heading_deg))
            status, detail, grasped = "RUNNING", {"moved": "backward"}, self._held_object
        elif command == TURN_LEFT:
            self.body.heading_deg = (self.body.heading_deg - self.turn_degrees) % 360.0
            status, detail, grasped = "RUNNING", {"turned_deg": -self.turn_degrees}, self._held_object
        elif command == TURN_RIGHT:
            self.body.heading_deg = (self.body.heading_deg + self.turn_degrees) % 360.0
            status, detail, grasped = "RUNNING", {"turned_deg": self.turn_degrees}, self._held_object
        elif command == INTERACT:
            nearest = self._nearest_reachable()
            if self._held_object is not None:
                # Release the held object at the current pose.
                self.world.object_locations[self._held_object] = (self.body.x_m, self.body.y_m)
                released = self._held_object
                self._held_object = None
                status, detail, grasped = "SUCCESS", {"released": released}, None
            elif nearest is not None:
                self._held_object = nearest[0]
                status, detail, grasped = (
                    "SUCCESS",
                    {"grasped": nearest[0], "distance_m": round(nearest[1], 3)},
                    nearest[0],
                )
            else:
                status, detail, grasped = "FAILURE", {"reason": "object_not_in_reach"}, None
        elif command == SPEAK:
            status, detail, grasped = "SUCCESS", {"spoken": text or "acknowledgement"}, self._held_object
        else:  # pragma: no cover - ALL_COMMANDS guard above
            raise ValueError(f"unhandled teleop command: {command!r}")

        result = TeleOpStepResult(
            command=command,
            step_index=self._step_index,
            timestamp=now,
            pose=self.body.pose(),
            visible_objects=self.visible_objects(),
            outcome_status=status,
            outcome_detail=detail,
            object_grasped=grasped,
        )
        self._record(result, text=text)
        self._history.append(result)
        self._step_index += 1
        return result

    def _record(self, result: TeleOpStepResult, *, text: str) -> None:
        risk_class = "R1" if result.command == SPEAK else "R3"
        self.recorder.record_step(
            observation={
                "pose": dict(result.pose),
                "visible_objects": list(result.visible_objects),
                "held_object": self._held_object,
            },
            action={
                "skill": "teleop",
                "command": result.command,
                "parameters": {"text": text} if result.command == SPEAK else {},
                "risk_class": risk_class,
            },
            outcome={
                "status": result.outcome_status,
                "detail": dict(result.outcome_detail),
                "object_grasped": result.object_grasped,
            },
            timestamp=result.timestamp,
            provenance={"source": "mac_brain_teleop", "teleop_phase": "1_keyboard", "step_index": result.step_index},
        )

    # -- episode assembly ----------------------------------------------------

    def build_episode(self) -> NoviEpisode:
        """Assemble the recorded steps into a NoviEpisode."""
        episode = self.recorder.build_episode()
        episode.provenance["teleop_phase"] = "1_keyboard"
        # Preserve the execution order of commands used in the demonstration.
        episode.provenance["commands"] = list(dict.fromkeys(r.command for r in self._history))
        episode.metadata["teleop_phase"] = "1_keyboard"
        episode.metadata["end_state"] = {
            "pose": self.body.pose(),
            "held_object": self._held_object,
        }
        return episode

    @property
    def step_count(self) -> int:
        return self._step_index

    @property
    def history(self) -> tuple[TeleOpStepResult, ...]:
        return tuple(self._history)

    @property
    def held_object(self) -> str | None:
        return self._held_object

    def reset(self) -> None:
        """Reset the session (pose, held object, recorder, history)."""
        self.body.x_m, self.body.y_m, self.body.heading_deg = 0.0, 0.0, 0.0
        self._held_object = None
        self._step_index = 0
        self._history.clear()
        self.recorder.reset()


# ---------------------------------------------------------------------------
# Interactive keyboard demo (python -m novi.brain.teleop)
# ---------------------------------------------------------------------------


def _demo_world() -> tuple[SimBody, SimWorld]:
    body = SimBody(x_m=0.0, y_m=0.0, heading_deg=0.0, localized=True)
    world = SimWorld(
        object_locations={
            "cup_001": (2.0, 0.5),
            "phone_001": (4.0, -1.0),
        },
        forbidden_regions=[(5.0, 2.0, 6.0, 3.0)],
    )
    return body, world


def run_keyboard_demo(*, max_commands: int = 200) -> TeleOpSession:
    """Interactive keyboard teleoperation session.

    Reads single keys (or one-word commands) from stdin until ``q``/END or
    ``max_commands``. Prints the pose and visible objects after every command.
    """
    body, world = _demo_world()
    session = TeleOpSession(body, world)
    print("NOVI TeleOp Phase 1 — keyboard demonstration over the simulated embodiment")
    print("keys: w/s/a/d move · f interact · t speak · r reset · q end")
    commands = 0
    while commands < max_commands:
        raw = input("command> ").strip()
        if not raw:
            continue
        command = KEY_MAP.get(raw, raw)
        if command not in ALL_COMMANDS:
            print(f"unknown command {raw!r}")
            continue
        result = session.step(command, text="hello from teleop") if command == SPEAK else session.step(command)
        print(result.snapshot())
        commands += 1
        if command == END:
            break
    return session


def main() -> int:
    parser = argparse.ArgumentParser(description="Novi TeleOp Phase 1 — keyboard demonstration")
    parser.add_argument("--max-commands", type=int, default=200)
    parser.add_argument(
        "--out", type=str, default=None, metavar="PATH", help="write the assembled NoviEpisode JSON to PATH"
    )
    args = parser.parse_args()

    import json

    session = run_keyboard_demo(max_commands=args.max_commands)
    episode = session.build_episode()
    print(json.dumps(episode.snapshot(), indent=2, sort_keys=True, default=str))
    if args.out:
        from pathlib import Path

        Path(args.out).write_text(
            json.dumps(episode.snapshot(), indent=2, sort_keys=True, default=str), encoding="utf-8"
        )
        print(f"episode written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
