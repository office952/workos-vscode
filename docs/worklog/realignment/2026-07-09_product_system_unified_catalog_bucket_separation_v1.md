# Product System unified catalog bucket separation v1

**Task:** PRODUCT_SYSTEM_UNIFIED_CATALOG_BUCKET_SEPARATION_V1  
**Date:** 2026-07-09  
**Scope:** Frontend-only catalog presentation — group unified list into lifecycle buckets with clear labels.

## HEAD

| | Hash | Message |
|---|---|---|
| Before | `0eb5088` | Replace Product System tab shell with unified catalog |
| After | _(this commit)_ | Group Product System catalog by lifecycle buckets |

## What changed

- Replaced flat unified results list with 5 lifecycle buckets (fixed order, collapsible).
- Bucket assignment uses existing availability roles + `productTemplateScopePresentation` codes (no backend changes).
- Clear labels per task: LETTERS active root, LOGO candidate, component-first set, legacy modules, archived.
- Filters updated: Current products, Candidate products, Component-first sets, Legacy modules, Archived, Blocked.
- Default view: Current / Candidate / Component-first expanded; Legacy + Archived collapsed.
- LETTERS_v2 auto-selected on load when present.
- Detail panel bucket-aware copy (active root vs candidate vs legacy module).
- Row actions adapted: Open readonly / Open module / View parent usage where applicable.

## Files touched

| File | Change |
|---|---|
| `frontend/src/features/product-system/productSystemUnifiedCatalogTypes.ts` | Bucket + filter types |
| `frontend/src/features/product-system/buildUnifiedCatalogEntries.ts` | Bucket assignment + labels |
| `frontend/src/features/product-system/ProductSystemUnifiedCatalog.tsx` | Bucket sections UI |
| `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx` | Bucket-specific detail copy |
| `frontend/src/pages/ProductSystem.badges.test.tsx` | Bucket + label tests |
| `frontend/scripts/capture-product-system-unified-catalog-buckets-screenshots.mjs` | Screenshot capture |
| `docs/qa/product-system-unified-catalog-buckets-2026-07-09/screenshots/` | UI verification |

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

**Result:** 95/95 PASS

## UI verification

- **URL:** http://127.0.0.1:3000/product-system
- **Screenshots:** `docs/qa/product-system-unified-catalog-buckets-2026-07-09/screenshots/`
  - `01_default_bucketed_catalog_view.png`
  - `02_current_products_bucket_letters_v2.png`
  - `03_candidate_products_bucket.png` (when LOGO in live DB)
  - `04_component_first_candidate_sets_bucket.png`
  - `05_component_first_detail_composer_and_components.png`
  - `06_legacy_shared_modules_collapsed.png`
  - `07_legacy_shared_modules_expanded.png`
  - `08_letters_detail_current_active_root.png`
  - `09_logo_detail_not_work_intake_owner_go.png` (when LOGO in live DB)
  - `10_proof_bucketed_not_flat_mixed_list.png`

## Forbidden scope check

| Item | Status |
|---|---|
| Backend / DB / seed / migration | NO |
| Activation / Work Intake / Pricing / Quote / Order / Execution | NO |
| ProductDefinition / ProductAggregate runtime | NO |

## Honest limitations

- Bucket assignment is frontend presentation logic mirroring availability API — not a new backend taxonomy.
- Live DB may omit LOGO or some legacy modules; bucket sections hide when empty.
- Legacy module parent usage is summary text from availability, not a full composition graph.
- 100 products / 600 modules still need virtualisation within buckets.

## Next recommended slice

1. Virtualised rows inside each bucket for scale.
2. Per-bucket counts on filter chips.
3. “View parent usage” deep-link from legacy module row to parent product detail without opening editor.
