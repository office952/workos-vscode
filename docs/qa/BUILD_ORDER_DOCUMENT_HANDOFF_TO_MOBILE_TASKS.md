# BUILD: Order / Production Document Handoff to Mobile Tasks

## 1. Purpose

Expose **real production documents** from WorkOS (intake work-files linked to the employee’s assigned order) on Employee Mobile task detail — without commercial quote PDFs, without a new mobile-only document model, and without viewer/upload scope.

**Base commit:** `ef5300b` — `feat(employee): show task documents and instructions on mobile`

## 2. Document source audit

| Source | Finding | Decision |
|--------|---------|----------|
| **Intake work-files** | Stored in `intake_requests.product_spec_json.workFileAttachments`; files on disk under `backend/storage/intake_work_files/{intake_code}/`; operator download via `GET /api/v1/entities/intake_requests/by-code/{code}/work-files/{id}/download` requires **`intake.update`** | **Accepted** via new employee-scoped download endpoint |
| **Order 1 (Sandu fixture)** | `intake_code = WI-E2E-COMMERCIAL-001`; quote chain order → quote → intake | **Used** — dev fixture added one SVG work-file for smoke |
| **Quote documents archive** | Real PDFs exist; download requires `quote.export_pdf`; content is client-facing commercial (prices, VAT, discounts) | **Excluded** — blocked by source/type/URL filters |
| **Order snapshot JSON** | Contains costing/pricing fields | **Not exposed** — never serialized to mobile tasks |
| **execution_plan.tasks_json** | No documents at generation; task-level passthrough from foundation build retained | **Merged** with order-level intake docs |
| **execution_reality.tasks_json** | Runtime facts only | **Not a document source** |
| **Document Center** | No generic backend entity | **Out of scope** |
| **Frontend SVG upload** | Same intake work-file pipeline when saved on intake | **Same backend path** when linked to order intake |

## 3. Accepted sources

1. **Intake production work-files** for the order’s linked `intake_code` (normalized metadata + employee download URL).
2. **Task-level `documents[]`** already present in `execution_plan.tasks_json` (passthrough, normalized).

## 4. Excluded sources (and why)

| Source | Reason |
|--------|--------|
| Quote PDF / `quote_documents_archive` | Commercial/sensitive — prices, client offer |
| Order snapshot pricing/cost JSON | Not production handoff; financial data |
| Global intake/quote download endpoints | Bypass employee task ownership; wrong permission model |
| Mobile-only document records | Violates architecture rule |

Blocked defensively in `employee_mobile_production_documents_service.py` via `BLOCKED_DOCUMENT_SOURCES`, `BLOCKED_DOCUMENT_TYPES`, and URL fragment checks.

## 5. Permissions / access boundary

| Action | Rule |
|--------|------|
| List documents on task | Existing `list_my_tasks` — employee sees only own assigned tasks; order work-files merged per task’s `order_id` |
| Download work-file | `GET /api/v1/employee-mobile/orders/{order_id}/work-files/{file_id}/download` — requires `employee_mobile` + **assigned task on that order** (`employee_has_assigned_order_task`) |
| Operator intake download | Unchanged — still `intake.update`; employees do not get that route |
| Quote PDF | Not included in merge; blocked if ever present in task JSON |

## 6. Implemented

### Backend

- **`backend/services/employee_mobile_production_documents_service.py`** (new)
  - `load_intake_work_files_for_order()` — reads `workFileAttachments` from intake linked to order
  - `merge_production_documents()` — task + order docs, dedupe by `id`, block commercial sources
  - `normalize_intake_work_file_document()` — metadata + mobile download path
  - `employee_has_assigned_order_task()` — ownership check for download
  - `download_order_work_file_for_employee()` — delegates to `WorkIntakeWorkFileService.download`

- **`backend/services/employee_mobile_tasks_service.py`**
  - Preloads intake work-files per order; merges into each task’s `documents[]`

- **`backend/routers/employee_mobile_tasks.py`**
  - `GET /api/v1/employee-mobile/orders/{order_id}/work-files/{file_id}/download`

### Frontend (task detail only)

- **`employeeMobileTaskDocuments.ts`** — `documentSourceLabel()`, `downloadable` handling
- **`EmployeeMobileTasksPanel.tsx`** — source label “Fișier comandă”; “Deschide” when URL present; “Disponibil în sistem, fără link mobil momentan” when not

**Not changed:** Home layout, bottom nav, Personal, Info & acces, task actions.

### Dev fixture (local DB only — not in git)

Added to intake `WI-E2E-COMMERCIAL-001`:

- File id: `sandu-sketch-001`
- Name: `Schiță litere volumetrice.svg`
- Storage: `backend/storage/intake_work_files/WI-E2E-COMMERCIAL-001/sandu-sketch-001_Schiță_litere_volumetrice.svg`
- `product_spec_json.workFileAttachments[0].source = dev_fixture_production_handoff`

Sandu profile unchanged: `employee_id = 4`, 6 tasks on order `1`, T-001 remains Calin.

## 7. Not implemented (by design)

- PDF/SVG/image viewer
- Upload from mobile
- Image gallery
- Document versioning
- Document Center
- Granular production document permissions matrix
- Quote commercial PDF handoff (even filtered)
- Schema migration
- ExecutionPlanService auto-emission of documents at plan generation

## 8. Smoke — Sandu (`dev-sandu-employee-001`)

**Backend env:** `$env:WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'`

| Check | Result |
|-------|--------|
| `GET /api/v1/auth/me` | Sandu, `employee_mobile` |
| `GET /api/v1/employee-mobile/tasks` | 6 tasks; each includes `documents[]` with intake work-file |
| Document shape | `source: intake_work_file`, `downloadable: true`, URL `/api/v1/employee-mobile/orders/1/work-files/sandu-sketch-001/download` |
| T-001 (Calin) | Not in Sandu list |
| Browser `/employee-app/tasks` | 6 tasks; “Documente disponibile” on cards |
| Task detail Montaj LED | “Schiță litere volumetrice.svg · Fișier comandă · Deschide” |
| Home | Unchanged (not modified in this build) |

Download endpoint verified in pytest (`test_employee_mobile_tasks.py`); live curl requires dev-auth session same as other mobile routes.

## 9. Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_tasks.py -q
```

**Result:** 11 passed

Coverage added:

- Task-level documents passthrough retained
- Order intake work-files merged on list
- Quote/commercial document sources excluded from merge
- Download 403 when employee has no assigned task on order

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/pages/EmployeeMobileApp.test.tsx
```

**Result:** 74 passed

Added: task detail renders intake work-file with “Deschide” when URL present.

## 10. Deferred

- In-app PDF/SVG preview viewer
- Field photo upload / attachments
- Document versioning and audit trail
- Document Center product surface
- Per-document-type permission matrix for production
- Filtered “technical excerpt” from quote PDF (separate security decision)
- Upstream ExecutionPlanService document emission at plan generation

## Boundary

This build wires **intake production work-files** to assigned mobile tasks only. Commercial quote artifacts and order financial snapshots remain operator/admin scope.
