# BUILD: Production Plan Document Handoff + Optional Manual Task Instructions

## Purpose

Ensure technical execution information reaches Employee Mobile coherently:

1. Eligible intake work-files attach automatically to every task in `execution_plan.tasks_json` at plan generation.
2. Optional manual task `instructions` can be saved by admin/operator/manager and appear on Employee Mobile when present.
3. Clarification requests remain read-only visibility (no chat) from prior build `a24c370`.
4. Commercial/quote/snapshot pricing data stays blocked from `employee_mobile`.

## Audit — plan generation path

| Item | Finding |
|------|---------|
| Endpoint | `POST /api/v1/execution/plan/from-order/{order_id}` |
| Service | `ExecutionPlanService.from_order()` — snapshot-only task emission |
| Write-once | 409 `plan_already_exists` on duplicate |
| Integration | After `from_order()`, router loads eligible intake docs and calls `attach_documents_to_planned_tasks()` before persist |

## Order → intake

- Resolved via `orders.quote_id → quotes.intake_code`.
- Dev fixture order `1` → `WI-E2E-COMMERCIAL-001`.
- Safe link fields: `quotes.intake_code`, intake `product_spec_json.workFileAttachments`.

## Document handoff

**Service:** `backend/services/production_document_handoff_service.py`

- Loads `workFileAttachments` from intake linked to order.
- Filters commercial/quote/snapshot sources and suspicious PDF names.
- Normalizes plan metadata (no employee URL at plan storage).
- Dedupes by `source:id`; preserves existing task-level docs.
- Mobile layer adds employee-scoped download URL at read time.

**Plan task document shape (stored):**

```json
{
  "id": "sandu-sketch-001",
  "name": "Schiță litere volumetrice.svg",
  "type": "svg",
  "mime_type": "image/svg+xml",
  "source": "intake_work_file",
  "downloadable": true
}
```

## Manual instructions — no auto-generation

Instructions are **not** generated from `process_type` or task templates.

- Removed auto-generated operator placeholder text in `useOperatorData.ts` (was inventing generic instructions).
- Only explicit `tasks_json[*].instructions` values are shown on mobile.

## Editor (Variant B — implemented)

| Layer | Detail |
|-------|--------|
| API | `PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/instructions` |
| Permission | `execution.task_assign` (admin/operator/manager) |
| Storage | `execution_plan.tasks_json[*].instructions` |
| UI | `OperatorTaskAssignmentPanel` — textarea **Instrucțiuni execuție** + Salvează |
| Mobile | Read-only display in task detail |

Empty string removes the field. Does not touch `execution_reality` or task status.

## When no instructions exist

Employee Mobile shows empty instructions state; task remains fully actionable.

## Sandu fixture extension

Script: `backend/scripts/dev_seed_employee_mobile_sandu_fixture.py --apply`

Dev-only idempotent actions added:

- Backfill plan task `documents[]` from intake work-file on existing order `1` plan.
- Set smoke instruction on `T-008` only.

## Clarification requests

No change in this build. Prior behavior retained:

- Open request visible on task detail.
- Resolved requests not shown as open.
- Does not change task status.

## Security boundary

**Allowed:** intake work-files (`intake_work_file`), task-attached production metadata.

**Blocked:** quote PDF, quote archive, commercial offer sources, order snapshot cost/price/margin payloads, documents without order/intake linkage.

**Download:** `GET /api/v1/employee-mobile/orders/{order_id}/work-files/{file_id}/download` — employee must own an assigned/active task on that order.

## Existing plans vs new plans

| Scope | Behavior |
|-------|----------|
| New plans | Documents attached at generation |
| Existing plans | No global auto-backfill |
| Dev Sandu | Fixture script can backfill documents + one smoke instruction on order `1` |

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_tasks.py tests/test_task_clarification_requests.py tests/test_dev_employee_mobile_sandu_fixture.py tests/test_production_document_handoff.py tests/test_execution_task_instructions.py -q
```

## Smoke (Sandu)

```powershell
$env:WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/tasks
```

After `--apply` fixture: 6 tasks, SVG document present, `T-008` has manual instruction, others without instructions unchanged.

Browser: `http://127.0.0.1:3000/employee-app/tasks`

## Deferred

- Rich markdown/WYSIWYG instruction editor
- Per-task selective document classification
- In-app PDF/SVG viewer
- Photo upload from mobile
- Push notifications for clarifications/instructions
