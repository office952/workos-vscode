# Component-first RETURN-CANT — Owner Answers Apply v2

## HEAD before

`d64c427` — Prepare RETURN-CANT owner answers workshop

## Scope

Apply confirmed owner answers from prompt to readonly contract/workshop. No runtime, no Product Truth write, no invented catalogs/prices.

## Owner answers source

Owner prompt (this task) — explicit answers for items 1–11.

## Owner answers applied

| Topic | Contract key | Applied value | Status |
|-------|--------------|---------------|--------|
| Oracal selector | `oracal_selector_mode` | listă completă Oracal | owner_confirmed |
| Oracal pricing mode | `oracal_pricing_mode` | preț pe cod/familie | owner_confirmed |
| RAL input mode | `ral_input_mode` | selector standard RAL | owner_confirmed |
| Depths | `return_depths_standard` | 30 / 60 / 80 / 100 mm | owner_confirmed |
| Material | `return_material` | aluminiu 0.6 mm | owner_confirmed |
| Material unit | `return_material_unit` | ml | owner_confirmed |
| Labor unit | `return_labor_unit` | ml | owner_confirmed |
| Stock pricing | `stock_color_affects_price` | false (atelier only) | owner_confirmed |
| Perimeter | `perimeter_geometry_source` | perimetru/contur real al literelor | owner_confirmed |

## Partial applied

| Topic | Contract key | Partial value | Status |
|-------|--------------|---------------|--------|
| RAL material | `ral_material_price_rule` | Unitate ml — preț neconfirmat | partial_confirmed |
| RAL labor | `ral_labor_price_rule` | Unitate ml — preț/minim neconfirmat | partial_confirmed |

## Still pending

- `oracal_code_list` — catalog efectiv
- `ral_selector_source` — sursă/listă RAL
- `minimum_price_rule` — minim preț
- `material_depth_compatibility` — combinații valide
- Oracal price table by code/family (data, not mode)
- RAL material/labor price values

## What was not invented

No Oracal codes · no RAL table · no prices · no formulas · no Product Truth write · no pricing activation

## Files changed

- `componentFirstReturnCantOwnerInputs.ts` — applied confirmed + partial values
- `componentFirstLettersProductTruthWorkshop.ts` — workshop fields aligned
- `ReturnCantOwnerInputsPanel.tsx` — partial section + summary
- `componentFirstReturnCantOwnerApplyPlan.ts` — topic statuses updated
- Tests + Playwright spec
- `return_cant_owner_answers_pending.md`
- Screenshot script + 11 QA screenshots

## Tests

Unit: **142/142 PASS**

```powershell
cd frontend
npm.cmd run test -- componentFirstReturnCantOwnerInputs.test.ts ...
```

Playwright: **1/1 PASS**

```powershell
$env:PW_SKIP_WEB_SERVER='1'; $env:PW_BASE_URL='http://127.0.0.1:3000'
npm.cmd run test:e2e:product-system-readonly-smoke
```

## Screenshots

`docs/qa/component-first-return-cant-owner-answers-apply-v2/screenshots/` — 11 files (01–11)

## Final verdict

**PASS**

## Next owner questions

1. Catalog Oracal efectiv (coduri)
2. Tabel prețuri Oracal pe cod/familie
3. Sursă/listă RAL standard
4. Valori preț material Vopsit RAL
5. Valori preț/minim manoperă Vopsit RAL
6. Compatibilitate material ↔ adâncime
