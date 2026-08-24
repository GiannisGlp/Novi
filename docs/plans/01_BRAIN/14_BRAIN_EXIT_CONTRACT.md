# Brain — Exit Contract

## Objective

Define the measurable condition under which the Brain workstream (`01_BRAIN/`) is declared accepted on the Mac prototype body, making the compute decision (Jetson AGX Orin 64GB vs AGX Thor) a data-backed formality under [`05-hardware/26_HARDWARE_SELECTION_AND_BOM_BASELINE.md`](../../05-hardware/26_HARDWARE_SELECTION_AND_BOM_BASELINE.md) freeze gate §31.

This contract answers: **"the brain works as intended"** as falsifiable evidence, not recollection.

It extends, and does not replace:

- [`12_BRAIN_INTEGRATION_GATE.md`](12_BRAIN_INTEGRATION_GATE.md) — component/pipeline integration evidence;
- [`00_IMPLEMENTATION_PROGRAM.md`](../00_IMPLEMENTATION_PROGRAM.md) — global lifecycle (…→ EVIDENCE → SYSTEM VALIDATE → ACCEPT);
- [`13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md`](13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md) — gap closure plan feeding these gates.

---

## Behavioral gates

Each gate is a standalone acceptance target. All five must hold simultaneously before the exit condition fires. Gate order below is presentation order, not build order; build sequencing remains governed by the gap audit plan.

### B1 — Autonomy

Novi runs its own life, unprompted.

**Requirements:**

1. Continuous unattended operation ≥ 24 h on the Mac body.
2. Goal pursuit initiated from internal motivations/soul state — not from user prompts.
3. Interruption handling: external events (speech, person present, novel stimulus) preempt and resume or explicitly abandon active tracks; no silent task loss.
4. Multitasking: ≥ 2 concurrent background goal tracks progress in one session while the cognitive loop stays responsive.
5. Every autonomous action carries decision provenance (which motivation, which context package, which expectation).

**Required evidence:** autonomy session logs; preemption/resume event traces; multitask track completion records; provenance chains per action proposal.

### B2 — Self-learning

Novi measurably improves from experience only.

**Requirements:**

1. A designated capability benchmark improves after experience accumulation (consolidation, curiosity cycles, prediction-error learning) with **no code changes and no direct teaching in the improvement window**.
2. Improvement survives restart (persisted learning, not runtime warm-up).
3. The regression wall holds: full test suite + benchmark suite green after each consolidation cycle; any adopted self-change carries audit-trail provenance (what changed, why, what evidence).
4. Failed experiments are retained and cited (learning includes negative results).

**Required evidence:** before/after benchmark runs from pinned configurations; adoption audit records; regression wall run logs; restart-survival proof.

### B3 — Cognition and reasoning

Reasoning is typed, grounded, and prediction-driven.

**Requirements:**

1. Typed cognition canonical in the main loop (closes G1): every cycle emits a typed situation snapshot; legacy structures are projections, never parallel authorities.
2. Context grounding canonical: dialogue and action proposals consume a `ContextPackage`; addressee resolution uses identity providers, not regex (closes G2/G3 core).
3. Spatial/temporal binding: memories are written with place/time/persons/goal tags; retrieval by current context works (closes G7).
4. Predictions are made, scored against outcomes, and prediction error feeds learning (closes G10).
5. Belief updates follow the Bayesian belief system design (closes G5).

**Required evidence:** context-resolution benchmark suite (scripted scenarios: anaphora, addressee, spatial recall); calibration harness output for predictions; determinism tests (same inputs → same situation id).

### B4 — Soul

Personality is stable, expressive, and governing.

**Requirements:**

1. Identity continuous across restarts (self-model persists and reconciles).
2. Personality drift is bounded and slow-clock: measurable but non-oscillating over weeks; drift events logged with causes.
3. Values demonstrably veto or reshape proposed actions (soul participates in governance, observably).
4. Affect shapes expression within documented bounds (docs/06-soul/05 §12/§14 behavior maintained).
5. Motivations feed attention ranking and goal selection (closes G11's steering half).

**Required evidence:** long-horizon personality stability measurements; value-veto case records; motivation-influence traces on attention/goal selection.

### B5 — Soak

A week of continuous life.

**Requirements:**

1. ≥ 168 h continuous operation with daily self-written reports (what happened, what was learned, what failed).
2. Zero silent failures: every degradation event visible in health/capability state and reflected in behavior.
3. Human interaction limited to natural conversation — no maintenance commands during the soak.
4. Memory footprint and retrieval quality remain stable across the week (consolidation compresses; no unbounded growth).

**Required evidence:** soak session archive; daily reports; degradation event log; storage/retrieval trend metrics.

---

## Resource-parity rules

Every capability Novi uses on the Mac must name a board-plausible local equivalent for the Jetson deployment class. Disallowed in the cognitive path: cloud API calls; models whose memory/bandwidth profile has no Orin/Thor-plausible mapping; power-blind autonomy logic.

Simulated telemetry rule: battery voltage, thermal state, and power budget are emulated behind the hardware-health interface from now on, so power-aware autonomy (hardware doc §14/§20) is implemented and tested before real telemetry exists. Jetson integration later swaps simulation for real sensors behind the same interface.

Parity table maintenance: `docs/plans/01_BRAIN/resource_parity_table.md` lists each capability → Mac provider → deployment-class equivalent → status.

---

## Evidence format

All gate evidence lands in the existing evidence pattern (`brain_evidence.json` lineage), extended with:

```json
{
  "gate": "B2",
  "capability": "<benchmarked-capability>",
  "before": {"config": "...", "score": 0.0},
  "after": {"config": "...", "score": 0.0},
  "experience_window": {"cycles": 0, "interactions": 0},
  "regression_wall": "pass",
  "provenance": ["audit-record-id", ...],
  "timestamp": "..."
}
```

Evidence must be reproducible from pinned configurations (per `12_BRAIN_INTEGRATION_GATE.md` requirement 6). A gate claim without machine-checkable evidence does not count.

---

## Hardware handoff trigger

When B1–B5 all hold:

1. Run the compute decision harness (benchmark profile from `05-hardware/26` §29) on candidate boards when available.
2. Freeze-gate §31 conditions evaluate on measured workload.
3. BOM decision proceeds per the hardware workstream — not before.

Until then, neither board choice blocks brain work, and brain work does not assume either board beyond the parity rules above.

---

## Known limits of this phase

Not validatable on the Mac, deferred to body integration: multi-camera bandwidth, sustained-load thermal throttling, real power duty cycles, actuator-safety integration, physical sensor fusion.

---

## Open questions (decide before first gate run)

1. **Gate strictness**: hard thresholds vs N-consecutive-pass policy per gate (e.g., B1: single 24 h pass vs 3 consecutive).
2. **B2 demonstration target**: which capability benchmark defines "measurably improves" (candidate: spatial-context recall precision; alternative: prediction accuracy on routine events).
3. **Adoption authority**: initially human-gated overnight adoptions with per-category earned autonomy, or immediate autonomous adoption inside the regression wall?

---

## Gate status

Derived from `benchmarks/gate_runner.py` (evidence JSON under `mac_test_results/gates/`). Status is computed, never hand-written.

| Gate | Status | Evidence |
|---|---|---|
| B1 Autonomy | **OPEN** | requires ≥24 h session archive (`mac_test_results/gates/B1/uptime.json`) |
| B2 Self-learning | **CLOSED** (2026-08-23) | spatial-context-recall 0.0 → 1.0 after experience; restart-survival ✓; regression wall pass |
| B3 Cognition and reasoning | **CLOSED** (2026-08-23) | context scenarios 3/3 — anaphora ✓, addressee ✓, spatial_recall ✓ (closes G2/G3/G7 evidence) |
| B4 Soul | **CLOSED** (2026-08-23) | identity persistence across rebuilds ✓; bounded drift (`decay_toward_baseline`) ✓; value/veto mechanism present (P0 gate) ✓ |
| B5 Soak | **OPEN** | requires ≥168 h continuous-operation archive |

The exit condition is: all five CLOSED with reproducible evidence, parity table complete, regression wall green.

### Remaining path to exit

1. **B1**: run a ≥24 h unattended autonomy session with preemption/resume + multitask tracking writing `uptime.json`.
2. **B5**: run the ≥168 h soak with daily reports (can subsume B1's window if instrumented for both).
3. Keep `gate_runner.py` green on B2–B4 as code evolves.
