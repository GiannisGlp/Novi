# 43 — ARCH-CLOSE-005 Safety Integration Evidence

**Status:** PARTIALLY EVIDENCED — software integration gate passed; physical safety validation deferred
**Authority:** System Architecture / Safety boundary
**Closure item:** ARCH-CLOSE-005 — Safety integration

## 1. Evidence basis

The normative safety architecture defines an independent boundary between cognitive/autonomy proposals and physical execution. Model output is untrusted input; authorization and safety decisions are explicit; hardware health and emergency-stop state constrain execution. `20_SAFETY_AND_AUTHORIZATION_ARCHITECTURE.md` remains authoritative for these invariants.

The executable integration gate is:

`contracts/tests/integration/test_safety_authorization_integration.py`

The gate is included in `.github/workflows/recovered-architecture-gates.yml` alongside the recovered time and resource validation gates.

## 2. Software scenarios covered

The integration test verifies:

- required safety/control contracts are present in the registry and schema tree;
- a valid proposal + authorization + safety decision + healthy hardware state can pass;
- capability mismatch is rejected;
- authorization denial is rejected;
- expired authorization is rejected;
- denied safety decisions are rejected;
- unhealthy hardware is rejected;
- disconnected hardware is rejected;
- invalid calibration is rejected;
- emergency-stop fault state is rejected.

## 3. Architectural traceability

```text
ActionProposal
      ↓
AuthorizationDecision
      ↓
SafetyDecision
      ↓
HardwareHealth
      ↓
permitted execution boundary
```

The implementation test enforces the core invariant that a proposal is not sufficient for execution: capability, authorization validity, safety decision, hardware health, communication, calibration and emergency-stop state all participate in the decision.

## 4. What this evidence proves

The repository has an executable software-level safety authorization boundary and regression gate.

It does **not** prove:

- physical emergency-stop electrical behavior;
- actuator hard-limit enforcement;
- real sensor-failure behavior;
- watchdog timing on robot hardware;
- controller failure behavior;
- obstacle/collision safety;
- localization-loss behavior on the physical robot;
- SIL/HIL/physical acceptance scenarios.

Those require implementation and hardware evidence and remain deferred until the corresponding runtime and prototype exist.

## 5. Closure decision

ARCH-CLOSE-005 is **not fully closed**. The software integration portion is evidenced; the remaining physical/controller/simulation validation is explicitly tracked as implementation-dependent rather than being claimed prematurely.

The next evidence required is progressive validation through simulation, then HIL where justified, then controlled physical tests after the safety controller and robot hardware exist.
