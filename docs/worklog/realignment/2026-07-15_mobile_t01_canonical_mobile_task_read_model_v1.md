# MOBILE-T01 — Canonical Mobile Task Read Model v1

**Date:** 2026-07-15  
**Starting HEAD:** `5010e4e`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Trusted backend:** `http://127.0.0.1:8001`  
**Frontend:** `http://127.0.0.1:3000`

## Objective

Implement `employee_mobile_task_truth/v1` so Employee Mobile reads V2 `operational_tasks[]` envelopes via the shared execution-plan parser, exposes frozen identity/readiness/release fields, and stops returning empty lists on frozen-spine order `23099`.

## Root cause

`employee_mobile_tasks_service._parse_json` accepted only legacy list-shaped `tasks_json`. Canonical V2 plans store `{ operational_tasks: [...] }`, so mobile loaders iterated zero plan tasks.

## Parser strategy

`WRAP_EXISTING_CANONICAL_PARSER` — `resolve_operational_plan_tasks()` wraps `execution_plan_task_parser.parse_tasks_json_raw` (same authority as `operator_task_truth_service` and `task_start_gate_service`).

## Contract

- Version: `employee_mobile_task_truth/v1`
- Endpoint: `GET /api/v1/employee-mobile/tasks/truth`
- Existing `/tasks` and `/tasks/available` remain projections with extended fields (`contract_version`, frozen identity, production blocker summary, assignment flags).

## V2 fail-closed

Structured 422 errors for canonical V2 orders with corrupt/missing envelopes (`MOBILE_V2_TASK_ENVELOPE_CORRUPT`, `MOBILE_V2_TASK_ENVELOPE_MISSING`, `MOBILE_V2_TASK_CONTRACT_UNSUPPORTED`). No silent `[]` fallback from V2 to legacy.

## Legacy policy

`LEGACY_MOBILE_TASK_ADAPTER` — legacy list plans set `legacy_mode=true` explicitly; V2 envelope never falls back to list parsing.

## Entry-gate test reclassification

| Test | Classification |
|------|----------------|
| `test_start_assigned_task` | `FIXED_BY_CANONICAL_ADAPTER` (added `_seed_active_order` + print eligibility) |
| `test_employee_mobile_start_flow_still_works` | `FIXED_BY_CANONICAL_ADAPTER` (session fixture seeds active order + eligibility) |

## Tests

| Suite | Passed | Failed |
|-------|--------|--------|
| `test_employee_mobile_task_truth.py` | 10 | 0 |
| `test_employee_mobile_tasks.py` + parser consumers + operator truth (focused) | 63 | 0 |
| Frontend `employeeMobileTaskSummary.test.ts` | 10 | 0 |

## Runtime (order 23099, employee Sandu id=4)

- Plan operational tasks: **13** (`v2_envelope`)
- Assigned API after gate assignment: **5** (includes prior in-progress sessions)
- Available API: **7**
- Truth contract: `employee_mobile_task_truth/v1`
- Root identity: `frozen_task_identity/v1`, `component_role=root_product`
- Production release: blocked (owner decisions — desktop resolution only)
- Plan mutation: assignment only for gate proof (`plan_assignment_only`)
- Snapshot mutation: **NO**

Evidence: `docs/qa/product-system-active-path-isolation-v1/mobile_t01_gate_evidence.json`

## UI evidence

Runtime API proof confirms non-empty V2 task payloads. Browser screenshot capture deferred — frontend dev server not reachable at gate time (`chrome-error://chromewebdata/`). MOBILE-T02 owns list/detail UX polish.

## Temporary debt (classified)

| Item | Classification |
|------|----------------|
| Assigned/available list UX | `KEEP_FOR_MOBILE_T02` |
| Task detail UX | `KEEP_FOR_MOBILE_T02` |
| Blocker visibility polish | `KEEP_FOR_MOBILE_T03` |
| Start action wiring | `KEEP_FOR_MOBILE_T04` |
| Complete/pause UX | `KEEP_FOR_MOBILE_T05` |
| Mobile shell v1 duplication | `LEGACY_ISOLATED` |
| Offline/notifications/camera | `MOBILE_FUTURE_ENHANCEMENT` |

## Verdict

`MOBILE_TASK_READ_MODEL_PASS_COMMITTED`

## Next allowed task

`MOBILE-T02-ASSIGNED-AVAILABLE-TASK-LIST-AND-DETAIL`
