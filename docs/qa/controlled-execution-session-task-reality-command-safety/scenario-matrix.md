# Controlled scenario matrix

Evidence: `tests/test_controlled_session_command_safety.py` (10) + existing controlled/reality/phase_b suites + QA read-only + browser.

| # | Scenario | Result | Notes |
|---|----------|--------|-------|
| 1 | Valid START assigned employee | `SUPPORTED` | isolated DB |
| 2 | START unassigned | `EXPECTED_GUARD` | `task_unassigned` |
| 3 | START wrong employee | `EXPECTED_GUARD` | `employee_not_assigned` |
| 4 | Duplicate START | `SUPPORTED` | `already_active`, no timestamp rewrite |
| 5 | Concurrent START | `SUPPORTED` | two sessions → one active observation |
| 6 | Forged / wrong plan task | `EXPECTED_GUARD` | `operational_task_not_found` |
| 7 | Inactive employee | `EXPECTED_GUARD` | `inactive_employee` |
| 8 | Task-state invalid START | `EXPECTED_GUARD` | `active_session_exists` / elsewhere |
| 9 | Resource-state guarded START | `EXPECTED_GUARD` | **not required** by controlled contract; no CLEAR invented |
| 10 | MachineRun boundary | `SUPPORTED` | no coupling; mutations 0 |
| 11 | Backend restart while active | `SUPPORTED` | re-read committed `tasks_json` |
| 12 | Normal END | `SUPPORTED` | duration = ended−started |
| 13 | END without START | `EXPECTED_GUARD` | `no_active_session` |
| 14 | Duplicate END | `SUPPORTED` | `already_ended` |
| 15 | Concurrent END | `SUPPORTED` | FOR UPDATE + idempotent end |
| 16 | Stale CAS | `SUPPORTED` | row lock + active predicates |
| 17 | Idempotency conflict | `SUPPORTED` | natural-key replay (no client key) |
| 18 | Forced transaction rollback | `SUPPORTED` | single-row commit unit (session=actual) |
| 19 | Read-after-START parity | `SUPPORTED` | response == reality row |
| 20 | Read-after-END parity | `SUPPORTED` | actuals projection matches |
| 21 | Active session vs REASSIGN | `EXPECTED_GUARD` | `task_has_execution_history` / Phase E |
| 22 | Active session vs UNASSIGN | `EXPECTED_GUARD` | same |
| 23 | Multiple employee/session | `EXPECTED_GUARD` | single active primary; elsewhere blocked |
| 24 | No pricing/cost mutation | `SUPPORTED` | flags + no commercial writers |
| 25 | No Capacity/scheduling/machine mutation | `SUPPORTED` | QA + service boundary |

## Severity

| ID | Sev | Finding | Disposition |
|----|-----|---------|-------------|
| L1 | S2 | Raw `/reality/start-task` + operator start bypass assignment | `BYPASS_RISK` / `ACTIVE_LEGACY` — documented; next roadmap domain |
| L2 | S2 | Raw start accepts client timestamp | `ACTIVE_LEGACY` SECURITY_REVIEW for that path; controlled path server-owned |
| L3 | S0 | Controlled FE client missing | backend/API canonical; shop-floor RO |

No S4 IDOR on controlled path. No schema change required for PASS of controlled command.
