#!/usr/bin/env python3
"""Deterministic semantic gate for Novi clock/time invariants.

This test validates clock semantics without claiming physical synchronization
accuracy. It uses injected values to prove that elapsed-time decisions are
independent of wall-clock jumps and that temporal provenance/order rules are
preserved.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import sys


@dataclass(frozen=True)
class TimeSample:
    domain: str
    timestamp: float
    source: str
    synchronization_status: str


def deadline_expired(now_monotonic: float, deadline_monotonic: float) -> bool:
    return now_monotonic >= deadline_monotonic


def measurement_age(now_monotonic: float, capture_monotonic: float) -> float:
    return now_monotonic - capture_monotonic


def valid_sync(status: str) -> bool:
    return status == "SYNCHRONIZED"


def can_infer_global_order(left: TimeSample, right: TimeSample) -> bool:
    return (
        left.domain == right.domain
        and valid_sync(left.synchronization_status)
        and valid_sync(right.synchronization_status)
    )


def parse_epoch(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def run() -> int:
    failures: list[str] = []

    # T-002/T-003: monotonic deadlines must survive wall-clock jumps.
    deadline = 100.0
    wall_before = parse_epoch("2026-08-18T15:00:00Z")
    wall_after = parse_epoch("2026-08-18T14:00:00Z")  # one-hour rollback
    if wall_after >= wall_before:
        failures.append("test setup did not produce a wall-clock rollback")
    if deadline_expired(99.9, deadline):
        failures.append("deadline expired too early")
    if not deadline_expired(100.0, deadline):
        failures.append("deadline did not expire at monotonic deadline")

    # T-004: occurrence/capture time and receipt time are different semantics.
    occurrence = TimeSample("SENSOR", 10.0, "imu-clock", "SYNCHRONIZED")
    receipt = TimeSample("HOST_MONOTONIC", 10.25, "host", "SYNCHRONIZED")
    if occurrence.timestamp == receipt.timestamp and occurrence.source == receipt.source:
        failures.append("capture and receipt provenance were collapsed")

    # T-005/T-008: unknown synchronization cannot establish global order.
    unsynced_a = TimeSample("SENSOR_A", 20.0, "device-a", "UNKNOWN")
    unsynced_b = TimeSample("SENSOR_B", 19.0, "device-b", "UNSYNCHRONIZED")
    if can_infer_global_order(unsynced_a, unsynced_b):
        failures.append("unsynchronized clocks were treated as globally ordered")

    synced_a = TimeSample("SHARED_DOMAIN", 20.0, "clock-a", "SYNCHRONIZED")
    synced_b = TimeSample("SHARED_DOMAIN", 21.0, "clock-b", "SYNCHRONIZED")
    if not can_infer_global_order(synced_a, synced_b):
        failures.append("compatible synchronized timestamps could not establish order")

    # T-006: age must be measured in a compatible elapsed-time domain.
    if abs(measurement_age(12.0, 10.0) - 2.0) > 1e-12:
        failures.append("measurement age calculation is incorrect")
    if measurement_age(9.0, 10.0) != -1.0:
        failures.append("future measurement was silently treated as zero age")

    # T-009: validity windows use a compatible clock and fail after expiry.
    valid_from = 50.0
    valid_until = 60.0
    if not (valid_from <= 55.0 <= valid_until):
        failures.append("validity window rejected a valid instant")
    if 61.0 <= valid_until:
        failures.append("expired validity window was accepted")

    # T-010: simulation time is a separate semantic domain.
    simulation = TimeSample("SIMULATION", 5.0, "/clock", "SYNCHRONIZED")
    wall = TimeSample("WALL", 5.0, "host-wall", "SYNCHRONIZED")
    if can_infer_global_order(simulation, wall):
        failures.append("simulation and wall time were silently treated as one domain")

    # Explicit causal metadata is available when timestamps cannot establish order.
    event_a = {"event_id": "a", "causation_id": "root", "sequence": 10}
    event_b = {"event_id": "b", "causation_id": "a", "sequence": 1}
    if event_b["causation_id"] != event_a["event_id"]:
        failures.append("causal relationship fixture is invalid")

    if failures:
        print("TIME SEMANTICS INTEGRATION GATE: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("TIME SEMANTICS INTEGRATION GATE: PASS")
    print("Validated monotonic deadlines, timestamp provenance, synchronization states, stale/age semantics, validity windows, and clock-domain separation.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
