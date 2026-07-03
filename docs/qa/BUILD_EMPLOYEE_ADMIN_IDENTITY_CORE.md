# BUILD: Employee Admin & Identity Core Polish

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `984e9cb` — `feat(employee): consolidate Employee Mobile core workflows` |
| **HEAD after** | _(pending owner confirm)_ |
| **Status** | PASS (targeted tests + manual smoke) |

## 1. Scop build

Clarificare UX pentru:

- lista admin angajați operaționali (`/employees`);
- profil/cont Employee Mobile (identitate user + acces);
- documentare boundary identitate user ↔ employee fără logică organizațională nouă.

## 2. Audit (read-only)

### Employees Admin List (`/employees` → `Employees.tsx`)

| Aspect | Stare înainte |
|--------|----------------|
| Implementare | `frontend/src/pages/Employees.tsx` — LIVE DB via `/api/v1/entities/employees` |
| Câmpuri listă | nume, tip, rol, departament, status, cost orar, CostEngine badge |
| Email/telefon | **Nu** în `EmployeeDTO` |
| User linked / Mobile access | **Nu** în payload API — deferred backend |
| Search/filter | search text + select status/tip |
| Empty/loading/error | existente, minimal |

`EmployeesRecords.tsx` = modul demo HR separat — **out of scope**.

### User ↔ employee identity

| Layer | Mecanism |
|-------|----------|
| Auth | `GET /api/v1/auth/me` → user id, email, name, role |
| Mobile self | `employees.user_id` → `resolve_employee_for_user()` (backend) |
| Fără link | 403 `employee_link_missing` |
| Inactiv | 403 `employee_not_active` |
| Frontend mobile | **Nu** trimite `employee_id`; probe self via endpoint-uri existente |

Cazuri seed (neatinse):

- `dev-employee-test-001` → user auth „Test Employee”, employee HR Calin Cimpean id 1
- `dev-admin-user-00000000` → Dev Admin
- Axinte Remus id 9 / `dev-owner-office-p-media-ro` — neatins

### Employee Mobile profile

Înainte: secțiune „Cont și instalare” minimală (user hint în header + PWA install).

### Gaps identificate

| Gap | Acțiune |
|-----|---------|
| Lista angajați aglomerată | Polish frontend listă |
| Fără indicator user/mobile în admin | **Deferred** — necesită `user_id` în API |
| Profil mobil incomplet | Panel cont cu rol + acces + probe link |
| Nume HR vs auth name | Afișat doar dacă vine din API existent (attendance `employee_name`) |

## 3. Implementare

### Fișiere modificate

| Fișier | Schimbare |
|--------|-----------|
| `frontend/src/pages/Employees.tsx` | Listă clară: status badge, iconițe rol/dept, filtre rapide, empty/loading |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileAccountPanel.tsx` | **NOU** — profil/cont mobil |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileHomeDashboard.tsx` | Folosește AccountPanel |
| `frontend/src/hooks/useEmployeeMobileSelfLink.ts` | **NOU** — probe link via API existente |
| `frontend/src/lib/employeeMobileAccess.ts` | Helpers rol/acces/probe |
| `frontend/src/lib/employeeMobileAccess.test.ts` | Teste helpers |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | Teste account panel + mock fetch |
| `docs/qa/BUILD_EMPLOYEE_ADMIN_IDENTITY_CORE.md` | Acest document |

### Employees Admin

- Badge status Activ/Inactiv cu iconițe
- Rol + departament cu iconițe
- Filtre rapide client-side: Toți / Activi / Inactivi
- Empty/loading states îmbunătățite
- `data-testid` pe listă/filtre

### Employee Mobile Profile

- Bloc autentificare: nume, email, rol RO
- Rezumat acces self vs manager/admin
- Probe link angajat (employee_mobile/manager) fără endpoint nou
- Notă admin pentru cont fără probe self
- PWA install păstrat

### Neatins

- Backend, DB, migrations, seed, auth, roluri
- Axinte Remus, Calin Cimpean records
- Direct reports, manager assignment, ierarhii, payroll

## 4. Reguli păstrate

- Owner/admin administrează centralizat
- `employee_mobile` → doar zona personală
- Review + Echipa mea ascunse UI pentru `employee_mobile`
- Backend guards = sursa de securitate; UI = preventiv

## 5. Deferred backend

- `user_id` / email / mobile access flag în `EmployeeDTO` pentru admin list
- Endpoint dedicat profil self (`/employee-mobile/me`) — opțional viitor

## 6. Teste

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/pages/EmployeeMobileApp.test.tsx src/pages/Employees.internalPayBase.test.tsx
```

## 7. Smoke manual

### employee_mobile (`WORKOS_DEV_AUTH_USER_ID=dev-employee-test-001`)

- `/auth/me` → test.employee@local, employee_mobile
- `/employee-app` → fără Review/Echipa mea, profil/cont OK

### admin (`WORKOS_DEV_AUTH_USER_ID=dev-admin-user-00000000`)

- `/auth/me` → Dev Admin, admin
- Review + Echipa mea vizibile, profil admin OK
- `/employees` → listă clară

## 8. Commit propus

```
feat(employee): clarify employee admin and mobile identity
```
