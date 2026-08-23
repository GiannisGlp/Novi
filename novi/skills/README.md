# Novi Skills

Skills are portable capability packages Novi loads dynamically: each folder
holds a `SKILL.md` (frontmatter + instructions) and, for executable skills, a
bundled Python script with a JSON-on-stdout contract.

**Location:** this directory (`novi/skills/`) ships with Novi. User-installed
skills go to `~/.novi/skills/` or any directory listed in
`MacBrainConfig(skill_dirs=(...))`.

**How Novi uses them**

1. *Deterministic auto-run* — when a message confidently matches a script
   skill's triggers and an argument can be extracted without a model, the
   brain runs it through governed invocation and answers from the exact
   result. Works fully offline.
2. *Model-requested* — the local LLM is told which runnable skills exist in
   every system prompt; it can answer with one strict line,
   `@skill <name> <arguments>`, which the brain parses, executes, and turns
   into a natural reply (one bounded second pass).
3. *Direct* — `brain.brain_use_skill(name, args)` from code or tests.

Every invocation emits a `skill.invoked` event, lands in the AuditTrail, and
successful results are stored to memory with provenance `skill:<name>`.

## Shipped skills

| Skill | Kind | What it does | Triggers (auto-activation) | Origin |
|---|---|---|---|---|
| `maths` | script | Exact arithmetic: expressions, `15% of 240`, word ops (plus/minus/times), powers | calculate, compute, solve, math, percent… | original (Novi) |
| `pdf-reader` | script | Extract text from local PDF files, page-ranged (needs optional pypdf; reports `dependency_missing` honestly) | pdf, read-pdf | original (Novi) |
| `pdf-creator` | script | Create a titled PDF from plain lines (needs optional fpdf2; reports `dependency_missing` honestly) | create-pdf, make-pdf | original (Novi) |
| `symbolic-math` | hybrid | Symbolic algebra & calculus via sympy: solve, diff, integrate, simplify, expand, factor, limit — exact results, offline | algebra, derivative, integral, simplify, factorize, calculus… | adapted from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `geometry-construction` | instruction | Ruler-and-compass Euclidean constructions with step-by-step justification; includes classical citations | construction, compass, euclidean, bisector, polygon | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `geometry-proofs` | instruction | Prove geometric theorems by Euclidean axiomatic method | prove, proof, theorem, pythagorean, congruent | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `trigonometry` | instruction | Trig equations, triangle resolution (SSS/SAS/ASA), identities, applied modeling | trigonometry, sine, cosine, triangle-sides | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `prime-numbers` | instruction | Primality testing, factorization, divisibility analysis | primes, prime, divisibility, factorization | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `humanizer` | instruction | Rewrite AI-sounding text so it reads naturally without changing claims | humanize, rewrite, natural, sound-human | agent-skills catalog humanizer v2.11.2 (MIT, © 2025 Siqi Chen) — body kept upstream-faithful |

## Skill kinds

- **script** — runs bundled Python deterministically (no LLM needed).
  Contract: JSON object on stdout; optional dependencies must report
  `{"ok": false, "outcome": "dependency_missing", "dependency": "..."}`
  instead of failing silently.
- **instruction** — pure guidance the LLM applies when active; FORBIDDEN
  guard and dialogue rules always run after it.
- **hybrid** — both: instructions for reasoning, script for exact execution.

## Adding a skill

```
~/.novi/skills/<my-skill>/
  SKILL.md      # ---\nname: my-skill\ndescription: ...\nkind: script|instruction|hybrid\ntriggers: a, b\nscript: script.py\n---
  script.py     # prints {"ok": true, ...} as JSON
```

Restart Novi (or call `brain.skills.discover()`); invalid manifests are
skipped safely, never crash the brain.

*License note:* only MIT-licensed third-party skills are ported here (with
LICENSE/attribution kept); everything else is original Novi authorship.
