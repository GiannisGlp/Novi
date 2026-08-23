# 08 — Gap Analysis: Soul

## Docs: 06-soul (00-08)
Constitution; identity & self-model (capability states AVAILABLE/DEGRADED/UNAVAILABLE/
RESTRICTED/UNCERTAIN/UNKNOWN); personality/values/motivations; social intelligence
(group/multi-person, addressee, turn-taking, restraint, silence); relationships
(multi-dimension, evidence-backed, categories not immutable truth); affect/internal
life; learning/adaptation (candidate lifecycle); communication & living lexicon
(global vs relationship/context/ephemeral scope); behavioral acceptance (scenarios,
acceptance classes P0-P3, release gates, DoD). No-assistant-persona / natural speech.
Honesty is non-negotiable. Soul never directly chooses physical actions or bypasses
governance.

## Exists today
- identity + personality/values/affect (soul.py), relationships + social initiative
  (social.py), living lexicon (lexicon.py), natural dialogue engine (dialogue.py),
  first-person self-model + capability honesty (self_model.py). Closest to complete.

## Delta (what's missing)
- **Behavioral acceptance suite (08)**: scenario format, acceptance classes, adversarial
  + longitudinal evaluation, release gates, DoD are specified but not executable.
- **Communication modes + lexicon scope artifacts (07)**: schemas/workflows for
  global vs relationship-scoped vocabulary, pronunciation, preference — not fully built.
- **Candidate-adoption / correction workflows (06)**: learned preferences go through
  evidence -> validation -> scoped adoption; partly in lexicon but not a formal contract.
- **Multi-person group handling** (addressee discrimination, turn-taking, restrained
  interruption) is thinner than the docs require.
- **Affect -> communication mapping** and affect-is-not-memory boundaries are light.
- **Social-fatigue/cooldown** and "prefer silence" budget not fully enforced.

## Next action (roadmap Step 4)
- Turn the dialogue/social layer into contract-compliant, scenario-accepted behavior:
  implement the (08) acceptance harness with the P0 gates (zero constitutional/privacy/
  escalation/identity/safety violations), and the (07) vocabulary-scope model.

