# 2026-07-09 - return cant runtime pricing backfill apply v1

HEAD before:

- `60ece9d`

Task:

- `RETURN_CANT_RUNTIME_PRICING_BACKFILL_APPLY_OWNER_GO_V1`

Mode / target:

- `mode = runtime_pricing_backfill_apply`
- `target = local active runtime DB pricing rows`

Files read:

- `backend/scripts/backfill_return_cant_pricing_keys.py`
- `backend/tests/test_return_cant_runtime_pricing_backfill.py`
- `docs/worklog/realignment/2026-07-09_return_cant_runtime_pricing_backfill_alignment_v1.md`

Pre-apply safety gate:

- HEAD confirmed = `60ece9d`
- no staged files
- `git diff --check` clean
- existing unrelated untracked worktree preserved untouched

Pre-apply runtime DB inspection:

- DB path: `C:\Users\offic\workos_app_vs\backend\dev.db`
- target material rows present before apply: `0/4`
- target workcenter rows present before apply: `0/2`
- protected legacy rows present and healthy before apply:
  - `MAT-ORACAL-641`
  - `MAT-ORACAL-651`
  - `MAT-PROFIL-LATERAL-LITERE-30MM`
  - `MAT-PROFIL-LATERAL-LITERE-60MM`
  - `MAT-PROFIL-LATERAL-LITERE-80MM`
  - `MAT-PROFIL-LATERAL-LITERE-100MM`
  - `MAT-VOPSEA-RAL`
  - `FACE_VINYL_APPLICATION_LABOR`
  - `PAINTING`
  - `VINYL_APPLICATION`

Tests rerun before apply:

- `.\.venv\Scripts\python.exe -m pytest tests/test_return_cant_runtime_pricing_backfill.py tests/test_return_cant_pricing_registry_keys.py tests/test_return_cant_owner_confirmed_materials.py tests/test_volumetric_operation_labor_rates.py -q`
- result: `13 passed, 2 warnings in 1.55s`

Apply command:

- `.\.venv\Scripts\python.exe scripts/backfill_return_cant_pricing_keys.py`

Script output:

- inserted:
  - `MAT-VOPSEA-RAL-CANT-30MM`
  - `MAT-VOPSEA-RAL-CANT-60MM`
  - `MAT-VOPSEA-RAL-CANT-80MM`
  - `MAT-VOPSEA-RAL-CANT-100MM`
  - `RETURN_CANT_VINYL_APPLICATION_LABOR`
  - `RETURN_CANT_RAL_PAINT_LABOR`
- `already_ok = 0`
- `conflicts = 0`
- `skipped = 0`

Conflict handling result:

- no conflicts detected
- no overwrite attempted

Post-apply runtime DB inspection:

- target material rows present after apply: `4/4`
- target workcenter rows present after apply: `2/2`
- values correct:
  - `MAT-VOPSEA-RAL-CANT-30MM = 2 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-60MM = 2.5 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-80MM = 3 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-100MM = 4 EUR/ml`
  - `RETURN_CANT_VINYL_APPLICATION_LABOR = 1 EUR/ml`
  - `RETURN_CANT_RAL_PAINT_LABOR = 1 EUR/ml`
- legacy rows unchanged after apply

API verification:

- live pricing registry endpoint returned all six target keys with:
  - `base_cost` populated
  - `status = active`
  - `confidence = owner_confirmed`

UI verification:

- route checked: `http://127.0.0.1:3000/inventory/pricing`
- `Toate intrările` refreshed successfully
- search `RETURN_CANT_` displayed both labor rows at `1,00 EUR`
- search `MAT-VOPSEA-RAL-CANT-` displayed the four material rows at `2,00 / 2,50 / 3,00 / 4,00 EUR`
- integrated browser screenshots captured for:
  - general Pricing / `Toate intrările`
  - `RETURN_CANT_`
  - `MAT-VOPSEA-RAL-CANT-`

Files touched in this apply slice:

- `docs/qa/return-cant-runtime-pricing-backfill-apply-2026-07-09/RETURN_CANT_RUNTIME_PRICING_BACKFILL_APPLY_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_runtime_pricing_backfill_apply_v1.md`

Forbidden scope confirmation:

- no Pricing UI changes
- no code changes except docs created for apply record
- no Product Truth changes
- no adapter changes
- no Intake UI changes
- no Quote/Order/Execution changes
- no ProductAggregate/TaskGraph/ExecutionPlan changes
- no DB migration
- no general seed run
- no conflict overwrite

Validation pending before commit:

- `git diff --check` for the two docs

Recommended next prompt:

- `RETURN_CANT_PRICING_UI_RUNTIME_RECHECK_V1`