# Product System IA Shell — Existing Roots Separation v1

**Date:** 2026-07-09  
**Task:** PRODUCT_SYSTEM_IA_SHELL_EXISTING_ROOTS_SEPARATION_V1  
**Slice:** 1 — navigation/layout only

## Scope

Replace vertical stack (Catalog Overview → Candidate Sets → Existing Roots) with a scalable top-level tab shell:

- Products (default)
- Components
- Candidate Sets
- Dossiers (readonly placeholder)
- Guards / Audit (readonly placeholder)
- Archived

Add top summary bar with catalog counts derived from existing availability data.

## HEAD

- **Before:** `79c1b54` — Polish component first card UI and drawer QA
- **After:** (commit on main)

## Files touched

- `frontend/src/features/product-system/ProductSystemCatalogShell.tsx` — new shell: summary bar, primary tabs, tab panels
- `frontend/src/features/product-system/productSystemCatalogShellTypes.ts` — primary tab ids/types
- `frontend/src/features/product-system/TemplateLibraryView.tsx` — optional `shellContextLabel`, `restrictCatalogView`
- `frontend/src/pages/ProductSystem.tsx` — wire shell, default Products tab
- `frontend/src/pages/ProductSystem.badges.test.tsx` — IA shell tests + tab navigation helpers
- `frontend/scripts/capture-product-system-ia-shell-screenshots.mjs` — screenshot capture
- `docs/qa/product-system-ia-shell-2026-07-09/screenshots/` — UI verification
- `docs/qa/product-system-ia-shell-2026-07-09/screenshots_index.md`

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

**Result:** 94/94 PASS (62 completeness + 32 badges)

## UI verification

URL: http://127.0.0.1:3000/product-system

Screenshots: `docs/qa/product-system-ia-shell-2026-07-09/screenshots/`

## Forbidden scope check

- No backend / DB / seed / migration
- No activation, Work Intake, Pricing, Quote, Order, Execution
- No ProductDefinition / ProductAggregate / TaskGraph runtime
- Component-first candidate logic unchanged (readonly, inactive, not offerable)

## Honest limitations

- No search/pagination/virtualization (Slice 3)
- Compact card rows + visible legacy Open/Settings not yet done (Slice 2)
- Dossiers and Guards tabs are readonly placeholders with pointers to Candidate Sets detail
- Products tab still uses TemplateLibraryView internal sub-tabs (Overview/Produse/Componente…) — contextualized with “Active catalog roots / existing templates” label
- Summary blocked count uses `owner_decision_required` from availability API when present

## Honest UI opinion

- **More scalable:** Yes — one surface per tab; Existing Roots no longer stacks under candidates
- **Products vs Candidate Sets:** Clearer via primary tabs
- **TPL-VOLUMETRIC-LETTERS_v2:** One click (Products default) + scroll; still inside nested catalog sub-tabs
- **Candidate detail:** Still easy — Candidate Sets tab → View candidate readonly
- **New confusion:** Two tab layers on Products (primary + TemplateLibraryView sub-tabs) — acceptable for Slice 1, reduce in Slice 2
- **100 products / 600 modules:** Still needs compact list/table + pagination (Slices 2–3)

## Next recommended slice

**Slice 2:** Compact scalable catalog rows + visible Open / Settings / Dossier on legacy cards; demote hero cards to detail-only.
