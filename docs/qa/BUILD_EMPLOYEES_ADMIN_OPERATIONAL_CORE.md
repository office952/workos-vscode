# BUILD: Employees Admin Operational Core

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `d084a55` — `feat(employee): guard mobile deep links and improve PWA readiness` |
| **HEAD after** | _(pending owner confirm)_ |
| **Status** | PASS (targeted tests + manual smoke) |

## 1. Scop build

Consolidare zona `/employees` pentru administrare operațională:

- listă clară + filtre;
- fișă angajat cu acces Employee Mobile;
- context cereri/pontaj (read-only) din API existente;
- expunere minimală backend pentru `user_id` + flags derivate.

## 2. Audit

### Employees Admin List (înainte)

| Aspect | Stare |
|--------|--------|
| API | `GET /api/v1/entities/employees` |
| Câmpuri API | operaționale + CostEngine; `user_id` în backend dar **lipsă din frontend DTO** |
| UI | listă + detaliu + edit/create/delete; filtre status/tip; KPI |
| Mobile access | **Nu vizibil** |

### User ↔ employee identity

| Layer | Stare |
|-------|--------|
| Model | `employees.user_id` există |
| API backend | `user_id` serializat, dar fără email/rol user |
| Employee Mobile | `resolve_employee_for_user()` pe `user_id` + status activ |

### Cereri / pontaj per employee

| Sursă | Disponibil |
|-------|------------|
| Cereri | `GET /api/v1/employee-requests/review` — filtrare client `employee_id` |
| Pontaj | `GET /api/v1/employee-attendance/events?employee_id=` — filtrare server |

### Gaps clasificate

| Gap | Clasificare | Acțiune |
|-----|-------------|---------|
| Mobile badge în listă | Backend minimal + frontend | Implementat |
| auth_email / auth_role | Backend minimal | Implementat (join User) |
| Filtre mobile | Frontend | Implementat |
| Context cereri/pontaj | Frontend (API existente) | Implementat |
| User linking UI | Deferred | Fără endpoint dedicat |
| Manager assignment | Out of scope | — |

## 3. Implementare

### Fișiere modificate

| Fișier | Schimbare |
|--------|-----------|
| `backend/routers/employees.py` | `auth_email`, `auth_role`, `is_linked_to_user`, `has_mobile_access` |
| `backend/tests/test_employees_mobile_access_fields.py` | **NOU** |
| `frontend/src/api/costEngine.ts` | EmployeeDTO extins |
| `frontend/src/lib/employeeAdminAccess.ts` | **NOU** — helpers |
| `frontend/src/lib/employeeAdminAccess.test.ts` | **NOU** |
| `frontend/src/components/workos/employees/EmployeeMobileAccessBadge.tsx` | **NOU** |
| `frontend/src/components/workos/employees/EmployeeAdminOperationalSummary.tsx` | **NOU** |
| `frontend/src/pages/Employees.tsx` | Listă, filtre, detaliu, mobile access |
| `frontend/src/pages/Employees.operationalAdmin.test.tsx` | **NOU** |
| `docs/qa/BUILD_EMPLOYEES_ADMIN_OPERATIONAL_CORE.md` | Acest document |

### Backend minimal

- Fără migrații, seed-uri, roluri noi.
- Join opțional `users` la list/get/create/update.
- `has_mobile_access` = linked + `status=active` + rol în `{employee_mobile, manager, admin}`.

### Neatinse

Axinte Remus, Calin Cimpean, seed-uri, auth impersonation, Employee Mobile boundaries, ierarhii, direct reports, manager assignment, payroll, creare conturi.

## 4. Reguli păstrate

- Owner/admin administrează centralizat.
- `employee_mobile` — doar zona self; deep-link guard neschimbat.
- Fără logică organizațională complexă.

## 5. Cazuri verificate

| Caz | Verificare |
|-----|------------|
| Dev Admin | `/employees` listă + detaliu + filtre |
| Test Employee (id 1) | Mobile activ în API + badge |
| Axinte Remus | Neatins (seed) |

## 6. Deferred

- UI linking user ↔ employee;
- management conturi;
- dashboard HR complet;
- endpoint dedicat cereri per employee (filtrare client suficientă acum).

## 7. Teste

```powershell
# frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/employeeMobileAccess.test.ts `
  src/pages/EmployeeMobileApp.test.tsx `
  src/pages/Employees.internalPayBase.test.tsx `
  src/lib/employeeAdminAccess.test.ts `
  src/pages/Employees.operationalAdmin.test.tsx

# backend
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employees_mobile_access_fields.py tests/test_employee_internal_pay_base.py -q
```

## 8. Smoke

- Admin: `/employees` + `/employee-app` (Review/Echipa mea)
- Employee: `/employee-app` + deep links blocked
