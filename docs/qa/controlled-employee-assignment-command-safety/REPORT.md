# CONTROLLED EMPLOYEE ASSIGNMENT COMMAND SAFETY — evidence report

## Verdict

```text
CONTROLLED_EMPLOYEE_ASSIGNMENT_COMMAND_SAFETY = PASS
HARDENING_APPLIED = NO
HARDENING_SCOPE = none
```

## Starting state (verified)

```text
worktree = C:\w\psiso
branch = feat/f7i-owner-rate-activation
HEAD = 5daa3b86
MACHINE_RUN_V1_E2E = STABLE_BASELINE_AFTER_HARDENING
```

Protected QA (`backend/dev.db`, read-only):

```text
order_id = 880750
execution_plan_id = 23
operational_tasks = 13
assigned = 1 → employee 7 (led_install_letters)
unassigned = 12
assignment_transitions = 7
machine_runs = 0
session_tables = []
alembic = s67_machine_run_execution_status
QA_*_COMMANDS = 0
QA_MUTATIONS = 0
```

## Architecture (summary)

- Canonical task source: `ExecutionPlan V2 operational_tasks[]`
- Canonical commands: ASSIGN / REASSIGN / UNASSIGN (see `call-graph.md`)
- Eligibility ≠ assigned ≠ scheduled ≠ session
- Phase B = pre-start reassignment/unassignment (implemented)
- Phase E = post-start transfer (fail-closed / deferred)

## Safety scores

```text
CANONICAL_TASK_SOURCE = EXECUTION_PLAN_V2_OPERATIONAL_TASKS
CANONICAL_ASSIGNMENT_COMMAND = VERIFIED
INITIAL_ASSIGNMENT = VERIFIED
PRE_START_REASSIGNMENT = VERIFIED
PRE_START_UNASSIGNMENT = VERIFIED
POST_START_REASSIGNMENT = FAIL_CLOSED_REASSIGNMENT_PHASE_E
ELIGIBILITY_WRITE_PARITY = VERIFIED
AUTHORIZATION = VERIFIED
IDOR_PROTECTION = VERIFIED_TASK_PLAN_SCOPE
PII_BOUNDARY = VERIFIED
IDEMPOTENCY = PROVEN
CAS_CONCURRENCY = PROVEN
TRANSACTIONALITY = PROVEN
TWO_EMPLOYEE_RACE = SAFE
ELIGIBILITY_CHANGE_RACE = SAFE
TASK_STATE_RACE = SAFE
RESOURCE_STATE_RACE = SAFE
ASSIGNMENT_TRANSITION_HISTORY = VERIFIED
READ_AFTER_WRITE_PARITY = VERIFIED
TASK_STATE_MUTATIONS = 0
SESSION_MUTATIONS = 0
SCHEDULING_MUTATIONS = 0
CAPACITY_MUTATIONS = 0
MACHINE_ASSIGNMENT_MUTATIONS = 0
MACHINE_RUN_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0
NEW_FEATURES = 0
MODULES_IMPACT = NO_CODE_CHANGE (stale Phase B wording = UI_HARDENING_CANDIDATE)
GOVERNANCE_IMPACT = NO_CODE_CHANGE
REASSIGNMENT_PHASE_E = DEFERRED
EMPLOYEE_SESSION_COUPLING = DEFERRED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
NEXT_TASK = NOT_AUTHORIZED
```

## Notes

1. **Idempotency strategies differ by command:** ASSIGN uses same-employee `already_same`; Phase B uses `transition_id` + payload fingerprint.
2. **Initial ASSIGN history** is embedded in `tasks_json` audit fields; Phase B writes append-only `execution_task_assignment_transitions`.
3. **Resource guards** are fail-closed placeholders; CLEAR is TEST_ONLY. Live commitment probes are not wired — cannot bypass required evaluation call.
4. **IDOR:** forged/cross-plan/cross-order task keys rejected. App remains role-scoped (not multi-tenant row ACL).
5. **No push.** Docs/evidence commit only.
