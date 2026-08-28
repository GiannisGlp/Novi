# Perception — Vision, Recognition, and Spatial Memory

**Status: OPEN**
**Workstream:** `docs/plans/02_PERCEPTION/`
**Sibling docs:** [`01_CAMERA_ACQUISITION.md`](01_CAMERA_ACQUISITION.md) · [`../UNIFIED_INPUT_NORTH_STAR.md`](../UNIFIED_INPUT_NORTH_STAR.md)
**Purpose:** This is the **single combined plan** for perception recognition work — it unifies visual
recognition (object detection, face detection + identity) with durable spatial observation memory
("remember what I saw and where") into one canonical document. Recognition is largely
**implemented**; this plan documents that canon and carries the **still-open spatial-memory** workstream forward.
**Governing:** single canonical DB (`novi/data/novi.db`), resource parity, evidence gates, docs before implementation,
one patch at a time.

---

## Objective

Give Novi **real, durable visual understanding** — two halves, one story:

1. **Recognize in the moment** — identify objects (category + instance) and people (face),
   through a provider-based pipeline feeding the brain's existing identity tier system
   (`unknown → recognized → verified`), closing gap **G4** (identity providers unimplemented)
   from [`13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md`](../01_BRAIN/13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md).
2. **Remember what it saw and where** — persist each recognized *face* and *object instance*
   with a place, a frame position, a timestamp, **and its perceptual vector**, so Novi can
   answer "where did I last see my blue mug?" across restarts.

This turns transient recognition ("a mug is here now") into recallable memory ("I last saw the
blue mug on the kitchen counter at 14:32 yesterday"). Everything stays behind the brain's
capability interfaces — perception is a provider, never a brain-core change.

---

## 1. Architecture overview

```text
 camera frame
   │  (01_CAMERA_ACQUISITION)
   ▼
 PerceptionPipeline.process_frame()         novi/perception/pipeline.py
   │  detector.detect()  → Detection {label, conf, bbox, frame_id, ts}
   │  tracker.update()   → active Track (IoU + hysteresis)
   │  faces.observe_observation() → IdentityDecision (unknown/recognized/verified)
   ▼
 MultimodalRuntime.process_camera_frame()   novi/integration/multimodal.py
   │  current_place ← place descriptor match
   │  identity.recognized / identity.proposal
   │  recognize_objects(pairs) → object.recognized / object.proposal
   │  presence.entered/left · scene.changed   (salience)
   ▼
 [[ NEW ]] ObservationRecorder                            (§3 — spatial memory)
   │  persists face/object sightings → observation_records (novi.db)
   ▼
 InputBus.brain.submit("camera", kind, payload)           (north-star §4.2)
```

**Two provider boundaries (no brain-core change):**
- `ObjectDetector.detect(frame) -> list[Detection]` (canonical, exists)
- `FaceIdentifier.observe_observation(...) -> IdentityDecision` (exists)
- `ObservationRecorder.record(...)` (**new**, §3.2)

---

## 2. What already exists (recognized, verified 2026-08-28)

| Capability | Where | Status |
|---|---|---|
| Object detection — SSDLite320–MobileNetV3 (MPS), `ObjectDetector` contract | `perception/real_backends.py` `TorchvisionPerceptionDetector` | ✅ live, deterministic fallback |
| Tracking-lite (IoU + hysteresis) | `perception/tracking.py` | ✅ live |
| Face detect + SFace **128-d embedding** | `perception/real_backends.py` `OpenCVFaceEmbedder` | ✅ live |
| Face identity tiers + conversational enrollment + privacy gate + cross-modal voice escalation | `perception/faces.py` | ✅ live |
| Instance object recognition — ResNet18 **512-d crop embeddings**, `RecognitionKind.OBJECT` | `real_backends.py` `TorchvisionObjectEmbedder`; `multimodal.recognize_objects` | ✅ live (commit `5ebfb87`) |
| Durable enrollment store **saving the vectors** (`embedding_json`, cosine match, privacy-gated) | `integration/recognition_store.py` (same `novi.db`) | ✅ live |
| Real camera loop → face→∞id, object→match, presence/scene → InputBus | `web/integration_api.py` `_start_camera_loop` | ✅ live |
| Durable memory primitives — `spatial_context`/`temporal_context`, `place` filter, semantic `vectors` table | `brain/storage.py` `DurableMemoryStore`; `b1_memory.py` `MemoryRecord` | ✅ exists, **unused by perception** |

**Confirmed:** the ask "saving vectors" is already met — perceptual embeddings are persisted in
the canonical DB and matched by cosine. The open work is the **observation (spatial) memory**.

---

## 3. Gaps still open (the work)

- **GAP-S1 — No durable observation record.** The camera loop drops the resolved instance name,
  the person, the bbox position, and the place before submitting to the brain; `object.recognized`
  and `identity.recognized` events aren't forwarded at all. Nothing binds {object/person, place,
  position, time, vector} durably ⇒ can't answer "where is X.".
- **GAP-S2 — Place binding isn't automatic.** `current_place` only tags a frame when a
  manual-enrolled PLACE descriptor's landmarks match; recognition never enrolls/binds places.
- **GAP-S3 — Novel-object & novel-person naming loops unclosed** (doc02 §1.5 tail). `object.proposal`
  and `identity.proposal` fire but no conversational "what is this?" / "what's your name?" loop.
- **GAP-S4 — Evidence gates not formally run on-Mac** (doc02 gates + a spatial-recall gate §5).
- **GAP-S5 — Index/search scale.** Linear brute-force cosine over per-row JSON. Fine now (~dozens
  of enrollments); revisit (in-Python limit, encoder) only above ~few-thousand enrollments. No cloud, no heavy ANN yet.

---

## 3B. Recognition design (reference — canonical + candidate models)

### Object detection candidates
| Candidate | Role | Parity |
|---|---|---|
| Torchvision SSDLite320-MobileNetV3 (shipped) | primary | TensorRT-exportable, Jetson-class |
| RT-DETR | accuracy alternative | benchmark-gated, not evaluated |
| YOLO-nano class | latency alternative | benchmark-gated, not evaluated |

Selection rule: a candidate becomes an official provider only after real on-Mac execution with
representative inputs + evidence. Detection rate decoupled from cognitive rate (world state updates
at cognitive sampling). Confidence floor + hysteresis prevent flicker. Novel labels → generic
"unknown object" entities until named by dialogue.

### Face pipeline (shipped)
```text
frame → face detect (YuNet) → align (SFace) → embedding (SFace 128-d) → match vs enrolled
        match ≥ τ → tier assignment; match ≥ τ_ambig & < τ → ambiguous (stays unknown, no guess)
```
Identity tiers existing: `unknown` (propose by dialogue) / `recognized` (match) / `verified`
(cross-modal face+voice agreement). Biometrics are **local-only**, privacy-gated (camera off ⇒ no
face processing, audited), provenance-chained, deletable per person. Ambigual matches stay ambiguous.

### Cross-modal fusion payoff (doc02 §3)
Face+voice co-presence escalates to `verified`, making addressee resolution (G2) trustworthy:
```
person walks in ─► face→recognized "Anna"
Anna speaks ─────► diarization+voiceprint evidence → same person → verified
Novi greets Anna by name while continuing navigation; chat mid-exchange → turn_taking arbitrates.
```

---

## 4. Spatial Observation Memory (the new design)

### 4.1 One more table in the canonical DB (never a second DB)
New `observation_records` in `novi/data/novi.db` (WAL), additive to `schema_version` migrations:

```text
observation_records(
  id          INTEGER PRIMARY KEY,
  obs_kind    TEXT NOT NULL,          -- 'face' | 'object'
  entity_ref  TEXT NOT NULL,          -- recognition person_id / object_id (="object-my-blue-mug")
  category    TEXT,                   -- detector label, e.g. 'cup' (empty when instance-only)
  label_name  TEXT NOT NULL,          -- resolved human name ('Vano', 'my blue mug')
  place       TEXT,                   -- spatial anchor (may be NULL → 'unspecified')
  bbox_json   TEXT NOT NULL DEFAULT '[]',   -- (x,y,w,h) in frame px
  temporal_at TEXT NOT NULL,               -- ISO8601 UTC
  frame_ref   TEXT NOT NULL DEFAULT '',
  vector_json TEXT NOT NULL DEFAULT '[]',  -- perceptual embedding saved at sight (128-d/512-d)
  provenance  TEXT NOT NULL DEFAULT '{}',  -- source, camera, privacy state
)
CREATE INDEX idx_obs_entity ON observation_records(entity_ref, temporal_at);
CREATE INDEX idx_obs_place  ON observation_records(place, temporal_at);
```
Same SQLite WAL file, `RLock`-guarded like `RecognitionStore`/`DurableMemoryStore`. **Vectors
saved on every observation** (the ask) — bounded write, independent of later enrollment updates;
storage is small and retention-bounded.

### 4.2 ObservationRecorder (adapter, no brain-core change)
A small recorder called from the **camera loop adapter** (`integration_api._start_camera_loop`)
and `MultimodalRuntime` at events/decision points:
- resolved `identity.{recognized,verified}` → insert `obs_kind='face'`, `entity_ref=person_id`,
  place from current_place, bbox from the face stage;
- `object.{recognized,proposal}` → insert `obs_kind='object'`, `entity_ref=object_id` (or a
  device-observed-instance if unresolved), bbox from the Detection.
- Coalesce per observation window / per presence departure (e.g. one record per
  `(entity_ref, place)` with a last-seen timestamp), honoring the repo's "detection rate decoupled
  from cognitive rate" rule so disk growth stays bounded.

### 4.3 Retrieval / "where" surface
Thin query methods used by the brain + web API:
- `last_sighting(entity_ref) -> {place, bbox, temporal_at, vector}`
- `objects_in(place) -> [label_name, temporal_at]`
- `recall(query_embedding, place?, since?) -> top-k episodes` (cosine over `vector_json`) —
  the instance-search path to add a `.search()` on the store.

### 4.4 Naming-loop wiring (closes GAP-S3 / doc02 §1.5)
Route `object.proposal`/`identity.proposal` into a conversational-capability surface (web
thin-client / dialogue hook) that asks the human for a name and calls the existing
`recognize_object` / `recognize_person` enrollment APIs; the resulting `entity_ref` binds to the
already-recorded (abstract) `observation_records`.

### 4.5 Privacy & resource parity
- Face observations gated by `privacy_enabled` (biometric) mirroring `RecognitionStore`; object
  observations are non-biometric (always allowed). Privacy transitions audit-recorded.
- Local-only; no cloud. Vectors are tiny (128/512−d) ⇒ Jetson-Orin/Thor-plausible.

---

## 5. Deterministic testing (CI, no models/hardware)
Scripted fixtures (synthetic frames, planted faces/objects, scripted embedders) cover:
- detection→world-state updates with tracking continuity (IoU association), correct last_seen decay;
- tier transitions incl. ambiguous-match refusal; cross-modal face+voice→`verified`; privacy-gate refusal + audit;
- enrollment conversational flow (via web API contract);
- observation insert with bbox/place/time/vector correctness; last_sighting + in_place queries deterministic;
- coalescing (no duplicate rows per window); instance-search ranking; privacy gate on face obs;
- restart persistence: a fresh `ObservationRecorder` on the same DB reads prior observations;
- regression wall green with the deterministic suite.

## 6. Evidence gates (on-Mac, real images/objects/lighting)
1. **Live detection:** common household objects ≥10 FPS sustained, world-state entities updating with correct last_seen decay.
2. **Identity:** 3 enrolled persons, tier transitions exercised live incl. one deliberate ambiguity (stays `unknown`).
3. **Cross-modal:** face + voice co-presence escalates to `verified` in a recorded session.
4. **Spatial recall:** visit two places, leave a known object at the first, return later; "where did I last see my blue mug?" returns the correct place + approx-time — recorded, reproducible trace.
5. **Durability:** after restart with a fresh process, `last_sighting` still answers, proving vectors + episodes in canonical DB.
The first three carry over from the former face/documentation plan; the last two (spatial recall,
durability) gate the new observation-memory work. All gates are the workstream boundary.

## 7. Scope of first implementation (smallest closing at a time)
1. `observation_records` table + `ObservationRecorder` (persist + coalescing) + tests.
2. Wire recorder into `MultimodalRuntime`/camera loop (identity + object resolution).
3. `last_sighting` / `in_place` / instance `search` retrieval + web endpoints.
4. Naming loops → conversational enrollment (GAP-S3), auto place (GAP-S2).

## 8. Non-Do
- No second database (single `novi.db`).
- No cloud vision/embedding path; no ANN index yet.
- No change to `novi/brain/` core; `novi/web/ui/` React SPA untouched.

## 9. Status
**OPEN.** Recognition + vector storage shipped (see §2). Spatial observation memory (§3–§4) is
planned, not implemented. Registration into `02_PERCEPTION_IMPLEMENTATION_INDEX.md` is a
separate follow-up patch (workflow rule 2). Implementation waits for user approval of this doc.

Header note: this file consolidates the former `02_FACE_AND_OBJECT_RECOGNITION.md` and
`03_SPATIAL_OBSERVATION_MEMORY.md` into one canonical plan. The former `03` file was removed.