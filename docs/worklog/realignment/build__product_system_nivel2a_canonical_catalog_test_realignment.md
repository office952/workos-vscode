# Build — Nivel 2A: Canonical Catalog Test Realignment + Internal Naming Audit

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Verdict** | **PASS** |
| **Parent** | Nivel 1B — [`build__product_template_modules_nivel1b_consistency.md`](./build__product_template_modules_nivel1b_consistency.md) |
| **Forbidden (respected)** | DB rename, `module_template_*`, migrations, Aggregate/PD/CPP/EIC/pricing/formulas, legacy functional cleanup, SVG/DWG, architectural rewrite |

---

## Verdict

**PASS**

`ProductSystem.badges.test.tsx` no longer asserts the legacy unified-bucket catalog. Tests match live `ProductSystemCanonicalCatalog` behavior. Safe UI/docs leftovers cleaned. `ComponentFirst*` / `component-first-*` remaining mass inventaried for Nivel 2B. Zero functional / storage changes.

---

## Cat suntem in directia stabilita

**94/100%**

| Layer | Score | Note |
|-------|------:|------|
| Operator-visible vocabulary | 96% | Safe leftovers cleared (`Template componenta`, RO copy) |
| Test ↔ live UI alignment | 95% | Badges suite on CanonicalCatalog + panel contract |
| Internal IDs / filenames `ComponentFirst*` | 35% | Nivel 2B |
| DB/API `module_template_*` | 0% rename | Nivel 3 |

---

## What changed

### 1. Test realignment (`ProductSystem.badges.test.tsx`)

| Before | After |
|--------|--------|
| `product-system-unified-row-*` + bucket expand | Canonical cards `[data-testid=product-system-canonical-catalog-card][data-template-code=…]` |
| Filter chips `product-system-filter-*` | `product-system-canonical-filter-*` |
| Synthetic candidate-set catalog row | **Removed** — not on CanonicalCatalog |
| Candidate panel via bucket click | Controlled `ComponentFirstReadonlyCandidatePanel` `variant="detail-panel"` (same component UnifiedCatalog used) |
| Editor open via row action | Detail → Dossier tab → `product-system-template-detail-open-editor` |
| Legacy bucket banner / toggle | Legacy Module produs → Internal filter → Guards → `LegacyReplacementReadinessPanel` |
| Summary-bar component-first metrics | Assert **absent** on CanonicalCatalog page |

Added:

- `ProductSystemShellProvider` + mocked `useCurrentPermissions` (`can → true`) so Advanced filters / open-editor match admin path.
- Smoke: CanonicalCatalog deprecated filter → composer → editor → panel visible.
- Fixture: composer `is_parent: true` (catalog eligibility); family labels → Module produs vocabulary.

### 2. Safe UI/docs (Nivel 2A)

| File | Change |
|------|--------|
| `TemplateLibraryView.tsx` | Column „Template componenta” → **Module produs** |
| `ProductSystemTemplateDetailPanel.tsx` | „component-first” helper copy → Module produs set |
| `lettersFinishMountingOwnership.ts` | „child templates” → Module produs (child Product Template) |
| `productSystemCanonicalModel.ts` | meaningRo candidate set → Module produs |

---

## Naming inventory (classification)

### Changed now (test-only / UI-docs)

- Badges helpers, fixtures, catalog assertions
- Visible leftover strings listed above
- Fixture `family_name` for candidate composer

### Intentional keep (negation / guards)

- Canonical dictionary / Control Center: „Nu folosi eticheta Component Template / Module Template”
- Vocabulary tests that `not.toMatch(/Component Template/)`

### Nivel 2B — code / internal ID (do not rename in 2A)

| Cluster | Examples |
|---------|----------|
| Filenames / symbols | `ComponentFirstReadonly*.tsx`, `componentFirstReadonly*.ts`, `legacyToComponentFirstReplacementMap.ts` |
| Bucket / entry IDs | `component-first-sets`, `candidate-set:component-first-letters` |
| Testids | `product-system-component-first-*`, filter/bucket ids still used by dead UnifiedCatalog |
| Internal enums | `sourceType: "component template"`, display-mapped already |
| Dead surface (not live) | `ProductSystemUnifiedCatalog.tsx` still has legacy buckets — retire/rename with 2B |

### Nivel 3 — DB/API

- All `module_template_*` / `*_module_template_code` / `component_template_code` wire fields
- No table rename inventat

---

## Acceptance check

| Criterion | Result |
|-----------|--------|
| Badges tests do not require legacy bucket catalog | **PASS** |
| Tests reflect CanonicalCatalog live behavior | **PASS** |
| No functional / formula / Aggregate / pricing changes | **PASS** |
| Remaining ComponentFirst inventaried | **PASS** |
| Worklog created | **PASS** |

---

## Files touched (2A focus)

- `frontend/src/pages/ProductSystem.badges.test.tsx` (primary)
- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/lib/lettersFinishMountingOwnership.ts`
- `frontend/src/lib/productSystemCanonicalModel.ts`
- this worklog

*(Working tree may still include Nivel 1 / 1B label files from the same branch — not re-scoped here.)*

---

## Tests run

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/pages/ProductSystem.badges.test.tsx `
  src/features/product-system/productTemplateModulesVocabulary.test.ts `
  src/features/product-system/TemplateLibraryView.test.tsx `
  src/lib/productSystemCanonicalModel.test.ts `
  src/features/product-system/productSystemCanonicalCatalog.test.ts `
  src/features/product-system/productSystemHonestyShell.test.ts
```

**Result:** 6 files, **86 passed** (including **51/51** badges).

---

## Ce intră în Nivel 2B

1. Rename `ComponentFirst*` modules / symbols / testids → Module-produs naming (mechanical FE + tests + capture scripts).
2. Rename catalog bucket id `component-first-sets` (and consumers).
3. Decide fate of unused `ProductSystemUnifiedCatalog` (delete or quarantine).
4. Optional path rename `/product-system/components` (id stays; label already Module produs).

## Ce rămâne Nivel 3

- `module_template_*` DB/API field renames + migrations + Intake consumers.

---

## Boundary

- No migrations / schema
- No `module_template_*` renames
- No CPP / EIC / ProductDefinition / ProductAggregate / Pricing Registry behavior changes
- No SVG/DWG / legacy functional cleanup
