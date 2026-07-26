# Component-first Letters — Product Truth Owner Workshop v1

## HEAD before

`aade5d0` — Add legacy to component-first replacement map

## Goal

Prepare a read-only Product Truth owner-workshop contract for component-first Letters templates, with **RETURN-CANT first** detail. No runtime activation, no live Product Truth write, no invented commercial values.

## Scope (respected)

| Area | Touched |
|------|---------|
| Frontend static contract + readonly UI | YES |
| Backend / DB / seed / migration | NO |
| Product Truth live write | NO |
| Pricing / ProductDefinition / ProductAggregate runtime | NO |
| Quote / Order / Execution / Work Intake | NO |
| Legacy delete / activation | NO |

## Audit — what existed vs missing

| Exists | Location |
|--------|----------|
| Product Truth path mapping (readonly) | `componentFirstReadonlyProductTruthMapping.ts` — 29 paths incl. `return_cant.material/depth/finish` |
| Form readiness groups | `componentFirstReadonlyFormSystemReadiness.ts` |
| Dossier contract fixture | `componentFirstReadonlyDossierAlignment.ts` |
| Component ownership / guards | `ComponentFirstReadonlyCandidatePanel.tsx`, `componentFirstReadonlyUiShared.tsx` |
| Legacy → component-first map | `legacyToComponentFirstReplacementMap.ts` |

| Missing (filled by this task) | |
|--------------------------------|---|
| Field-level owner workshop contract | `componentFirstLettersProductTruthWorkshop.ts` |
| RETURN-CANT finish_type / Oracal / RAL / units / pricing rules structure | Same |
| Owner questions export by severity | Helpers in workshop contract |
| UI “Product Truth owner workshop” panel | `ComponentFirstProductTruthWorkshopPanel.tsx` in Guards/Audit |

## Files changed

- `frontend/src/features/product-system/componentFirstLettersProductTruthWorkshop.ts`
- `frontend/src/features/product-system/componentFirstLettersProductTruthWorkshop.test.ts`
- `frontend/src/features/product-system/ComponentFirstProductTruthWorkshopPanel.tsx`
- `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx` (workshop UI tests + flaky wait fix)
- `frontend/e2e/product-system-readonly-smoke.spec.ts`
- `frontend/scripts/capture-component-first-truth-workshop-screenshots.mjs`
- `docs/qa/component-first-letters-product-truth-workshop-v1/screenshots/` (10 PNGs)

## RETURN-CANT fields (12)

| Field | Status |
|-------|--------|
| finish_type | confirmed (Culoare Stock / Oracal / Vopsit RAL) |
| stock_color_note | confirmed |
| oracal_code | owner_input_required |
| ral_code | owner_input_required |
| return_depth_mm | owner_input_required |
| return_material | owner_input_required |
| return_material_unit | owner_input_required |
| return_labor_unit | owner_input_required |
| ral_material_price_rule | owner_input_required |
| ral_labor_price_rule | owner_input_required |
| separate_calculation_allowed | confirmed |
| pricing_status | blocked_until_owner_decision |

Paths cross-reference existing mapping where available (`return_depth` → `product.components.return_cant.depth`, etc.); new fields marked `proposed_workshop`.

## What remains unknown (needs owner)

- Oracal code list and per-code pricing
- RAL input mode (free text vs selector) and standard list
- Standard cant depths (30/60/80 mm?)
- Cant materials and depth-specific treatment
- Material/labor units (ml/mp/buc/set)
- RAL material and labor price rules for 30 mm / 60 mm
- FINISH vs RETURN-CANT overlap for RAL
- FACE/BACK/LED/MOUNTING skeleton answers

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/features/product-system/legacyToComponentFirstReplacementMap.test.ts src/features/product-system/componentFirstLettersProductTruthWorkshop.test.ts src/pages/ProductSystem.badges.test.tsx
# 118/118 PASS

$env:PW_SKIP_WEB_SERVER='1'; $env:PW_BASE_URL='http://127.0.0.1:3000'; npm.cmd run test:e2e:product-system-readonly-smoke
# 1/1 PASS
```

## Screenshots

`docs/qa/component-first-letters-product-truth-workshop-v1/screenshots/01`–`10_*.png`

## Final verdict

**PASS** — readonly owner workshop contract delivered; RETURN-CANT detailed; no forbidden scope touched.

## Next owner questions (priority)

1. Oracal list + same/different pricing
2. RAL selector vs free text
3. Standard cant depths and materials
4. Material/labor units for cant
5. RAL material + labor rules for 30/60 mm
