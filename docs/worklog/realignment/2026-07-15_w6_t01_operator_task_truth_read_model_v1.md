# W6-T01 — Operator task truth read model

**Date:** 2026-07-15  
**Task:** W6-T01 `OPERATOR_TASK_TRUTH_READ_MODEL_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `71fe531`  
**Verdict:** `W6_OPERATOR_READ_MODEL_PASS_COMMITTED`

## Summary

Implemented canonical backend read model `operator_task_truth/v1` at  
`GET /api/v1/operator/orders/{order_id}/task-truth`.

Composes frozen task identity, operational readiness, production-release evaluation, and owner-decision summary in one role-safe response. No Wave 6 UI rendering in this task.

## Endpoint strategy

| Endpoint | Role after W6-T01 |
|----------|-------------------|
| `GET .../task-truth` | **Canonical** operator execution truth |
| `GET .../production-blueprint` | `KEEP_AS_ADAPTER` (projection; migrate UI in W6-T02) |
| `GET /operator/tasks` | `KEEP_AS_ADAPTER` (list enrichment only) |
| `GET .../production-release-status` | `KEEP_AS_ADAPTER` (now composed into task-truth) |
| `GET /execution/plan/{id}` | Admin plan authority (frozen_identity source) |

## ShopFloor boundary

**`REDUCED_PROJECTION_FROM_CANONICAL_MODEL`** — ShopFloor remains machine-centric; may consume reduced task-truth projection in W6-T02 alignment.

## Tests

| Suite | Passed | Failed |
|-------|--------|--------|
| `test_operator_task_truth.py` | 13 | 0 |
| W5 regressions (identity + guard + int02) | 42 | 0 |
| Frontend `operatorTaskTruth.test.ts` | 2 | 0 |
| Frontend `OperatorView.badges.test.tsx` | 6 | 0 |

## Runtime (`:8001`)

Order `23099` — 13 tasks, `operator_task_truth/v1`, root/mounting/logo identities, `RELEASE_ALLOWED`.  
Evidence: `docs/qa/product-system-active-path-isolation-v1/w6_t01_runtime_gate_evidence.json`

## Next task

**`W6-T02-TASK-IDENTITY-AND-COMPONENT-PRESENTATION`** — wire desktop UI to canonical read model; replace raw task keys.

## Debt

- Production blueprint still separate (`KEEP_AS_ADAPTER`)
- Manager resolution UI absent (`KEEP_FOR_LATER_W6`)
- ShopFloor alignment (`KEEP_FOR_LATER_W6`)
- Employee Mobile deferred (`MOBILE_DEFERRED`)
