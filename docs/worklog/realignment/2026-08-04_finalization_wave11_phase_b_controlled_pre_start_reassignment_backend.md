# Finalization Wave 11 / Phase B — Controlled Pre-Start Reassignment Backend

**Task:** `FINALIZATION_WAVE_11 = PHASE_B_CONTROLLED_PRE_START_REASSIGNMENT_BACKEND_IMPLEMENTATION`  
**Date:** 2026-08-04  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `f6dc7bae`  
**Owner GO:** `PHASE_B_CONTROLLED_PRE_START_REASSIGNMENT_BACKEND_IMPLEMENTATION`

---

## Verdict

```text
FINALIZATION_WAVE_11 = PASS
PHASE_B_BACKEND_IMPLEMENTATION = VERIFIED
REASSIGNMENT_ROUTE = IMPLEMENTED
UNASSIGNMENT_ROUTE = IMPLEMENTED
REASSIGN_PERMISSION = VERIFIED
UNASSIGN_PERMISSION = VERIFIED
EXPECTED_CURRENT_EMPLOYEE_CAS = VERIFIED
TRANSITION_ID_IDEMPOTENCY = VERIFIED
ATOMIC_DUAL_WRITE = VERIFIED_SQLITE_BOUNDARY
APPEND_ONLY_HISTORY = VERIFIED
CONSISTENCY_GUARD = VERIFIED
DEC015_REVALIDATION = VERIFIED
PRE_START_GUARDS = VERIFIED
SESSION_HISTORY_GUARD = VERIFIED
SCHEDULING_RESERVATION_CAPACITY_GUARDS = VERIFIED_FAIL_CLOSED
ISOLATED_RUNTIME_PROOF = VERIFIED
QA_REASSIGNMENT_MUTATIONS = 0
QA_UNASSIGNMENT_MUTATIONS = 0
QA_OPERATIONAL_STATE = UNCHANGED
FRONTEND_IMPLEMENTED = NO
EMPLOYEE_MOBILE = FROZEN_FINAL_FINAL
PHASE_C = NOT_AUTHORIZED
WAVE_12 = NOT_AUTHORIZED
```

---

## Owner GO readback

Authorized: backend reassign/unassign, routes, schemas, permissions, dual-write, isolated tests.  
Forbidden: QA mutations, UI, Mobile, sessions/scheduling/capacity engines, new migrations, push/PR/deploy, Phase C.

---

## Repo / preflight

| Item | Value |
| ---- | ----- |
| Repo root | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `f6dc7bae` |
| Migration head | `s63_execution_task_assignment_transitions` |
| Tracked conflicts | none |
| Untracked leftovers | `docs/qa/**`, `backend/_qa_backups/**` (not staged) |
| Live ports (Owner stack) | `:3000`, `:8000` — untouched for proofs |

Ancestry through Wave 10 tip `f6dc7bae` verified.

---

## Permissions

```text
execution.task_reassign → admin, manager
execution.task_unassign → admin, manager
```

`execution.task_assign` alone is insufficient. Enforced at route (`require_permission`) **and** service (`has_permission` + manager/admin).

---

## Routes / schemas

```text
PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/reassign
PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/unassign
```

Bodies: `transition_id` (UUID), `expected_current_employee_id`, `reason_code`, optional `reason_note`; reassign adds `new_employee_id`.  
Rejects `controlled=false`, `allow_reassign=true`, OTHER without note, same-employee reassign.

---

## Call graph (summary)

Auth → distinct permission → plan lock (`asyncio.Lock` + `SELECT FOR UPDATE`) → re-read tasks → consistency MATCH required → CAS expected employee → session-history fail-closed → resource guards (CLEAR only) → DEC-015 inside lock (reassign) → transition_id idempotency → INSERT transition + UPDATE `tasks_json` → post consistency → COMMIT / ROLLBACK.

---

## Guards

| Guard | Behavior |
| ----- | -------- |
| Consistency | No history / mismatch → `assignment_transition_state_mismatch` |
| CAS | Stale → `stale_current_assignment`; null → `task_not_currently_assigned` |
| Session history | Any `started_at` in ExecutionReality → `task_has_execution_history` |
| Resources | Default `NOT_CONFIGURED` (fail-closed). Isolated tests set `WORKOS_PHASE_B_RESOURCE_GUARDS=CLEAR`. QA/dev runtime without CLEAR cannot mutate via these routes — correct. |
| DEC-015 | Reassign only, inside lock |

---

## Idempotency / dual-write

Same `transition_id` + same canonical payload → `already_applied`, no second row, no `tasks_json` rewrite.  
Different payload → `transition_id_payload_conflict`.  
Insert + embedded update in one transaction; failure rolls back both.

---

## Observability

Safe structured log events: `TASK_REASSIGNMENT_*` / `TASK_UNASSIGNMENT_*` with IDs/codes only.  
`reason_note` persisted on transition row, not in normal operational logs.

---

## Tests

```text
command: pytest -q tests/test_finalization_wave11_phase_b_reassignment.py
engine: isolated SQLite (IsolatedDBFixture tempfile)
passed: 11
failed: 0
skipped: 0
classification: WAVE11_PHASE_B_BACKEND
```

Coverage: permissions, roles HTTP, schemas, reassign/unassign history, idempotency, CAS, session history, NOT_CONFIGURED resources, mismatch without history, service-level auth, legacy/Mobile blocks, concurrency (one wins), HTTP success+retry.

Isolated HTTP proof: FastAPI `TestClient` against isolated DB (ASGI), not QA `dev.db`.

---

## QA read-only (unchanged)

```text
QA_DB_FILE_SHA = 0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2
QA_TRANSITION_ROW_FINGERPRINT = bea29ac2e60690f78efa6d399972d0132145be05eae00a4c1a13d33c43f3ee4b
tasks_json SHA = 00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2
updated_at = 2026-08-04 19:16:57.407320
transition rows = 7
880750 / plan 23 / LED→7 / 1 assigned / 12 unassigned
QA_REASSIGN_ROUTE_REQUESTS = 0
QA_UNASSIGN_ROUTE_REQUESTS = 0
```

Baselines: 880811+22, 973019+21, 88002 absent. F7I 15/1.5/35/20 EUR unchanged.

---

## Mutation budget

```text
ISOLATED_REASSIGNMENT_MUTATIONS = exercised in tempfile DB only
ISOLATED_UNASSIGNMENT_MUTATIONS = exercised in tempfile DB only
QA_ASSIGNMENT_REQUESTS = 0
QA_REASSIGNMENT_REQUESTS = 0
QA_UNASSIGNMENT_REQUESTS = 0
QA_SUCCESSFUL_MUTATIONS = 0
```

---

## Dead Pieces Check

| Piece | Classification |
| ----- | -------------- |
| allow_reassign | `BLOCKED_LEGACY` |
| controlled=false | `BLOCKED_LEGACY` |
| clear_plan_task_assignment | `ACTIVE_LEGACY` (not Phase B unassign) |
| direct assign_plan_task | `BLOCKED_LEGACY` |
| Mobile claim/start | `BLOCKED_LEGACY` / frozen |
| QA duplicate indexes | `ACTIVE_LEGACY` |
| WORKOS_PHASE_B_RESOURCE_GUARDS | `ACTIVE_CONTROLLED` test/isolated override |

```text
Dead pieces removed: NONE
FRONTEND_CHANGED = NO
```

---

## Remaining risks

1. Real QA/dev cannot reassign until scheduling/reservation/capacity expose authoritative CLEAR (fail-closed today).  
2. Initial ASSIGN path still does not dual-write transitions (Phase A backfill / seed history required before reassign).  
3. SQLite single-writer — multi-node NOT_PROVEN (DEC-DATABASE-01).  
4. Phase C QA proof not authorized.

---

## Files changed

- `backend/dependencies/permissions.py`
- `backend/schemas/controlled_pre_start_reassignment.py`
- `backend/services/phase_b_resource_guard_service.py`
- `backend/services/controlled_pre_start_reassignment_service.py`
- `backend/routers/execution.py`
- `backend/tests/test_finalization_wave11_phase_b_reassignment.py`
- architecture/worklog/route updates (docs commit)

---

## Scores

```text
Direction alignment score: 96/100
Operational completion score: 71/100
```

(Phase C / UI / QA live transition not done — score not inflated.)

---

## Next step

```text
FUTURE CANDIDATE:
PHASE_C_CONTROLLED_SINGLE_QA_PRE_START_REASSIGNMENT_PROOF
```

Not started. Await Owner review.
