# RETURN_CANT_RAL_PRICING_KEY_DEDUP_V1

**Date:** 2026-07-09  
**HEAD before:** `2eb29d7`  
**Scope:** Deduplicate RETURN-CANT RAL material/labor EUR literals in Product System workshop to Pricing Registry key references. RAL minimum 100 lei remains owner commercial policy (not Pricing Registry).

## Audit recap (read-only, pre-edit)

### RAL material/labor literals found (Product System)

| Location | Before |
|----------|--------|
| `ral_material_price_by_depth.confirmedValue` | `30 mm: 2.00 EUR/ml` … `100 mm: 4.00 EUR/ml` (+ keys in parens) |
| `ral_labor_price_by_depth.confirmedValue` | `30/60/80/100 mm: 1.00 EUR/ml` |
| `ral_material_price_rule` (owner inputs) | `30=2.00 EUR/ml · 60=2.50 · 80=3.00 · 100=4.00 EUR/ml` |
| `ral_labor_price_rule` (owner inputs) | `1.00 EUR/ml — același preț toate adâncimile` |
| `componentFirstReturnCantOwnerApplyPlan.ts` notes | `Manoperă 1.00 EUR/ml confirmată…` |

### Pricing Registry keys (authority — values match, no divergence)

| Key | Unit | Registry value |
|-----|------|----------------|
| `MAT-VOPSEA-RAL-CANT-30MM` | ml / EUR | 2.0 |
| `MAT-VOPSEA-RAL-CANT-60MM` | ml / EUR | 2.5 |
| `MAT-VOPSEA-RAL-CANT-80MM` | ml / EUR | 3.0 |
| `MAT-VOPSEA-RAL-CANT-100MM` | ml / EUR | 4.0 |
| `RETURN_CANT_RAL_PAINT_LABOR` | EUR/ml | 1.0 |

### RAL minimum carve-out

- `RETURN_CANT_RAL_MINIMUM` / `ral_minimum_rule` / `minimum_price_rule` **unchanged**
- 100 lei = owner commercial policy in RON, per RAL color, material+labor total
- **NOT** in Pricing Registry — no `MAT-*` key, no `/inventory/pricing` source for minimum

### Backend change needed

**NO** — Product Truth adapter already key-based; registry values unchanged.

## Implementation

### Contract updates

- Added `RETURN_CANT_RAL_PRICING_REGISTRY_KEYS` (4 material + 1 labor)
- Derived `RETURN_CANT_RAL_MATERIAL_PRICE_CODES` from registry keys array
- Added `buildRalPricingKeyCoverageSummary` + summary field on catalog price summary
- Replaced RAL material/labor `confirmedValue` and `knownSoFarRo` with key references only

### UI updates

- `ReturnCantCatalogPriceInputsPanel`: RAL pricing registry keys section + owner commercial policy section for minimum

### Owner inputs

- `ral_material_price_rule` / `ral_labor_price_rule` → registry keys + `/inventory/pricing`
- Apply plan notes updated (no EUR literal)

## Search gate

| Pattern | product-system + e2e | Result |
|---------|----------------------|--------|
| `2.00 EUR/ml` … `1.00 EUR/ml` | active PS RAL material/labor | **REMOVED** |
| `100 lei` | minimum owner policy | **RETAINED** (not attached to registry) |

## Files changed

- `frontend/src/features/product-system/componentFirstReturnCantCatalogPriceInputs.ts`
- `frontend/src/features/product-system/componentFirstReturnCantOwnerInputs.ts`
- `frontend/src/features/product-system/componentFirstReturnCantOwnerApplyPlan.ts`
- `frontend/src/features/product-system/ReturnCantCatalogPriceInputsPanel.tsx`
- `frontend/src/features/product-system/componentFirstReturnCantCatalogPriceInputs.test.tsx`
- `frontend/src/features/product-system/componentFirstReturnCantOwnerInputs.test.ts`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/e2e/product-system-readonly-smoke.spec.ts`
- `frontend/scripts/capture-return-cant-ral-pricing-key-dedup-v1-screenshots.mjs`
- `docs/qa/return-cant-ral-pricing-key-dedup-v1/screenshots/*.png`

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReturnCantCatalogPriceInputs.test.tsx src/features/product-system/componentFirstReturnCantOwnerInputs.test.ts src/pages/ProductSystem.badges.test.tsx src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/features/product-system/legacyToComponentFirstReplacementMap.test.ts src/features/product-system/componentFirstLettersProductTruthWorkshop.test.ts src/features/product-system/componentFirstReturnCantOwnerApplyPlan.test.ts
```

**Result:** 161/161 PASS

```powershell
$env:PW_SKIP_WEB_SERVER='1'; $env:PW_BASE_URL='http://127.0.0.1:3000'; npm.cmd run test:e2e:product-system-readonly-smoke
```

**Result:** 1/1 PASS

## Screenshots

`docs/qa/return-cant-ral-pricing-key-dedup-v1/screenshots/`

1. `01_return_cant_catalog_price_inputs_after_ral_dedup.png`
2. `02_ral_material_keys_visible.png`
3. `03_ral_labor_key_visible.png`
4. `04_inventory_pricing_source_visible.png`
5. `05_ral_minimum_100_lei_owner_commercial_rule.png`
6. `06_not_in_pricing_registry_for_minimum.png`
7. `07_not_ready_for_pricing_still_visible.png`
8. `08_no_save_apply_pricing_activation_actions.png`
9. `09_active_root_offerable_work_intake_yes.png`
10. `10_logo_not_work_intake_owner_go.png`

## Final verdict

**PASS** — RAL material/labor deduped to Pricing Registry keys; minimum 100 lei stays owner commercial policy; forbidden scope respected.

## Next steps

- Pricing activation (forbidden until dedicated build)
- Product Truth live write / CPP commercial rules consuming minimum policy
- Oracal full price table per code/family (still partial)
- Broader source-of-truth audit if needed
