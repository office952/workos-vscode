# BUILD — Employee Request UI (self-only)

## Purpose

Minimal **Cereri** UI in `/employee-app/requests` wired to self-only backend endpoints — list, create, cancel with loading/error/empty states. No attendance/payment integration.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base: `3eedce0` — `feat(employee): add self-only request foundation`
- Backend contract unchanged in this build.

## Files changed

| Path | Change |
|------|--------|
| `frontend/src/api/employeeMobileRequests.ts` | API client + payload builder |
| `frontend/src/pages/EmployeeMobileApp.tsx` | Cereri panel (list/create/cancel) |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | UI + payload safety tests |
| `docs/qa/BUILD_EMPLOYEE_REQUEST_UI_SELF_ONLY.md` | This doc |

## API pattern

Follows existing `frontend/src/api/employeeAttendance.ts` pattern:

- `fetch` + `getAPIBaseURL()` + `credentials: "include"`
- CSRF headers via global `installCsrfFetchHeaderSupport()` in `main.tsx`
- No axios, no new libraries, no react-query for this section

### Endpoints used

| Method | Path |
|--------|------|
| GET | `/api/v1/employee-mobile/requests` |
| POST | `/api/v1/employee-mobile/requests` |
| PATCH | `/api/v1/employee-mobile/requests/{id}/cancel` |

## Payload rules

**Sent by frontend (create):**

- `request_type`, `title`, optional `description`, `reason`, `start_date`, `end_date`
- `amount` + `currency` only for `advance` when amount > 0

**Never sent:**

- `employee_id`
- `status`
- `submitted_at`, `reviewed_at`, `reviewed_by_user_id`, `review_note`

Body built via `buildEmployeeRequestCreatePayload()` — no client identity authority.

## UI states

| State | Behavior |
|-------|----------|
| Loading | Spinner + “Se încarcă cererile…” |
| Empty | “Nu ai cereri trimise.” |
| Error | Red banner with API message (403 auth expected without employee_mobile) |
| Success | Green message after create; list reload |
| Cancel | Button only for `draft` / `submitted` |

Panel copy:

- Badge: **Self-only live**
- “Cererile sunt trimise doar pentru angajatul autentificat.”
- “Nu se trimite employee_id din client.”

## Tests

### Backend regression

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_requests.py -v
```

Expected: **20 passed**

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeeMobileApp.test.tsx
```

Covers: shell, Cereri section, list/empty/error, create payload safety, cancel endpoint, cancel visibility.

## Smoke

`/employee-app/requests`:

- Page loads with WorkOS Employee shell
- Cereri panel visible
- Without `employee_mobile` auth → error banner (not fake live data)
- Form has no `employee_id` field
- Submit may fail with auth in normal browser — acceptable

## Limitations

- Browser requires authenticated `employee_mobile` user + `employees.user_id` link for live data
- No manager approval UI
- No attendance/payment side effects
- Home shell disclaimer still mentions MOCK for other sections
- `employee_id` returned in API response (server-resolved) — display uses type/status/title only

## Boundaries (confirmed)

- No attendance integration
- No payment / advance ledger integration
- No payroll fiscal
- No CostEngine / Quote / Pricing / Margins changes
- No sensitive cost/salary fields in UI
- No manager approval
- No client `employee_id` authority
- No backend/DB changes

## Next build

**Employee Request Manager Review — approve/reject without side effects**

## Recommended commit message

```
feat(employee): add self-only request UI
```

## Status

READY for manual `git commit-tree` after review.
