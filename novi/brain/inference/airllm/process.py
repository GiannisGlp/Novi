"""AirLLM process isolation (plan 12, §32 Phase 27).

The first implementation runs in-process; the interface is compatible with
either in-process or worker execution. An isolated worker is introduced only
if model lifecycle or memory fragmentation makes in-process unsafe — never
prematurely (plan 12, §32). This module owns the worker-mode configuration so
the runtime contract does not change when the mode does.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkerMode(str, Enum):
    IN_PROCESS = "in_process"
    WORKER = "worker"


@dataclass(frozen=True)
class WorkerConfig:
    mode: WorkerMode = WorkerMode.IN_PROCESS
    timeout_s: float = 30.0
    restart_on_fatal: bool = True
    extra_env: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"mode": self.mode.value, "timeout_s": self.timeout_s, "restart_on_fatal": self.restart_on_fatal}


def build_worker_command(model_id: str, artifact_path: str, *, mode: WorkerMode = WorkerMode.IN_PROCESS) -> list[str]:
    """Command for a worker process (in-process mode returns an empty command).

    Worker responsibilities (plan 12, §32): load model, accept inference RPC,
    return response, report health, release resources, terminate on fatal
    corruption.
    """
    if mode is WorkerMode.IN_PROCESS:
        return []
    return [
        "python",
        "-m",
        "novi.brain.inference.airllm.worker",
        "--model-id",
        model_id,
        "--artifact",
        artifact_path,
    ]
