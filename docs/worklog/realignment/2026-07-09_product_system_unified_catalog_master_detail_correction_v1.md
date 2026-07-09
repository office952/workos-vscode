# Product System unified catalog master-detail correction v1

**Task:** PRODUCT_SYSTEM_UNIFIED_CATALOG_MASTER_DETAIL_CORRECTION_V1  
**Date:** 2026-07-09  
**Scope:** Frontend-only IA correction — replace tab-first shell with unified catalog + filter chips + master-detail.

## HEAD

| | Hash | Message |
|---|---|---|
| Before | `3be9c72` | Separate Product System IA shell tabs |
| After | _(this commit)_ | Replace Product System tab shell with unified catalog |

## What changed

- Removed 6 top-level primary tabs (Products / Components / Candidate Sets / Dossiers / Guards / Archived) from the library screen.
- Added unified catalog surface: compact summary, global search, filter chips, compact results list, master-detail panel.
- `TPL-VOLUMETRIC-LETTERS_v2` appears in unified list without Products → Produse sub-tab hopping.
- Component-first Letters Candidate is a single unified row; detail panel uses 4 sections (Overview / Components / Dossier / Guards). Form System + Product Truth folded into Guards.
- Dossier and Guards accessed via row text actions and detail panel — no empty global tabs.
- Removed permanent “Existing Roots” block; active roots are catalog rows with lifecycle labels.
- Row actions remain visible as text: Open, Settings, Dossier, Components, Guards.

## Files touched

| File | Change |
|---|---|
| `frontend/src/features/product-system/ProductSystemUnifiedCatalog.tsx` | New unified catalog UI |
| `frontend/src/features/product-system/productSystemUnifiedCatalogTypes.ts` | Filter/entry types |
| `frontend/src/features/product-system/buildUnifiedCatalogEntries.ts` | List builder + filters |
| `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx` | Template master-detail sections |
| `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx` | `detail-panel` variant, 4 tabs, guards fold |
| `frontend/src/pages/ProductSystem.tsx` | Wire unified catalog; remove shell wiring |
| `frontend/src/pages/ProductSystem.badges.test.tsx` | Unified catalog assertions |
| `frontend/scripts/capture-product-system-unified-catalog-screenshots.mjs` | Screenshot capture |
| `docs/qa/product-system-unified-catalog-2026-07-09/screenshots/` | UI verification (10 images) |

`ProductSystemCatalogShell.tsx` remains in repo but is no longer mounted on the library screen.

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

**Result:** 94/94 PASS

## UI verification

- **URL:** http://127.0.0.1:3000/product-system
- **Screenshots:** `docs/qa/product-system-unified-catalog-2026-07-09/screenshots/`
  - `01_unified_catalog_search_filter_list.png`
  - `02_unified_list_tpl_volumetric_letters_v2.png`
  - `03_unified_list_component_first_candidate.png`
  - `04_selected_tpl_volumetric_detail_panel.png`
  - `05_selected_candidate_detail_panel.png`
  - `06_candidate_detail_components_table.png`
  - `07_candidate_detail_dossier.png`
  - `08_candidate_detail_guards.png`
  - `09_proof_no_six_top_level_tabs.png`
  - `10_proof_no_existing_roots_bottom_block.png`

## Forbidden scope check

| Item | Status |
|---|---|
| Backend / DB / seed / migration | NO |
| Activation / promote / Work Intake exposure | NO |
| Pricing / Quote / Order / Execution | NO |
| ProductDefinition / ProductAggregate runtime | NO |
| TaskGraph / ExecutionPlan | NO |

## Honest limitations

- Template detail panel is read-only summary (composition/dossier/guards placeholders); full editor still via **Open**.
- At 100 products / 600 modules, list needs virtualisation, column sort, and richer row metadata — not in this slice.
- `ProductSystemCatalogShell` + `TemplateLibraryView` sub-tab model still exist as dead code paths; safe delete is a follow-up cleanup slice.
- Filter chip counts on summary bar are aggregate hints, not live per-chip counts.

## Next recommended slice

1. Virtualised unified list + sticky filter bar for scale.
2. Remove unused `ProductSystemCatalogShell` / library sub-tab dead code after one release window.
3. Enrich template detail panel with real composition/dossier read models (readonly) without opening editor.
