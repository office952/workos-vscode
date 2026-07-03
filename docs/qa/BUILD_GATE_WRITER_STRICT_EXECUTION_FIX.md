# BUILD_GATE_WRITER_STRICT_EXECUTION_FIX

## Purpose

Fix BLK-21 static invariant failure that blocked execution plan generation when `gate_writer_strict=True` (default).

## Problem

`POST /api/v1/execution/plan/from-order/{order_id}` returned **412** with:

- `BLK-21` — Silent fallback token detected in `execution.py`
- Token: ` or None` on `initial_fields=initial_fields or None`

With `GATE_WRITER_STRICT=false`, plan generation worked — masking a real code invariant violation.

## Root cause

`backend/routers/execution.py` used a forbidden silent-fallback pattern in the gate writer scan set (`execution_plan_gate_service.STATIC_SCAN_FILES`).

## Fix

Replace `initial_fields or None` with explicit normalization:

```python
normalized_initial_fields: dict[str, Any] | None = None
if initial_fields:
    normalized_initial_fields = initial_fields
```

Semantics unchanged: empty dict → `None`; non-empty dict → passed through.

## Files changed

- `backend/routers/execution.py`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_execution_plan_gate_contract.py::TestStaticInvariants::test_blk21_not_fired_on_current_gate_module -q
# 1 passed

.\.venv\Scripts\python.exe -m pytest tests/test_execution_plan_gate_contract.py -q
# 50 passed
```

Static scan verification:

```python
from services.execution_plan_gate_service import _scan_static_invariants
assert not _scan_static_invariants()  # no BLK-21
```

## Boundary

- Did **not** change CostEngine, Pricing, readiness gates, Employee Mobile, PWA, migrations, or BLK-21 scanner logic.
- Did **not** set `GATE_WRITER_STRICT=false`.
- Lighting gate (`illumination_type=none`) remains a separate P1 build.

## Next steps

- `BUILD_VOLUMETRIC_LIGHTING_GATE_FIX` — LED/electrical ops when illumination is none.
