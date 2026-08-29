# ADR-LA-01 — LocateAnything as a secondary spatial-grounding backend

**Status:** ACCEPTED (2026-08-29) — implementation in progress per
`docs/plans/LOCATE_ANYTHING_IMPLEMENTATION_PLAN_2026-08-28.md`.
**Scope:** perception integration only. This record does not grant
LocateAnything any role in cognition, planning, governance, or action.

---

## 0. Freeze record — external model version (plan Phase 0, Step 0.2)

The same revision must be reproducible later. **No floating `main` reference.**

| Item | Value |
|---|---|
| Hugging Face model ID | `nvidia/LocateAnything-3B` |
| Exact revision (commit) | `c32291ca5e996f5a7a485845b4f57a233936bba0` |
| Revision date | 2026-06-12 |
| Model config hash (sha256) | `59e6b5104f9d948db6a38f778e29f86d5c01e373f46d02008fc3070377917007` |
| Weights | `model-00001-of-00002.safetensors` (4 959.6 MB) + `model-00002-of-00002.safetensors` (2 701.8 MB), BF16 |
| Published repo footprint | ~7.80 GB (7.66 GB weights + assets/config/vocab) |
| Tokenizer/processor revision | same pinned revision (`c32291ca…`; `merges.txt`, `vocab.json`, `tokenizer_config.json` in snapshot) |
| Upstream code commit | `NVlabs/Eagle` `783f656d127ee498137b5ff52603ce36c292d317` (2026-06-24) |
| Model license file | `Embodied/LICENSE_MODEL`, sha256 `fe39c45188adbde02599ed88f7e018a242a3e786ca1add8b35d264e89524bada` |
| Model license terms | **Non-commercial research/evaluation only** (NVIDIA License). Tracked independently from Novi's MIT code license; commercial deployment blocked until Phase 13 (license gate) passes. |
| Runtime contract | `AutoTokenizer/AutoProcessor/AutoModel` with `trust_remote_code=True` — explicit supply-chain boundary; remote code must be reviewed before any production use. |

Reproduction commands:

```bash
# isolated env:  scripts/mac-locateanything-env.sh  (pins the revision above)
# verify pin:    ls ~/.cache/novi/models/locateanything-hf/.../snapshots/c32291ca5e996f5a7a485845b4f57a233936bba0/
```

---

## 1. Decision

Implement NVIDIA LocateAnything as a **secondary, optional, language-conditioned
spatial-grounding backend** behind a Novi-owned interface
(`SpatialPerceptionBackend`). It is a perception capability — never a world
model, memory, planner, identity system, or governance layer.

## 2. Ownership boundaries (Step 0.1 acceptance)

Reviewers must be able to identify exactly which layer owns each responsibility:

| Responsibility | Owner | Notes |
|---|---|---|
| Fast category detection | **Perception — SSDLite** (unchanged baseline) | `ObjectDetector` contract stays stable; LocateAnything does not replace it |
| Semantic query generation | **Cognition** | "find my keys" → visual query; perception never invents goals |
| Geometric localization | **Perception** (LocateAnything adapter) | boxes/points in the image; strictly observational |
| Persistent interpretation | **World state** | only validated observations enter the world model |
| Action permission | **Governance/safety** | grounding output is evidence, never authorization |
| Model licensing | **Tracked independently** of code licensing | freeze record §0; release gate Phase 13 |
| 3D reasoning | **Deferred** | a 2D box is not a 3D position; depth+intrinsics+extrinsics+pose required before any `(x,y,z)` claim |

## 3. Contract boundaries

- **`SpatialPerceptionBackend`**: `ground(image, query, policy) -> GroundingResult`,
  `point(...) -> PointingResult`, `detect(...) -> GroundingResult`,
  `capabilities() -> CapabilityReport`. Implemented in `novi/perception/grounding.py`.
- Raw NVIDIA special tokens (`<ref>…</ref><box>…</box>`) are parsed by a strict
  parser in `novi/perception/locate_anything_parse.py`; **no other Novi component
  ever sees them**.
- The backend must report one of: `available | loading | unavailable |
  unsupported | dependency_missing | model_missing | failed`.
  Missing LocateAnything must never crash normal Novi startup.
- Coordinates: LocateAnything emits integer-normalized `[0,1000]` corners; the
  adapter retains the source representation **and** converts to Novi's canonical
  integer pixel box `(x, y, w, h)`, clamping bounds and rejecting
  inverted/zero-area boxes (spec `02_MODEL_AND_RUNTIME_SPEC.md` §4).
- Inference modes `fast | slow | hybrid`, **default `hybrid`**; generation
  defaults owned by the backend (`generation_mode="hybrid"`,
  `max_new_tokens=8192`), not exposed wholesale to cognition.

## 4. Explicit non-goals (do not do)

- Do not replace SSDLite; do not make Transformers/DeepSpeed/CUDA mandatory Novi deps.
- Do not let raw model output or model-chosen behavior enter the world model or action path.
- Do not assume Apple MPS support (NVIDIA documents H100/A100). Mac path is an
  **experiment with an explicit decision gate** (Phase 4).
- Do not assume commercial licensing; do not ship visual-prompt capability
  (released 3B weights do not support it).
- Do not couple Novi's architecture to NVIDIA's worker class (`LocateAnythingWorker`
  is reference code, not Novi code — a narrow adapter is used instead).

## 5. Safety posture

- Grounding output is **observational only**; confidence is never permission.
- High-risk actions require re-observation + verification (plan Phase 9).
- Failure is **fail-closed**: no localization ⇒ report unknown/uncertain, never
  infer absence.

## 6. Decision context / alternatives

- **Reject:** replace SSDLite entirely with LocateAnything — loses the cheap
  continuous baseline; makes a 7.8 GB model mandatory on every frame.
- **Reject:** expose NVIDIA worker/raw generation to the brain — couples Novi to
  NVIDIA internals and special tokens.
- **Reject:** assume a remote/cloud runtime — violates the resource-parity rule
  (no cloud in the cognitive path).
- **Accepted:** local optional backend; NVIDIA workstation/server path is the
  documented fallback if MPS proves unusable (Phase 4 decision gate outcome B).

## 7. Evidence and status

Implementation status per plan §19 sequence: `docs/07-locate-anything/08_IMPLEMENTATION_STATUS.md`.
Mac feasibility evidence: `docs/07-locate-anything/07_MAC_FEASIBILITY.md` (after Phase 4 runs).
