# After call graph

```text
POST /api/v1/execution/plan/{order}/tasks/{task}/sessions/start|end
  → controlled_task_session_service  [CANONICAL]

POST /api/v1/execution/reality/start-task
  → resolve assignee
  → (idempotent if active) else readiness
  → start_controlled_task_session
  → return reality row
  [COMPATIBILITY_BRIDGE_SAFE]
  client timestamp IGNORED

POST /api/v1/execution/reality/end-task
  → resolve assignee
  → end_controlled_task_session   # not complete
  [COMPATIBILITY_BRIDGE_SAFE]

POST /api/v1/operator/task-action action=start
  → resolve/match assignee
  → readiness (unless already active)
  → start_controlled_task_session
  [COMPATIBILITY_BRIDGE_SAFE]

POST /api/v1/operator/task-action action=complete
  → resolve/match assignee
  → complete_controlled_task_session
  [COMPATIBILITY_BRIDGE_SAFE]

PATCH /api/v1/employee-mobile/tasks/{id}/start|complete
  → start/complete_controlled_task_session
  [COMPATIBILITY_BRIDGE_SAFE]
```

```text
EXECUTION_REALITY_WRITE_AUTHORITY =
  controlled_task_session_service
```
