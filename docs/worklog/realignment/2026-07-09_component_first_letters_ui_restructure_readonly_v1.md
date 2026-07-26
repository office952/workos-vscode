# Component-first Letters UI Restructure (Readonly) v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-09 |
| **Task** | COMPONENT_FIRST_LETTERS_UI_RESTRUCTURE_READONLY_V1 |
| **Scope** | Frontend layout only — reorganize component-first readonly UI |

## Purpose

Transform the component-first letters readonly UI from a vertical stack of audit panels into a tabbed candidate section separated from the existing Product System catalog.

## HEAD

| | Commit |
|---|--------|
| **Before (task gate)** | `2f1aad9` (specified) / `7e6ff32` (actual working HEAD) |
| **After** | _(filled at commit)_ |

## Files touched

- `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx` — new tabbed candidate UI
- `frontend/src/features/product-system/componentFirstReadonlySetModel.ts` — extracted set model builders from page
- `frontend/src/pages/ProductSystem.tsx` — catalog separation (Overview / Candidate Sets / Existing Roots)
- `frontend/src/pages/ProductSystem.badges.test.tsx` — updated + new structure tests

## UI structure

1. **Catalog Overview** — orientation copy
2. **Candidate Sets** — tabbed `Component-first Letters Candidate` panel
3. **Existing Roots** — `TemplateLibraryView` including TPL-VOLUMETRIC-LETTERS_v2

Candidate tabs: Overview | Components | Dossier | Form System | Product Truth | Guards / Audit

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

**Result:** 92 passed (62 + 30)

## UI verification

- URL: http://127.0.0.1:3000/product-system
- Screenshots: `docs/audit/component-first-ui-restructure-v1/*.png`

## Forbidden scope check

| Item | Touched |
|------|---------|
| seed / DB / backend / activation / pricing / quote / order / execution | NO |
| ProductDefinition runtime wiring | NO |
| TPL-VOLUMETRIC-LETTERS_v2 semantic change | NO |

## Honest limitations

- In-page tabs only (no new route) — deep-linking to a tab not supported yet
- Dependency graph collapsed under Guards / Audit `<details>`
- HEAD gate specified `2f1aad9`; implementation based on successor `7e6ff32` (ProductDefinition readiness already present)

## Next recommended slice

- Deep-link query param for candidate tab (`?candidateTab=dossier`)
- Optional Figma alignment pass for tab visual hierarchy
- Consider moving candidate panel to dedicated route only if catalog page remains crowded
