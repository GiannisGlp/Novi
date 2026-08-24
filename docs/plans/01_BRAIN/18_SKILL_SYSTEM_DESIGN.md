# 17 — Brain Skill System: analysis & solution

*2026-08-23. Goal: "analyze and come back with a solution of how we could load
some skills to Novi — examples being humanizer, maths, pdf reader and creator."*

## 1. Analysis

### 1.1 What a "skill" actually is (verified on disk)

The coding-agent harness skills this request references are **portable folders,
not code plugins**: one `SKILL.md` with a small frontmatter block plus markdown
instructions, optionally a bundled script:

```
skills/<name>/
  SKILL.md        # frontmatter (name, description, kind, triggers, script) + instructions
  <script>.py     # optional executable entry point, JSON-on-stdout
```

Three properties make the pattern work:
1. **Progressive disclosure** — only `name`+`description` stay resident; the
   full body loads when the skill activates. Context cost is bounded no matter
   how many skills exist.
2. **Activation is decided cheaply** — trigger phrases/description matching,
   not model reasoning.
3. **Capability lives in files** — installing a skill is copying a folder; no
   registry edits, no code changes.

### 1.2 What Novi already has to build on

| Need | Existing surface |
|---|---|
| Deciding *when* something applies | Deterministic dialogue classifiers (`dialogue.py`: `_is_joke_request`, …) |
| Doing the work | LLM transport (`_chat(system,user)`) for text; Python subprocesses for tools |
| Trust boundary | FORBIDDEN assistant-speak guard runs *after* any content transform |
| Governance | `AuditTrail.record(...)` on consequential actions; privacy classification on every memory admit |
| Provenance | Memory admits carry `provenance.source`; recall surfaces it |
| Honest degradation | Established pattern: optional deps (MiniLM/OpenCV/Ollama/networkx) degrade deterministically |

Novi has **no plugin system today** — which is fine: the skill pattern needs
exactly one loader, not a framework.

### 1.3 The requested examples decompose into two kinds

| Requested | Kind | Needs LLM? | Works offline? |
|---|---|---|---|
| humanizer | **instruction** (style rules applied to a draft reply) | yes | degrades to no-op without Ollama |
| maths | **script** (deterministic evaluation) | no | fully |
| pdf reader / creator | **script** (pypdf/fpdf2 via bundled scripts) | no | once deps installed |

This split drives the whole design: scripts give Novi *capabilities*, even
model-free; instruction skills shape *how it speaks*, always behind the
existing rule guards.

## 2. Solution

```
novi/skills/                  # shipped packages (inside the package)
~/.novi/skills/               # user-installed packages (config: MacBrainConfig.skill_dirs)

novi/brain/skills.py
  SkillManifest               # frozen frontmatter: name/description/kind/triggers/script/path
  load_manifest(path)         # validate; None on any malformation (never raises)
  SkillRegistry(dirs)
    .discover()               # manifests only (progressive disclosure)
    .catalog()                # manifest snapshots for prompts/UI
    .body(name)               # full instructions, loaded on activation
    .match(text)              # whole-word trigger ranking, deterministic
    .run(name, args)          # script execution (below), structured SkillRunResult

engine integration
  brain.skills                # registry, shipped + user dirs
  brain_use_skill(name,args)  # run → emit skill.invoked → AuditTrail.record →
                              #   admit memory provenance source="skill:<name>"
```

Script execution contract (the security perimeter):
- one **allowlisted interpreter** (`sys.executable`), script path resolved
  inside the skill directory at manifest-load time (escapes rejected);
- **hard timeout** (default 20s) kills runaway processes;
- **JSON object on stdout** or the run fails with `outcome:"error"`;
- optional-dependency gaps return `{"outcome":"dependency_missing",
  "dependency": ...}` so Novi can say plainly what's missing instead of failing silently;
- every invocation audited (`action="skill:<name>"`) and emitted;
- results admitted to memory classified through governance, confidence 0.9,
  provenance `skill:<name>` — recall always shows where tool facts came from.

Instruction skills (P2, next): after `_compose_reply_impl` drafts a reply, if a
matched instruction skill applies and an LLM transport exists, prepend its body
to the system prompt for a single rewrite pass; the FORBIDDEN guard and all
rule checks still run **after** the rewrite. No transport ⇒ skill skipped, honest.

## 3. Implemented now vs roadmap

**P1 — implemented & tested**: loader/registry/matcher/runner; shipped
skills in **`novi/skills/`** (moved into the package): `pdf-reader`,
`pdf-creator` (original Novi authorship) and `humanizer`
(ported from the agent-skills catalog); engine `brain.skills` +
`brain_use_skill`; 19 tests (`novi/brain/tests/test_skills.py`).

### Skill sourcing policy (license survey of the .dsh catalog, 2026-08-23)

The agent-harness catalog this design was inspired by lives at
`.dsh/skills/` (166 packages). License survey: **2 MIT** (`humanizer`,
`pacsomatic`), **4 Anthropic all-rights-reserved** (`pdf`, `docx`, `xlsx`,
+1), **159 without a license file** (default copyright — not redistributable).

Policy that follows:
- MIT-licensed skills are ported with their `LICENSE` file and attribution
  (`humanizer` done; frontmatter extended with Novi's kind/triggers and a
  "Novi usage" section; body kept upstream-faithful, pinned by test).
- Anthropic-reserved and unlicensed skills are **not** pasted. Where Novi
  needs the capability (pdf reader/creator, maths), it gets original
  Novi-authored implementations instead.
- The loader reads the catalog's format either way (block-scalar
  descriptions included), so future properly-licensed skills stay
  drop-in compatible.

### External sources used (2026-08-23 web search, all MIT-verified)

Advanced math/geometry skills were sourced from two MIT-licensed GitHub
repositories found via web search, ported with adapted frontmatter
(kind/triggers/metadata.origin) and a "Novi usage" section:

| Novi skill | Upstream | Source repo |
|---|---|---|
| `humanizer` | humanizer v2.11.2 | agent-skills catalog (.dsh, MIT) |
| `geometry-construction` | construct-geometric-figure (+CITATIONS.bib) | [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac), MIT |
| `geometry-proofs` | prove-geometric-theorem | [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac), MIT |
| `trigonometry` | solve-trigonometric-problem | [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac), MIT |
| `prime-numbers` | analyze-prime-numbers | [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac), MIT |
| `symbolic-math` (hybrid: body + sympy `solve.py`) | sympy skill | [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates), MIT |

`symbolic-math` is the first **hybrid** skill: the ported instruction body
guides LLM reasoning while the bundled `solve.py` executes real symbolic
operations offline through the installed sympy 1.14.0 (solve / diff /
integrate / simplify / expand / factor / limit), JSON-on-stdout, honest
`dependency_missing` if sympy is ever absent.

### Domain expansion (2026-08-23, second sourcing round)

Covering advanced math/algebra, computer & data science, business
management, sales & marketing — same license discipline:

| Novi skill | Kind | Source |
|---|---|---|
| `linear-algebra` | hybrid (numpy `linalg.py`: solve/det/eig/rank/inverse/mul) | original |
| `data-profile` | script (stdlib CSV profiler: types, missing, numeric stats, top values) | original |
| `statistical-analysis`, `sql-pro`, `ceo-advisor`, `marketing-strategy`, `copywriting` | instruction | ported from [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT; business skills © Alireza Rezvani) |

Matcher upgraded for multi-word triggers: hyphenated triggers like
`go-to-market` match their contiguous word sequence after tokenization.
Runner upgrade: a script's structured `{"ok": false}` JSON is honored even
when it exits nonzero, so honest errors survive end-to-end.

**P2 — dialogue wiring for instruction skills** (~half day): apply matched
instruction bodies as a rewrite pass in chat; add `skill.applied` event.

**P3 — permission grants** (~day): per-skill capability declarations
(filesystem scope, network off by default) confirmed per person via the
existing relationships/preferences layer before first use; audit shows grant.

**P4 — distribution** (~day): `skills install <path|git>` into
`~/.novi/skills`; signature/manifest hash check; sync across machines.

## 4. Verification evidence (P1)

- `pytest novi/brain/tests/test_skills.py` — 19 passing: discovery, malformed
  manifests rejected, path-escape rejected, whole-word matching (no
  "mathematics"→maths false positive), `12*(3+4)=84`, `"15% of 240"=36`,
  `2^10=1024`, bad input refused, dependency_missing honesty, timeout kill,
  instruction-kind refuses `run()`, unknown-skill structured error, engine
  event + audit + provenance-stamped memory admit, failed runs admit nothing.
- Engine smoke unchanged; full suite re-run green after wiring.

### CS & data-science expansion (2026-08-23)

| Novi skill | Kind | Source |
|---|---|---|
| `algorithms-complexity` | instruction (sorting/graphs/Big-O/paradigms — original text) | original |
| `exploratory-data-analysis`, `scikit-learn`, `matplotlib` | instruction | [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) (MIT) |
| `version-ml-data` (DVC dataset versioning) | instruction | [pjt222/agent-almanac](https://github.com/pjt222/agent-almanac) (MIT) |

A candidate algorithms skill from Tibsfox/gsd-skill-creator was rejected
(NOASSERTION license) and written originally instead. Matcher ranking now
prefers longer (more specific) trigger matches over alphabetical ties.

### maths skill removed (2026-08-23)

The standalone `maths` skill was removed by product decision; its exact
arithmetic (percent-of phrasing, word ops, pure-expression evaluation) was
absorbed into `symbolic-math` (hybrid script), which also inherits its
triggers (calculate/compute/solve/math/percent). No capability lost; one
fewer overlapping skill.

### diagram-design (2026-08-23)

`diagram-design` (instruction, original Novi authorship): choosing the right
Mermaid diagram type by question, syntax essentials, and readability rules
(shape/label-first colorblind-safe emphasis, node-count budgets, labeled
decision edges). Dedicated mermaid repos found via web search were skipped —
none carried a license.

### P3 implemented — dynamic instruction-skill activation (2026-08-23)

`_matched_instruction_guidance(grounding_text)` runs on every reply:
instruction-kind skills whose triggers match the utterance plus the discourse
topic hint get their bodies loaded on demand, clipped to a per-skill char
budget at a line boundary (max 2 skills), and injected into that reply's
system prompt. Every activation emits `skill.applied` and is surfaced in the
reply grounding (`skills_applied`). Script/hybrid skills keep their own paths;
their bodies are never prompt-injected.

### Context-sourced activation + always-on humanizer (2026-08-23)

`_matched_instruction_guidance` now takes a second source: ``memory_text`` —
recent knowledge/recall/perception facts plus the last two history turns — so
skills fire from what Novi saw, heard, or remembers, not only from the current
utterance. Sources merge with per-name dedupe; the 2-skill cap and 1600-char
budget are unchanged.

Humanizer is special-cased as an **unconditional style pass**: its principle
sections (up to the example-heavy pattern catalog) are extracted once per
process (`_humanizer_core_cache`, ~2.5 KB) and appended to every composed
reply's system prompt, silently and never consuming a matched-guidance slot.
It appears in `skills_applied` on every LLM reply; `skill.applied` events
still fire only for context-matched skills to avoid spam.

### P4 implemented — centralized SkillActivator (2026-08-23)

Skill activation moved out of chat into `novi/brain/skill_activation.py`
(`SkillActivator`, engine-owned at `brain.skill_activator`). One place now
decides relevance for every response surface:

- **guidance_for(utterance, memory_context)** — instruction-skill prompt
  guidance (budgeted, capped), considering utterance + memory + primed set.
- **style_pass_block()** — the always-on humanizer pass, process-cached.
- **observe_cycle(...)** — each engine cycle primes instruction skills from
  perception detections, recalled memories, and the situation narrative
  (`skill.primed` events); primes decay after 10 cycles, capped at 4,
  humanizer never primed.

Chat (`chat.py`) is now a thin consumer: its two helpers delegate to the
activator; auto-execution (`plan_auto`) and `@skill` parsing remain reply-time
entry points into the same governed engine executor. New tests cover priming
without utterance matches, TTL expiry, cap/humanizer exclusion, cross-consumer
sharing, and cycle-primed → later-reply shaping.

### Audio-STT priming symmetry (2026-08-23)

`ingest_transcript` now primes the same `SkillActivator` with the heard
transcript (`heard=` parameter on `observe_cycle`), so speech mentioning
diagram, marketing, statistics, etc. activates those skills for subsequent
replies even when the user's next message matches nothing. Tests cover
priming from heard speech, shaping the next reply, and no-false-prime on
plain conversation.
