# Component-first RETURN-CANT — Catalog & Price Inputs Workshop v1

## HEAD before

`94ff0f2` — Apply confirmed RETURN-CANT owner answers

## Scope

Add readonly catalog/price inputs contract and UI panel for RETURN-CANT. No pricing activation, no invented catalogs/prices.

## Already confirmed (prior slices)

- Oracal selector = listă completă · Oracal pricing = preț pe cod/familie
- RAL mode = selector standard · Depths 30/60/80/100 mm · Material aluminiu 0.6 mm
- Units ml · Stock no price impact · Geometry perimetru/contur real
- RAL material/labor unit ml (prices still missing)

## Contract added

`frontend/src/features/product-system/componentFirstReturnCantCatalogPriceInputs.ts`

13 entries across Oracal catalog/pricing, RAL catalog, RAL material/labor pricing, minimum rule, material-depth compatibility.

## Summary state

| Metric | Value |
|--------|-------|
| Total inputs | 13 |
| Confirmed | 3 |
| Partial | 2 |
| Owner input required | 8 |
| Pricing active | 0 |
| Ready for pricing | false |

## Blockers before pricing

- Oracal actual catalog missing
- Oracal price table missing
- RAL selector source/list missing
- RAL material prices missing
- RAL labor prices/minimum missing
- Material/depth compatibility missing

## What was not invented

No Oracal codes · no RAL list · no prices · no formulas · no Product Truth write

## Files changed

- `componentFirstReturnCantCatalogPriceInputs.ts` (new)
- `ReturnCantCatalogPriceInputsPanel.tsx` (new)
- `componentFirstReturnCantCatalogPriceInputs.test.tsx` (new)
- `ComponentFirstProductTruthWorkshopPanel.tsx` (integrated panel)
- `return_cant_owner_answers_pending.md` (sections J–P)
- Playwright + badges tests + screenshot script

## Tests

Unit: **154/154 PASS** (7 files)

Playwright: **1/1 PASS**

## Screenshots

`docs/qa/component-first-return-cant-catalog-price-inputs-workshop-v1/screenshots/` — 11 files

## Final verdict

**PASS**

## Next owner questions

1. Oracal catalog source / list
2. Oracal price table by code/family + unit
3. RAL list source (Classic vs other)
4. RAL material price per ml/depth
5. RAL labor price/minimum per ml/depth
6. Material-depth compatibility rules
