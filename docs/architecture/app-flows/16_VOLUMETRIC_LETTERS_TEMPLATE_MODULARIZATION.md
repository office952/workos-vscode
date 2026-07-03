# 16 — Volumetric Letters Template Modularization

**Version:** 1.0.0  
**Date:** 2026-06-30  
**Template:** `TPL-VOLUMETRIC-LETTERS_v2`  
**Fixture:** order `88002`, snapshot `QSN2-2026-0003`, plan `id=2`

---

## 1. Purpose

Document how the **volumetric letters** pilot template is composed today: modules, dossier, task_rules, parent vs linked-module operations, Form System mapping, and execution output — including **canonical vs alias** rules (DEC-003/004).

---

## 2. Current template identity

| Item | Value | Evidence |
| ---- | ----- | -------- |
| Template code | `TPL-VOLUMETRIC-LETTERS_v2` | registry `PILOT_TEMPLATE`, intake binding |
| Product family | Litere volumetrice | `volumetricIntakeRoute.ts`, intake product family |
| Dossier | `product_blueprint_dossier` row | `task_rules_json`, sections |
| Linked child templates | `TPL-VOLUM-ALUMINIU_v1`, `TPL-METAL-PREMOUNT-STRUCTURE_v1` | module links + aggregate provenance |
| Commercial rules | `commercial_rules_volumetric_v2` | CPP service |
| Internal rules | `internal_cost_rules_volumetric_v2` | EIC service |
| Execution output | 12 planned tasks / 17 ops | order 88002 worklogs |
| Known order | `88002`, `quote_snapshot_v2_id=3` | Step 8/9 QA |

---

## 3. Current modules (mini-module registry)

| Module | Source | Purpose | Active? | Form System? | ProductDefinition? | Aggregate? | ExecutionPlan? | Risk |
| ------ | ------ | ------- | ------- | ------------ | ------------------ | ---------- | -------------- | ---- |
| geometry_svg | registry | SVG gate, base geometry | Yes | Yes (bindings) | Yes | ops: svg_geometry_analysis | Orphan op (DEC-001) | Readiness vs op |
| debitare_fata | registry | Face CNC, front | Yes | Yes | Yes | parent comp_face | tasks: cnc_face_cut | WC null |
| debitare_spate | registry | Back cut | Yes | Partial | Yes | comp_spate | cnc_back_cut | WC null |
| modelare_cant | registry + **linked** TPL-VOLUM-ALUMINIU | Return/lateral | Yes | Yes | Yes | **duplicate ops** | return_profile_forming | **DEC-003** |
| structura_suport | registry + premount link | Bars/premount | Conditional | Partial | Conditional | premount op orphan | DEC-002 | BOM vs task |
| sistem_led | registry | LED modules | Conditional | Yes | Conditional | comp_led | led_installation | WC null |
| finisaje | registry | Paint/finish | Conditional | Yes | Conditional | parent painting | painting task | **DEC-004** |
| electrica_logo | registry | Electrical | Future/partial | Partial | Partial | electrical op | electrical_wiring | WC null |

**Registry modules (8):** confirmed in `mini_module_registry_volumetric_v2.py`.

**Dossier task_rules mini-map (aggregate service):** also maps `colantare_fata`, `sablon_montaj`, `ambalare_livrare_montaj`, `asamblare` — from dossier rules, not all separate registry entries.

---

## 4. Parent operations vs module operations

| Semantic step | Parent `priced_operation` (canonical) | Module operation (alias) | Planned task uses | Materialize risk |
| ------------- | ------------------------------------- | ------------------------ | ----------------- | ---------------- |
| Return forming | `side_forming` | `RETURN_PROFILE_MACHINE_FORMING` | parent (`return_profile_forming`) | Double if both — **DEC-003** |
| Face bonding | `return_face_bonding` | `RETURN_PROFILE_FACE_BONDING` | parent | **DEC-003** |
| Painting | `painting` (lowercase) | `PAINTING` (module) | parent | **DEC-004** |
| Face CNC | `face_cnc_cut` / vector ops | — | cnc_face_cut, vector_prep | WC null |
| Vinyl | `vinyl_application` | — | vinyl_application | Linear dep risk DEC-007 |

**Rule (recommended, pending owner):** parent task_rules + parent priced_operation = **execution canonical**; module rows = **aggregate/BOM/cost alias only**.

---

## 5. Task rules and execution plan output

**Summary (order 88002):** 12 `planned_tasks[]`, 17 `planned_operations[]`, 0 `operational_tasks[]`, all `workcenter` null, all `estimated_minutes` null.

| task_key (representative) | task_rule source | Planned? | WC | Minutes | Dependencies | Materializable? | Gap |
| ------------------------- | ---------------- | -------- | -- | ------- | ------------ | --------------- | --- |
| vector_prep | dossier task_rules | Yes | null | null | linear chain | Blocked quality | DEC-005, DEC-007 |
| cnc_face_cut | debitare_fata | Yes | null | null | after vector_prep | Audit OK, WC missing | DEC-005 |
| cnc_back_cut | debitare_spate | Yes | null | null | linear | same | DEC-005 |
| return_profile_forming | side_forming | Yes | null | null | linear | duplicate risk if module added | DEC-003 |
| return_face_bonding | return_face_bonding | Yes | null | null | linear | DEC-003 | |
| painting | painting | Yes | null | null | linear | DEC-004 | |
| vinyl_application | colantare / vinyl | Yes | null | null | after painting (wrong for vinyl-only?) | DEC-007 | |
| led_installation | sistem_led | Yes | null | null | linear | | DEC-005 |
| electrical_wiring | electrica | Yes | null | null | linear | | DEC-005 |
| mounting_template | sablon_montaj | Yes | null | null | chained late (should parallel?) | DEC-007 | |
| qc_internal_check | dossier | Yes | null | null | linear | | DEC-005 |
| packaging | ambalare | Yes | null | null | linear | | DEC-005 |

**Orphan operations (no task_rule):** `svg_geometry_analysis`, `premount_bar_preparation`, module `RETURN_PROFILE_*`, module `PAINTING` — see DEC-001/002/003/004.

---

## 6. Form System modules for volumetric letters

| Form module | Key fields | Activates PS module | ProductDefinition | Aggregate | Execution |
| ----------- | ---------- | ------------------- | ----------------- | --------- | --------- |
| geometry_svg | SVG, letter_count, areas | geometry_svg | geometry gates | svg op | vector_prep |
| face_front | face_finish_type | debitare_fata | face layers | comp_face | CNC face |
| side_return | return_depth_mm, return finish | modelare_cant | lateral | comp_lateral + **linked module** | forming/bonding |
| back_support | backing_mode | debitare_spate, structura_suport | back/support | comp_spate, premount | back cut / premount |
| lighting_led | illuminated, PSU, modules | sistem_led | LED | comp_led | led + electrical |
| mounting | mounting_system, template | structura_suport, sablon | mounting | template op | mounting_template task |
| finish | RAL, vinyl, paint flags | finisaje, colantare | finish processes | paint/vinyl ops | painting, vinyl |
| readiness | confirmations | dossier gates | validation | readiness | READINESS_GATE excluded |

---

## 7. Dossier responsibilities

**Belongs in dossier:** task_rules, operation templates, costengine_mapping (audit), sections, readiness gates, owner-decision placeholders.

**Does not belong in dossier:** live workspace values; commercial client totals; employee assignments; session minutes.

**task_rules:** single source for ExecutionPlan task list (via frozen aggregate snapshot).

**Warnings/owner_decisions:** partial readiness at freeze — carried in Quote Snapshot V2.

---

## 8. Pricing / internal cost links

| Module | CPP contribution | EIC contribution | Must NOT |
| ------ | ---------------- | ---------------- | -------- |
| geometry_svg | letter_count, areas, perimeter | geometry readiness | hourly client rate |
| debitare_fata/spate | ml/mp/buc rules | material + op internal | WC as commercial |
| modelare_cant | ml return rules | internal lateral cost | duplicate commercial line for alias op |
| sistem_led | module/set rules | LED BOM + internal | minute × rate client |
| finisaje | m²/min job paint | paint consumables | module PAINTING duplicate price |
| structura_suport | conditional commercial | premount internal | auto task without DEC-002 |

---

## 9. Execution readiness links

| Module | Becomes task candidate? | BOM/cost only? | Needs WC? | Needs skills (later)? |
| ------ | ----------------------- | -------------- | --------- | --------------------- |
| geometry_svg | via vector_prep (not svg_geometry_analysis op) | svg op analytics | PREPRESS? DEC-001 | Prepress |
| debitare_* | Yes | — | WC_CNC (DEC-005) | CNC operator |
| modelare_cant | Yes (parent only) | module ops alias | WC_FORMING | Forming |
| sistem_led / electrica | Yes | — | WC_ELECTRICAL | Electrical |
| finisaje / colantare | Yes | — | WC_PAINT | Paint/finish |
| structura_suport | DEC-002 | premount often BOM | WC metal fab | Fab |
| readiness | READINESS_GATE excluded | — | — | — |

---

## 10. Gaps and decisions

| Gap/Decision | Description | Blocks | Owner |
| ------------ | ----------- | ------ | ----- |
| DEC-003 | RETURN parent vs module canonical | Materialize | PENDING_OWNER |
| DEC-004 | painting vs PAINTING | Materialize | PENDING_OWNER |
| DEC-005 | workcenter on parent ops | Scheduling | PENDING_OWNER |
| DEC-006 | planning minutes source | Capacity | PENDING_OWNER |
| DEC-007 | DAG vs linear chain | Realistic schedule | PENDING_OWNER |
| DEC-009 | POST materialize | operational_tasks | PENDING_OWNER (blocked) |

---

## 11. Modularization recommendation (docs only)

1. **Parent template** owns canonical `task_rules` + parent `priced_operation` codes.
2. **Linked modules** (`TPL-VOLUM-ALUMINIU`, premount) supply BOM/materials/**alias ops only** — exclude from materialization when parent task exists.
3. **Form modules** map 1:N to mini-module registry — no duplicate forms per product.
4. **ProductDefinition** activates modules from workspace + registry rules.
5. **ProductAggregate** expands graph; marks provenance `parent` vs `linked_module`.
6. **Quote/Order Snapshot V2** freezes aggregate + task_contract.
7. **ExecutionPlan V2** reads frozen `task_rules` only; enrich WC/minutes upstream (Faza 2) before materialize GO.

---

## 12. Next safe step

**Owner decisions DEC-003 / DEC-004 / DEC-005 first** — then dossier/registry alignment doc + Faza 2 scoping (no implementation without GO).
