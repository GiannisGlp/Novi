# 45 — ARCH-CLOSE-007 Resource & Storage Policy

**Status:** BASELINE / MEASUREMENT PENDING  
**Priority:** P0  
**Authority:** System Architecture  
**Closure item:** ARCH-CLOSE-007 — Resource budgets

## 1. Purpose

Define the resource accounting rule for Novi before hardware is selected. The purpose is to prevent nominal hardware capacity from being mistaken for usable production capacity.

## 2. Existing Stage-1 budgets

The current provisional baseline defines:

| Resource | Target | Minimum acceptable | Degraded threshold |
|---|---:|---:|---:|
| CPU sustained | <=70% | <=80% | >80% |
| GPU sustained | <=75% | <=85% | >85% |
| Unified RAM working set | <=12 GB | <=13 GB | >13 GB |
| Model/inference allocation | <=10 GB | <=12 GB | >12 GB |
| Active runtime storage | <=200 GB | <=300 GB | >300 GB |
| Compute power | 25 W | 40 W test envelope | throttling |
| SoC temperature | <80 C | <90 C | >=90 C |

These are targets, not achieved measurements. Hardware validation remains pending. fileciteturn386file0

## 3. Mandatory SSD / storage reserve rule

For Novi's planning calculations, **usable storage requirement is doubled for backup/recovery capacity**.

Formula:

```text
primary_required_storage = measured_or_estimated_active_storage
backup_reserve = primary_required_storage
minimum_planned_capacity = 2 × primary_required_storage
```

Example:

```text
active requirement = 2 GB
backup reserve     = 2 GB
planned minimum    = 4 GB
```

This is a **minimum planning rule**, not a claim that the entire disk must remain permanently empty or that a backup must always consume an identical second physical partition. The implementation may use snapshots, a second logical dataset, an external backup target, or another validated mechanism, but capacity planning must reserve equivalent backup headroom.

## 4. Practical capacity selection

The 2× rule is applied before selecting a commercially available SSD size.

```text
measured need
    ↓
2× backup/recovery reserve
    ↓
capacity ceiling / growth allowance
    ↓
choose next practical SSD tier
```

Example:

```text
2 GB measured
→ 4 GB minimum planning capacity
→ select a practical larger device because 4 GB is not an appropriate robot SSD tier
```

For Novi, the current architecture baseline recommends **1 TB NVMe** because logs, datasets, model artifacts, caches, recovery space and future sensor recordings make a tiny capacity calculation misleading. The 1 TB recommendation is therefore a practical platform recommendation, not merely the result of multiplying today's measured database by two. fileciteturn386file0

## 5. What counts toward primary storage

Capacity calculations must include, where applicable:

- durable event/state database;
- memory stores;
- model files;
- model caches;
- application binaries;
- logs and audit records;
- configuration;
- telemetry;
- sensor recordings retained locally;
- map/localization data;
- simulation/replay datasets;
- temporary working data that can prevent safe operation if the disk fills;
- filesystem/database overhead.

## 6. Backup policy

The backup reserve must support recovery from at least the failure classes defined by the storage architecture. A backup is not useful if it shares the same failure mode without protection.

Therefore later implementation must define:

- what is backed up;
- backup frequency;
- retention count;
- integrity verification;
- restore procedure;
- where the backup resides;
- behavior when backup capacity is exhausted;
- whether an external/offline backup is required.

## 7. Storage-full safety

Storage exhaustion is a resource-safety condition.

Novi must not respond to a full disk by allowing unbounded queue/log growth. The system must have bounded retention, controlled log rotation, explicit telemetry degradation and safe behavior for state that cannot be durably committed.

## 8. Relation to ARCH-CLOSE-003

ARCH-CLOSE-003 determines whether SQLite is sufficient for Stage 1. Its measured database footprint becomes an input to this policy, but the storage backend decision and robot SSD capacity decision remain separate.

The existing SQLite benchmark demonstrated approximately 0.75 MiB for 10,000 benchmark events, but that number is not a production capacity forecast. Production capacity must be calculated from expected event rates, retention, models, logs, sensor data and recovery requirements.

## 9. Relation to robot hardware

Final SSD selection is deferred until:

1. Novi's Mac workload is characterized;
2. expected retention and sensor-recording policy are defined;
3. AGX Orin 64 GB vs Thor is selected or narrowed;
4. physical SSD interface, power and thermal constraints are known;
5. long-duration growth is measured.

## 10. Closure gate

ARCH-CLOSE-007 cannot close from this document alone. Closure requires the existing acceptance sequence: unit benchmark, pipeline benchmark, sensor-to-action benchmark, full concurrent load, constrained/degraded load, fault injection and long-duration soak, with resource telemetry and power/thermal evidence. fileciteturn386file0

## 11. Architectural invariant

> **Novi never treats nominal storage capacity as usable capacity; required primary storage is always planned with an equivalent backup/recovery reserve before hardware selection.**
