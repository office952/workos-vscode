# BUILD: Employee Mobile Experience Completion

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `1d69e87` — `feat(employee): define identity session and pwa foundation` |
| **HEAD after** | _(post-commit)_ |
| **Status** | PASS |

## 1. UX audit summary

| Topic | Before | After |
|-------|--------|-------|
| Home | Grid of all sections + blueprint noise | Dashboard cu 4 cards acționabile + rezumat API |
| Navigation | Link-uri în grid + tabs requests/review | Bottom nav persistent (Home, Cereri, Pontaj, Review) |
| Header | MOBILE SHELL badge + disclaimer | Titlu, subtitlu, same-account hint, user din AuthContext |
| States | Inline per panel | `EmployeeMobileStates` unificat |
| Structure | Monolith `EmployeeMobileApp.tsx` | Shell, dashboard, requests panel extrase |

Note: `EmployeeMobileRequests.tsx` / `EmployeeMobileAttendance.tsx` / `EmployeeMobileReview.tsx` nu există ca pagini separate — logică în `EmployeeMobileApp.tsx` + `components/workos/employee-mobile/*`.

## 2. Product/UX decision

`docs/architecture/EMPLOYEE_MOBILE_EXPERIENCE_DECISION.md`

## 3. Routes affected

- `/employee-app` — dashboard
- `/employee-app/requests`, `/attendance`, `/review` — polish + nav
- Blueprint routes (`/today`, `/tasks`, etc.) — placeholder simplu
- PWA `start_url` unchanged: `/employee-app`
- Desktop `/attendance/effects` — neatinse

## 4. Components/pages changed

| File | Change |
|------|--------|
| `EmployeeMobileApp.tsx` | Shell layout, routing, export sections |
| `EmployeeMobileShell.tsx` | Header, bottom nav, install card |
| `EmployeeMobileHomeDashboard.tsx` | Dashboard + API summaries |
| `EmployeeMobileStates.tsx` | Loading/empty/error/section card/badge |
| `EmployeeMobileRequestsPanel.tsx` | Extracted + polish |
| `EmployeeMobileAttendancePanel.tsx` | Unified states + read-only badge |
| `EmployeeRequestReviewPanel.tsx` | Unified states + copy |
| `EmployeeMobileApp.test.tsx` | Dashboard, nav, badge tests |

## 5. API calls used

- `listEmployeeRequests()` — home summary + requests panel
- `listMyAttendanceEvents({ start_date, end_date })` — home summary + attendance panel
- Review APIs unchanged

Dashboard: erori independente per secțiune.

## 6. Frontend states unified

- `EmployeeMobileLoadingState` — „Se încarcă datele tale…”
- `EmployeeMobileEmptyState`
- `EmployeeMobileErrorState` — mesaje din `employeeRequestErrors.ts`
- `EmployeeMobileSectionCard`, `EmployeeMobileStatusBadge`

## 7. Tests added/updated

- Mock `useAuth` pentru header user hint
- Dashboard cards + bottom nav assertions
- Read-only badge, Self-only badge, status labels RO
- 27 tests total în `EmployeeMobileApp.test.tsx`

## 8. Tests run + results

```text
backend employee suites → 116 passed
vitest EmployeeMobileApp.test.tsx → 27 passed
```

## 9. Manual smoke

Not run (stack local nepornit).

## 10. Limitations / deferred

- Blueprint sections fără date reale
- PNG maskable PWA icons
- `beforeinstallprompt` install button
- Manager team attendance, payroll, push, offline

## 11. Confirmations

- [x] No backend business logic change
- [x] No DB/migration
- [x] No payroll/payment/cost
- [x] No auth rewrite
- [x] No native app
- [x] PWA start_url `/employee-app`
- [x] Same credentials copy preserved
- [x] Employee self attendance read-only
- [x] No client employee_id input (sr-only test hook kept)
- [x] Attendance CRUD admin/operator only (unchanged)
- [x] No manager team attendance
- [x] Approval status-only (unchanged)
