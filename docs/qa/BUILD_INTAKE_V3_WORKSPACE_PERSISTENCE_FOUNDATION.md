# BUILD — INTAKE_V3_WORKSPACE_PERSISTENCE_FOUNDATION

**Date:** 2026-06-18  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD:** `fa580de` (base; changes uncommitted)  
**Backup note:** `C:\Users\offic\Desktop\salvari\workos_backup_after_intake_v3_readonly_preview_switcher_fa580de_20260618_1633.zip`  
**Verdict:** **PASS**

## Purpose

Add draft workspace persistence for Intake V3 — save/load/list/archive workspaces and preview from saved payload — without quote/order/execution/inventory side effects.

## Audit — storage / migration conventions

| Finding | Choice |
|---------|--------|
| ORM | SQLAlchemy declarative, `core.database.Base` |
| Models | `backend/models/*.py`, registered in `models/__init__.py` |
| JSON | `Text` columns + `json.dumps` / `json.loads` (project pattern) |
| Timestamps | `DateTime(timezone=True)` + `func.now()` / `onupdate` |
| User ids | `String` UUID from `UserResponse.id` |
| Migrations | Alembic `backend/alembic/versions/sNN_*.py` sprint labels |
| Tests | `IsolatedDBFixture` + `auth_client` from `conftest.py` |
| Dev boot | `Base.metadata.create_all` when model imported |

**Avoided:** mutating `intake_requests`, CostEngine, quotes/orders tables, inventory.

## DB model / migration

| Item | Value |
|------|-------|
| Model | `IntakeV3WorkspaceRecord` — `backend/models/intake_v3_workspace.py` |
| Table | `intake_v3_workspaces` |
| Migration | `s52_add_intake_v3_workspaces` |
| PK | `id` String(36) UUID |
| Unique | `workspace_code` |
| JSON fields | `payload_json`, `preview_snapshot_json`, `metadata_json` |
| Indexes | `workspace_code`, `template_code`, `status`, `created_at`, `created_by_user_id`, `archived_at` |
| Soft delete | `archived_at` + `status=archived` |

### Status values

`draft`, `collecting_data`, `blocked`, `ready_for_quote_preview`, `archived`

## Backend service

`backend/services/intake_v3_workspace_service.py`:

- `sanitize_intake_v3_workspace_payload()` — strips forbidden ids; forces `inventory_mutation_allowed=false`, `preview_only=true`, `non_executable=true`
- `create_intake_v3_workspace`, `get`, `list`, `update`, `archive`
- `seed_workspace_from_preview_scenario`
- `build_preview_for_workspace_record` — regenerates preview via `build_intake_v3_workspace_preview`

## Endpoints

| Method | Path |
|--------|------|
| GET | `/api/v1/intake-v3/workspaces` |
| POST | `/api/v1/intake-v3/workspaces` |
| GET | `/api/v1/intake-v3/workspaces/{workspace_id}` |
| PATCH | `/api/v1/intake-v3/workspaces/{workspace_id}` |
| POST | `/api/v1/intake-v3/workspaces/{workspace_id}/archive` |
| GET | `/api/v1/intake-v3/workspaces/{workspace_id}/preview` |
| POST | `/api/v1/intake-v3/workspaces/seed-from-scenario` |

Existing scenario preview `GET /api/v1/intake-v3/preview` unchanged.

## Files changed

### Backend (new)
- `backend/models/intake_v3_workspace.py`
- `backend/alembic/versions/s52_add_intake_v3_workspaces.py`
- `backend/services/intake_v3_workspace_service.py`
- `backend/routers/intake_v3_workspaces.py`
- `backend/tests/test_intake_v3_workspace_persistence.py`

### Backend (modified)
- `backend/models/__init__.py`
- `backend/schemas/intake_v3.py` — persistence API contracts

### Frontend
- `frontend/src/lib/intakeV3/api.ts` — workspace CRUD + preview
- `frontend/src/lib/intakeV3/contracts.ts` — workspace types
- `frontend/src/pages/IntakeV3App.tsx` — draft UI
- `frontend/src/components/workos/intake-v3/IntakeV3PreviewShell.tsx` — boundary banner
- `frontend/src/pages/IntakeV3App.test.tsx` — 9 tests

### Docs
- `docs/intake-v3/00_STATUS.md`, `02`, `03`, `06`, `07`, `10_PRODUCTION_HANDOFF_ADAPTER.md`

## UI changes

- Header: **Preview + Draft Workspace**
- Scenario selector + **Create draft from selected scenario**
- Workspace list/selector, title save, archive
- Preview sources: backend scenario / saved workspace / local fallback
- Boundary banner: **Draft workspace only** — quote/order/plan/inventory disabled

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_workspace_persistence.py tests/test_intake_v3_preview_endpoint.py tests/test_intake_v3_workspace_preview_service.py -q
# 26 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_production_handoff_adapter.py tests/test_intake_v3_pricing_input_adapter.py tests/test_intake_v3_finish_and_material_workflow.py tests/test_intake_v3_vector_and_letter_model.py tests/test_intake_v3_architecture_contracts.py tests/test_volumetric_execution_task_order.py tests/test_volumetric_finish_assignment_normalization.py tests/test_volumetric_quote_input_policy.py -q
# 97 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx
# 9 passed
```

## Boundary confirmation

- No CostEngine / pricing formulas / TVA / commercial markup
- No inventory / StockMovement
- No quote / order / execution plan / task creation
- No Employee Mobile runtime
- No Intake V2 changes
- No hardcoded employees
- No `backend/dev.db` manual edits
- No commit / push

## Limitations / pending

- No full field editor for workspace zones (title + seed only)
- No real SVG upload/parser
- `preview_snapshot_json` updated on preview GET; not a cache layer
- Alembic `s52` must be applied in staged/prod; dev uses `create_all`
- Quote handoff from persisted workspace not wired (by design)

## Recommended commit message

```
feat(intake-v3): add workspace draft persistence foundation
```
