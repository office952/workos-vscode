# Shared CNC Operation Model & Cutting Service Template

## 1. Why CNC must not be hardcoded in product forms

WorkOS ProductSystem templates (`TPL-VOLUMETRIC-LETTERS`, future lightboxes, CNC-only services) share the same physical CNC router constraints (depth per pass, bevel passes, perimeter basis) but differ in **what geometry is available** and **whether material is internal or client-supplied**.

Hardcoding CNC formulas inside a single product intake form causes:

- duplicated pass rules across templates;
- material rows mistaken for operation/labor cost;
- inability to offer standalone CNC cutting without volumetric letter logic;
- drift between Intake V4 preview and CostEngine template seeds.

**Direction:** encode CNC as a **reusable operation model** consumed by templates; templates emit geometry + material choices; the shared module produces **operation preview rows**.

## 2. Product template vs reusable module vs service template

| Layer | Role | Example |
|-------|------|---------|
| **Product template** | Full manufactured product with materials, finishes, LED, assembly | `TPL-VOLUMETRIC-LETTERS` |
| **Reusable technology module** | Shared rules for CNC cutting/bevel, pass counts, basis keys | `shared_cnc_operation_model` |
| **Service template** | Operator orders a process, not a finished sign product | `TPL-CNC-CUTTING-SERVICE` (foundation) |

## 3. Shared CNC model (`CNC_OPERATION_MODEL`)

Implementation: `backend/services/shared_cnc_operation_model.py`

### Semantic entities

- **`CncOperationRule`** — static rule + **`CncProductionResourceBinding`** (machine, workstation, skill, catalog keys).
- **`CncOperationPreviewRow`** — runtime preview row with quantity, passes, operation_equivalent_quantity, pricing_status, and production bindings.

### Production resource fields (not an isolated calculator)

Each row can carry bindings aligned to existing registries:

| Field | Example (face cut) | Source in repo |
|-------|----------------------|----------------|
| `required_machine_key` | `MCH-CNC-4020` | `seed_operational_workforce_registry` |
| `machine_type` | `cnc_router` | machine registry / tpl hints |
| `workstation_key` | `cnc_router` | `tpl_volumetric_operation_keys_service.station_hint` |
| `workcenter_code` | `WC_CNC_ROUTING` | operational registry |
| `required_skill_key` | `cnc_operator` | tpl `role_hint`, frontend routing |
| `registry_skill_code` | `SK_CNC_OPERATOR` | operational workforce seed |
| `operation_catalog_key` | `face_and_backing_cnc_cut` | V3 operation catalog |
| `dossier_operation_key` | `face_cnc_cut` | CostEngine priced_operation |
| `production_task_type` | `cnc_routing` | tpl `future_execution_task_type` |
| `tpl_operation_key` | `cnc_face_cutting` | tpl dry-run key |

When catalog/dossier split is not yet defined (e.g. separate face bevel row), `resource_mapping_status = pending_mapping` with explicit `mapping_gaps` — **no invented keys**.

Bridge helper: `cnc_preview_row_to_task_candidate_hints()` maps rows to task dry-run vocabulary without writing tasks.

### Basis types

- `path_perimeter` — CNC debit on contour (ml)
- `path_length`, `area`, `piece_count`, `machine_time` — reserved for service template expansion

### Pricing

- Rows reference `pricing_rate_key` = `workcenter_rates:CNC_ROUTER:per_linear_meter` (documented contract).
- **This build does not mutate Pricing Registry or CostEngine.**
- Default `pricing_status = missing_rate`, `estimated_cost = null` until a dedicated operation-pricing build wires read-only registry lookup.

## 4. How `TPL-VOLUMETRIC-LETTERS` consumes the module

The volumetric letters template **does not** embed CNC pass math in Intake V4 finish forms.

It provides:

- `face_cutting_perimeter_ml` / `cnc_cutting_perimeter_ml` from quote geometry;
- backing layer confirmation (`backing` role in `layer_role_setup`);
- optional `back_bevel_enabled` on quote geometry / pricing input.

The shared module emits `required_cnc_operations` preview rows:

| operation_key | When |
|---------------|------|
| `cnc_face_cutting_plexiglas_3mm` | Always (when perimeter known) |
| `cnc_face_bevel_plexiglas_3mm` | Always mandatory for volumetric face |
| `cnc_backing_cutting_forex_10mm` | Backing layer confirmed |
| `cnc_backing_bevel_forex_10mm` | Backing + back bevel enabled |

**CostEngine template** (`seed_build4_templates.py`) still uses `perimeter_pass_linear_meter` on `face_cnc_cut` / `back_cut` — unchanged in this foundation build. Intake V4 **material breakdown** now adds separate `operation_rows` for operator clarity.

## 5. Classic lightboxes / casete luminoase

`TPL-ACM-CASSETTED-PANEL` / lightbox seeds use CNC on ACM, diffuser plexi, routing — same **workcenter** (`CNC_ROUTER`) and `perimeter_pass_linear_meter` formula family.

Future consumption:

- lightbox face/back panels → `build_cutting_service_cnc_operation_rows` or template-specific rule set;
- no letter/cant/LED logic in CNC service template.

## 6. `TPL-CNC-CUTTING-SERVICE` (foundation contract)

**Not fully onboarded in this build** — contract defined in `build_cutting_service_cnc_operation_rows()`.

### Inputs (minimum)

1. File type + CNC file prep flag  
2. `material_source`: `internal_stock` | `client_supplied`  
3. Material family + thickness  
4. Operations: cutting, bevel, engraving, pocket, drilling  
5. Geometry: perimeter, piece count, passes override  
6. Cost: material rows only if internal stock; always operation rows

### Outputs

- Material rows + nesting only for internal stock  
- CNC operation rows always when cutting enabled  
- Warnings for client material (no stock consumption, quality disclaimer)

## 7. Internal material vs client material

| | Internal (`internal_stock`) | Client (`client_supplied`) |
|---|---------------------------|---------------------------|
| Material breakdown rows | Yes (plexi, forex, nesting) | No material cost rows |
| Stock consumption | Quote estimate only (existing policy) | **Never** |
| CNC operation rows | Yes | Yes (labor/setup preview) |
| Warnings | Standard missing-rate | + client material liability warnings |

## 8. Owner rules — Plexiglas 3 mm, Forex 10 mm, bevel, passes

### Face letters (Plexiglas 3 mm)

- Material: **Plexiglas 3 mm** (material row — separate from CNC ops).
- **Debitare CNC față** = 1 pass × face CNC perimeter.
- **Șanfren CNC față** = mandatory, 1 pass × same perimeter.
- PBL example: perimeter CNC față **13.62 ml** → two operation rows at 13.62 ml each (not one bundled 2-pass row in UI).

### Backing (Forex 10 mm)

- Modes: `none` | `forex_10_no_bevel` | `forex_10_with_bevel`.
- **Debitare CNC spate**: `passes = 5`, `owner_pass_override = true` (owner decision — not strict `ceil(10/3.5)=3`).
- Operation equivalent: `perimeter_ml × 5` (e.g. 13.62 → **68.10 ml-pass**).
- **Șanfren spate**: 1 pass × backing perimeter, only if bevel mode selected.

### Depth per pass reference

- `depth_per_pass_mm = 3.5` documented on Forex cutting row; owner override on pass count takes precedence for 10 mm Forex.

## 9. Future operation pricing / rates

Existing sources (read-only, not modified here):

- `Workcenter_rates` / `seed_volumetric_workcenter_rates` — `CNC_ROUTER` `rate_per_linear_meter` (tests use 1.5 EUR/ml/pass).
- CostEngine: `perimeter_pass_linear_meter` × workcenter rate in `build_execution_layers_from_components`.
- `intake_v4_cnc_router_pass_policy_service` — legacy preview helper (still uses ceil-based Forex passes for CostEngine alignment).

Next build: wire `shared_cnc_operation_model` to read workcenter rates without inventing defaults in production paths.

## 10. LED shared rules (documented — not implemented here)

| Product class | LED basis |
|---------------|-----------|
| Volumetric letters | Exterior letter perimeter / pitch (e.g. PBL 11.63 m → 47 modules) |
| Emblem / casetă / area-lit surface | Outbox bounding area × **60 modules/m²**, `ceil(area_m2 × 60)` |

Do **not** hardcode 60 modules/m² in `TPL-VOLUMETRIC-LETTERS` — future `shared_led_module_density_rules` module.

## 11. Boundaries

This foundation does **not**:

- create quotes, orders, ExecutionPlan, ExecutionTask, `tasks_json`;
- consume inventory / stock;
- change Pricing Registry or global CostEngine;
- send quotes to clients;
- activate `TPL-CNC-CUTTING-SERVICE` in operator UI.

## 13. Production integration flow (target architecture)

```text
Product template / Service template
  → requests CNC operations (geometry + material choices)
  → shared_cnc_operation_model normalizes operation rows
  → rows carry machine / workstation / skill / catalog bindings
  → pricing rates attach later (workcenter_rates:CNC_ROUTER — separate build)
  → production preview reads same catalog keys (V3 operation catalog today)
  → task generator dry-run maps dossier/catalog keys → task candidates
  → after Order binding: ExecutionTask assigned via operational registry
     (employee skills + allowed machines/workcenters)
```

### 13.1 How `TPL-VOLUMETRIC-LETTERS` requests CNC

Geometry + layer roles → `build_volumetric_letters_cnc_operation_rows()` → `operation_rows` on material breakdown.

Parallel paths today (not yet unified):

- **Material breakdown CNC rows** — granular cut/bevel rows with production bindings.
- **Production task preview** — V3 catalog seed `face_and_backing_cnc_cut` (bundled face+back).
- **Task dry-run** — `cnc_face_cutting` / `cnc_backing_cutting` candidates via `MATERIAL_JOB_TO_OPERATION`.

Next build: feed dry-run from shared CNC rows via `cnc_preview_row_to_task_candidate_hints()`.

### 13.2 How `TPL-CNC-CUTTING-SERVICE` will request CNC

`build_cutting_service_cnc_operation_rows()` with `CUTTING_SERVICE_CNC_BINDING` (`pending_mapping` until template onboarded).

### 13.3 Production preview

`intake_v4_production_preview_service` → V3 `build_task_seed_candidates()` → catalog items with `required_station`, `required_skill`, `source=operation_catalog`.

CNC catalog entry `face_and_backing_cnc_cut`: station `cnc_router`, skill `cnc_router_operation` (catalog namespace — differs from tpl `cnc_operator`).

### 13.4 Task generator dry-run

`intake_v4_task_generation_dry_run_service` uses `station_hint` / `role_hint` from tpl registry and maps catalog codes to dossier keys (`face_and_backing_cnc_cut` → `face_cnc_cut`).

Face/back bevel rows: **no dry-run task** today (`provisional_reason` in tpl spec).

### 13.5 Machine / station / employee assignment (after Order)

`operational_registry_service` + `seed_operational_workforce_registry`:

- Operation `cnc_cutting` → skill `SK_CNC_OPERATOR`, workcenter `WC_CNC_ROUTING`, default machine `MCH-CNC-4020`.
- ProductSystem aliases include `face_cnc_cut`, `back_cut`, `cnc_routing`.

Assignment runtime is **out of scope** for this foundation — no real employee/machine binding in Intake V4 preview.

### 13.6 Pricing vs task generation

Pricing uses CostEngine `priced_operation` + workcenter rates (`CNC_ROUTER`). Task generation uses catalog + tpl keys. Shared CNC rows document both `dossier_operation_key` and `pricing_rate_key` so future builds can wire rates without coupling task creation to quote costing.

## 14. Supplementary audit — machines, skills, catalog, task generator

| Question | Answer |
|----------|--------|
| CNC utilaj în registry? | **Yes** — `MCH-CNC-4020` (`cnc_router`), `MCH-CNC-ROUTER-01` in tests; `machines` table / operational registry |
| Stație CNC? | **Yes** — `cnc_router` (tpl/UI), `WC_CNC_ROUTING` (operational), `CNC_ROUTER` (pricing workcenter) — **three namespaces** |
| Skill operator CNC? | **Yes** — `SK_CNC_OPERATOR` (registry), `cnc_operator` (tpl/frontend), `cnc_router_operation` (V3 catalog) |
| Catalog mapat la stație/utilaj? | **Partial** — catalog has station+skill; bundled `face_and_backing_cnc_cut`; operational registry maps `cnc_cutting` → machine |
| Task generator uses station/skill? | **Yes** — dry-run `station_hint`/`role_hint`; preview `required_station`/`required_skill` |
| Where to link Shared CNC model? | Material breakdown `operation_rows` → task dry-run via `cnc_preview_row_to_task_candidate_hints()` → enrich `IntakeV4TaskGenerationTaskCandidate` |
| Gap for real CNC task assignment? | Unify skill key namespaces; split catalog bundle; wire bevel rows; Order→ExecutionTask writer; employee eligibility API in operator UI |

### Known mapping gaps (`pending_mapping`)

- Separate face/back **bevel** rows — bundled in dossier `face_cnc_cut` / `back_cut`.
- Material-specific pricing keys (e.g. `cnc_cutting_plexiglas_3mm`) — use workcenter rate until defined.
- `TPL-CNC-CUTTING-SERVICE` — no dossier/catalog keys yet.
- CostEngine `back_cut` pass count (3) vs owner preview (5) — pricing alignment build.

## 15. Recommended implementation order (updated)

1. ✅ Shared CNC operation preview + production bindings on `operation_rows`.
2. Wire task dry-run to consume shared CNC rows (replace duplicate MATERIAL_JOB CNC hints).
3. Operator backing selector UI → `back_bevel_enabled`.
4. Read-only workcenter rate lookup.
5. Align CostEngine `back_cut` with 5-pass owner rule.
6. `TPL-CNC-CUTTING-SERVICE` onboarding.
7. ExecutionTask assignment bridge (post-Order) using operational registry.

## 16. Material Process Profiles

Implementation: `backend/services/shared_cnc_material_process_profiles.py`

Profiles link **material stock**, **pricing keys**, and **CNC machining rules** without merging material rows with operation rows.

### Plexiglas 3 mm (`plexiglas_3mm`)

| Field | Value |
|-------|-------|
| Denumire | Plexiglas 3 mm |
| Familie | plexiglas |
| Grosime | 3 mm |
| Stoc / inventory key | `MAT-ACP-FATA-LITERE` (**mapped**) |
| Unitate stoc | m² |
| Preț material | `inventory_materials:MAT-ACP-FATA-LITERE` — **pending_mapping** (price from `/inventory/pricing`) |
| Operații permise | cutting, bevel |
| Adâncime / trecere | 3.5 mm / 1 pass |
| Owner override | no |
| Șanfren | permis, **implicit obligatoriu** (TPL-VOLUMETRIC-LETTERS) |
| Utilaj | cnc_router (`MCH-CNC-4020`) |
| Skill | cnc_operator / `SK_CNC_OPERATOR` |
| Operație pricing | `workcenter_rates:CNC_ROUTER:per_linear_meter` — **missing_rate** in preview |

Note: `MAT-PLEXI-OPAL-3MM` exists in inventory stubs but volumetric template uses operational code `MAT-ACP-FATA-LITERE` (PMMA 3 mm, legacy ACP in code name).

### Forex 10 mm (`forex_10mm`)

| Field | Value |
|-------|-------|
| Denumire | Forex 10 mm |
| Familie | forex |
| Grosime | 10 mm |
| Stoc / inventory key | `MAT-SPATE-PVC-LITERE` (**mapped**) |
| Unitate stoc | m² |
| Preț material | `inventory_materials:MAT-SPATE-PVC-LITERE` — **pending_mapping** |
| Operații permise | cutting, bevel |
| Adâncime / treceri | 3.5 mm / **5 passes** |
| Owner override | **yes** |
| Șanfren | permis, implicit **no** (optional backing bevel) |
| Utilaj / skill | cnc_router / cnc_operator |
| Operație pricing | workcenter CNC_ROUTER — **missing_rate** in preview |

### Extensibility

Registry `CNC_MATERIAL_PROCESS_PROFILES` accepts future entries: Plexiglas 5 mm, Forex 3/5 mm, ACM/Dibond, MDF, etc. Use `stock_mapping_status=pending_mapping` until inventory codes are owner-confirmed.

### Material vs operation outputs

- **Material row** (`CncMaterialCostPreviewRow`): `row_type=material`, stock key, `consumes_stock_now=false` always in preview.
- **Operation row** (`CncOperationPreviewRow`): `material_key` links processed material; `consumes_stock_now=false`, `creates_task_now=false`.

### Internal vs client material (`TPL-CNC-CUTTING-SERVICE`)

| | `internal_stock` | `client_supplied` |
|---|------------------|-------------------|
| Material preview row | Yes (if area known) | **No** — no internal cost/stock |
| CNC operation rows | Yes | Yes |
| Warnings | missing price/stock mapping | client material liability |
| Stock consumption | **Never in preview** | Never |

## 17. Inventory / stock audit (supplementary)

| # | Finding |
|---|---------|
| Plexiglas 3 mm in registry? | **Yes** — `MAT-ACP-FATA-LITERE` (canonical PMMA 3 mm face); also stub `MAT-PLEXI-OPAL-3MM` not wired to volumetric breakdown |
| Forex 10 mm in registry? | **Yes** — `MAT-SPATE-PVC-LITERE` (PVC expandat 10 mm / Forex display name) |
| Material prices? | Tests/seed may set `unit_cost`; production path reads `/inventory/pricing` — preview does **not** invent prices |
| Aliases / canonical | `material_canonical_naming.py` documents canonical names; no runtime alias merge for volumetric codes |
| Material breakdown compatible? | **Yes** — `MATERIAL_REGISTRY_CODES` matches profile `stock_material_key` |
| Material availability? | Intake V3 `material_availability_service` — V4 breakdown feeds quote estimate rows; availability attach on order/quote path |
| Gap for real stock consumption? | Order binding + execution guard; inventory deduction service; profile→availability row bridge for V4 |

Preview may show stock mapping status and missing price warnings — **never consumes stock**.

## 18. Intake V4 backing integration (2026-06)

- Operator `backing_mode` on `finish_setup`: `none | forex_10_no_bevel | forex_10_with_bevel` overrides layer-role backing fallback.
- Material breakdown emits Plexiglas 3 mm / față and Forex 10 mm / spate only when backing active.
- CNC `operation_rows` from `build_volumetric_letters_cnc_operation_rows` — separate from material rows.

## 19. Task dry-run preview consumes `operation_rows` (2026-06)

**Canonical source:** `CNC_TASK_DRY_RUN_SOURCE = "operation_rows"` in `intake_v4_cnc_operation_dry_run_service.py`.

When Material Breakdown emits CNC `operation_rows`:

- Intake V4 **task generation dry-run** (`intake_v4_task_generation_dry_run_service`) derives CNC task candidates from those rows via `cnc_operation_row_to_task_candidate()`.
- Intake V4 **production task dry-run** (`intake_v4_production_task_dry_run_service`) appends V3-style candidate tasks via `build_iv3_cnc_candidate_tasks_from_operation_rows()` and drops aggregated catalog seed `face_and_backing_cnc_cut`.
- **Production handoff preview** exposes `cnc_operation_candidates`, `cnc_task_source`, and `legacy_cnc_mapping_used` on the handoff response.

**Fallback:** `legacy_parallel_mapping` only when `operation_rows` are completely missing — emits a warning, not silent divergence.

**Non-goals (this alignment):** real ExecutionTask creation, ExecutionPlan, `tasks_json`, stock consumption, Pricing Registry / CostEngine changes.

Bridge helper: `cnc_preview_row_to_task_candidate_hints()` in `shared_cnc_operation_model.py` documents field mapping; runtime path uses `IntakeV4CncOperationRow` directly.

## Code references

- `backend/services/shared_cnc_material_process_profiles.py`
- `backend/services/shared_cnc_operation_model.py`
- `backend/seeds/seed_build4_templates.py` (`face_cnc_cut`, `back_cut`)
- `backend/services/formula_handlers.py` (`perimeter_pass_linear_meter`)
- `backend/services/tpl_volumetric_operation_keys_service.py`
- `backend/services/intake_v4_cnc_operation_dry_run_service.py`
- `backend/services/intake_v4_task_generation_dry_run_service.py`
- `backend/services/intake_v4_production_preview_service.py`
- `backend/services/intake_v3_production_handoff_adapter.py` (operation catalog)
- `backend/seeds/seed_operational_workforce_registry.py`
- `backend/services/operational_registry_service.py`
- `frontend/src/lib/workstationRouting.ts`
