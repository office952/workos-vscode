# Product System bucketed catalog compact layout v1

**Date:** 2026-07-09  
**Task:** PRODUCT_SYSTEM_BUCKETED_CATALOG_COMPACT_LAYOUT_V1  
**Scope:** Frontend-only compact layout. No backend, DB, seed, activation, or classification logic changes.

## Changes

### Top area
- Catalog overview → single line (`product-system-catalog-overview`)
- Summary stat cards → inline horizontal strip inside compact toolbar
- Search + filters merged into one toolbar row (`product-system-compact-toolbar`)
- Page header tightened (smaller icon/title, subtitle removed on library view)
- `space-y-4` → `space-y-2`; master-detail grid starts immediately after toolbar

### Bucket styling
- Removed thick colored left borders and tinted bucket headers
- Neutral `border-slate-800/70` buckets with small lifecycle dot only
- Compact bucket headers (`py-1`, 11px title, count on right)

### Rows
- Reduced padding; metadata removed from list rows (shown in detail panel via `rowMetadata`)
- Actions on one compact row; primary Open + secondary link-style actions

### Detail panel
- Aligned with bucket list top; reduced padding; sticky `top-2`
- Overview bullets / guards readiness moved into `<details>` collapsibles
- Component-first detail-panel header compacted

## Files

- `frontend/src/features/product-system/ProductSystemUnifiedCatalog.tsx`
- `frontend/src/features/product-system/productSystemUnifiedCatalogTypes.ts`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`

## Validation

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

**Result:** 96/96 PASS

## Screenshots

`docs/qa/product-system-bucketed-catalog-compact-layout-2026-07-09/screenshots/`

Capture:

```powershell
cd frontend
node scripts/capture-product-system-bucketed-catalog-compact-layout-screenshots.mjs
```
