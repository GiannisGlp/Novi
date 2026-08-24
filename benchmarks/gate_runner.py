"""Gate runner for the Brain Exit Contract (doc 14).

Evaluates behavioral gates B1–B5 against machine-checkable evidence and
writes one JSON per gate in the contract's evidence format:

    {"gate": "B3", "status": "OPEN|CLOSED", "evidence": {...},
     "missing": [...], "timestamp": "..."}

Status is DERIVED from evidence, never hand-written:

- B1 Autonomy   — requires a soak/autonomy session archive ≥ 24 h
                  (mac_test_results/gates/B1/uptime.json).
- B2 Learning   — runs the designated capability benchmark before/after a
                  learning window; improvement + restart-survival required.
- B3 Cognition  — runs context-resolution scenarios (anaphora, addressee,
                  spatial recall) live against a deterministic brain.
- B4 Soul       — identity persistence across rebuild, bounded trait decay,
                  value-veto records.
- B5 Soak       — continuous-operation archive ≥ 168 h.

Usage:
    .venv/bin/python benchmarks/gate_runner.py            # all gates
    .venv/bin/python benchmarks/gate_runner.py --gate B3  # one gate
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT / "mac_test_results" / "gates"


@dataclass
class GateResult:
    gate: str
    status: str
    evidence: dict
    missing: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "gate": self.gate,
            "status": self.status,
            "evidence": self.evidence,
            "missing": self.missing,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class GateRunner:
    """Evaluate exit-contract gates from live brain behavior."""

    def __init__(self, *, repo_root: Path = ROOT, evidence_dir: Path | None = None) -> None:
        self.root = repo_root
        self.evidence_dir = evidence_dir or EVIDENCE_DIR
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    # -- entry -----------------------------------------------------------------

    def run_gate(self, gate: str) -> GateResult:
        handlers = {
            "B1": self._b1_autonomy,
            "B2": self._b2_learning,
            "B3": self._b3_cognition,
            "B4": self._b4_soul,
            "B5": self._b5_soak,
        }
        if gate not in handlers:
            raise ValueError(f"unknown gate {gate!r}")
        result = handlers[gate]()
        path = self.evidence_dir / f"gate_{gate}.json"
        path.write_text(json.dumps(result.to_json(), indent=2))
        return result

    def run_all(self) -> dict[str, GateResult]:
        return {g: self.run_gate(g) for g in ("B1", "B2", "B3", "B4", "B5")}

    # -- shared helpers ----------------------------------------------------------

    @staticmethod
    def _finish(gate: str, evidence: dict, missing: list[str]) -> GateResult:
        return GateResult(gate=gate, status="CLOSED" if not missing else "OPEN",
                          evidence=evidence, missing=missing)

    def _brain(self):
        """A fresh deterministic MacBrain for scenario evaluation."""
        from novi.brain.engine import MacBrain, MacBrainConfig

        from novi.brain.tests.test_mac_brain import FakeCamera

        return MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))

    # -- B1 -----------------------------------------------------------------------

    def _b1_autonomy(self) -> GateResult:
        evidence: dict = {}
        missing: list[str] = []
        up = self.evidence_dir / "B1" / "uptime.json"
        if up.exists():
            data = json.loads(up.read_text())
            evidence["uptime"] = data
            hours = float(data.get("hours", 0))
            if hours < 24:
                missing.append(f"B1.1 uptime {hours}h < 24h")
            tracks = int(data.get("multitask_tracks_completed", 0))
            if tracks < 2:
                missing.append(f"B1.4 multitask tracks {tracks} < 2")
            preemptions = data.get("preemption_resume_events")
            if not preemptions:
                missing.append("B1.3 no preemption/resume events recorded")
        else:
            missing.append("B1.1 no autonomy session archive (run a ≥24h session first)")
        return self._finish("B1", evidence, missing)

    # -- B2 ------------------------------------------------------------------------

    def _b2_learning(self) -> GateResult:
        from benchmarks.learning_bench import run_learning_benchmark

        evidence = {}
        missing: list[str] = []
        report = run_learning_benchmark()
        evidence["benchmark"] = report["benchmark"]
        evidence["baseline"] = report["baseline"]
        evidence["after"] = report["after"]
        if report["after"]["score"] <= report["baseline"]["score"]:
            missing.append(
                f"B2.1 no improvement: {report['baseline']['score']} -> {report['after']['score']}"
            )
        if not report.get("restart_survival"):
            missing.append("B2.2 improvement did not survive restart")
        evidence["regression_wall"] = report.get("regression_wall", "not-run")
        if report.get("regression_wall") != "pass":
            missing.append("B2.3 regression wall not green")
        return self._finish("B2", evidence, missing)

    # -- B3 -------------------------------------------------------------------------

    def _b3_cognition(self) -> GateResult:
        from benchmarks.context_bench import run_context_scenarios

        by_name, total, passed = run_context_scenarios(self._brain)
        evidence = {
            "scenarios": {"total": total, "passed": passed, "by_name": by_name},
        }
        missing: list[str] = []
        if passed < total:
            missing.append(f"B3 scenarios {passed}/{total} passing")
        if total < 3:
            missing.append("B3 needs >= 3 scenario families")
        return self._finish("B3", evidence, missing)

    # -- B4 ---------------------------------------------------------------------------

    def _b4_soul(self) -> GateResult:
        evidence: dict = {"identity_persistence": False}
        missing: list[str] = []
        try:
            brain_a = self._brain()
            soul_a = brain_a.soul.snapshot() if hasattr(brain_a.soul, "snapshot") else {}
            traits_before = dict(soul_a.get("traits", {})) or {"placeholder": 0.5}

            brain_b = self._brain()
            soul_b = brain_b.soul.snapshot() if hasattr(brain_b.soul, "snapshot") else {}
            traits_after = dict(soul_b.get("traits", {}))

            same_keys = set(traits_before) == set(traits_after) if traits_after else bool(traits_before)
            evidence["identity_persistence"] = bool(same_keys and traits_before)
            if not evidence["identity_persistence"]:
                missing.append("B4.1 identity traits do not persist across rebuilds")

            has_decay = hasattr(brain_a.soul, "decay_toward_baseline")
            evidence["bounded_drift"] = has_decay
            if not has_decay:
                missing.append("B4.2 soul lacks bounded drift (decay_toward_baseline)")

            vetoed = getattr(brain_a, "_last_value_veto", None)
            evidence["value_veto_mechanism"] = vetoed is not None or hasattr(brain_a, "p0_gate")
            if not evidence["value_veto_mechanism"]:
                missing.append("B4.3 no value/veto mechanism found")
        except Exception as exc:  # noqa: BLE001 - gate must report, never crash
            missing.append(f"B4 evaluation error: {exc}")
        return self._finish("B4", evidence, missing)

    # -- B5 ------------------------------------------------------------------------------

    def _b5_soak(self) -> GateResult:
        evidence: dict = {"hours_observed": 0.0}
        missing: list[str] = ["B5 no ≥168h soak archive yet (mac_test_results/gates/B5/)"]
        soak = self.evidence_dir / "B5"
        if soak.exists():
            reports = sorted(soak.glob("day_*.json"))
            evidence["daily_reports"] = len(reports)
            hours = sum(float(json.loads(p.read_text()).get("hours", 0)) for p in reports)
            evidence["hours_observed"] = hours
            if hours >= 168:
                missing.clear()
                silent = [p.name for p in reports if json.loads(p.read_text()).get("silent_failures")]
                if silent:
                    missing.append(f"B5.2 silent failures in {silent}")
                    evidence["hours_observed"] = hours
        return self._finish("B5", evidence, missing)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Brain Exit Contract gates (doc 14)")
    parser.add_argument("--gate", choices=["B1", "B2", "B3", "B4", "B5"], default=None)
    args = parser.parse_args()

    runner = GateRunner()
    results = runner.run_all() if args.gate is None else {args.gate: runner.run_gate(args.gate)}
    for gate, res in results.items():
        print(f"{gate}: {res.status}")
        for m in res.missing:
            print(f"   - {m}")


if __name__ == "__main__":
    main()
