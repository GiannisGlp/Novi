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
3. *Instruction guidance* — when discussion context (the utterance plus the
   discourse topic) matches an instruction skill, its body is injected into
   that reply's system prompt as bounded guidance (`skill.applied` event).
4. *Direct* — `brain.brain_use_skill(name, args)` from code or tests.

Every invocation emits a `skill.invoked` event, lands in the AuditTrail, and
successful results are stored to memory with provenance `skill:<name>`.

## Shipped skills

| Skill | Kind | What it does | Triggers (auto-activation) | Origin |
|---|---|---|---|---|
| `pdf-reader` | script | Extract text from local PDF files, page-ranged (needs optional pypdf; reports `dependency_missing` honestly) | pdf, read-pdf | original (Novi) |
| `pdf-creator` | script | Create a titled PDF from plain lines (needs optional fpdf2; reports `dependency_missing` honestly) | create-pdf, make-pdf | original (Novi) |
| `symbolic-math` | hybrid | Arithmetic AND symbolic algebra/calculus via sympy: `15% of 240`, solve, diff, integrate, simplify, expand, factor, limit — exact results, offline | algebra, derivative, integral, simplify, factorize, calculus… | adapted from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `geometry-construction` | instruction | Ruler-and-compass Euclidean constructions with step-by-step justification; includes classical citations | construction, compass, euclidean, bisector, polygon | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `geometry-proofs` | instruction | Prove geometric theorems by Euclidean axiomatic method | prove, proof, theorem, pythagorean, congruent | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `trigonometry` | instruction | Trig equations, triangle resolution (SSS/SAS/ASA), identities, applied modeling | trigonometry, sine, cosine, triangle-sides | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `prime-numbers` | instruction | Primality testing, factorization, divisibility analysis | primes, prime, divisibility, factorization | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `linear-algebra` | hybrid | numpy-backed linear algebra: solve Ax=b, determinant, eigenvalues/vectors, rank, inverse, products | matrix, eigenvalue, determinant, linear-system | original (Novi) |
| `data-profile` | script | Profile a CSV offline: rows/columns, types, missing values, numeric stats, top categorical values | dataset, csv, data-summary | original (Novi) |
| `statistical-analysis` | instruction | Hypothesis tests (t-test, ANOVA, chi-square), regression, correlation, Bayesian stats, power analysis | statistics, hypothesis-test, regression, p-value | adapted from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `sql-pro` | instruction | Modern SQL: query design, joins, OLTP/OLAP optimization patterns | sql, query, join, select | ported from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `ceo-advisor` | instruction | Executive/business management: strategy analysis, financial scenarios, board governance, investor relations | business-strategy, board, investors, executive | ported from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT, © Alireza Rezvani) |
| `marketing-strategy` | instruction | Product marketing: positioning, ICP, GTM playbooks, competitive battlecards, sales enablement | marketing, positioning, go-to-market, competitor, launch-plan | ported from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT, © Alireza Rezvani) |
| `copywriting` | instruction | Marketing copy: rewrite/improve ads, landing pages, taglines, sales content | copywriting, sales-copy, ad-copy, landing-page-copy, tagline | ported from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `algorithms-complexity` | instruction | CS fundamentals: sorting/searching/graphs, data-structure selection, Big-O & amortized analysis, design paradigms | algorithm, big-o, complexity, data-structures | original (Novi) |
| `exploratory-data-analysis` | instruction | Systematic EDA workflow on datasets before modeling | eda, explore-data, dataframe | ported from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `scikit-learn` | instruction | ML in Python: classification, regression, clustering, pipelines, model evaluation | machine-learning, model-training, classifier, train-model | ported from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `matplotlib` | instruction | Data visualization: line/scatter/bar plots, histograms, subplots, styling | plot, chart, visualize, histogram | ported from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `version-ml-data` | instruction | Version ML datasets with DVC and remote storage | dataset-version, ml-data, training-data-version | ported from [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |
| `diagram-design` | instruction | Design clear Mermaid diagrams: flowcharts, sequence/state/ER diagrams, architecture graphs — type choice, syntax, readability rules | diagram, flowchart, sequence-diagram, er-diagram, mermaid, architecture-diagram | original (Novi) |
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
