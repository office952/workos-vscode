# AUDIT: Material Planning Hints & Procurement Readiness

## Purpose

Read-only audit and foundation plan for separating **Material Planning**, **Procurement Readiness**, **Inventory**, and **Task Readiness** in WorkOS — aligned with Publimedia operational policy: no strict tracking for cheap consumables; project-critical materials may gate on advance/procurement.

**Build boundary:** audit + plan only. No runtime mutations. No implementation in this pass.

---

## Preflight (2026-06-14)

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD | `32da36b` — `feat(employee): add task readiness dependencies` |
| Working tree | clean |
| Backend auth | Putaru Sandu / `dev-sandu-employee-001` / `employee_mobile` |

---

## Audit finding — what exists today

### ProductSystem (`TPL-VOLUMETRIC-LETTERS`)

| Area | Status | Notes |
|------|--------|-------|
| Template components + `required_materials_json` | **Yes** | `seed_build4_templates._volumetric_letters_components()` — MAT-* with formula quantities (face, profil, spate, LED, etc.) |
| Blueprint dossier material keys | **Yes** | `seed_tpl_volumetric_letters_dossier.py` — structural keys, task rules, no commercial prices |
| `task_templates.material_requirements` | **Partial** | Validated by `ProductSystemLinkageValidator` / M22 tests; lives in DB table, not on execution plan |
| Execution preview API | **Yes** | `ProductSystemExecutionPreviewService.preview_for_execution()` → `generated_task_requirements[].material_requirements` |
| Flow into ExecutionPlan | **No** | `ExecutionPlanService.from_order()` builds tasks from snapshot `cost_result.processes` only — **no material fields copied** |

### Pricing / Material Registry

| Area | Status | Notes |
|------|--------|-------|
| `inventory_materials` registry | **Yes** | `unit_cost`, `stock_current`, `stock_min` — used for **quote costing** and admin |
| M22 `materials` table read service | **Yes** | `MaterialsReadService.material_available()` — exists but **gated** (`registry_materials_live`); not wired to task start |
| Pricing → physical availability | **No link** | Registry explicitly documents: Material Registry unit_cost ≠ commercial markup; ProductSystem gate is informational |

### Inventory

| Area | Status | Notes |
|------|--------|-------|
| Stock fields | **Yes** | `stock_current`, `stock_min`, `stock_max` on `inventory_materials` |
| Stock reservation | **No** | Only comment in `inventory_sheet_format.py` — not implemented for execution |
| Inventory deduction | **Yes (manual)** | `InventoryDeductionService` — deducts from `execution_reality.materials_json` rows with valid `material_id`; **not at task Start** |
| Availability check at production | **No** | No automatic block on stock for employee start |

### ExecutionPlan / Reality (order 1, live API)

| Field | Order 1 runtime |
|-------|-----------------|
| `material_requirements` on plan tasks | **Absent** |
| `material_hints` / `material_planning_items` | **Absent** |
| `procurement_status` / `awaiting_advance` | **Absent** |
| `depends_on_task_ids` | **Present** (post `32da36b` backfill) |
| `execution_reality.materials_json` | **Empty `[]`** |
| Task instructions | **Text only** (procedural, no structured materials) |

Tasks T-002…T-011: plan keys are process metadata + documents/instructions + deps where applied. No material structure.

### Task Readiness (`task_readiness_service.py`)

| Item | Status |
|------|--------|
| `waiting_material` constant + label | **Defined** |
| Used in `evaluate_task_readiness()` | **No** — placeholder only |
| Active logic | Dependencies, manual block, done, assignment |
| Material input needed | `material_planning_items` + per-item `procurement_status` with `readiness_impact` |

---

## Boundary answers (Faza 2)

1. **Material list for TPL-VOLUMETRIC-LETTERS?** Yes — in template components, dossier, CostEngine snapshot at quote time.
2. **Material requirements per process/task?** Yes in ProductSystem `task_templates` + preview; **not on ExecutionPlan tasks**.
3. **Pricing → inventory item map?** Material codes (MAT-*) shared; pricing uses registry `unit_cost`; inventory has `stock_*` on same table — **no execution handoff**.
4. **Stock availability check?** `MaterialsReadService.material_available()` exists; **not used** in execution/readiness.
5. **Material reservation?** **No**.
6. **Inventory deduction?** **Yes**, observational loop from reality JSON — operator-triggered, not automatic at Start.
7. **Procurement / achiziții workflow?** **No** production module; seed notes only (`seed_volumetric_owner_confirmed_prices` procurement record comment).
8. **`waiting_material` status?** Reserved in readiness service; **unused**.
9. **`awaiting_advance`?** **No** runtime concept today.
10. **Safe for material planning?** Quote snapshot material lines + template MAT-* codes + dossier task rules. **Unsafe** as availability: Pricing registry, `stock_current` without policy layer, or geometry re-derivation.

---

## Recommended architecture (foundation model)

### Separation of concerns

```text
Pricing          → standard costs / quote totals (MAT-* unit_cost)
Material Planning → estimated needs + category + policy (no stock truth)
Inventory        → physical stock where tracked (optional per material)
Procurement      → manual/owner status on planning items
Task Readiness   → deps + block + selective material gate
Execution Reality → what happened (tasks, optional materials_json)
```

### Material Planning Item (target shape)

```json
{
  "code": "MAT-LED-MODULE",
  "name": "Module LED",
  "category": "project_critical",
  "quantity_estimate": null,
  "unit": "buc",
  "confidence": "template_hint",
  "source": "template_component",
  "required_for_task_ids": ["T-006"],
  "planning_policy": "buy_after_advance",
  "procurement_policy": "buy_after_advance",
  "readiness_impact": "can_block_if_missing",
  "procurement_status": "not_checked"
}
```

### Categories (owner-aligned)

| Category | Examples | Readiness |
|----------|----------|-----------|
| `project_critical` | Plexi față, Forex spate, profil cant, LED modules, surse | May → `waiting_material` / `awaiting_advance` when operator marks missing |
| `standard_low_cost_stock` | Șuruburi, silicon, cablu uzual, conectori, cleme | `checklist_only` / `suggest_replenishment` — **no auto block** |
| `indirect_consumable` | Lavete, alcool, mănuși | `checklist_only` — no block |
| `internal_semifinished_output` | Față debitată, cant modelat | **`depends_on_task_ids`** — not inventory |

### Procurement status (manual MVP target)

`not_checked` | `available` | `check_required` | `suggest_replenish` | `awaiting_advance` | `to_order` | `ordered` | `received` | `not_required`

### Readiness priority (when implemented)

1. `done` → not startable  
2. `blocked_manual`  
3. `in_progress` (+ dependency warning if early start)  
4. `waiting_predecessor` (deps)  
5. `waiting_material` (only `readiness_impact=can_block_if_missing` + blocking procurement status)  
6. `eligible`  

**Rule:** predecessor readiness wins over material readiness (T-006 stays `waiting_predecessor` while T-005 not done).

---

## Volumetric material planning map (proposed, order 1 tasks)

| Task | Planning hints | Category default | Readiness impact |
|------|----------------|------------------|------------------|
| T-002 Debitare față | MAT-ACP-FATA-LITERE / plexi 3mm | project_critical | can_block_if_missing |
| T-003 Modelare canturi | MAT-PROFIL-LATERAL-LITERE | project_critical | can_block_if_missing |
| T-004 Lipire canturi | adeziv, consumabile asamblare | standard_low_cost / indirect | suggest_replenishment / checklist_only |
| T-005 Debitare spate | MAT-SPATE-PVC-LITERE (Forex 10mm) | project_critical | can_block_if_missing |
| T-006 Montaj LED | MAT-LED-MODULE + fixare | LED critical; fixare low-cost | mixed |
| T-007 Cablare | MAT-LED-PSU-12V + cablu/conectori | surse critical; rest low-cost | mixed |
| T-008 Pregătire montaj | MAT-SABLON-MONTAJ, bare, șuruburi | bare/sablon project; șuruburi checklist | mixed |
| T-009 Asamblare | consumabile montaj | standard_low_cost | checklist_only |
| T-010 QC | checklist electric | indirect | no_task_block |
| T-011 Ambalare | carton/folie | standard_low_cost | suggest_replenishment |

Semifinished outputs (față debitată, cant lipit, etc.) remain **`depends_on_task_ids`** only.

---

## Decision: **Option A — Audit only** (recommended next: **B → C**)

### Why not Option C now

1. **No persistence** for `material_planning_items` or `procurement_status` on plan/reality/order.
2. **No derivation path** from quote snapshot → execution plan tasks (preview exists but is not merged into plan).
3. **No operator API** to set procurement status manually.
4. **`waiting_material` unused** — wiring without storage would be hollow.
5. Quantity estimates need explicit source contract (snapshot material lines vs template hints); auto geometry calc is out of scope.
6. Risk of false precision on consumables if stock checks are wired too early.

### Recommended build sequence

| Phase | Option | Scope |
|-------|--------|-------|
| **Next 1** | **B — Planning hints foundation** | Derive read-only `material_planning_items` on plan generation or derived read model from template + snapshot material lines; categories/policies; **no block**, no stock |
| **Next 2** | **C — Manual procurement status MVP** | Persist `procurement_status` per item (plan JSON or order-scoped store); operator PATCH; readiness `waiting_material` only for `project_critical` + explicit status; employee-safe labels |
| **Deferred** | **D — Automatic stock check** | Only after inventory policy per category is defined and tested |

---

## Employee / Operator boundaries (target)

| Surface | Show | Hide |
|---------|------|------|
| Employee Mobile | `Așteaptă material`, `Verificare material`, blocking task names | cost, price, margin, payroll, supplier, advance amounts |
| Operator Blueprint | Material summary, procurement status, replenish hints | commercial totals |
| Admin / Commercial | Advance gate, buy-after-advance, owner override | — |

---

## What we explicitly do NOT do (owner policy)

- Strict inventory for șuruburi / silicon / cablu mărunt  
- Auto-block tasks for cheap consumables  
- Auto procurement orders  
- Pricing as availability source  
- Full geometry-derived BOM without verified inputs  

---

## Files referenced in audit

| Path | Role |
|------|------|
| `backend/seeds/seed_build4_templates.py` | Volumetric MAT-* + operations |
| `backend/seeds/seed_tpl_volumetric_letters_dossier.py` | Task rules + material keys |
| `backend/services/execution_plan_service.py` | Plan generation (no materials) |
| `backend/services/product_system_execution_output_service.py` | Preview with material_requirements |
| `backend/services/task_readiness_service.py` | `waiting_material` placeholder |
| `backend/services/inventory_deduction_service.py` | Post-reality deduction only |
| `backend/services/materials_read_service.py` | M22 availability read (unused in execution) |
| `backend/models/execution_reality.py` | Observational `materials_json` |
| `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` | Stoc ≠ preț quote |

---

## Tests / smoke (this pass)

- No new tests (audit only).
- Runtime confirmed: task dependency readiness on order 1 unchanged and working (`32da36b`).

---

## Deferred

- Stock reservation  
- Inventory deduction at Start  
- Procurement orders / supplier workflow  
- Automatic quantity from geometry  
- Low-level consumable tracking  
- Operator force-start with audit (material override)  
- Dependency editor UI  

---

## Proposed commit message (audit doc only — await owner)

`docs(employee): audit material planning readiness`
