# Product System — Legacy → Component-first Replacement Map v1

## HEAD before

`8076348` — Add Product System readonly Playwright smoke

## Scope

Read-only frontend contract + UI for legacy template deprecation readiness:

- Static replacement map (`legacyToComponentFirstReplacementMap.ts`)
- Legacy replacement readiness panel (Guards for legacy modules; Guards/Audit for component-first)
- Legacy bucket clarity (collapsed description, expanded banner, view replacement map)
- Component-first “Ce înlocuiește component-first?” context
- Unit + Playwright tests
- QA screenshots

**Out of scope (respected):** backend, DB, seed, migration, activation, Pricing, ProductDefinition runtime, Quote/Order/Execution, Work Intake exposure, delete/cleanup.

## Audit notes (read-only)

| Area | Location |
|------|----------|
| Legacy templates | Unified catalog bucket `legacy-shared-modules` via `buildUnifiedCatalogEntries.ts` + availability `internal_module` / `internal_modules` |
| Component-first | `ComponentFirstReadonlyCandidatePanel.tsx`, `componentFirstReadonlySetModel.ts`, composer `TPL-LETTERS-COMPOSER_v1` |
| Unified catalog | `ProductSystemUnifiedCatalog.tsx`, `productSystemUnifiedCatalogTypes.ts` |
| Legacy bucket | Default collapsed; internal modules from API |
| Existing tests | `ProductSystem.badges.test.tsx`, `componentFirstReadonlyCompleteness.test.ts`, `product-system-readonly-smoke.spec.ts` |

## Files changed

- `frontend/src/features/product-system/legacyToComponentFirstReplacementMap.ts` — contract + summary helpers
- `frontend/src/features/product-system/legacyToComponentFirstReplacementMap.test.ts`
- `frontend/src/features/product-system/LegacyReplacementReadinessPanel.tsx`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/ProductSystemUnifiedCatalog.tsx`
- `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx`
- `frontend/src/features/product-system/productSystemUnifiedCatalogTypes.ts`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/e2e/product-system-readonly-smoke.spec.ts`
- `frontend/scripts/capture-product-system-legacy-replacement-screenshots.mjs`
- `docs/qa/product-system-legacy-replacement-map-v1/screenshots/` (10 PNGs)

## Mapping summary

7 contract entries; all `canDeleteNow: false`; global verdict `not_ready_for_delete`.

| Legacy | Replacement | Status |
|--------|-------------|--------|
| TPL-VOLUMETRIC-FACE_v1 | TPL-COMP-LETTER-FACE_v1 | BLOCKED |
| TPL-VOLUMETRIC-BACK_v1 | TPL-COMP-LETTER-BACK_v1 | BLOCKED |
| TPL-VOLUMETRIC-LED_v1 | TPL-COMP-LETTER-LED_v1 | BLOCKED |
| TPL-VOLUM-ALUMINIU_v1 | TPL-COMP-LETTER-RETURN-CANT_v1 | PARTIAL |
| TPL-VOLUMETRIC-FINISH_v1 | TPL-COMP-LETTER-FINISH_v1 | PARTIAL |
| TPL-METAL-PREMOUNT-STRUCTURE_v1 | TPL-COMP-LETTER-MOUNTING_v1 | BLOCKED |
| TPL-VOLUMETRIC-LETTERS_v1 | TPL-LETTERS-COMPOSER_v1 | KEEP FOR HISTORY |

Unmapped legacy codes resolve via `resolveLegacyReplacementEntry()` → OWNER DECISION.

## Decisions

- UI lives in existing Guards sections — no new top-level tabs.
- Legacy bucket “View replacement map” selects FACE legacy row + opens Guards with full table.
- Wording: readonly mapping, no delete now, NOT READY FOR DELETE; never “migrated/activated/live”.
- `TPL-VOLUMETRIC-LETTERS_v2` untouched; composer/LOGO not activated.

## What remains blocked

- Component truth not confirmed end-to-end
- ProductDefinition / Pricing not consuming component truth
- Active root still uses legacy composition
- Historical Quote/Order snapshots
- Owner GO for cutover / overlap (FINISH vs FACE/RETURN-CANT)
- Runtime activation for component-first (0/7 live rows in fallback fixtures)

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/features/product-system/legacyToComponentFirstReplacementMap.test.ts src/pages/ProductSystem.badges.test.tsx
# 106/106 PASS

$env:PW_SKIP_WEB_SERVER='1'; $env:PW_BASE_URL='http://127.0.0.1:3000'; npm.cmd run test:e2e:product-system-readonly-smoke
# 1/1 PASS
```

## Screenshots

`docs/qa/product-system-legacy-replacement-map-v1/screenshots/01`–`10_*.png`

## Final verdict

**PASS** — controlled read-only replacement map delivered; no forbidden scope touched.

## Next recommended slices

1. **Legacy bucket scale readiness** — search/filter UX when module count > 20 (virtualized list).
2. **Component-first Product Truth contract** — confirm truth ownership per component before deprecation plan.
3. **Product System frontend surface cleanup** — unused shells (`TemplateLibraryView`) audit.
