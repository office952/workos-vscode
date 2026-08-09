# MACHINE_RUN — Candidate Discovery + Task Lookup Read API

**Task:** `MACHINE_RUN_CANDIDATE_DISCOVERY_AND_TASK_LOOKUP_READ_API`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_CANDIDATE_DISCOVERY_AND_TASK_LOOKUP_READ_API`  
**Date:** 2026-08-09  
**Status:** **PASS** · backend read-only · **no CREATE/ADD UI · no chips UI**  
**Starting HEAD:** `8aa733dd`  
**Worklog:** `docs/worklog/realignment/2026-08-09_machine_run_candidate_discovery_and_task_lookup_read_api.md`

```text
MACHINE_RUN_CANDIDATE_DISCOVERY_AND_TASK_LOOKUP_READ_API = PASS
CANDIDATE_DISCOVERY_API = VERIFIED
CREATE_CANDIDATES = VERIFIED
ADD_CANDIDATES = VERIFIED
ELIGIBILITY_SOURCE = EXISTING_CREATE_ADD_RUNTIME_VALIDATION
TASK_TO_ACTIVE_MACHINE_RUN_LOOKUP = VERIFIED
WRITER_READ_PARITY = VERIFIED
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
FRONTEND_UI_COMPONENTS = UNCHANGED
CREATE_UI = still deferred until UI closure build
ADD_UI = still deferred until UI closure build
SECONDARY_CONTEXT_LINKS = still deferred until UI closure build
NEXT_IMPLEMENTATION_SCOPE =
MACHINE_RUN_UI_CREATE_ADD_AND_CONTEXT_LINKS_CLOSURE
```

---

## Endpoints

```text
GET /api/v1/execution/resource-state/machine-runs/candidates
  ?machine_id=   (required)
  &execution_plan_id=
  &order_id=
  &operation_code=

GET /api/v1/execution/resource-state/machine-runs/{id}/candidate-participants
  &execution_plan_id=
  &order_id=
  &operation_code=

GET /api/v1/execution/resource-state/machine-runs/by-task
  ?execution_plan_id=
  &task_key=
```

Permission: `execution.machine_run.read` (does not grant CREATE/ADD).

---

## Eligibility source (no duplication)

Shared module: `backend/services/machine_run_eligibility.py`

| Predicate | Writer | Candidate |
| --------- | ------ | --------- |
| MACHINE_BOUND + capability + batch_eligible | `demand_stamps` | `evaluate_demand_stamps` |
| machine capability join | `validate_machine_capability_join` | `machine_capability_compatible` |
| reservable machine | `require_reservable_machine` | same |
| active membership | `find_active_membership` | exclude / lookup |

CREATE/ADD command service imports the same helpers (behavior unchanged).

---

## ADD context — non-HELD

```text
mutation_allowed = false
reason_code = invalid_transition
items = []
```

Does not advertise candidates for RESERVED/RUNNING/COMPLETED/RELEASED/CANCELLED.

---

## Lookup active semantics

Active when:

```text
participant.status = ACTIVE
run.status ∈ {HELD, RESERVED, RUNNING, COMPLETED}
reservation.status ∈ {HELD, RESERVED}
```

Excluded: REMOVED membership · RELEASED/CANCELLED/SUPERSEDED runs · closed reservation.

Uniqueness: >1 ACTIVE membership → `integrity_conflict` (HTTP 409).

Source: `machine_run_participants` → `machine_runs` → run-owned reservation. **Not R6.**

---

## Query strategy

Candidate discovery loads `ExecutionPlan` rows filtered by optional `execution_plan_id` / `order_id`. Without those filters, all plans are scanned and `tasks_json` operational tasks are evaluated in process — acceptable at current laboratory scale; no new indexes or materializations.

---

## UI still deferred

```text
CREATE_UI = DEFERRED
ADD_UI = DEFERRED
SECONDARY_CONTEXT_LINKS = DEFERRED
NEXT = MACHINE_RUN_UI_CREATE_ADD_AND_CONTEXT_LINKS_CLOSURE
```
