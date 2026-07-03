# BUILD — Material Registry Consolidation (static taxonomy + naming hints)

**Date:** 2026-06-09  
**Type:** Frontend static library + non-blocking admin UI hints + docs  
**DB / schema:** Not touched  
**CostEngine:** Not touched

---

## Scope

Non-destructive foundation for a mature Material Registry:

1. Static canonical material families + aliases + brand/series + usage warning terms.
2. Analysis helpers (normalize, family match, brand match, usage warnings, suggestions).
3. Non-blocking hints in Material Price Registry edit drawer (`Denumire` field).
4. Unit + component tests.
5. Architecture doc cross-reference update.

**Not in scope:** DB migration, seed rename, CostEngine formulas, material_code breakage, TPL-STRUCTURA-LITERE, push/commit (pending owner confirmation).

---

## Audit source

- `docs/architecture/MATERIAL_CANONICAL_NAMING_AND_ALIASES.md`
- `docs/qa/BUILD_DOCS_MATERIAL_CANONICAL_NAMING_AND_ALIASES.md`
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_MOUNTING_STRUCTURE_BOUNDARY.md`
- Read-only Material Naming & Alias Registry audit (2026-06-09)

---

## Implemented artifacts

| Path | Purpose |
|------|---------|
| `frontend/src/lib/materials/materialCanonicalTaxonomy.ts` | 8 material families, aliases, brands, series, usage terms, SKU patterns |
| `frontend/src/lib/materials/materialCanonicalAnalysis.ts` | `normalizeMaterialSearchTerm`, `findMaterialFamilyMatches`, `findBrandTermMatches`, `findUsageTermWarnings`, `getCanonicalMaterialSuggestion` |
| `frontend/src/lib/materials/MaterialNamingHints.tsx` | Non-blocking hint panel for registry edit form |
| `frontend/src/pages/MaterialPriceRegistry.tsx` | Wire hints under `Denumire` in `EditDrawer` |
| `frontend/src/lib/materials/materialCanonicalAnalysis.test.ts` | Required term mapping cases |
| `frontend/src/lib/materials/MaterialNamingHints.test.tsx` | Render tests for hint panel |
| `docs/architecture/MATERIAL_CANONICAL_NAMING_AND_ALIASES.md` | Updated §8 with implementation reference |

---

## Runtime boundaries

| Area | Changed? |
|------|----------|
| DB / Alembic | No |
| Backend APIs | No |
| CostEngine formulas | No |
| Pricing calculations | No |
| Existing `material_code` values | No rename/delete |
| Seeds | No |
| Save behavior in registry | Unchanged — hints do not block save |

---

## Families covered

1. Panou compozit aluminiu (ACM/ACP)
2. PVC expandat
3. PMMA / plexiglas acrilic
4. Folie autocolantă PVC
5. Țeavă / profil oțel
6. Profil aluminiu
7. Policarbonat
8. Consumabile montaj

---

## Tests

```bash
cd frontend
npx vitest run src/lib/materials/materialCanonicalAnalysis.test.ts src/lib/materials/MaterialNamingHints.test.tsx
npx tsc -b --noEmit
npx eslint --quiet src/lib/materials src/pages/MaterialPriceRegistry.tsx
```

---

## Follow-up builds

1. **Inventory / Pricing naming cleanup** — seed dedup, canonical `name` migration plan, `MAT-PREMOUNT-BAR-STEEL` → target `MAT-STEEL-SQUARE-TUBE-*` with stable code aliases in CostEngine
2. **Material alias / search support** — extend search bar in registry; duplicate-material guard on create
3. **Material metadata / schema** — `material_family`, `canonical_name`, `aliases`, `brand`, `series`, `usage_tags` columns

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-09 | Initial BUILD record for static taxonomy + naming hints |
