# 2026-07-23 — Nivel 1: Product Template → Modules (labels only)

| Field | Value |
|-------|-------|
| **Status** | DONE |
| **Type** | UI / docs / API-display vocabulary only |
| **Parent audit** | [`audit__product_system_to_offer_calculation_simplification.md`](./audit__product_system_to_offer_calculation_simplification.md) §8A |
| **Forbidden (respected)** | DB rename, `module_template_*` field rename, migrations, formulas, CPP/EIC, ProductAggregate semantics, legacy cleanup, SVG/DWG |

---

## Owner decision implemented

Keep storage:

- `product_templates`
- `product_template_module_links`

Simplify vocabulary:

| Old UI label | New UI label |
|--------------|--------------|
| Module Template | **Module** / Module produs |
| Component Template (as separate type) | **Module produs** |
| Child PT + links | **Module produs** |
| Mini-module | **Mini-modul operațional** (kept separate) |
| Face / cant / back as nested template classes | **Module produs egale** |

---

## Files changed

### Vocabulary source

- `frontend/src/features/product-system/productTemplateModulesVocabulary.ts` (new)
- `frontend/src/features/product-system/productTemplateModulesVocabulary.test.ts` (new)

### Product System UI

- `frontend/src/pages/ProductSystem.tsx` — ownership / composition / shared foundation help + source-type display mapper
- `frontend/src/features/product-system/componentFirstReadonlyUiShared.tsx`
- `frontend/src/features/product-system/buildUnifiedCatalogEntries.ts`
- `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx`
- `frontend/src/features/product-system/ComponentFirstReadonlySettingsSheet.tsx`
- `frontend/src/features/product-system/legacyToComponentFirstReplacementMap.ts`
- `frontend/src/features/product-system/componentFirstLettersProductTruthWorkshop.ts`
- `frontend/src/features/product-system/LegacyReplacementReadinessPanel.tsx`
- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts` (note copy)
- `frontend/src/features/product-system/TemplateLibraryView.tsx` — tab/chip „Module produs”

### Canonical / Control Center docs-in-UI

- `frontend/src/lib/productSystemCanonicalModel.ts`
- `frontend/src/lib/currentTruthControlCenter.ts`
- `frontend/src/pages/ModuleChain.tsx`

### Tests

- `frontend/src/pages/ModuleChain.test.tsx`
- `frontend/src/features/product-system/TemplateLibraryView.test.tsx` (aligned to Module produs + current RO status chips)

---

## What was NOT changed

- No DB columns / migrations
- No API field renames (`module_template_code`, `*_module_template_code`, `component_template_code` keys remain)
- No CPP / EIC / ProductDefinition / ProductAggregate behavior
- No pricing / formulas
- Internal TS discriminator `"component template / registry"` kept where used for className switches; **display** uses `displayModuleSourceTypeLabel()` → `module / registry`

---

## Verification

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/features/product-system/productTemplateModulesVocabulary.test.ts `
  src/pages/ModuleChain.test.tsx `
  src/features/product-system/TemplateLibraryView.test.tsx
```

**Result:** 3 files, **25 passed**.

---

## Screenshot / runtime proof

| Asset | Note |
|-------|------|
| Vitest vocabulary assertions | PASS — no „Component Template” / „Module Template” in semantic label |
| ModuleChain concept node | Asserts `Module (product)` + `Operational mini-module` |
| [`audit_assets/07_nivel1_product_system_modules_produs.png`](./audit_assets/07_nivel1_product_system_modules_produs.png) | Product System catalog (Playwright) |
| [`audit_assets/08_nivel1_product_template_detail.png`](./audit_assets/08_nivel1_product_template_detail.png) | Template detail (Playwright) |
| [`audit_assets/09_nivel1_module_chain_concepts.png`](./audit_assets/09_nivel1_module_chain_concepts.png) | Harta/ModuleChain — **Module produs** + **Mini-modul operațional** confirmed in page text |

Recommended manual check (operator/admin):

1. `/product-system/products` → tab **Module produs**
2. Product detail ownership panel → „Module calculation ownership” / „Owner boundary: Module produs”
3. Harta sistemelor → concept **Module produs**, **Mini-modul operațional**

---

## Acceptance checklist

| Criterion | Status |
|-----------|--------|
| No artificial Component/Module Template hierarchy in UI | **PASS** |
| Product Template is primary level | **PASS** |
| Under it: Module produs | **PASS** |
| Față / cant/volum / spate as equal modules | **PASS** (labels + hint) |
| Mini-module clearly operational | **PASS** |
| Worklog + tests | **PASS** |
| Screenshots | **PASS** (Playwright assets 07–09; map page text-verified) |

---

## Next (not in this GO)

Nivel 2 owner GO: deprecate remaining internal discriminator tokens / API display DTO polish without DB rename.

Nivel 3: `module_template_*` rename — blocked.
