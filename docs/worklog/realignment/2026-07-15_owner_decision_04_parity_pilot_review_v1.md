# OWNER-DECISION-04 — Parity pilot owner review v1

**Date:** 2026-07-15  
**Task:** OWNER-DECISION-04-PARITY-PILOT-OWNER-REVIEW-V1  
**Starting HEAD:** `0b5997f`  
**Verdict:** `OWNER_PARITY_PILOT_APPROVED_REMAIN_TWO_CONSUMERS` (recommended; pending explicit owner confirmation)  
**Next:** `APP-AUTH-06C-PARITY-SIGNAL-INTERPRETATION-PLAN`

## Scope

Decision and documentation gate only. No code, DB, endpoints, UI, persistence, enforcement, third-consumer wiring, or production flags.

## Gate 1 — Normalized consumer inventory

**Classification:** `REPORTING_AMBIGUITY_CORRECTED`

| Bucket | Count |
|--------|-------|
| Primary universe (APP-AUTH-03 `consumers[]`) | 18 |
| Request consumers | 17 |
| Helpers | 1 (`CONS-SANDU-REPORT`) |
| Connected | 2 |
| Unconnected candidates | 9 |
| Excluded within universe | 6 |
| Outside universe (CONS-MODULES-PAGE) | 1 |

**Equation:** `18 = 2 + 9 + 6 + 1`

**Corrections:**
- `CONS-MODULES-PAGE` is **not** in the 18; it lives in `excluded_consumers[]`.
- `CONS-SANDU-REPORT` is a **helper**, not a request consumer.
- The six excluded surfaces must **not** be counted as “remaining candidates.”
- The prior **14** and misleading **16 remaining** figures are reporting ambiguity, not inventory duplication.

## Gate 2 — Performance claim correction

**Classification:** `NON_COMPARABLE_ENVIRONMENTS`

- **Safe:** No regression detected that blocks observe-only continuation.
- **Not proven:** “Parity improved latency 78.21%” — compared `:8001` flags-off vs `:8011` flags-on in different processes.
- Repeat performance pilot **not required** for this owner decision.

## Owner decisions (recommended)

| ID | Recommendation | Summary |
|----|----------------|---------|
| P1 | **A** | Signal useful for observe-only continuation |
| P2 | **A** | Duplicate volume acceptable ephemeral |
| P3 | Refined | ACTIONABLE → CONFIRMATION_REQUIRED / POLICY_DECISION |
| P4 | **A** | Sandu remains read-only observe |
| P5 | **A** | Freeze at two request consumers |
| P6 | **DEFER** | Catalog consumer needs separate audit |
| P7 | **A** | No persistence |
| P8 | **A** | No manager projection |
| P9 | **CONFIRM** | Production flags remain false |
| P10 | **A** | Next: signal interpretation plan (06C) |

**Explicit owner confirmation:** not yet recorded in this commit.

## Signal interpretation summary

- **16** unique fingerprints; **11** unique actionable/policy patterns.
- **420** raw events; **404** duplicates from 20× HTTP repetition.
- **180** raw “actionable” labels ≠ 180 independent problems — mostly Sandu (employee 4) across 5 operations × 3 domains.
- Dominant drift: registry/legacy competence conflict + explicit mapping without registry competence.

## Third consumer audit (`CONS-REGISTRY-CATALOG-API`)

Deferred. Catalog route risks **self-comparison** or restating registry data already consumed indirectly. No CONNECT_NEXT authorization from this gate.

## Blocked

Persistence · enforcement · source switch · migration · third-consumer wiring · manager UI · production pilot.

## Evidence

`docs/qa/product-system-active-path-isolation-v1/owner_decision_04/*.json`

## Honest opinion

The pilot succeeded technically. The next mistake would be treating that success as automatic permission to add consumers or persist observations. Freeze at two request consumers, interpret the 11 unique actionable patterns with the owner, then decide whether a catalog audit is worth a plan-only APP-AUTH-07.
