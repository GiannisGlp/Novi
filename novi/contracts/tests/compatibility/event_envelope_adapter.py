#!/usr/bin/env python3
"""Explicit 1.0 -> 1.1 EventEnvelope compatibility adapter."""
from __future__ import annotations

import copy


def upgrade_1_0_to_1_1(event: dict) -> dict:
    """Upgrade a 1.0 EventEnvelope without changing existing semantics."""
    if event.get("schema_version") != "1.0.0":
        raise ValueError("adapter accepts only EventEnvelope 1.0.0")
    upgraded = copy.deepcopy(event)
    upgraded["schema_version"] = "1.1.0"
    return upgraded
