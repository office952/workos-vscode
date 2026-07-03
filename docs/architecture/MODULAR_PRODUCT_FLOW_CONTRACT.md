# Modular Product Flow Contract

**Version:** 1.0.0  
**Status:** Architectural contract (documentation-first)  
**Scope:** Intake V6 → ProductDefinition → ProductSystem → Cost Engine → Quote → Order → Tasks  
**Pilot product:** `TPL-VOLUMETRIC-LETTERS_v2` (litere volumetrice)

---

## 1. Purpose

Define a **single canonical contract** so the same product information flows without loss from:

- Intake V6 Form System
- ProductDefinition
- ProductSystem parent template
- ProductSystem dossier
- ProductSystem linked modules
- Cost Engine
- Quote / Offer
- Order snapshot
- Task Preview / Execution Plan

Goals:

- Same Romanian business terms and canonical keys everywhere
- No dead components, materials, or operations
- No form fields that do not reach cost or production
- No UI-only pricing separate from quote pricing (target state)
- No task generation from parallel catalogs (target state)
- Real modularity via **mini-modules** reusable across product families

This document does **not** define prices. Prices come from `inventory_materials` and `workcenter_rates` registries only.

---

## 2. Current problem

Confirmed by forensic audits (2026-06-30):

| Issue | Evidence |
|-------|----------|
| DB not corrupted | `TPL-VOLUMETRIC-LETTERS_v2` identical in good backup and current DB |
| Parent template minimal | `components_json=[]`, 1 SVG op, 2 sablon materials |
| Dossier has full structure | 5 components, costengine mapping, task_rules — **audit-only today** |
| Linked modules exist | `TPL-VOLUM-ALUMINIU_v1` (required), `TPL-METAL-PREMOUNT-STRUCTURE_v1` (optional) |
| UI shows `comp_auto_1` | `parseTemplateComponentsWithLegacy` synthesizes when parent empty |
| Intake V6 preview ≠ quote | Client offer ~6324 RON; draft quote `grand_total=0` until `/price` |
| Cost Engine reads parent BOM | Repricing fails or prices only sablon lines without aggregate expansion |
| Task preview parallel source | V3 operation catalog, not priced ProductDefinition |

Root cause: **6+ parallel contracts** without a shared aggregate read model.

---

## 3. Canonical flow

```
Intake V6 Form (mini-modules)
    ↓ workspace payload + quote_input
ProductDefinition builder
    ↓ canonical ProductDefinition
ProductAggregate (read model: parent + dossier + modules)
    ↓ expanded BOM
Cost Engine (preview dry_run = POST /price path)
    ↓ CostResult + commercial transform
Quote priced snapshot
    ↓ accept + convert
Order frozen snapshot
    ↓ explicit approval
Task Preview / Execution Plan (from ProductDefinition processes)
```

**Rules:**

1. ProductSystem defines product structure, not commercial markup.
2. Cost Engine calculates internal cost; does not mutate product.
3. Quotes apply commercial rules; do not embed formulas.
4. Orders freeze snapshot; do not recalculate.
5. Missing data must be explicit — no silent fallbacks.

---

## 4. Canonical terminology

| Romanian label | canonical_key | Primary workspace path | quote_input key | Status (v2 today) |
|----------------|---------------|------------------------|-----------------|-------------------|
| Produs | `product_id` | `product_binding.template_code` | `template_code` | aligned |
| Template | `template_code` | same | same | aligned |
| Dimensiuni SVG | `width_mm`, `height_mm`, `depth_mm` | `client`, `quote_geometry` | same | aligned |
| Suprafață | `letter_face_area_m2` | `quote_geometry` | same | partial (no parent BOM) |
| Perimetru | `letter_perimeter_m` | geometry sync | same | aligned |
| Număr litere | `letter_count` | metrics | same | aligned |
| Față | `face_finish_type` | `finish_setup` | same | mismatch (UI vs parent) |
| Debitare față | `face_cnc_cut` | — | operation_flags | pricing-only (breakdown) |
| Spate | `backing_mode` | `finish_setup` | same | partial |
| Debitare spate | `back_cut` | `back_bevel_enabled` | same | pricing-only |
| Cant/lateral | `return_depth_mm`, `return_finish_type` | `finish_setup` | same | partial (child module) |
| Modelare cant | `RETURN_PROFILE_MACHINE_FORMING` | return fields | same | linked_module |
| Volum/profil | `return_material_perimeter_ml` | computed | same | aligned |
| LED | `led_module_count` | `finish_setup` | same | partial |
| Sistem LED | `lighting_system_type` | `finish_setup` | same | aligned |
| Sursă alimentare | `selected_psu_watts`, `psu_configuration` | `finish_setup` | same | partial |
| Electrică litere | `electrical_letters` | — | derived | task-only in dossier |
| Electrică logo | `emblem_led_*`, `emblem_lighting_mode` | `finish_setup` | same | **OPEN QUESTION** — separate op? |
| Cablare | `electrical_wiring` | — | — | task-only docs |
| Șablon montaj | `mounting_template_area_m2` | `finish_setup` | same | aligned (parent mats) |
| Colantare față | `face_vinyl_*` | `finish_setup` | same | pricing-only |
| Finisaj | `letter_group_finishes` | `finish_setup` | same | mismatch |
| Culoare | `paint_ral_code`, `face_vinyl_color_code` | groups | same | partial |
| Material | `material_code` | — | — | duplicate lists |
| Grosime | `return_depth_mm`, `backing_thickness_mm` | finish | same | aligned |
| Operație | `operation_code` | — | operation_flags | mismatch naming |
| Cost intern | `cost_result.net` | offer (client) | — | duplicate paths |
| Markup/marjă | `markup_percent` | `commercial_inputs` | — | mismatch vs template default |
| TVA | `vat_percent` | `commercial_inputs` | — | aligned |
| Preț ofertat | `grand_total` | offer calc | — | mismatch (6324 vs 0) |
| Quote snapshot | `line_items` wrapper | — | notes.snapshot | partial |
| Order snapshot | `snapshot_line_items` | — | — | blocked until priced |
| Task | `task_code` | — | — | 3 sources |
| Utilaj/resursa | `machine_type` | — | — | partial |
| Workcenter | `workcenter` | — | — | registry |
| Skill | `task_type` | — | — | BLK-08 enum |
| Angajat eligibil | — | — | — | `operational_registry` — not wired to intake |

---

## 5. Mini-module schema

Each mini-module MUST declare:

| Field | Description |
|-------|-------------|
| `module_code` | Stable snake_case identifier |
| `business_name_ro` | Operator-facing label |
| `supported_product_families` | e.g. `litere_volumetrice` |
| `purpose` | One-line scope |
| `form_fields` | → canonical keys |
| `svg_inputs` | Keys derived from analyzer |
| `operator_confirmations` | Required confirmations |
| `computed_outputs` | quote_input keys produced |
| `product_definition_output` | component_id, processes, materials |
| `product_system` | parent component_ref and/or linked child template |
| `dossier_section` | Reference into sections_json |
| `material_requirements` | material_code, formula_id, gates |
| `finish_options` | Allowed finish variants |
| `operations` | operation_code, workcenter, priced flag |
| `cost_inputs` | Required quote_input keys |
| `price_sources` | `inventory_materials`, `workcenter_rates` |
| `quote_output` | cost line types |
| `order_snapshot_output` | frozen processes/materials |
| `task_outputs` | task_name, task_type, priced_operation |
| `required_skills` | operational_registry operation keys |
| `required_workcenters` | WC codes |
| `required_resources` | machine registry refs |
| `eligible_employee_resolution` | `get_eligible_employees_for_operation` |
| `dependencies` | Other module_code values |
| `validation_rules` | Fail-closed checks |
| `warnings_blockers` | Non-fatal vs fatal |

---

## 6. Volumetric letters module map

| # | module_code | Role | Child template |
|---|-------------|------|----------------|
| 1 | `geometry_svg` | SVG upload, layer roles, geometry | parent gate op |
| 2 | `debitare_fata` | Face CNC, vinyl path | dossier `comp_face_litere` |
| 3 | `debitare_spate` | Back panel, bevel | dossier `comp_spate_litere` |
| 4 | `modelare_cant` | Return profile forming | `TPL-VOLUM-ALUMINIU_v1` |
| 5 | `sistem_led` | LED modules/strips | dossier `comp_led_litere` |
| 6 | `electrica_litere` | Wiring per letter | dossier op `electrical_letters` |
| 7 | `electrica_logo` | Emblem lighting | **OPEN QUESTION** — shared or separate op |
| 8 | `colantare_fata` | Vinyl application | dossier op `vinyl_application` |
| 9 | `finisaje` | RAL paint, QC-adjacent | dossier `comp_finisaj_litere` |
| 10 | `sablon_montaj` | Mounting template | parent sablon materials |
| 11 | `asamblare` | Return-face bonding | dossier `return_face_bonding` |
| 12 | `ambalare_livrare_montaj` | Packaging | dossier `packaging_letters` |
| 13 | `structura_suport` | Metal bars (optional) | `TPL-METAL-PREMOUNT-STRUCTURE_v1` |

---

## 7. ProductAggregate model

**Definition:** Read-only merge of parent `product_templates` row, `product_blueprint_dossier`, active `product_template_module_links`, child template rows, and registry references.

**Endpoint (implemented Step 2):**

```
GET /api/v1/product-system/aggregate/{template_code}
```

**Provenance values:** `parent` | `dossier` | `linked_module` | `derived` | `registry` | `missing` | `conflict`

**Conflict/warning codes:**

| Code | Severity | Meaning |
|------|----------|---------|
| `PARENT_COMPONENTS_EMPTY` | warning | Parent `components_json=[]`; use dossier/modules |
| `TRIGGER_FIELD_MISMATCH` | warning | Link trigger ≠ Intake field (e.g. `metal_support_required` vs `mounting_system`) |
| `DOSSIER_MISSING` | warning | No dossier row |

**JSON shape:** See `backend/schemas/product_aggregate.py` — `ProductAggregate` model.

**Rule:** Never emit `comp_auto_1` as aggregate truth.

---

## 8. Form System integration

- Intake V6 steps compose from mini-module registry (Step 5 — not yet implemented).
- Each form field maps to `canonical_key` and `workspace_path`.
- Persisted in `intake_v6_workspaces.payload_json`.
- `quote_input_payload` built by adapter — must be derivable from same keys.
- Commercial inputs (`markup_percent`, `vat_percent`) are quote-layer, not product-layer.

---

## 9. ProductDefinition builder contract

**Input:** workspace payload + ProductAggregate + quote_input  
**Output:** `ProductDefinition` (`backend/data_models/product_contracts.py`)

Must include:

- `product_id` = template_code
- `dimensions`, `quantity`
- `layers[]` with `components`, `processes`, `materials` refs per mini-module
- `validation.missing_fields[]` — explicit, fail-closed

**Today:** Built only at quote `/price` via `ProductSystemService.build_product_definition`.  
**Target (Step 6):** Preview snapshot at draft quote create.

---

## 10. Cost Engine contract

**Input:** ProductDefinition + **aggregate-expanded BOM** (not parent-only) + quote_input + registries  
**Output:** `CostResult` — internal cost only

Rules:

- Same engine for Intake preview (dry_run) and `POST /quotes/{id}/price`
- Formula IDs from template/module rows — e.g. `mounting_template_area`
- Material rates from `inventory_materials` (active, unit_cost > 0)
- Workcenter rates from `workcenter_rates`
- Child modules via `linked_modules` in quote_input
- Dossier `costengine_mapping_json` is **documentation** until Step 7 wires aggregate expansion

**OPEN QUESTION:** Repopulate parent `components_json` vs runtime aggregate expansion only?

---

## 11. Quote/Order snapshot contract

**Quote draft:** `quotes.notes.intake_v6_linkage_v1` with `quote_input_payload`, `workspace_payload_snapshot` — totals zero by policy.

**Quote priced:** `quotes.line_items` wrapper with `product_definition`, `cost_result`, `price` — `grand_total > 0`.

**Order convert:** Requires priced snapshot; writes `orders.snapshot_line_items` frozen JSON.

**Must not:** Convert with plain line_items array (no product_definition).

---

## 12. Task Preview contract

**Target (Step 9):** Tasks derived from priced `ProductDefinition.layers[].processes` mapped via mini-module `task_outputs`.

**Today:**

- Intake task preview: V3 operation catalog (`preview_only`)
- Dossier `task_rules_json`: documentation
- Execution plan: order snapshot processes; fallback `produce_order`

**Canonical task types:** 20-value enum (BLK-08 gate).

**Employee eligibility:** `operational_registry_service.get_eligible_employees_for_operation(operation_key)` — wire in Step 9.

---

## 13. Migration/compatibility strategy

1. **No DB restore** — data consistent; architecture fix only.
2. **No seed_sync_all** until contract approved.
3. ProductSystem UI: show aggregate, deprecate `comp_auto_1` as truth (Step 3).
4. Linkage versioning: **OPEN QUESTION** — bump to `intake_v6_linkage_v2` when ProductDefinition in draft notes.
5. Legacy quotes (quote 4): reprice only after Step 7 — not before.

---

## 14. Acceptance criteria

| Step | Criteria |
|------|----------|
| 1–2 (this build) | Contract doc exists; GET aggregate returns 5 dossier components + 2 modules + warnings |
| 3 | Blueprint Studio shows aggregate, not comp_auto_1 |
| 4 | Mini-module YAML registry for 13 modules |
| 5 | No orphan Intake form fields |
| 6 | Draft quote notes include ProductDefinition preview |
| 7 | gradi-curat `/price` gross > 0; preview matches within tolerance |
| 8 | Order convert succeeds from priced quote |
| 9 | Task preview matches execution structure (dry-run) |
| 10 | Full UI E2E gradi-curat |

---

## 15. Implementation roadmap

| Step | Name | Pricing change? |
|------|------|-----------------|
| 0 | Stabilization + forensic backup | No |
| 1 | This contract document | No |
| 2 | ProductAggregate read service + GET | No |
| 3 | Blueprint Studio aggregate display | No |
| 4 | Mini-module registry | No |
| 5 | Form System modular | No |
| 6 | ProductDefinition builder | No (snapshot only) |
| 7 | Cost Engine aggregate integration | **Yes** |
| 8 | Quote/Order alignment | Yes |
| 9 | Task Preview from PD | No writes |
| 10 | gradi-curat E2E | Validation |

---

## 16. What not to do

- Do not run `seed_sync_all.py` without approval
- Do not restore DB for template "degradation" (not corrupted)
- Do not reprice quote 4 until Step 7 approved
- Do not use parent minimal row as UI truth
- Do not use dossier-only or catalog-only as pricing/task source
- Do not create UI-only forms without backend contract
- Do not hardcode prices in contract doc
- Do not create order/execution_plan during Steps 1–6

---

## OPEN QUESTIONS

1. Separate `electrical_logo` operation vs shared `electrical_letters`?
2. Repopulate parent `components_json` from aggregate vs expand at runtime only?
3. Exact `DEFAULT_PSU_RESERVE_PERCENT` for contract documentation?
4. Field installation task — part of `ambalare_livrare_montaj` or separate module?
5. Linkage version bump timing for `intake_v6_linkage_v2`?
6. Exact machine registry mapping per workcenter for cant/CNC?

---

*Document maintained as architectural source of truth. Implementation code references this contract via `ProductAggregate` schema and `GET /api/v1/product-system/aggregate/{template_code}`.*
