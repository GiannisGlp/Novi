"""Replay loader for cognitive contract fixtures (doc 26 §20)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cognition.replay.fixtures import SCENARIOS, all_scenarios


class ReplayLoadError(ValueError):
    pass


def load_scenario(scenario_id: str) -> dict[str, Any]:
    """Load a scenario fixture by id (from the embedded catalog or a JSON file)."""
    if scenario_id in SCENARIOS:
        return SCENARIOS[scenario_id]
    path = Path(scenario_id)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    raise ReplayLoadError(f"unknown scenario {scenario_id!r}")


def load_all() -> list[dict[str, Any]]:
    return all_scenarios()


def load_scenario_events(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the ordered event list of a scenario fixture."""
    events = scenario.get("events")
    if not isinstance(events, list):
        raise ReplayLoadError(f"scenario {scenario.get('scenario_id', '?')} has no events")
    return events
