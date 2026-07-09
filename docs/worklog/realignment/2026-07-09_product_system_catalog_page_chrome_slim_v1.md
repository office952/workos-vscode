# Product System catalog page chrome slim v1

**Date:** 2026-07-09  
**Task:** PRODUCT_SYSTEM_CATALOG_PAGE_CHROME_SLIM_V1 (follow-up to compact layout audit)  
**Scope:** Frontend-only. No backend, DB, seed, activation, or catalog logic changes.

## Changes

### Page header (library view)
- Single-row slim header: back arrow + title + SourceBadge | reload icon + Info + more menu + Șablon Nou
- Blueprint Dossier moved into overflow menu
- Overview line under header (testId preserved)
- Fixed Romanian encoding on library strings (Șablon, Reîncarcă, șabloane)

### Catalog toolbar
- Filter chips in horizontal scroll strip (`product-system-unified-filter-chips-scroll`) — single line
- Narrower search field beside chips

### Catalog rows
- Secondary actions (Settings, Dossier, Components, Guards) in ··· overflow menu
- Single-line row: badges + Open + overflow
- Primary Open remains visible; all action testIds preserved

## Files

- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/features/product-system/ProductSystemUnifiedCatalog.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`

## Validation

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

**Result:** 97/97 PASS

## Screenshots

`docs/qa/product-system-catalog-page-chrome-slim-2026-07-09/screenshots/`
