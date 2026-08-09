# Session / task reality call graph

HEAD start: `b7aebd04`

## Canonical assignment-gated path — `CANONICAL_ACTIVE`

```text
POST /api/v1/execution/plan/{order_id}/tasks/{task_id}/sessions/start
POST /api/v1/execution/plan/{order_id}/tasks/{task_id}/sessions/end
GET  /api/v1/execution/plan/{order_id}/execution-actuals

auth: execution.task_start (start AND end)
     execution.production_blueprint (actuals read)

→ _resolve_controlled_session_employee (self | supervisor)
→ start/end_controlled_task_session
     plan load + v2 operational_tasks[] only
     assigned_employee_id must match
     employee active
     single active primary session / employee-elsewhere guard
     server clock → timestamp
→ ExecutionRealityService.start_task / end_task
     SELECT execution_reality FOR UPDATE
     mutate tasks_json observation
     commit
→ ExecutionActuals = read projection over plan + sessions
```

SoT: `execution_reality.tasks_json` (no separate Session table).

## Other live writers

| Path | Class | Assignment gate | End vs complete |
|------|-------|-----------------|-----------------|
| Controlled sessions/* | `CANONICAL_ACTIVE` | YES | end ≠ complete |
| Mobile PATCH start/complete | `CANONICAL_ACTIVE` (self) | principal authority | complete stamps completed_by |
| `/reality/start-task` / `end-task` | `ACTIVE_LEGACY` | NO | end ≠ complete; **client timestamp accepted** |
| Operator `/task-action` | `ACTIVE_LEGACY` | NO on start | complete can stamp completion |
| claim / start-from-available | `FROZEN` | N/A | 403 |
| Helper session start/stop | `ACTIVE_LEGACY` | collab | end ≠ complete |
| MachineRun commands | separate | N/A | `MACHINE_RUN_MUTATIONS` from session = 0 |

## Task source

Controlled path: `operational_tasks[]` only. Planned-only → `v2_not_materialized`. Forged/cross-order → `operational_task_not_found`.
