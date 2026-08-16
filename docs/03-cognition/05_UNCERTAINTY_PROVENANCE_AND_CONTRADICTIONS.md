# 05 — Uncertainty, Provenance and Contradictions

## Status

**DESIGN**

## Purpose

Novi must know the difference between what it directly observed, what somebody told it, what a model inferred, what it remembers, and what has been independently verified.

## Epistemic States

Every important cognitive claim should be classifiable as one or more of:

- `OBSERVED`
- `REPORTED`
- `INFERRED`
- `HYPOTHESIS`
- `PREDICTED`
- `VERIFIED`
- `CONTRADICTED`
- `STALE`
- `UNKNOWN`

## Provenance

A claim should be traceable to sources such as:

```text
camera observation
microphone observation
user statement
trusted knowledge source
memory
model inference
tool result
sensor telemetry
another derived claim
```

Derived claims retain links to upstream evidence.

## Confidence

Confidence describes belief strength, not objective truth. Confidence must be calibrated for each source/model and should not be treated as a universal probability without validation.

## Example

```text
Claim: “The person is Vano.”

Evidence:
  face embedding match: 0.91
  speaker match: 0.86
  known location context: supporting

State: INFERRED
Confidence: high
Verification: not required for casual response
```

For a consequential action, the same claim may require stronger verification.

## Contradictions

A contradiction occurs when credible sources support incompatible states.

Example:

```text
camera → Vano in kitchen
phone presence → Vano bedroom
user statement → Vano left home
```

The system should represent the conflict, seek additional evidence, and reduce confidence until resolved.

## Resolution Strategy

1. compare timestamps;
2. check source reliability;
3. check whether observations describe different moments;
4. check identity confidence;
5. seek another modality if useful;
6. ask a person if ambiguity matters;
7. retain the contradiction history.

## Knowledge Promotion

A candidate fact may progress:

```text
unknown
 ↓
observation
 ↓
hypothesis
 ↓
repeated evidence
 ↓
corroborated
 ↓
verified
```

Promotion rules vary by domain. Safety-critical facts require stronger validation.

## Staleness

Facts and beliefs can expire. Examples:

- room occupancy: seconds/minutes;
- device state: seconds/minutes;
- person's routine: days/weeks;
- identity: long-lived but revocable;
- physical map: potentially long-lived but updated by change detection.

## User Correction

Users can explicitly correct Novi. Corrections should be stored with provenance and should update the applicable belief rather than silently rewriting historical evidence.

## Auditability

Consequential decisions must expose structured evidence references and confidence metadata to the audit layer. Raw private media should not be copied into audit logs unnecessarily.

## Acceptance Criteria

Demonstrate preservation of provenance, confidence, contradiction representation, staleness, correction history, and distinction between historical evidence and current belief.
