"""LeRobot dataset export + GR00T custom-embodiment config template.

NVIDIA research §24 Exp 5 (prep half, Mac-feasible): prepare LeRobot data and
a custom-embodiment config so that when GR00T is available (hardware/GPU phase)
Novi can fine-tune without re-authoring data.

Two deliverables:

1. ``export_lerobot_dataset`` — writes NoviEpisode datasets in the LeRobot
   dataset layout (``meta/info.json`` + ``meta/episodes/*.json`` + per-episode
   frame data). The Mac has no pyarrow/pandas, so frame data is written as
   JSON files that mirror the LeRobot per-frame fields (frame_index, timestamp,
   observation, action, reward, done) plus pinned ``_novi_evidence_class`` and
   ``_novi_provenance``; the included note documents the parquet conversion
   step that runs on the training machine.

2. ``build_gr00t_embodiment_config`` — a template describing the Novi
   embodiment: sensors, observation space, action space (derived from the
   skill contracts), control frequency. It is a template for the GR00T
   fine-tune step; the exact schema is validated against the GR00T release
   when that step is entered.

Episodes never lose provenance or evidence class (research §20): NVIDIA
formats are transport only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from novi.brain.nvidia_experiments import LeRobotAdapter, NoviEpisode

# ---------------------------------------------------------------------------
# LeRobot dataset export
# ---------------------------------------------------------------------------

# The LeRobot frame fields Novi maps onto (v2 single-file episode layout).
LEROBOT_FRAME_FIELDS = ("frame_index", "timestamp", "observation", "action", "reward", "done")
LEROBOT_LAYOUT_VERSION = "2.0"


@dataclass(frozen=True)
class ExportManifest:
    """Result of a LeRobot dataset export."""

    output_dir: str
    episode_count: int
    frame_count: int
    tasks: tuple[str, ...]
    files: tuple[str, ...]

    def snapshot(self) -> dict[str, Any]:
        return {
            "output_dir": self.output_dir,
            "episode_count": self.episode_count,
            "frame_count": self.frame_count,
            "tasks": list(self.tasks),
            "files": list(self.files),
        }


def export_lerobot_dataset(
    episodes: list[NoviEpisode],
    output_dir: str | Path,
    *,
    robot_type: str = "novi_mac_brain",
    env_type: str = "simulated",
    fps: int = 10,
) -> ExportManifest:
    """Write episodes in the LeRobot dataset layout.

    Layout::

        <output_dir>/
          meta/info.json              # dataset-level metadata (LeRobot fields)
          meta/episodes/<index>.json  # one per episode: episode_index, length, tasks
          data/chunk-0000/<index>.json# per-episode frames (JSON; parquet on the
                                      #   training machine, see data/README.md)
          data/README.md              # conversion note
    """
    out = Path(output_dir)
    meta_dir = out / "meta" / "episodes"
    data_dir = out / "data" / "chunk-0000"
    meta_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    adapter = LeRobotAdapter()
    total_frames = 0
    tasks: list[str] = []
    written: list[str] = []

    for index, episode in enumerate(episodes):
        lerobot = adapter.to_format(episode)
        length = len(episode.steps)
        total_frames += length
        if episode.task_name not in tasks:
            tasks.append(episode.task_name)

        # meta/episodes/<index>.json — LeRobot episode metadata.
        meta_file = meta_dir / f"{index:05d}.json"
        meta_file.write_text(
            json.dumps(
                {
                    "episode_index": index,
                    "length": length,
                    "tasks": [episode.task_name],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        written.append(str(meta_file.relative_to(out)))

        # data/chunk-0000/<index>.json — frames mirroring LeRobot fields.
        data_file = data_dir / f"{index:05d}.json"
        data_file.write_text(
            json.dumps(
                {
                    "episode_index": index,
                    "episode_id": episode.episode_id,
                    "frames": lerobot["frames"],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        written.append(str(data_file.relative_to(out)))

    # meta/info.json — LeRobot dataset-level metadata.
    info = {
        "codebase_version": LEROBOT_LAYOUT_VERSION,
        "total_episodes": len(episodes),
        "total_frames": total_frames,
        "fps": fps,
        "robot_type": robot_type,
        "env_type": env_type,
        "has_video": False,
        "features": {
            "observation": {"dtype": "json", "shape": [None], "names": []},
            "action": {"dtype": "json", "shape": [None], "names": []},
        },
        "novi": {
            "note": "Frame data written as JSON on the Mac; convert to parquet "
            "with the LeRobot toolchain on the GR00T training machine.",
            "evidence_classes_preserved": True,
            "provenance_preserved": True,
        },
    }
    (out / "meta" / "info.json").write_text(json.dumps(info, indent=2, sort_keys=True), encoding="utf-8")
    written.append("meta/info.json")

    # data/README.md — conversion note.
    (out / "data" / "README.md").write_text(
        "Novi LeRobot export (JSON frame layout).\n\n"
        "The Mac Brain writes frames as JSON because pyarrow/pandas are not "
        "installed here. On the GR00T training machine, convert each "
        "data/chunk-0000/<index>.json into LeRobot parquet chunks using the "
        "LeRobot dataset writer; the frames already carry the LeRobot fields "
        "frame_index/timestamp/observation/action/reward/done plus "
        "_novi_evidence_class and _novi_provenance.\n",
        encoding="utf-8",
    )
    written.append("data/README.md")

    return ExportManifest(
        output_dir=str(out),
        episode_count=len(episodes),
        frame_count=total_frames,
        tasks=tuple(tasks),
        files=tuple(written),
    )


def validate_lerobot_export(output_dir: str | Path) -> dict[str, Any]:
    """Validate an exported dataset directory.

    Checks: info.json present and consistent with episode count/frame count;
    every meta/episodes file has a matching data file; frame counts match the
    episode metadata. Returns a report dict (no exception on failure; the
    caller decides).
    """
    out = Path(output_dir)
    report: dict[str, Any] = {"valid": True, "issues": []}
    info_file = out / "meta" / "info.json"
    if not info_file.exists():
        return {"valid": False, "issues": ["meta/info.json missing"]}
    info = json.loads(info_file.read_text(encoding="utf-8"))
    episode_count = info.get("total_episodes", 0)
    frame_count = info.get("total_frames", 0)

    meta_dir = out / "meta" / "episodes"
    data_dir = out / "data" / "chunk-0000"
    meta_files = sorted(meta_dir.glob("*.json")) if meta_dir.exists() else []
    if len(meta_files) != episode_count:
        report["valid"] = False
        report["issues"].append(f"meta episode files {len(meta_files)} != total_episodes {episode_count}")

    counted_frames = 0
    for meta_file in meta_files:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        index = meta["episode_index"]
        data_file = data_dir / f"{index:05d}.json"
        if not data_file.exists():
            report["valid"] = False
            report["issues"].append(f"data file missing for episode {index}")
            continue
        frames = json.loads(data_file.read_text(encoding="utf-8"))["frames"]
        counted_frames += len(frames)
        if len(frames) != meta.get("length", -1):
            report["valid"] = False
            report["issues"].append(f"episode {index}: frames {len(frames)} != length {meta.get('length')}")
        for f in frames:
            for field_name in LEROBOT_FRAME_FIELDS:
                if field_name not in f:
                    report["valid"] = False
                    report["issues"].append(f"episode {index}: frame missing field {field_name}")

    if counted_frames != frame_count:
        report["valid"] = False
        report["issues"].append(f"counted frames {counted_frames} != total_frames {frame_count}")
    report["episode_count"] = episode_count
    report["frame_count"] = counted_frames
    return report


# ---------------------------------------------------------------------------
# GR00T custom-embodiment config template
# ---------------------------------------------------------------------------


def _skill_action_space() -> dict[str, dict[str, Any]]:
    """Derive the action space from the canonical skill contracts so the
    embodiment config can never drift from ``skill_contract.ALL_SKILLS``."""
    from novi.brain.skill_contract import ALL_SKILLS

    return {
        skill_id: {
            "description": contract.description,
            "parameters": dict(contract.parameter_schema),
            "risk_class": contract.risk_class,
        }
        for skill_id, contract in ALL_SKILLS.items()
    }


def build_gr00t_embodiment_config(
    *,
    robot_name: str = "novi",
    robot_model: str = "mac_brain_sim",
    body: str = "simulated_2d_diffdrive",
    sensors: list[dict[str, Any]] | None = None,
    control_frequency_hz: int = 10,
) -> dict[str, Any]:
    """Template for a GR00T custom-embodiment config (Exp 5 prep).

    Describes what Novi's embodiment looks like to a policy trainer: sensors,
    observation space (from the episode schema), and action space (from the
    skill contracts). The exact GR00T schema fields are validated against the
    GR00T release when the fine-tune step is entered; this template pins the
    Novi-side semantics.
    """
    default_sensors: list[dict[str, Any]] = [
        {"modality": "rgb", "rate_hz": control_frequency_hz, "role": "vision"},
        {"modality": "depth", "rate_hz": control_frequency_hz, "role": "depth"},
        {"modality": "proprioception", "state": ["x_m", "y_m", "heading_deg"], "role": "body_state"},
    ]
    return {
        "config_version": "1.0.0",
        "purpose": "GR00T custom-embodiment template (NVIDIA research §24 Exp 5 prep). "
        "Validate against the pinned GR00T release schema before fine-tuning.",
        "robot": {
            "name": robot_name,
            "model": robot_model,
            "body": body,
        },
        "sensors": sensors if sensors is not None else default_sensors,
        "observation_space": {
            "vision": {"rgb": [None, 3], "depth": [None, 1]},
            "robot_state": ["x_m", "y_m", "heading_deg"],
            "world_state_snapshot": "included_per_episode (NoviEpisode observation)",
        },
        "action_space": _skill_action_space(),
        "control_frequency_hz": control_frequency_hz,
        "data_format": {
            "episode_schema": "NoviEpisode",
            "lerobot_export": "export_lerobot_dataset()",
            "evidence_classes_preserved": True,
        },
        "notes": [
            "GR00T is research/skill infrastructure, not Novi's cognitive authority "
            "(research §8): the policy adapter receives only the state/action "
            "representation its task needs.",
            "Exp 5 runs only after the action space and hardware are stable (research §24).",
        ],
    }


def write_gr00t_embodiment_config(config: dict[str, Any], output_dir: str | Path) -> str:
    """Persist the embodiment config template as JSON; returns the file path."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "gr00t_embodiment_config.json"
    path.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)
