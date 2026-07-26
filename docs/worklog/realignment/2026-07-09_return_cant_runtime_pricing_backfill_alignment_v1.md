# 2026-07-09 - return cant runtime pricing backfill alignment v1

HEAD before:

- `d322d4c`

Task:

- `RETURN_CANT_RUNTIME_PRICING_BACKFILL_ALIGNMENT_V1`

Mode / target:

- `mode = runtime_pricing_backfill_alignment`
- `target = runtime DB active pricing rows`

Artifacts read:

- `docs/architecture/product-system/RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN.md`
- `docs/qa/return-cant-pricing-ui-visibility-fix-plan-2026-07-09/RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_ui_visibility_fix_plan_v1.md`
- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
- `backend/seeds/seed_volumetric_workcenter_rates.py`
- `backend/services/pricing_registry_service.py`
- `backend/tests/test_return_cant_pricing_registry_keys.py`
- `backend/tests/test_return_cant_owner_confirmed_materials.py`
- `backend/tests/test_volumetric_operation_labor_rates.py`
- `backend/models/inventory_materials.py`
- `backend/models/workcenter_rates.py`
- `backend/core/database.py`
- `backend/tests/_db_fixture.py`

DB inspection:

- inspected path: `backend/dev.db`
- absolute path observed: `C:\Users\offic\workos_app_vs\backend\dev.db`
- file exists: yes

Missing rows confirmed in runtime DB before any remediation:

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_RAL_PAINT_LABOR`

Non-regression rows confirmed present before any remediation:

- `MAT-ORACAL-641 = 6.5 EUR`
- `MAT-ORACAL-651 = 9 EUR`
- `MAT-PROFIL-LATERAL-LITERE-30MM = 2 EUR`
- `MAT-PROFIL-LATERAL-LITERE-60MM = 3 EUR`
- `MAT-PROFIL-LATERAL-LITERE-80MM = 4 EUR`
- `MAT-PROFIL-LATERAL-LITERE-100MM = 5 EUR`
- `FACE_VINYL_APPLICATION_LABOR = 5 EUR/mp`
- `PAINTING = 4 EUR/ml`
- `MAT-VOPSEA-RAL = 10 EUR/buc`

Files touched:

- `backend/scripts/backfill_return_cant_pricing_keys.py`
- `backend/tests/test_return_cant_runtime_pricing_backfill.py`
- `docs/worklog/realignment/2026-07-09_return_cant_runtime_pricing_backfill_alignment_v1.md`

Implementation summary:

1. added a dedicated insert-only remediation script for the six `return_cant` pricing rows;
2. script inserts missing rows only;
3. script reports `already_ok` when an existing row already matches the expected runtime values;
4. script reports `conflict` and does not overwrite when an existing row differs;
5. script does not touch legacy rows and does not run a general seed.

Target runtime rows covered by the script:

- materials:
  - `MAT-VOPSEA-RAL-CANT-30MM`
  - `MAT-VOPSEA-RAL-CANT-60MM`
  - `MAT-VOPSEA-RAL-CANT-80MM`
  - `MAT-VOPSEA-RAL-CANT-100MM`
- workcenter rates:
  - `RETURN_CANT_VINYL_APPLICATION_LABOR`
  - `RETURN_CANT_RAL_PAINT_LABOR`

Test scope added:

- inserts missing material rows;
- inserts missing labor rows;
- idempotent second run;
- does not overwrite conflicting existing row;
- does not touch legacy rows;
- values / units / currency remain correct.

Runtime apply status:

- `runtime_apply_pending_owner_go`

Forbidden scope confirmation:

- no Pricing UI changes
- no Product Truth changes
- no adapter changes
- no Intake V6 UI changes
- no Quote/Order/Execution changes
- no ProductAggregate/TaskGraph/ExecutionPlan changes
- no DB migration
- no general seed run

Validation run for this slice:

1. focused pytest command:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_return_cant_runtime_pricing_backfill.py tests/test_return_cant_pricing_registry_keys.py tests/test_return_cant_owner_confirmed_materials.py tests/test_volumetric_operation_labor_rates.py -q`
2. result:
  - `13 passed, 2 warnings in 1.52s`
3. `git diff --check`
  - clean for the scoped files
4. no general build

Recommended next prompt if this slice commits cleanly:

- `RETURN_CANT_RUNTIME_PRICING_BACKFILL_APPLY_OWNER_GO_V1`