# BUILD — Employee Request Review Hardening

## Purpose

Strengthen self requests and manager review UI/UX: clearer auth errors, status filters, grouping, manual refresh, list limit, and improved empty states — **without changing business model or backend contracts**.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base: `f13b543` — `feat(employee): add request manager review UI`
- **Backend unchanged** in this build.

## Files changed

| Path | Change |
|------|--------|
| `frontend/src/api/employeeRequestErrors.ts` | Shared API error normalization |
| `frontend/src/api/employeeMobileRequests.ts` | Use error helper (self context) |
| `frontend/src/api/employeeRequestReview.ts` | Use error helper (review context) |
| `frontend/src/lib/employeeRequestListUi.ts` | Filters, grouping, limit, empty messages |
| `frontend/src/components/workos/employee-mobile/EmployeeRequestStatusFilters.tsx` | Filter toolbar + refresh |
| `frontend/src/components/workos/employee-mobile/EmployeeRequestReviewPanel.tsx` | Review hardening |
| `frontend/src/pages/EmployeeMobileApp.tsx` | Self requests hardening |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | Extended tests |
| `docs/qa/BUILD_EMPLOYEE_REQUEST_REVIEW_HARDENING.md` | This doc |

## Backend

**Unchanged.** All improvements are client-side filtering/display on existing list endpoints.

## UX improvements

### Error normalization

User-facing messages for HTTP 401/403/409/422 with context-specific 403 handling:

| Context | Code | Message |
|---------|------|---------|
| self | `employee_link_missing` | Contul tău nu este legat încă de un angajat. |
| self | `employee_self_role_required` | Rolul tău nu permite accesul la aplicația personală. |
| review | `employee_request_reviewer_required` | Ai nevoie de rol manager sau admin pentru review cereri. |
| review | `self_review_forbidden` | Nu poți aproba sau respinge propria cerere. |
| any | 409 | Cererea a fost deja procesată sau nu mai poate fi modificată. |

Technical error codes logged to console in dev only.

### Self requests (`/employee-app/requests`)

- Status filters: Toate, Trimise, Aprobate, Respinse, Anulate (+ counts)
- Default filter: **Toate**
- Grouping by status when filter = Toate
- Manual **Refresh**
- Contextual empty states
- List limit: first **25** items with notice

### Manager review (`/employee-app/review`)

- Same filter set; default filter: **Trimise** (inbox focus)
- Grouping when Toate
- Manual **Refresh**
- Empty: `Nu există cereri trimise pentru review.` (default filter)
- Approve/reject buttons disabled while pending
- 409/403 action errors surfaced in detail panel

## Payload safety (unchanged)

- No `employee_id` in create/cancel/approve/reject bodies
- Approve/reject: `{ review_note }` only
- No attendance/payment/side-effect flags

## Tests

### Backend regression

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_requests.py tests/test_employee_request_review.py -v
```

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeeMobileApp.test.tsx
```

## Smoke

- `http://127.0.0.1:3000/employee-app/requests` — filters + refresh visible
- `http://127.0.0.1:3000/employee-app/review` — default Trimise filter + refresh

## Limitations

- Client-side filter/group only (no backend pagination)
- No notifications
- No attendance/payment side effects on approve/reject
- No team-lead scoped review
- List capped at 25 items in UI

## Boundaries (confirmed)

- No backend / DB / migrations
- No attendance / payment / payroll fiscal integration
- No CostEngine / Quote / Pricing / Margins
- No permission rule changes
- No self-approval bypass
- No sensitive data exposure

## Next build

- `Employee Request Review Pagination Backend` — server-side paging when lists grow
- Or `Employee Request Approved Leave Attendance Decision Doc` — only with owner approval
