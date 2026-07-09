# COMPONENT_FIRST_RETURN_CANT_RAL_MINIMUM_SCOPE_APPLY_V1

**Date:** 2026-07-09  
**HEAD before:** `9ddd939` — Apply RETURN-CANT catalog and RAL price answers  
**Scope:** Apply owner-confirmed RAL minimum scope only (readonly/workshop contract + UI + docs + tests). No pricing, backend, DB, Product Truth live write.

---

## Owner answer applied

| Field | Value |
|-------|-------|
| Amount | 100 lei |
| Currency | lei (no auto conversion to EUR) |
| Scope | pe culoare RAL (`per_ral_color`) |
| Applies to | total RAL material + manoperă (`material_plus_labor_total`) |
| Status | `owner_confirmed` |
| Pricing active | false |

Previously confirmed (unchanged): RAL material 2.00/2.50/3.00/4.00 EUR/ml, labor 1.00 EUR/ml all depths.

---

## Read-only audit (before apply)

**Already confirmed for RAL minimum:**
- Amount 100 lei
- Currency lei
- No automatic lei→EUR conversion

**Owner clarification applied now:**
- Scope = pe culoare RAL
- Applies to = total RAL material + manoperă

**Removed blocker:** `RAL minimum scope unresolved (100 lei confirmed)`

---

## Remaining blockers before pricing

1. Oracal actual catalog data/import not stored yet
2. Oracal price table values not stored yet
3. RAL list data/source not materialized in product system catalog
4. Pricing activation not allowed
5. Product Truth live write not allowed

`readyForPricing`: false · `pricingActiveCount`: 0 · all entries `pricingActive`: false

---

## What was NOT invented

- No fake Oracal codes or price table values
- No fake RAL list in product system catalog
- No pricing formulas / runtime activation
- No currency conversion
- No Product Truth live write
- No backend / DB / seed changes

---

## Files changed

| File | Change |
|------|--------|
| `frontend/src/features/product-system/componentFirstReturnCantCatalogPriceInputs.ts` | `RETURN_CANT_RAL_MINIMUM` constants; `ral_minimum_rule` → owner_confirmed; removed scope blocker |
| `frontend/src/features/product-system/componentFirstReturnCantOwnerInputs.ts` | `minimum_price_rule` confirmed; updated partial/missing lists |
| `frontend/src/features/product-system/componentFirstReturnCantOwnerApplyPlan.ts` | Topic G (RAL manoperă + minim) → answered |
| `frontend/src/features/product-system/componentFirstReturnCantCatalogPriceInputs.test.tsx` | RAL minimum scope tests + blocker update |
| `frontend/src/features/product-system/componentFirstReturnCantOwnerInputs.test.ts` | Minimum scope assertions; partialCount 1 |
| `frontend/src/features/product-system/componentFirstReturnCantOwnerApplyPlan.test.ts` | minimum_price_rule owner_confirmed |
| `frontend/src/pages/ProductSystem.badges.test.tsx` | RAL minimum scope UI assertions |
| `frontend/e2e/product-system-readonly-smoke.spec.ts` | Playwright RAL minimum scope assertions |
| `docs/worklog/owner-input/return_cant_owner_answers_pending.md` | Section O answered |
| `frontend/scripts/capture-return-cant-ral-minimum-scope-apply-v1-screenshots.mjs` | QA screenshot helper |
| `docs/qa/component-first-return-cant-ral-minimum-scope-apply-v1/screenshots/*.png` | 9 UI verification shots |

---

## Tests

**Unit (PASS):**
```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/features/product-system/legacyToComponentFirstReplacementMap.test.ts src/features/product-system/componentFirstLettersProductTruthWorkshop.test.ts src/features/product-system/componentFirstReturnCantOwnerInputs.test.ts src/features/product-system/componentFirstReturnCantOwnerApplyPlan.test.ts src/features/product-system/componentFirstReturnCantCatalogPriceInputs.test.tsx src/pages/ProductSystem.badges.test.tsx
```
159 tests passed.

**Playwright (PASS):**
```powershell
$env:PW_SKIP_WEB_SERVER='1'; $env:PW_BASE_URL='http://127.0.0.1:3000'; npm.cmd run test:e2e:product-system-readonly-smoke
```

---

## Screenshots

`docs/qa/component-first-return-cant-ral-minimum-scope-apply-v1/screenshots/`

1. `01_return_cant_catalog_price_panel.png`
2. `02_ral_minimum_100_lei.png`
3. `03_ral_minimum_scope_pe_culoare_ral.png`
4. `04_ral_minimum_applies_to_material_plus_labor.png`
5. `05_not_ready_for_pricing.png`
6. `06_safety_copy_no_truth_pricing_intake.png`
7. `07_no_save_apply_pricing_actions.png`
8. `08_active_root_offerable_work_intake.png`
9. `09_logo_not_work_intake_owner_go.png`

**UI opinion:** Panel clearly shows 100 lei minimum with pe culoare RAL scope and total material + manoperă basis; global NOT READY FOR PRICING and safety copy unchanged; no Save/Apply actions.

---

## Final verdict

**PASS** — Owner-confirmed RAL minimum scope applied to readonly contract/workshop only; forbidden scope respected.

---

## Next owner questions (priority)

1. Actual Oracal code list source/import
2. Actual Oracal price table values by code/family
3. Actual RAL list materialization in Product System catalog, if needed
4. Later currency/curs rule if needed
