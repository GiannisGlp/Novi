#!/usr/bin/env python3
"""Cross-system acceptance evidence (roadmap item 29).

Runs the canonical acceptance gates (P0–P3) plus the Step-1 pipeline items
(spatial model, typed cognition emission, learning pipeline, memory-class
decision) end-to-end against a live MacBrain, verifies the fast suite is green
(subprocess), runs the architecture-integrity checker, and writes an evidence
record into docs/plans/EVIDENCE/mac/<stamp>/:

  - one evidence file summarizing the cross-system acceptance run (E2
    reproducible / E3 integration evidence class);
  - commit_sha.txt and collection_time.txt;
  - an INDEX.md row for the run.

This is the completion-gate review for roadmap item 29: Soul → Cognition →
Memory → Autonomy → Safety → Brain exercised together on the Mac.

Usage:
    python scripts/mac/cross_system_acceptance.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EVIDENCE_ROOT = ROOT / "docs" / "plans" / "EVIDENCE" / "mac"
INDEX = EVIDENCE_ROOT / "INDEX.md"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _build_brain():
    from novi.brain.b2_perception import Detection, DeterministicPerceptionBackend, SpecialistPerception
    from novi.brain.contracts import utc_now
    from novi.brain.io import CameraFrame
    from novi.brain.engine import MacBrain, MacBrainConfig

    class FakeCamera:
        def __init__(self):
            self.sequence = 0

        def read(self):
            self.sequence += 1
            return CameraFrame(frame_id=f"acc-{self.sequence}", captured_at=utc_now(),
                               width=1, height=1, payload=b"frame",
                               metadata={"backend": "test"})

        def close(self):
            pass

    class PersonBackend(DeterministicPerceptionBackend):
        def detect(self, frame):
            return (Detection("alice", 0.95, (0.0, 0.0, 0.3, 0.5)),)

    brain = MacBrain(
        camera=FakeCamera(),
        perception=SpecialistPerception(PersonBackend()),
        config=MacBrainConfig(curiosity_enabled=False),
    )
    brain.start()
    brain.step()
    return brain


def _run_gates() -> dict:
    """Run each priority gate against a FRESH brain instance.

    Gates mutate long-lived brain state (fatigue/cooldown/affect/social
    memory), so sharing one instance across gates would make later gates
    order-dependent. Each gate is a clean-boot acceptance run instead.
    """
    from novi.brain.p0_gate_runner import run_acceptance_gate
    from novi.brain.soul_acceptance import AcceptanceClass

    results = {}
    all_green = True
    for priority in (AcceptanceClass.P0, AcceptanceClass.P1,
                     AcceptanceClass.P2, AcceptanceClass.P3):
        brain = _build_brain()
        try:
            gate = run_acceptance_gate(brain, priority)
        finally:
            brain.stop()
        green = gate.passed
        all_green = all_green and green
        results[priority.value] = {
            "passed": green,
            "total": gate.total_scenarios,
            "passed_scenarios": gate.passed_scenarios,
            "failed_scenarios": gate.failed_scenarios,
            "pending": gate.pending_scenarios,
            "violations": list(gate.violations) if gate.violations else [],
            "is_complete": gate.is_complete,
        }
    return results, all_green


def _run_pipeline_checks(brain) -> list[dict]:
    checks = []

    # Spatial model: place robot, resolve region, reachable regions.
    from novi.brain.spatial_map import SpatialReference
    brain.spatial.place("robot_001", SpatialReference(
        frame_id="map", pose={"x": 5.0, "y": 2.0}))
    region = brain.spatial.region_of("robot_001")
    reach = brain.spatial.reachable_regions(region) if region else set()
    checks.append({
        "check": "spatial_model",
        "passed": region in ("living_room", "kitchen") and len(reach) >= 2,
        "detail": {"region": region, "reachable": sorted(reach)},
    })

    # Typed cognition emission (validated contracts).
    out = brain.cognition_typed()
    decision_ok = bool(out.get("decision") and out["decision"]["situation_ref"])
    checks.append({
        "check": "typed_cognition",
        "passed": bool(out.get("situation")) and decision_ok,
        "detail": {"decision": out["decision"]["interpretation"] if out.get("decision") else None},
    })

    # Learning pipeline: promotion, correction provenance, counterfactual isolation.
    for i in range(3):
        brain.observe_knowledge("alice", "prefers", "concise_replies",
                                confidence=0.9, source=f"chat-{i}")
    promoted = brain.knowledge.leading("alice", "prefers") is not None
    changed = brain.correct_knowledge("alice", "prefers", "detailed_replies", person="alice")
    corrected = brain.knowledge.leading("alice", "prefers").object == "detailed_replies"
    cf = brain.counterfactual(premise="if door closed", if_evidence={"door": "closed"},
                              then_prediction="alice knocks")
    checks.append({
        "check": "learning_pipeline",
        "passed": promoted and changed and corrected and cf["epistemic"] == "SIMULATED",
        "detail": {"promoted": promoted, "corrected": corrected,
                   "counterfactual_status": cf["status"]},
    })

    # Memory-class decision is recorded.
    mc = brain.memory_classes.snapshot()
    checks.append({
        "check": "memory_class_decision",
        "passed": "semantic" in mc["implemented"] and "prospective" in mc["deferred"],
        "detail": {"deferred": mc["deferred"]},
    })

    # Event bus carries the new cross-system events.
    event_types = {e.get("event_type") for e in brain.events}
    needed = {"cognition.typed", "learning.candidate", "learning.corrected"}
    checks.append({
        "check": "event_bus_observability",
        "passed": needed <= event_types,
        "detail": {"found": sorted(needed & event_types)},
    })
    return checks


def _run_full_suite() -> dict:
    """Run the fast suite + integrity checker; returns summary."""
    fast = subprocess.run(
        [sys.executable, "-m", "pytest", "novi/brain/tests",
         "novi/contracts/tests", "novi/cognition/tests", "-q", "--disable-warnings"],
        cwd=ROOT, capture_output=True, text=True,
    )
    integrity = subprocess.run(
        [sys.executable, "scripts/validate_architecture_integrity.py"],
        cwd=ROOT, capture_output=True, text=True,
    )
    # Parse "N failed, M passed" / "N passed" summary line.
    import re
    combined = fast.stdout + fast.stderr
    passed = 0
    failed = None
    for line in combined.splitlines():
        m = re.search(r"(\d+) passed(?: in|\b)", line)
        fm = re.search(r"(\d+) failed", line)
        if m:
            passed = int(m.group(1))
        if fm:
            failed = int(fm.group(1))
    return {
        "full_suite_passed": fast.returncode == 0,
        "full_suite_count": passed,
        "full_suite_failed": failed,
        "full_suite_output_tail": combined.strip().splitlines()[-3:],
        "integrity_passed": integrity.returncode == 0,
        "integrity_output_tail": (integrity.stdout + integrity.stderr).strip().splitlines()[-3:],
    }


def main() -> int:
    gates, gates_green = _run_gates()

    brain = _build_brain()
    try:
        checks = _run_pipeline_checks(brain)
        suite = _run_full_suite()
    finally:
        brain.stop()

    all_green = gates_green and all(c["passed"] for c in checks) and suite["full_suite_passed"] and suite["integrity_passed"]

    stamp = utc_stamp()
    dest = EVIDENCE_ROOT / stamp
    dest.mkdir(parents=True, exist_ok=True)

    record = {
        "run_id": stamp,
        "kind": "cross_system_acceptance",
        "roadmap_item": 29,
        "status": "PASS" if all_green else "FAIL",
        "evidence_class": "E3",  # integration across brain subsystems (docs/01 §10)
        "environment": {"python": sys.version, "platform": sys.platform},
        "gates": gates,
        "pipeline_checks": checks,
        "full_suite": {"passed": suite["full_suite_passed"], "count": suite["full_suite_count"]},
        "integrity": {"passed": suite["integrity_passed"]},
        "failures": [],
    }
    if not all_green:
        for c in checks:
            if not c["passed"]:
                record["failures"].append(c["check"])
        for p, g in gates.items():
            if not g["passed"]:
                record["failures"].append(f"gate:{p}")
        if not suite["full_suite_passed"]:
            record["failures"].append("full_suite")
        if not suite["integrity_passed"]:
            record["failures"].append("integrity")

    fname = "cross_system_acceptance.json"
    (dest / fname).write_text(json.dumps(record, indent=2, default=str) + "\n")
    (dest / "commit_sha.txt").write_text(git_sha() + "\n")
    (dest / "collection_time.txt").write_text(f"Collected UTC: {stamp}\n")

    with INDEX.open("a", encoding="utf-8") as fh:
        fh.write(
            f"\n## Step 10 — Cross-system acceptance (roadmap item 29)\n"
            f"| Cross-system acceptance (Soul→Cognition→Memory→Autonomy→Safety→Runtime) | "
            f"`{stamp}/{fname}` | E3 integration — "
            f"{'PASS' if all_green else 'FAIL'} (gates: {len(gates)}, pipeline checks: {len(checks)}, "
            f"fast suite: {suite['full_suite_count']}, integrity: {suite['integrity_passed']}) |\n"
        )

    print(f"Written cross-system acceptance evidence to {dest}")
    for p, g in gates.items():
        print(f"  gate {p}: passed={g['passed']} total={g['total']} pending={g['pending']}")
    for c in checks:
        print(f"  check {c['check']}: {'PASS' if c['passed'] else 'FAIL'}")
    print(f"  full suite: {suite['full_suite_count']} passed (exit {0 if suite['full_suite_passed'] else 1})")
    print(f"  architecture integrity: {'PASS' if suite['integrity_passed'] else 'FAIL'}")
    return 0 if all_green else 1


if __name__ == "__main__":
    raise SystemExit(main())
