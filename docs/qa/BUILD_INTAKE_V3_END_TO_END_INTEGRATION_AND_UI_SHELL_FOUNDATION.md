# BUILD — INTAKE_V3_END_TO_END_INTEGRATION_AND_UI_SHELL_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `225e054` (base; changes uncommitted)  
**Verdict:** **PASS**

## Purpose

Compose Intake V3 services into a single workspace preview and expose a minimal preview-only UI shell at `/intake-v3` — without quote/order/execution/inventory side effects.

## Scope

| In scope | Out of scope |
|----------|--------------|
| `intake_v3_workspace_preview_service` | CostEngine / pricing formulas |
| Preview contracts (backend + TS alignment) | DB schema / migrations |
| UI shell + HUB fixture | Quote/order/plan creation |
| Backend + frontend tests | Employee Mobile runtime |
| Docs + QA | Intake V2 changes |

## Files changed

### Backend
- `backend/schemas/intake_v3.py` — `IntakeV3WorkspacePreview`, `IntakeV3BoundaryFlags`, section status models
- `backend/services/intake_v3_workspace_preview_service.py` — **new** composition orchestrator
- `backend/tests/test_intake_v3_workspace_preview_service.py` — **new** (8 tests)

### Frontend
- `frontend/src/lib/intakeV3/contracts.ts` — extended blocker codes + preview types
- `frontend/src/lib/intakeV3/fixtures.ts` — **new** HUB scenarios
- `frontend/src/lib/intakeV3/previewHelpers.ts` — **new** mock preview builder
- `frontend/src/components/workos/intake-v3/IntakeV3PreviewShell.tsx` — **new**
- `frontend/src/pages/IntakeV3App.tsx` — **new**
- `frontend/src/pages/IntakeV3App.test.tsx` — **new** (5 tests)
- `frontend/src/App.tsx` — route `/intake-v3`

### Docs
- `docs/intake-v3/00_STATUS.md`
- `docs/intake-v3/03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md`
- `docs/intake-v3/04_READINESS_AND_BLOCKERS_MODEL.md`
- `docs/intake-v3/06_BUILD_ROADMAP.md`
- `docs/intake-v3/07_DECISIONS_LOG.md`
- `docs/intake-v3/templates/TPL-VOLUMETRIC-LETTERS/09_PRICING_INPUT_ADAPTER.md`
- `docs/intake-v3/templates/TPL-VOLUMETRIC-LETTERS/10_PRODUCTION_HANDOFF_ADAPTER.md`
- `docs/intake-v3/templates/TPL-VOLUMETRIC-LETTERS/11_EMPLOYEE_MOBILE_PREVIEW_BOUNDARY.md`

## Backend composition

`build_intake_v3_workspace_preview(workspace)` calls existing services only:

- `evaluate_intake_v3_readiness`
- `validate_confirmed_production_model`
- `validate_finish_assignment` / `derive_material_intent`
- `build_pricing_input_candidate`
- `build_production_handoff_preview`

Boundary flags always false for real actions; `preview_only=true`.

## UI Shell

- **Route:** `/intake-v3`
- **Default fixture:** HUB MEDIA PRODUCTION — 18/27/9, return wrapped + face vinyl
- **Sections:** workspace, vector, finish, material, readiness, pricing preview, handoff seeds, disabled actions
- **Protections:** no API save; disabled CTA buttons; boundary banner

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_workspace_preview_service.py tests/test_intake_v3_production_handoff_adapter.py tests/test_intake_v3_pricing_input_adapter.py tests/test_intake_v3_finish_and_material_workflow.py tests/test_intake_v3_vector_and_letter_model.py tests/test_intake_v3_architecture_contracts.py tests/test_volumetric_execution_task_order.py tests/test_volumetric_finish_assignment_normalization.py tests/test_volumetric_quote_input_policy.py -q
# 105 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx
# 5 passed
```

## Pending / open

- Backend HTTP endpoint for preview (optional)
- Full editable workspace UI (upload, save, tabs)
- Scenario B (painted) in UI scenario switcher (fixture exists, default is wrapped)
- DB persistence `intake_schema_version=3`

## Boundary confirmation

No CostEngine, inventory, DB, quote/order/plan creation, Employee Mobile runtime, Intake V2 changes, hardcoded employees, commit, or push.

## Recommended commit message

```
feat(intake-v3): add end-to-end workspace preview and UI shell foundation

Compose readiness, adapters, and boundary flags into workspace preview service
and expose preview-only /intake-v3 shell with HUB fixture. No quote/order/plan.
```
