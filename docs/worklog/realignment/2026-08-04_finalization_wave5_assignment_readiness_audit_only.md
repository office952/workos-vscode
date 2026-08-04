# Finalization Wave 5 — Assignment Readiness Audit-Only

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Mini decision | `OWNER_GO = FINALIZATION_WAVE_5_AUDIT_ONLY` · `IMPLEMENT_REAL_ASSIGNMENT = NO` |
| Scope | Assignment readiness RO audit + command-contract research + candidate validation research + auth/idempotency/transactionality audit + zero mutation |
| Exclusions | real assignment, machine assignment, sessions, scheduling, capacity, Employee Mobile, command mutation, schema/migrations |
| Repo | `C:\Users\offic\workos_app_vs` (common git) |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `8386e3a6` |
| Final HEAD | `9f236010` (`feat(execution): add assignment readiness audit`) |
| Ancestry | `1e8d3344`, `6214ee7b`, `8386e3a6` ⊂ HEAD |
| Verdict | `FINALIZATION_WAVE_5 = PASS` |
| Implementation mode | **B** scoped RO Assignment Readiness Audit GET (compose Wave 4 + command inventory) |

## Alternatives evaluated

| Option | Decision |
| ------ | -------- |
| A docs/tests-only | Rejected — no single RO surface answered readiness + contract + hypothetical candidate |
| **B new RO GET audit** | **Chosen** — composes eligibility + resource readiness + embedded assignment state |
| C extend existing RM | Rejected — would overload eligibility/resource envelopes |
| D harden pure validator only | Partial reuse — pure `evaluate_candidate_for_future_assignment` included inside B; mutating command left untouched |
| E PARTIAL_BLOCKED | Not required — auditable without schema change |

## Canonical assignment command (researched, not executed)

```text
PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign
→ AssignPlanTaskRequest { assigned_employee_id, allow_reassign=false, controlled=true }
→ require_permission("execution.task_assign")
→ assign_operational_task_controlled (DEC-015 revalidate)
→ assign_plan_task (embed assigned_employee_id in tasks_json + commit)
```

| Step | Status |
| ---- | ------ |
| HTTP route | IMPLEMENTED_AND_PROVEN |
| Auth permission | IMPLEMENTED_AND_PROVEN |
| Order → plan | IMPLEMENTED_AND_PROVEN (latest plan by order_id) |
| Task from operational_tasks[] | IMPLEMENTED_AND_PROVEN |
| Eligibility revalidation (controlled) | IMPLEMENTED_AND_PROVEN |
| Frontend eligible override | absent / ignored (server rebuilds) |
| Legacy `controlled=false` bypass | ACTIVE_LEGACY / BYPASSABLE |
| Idempotency | IDEMPOTENCY_PARTIAL |
| Transactionality | TRANSACTIONALITY_PARTIAL |
| Concurrency | CONCURRENCY_PARTIAL |
| Owner GO gate inside command | MISSING (Wave 5 documents CLOSED; command remains permission-reachable) |

## Wave 5 deliverable

- Service: `assignment_readiness_audit_service.py`
- GET: `/api/v1/execution/plan-v2/from-order/{order_id}/assignment-readiness`
- Optional query: `task_key` + `candidate_employee_id` → hypothetical eval, **never persist**
- Always: `assignment_authorized=false` / `OWNER_GO_FOR_REAL_ASSIGNMENT_NOT_GRANTED`
- UI: `AssignmentReadinessPanel` on `/execution/880750`

## Runtime proof (fixture 880750 / plan 23)

| Check | Result |
| ----- | ------ |
| Backend | `:8002` worktree uvicorn · `APP_ENV=development` · `backend/dev.db` |
| Frontend | `:3001` Vite · `BACKEND_PORT=8002` |
| Audit | status=ok · ops=13 · assignments=0 · machine=0 · authorized=false |
| Hypothetical | VALID_CANDIDATE_FOR_FUTURE_ASSIGNMENT on CNC face cut / emp 7 · still authorized=false |
| tasks_json sha | `e120b0cb…` unchanged |
| plan updated_at | `2026-08-04 02:21:47.122899` unchanged |
| Protected 880811 / 973019 | 1847.5 / 847.5 unchanged |
| F7I | 15 / 1.5 / 35 / 20 EUR · 4/4 unchanged |
| Forbidden UI buttons | absent |

Local screenshots (not committed): `docs/qa/workos-wave5-assignment-readiness-audit-v1/screenshots/`

Dark: NOT_OFFICIALLY_SUPPORTED for this GO.

## Tests

- Backend: `test_finalization_wave5_assignment_readiness_audit.py` — PASS (8)
- Frontend: assignment readiness semantics + ExecutionDetail Step9B mock — PASS

## Dead pieces (read-only)

| Piece | Class |
| ----- | ----- |
| Ops-Graph Assign picker (`MaterializedOpsGraph`) | ACTIVE_LEGACY (mutation UI outside ExecutionDetail Wave path) |
| `controlled=false` manager assign | ACTIVE_LEGACY / BYPASSABLE |
| Finish/intake “assignment” services | DEVIATED domain (finish layers, not employee assign) |
| Employee Mobile assign helpers | FROZEN_FINAL_FINAL / UNTOUCHED |

Dead pieces removed: **NONE**.

## Owner decisions still required (Wave 6+)

1. Real assignment GO (authorize command execution on controlled fixture)
2. Whether `controlled=false` bypass is retired or constrained
3. Idempotency strategy (key / unique constraint / expected version) — may need schema
4. Cluster-safe concurrency (beyond process-local asyncio.Lock)
5. Machine assignment remains a separate GO

## Scores

- Direction alignment: **92/100**
- Operational completion: **50/100** (audit ≠ assigned shop floor)

## Exact next step

**DO NOT EXECUTE ASSIGNMENT.** Owner reviews Wave 5. Recommended unauthorized Wave 6: controlled employee assignment command hardening + one isolated QA fixture mutation proof.
