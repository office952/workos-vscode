# BUILD — Volumetric Owner Task Decisions

## Purpose

Close three owner decisions for `TPL-VOLUMETRIC-LETTERS` execution plan task generation.

## Owner decisions (closed)

| Task | Decision |
|------|----------|
| `back_cut` | **ALWAYS_REQUIRED** — no volumetric variant without Forex back on this template |
| `packaging_letters` | **CONDITIONAL_REQUIRED** — omit when direct on-site mounting; include otherwise (default) |
| `qc_letters` | **ALWAYS_REQUIRED** internal check — display title `Verificare finală lucrare` (no `QC` jargon) |

## Packaging rule

Omit `packaging_letters` when snapshot/spec signals direct mounting:

- `delivery_type == delivery_install`
- `installation_mode` / `mounting_mode` in direct-mount set
- boolean flags: `requires_installation`, `field_installation`, `is_direct_mount`, etc.

Default: include packaging when no direct-mount signal (backward compatible).

## Files changed

- `backend/services/volumetric_conditional_plan_tasks_service.py`
- `backend/services/volumetric_execution_dispatch.py`
- `backend/tests/test_volumetric_conditional_plan_tasks.py`
- `backend/tests/test_volumetric_execution_dispatch.py`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_conditional_plan_tasks.py tests/test_volumetric_face_vinyl_task.py tests/test_volumetric_order_execution_snapshot.py tests/test_execution_plan_gate_contract.py tests/test_employee_mobile_tasks.py -q
```

## Boundary

- No CostEngine / pricing / migrations / existing plan or reality mutation
- Applies only to **new** plan generation via `POST .../plan/from-order/{order_id}`

## Next steps

- Wire `delivery_type` from intake → order snapshot when handoff path is standardized (packaging helper already reads it when present)
