# 02 — What Is Already Implemented

Evidence-based map (code audit): active code = brain/ (21 src), MAC_BRAIN/ (~30 src),
contracts/ (registry + 16 JSON Schemas), web/ (server+UI). ~477 pytest tests + script
validators across brain/MAC_BRAIN/web/contracts.

## Brain (docs/02-novi-brain)
- B0: BrainSupervisor lifecycle (brain/runtime.py), typed events, mock-body loop, gating.
- B1: closed simulated cognitive loop (brain/b1_loop.py) — world model, cognition,
  memory, autonomy, execution, outcome/replay (b1_world, b1_cognition, b1_memory,
  b1_autonomy, b1_execution, b1_outcomes).
- B2: model runtime + contracts (brain/b2_model_runtime.py), Nemotron/Cosmos adapters,
  perception, real-inference policy, specialist adapters, evaluation harnesses.
- Health/observability (brain/observability.py, MAC_BRAIN/observability.py).

## Cognition (docs/03-cognition)
- Belief + prediction (MAC_BRAIN/cognition.py), situation understanding grounded in
  knowledge graph (cognition2.py), temporal/causal (temporal.py), multimodal fusion
  (fusion.py), reflection/self-correction, identity tiers (identity.py), entity KG
  (kgraph.py, incl. place/building/room typing).

## Memory & Knowledge (docs/04-memory-and-knowledge)
- Durable SQLite store (storage.py), consolidation/decay/archival (consolidation.py),
  vector recall (vector.py), privacy/data-governance (privacy.py), narrative + summary
  (summarizer/narrator/conversation_summarizer).

## Autonomy (docs/02-autonomy)
- Bounded goal to plan to action-proposal slice (MAC_BRAIN/autonomy.py, planner.py,
  brain/b1_autonomy.py), social initiative (social.py), continuous loop in runtime.py.

## Soul (docs/06-soul)
- Identity/values/affect (soul.py), relationships (social.py), learned lexicon
  (lexicon.py), natural dialogue engine (dialogue.py), first-person self-model
  (self_model.py), social initiative.

## Contracts (docs/01-16/17)
- Canonical registry + versioned JSON Schemas (contracts/): event-envelope, entity,
  evidence, observation, relationship, world-state-change, model-invocation, goal,
  plan, action-proposal, action-execution/outcome, memory-record, knowledge-record,
  safety/authorization, deployment manifest, hardware-health. Validators + compat tests.

## Web
- stdlib server + browser chat/dashboard (web/server.py, static/index.html). The server
  is a thin caller of the brain (compose_reply, self_model) — logic stays in MAC_BRAIN.

## NVIDIA / integration
- Portability seams only: ObjectDetector protocol, embedding provider, neural_backend
  bridge, recognition.py (voice/face provider boundaries + deterministic stubs).
  No Jetson/CUDA/TensorRT/ROS2/Isaac code yet (correct for brain phase; see 09).

