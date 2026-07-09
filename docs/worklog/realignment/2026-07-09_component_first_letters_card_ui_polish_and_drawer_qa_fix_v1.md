# Component-first Letters Card UI Polish + Drawer QA Fix v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-09 |
| **Task** | COMPONENT_FIRST_LETTERS_CARD_UI_POLISH_AND_DRAWER_QA_FIX_V1 |
| **Scope** | Frontend UI polish + screenshot QA proof only |

## Purpose

Address owner QA PARTIAL findings: visual density alignment with legacy Product System cards, readonly drawer proof, dossier focus highlight, legacy comparison screenshot.

## HEAD

| | Commit |
|---|--------|
| **Before (task gate)** | `b33ec3b` Add component first card based readonly UI |
| **After** | _(filled at commit)_ |

## Files touched

- `frontend/src/features/product-system/componentFirstReadonlyUiShared.tsx` — readonly drawer banner, status chips, card footer pattern
- `frontend/src/features/product-system/ComponentFirstReadonlySettingsSheet.tsx` — persistent READONLY · NO SAVE · NO WRITE header banner
- `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx` — product/component card polish, dossier focus stays on tab with highlight label
- `frontend/src/pages/ProductSystem.badges.test.tsx` — drawer banner + dossier focus tests
- `frontend/scripts/capture-component-first-card-ui-polish-screenshots.mjs` — drawer wait + viewport capture + legacy card
- `docs/qa/component-first-card-ui-polish-2026-07-09/` — verification screenshots

## Changes

1. **Drawer proof** — banner `READONLY · NO SAVE · NO WRITE` in Product/Component Settings sheet header; capture script waits for sheet + banner and screenshots drawer element
2. **Card polish** — legacy-like icon + title hierarchy, compact chips, footer actions, collapsible audit details on component cards
3. **Product composer hero** — type badge, NOT OFFERABLE chips, semantic label, metrics line, details collapsible
4. **Dossier focus** — View dossier / Focus component keeps Dossier tab; focused card gets ring + “Focused dossier” label + `data-focused="true"`
5. **Legacy comparison** — screenshot of `TPL-VOLUMETRIC-LETTERS_v2` full card via Existing Roots → Produse

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

**Result:** 93/93 PASS

## UI verification

- URL: http://127.0.0.1:3000/product-system
- Screenshots: `docs/qa/component-first-card-ui-polish-2026-07-09/screenshots/`

## Forbidden scope check

All forbidden items: **NO** (frontend UI/tests/docs only)

## Honest limitations

- Visual parity with legacy cards improved but not pixel-identical (candidate cards remain denser than offerable roots)
- Form System / Product Truth tabs still duplicate some settings drawer content
- Sheet UI chrome still resembles editable panels despite banner

## Next recommended slice

- Optional query-param deep link for candidate tab
- Further spacing/icon tuning against TemplateLibraryView compact mode
- Consider linking Form System / Product Truth tabs from settings instead of parallel full panels
