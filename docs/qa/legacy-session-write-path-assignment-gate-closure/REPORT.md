# LEGACY SESSION WRITE PATH ASSIGNMENT GATE CLOSURE

## Verdict

```text
LEGACY_SESSION_WRITE_PATH_ASSIGNMENT_GATE_CLOSURE = PASS
ACTIVE_LEGACY_UNSAFE = 0
EXECUTION_REALITY_WRITE_AUTHORITY =
  services.controlled_task_session_service
  (start_controlled_task_session / end_controlled_task_session /
   complete_controlled_task_session)
PROFITABILITY_LABOR_INPUT_READINESS = READY
EMPLOYEE_MOBILE_UI_CHANGED = NO
FRONTEND_FEATURE_CHANGES = 0
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
NEXT_ROADMAP_DOMAIN = PROFITABILITY_ACTUAL_LABOR_INPUT_CLOSURE
NEXT_TASK = NOT_AUTHORIZED
```

## Writer inventory (after)

| Entry | Class |
|-------|-------|
| `POST …/sessions/start\|end` | CANONICAL |
| `POST /reality/start-task\|end-task` | COMPATIBILITY_BRIDGE_SAFE → controlled |
| `POST /operator/task-action` start | COMPATIBILITY_BRIDGE_SAFE → controlled |
| `POST /operator/task-action` complete | COMPATIBILITY_BRIDGE_SAFE → complete_controlled |
| Mobile PATCH start/complete | COMPATIBILITY_BRIDGE_SAFE → controlled |
| Helper sessions | COMPATIBILITY_BRIDGE (assist role; not principal assignee path) |
| Pause/block annotations | DEPRECATE_LATER (not START/END labor authority) |
| claim / start-from-available | DEAD_CANDIDATE / FROZEN |

## Key proofs

- Assignment gate parity on legacy + canonical
- Client timestamps ignored on `/reality/*`
- Cross-path start/end idempotency
- END session ≠ task complete preserved (`/reality/end-task` + sessions/end)
- Operator/mobile complete uses explicit completion stamp via same authority
- Regression: 80 passed (targeted suite)
