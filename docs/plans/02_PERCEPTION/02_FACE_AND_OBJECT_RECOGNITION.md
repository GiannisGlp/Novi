# Perception — Face and Object Recognition

## Objective

Give Novi real visual recognition on the Mac body: object detection feeding world state, face detection + identity resolution feeding the existing `PersonIdentity` tier system — closing gap **G4** (identity providers unimplemented) from [`13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md`](../01_BRAIN/13_GAP_AUDIT_IMPLEMENTATION_PLAN_2026-08-23.md) and enabling cross-modal (face + speaker) verified identity.

Recognition runs over frames from [`01_CAMERA_ACQUISITION.md`](01_CAMERA_ACQUISITION.md) and stays behind the brain's capability interfaces (`ObjectDetector` pattern from README M1) — recognition is a provider, never a brain-core change.

## 1. Object detection

### Contract

Existing `ObjectDetector` capability interface remains canonical:

```text
ObjectDetector (capability)
  detect(frame) -> list[Detection]
  Detection: {label, confidence, bbox, frame_ref, timestamp}
```

### Candidate models

| Candidate | Role | Parity |
|---|---|---|
| Torchvision SSDLite320 MobileNetV3 | primary candidate per README M1 | TensorRT-exportable, Jetson-class |
| RT-DETR | accuracy alternative (see `05_RT_DETR.md`) | benchmark-gated |
| YOLO-nano class | latency alternative if SSDLite underperforms live | benchmark-gated |

Selection follows the repo rule: a candidate becomes an official provider only after successful execution on the actual Mac with representative inputs and evidence.

### Integration requirements

1. Detections update world-state entities: label, bbox, first_seen/last_seen, track continuity.
2. Tracking-lite: IoU/centroid association across consecutive frames to keep `last_seen` coherent (no heavy tracker; re-ID deferred).
3. Detection rate decoupled from cognitive rate: detector consumes full-rate frames, world state updates at cognitive sampling.
4. Confidence floor + hysteresis so world state doesn't flicker objects in/out at threshold boundary.
5. Novel-object handling: unseen labels enter as generic "unknown object" entities until named by dialogue (ties into knowledge learning loops).

## 2. Face detection and identity

### Pipeline

```text
frame ─► face detect ─► alignment ─► embedding (ArcFace-class) ─► match vs enrolled
                                                                      │
                                                        match ≥ τ ────┤──── no match ─► new-person proposal
                                                                      ▼
                                                     PersonIdentity tier assignment
```

### Identity tiers (existing system, now fed)

| Tier | Meaning | Trigger |
|---|---|---|
| `unknown` | detected face, not enrolled | first sighting → propose enrollment via dialogue |
| `recognized` | matched enrolled person | embedding distance < τ_match |
| `verified` | cross-modal confirmation | face match + speaker diarization/voiceprint agreement |

Requirements:

1. Enrollment is conversational ("I don't think we've met — what's your name?") — never silent database writes about people.
2. Embeddings stored with provenance (enrollment date, image quality, consent state); privacy states honored per hardware doc §26 (camera privacy off ⇒ no face processing).
3. Ambiguous matches stay ambiguous: below-threshold faces remain `unknown` rather than best-guessing identities.
4. Cross-modal verification: when voice activity and a face co-occur and the speaker embedding agrees, identity escalates to `verified` — this is what makes addressee resolution (G2) trustworthy instead of regex-guessed.

### Privacy boundaries

- Face processing only while camera privacy state permits; audit record per state transition (hardware docs §26).
- Biometric data is local-only storage, exportable/deletable per person on request.
- Recognition confidence and sensor provenance ride along wherever identity enters memory/knowledge records.

## 3. Multi-channel fusion payoff

This module plus voice closes the loop that SCENARIO-V1 needs:

```text
person walks in ─► face detect ─► recognized: "Anna" (tier: recognized)
Anna speaks ─────► diarization + voiceprint ─► same person (tier: verified)
Novi greets Anna by name while continuing navigation track;
owner's chat message arrives mid-exchange ─► turn_taking arbitrates (15_VOICE_CONTINUOUS_DIALOG.md)
```

## Deterministic testing

CI uses synthetic frames with planted faces/objects (deterministic fixtures, no model downloads): detection→world-state entity updates, tracking-lite continuity, tier transitions including ambiguous-match refusal, enrollment conversation flow, privacy-state gating, provenance chains. Real-model evidence runs happen on-Mac against real people/lighting.

## Evidence gates

- Live detection run: common household objects ≥ 10 FPS sustained on Mac, world-state entities updating with correct last_seen decay.
- Identity run: 3 enrolled persons, tier transitions exercised live including one deliberate ambiguity (stays unknown).
- Cross-modal: face+voice co-presence escalates to `verified` in a recorded session.
- Regression wall green with fakes; hardware absent ⇒ deterministic fallbacks.

## Resource parity

SSDLite/ArcFace-class/Silero-diarization all have Orin/Thor-plausible TensorRT/onnx deployments; embeddings are small (≤ 512-d), storage bounded. No cloud vision APIs anywhere.

## Status

**PLANNED / DOC PHASE.** Sequencing: object detection live → tracking-lite + world-state entities → face pipeline → enrollment dialogue → cross-modal verification.
