"""Replay fixtures + harness for the typed cognition contracts (doc 26 §20)."""

from cognition.replay.fixtures import SCENARIOS, all_scenarios
from cognition.replay.loader import ReplayLoadError, load_all, load_scenario, load_scenario_events
from cognition.replay.runner import (
    ReplayResult,
    ReplayStep,
    replay_all,
    replay_scenario,
    summarize,
)

__all__ = [
    "SCENARIOS",
    "all_scenarios",
    "ReplayLoadError",
    "load_all",
    "load_scenario",
    "load_scenario_events",
    "ReplayResult",
    "ReplayStep",
    "replay_all",
    "replay_scenario",
    "summarize",
]
