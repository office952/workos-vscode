# 2026-07-17 — W7-T02 Post-Job reconciliation breadth V1

## Owner decision

`OPTION A — BREADTH ON POSTJOBTRUTH = APPROVED`

## Objective

Prove Post-Job reconciliation across completed / partial / variance; expose `operations[]` in RO UI; freeze upstream truth; no labor $ / forced stock / parallel engine.

## Repository gate

- HEAD at start: `e5ac823`
- Branch: `feature/product-system-active-path-isolation-v1`
- Runtime: frontend `:3000`, backend `:8001`

## Research

PostJobTruth already owned plan-vs-actual. Gaps: operations not rendered; no summary counts; missing actuals could pair with value `0` before honesty fix; thin multi-task tests.

## Decision

Extend `post_job_truth` schema/service + `PostJobTruthPanel` only. Build 1 order `92402` = Scenarios A+B (read-only). New disposable `92403` = Scenario C (75 min variance).

## Implementation

- Schema: `reconciliation_state`, quantity presence fields (`not_captured`), `ReconciliationSummary`
- Service: honesty for missing actuals; classify matched/partial/missing_actual/variance
- UI: **Plan vs execuție** table + summary chips (RO)
- Tests: multi-task partial / variance / matched + panel tests

## Scenario IDs

| Scenario | IR | Order | Plan | Result |
|----------|----|-------|------|--------|
| A completed/match | IR-BUILD1-1784237119 | `92402` | `8` | matched=1 |
| B partial/missing | (same RO) | `92402` | `8` | missing_actual=17 |
| C minute variance | IR-W7T02-1784238040 | `92403` | `9` | variance=1 (0→75 min) |

## Freeze

Order `92403` commercial total unchanged after sessions. Build 1 not mutated.

## Evidence

`docs/qa/w7-t02-reconciliation-2026-07-17/`

## Remaining limitations (TE2E-028 still open)

- Planning-minute **source** often 0 (mechanics work; source incomplete)
- Stock G3 not forced
- Labor $ excluded
- Deterministic fixture origin
- Not all templates

## Next

W7-T03 owner sign-off — not started.
