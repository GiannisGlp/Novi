# 04 — Gap Analysis: Autonomy

## Docs: 02-autonomy
Continuous loop; DECIDE WHETHER TO ACT / SIGNAL; attention budget; social-initiative
budget; goals; governance; the communication decision chain
Soul - Cognition - Autonomy - Brain speech runtime - Hardware.

## Exists today
- Continuous prompt-independent loop (MAC_BRAIN/runtime.step: sense to world to cognition
  to reason to act to reflect to consolidate to soul).
- Bounded goal manager + typed plan (autonomy.py, planner.py) with replanning.
- Social initiative (neglect detection, spontaneous initiation) + attention/detail in
  runtime; governance contract schemas; web surfaces initiative turns.

## Delta (what's missing)
- Full autonomy state machine beyond bounded goals: idle/active/degraded modes,
  interruption/resume, attention arbitration across goals + social + survival.
- Attention engine: ranked attention candidates (salience/novelty/urgency/social-
  invitation/relevance/uncertainty) feeding one decision point (docs: Cognition supplies
  candidates, Autonomy decides).
- Safety/authorization at the action boundary is only contract schemas, not a runtime
  guard between proposal and execution (critical invariant: models never command action).
- Deterministic-vs-model split for autonomy decisions is not fully exercised.
- Communication "when/whether/how" as a unified autonomy method on the loop (now partly
  in dialogue/social).

## Next action (roadmap Step 3)
- Model the autonomy runtime as an explicit Decide / Plan / Propose / Grant / Act /
  Verify cycle with a governance call between proposal and execution, even for
  deterministic/simulated actions. Add attention ranking and communication decisions as
  first-class inputs.

