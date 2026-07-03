# TPL-VOLUMETRIC-LETTERS — Mounting vs Structure Boundary

**Date:** 2026-06-09  
**Status:** Architecture reference (documentation only — no runtime change)  
**Audience:** Product owner, Cursor agents, developers  
**Related audits:**

- `docs/architecture/TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md` — intake ↔ quote_input contract
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md` — CostEngine formulas and materials
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_CURRENT_STATE.md` — bounded-build context
- `docs/architecture/VOLUMETRIC_WORKINTAKE_V2_MIGRATION_BOUNDARY.md` — V2 vs classic vs QuoteWizard

---

## 1. Current state

`TPL-VOLUMETRIC-LETTERS` includes today a **simplified representation** of premount on support bars. This is a **temporary bridge**, not the final structural product model.

### 1.1 What exists in the letters template

| Area | What is implemented |
|------|---------------------|
| **Intake contract** | Canonical `mounting_system` enum + bar/template fields on `product_spec_json` |
| **WorkIntake V2 UI** | Section **„3. Montaj / suport”** in `V2ProductionStage` |
| **Classic intake UI** | Section **„Montaj / suport”** in `Product001IntakeSpecEditor` |
| **ProductSystem** | Component `comp_premount_bars` (type `STRUCTURA`) gated by `steel_bars` / `aluminum_bars` |
| **CostEngine** | Material lines `MAT-PREMOUNT-BAR-STEEL` / `MAT-PREMOUNT-BAR-ALUMINUM` on formula `mounting_bar_total_length` |
| **Forex template** | Independent `mounting_template_enabled` + `mounting_template_area_m2` (not structural bars) |

### 1.2 Current fields (letters template)

| Field | Role | Notes |
|-------|------|-------|
| `mounting_system` | Enum: `direct_wall`, `steel_bars`, `aluminum_bars`, `acm_panel` | Legacy sync: `mounting_type`, `premounting_type`, `premount_bar_material` |
| `mounting_bar_profile` | Bar profile string (e.g. `30x30x1.5`) | Only `30x30x1.5` is owner-confirmed in pricing today |
| `mounting_bar_count` | Number of bars (default 2) | Heuristic: top + bottom |
| `mounting_bar_length_m` | Optional total length override (ml) | **Classic only** in UI; preserved in JSON if already saved |
| `mounting_template_enabled` | Forex mounting template on/off | Independent of `mounting_system` |
| `mounting_template_area_m2` | Forex template area (m²) | V2 auto-calculates from `width_mm × height_mm` when enabled |
| `mounting_notes` | Free text | **Classic only** in UI |

### 1.3 WorkIntake V2 operator options (real UI)

In V2, mounting is **not** labeled „premontaj pe structură metalică”. Equivalent options:

- **Bare oțel premontaj** → `mounting_system = steel_bars`
- **Bare aluminiu premontaj** → `mounting_system = aluminum_bars`

When either is selected, V2 shows:

- **Profil bare premontaj** (`mounting_bar_profile`, default `30x30x1.5`)
- **Număr bare premontaj** (`mounting_bar_count`, default `2`)

V2 does **not** expose `mounting_bar_length_m` or `mounting_notes` (classic does).

### 1.4 SVG / layer reference (not structural costing)

Vector layers such as `support_bars`, `metal_frame`, and suggested roles **Cadru metalic** exist for mapping and preview. They are **reference only** for letter geometry gates — they do **not** drive bar length/profile costing today.

`TPL-STRUCTURA-LITERE` does **not** exist in the repository yet.

---

## 2. Boundary decision

### 2.1 `TPL-VOLUMETRIC-LETTERS` is responsible for

- Letter face (plexi / ACP face)
- Vinyl / Oracal / face finish
- Return / cant (depth, finish, RAL/Oracal)
- Visual chamfer / back bevel on **letters**
- Letter backing (Forex/PVC back)
- LED system, density, color
- PSU planning and allocation
- Letter geometry: perimeter, face area, letter count
- Letter costing (face, return profile, back, LED, paint tubes, vinyl)
- Simple mounting method selection (direct wall)
- **Temporary bridge** for premount bars (simplified fields + simplified ml costing)
- Forex mounting **template** (area-based, independent checkbox)

### 2.2 Future `TPL-STRUCTURA-LITERE` will be responsible for

- Support bars as a **product line**, not a sub-option of letters
- Frames / structural metalwork
- Structural profiles (steel, aluminum)
- Bar lengths derived from design (including SVG rectangles)
- Bar count and profile per bar
- Structural material registry and rates
- Structural finish (paint, treatment)
- Structural labor (cut, weld, assembly, premount)
- **Separate** structure costing (ml profile, not letter perimeter/area)
- Reading bars from SVG / file layers (`STRUCTURA_SUPORT`, `BARE_MONTAJ`, etc.)

### 2.3 Explicit non-overlap

| Concern | Letters template | Structure template (future) |
|---------|------------------|-------------------------------|
| Letter perimeter / face area | yes | **no** |
| Return depth / cant | yes | **no** |
| Bar ml from rectangle geometry | **no** (bridge heuristic only) | **yes** |
| Frame / complex structure | **no** | **yes** |
| Structural labor priced | **no** (warning: `mounting_labor_not_priced`) | **yes** |
| ACM casetted panel | captured only; separate template | out of scope for both unless dedicated ACM template |

---

## 3. Owner rule for SVG bars

When bars are drawn in SVG/file as **rectangles**, the future structure template must apply:

### 3.1 Rectangle → bar dimensions (from SVG)

- **Length of rectangle** = bar length
- **Smaller rectangle dimension** = **visible outer size** of the profile (one leg / outer width — not the full 3D profile)
- That outer size is rounded to **0 decimal places**
- Rounded value maps to the **nearest standard outer dimension** (e.g. 30, 35, 40 mm on the visible leg)
- Costing is in **linear meters** on bar length
- Bars are **not** costed as area
- Bars do **not** enter letter perimeter
- Bars do **not** enter letter return / cant
- Bars do **not** enter letter face geometry

SVG helps with **length** and **approximate outer profile size**. It does **not** define the complete structural profile alone.

### 3.2 Orientation rule

For horizontal or vertical bars:

- **Larger dimension** = length
- **Smaller dimension** = profile / visible outer leg

### 3.3 Complete profile and wall thickness (structural registry)

Structural metal bars are **not** defined only by outer dimensions such as 30×30 mm or 50×30 mm. The full profile is:

**lățime × înălțime × grosime perete** (wall thickness / **grosimea materialului**)

Examples of complete profiles:

| Complete profile | Meaning |
|------------------|---------|
| 30 × 30 × 1.5 mm | Square tube 30×30, **grosime perete 1.5 mm** |
| 30 × 30 × 2 mm | Square tube 30×30, **grosime perete 2 mm** |
| 50 × 30 × 2 mm | Rectangular tube 50×30, **grosime perete 2 mm** |
| 50 × 30 × 3 mm | Rectangular tube 50×30, **grosime perete 3 mm** |

Rules for `TPL-STRUCTURA-LITERE`:

1. **Complete profile** = width × height × **grosimea peretelui profilului** (not just the visible outer leg from the drawing).
2. **SVG rounding** helps identify the **nearest outer dimension** (e.g. 29.6 mm → 30 mm) — it does **not** infer wall thickness.
3. **Grosimea peretelui nu se deduce din dreptunghiul SVG** — the rectangle cannot reliably indicate material wall thickness.
4. **Grosimea peretelui** (and the full profile key) must come from the **structural profile selected** in **Material / Pricing Registry** (operator choice or default per mapped outer size + material).
5. **Costing must use the complete profile** (width × height × wall thickness) for material rate lookup — **not** the visible leg alone.

The letters-template bridge today stores a single string such as `30x30x1.5` in `mounting_bar_profile`; that is closer to a **registry profile key** than to SVG-derived geometry, but it is still embedded in the letters template and not sourced from SVG extraction.

### 3.4 Examples — SVG outer dimension mapping only

These examples apply to **length** and **outer leg** from the rectangle. Wall thickness is **not** derived here; it is chosen from registry after outer size is mapped.

| Rectangle (mm) | Bar length | Outer leg (round + map) | Wall thickness |
|----------------|------------|-------------------------|----------------|
| 1200 × 30 | 1200 mm | 30 mm | From registry (e.g. 1.5 or 2 mm) |
| 1200 × 29.6 | 1200 mm | 30 mm | From registry |
| 1200 × 34.7 | 1200 mm | 35 mm | From registry |
| 1200 × 39.8 | 1200 mm | 40 mm | From registry |

**Sections 3.1–3.4 are the target for `TPL-STRUCTURA-LITERE`.** They are **not** implemented in `TPL-VOLUMETRIC-LETTERS` today (no SVG bar extraction; no registry-driven wall thickness selection).

---

## Inventory & Pricing registry expectations

This section records **owner rules** and **current system gaps** for Inventory (`inventory_materials`) and Material Price Registry. It applies to the future `TPL-STRUCTURA-LITERE` template and to ACM/ACP products — not only the letters-template bridge.

**Related runtime (read-only reference):** `backend/models/inventory_materials.py`, `frontend/src/pages/MaterialPriceRegistry.tsx`, `backend/services/volumetric_quote_input_policy.py`, `backend/seeds/seed_build4_materials.py`, `backend/seeds/seed_volumetric_owner_confirmed_prices.py`.

### Structural profile identity

A complete structural profile is **not** defined by the visible outer dimension from SVG alone.

**Full profile expression:**

`lățime × înălțime × grosime perete` (wall thickness / **grosimea peretelui profilului** / **grosimea materialului**)

**Examples:**

| Complete profile |
|------------------|
| 30 × 30 × 1.5 mm |
| 30 × 30 × 2 mm |
| 50 × 30 × 2 mm |
| 50 × 30 × 3 mm |

**What SVG can indicate:**

- Bar **length** (larger rectangle dimension)
- **Visible outer size** of the profile (smaller dimension, rounded to 0 decimals)

**What SVG cannot reliably indicate:**

- **Wall thickness** of the profile — the drawing does not encode foil/tube wall gauge

**Wall thickness source:**

- Selected from **Inventory / Material Price Registry** (dedicated SKU per complete profile), or
- Default from template / operator choice after SVG proposes outer-size candidates

**Costing rule:**

- Pricing and CostEngine must use the **complete profile** for material rate lookup
- Quantity remains **ml on bar length** — not area, not letter perimeter

### Structural profile SKU pattern

**Recommended pattern** (not yet fully implemented in seeds):

| Rule | Detail |
|------|--------|
| One complete profile | **One Inventory / Pricing row** (separate SKU) |
| Unit | **`ml`** (linear meters) |
| Acquisition vs commercial | `unit_cost` = purchase/production cost; **commercial markup is a separate layer** (Material Price Registry UI) |
| Supplier / review | `source_review_status`, `source_notes`, price history — owner-confirmed before `active` |

**Example material codes** (recommended naming — not final enforced codes):

| Code | Human name |
|------|------------|
| `MAT-STRUCT-BAR-STEEL-30X30X1_5` | Țeavă pătrată oțel 30×30×1.5 mm |
| `MAT-STRUCT-BAR-STEEL-30X30X2` | Țeavă pătrată oțel 30×30×2 mm |
| `MAT-STRUCT-BAR-STEEL-50X30X2` | Profil rectangular oțel 50×30×2 mm |
| `MAT-STRUCT-BAR-ALUMINUM-30X30X2` | Profil aluminiu 30×30×2 mm |

**Reference pattern already in repo (letters cant — variant SKUs):**

- `MAT-PROFIL-LATERAL-LITERE-30MM` … `-100MM` with quote-time resolver — structural bars should follow similar **variant-per-complete-profile** discipline, not a single generic code per metal type.

**Letters bridge today (deprecated direction):**

- `MAT-PREMOUNT-BAR-STEEL` / `MAT-PREMOUNT-BAR-ALUMINUM` — one SKU each, name embeds only `30×30×1.5 mm`

### Current gap — structural profiles

| Area | Today | Target |
|------|-------|--------|
| **Inventory schema** | `code`, `name`, `unit`, `unit_cost` — no `profile_width_mm`, `profile_height_mm`, `wall_thickness_mm` | Complete profile in SKU + optional structured metadata later |
| **Inventory rows** | Two premount bar materials (steel/aluminum), each named for **30×30×1.5** only | Registry rows per complete profile × material kind |
| **Pricing** | Can differentiate profiles **only** if separate SKU + `unit_cost` exist | Registry-driven catalog of priced complete profiles |
| **Policy** | `PRICED_STEEL_BAR_PROFILES` / `PRICED_ALUMINUM_BAR_PROFILES` hardcoded to `{30x30x1.5}` in `volumetric_quote_input_policy.py` | Loaded from registry or dossier — not Python frozenset |
| **CostEngine** | `mounting_bar_profile` string gate on template material (`mounting_bar_profile_in: ["30x30x1.5"]`) | Profile key → material code resolver (like `return_depth_mm` → `MAT-PROFIL-LATERAL-LITERE-60MM`) |
| **Priced profile** | Effectively **`30x30x1.5` only** | 30×30×2, 50×30×2, etc. require new registry rows + gate/resolver update |
| **`TPL-STRUCTURA-LITERE`** | Not implemented | Must be **registry-driven** end-to-end |

New profiles without registry rows: material line **skipped**, warning `mounting_bar_profile_price_missing` — **no silent fallback**.

### SVG to Pricing mapping

End-to-end flow for structural bars (target — not live in letters bridge):

1. **SVG rectangle** → bar **length** + **visible outer dimension** (orientation: larger = length, smaller = outer leg).
2. **Outer dimension** rounded to **0 decimal places**; mapped to nearest standard outer candidate (e.g. 30 / 35 / 40 mm on that leg).
3. System **proposes profile candidates** sharing that outer size (e.g. 30×30×1.5 and 30×30×2 both have 30 mm visible leg on square tube — operator must pick wall thickness).
4. **Operator or template default** selects **complete profile** including **grosime perete**.
5. **Pricing** resolves **SKU** for that complete profile → `unit_cost` per **ml**.
6. **CostEngine** computes quantity as **ml on length** only — profile dimensions affect **unit rate**, not area-based quantity.

### ACM / ACP material identity

**Equivalent terms in WorkOS** (same product family — composite aluminum panel):

- ACM
- ACP (Aluminum Composite Panel)
- Dibond
- Alucobond
- material compozit aluminiu / panou compozit aluminiu

**ACM is not defined by total panel thickness alone** (e.g. 3 mm or 4 mm).

A complete ACM material identity should include, where known:

| Attribute | Notes |
|-----------|--------|
| **Total panel thickness** | e.g. 3 mm, 4 mm |
| **Aluminum foil / face thickness** | e.g. 0.21 mm, 0.30 mm, 0.50 mm per face — **critical price/quality differentiator** |
| Core type | PE, FR, etc. — when known |
| Sheet format | dimensions, roll vs sheet |
| Finish / colour | e.g. alb mat |
| Brand / supplier | verification in `source_*` fields |
| Price unit | typically **mp** (not ml) |
| Acquisition vs commercial | `unit_cost` separate from markup policy |

**Owner rule:**

> ACM 3 mm with aluminum foil **0.21 mm** is a **different material** from ACM 3 mm with aluminum foil **0.30 mm** — even when total thickness is identical.

**Examples of complete ACM descriptions:**

- ACM 3 mm, aluminiu 0.21 mm/față, alb mat
- ACM 3 mm, aluminiu 0.30 mm/față, alb mat
- ACM 4 mm, aluminiu 0.30 mm/față
- ACM 4 mm, aluminiu 0.50 mm/față

**Intake note:** `mounting_system=acm_panel` on `TPL-VOLUMETRIC-LETTERS` captures intent only; ACM casetted panel is a **separate template** for mature costing — see §4.3 and `captured_option_requires_separate_template`.

### ACM / ACP SKU pattern

**Recommended pattern** (illustrative — not enforced as final codes):

| Code | Identity |
|------|----------|
| `MAT-ACM-3MM-ALU0_21-WHITE` | ACM 3 mm total, alu foil 0.21 mm, white |
| `MAT-ACM-3MM-ALU0_30-WHITE` | ACM 3 mm total, alu foil 0.30 mm, white |
| `MAT-ACM-4MM-ALU0_30-WHITE` | ACM 4 mm total, alu foil 0.30 mm, white |
| `MAT-ACM-4MM-ALU0_50-WHITE` | ACM 4 mm total, alu foil 0.50 mm, white |

Encoding suggestion: total thickness + foil gauge + finish suffix; human `name` carries full specification for operators.

### ACM current impact

| Topic | Implication |
|-------|-------------|
| **Generic ACM** | Insufficient for mature costing — caseting, V-groove routing, rigidity, and unit price depend on **foil thickness**, not total mm alone |
| **Inventory / Pricing** | Must allow rows differentiated by **total thickness + aluminum foil thickness** (+ finish where priced) |
| **Letters template** | `acm_panel` option is capture/warning only — not full ACM product model |
| **`TPL-STRUCTURA-LITERE`** | Structure / casetted products consuming ACM must reference **complete ACM SKU**, not `ACM_PANEL_GENERIC` long term |
| **Related seeds today** | Volumetric seeds reference letter face ACP (`MAT-ACP-FATA-LITERE`) — distinct from ACM casetted panel stock; ACM panel templates need their own registry discipline |

---

## 4. Current costing limitation

Costing inside `TPL-VOLUMETRIC-LETTERS` for premount bars is **simplified** and must **not** be treated as the final structure model.

### 4.1 What CostEngine does today

| Behavior | Detail |
|----------|--------|
| Bar quantity | Formula `mounting_bar_total_length` |
| Default derivation | `assembly_width_m × mounting_bar_count` (default count **2**) |
| Override | `mounting_bar_length_m` when set (total ml) |
| Width source | `width_mm` from quote_input / simulate payload |
| Profile gate | Material priced only when `mounting_bar_profile` is in allowed list (today: **`30x30x1.5`**) |
| Labor | **Not priced** — `mounting_labor_not_priced` warning |
| Unknown profile | Material skipped — `mounting_bar_profile_price_missing` warning |

### 4.2 What it does **not** do

- Does not read bars from SVG layers
- Does not extract rectangles from geometry
- Does not round/map profile from rectangle width
- Does not cost frames or complex structures
- Does not include full structural finish or labor
- Does not separate structure as its own quote line / template

### 4.3 Forex mounting template (related but distinct)

`mounting_template_enabled` + `mounting_template_area_m2` gates **Forex 3 mm template** material and CNC — this is a **letter mounting aid**, not structural bar extraction. It remains in the letters template.

---

## 5. WorkIntake V2 behavior (today)

### 5.1 Operator selects **Bare oțel premontaj**

1. UI: `mounting_system` → `steel_bars`
2. Legacy sync on save: `mounting_type=premounted`, `premounting_type=metal_structure`, `premount_bar_material=steel`
3. Sub-fields shown: `mounting_bar_profile`, `mounting_bar_count`
4. Persisted in `product_spec_json` via workspace auto-save (`normalizeVolumetricIntakeSpecForSave`)
5. **Readiness:** production stage gate (`isProductionStageSaved`) does **not** require mounting fields — selection is optional for handoff
6. **QuoteWizard handoff:** `mapProductSpecToVolumetricQuotePrefill` copies `mounting_system`, bar profile/count; length derived at simulate time from `width_mm` unless `mounting_bar_length_m` already in spec (e.g. from classic)
7. **Handoff panel (read-only):** shows sistem montaj, șablon Forex if enabled, bare premontaj (count + profile) when `steel_bars` or `aluminum_bars`

### 5.2 Operator selects **Bare aluminiu premontaj**

Same flow with `mounting_system=aluminum_bars` and `premount_bar_material=aluminum`. CostEngine uses `MAT-PREMOUNT-BAR-ALUMINUM` instead of steel.

### 5.3 What remains bridge

- Enum + 2–3 scalar fields, not per-bar SVG entities
- No structural stage in V2
- No profile picker tied to pricing registry beyond free-text profile
- No structural labor or finish

### 5.4 What is not implemented

- SVG rectangle → bar list
- Per-bar length/profile in intake
- Structure readiness gates
- Cross-template handoff to `TPL-STRUCTURA-LITERE`

---

## 6. QuoteWizard behavior

### 6.1 Handoff from WorkIntake V2 (commercial mode)

- Mounting and bars appear in **`VolumetricWorkIntakeHandoffPanel`** — read-only snapshot
- Main geometry and cost options are hidden; commercial pricing rail stays editable
- **Advanced technical override:** operator can enable override + reason, then edit `CostOptionsPanel` / geometry — changes affect quote simulate/price **only**; they do **not** sync back to WorkIntake V2 (warning in UI)

### 6.2 Legacy / direct open

- `CostOptionsPanel` exposes `mounting_system` and Forex template fields
- Bar fields (`mounting_bar_profile`, `mounting_bar_count`, `mounting_bar_length_m`) exist in `quote_input` contract and payload builder but are **not** shown in the main CostOptions UI — they rely on prefill defaults
- Risk: operator can change mounting in wizard without updating intake spec

### 6.3 Future expectation

When `TPL-STRUCTURA-LITERE` exists:

- Structure must appear as a **separate section / line item** (or bundled quote with distinct template lines)
- Letters handoff panel should not imply full structural costing
- Override path should not be the long-term owner path for structure edits

---

## 7. Migration plan

### Phase 1 — Document boundary

**This document.** Lock product language: bridge in letters, structure in future template.

### Phase 2 — ProductSystem template

- Add `TPL-STRUCTURA-LITERE` as a **separate** active template (dossier, components, materials, operations)
- No automatic migration of existing quotes or specs
- Keep `comp_premount_bars` in letters template as deprecated bridge until owner sunset date

### Phase 3 — SVG structure extraction

- Dedicated layers, e.g. `STRUCTURA_SUPORT`, `BARE_MONTAJ`
- Parser: rectangle → length + profile (owner rounding/mapping rules §3)
- Persist structure-specific spec (per-bar or summarized ml by profile)
- Explicit rule: bar metrics **never** merge into `letter_perimeter_m` / `letter_face_area_m2`

### Phase 4 — Pricing separate

- ml-based profile costing per standard size (30 / 35 / 40 mm and registry expansion)
- Structural material, finish, labor operations
- Warnings/blockers owned by structure template policy — not volumetric letters policy

### Phase 5 — Quote bundle

- Single commercial quote may include:
  - `TPL-VOLUMETRIC-LETTERS` (letters line)
  - `TPL-STRUCTURA-LITERE` (structure line)
- Separate cost breakdowns, separate handoff panels, shared client/context only

---

## 8. Transitional rule

Until `TPL-STRUCTURA-LITERE` is live:

1. Bar fields on `TPL-VOLUMETRIC-LETTERS` (**`mounting_system`**, **`mounting_bar_*`**) remain **allowed** as a **bridge**.
2. Do **not** extend letters template aggressively with frame/cadre/SVG bar extraction — direct that work to the structure template build.
3. Do **not** document or sell bridge costing as „structură completă”.
4. Do **not** use `support_bars` / `metal_frame` layer geometry for letter costing or bar ml derivation in letters template.
5. Any **major** new structure capability (SVG bars, profile registry, structural labor, frame costing) must target **`TPL-STRUCTURA-LITERE`**, not new fields on letters.

### 8.1 Allowed interim fixes (letters template)

- Parity fixes (e.g. expose `mounting_bar_length_m` in V2 if classic already persists it)
- Documentation and warning text
- Critical regression fixes on existing bridge formula

### 8.2 Disallowed without structure template

- Rectangle parser wired into `TPL-VOLUMETRIC-LETTERS` quote_input as final behavior
- New structural components inside `comp_premount_bars` beyond bridge scope
- Treating `comp_premount_bars` as substitute for full structure product

---

## 9. Code pointers (read-only reference)

| Concern | Primary files |
|---------|----------------|
| Mounting enums / legacy sync | `frontend/src/lib/intakeVolumetricSpec.ts` |
| V2 UI | `frontend/src/components/workos/workIntakeV2/stages/V2ProductionStage.tsx` |
| Classic UI | `frontend/src/components/workos/Product001IntakeSpecEditor.tsx` |
| Quote prefill / payload | `frontend/src/lib/volumetricQuoteInput.ts` |
| Handoff display | `frontend/src/components/workos/VolumetricWorkIntakeHandoffPanel.tsx` |
| ProductSystem component | `backend/seeds/seed_build4_templates.py` → `comp_premount_bars` |
| Bar length formula | `backend/services/formula_handlers.py` → `mounting_bar_total_length` |
| Pricing tests | `backend/tests/test_volumetric_finish_mounting_pricing.py` |
| Dossier variants | `backend/seeds/seed_tpl_volumetric_letters_dossier.py` |

---

## 10. Changelog

| Date | Change |
|------|--------|
| 2026-06-09 | Initial boundary doc after read-only mounting/structure audit |
| 2026-06-09 | Owner clarification: complete profile includes **grosimea peretelui profilului**; SVG maps outer leg only; wall thickness from Material/Pricing Registry |
| 2026-06-09 | Added **Inventory & Pricing registry expectations** — structural profile SKU pattern, SVG→Pricing flow, gaps vs hardcoded frozenset; ACM/ACP identity (total thickness + aluminum foil thickness) |
