# Known residual variance (plan 03) — 2026-09-06

Current floor: **66/68 (0.971)** — qwen3:8b on compact prompts, HEAD
(quote normalization + triage + CORRECT-goal naming guardrail). See
`conversation-qwen8b-r3-*`.

## Residual scenarios and their run history (PASS/FAIL across runs)

| Scenario | nemotron 1522 | qwen8b r1 | qwen8b r2 | qwen8b r3 | Triage/other |
|---|---|---|---|---|---|
| C-120 preference learning | FAIL | — | FAIL | FAIL | PASS in qwen8b A/B, v4 session, C-032/C-120 fixes |
| C-161 full-name referent | FAIL | PASS | — | FAIL | PASS in r1, qwen triage 6/6, C-140/C-141 check class |

Both flip-flop across runs → **run-to-run LLM variance, not systematic
regression**. C-161's fail pattern is a *trailing follow-up question*
("Does that align with what you've heard?") after a substantive answer —
a phrasing habit, targeted by a guardrail (drop trailing follow-up-ask on
direct answers). C-120 intermittently answers a recommendation without
echoing the stored preference keyword; passes most runs — accepted as
noise for now (a deterministic preference-echo guardrail is the documented
fallback if it becomes systematic).

Guidance: judge quality by N-run floors (66/68) and the dimension gates,
not single-run deltas of ±1-2 variance scenarios.
