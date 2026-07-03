# BUILD — Docs: Material Canonical Naming and Aliases

**Date:** 2026-06-09  
**Type:** Documentation only  
**Runtime:** Not touched

---

## Scope

Document canonical material naming rules and accepted production aliases so WorkOS can avoid duplicate Inventory/Pricing rows while remaining compatible with real shop-floor language (bond, forex, stiplex, țeavă 30×30, Oracal 651).

Based on read-only audit **Material Naming & Alias Registry** (2026-06-09).

---

## Audit source

| Item | Detail |
|------|--------|
| **Build name** | Material Naming & Alias Registry Audit |
| **Mode** | Read-only — no file modifications |
| **Verdict** | Duplicate naming risk: **yes (partial)** |
| **Main risk zones** | ACM/ACP/Dibond/Alucobond/Bond; Forex vs PVC expandat; Plexiglas vs PMMA/acril; vinyl generic vs Oracal serie; profil vs țeavă/bară; usage baked into material name |
| **Existing mitigations** | Category/subcategory policy; quote-time resolvers (ACM bond thickness, volumetric profile/PSU); Color Registry brand+serie for Oracal |
| **Gap** | No `material_family`, `canonical_name`, or `aliases` on `inventory_materials`; no general deduplication or alias search |

---

## Documents created

| Path | Action | Purpose |
|------|--------|---------|
| `docs/architecture/MATERIAL_CANONICAL_NAMING_AND_ALIASES.md` | **Created** | Canonical naming table, brand vs generic, Inventory/Pricing/Template boundary, desired search behavior, no-schema and future-schema paths |
| `docs/qa/BUILD_DOCS_MATERIAL_CANONICAL_NAMING_AND_ALIASES.md` | **Created** | This QA record |

---

## Runtime not touched

Confirmed for this build:

- No frontend changes
- No backend changes
- No CostEngine / ProductSystem changes
- No seed / mock / Inventory / Pricing data changes
- No alias table or search implementation
- No tests run (docs-only build)

Validation: `git status --short` and `git diff --name-only` must list **only** documentation paths under `docs/`.

---

## Decisions documented

| Topic | Decision |
|-------|----------|
| **Canonical name** | Technical, neutral, family-first — not brand unless SKU is supplier-specific |
| **Aliases** | Popular/commercial terms (bond, forex, stiplex, țeavă, oracal 651) accepted for search — not separate SKUs for same physical stock |
| **Brand / serie** | Oracal, Dibond, Alucobond, Forex, Plexiglas stored separately from generic material family |
| **ACM identity** | Total thickness + aluminum foil thickness + finish = distinct SKUs (aligns with mounting/structure boundary doc) |
| **PVC expandat** | Canonical family; Forex = alias/brand |
| **PMMA** | Canonical; Plexiglas/Stiplex/acril = aliases |
| **Steel profile** | Complete identity = shape + dimensions + wall thickness; usage (premount) = tag, not name |
| **Inventory vs usage** | Inventory = physical material; Template/CostEngine = usage and quantity |
| **Product 001 crosswalk** | Remains documentation-only — not runtime aliases |
| **This build** | Docs only — no migration, no runtime |

---

## Follow-up builds recommended

### 1. Inventory / Pricing naming cleanup

- Deduplicate seeds: e.g. `MAT-ACP-3MM` vs `MAT-ACM-BOND-3MM`
- Rename `name` fields toward canonical pattern (keep `code` stable or migrate with owner approval)
- Retire composite names „ACP / Dibond / Alucobond” on single rows where one canonical SKU suffices
- Split ACM rows by foil thickness per boundary doc SKU pattern
- Align `MAT-ORACAL-651` vs `MAT_ORACAL_651` namespaces
- Rename usage-heavy names (e.g. premount bar → țeavă pătrată oțel + usage tag)

### 2. Material alias / search support

- Static then DB-backed alias map
- Search: canonical_name + aliases + brand + series + technical_specs
- Admin create: „similar material exists” warning
- Display: canonical title + alias chips + brand badge

### 3. Material metadata / schema design

- Add `material_family`, `canonical_name`, `aliases`, `brand`, `series`, `technical_specs`, `usage_tags`
- `equivalent_to` / `replacement_for` for supplier variants
- Migration plan from current `name` + `category` + `source_notes`

---

## Validation checklist

- [x] Architecture doc includes all required sections (Purpose through Stop condition)
- [x] Canonical table covers ACM, PVC expandat, PMMA, folie, oțel, aluminiu
- [x] Brand vs generic table includes Oracal, Dibond, Alucobond, Forex, Plexiglas, Stiplex, Komatex, Acrylon, bond, ACP/ACM
- [x] Repo findings synthesized from audit
- [x] Search behavior documented as desired future state (not implemented)
- [x] Stop condition explicit: no runtime change in this build

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-09 | Initial QA record for material canonical naming docs |
