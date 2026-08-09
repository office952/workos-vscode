# Assignment command call graph (factual)

HEAD audited: `5daa3b86`

## Canonical active paths

### ASSIGN (initial)

```text
PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign
  schema: AssignPlanTaskRequest.assigned_employee_id
  auth: get_current_user + require_permission("execution.task_assign")
       roles: admin | manager | operator
  → assign_operational_task_controlled
       pre: order exists, employee exists + is_assignable
       lock: asyncio per-order lock + ExecutionPlan.with_for_update()
       revalidate: employee active, build_employee_eligibility_read_model
       task identity: operational_tasks[] only (eligibility task_key == task_id)
       guards: eligibility status, eligible_ids membership, no active session,
               not completed, not assigned to different employee
       CAS: unassigned → assign; same employee → already_same (no rewrite)
       persist: tasks_json rewrite (embedded assigned_employee_id + audit fields)
       history: embedded provenance (assignment_updated_at / source / actor)
       NO execution_task_assignment_transitions row on initial ASSIGN
```

Classification: `CANONICAL_ACTIVE`

### REASSIGN (Phase B pre-start)

```text
PATCH …/reassign
  schema: transition_id, expected_current_employee_id, new_employee_id, reason_*
  auth: execution.task_reassign → admin | manager
  → reassign_operational_task_controlled
       plan lock + FOR UPDATE
       eligibility revalidation
       session-history guard (fail-closed if post-start / active session history)
       evaluate_resource_guards (scheduling / reservation / capacity)
       CAS: expected_current_employee_id + transition_id uniqueness/fingerprint
       atomic: INSERT transition + UPDATE tasks_json → commit / rollback all
```

Classification: `CANONICAL_ACTIVE`

### UNASSIGN (Phase B pre-start)

```text
PATCH …/unassign
  auth: execution.task_unassign → admin | manager
  → unassign_operational_task_controlled
  (same guard + transition atomicity family as REASSIGN)
```

Classification: `CANONICAL_ACTIVE`

### Read models

| Surface | Route | Permission | Class |
|--------|-------|------------|-------|
| Eligibility | `GET …/plan-v2/from-order/{order_id}/employee-eligibility` | `execution.plan_generate` | `CANONICAL_ACTIVE` |
| Assignment readiness | `GET …/assignment-readiness` | `execution.plan_generate` | `CANONICAL_ACTIVE` |

## Dead / blocked / compatibility

| Piece | Class | Note |
|-------|-------|------|
| `controlled=false` / public bypass assign | `DEAD_CANDIDATE` | Router always controlled |
| `allow_reassign=True` on ASSIGN | `DEAD_CANDIDATE` | Ignored; ASSIGN cannot silently become REASSIGN |
| Direct assign / mobile claim | `ACTIVE_LEGACY` / frozen | Phase B tests assert mobile frozen |
| `clear_plan_task_assignment` helper | `ACTIVE_LEGACY` | Not Phase B unassign path |
| FE reassign/unassign UI | `DEAD_CANDIDATE` | API only; panels are eligibility/readiness + assign client |

## Canonical authorities

| Concern | Authority |
|---------|-----------|
| Task identity | `ExecutionPlan.tasks_json.operational_tasks[]` |
| Assignment current state | `operational_tasks[].assigned_employee_id` |
| Transition history (Phase B) | `execution_task_assignment_transitions` |
| Eligibility | employee eligibility read model (DEC-015) |
| Workcenter / technical truth | frozen plan fields — assignment writer does not re-resolve |
