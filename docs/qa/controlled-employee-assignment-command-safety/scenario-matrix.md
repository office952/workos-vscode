# Controlled scenario matrix

Evidence base: isolated pytest suites (77 passed) + QA read-only baseline + browser read-only.

| # | Scenario | Result | Evidence |
|---|----------|--------|----------|
| 1 | Valid initial assignment | `SUPPORTED` | `test_controlled_accepts_eligible_and_persists`, wave6 assign success |
| 2 | Duplicate replay (same employee) | `SUPPORTED` | wave6 idempotent `already_same` / `already_assigned` |
| 3 | Different-payload conflict | `SUPPORTED` | ASSIGN→different employee `already_assigned_to_different_employee`; Phase B `transition_id_payload_conflict` |
| 4 | Assign already-assigned task | `EXPECTED_GUARD` | ASSIGN rejects other employee; does not become REASSIGN (`allow_reassign` ignored) |
| 5 | Valid pre-start reassignment | `SUPPORTED` | wave11 reassign happy path + history |
| 6 | Post-start reassignment blocked | `EXPECTED_GUARD` | session-history / completed → fail-closed (`EXPECTED_REASSIGNMENT_PHASE_E_BOUNDARY`) |
| 7 | Valid pre-start unassignment | `SUPPORTED` | wave11 unassign + transition |
| 8 | Post-start unassignment blocked | `EXPECTED_GUARD` | same Phase B session/resource/history guards |
| 9 | Ineligible employee | `EXPECTED_GUARD` | `employee_not_eligible` |
| 10 | Inactive employee | `EXPECTED_GUARD` | `inactive_employee` (pre + inside lock) |
| 11 | Forged task | `EXPECTED_GUARD` | `task_not_found` |
| 12 | Cross-plan task | `EXPECTED_GUARD` | task absent from requested order plan operational_tasks |
| 13 | Cross-order request | `EXPECTED_GUARD` | order/plan/task resolution fail-closed; role-wide order access (not multi-tenant ACL) |
| 14 | Stale CAS | `SUPPORTED` | Phase B `stale_current_assignment`; ASSIGN different-employee conflict |
| 15 | Two-employee race | `SUPPORTED` | wave6 one winner; wave11 two-session reassign one wins |
| 16 | Eligibility-change race | `SUPPORTED` | eligibility rebuilt inside lock before write |
| 17 | Task-state race | `SUPPORTED` | completed / session-active re-checked under lock |
| 18 | Resource-state race | `EXPECTED_GUARD` | Phase B always calls `evaluate_resource_guards`; non-test = `NOT_CONFIGURED` fail-closed; CLEAR override TEST_ONLY and not derived from live commitment tables → no live CLEAR→ACTIVE race path in current runtime |
| 19 | Forced transaction failure | `SUPPORTED` | Phase B rollback on persist/consistency failure; ASSIGN commit/rollback |
| 20 | Read-after-write parity | `SUPPORTED` | response fields + plan refresh / consistency `MATCH` |

## Severity findings

| ID | Severity | Finding | Disposition |
|----|----------|---------|-------------|
| F1 | S0 | Initial ASSIGN uses embedded provenance, not transition table | Documented dual-path (Wave 6 vs Phase B) — not a safety defect |
| F2 | S0 | Soft order-scope: any `task_assign` holder may target any known `order_id` | Expected role model; task/plan membership still enforced |
| F3 | S1 | `/modules` MachineRun copy still says “Phase B neautorizat” (stale) | `UI_HARDENING_CANDIDATE` — no UI rewrite in this GO |
| F4 | S0 | Resource guards are placeholder probes (`del order_id/plan_id/task_key`) | Fail-closed default; live probes deferred with Capacity/scheduling activation |

No S3/S4 deterministic defects requiring bounded code hardening under this GO.
