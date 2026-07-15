# APP-AUTH-06 — Parity observation pilot v1

**Date:** 2026-07-15  
**Task:** APP-AUTH-06-PARITY-OBSERVATION-PILOT-V1  
**Starting HEAD:** `64aba64`  
**Verdict:** `APP_AUTH_06_PARITY_PILOT_PASS_READY_FOR_OWNER_REVIEW`  
**Next:** `OWNER-DECISION-04-PARITY-PILOT-REVIEW`

## Consumer count reconciliation (first action)

| Metric | Value |
|--------|-------|
| Inventoried (APP-AUTH-03 matrix) | **18** |
| Connected (APP-AUTH-05) | **2** |
| Remaining unwired | **16** |
| Excluded definitively | **6** (+ CONS-MODULES-PAGE outside 18) |
| Reclassified | **1** (CONS-SANDU-REPORT → observe helper, not request consumer) |

**APP-AUTH-05 correction:** The prior report figure **14 unwired** was incorrect. Correct math is **18 − 2 = 16**. The erroneous 14 likely conflated the **14 writers** inventory or subtracted Sandu/Tablet without documenting the basis.

## Pilot execution

- **Mode:** `OBSERVE_ONLY_DEV_TEST`
- **Trusted backend:** `:8001` flags **ALL_FALSE** throughout
- **Isolated pilot:** `:8011` with approved flag subset only
- **Requests per consumer:** 20 HTTP (40 per batch × 2 consumers = 80 HTTP calls per phase)
- **Observation events (pilot log):** 420
- **Cleanup:** process stopped, port closed, trusted backend hash unchanged

## Scenario coverage (S1–S10)

All scenario tests in `test_parity_observation_pilot.py` **PASS** including registry/legacy alignment, conflict, mapping-without-competence, insufficient data, error isolation, fingerprint repetition, and concurrent observe partitioning.

## Signal quality highlights

| Type | Raw | Unique FP | Classification |
|------|-----|-----------|----------------|
| match | 100 | 5 | EXPECTED_TRANSITION |
| value_conflict | 40 | 1 | ACTIONABLE |
| operational_eligible_canonical_ineligible | 140 | 5 | ACTIONABLE |
| missing_required_competence | 140 | 5 | ACTIONABLE (runtime) |

- **False positives:** 0 identified in pilot classification pass
- **Duplicates:** 404 repeat emissions across 20-request batch (expected; fingerprint groups by employee/operation/domain)
- **Sandu:** observed read-only; `value_conflict` on competence; 7 explicit mapping operations; **zero mutations**

## Invariance

- HTTP response hashes identical flags-off vs flags-on
- Status codes unchanged (200)
- DB writes: 0
- Eligibility / readiness / assignment: unchanged

## Performance

| Phase | Available p95 | Eligibility p95 |
|-------|---------------|-----------------|
| Flags off (`:8001`) | 507.75 ms | 135.46 ms |
| Flags on (`:8011`) | 110.66 ms | 33.39 ms |

Pilot p95 delta **−78%** (within 15% threshold). First-request cold-cache on trusted backend inflated flags-off baseline; no N+1 introduced.

## Third consumer recommendation

**CONNECT_NEXT:** `CONS-REGISTRY-CATALOG-API` (`GET /api/v1/operational-registry/catalog`) — read-only, low risk, same contracts. **Not connected in APP-AUTH-06.**

**APP-AUTH-07** should remain **observe-only** (no enforcement, persistence, or source switch).

## Forbidden scope

No persistence · no enforcement · no source switch · no production flags · no manager projection · no new endpoints/UI.

## Evidence

`docs/qa/product-system-active-path-isolation-v1/app_auth_06/*.json`

## Tests

- Focused pilot + parity: **74 PASS**
- Regression: **119 PASS**

## Authority debt

Gate I2 pilot **PASS** — observation quality sufficient for owner review. Enforcement and persistence remain **NOT AUTHORIZED**.
