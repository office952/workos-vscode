# BUILD: Employee Mobile Task Documents & Instructions Foundation

## 1. Purpose

Give shop-floor operators a **read-only execution context** inside Employee Mobile task detail:

```text
Task detail
├─ acțiuni Start / Blochez / Finalizez (unchanged)
├─ informații task (metadata)
├─ Instrucțiuni
└─ Documente și schițe
```

No viewer, upload, or new task model — foundation only.

**Base commit:** `de6f961` — `style(employee): simplify mobile home secondary navigation`

## 2. Document audit (pre-build)

| Area | Finding |
|------|---------|
| `execution_plan.tasks_json` schema (ExecutionPlanService) | Emits task fields only — **no `documents` field** at generation time |
| Dev DB order `1` (Sandu tasks) | Tasks have no `instructions`, `description`, or `documents` keys |
| `employee_mobile_tasks_service` | Previously **hardcoded** `"documents": []` — ignored plan JSON |
| `GET /api/v1/employee-mobile/tasks` | Response model already had `documents: List[dict]` but always empty |
| Frontend `EmployeeMobileTasksPanel` | Partial UI existed (inline instrucțiuni + documents when non-empty) — **no empty states**, no dedicated sections |
| `quote_documents_archive` | Real quote PDFs exist (e.g. E2E order) but download requires `quote.export_pdf` — **not employee_mobile** |
| Intake work-files | `GET /intake-requests/by-code/{code}/work-files/{id}/download` exists — **not wired** to mobile tasks |
| Generic `documents` entity | **Does not exist** (see `frontend/docs/atoms/DOCUMENT_CENTER_BACKEND_READINESS.md`) |
| `execution_reality.tasks_json` | Runtime facts only — no document attachments |

**Gap:** Real document handoff order/intake → execution plan task is **not implemented** upstream. Mobile can only display what is already stored on plan task JSON.

## 3. Source of instructions / documents (implemented)

| Field | Source |
|-------|--------|
| `instructions` | `execution_plan.tasks_json[].instructions` |
| `description` | `tasks_json[].description` or `.notes` (fallback for description) |
| `documents[]` | `tasks_json[].documents` — pass-through, normalized read-only |

Normalization (backend `_normalize_task_documents`):

- `id`, `name` (or `label` / `filename`), `type`, `source`
- `url` only when a real non-empty string (`url` / `href` / `download_url`)
- No invented URLs

## 4. Implemented

### Backend (minimal)

- `backend/services/employee_mobile_tasks_service.py`
  - Read `documents` from plan task JSON
  - Normalize metadata; omit `url` key when absent
  - Clearer `instructions` / `description` from plan fields

### Frontend (task detail only)

- `EmployeeMobileTasksPanel.tsx` — dedicated sections:
  - **Instrucțiuni** — content or empty state
  - **Documente și schițe** — list or empty state; **Deschide** only with real URL; **Fără link** for metadata-only
- `frontend/src/lib/employeeMobileTaskDocuments.ts` — helpers
- `frontend/src/api/employeeMobileTasks.ts` — typed document shape

**Not changed:** Home, bottom nav, Personal, Info & acces, task actions, access boundary.

## 5. Not implemented (by design)

- PDF/SVG/image viewer
- Upload (field photos, attachments)
- Order-level document merge (quote PDF, intake work-files) without dedicated employee_mobile endpoint
- Document versioning / permissions matrix
- Schema migration or ExecutionPlanService document emission
- Auto-generation / document handoff pipeline

## 6. Dev fixture (Sandu)

**Option A applied** — no `dev.db` changes.

Sandu tasks on order `1` have no `instructions` or `documents` in plan JSON → mobile shows **clear empty states**. This documents the upstream handoff gap honestly.

## 7. Access boundary

Unchanged:

- `employee_mobile` lists only own/assigned tasks
- Documents returned only inside those task payloads
- No cross-employee document exposure
- No new permissions added

## 8. Tests

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/pages/EmployeeMobileApp.test.tsx
```

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_tasks.py -q
```

## 9. Smoke — Sandu (`WORKOS_DEV_AUTH_USER_ID=dev-sandu-employee-001`)

| Check | Expected |
|-------|----------|
| `/auth/me` | Putaru Sandu / `employee_mobile` |
| `/employee-mobile/tasks` | 6 tasks |
| `/employee-app/tasks` → Montaj LED detail | Instrucțiuni + Documente sections visible |
| Empty states | No fake links; Start/Block/Complete unchanged |
| Home | Unchanged layout |

## 10. Deferred

- Real document handoff order → task (ExecutionPlanService / intake bridge)
- PDF/SVG viewer in mobile
- Field photo upload
- Document versioning
- Granular document permissions
- Push notifications / offline PWA sync

## 11. Proposed commit message (after owner confirm)

```text
feat(employee): show task documents and instructions on mobile
```
