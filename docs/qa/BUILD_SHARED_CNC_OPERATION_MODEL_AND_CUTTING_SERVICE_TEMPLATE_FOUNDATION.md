# BUILD: Shared CNC Operation Model & Cutting Service Template Foundation

**Build name:** `AUDIT_AND_BUILD_SHARED_CNC_OPERATION_MODEL_AND_CUTTING_SERVICE_TEMPLATE_FOUNDATION`  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Status:** Foundation implemented (preview-only; no pricing registry / CostEngine changes)

## Owner decisions

- CNC/debitare/șanfren rules must not be hardcoded per product form.
- Shared module: `shared_cnc_operation_model` consumed by volumetric letters, future lightboxes, and `TPL-CNC-CUTTING-SERVICE`.
- Face letters: Plexiglas 3 mm, mandatory CNC cut + mandatory face bevel (separate operation rows, same perimeter).
- Backing: optional Forex 10 mm; cutting uses **5 passes** with `owner_pass_override=true` (not `ceil(10/3.5)=3`).
- Backing bevel only when operator selects bevel mode.
- Client-supplied material: no stock consumption, no material cost rows, liability warnings.
- LED area density (60 modules/m² for emblem/casetă): documented only — not implemented in this build.

## Audit findings

| Question | Finding |
|----------|---------|
| Where CNC ops defined? | `seed_build4_templates.py` — `face_cnc_cut`, `back_cut` with `perimeter_pass_linear_meter` |
| Generic vs template-specific? | Template-specific seeds; formula handler shared |
| Operation vs material pricing? | CostEngine uses workcenter `CNC_ROUTER` `rate_per_linear_meter` separately from material registry |
| CNC rates configured? | Yes in seeds/tests (1.5 EUR/ml/pass) — **not wired** to Intake V4 operation preview in this build |
| Operation DTO? | New `IntakeV4CncOperationRow` + `CncOperationPreviewRow` |
| Service templates? | None active; `TPL-CNC-CUTTING-SERVICE` contract defined in code only |
| Geometry keys | `face_cutting_perimeter_ml`, `cnc_cutting_perimeter_ml` via pricing input / path geometry |
| CNC in CostEngine? | Yes via template components — unchanged |
| Bevel in pricing input? | Partial via `back_bevel_enabled`; face bevel mandatory in preview model |
| Backing / Forex | Material rows when backing layer confirmed; CNC rows from shared model |
| Intake V4 hardcoding risk | Avoided by delegating to `shared_cnc_operation_model` |

## Supplementary audit — machines, skills, catalog, task generator

| # | Question | Finding |
|---|----------|---------|
| 1 | CNC utilaj în registry? | **Da** — `MCH-CNC-4020` (`cnc_router`) în `seed_operational_workforce_registry`; `machines` table / `MachineRegistry` |
| 2 | Stație CNC? | **Da** — `cnc_router` (tpl/UI), `WC_CNC_ROUTING` (operational), `CNC_ROUTER` (pricing workcenter) |
| 3 | Skill operator CNC? | **Da** — `SK_CNC_OPERATOR` (registry), `cnc_operator` (tpl), `cnc_router_operation` (V3 catalog) |
| 4 | Catalog → stație/utilaj? | **Parțial** — `face_and_backing_cnc_cut` → station `cnc_router`; operational `cnc_cutting` → `MCH-CNC-4020` |
| 5 | Task generator station/skill? | **Da** — dry-run `station_hint`/`role_hint`; preview `required_station`/`required_skill` |
| 6 | Unde legăm Shared CNC? | `operation_rows` → `cnc_preview_row_to_task_candidate_hints()` → task dry-run candidates (next build) |
| 7 | Gap pentru assignare reală? | Unificare skill namespaces; split catalog bundle; bevel dry-run rows; Order→ExecutionTask; eligibility API |

### Production integration (addendum)

Shared CNC rows now include `CncProductionResourceBinding`:

- `required_machine_key`, `machine_type`, `workstation_key`, `required_skill_key`
- `registry_skill_code`, `operation_catalog_key`, `dossier_operation_key`, `production_task_type`
- `resource_mapping_status`: `mapped` | `pending_mapping` with explicit `mapping_gaps`

Not an isolated calculator — rows align to tpl registry, V3 catalog, operational workforce registry, and **inventory material codes** via process profiles.

## Material process profiles (addendum)

- **File:** `backend/services/shared_cnc_material_process_profiles.py`
- **Profiles:** `plexiglas_3mm`, `forex_10mm`
- **Stock mapping:** `MAT-ACP-FATA-LITERE`, `MAT-SPATE-PVC-LITERE` — **mapped**
- **Material pricing:** `inventory_materials:<code>` — **pending_mapping** until `/inventory/pricing` wired to preview
- **Bundle:** `build_cutting_service_preview_bundle()` — internal vs client material behavior
- Preview: `consumes_stock_now=false` on all material and operation preview rows

## Inventory audit (addendum)

| Material | Registry code | Stock mapping | Price in preview |
|----------|---------------|---------------|----------------|
| Plexiglas 3 mm | MAT-ACP-FATA-LITERE | mapped | pending_mapping |
| Forex 10 mm | MAT-SPATE-PVC-LITERE | mapped | pending_mapping |

## Shared CNC model

- **File:** `backend/services/shared_cnc_operation_model.py`
- **Entities:** `CncOperationRule`, `CncOperationPreviewRow`, `CncProductionResourceBinding`
- **Builders:** `build_volumetric_letters_cnc_operation_rows`, `build_cutting_service_cnc_operation_rows`
- **Bridge:** `cnc_preview_row_to_task_candidate_hints()` (read-only task vocabulary)
- **Constants:** `FOREX_10MM_CUTTING_PASSES_OWNER = 5`, `REGISTRY_CNC_MACHINE_CODE = MCH-CNC-4020`

## TPL-CNC-CUTTING-SERVICE contract

Foundation in `build_cutting_service_cnc_operation_rows()`:

- Inputs: material source, family, thickness, perimeter, passes override, bevel flag
- Outputs: CNC operation rows + client-material warnings
- No UI onboarding, no quote creation in this build

## Material ours vs client

| | Internal | Client |
|---|----------|--------|
| Material breakdown rows | Yes | No |
| CNC operation rows | Yes | Yes |
| Stock | Quote estimate path only | Never |
| Warnings | missing_rate | + `CLIENT_MATERIAL_CNC_WARNINGS` |

## Face / backing / bevel model

- Face: always `cnc_face_cutting_plexiglas_3mm` + `cnc_face_bevel_plexiglas_3mm`
- Backing modes: `none` | `forex_10_no_bevel` | `forex_10_with_bevel`
- Resolved via `resolve_volumetric_backing_mode(backing_confirmed, back_bevel_enabled)`

## Forex 10 mm 5-pass rule

- `passes=5`, `owner_pass_override=true`, `depth_per_pass_mm=3.5`
- `operation_equivalent_quantity = perimeter_ml × 5`

## CNC as operation, not material

- `operation_rows` on `IntakeV4MaterialBreakdownResponse` — separate from `material_rows`
- UI section: "Operații CNC (preview — nu materiale)"

## Pricing / missing rate

- Default `pricing_status=missing_rate`, `estimated_cost=null`, `unit_price=null`
- UI: "Preț neconfigurat / necesită tarif operație CNC"
- Optional `configured_rate_eur_per_ml_pass` for tests only — not used in production breakdown path

## LED shared rule (future)

Documented in `docs/architecture/SHARED_CNC_OPERATION_MODEL_AND_CUTTING_SERVICE_TEMPLATE.md`:
- Volumetric: perimeter / pitch
- Emblem/casetă: `ceil(outbox_area_m2 × 60)`

## Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_shared_cnc_operation_model.py tests/test_shared_cnc_material_process_profiles.py -q
```

Result: **23 passed**

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
```

## Files changed

- `backend/services/shared_cnc_operation_model.py` (new)
- `backend/tests/test_shared_cnc_operation_model.py` (new)
- `backend/schemas/intake_v4.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `frontend/src/lib/intakeV4/intakeV4Api.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx`
- `docs/architecture/SHARED_CNC_OPERATION_MODEL_AND_CUTTING_SERVICE_TEMPLATE.md` (new)

## Boundaries (confirmed)

- No quote/order/task creation
- No ExecutionPlan / `tasks_json`
- No stock consumption
- No Pricing Registry mutation
- No CostEngine global changes
- No V2/V3/Auth changes
- No push in this build

## Next steps

1. Review-step backing selector UI (fără spate / Forex 10 mm fără/cu șanfren)
2. Read-only workcenter rate lookup into operation rows
3. Align CostEngine `back_cut` seed with owner 5-pass rule (separate pricing build)
4. `TPL-CNC-CUTTING-SERVICE` template onboarding
5. Shared LED area density module
