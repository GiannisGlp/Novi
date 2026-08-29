# Novi — Gap & Bug Analysis (2026-08-28)

**Status:** ANALYSIS — implementation targets for the current WIP (plan 20 follow-through)
**Date:** 2026-08-28
**Scope:** uncommitted working tree (model persistence / runtime switch / preview downscale / narrative cache / poll changes) + plan-vs-code drift across `docs/plans/01_BRAIN/` and `docs/plans/02_PERCEPTION/`
**Method:** every finding below was verified against the working tree (`git status` at `d61a6c0` + uncommitted WIP), with file:line evidence — by direct analysis, the plan-audit and health subagents, and a code-reviewer pass (which re-ran the web suite 88 passed + UI hook tests 7 passed and traced each failure path). Full suite: brain 1,467 passed · web+integration 177 passed · UI 54 passed · new WIP tests 11 passed. `ruff check novi/` = **54 findings**.
**Predecessor:** [`docs/audits/NOVI_CONSOLIDATED_GAP_ANALYSIS_2026-08-26.md`](../../audits/NOVI_CONSOLIDATED_GAP_ANALYSIS_2026-08-26.md) — this doc supersedes it for the state as of 2026-08-28.

---

## 1. Bugs in the uncommitted WIP (severity-ranked)

### H1 — Object enrollment crops the full-res bbox against a downscaled preview (coordinate mismatch)

`_start_camera_loop` (`novi/web/integration_api.py:182-188`) now stores the **downscaled** preview (`encode_preview_jpeg_b64`, ≤640px / q72) in `mm_last_frame_b64`. `enroll_object_from_camera` (`integration_api.py:390-433`) decodes that preview and then calls `embedder.embed(jpeg, [bbox])` with a `bbox` taken from `mm_last_tracks` — which was computed by `process_camera_frame` on the **full-resolution** `rec.frame.payload`. On any frame wider than 640px the crop is taken at wrong coordinates (up to ~2× offset), so object enrollment stores a misaligned/mis-scoped embedding. Before this WIP, `mm_last_frame_b64` was the full-res JPEG (`encode_frame_jpeg_b64`), so coordinates matched.

**Failure scenario:** camera 1280×720 → preview 640×360; the largest non-person track bbox `(x1,y1,x2,y2)` is in 1280-space, applied to a 640-wide image → wrong crop, degraded embedding, wrong "object instance" identity. `MacCamera` requests MJPG 640×480 (`brain/io.py:50-51`) but `CAP_PROP_FRAME_WIDTH` is a driver hint and many webcams deliver 1280×720; when the frame is wider than 640, the track bbox coordinates exceed the decoded preview and `_embed_crop` (`real_backends.py:320-324`) **clamps to a wrong or empty region** — silent mis-enrollment or "could not embed the object crop". No guard checks that the decoded image dimensions match the frame the tracks were computed on. At exactly 640px the quality-72 degradation still applies. (Face enrollment is worse in a different way: it never gets the coordinate mismatch, but the asymmetric embed source — q72 re-encode vs the loop's full-quality payload — can push matches below the SFace `tau_match=0.42` threshold.)

**Fix:** keep a full-res `mm_last_frame_bytes`/`mm_last_frame_b64` (full-res) for the enrollment paths and only use the downscaled preview for `/api/preview` display. The class annotation `mm_last_frame_bytes: bytes | None` (`integration_api.py:33`) is declared but **never assigned** — the intended full-res store exists only as a type hint today.

### H2 — Face enrollment quality regressed to a low-res source

`enroll_face_from_camera` (`integration_api.py:346-388`) embeds the **downscaled q72** preview instead of the full-res frame. Face embeddings are resolution-sensitive; enrollment now matches against a ≤640px, heavily-compressed face while the live loop embeds full-res frames, biasing recognition against the enrolled identity.

**Fix:** same as H1 — source enrollment from the full-res frame, not the preview.

### H3 — `_apply_model_to_components` prefers `.model` assignment over `set_model`; `OllamaReasoningProvider.set_model` is unreachable in the web path

`server.py:654-665` checks `hasattr(llm, "model")` **before** `hasattr(llm, "set_model")`. A provider that exposes both (as `OllamaReasoningProvider` does: `ollama_reasoning.py:100,103`) takes the `.model = self.llm_model` branch — but assigning the attribute **does not rebind** the model name captured by the `_ollama_backend_fn` closure, so the backend keeps calling the old model. `set_model` (which correctly rebuilds the closure) is shadowed.

Today this is latent: `_build_reasoning` (`server.py:361-382`) always constructs `DeliberativeLLMReasoningProvider` (or wraps it in `ReasoningRouter`), never `OllamaReasoningProvider`, so the `.model` branch is correct for the current wiring and `set_model` is **dead code in the product** (no production call site; only referenced at `server.py:661-662`). But the branch ordering is a trap: if `OllamaReasoningProvider` is ever wired as the web reasoning backend, `switch_model` will silently not switch the actual model.

**Fix:** prefer the capability method first (`set_model`), fall back to attribute assignment; or drop `set_model` if it stays unused.

### M1 — `switch_model` mutates shared state without the server lock

`switch_model` (`server.py:637-652`) writes `self.llm_model` and the component `.model` attributes outside `self._lock`, while `_llm_chat`/`_llm_chat_stream`/`state`/`_llm_up` read `self.llm_model` from the HTTP and brain-loop threads. A switch mid-reply can change the model used for an in-flight LLM call, and `_llm_up()` can re-probe against the new model before Ollama has it warm.

**Severity:** low (benign race, worst case a reply uses the new model a call early), but it is unsynchronized state mutation in an otherwise lock-disciplined file.

### M2 — `switch_model` never verifies the target model actually exists in Ollama

`_llm_up()` (`server.py:619-632`) treats `GET /api/tags` → 200 as "available" for **any** model. Switching to a name that is not pulled locally (typo, or a name in `available_models` that was never pulled) leaves `_llm_available=True`, so `chat_send` (`server.py:527`) selects the LLM transport and `_llm_chat` (`server.py:682`) raises `urllib.error.HTTPError` (Ollama returns 404 for unknown models). That propagates uncaught through `dialogue.reply` (`dialogue.py:1037`) → `compose_reply` (`chat.py:1137`) → `respond` (`chat.py:760`) to the handler catch-all (`server.py:1622`) — the client gets a **500 with no graceful fallback**. The same 404 breaks `DeliberativeLLMReasoningProvider._invoke` (`deliberation.py:169`), so every `brain.step()` that escalates fails and the loop records a `web.error` event each cycle.

**Fix:** in `_llm_up`/`switch_model`, parse the `/api/tags` model list and only set `_llm_available=True` when `self.llm_model` is present.

### M3 — `_cached_narrative` regenerates the narrative under the web lock

`_cached_narrative` (`server.py:1097-1119`) runs `self.brain._episodic_narrative()` (→ LLM narrator, ~5s timeout per `narrator.py:88`) **on the `/api/state` thread under `self._lock`** whenever the last-5 episodic `memory_id`s change. A `state()` poll that lands right after a new episodic memory blocks the endpoint (and every other locked brain operation) for the whole narrator call. `_episodic_narrative` is *also* invoked from `engine._assemble_world_context` (`engine.py:855`) during `step()`, so one new episodic memory can trigger **two serialized** narrator calls (both serialize on `self._lock`, they do not overlap) — one on the engine's step thread and one on the next state poll — doubling the lock-blocking time.

**Severity:** medium — the cache fixes the "quiet world" case but moves the latency onto the poll that follows new memory; worst case `/api/state` hangs ~2-5s (up to ~10s when the engine's narrator call runs first and the poll waits on it).

**Cache-key note (verified faithful):** `_episodic_narrative` (`chat.py:260-284`) depends only on the last-5 episodic memories, which is exactly what the sig captures — so the earlier concern that non-episodic state (knowledge, summaries) would never refresh the narrative **does not materialize**. The key is correct.

### M4 — Single-round deliberation at `num_predict=300` risks truncated JSON that silently degrades to default `observe`

`_build_reasoning` (`server.py:369-373`) constructs `DeliberativeLLMReasoningProvider(..., max_tokens=300, timeout=30)` — a deliberate latency tradeoff. But the deliberation prompt (`deliberation.py:29-42`) asks for `analysis` + 2-4 `options` with pros/cons + a `decision` with rationale, which can exceed 300 tokens on qwen3. A truncated response fails `_extract_json` (`deliberation.py:45-66`) → `{}` → `action=""` → **default `observe`** (`deliberation.py:135-137`). If truncation is at all common, the router silently stops taking real actions while advertising deliberation. (~70% confidence it manifests; the code comment acknowledges the 300-token choice.)

**Fix:** raise `max_tokens` to ~600 (the provider default) or measure truncation frequency on `qwen3:4b` and clamp only if needed.

### L1 — Stale "1s /api/state poll" comments

`STATE_POLL_MS = 2000` (`useBrainState.ts:6`) but comments still say "the 1s /api/state poll" (`server.py:164,1101`). Cosmetic.

### L2 — `usePreview.test.ts` still advances timers by 700ms

`usePreview.ts` now polls at 300ms but the test (`usePreview.test.ts:28-40`) advances fake timers by 700ms — each advance fires the 300ms interval ~2×. Tests pass but no longer pin the poll cadence; the "3 empty polls" test asserts behavior, not the constant. `PREVIEW_POLL_MS` is never referenced by a test.

### L3 — `fast_*` wrapper `.model` attributes go stale on switch

`fast_narrator.model`, `fast_summarizer.model`, `fast_conv_summarizer.model` are copied from `inner.model` at build time (`server.py:224,340,357`) and never refreshed by `_apply_model_to_components` (which updates only the `inner` objects). Nothing reads them today (introspection-only), but they are observably wrong after a switch.

### L4 — `model.json` persistence is a non-atomic write

`_save_model_choice` (`server.py:75-82`) truncate-writes `_model_choice_path` (`server.py:53-59`). Two concurrent `POST /api/model` calls can interleave truncate+write and corrupt the file; `_load_model_choice` degrades to `None` gracefully and the next explicit `--model`/persisted read recovers. Placement is correct (with `store_path=None` it lands in `novi/data/model.json`, beside the canonical DB — no second DB). Fix: tempfile + `os.replace`.

### L5 — `llm_url` is not propagated to the reasoning/narrator/summarizer providers

`server.py:369` (`DeliberativeLLMReasoningProvider(model=...)`), `:330`, `:349`, `:216` all construct providers **without** `base_url=self.llm_url`, so they hit `DEFAULT_OLLAMA_URL` (localhost:11434) even when `llm_url` is customized. Only `_llm_up`/`_llm_chat`/`_llm_chat_stream` respect `self.llm_url`. Pre-existing, but the WIP diff edited these exact lines, so the inconsistency is now adjacent to the touched code.

---

## 2. Feature shipped but not wired — the biggest capability gap

### GAP-1 — Plan 20 GAP-A/B/C (event-driven autonomous speech) is implemented but **inert in the live product**

`SurgeSalienceEvaluator` + `EventSaliencePolicy` (`novi/brain/salience.py`), `respond_event` (`chat.py:797`), and the engine wiring `_maybe_autonomous_speech` (`engine.py:562-600`, called from `step()` at `engine.py:1161`) are all present and tested (`test_salience_policy.py`, `test_respond_event.py`, `test_autonomous_speech.py`). **Two production wiring gaps keep it dead:**

1. **`event_autonomy_enabled` defaults `False`** (`engine.py:114`) and **no production caller sets it** — only tests do (`test_autonomous_speech.py:40,66,79,94,118`). The web server builds the brain with `MacBrainConfig(initiative_enabled=True, sleep_every_n_cycles=...)` (`server.py:265`) and never enables event autonomy. Novi therefore never speaks proactively from events in the shipped web app — exactly the behavior plan 20 §1 GAP-A describes.
2. **Only `presence.*` and `scene.changed` reach the InputBus.** The camera loop submits those two (`integration_api.py:263-270`). `identity.recognized`/`object.recognized` are emitted only on the multimodal event trail (`multimodal.py:151,337-339`) and **never submitted to the brain bus**; `hearing.anomaly` is emitted via `engine._emit` (`engine.py:1480`) but not through `submit()` → `drain_inputs`, so it never feeds the salience evaluator's drained-event stream. The `identity.recognized` (`salience.py:162`) and `hearing.anomaly` (`salience.py:164`) decision branches are **unreachable at runtime**.

**Fix (two small patches):** (a) surface `event_autonomy_enabled` as a web/server config knob (default on for `--camera real`, off for demo), and (b) submit `identity.recognized`, `object.recognized`, and `hearing.anomaly` to the InputBus with the payloads (`novelty`, `person`, `label`) the evaluator already reads.

### GAP-2 — GAP-S2 auto-place enrollment exists but is off in the live camera loop

`place_auto_enroll` is implemented in `MultimodalRuntime` (`multimodal.py:419-449`) but the web runtime constructs it **without** `place_auto_enroll=True` (`integration_api.py:92-98`), so real observations stay anchored to `""` until a human manually enrolls a place.

### GAP-3 — GAP-S3 naming loops are half-closed

Object naming + history rebind exist (`multimodal.py:353-369`, `name_proposal_object`, `/api/recognition/name-object`) with tests — but **no UI or dialogue hook drives "what is this?" from a proposal**, and there is **no person-naming loop** counterpart.

---

## 3. Plan-vs-code drift (governance) — docs that mislead the reader

The 2026-08-26 consolidated analysis (G-1) called for one source of truth; that discipline has already re-eroded. Each stale claim below is verifiable today:

| Doc | Claim (status) | Reality | Evidence |
|---|---|---|---|
| `20_...PLAN.md` | **Status: PLANNED / OPEN**; §1 GAP-A/B/C "not fed a proactive utterance" | GAP-A/B/C shipped (evaluator + engine + tests); only the wiring gaps in §2 remain | `salience.py:84`, `engine.py:562,1161` |
| `20_...PLAN.md` | "full suite ~1,624" | ≥1,467 brain + 177 web/integration + 54 UI + 11 new ≈ **1,709+** | pytest runs 2026-08-28 |
| `19_...PLAN.md` | §0 table "Web server still gates the whole loop on `_chat_busy`" (`server.py:345,441,…`); "`listen()` calls `compose_reply`" | `_chat_busy` is gone (lease replaces it); `listen()` calls `respond()` | `server.py:506,581,764`; `server.py:556,592`; `test_speaking_lease_web.py:33-35` |
| `19_...PLAN.md` | §0 "Prediction error does not drive curiosity/initiative" | `prediction.sequence_violated` → `curiosity.surprise` → investigate wired | `engine.py:799-813` |
| `02_PERCEPTION/02_...md` | §9 "Spatial observation memory (§3–§4) is planned, not implemented" | Shipped in `d61a6c0` (recorder, wiring, endpoints, tests) | `observation_recorder.py:136`, `multimodal.py:393`, `server.py:1610-1615` |
| `02_PERCEPTION/00_...INDEX.md` | Recognition Status **PLANNED** | Fully implemented | `real_backends.py`, `recognition_store.py`, `test_observation_*` |
| `BRAIN_COGNITION_IMPROVEMENT_PLAN_2026-08-25.md` | Status "planned" | P1–P5 all implemented (sleep cycle, router, temporal KG, prediction, deliberation memory) | `08-26` analysis §2, `engine.py:774-816` |
| `00_BRAIN_IMPLEMENTATION_INDEX.md` | Plan 20 registered "PLANNED/OPEN 2026-08-28" | Stale vs §2 above | index line 48 |
| `00_BRAIN_IMPLEMENTATION_INDEX.md` | `17_SKILL_SYSTEM_DESIGN.md` listed | Actual file is `18_SKILL_SYSTEM_DESIGN.md` (17 appears twice, 18 absent) — **corrected to `18_` in this session**; index also now registers doc `21` | `ls docs/plans/01_BRAIN/` |
| `test_web.py:154` | docstring "qwen3:32b is the default qwen model" | default is `qwen3:4b` | `ollama_reasoning.py:11` |

---

## 4. Code-health findings

1. **`ruff check novi/` = 54 findings** (statistics 2026-08-28): F401 unused-import ×13, I001 import-sort ×11, SIM105 ×10, F841 unused-variable ×4, F811 redefined ×3, SIM102 ×3, E702 ×2, SIM117 ×2, B007/B009/B905/SIM103/SIM108/W292 ×1 each. **Only `novi/brain` is lint-gated in CI** (`brain-runtime-validation.yml`), so the `novi/web`/`novi/integration` debt (incl. three F401s in `real_io.py:13-15`) is not enforced. ~30 are auto-fixable.
2. **The new model/narrative tests are untracked.** `novi/web/tests/test_model_and_narrative.py` (11 tests, all passing) is `??` in git — until committed, the model-persistence / propagation / narrative-cache coverage does not exist in the repo, and **CI does not run `novi/web/tests` at all**, so nothing gates it.
3. **Provider-level `max_tokens`/`timeout`/clamping of `DeliberativeLLMReasoningProvider` is untested** (only the web-path defaults are pinned, in the untracked file).
4. **`OllamaReasoningProvider.set_model` has no test and no production call** — see H3. `test_model_default.py` constructs the provider but never calls `set_model`.
5. **Dead code in `chat_send_stream`:** the nested `streaming_transport` generator (`server.py:806-826`) is defined but never invoked — `compose_reply` is called with `llm_chat=self._llm_chat` (`server.py:840`). The "true streaming" path is simulated by chunking the full reply (`server.py:861-873`); the 30-line generator is misleading dead weight.
6. `useModels.setModel` (`useModels.ts:35-37`) optimistically sets `current` even when the API call fails (no try/catch) — a failed switch is reported as successful in the UI. Pre-existing, not WIP.
7. After `clear_chat` (`server.py:967`), `_last_summarized_len` is not reset, so summarization is suppressed until the thread regrows past the old watermark. Pre-existing, low severity.

---

## 5. Recommended implementation plan (phased)

**Phase 1 — fix the WIP bugs (this patch):**
- [x] H1/H2: keep a full-res frame for `enroll_face_from_camera`/`enroll_object_from_camera`; use the downscaled preview only for `/api/preview`. Remove the dangling `mm_last_frame_bytes` annotation.
- [x] H3: `_apply_model_to_components` — call `set_model` when present before falling back to attribute assignment.
- [x] M2: verify the target model exists in `/api/tags` before switching/claiming availability.
- [x] M3: move narrative regeneration off the web lock (compute on a worker, or guard the cache miss with a "regenerating" latch so the engine step + state poll never double-run the narrator).
- [x] M4: raise deliberation `max_tokens` to ~600 (provider default) or measure truncation on `qwen3:4b` and clamp only if needed.
- [x] L1/L2/L3/L4/L5 + commit `test_model_and_narrative.py` and the `test_real_io.py` preview tests (atomic `model.json` write; propagate `llm_url` to the reasoning/narrator/summarizer providers).

**Phase 2 — close the plan-20 wiring gaps (makes the shipped feature real):**
- [x] GAP-1a: `event_autonomy_enabled` config knob surfaced from the web/CLI (default on for real sensing).
- [x] GAP-1b: submit `identity.recognized`, `object.recognized`, `hearing.anomaly` to the InputBus with the payloads the evaluator reads.
- [x] GAP-2: pass `place_auto_enroll=True` from `integration_api.py` (or gate on a flag).
- [x] GAP-3: add the "what is this?" / "what's your name?" UI/dialogue hooks over `/api/recognition/proposals` + `/api/recognition/name-object`.

**Phase 3 — doc drift sweep (half-day, mechanical):**
- [x] Update plan 19/20 status lines + tables; fix the perception index; rename index entry `17_→18_`; correct `test_web.py` docstring; refresh the test-count claims.
- [x] Add a `Lint (ruff)` step for `novi/web`+`novi/integration` to CI (mirrors the brain gate) and fix the 54 findings.
