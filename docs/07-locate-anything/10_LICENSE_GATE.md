# LocateAnything — License Gate Record (Phase 13, step 31)

**Status:** RECORDED — model is **research/evaluation only**; commercial deployment
NOT cleared. Legal review pending (needs counsel; not automatable).
**Freeze reference:** `06_ARCHITECTURE_DECISION.md` §0 — license file sha256
`fe39c45188adbde02599ed88f7e018a242a3e786ca1add8b35d264e89524bada`
(`NVlabs/Eagle@783f656d` `Embodied/LICENSE_MODEL`, 72 lines).

## 1. What the license actually says (quoted)

> **3.3 Use Limitation.** The Work and any derivative works thereof only may be
> used or intended for use non-commercially. Notwithstanding the foregoing,
> NVIDIA Corporation and its affiliates may use the Work and any derivative
> works commercially. As used herein, "non-commercially" means **for research
> or evaluation purposes only**.

## 2. Current status

| Item | Status |
|---|---|
| Model revision identified | ✅ `c32291ca5e996f5a7a485845b4f57a233936bba0` |
| Exact license retained | ✅ hashed + quoted above; full text at the pinned upstream commit |
| Research/evaluation use of released weights | ✅ permitted under 3.3 (Novi dev on Mac = research) |
| Commercial Novi product with these weights | ❌ **not cleared** — 3.3 forbids commercial use of the Work and derivative works |
| NVIDIA written permission | ❌ not obtained |
| Legal review | ❌ pending (counsel) |
| Decision recorded in release evidence | ✅ this record; referenced from `08_IMPLEMENTATION_STATUS.md` |

## 3. What clearance requires (checklist — complete before ANY commercial deployment)

1. Identify exact model revision — ✅ done (ADR §0).
2. Retain exact model license — ✅ done (this record).
3. **Obtain legal review** of 3.3's scope ("derivative works", "non-commercially").
4. **Determine whether NVIDIA commercial permission is required** — analysis in
   `05_LICENSE_SECURITY_AND_RISKS.md`; 3.3 strongly indicates yes.
5. **Obtain written permission** from NVIDIA, or
6. **Replace the model** with one whose rights permit commercial use (e.g. a
   compatible open-weight model) — the adapter architecture makes this a
   runtime swap, no Novi code changes.
7. Record the decision in Novi's release evidence — this record is the slot.

## 4. Code licensing note (tracked independently)

Novi's code remains MIT. The model license governs the *weights* only — the
adapter, parser, contracts, and benchmark code are Novi's. The separation is
deliberate (plan Phase 0 Step 0.1: "model licensing is tracked independently
from code licensing").

## 5. Operational guardrails until clearance

- The released weights are for research/evaluation only (this is also why the
  `locateanything` extra and the model download are NOT part of the default
  install).
- No Novi release may bundle or auto-download the weights for commercial use.
- The capability probe's honest `unavailable`/`model_missing` states keep
  Novi fully functional without the model.
