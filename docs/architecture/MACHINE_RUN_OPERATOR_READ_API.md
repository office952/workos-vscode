# MACHINE_RUN — Operator Read API

**Task:** `MACHINE_RUN_OPERATOR_READ_API`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_OPERATOR_READ_API`  
**Date:** 2026-08-07  
**Status:** **PASS** · backend read-only · **no shop-floor UI**  
**Starting HEAD:** `4ae976e7`  
**Worklog:** `docs/worklog/realignment/2026-08-07_machine_run_operator_read_api.md`

```text
MACHINE_RUN_OPERATOR_READ_API = PASS
LIST_ENDPOINT = VERIFIED
DETAIL_ENDPOINT = VERIFIED
READ_SOURCE_OF_TRUTH = MACHINE_RUN_RUNTIME
RESERVATION_PROJECTION = VERIFIED
MACHINE_PROJECTION = VERIFIED
PARTICIPANT_PROJECTION = VERIFIED
ACTIVE_REMOVED_PARTICIPANTS = VERIFIED
MULTI_PLAN = VERIFIED
MULTI_ORDER = VERIFIED
STARTED_AT = EXPOSED
COMPLETED_AT = EXPOSED
ACTUAL_RUNTIME_SECONDS = DERIVED_RESPONSE_ONLY
RUN_VERSION = EXPOSED
RESERVATION_VERSION = EXPOSED
READ_AFTER_COMMAND_CONSISTENCY = VERIFIED
READ_PERMISSION = execution.machine_run.read
QA_READ_SMOKE = VERIFIED
QA_MUTATIONS = 0
MODULES_IMPACT = UPDATED_SUPPORT_SYSTEM_ROWS
GOVERNANCE_IMPACT = UPDATED_OWNERSHIP_ROWS
FRONTEND_MACHINE_RUN_UI = PASS (shop-floor)
CANDIDATE_DISCOVERY_API = PASS
TASK_TO_ACTIVE_MACHINE_RUN_LOOKUP = PASS
CREATE_UI = DEFERRED
ADD_UI = DEFERRED
SECONDARY_CONTEXT_LINKS = DEFERRED
NEXT_IMPLEMENTATION_SCOPE =
MACHINE_RUN_UI_CREATE_ADD_AND_CONTEXT_LINKS_CLOSURE
PAUSE_RESUME = DEFERRED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

Canonical candidate/lookup doc: `docs/architecture/MACHINE_RUN_CANDIDATE_DISCOVERY_AND_TASK_LOOKUP_READ_API.md`

---

## Endpoints

```text
GET /api/v1/execution/resource-state/machine-runs
GET /api/v1/execution/resource-state/machine-runs/{machine_run_id}
GET /api/v1/execution/resource-state/machine-runs/candidates
GET /api/v1/execution/resource-state/machine-runs/{id}/candidate-participants
GET /api/v1/execution/resource-state/machine-runs/by-task
```

### List query params

| Param | Meaning |
| ----- | ------- |
| `status` | Canonical MachineRun status |
| `machine_id` | Exact machine |
| `execution_plan_id` | Runs that include this plan (any participant status) |
| `order_id` | Runs that include this order |
| `open_only` | Reservation status ∈ {HELD, RESERVED} (COMPLETED still open until RELEASE) |

### Sort

```text
open reservation first (HELD|RESERVED)
then reservation_start ASC
then machine_run_id ASC
```

### Pagination

```text
DEFERRED — not required for MVP; no nearby resource-state pagination pattern.
```

---

## Permission

```text
execution.machine_run.read → admin, manager, operator
```

**Why new key:**  
`plan_generate` excludes operators; `manage`/`execute` are write verbs. Read must not grant write.  
List/detail require `.read` only — no write side effects.

---

## Source of truth

```text
machine_runs
machine_run_participants
execution_task_machine_reservations (run-owned)
machines
execution_plan.tasks_json (frozen task stamps for participant enrich)
```

Not R6. Not frontend. Not Product System live recompute.

---

## Payload notes

- **List** = compact summary (counts + plan/order id arrays from ACTIVE participants).  
- **Detail** = full participants (ACTIVE first, REMOVED after) + machine + reservation.  
- Root has **no** singular `execution_plan_id` / `order_id`.  
- Statuses = raw enums.  
- `actual_runtime_seconds` = derived on detail when both timestamps present (not persisted).  
- No `allowed_actions[]`, Capacity fields, task/session coupling, history explorer.

---

## Modules / Governance

Updated via `frontend/src/lib/currentTruthControlCenter.ts` (data arrays only):

- Support systems: `machine_run`, `machine_reservation`
- Ownership rows for both  
No `/execution/machine-runs` UI route added.

---

## Next

```text
MACHINE_RUN_SHOP_FLOOR_UI
```

Requires separate Owner GO. Read contract is ready.
