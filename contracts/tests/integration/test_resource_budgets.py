#!/usr/bin/env python3
"""Deterministic validation of the Stage-1 resource budget baseline."""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BUDGET = ROOT / "resource_budgets.stage1.json"


def run() -> int:
    data = json.loads(BUDGET.read_text())
    r = data["resources"]
    classes = data["execution_classes"]
    failures: list[str] = []

    if r["cpu_sustained_utilization_max"] >= 0.9:
        failures.append("CPU budget leaves insufficient system headroom")
    if r["gpu_sustained_utilization_max"] >= 0.9:
        failures.append("GPU budget leaves insufficient critical-work headroom")
    if r["ram_working_set_gb_max"] >= 16:
        failures.append("RAM budget consumes the complete 16GB target")
    if r["model_memory_gb_max"] >= r["ram_working_set_gb_max"]:
        failures.append("model memory budget leaves no runtime memory headroom")
    if r["compute_power_w_target"] > r["compute_power_w_test_max"]:
        failures.append("target power exceeds test envelope")
    if r["compute_rail_current_a_min"] < (
        r["compute_power_w_test_max"] * 1.25 / r["compute_rail_voltage_v_nominal"]
    ):
        failures.append("compute rail current does not include 25% headroom")
    if r["soc_temperature_c_degraded_at"] >= r["soc_temperature_c_operating_limit"]:
        failures.append("thermal degradation begins too late")

    expected = {
        "S0": (2, 5, 1),
        "S1": (5, 10, 1),
        "S2": (25, 50, 2),
        "S3": (80, 120, 2),
        "S4": (500, 1000, 1),
    }
    for name, (p99, maximum, depth) in expected.items():
        cls = classes[name]
        if cls["p99_latency_ms"] != p99:
            failures.append(f"{name} p99 latency budget changed unexpectedly")
        if cls["max_latency_ms"] != maximum:
            failures.append(f"{name} maximum latency budget changed unexpectedly")
        if cls["queue_depth"] != depth:
            failures.append(f"{name} queue depth changed unexpectedly")

    for name, cls in classes.items():
        if cls["queue_depth"] is None or cls["queue_depth"] <= 0:
            failures.append(f"{name} queue is unbounded or invalid")

    if failures:
        print("RESOURCE BUDGET INTEGRATION GATE: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("RESOURCE BUDGET INTEGRATION GATE: PASS")
    print("Validated CPU/GPU/RAM/storage/power/thermal envelopes and bounded execution-class queues.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
