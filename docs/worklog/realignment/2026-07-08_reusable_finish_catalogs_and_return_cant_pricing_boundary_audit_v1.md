# 2026-07-08 - reusable finish catalogs and return cant pricing boundary audit v1

HEAD before:

- `570bd22`

HEAD after:

- pending at write time

Decision drafted:

- `REUSABLE_FINISH_CATALOGS_BOUNDARY_READY`

Files read:

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `docs/worklog/realignment/2026-07-08_return_cant_truth_field_capture_readonly_contract_adapter_v1.md`
- `docs/architecture/product-system/RETURN_CANT_VARIATION_SEMANTICS_AND_PRICING_BOUNDARY.md`
- `docs/architecture/product-system/RETURN_CANT_INTAKE_V6_VARIATIONS_TRUTH_CAPTURE_AUDIT.md`
- `docs/architecture/product-system/MATERIAL_COLOR_CATALOGS_AND_INVENTORY_KEY_MODEL_V1.md`
- `docs/architecture/SHARED_VINYL_MATERIAL_CATALOG.md`
- `docs/architecture/realignment/14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishModel.ts`
- `frontend/src/lib/intakeV6/intakeV6ReturnFinishRules.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantFields.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/lib/pricingRegistry.ts`
- `frontend/src/pages/Pricing.tsx`
- `frontend/src/pages/Utilaje.tsx`
- `frontend/src/api/pricingRegistry.ts`
- `backend/services/shared_vinyl_material_catalog.py`
- `backend/services/shared_edge_cant_rules.py`
- `backend/services/pricing_registry_service.py`
- `backend/services/intake_v4_ral_paint_rules_service.py`
- `backend/data/dev_volumetric_v2_registry_bridge.py`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`

Files touched:

- `docs/architecture/product-system/REUSABLE_FINISH_CATALOGS_AND_RETURN_CANT_PRICING_BOUNDARY.md`
- `docs/qa/reusable-finish-catalogs-and-return-cant-pricing-boundary-2026-07-08/REUSABLE_FINISH_CATALOGS_AND_RETURN_CANT_PRICING_BOUNDARY_AUDIT_V1.md`
- `docs/worklog/realignment/2026-07-08_reusable_finish_catalogs_and_return_cant_pricing_boundary_audit_v1.md`

Why the boundary is ready:

1. the catalog role is now clearly separated from Pricing role;
2. reusable Oracal and RAL catalog families are already supported conceptually by repo architecture;
3. `/utilaje` is clearly non-commercial and does not need to own quote pricing;
4. stock color remains non-priced as extra finish.

Key findings:

1. current `return_cant` UI is still `Oracal 651`-only for vinyl cant.
2. shared vinyl catalog already recognizes `641`, `651`, `8500` as distinct series.
3. Pricing/runtime evidence for profile width rows is solid.
4. Pricing/runtime evidence for final cant vinyl labor `1 EUR/ml` and width-based RAL material rows is not yet cleanly expressed in current live runtime.
5. this does not block the boundary contract; it creates a next runtime alignment task.

Adapter impact conclusion:

- current adapter remains valid as first pass;
- next adapter update should migrate from `oracal` / `ral_paint` to universal terms `vinyl_application` / `paint_application`;
- next adapter update should allow reusable series-aware vinyl references including `Oracal 641`.

Pricing boundary confirmation:

- profile material by width stays in Pricing
- return operations stay in Pricing
- vinyl material stays in Pricing per `mp`
- vinyl labor target stays in Pricing per `ml`
- RAL material target stays in Pricing by width
- RAL labor target stays in Pricing per `ml`
- catalog stores no price or cost

Reusable catalog boundary confirmation:

- Oracal is reusable
- RAL is reusable
- stock colors are reusable operational labels
- no catalog UI / CRUD introduced

Analyzer boundary confirmation:

- analyzer provides context only
- Product Truth remains the confirmation owner
- analyzer does not own cost or price

Forbidden scope confirmation:

- no code changes
- no UI changes
- no Pricing changes
- no DB / seed / migration
- no Quote / Order / Execution changes
- no ProductAggregate / TaskGraph / ExecutionPlan changes

Validation planned:

- `git diff --check`
- docs-only diff only
- no build
- no tests

Roadmap awareness checkpoint:

- note: `9/10`
- position: reusable finish boundary locked immediately before adapter terminology/runtime alignment
- dead pieces check: no new dead architecture branch introduced; current `oracal` / `ral_paint` wording is now explicitly transitional
- alignment with target direction: `96/100%`

Next recommended prompt:

- `RETURN_CANT_READONLY_ADAPTER_UNIVERSAL_FINISH_TERMS_UPDATE_V1`