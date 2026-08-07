# Worklog — MACHINE_RUN operator read API

**Owner GO:** `AUTHORIZE_MACHINE_RUN_OPERATOR_READ_API`  
**Date:** 2026-08-07  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `4ae976e7`  
**Canonical doc:** `docs/architecture/MACHINE_RUN_OPERATOR_READ_API.md`

---

## Verdict

```text
MACHINE_RUN_OPERATOR_READ_API = PASS
LIST_ENDPOINT = VERIFIED
DETAIL_ENDPOINT = VERIFIED
READ_PERMISSION = execution.machine_run.read
READ_AFTER_COMMAND_CONSISTENCY = VERIFIED
QA_MUTATIONS = 0
MODULES_IMPACT = UPDATED_SUPPORT_SYSTEM_ROWS
GOVERNANCE_IMPACT = UPDATED_OWNERSHIP_ROWS
FRONTEND_MACHINE_RUN_UI = NOT_STARTED
NEXT_IMPLEMENTATION_SCOPE = MACHINE_RUN_SHOP_FLOOR_UI
NO_PUSH = YES
```

---

## Delivered

| Piece | Location |
| ----- | -------- |
| Schemas | `backend/schemas/resource_state_machine_run_read.py` |
| Service | `backend/services/machine_run_read_service.py` |
| Routes | GET list + detail on `execution_plan_v2.py` |
| Permission | `execution.machine_run.read` |
| Tests | `backend/tests/test_machine_run_operator_read_api.py` |
| Modules/Gov data | `frontend/src/lib/currentTruthControlCenter.ts` |

### Endpoints

```text
GET /api/v1/execution/resource-state/machine-runs
GET /api/v1/execution/resource-state/machine-runs/{id}
```

Filters: `status`, `machine_id`, `execution_plan_id`, `order_id`, `open_only`  
`open_only` = reservation HELD|RESERVED (COMPLETED remains open until RELEASE).

### Permission decision

New `execution.machine_run.read` (admin/manager/operator).  
Not `manage`/`execute` (write verbs). Not `plan_generate` (no operator).

---

## Proofs

- Isolated: empty list, 404, lifecycle read-after-command, removed participant, multi-plan/order, filters, HTTP 403/200  
- QA: SHA unchanged · runs=0 · no POST writes from this GO  
- Frontend MachineRun UI: **no** routes/components  

---

## Next

```text
MACHINE_RUN_SHOP_FLOOR_UI — separate Owner GO
```
