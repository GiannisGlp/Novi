# Human ratings review — how to fill this workbook

Pairwise: **new = nemotron compact-prompt live (run 1522)** vs **old = frozen
deterministic baseline v6**. One row per scenario (68 rows; the 4 "regressed"
rows are listed first).

Open `ratings_review_workbook.csv` in Excel/Numbers/Sheets. Read the two
responses (old = left, new = right; multiple turns joined with ` | `).

## Fill only the EMPTY columns (leave `draft_*` as reference)
- `understood` … `trust` — 1–5:
  1 = clearly failed, 3 = mediocre, 5 = fully natural/correct/trustworthy.
- `preference` — which reply you'd rather receive: `old`, `new`, or `tie`.
- `made_repeat_yn`, `hallucinated_yn`, `unnecessary_q_yn` — `yes` / `no`
  (only if you observed it; blank if unsure).
- `what_wrong`, `what_instead`, `what_info` — free text, optional:
  what was wrong, what Novi should have said, what info it should have used.

## Focus suggestions (if you want a shorter pass)
The highest-value rows:
1. the 4 `regressed` rows (top of file) — is the new (live) reply really worse?
2. rows where `note` is non-empty (machine flagged a minor trailing question);
3. rows where you disagree with the `draft_preference`.

## After you finish
Save the CSV (keep the filename) and hand it back; the draft scores get
replaced by yours and `conversation_pairwise collect` is re-run to produce
the human-backed `ratings-summary.json`.
