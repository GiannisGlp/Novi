# Decision record: conversational model routing (2026-09-06)

Status: accepted (single-model primary; multi-backend router deferred to a
machine with more RAM or a cloud GPU).

## Evidence (68-scenario benchmark, compact prompts ~2.0K tok/turn)

| Config | Replay | Capability honesty | Referent | Correction | Recovery | Memory retr. | Soak |
|---|---|---|---|---|---|---|---|
| nemotron-3.5-lightning (1522) | 64/68 | 3/3 | 6/7 | 6/7 | 2/2 | 7/7 | PASS (fast) |
| qwen3:8b (r1, post quote-fix rescore) | 64/68 | 2/3 | 6/7 | 7/7 | 2/2 | 6/7 | — |
| qwen3:8b + triage fixes (subset 6/6) | C-003/C-082/C-160/C-172 fixed | — | — | — | — | — | — |
| v4 trained 4B adapter | 6/8 subset (referent-limited) | — | — | — | — | — | — |

Residual replay fails observed across runs (C-040, C-154, C-161, C-172,
C-003, C-082, C-160) all PASS in other runs/models → **run-to-run LLM
variance**, not systematic class failures. See the pairwise ratings draft
(45 new / 19 tie / 4 old) for the qualitative layer.

## Decision

1. **Primary conversational model: qwen3:8b** with compact prompts.
   - Best balance across the classes that mattered this round: correction
     handling 7/7, recovery 2/2, referents (post-triage verified), with
     honesty restored by the quote-normalization + triage fixes.
   - Runs inside the 36GB budget (~18-25GB alone; never stacked with Ollama
     nemotron or an MLX process).
2. **Alternate: nemotron-3.5-lightning** when honesty/capability framing is
   the priority (3/3 with zero criticals in run 1522) or when the faster
   soak cadence matters. Both are 64/68 — the choice is operational, not
   quality-critical.
3. **Trained adapters (v4 on qwen3:4B):** low-RAM conversational option
   (~10GB) with the style/grounding classes fixed; not referent-grade.

### v4 real-session feel-check (2026-09-06 evening) — NOT deployable
Driving v4 through the live brain (serve_adapter.sh + openai-compatible)
over a 9-turn natural session: memory/preference/correction turns behaved
(recalled and applied "dark -> light interiors", polite, no hallucination),
but **open information requests still emit the v1 echo template**
("Good question — what's your angle on Model/range/interior?") and per-turn
latency was 10-37s. The PASS-reply LoRA did not robustly cure the echo in
the real prompt distribution on a 4B base. **Verdict: v4 is an experiment,
not a runtime model.** Conversational runtime stays qwen3:8b (primary) /
nemotron (alternate) on the compact prompts; adapter work needs either an
8B-base fine-tune (bigger machine) or closing the remaining training/
distribution gap before it is considered again.
4. **Multi-backend per-turn routing is NOT deployed** on this machine: two
   resident models exceed 36GB. If a future host allows it, route per class
   (referent/correction/recovery-heavy → qwen3:8b; honesty/memory/emotion →
   nemotron; simple/style turns → 4B+v4) using the brain's existing
   `route_for_turn` tier signal and the OpenAI-compatible dialect
   (`serve_adapter.sh` shows the wiring).

## Open items
- Quantify residual variance with N-run repeats before treating any single
  run's 4 fails as regression.
- Optional: reduce context further to make 8B LoRA training feasible.

## Variance follow-up (2026-09-06 evening)
Three full runs on current HEAD each landed at 64/68 with ROTATING failure
sets (nemotron: C-040/C-154/C-161/C-172; qwen8b r1: C-003/C-082/C-160/C-172;
qwen8b r2: C-032/C-040/C-143/C-172). Conclusion: individual run fails are
mostly LLM noise; C-172 (correction without naming the subject) recurred in
3/3 runs and is now fixed by a deterministic CORRECT-goal guardrail
(verified C-040/C-143/C-172 PASS on qwen3:8b). C-032 (memory restraint)
flip-flops across runs — a borderline relevance case, not a systematic
regression.
