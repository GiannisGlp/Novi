# Mac Brain — Evidence Index

Consolidated on-device evidence for the Mac Brain implementation, keyed by capability.
All timestamps are UTC. Commit hashes and collection times are recorded inside each
directory (`commit_sha.txt`, `collection_time.txt`).

| Slice | Evidence (this directory) | What it proves |
|-------|---------------------------|----------------|
| Neural environment (torch/MPS) | `20260820T194919Z/neural_environment.json`, `M1-latest.json` | torch 2.13, MPS available, no CUDA (Mac) |
| Neural runtime | `20260820T203139Z/M1-runtime-latest.json` | model runtime registers a `sha256:`-digest artifact |
| Neural camera runtime | `20260820T203307Z/M1-camera-runtime-latest.json` | live-camera/vision runtime path |
| STT + reasoning (deterministic & Ollama) | `20260820T204022Z/STT-evidence.json`, `REASONING-deterministic.json`, `REASONING-ollama.json` | Whisper-style STT; qwen3.8 via local Ollama; deterministic reasoning |
| Perception → memory | `20260820T205556Z/perception-memory.json`, `STT-cognition-memory.json` | perception detections admitted as memory; speech-cognition wiring |
| Bounded goals (reach/turn) | `20260820T210219Z/GOAL-reach.json`, `GOAL-turn.json` | virtual movement goals reach/turn with bounded steps |
| Memory recall in autonomous loop | `20260820T210457Z/memory-recall.json` | `_recall_context` returns relevant memories to reasoning |
| Durable SQLite storage | `20260820T211900Z/durability.json` | memory records persist across a store reopen |
| Curiosity (novelty → investigate goal) | `20260820T212432Z/curiosity.json` | novel entity spawns a bounded investigate goal |
| Memory consolidation/decay | `20260820T212737Z/consolidation.json` | TTL expiry, confidence decay, archival, supersede |
| Goal scheduling/priority | `20260820T212911Z/scheduling.json` | priority queue + safe supersede of lower-priority goals |
| ARCH-CLOSE-003 (SQLite adoption gate) | `20260820T213139Z/arch-close-003-gate-result.json` | gate decision **ADOPT** (all 6 correctness checks) |
| Soul (identity/personality/affect) | `20260820T214002Z/soul.json` | affect responds to success/failure; durable identity/value |
| Social intelligence & relationships | `20260820T214257Z/social.json` | relationship tiers, relationship-sensitive expression, interaction gate |
| Learned preferences & living lexicon | `20260820T215223Z/lexicon.json` | candidate→adoption lifecycle, privacy scoping, correction supersession |
| Deepened cognition (beliefs/prediction) | `20260820T215417Z/cognition.json` | belief confidence, contradiction non-flip→flip, expectation violation |
| Temporal & causal cognition | `20260820T220655Z/temporal.json` | causal-link learning (verified tiers), expected-after prediction, dilution, durability |
| Multimodal fusion | `20260820T220930Z/fusion.json` | cross-modal confidence boost, provenance retention, conflict handling, stale rejection, determinism |
| Semantic/vector memory | `20260820T221211Z/vector-memory.json` | cosine retrieval, determinism, scale (5k docs, ~0.03s search), lexical-hashing provider + real-model seam |
| Interactive live brain demo | `20260820T222258Z/live-demo.json` `live-neural.json` | `--live` loop (camera+STT+reason+soul+TTS); neural MPS round detected tv/laptop with curious tone |
| Resume goals across restart | `20260820T222630Z/resume-goals.json` | active goal resumed w/ step budget + restored body pose, pursuit continues (no origin reset) |
| Retrieval index / FTS | `20260820T215645Z/retrieval-benchmark.json` | 3× / 9.7× / 18.4× read-latency speedup at 500/2000/5000 records |
| Final integration run | `20260820T215958Z/integration.json` | full pipeline across all subsystems + restart durability |
