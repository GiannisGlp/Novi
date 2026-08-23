"""Real resource telemetry for the Mac Brain.

Gap-analysis Step 3, item 19 (resource-aware behavioral adaptation): the
runtime must adapt to *real* host resource pressure, not only to the
failure-handler degraded mode. This module samples lightweight, read-only
host telemetry (CPU load, memory pressure) and maps it to a
``MultiSpeedRuntime.ResourceMode`` so the orchestrator can degrade gracefully
under genuine load.

Design notes
------------
- Stdlib-first: ``os.getloadavg()`` for CPU; memory uses ``psutil`` when it is
  installed and a bounded ``sysctl``/``vm_stat`` fallback on macOS otherwise.
- Read-only: no stress tests, no large allocations, no write probes, no
  device/driver changes (per the get-available-resources safety contract).
- A missing observation is ``None`` (unknown), never converted to "unlimited"
  or "healthy". Unknown signals do not force a downgrade.
- The most conservative (most degraded) signal wins when combining CPU and
  memory, and when combining telemetry with the failure-handler mode.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

from .multi_speed_runtime import ResourceMode

# Order from least to most degraded; used to pick the most conservative mode.
_MODE_RANK = {
    ResourceMode.FULL: 0,
    ResourceMode.DEGRADED: 1,
    ResourceMode.REACTIVE_ONLY: 2,
    ResourceMode.SAFE_MINIMUM: 3,
}


def combine_resource_modes(a: ResourceMode, b: ResourceMode) -> ResourceMode:
    """Return the more conservative (more degraded) of two resource modes."""
    return a if _MODE_RANK[a] >= _MODE_RANK[b] else b


@dataclass
class ResourceSample:
    """A point-in-time snapshot of host resource pressure.

    All fields are optional: ``None`` means the observation was unavailable and
    must not be treated as healthy.
    """

    cpu_load_1m: Optional[float] = None
    cpu_load_5m: Optional[float] = None
    cpu_count: Optional[int] = None
    available_memory_mib: Optional[float] = None
    total_memory_mib: Optional[float] = None
    memory_available_ratio: Optional[float] = None
    observed_at: float = field(default_factory=lambda: __import__("time").time())

    def snapshot(self) -> dict:
        return {
            "cpu_load_1m": self.cpu_load_1m,
            "cpu_load_5m": self.cpu_load_5m,
            "cpu_count": self.cpu_count,
            "available_memory_mib": self.available_memory_mib,
            "total_memory_mib": self.total_memory_mib,
            "memory_available_ratio": self.memory_available_ratio,
            "observed_at": self.observed_at,
        }


class ResourceTelemetry:
    """Samples real host resource pressure and maps it to a resource mode.

    Thresholds are deliberately conservative so the runtime degrades before
    the host is actually starved:

    - CPU load is normalized by core count (``load_1m / cpu_count``).
    - Memory pressure is the available/total ratio.
    - The most conservative of the CPU and memory verdicts is returned.
    """

    # CPU load (per core) thresholds.
    CPU_FULL_MAX = 0.7
    CPU_DEGRADED_MAX = 1.2
    CPU_REACTIVE_MAX = 2.0
    # Memory available-ratio thresholds.
    MEM_FULL_MIN = 0.35
    MEM_DEGRADED_MIN = 0.20
    MEM_REACTIVE_MIN = 0.10

    def __init__(self, *, cpu_count: Optional[int] = None) -> None:
        self._cpu_count = cpu_count or os.cpu_count()

    # -- sampling ---------------------------------------------------------

    def sample(self) -> ResourceSample:
        cpu = self._sample_cpu()
        mem = self._sample_memory()
        return ResourceSample(
            cpu_load_1m=cpu[0],
            cpu_load_5m=cpu[1],
            cpu_count=self._cpu_count,
            available_memory_mib=mem[0],
            total_memory_mib=mem[1],
            memory_available_ratio=(mem[0] / mem[1]) if (mem[0] and mem[1]) else None,
        )

    def _sample_cpu(self) -> tuple[Optional[float], Optional[float]]:
        try:
            one, five, _ = os.getloadavg()
            return float(one), float(five)
        except (OSError, AttributeError):
            return None, None

    def _sample_memory(self) -> tuple[Optional[float], Optional[float]]:
        # Prefer psutil when present (broader cross-platform coverage).
        try:
            import psutil  # type: ignore

            vm = psutil.virtual_memory()
            return vm.available / (1024 * 1024), vm.total / (1024 * 1024)
        except Exception:
            pass
        if sys.platform == "darwin":
            return self._memory_macos()
        return None, None

    def _memory_macos(self) -> tuple[Optional[float], Optional[float]]:
        """Best-effort macOS memory via bounded sysctl/vm_stat (no shell)."""
        try:
            total = self._sysctl_int("hw.memsize")
            if not total:
                return None, None
            pagesize = self._sysctl_int("hw.pagesize") or 4096
            vm = self._vm_stat()
            free = vm.get("Pages free", 0)
            inactive = vm.get("Pages inactive", 0)
            speculative = vm.get("Pages speculative", 0)
            available = (free + inactive + speculative) * pagesize
            return available / (1024 * 1024), total / (1024 * 1024)
        except Exception:
            return None, None

    def _sysctl_int(self, key: str) -> Optional[int]:
        try:
            out = subprocess.run(
                ["sysctl", "-n", key],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            return int(out.stdout.strip())
        except Exception:
            return None

    def _vm_stat(self) -> dict[str, int]:
        try:
            out = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except Exception:
            return {}
        result: dict[str, int] = {}
        for line in out.stdout.splitlines():
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            try:
                result[key.strip()] = int(val.strip().rstrip("."))
            except ValueError:
                continue
        return result

    # -- mapping ----------------------------------------------------------

    def to_resource_mode(self, sample: ResourceSample) -> ResourceMode:
        """Map a sample to the most conservative resource mode."""
        verdicts: list[ResourceMode] = []
        if sample.cpu_load_1m is not None and self._cpu_count:
            per_core = sample.cpu_load_1m / self._cpu_count
            if per_core >= self.CPU_REACTIVE_MAX:
                verdicts.append(ResourceMode.SAFE_MINIMUM)
            elif per_core >= self.CPU_DEGRADED_MAX:
                verdicts.append(ResourceMode.REACTIVE_ONLY)
            elif per_core >= self.CPU_FULL_MAX:
                verdicts.append(ResourceMode.DEGRADED)
            else:
                verdicts.append(ResourceMode.FULL)
        if sample.memory_available_ratio is not None:
            ratio = sample.memory_available_ratio
            if ratio <= self.MEM_REACTIVE_MIN:
                verdicts.append(ResourceMode.SAFE_MINIMUM)
            elif ratio <= self.MEM_DEGRADED_MIN:
                verdicts.append(ResourceMode.REACTIVE_ONLY)
            elif ratio <= self.MEM_FULL_MIN:
                verdicts.append(ResourceMode.DEGRADED)
            else:
                verdicts.append(ResourceMode.FULL)
        if not verdicts:
            # No usable signal: do not invent pressure.
            return ResourceMode.FULL
        return max(verdicts, key=lambda m: _MODE_RANK[m])
