# AUDIT — Structural Material & Profile Catalog Authority

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Owner GO | `GO_STRUCTURAL_MATERIAL_AND_PROFILE_RESOURCE_OPTIONS_AUTHORITY_DESIGN` |
| Start | `STRUCTURAL_RESOURCE_OPTIONS_AUTHORITY_DESIGN_IN_PROGRESS` |
| **Final verdict** | **`NEW_RESOURCE_OPTION_REGISTRY_REQUIRED`** |
| HEAD | `10253ff5c52fec36c069bb6857de7401ebfc3949` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Scope | Audit + design + owner decision prep — **no app edits, no seed, no migration, no commit** |

---

## Mini decizia mea (owner)

Nu rezolvăm lipsa catalogului global prin coduri speciale lipite de ACP (`OPT-ACP-FRAME-MAT-*`).  
Direcția corectă: **material structural + profil structural reutilizabile**, consumate de multiple utilizări (cadru interior ACP, premontaj, casete, totemuri), fiecare componentă declarând ce acceptă.

---

## Executive summary

WorkOS are **fragmente** de date (premount bars, letter cant profiles, lightbox frame SKU, mock totem tubes, FE taxonomy targets) dar **nu** un Resource Option subsystem canonic pentru material/profil structural.  
`inventory_materials` deține stoc + `unit_cost` (pricing acquisition) fără model dimensional tipizat (shape/W/H/T).  
Selectorii runtime (`bar_material`, `mounting_bar_profile`) sunt **allowlist-uri locale de produs**, nu catalog tehnic global.

**Recomandare registry:** Option **D** — shared technical Resource Options catalog + separate pricing mapping.  
**Next safe step:** Option **3** — owner confirmă sectiuni reale + reguli traverse înainte de Registry V1.

---

## Baseline

| Check | Result |
|-------|--------|
| HEAD | `10253ff` — ACP internal frame audit docs |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Dirty tree | Large unrelated WIP — **untouched** |
| Prior STOP | `FRAME_RESOURCE_OPTIONS_MISSING` + `FRAME_PROFILE_CATALOG_MISSING` |
| Resource Option subsystem | **NOT FOUND** as named registry/service |

---

## Inventory (complete relevant set)

| Cod/concept | Tip | Registry | Technical authority | Pricing authority | Consumers | Reusable | Conflict |
|-------------|-----|----------|---------------------|-------------------|-----------|----------|----------|
| `bar_material` | enum steel\|aluminum | mounting config / quote input | Metal Premount path | selects MAT-PREMOUNT-* | Intake Review, form contract | Pattern only | Not global RO |
| `mounting_bar_profile` | profile key string | canonical variants | `allowed_values: ["30x30x1.5"]` | priced frozenset only for that key | Letters / premount CostEngine | Key reusable | Local product allowlist |
| `MAT-PREMOUNT-BAR-STEEL` | inventory SKU | `inventory_materials` + seed_build4 | usage-named; section 30×30×1.5 baked in | `unit_cost` | Premount BOM | Partial | Usage in code (anti-pattern vs naming doc) |
| `MAT-PREMOUNT-BAR-ALUMINUM` | inventory SKU | same | same (Al) | `unit_cost` | Premount BOM | Partial | Same |
| `MAT-PROFIL-ALU-BOX` | inventory SKU | seed_build4 | Lightbox FRAME_PROFILE | `unit_cost` | Lightbox | Family-only | No WxHxT identity |
| `MAT-PROFIL-ALU` | generic stub | stubs / routed scripts | generic | occasional fill | Stub paths | Over-generic | No section |
| `MAT-PROFIL-LATERAL-LITERE-{30,60,80,100}MM` | return/cant Al by depth | inventory + rate resolver | letter return depth | EUR/ml | Letters CostEngine | Cant family | **Not** structural tube |
| `MAT-PROFIL-LATERAL-LITERE` | parent alias | inventory | alias → depth variants | often unpriced parent | Letters | Alias | — |
| `MAT_RECT_TUBE_PROFILE_MAIN` / `_RIB` | Product001 placeholders | product001 seed | BOM concept | missing_price | Product001 docs | No | Parallel underscore namespace |
| `MAT-STEEL-TUBE-40X40` | validator allowlist only | linkage validator | none seeded | none | Tests | Stub | Orphan |
| Profile key `20x20x1.5` | string | docs/tests/legacy UI | not in live allowed_values | unpriced | Historical | Candidate | Must not invent as ACP default |
| Profile key `40x40x2` | string | tests + totem mock | warning if used unpriced | missing price warning | Policy tests / mock | Candidate | Not allowlisted live |
| Mock `MAT-012` țeavă 40×40×2 | mock | FE mockData | demo totem | mock cost | Demo UI | Mock only | Parallel namespace |
| Mock `MAT-011` profil U 40×40 | mock | FE mockData | demo | mock | Demo | Mock only | — |
| Totem „Oțel 40x40x2” + traverse | demo labels | workstationRouting | mock lengths | none | Demo | Demo | No MAT code |
| Target `MAT-STEEL-SQUARE-TUBE-{W}x{H}x{T}` | naming target | MATERIAL_CANONICAL_NAMING + FE taxonomy | docs only | docs | Architecture | Intended | Not seeded |
| Target `MAT-STRUCT-BAR-*` | naming target | mounting boundary docs | docs only | docs | Architecture | Intended | Not seeded |
| ACP `internal_frame_enabled` | boolean marker | svg_support_selection | ACP nested intent | none | Step 1/PD | Config | No material/profile |
| ACP `frame_clearance_mm` | clearance mm | mounting ACM | setback | none | Step 2 | Config | Hidden default 5 historically |
| Proposed `OPT-ACP-FRAME-MAT-*` | rejected direction | worklog only | ACP-local | none | Proposed then rejected by owner | **Do not create** | Product-scoped RO anti-pattern |
| `FRAME_PROFILE` component type | PS component type | template contract | Lightbox | via MAT-PROFIL-ALU-BOX | Lightbox | Role reusable | ≠ ACP nested frame |
| FE families `steel_profile` / `aluminium_profile` | taxonomy | materialCanonicalTaxonomy.ts | classification only | none | Naming UI hints | Yes | Not selectable catalog |

---

## Technical vs pricing authority

| Layer | What it owns today | Gap |
|-------|-------------------|-----|
| Product / form variants | Allowed profile **keys** for letters | Not a dimensional catalog |
| `inventory_materials` | Stock row + acquisition `unit_cost` | No typed shape/W/H/T; usage baked into some codes |
| Pricing Registry (doc 08) | Classifies material_price vs commercial rules | Must not own product structure |
| CostEngine gates | Which profile keys are priced | Interim frozensets |
| ACP frame | Boolean + clearance | No technical RO |

**Boundary conflicts:** usage-named SKUs (`MAT-PREMOUNT-BAR-*`) mix Template usage into Inventory identity (forbidden by `MATERIAL_CANONICAL_NAMING_AND_ALIASES.md`). Pricing seeds must not become Product System technical allowlists.

---

## Premount / Lightbox / ACP findings

| Domain | Finding |
|--------|---------|
| Premount | Live steel/aluminum + **only** `30x30x1.5`; XOR with Alucobond **panel mounting support** (not nested frame) |
| Lightbox | `MAT-PROFIL-ALU-BOX` without section dimensions |
| ACP frame | Marker only; catalogs missing; independent of premount concept |
| Letters cant | Depth-based “profil” — different physical role |

---

## Crossbar audit

| Class | Status |
|-------|--------|
| Implemented | **Missing** |
| Documented formula | **Missing** (only TBD in ACP plans) |
| Owner convention | **Unknown** — worksheet required |
| Hardcoded | Totem mock `3x150mm traverse` only (non-authority) |
| Missing | Count, spacing, thresholds, orientation, service opening interaction |

---

## Dead pieces (report only — no cleanup)

- Usage-named `MAT-PREMOUNT-BAR-*` vs target `MAT-STEEL-SQUARE-TUBE-*`
- `aluminium` vs `aluminum` spelling split (US in codes, RO in UI)
- `20x20x1.5` / `40x40x2` mentioned outside live allowlist
- Product001 underscore tube codes without runtime alias
- `MAT-STEEL-TUBE-40X40` orphan allowlist
- Mock MAT-011/012 parallel namespace
- Lightbox profile without WxHxT
- ACP-local OPT-* proposal (rejected — do not implement)
- Hidden clearance default 5 mm (prior ACP audit)
- Dossier seed lag vs in-code mounting variants

---

## Single architectural recommendation

**Create a shared technical Resource Options catalog (materials + profiles) with separate pricing mapping — do not extend pricing/inventory alone as technical truth, and do not ACP-prefix reusable options.**

See `docs/architecture/STRUCTURAL_RESOURCE_OPTIONS_AUTHORITY.md`.

---

## STOP

Design package delivered. No implementation. Awaiting owner decision sheet.
