# FROZEN_MATERIAL_SOURCE_TRACE_MATRIX

**Path audited:** Component / module → ProductDefinition `material_roles` → ProductAggregate `materials` → Quote/Order Snapshot V2 → ExecutionPlan GET attach → Ops-graph  
**Fixture:** order `92401` · snapshot `QSN2-2026-0001` · template `TPL-VOLUMETRIC-LETTERS_v2`  
**Counts:** PA materials **22** · PD material_roles **24** · ops-graph entries **22** · quantity null **22** · false zero **0**

## Trace table (22)

| # | material_code | label (short) | unit | qty | formula_id | component_ref | provenance | template / module path | duplicate group | variant discriminator | ownership class | semantic status | planning future? |
|---|---------------|---------------|------|-----|------------|---------------|------------|------------------------|-----------------|------------------------|-----------------|-----------------|------------------|
| 0 | MAT-ACP-FATA-LITERE | Față plexi/ACP | mp | null | letter_face_area | comp_face_litere | parent | Parent letters face | — | face substrate | COMPONENT_OWNED | technical requirement; qty incomplete | YES if active finish path |
| 1 | MAT-ORACAL-651 | Oracal față | mp | null | face_vinyl_used_sqm | comp_face_litere | parent | Parent face finish | ORACAL×2 | face vinyl vs return wrap | COMPONENT_OWNED | finish alternative candidate | YES if Oracal face selected |
| 2 | MAT-VINYL-PRINT | Print față | mp | null | face_vinyl_used_sqm | comp_face_litere | parent | Parent face finish | face-vinyl family | print alt | COMPONENT_OWNED | finish alternative | YES if print selected |
| 3 | MAT-VINYL-PRINT-LAMINATED | Print+lam față | mp | null | face_vinyl_used_sqm | comp_face_litere | parent | Parent face finish | face-vinyl family | laminated alt | COMPONENT_OWNED | finish alternative | YES if laminated selected |
| 4 | MAT-PROFIL-LATERAL-LITERE | Profil lateral generic | ml | null | letter_perimeter | comp_lateral_litere | parent | Parent lateral | PROFILE family | generic vs sized | COMPONENT_OWNED | may overlap sized variants | OWNER filter needed |
| 5 | MAT-SPATE-PVC-LITERE | Forex spate | mp | null | letter_face_area | comp_spate_litere | parent | Parent back | — | — | COMPONENT_OWNED | requirement | YES |
| 6 | MAT-LED-MODULE | Module LED | buc | null | led_per_letter | comp_led_litere | parent | Parent LED | — | — | COMPONENT_OWNED | requirement | YES |
| 7 | MAT-LED-PSU-12V | Surse LED | buc | null | psu_count | comp_led_litere | parent | Parent LED | — | — | COMPONENT_OWNED | requirement | YES |
| 8 | MAT-VOPSEA-RAL | Vopsea RAL (parent) | buc | null | ceil_quote_input_quantity | comp_finisaj_litere | parent | Parent finish | VOPSEA×2 | parent finish vs return paint | COMPONENT_OWNED / PRODUCT_COMPOSITION | consumable; qty model unclear | CONDITIONAL |
| 9 | MAT-SABLON-HARTIE | Șablon hârtie | mp | null | letter_face_area | comp_finisaj_litere | parent | Parent finish | — | — | COMPONENT_OWNED | requirement | YES |
| 10 | MAT-SABLON-MONTAJ | Șablon Forex | mp | null | letter_face_area | comp_finisaj_litere | parent | Parent finish | — | — | COMPONENT_OWNED | requirement | YES |
| 11 | MAT-CONSUMABILE-MONTAJ | Consumabile | set | null | **null** | comp_finisaj_litere | parent | Parent finish | — | set without formula | UNKNOWN_NEEDS_OWNER / ORDER_CONFIGURATION | reference / incomplete | Model D until formula |
| 12 | MAT-PROFIL-LATERAL-LITERE-30MM | Profil 30 mm | ml | null | return_profile_linear_meter | node:volum_aluminum…comp_volum_aluminiu_module | linked_module | TPL-VOLUM-ALUMINIU_v1 | PROFILE sizes | depth 30 | COMPONENT_OWNED | size variant | YES **only active depth** |
| 13 | MAT-PROFIL-LATERAL-LITERE-60MM | Profil 60 mm | ml | null | return_profile_linear_meter | same module | linked_module | TPL-VOLUM-ALUMINIU_v1 | PROFILE sizes | depth 60 | COMPONENT_OWNED | size variant | YES only active |
| 14 | MAT-PROFIL-LATERAL-LITERE-80MM | Profil 80 mm | ml | null | return_profile_linear_meter | same module | linked_module | TPL-VOLUM-ALUMINIU_v1 | PROFILE sizes | depth 80 | COMPONENT_OWNED | size variant | YES only active |
| 15 | MAT-PROFIL-LATERAL-LITERE-100MM | Profil 100 mm | ml | null | return_profile_linear_meter | same module | linked_module | TPL-VOLUM-ALUMINIU_v1 | PROFILE sizes | depth 100 | COMPONENT_OWNED | size variant | YES only active |
| 16 | MAT-ORACAL-651 | Oracal return wrap | mp | null | return_wrap_area | volum_aluminum module | linked_module | TPL-VOLUM-ALUMINIU_v1 | ORACAL×2 | return wrap vs face | COMPONENT_OWNED | same code, different provenance | YES if return wrap finish |
| 17 | MAT-VOPSEA-RAL | Vopsea return | buc | null | return_paint_consumption | volum_aluminum module | linked_module | TPL-VOLUM-ALUMINIU_v1 | VOPSEA×2 | return paint | COMPONENT_OWNED | same code, different provenance | YES if return paint finish |
| 18 | MAT-ADEZIV-CANT-LITERE | Adeziv cant | ml | null | return_profile_adhesive | volum_aluminum module | linked_module | TPL-VOLUM-ALUMINIU_v1 | — | — | COMPONENT_OWNED | requirement | YES |
| 19 | MAT-ACM-BOND-PANEL | ACM față panel | mp | null | rectangular_panel_area | mounting_panel…comp_acm_panel_face | linked_module | TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 | ACM×2 | face panel | COMPONENT_OWNED | panel face | YES |
| 20 | MAT-ACM-BOND-PANEL | ACM canturi | mp | null | letter_face_area | mounting_panel…comp_casetted_returns | linked_module | TPL-ACM-… | ACM×2 | cassette returns | COMPONENT_OWNED | different component | YES |
| 21 | MAT-SURUBURI-GEN | Suruburi | set | null | **null** | mounting_panel…comp_mounting_fasteners | linked_module | TPL-ACM-… | — | set without formula | UNKNOWN_NEEDS_OWNER | reference / incomplete | Model D until formula |

### PD-only roles (not in PA materials)

| material_code | Why absent from PA/ops-graph | Status |
|---------------|------------------------------|--------|
| MAT-PREMOUNT-BAR-ALUMINUM | Module `structura_suport` inactive/pending | Correctly excluded from frozen PA list |
| MAT-PREMOUNT-BAR-STEEL | Same | Correctly excluded |

---

## Mandatory Q&A

1. **Where is each material born?** Component Template / linked module material roles → ProductDefinition roles → ProductAggregate materials freeze → Order Snapshot V2. Ops-graph only **reads** the freeze.
2. **Who owns the code?** Product/Component template material identity (`material_code`).
3. **Who owns the unit?** Same technical definition path (unit present on all 22).
4. **Who should own quantity?** Prefer **component-owned formula evaluation** at Product Truth / Aggregate compile time, then freeze (Model A). Composition-only where multi-component (Model B). Operator confirm only where formula insufficient (Model C). Set consumables without formula → Model D until owner defines.
5. **Can qty be calculated from existing truth?** **Partially** — 20/22 have `formula_id` names, but frozen snapshot stores `quantity: null` (inputs/evaluation not persisted). Geometry/config inputs exist in PD (`geometry_inputs`, canonical values) but not proven evaluated into these 22 rows.
6. **Null quantity meaning?** **Incomplete technical freeze / acceptable honesty gap** — not “zero”, not stock absence. Two rows lack even `formula_id` → stronger incompleteness.
7. **Duplicates classification:**
   - ORACAL / VOPSEA ×2 → **same code with different component provenance** (face vs return) — legitimate parallel emissions until active-finish filter.
   - ACM ×2 → **same code with different component provenance** (panel face vs cassette returns).
   - Profile 30/60/80/100 + generic → **same family with different size/lateral variant** (+ possible generic overlap) — **OWNER_DECISION_REQUIRED** for active depth.
   - Not proven accidental duplicates; do not auto-sum by code.
8. **Component-level material contract?** **Partial** — roles carry component_ref + formula_id; quantity contract incomplete.
9. **Material logic wrongly on Product Template?** Composition nodes host linked_module emissions; parent also emits finish materials. **Risk of Product Template composition emitting alternatives as concurrent requirements** — needs ownership contract, not silent delete.
10. **Dedupe / sum / null→0 rules?** Ops-graph display preserves 22 rows; null→Nespecificată; **no null→0** observed. No aggregator merge by code on this surface.
11. **Live lookup post-freeze?** Frozen materials attach reads **order snapshot** (not live inventory/pricing) — deviation risk low for this surface. Inventory/pricing live paths exist elsewhere and must stay out.
12. **Material → operation association demonstrable?** **No** — `material_inputs=[]` on all 18; no persisted readiness inputs; similar names only.
13. **Names vs real association contract?** **Names/similarity only** — no binding contract in envelope.
14. **Future planning requirements?** Geometry-driven BOM with formula_id once qty+active variant resolved (most rows). Premount bars only if module activated.
15. **Technical references only?** Consumables/screws without formula; inactive-module roles; possibly non-selected finish alternatives after Owner filter.

---

## Component-owned truth gate (families)

| Family | Class | Gap resolution locus |
|--------|-------|----------------------|
| Face substrate / vinyl finishes | COMPONENT_OWNED (+ active finish config) | Face component + Product Truth finish selection |
| Lateral / return profile | COMPONENT_OWNED (depth config) | Return/volum aluminum component; active depth |
| Back PVC | COMPONENT_OWNED | Back component |
| LED + PSU | COMPONENT_OWNED | LED component |
| Finish paint/template | COMPONENT_OWNED / PRODUCT_COMPOSITION_OWNED | Finish component; avoid double count with return paint |
| Return wrap/paint/adhesive | COMPONENT_OWNED | Volum aluminum linked module |
| ACM panel / cassette / fasteners | COMPONENT_OWNED | Mounting panel child template |
| Consumables / screws (no formula) | UNKNOWN_NEEDS_OWNER | Owner formula or Model D reference-only |
| Inventory stock | INVENTORY_OWNED *(availability only)* | Must not invent technical qty |
| Market price | PRICING_OWNED | Separate registry track |

**Rejected as technical qty source:** Model E (inventory-derived quantity).
