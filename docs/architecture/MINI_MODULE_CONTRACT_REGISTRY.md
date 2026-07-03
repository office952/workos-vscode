# Mini-module Contract Registry

**Version:** 1.0.0  
**Status:** Step 4 — read-only operational contract  
**Pilot product:** `TPL-VOLUMETRIC-LETTERS_v2`  
**Companion:** [MODULAR_PRODUCT_FLOW_CONTRACT.md](./MODULAR_PRODUCT_FLOW_CONTRACT.md)

---

## 1. What is a mini-module?

A **mini-module** is an **operational contract unit**, not a decorative UI block or empty template row.

Each mini-module declares:

| Question | Must answer |
|----------|-------------|
| What Intake/Form fields does it consume? | `consumed_form_fields` + `operational_destination.intake_source` |
| What ProductDefinition keys does it produce? | `product_definition_outputs` |
| What component roles does it produce? | `produced_component_roles` |
| What materials does it require? | `required_material_roles` |
| What operations does it require? | `required_operation_roles` |
| What appears in ProductAggregate? | `aggregate_outputs` |
| What will Cost Engine consume? | `cost_engine_inputs` |
| What enters Quote/Order snapshot? | `quote_snapshot_outputs`, `order_snapshot_outputs` |
| What can generate Task Preview? | `task_preview_outputs` |

**Rule:** If a field, component, material, operation, or module cannot declare an operational destination, it is **not active**. Mark it `FUTURE_RESERVED_STEP_X` or `DEAD_PIECE_REMOVE_OR_APPROVE`.

---

## 2. Why this is not a decorative template

Decorative templates:

- Have pretty names but no path to Cost Engine
- Appear in UI but never reach Quote snapshot
- Hold materials that `/price` never reads

Operational mini-modules:

- Map to **dossier components**, **linked child templates**, or **parent gate operations**
- Have explicit activation rules (required, optional, gated)
- Feed ProductDefinition → Cost Engine → Quote → Order → Task Preview in roadmap Steps 5–9

Step 4 registry is **read-only in code** — no DB writes, no seed, no migration.

---

## 3. Flow placement

```
Intake V6 Form (Step 5)
    ↓ consumed_form_fields
ProductDefinition builder (Step 6)
    ↓ product_definition_outputs
ProductAggregate (Step 2–3, enriched Step 4)
    ↓ aggregate_outputs + mini_module_registry refs
Cost Engine (Step 7)
    ↓ cost_engine_inputs
Quote / Offer snapshot (Step 8)
    ↓ quote_snapshot_outputs
Order frozen snapshot (Step 8)
    ↓ order_snapshot_outputs
Task Preview / Execution (Step 9)
    ↓ task_preview_outputs
```

---

## 4. Operational status taxonomy

| Status | Meaning |
|--------|---------|
| `ACTIVE_OPERATIONAL` | Has clear destination; used or wired in current pilot |
| `READONLY_EXPLANATORY` | Documentation-only until downstream step |
| `FUTURE_RESERVED_STEP_5` … `STEP_9` | Planned; not active until named step |
| `DEAD_PIECE_REMOVE_OR_APPROVE` | No destination; requires explicit approval to keep |

---

## 5. Implementation (Step 4)

| Artifact | Location |
|----------|----------|
| Schema | `backend/schemas/mini_module_registry.py` |
| Registry data | `backend/data/mini_module_registry_volumetric_v2.py` |
| Service | `backend/services/mini_module_registry_service.py` |
| Endpoints | `backend/routers/product_system_mini_modules.py` |

### Endpoints (GET-only)

```
GET /api/v1/product-system/mini-modules
GET /api/v1/product-system/mini-modules/{module_code}
GET /api/v1/product-system/mini-modules/by-template/{template_code}
```

### ProductAggregate integration

`ProductAggregate.mini_module_registry` carries lightweight refs (`module_code`, `operational_status`, template/component links). Full contracts via mini-modules endpoints.

---

## 6. Volumetric letters v2 — module inventory

### 6.1 Linked child templates (ProductSystem module links)

| module_code | child_template_code | relation | Status |
|-------------|---------------------|----------|--------|
| `modelare_cant` | `TPL-VOLUM-ALUMINIU_v1` | required_module | ACTIVE_OPERATIONAL |
| `structura_suport` | `TPL-METAL-PREMOUNT-STRUCTURE_v1` | optional_addon | ACTIVE_OPERATIONAL |

**Evidence (DB read-only audit):**

- Link id 2: required aluminiu, trigger `volum_aluminum_module_template_code`
- Link id 1: optional premount, trigger `metal_support_required` (Intake may use `mounting_system` — warning)

### 6.2 Dossier-backed components

| module_code | dossier component | dossier role | Status |
|-------------|-------------------|--------------|--------|
| `debitare_fata` | `comp_face_litere` | față plexi/acrilic | ACTIVE_OPERATIONAL |
| `debitare_spate` | `comp_spate_litere` | capac spate Forex | ACTIVE_OPERATIONAL |
| `sistem_led` | `comp_led_litere` | LED + PSU | ACTIVE_OPERATIONAL |
| `finisaje` | `comp_finisaj_litere` | finisaj, sablon, ambalare | ACTIVE_OPERATIONAL |

Note: `comp_lateral_litere` maps to `modelare_cant` (same module as linked child template).

### 6.3 Parent template gate

| module_code | source | Status |
|-------------|--------|--------|
| `geometry_svg` | parent `svg_geometry_analysis` op | ACTIVE_OPERATIONAL |

### 6.4 Future / open questions

| module_code | Reason | Status |
|-------------|--------|--------|
| `electrica_logo` | OPEN QUESTION — separate op vs `electrical_letters` | FUTURE_RESERVED_STEP_6 |

Modules **not included** as active (no clear isolated contract yet):

- `colantare_fata`, `asamblare`, `ambalare_livrare_montaj`, `electrica_litere` as standalone registry entries — covered inside dossier ops / child template ops until Step 6 ProductDefinition builder splits them explicitly.

---

## 7. Module operational sheets (summary)

### A. `modelare_cant` — TPL-VOLUM-ALUMINIU_v1

| Destination | Content |
|-------------|---------|
| Intake | `return_depth_mm`, `return_finish_type`, `letter_perimeter_m` |
| ProductDefinition | `comp_lateral_litere`, forming/bonding/paint processes |
| ProductAggregate | required module + lateral component + linked BOM |
| Cost Engine (Step 7) | `return_profile_linear_meter`, `return_profile_machine_forming`, gates by depth/finish |
| Quote snapshot | linked_modules line, side_forming cost |
| Order snapshot | frozen return processes/materials |
| Task Preview (Step 9) | `side_forming`, `return_face_bonding`, `return_painting` |

### B. `structura_suport` — TPL-METAL-PREMOUNT-STRUCTURE_v1

| Destination | Content |
|-------------|---------|
| Intake | `metal_support_required`, `premount_bar_length_ml`, `bar_material` |
| ProductDefinition | `comp_premount_bars` when activated |
| ProductAggregate | optional module + premount BOM |
| Cost Engine (Step 7) | `premount_bar_linear_meter` |
| Quote snapshot | optional line when trigger true |
| Order snapshot | frozen premount when accepted |
| Task Preview (Step 9) | `premount_bar_preparation` |

**Activation:** optional — only when metal support requested.

### C. Dossier modules (`debitare_fata`, `debitare_spate`, `sistem_led`, `finisaje`)

Each maps 1:1 to dossier `sections_json.components[]` and `costengine_mapping_json` operation/material keys. Parent BOM is minimal; dossier is audit authority until Step 7 aggregate expansion.

---

## 8. Mapping to ProductAggregate service

Existing maps in `product_aggregate_service.py` align with registry:

```python
DOSSIER_COMPONENT_MINI_MODULE = {
    "comp_face_litere": "debitare_fata",
    "comp_lateral_litere": "modelare_cant",
    "comp_spate_litere": "debitare_spate",
    "comp_led_litere": "sistem_led",
    "comp_finisaj_litere": "finisaje",
}
CHILD_TEMPLATE_MINI_MODULE = {
    "TPL-VOLUM-ALUMINIU_v1": "modelare_cant",
    "TPL-METAL-PREMOUNT-STRUCTURE_v1": "structura_suport",
}
```

Registry is the **documented source of truth** for operational destinations; aggregate maps remain runtime join keys.

---

## 9. Cost Engine (Step 7 — not Step 4)

Registry `cost_engine_inputs` declare **future/current formula and quote_input keys**. Cost Engine is **not modified** in Step 4.

Today:

- Parent BOM pricing only (sablon materials + SVG gate)
- Dossier mapping is audit-only
- Child modules expand via `linked_modules` in quote_input (partial)

Step 7 will consume registry + ProductDefinition expanded BOM.

---

## 10. Quote / Order snapshot (Step 8)

Registry `quote_snapshot_outputs` / `order_snapshot_outputs` describe frozen structures in:

- `quotes.line_items` wrapper (priced)
- `orders.snapshot_line_items` (frozen)

Not modified in Step 4.

---

## 11. Task Preview (Step 9)

Registry `task_preview_outputs` map to dossier `task_rules_json` and child template operations.

Today: Intake task preview uses V3 catalog — **not** this registry.

Step 9: derive tasks from priced ProductDefinition processes via registry mapping.

---

## 12. Unused / future modules

Mark with:

```yaml
operational_status: FUTURE_RESERVED_STEP_X
roadmap_owner_step: X
warnings:
  - "Concrete reason why not active"
```

Example: `electrica_logo` — OPEN QUESTION in main contract §16.

---

## 13. Acceptance criteria (Step 4)

- [x] This document exists and is implementable
- [x] Backend schema + read-only service + GET endpoints
- [x] `TPL-VOLUM-ALUMINIU_v1` as ACTIVE operational module
- [x] `TPL-METAL-PREMOUNT-STRUCTURE_v1` with optional activation rules
- [x] Every ACTIVE module declares operational destination
- [x] No decorative modules without destination
- [x] No DB writes / seeds / migrations
- [x] ProductAggregate optional metadata refs
- [x] Tests pass

---

## 14. Next step

**Step 5 — Form System modular:** wire Intake V6 steps from `consumed_form_fields` per ACTIVE module; no orphan form fields.

---

*Registry version `1.0.0` — maintained alongside `GET /api/v1/product-system/mini-modules`.*
