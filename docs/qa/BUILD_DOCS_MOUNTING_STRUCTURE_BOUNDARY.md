# BUILD — Docs: Mounting vs Structure Boundary

**Date:** 2026-06-09  
**Type:** Documentation only  
**Runtime:** Not touched

---

## Scope

Document the product and technical **boundary** between:

- **`TPL-VOLUMETRIC-LETTERS`** — letters product (with temporary premount-bar bridge)
- **`TPL-STRUCTURA-LITERE`** — future separate structure template (not implemented)

Based on read-only audits (2026-06-09):

- Partial structure/bars embedding in the letters template
- Inventory / Pricing readiness for **complete structural profiles** and **complete ACM/ACP** identity

---

## Documents created / modified

| Path | Action | Purpose |
|------|--------|---------|
| `docs/architecture/TPL_VOLUMETRIC_LETTERS_MOUNTING_STRUCTURE_BOUNDARY.md` | **Created / updated** | Boundary doc: current state, SVG rules, **Inventory & Pricing registry expectations**, V2/QuoteWizard, migration |
| `docs/qa/BUILD_DOCS_MOUNTING_STRUCTURE_BOUNDARY.md` | **Created / updated** | This QA record |

**Not modified:** `TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md`, `TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md`, `TPL_VOLUMETRIC_LETTERS_CURRENT_STATE.md` — remain authoritative for contract/costing detail; boundary doc cross-references them.

---

## Runtime not touched

Confirmed across all doc-only iterations:

- No frontend changes
- No backend changes
- No CostEngine / ProductSystem / seed changes
- No tests run (docs-only build)

Validation: `git diff` / `git status` must list **only** documentation paths under `docs/`.

---

## Owner clarifications documented

### Structural profiles — wall thickness

- Full profile = **lățime × înălțime × grosime perete** (not visible outer leg alone).
- Examples: 30×30×1.5, 30×30×2, 50×30×2, 50×30×3 mm.
- SVG provides **length** + **visible outer dimension**; **cannot** infer **grosimea peretelui profilului**.
- Wall thickness / complete profile must come from **Inventory / Material Price Registry** or operator/template default.
- Costing uses **complete profile** for €/ml rate; quantity = **ml on length**.

### ACM / ACP — total thickness + aluminum foil thickness

- ACM ≡ ACP ≡ Dibond ≡ Alucobond (composite aluminum panel family).
- **Not** defined by total panel thickness alone (3 mm ≠ fungible 3 mm).
- Must differentiate **aluminum foil / face thickness** (e.g. 0.21 vs 0.30 vs 0.50 mm).
- Rule: **ACM 3 mm alu 0.21 ≠ ACM 3 mm alu 0.30** — separate materials, separate SKUs, separate prices.
- Registry must carry total thickness + foil gauge + finish/supplier; `unit_cost` ≠ commercial markup.

---

## Decisions documented

| Topic | Decision |
|-------|----------|
| **Current bridge** | `steel_bars` / `aluminum_bars` + simplified ml costing stay in `TPL-VOLUMETRIC-LETTERS` until structure template exists |
| **Not final model** | Bridge uses `mounting_bar_count × width_mm` (or `mounting_bar_length_m` override); no SVG rectangle extraction |
| **Future template** | `TPL-STRUCTURA-LITERE` owns bars, frames, profiles, structural finish/labor, SVG bar rules |
| **Structural SKU pattern** | One Inventory row per complete profile; recommended codes e.g. `MAT-STRUCT-BAR-STEEL-30X30X2`; unit `ml` |
| **Structural gap** | No `wall_thickness_mm` column; hardcoded `PRICED_*_BAR_PROFILES`; only `30x30x1.5` priced; no premount variant resolver |
| **ACM SKU pattern** | Recommended e.g. `MAT-ACM-3MM-ALU0_30-WHITE` — total mm + foil gauge + finish |
| **ACM gap** | Generic ACM insufficient; casetted/structure templates need complete ACM identity in registry |
| **V2 gap** | No `mounting_bar_length_m` / `mounting_notes` in V2 UI (classic has them) |
| **Quote handoff** | Mounting/bars read-only in commercial handoff; Advanced override edits quote only |
| **Transitional** | Do not extend letters template with major structure/ACM features — route to dedicated templates + registry |

---

## Follow-up builds (recommended order)

### Docs (complete with this build)

- **Build A — Docs boundary + Inventory/Pricing expectations** — this document set

### Registry & metadata (no large CostEngine refactor first)

1. **Pricing registry alignment — structural profiles** — add owner-confirmed SKU rows per complete profile (steel/aluminum); €/ml; extend priced-profile list or registry API; update dossier allowed values
2. **Inventory metadata / SKU convention — structural profiles** — document and seed `MAT-STRUCT-BAR-*` pattern; optional future columns `profile_w_mm`, `profile_h_mm`, `wall_thickness_mm`
3. **ACM/ACP material identity registry** — separate rows per total thickness + alu foil thickness + finish; retire long-term reliance on generic ACM codes

### Template & engine

4. **CostEngine / `TPL-STRUCTURA-LITERE` — registry-driven pricing** — profile resolver (complete profile key → material code); SVG extraction (length + outer leg only); structure template bundle in quote
5. **Phase 2–5 from boundary doc** — ProductSystem template, SVG layers, separate costing, quote bundle

### Optional interim (letters bridge only)

- V2 parity: `mounting_bar_length_m` + `mounting_notes` — small intake alignment, not structure template

---

## Test plan

N/A — documentation only. No CI impact expected.

---

## Commit message (when requested)

```
docs: mounting vs structure boundary for TPL-VOLUMETRIC-LETTERS
```

Optional body mention: Inventory/Pricing expectations for structural profiles (wall thickness) and ACM/ACP (foil thickness).
