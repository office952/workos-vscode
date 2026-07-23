# Build — Nivel 2B: Internal Naming Cleanup (`ComponentFirst*` → Candidate Module produs)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Verdict** | **PASS** |
| **Parent** | Nivel 2A — [`build__product_system_nivel2a_canonical_catalog_test_realignment.md`](./build__product_system_nivel2a_canonical_catalog_test_realignment.md) |
| **Branch** | `feature/product-system-active-path-isolation-v1` |
| **Forbidden (respected)** | DB rename, `module_template_*` field rename, migrations, Aggregate / ProductDefinition / CPP / EIC / pricing / formulas, legacy functional cleanup, SVG/DWG, architectural rewrite, feature expansion under reference freeze |

---

## Verdict

**PASS**

Internal FE naming for the candidate Module produs surface is aligned with operator vocabulary. Dead `ProductSystemUnifiedCatalog` removed. Vitest cluster green (**247**). Live stack reused (healthy) with Dev Mode on. Runtime screenshots under `audit_assets/20_nivel2b_*`. Zero DB / formula / Aggregate / CPP / EIC changes.

---

## Cat suntem in directia stabilita

**97–98/100%**

| Layer | Score | Note |
|-------|------:|------|
| Operator-visible vocabulary | 98% | Products + Module produs tab/label; CanonicalCatalog live |
| Test ↔ live UI alignment | 97% | Badges + candidateModuleProdus* + CanonicalCatalog + smoke e2e realigned |
| Internal IDs / filenames `ComponentFirst*` | 97% | Mass rename done; dead UnifiedCatalog deleted |
| Route path `/product-system/components` | 90% | Label = Module produs; path id kept (optional, non-blocking) |
| DB/API `module_template_*` | 0% rename | Nivel 3 only |

---

## Scope

### In

1. Rename `ComponentFirst*` / `componentFirst*` modules, symbols, testids, capture scripts → Candidate Module produs naming.
2. Rename catalog entry types (`productSystemUnifiedCatalogTypes` → `productSystemCatalogEntries`) and replacement map (`legacyToCandidateModuleReplacementMap`).
3. Delete unused `ProductSystemUnifiedCatalog.tsx` (staged `D`).
4. Keep badges suite / CanonicalCatalog alignment from 2A; fix duplicate `CANDIDATE_MODULE_TAB` if present.
5. Runtime proof + screenshots + this worklog.

### Out / forbidden (respected)

- No migrations / schema
- No `module_template_*` / `*_module_template_code` / `component_template_code` wire renames
- No CPP / EIC / ProductDefinition / ProductAggregate / Pricing Registry behavior
- No SVG/DWG / Analyzer / offer-Execution expansion
- No inventing parallel Product System features under reference freeze

---

## What cleaned vs intentional leftovers

### Cleaned (2B)

| Cluster | Before → After |
|---------|----------------|
| Panels / sheets | `ComponentFirstReadonly*` → `CandidateModuleProdus*` |
| Readonly / workshop modules | `componentFirstReadonly*` / workshops → `candidateModuleProdus*` |
| Replacement map | `legacyToComponentFirstReplacementMap` → `legacyToCandidateModuleReplacementMap` |
| Catalog entry types | `productSystemUnifiedCatalogTypes` → `productSystemCatalogEntries` |
| Dead surface | `ProductSystemUnifiedCatalog.tsx` **deleted** |
| Capture scripts | `capture-component-first-*` → `capture-candidate-module-produs-*` (+ consumers updated) |
| E2E smoke | `product-system-readonly-smoke.spec.ts` → CanonicalCatalog selectors |

Working-tree check after 2B: **no** remaining `ComponentFirst*` / `componentFirst*` files under `frontend/src`.

### Intentional leftovers (not defects)

| Keep | Why |
|------|-----|
| Negation copy „Nu folosi eticheta Component Template / Module Template” | Canonical dictionary / Control Center — forbids old label |
| Vocabulary tests `not.toMatch(/Component Template/)` | Guard against regression |
| Template codes `TPL-COMP-*` | Stable product identity codes (Letters FACE/LED/…) — **not** UI type labels |
| Wire fields `module_template_*` / `shared_module_template_code` | API/DB contract — **Nivel 3** |
| Route path `/product-system/components` | Path id; operator label already **Module produs**; optional rename deferred |

---

## Files / clusters touched

### Rename cluster (git `R` / `RM`)

- `CandidateModuleProdusPanel.tsx` (+ SettingsSheet, TruthWorkshopPanel)
- `candidateModuleProdusReadonly*.ts(x)` (+ completeness tests)
- `candidateModuleProdusFace*` / `Finish*` / `Letters*` / `ReturnCant*` workshops & drafts
- `legacyToCandidateModuleReplacementMap.ts` (+ test)
- `productSystemCatalogEntries.ts` (from unified catalog types)

### Delete

- `ProductSystemUnifiedCatalog.tsx` (staged delete)
- Obsolete `capture-component-first-*` / unified-catalog capture scripts (replaced)

### Consumers / shell / pages

- `ProductSystem.tsx`, `ProductSystemCatalogShell.tsx`, `ProductSystemCanonicalCatalog.tsx`
- `ProductSystemTemplateDetailPanel.tsx`, `TemplateLibraryView.tsx` (+ test)
- `LegacyReplacementReadinessPanel.tsx`, Face/Finish/ReturnCant panels
- `productSystemShellConfig.ts`, `productSystemCatalogShellTypes.ts`
- `App.tsx` (routing consumers as needed)
- `frontend/e2e/product-system-readonly-smoke.spec.ts`
- Capture scripts under `frontend/scripts/`

### Evidence (this pass)

- `frontend/scripts/capture-product-system-nivel2b-screenshots.mjs`
- `docs/worklog/realignment/audit_assets/20_nivel2b_*.png`
- this worklog

---

## Tests

Parent session (naming + Vitest; do not re-run as gate here):

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/pages/ProductSystem.badges.test.tsx `
  src/features/product-system/candidateModuleProdus*.test.ts `
  src/features/product-system/candidateModuleProdus*.test.tsx `
  src/features/product-system/productTemplateModulesVocabulary.test.ts `
  src/features/product-system/productSystemCanonicalCatalog.test.ts `
  src/features/product-system/TemplateLibraryView.test.tsx `
  src/features/product-system/legacyToCandidateModuleReplacementMap.test.ts `
  src/lib/productSystemCanonicalModel.test.ts
```

**Result:** 15 files / **247 passed** (ProductSystem.badges + candidateModuleProdus* + vocabulary + canonical catalog + TemplateLibrary + model + replacement map).

---

## Runtime

| Item | Value |
|------|-------|
| Backend | `http://127.0.0.1:8000` — health `healthy`, local-compatibility `COMPATIBLE` |
| Frontend | `http://127.0.0.1:3000` — HTTP 200 |
| Dev Mode | **ON** — `VITE_ENABLE_DEV_AUTH=true`, backend `dev_auth_allowed` |
| Ownership | PIDs on :3000/:8000 are this repo (`C:\w\psiso` vite + uvicorn); stack **reused**, not killed/restarted |
| Blockers | None |

`npm run diag:local-listeners` confirmed ports occupied by WorkOS stack before screenshots.

---

## Screenshots

| File | Route / surface |
|------|-----------------|
| [`audit_assets/20_nivel2b_products_catalog.png`](./audit_assets/20_nivel2b_products_catalog.png) | `/product-system/products` — CanonicalCatalog |
| [`audit_assets/20_nivel2b_product_template_detail.png`](./audit_assets/20_nivel2b_product_template_detail.png) | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` — detail panel |
| [`audit_assets/20_nivel2b_components.png`](./audit_assets/20_nivel2b_components.png) | `/product-system/components` — Module produs planned section |
| [`audit_assets/20_nivel2b_modules_concepts.png`](./audit_assets/20_nivel2b_modules_concepts.png) | `/modules` — Module Chain concepts |

Capture: `frontend/scripts/capture-product-system-nivel2b-screenshots.mjs` (Playwright chromium, headless).

---

## Honest UI opinion (short)

Canonical Products catalog reads clean: **Module produs** tab label, no “Component Template” product type in chrome. Letters detail still shows honest lifecycle/readiness chips. `/product-system/components` correctly stays a non-operational placeholder — good that naming did not fake a live Module produs browser. Remaining visual debt is structural (planned section + Advanced catalog density), not 2B naming.

---

## Acceptance check

| Criterion | Result |
|-----------|--------|
| `ComponentFirst*` mass rename complete in FE source | **PASS** |
| `ProductSystemUnifiedCatalog` removed | **PASS** (staged `D`) |
| No DB / `module_template_*` / formulas / Aggregate / CPP / EIC | **PASS** |
| Vitest 247 (parent session) | **PASS** |
| Runtime + Dev Mode proven | **PASS** |
| Screenshots + worklog | **PASS** |

---

## Ce rămâne Nivel 3

1. DB/API field renames: `module_template_*`, `shared_module_template_code`, `component_template_code` (+ migrations + Intake consumers).
2. Optional route id rename `/product-system/components` → vocabulary-aligned path (label already Module produs).
3. Any remaining historical docs / compound-engineering dossiers that still say ComponentFirst in prose (evidence archives — do not rewrite history blindly).

---

## Boundary

- Reference freeze: naming / evidence / test realignment only
- Root locked: `C:\w\psiso`
- No commit in this pass unless owner asks
