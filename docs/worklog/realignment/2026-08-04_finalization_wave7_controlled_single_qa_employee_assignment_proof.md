# Finalization Wave 7 — Controlled Single QA Employee Assignment Proof

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Task | `FINALIZATION_WAVE_7_CONTROLLED_SINGLE_QA_FIXTURE_EMPLOYEE_ASSIGNMENT_PROOF` |
| Status | **`FINALIZATION_WAVE_7 = PASS`** |
| Starting HEAD | `f68790f3` |
| Final HEAD | b652d1bd |
| Repo / worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Production code changed | **NO** |
| Schema / migration | **NONE** |
| FRONTEND_CHANGED | **NO** |

## Verdict

```text
FINALIZATION_WAVE_7 = PASS
CONTROLLED_SINGLE_QA_ASSIGNMENT = VERIFIED
ORDER_ID = 880750
EXECUTION_PLAN_ID = 23
ASSIGNED_TASK = node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters
ASSIGNED_EMPLOYEE = employee_id=7 (Andrei Goghi — documented QA pick)
SUCCESSFUL_ASSIGNMENT_MUTATIONS = 1
SAME_EMPLOYEE_RETRY = IDEMPOTENT_NOOP
DIFFERENT_EMPLOYEE_REQUEST = CONFLICT (employee_id=6)
AUDIT_EVIDENCE = VERIFIED
OTHER_OPERATIONAL_TASKS = UNCHANGED
MACHINE_ASSIGNMENTS = 0
SESSIONS = 0
ATTENDANCE_MUTATIONS = 0
SCHEDULING = HOLD
CAPACITY_ALLOCATION = NOT_STARTED
EMPLOYEE_MOBILE = FROZEN_FINAL_FINAL
PROTECTED_BASELINES = UNCHANGED_EXCEPT_AUTHORIZED_ASSIGNMENT
PRODUCTION_ROLLOUT = NOT_AUTHORIZED
WAVE_8 = NOT_AUTHORIZED
```

## Owner authorization

Exactly one employee assignment on one operational task in plan 23 / order 880750.  
No reassignment, unassignment, sessions, Mobile, scheduling, or schema.

## Runtime identity

| Item | Value |
| ---- | ----- |
| Mutation runtime | uvicorn `main:app` `:8013` then proof reads on `:8000`/`:8002` |
| Commit served | `f68790f3` (Wave 6 tip) |
| APP_ENV | `development` |
| DB | `C:\w\psiso\backend\dev.db` (non-production local SQLite) |
| Concurrent writers | stopped before mutation (stale `:8002`/`:8001`) |
| Backup | `backend/_qa_backups/dev_db_wave7_preassign_20260804_191447.db` (outside git, SHA matched pre-mutation DB) |

Pre-mutation DB SHA-256: `4A77434502A8C2FA053DD083342DD829CA21064A01AA8651E1AB78717FD8CE4B`  
Pre-mutation `tasks_json` SHA-256: `e120b0cb91ff500504a9beb62d8e7f6608f5a6a14df2ae1a743c5c111dbac0f2`  
Pre-mutation `updated_at`: `2026-08-04 02:21:47.122899`

## Fixture preconditions

| Check | Result |
| ----- | ------ |
| order 880750 | present (`ORD-WAVE2-QA-880750`) |
| plan 23 belongs to order | yes |
| `execution_tasks_created` | true |
| operational_tasks | 13 |
| assigned before | 0 |
| sessions / reality | 0 / absent |
| readiness | assignment-readiness `ok`, scheduling HOLD |

## Task selection

```text
task_key / task_id =
  node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters
type = led_assembly
workcenter = WC_LED_ASSEMBLY (frozen on task / eligibility RM)
status = unassigned, not completed, no session
estimated_minutes = null (+ PLANNING_MINUTES_SOURCE_REQUIRED / planning_minutes_source_missing)
depends_on = [back_cut]
eligibility = ready_with_warnings; 3 eligible employees
```

Why safest QA proof: matches prior golden-pilot LED assignment pattern; DEC-015 ready; no machine required for employee assign proof; not PREPRESS-blocked.

## Employee selection

```text
selected QA employee_id = 7
display_name = Andrei Goghi
provenance = documented deterministic QA pick
  (docs/qa/golden-pilot-controlled-employee-assignment-v1 — Andrei/Costi/Vali triad)
active = yes
DEC-015 eligible for LED = yes
availability = not_evaluated (correct)
cost/rate/salary = not used
```

Second candidate for conflict only: `employee_id=6` (Costi Modelator) — also in golden-pilot QA triad.

## Candidate preview (read-only before mutation)

- Candidate exists/active: yes  
- Roles/skills: hybrid auth; `SK_ELECTRICIAN`; WC_LED_ASSEMBLY; operation `montaj_led`  
- DEC-015: `ready_with_warnings`  
- Assignment Owner gate for this Wave: authorized for this single QA proof  
- Current assignment: unassigned  

## Mutation sequence

### Authorized assignment (mutation #1)

```text
PATCH /api/v1/execution/plan/880750/tasks/{led_install_letters}/assign
body: {"assigned_employee_id":7}
```

Persisted:

| Field | Value |
| ----- | ----- |
| assigned_employee_id | 7 |
| assignment_source | `canonical_controlled_assign_v1` |
| assignment_actor_user_id | `dev-admin-user-00000000` |
| assignment_updated_at | `2026-08-04T16:16:57.406324+00:00` |
| plan.updated_at | `2026-08-04 19:16:57.407320` |
| tasks_json SHA after | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |

Note: first successful write occurred under `APP_ENV=development` auth bypass (synthetic admin). Actor has `execution.task_assign`. Payload was the intended canonical body.

### Same-employee retry

```text
assignment_outcome = already_assigned_to_same_employee
already_assigned = true
sessions_created = 0
tasks_json SHA unchanged
updated_at unchanged
```

### Different-employee conflict

```text
PATCH … assigned_employee_id=6
→ 409 assignment_conflict
reason = already_assigned_to_different_employee
current_assigned_employee_id = 7
tasks_json SHA unchanged
```

## Mutation budget

```text
AUTHORIZED_MUTATION_BUDGET = 1
SUCCESSFUL_ASSIGNMENT_MUTATIONS = 1
IDEMPOTENT_RETRIES = ≥1 (proven no-op)
CONFLICT_REQUESTS = 1
UNAUTHORIZED_MUTATIONS = 0
```

## Authorization / negative proofs

| Case | Result |
| ---- | ------ |
| `controlled=false` | 422 `legacy_controlled_false_forbidden` (no persist) |
| `allow_reassign=true` | 422 `silent_reassignment_forbidden` (no persist) |
| wrong order | 404 `order_not_found` |
| forged task | 404 `task_not_found` |
| unknown employee | 404 `employee_not_found` |
| missing Authorization header | **DEV bypass → synthetic admin** (environment design; not production) |
| invalid token | 503 (infra / decode path) |

## Audit evidence

Embedded in same `tasks_json` write: source, actor, timestamp, employee id.  
Retry does not rewrite audit fields / hash.

## Other task invariants

All 12 non-target tasks: non-assignment field fingerprints unchanged vs pre-mutation.  
`estimated_minutes` remain null; dependencies/workcenters unchanged on all tasks.

## Side effects

```text
team assignments = 0
machine assignments = 0
sessions = 0
attendance mutations = 0
scheduling = HOLD
capacity = NOT_STARTED
Employee Mobile = FROZEN_FINAL_FINAL
```

## Protected baselines / F7I

| Item | Status |
| ---- | ------ |
| 880811 / 973019 / 88002 | unchanged plan identities |
| F7I rates 15 / 1.5 / 35 / 20 EUR | unchanged in `commercial_rules_volumetric_v2.py` |

## UI proof

`FRONTEND_CHANGED = NO`  
Browser at `http://127.0.0.1:3000/execution/880750` blocked by Vite proxy infrastructure (proxy `/api` → 500 while direct backend `:8000` HEAD returns 200).  
API read-model proof: `assignment-readiness` reports `employee_assignment_count=1`, LED task assigned to 7, `scheduling=HOLD`.  
No Start/Available/Scheduled chrome introduced.

## Tests

```text
Before mutation:
  pytest Wave6 hardening + controlled + execution_task_assignment
  → 23 passed (isolated test DB; not QA DB)

After mutation:
  API read-after-write + idempotent retry + conflict (QA DB)
  Wave6 suites not re-run against QA DB
```

## Dead pieces

| Piece | Class |
| ----- | ----- |
| public controlled=false | BLOCKED_LEGACY |
| allow_reassign | BLOCKED_LEGACY |
| direct assign_plan_task | BLOCKED_LEGACY |
| Mobile claim / start_from_available | BLOCKED_LEGACY |
| canonical assign path | ACTIVE_CANONICAL |

Dead pieces removed: **NONE**

## Recovery

Backup retained outside git. No automatic restore/unassign after success (Owner rule).  
Recovery would require separate Owner GO to restore backup file.

## Remaining risks

- Multi-node concurrency still not proven (Wave 6 boundary).  
- Dev auth bypass authenticates bare requests as admin in `development`.  
- FE Vite proxy currently unhealthy for browser RO; assignment verified via API.

## Scores

```text
Direction alignment score: 90/100
Operational completion score: 82/100
```

## Next step (not started)

```text
FUTURE CANDIDATE:
ASSIGNMENT_OBSERVABILITY_AND_CONTROLLED_REASSIGNMENT_POLICY_AUDIT
```
