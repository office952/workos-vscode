# Wave 5 — employee-records model

Do not infer from labels. Sources traced in code + detail runtime on `/employees-records/7`.

```text
EMPLOYEE_RECORDS_MODEL = DEMO_DOSSIER_ON_REAL_EMPLOYEE
EMPLOYEE_ID_SOURCE = GET /api/v1/entities/employees (useOperationalEmployees → employeesApi.list)
EMPLOYEE_NAME_SOURCE = EmployeeDTO.name from the same master
DOSSIER_DATA_SOURCE = frontend deterministic builders in operationalEmployeeRecords.ts
DOCUMENT_DATA_SOURCE = buildDemoDocumentsForEmployees (hardcoded statuses/templates)
WRITE_ENDPOINT_EXISTS = NO (HR dossier / documents / alerts)
LIVE_MUTATION_SUPPORTED = NO
```

## Boundary

| Layer | Live? | Source |
|-------|-------|--------|
| Employee id | YES | master `employees.id` |
| Display name | YES | master `employees.name` |
| Role / department / skills / hire date / status | YES (with defaults) | `mapOperationalEmployeeToRecord` |
| Phone / email | empty strings | mapper, not API |
| Monthly internal sum | master `cost_lunar_firma` or index fallback | mixed default |
| Contract / fișă / medicina rows | NO | `buildDemoDocumentsForEmployees` |
| Alerts | NO | `buildDemoAlertsForEmployees` |
| Advances shown on profile | NO | `buildDemoAdvancesForEmployees` — **not** `/employee-advances` |
| Work program | NO | hardcoded in `EmployeeProfile` ProfileTab |

Hook: `usePersonalDemoModule` — comment in source: “Live operational employee population + deterministic demo HR module metadata.”

UI honesty: **DEMO** badge, “Contract demonstrativ — evidență internă”, “Avans demonstrativ pe angajat live”.

There is **no** HR-records store and **no** document upload API for this surface. `/employees` remains the only live employee master. Profile advances are **not** the live advances ledger.
