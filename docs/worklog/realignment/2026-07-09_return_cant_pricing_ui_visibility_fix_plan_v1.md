# 2026-07-09 - return cant pricing ui visibility fix plan v1

HEAD before:

- `3f9725b`

Task:

- `RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN_V1`

Files read:

- `docs/qa/return-cant-e2e-ui-readonly-verification-2026-07-09/RETURN_CANT_E2E_UI_READONLY_VERIFICATION_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_e2e_ui_readonly_verification_v1.md`
- `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
- `backend/seeds/seed_volumetric_workcenter_rates.py`
- `backend/services/pricing_registry_service.py`
- `frontend/src/pages/Pricing.tsx`
- `frontend/src/api/pricingRegistry.ts`
- `frontend/src/components/pricing/PricingRegistrySpaciousView.tsx`
- `frontend/src/components/pricing/PricingEntryRow.tsx`
- `frontend/src/lib/pricingRegistry.ts`
- `backend/tests/test_return_cant_pricing_registry_keys.py`
- `backend/tests/test_return_cant_owner_confirmed_materials.py`
- `backend/tests/test_volumetric_operation_labor_rates.py`

Runtime checks performed:

1. live API read:
   - `GET /api/v1/pricing/registry?template_code=TPL-VOLUMETRIC-LETTERS`
2. runtime DB read-only query in `backend/dev.db` for missing return_cant keys
3. runtime DB read-only contrast query in `backend/dev.db` for known-good legacy volumetric keys

Files touched:

- `docs/architecture/product-system/RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN.md`
- `docs/qa/return-cant-pricing-ui-visibility-fix-plan-2026-07-09/RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_ui_visibility_fix_plan_v1.md`

Decision:

- `RETURN_CANT_PRICING_UI_VISIBILITY_FIX_PLAN_READY`

Main findings:

1. noile key-uri `return_cant` sunt definite in seed source cu valorile asteptate;
2. `PricingRegistryService` le include in payload-ul live si le marcheaza `missing_price` doar cand rows-urile runtime lipsesc;
3. Pricing UI afiseaza `Lipsă` fidel cand `base_cost` este `null`, deci nu este cauza locala;
4. runtime DB-ul activ `backend/dev.db` nu contine rows pentru cele patru materiale RAL cant si cele doua workcenter rates return_cant;
5. runtime DB-ul activ contine in schimb rows active pentru codurile vechi care apar corect in UI, ceea ce elimina ipoteza unui esec general de Pricing registry.

Root cause bucket:

- `runtime_db_missing`

Rejected buckets:

- `service_mapping_issue`
- `ui_display_issue`
- `unknown`

Recommended next slice:

- `RETURN_CANT_RUNTIME_PRICING_BACKFILL_ALIGNMENT_V1`

Reason:

1. fixul corect este sa existe rows runtime pentru cele sase key-uri deja contractate;
2. un fix UI ar masca lipsa reala a registry-ului;
3. un one-off mapping hack ar dubla inutil logica deja existenta in seed-urile owner-confirmed.

Validation run:

- read-only audit only
- live API inspection
- runtime DB read-only inspection
- docs-only diff validation pending

Next recommended prompt:

- `RETURN_CANT_RUNTIME_PRICING_BACKFILL_ALIGNMENT_V1`