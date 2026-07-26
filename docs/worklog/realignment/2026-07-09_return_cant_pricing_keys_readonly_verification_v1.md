# 2026-07-09 - return cant pricing keys readonly verification v1

HEAD before:

- `98ebcb0`

HEAD after:

- pending at write time; finalized by docs-only commit if staged

Task:

- `RETURN_CANT_PRICING_KEYS_READONLY_VERIFICATION_V1`

Files read:

- `docs/worklog/realignment/2026-07-09_return_cant_pricing_keys_registry_implementation_v1.md`
- `docs/architecture/product-system/RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN.md`
- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
- `backend/seeds/seed_volumetric_workcenter_rates.py`
- `backend/tests/test_return_cant_pricing_registry_keys.py`
- `backend/tests/test_return_cant_owner_confirmed_materials.py`
- `backend/tests/test_volumetric_operation_labor_rates.py`
- `backend/services/pricing_registry_service.py`
- `frontend/src/pages/Pricing.tsx`

Files touched:

- `docs/qa/return-cant-pricing-keys-readonly-verification-2026-07-09/RETURN_CANT_PRICING_KEYS_READONLY_VERIFICATION_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_keys_readonly_verification_v1.md`

Verification summary:

1. The new material keys exist in the pricing seed source and owner-confirmed material source.
2. The new labor keys exist in the workcenter-rate seed source with `per_linear_meter` basis.
3. The Pricing Registry service remains read-only and derives required V2 pricing surface from `V6_MATERIAL_PRICES` and `V6_WORKCENTER_RATES`.
4. Focused tests confirm exact units, exact values, and legacy non-regression.
5. Runtime UI verification was not run because local frontend/backend servers were not already started.

Keys verified:

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_RAL_PAINT_LABOR`

Values verified:

- `RETURN_CANT_VINYL_APPLICATION_LABOR` = `1 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-30MM` = `2 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-60MM` = `2.5 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-80MM` = `3 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-100MM` = `4 EUR/ml`
- `RETURN_CANT_RAL_PAINT_LABOR` = `1 EUR/ml`

Non-regression checked:

- `MAT-ORACAL-641`
- `MAT-ORACAL-651`
- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`
- `FACE_VINYL_APPLICATION_LABOR`
- `VINYL_APPLICATION`
- `PAINTING`
- `MAT-VOPSEA-RAL`

Tests and validation run:

- `python -m pytest tests/test_return_cant_pricing_registry_keys.py tests/test_return_cant_owner_confirmed_materials.py tests/test_volumetric_operation_labor_rates.py -q`
- local port check for `8000` and `3000`
- `git diff --check`

Runtime verification status:

- `not_run_runtime_not_started`

Forbidden scope confirmation:

- no Pricing changes
- no UI changes
- no adapter changes
- no Product Truth changes
- no Quote / Order / Execution changes
- no ProductAggregate / TaskGraph / ExecutionPlan changes
- no DB migration
- no seed run without owner GO

Next recommended prompt:

- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN_V1`