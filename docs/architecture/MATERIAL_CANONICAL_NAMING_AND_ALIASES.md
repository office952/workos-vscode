# Material Canonical Naming and Aliases

**Date:** 2026-06-09  
**Status:** Architecture reference (documentation only — no runtime change)  
**Audience:** Product owner, Inventory/Pricing operators, Cursor agents, developers  
**Related audits:**

- Read-only audit **Material Naming & Alias Registry** (2026-06-09) — repo-wide term inventory
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_MOUNTING_STRUCTURE_BOUNDARY.md` — ACM/ACP identity and structural profile expectations
- `docs/qa/BUILD_DOCS_MOUNTING_STRUCTURE_BOUNDARY.md` — QA record for mounting/structure boundary docs

---

## 1. Purpose

WorkOS must use a **canonical material identity** so that:

1. **Inventory** does not accumulate duplicate rows for the same physical stock (e.g. “ACM 3 mm”, “Dibond 3 mm”, “Alucobond 3 mm”, “Bond 3 mm” as four separate materials).
2. **Pricing** applies one standardized offer price per canonical material (or per complete technical variant), not per popular name.
3. **ProductSystem / CostEngine** reference stable `material_code` values while operators and production staff continue to search and speak using **real production language** (bond, forex, stiplex, țeavă 30×30, Oracal 651).

This document defines:

- canonical naming rules;
- accepted aliases per material family;
- separation of **generic material** vs **brand/series** vs **product usage**;
- boundaries between Inventory, Pricing, and Template/CostEngine;
- desired future search/alias behavior (not implemented in this build).

**This build does not change runtime, seeds, or database schema.**

---

## 2. Core rule

### 2.1 Three layers — do not mix them in `name`

| Layer | What it is | Example |
|-------|------------|---------|
| **Inventory** | Physical material that exists in stock | Țeavă pătrată oțel 30×30×1.5 mm |
| **Pricing** | Standardized acquisition/offer unit cost for quoting | 2 EUR/ml for that profile (registry row) |
| **Template / CostEngine** | How the material is **used** in a product | Bare premontaj litere, structură suport, cadru, ramă |

**Wrong** (usage baked into material name):

- `Bare premontaj litere 30×30×1.5`
- `Spate litere Forex 10 mm` as the **only** identity (without canonical PVC expandat underneath)
- `ACP față litere` as a synonym for generic ACM panel stock

**Correct**:

| Layer | Value |
|-------|-------|
| Material brut (canonical) | **Țeavă pătrată oțel 30×30×1.5 mm** |
| Utilizare (usage tag / template role) | bare premontaj litere / structură suport / cadru / ramă |
| Registry code (stable) | e.g. `MAT-STRUCT-BAR-STEEL-30X30X1_5` (target pattern; today `MAT-PREMOUNT-BAR-STEEL` names usage) |

### 2.2 Naming principle

- **Canonical name** = technical, neutral, family-first — **not** a brand unless the SKU is explicitly supplier-specific.
- **Aliases** = popular/commercial terms accepted in search and operator input.
- **Brand / series** = separate attributes (Oracal 651, Dibond, Forex).
- **Usage tags** = where the material appears in production (premount, letter_face, letter_back, casetting, print) — **never** the material’s primary identity.

---

## 3. Canonical naming table

| Familie material | Denumire canonică WorkOS | Aliasuri acceptate | Brand/serie separat | Note |
|------------------|--------------------------|--------------------|---------------------|------|
| **Panou compozit aluminiu** | Panou compozit aluminiu (ACM/ACP) | ACM, ACP, Dibond, Alucobond, bond, panou bond, aluminiu compozit, material compozit aluminiu | Dibond, Alucobond = brand/denumire comercială | Identitatea completă include **grosime totală** + **grosime foi aluminiu** + **finisaj** + format/furnizor. Exemplu SKU țintă: `MAT-ACM-3MM-ALU0_30-WHITE`. ACM 3 mm alu 0.21 ≠ ACM 3 mm alu 0.30. |
| **PVC expandat** | PVC expandat | Forex, PVC, placă PVC, foam PVC, PVC expandat | Forex, Komatex (dacă apare în producție) | Forex este **alias/brand popular**, nu familia materialului. Cod istoric `MAT-SPATE-PVC-LITERE` poate rămâne; display alias „Forex 10 mm”. |
| **PMMA / acrilic** | PMMA / plexiglas acrilic | Plexiglas, plexi, acril, acrilic, PMMA, Stiplex | Plexiglas, Acrylon, Stiplex = brand/denumire comercială | Opal / difuzor / transparent = **variante tehnice/finisaj**, nu materiale separate dacă același stoc. |
| **Folie autocolantă PVC** | Folie autocolantă PVC | folie, autocolant, vinyl, sticker, print vinyl, autocolant print | **Oracal** = brand; **641 / 651 / 8500** = serie | Oracal este brand/serie, nu orice autocolant. Generic vinyl (`MAT-VINYL-*`) și Oracal (`MAT-ORACAL-651`) sunt roluri diferite în registry. |
| **Profile / țevi oțel** | Țeavă / profil oțel | țeavă, teava, profil, bară, bara, rectangular, pătrat, patrat, rotund, cornier, platbandă, oțel, otel | — | Profil complet = **formă + dimensiuni + grosime perete** (ex. 30×30×1.5). SVG poate da lungime + latură vizibilă; grosimea peretelui vine din registry/operator. |
| **Profile aluminiu** | Profil aluminiu | profil AL, aluminiu, profil structural aluminiu, profil ramă, profil casetă, profil textil/banner, profil literă volumetrică | — | Profil complet = formă + dimensiuni + grosime perete. Utilizarea (cant literă, cadru casetă, ramă banner) = **usage tag**, nu nume material. |
| **Policarbonat** (unde distinct de PMMA) | Policarbonat | policarbonat, PC | — | Difuzor opal poate fi PMMA sau policarbonat — separă doar dacă stocul fizic diferă. |
| **Consumabile montaj** | Consumabile montaj (generic) | adeziv, silicon, suruburi, prinderi, bandă, capse | Brand furnizor opțional | Nu confunda cu profil structural sau panou. |

---

## 4. Brand vs material generic

| Termen | Material generic asociat | Tip termen | Cum se modelează |
|--------|--------------------------|------------|------------------|
| **Oracal** | Folie autocolantă PVC | Brand + serie (641, 651, 8500) | `brand=Oracal`, `series=651`; culoare în Color Registry (`ORACAL,651,010`), nu în `name` Inventory |
| **Dibond** | Panou compozit aluminiu (ACM/ACP) | Brand / denumire comercială | `brand=Dibond` pe SKU sau notă furnizor; `canonical_name` neutru |
| **Alucobond** | Panou compozit aluminiu (ACM/ACP) | Brand / denumire comercială | Idem Dibond; supplier „Alucobond RO” = furnizor |
| **Forex** | PVC expandat | Brand / denumire comercială | `brand=Forex`; alias în search; cod `MAT-SPATE-PVC-*` = compatibilitate runtime |
| **Plexiglas** | PMMA / plexiglas acrilic | Brand / denumire comercială | `canonical_name` PMMA; Plexiglas = alias |
| **Stiplex** | PMMA / plexiglas acrilic | Denumire populară (RO) | Alias — **nu apare în repo azi**; acceptat în producție |
| **Komatex** | PVC expandat | Brand | Alias — **nu apare în repo azi** |
| **Acrylon** | PMMA / plexiglas acrilic | Brand | Alias / brand opțional |
| **bond** | Panou compozit aluminiu (ACM/ACP) | Sinonim popular | Alias search; nu SKU separat „bond” |
| **ACP / ACM** | Panou compozit aluminiu | Sinonim tehnic/comercial | Un singur `material_family`; nu două familii paralele |

**Rule:** A brand name must not become the only `name` in Inventory if the stock is fungible across brands with identical technical specs. Supplier-specific SKUs are allowed when purchase cost or format genuinely differs.

---

## 5. Existing repo findings

Synthesis from the read-only **Material Naming & Alias Registry** audit (2026-06-09):

### 5.1 Duplicate / confusion risks confirmed

| Risk | Evidence in repo |
|------|------------------|
| **ACM / ACP / Dibond / Alucobond / Bond** | **Preferred/canonical:** `MAT-ACM-BOND-3MM`. `MAT-ACP-3MM` = legacy alias (not a second technical/pricing option; no destructive migration). `MAT-ACM-BOND-PANEL` = thickness resolver alias. Names like „Panou ACM / Bond / Dibond 3 mm”; mock `MAT-001` „ACP / Dibond 3mm alb” |
| **Forex vs PVC expandat** | `MAT-SPATE-PVC-LITERE` (code PVC, name „Forex 10 mm”); category `forex`; mock `MAT-003` „PVC expandat 5mm alb” |
| **Plexiglas vs PMMA / acril** | Seeds use „Plexiglas” only (`MAT-PLEXI-*`); templates/intake say „plexi/acrilic” — no PMMA in registry `name` |
| **Oracal code namespace** | `MAT-ORACAL-651` (BUILD 4) vs `MAT_ORACAL_651` (Product 001 BOM, underscore codes) |
| **Material named by usage** | `MAT-PREMOUNT-BAR-STEEL` „Bare pătrate oțel 30×30×1.5 mm **premontaj**” — usage in name |
| **Composite brand+synonym names** | Seeds and mock data combine „ACP / Dibond”, „ACM / Alucobond / Dibond” in single `name` strings |
| **Face vs panel ACM** | `MAT-ACP-FATA-LITERE` „ACP / aluminiu față litere” — product role, not generic ACM panel stock |

### 5.2 What exists today (mitigations, not full registry)

| Mechanism | Scope | Limitation |
|-----------|-------|------------|
| **Category policy** (`inventory_materials_governance.py`, `MaterialPriceRegistry.tsx`) | UI canonical categories: Plăci, Profile metalice, Folii, … | Heuristic keyword inference; **no** material deduplication |
| **Recommended subcategories** | e.g. „ACM / Alucobond / Dibond”, „Forex”, „Oracal 651” | Display grouping only |
| **Quote-time resolvers** | `acm_bond_material_rate_resolver.py` — `MAT-ACM-BOND-PANEL` → 3/4 mm variant | ACM templates only |
| | `volumetric_material_rate_resolver.py` — profile depth, PSU watts | Volumetric letters only |
| **Product 001 crosswalk** | `PRODUCT_001_TO_VOLUMETRIC_CROSSWALK` in seed | Explicitly **not runtime aliases** |
| **Color Registry** | `ORACAL` brand + series 651/8500 + usage_tags | Separate from Inventory material rows |

### 5.3 What does not exist

- No `material_family`, `canonical_name`, or `aliases` columns on `inventory_materials`.
- No general alias table or search normalizer across Inventory.
- No admin guard „similar material already exists” on create.
- No automatic merge of Dibond/ACM/Bond into one SKU.

---

## 6. Inventory / Pricing / Template boundary

### 6.1 Inventory

**Purpose:** Record **physical material** that can be stocked, purchased, and consumed.

| Field (current + target) | Role |
|--------------------------|------|
| `code` | Stable identifier for CostEngine references (`MAT-*`) |
| `canonical_name` (target) | Neutral technical name shown in UI |
| `name` (today) | Should migrate toward canonical; avoid brand+synonym stacks |
| `material_family` (target) | ACM, PMMA, PVC_EXPANDED, VINYL_CAST, STEEL_TUBE_RECT, ALU_PROFILE, … |
| `unit` | mp, ml, buc, set — physical measure |
| `category` / `subcategory` | Governance taxonomy (Plăci → ACM / Alucobond / Dibond) |
| Format / sheet specs | `sheet_width`, `sheet_height`, `sheet_thickness`, … |
| `supplier` / `supplier_sku` (target) | Who we buy from — not material identity |
| `unit_cost` | Acquisition cost — **not** commercial markup |
| `technical_specs` (target) | thickness_mm, foil_mm, profile WxHxT, finish, color |
| `source_notes` | Cross-refs, alias hints, migration notes (usable without schema change) |

**Inventory row = one purchasable/stockable identity.** Not „bare premontaj” as a material type.

### 6.2 Pricing

**Purpose:** Standardized price used for **quoting** and CostEngine `material_rates`.

- One active price per canonical material variant (or variant resolver, as today for profile depth).
- Markup policy is **separate** from `unit_cost` (documented in governance warnings).
- Pricing must **reference** Inventory `code` — not invent parallel materials named „Dibond” vs „ACM”.
- May use supplier average when multiple suppliers stock the same canonical material (`equivalent_to` future).

### 6.3 Template / CostEngine

**Purpose:** Define **usage** and **quantity** in a product template.

- References `material_code` / `material_id` from registry.
- Formulas compute quantity (m², ml, buc) from quote_input / geometry.
- **Must not** encode usage in the material’s canonical name (premontaj, față litere, spate litere = usage tags or component labels).
- Finish options (Oracal 651, print+laminare) may be **product options** or separate material lines — not synonyms for letter face sheet stock.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│   Inventory     │     │     Pricing      │     │  Template / CostEngine   │
│  physical SKU   │────▶│  unit_cost for   │────▶│  material_code + formula │
│  canonical_name │     │  quoting         │     │  usage_tags / component  │
└─────────────────┘     └──────────────────┘     └─────────────────────────┘
```

---

## 7. Search / alias behavior (desired — not implemented)

When alias/search support is built, operator experience should be:

| Operator searches | Should find | Display |
|-------------------|-------------|---------|
| `bond` | Panou compozit aluminiu (ACM/ACP) | Canonical name + aliases + matching SKUs by thickness/foil |
| `dibond` | Same family | Show brand hint „Dibond” if SKU is brand-specific |
| `alucobond` | Same family | Supplier/brand secondary |
| `forex` | PVC expandat | „Forex” as alias; thickness variant (3 mm, 10 mm, …) |
| `pvc expandat` | PVC expandat | Direct canonical match |
| `stiplex` | PMMA / plexiglas acrilic | Popular RO alias |
| `plexi` / `acril` | PMMA / plexiglas acrilic | Variant finish in specs |
| `țeavă 30x30` / `30x30x1.5` | Țeavă pătrată oțel 30×30×1.5 mm | Profile dimensions in title |
| `profil lateral` / `cant aluminiu` | Profil aluminiu (return/cant litere) | Usage tag „litere volumetrice” |
| `oracal 651` | Folie autocolantă PVC | Brand Oracal, serie 651; link Color Registry |
| `autocolant` / `vinyl` | Folie autocolantă PVC (generic or serie) | Disambiguate generic vs Oracal serie |

**Non-goals for search v1:** fuzzy merge of distinct technical variants (e.g. ACM 0.21 vs 0.30 foil) — those remain separate SKUs.

---

## 8. No-schema-change path

Work that can proceed **without** database migration:

| Action | Description |
|--------|-------------|
| **Naming convention** | This document + owner approval; new rows use canonical `name` pattern |
| **Static alias map** | Implemented: `frontend/src/lib/materials/materialCanonicalTaxonomy.ts` + `materialCanonicalAnalysis.ts` (family/alias/brand/usage analysis; no DB) |
| **Seed cleanup** | Prefer `MAT-ACM-BOND-3MM`; keep `MAT-ACP-3MM` as legacy alias (no delete). Align Oracal code namespaces |
| **`source_notes`** | Record accepted aliases and cross-refs on existing rows |
| **Subcategory policy** | Already groups synonyms in UI — extend with alias hints in recommended subcategory labels |
| **Admin naming hints (non-blocking)** | Implemented in Material Price Registry edit drawer: `MaterialNamingHints` — alias/brand/usage warnings; does not block save |
| **Duplicate warning (future UI)** | On admin create: match alias map → „Material similar: MAT-ACM-BOND-3MM” |
| **Display-only canonical label** | ProductSystem component copy can show canonical name while keeping stable `material_code` |

---

## 9. Future schema / metadata path

Recommended fields when Inventory metadata matures:

| Field | Type | Purpose |
|-------|------|---------|
| `material_family` | enum / string | ACM, PMMA, PVC_EXPANDED, VINYL_CAST, STEEL_TUBE_RECT, ALU_PROFILE, … |
| `canonical_name` | string | Neutral display name |
| `aliases` | string[] or join table | bond, dibond, forex, stiplex, … |
| `brand` | string optional | Oracal, Dibond, Forex, Plexiglas |
| `series` | string optional | 641, 651, 8500 |
| `supplier_sku` | string optional | Vendor catalog number |
| `technical_specs` | JSON | thickness_mm, foil_mm, profile, finish, color |
| `usage_tags` | string[] | premount, letter_face, letter_back, casetting, print, structure |
| `equivalent_to` | material_id optional | Same canonical material, different supplier SKU |
| `replacement_for` | material_id optional | Successor SKU after rename/merge |

**`usage_tags` examples:** `premount`, `litere_volumetrice`, `casetare`, `print`, `montaj` — describe **where** the material is used, not **what** it is.

---

## 10. Stop condition

**This document build:**

- Does **not** change runtime (frontend, backend, CostEngine, ProductSystem).
- Does **not** migrate or rename existing `inventory_materials` rows.
- Does **not** modify seeds, mock data, or pricing registry data.
- Does **not** implement alias table, search, or admin duplicate guards.

Follow-up builds (see QA doc) own implementation and data migration.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-09 | Initial canonical naming and alias architecture reference |
| 2026-06-09 | Reference static taxonomy + analysis helpers + Material Price Registry naming hints (BUILD Material Registry Consolidation) |
| 2026-06-09 | Non-breaking seed `name`/`source_notes` cleanup via `backend/seeds/material_canonical_naming.py` (BUILD Inventory/Pricing Naming Cleanup) |
