# Novi × ECC — Workflow Mapping

**Purpose:** map ECC's engineering loop onto Novi's `AGENTS.md` workflow so the two
systems reinforce each other instead of conflicting. ECC supplies the *toolbox*
(agents, skills, rules, hooks); Novi's `AGENTS.md` supplies the *project-specific
constraints* (scoped footprint, docs-first, one database, resource parity).

## The loop

ECC's canonical loop is:

```text
plan -> test -> implement -> review -> verify -> remember -> improve
```

Novi's `AGENTS.md` already encodes most of this. The table below is the authoritative
mapping — when ECC and `AGENTS.md` disagree, **`AGENTS.md` wins** (it is the
project-specific override).

| ECC stage | ECC agent / skill | Novi `AGENTS.md` equivalent |
|---|---|---|
| **plan** | `planner` agent | Rule 2 — docs-first: definition doc in `docs/plans/<workstream>/NN_<NAME>.md` (Objective / requirements / contracts / evidence gates / Status), human reviews before implementation |
| **test** | `tdd-guide` agent | Rule 5 — strict TDD: watch each test fail for the right reason, then minimal GREEN; deterministic fakes so CI needs no hardware/models |
| **implement** | — | Rule 3 — step-by-step patches (one coherent change set, humans review and commit); Rule 1 — scoped footprint (read-import only, never modify other packages) |
| **review** | `code-reviewer` agent | Rule 3 — humans review diffs and commit; `novi/brain/` is a PARALLEL-WORKSTATION ZONE (do not modify unless tasked) |
| **verify** | — | `.venv/bin/python -m pytest novi/<pkg>/tests -q`; `.venv/bin/python -m ruff check`; full suite `novi/{integration,perception,voice,brain,web,cognition,contracts}/tests` |
| **remember** | — | `docs/00-strategy/STATUS_*.md` (source of truth), completion tracker, gap analysis |
| **improve** | — | gap analysis → next steps (the loop feeds back into the plan) |

## Where ECC lives in this repo

- **Plugin** — `ecc@ecc` (v2.2.0), declared in `.claude/settings.json`
  (`extraKnownMarketplaces` + `enabledPlugins`). Installed at user scope; the
  project declaration makes the repo self-contained for anyone who clones it.
- **Rule packs** — `.claude/rules/ecc/common/` (language-agnostic) and
  `.claude/rules/ecc/python/` (Python-specific). Copied whole (not flattened) so the
  language files' `../common/` references resolve. Language-specific rules override
  common rules where idioms differ.
- **Hooks** — `.claude/settings.json` already runs `ruff check --fix` on `Write(*.py)`;
  ECC's own hooks are governed by the plugin's `hooks_enabled` / `hook_profile` config
  (defaults: enabled, `standard`).

## Known differences (resolved)

1. **Git workflow.** ECC's default `common/git-workflow.md` assumed feature branches +
   pull requests. Novi overrides this: **commit directly to `main`, never push** — the
   user reviews local commits and pushes when they see fit. The rule file has been
   rewritten to match (see `.claude/rules/ecc/common/git-workflow.md`).
2. **Commit style.** ECC recommends conventional commits (`feat:`, `fix:`, …). Novi's
   history has been terse (`optimize`, `p plan`). Going forward, prefer
   conventional-commit prefixes for new work; do not rewrite history.
3. **Research order.** ECC's `development-workflow.md` says "GitHub code search first,
   then library docs, then Exa." Novi's rule 2 says "docs first" for *new capabilities*.
   These compose: research/reuse first (ECC), then write the definition doc (Novi)
   before any code.
4. **Review ownership.** ECC's `code-reviewer` agent is advisory; Novi's rule 3 keeps
   the *human* as the committer. Use the agent to surface CRITICAL/HIGH issues, but a
   human still reviews and commits.

## Status

**ACTIVE** — ECC plugin + rule packs + project declaration installed 2026-08-27.
Revisit this mapping if ECC's loop or `AGENTS.md` changes materially.
