# BUILD — INTAKE_V3_CONTROLLED_FIELD_EDITOR_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base HEAD:** `ed36e9f` (workspace persistence)  
**Verdict:** PASS (local, uncommitted)

---

## Scope

Transform `/intake-v3` persisted draft workspaces into **controlled-editable** drafts for volumetric letters. Operators can patch allowlisted fields, sanitize payload, regenerate preview (readiness + pricing input + production handoff), and see updated UI — without quote/order/execution/inventory/CostEngine changes.

**Out of scope:** SVG upload, graphic editor, quote/order creation, ExecutionPlan/Task runtime, Employee Mobile, Intake V2, DB migration.

---

## Payload shape audit (real saved JSON)

| Prompt path | Canonical payload path | Notes |
|-------------|------------------------|-------|
| `title` | workspace **record** `title` | not inside payload JSON |
| `dimensions.width_mm` | `client_request.width_mm` | alias accepted |
| `dimensions.height_mm` | `client_request.height_mm` | alias accepted |
| `dimensions.depth_mm` | `client_request.depth_mm` | optional |
| `support_context.support_mode` | `support_context.shared_support` + `client_request.mounting_intent` | synced on patch |
| `support_context.illuminated` | `support_context.illuminated` | default true when missing |
| `finish_assignment.face_finish.*` | same | `material` → `material_code`; `roll_width_mm` → `face_vinyl_roll_width_mm` |
| `finish_assignment.return_finish.*` | same | `material` → `material_code`; `depth_mm` → `return_depth_mm` |
| `finish_assignment.backing_finish.*` | same | |

Nested top-level keys: `client_request`, `finish_assignment`, `material_intent`, `production_handoff`, `employee_preview_seed`, `support_context` (optional, normalized on patch).

---

## Editable allowlist

Service: `backend/services/intake_v3_workspace_field_editor_service.py`

- `title`
- `dimensions.width_mm` / `height_mm` / `depth_mm` (aliases → `client_request.*`)
- `support_context.support_mode`, `support_context.illuminated`
- `finish_assignment.face_finish.enabled`, `finish_type`, `material`, `material_family`, `color_code`, `color_name`, `roll_width_mm`, `confirmed`
- `finish_assignment.return_finish.finish_type`, `depth_mm`, `material`, `material_family`, `color_code`, `color_name`, `confirmed`
- `finish_assignment.backing_finish.material`, `thickness_mm`, `color`, `confirmed`

Validation: positive dimensions, enum finish types, boolean flags, trimmed strings.

Patch semantics: **all-or-nothing** — any rejected patch blocks entire batch (HTTP 422).

---

## Forbidden fields

Rejected with HTTP 422, no payload mutation:

- `created_quote_id`, `quote_id`, `order_id`, `execution_plan_id`, `execution_task_id`, `stock_movement_id`
- `inventory_mutation_allowed`, `quote_creation_allowed`, `order_creation_allowed`, `execution_plan_creation_allowed`, `employee_mobile_action_allowed`
- `production_handoff.preview_only`, `production_handoff.task_seed`, `employee_preview_seed.non_executable`
- Any path outside allowlist

After valid patches: `sanitize_intake_v3_workspace_payload()` forces safe boundary flags.

---

## Backend endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| `GET` | `/api/v1/intake-v3/workspaces/editable-fields` | — | `IntakeV3EditableFieldsResponse` |
| `PATCH` | `/api/v1/intake-v3/workspaces/{workspace_id}/fields` | `IntakeV3WorkspaceFieldPatchRequest` | `IntakeV3WorkspaceFieldPatchResponse` |

`IntakeV3WorkspaceFieldPatchRequest`:

```json
{
  "patches": [{ "field_path": "dimensions.width_mm", "value": 8000 }],
  "regenerate_preview": true
}
```

`IntakeV3WorkspaceFieldPatchResponse`: `workspace`, `preview`, `applied_patches`, `rejected_patches`, `readiness_status`.

Archived workspaces: HTTP 400 `workspace_archived`.

---

## Sanitizer behavior

1. `validate_intake_v3_field_patch()` — allowlist + types  
2. `apply_intake_v3_field_patches()` — normalize `support_context`, apply nested sets  
3. `sanitize_intake_v3_workspace_payload()` — reset inventory/quote/order flags, `preview_only=true`, `non_executable=true`  
4. `build_preview_for_workspace_record()` when `regenerate_preview=true`

---

## UI editor

Component: `frontend/src/components/workos/intake-v3/IntakeV3FieldEditor.tsx`

- Sections: Workspace, Dimensions, Face finish, Return/cant, Backing, Support context
- Disabled until persisted workspace loaded (`getIntakeV3Workspace`)
- Batch **Save controlled fields** → `patchIntakeV3WorkspaceFields`
- States: Unsaved / Saving / Saved / Error saving
- Client validation: width/height > 0, optional roll width/depth > 0
- Preview refreshed from patch response; readiness blockers visible in `IntakeV3PreviewShell`
- Create quote/order/plan buttons remain disabled

---

## Tests

### Backend targeted

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_workspace_field_editor.py tests/test_intake_v3_workspace_persistence.py tests/test_intake_v3_preview_endpoint.py -q
```

**Result:** 29 passed

### Backend regression

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_workspace_preview_service.py tests/test_intake_v3_production_handoff_adapter.py tests/test_intake_v3_pricing_input_adapter.py tests/test_intake_v3_finish_and_material_workflow.py tests/test_intake_v3_vector_and_letter_model.py tests/test_intake_v3_architecture_contracts.py tests/test_volumetric_execution_task_order.py tests/test_volumetric_finish_assignment_normalization.py tests/test_volumetric_quote_input_policy.py -q
```

**Result:** 105 passed

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx
```

**Result:** 15 passed

---

## Safety boundaries confirmed

- No CostEngine / pricing formulas / TVA / commercial markup changes
- No Inventory / StockMovement
- No quote / order / ExecutionPlan / ExecutionTask creation
- No Employee Mobile runtime
- No Intake V2 changes
- No DB migration (Pydantic `support_context` on workspace model only)
- No commit / push

---

## Files changed

**Created**

- `backend/services/intake_v3_workspace_field_editor_service.py`
- `backend/tests/test_intake_v3_workspace_field_editor.py`
- `frontend/src/components/workos/intake-v3/IntakeV3FieldEditor.tsx`
- `docs/qa/BUILD_INTAKE_V3_CONTROLLED_FIELD_EDITOR_FOUNDATION.md`

**Modified**

- `backend/schemas/intake_v3.py` — patch schemas, `support_context` on workspace, painted trumps vinyl inference
- `backend/services/intake_v3_workspace_service.py` — `patch_intake_v3_workspace_fields`
- `backend/routers/intake_v3_workspaces.py` — fields + editable-fields routes
- `backend/services/intake_v3_workspace_preview_service.py` — support context in finish/material validation
- `backend/services/intake_v3_pricing_input_adapter.py` — `resolve_workspace_support_context`
- `frontend/src/lib/intakeV3/api.ts`, `contracts.ts`
- `frontend/src/pages/IntakeV3App.tsx`, `IntakeV3App.test.tsx`
- `docs/intake-v3/*` (status, lifecycle, readiness, roadmap, decisions, template docs)

---

## Pending work

- Per-field blur/auto-save (optional; batch save preferred)
- Full vector upload + Assisted Interpretation editor
- Operation Catalog first-class registry
- Quote handoff when operator explicitly triggers (separate build)
- `letter_custom` finish mode field editor granularity

---

## Recommended commit message

```
feat(intake-v3): add controlled field editor foundation for draft workspaces
```
