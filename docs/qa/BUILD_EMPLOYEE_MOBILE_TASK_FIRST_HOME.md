# BUILD: Employee Mobile Task-First Operational Home

## 1. Purpose

Refocus `/employee-app` home from HR-first cards to a **productivity-first operational workspace**:

```text
Acasă Employee Mobile
├─ Lucrez acum (hero)
├─ Taskurile mele azi
├─ Comenzi / lucrări în curs
├─ Montaje programate (empty/deferred when no real signal)
├─ Urmează
├─ Blocaje
└─ Secundar: Administrativ (Cereri / Pontaj / Profil / Review / Echipa)
```

Boundary: UI/UX + consolidation of **existing** API data only. No new backend endpoints, no mock-as-real, no auto-assign, no push/offline/planning engine.

## 2. Owner decision

Employee Mobile is **not** an HR portal on phone. Dominant surface = production execution (tasks, orders, blockers, start/block/complete). HR (cereri, pontaj, profil, PWA install) stays accessible but secondary.

## 3. Real data sources

| Section | Source |
|---------|--------|
| Hero, Azi, Urmează, Blocaje | `GET /api/v1/employee-mobile/tasks` |
| Comenzi în curs | Same payload — group by `order_id` |
| Montaje programate | Same payload — conservative keyword match on `process_type` / `machine_type` / `title` / `description` |
| Cereri / Pontaj | Existing self-only endpoints (unchanged) |
| Actions | Same PATCH routes as Task Workspace (`start` / `block` / `complete` / `unblock`) |

Not used for mobile home: shop-floor mock fallback, operator mock, invented client names.

## 4. Hero task selection

Priority in `frontend/src/lib/employeeMobileTaskSummary.ts`:

1. First `in_progress` → **Lucrez acum**
2. Else first `blocked` → **Blocaj activ**
3. Else first `assigned` → **Următorul de început**
4. Else empty state

Actions on hero reuse `EmployeeMobileTaskActionBar` (same API as Task Detail panel).

## 5. Comenzi în curs

- Group tasks by `order_id` where employee has **active** tasks (`assigned`, `in_progress`, `blocked`).
- Label: `order_code` if present, else `Comandă #ID`, optional `· client` only when API provides `client`.
- Show active count + done count on same order when present.

## 6. Montaje programate

Conservative detection only (`montaj`, `installation`, `field_install`, `teren`, etc.). If no match → empty copy:

> Nu ai montaje programate vizibile momentan.

No dedicated installation schedule model in backend yet.

## 7. Urmează

- `assigned` tasks excluding the hero assigned task.
- Copy: „Pregătit pentru începere” — no rigid planning promises.

## 8. Secondary (Administrativ)

Moved below operational sections:

- Cereri, Pontaj, Taskuri (link), Profil, Account panel
- Review + Echipa mea only for admin/manager (access boundary unchanged)

## 9. Not implemented (deferred)

- Auto-generation on production entry
- Document handoff to tasks
- Scheduled installations real model / calendar
- Auto-assign / eligible pool
- Push notifications / offline sync
- Document viewer complex
- Planning / priority engine

## 10. Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/employeeMobileTaskSummary.ts` | Hero/order/installation/upcoming helpers |
| `frontend/src/lib/employeeMobileTaskSummary.test.ts` | Unit tests |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileTaskActionBar.tsx` | Shared task actions |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileHomeDashboard.tsx` | Task-first home layout |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | Home structure + hero test |
| `docs/qa/BUILD_EMPLOYEE_MOBILE_TASK_FIRST_HOME.md` | This doc |

## 11. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/employeeMobileAccess.test.ts `
  src/lib/employeeMobileTaskSummary.test.ts `
  src/pages/EmployeeMobileApp.test.tsx
```

Access boundary preserved:

- `employee_mobile`: no Review / Echipa mea nav or dashboard cards
- Deep-link guard to `/review` and `/team` unchanged
- Admin/manager: Review + Echipa in Administrativ section

## 12. Smoke

### Employee (`WORKOS_DEV_AUTH_USER_ID=dev-employee-test-001`)

- `/api/v1/auth/me` → Test Employee / `employee_mobile`
- `/api/v1/employee-mobile/tasks` → T-001 assigned if dev DB fixture persists
- Browser `/employee-app`: hero shows T-001 as „Următorul de început”, Comandă #1 in orders, HR secondary

### Admin (`WORKOS_DEV_AUTH_USER_ID=dev-admin-user-00000000`)

- Home task-first layout intact
- Review + Echipa accessible in Administrativ
- Empty operational hero if admin has no assigned tasks

## 13. Coherence

- Home and Task Detail use same API + PATCH actions
- No mobile-only task state
- Desktop/admin/production remain source of truth via `execution_plan` / `execution_reality`

## 14. Navigation polish (owner feedback)

Home refactored to **command panel** — no long empty sections:

- Compact hero + CTA (`Deschide taskul` / `Vezi taskurile`)
- Nav cards: Azi, Comenzi, Montaje, Urmează, Blocaje → `/employee-app/tasks?view=…`
- Administrativ: 2-col shortcut grid (Cereri, Pontaj, Profil; Review/Echipa admin/manager only)

Tasks panel is the detailed workspace:

- Query views: `all`, `assigned`, `in_progress`, `blocked`, `done`, `orders`, `installations`, `upcoming`
- Orders view: list → drill-down by `orderId`
- Tabs + summary + task detail with `EmployeeMobileTaskActionBar`

## 15. Status

- Backend: unchanged
- Commit: **pending owner confirmation** — proposed message: `feat(employee): refocus mobile home on operational tasks`
