# COMPONENT_FIRST_RETURN_CANT_INTAKE_V6_COLOR_CATALOG_CROSS_REFERENCE_V1

**Date:** 2026-07-09  
**HEAD before:** `e468497` — Apply RETURN-CANT RAL minimum scope  
**Scope:** Readonly cross-reference Intake V6 Oracal/RAL catalogs + owner-confirmed Oracal series prices (651/641/8500). No pricing activation, backend, DB, Product Truth live write.

---

## Intake V6 source audit

| Catalog | Source file | Format | Reusable readonly? | Notes |
|---------|-------------|--------|--------------------|-------|
| Oracal 651 | `frontend/src/lib/colorRegistry/oracal651.ts` | `ColorRegistryItem[]` (79 colors) | YES | Structured frontend registry |
| Oracal 8500 | `frontend/src/lib/colorRegistry/oracal8500.ts` | `ColorRegistryItem[]` (55 colors) | YES | Translucent series |
| Oracal 641 | No separate file — reuses 651 palette | UI series token + pricing series | YES (policy) | `oracalColorPaletteSeriesForV6Face("oracal_641")` → `"651"` |
| Aggregator | `frontend/src/lib/colorRegistry/colorRegistry.ts` | `ALL_COLOR_REGISTRY_ITEMS` merge | YES | Shared by Intake V6 selectors |
| RAL Classic | `frontend/src/lib/colorRegistry/ralColors.ts` | `ColorRegistryItem[]` (213 colors) | YES | RAL Classic from import CSV |
| Intake V6 UI | `ColorRegistrySelect.tsx`, `IntakeV6ReturnCantFields.tsx` | Readonly UI consumer | YES | Cant uses ORACAL 651 + RAL filters |

**Not duplicated:** Product System workshop references Intake V6 sources only (`do_not_duplicate_catalog`).

---

## Owner answers applied

| Area | Applied value | Status | Remaining missing |
|------|---------------|--------|-------------------|
| Oracal catalog source | Intake V6 colorRegistry (651 + 8500; 641 → 651 palette) | `owner_confirmed` | Stable shared module extraction if Product System needs separate materialization |
| RAL catalog source | Intake V6 ralColors.ts — RAL Classic | `owner_confirmed` | Same as above |
| Oracal 651 price | 8 EUR/mp | `owner_confirmed` | Runtime formula |
| Oracal 641 price | 5 EUR/mp | `owner_confirmed` | Per-code prices beyond series |
| Oracal 8500 price | 13 EUR/mp | `owner_confirmed` | Per-code prices beyond series |
| Oracal full price table | Partial — known series only | `partial_confirmed` | All other official codes/series |
| RAL prices/minimum | Unchanged from prior commits | `owner_confirmed` | — |

---

## Remaining blockers before pricing

1. Oracal price table for all official codes/series not complete  
2. Stable shared catalog extraction remains future work if Product System catalog materialization is needed  
3. Pricing activation not allowed  
4. Product Truth live write not allowed  

`readyForPricing`: false · `pricingActiveCount`: 0

---

## What was NOT invented

- No fake Oracal color codes or full price table  
- No fake RAL list  
- No prices beyond owner-confirmed 651/641/8500 series values  
- No pricing formulas / runtime activation  
- No Product Truth live write  
- No backend / DB / seed changes  

---

## Files changed

| File | Change |
|------|--------|
| `componentFirstReturnCantCatalogPriceInputs.ts` | Intake V6 source refs, Oracal series prices, updated blockers |
| `ReturnCantCatalogPriceInputsPanel.tsx` | Oracal series price summary block |
| `componentFirstReturnCantOwnerInputs.ts` | Oracal catalog Intake V6 cross-ref |
| `componentFirstReturnCantCatalogPriceInputs.test.tsx` | Source + series price tests |
| `componentFirstReturnCantOwnerInputs.test.ts` | Updated catalog expectations |
| `ProductSystem.badges.test.tsx` | UI cross-ref + series price assertions |
| `product-system-readonly-smoke.spec.ts` | Playwright assertions |
| `return_cant_owner_answers_pending.md` | Owner doc updates |
| Screenshot script + 10 QA PNGs | UI verification |

---

## Tests

**Unit (PASS):** 161 tests  
**Playwright (PASS):** `test:e2e:product-system-readonly-smoke`

---

## Screenshots

`docs/qa/component-first-return-cant-intake-v6-color-catalog-cross-reference-v1/screenshots/` (01–10)

**UI opinion:** Panel clearly shows Intake V6 file paths for Oracal/RAL, series prices 651/641/8500, unchanged RAL cant values, and NOT READY FOR PRICING with updated blockers.

---

## Final verdict

**PASS**

---

## Next owner questions

1. Remaining Oracal series/code prices beyond 651/641/8500, if needed  
2. Stable catalog extraction/shared module if Product System needs separate materialization  
3. Later pricing activation plan only after Product Truth path is ready  
