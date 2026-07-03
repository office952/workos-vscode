# BUILD — Employee Request Manager UI (review inbox)

## Purpose

Minimal manager/admin UI at `/employee-app/review` to list, inspect, approve, and reject employee requests via existing review API — status-only, no side effects.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base: `ea6ee09` — `feat(employee): add request manager review`
- **Backend unchanged** in this build.

## Files changed

| Path | Change |
|------|--------|
| `frontend/src/api/employeeRequestReview.ts` | Review API client |
| `frontend/src/components/workos/employee-mobile/EmployeeRequestReviewPanel.tsx` | Review inbox UI |
| `frontend/src/pages/EmployeeMobileApp.tsx` | `/review` route, tabs, home card |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | Review UI tests |
| `docs/qa/BUILD_EMPLOYEE_REQUEST_MANAGER_UI.md` | This doc |

## Endpoints used

| Method | Path |
|--------|------|
| GET | `/api/v1/employee-requests/review` |
| GET | `/api/v1/employee-requests/review/{id}` |
| PATCH | `/api/v1/employee-requests/review/{id}/approve` |
| PATCH | `/api/v1/employee-requests/review/{id}/reject` |

## Payload approve/reject

```json
{ "review_note": "optional" }
```

Never sends: `employee_id`, attendance/payment flags, side-effect params.

## Role behavior

- UI calls review API; backend returns **403** if user is not `admin`/`manager`
- Self requests remain on **Cererile mele** tab (`/employee-app/requests`)
- Review tab is for others' requests; self-approval blocked server-side

## UI states

| State | Message / behavior |
|-------|-------------------|
| Loading | Spinner inbox |
| Empty | `Nu există cereri pentru review.` |
| Error | Red banner (403 auth, etc.) — no fake live data |
| Detail | Safe fields only; approve/reject only for `submitted` |
| Success | Green message after approve/reject + list reload |

Tabs: **Cererile mele** | **Review manager**

Disclaimer: *Aprobarea schimbă doar statusul cererii. Nu modifică pontajul sau plățile.*

## Tests

### Backend regression (unchanged)

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

`GET http://127.0.0.1:3000/employee-app/review` → shell + review panel; 403 without manager/admin role.

## Boundaries (confirmed)

- No backend / DB / migrations changes
- No attendance integration
- No payment integration
- No payroll fiscal exposure
- No CostEngine / Quote / Pricing / Margins
- No team lead scope
- No self-approval bypass (server enforced)
- No notifications

## Deferred

- Dedicated manager desktop view
- Notifications on approve/reject
- Attendance/payment hooks after approval (separate build)

## Recommended commit message

```
feat(employee): add request manager review UI
```

## Status

READY for manual `git commit-tree` after review.
