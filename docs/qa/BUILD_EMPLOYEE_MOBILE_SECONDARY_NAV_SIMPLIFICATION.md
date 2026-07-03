# BUILD: Employee Mobile Secondary Nav Simplification

## 1. Purpose

Polish Employee Mobile home hierarchy so the operator surface stays **operational-first** above the fold. Secondary HR/account/PWA content moves off Home into dedicated hubs — no new backend, no task logic changes.

## 2. Owner motivation

- Home was still too tall on secondary zones: large “WorkOS Employee” header, three big Administrativ cards (Cereri / Pontaj / Profil), and full **Cont și profil** + **Instalează pe telefon** blocks.
- Employee Mobile must read as a **shop-floor command panel**, not an HR portal on phone.
- Sandu preview validated the task-first hero; this build removes visual competition from administrativ/account/PWA on Home.

## 3. Changes

| Area | Before | After |
|------|--------|-------|
| Header | Tall card: WorkOS Employee, spațiu angajat, same-account hint, role repeat | Compact: **name** + `Panou operațional · {zi, dată}` + small avatar |
| Home secondary | 3 large Administrativ cards + AccountPanel + PWA install | Two compact cards: **Personal** · **Info & acces** |
| Personal | Cereri/Pontaj/Profil scattered on Home | Hub `/employee-app/personal` — Cereri, Pontaj, Profil (+ manager Review/Echipa) |
| Info & acces | On Home | Page `/employee-app/info` — cont, acces angajat, profil legat, PWA install |
| Bottom nav | Acasă · Cereri · Pontaj (+ Review admin) | **Acasă · Taskuri · Personal** (+ Review admin/manager only) |

Home layout (Sandu):

```text
Header compact
Hero task (Următorul task / …)
Carduri operaționale (Azi, Comenzi, Montaje, Urmează, Blocaje)
Personal          (compact)
Info & acces      (compact)
```

## 4. Scope

| In scope | Out of scope |
|----------|--------------|
| Frontend UI/layout/navigation only | Backend / API |
| Routes `personal`, `info` | Fixture Sandu in `dev.db` |
| Vitest updates for nav/routing | Task assignment logic |
| `EmployeeMobileSecondaryNavCard`, `PersonalHub`, `InfoAccessPage` | Auto-assign, eligible pool |
| Header + bottom nav simplification | Push, offline, document handoff |

**Base commit:** `e533181` — `feat(employee): refocus mobile home on operational navigation`

## 5. Access boundary (unchanged semantics)

| Role | Home | Bottom nav | Personal hub | Hidden |
|------|------|------------|--------------|--------|
| `employee_mobile` | Operational + Personal + Info cards | Acasă, Taskuri, Personal | Cereri, Pontaj, Profil | Review, Echipa mea |
| `manager` / `admin` | Same + Review in nav | + Review tab | + Management: Review, Echipa | — |

Deep links to `/review` and `/team` remain blocked for `employee_mobile` via `EmployeeMobileProtectedRoute`.

## 6. Files touched

| File | Role |
|------|------|
| `frontend/src/components/workos/employee-mobile/EmployeeMobileShell.tsx` | Compact header; bottom nav |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileHomeDashboard.tsx` | Home without administrativ/account blocks |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileSecondaryNavCard.tsx` | Compact secondary card |
| `frontend/src/components/workos/employee-mobile/EmployeeMobilePersonalHub.tsx` | `/personal` hub |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileInfoAccessPage.tsx` | `/info` page |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileAdminShortcuts.tsx` | Review/Echipa only (Personal hub) |
| `frontend/src/lib/employeeMobileUiHelpers.ts` | `formatOperationalPanelSubtitle()` |
| `frontend/src/pages/EmployeeMobileApp.tsx` | Routes |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | Nav/home/hub tests |

## 7. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/pages/EmployeeMobileApp.test.tsx
```

**Result:** `71/71 PASS` (2026-06-14)

## 8. Smoke — Sandu (`WORKOS_DEV_AUTH_USER_ID=dev-sandu-employee-001`)

| URL | PASS criteria |
|-----|---------------|
| `http://127.0.0.1:3000/employee-app` | Compact header; hero Lipire; counts 6/1/2/5/0; Personal + Info cards; no Cont/PWA on Home; no Review |
| `http://127.0.0.1:3000/employee-app/tasks` | 6 Sandu tasks; tabs/views OK |
| `http://127.0.0.1:3000/employee-app/personal` | Cereri, Pontaj, Profil accessible |
| `http://127.0.0.1:3000/employee-app/info` | Cont, acces, profil legat, PWA info |

## 9. Deferred

- Document handoff to tasks
- Auto-generation on production entry
- Push notifications
- Offline / PWA push sync
- Scheduled installation real model / calendar

## 10. Proposed commit message

```text
style(employee): simplify mobile home secondary navigation
```
