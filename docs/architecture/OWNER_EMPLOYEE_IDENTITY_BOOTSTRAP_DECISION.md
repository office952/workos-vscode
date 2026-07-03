# Owner Employee Identity Bootstrap — Decision

## Status

| Field | Value |
|-------|--------|
| **Status** | Decision + Implementation |
| **Runtime impact** | bootstrap/readiness scripts only |
| **Backend impact** | `owner_employee_bootstrap_service` + scripts + tests |
| **Frontend impact** | optional clearer employee-link error copy |
| **DB impact** | none (uses existing `employees.user_id`) |
| **Payroll impact** | none |

## Decizie

Ownerul poate avea un `Employee` record legat de `User` pentru:

- Employee Mobile self identity;
- cereri proprii;
- pontaj propriu read-only;
- review/approval (cu rol manager/admin);
- manager team scope (direct reports via `manager_employee_id`);
- participare operațională (observer/analyst/decision-maker).

Acest lucru **nu** implică automat payroll, salariu, pontaj normat obligatoriu, cost intern CostEngine sau workload operator producție.

## Reguli owner employee

| Field | Value |
|-------|--------|
| `name` | din `WORKOS_OWNER_EMPLOYEE_NAME` (ex. Axinte Remus) |
| `status` | `active` |
| `user_id` | legat la owner `users.id` |
| `manager_employee_id` | `null` (root manager) |
| `employee_type` | `management` (nu productive) |
| `department` / `role` | opțional din env |
| payroll/cost fields | **never set by bootstrap** |

## Reguli bootstrap

- Configurabil prin env vars;
- Idempotent — rerulare sigură;
- Dry-run suportat (`WORKOS_OWNER_BOOTSTRAP_DRY_RUN=1`);
- Fără hardcodare runtime (email/nume);
- Fără creare User nou (user trebuie să existe);
- Fără attendance events / requests / payment records;
- Fără backfill periculos;
- Fără modificare auth.

## Source of truth

```text
User → autentificare (OIDC/JWT)
Employee → identitate operațională
employees.user_id → legătura
employees.manager_employee_id → direct reports (formal manager scope)
```

## Role readiness (documented, not modified by bootstrap)

| Route / capability | Requirement |
|--------------------|-------------|
| `/employee-app` self | role in `employee_mobile`, `manager`, `admin` + linked active Employee |
| `/employee-app/review` | role `manager` or `admin` |
| `/employee-app/team` | role `manager` or `admin` + direct reports via `manager_employee_id` |
| `/attendance/effects` | role `admin` or `operator` |
| Desktop admin | role `admin` (JWT claim; OIDC-managed) |

Bootstrap **does not** change JWT/OIDC roles.

## Scripts

| Script | Purpose |
|--------|---------|
| `backend/scripts/bootstrap_owner_employee.py` | Link/create owner Employee |
| `backend/scripts/check_employee_mobile_readiness.py` | Read-only PASS/FAIL check |

## Deferred

- UI admin manager assignment;
- org chart;
- payroll separation model;
- task role taxonomy;
- delegated approvals;
- multi-company owner mapping;
- push notifications.

## Related

- `docs/architecture/EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md`
- `docs/architecture/EMPLOYEE_FORMAL_MANAGER_REPORTING_DECISION.md`
- `docs/operations/OWNER_EMPLOYEE_MOBILE_READINESS.md`
- `docs/qa/BUILD_OWNER_EMPLOYEE_IDENTITY_BOOTSTRAP.md`
