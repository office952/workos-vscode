# 2026-07-09 - return cant pricing keys registry implementation v1

HEAD before:

- `0455839`

HEAD after:

- pending at write time; finalized by the commit that stages this file

Task:

- `RETURN_CANT_PRICING_KEYS_REGISTRY_IMPLEMENTATION_V1`

Files read:

- `docs/architecture/product-system/RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN.md`
- `docs/qa/return-cant-pricing-keys-alignment-plan-2026-07-09/RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_keys_alignment_plan_v1.md`
- `docs/architecture/product-system/REUSABLE_FINISH_CATALOGS_AND_RETURN_CANT_PRICING_BOUNDARY.md`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `backend/services/pricing_registry_service.py`
- `backend/data/dev_volumetric_v2_registry_bridge.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/seeds/seed_intake_v6_unified_pricing.py`
- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
- `backend/seeds/seed_volumetric_workcenter_rates.py`
- `backend/routers/intake_v6_workspaces.py`
- `backend/tests/test_pricing_registry.py`
- `backend/tests/test_volumetric_owner_confirmed_prices.py`
- `backend/tests/test_volumetric_operation_labor_rates.py`
- `backend/services/active_template_scope.py`
- `backend/seeds/seed_active_template_scope.py`
- `backend/models/product_templates.py`
- `backend/services/inventory_materials_admin_service.py`

Files touched:

- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
- `backend/seeds/seed_volumetric_workcenter_rates.py`
- `backend/tests/test_return_cant_pricing_registry_keys.py`
- `backend/tests/test_return_cant_owner_confirmed_materials.py`
- `backend/tests/test_volumetric_operation_labor_rates.py`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_keys_registry_implementation_v1.md`

Entries added:

- `RETURN_CANT_VINYL_APPLICATION_LABOR` = `1 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-30MM` = `2 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-60MM` = `2.5 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-80MM` = `3 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-100MM` = `4 EUR/ml`
- `RETURN_CANT_RAL_PAINT_LABOR` = `1 EUR/ml`

Entries existente neatinse:

- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`
- `MAT-ORACAL-641`
- `MAT-ORACAL-651`
- `FACE_VINYL_APPLICATION_LABOR`
- `PAINTING`
- `MAT-VOPSEA-RAL`

Implementation notes:

1. Required Pricing Registry surface for `TPL-VOLUMETRIC-LETTERS_v2` is driven from `V6_MATERIAL_PRICES` and `V6_WORKCENTER_RATES`, which inherit from the V5 pricing seed lists.
2. Cant-specific material values were added to the existing material seed sources, not to Product Truth, adapter, catalog, or component formulas.
3. Cant-specific labor values were added to the existing workcenter-rate seed source with explicit dedicated codes, leaving legacy rows intact.
4. Focused self-contained tests were added because the older broad registry suites are not a reliable discriminating validator for the `v2` active-template path.

Tests and validation run:

- `python -m pytest tests/test_return_cant_pricing_registry_keys.py tests/test_return_cant_owner_confirmed_materials.py tests/test_volumetric_operation_labor_rates.py -q`
- `git diff --check`

Validation result summary:

- new material rows exist with `ml` units and owner-confirmed values
- new labor rows exist with `EUR/ml` registry units and `per_linear_meter` basis
- no duplicate pricing codes in the focused registry test
- legacy `PAINTING`, `MAT-VOPSEA-RAL`, `FACE_VINYL_APPLICATION_LABOR`, `MAT-ORACAL-641`, and `MAT-ORACAL-651` remained unchanged in focused validation

Forbidden scope confirmation:

- no UI changes
- no adapter changes
- no Product Truth changes
- no ProductDefinition changes
- no Quote / Order / Execution changes
- no ProductAggregate / TaskGraph / ExecutionPlan changes
- no DB migration
- no seed run outside test validation / no owner GO seed execution against dev data
- no pricing values added to component or catalog

Next recommended prompt:

- `RETURN_CANT_PRICING_KEYS_READONLY_VERIFICATION_V1`