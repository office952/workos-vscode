# W6-T02 — Task identity and component presentation

**Date:** 2026-07-15  
**Task:** W6-T02 `OPERATOR_TASK_IDENTITY_AND_COMPONENT_PRESENTATION_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `b08fdb3`  
**Application baseline:** `3485917`  
**Verdict:** `W6_TASK_IDENTITY_UI_PASS_COMMITTED`

## Summary

Wired desktop operator surfaces to canonical `operator_task_truth/v1` with `FLAT_LIST_WITH_COMPONENT_BADGES` presentation. Raw deterministic keys demoted to diagnostic `<details>` only. Start/readiness authority remains backend-owned.

## Canonical frontend source

`GET /api/v1/operator/orders/{order_id}/task-truth` via `useOperatorTaskTruth()` — single fetch per surface parent, props to children.

| Surface | Fetch owner | Consumer |
|---------|-------------|----------|
| `/execution/:order_id` | `ExecutionDetail.load()` | `RealityCapturePanel` |
| `/operator` | `OperatorView` (`blueprintTruthOrderId`) | Blueprint panel, assignment, current/next/timeline |
| `OperatorProductionBlueprintPanel` | Receives `taskTruthByTaskId` prop | Task list rows |

## Presentation

- Primary: `identity.display_label`
- Component: `identity.component_label` (backend preferred) + role badge
- Readiness/startability: `runtime.is_startable`, `readiness_reasons`
- Diagnostic: deterministic key, graph node, rule, contract source

## Runtime (`:8001`, read-only)

Order `23099` — 13 tasks; root `Vector Prep` + `Produs principal`; mounting `Panou montaj` + `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`; logo `Logo segment (logo_instance_001)`.  
Evidence: `docs/qa/product-system-active-path-isolation-v1/w6_t02_runtime_gate_evidence.json`

## Screenshots (6)

| # | File | Section |
|---|------|---------|
| 1 | `w6_t02_01_execution_task_list.png` | ExecutionDetail task table |
| 2 | `w6_t02_02_execution_mounting_task.png` | Mounting + logo rows |
| 3 | `w6_t02_03_execution_logo_task.png` | Logo segment detail |
| 4 | `w6_t02_04_operator_blueprint_mounting.png` | Operator blueprint mounting |
| 5 | `w6_t02_05_operator_next_tasks.png` | OperatorView next tasks |
| 6 | (blocked) | Face CNC Cut readiness in execution list |

## Tests

| Category | Passed | Failed | Skipped |
|----------|--------|--------|---------|
| Backend `test_operator_task_truth.py` | 13 | 0 | 0 |
| Backend W5 production guard | 19 | 0 | 0 |
| Frontend presentation + contract | 22 | 0 | 0 |

## Endpoint classification (post W6-T02)

| Endpoint | Classification |
|----------|----------------|
| `task-truth` | **CANONICAL_TASK_TRUTH** |
| `production-blueprint` | **KEEP_AS_ADAPTER** (materials, workers, procurement) |
| `/operator/tasks` | **TEMPORARY_ADAPTER** (list/actions; identity from truth when order loaded) |
| execution plan | **LEGACY_ISOLATED** (plan minutes/process; not identity authority) |
| ShopFloor | **KEEP_FOR_LATER_W6** |
| owner-decision resolution UI | **KEEP_FOR_W6_T03** |
| Employee Mobile | **MOBILE_DEFERRED** |

## Next task

**W6-T03-PRODUCTION-BLOCKER-VISIBILITY**

## Debt

- Logo hierarchy still partial (`PARTIAL_IDENTITY_NONBLOCKING`)
- Premount/volum not in gate fixture order (fixture tests only)
- Blueprint panel still fetches blueprint for non-identity fields
- Manager resolution UI deferred
