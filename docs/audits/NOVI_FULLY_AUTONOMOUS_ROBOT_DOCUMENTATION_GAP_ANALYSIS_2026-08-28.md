# Novi — Fully Autonomous Robot: Documentation Gap Analysis

**Status:** ANALYSIS — documentation-only; no implementation
**Date:** 2026-08-28
**Scope:** every document under `docs/` vs. the definition of a *fully autonomous robot* in `docs/00-strategy/NOVI_NORTH_STAR.md`
**Method:** six parallel documentation surveys (robotics/control, simulation, hardware, validation, security/safety, action/skill/embodiment) plus direct verification of the plan-workstream indexes, the docs authority map, and the North Star itself. Every verdict below cites file:line evidence; nothing was modified.
**Predecessor:** [`docs/audits/NOVI_CONSOLIDATED_GAP_ANALYSIS_2026-08-26.md`](../../audits/NOVI_CONSOLIDATED_GAP_ANALYSIS_2026-08-26.md) — this doc supersedes it for the *physical/embodied* path.

---

## 1. The target — what "fully autonomous robot" means in the North Star

The North Star defines the end state across several interlocking sections:

- **Seven fundamental properties** (§5, `NOVI_NORTH_STAR.md:121-280`): Continuity, Situated Understanding, Agency, Memory and Learning, Reasoning and Planning, **Embodied Action**, Social and Personal Continuity.
- **The physical body** (§12, `:545-559`): cameras, microphones, speakers, **mobility**, orientation/head movement, display, environmental sensors, network, onboard compute, battery/power, **emergency-stop and hardware safety mechanisms**. The body is explicitly a **replaceable embodiment** (`:561-572`).
- **The development path** (§14, `:603-680`): V0–V8. **V5 Simulated Embodiment**, **V6 Learned Skills**, **V7 Physical Novi**, **V8 Persistent Autonomous Novi** are the stages this analysis concerns.
- **The first physical milestone** (§16, `:695-703`):

  > "A physically embodied Novi that can autonomously perceive a bounded environment, maintain a grounded world model, pursue explicitly defined goals, **navigate and interact through approved skills**, learn from task outcomes, and recover safely from expected failures without requiring a human prompt for every action."

- **Success criteria** (§19, `:752-822`): Cognitive / Autonomous / Learning / **Embodied** (perception reliability, localization, navigation, action execution, closed-loop feedback, sim-to-real transfer) / **Safety** (zero unauthorized actuator access, emergency-stop reliability, policy enforcement, bounded behavior, safe failure, auditable actions, protected safety invariants) / Reliability / Social.
- **Safety is a permanent boundary** (§23, `:942`): the cognitive intention → action proposal → governance → safety → **skill → robotics middleware (ROS 2 / ros2_control) → controller → actuator** → consequence → observation → world-model update chain. Novi should never need to give an LLM direct motor authority.

**This analysis measures documentation coverage against that definition.** The question is not "is it implemented" — it is "if a new engineer (or an ECC subagent) wanted to build the physical Novi, would the docs tell them what to build, how to verify it, and how to keep it safe?" The answer is: **not yet — the cognitive half yes, the embodied half no.**

---

## 2. Headline finding

The documentation is **comprehensive and closure-grade for the cognitive/software path** (brain, memory, cognition, autonomy, soul, system architecture all have canonical, P0-normative specs and closed evidence). The **physical/embodied path is nearly absent**:

1. **Every physical robot workstream is a one-page `PLANNED` placeholder.** `docs/plans/03_LOCALIZATION` through `14_DEPLOYMENT` (13 indexes; e.g. `05_NAVIGATION/00_..._INDEX.md` = 18 lines, "Status: PLANNED") contain only a scope line and a planned-progression list. `02_PERCEPTION` is the sole workstream with real content.
2. **Four of the twelve Global Completion Gate domains have no authoritative document and no domain directory:** Simulation, Validation, Security, and Deployment. The docs authority map (`NOVI_DOCUMENTATION_MASTER_INDEX.md`) covers Strategy, System Architecture, Brain, Autonomy, Cognition, Memory, Hardware, Soul — and stops; the tracker's §5.9/§5.10/§5.11 sections are "must create / IN PROGRESS — P0 unification required" stubs.
3. **`docs/05-hardware/` promises 26 documents and contains 5.** The README table (`05-hardware/README.md:24-49`) advertises `01_COMPUTE...23_HARDWARE_VALIDATION`; none of those files exist. The BOM (`26_...md`) is a template with **zero populated rows**; every subsystem status row reads "Missing" or "Not frozen" (`26_...md:844-869`).
4. **The two safety/security artifacts the tracker itself calls P0 are formally not started:** the consolidated physical-AI threat model (§5.11 / readiness-audit GAP-019) and the physical safety case (GAP-014).
5. **The embodied-action chain breaks at the skill boundary.** The plan/action-proposal half is canonical; the half from *skill → robotics middleware → controller → actuator* has no authoritative design anywhere — it exists only as references inside specs, and the one detailed skill spec (`archive/84_...`) is marked **NON-NORMATIVE/archived**.

The tracker's own rule applies: "Never mark a domain COMPLETE merely because a document exists" (`NOVI_DOCUMENTATION_AND_IMPLEMENTATION_COMPLETION_TRACKER.md:92`). None of these domains are complete.

---

## 3. North Star property coverage matrix

| North Star property | What exists | Verdict |
|---|---|---|
| 5.1 Continuity (`:121`) | Canonical episodic memory, identity, persistence (`01_MEMORY_TAXONOMY`, `02_MEMORY_LIFECYCLE`, Brain Exit Contract B5 soak) | **COVERED** |
| 5.2 Situated Understanding (`:143`) | Perception architecture, world model, multimodal integration, recognition (implemented 2026-08-27) | **COVERED** |
| 5.3 Agency (`:166`) | Goals/curiosity/learning, initiative, autonomous speech (plan 20) | **COVERED** |
| 5.4 Memory and Learning (`:186`) | Taxonomy, lifecycle, skill/competence verification (`11_SKILL_AND_COMPETENCE_VERIFICATION.md` canonical) | **COVERED** for memory; **skill representation is MISSING** (see §4.6) |
| 5.5 Reasoning and Planning (`:207`) | Reasoning engine, decision/planning, canonical `Plan`/`ActionProposal` contracts | **COVERED**; **plan→skill decomposition MISSING** |
| 5.6 **Embodied Action** (`:228`) | Spatial/proprioceptive fusion spec (`17_SPATIAL_AND_PROPRIOCEPTIVE_FUSION.md` is P0-canonical); action-execution loop | **PARTIAL** — the physical bottom of the chain is the gap (§4.2–4.7) |
| 5.7 Social and Personal Continuity (`:262`) | Soul specs, behavioral scenarios, identity continuity | **COVERED** |
| §12 Physical body (`:545`) | Hardware requirements + selection *framework* only; **no selected parts, no mechanical/electrical design** | **PARTIAL** |
| §14 V0–V4 (`:610-646`) | Implemented and documented | **COVERED** |
| §14 V5 Simulated Embodiment (`:647`) | B1 simulated-execution boundary (mock body) documented; real simulator workstream **PLANNED** | **PARTIAL** |
| §14 V6 Learned Skills (`:654`) | Neural-strategy + NVIDIA research coverage only; no skill-acquisition/policy-promotion design | **MISSING** |
| §14 V7/V8 Physical Novi (`:661-680`) | Only plan stubs | **MISSING** |
| §16 First physical milestone (`:695`) | The milestone itself is the target; **no document specifies how it is met or verified** | **MISSING** |
| §19 Success criteria — Embodied/Safety (`:785-802`) | Metric *frameworks* and Mac-body gates (B1–B5, M0–M9); **no numeric physical thresholds** | **PARTIAL** |
| §23 Safety permanent boundary (`:942`) | Logical safety/authorization P0-normative (`20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md`); **physical safety case MISSING** | **PARTIAL** |

---

## 4. Domain-by-domain gap analysis

### 4.1 Hardware — `docs/05-hardware/` (26 advertised, 5 present)

**Inventory:** the folder holds exactly five files — `README.md`, `00_HIGH_LEVEL_HARDWARE_ARCHITECTURE.md`, `24_GNSS_GPS_AND_GLOBAL_POSITIONING.md`, `25_HARDWARE_VALIDATION_AND_TESTING.md`, `26_HARDWARE_SELECTION_AND_BOM_BASELINE.md`. The README's planned table (`README.md:24-49`) lists `01_COMPUTE...23_HARDWARE_VALIDATION`; a repo-wide grep matches only the README itself.

**The BOM is a template, not a selection.** `26_...md:3-7` ("components not yet frozen"); the status table `:844-869` reads: Compute **Not frozen**; Camera/Depth/LiDAR/IMU/Audio/Thermal/Motor controller/Battery-BMS **Missing**; Displays/Lighting **Conceptual only**; Power/Safety controller **Missing detailed design**; Mechanical CAD, Sensor synchronization, Hardware BOM, Validation plan **Missing**. §27 defines the BOM structure (`:753-792`) with **zero rows populated**. The freeze gate defers BOM until workload, geometry, FOV, power/thermal, safety, sync, drivers, and validation all exist (`:873-889`).

**Entirely absent as documents** (only "future work must define…" mentions): mechanical/electrical architecture and chassis/CoG/drive-geometry sizing (`00_...md:445-476`, `26_...md:615-638`); PCB/MCU design (`00_...md:465-466`); battery pack/BMS and power rails/fusing (`26_...md:448-511,861-862`); cooling/thermal design (`00_...md:464`); EMI/EMC (`README.md:133`); serviceability (`26_...md:633-634`); the physical safety case (no risk-assessment doc exists; `15_HARDWARE_SAFETY_SYSTEM.md` is advertised but never authored).

**Per-subsystem verdicts vs. tracker §5.7 exit criteria** (`tracker:383-404`; every subsystem needs a selected baseline + alternative + interfaces + power/thermal + safety + calibration + validation): **1 of 18 subsystems passes** — Validation plan (`25_...md`, the full program). All 17 others are PARTIAL (requirements/candidate families only, nothing selected) or MISSING (mechanical/electrical architecture, BOM/sourcing, serviceability, physical safety case).

### 4.2 Robotics middleware, control, and robot description — MISSING at decision level

- **No ROS 2 ADR.** ROS 2 Jazzy is a *candidate* only; readiness-audit GAP-005 makes the ROS 2 decision P0 (`NOVI_PRE_IMPLEMENTATION_READINESS_AUDIT.md`), but no ADR records a decision. Isaac ROS/Isaac Sim/Isaac Lab are referenced as "adopt where they provide measurable value" (`NOVI_NORTH_STAR.md:599`) — no decision record.
- **No `ros2_control` design.** The control boundary is drawn (Policy/Safety owns final authorization — `02-autonomy/16_AUTONOMY_ARCHITECTURE_BOUNDARY_AUDIT.md:111-119`), but controller/actuator interfaces, hardware interface layers, and the middleware→controller→actuator chain have no authoritative interface/behavior design.
- **No navigation/localization/mapping decision record.** Nav2 is referenced inside specs (`02-novi-brain/17_...md`, `06_ACTION_EXECUTION_AND_FEEDBACK.md`) but no ADR selects a stack; the three workstreams (`plans/03_LOCALIZATION`, `04_MAPPING`, `05_NAVIGATION`) are PLANNED stubs.
- **No robot-description contract.** Nothing defines a URDF/xacro (or USD for Isaac Sim) describing the body, joints, sensors, and transmission that the brain's `EmbodiedState` (`17_...md:47-76`) is supposed to consume. The brain spec's joint/wheel/contact/sensor-pose fields have no upstream source document.
- **No sensor drivers / message-standard contract.** No document defines how camera/LiDAR/IMU/encoder/audio data cross into the perception stack on the real body (the Mac `real_io` path is a prototype, not a robot data path).
- **No skill → ROS 2 mapping.** Plans name capabilities ("request navigation route") but nothing maps an approved skill to a set of middleware actions, preconditions, and recovery.

### 4.3 Simulation — PLANNED workstream, no authoritative doc

- No consolidated Simulation domain document; the only artifacts are `specs/testing/07_SIMULATION.md` (simulator as a *candidate*: "Isaac Sim or another simulator can become a higher-fidelity validation environment", `:22-24`) and the 18-line `plans/10_SIMULATION/00_..._INDEX.md`.
- **Missing:** simulator selection ADR; URDF/USD pipeline; physics-engine choice and fidelity guarantees; scenario schema; domain-randomization / seed policy; SIL spec (what is mocked, what runs, pass criteria — SIL is *named* in ladders, `05-hardware/25_...md:198-222`, but has no executable spec); sim-to-real drift-analysis method; promotion thresholds.
- The sim-to-real *ladder* is documented (`25_...md:198-222`, `47_ARCH_CLOSE_008:223-244`) including the "no benchmark laundering" rule (`10_...md:216-225`); the *plan* is not.

### 4.4 Validation — no consolidated VALIDATION DOMAIN doc (§5.10 "P0 unification required")

- The 9-level hierarchy is *listed* (`tracker:471-489`) but content is scattered across ≥20 files; §5.10 status is **"IN PROGRESS — P0 unification required"** (`tracker:506`).
- **REAL-WORLD validation level: MISSING.** Only a level name (`tracker:488`); no document defines field/operational validation (environment, scenarios, instrumentation, acceptance criteria, duration, data collection).
- **No test ownership matrix** anywhere in the validation corpus.
- **No North Star → requirements → tests traceability.** Architecture-invariant traceability is CLOSED (T-001…T-030, `50_ARCH_CLOSE_009...md`), but the North Star's properties and §19 success criteria are never linked to requirements and tests.
- **No quantitative cognitive/behavioral benchmark suite.** Frameworks exist (`06-soul/08_...md:632-650` — 11 named indicators, no numeric targets); numeric thresholds explicitly deferred ("Exact numeric thresholds will be set after the robot sensor/control requirements are documented" — `02-novi-brain/40_...md:183-194`). The only numeric budgets are latency/resource (`31_ARCH_CLOSE_007...md:28-47`).
- **No executable SIL/HIL test plans**, no controlled-physical test protocols, no consolidated longitudinal plan, no regression policy, no canonical labeled ground-truth dataset, no numeric safety/recovery targets (e-stop response time, watchdog timing, thermal-shutdown thresholds).
- The only executable robot-gate content is the Mac-virtual-body set: Brain Exit Contract B1/B5 **OPEN**, B2–B4 **CLOSED** (`plans/01_BRAIN/14_BRAIN_EXIT_CONTRACT.md:152-158`); Mac testing acceptance gate **OPEN** (`specs/testing/14_MAC_TEST_ACCEPTANCE_GATE.md:19-24`).

### 4.5 Security & physical safety — the logical layer is strong, the physical layer is absent

**Strong (do not rewrite):** the logical safety/authorization architecture is P0-normative and comprehensive — `01-system-architecture/20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md` (§2 safety hierarchy; §5 action classes S0–S4; §6–§8 ALLOW/DENY/DEFER/EMERGENCY_STOP; §10 software E-stop; §11 watchdogs; §15 human presence; §17 policy hierarchy; §19 degraded operation; §28 testing). Supporting: `02-autonomy/09_AUTONOMY_SAFETY_BOUNDARIES.md` (immutable boundary, risk classes R0–R5), `07_AUTONOMY_STATE_MACHINE.md` (EMERGENCY_STOP state), `02-novi-brain/29_BRAIN_B0_6_SAFETY_AND_MOCK_BODY_WORKFLOW.md` (protected actions always denied), and the safety-integration evidence `43_ARCH_CLOSE_005...md` (software gate passed; **physical electrical E-stop, watchdog timing, controller/sim validation explicitly deferred until hardware exists**).

**Missing / not started:**
1. **Consolidated physical-AI threat model** — §5.11 (`tracker:510-530`) and GAP-019 (`readiness-audit:409-416`) both require it at P0; status **"IN PROGRESS — P0"**. The only documents titled "threat model" are **archived/NON-NORMATIVE** (`04-memory-and-knowledge/archive/94_...`, `archive/README.md:4-8`) and memory-scoped. No unified model covers physical access, firmware compromise, sensor spoofing of camera/LiDAR/IMU/encoder (GNSS spoofing is acknowledged once: `05-hardware/24_...md:169-175`), update/rollback, or adversarial perception.
2. **Physical safety case** — GAP-014 (`readiness-audit:312-331`, "P0 before physical actuation"): hazard analysis **MISSING** (no doc performs hazard identification); E-stop *electrical* design missing (`20_SAFETY:245` defers to a `15_HARDWARE_SAFETY_SYSTEM.md` that does not exist); motor-power isolation, watchdog *architecture* (MCU/timing/independent path), per-actuator safe-states, BMS design, over-current/over-temperature thresholds, numeric speed/force limits, human-proximity behavior spec, fault-injection *results* (the matrix exists in `25_...md:226-247`; the evidence does not) — all requirement-lists only.
3. **Security incident response & recovery** — no active document (only privacy-scoped IR in `09_111_PRIVACY...md` §62 and archived docs).
4. **Sensor-spoofing / adversarial-perception defense design** — acknowledged as threats, no mitigation design.
5. **No consolidated SECURITY domain authority** — content scattered across ≥13 active files (the tracker's own §5.11 is the only "domain" artifact and it is a to-do list).
6. **Update/rollback attack surface for the robot** — model/runtime integrity is defined (`09_MODEL_LIFECYCLE.md` §23, `22_RUNTIME_VERSION...md` §18); firmware/boot integrity and signed-update trust roots on the robot are not.

### 4.6 Action / skill / embodiment — the cognitive half is canonical, the skill half is the single biggest gap

**Covered (spec-level, strong):**
- Goal→plan→proposal chain: `02-autonomy/05_DECISION_AND_PLANNING.md:11-31,93-120,156-183`; canonical `Plan`/`ActionProposal` contracts (`01-system-architecture/16_CANONICAL_SYSTEM_CONTRACTS.md:243-266`); planning/action separation of duties (`16_AUTONOMY_ARCHITECTURE_BOUNDARY_AUDIT.md:315-358`).
- Competence ≠ authorization rule, canonical and strong: `04-memory-and-knowledge/11_SKILL_AND_COMPETENCE_VERIFICATION.md:9-14,108-116`; capability-state ladder (`20_SAFETY_...md:296-306`); "no thought/prediction/memory/LLM output/learned policy/goal/plan/user request is itself permission to move the robot" (`:737-739`).
- Spatial self-model / proprioception: **the strongest area** — `02-novi-brain/17_SPATIAL_AND_PROPRIOCEPTIVE_FUSION.md:47-76` (`EmbodiedState`: pose, velocities, gravity, joints, wheels, contacts, sensor poses, localization_status, covariance), localization state machine `:254-280`, commanded-vs-observed attribution `:329-349`. (Implementation deferred; contracts "to be finalized by ADRs", `:582-596`.)
- Embodied feedback loop: `06_ACTION_EXECUTION_AND_FEEDBACK.md:13-23,64-97`; commanded/controller-accepted/physically-executed/world-observed grounding (`02_WORLD_MODEL.md:273-291`); simulated loop implemented (`37_BRAIN_B1_8_...md:11-25`, `36_BRAIN_B1_6_...md:11-25`).

**Missing:**
1. **No canonical `Skill` contract, no skill representation, no skill library.** `16_CANONICAL_SYSTEM_CONTRACTS.md` has Plan, ActionProposal, AuthorizationDecision, SafetyDecision, ActionExecution, ActionOutcome — **no Skill**. The detailed skill spec (primitives NAVIGATE/ALIGN/GRASP/MOVE/RELEASE/PRESS, pre/postconditions, composite skills, manipulation) exists **only** in archived NON-NORMATIVE `archive/84_MEMORY_KNOWLEDGE_PROCEDURAL_MEMORY_AND_SKILL_MEMORY.md:52-88,324-346,485-495`. "Skill library" appears only as a V6 aspiration (`NOVI_NORTH_STAR.md:659`, strategy `:784`). The *implemented* skill system is the cognitive/tool catalog (`plans/01_BRAIN/18_SKILL_SYSTEM_DESIGN.md`) — no motor/actuator semantics.
2. **No plan→skill decomposition.** Plans stop at typed capability references; multi-step planning is an explicit B1 non-goal (`02-novi-brain/35_...md:90-103`); nothing turns "request navigation route" into an executable skill.
3. **No manipulation/interaction path.** The action gateway lists navigation, speech, display, head movement, lighting, smart-home, media, diagnostics, memory, file ops — **no manipulation** (`06_ACTION_EXECUTION_AND_FEEDBACK.md:27-38`). No arm/gripper/end-effector anywhere in the hardware or BOM. The §16 milestone's "navigate **and interact** through approved skills" is only half-addressable.
4. **No robotics middleware → controller → actuator design** (see §4.2).
5. **No V6 learned-skills design** (imitation, policy training/evaluation/promotion gates, authorization of learned policies behind the safety boundary).
6. **No skill-approval-for-physical-execution mechanism** — the competence≠authorization rule is canonical; the mechanism that turns a skill into an authorized physical action is undefined (doc `11` defers to `15`/`16`; the safety doc authorizes *action proposals*, not *skills*).
7. **No physical-outcome-driven skill learning** — outcome verification is covered; converting physical outcomes into skill confidence/status/adaptation is generic "learning candidate" language plus archived material.

### 4.7 Plan workstreams & the docs authority map

- **13 robot workstream indexes are one-page PLANNED stubs** (`plans/03_LOCALIZATION`…`14_DEPLOYMENT`, 17–25 lines each, "Status: PLANNED"). `02_PERCEPTION` is the only workstream with real implementation plans.
- **Four completion-gate domains have no authoritative document:** Simulation, Validation, Security, Deployment. `NOVI_DOCUMENTATION_MASTER_INDEX.md`'s authority map ends at Hardware + Soul and has no section for any of the four.
- **`05-hardware/README.md` advertises 23 documents that don't exist** and its own numbering note is stale (`README.md:59-65` declares 24/25/26 canonical; the table at `:24-49` still lists 23).

---

## 5. Ranked list of MISSING documentation (for a fully autonomous robot)

### P0 — required before the first physical milestone is credible
1. **Physical Safety Case** (GAP-014): hazard analysis, robot-specific risk classification, E-stop *electrical* design, motor-power isolation, watchdog architecture (independent path/timing), per-actuator safe-states, BMS/power protection thresholds, numeric speed/force limits, human-proximity behavior, communication-loss recovery, fault-injection results, test evidence. Also author the advertised `05-hardware/15_HARDWARE_SAFETY_SYSTEM.md`.
2. **Consolidated Physical-AI Threat Model** (§5.11 / GAP-019): actors, assets, trust boundaries (incl. electrical/CAN), attack paths, controls, monitoring, incident response/recovery, residual risk — spanning software, models, data, hardware, network, and physical access; sensor spoofing for all sensor classes; firmware/update/rollback.
3. **Canonical Skill representation + `Skill` contract + skill library**: promote `archive/84` to canonical status, add the missing contract to `16_CANONICAL_SYSTEM_CONTRACTS.md`, define skill lifecycle and the propose→validate→authorize→promote physical-execution gate (closes §4.6 gaps 1, 6).
4. **Robot-description contract** (URDF/xacro/USD) and the **robotics-middleware ADR** (ROS 2/Isaac ROS selection per GAP-005) plus **ros2_control / controller→actuator interface design** — the authoritative layer under `17_SPATIAL...` and `06_ACTION_EXECUTION...`.

### P1 — needed to *execute* the milestone (build + verify path)
5. **Consolidated VALIDATION DOMAIN document** (satisfies §5.10 "P0 unification required"): reconcile the two evidence-class vocabularies (E0–E5 vs D/U/I/S/H/P/L/B/R), the validation-status vocabulary (`10_...md:268-279`), the gate sets (H0–H5 / B1–B5 / M0–M9 / G0–G6 / P0–P3) into one release chain with the required evidence class per gate; add test ownership matrix, regression policy, canonical labeled ground-truth dataset, and the REAL-WORLD level spec.
6. **Simulator selection ADR + SIL spec**: simulator choice, physics fidelity, URDF/USD pipeline, scenario schema, domain randomization/seeds, SIL pass criteria, sim-to-real drift analysis and promotion thresholds.
7. **Mechanical / electrical architecture + populated BOM**: chassis, mass/CoG budget, drive geometry/wheel sizing, actuator & motor-controller sizing (torque/speed/current), battery pack/BMS design, power rails/fusing, thermal design, connectors/harness, calibration & time-sync procedures, serviceability, per-part sourcing/replacement.
8. **North Star → requirements → tests traceability matrix** linking the seven properties and §19 success criteria to the T-001…T-030 invariants and the B/M gates.
9. **Quantitative cognitive/behavioral benchmark suite** with numeric thresholds (reasoning accuracy, prediction calibration, retrieval precision/recall, planning success, personality-stability bounds, safety-response latencies).

### P2 — makes the milestone *convincing* and the path repeatable
10. **V6 learned-skills design** (imitation, policy training/evaluation/promotion gates, authorization of learned policies).
11. **Manipulation path** (capability, hardware, controller, skill primitives) — required for the §16 "interact" clause.
12. **Security incident-response & recovery plan** and **sensor-spoofing / adversarial-perception defense design**.
13. **Update/rollback attack surface for the robot** (firmware/boot integrity, signed-update trust roots, OTA).
14. **Consolidated SECURITY domain authority** reconciling the ≥13 scattered sources.
15. **Longitudinal evaluation plan** for the full physical system; **numeric safety/recovery metrics**; **plan workstream docs for 03–14** promoted from PLANNED stubs to real implementation plans.

---

## 6. What is genuinely covered — do not rewrite

- **Cognitive brain, memory, cognition, autonomy, soul:** canonical P0 specs, implemented, evidence-closed (Brain Exit B2–B4 CLOSED).
- **Logical safety/authorization architecture** (`20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md` + `09_AUTONOMY_SAFETY_BOUNDARIES.md` + B0.6): P0-normative, genuinely strong.
- **Spatial self-model / proprioception / localization-state spec** (`02-novi-brain/17_...md`): the single best-prepared physical-path spec; it is the natural anchor for the missing robot-description contract.
- **Embodied feedback loop** (outcome → world-model → memory), including commanded-vs-observed discrepancy handling.
- **The sim-to-real ladder, promotion gate, and evidence-class disciplines** (`25_...md:198-222`, `19_...md:238-258`, `47_ARCH_CLOSE_008:223-244`, `10_...md:216-225`) — the *framework* for validation, which the missing plans must populate, not replace.
- **The §16 milestone's cognitive half** (perceive, world model, goals, plan, governance, observe, learn) — implemented in the B1 simulated loop.

---

## 7. Recommended next steps (documentation only)

1. **Author the two P0 safety/security docs first** — Physical Safety Case (GAP-014) and Physical-AI Threat Model (§5.11/GAP-019) — because every hardware, validation, and skill document must reference them. Both have named owners (the tracker/readiness audit) and explicit P0 status.
2. **Promote the skill spec** (`archive/84`) to a canonical `SKILLS_AND_PROCEDURAL_MEMORY` document, add the `Skill` contract to `16_CANONICAL_SYSTEM_CONTRACTS.md`, and define the skill→authorization→execution gate.
3. **Write the robot-description contract + ROS 2/Isaac ROS ADR + ros2_control interface design** as the authoritative bottom of the embodied-action chain (anchor: `17_SPATIAL_AND_PROPRIOCEPTIVE_FUSION.md`).
4. **Consolidate the VALIDATION DOMAIN document** (§5.10) and the **Simulation domain** (simulator ADR + SIL spec) — they share the sim-to-real ladder and should be written together.
5. **Populate the hardware BOM and mechanical/electrical architecture** once the safety case and robot-description contract exist (the BOM's own freeze gate demands exactly that order, `26_...md:873-889`).
6. Then, and only then, promote the 13 `PLANNED` workstream stubs into real implementation plans.

No implementation changes were made; this is analysis only.
