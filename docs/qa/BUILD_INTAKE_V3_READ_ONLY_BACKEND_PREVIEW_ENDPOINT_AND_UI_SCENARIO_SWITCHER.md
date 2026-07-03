# BUILD — INTAKE_V3_READ_ONLY_BACKEND_PREVIEW_ENDPOINT_AND_UI_SCENARIO_SWITCHER

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `e6c3361` (base; changes uncommitted)  
**Verdict:** **PASS**

## Purpose

Expose a read-only backend preview endpoint for Intake V3 and wire `/intake-v3` to consume it with a scenario selector, local fixture fallback, and permanent preview-only boundary — no quote/order/plan/inventory side effects.

## Scope

| In scope | Out of scope |
|----------|--------------|
| `GET /api/v1/intake-v3/preview` read-only | CostEngine / pricing formulas |
| Scenario fixture builder (3 HUB scenarios) | DB schema / migrations / writes |
| UI scenario selector + source mode | Quote/order/plan creation |
| Local fixture fallback on backend failure | Employee Mobile runtime |
| Backend + frontend tests | Intake V2 changes |
| Docs + QA | Inventory / StockMovement |

## Endpoint

| Property | Value |
|----------|-------|
| Method | `GET` |
| Path | `/api/v1/intake-v3/preview` |
| Query | `scenario=<id>` |
| List | `GET /api/v1/intake-v3/scenarios` |
| Auth | `get_current_user` (project standard) |
| Response | `IntakeV3PreviewBuildResult` |

### Scenarios

| ID | Intent |
|----|--------|
| `hub_wrapped_face_vinyl` | HUB 18/27/9, return wrapped + face vinyl, readiness OK |
| `hub_painted_face_vinyl` | Painted return after assembly; face vinyl after painting |
| `hub_missing_face_roll_width` | Blocker `MISSING_FACE_VINYL_ROLL_WIDTH`; preview still renders |

Unknown scenario → **400** with `supported_scenarios` list.

### Read-only guarantees

- No DB access or writes
- No quote / order / execution plan IDs in response
- `IntakeV3BoundaryFlags`: all action flags `false`, `preview_only=true`
- Composes existing `build_intake_v3_workspace_preview()` only

## Files changed

### Backend (new)
- `backend/services/intake_v3_preview_fixtures.py` — scenario workspace builders
- `backend/routers/intake_v3_preview.py` — read-only HTTP surface (auto-discovered)
- `backend/tests/test_intake_v3_preview_endpoint.py` — 7 tests

### Frontend
- `frontend/src/lib/intakeV3/api.ts` — **new** `fetchIntakeV3Preview`, `listLocalIntakeV3Scenarios`
- `frontend/src/lib/intakeV3/fixtures.ts` — added `hub_missing_face_roll_width`
- `frontend/src/pages/IntakeV3App.tsx` — scenario selector, loading, backend/fallback source
- `frontend/src/components/workos/intake-v3/IntakeV3PreviewShell.tsx` — boundary banner text alignment
- `frontend/src/pages/IntakeV3App.test.tsx` — 8 tests (mocked API)

### Docs
- `docs/intake-v3/00_STATUS.md`
- `docs/intake-v3/03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md`
- `docs/intake-v3/06_BUILD_ROADMAP.md`
- `docs/intake-v3/07_DECISIONS_LOG.md`
- `docs/intake-v3/templates/TPL-VOLUMETRIC-LETTERS/10_PRODUCTION_HANDOFF_ADAPTER.md`
- `docs/intake-v3/templates/TPL-VOLUMETRIC-LETTERS/11_EMPLOYEE_MOBILE_PREVIEW_BOUNDARY.md`

## UI behavior

- **Route:** `/intake-v3`
- **Scenario selector:** 3 options (wrapped, painted, missing roll width)
- **Source indicator:** `Backend preview` / `Local fixture fallback` / `Loading preview…`
- **Fallback banner:** shown when backend unavailable
- **Boundary banner:** permanent preview-only message
- **Actions:** Create quote / order / execution plan remain disabled

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_preview_endpoint.py tests/test_intake_v3_workspace_preview_service.py tests/test_intake_v3_production_handoff_adapter.py tests/test_intake_v3_pricing_input_adapter.py -q
# 37 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_finish_and_material_workflow.py tests/test_intake_v3_vector_and_letter_model.py tests/test_intake_v3_architecture_contracts.py tests/test_volumetric_execution_task_order.py tests/test_volumetric_finish_assignment_normalization.py tests/test_volumetric_quote_input_policy.py -q
# 75 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx
# 8 passed
```

## Boundary confirmation

- No CostEngine / pricing formula / TVA / commercial markup changes
- No inventory / StockMovement changes
- No DB schema / migrations / `dev.db` writes
- No quote / order / execution plan creation endpoints touched
- No ExecutionPlanService / ExecutionTask runtime changes
- No Employee Mobile runtime changes
- No Intake V2 changes
- No hardcoded employee names
- No commit / push (per build instruction)

## Pending / open

- Workspace persistence (`intake_schema_version=3`)
- Full Intake V3 editor UI (upload, save, tabs)
- Real SVG parser / Assisted Interpretation
- Optional unauthenticated dev preview endpoint (currently requires auth like other `/api/v1` routes)
- Frontend/backend fixture parity is intentional but not byte-identical (local fallback is static)

## Recommended commit message

```
feat(intake-v3): add read-only preview endpoint and UI scenario switcher
```
