# BUILD — INTAKE_V3_FINISH_ASSIGNMENT_PER_LETTER_GROUP_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base commit:** `a1a07f1` — confirmed production model review foundation  
**Verdict:** PASS (local, uncommitted)

---

## Scope

Operator can assign finish overrides per letter group or per individual letter after confirming the production model. Global finish remains the default fallback. Payload-only persistence in `intake_v3_workspaces.payload_json` — no quote, order, execution plan, inventory, CostEngine, or Intake V2 changes.

## Payload / confirmed model audit

| Field | Location | Notes |
|-------|----------|-------|
| `confirmed_production_model` | workspace payload | Required before assignments |
| `letter_model.letters[]` | confirmed model | Scaffold IDs `L-01`…`L-18` (HUB 18/27/9) |
| Hole contours | `cut_contour_model` | `C-HOLE-01`… — **not** assignment targets |
| `finish_assignment` | workspace payload | Global default (face / return / backing) |
| `letter_group_finish_assignments` | workspace payload | New — group overrides |
| `letter_finish_assignments` | workspace payload | New — per-letter overrides |
| `finish_assignment_status` | workspace payload | `global_only` \| `group_overrides` \| `letter_overrides` \| `mixed` |

**Modeling decision:** Reuse existing `FinishAssignment.groups` sync for validators/preview; store canonical group/letter lists separately for UI and precedence resolution. No new DB table.

**Pending:** Visual SVG letter selection, per-path CNC geometry mapping, granular pricing per group (separate build).

## Precedence

1. **Letter override** (enabled)
2. **Group override** (enabled, if letter not overridden)
3. **Global finish** (`finish_assignment`)

`enabled=false` assignments are stored but ignored for effective finish.

## Backend

### Service

`backend/services/intake_v3_finish_assignment_service.py`

- `get_confirmed_letter_targets`
- `validate_finish_assignments`
- `apply_finish_assignments_to_payload`
- `resolve_effective_finish_for_letter`
- `summarize_finish_assignments`

### Endpoints

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/api/v1/intake-v3/workspaces/{id}/finish-assignments/targets` | Letter targets from confirmed model |
| GET | `/api/v1/intake-v3/workspaces/{id}/finish-assignments` | Current assignments + summary |
| PATCH | `/api/v1/intake-v3/workspaces/{id}/finish-assignments` | Validate, save, regenerate preview |

### Validation

- Requires confirmed production model (PATCH)
- Rejects unknown letter IDs and hole IDs (`C-HOLE-*`)
- Reuses `validate_finish_assignment` for wrapped return depth, painted return, face vinyl roll width
- Disabled-only assignments do not block global finish readiness

### Preview integration

`IntakeV3FinishSummary` extended with `finish_variations_present`, `assignment_summary`, counts. No pricing formula changes.

## Frontend

- `IntakeV3FinishAssignmentPanel` — group form, letter override form, summary, save
- Integrated in `IntakeV3App` after production model review
- Command bar shows finish assignment status
- Preview shell shows finish variations note when present

## Tests

### Backend targeted

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_finish_assignments.py tests/test_intake_v3_production_model_review.py tests/test_intake_v3_svg_upload_analysis.py -q
```

**Result:** 28 passed

### Backend regression

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_workspace_field_editor.py tests/test_intake_v3_workspace_persistence.py tests/test_intake_v3_preview_endpoint.py tests/test_intake_v3_workspace_preview_service.py tests/test_intake_v3_vector_and_letter_model.py tests/test_intake_v3_finish_and_material_workflow.py tests/test_volumetric_execution_task_order.py -q
```

**Result:** 75 passed

### Frontend targeted

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
```

**Result:** 54 passed

## Boundary confirmation

| Area | Touched? |
|------|----------|
| CostEngine / pricing formulas | ❌ |
| Inventory / StockMovement | ❌ |
| Quote / order creation | ❌ |
| ExecutionPlan / ExecutionTask runtime | ❌ |
| Employee Mobile | ❌ |
| Intake V2 | ❌ |
| DB migration | ❌ |
| Commit / push | ❌ |

## Open questions

- Granular pricing input per group/letter — deferred to dedicated build
- Visual SVG click-to-select letters — deferred
- Whether `letter_custom` mode should require per-letter confirmation flags in UI (warning only today)

## Recommended commit message

```
feat(intake-v3): add finish assignment per letter and group foundation
```
