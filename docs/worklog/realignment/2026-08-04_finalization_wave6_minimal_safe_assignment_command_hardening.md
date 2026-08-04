# Finalization Wave 6 — Minimal Safe Assignment Command Hardening

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Task | `FINALIZATION_WAVE_6_MINIMAL_SAFE_ASSIGNMENT_COMMAND_HARDENING` |
| Status | **`FINALIZATION_WAVE_6 = PASS`** |
| Starting HEAD | `ed153898` |
| Implementation commit | `4a72025e` |
| Final HEAD | `4a72025e` |
| Repo / worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Pre-existing tracked changes | none |
| Untracked leftovers | `docs/qa/**` — untouched |
| Schema / migration | **NONE** |
| QA fixture assignment | **NO** |
| Wave 7 | **NOT_AUTHORIZED** |

## Verdict block

```text
FINALIZATION_WAVE_6 = PASS
ASSIGNMENT_COMMAND_HARDENING = VERIFIED
PUBLIC_BYPASS = CLOSED
DIRECT_SERVICE_BYPASS = CLOSED_OR_BLOCKED
AUTHORIZATION = VERIFIED
IDEMPOTENCY = VERIFIED_FOR_EMBEDDED_MODEL
TRANSACTIONALITY = VERIFIED_WITHIN_DOCUMENTED_BOUNDARY
CONCURRENCY_PROTECTION = VERIFIED_WITHIN_DOCUMENTED_BOUNDARY
REAL_QA_ASSIGNMENT_EXECUTED = NO
PERSISTED_QA_MUTATIONS = NONE
SCHEMA_CHANGES = NONE
WAVE_7 = NOT_AUTHORIZED
```

## Owner decisions readback

Implemented DEC-ASSIGN-01…08: close public bypass; order/plan/task/DEC-015 scope; state CAS first; no schema; keep embedded assignment; audit required (embedded in same JSON write); deterministic retry; inventory/migrate with Mobile frozen.

## Architecture analysis

- Canonical mutation: `assign_operational_task_controlled` owns lock → FOR UPDATE → readiness → DEC-015 revalidation → CAS → single `tasks_json` persist with audit fields.
- `assign_plan_task` → `403 direct_assign_blocked` (`BLOCKED_LEGACY`).
- Public `controlled=false` / `allow_reassign=true` → `422` validation errors.
- Mobile `claim` / `start_from_available` → `403 employee_mobile_assignment_frozen`.
- No tenant model in Orders/Employees; strongest scope = order existence + plan-by-order + task-in-plan + active/assignable + DEC-015 eligibility.
- Process-local plan lock + DB `SELECT FOR UPDATE`; **cluster-wide lock not claimed**.

## Files changed (production)

| File | Purpose |
| ---- | ------- |
| `backend/services/controlled_employee_assignment_service.py` | Canonical in-lock CAS command |
| `backend/services/execution_task_assignment_service.py` | Direct assign blocked |
| `backend/routers/execution.py` | Public schema rejects bypass; always canonical |
| `backend/services/employee_mobile_tasks_service.py` | Freeze claim/start_from_available |
| `backend/services/dev_employee_mobile_sandu_fixture_service.py` | Stop direct assign apply |
| `backend/services/assignment_readiness_audit_service.py` | Inventory reflects Wave 6 |
| `frontend/src/api/executionTaskAssignment.ts` | Caller alignment — no bypass flags |
| `frontend/src/pages/MaterializedOpsGraph.tsx` | Drop controlled/allowReassign options |

Plus tests + this worklog + route pointer.

## Route contract

`PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign`  
Body: `{ assigned_employee_id }` only (legacy bypass fields rejected).  
Outcomes: `assigned` / `already_assigned_to_same_employee`; conflicts for different employee / stale completed / eligibility failures.

## Authorization model

```text
authenticated
+ execution.task_assign
+ order exists
+ plan belongs to order (FOR UPDATE)
+ task in operational_tasks[]
+ employee active/assignable
+ DEC-015 eligible for that task
```

## Bypass closure

| Path | Classification |
| ---- | -------------- |
| public `controlled=false` | `BLOCKED_LEGACY` (422) |
| public `allow_reassign=true` | `BLOCKED_LEGACY` (422) |
| `assign_plan_task` | `BLOCKED_LEGACY` (403) |
| Mobile claim / start_from_available | `BLOCKED_LEGACY` / frozen |
| Controlled HTTP path | `ACTIVE_CANONICAL` |

Dead pieces removed: **NONE** (blocked/frozen, not deleted).

## Locking / CAS / transactionality / audit

- Plan-scoped `asyncio.Lock` + `SELECT FOR UPDATE`.
- Eligibility + assignability + task state revalidated inside lock.
- Same employee → idempotent no-write; different → 409; completed → stale conflict.
- Audit evidence: `assignment_source`, `assignment_updated_at`, `assignment_actor_user_id` in same JSON commit; success checks fields after refresh.
- Boundary: not multi-node cluster-safe; no client version token; no separate audit table.

## Tests

```text
pytest tests/test_finalization_wave6_assignment_command_hardening.py
     + controlled / execution_task_assignment / readiness / parser consumers
     + wave5 audit inventory / mobile claim concurrency
→ 66 passed (isolated DB)

pytest tests/test_employee_mobile_tasks.py → 25 passed (alone)

CI targeted four files → 28 passed
```

## Runtime proof

- Temp uvicorn `:8012` (fresh code): `controlled=false` → 422; `allow_reassign=true` → 422; invalid task → 404 `task_not_found` (no persist).
- Detached stack reused `:3000` + `:8002` (stale BE possible); UI RO `/execution/880750` shows assignment still blocked on surface.
- No valid PATCH assign against QA fixture.

## Zero mutation (880750)

| Metric | Value |
| ------ | ----- |
| plan | 23 |
| ops | 13 |
| tasks_json SHA-256 | `e120b0cb91ff500504a9beb62d8e7f6608f5a6a14df2ae1a743c5c111dbac0f2` |
| updated_at | `2026-08-04 02:21:47.122899` |
| assigned / sessions | 0 / 0 |
| Protected 880811/973019/88002 | unchanged |
| F7I | unchanged (not touched) |
| Scheduling / capacity | HOLD / NOT_STARTED |

## UI

`FRONTEND_CHANGED = YES` (caller alignment only).  
No new Assign/Confirm/Auto-assign chrome. Screenshot RO local (not committed): execution 880750 still shows assignment blocked.

## Risks / remaining gaps

- Cluster / multi-worker asyncio.Lock not proven.
- No client ETag/version CAS.
- No multi-tenant org boundary (system has none).
- Live detached `:8002` may lag until process recycle; code proven via tests + temp server.

## Scores

```text
Direction alignment score: 92/100
Operational completion score: 78/100
```

## Next step (not started)

```text
FUTURE CANDIDATE:
CONTROLLED_SINGLE_QA_FIXTURE_EMPLOYEE_ASSIGNMENT_PROOF
```
