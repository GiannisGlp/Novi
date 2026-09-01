# Perception — Camera, Vision Self-Awareness, Grounded Dialogue, and Person-Object Memory

**Status: DONE**
**Workstream:** `docs/plans/02_PERCEPTION/`
**Sibling docs:** [`00_PERCEPTION_IMPLEMENTATION_INDEX.md`](00_PERCEPTION_IMPLEMENTATION_INDEX.md) · [`01_CAMERA_ACQUISITION.md`](01_CAMERA_ACQUISITION.md) · [`02_FACE_AND_OBJECT_RECOGNITION.md`](02_FACE_AND_OBJECT_RECOGNITION.md)
**Purpose:** improve everything around the camera — raise frame rate and cut redundant work (A), make Novi know it can see and recognize (B), ground conversations in what it currently sees and remembers seeing (C), and give it durable person↔object association memory (D). **Reuses the existing vector-saving logic** (`RecognitionStore`, `ObservationRecorder`) — no rebuild.
**Governing:** single canonical DB (`novi/data/novi.db`), resource parity, evidence gates, docs before implementation, one patch at a time, plan-25 trained adapters unchanged.

---

## Objective

The perception stack already detects (SSDLite320), tracks, embeds faces (SFace 128-d), matches object instances (ResNet18 512-d), and durably enrolls/sights people + objects. Four gaps block the goal:

| # | Gap | Evidence |
|---|-----|----------|
| A | **Performance / frame rate.** The camera loop runs every expensive stage every frame and decodes the JPEG 3–4×/frame. | `_start_camera_loop` (`novi/web/integration_api.py:232`): `_store_preview_frame` (b64 encode), `OpenCVFaceEmbedder.embed` decode (`real_backends.py:193`), `TorchvisionPerceptionDetector._decode` (`real_backends.py:80`), `TorchvisionObjectEmbedder._decode` (`real_backends.py:333`). No throttle, no timing telemetry. |
| B | **No vision self-awareness.** Novi can't honestly say what it sees (or that it can't). | `build_self_model` (`novi/brain/self_model.py:60`) reports capability health but never live camera state (camera_live, current person/objects, fps). |
| C | **Conversations not grounded in live sight.** | `_assemble_world_context` (`novi/brain/chat.py:127`) reads only the unified world model; `MultimodalRuntime` state never reaches the dialogue payload, so trained replies can't reference what Novi currently sees. |
| D | **No durable person↔object association memory.** | Only transient `person.holding` events exist (`multimodal.py:532`); no queryable "Vano was seen with the blue mug in the kitchen". |

---

## 1. Workstream A — Performance: single decode + `VisionBudget` cadence + telemetry

### 1.1 `VisionBudget` — `novi/perception/cadence.py` (new)

Pure, deterministic cost gate + timing telemetry. Injectable `clock` for tests.

```text
decide(frame_seq, scene_changed=False) -> {"detect": True, "face_embed", "object_embed", "preview"}
  - counter gate: stage runs when n % every_n == 1 (frame 1 = baseline runs all)
  - min-interval gate: stage skipped if it last ran < min_interval_s ago (fast loop can't hammer NN)
  - scene_changed forces every stage for one frame (novel content re-embedded immediately)
add_sample(stage, elapsed_ms) / mark_processed() / telemetry() -> {"processed_fps", "frames_processed",
  "stage_ms": {stage: {avg_ms, max_ms, samples}}, "runs": {stage: count}}
```

Defaults: detection every frame (`detect_every_n=1`); `face_every_n=3`, `object_every_n=4`, `preview_every_n=2`; `scene_resets=True`.

### 1.2 Single decode in the camera loop

- Decode the JPEG **once** with `cv2.imdecode` → BGR ndarray. Detector and object embedder already accept ndarrays (`_decode` accepts `np.ndarray.ndim==3`). Build a `CameraFrame(..., payload=bgr)` (width=`shape[1]`, height=`shape[0]`).
- **SFace:** add `OpenCVFaceEmbedder.embed_bgr(img)` (same pipeline over the decoded array); `embed(payload)` keeps its API and delegates. Loop calls `embed_bgr` when present, else re-encodes (deterministic fake-embedder fallback).
- **Reuse** the last face embedding on skipped face frames so in-memory identity matching keeps presence alive (the "recent proposal" guard already prevents re-enroll churn).
- **Preview:** `_store_preview_frame` stops generating a full-res JPEG+b64 every frame. Store `mm_last_frame_bgr = bgr` + preview b64; enroll endpoints encode jpeg from `mm_last_frame_bgr` on demand (rare, manual).
- **Gate** `recognize_objects` / `_note_person_holding` / preview on the decision; wrap each stage with `add_sample(stage, ms)`.

Heavy loop logic moves to `novi/web/camera_loop.py` (`build_camera_loop(server) -> callable`); `integration_api.py` (770 lines, near the 800 cap) keeps thin wrappers because tests call `_store_preview_frame` / `_note_person_holding` / `_start_camera_loop` by name.

### 1.3 Telemetry surface

- `MultimodalRuntime.__init__` gains `budget: VisionBudget | None` (lazily created); `snapshot()` gains `"cadence": budget.telemetry()`.
- Web `perception_state()` merges `camera_feed` drop rate (`dropped / (captured+dropped)`) and `last_frame_age_s()` into the vision provider + cadence.

## 2. Workstream B — Vision self-awareness (`novi/brain/vision_status.py`, new)

`build_vision_status(brain, provider)` → JSON-safe dict (it is `json.dumps`'d into the user payload):

```text
{camera_live, health, recognition_available, person, person_tier, place, objects (<=8),
 scene_labels (<=8), last_frame_age_s, processed_fps, stage_ms, drop_rate,
 can_see = camera_live AND health not in {"offline","failed"}, available}
```

- `MacBrain.set_vision_provider(provider)` / `MacBrain.vision_status()` — **default `None` keeps every existing brain test byte-identical**.
- `build_self_model` merges a `"vision"` capability (`PASS`/`WARN`/`FAIL`) from the provider's status; the existing `_dialogue_system_prompt` capabilities clause then makes a degraded camera produce the honesty line automatically ("say plainly that you can't perceive that right now").
- Web installs the provider in `novi/web/vision_provider.py` (`build_vision_provider(server) -> callable`): merges `mm_runtime.snapshot()` with `camera_feed` health/drop-rate/age and the association summary. **Deadlock rule: the provider only *reads*** runtime/feed/stores — it never calls brain methods (reply thread holds `self._lock`, camera thread holds `mm_lock`; no reverse ordering).

## 3. Workstream C — Perception → conversation bridge (`novi/brain/chat.py`)

Injection seam at the only two call sites of `_assemble_world_context` (`chat.py:1063`, `server.py:1588`):

```text
_assemble_world_context(text, person="", *, vision_provider=None)
  None  -> byte-identical to today's behavior
  set   -> merges into the returned dict:
    1. "perception" key  {camera_live, person, person_tier, place,
                           objects: [{label, kind, recognized}], associations: [...]}  (bounded)
    2. live entities prepended into visible_entities as
       {id, type: "perception.object", label, source: "camera"}  (deduped by label against
       the unified-world list) — so trained_reply's World: line carries what Novi sees
```

- `_compose_reply_impl` passes `vision_provider=self._vision_provider`.
- When no person/addressee is given but a provider is installed, default the addressee to the vision `current_person` so the trained `Person:` line references the actual seen person instead of `user (unknown)` — one line, provider-gated.

## 4. Workstream D — Person-object association memory (`novi/integration/person_object_store.py`, new)

Durable co-occurrence memory on the **same single** `novi/data/novi.db` (WAL, `CREATE TABLE IF NOT EXISTS`, same conventions as `ObservationRecorder`).

```text
person_object_associations (
  person_id, object_ref, object_label, category, place,
  seen_count, first_seen, last_seen, provenance_json,
  UNIQUE(person_id, object_ref, place),  -- coalescing upsert: count++, last_seen=now
)
```

- API: `note(...)` (coalesces; raises `PermissionError` when the privacy switch is off — caught best-effort by callers, mirroring observation privacy), `objects_with(person, limit)`, `seen_with(person, object_ref)`, `recent_summary(limit)` (for dialogue), `rename_person(old, new)` (merge rows on the naming loop).
- Recording gates (mirror `_note_person_holding`): only when `current_person` is a recognized identity — not `"someone"`, not `new-person-*`, tier ∈ {recognized, verified}. `_note_cooccurrence` called from `recognize_objects` (matched instance) and `note_person_holding` (held object).
- Wiring: `MultimodalRuntime.__init__(associations=...)`; web `/api/association` POST route (`action` in objects_with / seen_with / recent_summary); `name_person` also renames association rows.

---

## 5. Implementation order (TDD — test first, deterministic fakes)

| Step | New tests | Code lands in |
|------|-----------|---------------|
| 1. Association store (standalone) | `novi/integration/tests/test_person_object_store.py` | `person_object_store.py` |
| 2. `VisionBudget` (standalone) | `novi/perception/tests/test_cadence.py` | `cadence.py` |
| 3. Loop rewrite (single decode + gating + `embed_bgr` + preview-bgr + cadence) | extend `test_camera_loop.py`, update `test_store_preview_frame_keeps_full_res_for_enrollment` | `camera_loop.py`, `real_backends.py`, `integration_api.py`, `multimodal.py` (budget) |
| 4. Runtime association wiring | `test_observation_wiring.py`-style co-occurrence tests | `multimodal.py` + `/api/association` |
| 5. Vision self-awareness + provider | `novi/brain/tests/test_vision_status.py`, `novi/web/tests/test_vision_provider.py` | `vision_status.py`, `web/vision_provider.py`, `engine.py`, `self_model.py` |
| 6. Conversation bridge | `test_vision_status.py` end-to-end (reply payload carries perception) | `chat.py`, `server.py` |

## 6. Verification

```bash
# fast new-unit targets
.venv/bin/python -m pytest novi/perception/tests/test_cadence.py novi/integration/tests/test_person_object_store.py -q
.venv/bin/python -m pytest novi/integration/tests/test_multimodal.py novi/integration/tests/test_observation_wiring.py -q

# regression — prove no-provider default is byte-identical
.venv/bin/python -m pytest novi/brain/tests novi/web/tests -q

# full suite + lint before commit
.venv/bin/python -m pytest novi/{integration,perception,voice,brain,web,cognition,contracts}/tests -q
.venv/bin/python -m ruff check novi/brain novi/perception novi/integration novi/web
```

Manual smoke (with hardware): run the web server with the real camera and `novi-trained` reply; verify `/api/perception/state` shows `cadence.processed_fps` + per-stage `stage_ms`; ask "what do you see?" and "have you seen this mug with Vano before?" and confirm replies reference the current scene/memory; confirm the loop no longer re-encodes full-res JPEG every frame.

## 7. Risks / gotchas

1. **Camera-frame payload type change** (bytes → ndarray): `process_camera_frame`/detector already accept both via `_decode`; keep determinism fakes compatible.
2. **`mm_last_frame_bytes` consumers**: audit before changing the loop (enroll endpoints + the one preview test); update together.
3. **Reused face embedding must not re-trigger proposal enrollment** — the existing "recent proposal" gate covers it; verify with a test.
4. **Bounded `perception` key**: trained prompts are token-sensitive; cap objects (≤8) and associations (≤3).
5. **Provider-gated vision**: default brains (no provider) stay byte-identical; do not flip that default.
