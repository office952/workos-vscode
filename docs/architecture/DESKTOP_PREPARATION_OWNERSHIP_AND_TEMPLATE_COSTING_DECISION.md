# Desktop Preparation Ownership and Template Costing — Decision

## Context

WorkOS desktop/admin must separate operational preparation between CNC routing and order instrumentation (documents, workshop info, print templates). A read-only audit confirmed gaps in intake creator propagation and existing template pricing for volumetric letters.

This build is **desktop/admin only**. Employee Mobile v1/v2, PWA, and CostEngine refactor are out of scope.

## Audit summary

| Finding | Status |
|---------|--------|
| Intake has no `created_by_user_id` | Confirmed — not invented in this build |
| Creator does not propagate end-to-end | Confirmed |
| `execution_plan.prepared_by_user_id` exists | Set on `POST /execution/plan/from-order/{id}` |
| CNC tasks exist via `process_id` / `machine_type` | e.g. `face_cnc_cut`, `mounting_template_cnc_cut` |
| No `preparation_domain` before this build | Added as derived DTO field (no migration) |
| `MAT-SABLON-MONTAJ` at 6 EUR/mp (Forex/PVC 3 mm) | Reused — no duplicate Forex material |
| Paper template 5 EUR/mp | Added as `MAT-SABLON-HARTIE` in registry/seeds |

## MVP decision: instrumentation owner

**Source of truth:** `execution_plan.prepared_by_user_id`

- This is the user who generated the execution plan, not an invented intake creator.
- Blueprint and clarification routing already use this field.
- If intake creator is added in a future build, it may complement — not replace — this MVP contract without breaking existing plans.

## CNC vs instrumentation preparation

| Domain | Meaning | Examples |
|--------|---------|----------|
| `cnc` | CNC router tasks | `face_cnc_cut`, `back_cut`, `mounting_template_cnc_cut`, `CNC_ROUTER` |
| `instrumentation` | Vector/file prep, documents, handoff, sketches | `document_handoff`, tasks with attached documents |
| `print` | Print / vinyl / laminating | `print`, `PRINTER`, vinyl process ids |
| `workshop_info` | Workshop-specific info tasks | `workshop_info` markers |
| `other` | Remaining plan tasks | Assembly, QC, etc. |

CNC responsibility is **not** auto-assigned. Blueprint exposes CNC task grouping and operational registry hint (`cnc_cutting`) only.

## Template material rules

### Paper — `MAT-SABLON-HARTIE`

- Unit: `mp`
- Owner-confirmed cost: **5 EUR/mp** (excluding TVA)
- Gated by `mounting_template_material_type = paper`
- Price lives in inventory / owner-confirmed seeds — **not** hardcoded in CostEngine formulas

### Forex — `MAT-SABLON-MONTAJ`

- Existing material — **6 EUR/mp**
- Gated by `mounting_template_material_type = forex`
- CNC service `mounting_template_cnc_cut` applies only for **forex** templates

### Template type semantic

`mounting_template_material_type`:

| Value | Material | CNC template cut |
|-------|----------|------------------|
| `none` | none | skipped |
| `paper` | `MAT-SABLON-HARTIE` | skipped |
| `forex` | `MAT-SABLON-MONTAJ` | included when area/perimeter inputs present |

**Backward compatibility:** legacy quotes with `mounting_template_enabled = true` and no material type resolve to **`forex`**.

## Included in this build

- `preparation_domain` derivation on blueprint tasks
- Blueprint payload: `prepared_by_*`, `preparation_ownership`, `preparation_groups`, mounting template summary
- `MAT-SABLON-HARTIE` registry + template line + owner-confirmed seed
- `mounting_template_material_type` quote_input gate (no DB migration)
- Desktop UI: `OperatorProductionBlueprintPanel`, minimal `ExecutionDetail` prepared-by hint
- Targeted pytest coverage

## Deferred

- Intake `created_by_user_id` migration
- `orders.instrumentation_owner_user_id`
- Forced CNC auto-assignment
- Employee Mobile changes
- CostEngine refactor
- Full ExecutionDetail redesign
- Multi-person confirmations / ExecutionTaskIssue / Notification Center

## PASS / FAIL

**PASS** when:

- Employee Mobile untouched
- CostEngine logic unchanged (only template gates / seeds)
- `prepared_by_user_id` used for instrumentation MVP
- CNC and instrumentation visibly separated in blueprint
- `MAT-SABLON-HARTIE` at 5 EUR/mp in registry
- Forex uses existing `MAT-SABLON-MONTAJ` without duplicate
- Legacy `mounting_template_enabled` remains compatible
- Targeted tests green

**FAIL** if any boundary above is violated.
