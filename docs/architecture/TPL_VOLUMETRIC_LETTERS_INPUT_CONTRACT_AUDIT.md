# TPL-VOLUMETRIC-LETTERS — Input Contract Audit

**Date:** 2026-06-06 (Work Intake ↔ QuoteWizard alignment)  
**Scope:** Active template `TPL-VOLUMETRIC-LETTERS` only.  
**Baseline:** Live preliminary costing PASS (**844.41 EUR**, `status=simulated`, zero cost blockers). With `back_bevel_enabled=true`: **898.41 EUR**.

> **Process reference, not universal template:** Acest document descrie **doar** contractul și policy-urile pentru `TPL-VOLUMETRIC-LETTERS`. Pentru onboarding-ul unui template nou, folosește `PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` (proces universal, **secțiunea 2**) și creează un audit dedicat noului `template_code`. Nu copia blockers, formule, câmpuri QuoteWizard sau task order din acest fișier fără confirmare owner.

**Related commits on `master`:**

- `46c8260` — derive premount bar length from assembly width × bar count; profile-specific pricing
- `a535b59` — finish/mounting option pricing
- `fe0be10` — blueprint dossier seed
- `a7022a8` — unit-based operations
- `544805d` — paint tube whole-tube material
- `6f83e6b` — `paint_tube_count` in QuoteWizard
- `d4264fa` — QC internal-only / costing basis cleanup

---

## 1. Executive summary

Costing works for the **Product 001 baseline** (geometry, LED, paint tubes, optional Forex mounting template). **Face finish vinyl**, **back bevel**, and **premount bar material** are wired into `quote_input`, QuoteWizard, and CostEngine. **Mounting labor** and **ACM casetted panel** remain captured-only (warnings, no invented cost).

**Current status:**

| Area | Status |
|------|--------|
| Geometry / LED / paint tubes | Aligned (QuoteWizard ↔ CostEngine) |
| Work Intake → QuoteWizard prefill | **Aligned** — business choices prefilled; geometry never invented |
| Back bevel | `back_bevel_enabled` toggles CNC back passes |
| Face finish / vinyl | Priced per owner-confirmed rates; Oracal metadata soft-warned when missing |
| Forex mounting template | Gated by `mounting_template_enabled` (independent of `mounting_system`) |
| Premount steel/aluminum bars | Auto length from `width_mm × mounting_bar_count`; profile-specific material pricing |
| ACM panel | Captured; **separate template** required — not priced here |
| Dossier | Template-level dossier v2 (`fe0be10` + task order update) |
| Readiness | Vector file warning remains; `ready_for_quote=false` until policy satisfied |

---

## 2. Current input contract map

### 2.1 Known costing fields (live PASS baseline)

| Field | ProductSystem | Work Intake | QuoteWizard | CostEngine | Dossier | Required | Default | Pricing |
|-------|:-------------:|:-----------:|:-----------:|:----------:|:-------:|:--------:|---------|---------|
| `width_mm` | notes only | yes | Step 2 dims | simulate dims | — | wizard yes | 1000 | — |
| `height_mm` | notes only | yes (`letter_height_mm` legacy) | Step 2 dims | simulate dims | — | wizard yes | 2000 | — |
| `depth_mm` | notes only | `return_depth_mm` | Step 2 dims | simulate dims | — | wizard yes | 80 | — |
| `letter_face_area_m2` | formula | — | Step 3 | yes | — | yes | empty | MAT face/spate mp |
| `letter_perimeter_m` | formula | — | Step 3 | yes | — | yes | empty | ops ml |
| `letter_count` | formula | — | Step 3 | yes | — | yes | empty | PREPRESS, electrical |
| `return_depth_mm` | variant tiers | yes | Step 3 select | yes | described | yes | empty | profil EUR/ml |
| `selected_psu_watts` | PSU variants | — | Step 3 select | yes | — | yes | empty | MAT-LED-PSU-12V |
| `psu_watts` | mirror | — | derived | yes | — | auto | = selected | formula compat |
| `led_module_count` | derived | — | computed | yes | — | derived | from perimeter | LED ops/modules |
| `mounting_template_area_m2` | formula | — | Step 3 | yes | — | yes | empty | MAT-SABLON + CNC |
| `paint_tube_count` | formula | — | Step 3 | yes | — | yes | empty | MAT-VOPSEA-RAL |

† Intake `letter_height_mm` / `return_depth_mm` are **not** the same keys as wizard `height_mm` / `depth_mm`; only `return_depth_mm` prefills wizard.

### 2.2 Business-option fields (owner-identified gaps)

| Field (proposed key) | ProductSystem | Work Intake | QuoteWizard | CostEngine | Dossier | Intake key today | Notes |
|----------------------|:-------------:|:-----------:|:-----------:|:----------:|:-------:|------------------|-------|
| Back bevel | notes (optional) | `backing_chamfer` | **missing** | **fixed 5-pass** | production rules | `backing_chamfer` | 3 vs 5 passes not selectable |
| Face finish | notes (optional vinyl) | `face_finish` | **missing** | **not used** | production hints | `face_finish` | No vinyl materials in template |
| Face vinyl area | — | — | **missing** | **not used** | — | — | Could default to `letter_face_area_m2` |
| Volume finish (lateral) | notes | `volume_finish` | **missing** | **not used** | hints | `volume_finish` | Production path only |
| Face miter chamfer | notes | `face_miter_chamfer` | **missing** | face **fixed 2-pass** | rules | `face_miter_chamfer` | Face bevel always 2 passes in template |
| Mounting system | notes | split fields | **missing** | **Forex always on** | notes | see below | No conditional gating |
| Mounting bars | — | coarse premount | **missing** | **not priced** | — | `premounting_type` | No steel/alu bar registry for volumetric |
| Vector file | notes | — | SVG panel | readiness warn | — | — | `letters_vector_file_required` |

**Work Intake mounting today (two fields):**

- `mounting_type`: `direct_wall` | `premounted`
- `premounting_type`: `none` | `metal_structure` | `acm_casetted_panel`

**Intake face_finish enum today:**

- `plexi` (no vinyl)
- `oracal_651`
- `oracal_8500_translucent`
- `print_laminated`
- `other`

### 2.3 ProductSystem template structure (source of truth for costing)

File: `backend/seeds/seed_build4_templates.py` → `_volumetric_letters_components()`

| Component | Operations | Materials | quote_input keys |
|-----------|------------|-----------|------------------|
| comp_face_litere | vector_prep, face_cnc_cut (2 passes) | MAT-ACP-FATA-LITERE | letter_count, letter_perimeter_m, letter_face_area_m2 |
| comp_lateral_litere | side_forming, return_face_bonding | MAT-PROFIL-LATERAL-LITERE | letter_perimeter_m, return_depth_mm |
| comp_spate_litere | back_cut (**5 passes fixed**) | MAT-SPATE-PVC-LITERE | letter_perimeter_m, letter_face_area_m2 |
| comp_led_litere | led_install, electrical | MAT-LED-MODULE, MAT-LED-PSU-12V | led_module_count, letter_count, letter_perimeter_m |
| comp_finisaj_litere | mounting_template_cnc (1 pass), painting, assembly†, qc†, packaging | MAT-VOPSEA-RAL, MAT-SABLON-MONTAJ, MAT-CONSUMABILE | paint_tube_count, mounting_template_area_m2, letter_face_area_m2, letter_perimeter_m |

† `assembly_letters` quote_priced=false; `qc_letters` internal_only=true.

**Critical:** `mounting_template_cnc_cut` + `MAT-SABLON-MONTAJ` are **unconditional** — not gated by mounting choice.

### 2.4 Quote workspace contract (volumetric)

Files: `frontend/src/lib/volumetricQuoteInput.ts`, `frontend/src/lib/volumetricQuoteFlowState.ts`, `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx`

- **Routing:** `TPL-VOLUMETRIC-LETTERS` → `VolumetricLettersQuoteFlow`; other templates → generic `QuoteWizard`.
- **Effective state precedence:** user edit > Work Intake `product_spec_json` > template defaults (`width_mm`/`height_mm` must not stay at 1000×2000 when intake has 4800×600).
- Fields: geometry, electrical, `mounting_template_area_m2`, `paint_tube_count`, derived LED — same `quote_input` contract as before.
- Intake prefill: `mapProductSpecToVolumetricQuotePrefill` → `buildInitialVolumetricQuoteFlowState` (dimensions + costing keys).
- Validation: `volumetricQuoteInputStepValid` on effective strings; `paint_tube_count > 0`.
- Payload: `buildSimulateQuoteInputPayload` merges dimensions into simulate/price requests.
- Photos / vector preview: context only — no geometry or pricing inference.

### 2.5 Work Intake contract

Files: `frontend/src/lib/intakeProductSpec.ts`, `Product001IntakeSpecEditor.tsx`, `backend/validators/intake_product_spec.py`

- Flexible JSON — **no DB migration** needed for new keys.
- Captures rich business choices (finish, chamfer, mounting).
- **Capture-only** relative to costing — validator strips unknown keys silently.
- Does not capture: `paint_tube_count`, geometry areas, bar dimensions, `mounting_system` granularity.

### 2.6 Blueprint Dossier

- **Template-level** entity (`product_blueprint_dossier` per `template_id`).
- Sections: variants, task rules, production notes, costengine mapping, QC, etc.
- Does **not** store per-quote selected options.
- Missing dossier → readiness warning `blueprint_dossier_missing` (current live behavior).
- **Recommendation:** Document allowed options at template level; defer quote-specific snapshot.

### 2.7 Pricing Registry (TPL-VOLUMETRIC-LETTERS)

**Owner-confirmed / active for costing:**

| Code | Unit | Price | Used when |
|------|------|-------|-----------|
| MAT-ACP-FATA-LITERE | mp | 16 EUR | always |
| MAT-SPATE-PVC-LITERE | mp | 16 EUR | always |
| MAT-PROFIL-LATERAL-LITERE-{30,60,80,100}MM | ml | 2–5 EUR | return_depth_mm |
| MAT-LED-MODULE | buc | 0.5 EUR | illuminated |
| MAT-LED-PSU-12V-{60,100,160,200}W | buc | tiered | selected_psu_watts |
| MAT-SABLON-MONTAJ | mp | 6 EUR | mounting_template_area_m2 > 0 |
| MAT-VOPSEA-RAL | buc | 10 EUR/tub | paint_tube_count |
| MAT-CONSUMABILE-MONTAJ | set | 5 EUR est. | needs_review |
| Workcenters PREPRESS…PACKAGING | — | owner rates | unit ops |

**Not in active volumetric pricing:**

- `MAT-ORACAL_651`, `MAT-ORACAL_641`, `MAT-VINYL_PRINT_LAMINATED` — exist in **PRODUCT-001 draft** registry test fixtures only.
- Steel tube 20×20 / mounting bar profiles — **no owner-confirmed row** for volumetric premount bars.
- ACM premount panel — not in volumetric material list (intake `acm_casetted_panel` is capture-only).

### 2.8 CostEngine formula behavior (relevant)

- `perimeter_pass_linear_meter`: `letter_perimeter_m × pass_count` — **pass_count from template `formula_params`, not quote_input**.
- No handler reads `backing_chamfer` / `back_bevel_enabled`.
- Missing `paint_tube_count` → `NEEDS_QUOTE_INPUT` on MAT-VOPSEA-RAL (fixed in wizard).
- No `not_priced_option` warning type today for captured intake choices.

---

## 3. Proposed canonical input contract

Keys below are **proposed** for alignment. Existing keys unchanged unless noted.

### A. Geometry / measurable

| Key | Type | Allowed / default | Required when | Priced now |
|-----|------|-------------------|---------------|------------|
| `width_mm` | number | > 0 | preliminary wizard | no |
| `height_mm` | number | > 0 | preliminary wizard | no |
| `depth_mm` | number | > 0 | preliminary wizard | no |
| `letter_face_area_m2` | number | > 0 | always costing | yes (materials) |
| `letter_perimeter_m` | number | > 0 | always costing | yes (ops) |
| `letter_count` | int | ≥ 1 | always costing | yes |
| `mounting_template_area_m2` | number | ≥ 0 | if `mounting_system=forex_template` | yes (Forex) |

### B. Electrical / lighting

| Key | Type | Default | Required when | Priced now |
|-----|------|---------|---------------|------------|
| `selected_psu_watts` | enum 60/100/160/200 | — | LED jobs | yes (variant) |
| `psu_watts` | number | mirror selected | formula compat | yes |
| `led_module_count` | int | derived | always if LED | yes |
| `illumination_type` | enum | from intake | capture; future gating | partial (LED conditional in template) |

### C. CNC / machining

| Key | Type | Default | Required when | Priced now |
|-----|------|---------|---------------|------------|
| `back_bevel_enabled` | boolean | **false** (recommended) | explicit choice | **Stage 2** — drives pass_count 3 vs 5 |
| `face_bevel_enabled` | boolean | **true** (implicit today) | optional explicit | face always 2 passes today |
| `face_plexi_thickness_mm` | number | 3 | future | no |
| `back_forex_thickness_mm` | number | 10 | future | no |

**Intake mapping:** `backing_chamfer` → `back_bevel_enabled` (rename at contract boundary).

### D. Face finish

| Key | Type | Values | Default | Priced now |
|-----|------|--------|---------|------------|
| `face_finish_type` | enum | `none`, `oracal_651`, `printed_vinyl`, `printed_laminated_vinyl` | `none` | **no — Stage 4** |
| `face_vinyl_area_m2` | number | default `letter_face_area_m2` | when finish ≠ none | no |
| `vinyl_notes` | string | — | optional | no |

**Intake mapping:**

| Intake `face_finish` | Canonical `face_finish_type` |
|----------------------|------------------------------|
| `plexi` | `none` |
| `oracal_651` | `oracal_651` |
| `oracal_8500_translucent` | extend enum or map to `oracal_651` + flag |
| `print_laminated` | `printed_laminated_vinyl` |
| `other` | capture + `not_priced_option` warning |

**Unpriced behavior (proposed):** warning `captured_option_not_priced:face_finish_type=<value>` — never zero-cost.

### E. Mounting / premount

| Key | Type | Values | Default policy | Priced now |
|-----|------|--------|----------------|------------|
| `mounting_system` | enum | `direct_wall`, `forex_template`, `steel_bars`, `aluminum_bars`, `acm_panel` | **require selection** (owner decision) | partial |
| `mounting_bar_material` | enum | `none`, `steel`, `aluminum` | when bars selected | no |
| `mounting_bar_profile` | string | e.g. `20x20` | when bars selected | no |
| `mounting_bar_length_m` | number | > 0 | when bars selected | no |
| `mounting_bar_count` | int | ≥ 1 | optional alt to length | no |
| `mounting_notes` | string | — | optional | no |

**Intake mapping (proposed):**

| mounting_type | premounting_type | mounting_system |
|---------------|------------------|-----------------|
| direct_wall | * | `direct_wall` |
| premounted | none | `forex_template`? or require explicit |
| premounted | metal_structure | `steel_bars` or `aluminum_bars` (needs sub-choice) |
| premounted | acm_casetted_panel | `acm_panel` |

**Per-system costing behavior (target):**

| mounting_system | Material ops | Notes |
|-----------------|-------------|-------|
| `direct_wall` | skip MAT-SABLON + mounting CNC | Stage 5 |
| `forex_template` | current behavior | PASS baseline |
| `steel_bars` / `aluminum_bars` | bar material + labor TBD | warning until priced |
| `acm_panel` | captured-only | future |

### F. Consumables / finishing

| Key | Type | Priced now |
|-----|------|------------|
| `paint_tube_count` | number (ceil at engine) | yes |
| `volume_finish` | enum from intake | capture; lateral Oracal/paint path |
| `ral_color` | string | capture |
| `finishing_notes` | string | capture |

### G. Readiness / files

| Key | Source | Effect |
|-----|--------|--------|
| `vector_file_present` | future upload | clears `letters_vector_file_required` |
| `blueprint_dossier_status` | dossier entity | readiness |
| `owner_approval_status` | future | commercial gate |

---

## 4. Back bevel policy

### Implementation (Stage 2 — done)

| back_bevel_enabled | Passes | Cost @ 18 m, 1.5 EUR/ml |
|--------------------|--------|-------------------------|
| false / missing (default) | 3 (cut only) | **81 EUR** |
| true | 5 (3 cut + 2 bevel) | **135 EUR** |

- **QuoteWizard:** checkbox `back_bevel_enabled` — label „Șanfren spate litere”, default unchecked (`false`).
- **Template:** `back_cut` uses `perimeter_pass_linear_meter` with `base_pass_count: 3`, `bevel_pass_count: 2`, `bevel_quote_input_key: back_bevel_enabled`.
- **Formula handler:** computes `pass_count = base + (bevel if enabled else 0)`; missing key → `false`, breakdown `default_applied: true`.
- **Intake prefill:** `backing_chamfer: true` → `back_bevel_enabled: true` (trivial map in `mapProductSpecToVolumetricQuotePrefill`).
- **Face bevel:** unchanged — `face_cnc_cut` remains 2 passes (54 EUR @ 18 m).
- **Rates unchanged:** CNC 1.5 EUR/ml/pass; no paint/material rate changes.

**Example (known payload, 18 m perimeter):**

- `back_bevel_enabled=false` → labour total drops **54 EUR** vs old fixed 5-pass back_cut (577.80 → 523.80 EUR partial).
- `back_bevel_enabled=true` → matches previous 5-pass behaviour (back_cut 135 EUR).

---

## 5. Face finish / vinyl policy

### Current

- ProductSystem notes mention optional vinyl/oracal; **no** vinyl materials or application labor in volumetric components.
- Work Intake captures `face_finish` + production timing hints (`volumetricLettersProduction.ts`).
- QuoteWizard does not ask.
- Pricing: Oracal/vinyl codes exist only in **inactive** PRODUCT-001 draft registry — **not** owner-confirmed for TPL-VOLUMETRIC-LETTERS.

### Proposed

1. **Capture** `face_finish_type` in Intake + QuoteWizard (required business choice).
2. **Default** `none` unless owner mandates required selection.
3. If `face_finish_type != none` before Stage 4 pricing:
   - Emit warning: `captured_option_not_priced:face_finish_type`
   - Do **not** add zero-cost material lines.
4. **Future pricing** (owner confirmation required):
   - Material area = `letter_face_area_m2` (or `face_vinyl_area_m2`)
   - Oracal 651 EUR/mp, print EUR/mp, lamination EUR/mp, application labor if separate
   - Reuse registry codes `MAT-ORACAL_651`, `MAT-VINYL_PRINT_LAMINATED` only after owner activates for this template

---

## 6. Mounting / premount policy

### Current

- `mounting_template_area_m2` always required in QuoteWizard.
- `MAT-SABLON-MONTAJ` (6 EUR/mp) + `mounting_template_cnc_cut` (1 pass CNC) always run.
- Intake `mounting_type` / `premounting_type` not passed to costing.
- No steel/aluminum **premount bar** material in volumetric owner-confirmed prices (lateral profil is **letter return**, not premount structure).

### Proposed

1. **Capture** `mounting_system` (single enum) in Intake + QuoteWizard.
2. **Conditional costing:**
   - `forex_template` → keep current MAT-SABLON + CNC (PASS path)
   - `direct_wall` → skip sablon material + mounting CNC (Stage 5)
   - `steel_bars` / `aluminum_bars` → require bar length/profile; warn until priced
   - `acm_panel` → captured-only (Stage 5+)
3. **Default recommendation:** **Require operator selection** — do not silently default to `forex_template`. If shop practice is “always Forex unless stated,” document as UI default with visible override.
4. **Owner decision needed:** Is `metal_structure` in intake always steel, or must user pick steel vs aluminum?

---

## 7. Work Intake alignment (implemented)

**Files:** `frontend/src/lib/intakeVolumetricSpec.ts`, `Product001IntakeSpecEditor.tsx`, `intakeProductSpec.ts`, `volumetricQuoteInput.ts`, `backend/validators/intake_product_spec.py`

Work Intake now captures canonical `product_spec_json` fields in **form v1** (`Product001IntakeSpecEditor`): header template identity, 10 numbered sections (produs, dimensiuni, geometrie ofertare, construcție, finisaj, RAL, iluminare, montaj, Vector Studio, pregătire ofertă). Field ownership tags in UI: intake vs prefill vs production vs readiness. Partial specs save without faking geometry or price. JSON keys unchanged.

### 7.1 Canonical Intake → QuoteWizard prefill mapping

| Work Intake field | QuoteWizard / `quote_input` | Prefill rule |
|-------------------|----------------------------|--------------|
| `back_bevel_enabled` / `backing_chamfer` | `back_bevel_enabled` | yes |
| `face_finish_type` / legacy `face_finish` | `face_finish_type` (+ `face_finish_subtype` for Oracal 8500) | yes; 8500 costs as `oracal_651` |
| `face_vinyl_color_code/name`, `face_vinyl_roll_width_mm`, `face_vinyl_finish`, `face_vinyl_notes` | same keys | yes when present |
| `paint_ral_code/name`, `paint_finish`, `paint_tube_count` | same keys | yes when present |
| `selected_psu_watts`, `lighting_notes` | `selected_psu_watts` | yes when present |
| `return_depth_mm`, `width_mm`, `height_mm` | dims + `return_depth_mm` | yes when explicitly set |
| `mounting_system` / legacy `mounting_type`+`premounting_type`+`premount_bar_material` | `mounting_system` | yes |
| `mounting_template_enabled` / legacy premount `none` | `mounting_template_enabled` | yes; **not** mapped to `mounting_system` |
| `mounting_bar_profile`, `mounting_bar_count`, `mounting_bar_length_m`, `mounting_template_area_m2` | same keys | yes when present |
| `letter_face_area_m2`, `letter_perimeter_m`, `letter_count` | same keys | **only if operator entered** — never invented |

**Legacy mapping (read-only compat):**

- `backing_chamfer` → `back_bevel_enabled`
- `face_finish=plexi` → `face_finish_type=none`
- `face_finish=oracal_8500_translucent` → `face_finish_type=oracal_651` + subtype `oracal_8500`
- `mounting_type=direct_wall` → `mounting_system=direct_wall`
- `premounting_type=metal_structure` + `premount_bar_material=steel|aluminum` → `steel_bars` / `aluminum_bars`
- `premounting_type=acm_casetted_panel` → `mounting_system=acm_panel`
- `forex_template` / premount `none` → `mounting_template_enabled=true` only

**Intentionally not prefilled:** `letter_face_area_m2`, `letter_perimeter_m`, `letter_count` unless explicitly in intake; `led_module_count` remains QuoteWizard-derived from perimeter.

### 7.2 Production metadata warnings (soft)

Emitted by `volumetric_quote_input_policy.py` — do **not** block simulate or invent cost:

| Code | When |
|------|------|
| `production_metadata_missing:face_vinyl_color_code` | Oracal or printed vinyl selected |
| `production_metadata_missing:face_vinyl_roll_width_mm` | Oracal 651/8500 without roll 1000/1260 |
| `production_metadata_missing:paint_ral_code` | `paint_tube_count > 0` without RAL code |
| `production_metadata:oracal_8500_priced_as_oracal_651` | subtype `oracal_8500` on costing line |

---

## 8. QuoteWizard alignment gaps

**Missing Step 3 fields:**

| Proposed UI (RO) | Key | Required | If unpriced |
|------------------|-----|----------|-------------|
| Șanfren spate litere | `back_bevel_enabled` | yes (checkbox) | priced Stage 2 |
| Finisaj față | `face_finish_type` | yes (select) | warning Stage 1 |
| Sistem montaj / premontaj | `mounting_system` | yes (select) | conditional |
| Material bare premontaj | `mounting_bar_material` | if bars | warning |
| Profil bară | `mounting_bar_profile` | if bars | warning |
| Lungime bare (ml) | `mounting_bar_length_m` | if bars | warning |
| Tuburi vopsea RAL estimate | `paint_tube_count` | yes | **live** |

**Conditional validation (proposed):**

- `mounting_template_area_m2` required only if `mounting_system === forex_template`
- Bar fields required if `steel_bars` or `aluminum_bars`

---

## 9. Dossier alignment recommendation

| Content | Now | Target |
|---------|-----|--------|
| Allowed face finishes | production notes / hints | `production_notes_json` + variants |
| Allowed mounting systems | template description | dossier section |
| Back bevel optional | intake + rules text | dossier QC/production notes |
| Selected quote values | not stored | **defer** — quote snapshot future |
| paint_tube_count | not in dossier | optional in production notes as “estimate at quote time” |

**Do not overbuild dossier in Stage 1.** Keep template-level “allowed options + production logic.” Quote-specific values stay in `quote_input` / future quote entity.

---

## 10. Staged implementation plan

### Stage 1 — Quote input contract (capture + warnings)

**Goal:** Single contract across types; no pricing for new options; preserve PASS baseline when options = defaults.

| Files likely touched |
|----------------------|
| `frontend/src/api/quotes.ts` (QuoteInputPayload) |
| `frontend/src/lib/volumetricQuoteInput.ts` |
| `frontend/src/lib/intakeProductSpec.ts` + validator |
| `backend` simulate-cost warning emitter (read-only policy helper) |

| Risk | Low if defaults match current costing |
| Tests | extend `volumetricQuoteInput.test.ts`; API smoke unchanged for baseline payload |
| Owner decisions | Default values for new enums; warning copy |

### Stage 2 — Back bevel costing

| Files | `seed_build4_templates.py`, `formula_handlers.py` or op params resolver, tests |
| Risk | **Medium** — changes back_cut line total |
| Tests | Update 135→81 EUR scenario; re-run live smoke |
| Owner | Confirm default `false` vs required checkbox |

### Stage 3 — Work Intake → QuoteWizard prefill

| Files | `Product001IntakeSpecEditor`, `mapProductSpecToVolumetricQuotePrefill`, `QuoteWizard` summaries |
| Risk | Low |
| Tests | intake prefill tests |

### Stage 4 — Face finish pricing

| Files | template materials/ops, registry seeds, pricing |
| Risk | High — new material lines |
| Owner | EUR/mp rules, Oracal vs print vs laminate, application labor |

### Stage 5 — Mounting system pricing

| Files | conditional template ops, new materials (bars), registry |
| Risk | High — changes total when not forex |
| Owner | steel 20×20 price, alu profile, ACM panel scope |

### Stage 6 — Dossier representation

| Files | `BlueprintDossierStudio`, production notes editors |
| Risk | Low |
| Owner | Which options are owner-valid vs experimental |

---

## 11. Risk summary

| Risk | Mitigation |
|------|------------|
| Break PASS costing | Stage 1 defaults = current behavior; Stage 2 behind explicit flag |
| Silent free options | `captured_option_not_priced` warnings from Stage 1 |
| Intake/wizard drift | Canonical enum table + mapping functions |
| Forex template always charged | Stage 5 conditional ops; until then document as known limitation |
| Invented vinyl/bar prices | Stages 4–5 blocked on owner confirmation |

---

## 12. Owner decisions needed (before implementation)

1. **Back bevel default:** `false` with explicit opt-in, or always ask without default?
2. **Mounting default:** require selection vs default `forex_template`?
3. **metal_structure:** steel only, or steel/aluminum sub-choice?
4. **oracal_8500_translucent:** separate priced SKU or alias of 651?
5. **Face finish:** required at quote time or default `none`?
6. **When to price vinyl vs capture-only warning?**

---

## 13. Implemented contract (2026-06-05 — finish / mounting pricing)

### QuoteWizard / `quote_input` fields

| Field | Values | Required | Default |
|-------|--------|----------|---------|
| `face_finish_type` | `none`, `oracal_651`, `printed_vinyl`, `printed_laminated_vinyl` | yes | `none` |
| `mounting_system` | `direct_wall`, `steel_bars`, `aluminum_bars`, `acm_panel` | yes | `direct_wall` |
| `mounting_template_enabled` | boolean | no | `true` (preserves baseline sablon) |
| `mounting_template_area_m2` | number | when template enabled | — |
| `mounting_bar_length_m` | number (ml) | optional override | — |
| `mounting_bar_count` | number | optional | `2` |
| `mounting_bar_profile` | string | when steel/aluminum | `30x30x1.5` |
| `width_mm` | number | Step 2 dims / simulate | enables auto bar length |

**Deprecated:** `mounting_system=forex_template` → `direct_wall` + `mounting_template_enabled=true`.

### Work Intake mapping

| Intake | Quote field |
|--------|-------------|
| `face_finish=oracal_651` | `face_finish_type=oracal_651` |
| `face_finish=print_laminated` | `printed_laminated_vinyl` |
| `face_finish=plexi` | `none` |
| `mounting_type=direct_wall` | `mounting_system=direct_wall` |
| `premounted` + `premounting_type=none` | `direct_wall` + `mounting_template_enabled=true` |
| `premounting_type=metal_structure` | `steel_bars` |
| `premounting_type=acm_casetted_panel` | `acm_panel` |

### Premount bar length rule (implemented `46c8260`)

For `mounting_system=steel_bars` or `aluminum_bars`:

1. **Override:** if `mounting_bar_length_m` is provided, use it as **total bar length** (no width derivation).
2. **Auto default:** else if `width_mm` is available:
   - `assembly_width_m = width_mm / 1000`
   - `mounting_bar_count` defaults to **2** (one bar top, one bar bottom)
   - `total_bar_length_m = assembly_width_m × mounting_bar_count`
3. **Missing input:** if neither `mounting_bar_length_m` nor `width_mm` → `NEEDS_QUOTE_INPUT` on `mounting_bar_total_length` formula (no silent zero).

**Examples (width_mm=4800, profile 30×30×1.5, no override):**

| Material | Total length | Rate | Material cost |
|----------|--------------|------|---------------|
| Steel | 9.6 ml | 2 EUR/ml | **19.20 EUR** |
| Aluminum | 9.6 ml | 3.5 EUR/ml | **33.60 EUR** |

**Override example:** `mounting_bar_length_m=5` → steel **10.00 EUR**, aluminum **17.50 EUR**.

**Count override:** `mounting_bar_count=3` + `width_mm=4800` → 14.4 ml steel → **28.80 EUR** at 2 EUR/ml.

### Profile-specific pricing rule

| Field | Behavior |
|-------|----------|
| `mounting_bar_profile` | Selectable string (e.g. `20x20x1.5`, `30x30x1.5`, `40x40x2`); default **`30x30x1.5`** |
| Known priced profiles | Steel 30×30×1.5 = **2 EUR/ml**; aluminum 30×30×1.5 = **3.5 EUR/ml** (excluding TVA) |
| Unknown profile | Material line **skipped**; warning `mounting_bar_profile_price_missing:<steel\|aluminum>:<profile>` — **no silent fallback** to 30×30×1.5 |

`mounting_bar_material` is derived from `mounting_system` (`steel_bars` → steel, `aluminum_bars` → aluminum).

### QuoteWizard validation (steel/aluminum bars)

- `mounting_bar_length_m` is **optional** when `width_mm` exists (label: *Lungime totală bare premontaj override*).
- Helper: *Dacă este gol, se calculează automat: lățimea ansamblului × număr bare (implicit 2: sus + jos).*
- `mounting_bar_count` optional, default **2** (*Număr bare premontaj*).
- `mounting_bar_profile` visible for steel/aluminum; default **30x30x1.5**.
- Validation error if neither `width_mm` nor `mounting_bar_length_m`: *Pentru bare premontaj este necesară lățimea ansamblului sau o lungime totală introdusă manual.*
- `direct_wall` and `acm_panel` do **not** require bar length or profile.

### ACM panel — separate template rule

`mounting_system=acm_panel`:

- Option remains **captured** in QuoteWizard.
- **No material cost** invented inside TPL-VOLUMETRIC-LETTERS.
- **No dimensions** derived from letter `width_mm` / `height_mm`.
- Warning: `captured_option_requires_separate_template:mounting_system=acm_panel`
- ACM/Alucobond casetted panel must be calculated as a **separate template/product** with its own dimensions (usually **larger** than the letter assembly).

Forex mounting template (`mounting_template_enabled`) remains **optional and independent** from `mounting_system`.

### Warnings policy

- **Production metadata (soft):** `production_metadata_missing:*` — Oracal color/roll, paint RAL when tubes present; simulate allowed.
- Priced face finishes: no `captured_option_not_priced` for `face_finish_type`.
- Priced bar profiles: `mounting_labor_not_priced:mounting_system=steel_bars|aluminum_bars` (material only; no mounting labor pricing).
- Unknown profile: `mounting_bar_profile_price_missing:<material>:<profile>` — no invented rate.
- `acm_panel`: `captured_option_requires_separate_template` — separate template required.
- **Readiness gate:** `letters_vector_file_required` remains; `ready_for_quote=false` until vector policy satisfied.

---

## Appendix — Live PASS reference (Product 001)

```
quote_input: width 4800, height 600, depth 60, letter_face_area_m2 2.88,
  letter_perimeter_m 18, letter_count 9, return_depth_mm 60,
  selected_psu_watts 100, mounting_template_area_m2 2.88, paint_tube_count 3,
  led_module_count 180 (derived), back_bevel_enabled false,
  face_finish_type none, mounting_system direct_wall, mounting_template_enabled true

Result: simulated, is_valid true, blockers [], total 844.41 EUR (baseline unchanged)
```

**Deltas (2.88 m² face):** oracal_651 +23.04 EUR; printed_laminated_vinyl +37.44 EUR; template disabled ≈ −44.28 EUR; steel 5 m +10 EUR; aluminum 5 m +17.5 EUR.

Operation line totals (default, no back bevel): PREPRESS 18, face CNC 54, **back CNC 81**, mounting CNC 27, side 90, bond 126, LED 9, electrical 18, paint 72, pack 28.8, MAT-VOPSEA 30 (3 tubs).

With `back_bevel_enabled: true`: back CNC **135**, labour **577.80**, total **898.41** EUR.

---

## Blueprint Dossier (template-level)

**Seed:** `backend/seeds/seed_tpl_volumetric_letters_dossier.py`  
**Runner:** `backend/scripts/seed_tpl_volumetric_letters_dossier.py`  
**Status:** `approved` (structural mapping + production rules; no quote-specific values)

**Version:** `DOSSIER_VERSION=2` — task order: vector check → prepress → CNC → forming → paint → vinyl (conditional) → LED → electrical → mounting template (conditional) → bars (conditional) → ACM separate-template note → QC internal → packaging.

Documents allowed options: `back_bevel_enabled`, `face_finish_type`, `mounting_template_enabled`, `mounting_system`, `mounting_bar_profile`, Oracal/RAL production metadata, ACM separate-template rule, QC internal-only, vector/file policy.

**Readiness after seed (dev.db):**

| Warning | After seed |
|---------|------------|
| `blueprint_dossier_missing` | cleared |
| `costengine_mapping_missing_no_dossier` | cleared |
| `output_blocks_missing` | cleared |
| `task_rules_missing` | cleared |
| `letters_vector_file_required` | **remains** (expected) |

`ready_for_quote` stays `false` until vector/file + any remaining policy gates — not bypassed by dossier alone.

---

## API smoke (2026-06-06, dev.db, backend restarted)

| Case | Total EUR | Blockers | Key warnings |
|------|-----------|----------|--------------|
| Baseline direct_wall + template | **844.41** | none | `letters_vector_file_required`, `production_metadata_missing:paint_ral_code` |
| Oracal 651 + color + roll 1260 | **867.45** (+23.04) | none | metadata OK for vinyl |
| Oracal 651 missing metadata | **867.45** | none | `production_metadata_missing:face_vinyl_*` |
| Steel bars 30×30×1.5, width 4800 | **863.61** (+19.20) | none | `mounting_labor_not_priced` |
| Unknown profile 40×40×2 | **844.41** | none | `mounting_bar_profile_price_missing` |
| ACM panel | **844.41** | none | `captured_option_requires_separate_template` |

All cases: `persisted=false`, `ready_for_quote=false`, no quote/order created.

---

## 13. Vector / DWG / SVG readiness flow (2026-06-06)

### Policy (TPL-VOLUMETRIC-LETTERS)

| Layer | Behavior |
|-------|----------|
| Template readiness (`/product_system/readiness/{id}`) | Always warns `letters_vector_file_required` until intake context supplied |
| Intake readiness (`?intake_id=`) | Evaluates `product_spec_json` vector metadata via `volumetric_vector_readiness_policy` |
| Preliminary simulate | Allowed without vector (`preliminary_simulation_without_vector=true`) |
| Final quote | Requires vector gate satisfied — not bypassed |

### Accepted file types

| Type | File presence | Auto analysis | Quote vector gate |
|------|---------------|---------------|-------------------|
| **SVG** | yes | Yes — `SvgLayerAnalysisService` (layers/metrics); no letter_count auto-fill | `analyzed` or `manual_review_approved` |

**CorelDRAW SVG exports:** files may include `<!DOCTYPE svg ...>`. WorkOS keeps the **original upload unchanged** and runs analysis on a **sanitized copy** that strips DOCTYPE/ENTITY declarations only (no DTD fetch, no entity expansion, geometry untouched). Successful sanitized analysis returns `parse_status=parsed_sanitized` and warning `svg_sanitized_doctype_removed`. Sanitized analysis does **not** auto-trust geometry — generic layers (e.g. `Layer_x0020_1`) stay unmapped; `*_bari.svg` support files must not supply letter metrics unless layers are explicitly mapped.
| **DXF** | yes | **No parser** | `manual_review_approved` or `vector_manual_review_required` warning |
| **DWG** | yes (source attachment) | **No parser** | `manual_review_approved` or `dwg_analysis_not_supported` + manual review warning |
| **other** | yes | No | `vector_file_type_unsupported` + manual review |

**Hard rule:** geometry (`letter_face_area_m2`, `letter_perimeter_m`, `letter_count`) is **never** invented from filename or unparsed DWG/DXF.

### Work Intake `product_spec_json` fields

- `vector_file_present`, `vector_file_name`, `vector_file_url`, `vector_attachment_id`
- `vector_file_type`: `svg` \| `dxf` \| `dwg` \| `other`
- `vector_analysis_status`: `not_provided` \| `attached_unanalyzed` \| `analyzed` \| `analysis_failed` \| `manual_review_approved`
- `vector_manual_review_approved`, `vector_manual_review_notes`
- `vector_metrics_source`, `vector_layer_mapping_status`
- `svg_layer_mappings` — operator manual layer name → target (`TPL-VOLUMETRIC-LETTERS`, `support_bars`, `mounting_reference`, `ignore`)

### Warning / blocker codes

| Code | When |
|------|------|
| `letters_vector_file_required` | No file metadata on intake |
| `dwg_analysis_not_supported` | DWG present — informational even when gate satisfied |
| `dxf_analysis_not_supported` | DXF present without analysis |
| `vector_manual_review_required` | DWG/DXF/unanalyzed SVG/other without manual approval |
| `vector_analysis_pending` | SVG attached, analysis not run |
| `vector_analysis_failed` | SVG parser failed |
| `vector_file_type_unsupported` | `other` without manual approval |
| `vector_layer_mapping_failed` | SVG analyzed but layer mapping failed |
| `vector_layer_mapping_pending` | SVG analyzed but primary letters layer not mapped |

### Clears `letters_vector_file_required`

- Intake has retrievable file metadata (`vector_file_present` or `vector_file_name` / url / attachment id)
- Does **not** alone set `ready_for_quote=true` — PSU/profile variant warnings and dossier gates remain

### Implementation

- `backend/services/volumetric_vector_readiness_policy.py`
- `backend/services/svg_sanitization_service.py` — DOCTYPE-safe analysis copy for CorelDRAW SVG
- `ProductReadinessService.evaluate(template_id, product_spec=None)`
- Readiness API: optional `intake_id` query loads intake spec
- `Product001IntakeSpecEditor` — Fișier vector / producție section (metadata only; no upload duplication)
- Dossier v2 `quote_readiness_json.vector_analysis_policy` + `vector_file_verification` task notes

### Smoke (dev, 2026-06-06)

| Case | Result |
|------|--------|
| A — template, no intake | `letters_vector_file_required`, simulate **844.41 EUR** |
| B — DWG metadata | `dwg_analysis_not_supported`, `vector_manual_review_required`, gate false |
| C — DWG + manual review | gate satisfied; `letters_vector_file_required` cleared; `ready_for_quote` still false (PSU/profile warnings) |
| D — SVG analyzed | gate satisfied; geometry not invented |
| E — other type | `vector_file_type_unsupported` |

Unit tests: `tests/test_volumetric_vector_readiness_policy.py` (18 cases). Frontend: `intakeVolumetricSpec.test.ts` vector metadata tests.

---

## 14. Vector Studio — multi-layer workflow (2026-06-05)

### Preferred operator workflow

| Principle | Rule |
|-----------|------|
| **One file, many layers** | Preferred: a single SVG/DXF/DWG with letters, support bars, mounting refs, and helper layers. Separate files per layer are allowed but **not required**. |
| **Preview ≠ pricing** | Vector Studio preview is orientative only. CostEngine totals use `quote_input` metrics entered or explicitly trusted — never preview pixels. |
| **Mapping ≠ geometry** | Layer role mapping (`svg_layer_mappings`) does not invent `letter_face_area_m2`, `letter_perimeter_m`, or `letter_count`. |
| **Parsed ≠ quote-ready** | `parse_status=parsed_sanitized` clears parser risk only; readiness still requires letters layer mapped + manual review or trusted metrics. |
| **Support bars** | `support_bars` layers are production reference only — never letter geometry for costing. |
| **Ignore** | `ignore` on helper/guide layers does not block mapping review once explicitly set. |

### Layer mapping targets (`svg_layer_mappings`)

| Target | Meaning |
|--------|---------|
| `TPL-VOLUMETRIC-LETTERS` | Primary letters / main graphics layer (only this satisfies letters vector mapping gate) |
| `support_bars` | Rear bars / support structure — visible in studio, no CostEngine letter metrics |
| `mounting_reference` | Mounting / positioning reference — orientative |
| `ignore` | Guides, dimensions, cotes — excluded after explicit operator choice |

### Vector Studio UI (Work Intake Product001)

**Component:** `frontend/src/components/workos/VectorStudioPanel.tsx` (section title: *Fișier vector / producție*).

| Area | Behavior |
|------|----------|
| File metadata | Name, type, parse status, sanitization note |
| Preview | Safe SVG via `preview_svg` from analysis API (`data:image/svg+xml`); scripts/DOCTYPE blocked; DWG/DXF placeholder |
| Info under preview | Layers count, letters layer mapped/missing, metrics or *Nu s-au extras metrici geometrice automat.* |
| Layer table | Per-layer dropdown + role explanation; multiple mappings in one analyze request |
| Manual review | `vector_manual_review_approved` + notes — does not invent geometry |
| Disclaimer | *Preview-ul este orientativ. Calculul de ofertă folosește doar metrici extrase valid sau valori introduse manual.* |

### Persisted analysis summary (`product_spec_json`)

On analyze + save, Work Intake persists **safe summary only** (no raw SVG, no `preview_svg` blob):

| Field | Purpose |
|-------|---------|
| `vector_parse_status` | Last parse result (`parsed` / `parsed_sanitized` / `failed`) |
| `vector_analysis_warnings` | Sanitization/analysis warnings (e.g. DOCTYPE removed) |
| `vector_detected_layers_summary` | Per-layer name, mapping status, `mapped_by`, target — no geometry metrics |
| `vector_preview_available` | Boolean — preview was available in last session; content is **not** stored |
| `svg_layer_mappings` | Operator manual mappings — always visible after refresh |

**Preview policy:** `preview_svg` is session-only (from analyze API). After refresh, UI explains that SVG content is not stored and operator must re-analyze for preview. Saved `svg_layer_mappings` and summary remain coherent — UI must not show “Layere detectate: 0” when mappings exist.

### Backend API additions

- `POST /vector-assets/analyze-layers` accepts `manual_layer_mappings` with **multiple** entries in one request.
- Response includes `preview_svg` (sanitized analysis copy, `svg_preview_service.build_safe_svg_preview`).
- `derive_vector_layer_mapping_status` returns `pending` unless `TPL-VOLUMETRIC-LETTERS` is mapped (support-only mappings insufficient).

### Readiness recap

| State | `vector_layer_mapping_status` / warnings | `ready_for_quote` |
|-------|------------------------------------------|-------------------|
| No vector file | `letters_vector_file_required` | false |
| File present, no letters layer mapped | `vector_layer_mapping_pending` | false |
| Letters mapped, no trusted geometry / no manual approval | `vector_manual_review_required` | false |
| Letters mapped + `vector_manual_review_approved=true` | vector gate clears | still depends on PSU/profile/dossier gates |
| Only `support_bars` mapped | letters mapping still pending | false |
| Helper layers set to `ignore` | do not block after explicit ignore | — |

### CostEngine regression (unchanged)

Manual baseline payload simulate remains **844.41 EUR** — separate from SVG analysis; no SVG-derived pricing in this workflow.

---

## 15. Final commercial quote readiness gate (2026-06-05)

### Three distinct states

| State | Meaning | API field |
|-------|---------|-----------|
| **Simulation-ready** | CostEngine can calculate with provided `quote_input`; no cost blockers | `simulate_ready` |
| **Quote-ready (dossier)** | Blueprint dossier approved; template active; ProductReadinessService sections ready | `ready_for_quote` |
| **Commercial quote** | All final blockers cleared; quote persistence allowed | `can_create_commercial_quote` |

`simulate_ready=true` while `can_create_commercial_quote=false` is **expected** for manual baseline payloads without vector intake context.

### Policy implementation

- `backend/services/volumetric_quote_ready_policy.py` — `evaluate_volumetric_quote_ready()`
- Wired into `POST /api/v1/product-system/simulate-cost` as `readiness.quote_gate`
- Enforced on `POST /entities/quotes/price` and `POST /entities/quotes/{id}/price` via `_assert_commercial_quote_gate()`
- Optional `intake_id` loads `product_spec_json` for vector/file gates

### Final quote blockers (TPL-VOLUMETRIC-LETTERS)

| Category | Blocker | Notes |
|----------|---------|-------|
| Vector | `letters_vector_file_required` | No vector file metadata |
| Vector | `vector_layer_mapping_pending` | Primary letters layer not mapped to `TPL-VOLUMETRIC-LETTERS` |
| Vector | `vector_manual_review_required` | No manual review and no trusted extracted geometry |
| Vector | `vector_analysis_failed` | Parse failed without manual approval |
| Geometry | `quote_input_missing:*` | `width_mm`, `height_mm`, depth, `letter_face_area_m2`, `letter_perimeter_m`, `letter_count`, PSU, mounting template/bars as applicable |
| Metadata | `production_metadata_missing:face_vinyl_color_code` | Oracal selected |
| Metadata | `production_metadata_missing:face_vinyl_roll_width_mm` | Oracal selected |
| Metadata | `production_metadata_missing:paint_ral_code` | `paint_tube_count > 0` |
| Capture | `captured_option_requires_separate_template:mounting_system=acm_panel` | ACM requires separate template |
| Capture | `mounting_bar_profile_price_missing:*` | Unknown bar profile |
| Dossier | `ready_for_quote:false`, section blockers | Blueprint dossier not approved |

### Warnings only (do not block commercial quote)

- Mounting notes missing
- `oracal_8500_priced_as_651` informational subtype
- CostEngine `needs_review` registry lines (unless escalated to cost blocker)
- Internal-only QC operations

### Vector / manual review rule

- Layer mapping **does not** satisfy geometry gate.
- `vector_manual_review_approved=true` clears vector gate but geometry must still be in `quote_input`.
- Preview SVG and persisted analysis summary are **not** trusted geometry.

### Frontend (QuoteWizard)

- **Simulare preliminară** — read-only `simulate-cost`; always shows breakdown when CostEngine succeeds.
- **Creează ofertă comercială** — disabled unless `can_create_commercial_quote=true`; grouped blocker panel (vector, geometrie, costuri, metadate, dossier).
- Work Intake Vector Studio shows readiness hint; manual review message when approved.

### Error on blocked commercial quote

HTTP 422: `Template-ul nu este pregătit pentru ofertă comercială. Rezolvă blocker-ele de readiness.`

Unit tests: `tests/test_volumetric_quote_ready_policy.py`. Frontend: `volumetricQuoteReady.test.ts`.

---

## 16. Process reference vs product-specific scope

| Question | Answer for this document |
|----------|--------------------------|
| Este `TPL-VOLUMETRIC-LETTERS` model universal? | **Nu** — este referință de **proces** matură și documentație de **produs** pentru litere volumetrice 3D |
| Ce preia un template nou din volumetric? | Disciplina: dossier → registry → CostEngine → intake → readiness → quote gate → tests/smoke |
| Ce nu preia automat? | CNC/perimetru, tuburi vopsea, Oracal/RAL, bare premontaj, vector gate, lista operații/materiale, layout QuoteWizard Product 001 |
| Unde e procesul universal? | `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` — **secțiunea 2** |
| Regulă agent/Cursor | Pornește din playbook; adaptează regulile product-specific; nu copia valori volumetrice fără confirmare owner |

Fiecare template viitor necesită propriul audit (`TPL_<CODE>_INPUT_CONTRACT_AUDIT.md` sau echivalent) înainte de pricing sau quote logic.
