# Component-first Letters Card-Based UI Restructure (Readonly) v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-09 |
| **Task** | COMPONENT_FIRST_LETTERS_CARD_BASED_UI_RESTRUCTURE_READONLY_V1 |
| **Scope** | Frontend readonly UI — card-based candidate presentation |

## Purpose

Transform the component-first letters readonly Candidate UI into a card-based layout aligned with legacy Product System patterns: candidate set card, product/composer card, six component cards, readonly settings drawers, dedicated dossier workspace, and isolated Guards/Audit.

## HEAD

| | Commit |
|---|--------|
| **Before (task gate)** | `8ac103e` Organize component first readonly Product System UI |
| **After** | _(filled at commit)_ |

## Files touched

- `frontend/src/features/product-system/componentFirstReadonlyUiShared.tsx` — status strip, semantic label, card shell, readonly link buttons
- `frontend/src/features/product-system/ComponentFirstReadonlySettingsSheet.tsx` — readonly Product/Component Settings drawer
- `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx` — card-based catalog + detail (overview, components, dossier, guards)
- `frontend/src/pages/ProductSystem.tsx` — editor panel uses inline variant
- `frontend/src/pages/ProductSystem.badges.test.tsx` — card UI tests + catalog open helper
- `frontend/scripts/capture-component-first-card-ui-screenshots.mjs` — QA screenshot helper
- `docs/qa/component-first-card-ui-restructure-2026-07-09/` — browser verification screenshots

## UI structure

1. **Candidate Set Card** (catalog) — compact card with semantic label `1 Product Composer + 6 Component Templates`, status chips, readonly action
2. **Overview** — status strip → Product Composer card → compact owner review → forbidden summary
3. **Components** — composer hero + grid of exactly 6 component cards (not 7)
4. **Product Settings drawer** — readonly sections: Overview, Composition, Dossier, Form System readiness, Product Truth mapping, Guards
5. **Component Settings drawer** — readonly per-component sections
6. **Dossier workspace** — composer dossier card + 6 component dossier cards + focus actions
7. **Guards/Audit** — completeness, drift, ProductDefinition readiness, collapsed dependency graph
8. **Existing Roots** — unchanged separation from Candidate Sets

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

**Result:** 93 passed (62 + 31)

Added/updated coverage:

- Candidate set card + semantic label
- Product composer card (not counted as component)
- Six component cards with settings/dossier actions
- Product + component settings drawers (Face, LED)
- Dossier workspace (1 composer + 6 component cards)
- No activate/promote/quote/Work Intake buttons in candidate context
- Dangerous wording absent in candidate panel

## UI verification

- URL: http://127.0.0.1:3000/product-system
- Screenshots: `docs/qa/component-first-card-ui-restructure-2026-07-09/screenshots/`
- Index: `docs/qa/component-first-card-ui-restructure-2026-07-09/screenshots_index.md`

## Forbidden scope check

| Item | Touched |
|------|---------|
| seed live / seed_sync_all | NO |
| migration / DB write | NO |
| backend / ProductDefinition builder | NO |
| activation / promote / writer path | NO |
| Pricing / Quote / Order / Execution | NO |
| Work Intake exposure | NO |
| ProductAggregate / TaskGraph / ExecutionPlan | NO |
| component root / quote / Logo activation | NO |
| TPL-VOLUMETRIC-LETTERS_v2 semantic change | NO |
| Product Truth write / confirmed values | NO |

## Honest limitations

- Settings drawers are read-only Sheet panels, not full parity with legacy Product System editor chrome
- Dossier focus action switches tab/highlight; no dedicated dossier route yet
- Component cards show Product Truth prefix summary, not full path tables (detail in settings + Product Truth tab)
- Catalog mode requires explicit “View candidate readonly” to expand detail (intentional separation)
- Some audit enums remain verbose in Guards/Audit; Overview shows one-line drift/completeness summary only

## Honest UI opinion (post-build)

- **Composer vs components:** Clear — semantic label and separate cards prevent counting composer as a component
- **Settings entry:** Clear via “View product settings” / “View component settings” on cards
- **Dossier:** Improved — dedicated workspace with distinct composer card; still dense
- **Card parity with legacy Product System:** Partial — structure matches, visual density and spacing differ
- **Activation risk:** Low — status chips and forbidden strips are always visible; Existing Roots wording for v2 remains separate
- **Next slice:** Visual polish (card spacing/icons), deep-link `?candidateTab=`, optional Figma alignment pass

## Next recommended slice

- Query-param deep link for candidate tab
- Figma design-system alignment for card hierarchy
- Consider extracting candidate detail to sub-route if catalog page grows further
