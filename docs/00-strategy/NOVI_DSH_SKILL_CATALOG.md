# Novi — DSH Skill Catalog Reference

**Purpose.** Map the `.dsh/skills/` catalog (165 skills) to the Novi project so we
know which skills exist, when to trigger them, and how each maps onto Novi's
work (autonomous embodied AI on Apple Silicon Mac; Python 3.14; PyTorch on MPS;
no CUDA/ROS). This is a working index, not a policy document.

**Convention.** "Skill" here means a documented `.dsh/skills/<name>/SKILL.md`
that a DeepSeek Harness agent can load via the `skill` tool. We note the ones
that are *high-leverage for Novi* and the ones that are only relevant if Novi
expands into a new domain.

---

## Core rule: Mac-first means no NVIDIA/CUDA

Novi runs on Apple Silicon with PyTorch/MPS. Any skill that is NVIDIA/CUDA-centric
is **mismatched** and should be reused only for its discipline, never its stack:

- `optimize-for-gpu` targets NVIDIA/RAPIDS (CuPy, cuDF, cuML, cuGraph). For Novi
  reuse only its contract-first workflow (define numerical contract, baseline,
  profile, correctness-first benchmarking) and **do not install RAPIDS/cuDF**.
- `python-ai-robotics-nvidia` — the robotics/ML environment discipline applies,
  but its NVIDIA/Jetson specifics are for the Jetson port (deferred), not the Mac.

---

## High-leverage skills for Novi (load these)

### Agent self-improvement
- **arbor** — Autonomous Optimization via Hypothesis Tree Refinement (HTR).
  Iteratively improve an artifact against a measurable objective with a
  **dev/test split** to prevent overfitting. Uses `scripts/tree.py` as a durable
  hypothesis tree (not conversation memory). Ideal for tuning Novi's harness,
  data pipeline, or model recipe over many experiments. Overkill for one-shot
  fixes. Distinguish from `hypothesis-generation` (ideation) and
  `scientific-brainstorming` (direction setting).
- **get-available-resources** — Read-only, redacted host/process resource
  snapshot (CPU, memory, disk, scheduler/container, accelerators) before any
  resource-sensitive workload. Safety contract: no stress tests, no large
  allocations, treat missing as unknown, never infer visibility = usability.
  Use before Novi plans a big local run.

### Simulation & embodied modeling
- **simpy** — Process-based discrete-event simulation (queues, resources,
  scheduling, energy budgets). Strong fit for Novi's agent/embodiment
  simulation. Pure CPU; works on Apple Silicon; SimPy 4.1.2 supports Python 3.14.
- **pymoo** — Multi-/single-objective optimization (NSGA-II/III, MOEA/D, GA/DE/
  PSO/CMA-ES) with Pareto fronts and constraints. Optimize Novi control/behavior
  parameters (e.g. energy vs speed vs safety) as Pareto search. Python-native.

### Units, uncertainty, statistics
- **uncertainty-and-units** — Track physical units (pint) and propagate
  uncertainty (uncertainties/GUM) with Monte Carlo and plausibility checks. Core
  to Novi's units/uncertainty requirement; the bundled `audit_units.py` can gate
  CI. New deps pint 0.25.3 / uncertainties 3.2.3 are already in Novi's
  `metrology` extra.
- **statistical-analysis** — Guided stats (test selection, assumption checks,
  effect sizes, power, Bayesian alternatives, APA-style reporting). Novi's
  statistical engine; closes design → power → results loop.
- **statsmodels** — Inference-first stats (OLS/GLM, mixed models, time series
  ARIMA/SARIMAX) with diagnostics. Complement to scikit-learn (prediction).
  Pin `statsmodels==0.14.6` for Python 3.14.
- **pymc** — Bayesian modeling/MCMC (NUTS), prior predictive before fitting, ≥4
  chains, report HDI. For Novi's latent-state/sensor-fusion/parameter
  uncertainty. PyMC 6 needs Python 3.12+ (fine on 3.14); Numba on Apple Silicon
  may need tuning.

### Data & modeling
- **polars** — Fast CPU-native DataFrames (lazy expressions, Arrow/Parquet).
  Great for Novi's measurement/sensor/statistical data. Works on Apple Silicon.
- **scikit-learn** — Classical ML with `Pipeline`/`ColumnTransformer`; always fit
  preprocessing inside a Pipeline (leakage); never `fit` on test data. Good for
  perception/behavior analytics baselines.
- **transformers** — Hugging Face models/pipelines/Trainer. Gives Novi a
  pretrained perception/language layer, PyTorch/MPS-compatible. Pin versions;
  fine-tune small models on Apple Silicon.
- **pytorch-lightning** — Structure PyTorch into `LightningModule`/`Trainer`;
  device-agnostic, callbacks, `seed_everything`. Clean training harness for
  Novi's networks on MPS.
- **stable-baselines3** — Reliable single-agent RL (PPO/SAC/DQN/...). Drop-in
  decision-policy trainer; use MPS device; `check_env()` before training.
- **pufferlib** — High-throughput/multi-agent RL. Prefer 3.0 Python path on Mac;
  4.0 native is CUDA/Linux-oriented. Reuse its checkpoint-hash + seed-isolation
  safety discipline.
- **aeon** — scikit-learn-compatible time-series ML (ROCKET/MiniRocket, DTW,
  forecasting, anomaly). Sensor/telemetry prediction & anomaly detection. CPU,
  ROCKET/DTW are CPU-friendly.
- **sympy** — Exact symbolic math; derive/verify closed-form kinematics/dynamics/
  reward equations, convert to NumPy via `lambdify`.
- **astropy** — Mature units/quantities, coordinates, time scales. Reusable
  `astropy.units` complement to pint if Novi handles spatial/time-indexed data.

### Scientific method & writing
- **scientific-writing** — Draft/audit manuscripts with evidence provenance
  (every claim bound to an evidence ID, never fabricate). Two-stage: AI drafts,
  human approves. Core for any Novi-generated report.
- **scientific-critical-thinking** — Evaluate claims/evidence quality (GRADE,
  RoB). Novi's reasoning guardrail against overclaiming.
- **hypothesis-generation** — Turn observations into testable hypotheses with
  rival explanations and pre-registered plans, before choosing tests (no HARKing).
- **experimental-design** — Design studies *before* data: randomization,
  replication level, blocking, factorial/DOE. Prevents pseudoreplication — the
  most common fatal error.
- **statistical-analysis** (see above) + **peer-review** (evidence-bounded
  manuscript critique) + **literature-review** (systematic multi-database
  review, verified citations, PRISMA).
- **markdown-mermaid-writing** — Mermaid-in-Markdown as the canonical doc
  standard (git-diffable, AI-parseable, accessible). The documentation layer
  wrapping the other outputs.
- **humanizer** — Rewrite AI-sounding prose to read naturally without changing
  meaning. Use for Novi's user-facing copy, docs, and release notes. Based on
  Wikipedia's "Signs of AI writing"; keep every claim, never invent facts.
- **scientific-brainstorming** — Evidence-aware ideation with adversarial
  review and decision logs. Proposals, not findings.

---

## Skills only relevant if Novi enters a new domain

These are well-built but apply only if Novi expands into the matching domain:

- **matlab** — interface/migrate legacy MATLAB/Octave code (static review only,
  never execute untrusted `.m`/MEX/MAT). Not needed for the Python/PyTorch core.
- **pydeseq2**, **arboreto**, **scikit-survival**, **bulk-rnaseq**, **scanpy** —
  transcriptomics / GRN / survival. Only if Novi does gene-expression or
  time-to-event modeling.
- **pymatgen** — materials/crystal structure. Only if Novi touches materials
  science.
- **deepchem / datamol / rdkit / molfeat / medchem / diffdock / esm / rowan /
  tamarind / biopython / gget / bioservices** — chemistry / proteins / small
  molecules / sequences. Only for a chemistry/protein frontier.
- **bids, neuroimaging (deeptools, pysam, pyopenms, matchms, flowio, histolab,
  pathml, imaging-data-commons)** — specific assay/imaging data formats.
- **qiskit/cirq/pennylane/qutip** — quantum. Only with a quantum angle.
- **fluidsim/openpiv/simPy(already)** — fluid mechanics simulation. Only if Novi
  simulates fluids.
- **usfiscaldata / market-research-reports / research-grants / venue-templates /
  latex-posters / infographics / scientific-slides / generate-image /
  scientific-schematics / docx / pptx / xlsx / pdf** — publishing/outreach.
- **consciousness-council / what-if-oracle / dhdna-profiler** — optional
  perspectives/speculation; low priority.

---

## Practical integration notes for the Novi agent

1. **Verify before acting** (`python-ai-robotics-nvidia`): query the real
   interpreter, torch/MPS availability, and environment before writing code
   that depends on it. Never assume a GPU or a stack that isn't present.
2. **Deterministic-first** (fits Novi): set seeds, pin devices, prefer
   deterministic reasoning; LLM is opt-in.
3. **Evidence-bounded**: when Novi generates reports/manuscripts, bind every
   claim to an evidence ID and use the `humanizer` and `markdown-mermaid-writing`
   conventions for prose and diagrams.
4. **Use `get-available-resources`** before any resource-sensitive run; keep
   unknown = unknown.
5. **Use `arbor`** when a repeated experiment-and-evaluate loop needs a durable
   search with a dev/test split — this matches Novi's autonomous improvement
   ambition and avoids overfitting to a feedback signal.
6. **Version-pin and wheel-check** before installing anything new on
   Apple Silicon/Python 3.14 (PyMC, statsmodels, polars, astropy, pufferlib,
   simpy, pint, uncertainties all carry pinned versions).

---

## Sources

The `.dsh/skills/<name>/SKILL.md` files themselves (read directly or summarized
by subagents). This document is a working index; re-read a skill's `SKILL.md`
before relying on its details.
