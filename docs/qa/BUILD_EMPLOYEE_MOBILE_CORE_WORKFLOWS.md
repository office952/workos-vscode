# BUILD: Employee Mobile Functional Core Review

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `6e14d9c` — `style(employee): polish admin review flow in Employee Mobile` |
| **HEAD after** | _(post-commit — pending owner confirm)_ |
| **Status** | PASS (targeted tests + manual smoke) |

## 1. Preflight

- Branch: `local/integration-pr4-plus-svg-path`
- HEAD before: `6e14d9c`
- Working tree: clean before start

## 2. Audit summary (read-only)

### Angajat normal (`dev-employee-test-001`)

| Check | Result |
|-------|--------|
| `/auth/me` | `test.employee@local`, role `employee_mobile` |
| Home | Calin Cimpean (employee name from linked record) |
| Bottom nav | Acasă / Cereri / Pontaj only |
| Review | Hidden (nav + dashboard) |
| Echipa mea | Hidden |
| Cereri | Self-only list + create form |
| Pontaj | Read-only month view |

### Admin (`dev-admin-user-00000000`)

| Check | Result |
|-------|--------|
| `/auth/me` | Dev Admin, role `admin` |
| Review + Echipa mea | Visible |
| `/employee-app/review` | Accessible; review APIs 200 |

### Cereri flow

- **Types:** leave, day_off, time_off, advance, attendance_correction, equipment, issue_report, other
- **Create:** POST `/api/v1/employee-mobile/requests` — no `employee_id` / status from client
- **Cancel:** PATCH `/{id}/cancel` for draft/submitted
- **Review:** GET `/api/v1/employee-requests/review`, PATCH approve/reject
- **Post-review:** Employee sees updated status + optional `review_note` / `reviewed_at` in list

### Pontaj

- **Endpoint:** GET `/api/v1/employee-mobile/attendance?start_date&end_date`
- **Mode:** Read-only; no mutations
- **Data:** event_type, event_status, date range, notes

### Issues found (pre-implementation)

1. Status label inconsistency (`Draft` / `Trimisă` vs review `În așteptare`)
2. Review success toast disappeared after approve (message inside detail panel cleared with selection)
3. Employee list did not surface review outcome after approve/reject
4. Attendance showed raw English `event_status` in UI

## 3. Implementation

### Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/employeeMobileUiHelpers.ts` | **NEW** — shared RO labels, date formatters, attendance labels |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileStates.tsx` | `EmployeeMobileSuccessState` |
| `EmployeeMobileRequestsPanel.tsx` | Pending banner, card polish, review outcome, unified labels |
| `EmployeeRequestReviewPanel.tsx` | Shared helpers; success message persists after action |
| `EmployeeMobileAttendancePanel.tsx` | RO month label, type summary, status labels, copy |
| `EmployeeMobileApp.test.tsx` | Status label assertion update |
| `docs/qa/BUILD_EMPLOYEE_MOBILE_CORE_WORKFLOWS.md` | This doc |

### Not touched

- Backend, DB, migrations, seed, auth, roles, endpoints
- `employeeMobileAccess.ts` guards
- Manager team workspace logic

## 4. Access boundary

- `employee_mobile`: no Review, no Echipa mea (unchanged helpers)
- `admin` / `manager`: Review + Echipa mea visible
- Direct `/employee-app/review` still backend-guarded for non-reviewers

## 5. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/pages/EmployeeMobileApp.test.tsx
```

Result: **39/39 PASS**

## 6. Manual smoke

### Smoke 1 — employee (`WORKOS_DEV_AUTH_USER_ID=dev-employee-test-001`)

- `/auth/me` → employee_mobile
- `/employee-app` → no Review / Echipa mea; Cereri + Pontaj coherent
- No console errors observed

### Smoke 2 — admin (`WORKOS_DEV_AUTH_USER_ID=dev-admin-user-00000000`)

- `/auth/me` → admin
- `/employee-app/review` → inbox, filters, approve/reject UI clear
- Success message visible after approve/reject action

## 7. Boundary

- No organizational model changes
- No new dependencies
- No payroll / costing

## 8. Suggested commit message

```
feat(employee): consolidate Employee Mobile core workflows
```
