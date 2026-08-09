# Worklog — MACHINE_RUN candidate discovery + task lookup read API

**Owner GO:** `AUTHORIZE_MACHINE_RUN_CANDIDATE_DISCOVERY_AND_TASK_LOOKUP_READ_API`  
**Date:** 2026-08-09  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `8aa733dd`  
**Canonical doc:** `docs/architecture/MACHINE_RUN_CANDIDATE_DISCOVERY_AND_TASK_LOOKUP_READ_API.md`

---

## Verdict

```text
MACHINE_RUN_CANDIDATE_DISCOVERY_AND_TASK_LOOKUP_READ_API = PASS

CANDIDATE_DISCOVERY_API = VERIFIED
CREATE_CANDIDATES = VERIFIED
ADD_CANDIDATES = VERIFIED
ELIGIBILITY_SOURCE =
EXISTING_CREATE_ADD_RUNTIME_VALIDATION
MACHINE_BOUND_FILTER = VERIFIED
CAPABILITY_FILTER = VERIFIED
BATCH_ELIGIBILITY_FILTER = VERIFIED
MACHINE_COMPATIBILITY = VERIFIED
ACTIVE_MEMBERSHIP_EXCLUSION = VERIFIED
MULTI_PLAN = VERIFIED
MULTI_ORDER = VERIFIED

TASK_TO_ACTIVE_MACHINE_RUN_LOOKUP = VERIFIED
REMOVED_MEMBERSHIP_EXCLUDED = VERIFIED
TERMINAL_RUN_EXCLUDED = VERIFIED
UNIQUENESS_GUARD = VERIFIED
WRITER_READ_PARITY = VERIFIED

DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
FRONTEND_UI_COMPONENTS = UNCHANGED
  (modules/gov truth rows only)

CREATE_UI = still deferred until UI closure build
ADD_UI = still deferred until UI closure build
SECONDARY_CONTEXT_LINKS = still deferred until UI closure build

NEXT_IMPLEMENTATION_SCOPE =
MACHINE_RUN_UI_CREATE_ADD_AND_CONTEXT_LINKS_CLOSURE
PAUSE_RESUME = DEFERRED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
NO_PUSH = YES
```

---

## Delivered

| Piece | Location |
| ----- | -------- |
| Shared eligibility | `backend/services/machine_run_eligibility.py` |
| Candidate + lookup service | `backend/services/machine_run_candidate_service.py` |
| Schemas | `backend/schemas/resource_state_machine_run_candidate.py` |
| Routes | `execution_plan_v2.py` (before `{id}` detail) |
| Writer reuse | `machine_run_command_service.py` imports shared helpers |
| Tests | `tests/test_machine_run_candidate_discovery_and_task_lookup.py` |

### Endpoints

```text
GET …/machine-runs/candidates?machine_id=
GET …/machine-runs/{id}/candidate-participants
GET …/machine-runs/by-task?execution_plan_id=&task_key=
```

ADD non-HELD: `mutation_allowed=false` · `reason_code=invalid_transition` · empty items.

### Query strategy

Optional plan/order filters; otherwise scan ExecutionPlan rows and evaluate `operational_tasks[]` in process. No new indexes / materializations.

---

## Proofs

- Isolated: 7 candidate/lookup tests PASS  
- Writer regressions (create/add/remove/confirm/reschedule/start/complete/read): **97 passed**  
- QA: `machine_runs = 0`  
- Schema migrations: none  

---

## Next

```text
MACHINE_RUN_UI_CREATE_ADD_AND_CONTEXT_LINKS_CLOSURE
```

Separate Owner GO — wire CREATE/ADD UI + ExecutionDetail/Ops-Graph chips to these read APIs.
