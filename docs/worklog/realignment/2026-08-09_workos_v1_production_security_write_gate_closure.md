# WorkOS V1 — Production Security Write Gate Closure

**Date:** 2026-08-09  
**Owner GO:** `AUTHORIZE_WORKOS_V1_PRODUCTION_SECURITY_WRITE_GATE_CLOSURE`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `8f6e9f8c`  
**Verdict:** `PASS` (engineering gate)  

---

## Outcome

```text
WORKOS_V1_PRODUCTION_SECURITY_WRITE_GATE_CLOSURE = PASS
PRODUCTION_SECURITY_WRITE_GATE = DONE_FOR_V1
INTAKE_V5_DISPOSITION = DEPRECATED_NOT_MOUNTED
OPERATIONAL_EMPLOYEE_READ = SAFE_PROJECTION
HR_EMPLOYEE_READ = AUTHORIZED_RESTRICTED (employee.view_hr_cost)
OPERATIONAL_SALARY_EXPOSURE = 0
UNAUTHENTICATED_V1_WRITE_PATHS = 0
ACTIVE_SECURITY_BYPASS = 0
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
```

---

## What closed

1. **Intake V5** — renamed auto-discovered `router` → `_deprecated_router` (same pattern as V3). Not production-mounted. Defense-in-depth: `_deprecated_router` still carries `get_current_user` if manually remounted. Lazy SVG analyzer import so missing optional deps cannot block module load checks.
2. **Employee HR/cost fields** — same `/api/v1/entities/employees` endpoints; response strips HR-restricted fields unless `employee.view_hr_cost` (admin/manager).
3. **Operational registry employees** — salary fields omitted unless same permission.
4. **Employee payments + HR capacity** — permission-gated (`employee_payments.read|write`, `employee.view_hr_cost`).
5. **Bounded UI** — registry panel hides salary row when API omits amount.

---

## Authority

| Concern | Authority |
|---------|-----------|
| Auth identity | `dependencies.auth.get_current_user` (+ JWT / cookie; prod fail-closed when `dev_auth_allowed=False`) |
| Permissions | `dependencies.permissions.PERMISSION_MATRIX` + `require_permission` / `has_permission` |
| Operational employee projection | `employees._serialize(include_hr_cost=False)` + registry `_employee_registry_dict` |
| HR-sensitive projection | same endpoints with `employee.view_hr_cost` |
| Intake V5 | not mounted (`_deprecated_router` only) |

---

## Intake versions (mounted truth)

| Version | Mounted | Auth | Write | V1 canonical |
|---------|---------|------|-------|--------------|
| V2 (entities/intake_requests) | YES | YES | YES | legacy active, secured |
| V3 | NO (`_deprecated_router`) | (if remounted) YES | YES | deprecated |
| V4 | YES | YES | YES | compatibility |
| V5 | NO (`_deprecated_router`) | (if remounted) YES | YES | deprecated |
| V6 | YES | YES | YES | **canonical** |

---

## HR field classification (employee APIs)

| Field | Class |
|-------|-------|
| id, name, role, department, status, employee_type | OPERATIONAL_SAFE |
| user_id, auth_email, auth_role, mobile flags, skills, machines | OPERATIONAL_SAFE |
| data_angajare, end_date, is_assignable | OPERATIONAL_SAFE |
| cost_lunar_firma, salary_amount, monthly_internal_pay_amount | HR_RESTRICTED |
| salary_currency, salary_period, cost_ora_calculat | HR_RESTRICTED |
| ore_lucru_luna, ore_productive_luna (+ source), valid_for_cost_engine | HR_RESTRICTED |
| observatii | HR_RESTRICTED |

---

## Explicit non-goals honored

No SSO, MFA, new RBAC platform, Capacity, Phase E, MachineRun rework, Profitability monetary, Material Actuals impl, Postgres, push.

---

## Evidence

`docs/qa/workos-v1-production-security-write-gate-closure/`

## Next

```text
NEXT_RECOMMENDED_BUILD = WORKOS_V1_MATERIAL_ACTUALS_SUFFICIENCY
NEXT_TASK = NOT_AUTHORIZED
```
