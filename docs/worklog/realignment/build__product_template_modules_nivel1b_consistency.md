# Build — Nivel 1B: Product Template → Module produs Consistency Audit + UI Cleanup

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Verdict** | **PASS_WITH_WARNINGS** |
| **Parent** | Nivel 1 DONE — [`2026-07-23_product_template_modules_nivel1_labels.md`](./2026-07-23_product_template_modules_nivel1_labels.md) |
| **Audit context** | [`audit__product_system_to_offer_calculation_simplification.md`](./audit__product_system_to_offer_calculation_simplification.md) §8A |
| **Forbidden (respected)** | DB rename, `module_template_*` field rename, migrations, formulas, CPP/EIC, ProductAggregate semantics, Pricing Registry logic, legacy functional cleanup, SVG/DWG |

---

## Verdict

**PASS_WITH_WARNINGS**

UI/docs vocabulary for **Product Template → Module produs egale** is consistent on live operator surfaces. Mini-modul operațional remains explicitly separate. No functional / storage / formula changes.

Warnings:

1. `ProductSystem.badges.test.tsx` still targets legacy unified-bucket catalog (`product-system-catalog-bucket-component-first-sets`). Live page uses `ProductSystemCanonicalCatalog` — suite fails for structural reasons **pre-existing vs catalog variant**, not label regressions. Deferred to Nivel 2 test realignment.
2. Internal IDs / file names / bucket ids still use `component-first-*` (code-only).
3. Control Center / canonical dictionary keep **negation** copy that *mentions* „Component Template” / „Module Template” to forbid them — intentional, not a product hierarchy.

---

## Cat suntem in directia stabilita

**90/100%** (vocabular UI + docs operator vizibile)

| Layer | Score | Note |
|-------|------:|------|
| Storage model (`product_templates` + links) | 100% | Already matched target before Nivel 1 |
| Operator-visible labels (Product System / ModuleChain / Template library) | 92% | Residual: intentional negation notes; internal IDs |
| Internal code / testids / file names | 40% | Nivel 2 |
| DB/API field names `module_template_*` | 0% rename | Nivel 3 only (by design) |

---

## Files touched (Nivel 1 + 1B working tree)

### Vocabulary / UI

- `frontend/src/features/product-system/productTemplateModulesVocabulary.ts` (+ test)
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/features/product-system/ProductSystemCatalogShell.tsx`
- `frontend/src/features/product-system/productSystemCatalogShellTypes.ts`
- `frontend/src/features/product-system/productSystemShellConfig.ts`
- `frontend/src/features/product-system/ProductSystemPlannedSectionPage.tsx`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/ProductE2EReadinessPanel.tsx`
- `frontend/src/features/product-system/TemplateLibraryView.tsx` (+ test)
- `frontend/src/features/product-system/buildUnifiedCatalogEntries.ts`
- `frontend/src/features/product-system/productSystemUnifiedCatalogTypes.ts`
- `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx`
- `frontend/src/features/product-system/ComponentFirstReadonlySettingsSheet.tsx`
- `frontend/src/features/product-system/componentFirstReadonlyUiShared.tsx`
- `frontend/src/features/product-system/LegacyReplacementReadinessPanel.tsx`
- `frontend/src/features/product-system/legacyToComponentFirstReplacementMap.ts`
- `frontend/src/features/product-system/componentFirstLettersProductTruthWorkshop.ts`
- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`
- `frontend/src/lib/productSystemCanonicalModel.ts`
- `frontend/src/lib/currentTruthControlCenter.ts`
- `frontend/src/pages/ModuleChain.tsx` (+ test)
- `frontend/src/pages/ProductSystem.badges.test.tsx` (expectation string only)

### Adjacent (same working tree, not 1B scope)

- `frontend/src/App.tsx` — removed missing `WorkIntakeProductDefinitionDemo` import (boot restore)

### Worklog / proof

- this file
- screenshots under `docs/worklog/realignment/audit_assets/`

---

## Labels found → decision

| Finding | Decision | Action |
|---------|----------|--------|
| UI „Component Template” / „Module Template” as hierarchy | Change now | Replaced with **Module produs** / Product Template composer |
| „Component-first Letters Candidate” panel title | Change now | **Candidate Module produs — Litere** |
| „Component templates / shared modules” | Change now | **Module produs / Module partajate** |
| Shell nav / planned section „Components” | Change now | **Module produs** |
| Primary tab „Candidate Sets” | Change now | **Seturi Module produs** |
| Summary metric „Components” | Change now | **Module produs** |
| Helper / empty / ownership notes „child template” | Change now | **Module produs** (child Product Template where needed) |
| Face / cant / volum / spate as nested template classes | Change now | Explicit **Module produs egale** |
| „Mini-modul” without operational | Change now | **Mini-modul operațional** |
| Canonical / Control Center negation of old labels | Keep intentional | Documents what *not* to say |
| Bucket id `component-first-sets`, testids `product-system-component-first-*` | Internal / code-only | Nivel 2 GO |
| File names `ComponentFirst*` | Internal / code-only | Nivel 2 GO |
| API/DB `module_template_*`, `component_template_code` keys | Keep | Nivel 3 DB/API rename GO |
| Backend readiness message „Required child template …” | Keep (API message) | Nivel 2/3 display mapping if desired |
| Historical audit / older worklogs | Keep | Evidence; do not rewrite history |
| `ProductSystem.badges.test` catalog-bucket helpers | Needs Nivel 2 | Align tests to CanonicalCatalog |

---

## Acceptance check

| Criterion | Result |
|-----------|--------|
| Product Template = singurul nivel vizibil de template | **PASS** |
| Sub el apar Module produs egale | **PASS** |
| Față / cant / volum / spate nu ca sub-template speciale | **PASS** (help + composition copy) |
| Mini-modul operațional clar separat | **PASS** |
| Fără schimbări funcționale / DB / formulas | **PASS** |
| Worklog + screenshots + teste | **PASS** (cu warning pe badges suite) |

---

## Labels rămase intenționat

1. Internal discriminators: `"component template"`, `"component template / registry"` (display via `displayModuleSourceTypeLabel`).
2. Bucket / filter / testid ids: `component-first-sets`, `product-system-component-first-*`.
3. File / symbol names: `ComponentFirst*`, `isComponentFirstLettersTemplate`, etc.
4. Field keys: `component_template_code`, `*_module_template_code` (storage truth).
5. Negation prose in `productSystemCanonicalModel` / Control Center: „Nu folosi eticheta Component Template / Module Template”.
6. Test fixture `family_name: "Litere component-first candidate"` in badges mock data (API-shaped fixture; suite currently blocked by catalog variant).

---

## Ce necesită Nivel 2

- Rename internal bucket ids / testids / primary-tab ids away from `component-first` / `components` where user-facing routes allow (`/product-system/components` path rename is optional UX).
- Realign `ProductSystem.badges.test.tsx` to `ProductSystemCanonicalCatalog` (or restore dual catalog only under feature flag — prefer test update).
- Optional FE display mapping for backend strings containing „child template”.
- File renames `ComponentFirst*` → Module-produs naming (mechanical, large diff).

## Ce necesită Nivel 3

- DB/API rename of `module_template_*` / related keys (migrations, consumers, freeze gate).

---

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/features/product-system/productTemplateModulesVocabulary.test.ts `
  src/pages/ModuleChain.test.tsx `
  src/features/product-system/TemplateLibraryView.test.tsx `
  src/lib/productSystemCanonicalModel.test.ts `
  src/features/product-system/productSystemHonestyShell.test.ts
```

**Result:** 5 files, **32 passed**.

| Suite | Result |
|-------|--------|
| Vocabulary + ModuleChain + TemplateLibrary + CanonicalModel + HonestyShell | **32 passed** |
| `ProductSystem.badges.test.tsx` | **WARN** — fails opening legacy component-first bucket; CanonicalCatalog has no that bucket. Not a label regression. |

No DB / backend pytest required (labels-only).

---

## Screenshot paths

| Asset | Proof |
|-------|--------|
| [`audit_assets/10_nivel1b_product_system_catalog.png`](./audit_assets/10_nivel1b_product_system_catalog.png) | Catalog — 0× „Component Template” / „Module Template”; Module produs present |
| [`audit_assets/11_nivel1b_modules_produs_view.png`](./audit_assets/11_nivel1b_modules_produs_view.png) | Shell nav **Module produs** planned section |
| [`audit_assets/12_nivel1b_product_template_detail.png`](./audit_assets/12_nivel1b_product_template_detail.png) | Product Template detail |
| [`audit_assets/13_nivel1b_module_chain_concepts.png`](./audit_assets/13_nivel1b_module_chain_concepts.png) | ModuleChain — Module produs + Mini-modul operațional; only intentional negation of old labels |
| Nivel 1 prior | `07`–`09_nivel1_*.png` |

Runtime OCR/text scan (Playwright, live `:3000`):

- `/product-system/products`: Component Template = 0, Module Template = 0, Module produs ≥ 2
- `/modules`: Component/Module Template appear only inside forbidden-label negation sentence

---

## Boundary respected

- No migrations / schema changes
- No `module_template_*` renames
- No CPP / EIC / Aggregate / Pricing Registry behavior changes
- No legacy functional cleanup
- No SVG/DWG work
