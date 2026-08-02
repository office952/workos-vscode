# 2026-08-03 — F7C Operational Resource Readiness (read-only)

## Status

```text
INTERNAL GATE = GO (Lead)
F7C = PASS_WITH_WARNINGS
DB WRITES = ZERO
GATE FINAL STATE = CLOSED (unchanged)
PUSH = NOT EXECUTED
```

## Identity

`C:\w\psiso` · `feat/capacity-batch-20d-scoped-b-92401` · HEAD near `c12ed226`.

## What was built

One canonical read-only surface: `OperationalTask -> WorkcenterRequirement -> ResourceRequirementMode -> CompatibleMachineCandidates -> ResourceReadinessResult`, composed from existing ORR (`operation_resource_requirements`) ∩ `machines` registry ∩ `data/operational_workcenters.py`. No new registry, no formal `machine_required|optional` enum invented — `resource_requirement_mode` is derived from truth only.

- New: `backend/schemas/operational_resource_readiness.py`, `backend/services/operational_resource_readiness_service.py`, `backend/tests/test_operational_resource_readiness.py` (14 tests).
- Extended (no duplicate namespace): `backend/routers/execution_plan_v2.py` — `GET /api/v1/execution/plan-v2/from-order/{order_id}/resource-readiness`.
- Frontend: `ResourceReadinessPanel.tsx` + `resourceReadinessDisplay.ts` (+ test), wired into `ExecutionDetail.tsx` after `BlockersPanel`, before `WorkPanel`. Read-only table, no Assign/Schedule/Start controls.

## Readiness matrix — 880811 / plan 22

5/5 tasks resolved (`face_cnc_cut`, `side_forming`, `return_face_bonding` → `ready_with_warnings`; `painting`, `packaging_letters` → `workcenter_only`). 0 blocked. All 5 carry `PLANNING_MINUTES_SOURCE_MISSING` (capacity warning, not a commercial blocker). Cross-checked against the 18-task protected fixture 973019/21 — same shape, no crash.

## Proof

- Snapshot SHA-256 + `execution_plan.updated_at` for 880811 and 973019 identical before/after the GET (zero writes).
- `evaluate_materialize_authorization` → `pilot_gate_open=False` before and after (gate untouched).
- Screenshot: `docs/qa/workos-f7c-operational-resource-readiness-v1/screenshots/f7c-01-execution-880811-resource-readiness-panel.png`.
- Backend: 14/14 new tests pass; 144/145 regression subset pass (1 pre-existing unrelated failure, confirmed red before this change too).
- Frontend: lint clean, build green, new logic tests pass; pre-existing `MaterializedOpsGraph.test.tsx` failures confirmed unrelated (red on clean stash).

## Note

Frontend dev server (`:3000`) had dropped mid-session; restarted via `scripts/dev-detached.ps1` (backend `:8000` was untouched, no port killed) per the live-stack rule.

## Remaining Owner decisions

No formal `machine_required|optional|workcenter_only` enum in the registry (derivation only). DEC-006 planning minutes still open. `maintenance_conflict` and `machine_optional_no_candidate` are schema-complete but currently unreachable with today's registry truth — documented, not silently collapsed into another status.

Full detail: `docs/qa/workos-f7c-operational-resource-readiness-v1/WORKOS_F7C_OPERATIONAL_RESOURCE_READINESS_V1_REPORT.md`.
