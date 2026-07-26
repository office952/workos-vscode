# 2026-07-09 - return cant pricing keys alignment plan v1

HEAD before:

- `d6b8d09`

HEAD after:

- pending

Task:

- `RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN_V1`

Files read:

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `docs/worklog/realignment/2026-07-08_return_cant_readonly_adapter_universal_finish_terms_update_v1.md`
- `docs/architecture/product-system/REUSABLE_FINISH_CATALOGS_AND_RETURN_CANT_PRICING_BOUNDARY.md`
- `docs/qa/reusable-finish-catalogs-and-return-cant-pricing-boundary-2026-07-08/REUSABLE_FINISH_CATALOGS_AND_RETURN_CANT_PRICING_BOUNDARY_AUDIT_V1.md`
- `frontend/src/lib/pricingRegistry.ts`
- `frontend/src/pages/Pricing.tsx`
- `backend/services/pricing_registry_service.py`
- `backend/data/dev_volumetric_v2_registry_bridge.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/seeds/material_canonical_naming.py`
- `backend/seeds/seed_build4_materials.py`
- `backend/services/shared_vinyl_material_catalog.py`
- `backend/services/shared_edge_cant_rules.py`
- `backend/services/intake_v4_ral_paint_rules_service.py`
- `backend/seeds/seed_intake_v6_unified_pricing.py`
- `backend/seeds/seed_volumetric_workcenter_rates.py`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
- `backend/services/volumetric_material_rate_resolver.py`
- `docs/architecture/realignment/14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md`

Files touched:

- `docs/architecture/product-system/RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN.md`
- `docs/qa/return-cant-pricing-keys-alignment-plan-2026-07-09/RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_keys_alignment_plan_v1.md`

Decision drafted:

- `RETURN_CANT_PRICING_KEYS_ALIGNMENT_READY`

Key conclusions:

1. profile width material rows already exist and remain valid;
2. `MAT-ORACAL-641` and `MAT-ORACAL-651` already exist in Pricing evidence;
3. no exact cant-specific vinyl labor row exists yet;
4. no exact width-based RAL cant material rows exist yet;
5. no exact cant-specific RAL labor row exists yet;
6. legacy `PAINTING`, `VINYL_APPLICATION`, `FACE_VINYL_APPLICATION_LABOR`, and `MAT-VOPSEA-RAL` must not be relabeled as if they already satisfy the final target semantics.

Naming recommendation:

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_RAL_PAINT_LABOR`

Boundary confirmation:

- no Pricing changes
- no UI changes
- no adapter changes
- no DB / seed / migration
- no Product Truth writes
- no component calculation

Validation run:

- `git diff --check`

Next recommended prompt:

- `RETURN_CANT_PRICING_KEYS_CREATION_AND_REGISTRY_ALIGNMENT_V1`