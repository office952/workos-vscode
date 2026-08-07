# Worklog — MACHINE_RUN schema and contract readiness

**Date:** 2026-08-07  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_SCHEMA_AND_CONTRACT_READINESS`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `2e7e4310`  
**Tip HEAD:** `fdb31fbb2b69e998472a5a7182e4d5c05435e9ca`  
**Verdict:** **PASS**  
**Scope:** docs-only · read-only audit · **no ORM · no migration · no runtime**

---

## Verdict block

```text
MACHINE_RUN_SCHEMA_AND_CONTRACT_READINESS = PASS
MACHINE_RUN_OWNERSHIP = FINALIZED
RESERVATION_RELATION = FINALIZED
PARTICIPANT_MODEL = FINALIZED
MULTI_PLAN_PARTICIPATION = SUPPORTED
BATCH_ELIGIBILITY_BOUNDARY = FINALIZED
NESTING_BOUNDARY = FINALIZED
MACHINE_TIME_COUNTING = ONCE_PER_RUN
STATUS_MODEL = BOUNDED_FOR_READINESS
CAS_IDEMPOTENCY_HISTORY = FINALIZED
SCHEMA_GAP = FINALIZED
RUNTIME_IMPLEMENTATION = NOT_STARTED
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## Decisions applied

| Topic | Decision |
| ----- | -------- |
| Ownership | Task = demand; Reservation = exclusive clock; MACHINE_RUN = shared grouping + participants |
| Reservation FK | `machine_runs.reservation_id` (run owns reservation) |
| Participants | Reference `(execution_plan_id, task_key, order_id)` — no task clone |
| Multi-plan | Supported when operationally valid — not automatic |
| Eligibility | Three stamps → `MAY_JOIN_FUTURE_MACHINE_RUN` only; not auto-group |
| Nesting | Commercial/Intake nesting informs/attaches later; does not own MACHINE_RUN |
| Status | HELD / RESERVED / CANCELLED / RELEASED (+ SUPERSEDED later); RUNNING/COMPLETED deferred |
| Schema gap | Future: `machine_runs` + `machine_run_participants` + `machine_run_transitions` |
| Machine time | Counted once per run |

---

## Audit evidence (read-only)

### Track A — Reservation

- Tables: `execution_task_machine_reservations` + `_transitions` (s64).
- Statuses: HELD → RESERVED → CANCELLED | RELEASED | SUPERSEDED.
- CAS + idempotency + append-only transitions (R9 writer).
- Grain today: task-keyed; open unique `(plan, task_key, machine_id)`.
- No `machine_runs` table.

### Track B — Task / nesting

- Task identity: `(execution_plan_id, task_key)`.
- `face_cnc_cut` stamps capability / MACHINE_BOUND / `batch_eligible=true`.
- All `*nesting*` services = commercial/material/preview — not MACHINE_RUN.
- `batch_eligible` ≠ grouped (Owner D4 + E2E).

### Track C — CAS / schema

- Canonical pattern = Resource State current row + transition table.
- Capacity Stage 1 IMPLEMENTED_INACTIVE; CAPACITY domain not configured in QA.
- Recommend three-table mirror for future GO only.

---

## QA zero-mutation proof

```text
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
QA Alembic = s65_workcenter_capacity_source
Scheduling = ACTIVE
Reservation = ACTIVE
Capacity = NOT_CONFIGURED
MACHINE_RUN tables = absent
capacity source/alloc = 0
assignment transitions = 7
foreign_key_check = 0
plan 21 SHA = 75933211…
plan 22 SHA = 0ec2dce6…
plan 23 SHA = 00ee947c…
```

---

## Artifacts

| Path | Action |
| ---- | ------ |
| `docs/architecture/MACHINE_RUN_SCHEMA_AND_CONTRACT_READINESS.md` | created |
| `docs/architecture/FACE_CNC_CUT_MACHINE_REQUIREMENT_OWNER_DECISIONS.md` | updated |
| `docs/architecture/MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISIONS.md` | updated |
| `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md` | updated |
| this worklog | created |

---

## Boundaries respected

```text
ORM / migration / MACHINE_RUN tables = NOT_STARTED
batch grouping runtime = NOT_STARTED
Reservation writes = 0
Capacity activation = NOT_AUTHORIZED
Phase B/C = untouched
FRONTEND_CHANGED = NO
PUSH = NO
```
