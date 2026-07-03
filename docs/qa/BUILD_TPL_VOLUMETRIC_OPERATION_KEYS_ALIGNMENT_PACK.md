# BUILD_TPL_VOLUMETRIC_OPERATION_KEYS_ALIGNMENT_PACK

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before build | `845a2f32fc20928189cd8b04e369d5606fe42910` |
| Build flags | `creates_execution_tasks=false`, `writes_execution_plan=false`, `stock_consumption=false`, `template_operation_alignment=true`, `reduces_provisional_tasks=true` |

## Working tree status (at build time)

Dirty V2/V3 WIP, `tmp/`, atoms/audit untracked — **not part of this build commit scope**.

**Files changed by this build only:**

- `backend/services/tpl_volumetric_operation_keys_service.py` (NEW)
- `backend/schemas/intake_v4.py`
- `backend/services/intake_v4_production_handoff_preview_service.py`
- `backend/services/intake_v4_task_generation_dry_run_service.py`
- `backend/services/intake_v4_order_bound_task_readiness_service.py`
- `backend/tests/test_tpl_volumetric_operation_keys_alignment.py` (NEW)
- `frontend/src/lib/intakeV4/intakeV4Api.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4TaskGenerationDryRunPanel.tsx`
- `docs/qa/BUILD_TPL_VOLUMETRIC_OPERATION_KEYS_ALIGNMENT_PACK.md` (this file)

## Part 1 — Audit summary

### A. Dossier / ProductSystem / template

| Source | Location | Operation keys |
|--------|----------|----------------|
| Dossier CostEngine mapping | `backend/seeds/seed_tpl_volumetric_letters_dossier.py` | 12 keys: `vector_prep`, `face_cnc_cut`, `back_cut`, `side_forming`, `return_face_bonding`, `led_install_letters`, `electrical_letters`, `painting`, `vinyl_application`, `packaging_letters`, `mounting_template_cnc_cut`, `qc_letters` |
| ProductSystem seed | `backend/seeds/seed_build4_templates.py` | Adds `assembly_letters`; runtime injects `return_vinyl_application` |
| Intake catalog (doc) | `intake_v3_production_handoff_adapter.py` / `05_OPERATION_CATALOG.md` | 13 long descriptive codes (e.g. `graphic_vector_preflight`, `face_and_backing_cnc_cut`) |
| V4 dry-run task_key | `intake_v4_task_generation_dry_run_service.py` | ~15 task keys (e.g. `cnc_face_cutting`, `letter_assembly`) |

**Owner-confirmed in dossier:** all 12 priced operations above.

**Documented only / runtime:** `assembly_letters` (PS), `return_vinyl_application` (runtime).

**Missing from V4 form:** `back_bevel_enabled`, mounting bar/template capture for task split, RAL painting dry-run split, Oracal multi-color per-layer warnings.

### B. Production handoff preview (before → after)

**Before:** 7 operation groups with catalog `operation_codes` only.

**After:** Each group includes `canonical_operation_keys` + `template_alignment` (`aligned` / `partial` / `missing` / `not_applicable`).

### C. Task dry-run (before → after)

**Before:** `operation_key` = dossier key; provisional heuristic from dossier membership.

**After:** Adds `canonical_operation_key`, `template_alignment_status`, `dossier_backed`, `critical_for_execution`, `future_execution_task_type`, `provisional_reason`. Confirmed CNC/vinyl/return/LED ops no longer provisional; assembly remains provisional.

### D. ExecutionPlanService (read-only audit)

`PlannedTask.to_dict()` fields for future adapter mapping:

| Field | Maps from canonical pack |
|-------|--------------------------|
| `task_id` | generated at write time |
| `name` / `display_name` | `TplVolumetricOperationSpec.label` + `volumetric_execution_dispatch` |
| `process_type` | `future_execution_task_type` (e.g. `cnc_routing`, `led_wiring`) |
| `process_id` | `future_process_id` / dossier key |
| `machine_type` | TBD — station_hint → workcenter registry |
| `layer_id` | from order snapshot layers |
| `quantity` | material job quantity basis |
| `estimated_time_minutes` | `VOLUMETRIC_PRICED_OP_SCHEDULING_MINUTES` / priced breakdown |
| `instructions` / `documents` | not in this build |
| Employee Mobile | reads `execution_plan.tasks_json` via `employee_mobile_tasks_service` |

**No write adapter implemented in this build.**

## Part 2 — Canonical operation registry

**Module:** `backend/services/tpl_volumetric_operation_keys_service.py`

Runtime canonical helper mirrors current TPL dossier operation keys until ProductSystem operation registry is made runtime-readable.

**32 canonical operation keys** covering preflight, CNC, vinyl/print, return, LED, assembly/QC/packaging, mounting, painting.

Each spec includes: label, station_hint, role_hint, dossier_operation_key, future_execution_task_type, template_backed, dossier_backed, requires_material_job, requires_finish, requires_mounting_data, critical_for_execution, can_generate_task_candidate, provisional_reason.

## Part 3 — Mapping table summary

| handoff_group | canonical keys (sample) | dry_run_task_key | future_execution_task_type | status |
|---------------|-------------------------|------------------|----------------------------|--------|
| cnc_cutting | cnc_face_cutting, cnc_backing_cutting | cnc_face_cutting, cnc_backing_cutting | cnc_routing | confirmed |
| vinyl_print_finish | vinyl_cutting, print, laminate, face_finish | oracal_vinyl_cutting, print_artwork, … | vinyl_cutting | confirmed |
| return_forming | return_side_forming | return_side_forming | edge_bending | confirmed |
| return_bonding | return_side_bonding | return_face_bonding | welding | confirmed |
| led_electrical | led_module_install, electrical_wiring, light_test | led_module_install, psu_electrical_wiring, light_test_qc | led_assembly / led_wiring / quality_control | confirmed / partial (PSU split) |
| assembly | letter_assembly | letter_assembly | volumetric_letter_assembly | partial |
| preflight_qc | preflight, production_file_prep, packaging, QC | preflight_vector_and_layers, … | file_preparation / packaging / quality_control | aligned / partial |

Full export: `get_mapping_catalog()` → `mapping_table` list.

## Part 4 — Production handoff preview changes

- `IntakeV4ProductionHandoffOperationGroup` extended with `canonical_operation_keys`, `template_alignment`.
- Summary includes `template_operation_alignment` aggregate counts.

## Part 5 — Task dry-run changes

- Candidates enriched via `enrich_task_candidate_alignment()`.
- Assembly uses `assembly_letters` dossier reference (not `packaging_letters` proxy).
- Summary includes `template_operation_alignment` with `blocks_real_task_generation`.
- Warning `template_operation_alignment_partial` when handoff groups incomplete.

## Part 6 — Readiness update

- `IntakeV4OrderBoundTaskReadinessResponse.template_operation_alignment` populated from dry-run summary.
- Warning when `blocks_real_task_generation=true`.
- `can_generate_real_tasks=false` unchanged.

## Part 7 — UI changes

- `IntakeV4TaskGenerationDryRunPanel`: shows alignment status, aligned/partial/missing counts, critical provisional task list.

## What this build does NOT do

- No `ExecutionTask` / `ExecutionPlan` creation or `tasks_json` writes
- No stock consumption / reservations
- No Quote/Order status changes
- No CostEngine / Pricing Registry changes
- No V2/V3 dirty file changes
- No real task generation enablement (`can_generate_real_tasks` stays false)

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_tpl_volumetric_operation_keys_alignment.py -q
# 22 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_task_generation_dry_run.py -q
# 11 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_production_handoff_preview.py -q
# 6 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_order_bound_task_readiness.py -q
# 18 passed
```

Vitest/E2E: **not run** — backend-only contract build; frontend change is read-only display of existing API summary fields.

## PASS / FAIL

**PASS** — all PASS criteria met:

1. Canonical mapping for TPL-VOLUMETRIC-LETTERS exists
2. Handoff preview reports alignment status
3. Dry-run includes `canonical_operation_key`
4. Provisional reduced for confirmed ops (CNC, vinyl, return, LED)
5. Real gaps remain marked (assembly, mounting, painting, back bevel)
6. Readiness reports alignment summary
7–11. No execution plan write, no real tasks, no stock, no Quote/Order mutation
12. Backend tests green
13. V2/V3 dirty untouched by this build scope

## Remaining provisional gaps

| Gap | Reason |
|-----|--------|
| `letter_assembly` | ProductSystem `assembly_letters` not in dossier; execution schema mapping unconfirmed |
| Mounting template / bars | V4 form lacks mounting capture for task split |
| `cnc_backing_bevel_optional` | `back_bevel_enabled` not wired in V4 |
| `return_painting` | Finish-dependent; no dedicated dry-run candidate |
| Oracal multi-color | Per-layer color warnings only |
| LED pitch / PSU model | Shared dossier ops; pitch-specific task split deferred |
| `cleaning` | Catalog-only, no dossier priced op |

## Next recommended build

**BUILD_INTAKE_V4_EXECUTION_TASK_WRITE_ADAPTER** (or equivalent gated build):

1. Map canonical registry → `PlannedTask` / `tasks_json` schema
2. Confirm `assembly_letters` in dossier or explicit PS→Execution adapter
3. Wire mounting/back bevel V4 form fields before enabling mounting tasks
4. Enable `can_generate_real_tasks` only when alignment `critical_missing_count=0` and owner/order gates pass
5. Employee Mobile smoke on generated `tasks_json`

## Commit recommendation

**Recommend commit** of the 9 files listed in scope above only — exclude V2/V3 WIP and `tmp/`.

Suggested message:

```
feat(intake-v4): align TPL-VOLUMETRIC operation keys for handoff and dry-run

Add canonical operation registry and template alignment reporting without
enabling real task generation or execution plan writes.
```
